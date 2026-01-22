/**
 * LAYER 4 - Flux-2 Prompt Generator
 * 
 * ⚠️ FLUX-2 EXCLUSIVE ⚠️
 * 
 * This is the SINGLE SOURCE OF TRUTH for Flux-2 prompt generation.
 * 
 * DO NOT use promptGenerator.ts for Flux-2.
 * DO NOT add natural-language paragraphs or realism wrappers from other generators.
 * 
 * Flux-2 prompts must be:
 * - Clause-based and constraint-driven
 * - Concise and non-redundant
 * - Optimized for photorealistic ecommerce catalog quality
 * 
 * Reference image handling (scale, shadow, static background) exists ONLY here for Flux-2.
 */

import { NormalizedGenerationInput } from './normalization';
import { PhotographyMode } from './modeResolver';
import { translateToEnglish } from './translator';

export interface FluxPromptOutput {
  positivePrompt: string;
  negativePrompt: string;
}

export interface FluxPromptOutputV2 {
  positivePrompt: string;
  negativePrompt: string;
  metadata: {
    engine: string;
    version: string;
  };
}

/**
 * Default negative prompt for Flux-2
 * Includes compositional hallucination prevention and fabric constraints
 */
const DEFAULT_NEGATIVE_PROMPT = 'plastic skin, artificial smoothness, airbrushed, CGI, 3d render, cartoon, anime, illustration, sketch, blurry, low resolution, distorted hands, extra fingers, mutated fingers, fused fingers, deformed anatomy, bad proportions, double heads, cloned face, unnatural eyes, watermark, text, signature, grainy, low quality, overexposed, messy background elements, floating products, disconnected limbs, scale mismatch, incorrect perspective, unrealistic shadows, floating objects, composition errors, hallucinated elements, added objects, removed objects, perspective distortion, fabric smoothing, fabric blur, plastic fabric, synthetic texture, over-smoothed cloth, washed fabric detail';

/**
 * Fixed negative prompt for V2 (simplified, focused)
 * Includes fabric constraints
 */
const FIXED_NEGATIVE_PROMPT_V2 = 'cartoon, anime, illustration, cgi, plastic skin, distorted anatomy, extra fingers, floating objects, unrealistic shadows, oversharpening, fabric smoothing, fabric blur, plastic fabric, synthetic texture, over-smoothed cloth, washed fabric detail, mannequin, manikin, doll-like, statue-like, rigid pose, stiff pose, lifeless, robotic, artificial human, fake human, wax figure, museum display, posed mannequin, store display mannequin, unrealistic pose, unnatural posture';

/**
 * Generate Flux-2 compatible prompt (V1 - legacy)
 * 
 * ⚠️ DEPRECATED: Use generateFluxPromptV2 instead
 * 
 * This function is kept for backward compatibility.
 * New code should use generateFluxPromptV2 which follows strict structure.
 */
