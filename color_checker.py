import cv2
import numpy as np
from typing import Optional, Tuple, List

# Standard ColorChecker Classic 24-patch reference values (sRGB, D65)
COLORCHECKER_REFERENCE = {
    # Row 1
    'dark_skin':        (115, 82, 68),
    'light_skin':       (194, 150, 130),
    'blue_sky':         (98, 122, 157),
    'foliage':          (87, 108, 67),
    'blue_flower':      (133, 128, 177),
    'bluish_green':     (103, 189, 170),
    
    # Row 2
    'orange':           (214, 126, 44),
    'purplish_blue':    (80, 91, 166),
    'moderate_red':     (193, 90, 99),
    'purple':           (94, 60, 108),
    'yellow_green':     (157, 188, 64),
    'orange_yellow':    (224, 163, 46),
    
    # Row 3
    'blue':             (56, 61, 150),
    'green':            (70, 148, 73),
    'red':              (175, 54, 60),
    'yellow':           (231, 199, 31),
    'magenta':          (187, 86, 149),
    'cyan':             (8, 133, 161),
    
    # Row 4 (Grayscale)
    'white':            (243, 243, 242),
    'neutral_8':        (200, 200, 200),
    'neutral_6.5':      (160, 160, 160),
    'neutral_5':        (122, 122, 121),
    'neutral_3.5':      (85, 85, 85),
    'black':            (52, 52, 52),
}

# Convert to array format (6 columns × 4 rows)
REFERENCE_COLORS = np.array([
    # Row 1
    [(115, 82, 68), (194, 150, 130), (98, 122, 157), (87, 108, 67), (133, 128, 177), (103, 189, 170)],
    # Row 2
    [(214, 126, 44), (80, 91, 166), (193, 90, 99), (94, 60, 108), (157, 188, 64), (224, 163, 46)],
    # Row 3
    [(56, 61, 150), (70, 148, 73), (175, 54, 60), (231, 199, 31), (187, 86, 149), (8, 133, 161)],
    # Row 4
    [(243, 243, 242), (200, 200, 200), (160, 160, 160), (122, 122, 121), (85, 85, 85), (52, 52, 52)]
], dtype=np.uint8)


def detect_colorchecker_grid(image_pil) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Alternative detection method: Look for the grid pattern of patches
    instead of looking for the outer border.
    """
    img = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Use adaptive threshold to find patches
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter for square-ish patches
    patch_candidates = []
    img_area = img.shape[0] * img.shape[1]
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Each patch should be roughly 0.1% to 5% of image
        if area > img_area * 0.001 and area < img_area * 0.05:
            # Approximate to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Should be roughly rectangular (4 corners)
            if len(approx) >= 4 and len(approx) <= 6:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Patches should be roughly square (aspect ratio 0.7 to 1.4)
                if 0.7 < aspect_ratio < 1.4:
                    patch_candidates.append({
                        'contour': contour,
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'center': (x + w//2, y + h//2),
                        'area': area
                    })
    
    if len(patch_candidates) < 20:
        return None
    
    # Find grid arrangement (look for 6 columns × 4 rows)
    grid_result = find_grid_arrangement(patch_candidates, img)
    
    if grid_result is None:
        return None
    
    corners, warped = grid_result
    return corners, warped


def find_grid_arrangement(patches, img):
    """
    Try to find 24 patches arranged in a 6×4 grid.
    """
    if len(patches) < 20:
        return None
    
    # Sort patches by position
    patches = sorted(patches, key=lambda p: (p['y'], p['x']))
    
    # Try to find 4 rows
    rows = []
    current_row = [patches[0]]
    
    for patch in patches[1:]:
        # If y-coordinate is similar to current row, add to it
        if abs(patch['y'] - current_row[0]['y']) < current_row[0]['h'] * 0.5:
            current_row.append(patch)
        else:
            # Start new row
            if len(current_row) >= 5:  # Should have ~6 patches per row
                rows.append(sorted(current_row, key=lambda p: p['x']))
            current_row = [patch]
    
    # Add last row
    if len(current_row) >= 5:
        rows.append(sorted(current_row, key=lambda p: p['x']))
    
    # Check if we have 4 rows
    if len(rows) < 4:
        return None
    
    # Take the 4 most populated rows
    rows = sorted(rows, key=lambda r: len(r), reverse=True)[:4]
    rows = sorted(rows, key=lambda r: r[0]['y'])
    
    # Get bounding box of all patches
    all_patches = [p for row in rows for p in row[:6]]  # Take first 6 of each row
    
    if len(all_patches) < 20:
        return None
    
    min_x = min(p['x'] for p in all_patches)
    max_x = max(p['x'] + p['w'] for p in all_patches)
    min_y = min(p['y'] for p in all_patches)
    max_y = max(p['y'] + p['h'] for p in all_patches)
    
    # Add margin around the grid
    margin = int((max_x - min_x) * 0.1)
    img_shape = img.shape
    min_x = max(0, min_x - margin)
    max_x = min(img_shape[1], max_x + margin)
    min_y = max(0, min_y - margin)
    max_y = min(img_shape[0], max_y + margin)
    
    # Create corners
    corners = np.array([
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y]
    ], dtype=np.float32)
    
    # Get warped view
    warped = get_warped_board(img, corners)
    
    return corners, warped


def detect_colorchecker(image_pil) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Detects a ColorChecker board using multiple methods.
    """
    # Method 1: Try grid-based detection (more robust)
    result = detect_colorchecker_grid(image_pil)
    if result is not None:
        return result
    
    # Method 2: Try border-based detection (original method)
    img = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Try multiple edge detection parameters
    for low_thresh, high_thresh in [(30, 100), (50, 150), (70, 200)]:
        edges = cv2.Canny(gray, low_thresh, high_thresh, apertureSize=3)
        
        # Dilate edges to connect nearby edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                img_area = img.shape[0] * img.shape[1]
                
                # Lowered threshold to 3% instead of 5%
                if area > img_area * 0.03:
                    rect = cv2.minAreaRect(approx)
                    width, height = rect[1]
                    
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        
                        # Relaxed aspect ratio: 1.2 to 2.0
                        if 1.2 < aspect_ratio < 2.0:
                            corners = approx.reshape(4, 2)
                            warped = get_warped_board(img, corners)
                            
                            if verify_colorchecker_pattern(warped):
                                return corners, warped
    
    return None


