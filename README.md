# SYN DENSITIES

## Introduction

This repository contains the scripts used to perform Segmentation, Density and Distnce analysis of proteins in STORM images.


The script were used on the analisis of ____________________________________________ that can be found on ________________.


# Use

To use the package all the files should be downloaded and kept in the folder structure it has.

The functions can be executed through command line, it's recommended to use Anaconda's prompt.    

## SYN_SEGMENTATOR

The image segmentation process begins by creating a new directory to store the segmented data and then identifies all TIFF image files within the specified source directory. The script iterates through each image, loading it and checking if it's a binary image (only containing 0s and 1s). If so, it skips processing that image as it likely isn't a microscopy image.

For valid microscopy images, several pre-processing steps are applied. First, the intensity values are converted to floating-point numbers between 0 and 1. Then, a local mean filter is employed to calculate the average intensity within a user-defined window around each pixel. This local mean is subtracted from the original value, highlighting object boundaries.

A threshold is then calculated based on the local mean and a factor provided by the user. This threshold is used to create a binary image by comparing each pixel's intensity in the pre-processed image. Pixels exceeding the threshold are assigned 1 (foreground/object), while those below are assigned 0 (background). The binary image is inverted, so objects appear white on a black background.

An empty 3D array is created to store the segmented objects. The script iterates through each image slice (representing different depths) and uses a function to identify and label connected objects in the binary image. This assigns a unique label to each group of foreground pixels, separating objects.

The script then iterates through each labeled object and compares its size (total number of pixels) to a minimum size threshold. If an object meets this criteria, the coordinates of all its constituent voxels (3D pixels) are added to the 3D array, accumulating the identified objects across all slices and building a 3D representation.

A new 3D image is created with the same dimensions as the original but with intensity values corresponding to object membership. The script iterates through each voxel in this new image. If the corresponding voxel's coordinates are present in the 3D array (indicating it belongs to a segmented object), the original image intensity value from that location is copied. Otherwise, the intensity value in the new image is set to 0. This effectively segments the objects based on the selection criteria.

Two separate TIFF images are then saved: the segmented image containing the isolated objects and a mask image where objects are represented by white pixels on a black background. Finally, the script creates a text file storing the values of all function arguments used for future reference.  


### INPUTS

- -path : Path to the directory containing input images
- --window_size (-ws) : Window size for local mean or median filter
- --r_factor (-r) : Factor for calculating the threshold in the filter
- --method (-method) : Method for filtering
- --minimum_surface (-min_surf) : Minimum 2D surface of an object
- --minimum_size (-min_size) : Minimum 3D pixel volume of an object
- --maximum_size (-max_size) : Maximum 3D pixel volume of an object
- --threshold_2d (-th_2d) : Minimum intensity fraction for segmentation in 2 Dimensions
- --threshold_3d (-th_3d) : Minimum intensity fraction for segmentation in 3 Dimensions

### OUTPUTS

Identified objects:

'XXXX_join2D.tif' : Image segmented, based on the threshold_2d and the minimum surface, per frame.

'XXXX_join3D_segmented.tif' XXXX_join2D image stack filtered to keep only objects present in consecutive frames.

'XXXX_join3D_mask.tif' Merge of the original image and the XXXX_join3D_segmented image to obtain an image with the original intensity values on the selection of pixels from the segmented image.

Filtered objects:

'XXXX_join2D2.tif' : Segmentation of XXXX_join3D_mask based on the threshold_3d, per frame. 

'XXXX_join3D2_segmented.tif' : filtering of XXXX_join2D2 based on the number of frames, and minimum and maximum object size. 

'XXXX_join3D2_mask.tif' : Merge of the original image and the XXXX_join3D2 segmented image to obtain an image with the original intensity values on the selection of pixels from the segmented image.

### Example

