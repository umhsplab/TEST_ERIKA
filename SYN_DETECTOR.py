import argparse
import os
import cv2
import warnings
import numpy as np
import pandas as pd
from tifffile import imread, imwrite
from datetime import datetime
from PIL import Image 
from tqdm import tqdm
from pathlib import Path, PureWindowsPath
from functions.extract_unique_texts_between_underscores import extract_unique_texts_between_underscores 
from functions.group_files_by_common_part import group_files_by_common_part
from functions.preprocess_image import preprocess_image 
from functions.object_identificator import object_identificator 
from functions.calculate_per_dist import calculate_per_dist 
from functions.cmyk_to_rgb import cmyk_to_rgb 
from functions.spiderwebs import spiderwebs 
from functions.ROI_MAP import ROI_MAP
from functions.wrapper_function import log_function_call
warnings.simplefilter(action='ignore', category=FutureWarning)

#@log_function_call("SYN_DETECTOR_log_")
def extract_rois(PATH:str, 
                 x_y_ratio:float = 0.008, 
                 max_distance:float = 0.2, 
                 min_area:int = 6, 
                 th_percentage:float = 0.9, 
                 neuropil_channel = "SYPH",
                 saverois:bool = False,
                 Spiderweb:bool = False,
                 RoiMap:bool = True):
    """
    Extract and analyze regions of interest (ROIs) from image files.

    Parameters:
        PATH (str): The path to the directory containing image files.
        x_y_ratio (float, optional): Pixel size ratio for image analysis (default: 0.008).
        max_distance (float, optional): Maximum distance for considering objects as close (default: 0.2).
        min_area (int, optional): Minimum area of objects to be considered (default: 6).
        th_percentage (float, optional): Threshold percentage for image binarization (default: 0.9).
        saverois (bool, optional): Whether to save extracted ROIs (default: False).
        Spiderweb (bool, optional): Whether to generate spiderweb visualizations (default: False).
        RoiMap (bool, optional): Whether to generate ROI maps (default: True).

    Returns:
        None
    """

    # Windows path management
    Wpath = PureWindowsPath(PATH)
    PATH = Path(Wpath)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S').replace(" ", "_")

    ### REQUIRED OBJECTS GENERATION
    structure_3D = np.array([
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        ])
    
    # kernel generation
    kernel_3x3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))

    ### Directory file listing and sorting 
    file_list = [file for file in os.listdir(PATH) if file.endswith(".tif")]
    unique_texts_between_parentheses = extract_unique_texts_between_underscores(file_list)
    Files = group_files_by_common_part(file_list, unique_texts_between_parentheses, neuropil_channel)


    ### MAKING STORAGE FOLDERS 
    if not os.path.exists(PATH /"Filtered"):
        os.mkdir(PATH / "Filtered")

    if saverois == True:
        if not os.path.exists(PATH / "ROIs"):
            os.mkdir(PATH / "ROIs")

    if not os.path.exists(PATH / "ROI_MAPS"):
        os.mkdir(PATH / "ROI_MAPS")  

    ### File Management
    for Filegroup in Files:
        c=0
        # Read files
        image = imread(PATH / Filegroup[0])
        image2 = imread(PATH / Filegroup[1])

        #### Preprocess the image format  
        image = image * (255 / np.max(image))
        image2 = image2 * (255 / np.max(image2))

        # Confirm the given image shapes match
        if not image.shape == image2.shape:
            print(f"Shapes of {Filegroup[0]} ({image.shape}) and {Filegroup[1]} ({image2.shape}) doesn't match")
            continue
        
        # Extract image shapes
        frame_n, x, y = image.shape
        # Calculate the maximum distances 
        max_distance_px = max_distance/x_y_ratio
        max_distance_px = max_distance_px**2

        # Generate empty images to store results and intermediate images
        mask = np.zeros_like(image)
        closed = np.zeros_like(image)
        closed2 = np.zeros_like(image2)

        # Generate empty dataframes to store the results
        df = pd.DataFrame(columns = [
                                    'ImageName',
                                    'Frame',
                                    'com',
                                    'com2',
                                    'object_label',
                                    'object2_label',
                                    'Distance_com',
                                    'Distance_um',
                                    'object_roi',
                                    'object2_roi',
                                    'big_roi',
                                    'Area',
                                    'Area2',
                                    'Object_nearest_point',
                                    'Object2_nearest_point',
                                    'Min_distance'
                                    ])
        
        image_props = pd.DataFrame()   
        image2_props = pd.DataFrame()   
        
        # Iterate through frames
        for frame in range(frame_n):
            
            # Apply a closing filter to the images
            closing = preprocess_image(image, frame, th_percentage, kernel_3x3)
            closing2 = preprocess_image(image2, frame, th_percentage, kernel_3x3)

            # Store the filtered image to it's correspondent stack
            closed[frame,:,:] = closing
            closed2[frame,:,:] = closing2

            # Generate filenames
            im_name = str(Filegroup[0]).replace(".tif", '_layer_closed_') + str(frame) + '.tif'
            im_name2 = str(Filegroup[1]).replace(".tif", '_layer_closed_') + str(frame) + '.tif'

            # Save the filtered frame images
            imwrite(PATH / "Filtered" / im_name, closing.astype(np.uint8))
            imwrite(PATH / "Filtered" / im_name2, closing2.astype(np.uint8))

            # Identify objects on the image and get their propieties
            image_labeled, image_proprieties = object_identificator(closing, frame, min_area)
            image2_labeled, image2_proprieties = object_identificator(closing2, frame, min_area)

            # Concatenate the dataframe with the object proprieties per each image independently
            image_props = pd.concat([image_props, image_proprieties])
            image2_props = pd.concat([image2_props, image2_proprieties])

            # Visual progressbar
            with tqdm( total=image_proprieties.shape[0],desc= str(Filegroup[0])+"_"+str(frame) ,unit=' objects', leave=False) as progress_bar:

                # Iterate throug objects found on the first image
                for object_index, object_index_props in image_proprieties.iterrows():
                    progress_bar.update(1)

                    # Iterate through objects found on the second image
                    for object2_index, object2_index_props in image2_proprieties.iterrows():
                        
                        # If the frame number does not match among the images go to the next object
                        if object2_index_props["Frame"] != object_index_props["Frame"]:
                            continue
                        
                        # Extract the x and y coordinates for each object centroid
                        ob_x, ob_y = object_index_props['centroid-0'], object_index_props['centroid-1']
                        ob2_x, ob2_y = object2_index_props['centroid-0'], object2_index_props['centroid-1']

                        # Calculate the diference of position between the centroids of the 2 objects
                        x_dif = np.abs(ob_x - ob2_x)
                        y_dif = np.abs(ob_y - ob2_y)

                        # Calculate the sum of the squared coordinate disatances ( Equivalent to hipotenusa  but without squared root for computational optimization)
                        distance = x_dif**2 + y_dif**2

                        # If the calculated distance is bigger than the max distance stablished by the user squared
                        if distance < max_distance_px:
                            c += 1
                            
                            # Calculate the distance using pythagoras (squared root of the sum of the squared cateters)
                            distance_final = np.sqrt(x_dif**2 + y_dif**2)
                            
                            #Obtain a list of the coordinates of the pixels in each object
                            object_positions = np.where(image_labeled == object_index)
                            object2_positions = np.where(image2_labeled == object2_index)

                            # Generate empty lists to append the positions
                            POS_A = []
                            POS_B = []

                            # Format the positions in a list for easy access
                            for posit in range(len(object_positions[0])):
                                POS_A.append((object_positions[0][posit], object_positions[1][posit]))
                            #
                            for posit in range(len(object2_positions[0])):
                                POS_B.append((object2_positions[0][posit], object2_positions[1][posit]))

                            # Generate a set with the lists of pixel positions
                            A_set = set(POS_A)
                            B_set = set(POS_B)

                            # Chech if there is an overlap of the objects
                            if A_set.intersection(B_set):

                                # Set the values for the overlap case
                                min_distance = "OVERLAP"
                                object_near_point = ""
                                object2_near_point = ""

                            # If there is no overlap between the objects
                            else:
                                # Calculate the minimum distance between the objects
                                min_distance, object_near_point, object2_near_point, avg_min_dist = calculate_per_dist(POS_A, POS_B)

                            # Obtain the rois that capture the objects 
                            min_row, min_col, max_row, max_col = object_index_props['bbox-0'], object_index_props['bbox-1'], object_index_props['bbox-2'], object_index_props['bbox-3']
                            min_row2, min_col2, max_row2, max_col2 = object2_index_props['bbox-0'], object2_index_props['bbox-1'], object2_index_props['bbox-2'], object2_index_props['bbox-3']

                            # Select the minimum and maximum coordinates of the 2 objects with 10 pixels margin
                            big_roi_min_x = min(min_row, min_row2) - 10
                            big_roi_min_y = min(min_col, min_col2) - 10
                            big_roi_max_x = max(max_row, max_row2) + 10
                            big_roi_max_y = max(max_col, max_col2) + 10
    
                            # Ensure the roi exists in the image ( no negative pixels or position bigger than the image dimensions)
                            big_roi_min_x = max(big_roi_min_x, 0)
                            big_roi_max_x = min(big_roi_max_x, x-1)
                            big_roi_min_y = max(big_roi_min_y, 0)
                            big_roi_max_y = min(big_roi_max_y, y-1)

                            #List the final positions of the roi that captures the 2 objects
                            big_roi = [big_roi_min_x, 
                                    big_roi_max_x,
                                    big_roi_min_y, 
                                    big_roi_max_y]

                            # Create a dictionary to store the results obtained on the analisis process
                            df_new_row = {
                                'ImageName': Filegroup[0],
                                'Frame': object2_index_props['Frame'],
                                'com': [object_index_props['centroid-0'], object_index_props['centroid-1']],
                                'com2': [object2_index_props['centroid-0'], object2_index_props['centroid-1']],
                                'object_label': object_index,
                                'object2_label': object2_index,
                                'Distance_com': distance_final,
                                'Distance_um' : distance_final*x_y_ratio,
                                'object_roi': [min_row, min_col, max_row, max_col],
                                'object2_roi': [min_row2, min_col2, max_row2, max_col2],
                                'big_roi': big_roi,
                                'Area': object_index_props['area'],
                                'Area2': object2_index_props['area'],
                                'Object_nearest_point': object_near_point,
                                'Object2_nearest_point': object2_near_point,
                                'Min_distance': min_distance
                                }
                            
                            # Save the dictionary as a dataframe
                            newrow = pd.DataFrame.from_dict(df_new_row)
                            
                            # Join the Results dataframe with the new generated dataframe.
                            df = pd.concat([df, newrow], ignore_index= True)

                            # Extract the ROI corner positions 
                            i_x = int(big_roi[0])
                            f_x = int(big_roi[1])
                            i_y = int(big_roi[2])
                            f_y = int(big_roi[3])
                            
                            # If the images are too big 
                            if f_x - i_x >200 or f_y - i_y > 200:
                                continue

                            # Add the roi to the mask
                            mask[int(df_new_row['Frame']), i_x:f_x, i_y:f_y] = 1

                            # If the user selected to save images
                            if saverois == True:
                                
                                # Generate a blank image of the size of the calculated roi in RGB format
                                Final_ROI = np.zeros((frame_n,f_x-i_x,f_y-i_y, 3))

                                # Generate a blank image of the size of the calculated roi in CMYK format
                                ROI = np.zeros((frame_n,f_x-i_x,f_y-i_y, 4))

                                #Iterate per frame
                                for frame in range(frame_n):

                                    # Calculate the positions of the center of mass for the 2 objects in the roi.
                                    cm1x = int(ob_x) - int(i_x)
                                    cm1y = int(ob_y) - int(i_y)
                                    cm2x = int(ob2_x) - int(i_x)
                                    cm2y = int(ob2_y) - int(i_y)

                                    # Store each protein in a diferent color channel (Cyan and Magenta)
                                    ROI[frame,:,:,0] = image[frame,i_x:f_x,i_y:f_y]
                                    ROI[frame,:,:,1] = image2[frame,i_x:f_x,i_y:f_y]

                                    # Set the center of mass pixels for each object yellow 
                                    ROI[frame,cm1x,cm1y,:] = [0,0,255,0] 
                                    ROI[frame,cm2x,cm2y,:] = [0,0,255,0]
                                    
                                    # transform the CMYK image format to RGB 
                                    ROI_rgb = cmyk_to_rgb(ROI[frame,:,:,0] ,ROI[frame,:,:,1], ROI[frame,:,:,2], ROI[frame,:,:,3])
                                    
                                    # Store the frame in RGB on i'ts correpondent Image
                                    Final_ROI[frame,:,:,:] = ROI_rgb.astype(np.uint8)
                                
                                # Save the generated RGB image of the ROI 
                                ROIname = str(Filegroup[0]).replace('.tif','')+"_ROI_"+"_y_"+str(i_x)+"_"+str(f_x)+"_x_"+str(i_y)+"_"+str(f_y)+"_n_"+str(c)+".tif"
                                imwrite(PATH / "ROIs"/ ROIname, Final_ROI.astype(np.uint8))

