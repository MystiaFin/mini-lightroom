import numpy as np
from PIL import Image, ImageEnhance
import cv2

def apply_adjustments(image, cfg):
    """
    Applies all variables from the config file to the image.
    """
    if cfg.SATURATION != 1.0:
        converter = ImageEnhance.Color(image)
        image = converter.enhance(cfg.SATURATION)

    arr = np.array(image, dtype=np.float32)

    # 2. Apply RGB Channel Balance (Redness, Greenness, Blueness)
    arr[:, :, 0] = arr[:, :, 0] * cfg.REDNESS
    arr[:, :, 1] = arr[:, :, 1] * cfg.GREENNESS
    arr[:, :, 2] = arr[:, :, 2] * cfg.BLUENESS

    # 3. Apply White (Exposure)
    arr = arr * cfg.WHITE

    # 4. Apply Blacks (Subtractive clipping)
    arr = arr - cfg.BLACK

    # 5. Apply Shadows (Lifting dark areas)
    if cfg.SHADOW > 0:
        # Calculate luminance
        # Standard formula: 0.299R + 0.587G + 0.114B
        luminance = (arr[:, :, 0] * 0.299) + (arr[:, :, 1] * 0.587) + (arr[:, :, 2] * 0.114)
        
        # Create a mask: 1.0 for dark pixels, 0.0 for bright pixels
        # Normalize luminance to 0-1 range
        norm_lum = np.clip(luminance / 255.0, 0, 1)
        shadow_mask = 1.0 - norm_lum # Invert: Darks become high numbers
        
        # Add brightness only where the shadow mask is strong
        # Reshape mask to match (H, W, 1) so we can add to RGB
        shadow_boost = cfg.SHADOW * 50 # Intensity multiplier
        arr += shadow_mask[:, :, np.newaxis] * shadow_boost

    # 6. Apply Hue (Requires Color Space conversion)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    processed_img = Image.fromarray(arr)

    if cfg.HUE != 0:
        processed_img = apply_hue(processed_img, cfg.HUE)

    return processed_img

def apply_hue(img, hue_amount):
    """
    Rotates the hue. 
    """
    img_hsv = img.convert("HSV")
    h, s, v = img_hsv.split()
    np_h = np.array(h, dtype=np.int16)

    # Add hue shift
    np_h = (np_h + hue_amount) % 255

    h_new = Image.fromarray(np_h.astype(np.uint8), "L")
    img_hsv = Image.merge("HSV", (h_new, s, v))
    return img_hsv.convert("RGB")
