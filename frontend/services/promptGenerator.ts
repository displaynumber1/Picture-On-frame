/**
 * Professional Prompt Generator
 * 
 * ⚠️ DEPRECATED FOR FLUX-2 USAGE ⚠️
 * 
 * This generator is for NON-Flux engines only (generic, creative, legacy models).
 * 
 * DO NOT use this for Flux-2 generation.
 * Flux-2 must use fluxPromptGenerator.ts (generateFluxPromptV2) exclusively.
 * 
 * This generator creates natural-language, paragraph-style prompts suitable for
 * creative models that benefit from descriptive text rather than constraint-driven clauses.
 */

import { GenerationOptions } from '../types';
import { translateToEnglish } from './translator';
import { translateTextToEnglish } from './falService';

/**
 * Technical Realism Wrapper
 * Ensures professional catalog photography quality
 */
const TECHNICAL_REALISM_WRAPPER = `Professional catalog photography with natural skin texture showing subtle imperfections. Realistic fabric and material appearance. No beauty retouching, no artificial smoothing, no CGI or plastic look. Commercial-ready, honest photography.`;

/**
 * Lifestyle Realism Wrapper
 * For lifestyle mode: emphasizes natural usage, real environment, and honest photography
 * Only used when lifestyle mode is active
 */
const LIFESTYLE_REALISM_WRAPPER = `Natural everyday context with realistic product usage. Real environment with practical application. Honest photography showing product in daily use. Product remains visually dominant with clear visibility and detail.`;

/**
 * Reference Image Instructions
 * For LoRA/edit models to maintain consistency with reference images
 * 
 * NOTE: Flux-2 specific constraints (static background, scale preservation, shadow grounding)
 * are NOT included here. Those belong exclusively in fluxPromptGenerator.ts.
 */
const REFERENCE_IMAGE_INSTRUCTIONS_BASE = `Maintain design details from the reference images. Preserve product specifications. Combine reference images with consistent relationships between face, products, and background. Ensure natural composition.`;

/**
 * Reference Image Order Instructions
 * Specifies the order of reference images to prevent confusion
 * Order: Ref 1 (Main Product) → Ref 2 (Optional Product) → Ref 3 (Face) → Ref 4 (Background)
 * Includes explicit instructions for proportional integration
 */
const REFERENCE_IMAGE_ORDER_INSTRUCTIONS = (hasFace: boolean, hasProducts: boolean, hasBackground: boolean) => {
  const parts: string[] = [];
  
  // Ref 1: "The Main" - Main Product Image (always first if products exist)
  if (hasProducts) {
    parts.push(`Reference 1 is "The Main" product image. Maintain product design, colors, textures, and proportions from this primary reference. Use this as the primary product reference and maintain its scale relative to other elements.`);
  }
  
  // Ref 2: "The Optional" - Optional Product Image (if multiple products)
  if (hasProducts) {
    parts.push(`Reference 2 is "The Optional" product image (if provided). Use this as secondary product reference for additional details or variations. Maintain proportional relationship between Reference 1 and Reference 2 products.`);
  }
  
  // Ref 3: "The Face" - Face Image (if provided)
  if (hasFace) {
    parts.push(`Reference 3 is "The Face" image. Maintain facial features, skin tone, facial structure, and facial proportions from this reference. Integrate the face proportionally with the product(s). Ensure the face size matches the product scale realistically. Position the face naturally relative to the product(s) with correct perspective and scale.`);
  }
  
  // Ref 4: "The Background Environment" - Background Image (if provided, always last)
  // NOTE: Flux-2 specific constraints (static environment, scale preservation, shadow grounding)
  // are NOT included here. Use fluxPromptGenerator.ts for Flux-2.
  if (hasBackground) {
    parts.push(`Reference 4 is "The Background Environment". Use this background reference. Place the subject (face and/or products) in this background with proper integration and color matching.`);
  }
  
  // Add integration instructions if multiple references exist
  if ((hasFace && hasProducts) || (hasProducts && hasBackground) || (hasFace && hasBackground)) {
    parts.push(`Integrate all reference images proportionally. Maintain correct scale relationships between face, product(s), and background. Ensure all elements appear naturally composed together with realistic proportions, proper perspective, and seamless integration.`);
  }
  
  return parts.join('. ') + (parts.length > 0 ? '.' : '');
};