`python SYN_SEGMENTATOR.py /path/to/files -ws 150 -r 1.5 -method mean -min_surf 64 -min_size 150 -max_size 9999 -th_2d 0 -th_3d 0.2`

## SYN_DENSITY

The SYN_DENSITY script serves as the core component for calculating object density within images, particularly applicable in neuroscience for analyzing synaptic density via microscopy images. It employs a series of image processing techniques to accurately identify and quantify objects of interest within the images.

The "Densiometer" function in the script is defined to encapsulate the density calculation process. It accepts various input parameters such as the directory path containing the image files, the project technique, the neuropil channel identifier, pixel size ratios, and the channels to process.

The function iterates through each image file containing the neuropil channel in the specified directory, performing the following process for it and each channel specified. The image is loaded using CV2 and segmented selecting all the signal above 0 to detect the objects per frame using scipy.

For the neuropil channel a z projection of the stack of images is calculated selecting the maximum pixel value of each pixel across the z axis. The image is then dilated and eroded using CV2 with a eliptic kernel of 39 x 39 and 21 x 21 pixels resectivly. The resulting image is segmented keeping the signal avobe 0 and the area with signal is obtained, multiplyed by the number of frames and substracted from the total pixel volume of the satck. The neuropil area image is saved as Neuropilmask.tif using CV2.

Finally , for each channel the density of objects per neuropil area is calculated and transformed to um using the user specifyed x-y and z ratios. The same calculation is performed to calculate also the density per total area. 

The results from each iteration, total area, neuropil area, object number, total density, neuropil density and surface area, are compiled into a pandas DataFrame(REF. PANDAS) for ease of manipulation. Columns are then reordered for improved readability. Finally, the results are written to a TSV file for further analysis and visualization.


### INPUTS
- Path: path to the directory containing the image files to process.
    - The program expects the filenames of the images from the same region to keep the same filename only changing the channel. (Ex: 001_PSD95_segmentation.tif, 001_SYPH_segmentation.tif)
- --PROJECT_TECHNIQUE (-tech): Indicates the technique of image aquisition to load presets for the pixel size parameters.
- --NEUROPIL_CHANNEL (-nc) : Channel name indicating the protein used to calculate the neuropil area.
- --X_Y_RATIO (-xy): pixel size for x and y dimensions.
- --Z_RATIO (-z): pixel size for z dimension.
- --CHANNELS (-c): Project channel names.

### OUTPUTS

- Density_results_(date).csv 
    This file contains the results calculated on the script.
    Each row represents an image.
    The columns contain:
    - areatotal : Total volume of pixels on the image.
    - areaneuropil : The area where the proteins can be detected (outside nucleus).
    - ObjN : Total number of identifyed objects (accounting for connectivity on the 3 dimensions).
    - density_total_area : density of objects per um in the total image pixel volume.
    - density_area_neuropil : density of objects per um the area neuropil volume of pixels calculated.
    - layer_surface: surface of pixels on a frame of the image.
    - frame_(X)_ObjN : Number of objects identifyed on the frame X.
    - density_frame_(X) : Density of objects on a frame per surface of the frame.

### Example

`python SYN_DENSITY.py /path/to/files -tech STORM -nc SYPH -c SYPH PSD95 -xy 0.008 -z 0.07`


## SYN_DENSITY_per_channel

The method described herein details the process of performing density calculations on image files utilizing Python programming language libraries. The primary functionalities involve image processing, object identification, and data analysis.

The function  accepts several parameters including the directory path containing image files, project technique, neuropil channel identifier, connectivity for object identification, intensity threshold for object identification, and pixel size ratios. This function iterates through each image file in the specified directory, performing the following procedure.

The function begins by checking whether the user has provided custom values for the pixel size ratios. If not, default values are assigned based on the specified project technique. For instance, if the project technique is "STORM," the pixel size ratios are set to 0.008 for X and Y dimensions and 0.07 for the Z dimension. 

