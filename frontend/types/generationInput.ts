/**
 * LAYER 1 - Frontend User Input
 * Raw user input interfaces for image generation
 * No prompt text embedded at this layer
 */

export interface ImageInput {
  base64: string;
  mimeType: string;
}

export interface RawGenerationInput {
  // Required
  subjectImage: ImageInput;
  
  // Optional images
  backgroundImage?: ImageInput;
  optionalSubjectImage?: ImageInput; // For multiple products
  
  // Mode selection
  mode: 'auto' | 'catalog' | 'lifestyle';
  
  // Photographic parameters
  category?: string;
  style?: string;
  lighting?: string;
  cameraAngle?: string;
  pose?: string;
  aspectRatio?: string;
  background?: string; // Background selection from UI (e.g., "Studio", "Kamar Aesthetic Women", etc.)
  
  // Additional options
  modelType?: string; // For human subjects
  interactionType?: string;
  customStylePrompt?: string;
  customPosePrompt?: string;
  customBackgroundPrompt?: string;
  customLightingPrompt?: string;
}
