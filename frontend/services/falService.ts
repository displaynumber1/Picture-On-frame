import { GenerationOptions } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

/**
 * Default negative prompt untuk menghindari hasil yang tidak diinginkan
 * Mencegah: plastic skin, artificial smoothness, CGI, 3D render, dll.
 */
const DEFAULT_NEGATIVE_PROMPT = 'plastic skin, artificial smoothness, airbrushed, CGI, 3d render, cartoon, anime, illustration, sketch, blurry, low resolution, distorted hands, extra fingers, mutated fingers, fused fingers, deformed anatomy, bad proportions, double heads, cloned face, unnatural eyes, watermark, text, signature, grainy, low quality, overexposed, messy background elements, floating products, disconnected limbs';

export interface FalGenerateRequest {
  prompt: string;
  product_images?: string[];  // Multiple product images (base64 atau data URL)
  face_image?: string;  // Face image (base64 atau data URL)
  background_image?: string;  // Background image (base64 atau data URL)
  identity_mode?: 'none' | 'avatar';
  // Fal.ai flux-2/lora/edit specific parameters
  image_strength?: number;  // Image strength for image-to-image generation (default: 0.67 - balanced for reference adherence)
  num_inference_steps?: number;  // Number of inference steps (default: 24)
  guidance_scale?: number;  // Guidance scale (CFG) for prompt adherence (default: 4.5 - natural and realistic)
  model?: string;  // Model endpoint (default: fal-ai/flux-2/lora/edit)
  negative_prompt?: string;  // Negative prompt untuk menghindari hasil yang tidak diinginkan
  aspect_ratio?: string;  // Aspect ratio (e.g., "9:16", "16:9", "1:1") - untuk menentukan width/height
  // Legacy field untuk backward compatibility
  reference_image?: string;  // Base64 image atau data URL (optional, akan dimap ke product_images[0])
}

export interface FalGenerateResponse {
  images: string[];
  remaining_coins?: number;
  remaining_quota?: number; // Legacy field, kept for backward compatibility
}

/**
 * Generate images using Fal.ai API (fal-ai/flux-2/lora/edit)
 * @param prompt - Text prompt for image generation (will be generated from options if not provided)
 * @param numImages - Number of images to generate (default: 2)
 * @param productImages - Optional array of product images (base64 atau data URL) - order: [Produk1, Produk2]
 * @param faceImage - Optional face image (base64 atau data URL) - order: Wajah
 * @param backgroundImage - Optional background image (base64 atau data URL) - order: Background
 * @param options - Optional generation options for prompt generation
 * @param referenceImage - Optional legacy single reference image (backward compatibility)
 * @returns Array of image URLs
 */