############################### SAVE RESULTS ############################

        # Generate the filenames for the closed (filtered) image
        closed1_name = str(Filegroup[0]).replace(".tif", '_closed_') + '.tif'
        closed2_name = str(Filegroup[1]).replace(".tif", '_closed_') + '.tif'
        
        # Generate the filename for the mask image
        mask_name = str(Filegroup[1]).replace(".tif", '_mask_') + '.tif'
        
        # Save the images with their respective names
        imwrite(PATH / "Filtered" / closed1_name, closed.astype(np.uint8), imagej=True)
        imwrite(PATH / "Filtered" / closed2_name, closed2.astype(np.uint8), imagej=True)
        imwrite(PATH / "Filtered" / mask_name , mask.astype(np.uint8), imagej=True)

        # Generate the Results file name
        results_detection_file = 'Results_Detection_' + str(current_time) + '.csv'
        
        # Save the results dataframe as csv file.
        df.to_csv(PATH / results_detection_file.replace(":","_"))

#################### FINAL ROI MAP ############################################################
        
        # Generate spiderweb visualization if selected
        if Spiderweb:
            spiderwebs(image=image, image2= image2, df= df, mask= mask, filename= Filegroup[0], PATH= PATH, th_percentage=th_percentage)

        # Generate Roi map visualization if selected
        if RoiMap:
            ROI_MAP(image=image, image2= image2, df= df, mask= mask, filename= Filegroup[0], PATH= PATH, th_percentage=th_percentage)

    