The code obtains a list of the image files within the specified directory, and then these filenames are stored in a list. A loop iterates through each image file in the list performing the following operations.

The image is read using the `tifffile` library (REF. TIFFFILE) and is then converted to a float32 format, ensuring consistency in data type for subsequent processing steps. The image pixel volume is calculated and stored.

For each frame of the image, utilizing the morphological operations from the OpenCV library (`cv2`), the algorithm performs a closing filtering to remove noise using a 3x3 pixels kernel generated with CV2. The frame is then segmented using the ratio of the maximum intensity established by the user, and using scipy, it identifies the objects within the frame. The total objects detected is calculated by adding the identified objects on each frame using numpy( REF. NUMPY).

Depending on the requirements, the complete segmented image stack is processed as a whole using scipy and a kernel determined by the connectivity established by the user, detecting the objects in contact on the same layer or on the volume of the stack generated with the same package.

Once all the images are processed, the density for each of them is calculated using the objects identified on the whole image with the connectivity specified and the total pixel volume, and the result is transformed to objects per um using the given ratios for x-y and z dimensions.

The results are finally stored in a CSV file for further processing and analysis.

### INPUTS

- PATH : The path to the directory containing image files.
    - The program expects the filenames to have the channel indicated between the first and second underscores. (001_PSD95_segmentation.tif, 001_SYPH_segmentation.tif)
- --PROJECT_TECHNIQUE (-tech) : The project imaging technique used to set predefined parameters of size ratio.
- --NEUROPIL_CHANNEL (-nc) : The neuropil channel identifier.
- --CONNECTIVITY (con) : The dimensions of connectivity for object identification.
- --THRESHOLD (-th): The threshold percentage of the maximum intensiti value for object segmentation.
- --X_Y_RATIO (-xy): The pixel size ratio for X and Y dimensions 
- --Z_RATIO (-z): The pixel size ratio for the Z dimension 

### OUTPUTS

- Results_density_(date).tsv
    This file contains the results calculated on the script.
    Each row represents an image.
    The columns contain:
    - frame_(X)_ObjN : Number of objects identifyed on the frame X.
    - density_frame_(X) : Density of objects on a frame per surface of the frame.
    - areatotal : Total volume of pixels on the image.
    - Obj_n : Total number of identifyed objects (accounting for connectivity on the 3 dimensions).
    - density : density of objects per um in the total image pixel volume.

### Example

`python SYN_DENSITY_per_channel_NEW.py /path/to/files -tech STORM -con 3 -th 0 -xy 0.008 -z 0.07`

## SYN_DETECTOR

The script begins by initializing necessary libraries and modules, such as OpenCV, NumPy, Pandas, and others. It also sets up some configurations and suppresses future warnings for better readability.

Following initialization, the script imports custom functions required for various tasks, such as preprocessing images, identifying objects, calculating distances, generating spiderweb visualizations, and creating ROI maps. These functions encapsulate specific functionalities and are essential for the overall image processing pipeline.

Next, the script parses command-line arguments provided by the user using the argparse module. These arguments specify parameters such as the input directory path, size ratio, maximum distance, minimum area, and other options for processing the images. Command-line argument parsing allows users to customize the behavior of the script based on their specific requirements.

Before proceeding with image processing, the script sets up the directory structure for storing the processed images, extracted ROIs, and other outputs. It creates necessary folders if they don't already exist, ensuring an organized storage of results.

The core of the script lies in the image processing stage. It iterates through each pair of images in the input directory, where each pair typically represents two channels of the same image. For each pair of images, the script performs a series of steps:

1.    Preprocessing: The images are preprocessed to enhance relevant features and remove noise. Preprocessing techniques may include filtering, thresholding, and morphological operations to prepare the images for object identification.

1.    Object Identification: Objects are identified in each image using segmentation techniques. These techniques partition the image into meaningful regions corresponding to individual objects. The script calculates properties of these objects, such as area, centroid, and bounding box, which are essential for further analysis.

