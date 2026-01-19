export interface GenerationOptions {
  background: string;
  customBackgroundPrompt: string;
  pose: string;
  customPosePrompt: string;
  style: string;
  customStylePrompt: string;
  lighting: string;
  customLightingPrompt: string;
  aspectRatio: string;
  cameraAngle: string;
  contentType: string; // Model or Non Model
  modelType: string;
  category: string;
  interactionType: string;
  backgroundColor?: string;
  additionalPrompt?: string;
}

export interface ImageData {
  base64: string;
  mimeType: string;
}

export interface GenerationResult {
  url: string;
  promptA: string;
  promptB: string;
}

export interface AppState {
  productImage: ImageData | null;
  productImage2: ImageData | null;
  productImage3: ImageData | null;
  productImage4: ImageData | null;
  faceImage: ImageData | null;
  backgroundImage: ImageData | null;
  options: GenerationOptions;
  isGenerating: boolean;
  isVideoGenerating: Record<number, boolean>;
  isKlingVideoGenerating: Record<number, boolean>;
  videoResults: Record<number, string>;
  klingVideoResults: Record<number, string>;
  klingSelectedImages: Record<number, string>;
  videoBatches: Record<number, string[]>;
  isVideoBatchGenerating: Record<number, boolean>;
  results: GenerationResult[];
  error: string | null;
}

// Legacy types for api.ts compatibility
export interface StudioConfig {
  contentType: string;
  category: string;
  pose: string;
  background: string;
  style: string;
  lighting: string;
  cameraAngle: string;
  aspectRatio: string;
  [key: string]: any;
}

export interface GeneratedImage {
  id: string;
  url: string;
  videoPrompt?: string;
  timestamp: number;
}
