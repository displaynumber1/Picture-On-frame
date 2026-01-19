# Fake Motion Generation Pipeline - Technical Explanation

## Overview

This project implements **two distinct fake motion systems** for converting static images into TikTok-ready videos:

1. **Standard Fake Motion** (for non-human images) - `video_service.py`
2. **Human-Safe Fake Motion** (for images with faces) - `human_video_service.py`

Both systems use **FFmpeg filters** to create motion effects without modifying the original image pixels directly. Instead, they apply **transformations** that simulate camera movement, lighting changes, and object motion.

---

## Pipeline Architecture

```
Input Image (Static)
    ↓
[Face Detection] (if human-safe mode)
    ↓
[FFmpeg Filter Chain]
    ├─ Scale & Pad (resolution normalization)
    ├─ Camera Motion (zoom/pan)
    ├─ Text Overlays (drawtext)
    └─ Encoding (H.264)
    ↓
Output Video (MP4, 5 seconds, 30fps)
```

---

## 1. STANDARD FAKE MOTION (Non-Human Images)

**File:** `backend/video_service.py` → `create_fake_motion_video()`

### Filter Chain Breakdown

#### A. **Scale & Pad** (Pixel Modification - Initial Setup)
```python
scale_filter = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2"
```

**What it does:**
- **Directly modifies pixels**: Resizes image to target resolution (720x1280)
- Maintains aspect ratio, adds black padding if needed
- **This is the ONLY direct pixel modification** - everything else is transformation

**Type:** Direct pixel manipulation (one-time, per-frame)

---

#### B. **Camera Zoom** (Camera Movement - Transformation)
```python
zoom_filter = "zoompan=z='min(zoom+0.0015,1.08)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
```

**What it does:**
- **Simulates camera movement**: Gradual zoom from 1.0x → 1.08x over 5 seconds
- **Does NOT modify pixels directly**: Uses **affine transformation** (scaling + translation)
- Keeps subject centered during zoom
- Creates **ease-in-out** motion effect

**Type:** Camera transformation (per-frame, non-destructive)

**Motion Type:**
- ✅ **Camera Movement** (zoom in)
- ❌ Not object movement
- ❌ Not light movement
- ❌ Not pixel modification (uses interpolation)

**How it works:**
- FFmpeg's `zoompan` filter samples pixels from the source image
- For each frame, it calculates a new zoom level: `zoom = min(zoom + 0.0015, 1.08)`
- It then **crops and scales** a region from the source image
- The center point is recalculated: `x = iw/2 - (iw/zoom/2)` to keep subject centered
- This creates the illusion of camera moving closer

---

#### C. **Text Overlays** (Direct Pixel Modification)
```python
hook_text_filter = "drawtext=text='Check This Out!':fontsize=102:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-192:enable='between(t,0,1.2)':alpha='...'"
```

**What it does:**
- **Directly modifies pixels**: Renders text on top of video frames
- Uses alpha blending for fade in/out effects
- Text appears/disappears based on timing

**Type:** Direct pixel modification (per-frame, additive)

**Motion Type:**
- ❌ Not camera movement
- ❌ Not object movement
- ❌ Not light movement
- ✅ **Direct pixel modification** (text rendering)

---

### Standard Motion Summary

| Component | Type | What Moves | Pixel Modification |
|-----------|------|------------|-------------------|
| **Scale & Pad** | Setup | None | ✅ Yes (one-time resize) |
| **Zoom Filter** | Camera | Camera (zoom) | ❌ No (transformation) |
| **Text Overlays** | Overlay | None | ✅ Yes (text rendering) |

**Key Point:** The zoom effect is a **camera simulation** - it doesn't move objects or modify pixels. It uses **affine transformations** to create the illusion of camera movement.

---

## 2. HUMAN-SAFE FAKE MOTION (Images with Faces)

**File:** `backend/human_video_service.py` → `create_human_safe_video()`

### Face Detection First

```python
face_info = get_face_region_info(image_path)  # MediaPipe detection
face_bbox = face_info["bbox"]  # (x, y, width, height)
face_mask = face_info["mask"]  # Binary mask with feathering
```