1.    Object Interaction Detection: The script identifies interactions between objects by calculating distances between them. It determines whether objects are within a certain threshold distance, indicating potential interactions or spatial relationships.

1.    ROI Extraction: Regions of interest (ROIs) are extracted based on the detected interactions and other criteria such as area thresholds. These ROIs represent areas of interest within the images and are crucial for subsequent analysis and interpretation.

Once image processing is complete for all image pairs, the script generates various outputs based on the processing results. These outputs include filtered images with applied filters, extracted ROIs saved as separate image files, spiderweb visualizations illustrating interactions between objects, ROI maps overlaying the extracted ROIs onto the original images, and a CSV file containing detailed information about the detected objects, including their positions, areas, distances, and other relevant attributes.

In summary, the script automates the process of extracting and analyzing regions of interest from image data by performing preprocessing, object identification, interaction detection, and ROI extraction. It provides users with customizable options to tailor the analysis according to their specific requirements, ultimately facilitating the interpretation and understanding of complex image datasets.

### INPUTS
- PATH: The path to the directory containing image files.
        
- --x_y_ratio (-xy): um to pixel size ratio for image analysis.
        
- --max_distance (-md): Maximum distance for considering objects as close.
        
- --min_area (-ma): Minimum area of objects to be considered.
        
- --th_percentage (-th): Threshold percentage for image binarization.
        This parameter determines the threshold percentage used for image binarization. It affects the segmentation of objects from the background in the images.

- --neuropil_channel (-nc): Indicate the neuropil channel.
        This parameter specifies the neuropil channel used in the image processing pipeline. It's used for segmenting neuropil regions in the images.

- --saverois (-roi): Whether to save extracted ROIs.
        This parameter controls whether the extracted regions of interest (ROIs) are saved as separate image files. If set to True, the ROIs will be saved.

- --Spiderweb (-sw): Whether to generate spiderweb visualizations.
        This parameter determines whether spiderweb visualizations should be generated based on the detected interactions between objects.

- --RoiMap (-roim): Whether to generate ROI maps.
        This parameter controls whether ROI maps should be generated, showing the regions of interest overlaid on the original images.

### OUTPUTS
    
- Filtered Images: Processed images with applied filters.
        These images are the result of preprocessing and filtering steps (closing) applied to the original images.

- CSV File: CSV file containing detection results.
    The script generates a CSV file containing detailed information about the detected objects, including their positions, areas, distances, and other relevant attributes. This file can be further analyzed or used for data visualization purposes.
    - ImageName: Image filename identificator
    - Frame: Frame containing the object
    - com: Center of mass of the object 1
    - com2: Center of mass of the object 2
    - object_label: Object identifyer
    - object2_label: Object 2 identifyer 
    - Distance_com: Distance between the centers of mass of the 2 objects in pixels
    - Distance_um : Distance between the centers of mass of the 2 objects in um
    - object_roi: Coordinates of the captured roi for the object 1 (Xinitial, Yiinitial, Xfinal, Yfinal)
    - object2_roi: Coordinates of the captured roi for the object 2 (Xinitial, Yiinitial, Xfinal, Yfinal)
    - big_roi: Coordinates of the calculated big roi (Xinitial, Yiinitial, Xfinal, Yfinal)
    - Area: Object 1 area
    - Area2: Object 2 area
    - Object_nearest_point: Nearest pixel of the object 1 to the object 2
    - Object2_nearest_point: Nearest pixel of the object 2 to the object 1
    - Min_distance: Minimum distance between the objects in pixels (Perimeter distance)


- Extracted ROIs: Regions of interest (ROIs) extracted from the images.
        These ROIs represent the regions identified as relevant for further analysis.

- Spiderweb Visualizations: Visualizations showing interactions between objects.
        Spiderweb visualizations are generated to illustrate the interactions between detected objects. These visualization indicates the distance between centers of mass of the objects found on the images. It only accounts for those at less then the specifyed maximum distance.