def get_warped_board(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """
    Apply perspective transformation to get a flat, front-facing view of the board.
    """
    corners = order_points(corners)
    
    width = 600
    height = 400
    
    dst_points = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    
    matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_points)
    warped = cv2.warpPerspective(img, matrix, (width, height))
    
    return warped


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order points in: top-left, top-right, bottom-right, bottom-left
    """
    rect = np.zeros((4, 2), dtype=np.float32)
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect


def verify_colorchecker_pattern(warped: np.ndarray) -> bool:
    """
    Verify that the detected region actually looks like a ColorChecker.
    """
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    
    rows, cols = 4, 6
    h, w = warped_rgb.shape[:2]
    
    patch_width = w // cols
    patch_height = h // rows
    
    colors = []
    
    for row in range(rows):
        for col in range(cols):
            y = int((row + 0.5) * patch_height)
            x = int((col + 0.5) * patch_width)
            
            sample = warped_rgb[y-5:y+5, x-5:x+5]
            if sample.size > 0:
                avg_color = sample.mean(axis=(0, 1))
                colors.append(avg_color)
    
    if len(colors) < 20:
        return False
    
    colors_array = np.array(colors)
    std_dev = colors_array.std()
    
    # Relaxed threshold: 25 instead of 30
    if std_dev < 25:
        return False
    
    brightness = colors_array.mean(axis=1)
    if brightness.max() - brightness.min() < 80:  # Relaxed from 100
        return False
    
    return True


def extract_patch_colors(warped: np.ndarray) -> np.ndarray:
    """
    Extract the average color from each of the 24 patches.
    """
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    
    rows, cols = 4, 6
    h, w = warped_rgb.shape[:2]
    
    patch_width = w // cols
    patch_height = h // rows
    
    extracted_colors = np.zeros((rows, cols, 3), dtype=np.float32)
    
    for row in range(rows):
        for col in range(cols):
            margin_w = int(patch_width * 0.2)
            margin_h = int(patch_height * 0.2)
            
            y1 = row * patch_height + margin_h
            y2 = (row + 1) * patch_height - margin_h
            x1 = col * patch_width + margin_w
            x2 = (col + 1) * patch_width - margin_w
            
            patch = warped_rgb[y1:y2, x1:x2]
            avg_color = patch.mean(axis=(0, 1))
            extracted_colors[row, col] = avg_color
    
    return extracted_colors.astype(np.uint8)


def visualize_detection(image_pil, corners, warped, extracted_colors):
    """
    Visualize the detection result for debugging.
    """
    import matplotlib.pyplot as plt
    from PIL import Image
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    img_with_corners = np.array(image_pil).copy()
    corners_int = corners.astype(int)
    
    for i in range(4):
        pt1 = tuple(corners_int[i])
        pt2 = tuple(corners_int[(i + 1) % 4])
        cv2.line(img_with_corners, pt1, pt2, (255, 0, 0), 3)
        cv2.circle(img_with_corners, pt1, 8, (0, 255, 0), -1)
    
    axes[0].imshow(img_with_corners)
    axes[0].set_title("Detected ColorChecker")
    axes[0].axis('off')
    
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    axes[1].imshow(warped_rgb)
    axes[1].set_title("Warped Board")
    axes[1].axis('off')
    
    cell_size = 50
    color_grid = np.zeros((4 * cell_size, 6 * cell_size, 3), dtype=np.uint8)
    
    for row in range(4):
        for col in range(6):
            color = extracted_colors[row, col]
            y1, y2 = row * cell_size, (row + 1) * cell_size
            x1, x2 = col * cell_size, (col + 1) * cell_size
            color_grid[y1:y2, x1:x2] = color
    
    axes[2].imshow(color_grid)
    axes[2].set_title("Extracted Colors")
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()


def detect_and_extract_colors(image_pil, visualize=False):
    """
    Main function: Detect ColorChecker and extract patch colors.
    """
    print("Searching for ColorChecker in image...")
    
    result = detect_colorchecker(image_pil)
    
    if result is None:
        print("❌ ColorChecker not found in image")
        return None, None
    
    corners, warped = result
    print("✓ ColorChecker detected!")
    
    extracted_colors = extract_patch_colors(warped)
    
    if visualize:
        visualize_detection(image_pil, corners, warped, extracted_colors)
    
    return extracted_colors, REFERENCE_COLORS
