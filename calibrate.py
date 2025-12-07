import numpy as np
from scipy.optimize import minimize
import color_checker
import processor

class CalibrationConfig:
    """Stores the calculated optimal configuration values"""
    def __init__(self):
        self.HUE = 0
        self.SATURATION = 1.0
        self.REDNESS = 1.0
        self.GREENNESS = 1.0
        self.BLUENESS = 1.0
        self.WHITE = 1.0
        self.BLACK = 0
        self.SHADOW = 0.0
        self.SHOW_COMPARISON = True


def calculate_color_error(extracted_colors, reference_colors):
    """
    Calculate the total color error (Delta E) between extracted and reference colors.
    Uses simple Euclidean distance in RGB space.
    
    Args:
        extracted_colors: (4, 6, 3) array of extracted RGB values
        reference_colors: (4, 6, 3) array of reference RGB values
    
    Returns:
        float: Total color error
    """
    # Flatten arrays
    extracted_flat = extracted_colors.reshape(-1, 3).astype(np.float32)
    reference_flat = reference_colors.reshape(-1, 3).astype(np.float32)
    
    # Calculate Euclidean distance for each patch
    differences = extracted_flat - reference_flat
    distances = np.sqrt(np.sum(differences ** 2, axis=1))
    
    # Return total error
    return np.sum(distances)


def apply_test_correction(extracted_colors, params):
    """
    Apply correction parameters to extracted colors to simulate the correction.
    This mimics what processor.py does.
    
    Args:
        extracted_colors: (4, 6, 3) array
        params: dict with keys: HUE, SATURATION, REDNESS, etc.
    
    Returns:
        np.ndarray: Corrected colors
    """
    from PIL import Image, ImageEnhance
    
    # Flatten to process all patches at once
    flat_colors = extracted_colors.reshape(-1, 3)
    
    corrected = []
    
    for color in flat_colors:
        # Create a tiny 1x1 image for this color
        img = Image.new('RGB', (1, 1), tuple(color.astype(int)))
        
        # Apply saturation
        if params['SATURATION'] != 1.0:
            converter = ImageEnhance.Color(img)
            img = converter.enhance(params['SATURATION'])
        
        # Convert to array for channel operations
        arr = np.array(img, dtype=np.float32).reshape(3)
        
        # Apply RGB channel balance
        arr[0] = arr[0] * params['REDNESS']
        arr[1] = arr[1] * params['GREENNESS']
        arr[2] = arr[2] * params['BLUENESS']
        
        # Apply white (exposure)
        arr = arr * params['WHITE']
        
        # Apply blacks
        arr = arr - params['BLACK']
        
        # Apply shadows (simplified - just add to dark pixels)
        if params['SHADOW'] > 0:
            luminance = (arr[0] * 0.299) + (arr[1] * 0.587) + (arr[2] * 0.114)
            norm_lum = np.clip(luminance / 255.0, 0, 1)
            shadow_mask = 1.0 - norm_lum
            shadow_boost = params['SHADOW'] * 50
            arr += shadow_mask * shadow_boost
        
        # Clip and store
        arr = np.clip(arr, 0, 255)
        corrected.append(arr)
    
    return np.array(corrected).reshape(4, 6, 3)


def optimize_parameters(extracted_colors, reference_colors):
    """
    Find optimal correction parameters using optimization.
    
    Args:
        extracted_colors: (4, 6, 3) array of extracted colors
        reference_colors: (4, 6, 3) array of reference colors
    
    Returns:
        CalibrationConfig: Optimized configuration
    """
    print("Optimizing correction parameters...")
    
    # Initial guess (neutral values)
    # Parameter order: [SATURATION, REDNESS, GREENNESS, BLUENESS, WHITE, BLACK, SHADOW]
    initial_params = [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0]
    
    # Bounds for parameters
    bounds = [
        (0.5, 2.0),   # SATURATION
        (0.7, 1.5),   # REDNESS
        (0.7, 1.5),   # GREENNESS
        (0.7, 1.5),   # BLUENESS
        (0.7, 1.5),   # WHITE
        (0, 30),      # BLACK
        (0.0, 0.5),   # SHADOW
    ]
    
    # Objective function to minimize
    def objective(params):
        param_dict = {
            'HUE': 0,  # Skip hue optimization
            'SATURATION': params[0],
            'REDNESS': params[1],
            'GREENNESS': params[2],
            'BLUENESS': params[3],
            'WHITE': params[4],
            'BLACK': params[5],
            'SHADOW': params[6],
        }
        
        # Apply correction
        corrected = apply_test_correction(extracted_colors, param_dict)
        
        # Calculate error
        error = calculate_color_error(corrected, reference_colors)
        
        return error
    
    # Run optimization
    result = minimize(
        objective,
        initial_params,
        method='L-BFGS-B',
        bounds=bounds,
        options={'maxiter': 100, 'disp': False}
    )
    
    # Create config with optimized values
    config = CalibrationConfig()
    config.HUE = 0  # Not optimized
    config.SATURATION = round(result.x[0], 2)
    config.REDNESS = round(result.x[1], 2)
    config.GREENNESS = round(result.x[2], 2)
    config.BLUENESS = round(result.x[3], 2)
    config.WHITE = round(result.x[4], 2)
    config.BLACK = round(int(result.x[5]))
    config.SHADOW = round(result.x[6], 2)
    
    print("✓ Optimization complete!")
    print(f"  Final error: {result.fun:.2f}")
    
    return config


