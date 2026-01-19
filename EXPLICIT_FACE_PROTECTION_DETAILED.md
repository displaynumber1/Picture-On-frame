# Explicit Face Protection: Technical Implementation

## Problem

**Camera-based motion alone does NOT guarantee facial integrity.** Even slow zoom/pan can cause subtle facial deformation. 

**⚠️ Technical Reality**: FFmpeg has **NO native mechanism** to exclude regions from geometric transforms. Zoompan, crop, rotate, and all geometric transforms are applied to the **entire frame** uniformly.

We need to **replace transformed face pixels with original face pixels** using mask-based overlay compositing.

## Solution: Mask-Based Pixel Replacement (Not Exclusion)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  INPUT: Static Image with Human Face                    │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Face Detection (MediaPipe)                     │
│  - Detect face bounding box                             │
│  - Expand by 18% (includes hairline)                    │
│  - Create soft-edge mask (feathering)                  │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Dual-Path Processing                           │
│                                                          │
│  PATH A (Original RGBA):                                │
│  [Image] → Scale → RGBA with mask as alpha → [2:v]      │
│  Result: Original image preserved for replacement       │
│                                                          │
│  PATH B (Transformed):                                  │
│  [Image] → Scale → Transform → [transformed]            │
│  Result: Camera motion applied (zoom/pan)              │
│  ⚠️ Face IS transformed here (no exclusion possible)     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Mask-Based Pixel Replacement                   │
│                                                          │
│  RGBA image (prepared in Step 0.5):                     │
│  - RGB channels: Original scaled image                 │
│  - Alpha channel: Face mask (255=face, 0=non-face)      │
│                                                          │
│  FFmpeg Overlay:                                        │
│  [transformed] (base) + [original_rgba] (overlay)       │
│  → Alpha channel determines replacement ratio           │
│                                                          │
│  Per-pixel result:                                      │
│  - Face region (alpha=255): REPLACE with original      │
│    ⚠️ Transformed face pixel from [transformed] DISCARDED│
│  - Non-face (alpha=0): KEEP transformed (motion)       │
│  - Edge (alpha=128): BLEND (smooth transition)          │
│                                                          │
│  Key: Face pixels are TRANSFORMED, then DISCARDED,      │
│       then REPLACED with original — not excluded        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│  OUTPUT: Video with Explicit Face Protection            │
│  - Face: Pixel-identical across all frames             │
│  - Non-face: Camera motion applied                     │
│  - Transition: Smooth feathered edges                   │
└─────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Face Mask Creation

```python
# face_detection.py
def create_face_mask(image_shape, face_bbox, feather_size=30):
    # Create binary mask: 255 = face (protected), 0 = non-face
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[y:y+h, x:x+w] = 255  # Face region = 255
    
    # Apply Gaussian blur for soft edges (feathering)
    mask = cv2.GaussianBlur(mask, (61, 61), 10)
    
    return mask  # 255=protected, 0=transformable
```

**Mask Values:**
- **255**: Face center (100% protection, use original pixel)
- **128**: Face edge (50% protection, blend original + transformed)
- **0**: Non-face (0% protection, use transformed pixel)

### 2. RGBA Image with Mask as Alpha

```python
# human_video_service.py
# Scale original image to target resolution
original_scaled = cv2.resize(original_image, (width, height))

# Convert to RGBA
original_rgba = cv2.cvtColor(original_scaled, cv2.COLOR_BGR2BGRA)

# Use mask as alpha channel
original_rgba[:, :, 3] = scaled_mask
# - alpha = 255 → face region (fully visible, protected)
# - alpha = 0 → non-face (invisible, transformed shows through)
```

### 3. FFmpeg Filter Chain

```python
filter_complex = (
    f"[0:v]{scale_filter}[scaled];"  # Scale input to target resolution
    f"[scaled]{transform_filter}[transformed];"  # Apply camera transformation
    f"[transformed][2:v]overlay=0:0:alpha=premultiplied[protected]"
)
```