export async function generateImagesWithFal(
  prompt?: string,
  numImages: number = 1,
  productImages?: string[],
  faceImage?: string,
  backgroundImage?: string,
  options?: GenerationOptions,
  referenceImage?: string,  // Legacy parameter untuk backward compatibility
  identityMode?: 'none' | 'avatar'
): Promise<string[]> {
  try {
    // Get access token from Supabase
    const { supabaseService } = await import('./supabaseService');
    
    // Get current session
    let { data: { session } } = await supabaseService.supabase.auth.getSession();
    
    // If no session, try to refresh
    if (!session) {
      const { data: { session: refreshedSession }, error } = await supabaseService.supabase.auth.refreshSession();
      if (error || !refreshedSession) {
        throw new Error('User not authenticated. Please login again.');
      }
      session = refreshedSession;
    }
    
    // Get token from session
    const token = session?.access_token;
    
    if (!token) {
      throw new Error('User not authenticated. Please login again.');
    }

    // Generate prompt from options if prompt not provided and options available
    let finalPrompt = prompt;
    let finalNegativePrompt = DEFAULT_NEGATIVE_PROMPT;
    
    if (!finalPrompt && options) {
      // Use new 4-layer architecture with Flux-2 exclusive generator
      const { adaptLegacyInput } = await import('./inputAdapter');
      const { normalizeGenerationInput } = await import('./normalization');
      const { generateFluxPromptV2 } = await import('./fluxPromptGenerator');
      
      const adaptedOptions = options;

      // Convert legacy format to new format
      const rawInput = adaptLegacyInput(
        adaptedOptions,
        null, // productImage - not needed when using data URLs
        null, // productImage2 - not needed when using data URLs
        null, // faceImage - not needed when using data URLs
        null, // backgroundImage - not needed when using data URLs
        productImages && productImages.length > 0 ? productImages[0] : undefined,
        productImages && productImages.length > 1 ? productImages[1] : undefined,
        faceImage,
        backgroundImage
      );
      
      // Normalize and generate prompt using Flux-2 exclusive generator
      const hasFaceImage = !!faceImage; // Check if face image is provided
      const normalized = normalizeGenerationInput(rawInput, hasFaceImage);
      const promptOutput = generateFluxPromptV2(normalized, normalized.mode);
      
      finalPrompt = promptOutput.positivePrompt;
      finalNegativePrompt = promptOutput.negativePrompt;
    }

    if (!finalPrompt) {
      throw new Error('Prompt is required. Please provide either prompt or options.');
    }

    // Generate images in batches (Fal.ai generates 2 images per request)
    const imageUrls: string[] = [];
    const batches = Math.ceil(numImages / 2);
    
    for (let i = 0; i < batches; i++) {
      let response: Response;
      
      try {
        // Build request body with all images in correct order: [Produk1, Produk2, Wajah, Background]
        // Order: Product images first, then face, then background
        const requestBody: FalGenerateRequest = {
          prompt: finalPrompt,
          model: 'fal-ai/flux-2/lora/edit',  // Use flux-2/lora/edit model
          image_strength: 0.67,  // Balanced image strength for reference adherence
          num_inference_steps: 24,  // Increased steps to prevent blank images
          guidance_scale: 4.5,  // Natural CFG for realistic results (not mannequin-like)
          negative_prompt: finalNegativePrompt,  // Use generated negative prompt with fabric constraints
          aspect_ratio: options?.aspectRatio,  // Aspect ratio from options (e.g., "9:16" → 720x1280)
        };
        
        // Include product images if provided (order: Produk1, Produk2)
        if (productImages && productImages.length > 0) {
          requestBody.product_images = productImages.filter(Boolean);
        }
        
        // Include face image if provided (order: Wajah)
        if (faceImage) {
          requestBody.face_image = faceImage;
        }
        
        // Include background image if provided (order: Background)
        if (backgroundImage) {
          requestBody.background_image = backgroundImage;
        }
        
        // Legacy: if only referenceImage provided, map to product_images[0]
        if (referenceImage && (!productImages || productImages.length === 0)) {
          requestBody.reference_image = referenceImage;
        }
        
        const resolvedIdentityMode = identityMode === 'avatar' ? 'avatar' : 'none';
        requestBody.identity_mode = resolvedIdentityMode;

        const readErrorDetail = async (res: Response) => {
          let detail = 'Failed to generate images';
          try {
            const errorData = await res.json();
            detail = errorData.detail || errorData.message || detail;
          } catch (e) {
            try {
              const errorText = await res.text();
              detail = errorText || `HTTP ${res.status}: ${res.statusText}`;
            } catch (e2) {
              detail = `HTTP ${res.status}: ${res.statusText}`;
            }
          }
          return detail;
        };

        response = await fetch(`${API_URL}/api/generate-image`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(requestBody)
        });
      } catch (fetchError: any) {
        // Handle network errors (Failed to fetch, CORS, etc.)
        console.error('Network error when calling API:', fetchError);
        
        if (fetchError.message === 'Failed to fetch' || fetchError.name === 'TypeError') {
          throw new Error(
            `Tidak dapat terhubung ke server backend. ` +
            `Pastikan backend server berjalan di ${API_URL}. ` +
            `Error: ${fetchError.message}`
          );
        }
        throw fetchError;
      }

      if (!response.ok) {
        let errorDetail = await readErrorDetail(response);

        if (response.status === 422 && /identity_mode/i.test(errorDetail)) {
          console.warn('Backend schema does not accept identity_mode, retrying without it.');
          const fallbackBody = { ...requestBody };
          delete fallbackBody.identity_mode;
          response = await fetch(`${API_URL}/api/generate-image`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(fallbackBody)
          });

          if (response.ok) {
            const result: FalGenerateResponse = await response.json();
            if (!result.images || result.images.length === 0) {
              throw new Error('Server mengembalikan response kosong. Silakan coba lagi.');
            }
            imageUrls.push(...result.images);
            if (imageUrls.length >= numImages) {
              break;
            }
            continue;
          }

          errorDetail = await readErrorDetail(response);
        }
        
        // Provide more specific error messages based on status code
        if (response.status === 401) {
          throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
        } else if (response.status === 403) {
          throw new Error(errorDetail || 'Quota Anda telah habis. Silakan top up untuk melanjutkan.');
        } else if (response.status === 404) {
          throw new Error('Endpoint API tidak ditemukan. Pastikan backend server berjalan dan menggunakan versi terbaru.');
        } else if (response.status >= 500) {
          throw new Error(`Server error: ${errorDetail}. Silakan coba lagi nanti.`);
        } else {
          throw new Error(errorDetail || `HTTP ${response.status}: Gagal membuat gambar`);
        }
      }

      const result: FalGenerateResponse = await response.json();
      if (!result.images || result.images.length === 0) {
        throw new Error('Server mengembalikan response kosong. Silakan coba lagi.');
      }
      
      imageUrls.push(...result.images);
      
      // If we have enough images, break
      if (imageUrls.length >= numImages) {
        break;
      }
    }

    // Return only the requested number of images
    return imageUrls.slice(0, numImages);
  } catch (error: any) {
    console.error('Error generating images with Fal.ai:', error);
    const message = typeof error?.message === 'string' ? error.message : '';
    // If error message is already user-friendly, throw as is
    if (message && (
      message.includes('Tidak dapat terhubung') ||
      message.includes('Sesi Anda') ||
      message.includes('Quota') ||
      message.includes('Server error') ||
      message.includes('Silakan')
    )) {
      throw error;
    }
    throw new Error('fal.ai generation failed');
  }
}

