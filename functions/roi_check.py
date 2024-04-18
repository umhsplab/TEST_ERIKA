import numpy as np
import matplotlib.pyplot as plt

def roi_check(image:np.ndarray,
              template:np.ndarray,
              layer:int,
              X:int,
              Y:int,
              H:int,
              W:int) -> None:
    """
    Display a frame, its corresponding ROI, and the template side by side.

    Parameters:
        image(np.ndarray): The image to be displayed.
        template(np.ndarray): The template image to be displayed.
	layer(int): The frame to be displayed
	X (int): Minimum X coordinate of the ROI
	Y (int): Minimum Y coordinate of the ROI
	H (int): Height of the ROI
	W (int): Weight of the ROI
	
    Returns:
        None
    """

    temp = template.copy()
    temp[layer-1, Y:Y+H, X:X+W] = 255
    fig, axs = plt.subplots(1, 3, figsize=(20, 10))

    axs[0].imshow(image[layer-1], cmap="gray")
    axs[0].set_title('Frame')
    
    axs[1].imshow(image[layer-1, Y:Y+H, X:X+W], cmap="gray")
    axs[1].set_title('ROI')
    
    axs[2].imshow(temp[layer-1], cmap="gray")
    axs[2].set_title('Template')
    
    plt.tight_layout()
    plt.show()
    plt.close()
    return