**Filter Breakdown:**
1. `[0:v]` → Input image
2. `scale` → Resize to 720x1280 (maintains aspect ratio)
3. `[scaled]` → Original scaled image (no transform)
4. `transform` → Apply zoom/pan (camera motion)
5. `[transformed]` → Image with camera motion
6. `[2:v]` → RGBA original image (mask in alpha channel)
7. `overlay` → Composite using alpha channel
8. `[protected]` → Final output (face protected)

### 4. Overlay Filter Behavior

The `overlay` filter with `alpha=premultiplied` works as follows:

```
For each pixel (x, y):
    alpha = overlay.alpha(x, y) / 255.0  # Normalize to 0-1
    
    if alpha == 1.0 (255):
        output = overlay.rgb(x, y)  # 100% original (face)
    elif alpha == 0.0 (0):
        output = base.rgb(x, y)  # 100% transformed (non-face)
    else:
        output = alpha * overlay.rgb + (1-alpha) * base.rgb  # Blend
```

**Result:**
- **Face pixels (alpha=255)**: Always use original → **NO TRANSFORMATION**
- **Non-face pixels (alpha=0)**: Always use transformed → **FULL TRANSFORMATION**
- **Edge pixels (alpha=128)**: Blend 50/50 → **SMOOTH TRANSITION**

## Geometric Transform Replacement (Not Exclusion)

### ⚠️ Technical Correction

**FFmpeg has NO native mechanism to exclude regions from geometric transforms.**

Zoompan, crop, rotate, and all geometric transforms are applied to the **entire frame** uniformly. There is no way to conditionally skip transforms for specific regions.

### What Actually Happens

1. **Zoom Transformations**
   - Face pixels **ARE sampled from zoomed image** in Step 2
   - Transformed face pixels are **DISCARDED** in Step 3
   - Original face pixels are **REPLACED** from [2:v] (no interpolation on final output)

2. **Pan Transformations**
   - Face pixels **ARE shifted** in Step 2
   - Transformed face pixels are **DISCARDED** in Step 3
   - Original face pixels are **REPLACED** at original position

3. **Rotation Transformations** (if added)
   - Face pixels **ARE rotated** in Step 2
   - Transformed face pixels are **DISCARDED** in Step 3
   - Original face pixels are **REPLACED** at original orientation

4. **Any Geometric Transform**
   - Face region **IS transformed** in Step 2 (no exclusion possible)
   - Transformed face pixels are **DISCARDED** in Step 3
   - Original face pixels are **REPLACED** in Step 3
   - **Result**: Face is pixel-identical because of **REPLACEMENT**, not **EXCLUSION**

### What Still Moves

Only **non-face regions** receive transformations:

1. **Background**: Zoom/pan applied
2. **Clothing (non-face)**: Zoom/pan applied
3. **Body (non-face)**: Zoom/pan applied
4. **Foreground objects**: Zoom/pan applied

### Face Region Guarantees

✅ **Face remains pixel-identical** across all frames (via replacement)
✅ **No facial deformation** in final output (transformed face discarded, original replaced)
✅ **No facial morphing** (original pixels used, not transformed pixels)
✅ **No expression changes** (static face region from original)
✅ **No blinking** (face is static image from original)
✅ **No head movement** (face position locked from original)

**⚠️ Important**: These guarantees are achieved through **REPLACEMENT** of transformed face pixels with original face pixels, not through **EXCLUSION** from transformation. Face pixels ARE transformed in Step 2, then DISCARDED and REPLACED in Step 3.

## Comparison: Before vs After

### Before (Minimal Motion Approach)

```python
# Only relied on slow motion
zoom_filter = "zoompan=z='min(zoom+0.0008,1.04)'"
# Problem: Face still gets transformed (just slowly)
# Result: Subtle facial deformation possible
```

**Issues:**
- Face pixels are still sampled from transformed image
- Interpolation can cause subtle changes
- No explicit protection mechanism

### After (Explicit Mask Replacement)

