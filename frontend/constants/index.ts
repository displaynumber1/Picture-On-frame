export const BACKGROUND_OPTIONS = [
  "Studio",
  "Kamar Aesthetic Women",
  "Kamar Aesthetic Men",
  "Lantai Vynil & Gorden",
  "Dinding, Karpet & Standing Lampu",
  "Minimalis",
  "Jalan",
  "Meja Aesthetic",
  "Karpet",
  "Gorden",
  "Tembok Polos",
  "Interior Mobil",
  "Mall",
  "Hapus Latar",
  "Upload Background"
];

export const CONTENT_TYPES = ["Model", "Non Model"];

export const MODEL_TYPES = [
  "Wanita",
  "Pria",
  "Anak LakiLaki",
  "Anak Perempuan",
  "Hewan",
  "Cartoon"
];

export const CATEGORY_OPTIONS = [
  "Fashion",
  "Beauty",
  "Tas",
  "Sandal/Sepatu",
  "Aksesoris",
  "Home Living",
  "Food & Beverage"
];

export const INTERACTION_OPTIONS = [
  "Pegang 1 Tangan Wanita",
  "Pegang 2 Tangan Wanita",
  "Pegang 1 Tangan Pria",
  "Pegang 2 Tangan Pria",
  "Kaki Wanita",
  "Kaki Pria",
  "Pegang Hanger dengan Produk",
  "Tanpa Interaksi"
];

export const POSE_MAP: Record<string, Record<string, string[]>> = {
  "Model": {
    "Fashion": [
      "Standing Portrait",
      "Seated Presentation",
      "Direct Gaze",
      "Half Body Frame",
      "Professional Stance",
      "Casual Moment",
      "Mirror Selfie",
      "Front Camera Selfie",
      "Close-Up Portrait",
      "Product Showcase"
    ],
    "Beauty": [
      "Close-Up Beauty",
      "Natural Half Body",
      "Product Focus",
      "Relaxed Seated"
    ],
    "Tas": [
      "Standing with Bag",
      "Lifestyle Half Body",
      "Casual Moment",
      "Casual Seated"
    ],
    "Sandal/Sepatu": [
      "Natural Standing",
      "Walking Pose",
      "Seated Wearing",
      "Lifestyle Half Body"
    ],
    "Aksesoris": [
      "Close-Up Portrait",
      "Direct Gaze",
      "Hand Display",
      "Editorial Style"
    ],
    "Home Living": [
      "Standing Portrait",
      "Seated Presentation",
      "Lifestyle Usage",
      "Product Focus"
    ],
    "Food & Beverage": [
      "Seated Enjoying",
      "Direct Gaze",
      "Lifestyle Half Body",
      "Casual Moment"
    ]
  },
  "Non Model": {
    "Fashion": [
      "Pegang produk dengan satu tangan",
      "Pegang produk dengan dua tangan",
      "Pegang hanger dengan produk",
      "Produk digantung menggunakan hanger",
      "Hanger digantung di standing rack",
      "Hanger digantung di hook",
      "Produk dilipat dan diletakkan di meja",
      "Flatlay produk fashion"
    ],
    "Beauty": [
      "Tangan memegang produk",
      "Dua tangan menampilkan produk",
      "Produk diletakkan di meja aesthetic",
      "Produk didekatkan ke area wajah tanpa menampilkan wajah",
      "Flatlay produk beauty"
    ],
    "Tas": [
      "Tangan memegang tas",
      "Dua tangan menampilkan tas",
      "Tas digantung",
      "Tas diletakkan di meja aesthetic",
      "Tas disandarkan pada kursi atau properti"
    ],
    "Sandal/Sepatu": [
      "Tangan Memegang Sepasang Sandal/Sepatu",
      "Dua tangan menampilkan sepatu",
      "Kaki wanita berdiri natural mengenakan sepatu",
      "Kaki wanita melangkah",
      "Kaki wanita dengan tumit terangkat",
      "Kaki wanita naik tangga",
      "Kaki wanita berdiri simetris (dua kaki sejajar)",
      "Kaki pria berdiri tegap mengenakan sepatu",
      "Kaki pria melangkah santai",
      "Kaki pria satu kaki maju ke depan",
      "Kaki pria berada di jalan atau tangga",
      "Produk sepatu diletakkan di lantai",
      "Produk sepatu disandarkan",
      "Flatlay sepatu",
      "Gaya lifestyle di jalan atau tangga"
    ],
    "Aksesoris": [
      "Tangan memegang produk",
      "Produk di meja aesthetic",
      "Detail tekstur close-up",
      "Flatlay aksesoris"
    ],
    "Home Living": [
      "Tangan memegang produk",
      "Dua tangan menampilkan produk",
      "Tangan mengangkat produk untuk menampilkan detail",
      "Produk diletakkan di meja",
      "Produk diletakkan di lantai",
      "Produk digunakan tanpa menampilkan wajah",
      "Detail tekstur produk",
      "Flatlay produk home living"
    ],
    "Food & Beverage": [
      "Tangan memegang produk",
      "Dua tangan menampilkan produk",
      "Produk diletakkan di meja",
      "Close-up tekstur makanan atau minuman",
      "Flatlay food and beverage"
    ]
  }
};

export const STYLE_OPTIONS = [
  "Studio Clean",
  "Lifestyle",
  "Indoor/Outdoor",
  "Editorial",
  "Beauty Glamour",
  "Minimalist",
  "TikTok Trendy",
  "Cinematic",
  "Neon Futuristic",
  "Flat Lay",
  "Product-on-Table",
  "Campaign Poster",
  "Macro",
  "Outdoor Cafe"
];

export const LIGHTING_OPTIONS = [
  "Natural Daylight",
  "Golden Hour",
  "Sunset Glow",
  "Dramatic Contrast",
  "Low-key",
  "High-key",
  "Diffused Window Light",
  "Neon Ambience",
  "Warm Candle",
  "Reflective Glow",
  "Softbox",
  "Ring Light",
  "Cool Tone",
  "Editorial"
];

export const ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"];

export const CAMERA_ANGLES = [
  "Eye-Level",
  "45° Angle",
  "Over-the-Shoulder",
  "Macro Close-Up",
  "Medium Shot",
  "Tight Portrait Crop",
  "Dutch Angle",
  "Top-Down Flat Lay",
  "Side Angle (30-60°)",
  "Front Symmetrical",
  "Wide Full Body",
  "Bird's Eye View"
];