def simple_white_balance_correction(extracted_colors, reference_colors):
    print("Calculating white balance correction...")
    
    # Use the grayscale row (row 3, bottom row)
    gray_extracted = extracted_colors[3, :, :].astype(np.float32)
    gray_reference = reference_colors[3, :, :].astype(np.float32)
    
    # Calculate average gray patch
    avg_extracted = gray_extracted.mean(axis=0)  # Average across patches
    avg_reference = gray_reference.mean(axis=0)
    
    # Calculate RGB multipliers (simple ratio)
    config = CalibrationConfig()
    
    # Avoid division by zero
    if avg_extracted[0] > 10:
        config.REDNESS = round(avg_reference[0] / avg_extracted[0], 2)
    if avg_extracted[1] > 10:
        config.GREENNESS = round(avg_reference[1] / avg_extracted[1], 2)
    if avg_extracted[2] > 10:
        config.BLUENESS = round(avg_reference[2] / avg_extracted[2], 2)
    
    # Clamp to reasonable ranges
    config.REDNESS = np.clip(config.REDNESS, 0.7, 1.5)
    config.GREENNESS = np.clip(config.GREENNESS, 0.7, 1.5)
    config.BLUENESS = np.clip(config.BLUENESS, 0.7, 1.5)
    
    # Calculate overall brightness adjustment
    extracted_brightness = avg_extracted.mean()
    reference_brightness = avg_reference.mean()
    
    if extracted_brightness > 10:
        config.WHITE = round(reference_brightness / extracted_brightness, 2)
        config.WHITE = np.clip(config.WHITE, 0.7, 1.5)
    
    # Adjust saturation based on color patches
    # Use the colorful patches (rows 0-2)
    color_extracted = extracted_colors[:3, :, :].reshape(-1, 3).astype(np.float32)
    color_reference = reference_colors[:3, :, :].reshape(-1, 3).astype(np.float32)
    
    # Calculate saturation as std dev of RGB
    sat_extracted = color_extracted.std()
    sat_reference = color_reference.std()
    
    if sat_extracted > 5:
        config.SATURATION = round(sat_reference / sat_extracted, 2)
        config.SATURATION = np.clip(config.SATURATION, 0.5, 2.0)
    
    print("✓ White balance correction calculated!")
    
    return config


def auto_calibrate(image_pil, method='simple', visualize=False):
    # Detect and extract colors
    extracted, reference = color_checker.detect_and_extract_colors(image_pil, visualize)
    
    if extracted is None:
        return None
    
    # Calculate optimal parameters
    if method == 'optimize':
        config = optimize_parameters(extracted, reference)
    else:  # 'simple'
        config = simple_white_balance_correction(extracted, reference)
    
    # Display results
    print("\n--- Calculated Correction Parameters ---")
    print(f"HUE = {config.HUE}")
    print(f"SATURATION = {config.SATURATION}")
    print(f"REDNESS = {config.REDNESS}")
    print(f"GREENNESS = {config.GREENNESS}")
    print(f"BLUENESS = {config.BLUENESS}")
    print(f"WHITE = {config.WHITE}")
    print(f"BLACK = {config.BLACK}")
    print(f"SHADOW = {config.SHADOW}")
    print("----------------------------------------\n")
    
    return config


def save_config_to_file(config, filename='config_auto.py'):
    """
    Save the calibrated config to a Python file.
    
    Args:
        config: CalibrationConfig object
        filename: Output filename
    """
    with open(filename, 'w') as f:
        f.write("# Auto-generated configuration from color calibration\n\n")
        f.write(f"SHOW_COMPARISON = {config.SHOW_COMPARISON}\n\n")
        f.write("# --- COLOR ---\n")
        f.write(f"HUE = {config.HUE}\n")
        f.write(f"SATURATION = {config.SATURATION}\n\n")
        f.write("# --- CHANNEL MIXER ---\n")
        f.write(f"REDNESS = {config.REDNESS}\n")
        f.write(f"GREENNESS = {config.GREENNESS}\n")
        f.write(f"BLUENESS = {config.BLUENESS}\n\n")
        f.write("# --- TONE ---\n")
        f.write(f"WHITE = {config.WHITE}\n")
        f.write(f"BLACK = {config.BLACK}\n")
        f.write(f"SHADOW = {config.SHADOW}\n")
    
    print(f"✓ Configuration saved to {filename}")
