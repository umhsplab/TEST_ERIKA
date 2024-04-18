import os
import numpy as np
from tifffile import imread, imwrite, imsave
from scipy.ndimage import label, median_filter
from skimage.measure import regionprops
import cv2
import argparse 

def segment(srcPath:str = "/media/jaumatell/datos/MicroscopyIMG/DENSITY_02_24/231127/PSD95",
            ws:int = 150,   
            r:float = 1.5,
            method:str = "mean",
            min_size_2d:int = 64, # MINIM PIXELS SUPERFICIE EN EL FRAME
            min_size:int = 150, # MINIM PIXELS AREA EN L'STACK
            max_size:int = 9999, # MAXIM PIXELS AREA EN L'STACK 
            th_2d:float = 0, # NO TOCAR AQUEST
            th_3d:float = 0.2):
    
    output_path = os.path.join(srcPath, "Segmented_for_density")
    os.mkdir(output_path) 
    srcFiles = [f for f in os.listdir(srcPath) if f.endswith('.tif')]
    seq = []

    for iterator_value in range(len(srcFiles)):
        jj = iterator_value
        file_name = srcFiles[iterator_value]

        print(f"Starting image {file_name}.")

        I = imread(os.path.join(srcPath, file_name))
        seq.append({"name": file_name, "I": np.uint16(I)})
        f, c, p = I.shape

        is_binary_image = np.all((I == 0) | (I == 1))
        if is_binary_image:
            print(f'The image {seq[jj]["name"]} is a bw image. It will not be processed')
        else:
            Imat = I.astype(float) / np.max(I)
            meanImat = np.zeros_like(Imat)
            sImat = meanImat
            medianImat = np.zeros_like(Imat)
            bwImat = meanImat
            join1D = np.zeros((c, p))
            join2D = np.zeros_like(bwImat).astype(np.uint8)

            for i in range(f):

                meanImat[i, :, :] = cv2.blur(Imat[1, :, :], (int(ws), int(ws)))
                img_to_store = meanImat * 255/np.max(meanImat)

                C = -np.mean(Imat[i, :, :]) / r
                sImat[i, :, :] = meanImat[i, :, :] - Imat[i, :, :] - C
                sImat = sImat * (255/np.max(sImat))
                
                bwImat[i, :, :] = sImat[i, :, :] > th_2d
                bwImat[i, :, :] = np.logical_not(bwImat[i, :, :])
                bwImat = bwImat * (255/np.max(bwImat))
            
            labeled_bw, num_objects = label(bwImat[i, :, :], structure=[[1, 1, 1], [1, 1, 1], [1, 1, 1]])

            for i in range(f):
                labeled_bw, num_objects = label(bwImat[i, :, :], structure=[[1, 1, 1], [1, 1, 1], [1, 1, 1]])
                for obj_id in range(1, num_objects + 1):
                    pix_id = np.where(labeled_bw == obj_id)
                    if len(pix_id[0]) > min_size_2d:
                        for pix in range(len(pix_id[0])):
                            join1D[pix_id[0][pix], pix_id[1][pix]] = 1

                join2D[i, :, :] = join1D
                join1D = np.zeros((c, p))

            imwrite(os.path.join(output_path, file_name + "_join2D.tif"), join2D.astype(np.uint8))

            labeled_j2D, num_objects_j2D = label(join2D, structure=np.ones((3, 3, 3)))
            props_j2D = regionprops(labeled_j2D)

            join3D = np.zeros_like(join2D)
            for obj in props_j2D:
                object_size = obj["area"]
                Num_frames = len(np.unique(obj["coords"][:,0]))
                if (Num_frames > 1 and object_size + 1 > min_size and object_size + 1 < max_size):
                    join3D[obj.coords[:, 0], obj.coords[:, 1], obj.coords[:, 2]] = True

            segmented_image = join3D * (I * (255/65535))
            join3D = join3D * (255/np.max(join3D))
            output_file_name = os.path.join(output_path, file_name + '_join3D' + '_segmented.tif')
            imwrite(output_file_name, join3D.astype(np.uint8), append=True, photometric= "minisblack")
            output_file_name = os.path.join(output_path, file_name + '_join3D' + '_mask.tif')
            imwrite(output_file_name, segmented_image.astype(np.uint8), append=True, photometric= "minisblack")

            print("Object selection")
            thIseg3D = np.zeros_like(segmented_image)
            for i in range(f):
                thIseg3D[i, :, :] = segmented_image[i, :, :] > (th_3d*np.max(segmented_image))
                labeled_bw2, num_objects2 = label(thIseg3D[i, :, :], structure=[[1, 1, 1], [1, 1, 1], [1, 1, 1]])
            join1D2 = np.zeros((c, p))
            join2D2 = np.zeros_like(thIseg3D)


            for i in range(f):
                labeled_bw2, num_objects2 = label(thIseg3D[i, :, :], structure=[[1, 1, 1], [1, 1, 1], [1, 1, 1]])
                count_obj = 0
                for obj_id in range(1, num_objects2 + 1):
                    pix_id = np.where(labeled_bw2 == obj_id)
                    if len(pix_id[0]) > min_size_2d:
                        count_obj = count_obj + 1
                        for pix in range(len(pix_id[0])):
                            join1D2[pix_id[0][pix], pix_id[1][pix]] = 1                
                join2D2[i, :, :] = join1D2
                join1D2 = np.zeros((c, p))
            imwrite(os.path.join(output_path, file_name + "_join2D2.tif"), join2D2.astype(np.uint8)*255, photometric= "minisblack") 

            labeled_j2D2, num_objects_j2D2 = label(join2D2, structure=np.ones((3, 3, 3)))
            props_j2D2 = regionprops(labeled_j2D2)

            join3D2 = np.zeros_like(join2D2)
            for obj in props_j2D2:
                object_size = obj["area"]
                # Check if there is more than one different frame on the pixels pb the object 
                Num_frames = len(np.unique(obj["coords"][:,0]))
                if (Num_frames > 1 and object_size + 1 > min_size and object_size + 1 < max_size):
                    join3D2[obj.coords[:, 0], obj.coords[:, 1], obj.coords[:, 2]] = True

            segmented_image2 = np.zeros_like(join3D2)
            segmented_image2 = (join3D2/255) * I
            segmented_image2 = segmented_image2 * (255/np.max(I))
            segmented_image2 = segmented_image2.astype(np.uint8)
            segmented_image2 = segmented_image2 *255

            join3D2 = join3D2 * (255/np.max(join3D2))

            output_file_name = os.path.join(output_path, file_name + '_join3D2' + '_segmented.tif')
            imwrite(output_file_name, join3D2.astype(np.uint8), photometric= "minisblack")

            output_file_name = os.path.join(output_path, file_name + '_join3D2' + '_mask.tif')
            imwrite(output_file_name, segmented_image2.astype(np.uint8), photometric= "minisblack")


    with open(os.path.join(output_path, "parameters.txt"), 'w') as file:
        # Write variable names and values to the file
        file.write(f"srcPath: {srcPath}\n")
        file.write(f"WS: {ws}\n")
        file.write(f"r: {r}\n")
        file.write(f"method: {method}\n")
        file.write(f"min_size_2d: {min_size_2d}\n")
        file.write(f"min_size: {min_size}\n")
        file.write(f"max_size: {max_size}\n")
        file.write(f"threshold_2d: {th_2d}\n")
        file.write(f"threshold_3d: {th_3d}\n")

    print("Process complete.")