- ROI Maps: Maps showing regions of interest overlaid on original images.
        The RoiMap overlays the extracted regions of interest onto the original images. These maps provide a visual representation of the detected ROIs in their original context.



### EXAMPLE

`python roi_extractor.py /path/to/files -xy 0.008 -md 0.3 -ma 10 -th 0.8 -roi -nc "SYPH" -sw -roim`

## SYN_DISTANCE

Perform a workflow to analyze and measure objects in a series of microscopy images.

This function reads a series of microscopy images from a specified directory, performs object
detection and measurement, and saves the results to a CSV file. It also provides the option
to save visualization plots.

### INPUTS
- PATH : path to the directory containing the image files to process.
- th_percent (-th): percentageof maximum intensity to segment the image.
- x_y_ratio (-xy): ratio of pixel to um 
- plot_save (-ps): Indicate to save or not the image intermediate files.

### OUTPUTS

- Distance_results_(date).csv
    This file contains the following information for each image frame:
    - Name : File name
    - Frame : Frame indicator
    - Centroid_(CH1_name) : Centroid coordinates for the first protein channel
    - Centroid_(CH2_name) : Centroid coordinates for the second protein channel
    - Perimeter_P_(CH1_name) : Perimeter point nearest to the other protein channel
    - Perimeter_P_(CH2_name) : Perimeter point nearest to the other protein channel
    - Area_(CH1_name) : Channel 1 image Area in pixels
    - Area_(CH2_name) : Channel 2 image Area in pixels
    - Area_um_(CH1_name) : Image area in um
    - Area_um_(CH2_name) : Image area in um
    - Center_Distance_px:
    - Perimeter_Distance_px :
    - Center_Distance_um :
    - Perimeter_Distance_um : 
    - Perimeter_Distance_um : 
    - Average_Distance_um: 

Images:
    Inside a new folder called VIZ the visualization of the distance per frame is stored as .tif files.

### Example

`python SYN_DISTANCE.py /path/to/files -th_percent 0.2 -xy 0.008 -ps`


# Requirements
OS: Windows 11

Python version : Python 3.10.10

Packages and versions used in requirements.txt

# WARNINGS

The scripts are prepared to accept windows paths and might rise errors due to paths if used from a linux computer. To solve it check the indications on the comments of the script.

The image files must be .tif format and have a filename with the following pattern:
- `ImageID_ProteinChannel_Metadata.tif`
This pattern will permit the functions to recognise correctly the information obtained from the filename.


# REFERENCES

1. McKinney, Ryan. "Data Structures for Statistical Computing in Python." Proceedings of the 9th Python in Science Conference (2010): 51-56. [https://pandas.pydata.org/](https://pandas.pydata.org/)
2. Pearu, Manoj et al. "tifffile: TIFF File I/O Library." (2010). [https://pypi.org/project/tifffile/](https://pypi.org/project/tifffile/)
3. Harris, CR et al. "Array programming with NumPy." Nature 520.7545 (2015): 315-322. [https://numpy.org/](https://numpy.org/)
4. Virtanen, Pauli et al. "SciPy 1.1--User Guide." (2020). [https://docs.scipy.org/doc/scipy/reference/ndimage.html](https://docs.scipy.org/doc/scipy/reference/ndimage.html) 
5. .MemoryUnitSantPau, SynSeg. [https://github.com/MemoryUnitSantPau/SynSeg/tree/master](https://github.com/MemoryUnitSantPau/SynSeg/tree/master)
6. Anaconda [https://www.anaconda.com/](https://www.anaconda.com/)

# Licenses

This code belongs to the Memory Unit of the Hospital de Sant Pau in Barcelona and Biomedical Research Institute Sant Pau (IIB Sant Pau), Barcelona, Spain.

For any question or bug report you can contact: jaumatelle@santpau.cat