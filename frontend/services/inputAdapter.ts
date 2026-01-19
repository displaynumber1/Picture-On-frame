/**
 * Adapter: Convert legacy GenerationOptions to new RawGenerationInput
 * Maintains backward compatibility during migration
 */

import { GenerationOptions } from '../types';
import { ImageData } from '../types';
import { RawGenerationInput } from '../types/generationInput';

/**
 * Extract base64 from data URL
 */
function extractBase64(dataUrl: string): string {
  const commaIndex = dataUrl.indexOf(',');
  return commaIndex >= 0 ? dataUrl.substring(commaIndex + 1) : dataUrl;
}

/**
 * Extract mime type from data URL
 */
function extractMimeType(dataUrl: string): string {
  const match = dataUrl.match(/data:([^;]+);/);
  return match ? match[1] : 'image/jpeg';
}

/**
 * Convert legacy GenerationOptions + ImageData to RawGenerationInput
 */
export function adaptLegacyInput(
  options: GenerationOptions,
  productImage: ImageData | null,
  productImage2: ImageData | null,
  faceImage: ImageData | null,
  backgroundImage: ImageData | null,
  productImageDataUrl?: string,
  productImage2DataUrl?: string,
  faceImageDataUrl?: string,
  backgroundImageDataUrl?: string
): RawGenerationInput {
  // Determine mode from style (backward compatibility)
  let mode: 'auto' | 'catalog' | 'lifestyle' = 'auto';
  if (options.style === 'Lifestyle') {
    mode = 'lifestyle';
  } else if (options.style === 'Studio Clean') {
    mode = 'catalog';
  }
  
  // Map contentType to modelType inference
  const hasHuman = options.contentType === 'Model';
  
  // Prefer data URLs if provided, otherwise use ImageData
  const subjectImageData = productImageDataUrl 
    ? { base64: extractBase64(productImageDataUrl), mimeType: extractMimeType(productImageDataUrl) }
    : productImage || { base64: '', mimeType: 'image/jpeg' };
  
  const optionalSubjectImageData = productImage2DataUrl
    ? { base64: extractBase64(productImage2DataUrl), mimeType: extractMimeType(productImage2DataUrl) }
    : productImage2 || undefined;
  
  const backgroundImageData = backgroundImageDataUrl
    ? { base64: extractBase64(backgroundImageDataUrl), mimeType: extractMimeType(backgroundImageDataUrl) }
    : backgroundImage || undefined;
  
  return {
    subjectImage: subjectImageData,
    backgroundImage: backgroundImageData,
    optionalSubjectImage: optionalSubjectImageData,
    mode,
    category: options.category,
    style: options.style,
    lighting: options.lighting,
    cameraAngle: options.cameraAngle,
    pose: options.pose,
    aspectRatio: options.aspectRatio,
    background: options.background,
    modelType: hasHuman ? options.modelType : undefined,
    interactionType: options.interactionType,
    customStylePrompt: options.customStylePrompt,
    customPosePrompt: options.customPosePrompt,
    customBackgroundPrompt: options.customBackgroundPrompt,
    customLightingPrompt: options.customLightingPrompt,
  };
}