/**
 * Generate professional, natural-language prompt from user options
 * 
 * ⚠️ NOT FOR FLUX-2 ⚠️
 * 
 * This function creates flowing descriptive text for generic/creative models.
 * For Flux-2, use fluxPromptGenerator.ts (generateFluxPromptV2) instead.
 * 
 * @param options - User's generation options from frontend
 * @param hasFaceImage - Whether face image is provided (for reference order)
 * @param hasProductImages - Whether product images are provided (for reference order)
 * @param hasBackgroundImage - Whether background image is provided (for reference order)
 * @returns Professional English prompt string
 */
export async function generateProfessionalPrompt(
  options: GenerationOptions,
  hasFaceImage: boolean = false,
  hasProductImages: boolean = false,
  hasBackgroundImage: boolean = false
): Promise<string> {
  const sentences: string[] = [];
  
  // ========== LIFESTYLE MODE DETECTION ==========
  const isLifestyleMode = options.style === 'Lifestyle';

  // ========== STYLE (Photographic Style) ==========
  if (options.style && options.style !== 'Custom') {
    const styleDesc = translateToEnglish(options.style);
    if (styleDesc && styleDesc !== options.style) {
      sentences.push(`A professional ${styleDesc.toLowerCase()}`);
    }
  } else if (options.customStylePrompt) {
    const translatedStyle = await translateTextToEnglish(options.customStylePrompt);
    if (translatedStyle) {
      sentences.push(`A professional ${translatedStyle.toLowerCase()}`);
    }
  } else {
    sentences.push('A professional photography');
  }

  // ========== CONTENT TYPE & MODEL ==========
  if (options.contentType === 'Non Model') {
    // Product-focused photography (still life / inanimate objects)
    // NO human instructions should be included
    if (options.category) {
      const categoryDesc = translateToEnglish(options.category);
      sentences.push(`featuring ${categoryDesc.toLowerCase()} products as inanimate objects`);
    } else {
      sentences.push('featuring products as inanimate objects');
    }
  } else {
    // Model-focused photography
    if (options.modelType) {
      const modelDesc = translateToEnglish(options.modelType);
      sentences.push(`featuring a ${modelDesc}`);
    }

    if (options.category) {
      const categoryDesc = translateToEnglish(options.category);
      sentences.push(`in ${categoryDesc.toLowerCase()}`);
    }

    // ========== POSE (Face Instructions from Step 2) - ONLY for Model ==========
    // Include pose/face instructions when contentType is 'Model'
    // In lifestyle mode, adjust for natural, relaxed posture
    if (options.pose && options.pose !== 'Prompt Kustom' && options.pose !== 'Prompt Custom (bisa diedit)') {
      const poseDesc = translateToEnglish(options.pose);
      if (poseDesc && poseDesc !== options.pose) {
        if (isLifestyleMode) {
          // Lifestyle mode: emphasize natural, relaxed posture with product visibility
          sentences.push(`${poseDesc.toLowerCase()}, natural everyday posture with clear product visibility`);
        } else {
          sentences.push(`${poseDesc.toLowerCase()}`);
        }
      }
    } else if (options.customPosePrompt) {
      const translatedPose = await translateTextToEnglish(options.customPosePrompt);
      if (translatedPose) {
        if (isLifestyleMode) {
          sentences.push(`${translatedPose.toLowerCase()}, natural everyday posture with clear product visibility`);
        } else {
          sentences.push(`${translatedPose.toLowerCase()}`);
        }
      }
    }
  }

  // ========== INTERACTION ==========
  if (options.interactionType && options.interactionType !== 'Tanpa Interaksi') {
    const interactionDesc = translateToEnglish(options.interactionType);
    if (interactionDesc && interactionDesc !== options.interactionType) {
      if (isLifestyleMode) {
        // Lifestyle mode: emphasize light, realistic interaction with practical usage
        sentences.push(`${interactionDesc.toLowerCase()}, showing practical product usage in natural context`);
      } else {
        sentences.push(`${interactionDesc.toLowerCase()}`);
      }
    }
  } else if (options.interactionType === 'Tanpa Interaksi') {
    // ========== PRODUCT PLACEMENT (Step 5) - When No Interaction ==========
    // Add product placement instructions based on background selection
    if (options.background && options.background !== 'Upload Background' && options.background !== 'Warna (Custom)') {
      const backgroundDesc = translateToEnglish(options.background);
      if (backgroundDesc && backgroundDesc !== options.background) {
        // Determine placement based on background type
        if (backgroundDesc.toLowerCase().includes('meja') || backgroundDesc.toLowerCase().includes('table')) {
          sentences.push('product placed on table surface');
        } else if (backgroundDesc.toLowerCase().includes('lantai') || backgroundDesc.toLowerCase().includes('floor')) {
          sentences.push('product placed on floor surface');
        } else {
          sentences.push(`product placed on ${backgroundDesc.toLowerCase()} surface`);
        }
      }
    } else if (options.background === 'Upload Background') {
      // Will be handled in background section below
      sentences.push('product placed on the ground/surface of the uploaded background');
    } else {
      // Default placement for "Tanpa Interaksi"
      sentences.push('product placed on table or floor surface');
    }
  }

  // ========== BACKGROUND ==========
  if (options.background && options.background !== 'Upload Background' && options.background !== 'Warna (Custom)') {
    const backgroundDesc = translateToEnglish(options.background);
    if (backgroundDesc && backgroundDesc !== options.background) {
      if (isLifestyleMode) {
        // Lifestyle mode: emphasize natural everyday context
        const bgLower = backgroundDesc.toLowerCase();
        if (bgLower.includes('home') || bgLower.includes('kamar') || bgLower.includes('interior')) {
          sentences.push(`set in natural home environment with ${bgLower}`);
        } else if (bgLower.includes('jalan') || bgLower.includes('street') || bgLower.includes('outdoor')) {
          sentences.push(`set in natural street environment with ${bgLower}`);
        } else if (bgLower.includes('cafe') || bgLower.includes('mall')) {
          sentences.push(`set in natural everyday setting with ${bgLower}`);
        } else {
          sentences.push(`set against ${bgLower}, natural everyday context`);
        }
      } else {
        sentences.push(`set against ${backgroundDesc.toLowerCase()}`);
      }
    }
  } else if (options.background === 'Upload Background') {
    // ========== UPLOAD BACKGROUND INSTRUCTIONS (Step 7) ==========
    // Instructions for using uploaded background as static reference
    sentences.push('integrated into the provided custom background image');
    sentences.push('use the last reference image as a static background environment');
    sentences.push('place the subject on the ground/surface of the uploaded background with shadow integration and color matching');
    sentences.push('ensure realistic shadow casting from subject onto background surface');
    sentences.push('match color temperature and lighting conditions between subject and uploaded background');
  } else if (options.customBackgroundPrompt) {
    const translatedBg = await translateTextToEnglish(options.customBackgroundPrompt);
    if (translatedBg) {
      sentences.push(`set against ${translatedBg.toLowerCase()}`);
    }
  }

  // ========== LIGHTING ==========
  if (options.lighting && options.lighting !== 'Custom') {
    const lightingDesc = translateToEnglish(options.lighting);
    if (lightingDesc && lightingDesc !== options.lighting) {
      if (isLifestyleMode) {
        // Lifestyle mode: prefer realistic daylight or soft indoor lighting
        const lightLower = lightingDesc.toLowerCase();
        if (lightLower.includes('daylight') || lightLower.includes('natural') || lightLower.includes('window')) {
          sentences.push(`illuminated with ${lightLower}, realistic everyday lighting`);
        } else {
          sentences.push(`illuminated with ${lightLower}`);
        }
      } else {
        sentences.push(`illuminated with ${lightingDesc.toLowerCase()}`);
      }
    }
  } else if (options.customLightingPrompt) {
    const translatedLighting = await translateTextToEnglish(options.customLightingPrompt);
    if (translatedLighting) {
      if (isLifestyleMode) {
        sentences.push(`illuminated with ${translatedLighting.toLowerCase()}, realistic everyday lighting`);
      } else {
        sentences.push(`illuminated with ${translatedLighting.toLowerCase()}`);
      }
    }
  } else if (isLifestyleMode) {
    // Default lifestyle lighting if not specified
    sentences.push('illuminated with realistic daylight or soft indoor lighting');
  }

  // ========== CAMERA ANGLE ==========
  if (options.cameraAngle) {
    const angleDesc = translateToEnglish(options.cameraAngle);
    if (angleDesc && angleDesc !== options.cameraAngle) {
      sentences.push(`captured from ${angleDesc.toLowerCase()}`);
    }
  }

  // ========== ADDITIONAL PROMPT ==========
  if (options.additionalPrompt) {
    const translatedAdditional = await translateTextToEnglish(options.additionalPrompt);
    if (translatedAdditional) {
      sentences.push(translatedAdditional);
    }
  }

  // ========== VISUAL WEIGHTING ==========
  // Add emphasis on face and product texture for FLUX models
  if (options.contentType === 'Model') {
    if (isLifestyleMode) {
      sentences.push('with natural facial appearance and realistic skin texture, neutral expression');
    } else {
      sentences.push('with natural facial appearance and realistic skin texture');
    }
  }
  
  if (options.category) {
    const categoryDesc = translateToEnglish(options.category);
    if (isLifestyleMode) {
      sentences.push(`with accurate material detail on the product, product remains visually dominant`);
    } else {
      sentences.push(`with accurate material detail on the product`);
    }
  }

  // ========== REFERENCE IMAGE INSTRUCTIONS ==========
  // Add base reference image instructions
  sentences.push(REFERENCE_IMAGE_INSTRUCTIONS_BASE);

  // ========== REFERENCE IMAGE ORDER INSTRUCTIONS ==========
  // Specify image order to prevent confusion (Reference 1, 2, 3)
  const orderInstructions = REFERENCE_IMAGE_ORDER_INSTRUCTIONS(hasFaceImage, hasProductImages, hasBackgroundImage);
  sentences.push(orderInstructions);

  // ========== TECHNICAL REALISM WRAPPER ==========
  // Add technical specifications at the end
  // Use lifestyle wrapper if lifestyle mode is active, otherwise use catalog wrapper
  if (isLifestyleMode) {
    sentences.push(LIFESTYLE_REALISM_WRAPPER);
  } else {
    sentences.push(TECHNICAL_REALISM_WRAPPER);
  }

  // ========== ASPECT RATIO ==========
  // Add aspect ratio specification
  if (options.aspectRatio) {
    const ratioDesc = translateToEnglish(options.aspectRatio);
    if (ratioDesc && ratioDesc !== options.aspectRatio) {
      sentences.push(`Composed in ${ratioDesc}.`);
    }
  }

  // Combine all sentences into natural flowing paragraph
  let prompt = sentences
    .filter(s => s.trim().length > 0) // Remove empty sentences
    .join('. ') // Join with periods and spaces
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim();

  // Ensure prompt ends with period
  if (prompt && !prompt.endsWith('.')) {
    prompt += '.';
  }

  return prompt;
}

