import { ImageData, GenerationOptions, GenerationResult } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function generateProductPhoto(
  productImages: (ImageData | null)[],
  faceImage: ImageData | null,
  backgroundImage: ImageData | null,
  options: GenerationOptions
): Promise<GenerationResult> {
  // Filter out null images
  const validProductImages = productImages.filter(img => img !== null) as ImageData[];
  
  if (validProductImages.length === 0) {
    throw new Error('At least one product image is required');
  }

  const requestBody = {
    productImages: validProductImages.map(img => ({
      base64: img.base64,
      mimeType: img.mimeType
    })),
    faceImage: faceImage ? {
      base64: faceImage.base64,
      mimeType: faceImage.mimeType
    } : null,
    backgroundImage: backgroundImage ? {
      base64: backgroundImage.base64,
      mimeType: backgroundImage.mimeType
    } : null,
    options
  };

  const response = await fetch(`${API_URL}/api/generate-photo`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to generate photo' }));
    throw new Error(error.message || 'Failed to generate photo');
  }

  const result = await response.json();
  return result;
}

export async function generateProductVideo(
  base64Image: string,
  options: GenerationOptions
): Promise<string> {
  const response = await fetch(`${API_URL}/api/generate-video`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image: base64Image,
      options
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to generate video' }));
    throw new Error(error.message || 'Failed to generate video');
  }

  const result = await response.json();
  return result.videoUrl;
}