export function generateFluxPrompt(
  normalizedInput: NormalizedGenerationInput,
  resolvedMode: PhotographyMode
): FluxPromptOutput {
  const clauses: string[] = [];
  
  // ========== STYLE ==========
  if (normalizedInput.style && normalizedInput.style !== 'Custom') {
    const styleDesc = translateToEnglish(normalizedInput.style);
    if (styleDesc && styleDesc !== normalizedInput.style) {
      clauses.push(`professional ${styleDesc.toLowerCase()}`);
    }
  } else if (normalizedInput.customStylePrompt) {
    clauses.push(`professional ${normalizedInput.customStylePrompt.toLowerCase()}`);
  } else {
    clauses.push('professional photography');
  }
  
  // ========== SUBJECT ==========
  if (normalizedInput.isProductOnly) {
    // Product-only photography
    if (normalizedInput.category) {
      const categoryDesc = translateToEnglish(normalizedInput.category);
      clauses.push(`${categoryDesc.toLowerCase()} product`);
    } else {
      clauses.push('product');
    }
  } else if (normalizedInput.hasHuman) {
    // Human subject
    if (normalizedInput.modelType) {
      const modelDesc = translateToEnglish(normalizedInput.modelType);
      clauses.push(`${modelDesc}`);
    }
    
    if (normalizedInput.category) {
      const categoryDesc = translateToEnglish(normalizedInput.category);
      clauses.push(`${categoryDesc.toLowerCase()} category`);
    }
    
    // Pose (only for human subjects)
    if (normalizedInput.pose && normalizedInput.pose !== 'Prompt Kustom' && normalizedInput.pose !== 'Prompt Custom (bisa diedit)') {
      const poseDesc = translateToEnglish(normalizedInput.pose);
      if (poseDesc && poseDesc !== normalizedInput.pose) {
        if (resolvedMode === 'lifestyle') {
          clauses.push(`${poseDesc.toLowerCase()}, natural posture`);
        } else {
          clauses.push(poseDesc.toLowerCase());
        }
      }
    } else if (normalizedInput.customPosePrompt) {
      if (resolvedMode === 'lifestyle') {
        clauses.push(`${normalizedInput.customPosePrompt.toLowerCase()}, natural posture`);
      } else {
        clauses.push(normalizedInput.customPosePrompt.toLowerCase());
      }
    }
  }
  
  // ========== INTERACTION ==========
  if (normalizedInput.interactionType && normalizedInput.interactionType !== 'Tanpa Interaksi') {
    const interactionDesc = translateToEnglish(normalizedInput.interactionType);
    if (interactionDesc && interactionDesc !== normalizedInput.interactionType) {
      if (resolvedMode === 'lifestyle') {
        clauses.push(`${interactionDesc.toLowerCase()}, practical usage`);
      } else {
        clauses.push(interactionDesc.toLowerCase());
      }
    }
  } else if (normalizedInput.interactionType === 'Tanpa Interaksi' && normalizedInput.isProductOnly) {
    clauses.push('product placement');
  }
  
  // ========== BACKGROUND ==========
  if (normalizedInput.useBackground) {
    // Background image exists - treat as STATIC ENVIRONMENT (not inspiration)
    // Enforce scale preservation and shadow grounding
    clauses.push('static background environment, subject composited onto uploaded background');
    clauses.push('preserve subject scale relative to background, maintain correct perspective and proportions');
    clauses.push('realistic shadow grounding, subject casts shadow onto background surface, shadow matches lighting direction');
    clauses.push('subject placed on ground/surface of background with shadow integration and color matching');
    clauses.push('background remains unchanged, static reference, no compositional changes');
  } else if (normalizedInput.customBackgroundPrompt) {
    clauses.push(`background: ${normalizedInput.customBackgroundPrompt.toLowerCase()}`);
  } else if (normalizedInput.category && resolvedMode === 'lifestyle') {
    // Use category-appropriate background hint if no explicit background (lifestyle only)
    const categoryDesc = translateToEnglish(normalizedInput.category);
    clauses.push(`natural everyday setting, ${categoryDesc.toLowerCase()} context`);
  }
  
  // ========== LIGHTING ==========
  if (normalizedInput.lighting && normalizedInput.lighting !== 'Custom') {
    const lightingDesc = translateToEnglish(normalizedInput.lighting);
    if (lightingDesc && lightingDesc !== normalizedInput.lighting) {
      if (resolvedMode === 'lifestyle') {
        const lightLower = lightingDesc.toLowerCase();
        if (lightLower.includes('daylight') || lightLower.includes('natural') || lightLower.includes('window')) {
          clauses.push(`lighting: ${lightLower}, realistic everyday`);
        } else {
          clauses.push(`lighting: ${lightLower}`);
        }
      } else {
        clauses.push(`lighting: ${lightingDesc.toLowerCase()}`);
      }
    }
  } else if (normalizedInput.customLightingPrompt) {
    if (resolvedMode === 'lifestyle') {
      clauses.push(`lighting: ${normalizedInput.customLightingPrompt.toLowerCase()}, realistic everyday`);
    } else {
      clauses.push(`lighting: ${normalizedInput.customLightingPrompt.toLowerCase()}`);
    }
  } else if (resolvedMode === 'lifestyle') {
    clauses.push('lighting: realistic daylight or soft indoor');
  }
  
  // ========== CAMERA ANGLE ==========
  if (normalizedInput.cameraAngle) {
    const angleDesc = translateToEnglish(normalizedInput.cameraAngle);
    if (angleDesc && angleDesc !== normalizedInput.cameraAngle) {
      clauses.push(`angle: ${angleDesc.toLowerCase()}`);
    }
  }
  
  // ========== REFERENCE IMAGE INSTRUCTIONS ==========
  // Favor image-to-image fidelity, avoid compositional hallucination
  if (normalizedInput.hasSubject || normalizedInput.hasOptionalSubject || normalizedInput.hasHuman || normalizedInput.useBackground) {
    const refParts: string[] = [];
    
    if (normalizedInput.hasSubject || normalizedInput.hasOptionalSubject) {
      refParts.push('strict fidelity to product reference, maintain exact design, colors, textures, proportions');
      // HARD CONSTRAINT: Fabric texture preservation
      clauses.push('preserve original fabric texture');
      clauses.push('visible knit pattern');
      clauses.push('no smoothing on fabric');
      clauses.push('retain original fabric grain');
      clauses.push('fabric texture from reference image');
      // HARD CONSTRAINT: Color drift fix
      clauses.push('preserve original garment color');
      clauses.push('no color reinterpretation');
      clauses.push('no hue shift');
      clauses.push('match reference garment color exactly');
    }
    
    if (normalizedInput.hasHuman) {
      refParts.push('strict fidelity to facial reference, maintain exact features, skin tone, structure');
      // HARD CONSTRAINT: Face identity locked
      clauses.push('face reference is identity locked');
      clauses.push('do not alter facial structure');
      clauses.push('do not beautify face');
      clauses.push('no facial reshaping');
      clauses.push('no face regeneration');
    }
    
    if (normalizedInput.useBackground) {
      refParts.push('background reference as static environment, no compositional changes, preserve scale relationships');
    }
    
    // Scale preservation constraint
    if ((normalizedInput.hasSubject || normalizedInput.hasOptionalSubject) && normalizedInput.useBackground) {
      refParts.push('preserve subject scale relative to background, maintain correct size relationships');
    }
    
    if (refParts.length > 0) {
      clauses.push(`reference fidelity: ${refParts.join(', ')}`);
    }
  }
  
  // ========== REALISM WRAPPER ==========
  // Enforce image-to-image fidelity constraints
  if (resolvedMode === 'lifestyle') {
    clauses.push('natural everyday context, realistic product usage, honest photography, product visually dominant, no compositional hallucination');
  } else {
    clauses.push('catalog photography, natural skin texture with subtle imperfections, realistic fabric and material, no beauty retouching, no artificial smoothing, no CGI, commercial-ready, strict reference fidelity');
  }
  
  // Shadow grounding constraint (always enforce)
  if (normalizedInput.useBackground || normalizedInput.hasSubject || normalizedInput.hasHuman) {
    clauses.push('realistic shadow grounding, subject connected to surface, no floating objects');
  }
  
  // ========== ASPECT RATIO ==========
  if (normalizedInput.aspectRatio) {
    const ratioDesc = translateToEnglish(normalizedInput.aspectRatio);
    if (ratioDesc && ratioDesc !== normalizedInput.aspectRatio) {
      clauses.push(`format: ${ratioDesc}`);
    }
  }
  
  // Combine clauses into dense prompt
  const positivePrompt = clauses
    .filter(c => c.trim().length > 0)
    .join(', ')
    .replace(/\s+/g, ' ')
    .trim() + '.';
  
  return {
    positivePrompt,
    negativePrompt: DEFAULT_NEGATIVE_PROMPT,
  };
}

