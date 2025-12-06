import config
import file_io
import processor
import visualizer
import time

def main():
    print("--- Mini Python Lightroom ---")
    
    images_list = file_io.load_images("images")
    
    if not images_list:
        print("No images found in 'images/'. Exiting.")
        return

    print(f"Found {len(images_list)} images. Processing...")
    start_time = time.time()

    for filename, original_img in images_list:
        print(f"Processing: {filename}...")
        
        result_img = processor.apply_adjustments(original_img, config)
        
        # Save Result
        file_io.save_image(result_img, filename, "result")

        if config.SHOW_COMPARISON:
            print("Displaying comparison... (Close window to continue)")
            visualizer.show_comparison(original_img, result_img, filename)

    end_time = time.time()
    print(f"--- Done in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    main()