#########################################################################################
# ARGPARSE

def main():
    parser = argparse.ArgumentParser(description='Extract and analyze regions of interest (ROIs) from image files.')
    
    parser.add_argument('PATH', 
                        type=str, 
                        help='Path to the directory containing image files.')
    parser.add_argument('-xy',
                        '--x_y_ratio', 
                        type=float, 
                        default=0.008, 
                        help='Pixel size ratio for image analysis (default: 0.008).')
    parser.add_argument('-md',
                        '--max_distance', 
                        type=float, 
                        default=0.2, 
                        help='Maximum distance for considering objects as close (default: 0.2).')
    parser.add_argument('-ma',
                        '--min_area', 
                        type=int, 
                        default=6, 
                        help='Minimum area of objects to be considered (default: 6).')
    parser.add_argument('-th',
                        '--th_percentage', 
                        type=float, 
                        default=0.9, 
                        help='Threshold percentage for image binarization (default: 0.9).')
    parser.add_argument('-roi',
                        '--saverois', 
                        action='store_true', 
                        help='Whether to save extracted ROIs (default: False).')
    parser.add_argument('-nc',
                            '--neuropil_ch', 
                            type=str,
                            default= "SYPH",
                            help='Indicate the neuropil channel.')
    parser.add_argument('-sw',
                        '--Spiderweb', 
                        action='store_true', 
                        help='Generate spiderweb visualizations (default: False).')
    parser.add_argument('-roim',
                        '--RoiMap', 
                        action='store_true', 
                        help='Generate ROI maps (default: True).')

    args = parser.parse_args()
    
    extract_rois(args.PATH, 
                 args.x_y_ratio, 
                 args.max_distance, 
                 args.min_area, 
                 args.th_percentage, 
                 args.neuropil_ch,
                 args.saverois, 
                 args.Spiderweb, 
                 args.RoiMap)

if __name__ == "__main__":
    main()