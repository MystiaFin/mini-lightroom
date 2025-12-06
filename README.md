# Mini Python Lightroom

## Dependencies

### Option 1: Manual Installation (pip)

Install the required Python packages:

```bash
pip install opencv-python numpy pillow matplotlib
```

**Required modules:**
- `opencv-python` - Image processing operations
- `numpy` - Array manipulation
- `pillow` (PIL) - Image loading and basic adjustments
- `matplotlib` - Visual comparison display

### Option 2: Nix Flake

If you're using Nix with flakes enabled, simply run:

```bash
nix develop
```

This will automatically set up a development shell with all dependencies installed.

The `flake.nix` includes:
- Python 3 with all required packages (opencv, numpy, pillow, matplotlib)
- Black formatter for code formatting

## Usage

### Step 1: Add Your Images

Place all the images you want to process in the `images/` directory:

```
mini-lightroom/
├── images/
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── photo3.png
├── main.py
├── config.py
└── ...
```

### Step 2: Configure Adjustments

Open `config.py` and adjust the parameters to your liking:

```python
# --- DISPLAY ---
SHOW_COMPARISON = True  # Show before/after comparison for each image

# --- COLOR ---
HUE = 0              # Hue shift: -180 to 180 (0 = no change)
SATURATION = 1.2     # Saturation: 0.0 (grayscale) to 2.0+ (vibrant), 1.0 = neutral

# --- CHANNEL MIXER ---
REDNESS = 1.0        # Red channel multiplier (1.0 = neutral)
GREENNESS = 1.0      # Green channel multiplier
BLUENESS = 1.1       # Blue channel multiplier

# --- TONE ---
WHITE = 1.1          # Exposure/brightness (1.0 = neutral)
BLACK = 10           # Black clipping (0-255, higher = darker blacks)
SHADOW = 0.2         # Shadow lift (0.0-1.0, lifts dark areas)
```

### Step 3: Run the Script

Execute the main script:

```bash
python main.py
```

Or if using Nix:

```bash
nix develop
python main.py
```

### Step 4: View Results

- Processed images are saved in the `result/` directory with the prefix `edited_`
- If `SHOW_COMPARISON = True`, a matplotlib window will display the before/after comparison for each image (close the window to continue to the next image)
- Processing time is displayed at the end
