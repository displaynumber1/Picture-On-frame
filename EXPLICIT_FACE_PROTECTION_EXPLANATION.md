# Explicit Face Protection Implementation

## Problem Statement

**Camera-based motion alone does NOT guarantee facial integrity.** Even slow zoom/pan can cause subtle facial deformation. We need to **explicitly exclude facial regions from geometric transformations** rather than relying on minimal motion values.

## Solution: Mask-Based Face Protection

### Implementation Strategy

1. **Face Detection** → MediaPipe detects face and creates bounding box
2. **Mask Creation** → Generate soft-edge mask (255 = face, 0 = non-face)
3. **Dual-Path Processing**:
   - **Path 1**: Apply transformation to entire image → `[transformed]`
   - **Path 2**: Keep original image (no transformation) → `[original]`
4. **Mask Blending** → Use mask to composite: face from original, non-face from transformed

### FFmpeg Filter Chain

```
Input Image [0:v]
    ↓
[Scale & Pad] → [scaled] (original, no transform)
    ↓
[Transform] → [transformed] (camera motion applied)
    ↓
[Overlay with Mask] → [protected]
    ├─ Face region (mask=255): Use [original] pixel
    └─ Non-face region (mask=0): Use [transformed] pixel
```

### Code Implementation

```python
# 1. Create RGBA version of original with mask as alpha channel
original_rgba = cv2.cvtColor(original_scaled, cv2.COLOR_BGR2BGRA)
original_rgba[:, :, 3] = scaled_mask  # Mask as alpha

# 2. FFmpeg filter chain
filter_complex = (
    f"[0:v]{scale_filter}[scaled];"  # Original (no transform)
    f"[scaled]{transform_filter}[transformed];"  # Apply transformation
    f"[transformed][2:v]overlay=0:0:alpha=premultiplied[protected]"  # Overlay original with mask
)
```

### How It Works

1. **RGBA Image Creation**:
   - Original image converted to RGBA
   - Mask values copied to alpha channel
   - High mask value (255) = high alpha = more visible (protected)

2. **Overlay Filter**:
   - Base: `[transformed]` (camera motion applied)
   - Overlay: `[original_rgba]` (original with mask as alpha)
   - Alpha channel determines blend ratio:
     - `alpha = 255`: 100% overlay (original face) - **FULL PROTECTION**
     - `alpha = 0`: 0% overlay (transformed) - **NO PROTECTION**
     - `alpha = 128`: 50/50 blend - **SMOOTH TRANSITION**

3. **Result**:
   - Face region: **Pixel-identical** to original (no transformation)
   - Non-face region: **Transformed** (camera motion applied)
   - Transition zone: **Smooth blend** (feathered edge)

### Key Differences from Previous Approach

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Face Protection** | Minimal motion (slow zoom) | Explicit mask exclusion |
| **Face Deformation** | Possible (subtle) | **Impossible** (excluded) |
| **Transformation** | Applied to entire image | Applied only to non-face regions |
| **Reliability** | Depends on motion speed | **Guaranteed** by mask |

### Technical Details

#### Mask Format
- **255** = Face region (protected, use original)
- **0** = Non-face region (transformable, use transformed)
- **128** = Transition zone (50/50 blend)

#### FFmpeg Overlay Filter
```bash
overlay=0:0:alpha=premultiplied
```
- `0:0`: Position (top-left)
- `alpha=premultiplied`: Use alpha channel of overlay input
- Alpha value determines blend ratio per pixel

#### Face Detection
- MediaPipe Face Detection (model_selection=1, full-range)
- Bounding box expanded by 18% (includes hairline)
- Gaussian blur for soft edges (feathering)

### Advantages

1. **Guaranteed Face Integrity**: Face region is **completely excluded** from transformations
2. **No Facial Deformation**: Face remains **pixel-identical** across all frames
3. **Flexible Motion**: Can use **any camera motion** (zoom, pan, rotation) without affecting face
4. **Smooth Transitions**: Feathered mask edges prevent visible seams
5. **Per-Pixel Control**: Mask provides explicit control over which pixels are protected

### Limitations

1. **Face Detection Required**: Must detect face first (MediaPipe)
2. **Mask Accuracy**: Depends on face detection quality
3. **Processing Overhead**: Requires creating RGBA image and additional overlay step
4. **Edge Cases**: Multiple faces or partial face detection may need special handling

### Testing

To verify face protection:
1. Generate video with face
2. Extract frames at different timestamps
3. Compare face region pixels - should be **identical**
4. Compare non-face regions - should show **transformation**

### Future Enhancements

1. **Multiple Face Support**: Handle images with multiple faces
2. **Dynamic Mask Updates**: Adjust mask if face moves (for video input)
3. **Landmark-Based Masking**: Use facial landmarks for more precise protection
4. **Body Region Protection**: Extend to protect entire body, not just face
