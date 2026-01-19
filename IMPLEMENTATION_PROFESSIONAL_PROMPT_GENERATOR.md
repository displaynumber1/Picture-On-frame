# Implementation: Professional Prompt Generator

## ✅ Files Created/Modified

### 1. New Files Created

#### `frontend/services/translator.ts`
- **Purpose:** Professional translation mapping from Indonesian to detailed English photographic descriptions
- **Content:**
  - `MAPPING` object with detailed English descriptions for all options
  - `translateToEnglish()` function for mapping lookup
  - Covers: Model Types, Categories, Backgrounds, Styles, Lighting, Camera Angles, Interactions, Poses, Aspect Ratios

#### `frontend/services/promptGenerator.ts`
- **Purpose:** Professional prompt generation with natural language synthesis
- **Content:**
  - `generateProfessionalPrompt()` function - main prompt generator
  - `getDefaultFalAIConfig()` function - Fal.ai API configuration
  - `TECHNICAL_REALISM_WRAPPER` - Phase One camera, skin pores, fabric texture specifications
  - `REFERENCE_IMAGE_INSTRUCTIONS` - Instructions for LoRA/edit models

### 2. Modified Files

#### `frontend/services/falService.ts`
- **Modified:** `buildPromptFromOptions()` function
- **Change:** Now delegates to `generateProfessionalPrompt()` for backward compatibility
- **Status:** Deprecated but kept for compatibility

## 📋 Key Features Implemented

### 1. Natural Language Synthesis
- ✅ Flowing descriptive sentences (not comma-separated lists)
- ✅ Professional photographic language
- ✅ Natural sentence structure optimized for FLUX models

### 2. Technical Realism Wrapper
- ✅ Phase One medium format camera specification
- ✅ Visible skin pores mention
- ✅ Authentic fabric textures
- ✅ No plastic skin appearance
- ✅ Extremely detailed skin shaders
- ✅ Fabric micro-textures

### 3. Reference Image Instructions
- ✅ Instructions for LoRA/edit models
- ✅ Maintain facial features consistency
- ✅ Preserve product design details
- ✅ Do not deviate from reference shapes/textures

### 4. Visual Weighting
- ✅ Hyper-realistic focus on facial features
- ✅ Extremely detailed skin shaders
- ✅ Hyper-realistic focus on category details
- ✅ Material texture emphasis

### 5. Professional Translation Mapping
- ✅ Detailed English descriptions (not just word translations)
- ✅ Photographic terminology
- ✅ Professional language
- ✅ Covers all option categories

### 6. Fal.ai API Configuration
- ✅ Default configuration object
- ✅ `image_strength: 0.65` (optimal for reference consistency)
- ✅ `num_inference_steps: 7`
- ✅ `guidance_scale: 4.0` (between 3.5-4.5)
- ✅ `image_size` mapping based on aspect ratio

## 🔧 Function Structure

### `generateProfessionalPrompt(options: GenerationOptions): Promise<string>`

**Structure:**
1. Style (Photographic Style)
2. Content Type & Model
3. Pose
4. Interaction
5. Background
6. Lighting
7. Camera Angle
8. Additional Prompt
9. Visual Weighting (face & texture emphasis)
10. Reference Image Instructions
11. Technical Realism Wrapper
12. Aspect Ratio

**Output:** Natural flowing paragraph optimized for FLUX models

### `getDefaultFalAIConfig(aspectRatio?: string): FalAIConfig`

**Returns:**
```typescript
{
  model: 'fal-ai/flux-2/lora/edit',
  image_strength: 0.65,
  num_inference_steps: 7,
  guidance_scale: 4.0,
  image_size: 'square_hd' | 'portrait_4_3' | 'landscape_16_9' | ...
}
```

## 📝 Example Output

### Input Options:
- Style: "Editorial"
- Content Type: "Model"
- Model Type: "Wanita"
- Category: "Fashion"
- Pose: "Berdiri santai memegang produk"
- Interaction: "Pegang 1 Tangan Wanita"
- Background: "Studio"
- Lighting: "Natural Daylight"
- Camera Angle: "Eye-Level"
- Aspect Ratio: "1:1"

### Output Prompt:
```
A professional editorial fashion photography featuring a female model in fashion, standing casually while holding the product, displaying relaxed posture and natural interaction. Female model naturally holding the product with one hand, showing elegant grip and graceful presentation. Set against clean professional studio backdrop with seamless white or gray background. Illuminated with natural daylight illumination creating soft, even lighting with authentic color temperature. Captured from eye-level camera angle creating natural, relatable perspective. With hyper-realistic focus on facial features and extremely detailed skin shaders. With hyper-realistic focus on fashion photography details and material textures. Strictly maintain the facial features from the reference face image and the specific design details of the product images. Do not deviate from the reference shapes, textures, and proportions. Preserve exact product specifications and model facial characteristics throughout the generation. Photographed with Phase One medium format camera system, capturing hyper-realistic detail with visible skin pores, authentic fabric textures, and natural material qualities. No plastic skin appearance, no artificial smoothness - pure photographic realism with extremely detailed skin shaders and fabric micro-textures. Composed in 1:1 square format.
```

## ✅ Special Handling

### 1. "Upload Background"
- Replaces with: "seamlessly integrated into the provided custom background image"

### 2. "Tanpa Interaksi"
- Removed from prompt (not included in final output)

### 3. "Prompt Kustom" / "Custom"
- Uses custom prompt field instead
- Falls back to empty if no custom prompt

### 4. Non Model Content Type
- Focuses on product photography
- Removes model-related descriptions
- Emphasizes product details

## 🔄 Integration

### Backward Compatibility
- `buildPromptFromOptions()` still works
- Delegates to `generateProfessionalPrompt()`
- No breaking changes to existing code

### Next Steps
1. ✅ Files created
2. ⏳ Test with real options
3. ⏳ Verify prompt quality
4. ⏳ Update App.tsx if needed (optional - backward compatible)

---

**Implementation complete! Files created and ready for testing.**
