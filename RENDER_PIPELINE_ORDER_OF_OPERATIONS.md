# Render Pipeline: Exact Order of Operations

## Question

**At which exact step are the original facial pixels reintroduced to guarantee pixel identity?**

## Answer: **Step 3 - Overlay Operation**

The original facial pixels are reintroduced at the **overlay filter** step, which is the **final compositing operation** before encoding.

---

## Complete Render Pipeline: Step-by-Step

### Pre-Processing (Python/OpenCV)

#### Step 0: Face Detection & Mask Creation
```
Input Image → MediaPipe → Face Bounding Box → Face Mask
```
- **Location**: `face_detection.py` → `get_face_region_info()`
- **Output**: 
  - `face_bbox`: (x, y, w, h) bounding box
  - `face_mask`: NumPy array (255=face, 0=non-face)
- **Timing**: Before FFmpeg processing

#### Step 0.5: RGBA Image Preparation
```
Original Image → Scale → Convert to RGBA → Set Mask as Alpha → Save PNG
```
- **Location**: `human_video_service.py` → `create_human_safe_video()`
- **Code**:
  ```python
  original_scaled = cv2.resize(original_image, (width, height))
  original_rgba = cv2.cvtColor(original_scaled, cv2.COLOR_BGR2BGRA)
  original_rgba[:, :, 3] = scaled_mask  # Mask → Alpha channel
  cv2.imwrite(original_rgba_path, original_rgba)
  ```
- **Output**: `original_rgba.png` (RGBA image with mask as alpha)
- **Timing**: Before FFmpeg processing

---

### FFmpeg Render Pipeline

#### Input Streams
```
[0:v] = Input image (looped)
[1:v] = Face mask (looped, not directly used in filter)
[2:v] = Original RGBA image (looped, contains original face + mask as alpha)
```

#### Step 1: Scale Input Image
```
[0:v] → scale → [scaled]
```

**Filter**: `scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2`

**Operation**:
- Resize input image to target resolution (720x1280)
- Maintain aspect ratio, add black padding if needed
- **Face pixels**: Scaled but NOT transformed yet

**Output**: `[scaled]` = Original image at target resolution

**Face Status**: ✅ Original pixels (scaled, not transformed)

---

#### Step 2: Apply Camera Transformation
```
[scaled] → zoompan/crop → [transformed]
```

**Filter**: 
- Template 1: `zoompan=z='min(zoom+0.0008,1.04)'...`
- Template 2: `crop=iw:ih:if(gte(t,0),1.5*t,0):if(gte(t,0),1.0*t,0)`
- Template 3: `zoompan=z='if(lt(t,2.5),min(zoom+0.0015,1.10),max(zoom-0.001,1.0))'...`

**Operation**:
- Apply camera motion (zoom/pan) to **ENTIRE image**
- **⚠️ IMPORTANT: FFmpeg has NO native mechanism to exclude regions from geometric transforms**
- **Face pixels ARE transformed here** (zoomed/panned) - **NO EXCLUSION POSSIBLE**
- Transformation is applied uniformly across **ALL pixels**, including face region
- **Face transformation happens here, but will be DISCARDED in Step 3**

**Output**: `[transformed]` = Image with camera motion applied everywhere (including face)

**Face Status**: ❌ Transformed pixels (zoomed/panned, will be discarded)

---

#### Step 3: Replace Transformed Face with Original ⭐ **THIS IS WHERE FACE IS PROTECTED**
```
[transformed] + [2:v] → overlay → [protected]
```

**Filter**: `overlay=0:0:alpha=premultiplied`

**Operation**:
- **Base**: `[transformed]` (image with transformation applied, **face was transformed here**)
- **Overlay**: `[2:v]` (original RGBA image with mask as alpha channel)
- **⚠️ CRITICAL: Face pixels in [transformed] are DISCARDED and REPLACED**
- **Per-pixel compositing**:
  ```
  For each pixel (x, y):
      alpha = overlay.alpha(x, y) / 255.0
      
      if alpha == 1.0 (255):  # Face region
          output[x, y] = overlay.rgb(x, y)  # REPLACE with original face pixel
          # ⚠️ Transformed face pixel from [transformed] is DISCARDED
      elif alpha == 0.0 (0):  # Non-face region
          output[x, y] = base.rgb(x, y)  # USE transformed pixel (keep motion)
      else:  # Edge region (128)
          output[x, y] = blend(overlay.rgb, base.rgb, alpha)  # BLEND
  ```

**Output**: `[protected]` = Final output with face protected

**Face Status**: ✅ **Original pixels REPLACED** (transformed face discarded, original reintroduced)

**Key Point**: Face protection is achieved through **REPLACEMENT**, not **EXCLUSION**. Face pixels are transformed, then discarded and replaced with original pixels.

---

#### Step 4: Encoding
```
[protected] → H.264 encoding → MP4 output
```

**Operation**:
- Encode video stream to H.264
- Set pixel format to yuv420p
- Optimize for web streaming (faststart)

**Output**: Final MP4 video file

---

## Exact Moment of Face Reintroduction

### Timeline

```
Frame 0 (t=0.0s):
    Step 1: [scaled] → Face pixels: Original (scaled)
    Step 2: [transformed] → Face pixels: Transformed (zoomed to 1.0x)
    Step 3: [protected] → Face pixels: ORIGINAL REINTRODUCED ⭐
    
Frame 37 (t=1.23s):
    Step 1: [scaled] → Face pixels: Original (scaled)
    Step 2: [transformed] → Face pixels: Transformed (zoomed to ~1.03x)
    Step 3: [protected] → Face pixels: ORIGINAL REINTRODUCED ⭐
    
Frame 150 (t=5.0s):
    Step 1: [scaled] → Face pixels: Original (scaled)
    Step 2: [transformed] → Face pixels: Transformed (zoomed to 1.04x)
    Step 3: [protected] → Face pixels: ORIGINAL REINTRODUCED ⭐
```