/**
 * Generate Flux-2 compatible prompt V2 — FINAL (RECOMMENDED)
 * 
 * ⚠️ CRITICAL RULES:
 * - Flux lebih patuh pada constraint daripada kalimat cantik
 * - Jangan gabungkan dengan generator lain
 * - Jangan tambahkan "story / descriptive paragraph"
 * - Clause-based constraints only
 * 
 * RECOMMENDED FLUX PARAMS (WAJIB SELARAS):
 * - image_strength: 0.4 (⚠️ > 0.5 = wajah pasti berubah)
 * - guidance_scale: 7.0 (⚠️ > 6 = fabric mulai "beauty smooth" - but user requested 7)
 * - num_inference_steps: 24
 */
export function generateFluxPromptV2(
  normalizedInput: NormalizedGenerationInput,
  resolvedMode: PhotographyMode
): FluxPromptOutputV2 {
  const clauses: string[] = [];
  const negative: string[] = [];
  
  // Map normalized input to simplified structure
  const subjectType: 'human' | 'product' = normalizedInput.hasHuman ? 'human' : 'product';
  const hasFace = normalizedInput.hasFaceImage; // Check if face reference image is provided
  const garmentType = normalizedInput.category ? translateToEnglish(normalizedInput.category) : undefined;
  const style: 'lifestyle' | 'studio' = resolvedMode === 'lifestyle' ? 'lifestyle' : 'studio';
  
  /* --------------------------------------------------
   * BASE STYLE — FLUX PREFERS CLAUSE CONSTRAINTS
   * -------------------------------------------------- */
  clauses.push(
    'professional ecommerce catalog photography',
    'photorealistic',
    'commercial ready',
    'no stylization',
    'no artistic interpretation'
  );
  
  /* --------------------------------------------------
   * SUBJECT
   * -------------------------------------------------- */
  if (subjectType === 'human') {
    clauses.push(
      'real human model',
      'lifelike appearance',
      'natural body proportion',
      'natural body posture',
      'relaxed natural pose',
      'organic body movement',
      'natural human expression',
      'not mannequin',
      'not doll-like',
      'not statue-like',
      'living person',
      'breathing human',
      'natural skin texture',
      'realistic human anatomy'
    );
  } else {
    if (garmentType) {
      clauses.push(`${garmentType.toLowerCase()} product`);
    } else {
      clauses.push('product');
    }
    const interactionType = normalizedInput.interactionType || '';
    const pose = normalizedInput.pose || '';
    const isNoInteraction = interactionType === 'Tanpa Interaksi';
    const translatedInteraction = translateToEnglish(interactionType);
    const translatedPose = translateToEnglish(pose);

    if (!isNoInteraction && interactionType) {
      clauses.push(translatedInteraction.toLowerCase());
    } else {
      clauses.push('product placement', 'no human model', 'no hands', 'no feet', 'no human body parts');
    }

    if (pose && pose !== 'Prompt Kustom' && pose !== 'Prompt Custom (bisa diedit)') {
      clauses.push(translatedPose.toLowerCase());
    } else if (normalizedInput.customPosePrompt) {
      clauses.push(normalizedInput.customPosePrompt.toLowerCase());
    }

    clauses.push(
      'balanced composition',
      'product clearly visible',
      'full product in frame'
    );

    const isHandInteraction = /tangan/i.test(interactionType);
    const isFootInteraction = /kaki/i.test(interactionType);
    const isSingleHand = /Pegang\s*1/i.test(interactionType);
    const isTwoHands = /Pegang\s*2/i.test(interactionType);
    const categoryKey = (normalizedInput.category || '').toLowerCase();
    const isFootwearCategory = /sandal|sepatu|shoe|footwear/.test(categoryKey);

    if (isHandInteraction) {
      if (/wanita/i.test(interactionType)) {
        clauses.push(
          'female model wearing a high-quality oversized cream cashmere sweater',
          'long sleeves partially covering the hands',
          'soft fabric texture with visible knit patterns',
          'sleeves providing a cozy and warm aesthetic',
          'soft natural lighting catching the fabric fibers'
        );
      }
      clauses.push(
        'reaching from the bottom center of the frame',
        'palm facing upwards to support the product',
        'hand gently cradling the product',
        'hands only',
        'no feet',
        'no legs',
        'no shoes worn on feet',
        'realistic skin texture',
        'natural skin tone',
        'lifelike hand anatomy',
        'visible skin pores',
        'natural finger proportions',
        'no full body',
        'no face visible'
      );
      if (isSingleHand) {
        clauses.push('single hand only', 'one hand holding product');
        negative.push('two hands', 'both hands');
        if (isFootwearCategory) {
          clauses.push(
            'single hand holding a single sandal',
            'clean single-sandal presentation',
            'focus on stitching, logo, and material texture',
            'no second sandal in the hand'
          );
          negative.push('two sandals in one hand', 'crowded grip', 'mismatched shoes');
        }
      } else if (isTwoHands) {
        clauses.push(
          'two hands only',
          'both hands holding product',
          'symmetrical hand placement',
          'both hands visible',
          'balanced grip',
          'gently cradling with both hands',
          'cupping the product',
          'hands meeting at the center',
          'arms reaching from the bottom corners',
          'sleeves covering both wrists',
          'fingers wrapped naturally around the edges',
          'thumbs visible on top'
        );
        negative.push('single hand', 'one hand only');
        if (isFootwearCategory) {
          clauses.push('both hands holding a pair of sandals/shoes', 'matched pair, both shoes visible');
          negative.push('single shoe', 'missing pair', 'mismatched shoes');
        }
      }
      negative.push('extra hands', 'extra fingers', 'extra legs', 'extra feet', 'detached limbs', 'floating limbs');
    }

    if (isFootInteraction) {
      if (/wanita/i.test(interactionType)) {
        clauses.push('straight-leg jeans', 'denim straight-leg pants');
        negative.push('bare legs', 'bare skin legs', 'shorts', 'mini skirt');
      }
      clauses.push(
        'feet only',
        'no hands',
        'realistic skin texture',
        'natural skin tone',
        'lifelike foot anatomy',
        'visible skin pores',
        'natural foot proportions',
        'no full body',
        'no face visible'
      );
      negative.push('extra feet', 'extra legs', 'extra hands', 'detached limbs', 'floating limbs');
    }
  }
  
  /* --------------------------------------------------
   * FACE HARD LOCK (CRITICAL)
   * -------------------------------------------------- */
  if (hasFace) {
    clauses.push(
      'face identity locked',
      'exact facial features from reference image',
      'exact face from reference image',
      'face must match reference image exactly',
      'preserve exact face from reference',
      'maintain face identity from reference image',
      'face unchanged from reference',
      'do not change face',
      'keep face unchanged from reference',
      'exact facial structure from reference',
      'exact eye shape from reference',
      'exact nose shape from reference',
      'exact mouth shape from reference',
      'exact face shape from reference',
      'exact skin tone from reference',
      'exact facial proportions from reference',
      'natural skin texture',
      'realistic skin appearance',
      'visible skin pores',
      'natural skin imperfections',
      'do not alter facial structure',
      'no face regeneration',
      'no beautification',
      'no facial reshaping',
      'no face modification',
      'no face changes',
      'single identity face only',
      'preserve face exactly as in reference',
      'face must be identical to reference image',
      'preserve head covering from reference image',
      'exact head covering color from reference',
      'exact head covering pattern from reference',
      'exact head covering details from reference',
      'do not alter head covering',
      'do not change hijab color',
      'do not change hijab pattern',
      'do not change hijab style',
      'head covering unchanged from reference'
    );
    
    // Adjust pose style based on model type when face reference exists
    const modelType = normalizedInput.modelType || 'Wanita';
    if (normalizedInput.pose) {
      if (modelType === 'Wanita') {
        clauses.push('feminine pose', 'elegant posture', 'graceful stance', 'feminine body language');
        negative.push('masculine pose', 'aggressive posture', 'manly stance');
      } else if (modelType === 'Pria') {
        clauses.push('gentle pose', 'soft posture', 'calm stance', 'gentle body language', 'relaxed masculine pose');
        negative.push('aggressive pose', 'harsh posture', 'intimidating stance', 'feminine pose');
      } else if (modelType === 'Anak LakiLaki') {
        clauses.push('child-like pose', 'playful posture', 'natural child stance', 'youthful body language', 'energetic pose');
        negative.push('adult pose', 'serious posture', 'mature stance');
      } else if (modelType === 'Anak Perempuan') {
        clauses.push('child-like pose', 'playful posture', 'natural child stance', 'youthful body language', 'energetic pose', 'innocent expression');
        negative.push('adult pose', 'serious posture', 'mature stance');
      } else if (modelType === 'Hewan') {
        clauses.push('pet-like pose', 'natural animal posture', 'domesticated animal stance', 'friendly animal pose', 'natural pet behavior');
        clauses.push(
          'balanced composition',
          'subject centered',
          'accessory product clearly visible',
          'pet and accessory equally prominent',
          'clean framing with full product visibility'
        );
        negative.push('wild animal pose', 'aggressive animal', 'dangerous animal', 'predator stance');
      } else if (modelType === 'Cartoon') {
        clauses.push('cartoon character pose', 'animated character posture', 'illustrated character stance', 'cartoon style pose', 'animated style body language');
        negative.push('photorealistic pose', 'realistic proportions', 'realistic features');
      }
    }
    
    negative.push(
      'beautified face',
      'face reshaping',
      'face regeneration',
      'face modification',
      'face changes',
      'different face',
      'face not matching reference',
      'altered facial features',
      'changed facial structure',
      'modified face',
      'cgi face',
      'plastic skin',
      'over-smooth skin',
      'airbrushed skin',
      'artificial smoothness',
      'face not from reference',
      'wrong face',
      'different person',
      'face mismatch',
      'changed head covering',
      'altered hijab',
      'different head covering color',
      'different head covering pattern'
    );
  } else if (hasFace === false && normalizedInput.hasHuman) {
    /* --------------------------------------------------
     * GENERATE FACE BASED ON MODEL TYPE (NO FACE REFERENCE)
     * Special scenario: User uploads image without face
     * AI must generate face based on modelType (Wanita, Pria, Anak LakiLaki, Anak Perempuan, Hewan, Cartoon)
     * And adjust pose style based on model type
     * -------------------------------------------------- */
    const modelType = normalizedInput.modelType || 'Wanita';
    
    // Generate face characteristics based on model type
    if (modelType === 'Wanita') {
      clauses.push(
        'natural female face',
        'feminine facial features',
        'natural female facial structure',
        'realistic female appearance',
        'natural female skin texture',
        'feminine facial proportions',
        'natural female expression'
      );
      
      // Adjust pose to be feminine
      if (normalizedInput.pose) {
        clauses.push('feminine pose', 'elegant posture', 'graceful stance', 'feminine body language');
      }
      
      negative.push(
        'masculine face',
        'male features',
        'manly appearance',
        'masculine pose',
        'aggressive posture'
      );
    } else if (modelType === 'Pria') {
      clauses.push(
        'natural male face',
        'masculine facial features',
        'natural male facial structure',
        'realistic male appearance',
        'natural male skin texture',
        'masculine facial proportions',
        'natural male expression'
      );
      
      // Adjust pose to be gentle
      if (normalizedInput.pose) {
        clauses.push('gentle pose', 'soft posture', 'calm stance', 'gentle body language', 'relaxed masculine pose');
      }
      
      negative.push(
        'feminine face',
        'female features',
        'girly appearance',
        'aggressive pose',
        'harsh posture',
        'intimidating stance'
      );
    } else if (modelType === 'Anak LakiLaki') {
      clauses.push(
        'natural child boy face',
        'boyish facial features',
        'natural child facial structure',
        'realistic child boy appearance',
        'natural child skin texture',
        'child facial proportions',
        'natural child expression',
        'youthful appearance',
        'child-like features'
      );
      
      // Adjust pose to be child-like
      if (normalizedInput.pose) {
        clauses.push('child-like pose', 'playful posture', 'natural child stance', 'youthful body language', 'energetic pose');
      }
      
      negative.push(
        'adult face',
        'mature features',
        'grown-up appearance',
        'adult pose',
        'serious posture',
        'mature stance'
      );
    } else if (modelType === 'Anak Perempuan') {
      clauses.push(
        'natural child girl face',
        'girlish facial features',
        'natural child facial structure',
        'realistic child girl appearance',
        'natural child skin texture',
        'child facial proportions',
        'natural child expression',
        'youthful appearance',
        'child-like features'
      );
      
      // Adjust pose to be child-like
      if (normalizedInput.pose) {
        clauses.push('child-like pose', 'playful posture', 'natural child stance', 'youthful body language', 'energetic pose', 'innocent expression');
      }
      
      negative.push(
        'adult face',
        'mature features',
        'grown-up appearance',
        'adult pose',
        'serious posture',
        'mature stance'
      );
    } else if (modelType === 'Hewan') {
      clauses.push(
        'natural pet animal',
        'realistic animal appearance',
        'natural animal features',
        'realistic animal proportions',
        'natural animal expression',
        'pet-like appearance',
        'domesticated animal',
        'friendly animal expression'
      );
      
      // Adjust pose to be pet-like
      if (normalizedInput.pose) {
        clauses.push('pet-like pose', 'natural animal posture', 'domesticated animal stance', 'friendly animal pose', 'natural pet behavior');
      }
      
      negative.push(
        'wild animal',
        'aggressive animal',
        'feral appearance',
        'wild animal pose',
        'dangerous animal',
        'predator stance'
      );
    } else if (modelType === 'Cartoon') {
      clauses.push(
        'cartoon character face',
        'animated character appearance',
        'cartoon style facial features',
        'animated character proportions',
        'cartoon character expression',
        'illustrated character',
        'animated style',
        'cartoon art style'
      );
      
      // Adjust pose to be cartoon-like
      if (normalizedInput.pose) {
        clauses.push('cartoon character pose', 'animated character posture', 'illustrated character stance', 'cartoon style pose', 'animated style body language');
      }
      
      negative.push(
        'photorealistic face',
        'realistic appearance',
        'real human face',
        'photorealistic pose',
        'realistic proportions',
        'realistic features'
      );
    }
    
    // Common prompts for all model types without face reference
    clauses.push(
      'natural facial expression',
      'realistic appearance',
      'natural skin texture',
      'lifelike features'
    );
  }
  
  // Special pose scenarios (only if no face reference)
  // These scenarios will use the face generated based on modelType above
  // Pose style is already adjusted based on modelType in the section above
  if (hasFace === false && normalizedInput.hasHuman && (normalizedInput.pose === 'Mirror Selfie' || normalizedInput.pose === 'Mirror selfie menggunakan iPhone')) {
    /* --------------------------------------------------
     * MIRROR SELFIE WITH IPHONE (NO FACE REFERENCE)
     * Special scenario: User uploads image without face but wants mirror selfie
     * AI must generate natural face based on modelType that is partially covered by iPhone in realistic mirror selfie pose
     * Face characteristics and pose style are already set in the modelType section above
     * -------------------------------------------------- */
    clauses.push(
      'mirror selfie pose',
      'standing in front of mirror',
      'holding iPhone in hand',
      'iPhone partially covering lower portion of face naturally',
      'face visible through iPhone screen area',
      'eyes and upper face clearly visible above iPhone',
      'forehead and eyes area not covered',
      'cheek and chin area may be partially covered by iPhone',
      'realistic iPhone size and proportions',
      'iPhone size matches real iPhone device dimensions',
      'iPhone held at natural selfie angle',
      'iPhone positioned at chest to face level',
      'hand holding iPhone naturally',
      'realistic hand position',
      'fingers visible holding iPhone',
      'natural phone grip',
      'iPhone screen showing camera view',
      'iPhone screen reflection visible',
      'mirror shows full reflection of person',
      'reflection visible in mirror',
      'natural mirror selfie composition',
      'face not completely hidden',
      'face partially visible behind iPhone',
      'natural selfie expression',
      'relaxed selfie pose',
      'authentic mirror selfie moment',
      'natural selfie angle',
      'authentic smartphone selfie',
      'realistic mirror reflection',
      'natural pose as if taking selfie',
      'realistic iPhone bezels and screen',
      'proportional iPhone to face ratio',
      'iPhone covers approximately 30-40% of face area',
      'upper 60-70% of face clearly visible',
      'natural mirror selfie lighting',
      'realistic iPhone dimensions',
      'iPhone width approximately 7-8cm in real scale',
      'iPhone height approximately 15-16cm in real scale',
      'proportional phone size relative to face',
      'natural hand-to-phone-to-face proportions'
    );
    
    negative.push(
      'face completely hidden',
      'face fully covered by phone',
      'no face visible',
      'face not visible',
      'completely hidden face',
      'no facial features visible',
      'eyes not visible',
      'forehead covered by phone',
      'oversized iPhone',
      'undersized iPhone',
      'unrealistic phone size',
      'iPhone too large',
      'iPhone too small',
      'disproportionate phone',
      'fake phone size',
      'unnatural phone position',
      'phone covering entire face',
      'phone covering eyes',
      'phone covering forehead',
      'unrealistic phone dimensions',
      'cartoon phone',
      'fake phone',
      'not real iPhone',
      'wrong phone size',
      'giant phone',
      'tiny phone',
      'unnatural selfie pose',
      'not mirror selfie',
      'no mirror reflection',
      'fake mirror',
      'unrealistic reflection',
      'no reflection visible',
      'phone floating',
      'phone not held by hand',
      'unnatural phone grip',
      'phone covering more than 50% of face'
    );
  } else if (hasFace === false && normalizedInput.hasHuman && normalizedInput.pose === 'Front Camera Selfie') {
    /* --------------------------------------------------
     * FRONT CAMERA SELFIE (NO FACE REFERENCE)
     * Special scenario: User uploads image without face but wants front camera selfie
     * AI must generate natural face in front-facing camera selfie pose
     * -------------------------------------------------- */
    clauses.push(
      'front-facing camera selfie',
      'holding smartphone in hand',
      'natural selfie angle',
      'camera pointing at face',
      'natural selfie expression',
      'relaxed selfie pose',
      'authentic smartphone selfie',
      'natural hand position',
      'realistic smartphone size',
      'smartphone held at natural selfie distance',
      'face clearly visible',
      'natural selfie lighting',
      'authentic selfie moment',
      'realistic smartphone dimensions',
      'proportional phone to face ratio',
      'natural phone grip',
      'fingers visible holding phone',
      'phone screen showing camera view',
      'natural selfie composition',
      'authentic front camera selfie',
      'face fills frame appropriately',
      'natural facial proportions',
      'realistic selfie appearance'
    );
    
    negative.push(
      'face not visible',
      'face hidden',
      'oversized phone',
      'undersized phone',
      'unrealistic phone size',
      'unnatural selfie pose',
      'not selfie',
      'fake phone',
      'wrong phone size',
      'phone covering face',
      'unnatural phone position',
      'blurry face',
      'distorted face',
      'unrealistic facial features'
    );
  } else if (hasFace === false && normalizedInput.hasHuman && normalizedInput.pose === 'Close-Up Portrait') {
    /* --------------------------------------------------
     * CLOSE-UP PORTRAIT (NO FACE REFERENCE)
     * Special scenario: User uploads image without face but wants close-up portrait
     * AI must generate natural face based on modelType in close-up portrait composition
     * Face characteristics are already set in the modelType section above
     * -------------------------------------------------- */
    clauses.push(
      'close-up portrait',
      'face clearly visible',
      'natural facial expression',
      'professional portrait composition',
      'natural skin texture',
      'realistic facial features',
      'natural portrait lighting',
      'focused on face and product',
      'product visible in frame',
      'natural portrait pose',
      'professional close-up framing',
      'face fills frame appropriately',
      'natural facial proportions',
      'realistic portrait appearance',
      'natural portrait expression',
      'professional portrait quality',
      'clear facial details',
      'natural portrait composition'
    );
    
    negative.push(
      'face not visible',
      'face hidden',
      'blurry face',
      'distorted face',
      'unnatural facial features',
      'fake face',
      'unrealistic portrait',
      'face too small',
      'face too large',
      'wrong portrait composition',
      'unrealistic facial proportions',
      'distorted facial structure'
    );
  }
  
  /* --------------------------------------------------
   * GARMENT HARD LOCK
   * -------------------------------------------------- */
  if (garmentType && (normalizedInput.hasSubject || normalizedInput.hasOptionalSubject)) {
    const hasMultipleProducts = normalizedInput.hasSubject && normalizedInput.hasOptionalSubject;
    const isFootwearCategory = normalizedInput.category === 'Sandal/Sepatu' || 
                               garmentType?.toLowerCase().includes('footwear') || 
                               garmentType?.toLowerCase().includes('shoe') ||
                               garmentType?.toLowerCase().includes('sandal');
    
    clauses.push(
      `wearing ${garmentType.toLowerCase()}`,
      'exact garment from reference image',
      'preserve original garment color',
      'no color reinterpretation',
      'no hue shift',
      'preserve original fabric texture',
      'visible fabric weave',
      'retain fabric grain',
      'no fabric smoothing'
    );
    
    // Complete outfit handling dengan skenario khusus:
    // - If multiple product images (baju + celana/sendal), use complete outfit from reference
    // - Special scenario: Baju/atasan wanita + Sendal → Celana pakai jeans
    // - Special scenario: Hanya baju saja → Celana menyesuaikan dengan baju (matching)
    // - If single product image:
    //   * Only baju → AI buat celana matching DAN sendal yang sesuai
    //   * Only celana → AI buat baju DAN sendal yang sesuai
    //   * Only sendal/sepatu → AI buat baju DAN celana yang sesuai
    
    // Deteksi skenario khusus untuk outfit completion
    const isWomanModel = normalizedInput.modelType === 'Wanita';
    const isFashionCategory = normalizedInput.category === 'Fashion';
    
    // Skenario 1: Hanya baju/atasan wanita saja (tidak ada optionalSubject)
    const isTopGarmentOnly = isFashionCategory && normalizedInput.hasSubject && !normalizedInput.hasOptionalSubject && isWomanModel;
    
    // Skenario 2: Baju/atasan wanita + Sendal (ada optionalSubject, asumsi adalah sendal karena biasanya user upload baju + sendal)
    // Catatan: Kita tidak bisa langsung tahu apakah optionalSubject adalah sendal atau celana,
    // tapi berdasarkan konteks umum, jika Fashion category + hasOptionalSubject, kemungkinan besar adalah sendal
    const isTopGarmentWithFootwear = isFashionCategory && normalizedInput.hasSubject && normalizedInput.hasOptionalSubject && isWomanModel;
    
    if (hasMultipleProducts) {
      // Multiple products = complete outfit from reference (baju + celana/sendal dari referensi)
      clauses.push(
        'complete outfit from reference',
        'wearing matching bottom garment from reference',
        'wearing footwear from reference',
        'full outfit visible from reference images'
      );
    } else if (normalizedInput.hasSubject && normalizedInput.hasHuman) {
      if (isFootwearCategory) {
        // Single product (only sendal/sepatu) + human = AI harus buat baju DAN celana yang sesuai
        clauses.push(
          'complete outfit with appropriate matching top garment',
          'wearing appropriate top that matches the footwear',
          'wearing appropriate matching bottom garment',
          'wearing appropriate lower garment that matches the footwear',
          'full outfit visible',
          'top garment complements the reference footwear',
          'bottom garment complements the reference footwear'
        );
      } else if (isTopGarmentWithFootwear) {
        // SCENARIO KHUSUS: Baju/atasan wanita + Sendal → Celana pakai jeans
        clauses.push(
          'complete outfit with jeans bottom garment',
          'wearing blue denim jeans',
          'wearing jeans that match the top garment style',
          'wearing appropriate footwear that matches the outfit',
          'full outfit visible',
          'jeans complement the reference top garment',
          'footwear complements the reference top garment',
          'jeans style coordinates with top garment',
          'jeans color coordinates with top garment'
        );
      } else if (isTopGarmentOnly) {
        // SCENARIO KHUSUS: Hanya baju/atasan wanita saja → Celana matching + Sendal/sepatu
        clauses.push(
          'complete outfit with matching bottom garment',
          'wearing bottom garment that matches the top garment color',
          'wearing bottom garment that matches the top garment style',
          'wearing bottom garment that complements the reference top garment',
          'wearing shoes or sandals',
          'wearing footwear that matches the outfit',
          'wearing appropriate footwear that complements the outfit',
          'full outfit visible',
          'bottom garment color coordinates with top garment',
          'bottom garment style coordinates with top garment',
          'bottom garment fabric coordinates with top garment',
          'footwear complements the reference top garment',
          'footwear style coordinates with top garment',
          'footwear color coordinates with outfit'
        );
      } else {
        // Single product (baju ATAU celana) + human = AI harus melengkapi dengan bagian lain
        clauses.push(
          'complete outfit with appropriate matching garments',
          'wearing appropriate top garment that complements the reference',
          'wearing appropriate bottom garment that complements the reference',
          'wearing appropriate footwear that matches the outfit',
          'full outfit visible',
          'all garments complement each other and the reference product'
        );
      }
    }
    
    negative.push(
      'missing bottom garment',
      'incomplete outfit',
      'exposed underwear',
      'naked lower body',
      'fabric smoothing',
      'plastic fabric',
      'washed fabric detail',
      'synthetic texture',
      'blurred fabric',
      'color shift',
      'hue change'
    );
  }
  
  /* --------------------------------------------------
   * BACKGROUND & SCALE CONTROL
   * -------------------------------------------------- */
  if (normalizedInput.useBackground) {
    // Background is the SECOND image in the array sent to Fal.ai (priority order)
    // Order: [Product1, Background (second), Product2/Face (optional)]
    // This ensures background is always included if uploaded (priority over face)
    clauses.push(
      'second reference image is background environment',
      'use second reference image as static background',
      'background from second reference image must be used exactly',
      'static background environment from second reference image',
      'background not reinterpreted',
      'background unchanged from second reference image',
      'background is the scene environment',
      'composite subject onto uploaded background from second reference image',
      'subject placed on ground/surface of background from second reference image',
      'subject scale preserved relative to background from second reference image',
      'correct subject-to-background ratio',
      'realistic grounded shadow on background',
      'natural contact shadow on background surface',
      'shadow integration with background',
      'color temperature match with background',
      'background environment must be visible',
      'use entire background from reference image',
      'do not crop or modify background',
      'preserve background composition exactly',
      'background is critical for scene composition',
      'background defines the entire environment'
    );
  } else {
    // No background image uploaded - use user's background selection from UI
    if (normalizedInput.customBackgroundPrompt) {
      // User provided custom background prompt
      clauses.push(`background: ${normalizedInput.customBackgroundPrompt.toLowerCase()}`);
    } else if (normalizedInput.background && normalizedInput.background !== 'Upload Background' && normalizedInput.background !== 'Hapus Latar') {
      // User selected a background option from UI - translate it to English
      const backgroundDesc = translateToEnglish(normalizedInput.background);
      if (backgroundDesc && backgroundDesc !== normalizedInput.background) {
        clauses.push(`background: ${backgroundDesc.toLowerCase()}`);
      } else {
        // Fallback to neutral studio backdrop
        clauses.push(
          'neutral studio backdrop',
          'plain background',
          'no background stylization'
        );
      }
    } else {
      // No background selection or "Hapus Latar" (remove background) - use neutral studio backdrop
      clauses.push(
        'neutral studio backdrop',
        'plain background',
        'no background stylization'
      );
    }
  }
  
  negative.push(
    'floating subject',
    'scale mismatch',
    'incorrect subject-to-background ratio',
    'detached shadow',
    'distorted proportions',
    'incorrect shadow direction',
    'unrealistic lighting',
    'fake lighting'
  );
  
  /* --------------------------------------------------
   * LIGHTING — SAFE FOR VIDEO EXTENSION
   * -------------------------------------------------- */
  if (normalizedInput.lighting && normalizedInput.lighting !== 'Custom') {
    const lightingDesc = translateToEnglish(normalizedInput.lighting);
    if (lightingDesc && lightingDesc !== normalizedInput.lighting) {
      const lightLower = lightingDesc.toLowerCase();
      if (lightLower.includes('daylight') || lightLower.includes('natural') || lightLower.includes('window')) {
        clauses.push('soft natural lighting');
      } else {
        clauses.push(`lighting: ${lightLower}`);
      }
    }
  } else {
    clauses.push(
      'soft natural lighting',
      'balanced exposure',
      'no dramatic lighting',
      'no cinematic lighting'
    );
  }
  
  negative.push(
    'dramatic lighting',
    'cinematic light',
    'harsh shadow',
    'oversoft lighting',
    'glow effect'
  );
  
  /* --------------------------------------------------
   * FINAL SAFETY NET
   * -------------------------------------------------- */
  negative.push(
    'anime',
    'cartoon',
    'illustration',
    'stylized',
    'artistic',
    'unrealistic',
    'cgi',
    'mannequin',
    'manikin',
    'doll-like',
    'statue-like',
    'rigid pose',
    'stiff pose',
    'lifeless',
    'robotic',
    'artificial human',
    'fake human',
    'wax figure',
    'museum display',
    'posed mannequin',
    'store display mannequin',
    'unrealistic pose',
    'unnatural posture',
    'plastic appearance',
    'synthetic look'
  );
  
  // Combine clauses into prompt
  const positivePrompt = clauses
    .filter(c => c.trim().length > 0)
    .join(', ')
    .replace(/\s+/g, ' ')
    .trim() + '.';
  
  const negativePrompt = negative
    .filter(n => n.trim().length > 0)
    .join(', ')
    .replace(/\s+/g, ' ')
    .trim();
  
  return {
    positivePrompt,
    negativePrompt,
    metadata: {
      engine: 'flux-2',
      version: 'v2',
    },
  };
}
