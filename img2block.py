#!/usr/bin/env python3
"""convert images to unicode block characters with quadrant best-fit matching"""

import argparse
from PIL import Image
import numpy as np

# quadrant block patterns as 2x2 matrices: [[tl, tr], [bl, br]]
QUADRANT_PATTERNS = [
    (' ', [[0, 0], [0, 0]]),
    ('▗', [[0, 0], [0, 1]]),
    ('▖', [[0, 0], [1, 0]]),
    ('▄', [[0, 0], [1, 1]]),
    ('▝', [[0, 1], [0, 0]]),
    ('▐', [[0, 1], [0, 1]]),
    ('▞', [[0, 1], [1, 0]]),
    ('▟', [[0, 1], [1, 1]]),
    ('▘', [[1, 0], [0, 0]]),
    ('▚', [[1, 0], [0, 1]]),
    ('▌', [[1, 0], [1, 0]]),
    ('▙', [[1, 0], [1, 1]]),
    ('▀', [[1, 1], [0, 0]]),
    ('▜', [[1, 1], [0, 1]]),
    ('▛', [[1, 1], [1, 0]]),
    ('█', [[1, 1], [1, 1]]),
]

# shade patterns as uniform fills (all quadrants same value)
SHADE_PATTERNS = [
    ('░', [[0.25, 0.25], [0.25, 0.25]]),  # light shade (25%)
    ('▒', [[0.5, 0.5], [0.5, 0.5]]),      # medium shade (50%)
    ('▓', [[0.75, 0.75], [0.75, 0.75]]),  # dark shade (75%)
]

# combine all patterns for best-fit matching
ALL_PATTERNS = QUADRANT_PATTERNS + SHADE_PATTERNS

# precompute as numpy arrays for fast matching
PATTERNS = [(char, np.array(pattern, dtype=np.float32)) for char, pattern in ALL_PATTERNS]

# kept for potential future use
VERTICAL = ' ▁▂▃▄▅▆▇█'
HORIZONTAL = ' ▏▎▍▌▋▊▉█'
SHADES = ' ░▒▓█'

def boost_contrast(brightness: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """apply contrast boost to push values toward 0 or 1"""
    # linear contrast: (value - 0.5) * strength + 0.5
    # strength = 1: no change, strength > 1: increase contrast
    return np.clip((brightness - 0.5) * strength + 0.5, 0, 1)

def best_fit_quadrant(quad: np.ndarray) -> str:
    """find quadrant block with minimum L2 distance to brightness quad"""
    # quad values are already 0-1 averages per quadrant
    # find closest match to binary patterns
    min_dist = float('inf')
    best_char = ' '

    for char, pattern in PATTERNS:
        dist = np.sum((quad - pattern) ** 2)
        if dist < min_dist:
            min_dist = dist
            best_char = char

    return best_char

def sample_cell(img_array: np.ndarray, x: int, y: int, cell_w: float, cell_h: float, threshold: float = 0.5) -> np.ndarray:
    """
    sample 2x2 quadrant values - average brightness in each quadrant
    returns shape (2, 2) with values in [0, 1]
    """
    h, w = img_array.shape

    # calculate pixel boundaries for this character cell
    x_start = int(x * cell_w)
    x_mid = int((x + 0.5) * cell_w)
    x_end = int((x + 1) * cell_w)

    y_start = int(y * cell_h)
    y_mid = int((y + 0.5) * cell_h)
    y_end = int((y + 1) * cell_h)

    # average brightness per quadrant
    tl = img_array[y_start:y_mid, x_start:x_mid].mean()
    tr = img_array[y_start:y_mid, x_mid:x_end].mean()
    bl = img_array[y_mid:y_end, x_start:x_mid].mean()
    br = img_array[y_mid:y_end, x_mid:x_end].mean()

    return np.array([[tl, tr], [bl, br]], dtype=np.float32)

def image_to_blocks(path: str, lines: int, contrast: float = 1.0, brightness: float = 0.0) -> str:
    """convert image to block characters with quadrant best-fit matching"""
    img = Image.open(path)

    # convert to grayscale with alpha
    if img.mode != 'LA':
        img = img.convert('RGBA').convert('LA')

    # calculate target dimensions (chars are ~2x taller than wide)
    aspect = img.width / img.height
    cols = int(lines * aspect * 2)

    # resize with quality resampling
    target_w = cols * 2  # 2x supersampling for quadrant detection
    target_h = lines * 2
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # extract brightness and alpha channels
    la = np.array(img).astype(np.float32)
    gray_arr = la[:, :, 0] / 255.0
    alpha_arr = la[:, :, 1] / 255.0

    # apply brightness shift BEFORE alpha so transparency stays dark
    if brightness != 0.0:
        gray_arr = np.clip(gray_arr + brightness, 0.0, 1.0)

    # combine: transparent pixels become dark
    brightness_arr = gray_arr * alpha_arr

    # boost contrast to favor quadrant blocks
    brightness_arr = boost_contrast(brightness_arr, contrast)

    # map to character grid using best-fit matching
    cell_h = target_h / lines
    cell_w = target_w / cols

    result = []
    for y in range(lines):
        row = []
        for x in range(cols):
            quad = sample_cell(brightness_arr, x, y, cell_w, cell_h)
            char = best_fit_quadrant(quad)
            row.append(char)
        result.append(''.join(row))

    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(
        description='convert image to unicode blocks with quadrant best-fit matching'
    )
    parser.add_argument('image', help='path to image file')
    parser.add_argument('--lines', type=int, default=40, help='output height in lines')
    parser.add_argument('--contrast', type=float, default=1.0, help='contrast boost strength')
    parser.add_argument('--brightness', type=float, default=0.0, help='additive brightness shift applied before alpha compositing (negative to darken, positive to lighten)')
    args = parser.parse_args()

    output = image_to_blocks(args.image, args.lines, args.contrast, args.brightness)
    print(output)

if __name__ == '__main__':
    main()
