/**
 * LAYER 2 - Normalization Layer
 * Converts raw user input into deterministic backend-ready schema
 */

import { RawGenerationInput } from '../types/generationInput';
import { resolvePhotographyMode } from './modeResolver';

export interface NormalizedGenerationInput {
  // Image flags
  hasSubject: boolean;
  hasBackground: boolean;
  hasOptionalSubject: boolean;
  hasHuman: boolean;
  hasFaceImage: boolean; // Whether face reference image is provided
  isProductOnly: boolean;
  
  // Background usage signal (boolean, not natural language)
  useBackground: boolean;
  
  // Mode (resolved from 'auto' if needed)
  mode: 'catalog' | 'lifestyle';
  
  // Photographic parameters (normalized)
  category?: string;
  style?: string;
  lighting?: string;
  cameraAngle?: string;
  pose?: string;
  aspectRatio?: string;
  background?: string; // Background selection from UI
  modelType?: string;
  interactionType?: string;
  
  // Custom prompts
  customStylePrompt?: string;
  customPosePrompt?: string;
  customBackgroundPrompt?: string;
  customLightingPrompt?: string;
}

/**
 * Normalize raw user input to backend-ready schema
 * Integrates Layer 3 (mode resolution) for complete normalization
 */
export function normalizeGenerationInput(input: RawGenerationInput, hasFaceImage: boolean = false): NormalizedGenerationInput {
  const hasSubject = !!input.subjectImage;
  const hasBackground = !!input.backgroundImage;
  const hasOptionalSubject = !!input.optionalSubjectImage;
  
  // Determine if human is present (based on modelType or contentType inference)
  const hasHuman = !!input.modelType && input.modelType !== '';
  const isProductOnly = !hasHuman;
  
  // Background usage signal: true if background image exists
  const useBackground = hasBackground;
  
  // Create temporary normalized input for mode resolution
  const tempNormalized: NormalizedGenerationInput = {
    hasSubject,
    hasBackground,
    hasOptionalSubject,
    hasHuman,
    hasFaceImage,
    isProductOnly,
    useBackground,
    mode: 'catalog', // Temporary, will be resolved
    category: input.category,
    style: input.style,
    lighting: input.lighting,
    cameraAngle: input.cameraAngle,
    pose: input.pose,
    aspectRatio: input.aspectRatio,
    background: input.background,
    modelType: input.modelType,
    interactionType: input.interactionType,
    customStylePrompt: input.customStylePrompt,
    customPosePrompt: input.customPosePrompt,
    customBackgroundPrompt: input.customBackgroundPrompt,
    customLightingPrompt: input.customLightingPrompt,
  };
  
  // Resolve mode using Layer 3
  const resolvedMode = resolvePhotographyMode(tempNormalized, input.mode);
  
  return {
    ...tempNormalized,
    mode: resolvedMode,
  };
}