/**
 * Translation mapping from Indonesian to English
 */
const translationMap: Record<string, string> = {
  // Model Types
  'Wanita': 'Woman',
  'Pria': 'Man',
  'Anak LakiLaki': 'Boy',
  'Anak Perempuan': 'Girl',
  'Hewan': 'Animal',
  'Cartoon': 'Cartoon',
  
  // Categories
  'Fashion': 'Fashion',
  'Beauty': 'Beauty',
  'Tas': 'Bag',
  'Sandal/Sepatu': 'Sandals/Shoes',
  'Aksesoris': 'Accessories',
  'Home Living': 'Home Living',
  'Food & Beverage': 'Food & Beverage',
  
  // Backgrounds
  'Studio': 'Studio',
  'Kamar Aesthetic Women': 'Aesthetic Women\'s Room',
  'Kamar Aesthetic Men': 'Aesthetic Men\'s Room',
  'Lantai Vynil & Gorden': 'Vinyl Floor & Curtains',
  'Dinding, Karpet & Standing Lampu': 'Wall, Carpet & Standing Lamp',
  'Minimalis': 'Minimalist',
  'Jalan': 'Street',
  'Warna (Custom)': 'Color (Custom)',
  'Meja Aesthetic': 'Aesthetic Table',
  'Karpet': 'Carpet',
  'Gorden': 'Curtains',
  'Tembok Polos': 'Plain Wall',
  'Interior Mobil': 'Car Interior',
  'Mall': 'Mall',
  'Hapus Latar': 'Remove Background',
  'Upload Background': 'Upload Background',
  
  // Styles
  'Studio Clean': 'Studio Clean',
  'Lifestyle': 'Lifestyle',
  'Indoor/Outdoor': 'Indoor/Outdoor',
  'Editorial': 'Editorial',
  'Beauty Glamour': 'Beauty Glamour',
  'Minimalist': 'Minimalist',
  'TikTok Trendy': 'TikTok Trendy',
  'Cinematic': 'Cinematic',
  'Neon Futuristic': 'Neon Futuristic',
  'Flat Lay': 'Flat Lay',
  'Product-on-Table': 'Product-on-Table',
  'Campaign Poster': 'Campaign Poster',
  'Macro': 'Macro',
  'Outdoor Cafe': 'Outdoor Cafe',
  'Custom': 'Custom',
  
  // Lighting
  'Natural Daylight': 'Natural Daylight',
  'Golden Hour': 'Golden Hour',
  'Sunset Glow': 'Sunset Glow',
  'Dramatic Contrast': 'Dramatic Contrast',
  'Low-key': 'Low-key',
  'High-key': 'High-key',
  'Diffused Window Light': 'Diffused Window Light',
  'Neon Ambience': 'Neon Ambience',
  'Warm Candle': 'Warm Candle',
  'Reflective Glow': 'Reflective Glow',
  'Softbox': 'Softbox',
  'Ring Light': 'Ring Light',
  'Cool Tone': 'Cool Tone',
  
  // Camera Angles
  'Eye-Level': 'Eye-Level',
  '45° Angle': '45° Angle',
  'Over-the-Shoulder': 'Over-the-Shoulder',
  'Macro Close-Up': 'Macro Close-Up',
  'Medium Shot': 'Medium Shot',
  'Tight Portrait Crop': 'Tight Portrait Crop',
  'Dutch Angle': 'Dutch Angle',
  'Top-Down Flat Lay': 'Top-Down Flat Lay',
  'Side Angle (30-60°)': 'Side Angle (30-60°)',
  'Front Symmetrical': 'Front Symmetrical',
  'Wide Full Body': 'Wide Full Body',
  'Bird\'s-Eye View': 'Bird\'s-Eye View',
  
  // Aspect Ratios
  '1:1': '1:1',
  '1:1 (Square)': '1:1 (Square)',
  '2:3': '2:3',
  '2:3 (Portrait)': '2:3 (Portrait)',
  '4:5': '4:5',
  '4:5 (Portrait)': '4:5 (Portrait)',
  '16:9': '16:9',
  '16:9 (Landscape)': '16:9 (Landscape)',
  '3:4': '3:4',
  '3:4 (Portrait)': '3:4 (Portrait)',
  '4:3': '4:3',
  '9:16': '9:16',
  '9:16 (Story)': '9:16 (Story)',
  
  // Interaction Types
  'Tanpa Interaksi': 'No Interaction',
  'Pegang produk – 1 tangan (Pria)': 'Holding product - 1 hand (Man)',
  'Pegang produk – 2 tangan (Pria)': 'Holding product - 2 hands (Man)',
  'Pegang produk – 1 tangan (Wanita)': 'Holding product - 1 hand (Woman)',
  'Pegang produk – 2 tangan (Wanita)': 'Holding product - 2 hands (Woman)',
  'Interaksi Kaki (Pria)': 'Foot Interaction (Man)',
  'Interaksi Kaki (Wanita)': 'Foot Interaction (Woman)',
  'Pegang 1 Tangan Wanita': 'Holding with 1 hand (Woman)',
  'Pegang 2 Tangan Wanita': 'Holding with 2 hands (Woman)',
  'Pegang 1 Tangan Pria': 'Holding with 1 hand (Man)',
  'Pegang 2 Tangan Pria': 'Holding with 2 hands (Man)',
  'Kaki Wanita': 'Woman\'s foot',
  'Kaki Pria': 'Man\'s foot',
  'Pegang Hanger dengan Produk': 'Holding hanger with product',
  
  // Common Pose Translations
  'Berdiri santai memegang produk': 'Standing casually holding product',
  'Duduk sambil memegang produk': 'Sitting while holding product',
  'Tatap kamera dengan senyum': 'Looking at camera with smile',
  'Half body dengan ekspresi percaya diri': 'Half body with confident expression',
  'Berdiri dengan gaya profesional': 'Standing in professional style',
  'Pose candid casual': 'Casual candid pose',
  'Mirror selfie menggunakan iPhone': 'Mirror selfie using iPhone',
  'Casual selfie menggunakan kamera depan': 'Casual selfie using front camera',
  'Close-up wajah bersama produk': 'Close-up face with product',
  'Mengangkat produk di depan dada untuk menampilkan detail': 'Lifting product in front of chest to show detail',
};

