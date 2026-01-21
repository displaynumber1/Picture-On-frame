/**
 * Professional Translation Mapping
 * Maps Indonesian options to detailed English photographic descriptions
 * Used by generateProfessionalPrompt for natural language synthesis
 */

export const MAPPING: Record<string, string> = {
  // ========== MODEL TYPES ==========
  'Wanita': 'female model',
  'Pria': 'male model',
  'Anak LakiLaki': 'young boy model',
  'Anak Perempuan': 'young girl model',
  'Hewan': 'animal model',
  'Cartoon': 'cartoon character',

  // ========== CATEGORIES ==========
  'Fashion': 'fashion photography',
  'Beauty': 'beauty photography',
  'Tas': 'bag and accessories',
  'Sandal/Sepatu': 'footwear and shoes',
  'Aksesoris': 'fashion accessories',
  'Home Living': 'home and lifestyle products',
  'Food & Beverage': 'food and beverage',

  // ========== BACKGROUNDS ==========
  'Studio': 'clean professional studio backdrop with seamless white or gray background',
  'Kamar Aesthetic Women': 'women\'s bedroom with neutral tones and simple furniture',
  'Kamar Aesthetic Men': 'men\'s bedroom with minimalist design, neutral colors, and contemporary furniture',
  'Lantai Vynil & Gorden': 'vinyl flooring with curtain backdrop, creating a neutral interior setting',
  'Dinding, Karpet & Standing Lampu': 'interior space with textured wall, carpet, and standing lamp providing controlled lighting',
  'Minimalis': 'minimalist setting with clean lines, neutral tones, and uncluttered composition',
  'Jalan': 'urban street setting with natural outdoor lighting and neutral urban backdrop',
  'Warna (Custom)': 'custom colored background',
  'Meja Aesthetic': 'table setting with clean composition',
  'Karpet': 'textured carpet background providing neutral surface',
  'Gorden': 'curtain backdrop with fabric texture',
  'Tembok Polos': 'plain wall background with neutral texture',
  'Interior Mobil': 'car interior with upholstery, dashboard details, and neutral automotive environment',
  'Mall': 'shopping mall interior with contemporary architecture and retail setting',
  'Hapus Latar': 'isolated product on transparent background',
  'Upload Background': 'integrated into the provided custom background image',

  // ========== STYLES ==========
  'Studio Clean': 'studio clean photography style with controlled lighting and professional composition, shot on 85mm lens, shallow depth of field',
  'Lifestyle': 'lifestyle photography with everyday usage and practical product application, shot on 85mm lens, shallow depth of field',
  'Indoor/Outdoor': 'versatile indoor-outdoor photography blending interior and exterior elements, shot on 85mm lens, shallow depth of field',
  'Editorial': 'editorial fashion photography with balanced composition and professional aesthetic, shot on 85mm lens, shallow depth of field',
  'Beauty Glamour': 'beauty photography with clear presentation and professional quality, shot on 85mm lens, shallow depth of field',
  'Minimalist': 'minimalist photography style emphasizing simplicity and clean composition, shot on 85mm lens, shallow depth of field',
  'TikTok Trendy': 'social media style with balanced composition and contemporary appeal, shot on 85mm lens, shallow depth of field',
  'Cinematic': 'photography with controlled lighting and professional quality, shot on 85mm lens, shallow depth of field',
  'Neon Futuristic': 'neon aesthetic with vibrant colors and modern appearance, shot on 85mm lens, shallow depth of field',
  'Flat Lay': 'professional flat lay composition with carefully arranged products from top-down perspective, shot on 85mm lens, shallow depth of field',
  'Product-on-Table': 'product photography on table surface with clean staging, shot on 85mm lens, shallow depth of field',
  'Campaign Poster': 'campaign poster style with balanced composition and marketing appeal, shot on 85mm lens, shallow depth of field',
  'Macro': 'macro photography with close-up detail and texture focus, shot on 85mm lens, shallow depth of field',
  'Outdoor Cafe': 'outdoor café setting with natural lighting and neutral atmosphere, shot on 85mm lens, shallow depth of field',

  // ========== LIGHTING ==========
  'Natural Daylight': 'natural daylight illumination creating soft, even lighting with neutral color temperature, shot on 85mm lens, shallow depth of field',
  'Golden Hour': 'golden hour lighting with warm tones and gentle shadows, shot on 85mm lens, shallow depth of field',
  'Sunset Glow': 'sunset lighting with warm colors and neutral ambiance, shot on 85mm lens, shallow depth of field',
  'Dramatic Contrast': 'contrast lighting with shadows and highlights creating depth, shot on 85mm lens, shallow depth of field',
  'Low-key': 'low-key lighting with darker tones and controlled atmosphere, shot on 85mm lens, shallow depth of field',
  'High-key': 'high-key lighting with bright, even illumination and minimal shadows, shot on 85mm lens, shallow depth of field',
  'Diffused Window Light': 'diffused window light creating soft, natural illumination with gentle shadows, shot on 85mm lens, shallow depth of field',
  'Neon Ambience': 'neon lighting with vibrant colored illumination and contemporary appearance, shot on 85mm lens, shallow depth of field',
  'Warm Candle': 'candlelight with warm tones and controlled atmosphere, shot on 85mm lens, shallow depth of field',
  'Reflective Glow': 'reflective lighting with subtle highlights and clear quality, shot on 85mm lens, shallow depth of field',
  'Softbox': 'softbox studio lighting providing even, professional illumination with controlled shadows, shot on 85mm lens, shallow depth of field',
  'Ring Light': 'ring light illumination creating even facial lighting with catchlights in eyes, shot on 85mm lens, shallow depth of field',
  'Cool Tone': 'cool tone lighting with bluish-white color temperature and crisp appearance, shot on 85mm lens, shallow depth of field',

  // ========== CAMERA ANGLES ==========
  'Eye-Level': 'eye-level camera angle creating natural perspective',
  '45° Angle': '45-degree angle providing balanced composition with depth and dimension',
  'Over-the-Shoulder': 'over-the-shoulder angle creating clear perspective',
  'Macro Close-Up': 'macro close-up capturing detail and texture',
  'Medium Shot': 'medium shot framing with balanced composition',
  'Tight Portrait Crop': 'tight portrait crop focusing on facial features and neutral expression',
  'Dutch Angle': 'dutch angle with tilted composition creating balanced effect',
  'Top-Down Flat Lay': 'top-down flat lay angle providing comprehensive product overview',
  'Side Angle (30-60°)': 'side angle between 30-60 degrees offering dimensional perspective',
  'Front Symmetrical': 'front symmetrical angle with balanced, centered composition',
  'Wide Full Body': 'wide full body shot capturing complete subject and environment',
  'Bird\'s-Eye View': 'bird\'s-eye view from above creating comprehensive overhead perspective',

  // ========== INTERACTION TYPES ==========
  'Pegang 1 Tangan Wanita': 'female model holding the product with one hand, showing clear grip and product visibility',
  'Pegang 2 Tangan Wanita': 'female model holding the product with both hands, displaying clear product presentation',
  'Pegang 1 Tangan Pria': 'male model holding the product with one hand, demonstrating clear grip and product visibility',
  'Pegang 2 Tangan Pria': 'male model holding the product with both hands, showing clear product presentation',
  'Kaki Wanita': 'female model\'s foot positioned, showing product interaction with leg and foot',
  'Kaki Pria': 'male model\'s foot positioned, demonstrating product interaction with leg and foot',
  'Pegang Hanger dengan Produk': 'holding hanger with product, displaying clear product presentation and professional staging',
  'Tanpa Interaksi': 'product-focused composition without human interaction, emphasizing product details and design',

  // ========== POSE DESCRIPTIONS (from POSE_MAP) ==========
  // Model - Fashion (New Professional Names)
  'Standing Portrait': 'standing while holding the product, displaying neutral posture and clear product visibility',
  'Seated Presentation': 'sitting while holding the product, showing neutral posture and clear product presentation',
  'Direct Gaze': 'looking directly at the camera with neutral expression, showing clear product visibility',
  'Half Body Frame': 'half-body frame with neutral expression, showcasing clear product presentation',
  'Professional Stance': 'standing in professional style with neutral posture and clear product presentation',
  'Casual Moment': 'relaxed interaction with natural posture and clear product visibility',
  'Mirror Selfie': 'mirror selfie using iPhone, showing clear product presentation with relaxed interaction',
  'Front Camera Selfie': 'front-facing camera selfie with relaxed interaction and clear product visibility',
  'Close-Up Portrait': 'close-up frame featuring face with product, highlighting product details in clear composition',
  'Product Showcase': 'lifting product in front of chest to showcase details, creating focused presentation with product prominence',
  
  // Legacy support (backward compatibility)
  'Berdiri santai memegang produk': 'standing while holding the product, displaying neutral posture and clear product visibility',
  'Duduk sambil memegang produk': 'sitting while holding the product, showing neutral posture and clear product presentation',
  'Tatap kamera dengan senyum': 'looking directly at the camera with neutral expression, showing clear product visibility',
  'Half body dengan ekspresi percaya diri': 'half-body frame with neutral expression, showcasing clear product presentation',
  'Berdiri dengan gaya profesional': 'standing in professional style with neutral posture and clear product presentation',
  'Pose candid casual': 'relaxed interaction with natural posture and clear product visibility',
  'Mirror selfie menggunakan iPhone': 'mirror selfie using iPhone, showing clear product presentation with relaxed interaction',
  'Casual selfie menggunakan kamera depan': 'front-facing camera selfie with relaxed interaction and clear product visibility',
  'Close-up wajah bersama produk': 'close-up frame featuring face with product, highlighting product details in clear composition',
  'Mengangkat produk di depan dada untuk menampilkan detail': 'lifting product in front of chest to showcase details, creating focused presentation with product prominence',

  // Model - Beauty (New Professional Names)
  'Close-Up Beauty': 'close-up frame featuring face with product, highlighting product details in clear composition',
  'Natural Half Body': 'half-body frame with natural style, emphasizing clear product presentation',
  'Product Focus': 'holding product with focus on product details, ensuring product is the visual centerpiece',
  'Relaxed Seated': 'sitting while holding the product, displaying clear product presentation',
  
  // Legacy support
  'Half body with gaya natural': 'half-body frame with natural style, emphasizing clear product presentation',
  'Memegang produk dengan fokus pada produk': 'holding product with focus on product details, ensuring product is the visual centerpiece',
  'Duduk santai sambil memegang produk': 'sitting while holding the product, displaying clear product presentation',

  // Model - Tas (New Professional Names)
  'Standing with Bag': 'standing while holding the bag, showing clear product visibility',
  'Lifestyle Half Body': 'half-body frame with lifestyle style, showing everyday usage with clear product presentation',
  'Casual Seated': 'sitting with the bag, displaying clear product presentation',
  
  // Legacy support
  'Berdiri santai sambil memegang tas': 'standing while holding the bag, showing clear product visibility',
  'Half body dengan gaya lifestyle': 'half-body frame with lifestyle style, showing everyday usage with clear product presentation',
  'Duduk santai sambil membawa tas': 'sitting with the bag, displaying clear product presentation',

  // Model - Sandal/Sepatu (New Professional Names)
  'Natural Standing': 'standing while wearing the shoes, showing neutral posture and clear product visibility',
  'Walking Pose': 'walking with natural movement, showing clear product visibility and everyday usage',
  'Seated Wearing': 'sitting while wearing the shoes, displaying clear product presentation',
  
  // Legacy support
  'Berdiri natural mengenakan sepatu': 'standing while wearing the shoes, showing neutral posture and clear product visibility',
  'Pose berjalan santai': 'walking with natural movement, showing clear product visibility and everyday usage',
  'Duduk santai mengenakan sepatu': 'sitting while wearing the shoes, displaying clear product presentation',

  // Model - Aksesoris (New Professional Names)
  // Note: 'Close-Up Portrait' and 'Direct Gaze' already defined in Fashion section above
  'Hand Display': 'hand displaying jewelry, showcasing clear product presentation and detail',
  'Editorial Style': 'editorial style with balanced composition and professional aesthetic',
  
  // Legacy support
  'Tangan menampilkan perhiasan': 'hand displaying jewelry, showcasing clear product presentation and detail',
  'Gaya Editorial': 'editorial style with balanced composition and professional aesthetic',

  // Model - Home Living
  'Produk digunakan dalam aktivitas sehari-hari': 'product used in daily activities, showing everyday usage and practical product application',
  'Memegang produk tanpa fokus ke wajah': 'holding product without facial focus, emphasizing product details and design',

  // Model - Food & Beverage
  'Duduk menikmati produk': 'sitting with the product, displaying clear product visibility',
  'Pegang produk sambil tersenyum': 'holding product with neutral expression, creating clear product presentation',
  'Candid eating/drinking': 'eating or drinking with relaxed interaction, showing clear product visibility and everyday usage',

  // Non Model - Fashion
  'Pegang produk dengan satu tangan': 'holding product with one hand, displaying clear single-hand presentation',
  'Pegang produk dengan dua tangan': 'holding product with two hands, showing clear product presentation',
  'Pegang hanger dengan produk': 'holding hanger with product, displaying professional staging and clear presentation',
  'Produk digantung menggunakan hanger': 'product hanging from hanger, showing clear display and professional presentation',
  'Hanger digantung di standing rack': 'hanger hanging on standing rack, displaying professional retail presentation',
  'Hanger digantung di hook': 'hanger hanging on hook, showing simple, clear display',
  'Produk dilipat dan diletakkan di meja': 'product folded and placed on table, displaying organized presentation and clean composition',
  'Flatlay produk fashion': 'fashion product flat lay with professional top-down composition',

  // Non Model - Beauty
  'Tangan memegang produk': 'hand holding product, showcasing clear grip and product presentation',
  'Dua tangan menampilkan produk': 'two hands displaying product, showing clear product presentation and professional staging',
  'Produk diletakkan di meja aesthetic': 'product placed on table, displaying clean composition',
  'Produk didekatkan ke area wajah tanpa menampilkan wajah': 'product positioned near face area without showing face, emphasizing product details and application',
  'Flatlay produk beauty': 'beauty product flat lay with professional composition',

  // Non Model - Tas
  'Tangan memegang tas': 'hand holding bag, displaying clear grip and product presentation',
  'Dua tangan menampilkan tas': 'two hands displaying bag, showing clear product presentation and professional staging',
  'Tas digantung': 'bag hanging, displaying clear presentation and professional staging',
  'Tas diletakkan di meja aesthetic': 'bag placed on table, showing clean composition',
  'Tas disandarkan pada kursi atau properti': 'bag leaning against chair or prop, displaying clear product presentation',

  // Non Model - Sandal/Sepatu
  'Tangan Memegang Sepasang Sandal/Sepatu': 'hand holding a pair of sandals/shoes, displaying clear grip and product presentation',
  'Dua tangan menampilkan sepatu': 'two hands displaying shoes, showing clear product presentation and professional staging',
  'Kaki wanita berdiri natural mengenakan sepatu': 'female foot standing while wearing shoes, showing neutral posture and clear product visibility',
  'Kaki wanita melangkah': 'female foot stepping with natural movement, showing clear product visibility',
  'Kaki wanita dengan tumit terangkat': 'female foot with raised heel, displaying clear product presentation',
  'Kaki wanita naik tangga': 'female foot on stairs with natural movement, showing clear product visibility',
  'Kaki wanita berdiri simetris (dua kaki sejajar)': 'female feet standing symmetrically with both feet parallel, showing balanced stance and clear product visibility',
  'Kaki pria berdiri tegap mengenakan sepatu': 'male foot standing while wearing shoes, showing neutral posture and clear product visibility',
  'Kaki pria melangkah santai': 'male foot walking with natural movement, showing clear product visibility and everyday usage',
  'Kaki pria satu kaki maju ke depan': 'male foot with one foot forward, displaying clear product presentation',
  'Kaki pria berada di jalan atau tangga': 'male foot on street or stairs, showing neutral outdoor setting and clear product visibility',
  'Produk sepatu diletakkan di lantai': 'shoe product placed on floor, displaying clean composition and professional staging',
  'Produk sepatu disandarkan': 'shoe product leaning, showing clear product presentation',
  'Flatlay sepatu': 'shoe flat lay with professional top-down composition',
  'Gaya lifestyle di jalan atau tangga': 'lifestyle style on street or stairs, showing everyday usage with clear product visibility',

  // Non Model - Aksesoris
  'Tangan memegang produk (Aksesoris)': 'hand holding product, showcasing clear grip and product presentation',
  'Produk di meja aesthetic (Aksesoris)': 'product on table, displaying clean composition',
  'Detail tekstur close-up': 'texture detail close-up, emphasizing material quality and clear craftsmanship',
  'Flatlay aksesoris': 'accessories flat lay with professional composition',

  // Non Model - Home Living
  'Tangan memegang produk (Home Living)': 'hand holding product, showcasing clear grip and product presentation',
  'Dua tangan menampilkan produk (Home Living)': 'two hands displaying product, showing clear product presentation and professional staging',
  'Produk digunakan dalam konteks rumah': 'product used in home context, showing practical application and clear product visibility',

  // Non Model - Food & Beverage
  // Note: 'Tangan memegang produk', 'Dua tangan menampilkan produk', 'Produk diletakkan di meja' already defined above
  'Close-up tekstur makanan atau minuman': 'close-up texture of food or beverage, emphasizing material quality and clear details',
  'Flatlay food and beverage': 'food and beverage flat lay with professional composition',
  'Produk dalam setting meja makan': 'product in dining table setting, showing clear presentation',

  // ========== ASPECT RATIOS ==========
  '1:1': '1:1 square format',
  '1:1 (Square)': '1:1 square format',
  '2:3': '2:3 portrait format',
  '2:3 (Portrait)': '2:3 portrait format',
  '4:5': '4:5 portrait format',
  '4:5 (Portrait)': '4:5 portrait format',
  '16:9': '16:9 landscape format',
  '16:9 (Landscape)': '16:9 landscape format',
  '3:4': '3:4 portrait format',
  '3:4 (Portrait)': '3:4 portrait format',
  '4:3': '4:3 landscape format',
  '9:16': '9:16 vertical format',
  '9:16 (Story)': '9:16 vertical story format',

  // ========== SPECIAL VALUES ==========
  'Prompt Kustom': '',
  'Prompt Custom (bisa diedit)': '',
  'Custom': '',
};

/**
 * Get translated value from mapping
 * Returns the mapped value if found, otherwise returns the original value
 */
export function translateToEnglish(value: string): string {
  if (!value) return value;
  return MAPPING[value] || value;
}