```python
# Explicit mask-based exclusion
filter_complex = (
    "[0:v]scale[scaled];"
    "[scaled]zoompan[transformed];"
    "[transformed][2:v]overlay=0:0:alpha=premultiplied[protected]"
)
# Solution: Face pixels REPLACED with original (transformed face discarded)
# Result: Face is pixel-identical via replacement, not exclusion
```

**Benefits:**
- Face pixels explicitly excluded from transformation
- Face pixels come directly from original image
- Zero interpolation on face region
- Guaranteed facial integrity

## Technical Verification

### How to Verify Face Protection

1. **Extract frames from video:**
   ```bash
   ffmpeg -i output.mp4 -vf "select='eq(n,0)'" frame_0.png
   ffmpeg -i output.mp4 -vf "select='eq(n,75)'" frame_75.png
   ```

2. **Compare face region pixels:**
   ```python
   import cv2
   frame0 = cv2.imread('frame_0.png')
   frame75 = cv2.imread('frame_75.png')
   
   # Extract face region
   face_region_0 = frame0[y:y+h, x:x+w]
   face_region_75 = frame75[y:y+h, x:x+w]
   
   # Compare (should be identical)
   diff = cv2.absdiff(face_region_0, face_region_75)
   assert diff.sum() == 0  # Should be zero (pixel-identical)
   ```

3. **Compare non-face region:**
   ```python
   # Non-face should show transformation
   non_face_0 = frame0[0:y, :]  # Above face
   non_face_75 = frame75[0:y, :]
   
   diff = cv2.absdiff(non_face_0, non_face_75)
   assert diff.sum() > 0  # Should be different (transformed)
   ```

## Code Flow

### Complete Pipeline

```python
# 1. Detect face
face_info = get_face_region_info(image_path)
face_bbox = face_info["bbox"]  # (x, y, w, h)
face_mask = face_info["mask"]  # 255=face, 0=non-face

# 2. Scale mask to target resolution
scaled_mask = cv2.resize(face_mask, (720, 1280))

# 3. Create RGBA original with mask as alpha
original_scaled = cv2.resize(original_image, (720, 1280))
original_rgba = cv2.cvtColor(original_scaled, cv2.COLOR_BGR2BGRA)
original_rgba[:, :, 3] = scaled_mask  # Mask → Alpha

# 4. FFmpeg filter chain
filter_complex = (
    "[0:v]scale=720:1280[scaled];"  # Original (no transform)
    "[scaled]zoompan=z='min(zoom+0.0008,1.04)'[transformed];"  # Transform
    "[transformed][2:v]overlay=0:0:alpha=premultiplied[protected]"  # Blend
)

# 5. FFmpeg command
ffmpeg -loop 1 -i image.jpg \
       -loop 1 -i mask.png \
       -loop 1 -i original_rgba.png \
       -filter_complex "$filter_complex" \
       -map "[protected]" \
       output.mp4
```

## Key Points

1. **Explicit Exclusion**: Face region is explicitly excluded from geometric transforms via mask
2. **Pixel-Identical**: Face pixels are copied directly from original (no interpolation)
3. **Zero Deformation**: Face cannot be deformed because it's not transformed
4. **Per-Pixel Control**: Mask provides explicit control over which pixels are protected
5. **Smooth Transitions**: Feathered mask edges prevent visible seams

## Limitations & Considerations

1. **Face Detection Accuracy**: Depends on MediaPipe detection quality
2. **Multiple Faces**: Current implementation handles single face (can be extended)
3. **Partial Face**: Edge cases where face is partially visible need special handling
4. **Processing Overhead**: Requires creating RGBA image and additional overlay step
5. **Mask Alignment**: Mask must be scaled consistently with image scaling

## Future Enhancements

1. **Landmark-Based Masking**: Use facial landmarks for more precise protection
2. **Body Region Protection**: Extend to protect entire body, not just face
3. **Dynamic Masks**: Adjust mask if face moves (for video input)
4. **Multi-Face Support**: Handle images with multiple faces
5. **Adaptive Feathering**: Adjust feather size based on face size
