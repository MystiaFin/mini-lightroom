import matplotlib.pyplot as plt
import numpy as np

def show_comparison(original_img, processed_img, filename):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
    # Title
    fig.suptitle(f"Comparison: {filename}", fontsize=16)

    # Left: Original
    axes[0].imshow(original_img)
    axes[0].set_title("Original")
    axes[0].axis('off')

    # Right: Processed
    axes[1].imshow(processed_img)
    axes[1].set_title("Processed")
    axes[1].axis('off')

    plt.tight_layout()
    plt.show()