**What it does:**
- Uses **MediaPipe Face Detection** to locate human faces
- Creates a **face mask** with soft edges (feathering)
- Face region is identified but **not directly protected** in FFmpeg (motion is kept minimal instead)

**Type:** Detection (pre-processing)

---

### Template 1: Confident Intro

```python
zoom_filter = "zoompan=z='min(zoom+0.0008,1.04)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
```

**What it does:**
- **Camera movement**: Very slow zoom (1.0 → 1.04, vs 1.08 in standard)
- **Motion is minimal** to prevent face deformation
- Face remains pixel-identical due to subtle motion

**Type:** Camera transformation (very subtle)

**Motion Type:**
- ✅ **Camera Movement** (slow zoom)
- ❌ Not object movement
- ❌ Not light movement
- ❌ Not pixel modification

---

### Template 2: Style Flow

```python
pan_filter = "crop=iw:ih:if(gte(t,0),1.5*t,0):if(gte(t,0),1.0*t,0)"
```

**What it does:**
- **Camera movement**: Diagonal pan (horizontal + vertical)
- Very subtle movement (1.5px/frame horizontal, 1px/frame vertical)
- Creates parallax effect

**Type:** Camera transformation (pan)

**Motion Type:**
- ✅ **Camera Movement** (pan)
- ❌ Not object movement
- ❌ Not light movement
- ❌ Not pixel modification

---

### Template 3: Detail & Value

```python
zoom_in = "zoompan=z='if(lt(t,2.5),min(zoom+0.0015,1.10),max(zoom-0.001,1.0))':d=150:..."
```

**What it does:**
- **Camera movement**: Zoom in (0-2.5s) then pull back (2.5-5s)
- Creates focus on product detail, then reveal full scene

**Type:** Camera transformation (zoom in/out)

**Motion Type:**
- ✅ **Camera Movement** (zoom in → zoom out)
- ❌ Not object movement
- ❌ Not light movement
- ❌ Not pixel modification

---

### Human-Safe Motion Summary

| Template | Camera Movement | Object Movement | Light Movement | Pixel Modification |
|----------|----------------|-----------------|----------------|-------------------|
| **Confident Intro** | ✅ Slow zoom (1.04x) | ❌ No | ❌ No | ❌ No |
| **Style Flow** | ✅ Diagonal pan | ❌ No | ❌ No | ❌ No |
| **Detail & Value** | ✅ Zoom in/out | ❌ No | ❌ No | ❌ No |

**Key Point:** All human-safe motion is **camera-only**. No object movement, no light changes, no pixel modification (except initial scale). Face protection is achieved through **minimal motion values**.

---

## 3. WHAT MOVES WHAT?

### Camera Movement ✅
- **Standard:** Zoom (1.0 → 1.08) via `zoompan` filter
- **Human-Safe:** 
  - Zoom (1.0 → 1.04) - Template 1
  - Pan (diagonal) - Template 2
  - Zoom in/out - Template 3

**How:** FFmpeg `zoompan` and `crop` filters apply **affine transformations** (scaling, translation) to simulate camera movement. The source image pixels are **sampled and transformed**, not modified.

---

### Light Movement ❌
**Currently NOT implemented.**

The code mentions "light sweep" in comments, but the actual FFmpeg filters don't include brightness/lighting effects. To add light movement, you would need:
- `geq` filter for brightness manipulation
- `curves` filter for color grading
- `eq` filter for exposure changes

**Example (not currently used):**
```python
light_sweep = "geq=lum='lum(X,Y)+if(between(t,1,4),20*sin(2*PI*(X/W+t/2)),0))'"
```

---

### Object Movement ❌
**Currently NOT implemented.**

No filters move objects within the scene. Objects remain static - only the camera view changes.

To add object movement, you would need:
- `perspective` filter for 3D rotation
- `warp` filters for deformation
- `rotate` filter for object rotation

---

### Shadow Movement ❌
**Currently NOT implemented.**

No shadow effects are applied. The code mentions "shadow movement" in comments, but no actual shadow filters are used.