def main():
    parser = argparse.ArgumentParser(
        description="""
Synapse Segmentation:

This function lists the tif files contained on the given directory 
and segments the objects after a preprocessing step.

        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-path', 
                        dest='src_path', 
                        type=str, 
                        required=True, 
                        help='Path to the directory containing input images')
    parser.add_argument('-ws',
                        '--window_size', 
                        type=int, 
                        default=150, 
                        help='Window size for local mean or median filter')
    parser.add_argument('-r',
                        '--r_factor', 
                        type=float, 
                        default=1.5, 
                        help='Factor for calculating the threshold in the filter')
    parser.add_argument('-method',
                        '--method', 
                        choices=['mean', 'median'], 
                        default= 'mean', 
                        help='Method for filtering')
    parser.add_argument('-min_surf',
                        '--minimum_surface', 
                        type=int, 
                        default=16, 
                        help='Minimum 2D surface of an object')
    parser.add_argument('-min_size',
                        '--minimum_size',
                        type=int, 
                        default=150, 
                        help='Minimum 3D volume of an object')
    parser.add_argument('-max_size',
                        '--maximum_size', 
                        type=int, 
                        default=99999, 
                        help='Maximum 3D volume of an object')
    parser.add_argument('-th_2d',
                        '--threshold_2d', 
                        type=float, 
                        default=0, 
                        help='Minimum size of an object')
    parser.add_argument('-th_3d', 
                        '--threshold_3d'
                        type=float, 
                        default=0.2, 
                        help='Minimum size of an object')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the function with the parsed arguments
    segment(args.src_path, args.ws, args.r, args.method, args.min_surf, args.min_size, args.max_size, args.th1,  args.th2)



if __name__ == "__main__":
    main()