/**
 * Default fal API Configuration
 * Based on flux-2/lora/edit model requirements
 */
export interface FalAIConfig {
  model: string;
  image_strength: number;
  num_inference_steps: number;
  guidance_scale: number;
  image_size?: string; // Based on aspect ratio
}

/**
 * Get default fal configuration
 * @param aspectRatio - User's selected aspect ratio
 * @returns fal API configuration object
 */
export function getDefaultFalAIConfig(aspectRatio?: string): FalAIConfig {
  // Map aspect ratios to image sizes
  const aspectRatioToSize: Record<string, string> = {
    '1:1': 'square_hd',
    '1:1 (Square)': 'square_hd',
    '4:5': 'portrait_4_3',
    '4:5 (Portrait)': 'portrait_4_3',
    '3:4': 'portrait_4_3',
    '3:4 (Portrait)': 'portrait_4_3',
    '2:3': 'portrait_4_3',
    '2:3 (Portrait)': 'portrait_4_3',
    '16:9': 'landscape_16_9',
    '16:9 (Landscape)': 'landscape_16_9',
    '4:3': 'landscape_4_3',
    '9:16': 'portrait_9_16',
    '9:16 (Story)': 'portrait_9_16',
  };

  return {
    model: 'fal-ai/flux-2/lora/edit',
    image_strength: 0.55, // Optimal for maintaining reference image consistency
    num_inference_steps: 20, // Generation with good quality
    guidance_scale: 5.0, // Balanced prompt adherence
    image_size: aspectRatio ? aspectRatioToSize[aspectRatio] || 'square_hd' : 'square_hd',
  };
}
