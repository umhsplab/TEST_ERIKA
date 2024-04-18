import os
import numpy as np
import tifffile
import argparse
import warnings
import pandas as pd
from tqdm import tqdm
from skimage import measure
from datetime import datetime
from scipy.ndimage import label, center_of_mass
from pathlib import Path, PureWindowsPath
from math import sqrt
from functions.extract_unique_texts_between_parentheses import extract_unique_texts_between_parentheses
from functions.group_files_by_common_part2 import group_files_by_common_part 
from functions.calculate_per_dist import calculate_per_dist
from functions.combine_and_draw2 import combine_and_draw2
from functions.combine_plots import combine_plots
from functions.wrapper_function import log_function_call

warnings.simplefilter(action='ignore', category=FutureWarning)

@log_function_call("SYN_DISTANCE_log")
def workflow(PATH:str, 
             th_percent:float = 0.2, 
             x_y_ratio:float = 0.008, 
             plot_save:bool = True)->None:
    """
    Perform a workflow to analyze and measure objects in a series of microscopy images.

    This function reads a series of microscopy images from a specified directory, performs object
    detection and measurement, and saves the results to a CSV file. It also provides the option
    to save visualization plots.

    Parameters:
        PATH (str): The path to the directory containing the microscopy images.
        th_percent (float): The threshold percentage for image binarization.
        x_y_ratio (float): The ratio of micrometers (um) to pixels (pix) for distance conversion.
        plot_save (bool): If True, generate and save visualization plots.

    Returns:
        None

    Example:
        >>> workflow("image_directory", 0.7, 0.1, True)
    """

    Wpath = PureWindowsPath(PATH)
    PATH = Path(Wpath)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    file_list = [file for file in os.listdir(PATH) if file.endswith(".tif")]
    unique_texts_between_parentheses = extract_unique_texts_between_parentheses(file_list)
    Files = group_files_by_common_part(file_list, unique_texts_between_parentheses)

    if plot_save:
        if not os.path.exists(PATH / "VIZ"):
                            os.mkdir(PATH / "VIZ")
    df = pd.DataFrame()
    count = 0
    with tqdm( total=len(Files),desc= "Images processed" ,unit='image', leave=False) as progress_bar:
        for Filegroup in Files:
            progress_bar.update(1)
            count += 1
            Filegroup = sorted(Filegroup)

            I = tifffile.imread(PATH / Filegroup[0])
            I2 = tifffile.imread(PATH / Filegroup[1])
            CH1_name = str(extract_unique_texts_between_parentheses([Filegroup[0]])[0])
            CH2_name = str(extract_unique_texts_between_parentheses([Filegroup[1]])[0])

            Dist = None

            frame_range = 1 if len(I.shape) == 2 else I.shape[0] 
            for frame in range(frame_range):
                
                # miss object
                miss_A = False
                miss_B = False
                if frame_range == 1:
                    threshold_A = np.max(I)*th_percent
                    threshold_B = np.max(I2)*th_percent

                    # Threshold
                    A = label(I>threshold_A)[0]
                    B = label(I2>threshold_B)[0]

                else:
                    threshold_A = np.max(I[frame])*th_percent
                    threshold_B = np.max(I2[frame])*th_percent

                    A = label(I[frame]>threshold_A)[0]
                    B = label(I2[frame]>threshold_B)[0]

                PropA = measure.regionprops(A)
                PropB = measure.regionprops(B)
                
                try:
                    Index_A = max(PropA, key=lambda region: region.area).label
                except:
                    Index_A = 1
                    miss_A = True
                try:
                    Index_B = max(PropB, key=lambda region: region.area).label
                except:
                    Index_B = 1
                    miss_B = True

                if miss_A == False and miss_B == False:
                    COM_A = center_of_mass(A == Index_A)
                    COM_B = center_of_mass(B == Index_B)

                    X = abs(COM_A[0] - COM_B[0]) if COM_A[0] > COM_B[0] else abs(COM_B[0] - COM_A[0])
                    Y = abs(COM_A[1] - COM_B[1]) if COM_A[1] > COM_B[1] else abs(COM_B[1] - COM_A[1])
                    
                    COM_Dist = sqrt(X**2 + Y**2)
                    COM_Dist_um = COM_Dist * x_y_ratio

                    POSA = np.where(A == Index_A)
                    POSB = np.where(B == Index_B)

                    POS_A = []
                    POS_B = []

                    for posit in range(len(POSA[0])):
                        POS_A.append((POSA[0][posit], POSA[1][posit]))
                    for posit in range(len(POSB[0])):
                        POS_B.append((POSB[0][posit], POSB[1][posit]))

                    A_set = set(POS_A)
                    B_set = set(POS_B)

                    if A_set.intersection(B_set):
                        Per_Dist = "OVERLAP"
                        Per_Dist_um = "OVERLAP"
                        A_position = ""
                        B_position = ""
                        Avg_per_dist_um = "CONTACT"
                        Avg_per_dist = "CONTACT"
                        
                    else:
                        Per_Dist, A_position, B_position, Avg_per_dist = calculate_per_dist(POS_A, POS_B, 3)
                        if Per_Dist == 0:
                            Per_Dist = "CONTACT"
                            per_Dist_um = "CONTACT"
                            Avg_per_dist_um = "CONTACT"
                            Avg_per_dist = "CONTACT"
                            
                        else:
                            Per_Dist_um = Per_Dist * x_y_ratio
                            Avg_per_dist_um = Avg_per_dist * x_y_ratio


                    if plot_save:
                        center_of_mass_plot  = combine_and_draw2(A, B, COM_A, COM_B)
                        if Per_Dist == "OVERLAP":
                            X, Y = A.shape
                            image1  = np.zeros((X, Y, 4), dtype=np.uint8)
                            image1 [:, :, 0] = A*(255/np.max(A))
                            image1 [:, :, 1] = B*(255/np.max(B))

                            plot_perimeter_distance = image1

                            for x,y in A_set.intersection(B_set):
                                plot_perimeter_distance[x,y] = [0, 77, 255, 0] 
                        else:    
                            plot_perimeter_distance = combine_and_draw2(A, B, A_position, B_position)

                        file_name = Filegroup[0].split("(")[0]+str(frame)+".png"
                        combine_plots(A = A, 
                                    B = B, 
                                    image2 = center_of_mass_plot, 
                                    image3 = plot_perimeter_distance, 
                                    COM_dis = COM_Dist_um, 
                                    PER_dis = Per_Dist_um,
                                    Path = PATH / "VIZ" / file_name )


                    data = {
                        'Name': Filegroup[0].split("(")[0],
                        'Frame': frame,
                        'Centroid_'+CH1_name: COM_A,
                        'Centroid_'+CH2_name: COM_B,
                        'Perimeter_P_'+CH1_name: A_position,
                        'Perimeter_P_'+CH2_name: B_position,
                        'Area_'+CH1_name: PropA[Index_A-1].area,
                        'Area_'+CH2_name: PropB[Index_B-1].area,
                        'Area_um_'+CH1_name: PropA[Index_A-1].area * x_y_ratio**2,
                        'Area_um_'+CH2_name: PropB[Index_B-1].area * x_y_ratio**2,
                        'Center_Distance_px': COM_Dist,
                        'Perimeter_Distance_px' : Per_Dist,
                        'Center_Distance_um': COM_Dist_um,
                        'Perimeter_Distance_um' : Per_Dist_um,
                        'Perimeter_Distance_um' : Per_Dist_um,
                        'Average_Distance_um': Avg_per_dist_um
                        }   
                elif miss_A == True and miss_B == False:

                    POSB = np.where(B == Index_B)

                    data = {
                        'Name': Filegroup[0].split("(")[0],
                        'Frame': frame,
                        'Centroid_'+CH1_name: "null",
                        'Centroid_'+CH2_name: COM_B,
                        'Perimeter_P_'+CH1_name: "null",
                        'Perimeter_P_'+CH2_name: "null",
                        'Area_'+CH1_name: "null" ,
                        'Area_'+CH2_name: PropB[Index_B-1].area,
                        'Area_um_'+CH1_name: "null",
                        'Area_um_'+CH2_name: PropB[Index_B-1].area * x_y_ratio**2,
                        'Center_Distance_px': "null",
                        'Perimeter_Distance_px' : "null",
                        'Center_Distance_um': "null",
                        'Perimeter_Distance_um' : "null",
                        'Perimeter_Distance_um' : "null",
                        'Average_Distance_um': "null"
                        }  

                elif miss_A == False and miss_B == True:

                    POSA = np.where(A == Index_A)
                    
                    data = {
                        'Name': Filegroup[0].split("(")[0],
                        'Frame': frame,
                        'Centroid_'+CH1_name: COM_A,
                        'Centroid_'+CH2_name: "null",
                        'Perimeter_P_'+CH1_name: "null",
                        'Perimeter_P_'+CH2_name: "null",
                        'Area_'+CH1_name: PropA[Index_A-1].area,
                        'Area_'+CH2_name: "null",
                        'Area_um_'+CH1_name: PropA[Index_A-1].area * x_y_ratio**2,
                        'Area_um_'+CH2_name: "null",
                        'Center_Distance_px': "null",
                        'Perimeter_Distance_px' : "null",
                        'Center_Distance_um': "null",
                        'Perimeter_Distance_um' : "null",
                        'Perimeter_Distance_um' : "null",
                        'Average_Distance_um': "null"
                        }  
                else :

                    data = {
                        'Name': Filegroup[0].split("(")[0],
                        'Frame': frame,
                        'Centroid_'+CH1_name: "null",
                        'Centroid_'+CH2_name: "null",
                        'Perimeter_P_'+CH1_name: "null",
                        'Perimeter_P_'+CH2_name: "null",
                        'Area_'+CH1_name: "null",
                        'Area_'+CH2_name: "null",
                        'Area_um_'+CH1_name: "null",
                        'Area_um_'+CH2_name: "null",
                        'Center_Distance_px': "null",
                        'Perimeter_Distance_px' : "null",
                        'Center_Distance_um': "null",
                        'Perimeter_Distance_um' : "null",
                        'Perimeter_Distance_um' : "null",
                        'Average_Distance_um': "null"
                        }
                
                df = pd.concat([df,pd.DataFrame.from_dict(data)])
    results_file = "Distance_results_" + str(current_time) + ".csv"
    df.to_csv(PATH / results_file.replace(":", "_"))
    print("Process complete.")


#####################################################################################
# Parser 

def main():
    parser = argparse.ArgumentParser(description="Microscopy Image Analysis Workflow")
    parser.add_argument("PATH", 
                        type=str, 
                        help="Path to the image directory")
    parser.add_argument("-th",
                        "--th_percent", 
                        type=float, 
                        default=0.2, 
                        help="Threshold percentage for image binarization")
    parser.add_argument("-xy",
                        "--x_y_ratio", 
                        type=float, 
                        default=0.008, 
                        help="Ratio of micrometers to pixels for distance conversion")
    parser.add_argument("-ps",
                        "--plot_save", 
                        action="store_true", 
                        help="Save visualization plots")
    args = parser.parse_args()
    workflow(args.PATH, 
             args.th_percent, 
             args.x_y_ratio,
             args.plot_save)


if __name__ == "__main__":
    main()
