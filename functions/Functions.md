# FUNCTIONS SUMMARY

## Introduction

This repository contains the scripts used to perorm Segmentation, Density and Distnce analysis of proteins in STORM images.

## apply_threshold_and_binarize
Given an image and a percentage, this function applies thresholding , selecting the data with values over the percentage of the maximum intenity of the image, and binarization.

### Inputs
-   image_frame: A 2D image.
-   th_percentage: the percentage of the maximum intensity of the image used to segment it. 

### Returns
-   The segmented image.

## calculate_per_dist
Calculate the minimum Euclidean distance between two sets of points and the average distance of the N nearest elements between the objects.

### Inputs:
- POS_A: List of tupples containing the x and y coordinates for each pixel in object 1.
- POS_B: List of tupples containing the x and y coordinates for each pixel in object 2.
- elements: Elements to take into account for the average minimum distance.

### Returns:
- output: A list containing:
    - The minimum distance between the objects.
    - The pixel from the object 1 that's nearest to the object 2.
    - The pixel from the object 2 that's nearest to the object 1.
    - The minimum average distance among the N nearest elements.

## check_continuity
Given a list count if there are 2 or more consecutive elements containing 1 or true.

### Inputs:
- column : A list of values

### Returns:
- Number of consecutive objects found.

## cmyk_to_rgb
Convert CMYK color values to RGB color values.

### Inputs:
- c : A 2D image containing the cyan color of the image
- m : A 2D image containing the magenta color of the image
- y : A 2D image containing the yellow color of the image
- k : A 2D image containing the black color of the image
- cmyk_scale: The Maximum possible value in the range of the cmyk images

### Returns:
- A RGB 3D image.

## combine_and_draw
Combine two images and draw a colored line between two points using Bresenham's line algorithm.

### Inputs:
- image: Input image
- point1: position of the extreme of the line
- point2: position of the other extreme of the line
- color: tupple indicating the RGB color values.

### Returns:
- The image with the 2 points and a line connecting them.

## combine_and_draw2
Combine two images and draw a line between two specified points.

### Inputs:
- image1: Image containing the object 1
- image2: Image containing the object 2
- point1: Tupple containing the coordinates of the first point
- point2: Tupple containing the coordinates of the second point
- yellow_center: Boolean indicating wheather the objects centers should be yellow or not

### Returns:
- The combined images with a line drown between the 2 indicated points.

## combine_plots
Combine grayscale images and plot them in a 1x3 grid.

### Inputs:
A: Grayscale image of object 1 to combine in the image displayed on the left.
B: Grayscale image of object 2 to combine in the image displayed on the left.
image2: Image to be displayed on the center
image3: Image to be displayed on the right
COM_dis: Center of mass distance (to display)
PER_dis: Perimeter minimum distance (to display)
Path: Directory where to store the resulting composition of images.

### Returns:
None

## extract_common_part
Extracts the common part of a filename up to the first underscore.

### Inputs:
- filename: Name of the file where to extract the common part with the ROI identification

### Returns:
The ROI identifiicator part of the filename

## extract_common_part2
This function takes a filename and a list of unique texts and attempts to extract the common part of the filename that precedes any of the unique texts enclosed in parentheses.

### Inputs:
- filename: Name of the file where to extract the common part
- unique_texts: Options of text enclosed in parenthesis on the filenames

### Returns:
The common part of the filename preceding any of the unique texts.

## extract_unique_texts_between_parentheses
Extract unique texts found between parentheses in a list of strings.

### Inputs:
- strings_list: A list of strings.

### Returns:
A list of the unique texts found between parenthesis in the given strings.

## extract_unique_texts_between_underscores
Extracts unique texts found between underscores in a list of strings.

### Inputs:
- strings_list: A list of strings.
### Returns:
A list of unique texts found between underscores.

## group_files_by_common_part
Groups filenames by their common parts and sorts the groups based on neuropil_channel presence.

### Inputs:
- file_list: A list of filenames to be grouped.
- unique_texts: A list of unique texts found between underscores.
- neuropil_channel: Neuropil channel identifyer.

### Returns:
A list of grouped filenames, sorted based on neuropil_channel.

