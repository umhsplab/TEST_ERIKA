import os
import cv2
import numpy as np
import pandas as pd
from tifffile import imread, imwrite
from scipy.ndimage import label, generate_binary_structure
from datetime import datetime
from pathlib import Path, PureWindowsPath
from functions.extract_unique_texts_between_underscores import extract_unique_texts_between_underscores
from functions.group_files_by_common_part import group_files_by_common_part 
from functions.modify_filename import modify_filename
from functions.check_continuity import check_continuity
from functions.wrapper_function import log_function_call

import argparse


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

###############################################################################
# SYN_DENSITY. To CALCULATE PER LAYER AND TOTAL DENSITY                       #
###############################################################################

@log_function_call("SYN_DENSITY_log") # log file with the input parameters for the processing
def Densiometer(PATH:str, 
         PROJECT_TECHNIQUE:str = "STORM", 
         neuropil_channel:str = "SYPH", 
         channels = ["SYPH", "PSD95"],
         x_y_ratio = None, 
         z_ratio = None)-> None:
    """
    Main function to perform density calculations on image files.

    Parameters:
        PATH (str): The path to the directory containing image files.
        PROJECT_TECHNIQUE (str): The project technique, can be "STORM" or "ARRAY" (default: "STORM").
        neuropil_channel (str): The neuropil channel identifier (default: "SYPH").
        threshold (float): The threshold value for object identification (default: 0.9).
        x_y_ratio (float): The pixel size ratio for X and Y dimensions (default: None).
        z_ratio (float): The pixel size ratio for the Z dimension (default: None).

    Returns:
        None
    
    Generates:
        Results_density_(date).csv : This file contains a table with the obtained data from the process.
        Each row represents a image file. The columns contain the following information:
            -   name : Contains the filename of the processed image.
            -   areatotal : Contains the volume of pixels captured on the image as px³
            -   areaneuropil : Contains the volume of pixels of neuropil area captured on the image as px³
            -   objN : Quantification of total objects identifyed in the image.
            -   density_total_area : Objects per um³ on the total volume of the image.
            -   density_area_neuropil : Objects per um³ on the neuropil area of the image.
            -   layer_surface : Surface of pixels captured on each image frame as px²
            
    """

    # WINDOWS PATH MANAGEMENT
    Wpath = PureWindowsPath(PATH)
    PATH = Path(Wpath)    
    # Comment the windows path management if Linux path is being used. 
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    ################# Save Masks ? #####################################################
    save_masks = False        # Set to true to check intermediate images for debugging #
    ####################################################################################


    # PIXEL SIZE SELECTION
    # if not user stablished, the ratios are inhereted from the technique presets.
    if x_y_ratio == None:
        if PROJECT_TECHNIQUE == "STORM":
            x_y_ratio = 0.008
        elif PROJECT_TECHNIQUE == "ARRAY":
            x_y_ratio = 0.4274 
    
    if z_ratio == None:
        if PROJECT_TECHNIQUE == "STORM":
            z_ratio = 0.07
        elif PROJECT_TECHNIQUE == "ARRAY":
            z_ratio = 0.07
        
    # FILE LISTING AND SELECTION
    srcFiles = [file for file in os.listdir(PATH) if file.endswith('.tif')]
    filelist = [file for file in srcFiles if neuropil_channel in file]
    
    # REQUIRED OBJECTS DEFINITION

    ## dataframe to store results
    Results = pd.DataFrame()

    ## px3 to um3 ratio
    Area_ratio = x_y_ratio*x_y_ratio*z_ratio
    # px2 to um2 ratio
    Surface_ratio = x_y_ratio + x_y_ratio
    
    ## Object detection kernel generation
    structure = generate_binary_structure(3, 1)      # 3D continuity detector
    frame_structure = generate_binary_structure(2, 1)# 2D continuity detector
    
    ## Neuropil mask filtering kernels generation 
    dilating_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * 19 + 1, 2 * 19 + 1))
    eroding_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * 10 + 1, 2 * 10 + 1))

    # MAIN LOOP
    for Files in range(len(filelist)): # Iterate through Neuropil channel images
        
        ## Create empty "Channels" dictionary to temporally store the results of the images capturing the same region.
        Channels = {}

        ## Double check the current image contains neuropil channel
        if (channels[0] in filelist[Files]):
            
            ### Create an empty dictionary "Channel" inside the main dictionary for the current channel
            Channels[0] = {}

            ### Read image
            Channels[0]["image"] = imread(os.path.join(PATH, filelist[Files]))
 
            ### Segment the image (keep values over 0)
            Channels[0]["image"] = Channels[0]["image"] > 0
 
            ### Identify the continuous objects in a 3D continuum 
            arr , ObjN = label(Channels[0]["image"], structure)
 
            ### Store the channel values obtained in the "Channel" dictionary
            Channels[0]["CC"] = arr # Image with labeled objects
            Channels[0]["objN"] = ObjN # Number of objects detected
            Channels[0]["name"]=filelist[Files] # File name
            
            ### Object detection per frame
            if len(Channels[0]["image"].shape) == 3: # Check if the image has more than 2 dimentions (is a stack)
                print(f"First {Channels[0]['name']}")

                #### Obtain the image dimension sizes
                z,x,y = Channels[0]["image"].shape

                #### Iterate through the frames
                for image_frame in range(z):
                    ##### Subset the frame from the image
                    frame = Channels[0]["image"][image_frame,:,:]
                    ##### Identify and quantify the objects of the frame with 2D connectivity
                    arr , ObjN = label(frame, frame_structure)
                    ##### Store the result to the "Channel" dictionary
                    Channels[0]["frame_" + str(image_frame) + "_ObjN"] =  ObjN

            ### Iterate throuh the other channels capturing the same ROI
            for iii in  range (1, len(channels)):
                
                #### Create an empty dictionary "Channel" inside the main dictionary for the current channel
                Channels[iii] = {}

                #### read the image of the same region for the new selected channel
                Channels[iii]["image"] = imread(os.path.join(PATH, filelist[Files].replace(channels[0], channels[iii])))

                #### Segment the image (keep values over 0)
                Channels[iii]["image"] = Channels[iii]["image"]>0
                
                #### Identify the continuous objects in a 3D continuum
                arr, ObjN = label(Channels[iii]["image"], structure)
                
                #### Store the channel values obtained in the "Channel" dictionary
                Channels[iii]["CC"] = arr # Image with labeled objects
                Channels[iii]["objN"] = ObjN # Number of objects detected
                Channels[iii]["name"]=filelist[Files].replace(channels[0], channels[iii]) # File name

                #### Iterate through frames
                if len(Channels[iii]["image"].shape) == 3: # Check if the image has more than 2 dimentions (is a stack)
                    print(f"Second {Channels[iii]['name']}")

                    ##### Obtain the image dimension sizes
                    z,x,y = Channels[iii]["image"].shape
                    
                    ##### Iterate through the frames
                    for image_frame in range(z):
                        ##### Subset the frame from the image
                        frame = Channels[iii]["image"][image_frame,:,:]
                        ##### Identify and quantify the objects of the frame with 2D connectivity
                        arr , ObjN = label(frame , frame_structure)
                        ##### Store the result to the "Channel" dictionary
                        Channels[iii]["frame_" + str(image_frame) + "_ObjN"] =  ObjN

            ### Iterate through the channels given by the user
            for iii in range(len(channels)):
                
                #### Obtain the channel Image shape
                p,m,n = np.asarray(Channels[iii]["image"]).shape
                
                #### Calculate the total volume of pixels in the image
                Channels[iii]["areatotal"] = m*n*p
                
                #### Calculate the pixel surface of each frame
                Channels[iii]["layer_surface"] = m*n

                #### Check if the channel is the neuritic channel defined by the user
                if (neuropil_channel in Channels[iii]["name"]):

                    ##### Generate a z-projection from the image stack keeping the maximum value of each pizel across the diferent frames
                    zproj = np.max(Channels[iii]["image"], axis = 0)
                    
                    ##### Normalize the projection values 
                    zproj = zproj * (255/np.max(zproj))
                    
                    ##### Dilation filter  
                    zproj_dil = cv2.dilate(zproj, dilating_kernel)
                    
                    ##### Eroding filter
                    neuropilmask = cv2.erode(zproj_dil, eroding_kernel)
                    
                    ##### Segmentation of the mask (keep values above 0)
                    neuropilmask = neuropilmask >0
                    
                    ##### calculate the neuropil area substracting the calculated neuropil mask (per frame) from the total area.
                    areaneuropil = Channels[iii]["areatotal"] - (np.sum(neuropilmask>0)*p)
                    
                    ##### Store the neuropil channel values obtained 
                    Channels[iii]["areaneuropil"] = areaneuropil
                    seq_name = Channels[iii]["name"]
                    outputFileName = os.path.join(PATH,'Density_Results', 'Neuropilmask',str(seq_name)+'_neuropilMask.tif')
                    
                    ##### Save masks if needed 
                    if save_masks:
                        imwrite(outputFileName, neuropilmask)
                    neuropilarea = Channels[iii]["areaneuropil"]
                
                #### If it's not the neuropil channel
                else:
                    Channels[iii]["areaneuropil"] = 0

            ### Iterate through channels
            for iii in range(len(channels)):
                
                #### Neuropil area density
                density_neuropil_area = ((Channels[iii]["objN"]/neuropilarea)/(Area_ratio))*10**9 
                Channels[iii]["density_area_neuropil"] = density_neuropil_area

                ####  Total area density
                density_total_area = ((Channels[iii]["objN"]/Channels[iii]["areatotal"])/(Area_ratio))*10**9
                Channels[iii]["density_total_area"] = density_total_area

                ####  Frame density calculations
                A = sorted([key for key in Channels[iii].keys() if "frame_" in key])
                for frame in A:
                    Channels[iii]["density_" + frame.replace("_ObjN","")] = ((Channels[iii][frame]/Channels[iii]["layer_surface"])/(Surface_ratio))*10**6


            ### Append calculations to results dataframe
            NewRow  = pd.DataFrame.from_dict(Channels, orient='index')
            Results = pd.concat([Results, NewRow])

    # Set the index of each row correctly.
    Results.reset_index(drop=True, inplace=True)
    
    # Remove the image storing columns 
    columns_to_remove = ["image", "CC"]
    Results.drop(columns=columns_to_remove, inplace=True)

    # create a list of the columns containing frame information.
    frame_columns = [col for col in Results.columns if col.startswith('frame')]

    # Create a list of columns containing "density"
    density_columns = [col for col in Results.columns if 'density' in col]

    # Define the desired order of columns
    desired_order = [
        "name", 
        "areatotal", 
        "areaneuropil",
        "objN",
        "density_total_area",
        "density_area_neuropil",
        "layer_surface"      
    ]

    # Create a list containing only the desired columns
    density_columns = [col for col in density_columns if col not in desired_order]

    # Concatenate frame and density columns
    combined_columns = desired_order + frame_columns + density_columns

    #Generate a subset of the Results dataframe keeping only the selected columns
    Results = Results[combined_columns]

    # Save the final Results table to a tsv file.
    outputfilename = "Results_density_" + str(current_time) + ".tsv"
    Results.to_csv(os.path.join(PATH, outputfilename.replace(":", "_")) , sep='\t', index = False)
    print("Process complete.")