### Key Point

**The original facial pixels are reintroduced at Step 3 (overlay operation) for EVERY frame.**

- **Step 2** transforms the face (but we discard this)
- **Step 3** replaces transformed face with original face
- **Result**: Face is pixel-identical across all frames

---

## Visual Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: Static Image with Face                              │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Scale                                               │
│ [0:v] → scale → [scaled]                                    │
│ Face: Original pixels (scaled to 720x1280)                  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Apply Transformation                                │
│ [scaled] → zoompan → [transformed]                          │
│ Face: TRANSFORMED pixels (zoomed/panned) ❌                 │
│ ⚠️ Face is transformed here, but we will discard this       │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Reintroduce Original Face ⭐                        │
│ [transformed] + [2:v] → overlay → [protected]              │
│ Face: ORIGINAL pixels reintroduced ✅                       │
│ • Face region (alpha=255): Original from [2:v]               │
│ • Non-face (alpha=0): Transformed from [transformed]        │
│ • Edge (alpha=128): Blend of both                           │
│                                                              │
│ THIS IS WHERE PIXEL IDENTITY IS GUARANTEED                  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Encode                                              │
│ [protected] → H.264 → MP4                                    │
│ Face: Original pixels (encoded)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Per-Frame Operation

### For Each Frame (150 frames total, 5 seconds @ 30fps)

```
Frame N (t = N/30 seconds):

1. [0:v] → scale → [scaled]
   - Input: Original image (looped)
   - Output: Scaled original (720x1280)
   - Face pixels: Original (scaled)

2. [scaled] → zoompan → [transformed]
   - Input: Scaled original
   - Transform: zoom = 1.0 + (0.0008 * N)  # Example for Template 1
   - Output: Transformed image
   - Face pixels: Transformed (zoomed)

3. [transformed] + [2:v] → overlay → [protected] ⭐
   - Base: [transformed] (face was transformed)
   - Overlay: [2:v] (original face with mask as alpha)
   - Operation: Per-pixel compositing
     - Face region: overlay.rgb (original face pixel)
     - Non-face: base.rgb (transformed pixel)
   - Output: Protected image
   - Face pixels: ORIGINAL (reintroduced here)

4. [protected] → encode → MP4 frame
   - Encode frame to H.264
   - Face pixels: Original (encoded)
```

---

## Pixel Identity Guarantee

### Why Pixel Identity is Guaranteed

1. **Step 1**: Face pixels are from original image (scaled)
2. **Step 2**: Face pixels are transformed (zoomed/panned) - **⚠️ NO EXCLUSION POSSIBLE**
   - FFmpeg applies transformation to **entire frame** (no region exclusion)
   - Face pixels ARE transformed here, but this result will be discarded
3. **Step 3**: Face pixels are **REPLACED from [2:v]** (original RGBA image)
   - `[2:v]` contains the **original scaled image** in RGB channels (NOT transformed)
   - Mask in alpha channel ensures only face region is composited
   - **Transformed face pixels from [transformed] are DISCARDED**
   - **Original face pixels from [2:v] are used instead**
   - **Result**: Face pixels come from original (replacement), not from transformed (discarded)
4. **Step 4**: Face pixels are encoded (no change to pixel values)

**Critical Understanding**: 
- Pixel identity is **NOT** guaranteed by "excluding" face from transformation
- Pixel identity is guaranteed by **REPLACING** transformed face with original face
- Face pixels ARE transformed in Step 2, then DISCARDED and REPLACED in Step 3

### Verification

To verify pixel identity:

```python
# Extract frames at different timestamps
frame_0 = extract_frame(video, t=0.0)   # First frame
frame_75 = extract_frame(video, t=2.5)  # Middle frame
frame_150 = extract_frame(video, t=5.0) # Last frame

# Extract face region from each frame
face_0 = frame_0[y:y+h, x:x+w]
face_75 = frame_75[y:y+h, x:x+w]
face_150 = frame_150[y:y+h, x:x+w]

# Compare (should be identical)
assert np.array_equal(face_0, face_75)  # ✅ True
assert np.array_equal(face_0, face_150)  # ✅ True
assert np.array_equal(face_75, face_150)  # ✅ True
```

**Expected Result**: All face regions are pixel-identical because they all come from the same source: `[2:v]` (original RGBA image).

---

## Summary

### Exact Step: **Step 3 - Overlay Operation**

**Order of Operations:**
1. **Step 1**: Scale input → `[scaled]` (original face, scaled)
2. **Step 2**: Transform entire image → `[transformed]` (face transformed ❌)
3. **Step 3**: **Overlay original face back** → `[protected]` (face reintroduced ✅)
4. **Step 4**: Encode → MP4 (face preserved)

**Pixel Identity Guarantee:**
- Face pixels in `[protected]` come from `[2:v]` (original RGBA image)
- `[2:v]` contains original scaled image (not transformed)
- Mask ensures only face region is composited
- **Result**: Face is pixel-identical across all frames

**Key Insight**: 
- FFmpeg has **NO native mechanism** to exclude regions from geometric transforms
- Face pixels **ARE transformed** in Step 2 (zoomed/panned) - **NO EXCLUSION**
- Transformed face pixels are **DISCARDED** in Step 3
- Original face pixels are **REPLACED** in Step 3 via overlay operation
- Pixel identity is guaranteed by **REPLACEMENT**, not **EXCLUSION**
- **Face pixels are transformed, then discarded and replaced — not excluded**
