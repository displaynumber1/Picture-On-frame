import { GenerationOptions } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const raw = await response.text();
    try {
      const json = JSON.parse(raw);
      if (json && typeof json === 'object') {
        return json.detail || json.message || json.error || JSON.stringify(json);
      }
      return JSON.stringify(json);
    } catch {
      return raw || '';
    }
  } catch {
    return '';
  }
}

const DEFAULT_IMAGE_SIZE = { width: 768, height: 1024 };

function mapAspectRatioToSize(aspectRatio?: string) {
  switch (aspectRatio) {
    case '1:1':
      return { width: 768, height: 768 };
    case '3:4':
      return { width: 768, height: 1024 };
    case '4:3':
      return { width: 1024, height: 768 };
    case '9:16':
      return { width: 720, height: 1280 };
    case '16:9':
      return { width: 1280, height: 720 };
    default:
      return DEFAULT_IMAGE_SIZE;
  }
}

const PRESET_ID_BY_LABEL: Record<string, string> = {
  'Studio': 'studio_wall_fullbody_01',
  'Tembok Polos': 'studio_wall_fullbody_01',
  'Minimalis': 'minimalist_corner_01',
  'Kamar Aesthetic Women': 'minimalist_corner_01',
  'Kamar Aesthetic Men': 'minimalist_corner_01',
  'Meja Aesthetic': 'table_aesthetic_01',
  'Mall': 'mall_corridor_01',
  'Jalan': 'street_sidewalk_01',
  'Lantai Vynil & Gorden': 'flatlay_vinyl_01',
  'Gorden': 'flatlay_vinyl_01',
  'Karpet': 'minimalist_corner_01',
  'Dinding, Karpet & Standing Lampu': 'minimalist_corner_01',
  'Interior Mobil': 'car_interior_front_01'
};

function presetIdFromLabel(label: string) {
  return PRESET_ID_BY_LABEL[label];
}

export interface FalGenerateRequest {
  prompt: string;
  content_type?: string;
  category?: string;
  style?: string;
  product_main_url: string;
  product_opt_url?: string;
  face_reference_url?: string;
  background_url?: string | null;
  background_mode?: 'preset' | 'upload' | 'none' | 'remove';
  background_preset_id?: string;
  image_size?: { width: number; height: number };
  strength?: number;
  // Legacy field untuk backward compatibility
  init_image_urls?: string[];
}

export interface FalGenerateResponse {
  images: string[];
  remaining_coins?: number;
  remaining_quota?: number; // Legacy field, kept for backward compatibility
}

/**
 * Generate images using fal API (fal-ai/flux-2/lora/edit)
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
  referenceImage?: string  // Legacy parameter untuk backward compatibility
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
    }

    if (!finalPrompt) {
      throw new Error('Prompt is required. Please provide either prompt or options.');
    }

    // Generate images in batches (fal generates 2 images per request)
    const imageUrls: string[] = [];
    const batches = Math.ceil(numImages / 2);
    
    for (let i = 0; i < batches; i++) {
      let response: Response;
      let requestBody: FalGenerateRequest | null = null;
      
      try {
        const productMainUrl = productImages && productImages.length > 0 ? productImages[0] : referenceImage;
        const productOptUrl = productImages && productImages.length > 1 ? productImages[1] : undefined;
        const backgroundChoice = options?.background || 'Studio';
        let backgroundMode: 'preset' | 'upload' | 'none' | 'remove' = 'none';
        let backgroundPresetId: string | undefined;

        if (backgroundChoice === 'Upload Background') {
          backgroundMode = 'upload';
        } else if (backgroundChoice === 'Hapus Latar') {
          backgroundMode = 'remove';
        } else if (backgroundChoice) {
          backgroundMode = 'preset';
          backgroundPresetId = presetIdFromLabel(backgroundChoice);
        }

        const backgroundUrl = backgroundImage || null;

        if (!productMainUrl) {
          throw new Error('Produk utama wajib diupload terlebih dahulu.');
        }

        if (backgroundMode === 'preset' && !backgroundPresetId) {
          throw new Error('Background preset tidak dikenal. Silakan pilih preset yang valid.');
        }
        if (backgroundMode === 'upload' && !backgroundUrl) {
          throw new Error('Background wajib diupload jika memilih upload background.');
        }

        requestBody = {
          prompt: finalPrompt,
          content_type: options?.contentType,
          category: options?.category,
          style: options?.style,
          product_main_url: productMainUrl,
          product_opt_url: productOptUrl,
          face_reference_url: faceImage || undefined,
          background_url: backgroundUrl,
          background_mode: backgroundMode,
          background_preset_id: backgroundPresetId,
          image_size: mapAspectRatioToSize(options?.aspectRatio),
        };

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
    console.error('Error generating images with fal:', error);
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
    throw new Error('fal generation failed');
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