## group_files_by_common_part2
Group a list of filenames by their common parts based on unique texts.

### Inputs:
- file_list: A list of filenames to be grouped.
- unique_texts: A list of unique texts enclosed in parentheses.

### Returns:
A list of lists where each inner list contains filenames that share the same common part.

## initialize_alignment
Initialize the alignment process with image data and optional presets.

### Inputs:
- PATH: The path to the directory containing image files.
- Filenames: A list of filenames for the images to be aligned.
- Preset_file: Optionally, the name of the presets file (CSV format).
- save_template: Indicate to save the alignment template image.

### Returns:
A list containing the following elements:
- image: The first image loaded from Filenames.
- image2: The second image loaded from Filenames.
- Template: A blank image for alignment.
- final_img: A copy of the first image for aligned results.
- final_img2: A copy of the second image for aligned results.
- SelectedROIs: An empty DataFrame to store ROI information.

## modify_filename
Modify a filename to make it unique if it already exists in a specified directory.

### Inputs:
- PATH: Directory where the file should be saved.
- filename: Original filename.

### Returns:
The New modifyed filename.

## object_identificator
Identify and analyze objects in a preprocessed image frame.

### Inputs:
- closing: The preprocessed image frame.
- frame: The frame index associated with the image.
- min_area: The minimum area for an object to be considered.

### Returns:
A tuple containing:
- The labeled image of identified objects.
- A DataFrame the properties of the objects with bigger area than the minimum stablished.

## preprocess_image
Preprocesses a single frame of an image for further analysis.

### Inputs:
- image: The input image data.
- frame: The frame index to process.
- th_percentage: The threshold percentage for binarization.
- kernel_3x3: The 3x3 kernel for morphological operations.

### Returns:
The preprocessed image frame after thresholding, opening, and closing operations.

## roi_check
Display a frame, its corresponding ROI, and the template side by side.

### Inputs:
image: The image to be displayed.
template: The template image to be displayed.
layer: The frame to be displayed
X: Minimum X coordinate of the ROI
Y: Minimum Y coordinate of the ROI
H: Height of the ROI
W: Weight of the ROI
### Returns:
It Does not return nothing. It displays the ROI visulaization.

## ROI_MAP
Generate a map of regions of interest (ROIs) in image frames.

### Inputs:
- image: The first input image data.
- image2: The second input image data.
- df: DataFrame containing ROI data.
- mask: The mask data for visual analysis.
- filename: The name of the output file.
- PATH: The path to the directory where the output file will be saved.
- th_percentage: The threshold percentage for binarization.

### Returns:
The Generated map is saved as .tif file

## save_results
Save various results including CSV files, aligned images, and visualizations.

### Inputs:
- PATH: The path to the directory for saving results.
- Filenames: A list of filenames.
- SelectedROIs: A DataFrame containing ROI information.
- Template: The template image.
- image: The first image.
- image2: The second image.
- final_img: The final aligned image for the first image.
- final_img2: The final aligned image for the second image.
- save_template: Whether to save the template image.
- name: The name for the CSV file.

### Returns:
Save the generated images as .tif on the specifyed directory.

## spiderwebs
Generate spiderweb-like visualizations from image data.

### Inputs:
- image: The first input image data.
- image2: The second input image data.
- df: DataFrame containing object data.
- mask: The mask data for visual analysis.
- filename: The name of the output file.
- PATH: The path to the directory where the output file will be saved.
- th_percentage: The threshold percentage for binarization.

### Returns:
Save the generated images as .tif on the specifyed directory.

## update_template
Update a template image with a selected ROI and store ROI information in a DataFrame.

### Inputs:
- Template: The template image to be updated.
- SelectedROIs: A DataFrame to store ROI information.
- image: The image containing the ROI.
- layer: The layer (frame) in the template to update.
- X: X-coordinate of the top-left corner of the ROI.
- Y: Y-coordinate of the top-left corner of the ROI.
- W: Width of the ROI.
- H: Height of the ROI.
- Comment: Comments or notes about the ROI.

### Returns:
A list containing:
- Updated template image.
- A DataFrame with ROI information.


## wrapper_function
Creates a log file containing the call of the function executed with the given parameters.
