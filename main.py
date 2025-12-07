import config
import file_io
import processor
import visualizer
import calibrate
import time
import sys

def main():
    print("--- Mini Python Lightroom with Auto-Calibration ---")
    
    # Check if user wants auto-calibration
    print("\nModes:")
    print("1. AUTO-CALIBRATE: Detect ColorChecker and auto-calculate corrections")
    print("2. MANUAL: Use config.py values (traditional mode)")
    
    mode = input("\nSelect mode (1 or 2) [default: 1]: ").strip()
    
    if mode == '' or mode == '1':
        mode = 'auto'
    elif mode == '2':
        mode = 'manual'
    else:
        print("Invalid mode. Using AUTO-CALIBRATE.")
        mode = 'auto'
    
    # Load images
    images_list = file_io.load_images("images")
    
    if not images_list:
        print("No images found in 'images/'. Exiting.")
        return
    
    print(f"Found {len(images_list)} images.")
    
    # AUTO-CALIBRATE MODE
    if mode == 'auto':
        print("\n=== AUTO-CALIBRATION MODE ===")
        print("Looking for ColorChecker in the first image...")
        
        # Use first image for calibration
        first_filename, first_img = images_list[0]
        
        # Auto-calibrate
        calibration_method = input("Calibration method (simple/optimize) [default: simple]: ").strip()
        if calibration_method == '':
            calibration_method = 'simple'
        
        visualize = input("Show ColorChecker detection? (y/n) [default: y]: ").strip().lower()
        visualize = (visualize == '' or visualize == 'y')
        
        auto_config = calibrate.auto_calibrate(
            first_img, 
            method=calibration_method,
            visualize=visualize
        )
        
        if auto_config is None:
            print("\n❌ ColorChecker not found in the first image!")
            print("Please ensure the first image contains a visible ColorChecker board.")
            print("Falling back to MANUAL mode with config.py values.")
            active_config = config
        else:
            print("\n✓ Auto-calibration successful!")
            
            # Ask if user wants to save the config
            save_choice = input("Save calibration to 'config_auto.py'? (y/n) [default: n]: ").strip().lower()
            if save_choice == 'y':
                calibrate.save_config_to_file(auto_config)
            
            # Use the calibrated config
            active_config = auto_config
    
    # MANUAL MODE
    else:
        print("\n=== MANUAL MODE ===")
        print("Using config.py values")
        active_config = config
    
    # Process all images
    print(f"\nProcessing {len(images_list)} images...")
    start_time = time.time()
    
    for filename, original_img in images_list:
        print(f"Processing: {filename}...")
        
        # Apply corrections using the active config
        result_img = processor.apply_adjustments(original_img, active_config)
        
        # Save result
        file_io.save_image(result_img, filename, "result")
        
        # Show comparison if enabled
        if hasattr(active_config, 'SHOW_COMPARISON') and active_config.SHOW_COMPARISON:
            print("Displaying comparison... (Close window to continue)")
            visualizer.show_comparison(original_img, result_img, filename)
        elif config.SHOW_COMPARISON:
            print("Displaying comparison... (Close window to continue)")
            visualizer.show_comparison(original_img, result_img, filename)
    
    end_time = time.time()
    print(f"\n--- Done in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    main()