##########################################################################################
# ARGUMENT PARSER

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Perform density calculations on image files.')

    # Add arguments
    parser.add_argument('PATH', 
                        type=str, 
                        help='The path to the directory containing image files.')
    parser.add_argument('-tech',
                        '--PROJECT_TECHNIQUE', 
                        type=str, 
                        default='STORM', 
                        help='The project technique (default: "STORM").')
    parser.add_argument('-nc',
                        '--neuropil_channel', 
                        type=str, 
                        default='SYPH', 
                        help='The neuropil channel identifier (default: "SYPH").')
    parser.add_argument('-xy',
                        '--x_y_ratio', 
                        type=float, 
                        default=None, 
                        help='The pixel size ratio for X and Y dimensions (default: None).')
    parser.add_argument("-z",
                        '--z_ratio', 
                        type=float, 
                        default=None, 
                        help='The pixel size ratio for the Z dimension (default: None).')
    parser.add_argument("-c",
                        '--channels',
                        type=str,
                        nargs='+',
                        default=["SYPH", "PSD95"],
                        help='List of channels to process (default: SYPH and PSD95).')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call your main function with the parsed arguments
    Densiometer(args.PATH, 
                args.PROJECT_TECHNIQUE, 
                args.neuropil_channel,
                args.channels,  # Pass the channels argument
                args.x_y_ratio, 
                args.z_ratio)

# Execute the main function when the script is run
if __name__ == '__main__':
    main()