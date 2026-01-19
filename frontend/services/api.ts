import { StudioConfig, GeneratedImage } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface GenerateRequest {
  config: StudioConfig;
  productImage: string;
  faceImage?: string;
  customBgImage?: string;
}

export const api = {
  async generateImages(request: GenerateRequest): Promise<GeneratedImage[]> {
    const response = await fetch(`${API_URL}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to generate images');
    }

    const results = await response.json();
    return results.map((result: any, index: number) => ({
      id: `${Date.now()}-${index}`,
      url: result.url,
      videoPrompt: result.videoPrompt,
      timestamp: Date.now(),
    }));
  },

  async getPoseOptions(config: StudioConfig): Promise<string[]> {
    const response = await fetch(`${API_URL}/api/pose-options`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error('Failed to get pose options');
    }

    const data = await response.json();
    return data.options;
  },

  async getBackgroundOptions(config: StudioConfig): Promise<string[]> {
    const response = await fetch(`${API_URL}/api/background-options`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error('Failed to get background options');
    }

    const data = await response.json();
    return data.options;
  },
};



