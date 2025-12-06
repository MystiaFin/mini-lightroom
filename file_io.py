import os
from PIL import Image, ImageOps

def load_images(directory):
    valid_images = []
    
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}. Please put images inside.")
        return []
    
    print(f"Reading images from {directory}...")
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
        
        try:
            img = Image.open(filepath)
            
            img = ImageOps.exif_transpose(img)
            
            img = img.convert("RGB") 
            valid_images.append((filename, img))
            print(f"Loaded: {filename}")
        except IOError:
            print(f"Skipped (not an image): {filename}")
    
    return valid_images

def save_image(image_obj, original_filename, output_dir):
    """
    Saves the processed image to the result directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    save_name = f"edited_{original_filename}"
    save_path = os.path.join(output_dir, save_name)
    
    image_obj.save(save_path)
    print(f"Saved: {save_path}")