To add shadows, you would need:
- `geq` filter to create shadow regions
- `blend` filter to composite shadows
- Custom shader effects

---

## 4. PIXEL MODIFICATION BREAKDOWN

### Direct Pixel Modification ✅

1. **Initial Scale & Pad** (one-time, per frame)
   - Resizes image to target resolution
   - Adds black padding if needed
   - **Modifies:** All pixels (resize operation)

2. **Text Overlays** (per-frame)
   - Renders text on video frames
   - Uses alpha blending
   - **Modifies:** Pixels where text is rendered

### Transformation (No Direct Pixel Modification) ✅

1. **Zoom/Pan Filters**
   - Uses **affine transformation** (matrix operations)
   - Samples pixels from source image
   - **Does NOT modify source pixels**
   - Creates new frame by **interpolation** (bilinear/bicubic)

2. **Crop Filter**
   - Selects a region from source image
   - **Does NOT modify source pixels**
   - Just changes the viewport

---

## 5. TECHNICAL DETAILS

### FFmpeg Filter Processing Order

```
Frame 0: Source Image
    ↓
[Scale & Pad] → Resized image (720x1280)
    ↓
[Zoom Filter] → Transformed frame (zoom=1.0, center crop)
    ↓
[Text Overlay] → Frame with text rendered
    ↓
Frame 1: Source Image (same)
    ↓
[Scale & Pad] → Resized image (720x1280)
    ↓
[Zoom Filter] → Transformed frame (zoom=1.0015, center crop)
    ↓
[Text Overlay] → Frame with text rendered
    ↓
... (repeats for 150 frames = 5 seconds @ 30fps)
```

### Why Face Protection Works

For human-safe videos, face protection is achieved through:

1. **Minimal Motion Values:**
   - Standard zoom: `0.0015` per frame → 1.08x total
   - Human-safe zoom: `0.0008` per frame → 1.04x total
   - **50% slower motion** = less deformation

2. **Centered Transformations:**
   - All transforms keep subject centered
   - Face region experiences minimal displacement
   - **No warping or distortion** applied

3. **No Per-Pixel Manipulation:**
   - Only affine transformations (zoom/pan)
   - No local warping or mesh deformation
   - Face pixels remain relatively stable

---

## 6. SUMMARY TABLE

| Aspect | Standard Motion | Human-Safe Motion |
|--------|----------------|-------------------|
| **Camera Movement** | ✅ Zoom (1.08x) | ✅ Zoom/Pan (1.04x or pan) |
| **Object Movement** | ❌ No | ❌ No |
| **Light Movement** | ❌ No | ❌ No |
| **Shadow Movement** | ❌ No | ❌ No |
| **Pixel Modification** | ✅ Scale, Text | ✅ Scale only |
| **Face Protection** | ❌ N/A | ✅ Minimal motion |
| **Text Overlays** | ✅ Yes | ❌ No (not implemented) |

---

## 7. KEY INSIGHTS

1. **All motion is camera-based** - no objects or lights actually move
2. **Pixel modification is minimal** - only initial resize and text overlays
3. **Transformations use interpolation** - source pixels are sampled, not modified
4. **Face protection = minimal motion** - slower zoom/pan prevents deformation
5. **No AI/ML involved** - pure FFmpeg filter operations

---

## 8. POTENTIAL ENHANCEMENTS

To add more motion effects:

1. **Light Movement:**
   ```python
   light_filter = "geq=lum='lum(X,Y)+20*sin(2*PI*t)'"
   ```

2. **Shadow Movement:**
   ```python
   shadow_filter = "geq=lum='lum(X,Y)-if(between(Y,h*0.7,h),30,0)'"
   ```

3. **Object Rotation:**
   ```python
   rotate_filter = "rotate=PI/180*sin(2*PI*t/5)"
   ```

4. **Fabric Movement:**
   ```python
   warp_filter = "perspective=0:0:W:0:0:H:W:H:W*0.98:0:H*0.98"
   ```

These would require adding to the filter chain and testing for face safety.
