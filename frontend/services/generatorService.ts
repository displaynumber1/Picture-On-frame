/**
 * Service for image and video generation API calls
 * 
 * NOTE: Prompt generation is handled by:
 * - fluxPromptGenerator.ts (generateFluxPromptV2) for Flux-2
 * - promptGenerator.ts (generateProfessionalPrompt) for non-Flux engines
 * 
 * This service handles API communication only, not prompt generation.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface GenerateImageResponse {
  images: string[];
  remaining_quota: number;
}

export interface GenerateVideoResponse {
  video_url: string;
  remaining_coins: number;
}

export interface UserProfile {
  free_image_quota: number;
  coins_balance: number;
}

export const generatorService = {
  /**
   * Get user profile
   */
  async getProfile(token: string): Promise<UserProfile> {
    const response = await fetch(`${API_URL}/api/user/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to get profile' }));
      throw new Error(error.detail || 'Failed to get profile');
    }

    return await response.json();
  },

  /**
   * Generate images using fal
   */
  async generateImage(prompt: string, token: string): Promise<GenerateImageResponse> {
    const response = await fetch(`${API_URL}/api/generate-image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ prompt })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate images' }));
      throw new Error(error.detail || 'Failed to generate images');
    }

    return await response.json();
  },

  /**
   * Generate video using fal
   */
  async generateVideo(prompt: string, imageUrl: string | null, token: string): Promise<GenerateVideoResponse> {
    const response = await fetch(`${API_URL}/api/generate-video-saas`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt,
        image_url: imageUrl
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate video' }));
      throw new Error(error.detail || 'Failed to generate video');
    }

    return await response.json();
  }
};