/**
 * Translate Indonesian text to English using Google Translate API
 */
const translationCache = new Map<string, string>();

export async function translateTextToEnglish(text: string): Promise<string> {
  // If text is empty, return as is
  if (!text || text.trim().length === 0) {
    return text;
  }

  const cached = translationCache.get(text);
  if (cached) {
    return cached;
  }
  
  // Check if text exists in translation map first (faster)
  if (translationMap[text]) {
    return translationMap[text];
  }
  
  // For custom prompts, try to translate using Google Translate API
  try {
    // Use Google Translate API (free tier available)
    // Note: This requires GOOGLE_TRANSLATE_API_KEY in environment variables
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_TRANSLATE_API_KEY;
    
    if (apiKey) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);
      const response = await fetch(
        `https://translation.googleapis.com/language/translate/v2?key=${apiKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            q: text,
            source: 'id', // Indonesian
            target: 'en', // English
            format: 'text'
          }),
          signal: controller.signal
        }
      ).finally(() => clearTimeout(timeoutId));
      
      if (response.ok) {
        const data = await response.json();
        if (data.data && data.data.translations && data.data.translations.length > 0) {
          const translated = data.data.translations[0].translatedText;
          translationCache.set(text, translated);
          return translated;
        }
      }
    }
    
    // Fallback: Simple word-by-word translation for common Indonesian words
    const fallback = simpleTranslateToEnglish(text);
    translationCache.set(text, fallback);
    return fallback;
  } catch (error) {
    console.warn('Translation failed, using original text:', error);
    // Fallback to simple translation
    const fallback = simpleTranslateToEnglish(text);
    translationCache.set(text, fallback);
    return fallback;
  }
}

/**
 * Simple word-by-word translation for common Indonesian words
 * This is a fallback when Google Translate API is not available
 */
function simpleTranslateToEnglish(text: string): string {
  // Common Indonesian to English word mappings
  const wordMap: Record<string, string> = {
    'dengan': 'with',
    'sambil': 'while',
    'untuk': 'for',
    'dalam': 'in',
    'pada': 'on',
    'di': 'at',
    'ke': 'to',
    'dari': 'from',
    'dan': 'and',
    'atau': 'or',
    'tapi': 'but',
    'yang': 'that',
    'ini': 'this',
    'itu': 'that',
    'adalah': 'is',
    'menjadi': 'become',
    'memiliki': 'have',
    'membuat': 'make',
    'menggunakan': 'using',
    'menampilkan': 'showing',
    'menunjukkan': 'showing',
    'memegang': 'holding',
    'berdiri': 'standing',
    'duduk': 'sitting',
    'berjalan': 'walking',
    'tersenyum': 'smiling',
    'melihat': 'looking',
    'menatap': 'looking at',
    'wajah': 'face',
    'tangan': 'hand',
    'kaki': 'foot',
    'produk': 'product',
    'gaya': 'style',
    'warna': 'color',
    'cahaya': 'light',
    'latar': 'background',
    'belakang': 'back',
    'depan': 'front',
    'samping': 'side',
    'atas': 'top',
    'bawah': 'bottom',
    'natural': 'natural',
    'casual': 'casual',
    'profesional': 'professional',
    'aesthetic': 'aesthetic',
    'minimalis': 'minimalist',
    'modern': 'modern',
    'elegan': 'elegant',
    'cantik': 'beautiful',
    'indah': 'beautiful',
    'bagus': 'good',
    'detail': 'detail',
    'close-up': 'close-up',
    'half body': 'half body',
    'full body': 'full body',
    'selfie': 'selfie',
    'lifestyle': 'lifestyle',
    'editorial': 'editorial',
    'studio': 'studio',
    'outdoor': 'outdoor',
    'indoor': 'indoor',
  };
  
  // Split text into words and translate
  const words = text.split(/\s+/);
  const translatedWords = words.map(word => {
    const lowerWord = word.toLowerCase();
    // Remove punctuation for lookup
    const cleanWord = lowerWord.replace(/[.,!?;:]/g, '');
    
    if (wordMap[cleanWord]) {
      // Preserve original capitalization
      if (word[0] === word[0].toUpperCase()) {
        return wordMap[cleanWord].charAt(0).toUpperCase() + wordMap[cleanWord].slice(1);
      }
      return wordMap[cleanWord];
    }
    
    // If word not found in map, check if it's already in English (contains English letters)
    // If it looks like English, keep it as is
    if (/^[a-zA-Z]+$/.test(cleanWord)) {
      return word;
    }
    
    // Otherwise, return original word (might be Indonesian that we don't have mapping for)
    return word;
  });
  
  return translatedWords.join(' ');
}

/**
 * Translate Indonesian text to English (synchronous version for predefined options)
 */
function translateToEnglish(text: string): string {
  // Check if text exists in translation map
  if (translationMap[text]) {
    return translationMap[text];
  }
  
  // If not found, return as is (might already be in English or custom text)
  return text;
}

/**
 * Build prompt from generation options with automatic translation
 * 
 * ⚠️ NOT FOR FLUX-2 ⚠️
 * 
 * This function uses promptGenerator.ts which is for NON-Flux engines only.
 * Flux-2 generation should route through generateFluxPromptV2 in fluxPromptGenerator.ts.
 * 
 * @param options - Generation options from frontend
 * @param hasFaceImage - Whether face image is provided
 * @param hasProductImages - Whether product images are provided
 * @param hasBackgroundImage - Whether background image is provided
 * @returns Professional English prompt string
 */
export async function buildPromptFromOptions(
  options: GenerationOptions,
  hasFaceImage: boolean = false,
  hasProductImages: boolean = false,
  hasBackgroundImage: boolean = false
): Promise<string> {
  // Import and use the professional prompt generator (for non-Flux engines)
  const { generateProfessionalPrompt } = await import('./promptGenerator');
  return generateProfessionalPrompt(options, hasFaceImage, hasProductImages, hasBackgroundImage);
}

/**
 * Create TikTok-ready video from generated image
 * Converts static image to 5-second MP4 with fake motion effect
 * 
 * @param imageUrl - URL of the generated image
 * @param hookText - Optional hook text (default: "Check This Out!")
 * @param ctaText - Optional CTA text (default: "Shop Now")
 * @param token - Supabase auth token
 * @returns Video URL and metadata
 */
export async function createVideoFromImage(
  imageUrl: string,
  hookText: string = "Check This Out!",
  ctaText: string = "Shop Now",
  token: string
): Promise<{ video_url: string; file_size_mb: number; duration: number; resolution: string; fps: number }> {
  const response = await fetch(`${API_URL}/api/create-video`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      image_url: imageUrl,
      hook_text: hookText,
      cta_text: ctaText
    })
  });

  if (!response.ok) {
    let errorDetail = 'Failed to create video';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.message || errorDetail;
    } catch (e) {
      const errorText = await response.text();
      errorDetail = errorText || `HTTP ${response.status}: ${response.statusText}`;
    }
    
    if (response.status === 503) {
      throw new Error('Video generation service unavailable. FFmpeg is not installed on the server.');
    } else if (response.status === 401) {
      throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
    } else if (response.status >= 500) {
      throw new Error(`Server error: ${errorDetail}. Silakan coba lagi nanti.`);
    } else {
      throw new Error(errorDetail || `HTTP ${response.status}: Gagal membuat video`);
    }
  }

  const result = await response.json();
  if (result?.video_url) {
    return result;
  }
  const firstVideo = Array.isArray(result?.videos)
    ? result.videos.find((video: any) => video?.video_url)
    : null;
  if (firstVideo?.video_url) {
    return {
      video_url: firstVideo.video_url,
      file_size_mb: typeof firstVideo.file_size_mb === 'number' ? firstVideo.file_size_mb : 0,
      duration: typeof result?.duration === 'number' ? result.duration : 0,
      resolution: typeof result?.resolution === 'string' ? result.resolution : '',
      fps: typeof result?.fps === 'number' ? result.fps : 0
    };
  }
  throw new Error('Tidak ada video yang dihasilkan. Silakan coba lagi.');
}

/**
 * Create 3 TikTok-ready videos from generated image based on product category
 * Each category has 3 different fake motion variations
 * 
 * @param imageUrl - URL of the generated image
 * @param category - Product category (e.g., "Fashion", "Beauty", etc.)
 * @param token - Supabase auth token
 * @returns Array of 3 video URLs with metadata
 */
export async function createVideoBatchFromImage(
  imageUrl: string,
  category: string,
  token: string
): Promise<{ videos: Array<{ video_url: string; preset_name: string; file_size_mb: number; description: string }>; category: string; total_videos: number; remaining_coins?: number }> {
  const response = await fetch(`${API_URL}/api/create-videos-batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      image_url: imageUrl,
      category: category
    })
  });

  if (!response.ok) {
    let errorDetail = 'Failed to create videos';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.message || errorDetail;
    } catch (e) {
      const errorText = await response.text();
      errorDetail = errorText || `HTTP ${response.status}: ${response.statusText}`;
    }
    
    if (response.status === 503) {
      throw new Error('Video generation service unavailable. FFmpeg is not installed on the server.');
    } else if (response.status === 401) {
      throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
    } else if (response.status >= 500) {
      throw new Error(`Server error: ${errorDetail}. Silakan coba lagi nanti.`);
    } else {
      throw new Error(errorDetail || `HTTP ${response.status}: Gagal membuat videos`);
    }
  }

  const result = await response.json();
  return result;
}

/**
 * Create Kling video (image-to-video) using fal-ai/kling-video/v2.1/standard/image-to-video
 * 
 * @param imageUrl - URL of the generated image
 * @param token - Supabase auth token
 * @returns Video URL
 */
export async function createKlingVideoFromImage(
  imageUrl: string,
  token: string,
  prompt: string,
  negativePrompt?: string
): Promise<{ video_url: string; remaining_coins?: number }> {
  const response = await fetch(`${API_URL}/api/create-kling-video`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      image_url: imageUrl,
      prompt,
      negative_prompt: negativePrompt
    })
  });

  if (!response.ok) {
    let errorDetail = 'Failed to create Pro video';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.message || errorDetail;
    } catch (e) {
      const errorText = await response.text();
      errorDetail = errorText || `HTTP ${response.status}: ${response.statusText}`;
    }

    if (response.status === 401) {
      throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
    } else if (response.status >= 500) {
      throw new Error(`Server error: ${errorDetail}. Silakan coba lagi nanti.`);
    } else {
      throw new Error(errorDetail || `HTTP ${response.status}: Gagal membuat video`);
    }
  }

  const result = await response.json();
  return result;
}
