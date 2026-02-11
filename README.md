# img2block

convert images to unicode block characters using quadrant best-fit matching

## installation

```bash
uv pip install -e .
```

## usage

```bash
uv run python img2block.py image.png --lines 40 --contrast 2.5
```

**arguments:**
- `image`: path to image file (png, jpg, etc)
- `--lines`: output height in character lines (default: 40)
- `--contrast`: contrast boost strength (default: 2.5, can go as high as you like. to remove all shading unicode, set to something like 100. negative values will invert the image)

## how it works

1. **load image** - converts to grayscale with alpha channel
2. **resize** - scales to target character grid (chars are ~2x taller than wide)
3. **contrast boost** - applies linear contrast around midpoint to push values toward 0 or 1
4. **quadrant sampling** - divides each character cell into 2x2 quadrants, thresholds pixels at 0.5, computes fraction of "on" pixels per quadrant
5. **best-fit matching** - finds unicode block character with minimum L2 distance to quadrant brightness pattern

**unicode blocks used:**
- 16 quadrant blocks (` ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█`) - binary on/off patterns for each 2x2 region
- gives 2x2 spatial resolution per character for maximum detail at edges and internal features

**note:** vertical/horizontal fractional eighths and shade characters are defined in the code but not currently used - reserved for potential hybrid best-fit matching approach
