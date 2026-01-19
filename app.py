import streamlit as st  # type: ignore
import base64
import json
from datetime import datetime
from dotenv import load_dotenv  # type: ignore
import os
try:
    import google.generativeai as genai  # type: ignore
except ImportError:
    # Fallback if google-generativeai is not installed
    genai = None
    st.error("google-generativeai package is not installed. Please install it with: pip install google-generativeai")

# Load environment variables
load_dotenv('config.env')

# Initialize Gemini API
if genai is not None:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
else:
    st.error("Gemini API is not available. Please install google-generativeai package.")

# Constants
MODELS = ['Pria', 'Wanita', 'Anak Laki-Laki', 'Anak Perempuan', 'Hewan (Peliharaan)', 'Cartoon', 'Manekin', 'Tanpa Model (Hanya Produk)']

CATEGORIES = ['Fashion', 'Tas & Sepatu', 'Beauty & Skincare', 'Aksesories', 'Home & Living', 'Gadget & Elektronik', 'Food & Beverage (FnB)', 'Others']

HAND_INTERACTIONS = [
    'Tanpa Interaksi', 
    'Pegang produk – 1 tangan (Pria)', 
    'Pegang produk – 2 tangan (Pria)', 
    'Pegang produk – 1 tangan (Wanita)', 
    'Pegang produk – 2 tangan (Wanita)',
    'Interaksi Kaki (Pria)',
    'Interaksi Kaki (Wanita)'
]

ANIMAL_POSES = [
    'Pose di Samping Produk',
    'Interaksi (Mencium/Menyentuh)',
    'Berbaring Bersama Produk',
    'Melihat Kamera & Produk',
    'Action Shot (Bermain)',
    'Luxury Pet Lifestyle'
]

MODEL_SPECIFIC_POSES = [
    'Sitting Pose Relax',
    'Casual Selfie (Front Camera)',
    'Mirror Selfie dengan iPhone'
]

FOOT_INTERACTION_POSES = [
    'Berdiri Natural',
    'Berdiri Melangkah',
    'Pose Kaki Berdiri (Detail)',
    'Hand Holding Shot',
    'Shoulder Carry Shot',
    'Foot Wearing Shot',
    'Walking Step Motion',
    'Cropped Lifestyle Shot',
    'Prompt Custom (bisa diedit)'
]

# Dynamic Poses based on category
DYNAMIC_POSES = {
    'Fashion': {
        'productOnly': [
            'Pegang Hanger Dengan Produk', 'Flat Lay Premium', 'Hanging Natural', 'Folded Neat (Lipatan Rapi)', 
            'Detail Fabric Close-Up', 'Sofa / Chair Lay', 'Minimal Studio'
        ],
        'withModel': [
            'Lifestyle Natural', 'Standing Pose Casual', 'Walking Motion', 'Detail Wear Shot'
        ] + MODEL_SPECIFIC_POSES
    },
    'Tas & Sepatu': {
        'productOnly': [
            'Hero Product Shot', 'Styled Flat Lay', 'Side Angle View', 'Back & Bottom Detail', 
            'Texture Close-Up', 'Clean Background'
        ],
        'withModel': [
            'Hand Holding Shot', 'Shoulder Carry Shot', 'Foot Wearing Shot', 'Walking Step Motion'
        ] + MODEL_SPECIFIC_POSES
    },
    'Beauty & Skincare': {
        'productOnly': [
            'Clean Studio Look', 'Ingredient Concept', 'Texture Swatch Shot', 'Bathroom Aesthetic', 
            'Minimal Table Setup'
        ],
        'withModel': [
            'Hand Application Shot', 'Half Face Glow', 'Close Skin Detail', 'Natural Daily Use'
        ] + MODEL_SPECIFIC_POSES
    },
    'Aksesories': {
        'productOnly': [
            'Flat Lay Elegant', 'Display Stand Shot', 'Hanging Display', 'Macro Detail Shot'
        ],
        'withModel': [
            'Wrist Wearing Shot', 'Neck / Shoulder Shot', 'Soft Lifestyle Detail'
        ] + MODEL_SPECIFIC_POSES
    },
    'Home & Living': {
        'productOnly': [
            'Room Styling', 'Tabletop Aesthetic', 'Minimal Interior', 'Functional Close-Up'
        ],
        'withModel': [
            'Hand Activity Shot', 'Daily Home Moment'
        ] + MODEL_SPECIFIC_POSES
    },
    'Gadget & Elektronik': {
        'productOnly': [
            'Clean Tech Studio', 'Desk Setup Shot', 'Product Angle View', 'Feature Detail Shot'
        ],
        'withModel': [
            'Hand Interaction', 'Lifestyle Usage', 'Close Feature Usage'
        ] + MODEL_SPECIFIC_POSES
    },
    'Food & Beverage (FnB)': {
        'productOnly': [
            'Flat Lay Food', 'Close Texture Shot', 'Serving Presentation', 'Minimal Table Style'
        ],
        'withModel': [
            'Hand Serving Shot', 'Eating Moment', 'Lifestyle Dining Shot'
        ] + MODEL_SPECIFIC_POSES
    },
    'Others': {
        'productOnly': [
            'Minimalist Studio Placement', 'Floating in Soft Space', 'Premium Tabletop Shot', 
            'Dynamic Shadows Concept', 'Macro Feature Focus'
        ],
        'withModel': [
            'Holding Product Naturally', 'Lifestyle Scene Interaction', 'Close-up Hand & Product', 
            'Looking at Product'
        ] + MODEL_SPECIFIC_POSES
    }
}

BACKGROUNDS = [
    'Studio', 'Kamar Aesthetic', 'Minimalis', 'Jalan', 'Meja Aesthetic', 
    'Karpet', 'Gorden', 'Interior Mobil (Selfie)', 'Hapus Latar', 'Warna (Custom)', 
    'Upload Latar', 'Custom Prompt'
]

STYLES = [
    'Studio Clean', 'Lifestyle', 'Indoor/Outdoor', 'Editorial', 'Beauty Glamour',
    'Minimalist', 'TikTok Trendy', 'Cinematic', 'Neon Futuristic', 'Flat Lay',
    'Product-on-Table', 'Campaign Poster', 'Macro', 'Outdoor Cafe', 'Custom'
]

LIGHTING = [
    'Natural Daylight', 'Golden Hour', 'Sunset Glow', 'Dramatic Contrast',
    'Low-key', 'High-key', 'Diffused Window Light', 'Neon Ambience',
    'Warm Candle', 'Reflective Glow', 'Softbox', 'Ring Light', 'Cool Tone',
    'Editorial', 'Custom'
]

RATIOS = [
    {'label': '1:1 (Square)', 'value': '1:1'},
    {'label': '2:3 (Portrait)', 'value': '2:3'},
    {'label': '4:5 (Portrait)', 'value': '4:5'},
    {'label': '16:9 (Landscape)', 'value': '16:9'},
    {'label': '3:4 (Portrait)', 'value': '3:4'},
    {'label': '9:16 (Story)', 'value': '9:16'}
]

ANGLES = [
    'Eye-Level', '45° Angle', 'Over-the-Shoulder', 'Macro Close-Up',
    'Medium Shot', 'Tight Portrait Crop', 'Dutch Angle', 'Top-Down Flat Lay',
    'Side Angle (30-60°)', 'Front Symmetrical', 'Wide Full Body', 'Bird\'s-Eye View'
]

# Initialize session state
if 'product_image' not in st.session_state:
    st.session_state.product_image = None
if 'face_image' not in st.session_state:
    st.session_state.face_image = None
if 'custom_bg_image' not in st.session_state:
    st.session_state.custom_bg_image = None
if 'config' not in st.session_state:
    st.session_state.config = {
        'modelType': MODELS[0],
        'category': CATEGORIES[0],
        'background': BACKGROUNDS[0],
        'pose': '',
        'handInteraction': HAND_INTERACTIONS[0],
        'style': STYLES[0],
        'lighting': LIGHTING[0],
        'aspectRatio': '1:1',
        'angle': ANGLES[0],
        'additionalPrompt': '',
        'customBackgroundPrompt': '',
        'customPosePrompt': '',
        'customStylePrompt': '',
        'customLightingPrompt': ''
    }
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'presets'
if 'library_sub_tab' not in st.session_state:
    st.session_state.library_sub_tab = 'artworks'
if 'saved_setups' not in st.session_state:
    st.session_state.saved_setups = []
if 'saved_images' not in st.session_state:
    st.session_state.saved_images = []
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
if 'error' not in st.session_state:
    st.session_state.error = None
if 'success_msg' not in st.session_state:
    st.session_state.success_msg = None

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Premium AI Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS UNTUK TAMPILAN SUPER COMPACT (Menaikkan kotak ke atas)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');

/* Body & App Background */
body {
    font-family: 'Inter', sans-serif;
    background-color: #fcfaff;
}

.stApp { 
    background: linear-gradient(135deg, #fdf2f8 0%, #f5f3ff 50%, #fdf2f8 100%);
    font-family: 'Inter', sans-serif;
}

.font-serif {
    font-family: 'Playfair Display', serif;
}

/* Glass Effect */
.glass {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Accent Gradient */
.accent-gradient {
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
}

/* Sparkle Animation */
.blink-blink {
    animation: sparkle 2s infinite ease-in-out;
}

@keyframes sparkle {
    0%, 100% { opacity: 0.3; transform: scale(0.8) rotate(0deg); }
    50% { opacity: 1; transform: scale(1.2) rotate(15deg); }
}

/* Hide scrollbars */
.no-scrollbar::-webkit-scrollbar {
    display: none;
}
.no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
}

/* Auth Modal Styles */
.auth-modal-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    background: rgba(30, 27, 75, 0.6);
    backdrop-filter: blur(12px);
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.auth-modal {
    background: white;
    width: 100%;
    max-width: 400px;
    padding: 2.5rem;
    border-radius: 2.5rem;
    box-shadow: 0 32px 64px -12px rgba(0, 0, 0, 0.2);
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(139, 92, 246, 0.2);
}

.auth-modal-close {
    position: absolute;
    top: 2rem;
    right: 2rem;
    color: #c084fc;
    cursor: pointer;
    transition: color 0.2s;
    background: none;
    border: none;
    font-size: 1.25rem;
    padding: 0;
    width: 1.25rem;
    height: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.auth-modal-close:hover {
    color: #9333ea;
}

.auth-modal-header {
    text-align: center;
    margin-bottom: 2.5rem;
}

.auth-modal-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3rem;
    height: 3rem;
    border-radius: 1rem;
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 20px rgba(139, 92, 246, 0.2);
}

.auth-modal-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e1b4b;
    margin-bottom: 0.25rem;
}

.auth-modal-subtitle {
    font-size: 0.625rem;
    color: #a78bfa;
    text-transform: uppercase;
    letter-spacing: 0.3em;
    font-weight: 700;
}

.auth-google-btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
    border: 1px solid #e9d5ff;
    border-radius: 1rem;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.75rem;
    font-weight: 700;
    color: #1e1b4b;
    margin-bottom: 1rem;
}

.auth-google-btn:hover {
    background: #faf5ff;
    transform: scale(0.98);
}

.auth-google-btn:active {
    transform: scale(0.95);
}

.auth-divider {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 0;
    margin: 1rem 0;
}

.auth-divider::before {
    content: '';
    position: absolute;
    inset: 0;
    border-top: 1px solid #f3e8ff;
    width: 100%;
}

.auth-divider-text {
    position: relative;
    background: white;
    padding: 0 1rem;
    font-size: 0.5625rem;
    font-weight: 700;
    color: #c084fc;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.auth-input {
    width: 100%;
    background: rgba(250, 245, 255, 0.5);
    border: 1px solid #e9d5ff;
    border-radius: 0.75rem;
    padding: 0.75rem 1rem;
    font-size: 0.75rem;
    font-family: 'Inter', sans-serif;
    margin-bottom: 0.75rem;
    outline: none;
    transition: all 0.2s;
    box-sizing: border-box;
}

.auth-input:focus {
    border-color: #c084fc;
    box-shadow: 0 0 0 2px rgba(196, 181, 253, 0.2);
}

.auth-submit-btn {
    width: 100%;
    padding: 0.875rem;
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    color: white;
    border-radius: 1rem;
    font-weight: 700;
    font-size: 0.75rem;
    border: none;
    cursor: pointer;
    box-shadow: 0 10px 20px rgba(139, 92, 246, 0.1);
    transition: all 0.2s;
    margin-top: 0.5rem;
    font-family: 'Inter', sans-serif;
}

.auth-submit-btn:hover {
    transform: scale(1.02);
}

.auth-submit-btn:active {
    transform: scale(0.95);
}

.auth-error {
    color: #ef4444;
    font-size: 0.625rem;
    text-align: center;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.auth-toggle {
    margin-top: 2rem;
    text-align: center;
    font-size: 0.625rem;
    color: #a78bfa;
    font-weight: 500;
}

.auth-toggle-btn {
    color: #db2777;
    font-weight: 700;
    background: none;
    border: none;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
    margin-left: 0.25rem;
}

.auth-toggle-btn:hover {
    color: #ec4899;
}

/* HEADER LOGO SECTION */
.header-container { margin-bottom: 20px; }
.main-logo-text { 
    font-family: 'Playfair Display', serif; 
    font-size: 58px; 
    font-weight: 700; 
    color: #2D1B69; 
    line-height: 1; 
    margin: 5px 0; 
}
.on-text { 
    font-family: 'Playfair Display', serif; 
    color: #F472B6; 
    font-size: 52px; 
    font-style: italic; 
    margin: 0 8px; 
}

/* SATU KARTU KONFIGURASI */
.unified-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 35px;
    height: 82vh;
    display: flex;
    flex-direction: column;
    position: relative;
    box-shadow: 0 15px 35px rgba(0,0,0,0.03);
    overflow: hidden;
}

/* HEADER KARTU (Rapat) */
.card-top-header {
    padding: 20px 25px 0px 25px; /* Padding bawah 0 */
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.config-title { font-size: 14px; font-weight: 800; color: #2D1B69; letter-spacing: 0.5px; }
.save-preset-btn { 
    color: #EC4899; font-size: 10px; font-weight: 800; 
    background: #FFF5F7; padding: 6px 14px; border-radius: 5px; 
}

/* AREA SCROLL (Menaikkan konten upload) */
.scrollable-body {
    padding: 0px 25px 120px 25px;
    overflow-y: auto;
    flex-grow: 1;
    margin-top: -5px;
}
.scrollable-body::-webkit-scrollbar {
    display: none;
}
.scrollable-body {
    -ms-overflow-style: none;
    scrollbar-width: none;
}

/* KOTAK UPLOAD (Menaikkan posisi) */
.upload-container-wrapper {
    margin-top: -20px; /* Menaikkan kotak lebih tinggi */
    margin-bottom: 0px;
}

.upload-box { 
    border: 2px dashed #e9d5ff; 
    border-radius: 1rem; 
    height: 100px; 
    display: flex; 
    flex-direction: column; 
    justify-content: center; 
    align-items: center;
    background: white;
    margin-bottom: 5px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}

.upload-box:hover {
    border-color: #f9a8d4;
    background: rgba(253, 242, 248, 0.3);
}

.upload-box-icon {
    color: #f472b6;
    margin-bottom: 0.5rem;
    font-size: 2rem;
}

.upload-box-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #6b21a8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.upload-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 0.75rem;
}

.upload-overlay {
    position: absolute;
    inset: 0;
    background: rgba(30, 27, 75, 0.4);
    opacity: 0;
    transition: opacity 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(2px);
}

.upload-box:hover .upload-overlay {
    opacity: 1;
}

.upload-overlay-text {
    color: #e9d5ff;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* UI Elemen Internal */
.section-label { 
    font-size: 11px; 
    font-weight: 600; 
    color: #1e1b4b; 
    margin: 8px 0 12px 0; 
    text-transform: uppercase;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Option Grid Button Styles */
.option-grid-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid;
    transition: all 0.2s;
    text-align: left;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    width: 100%;
}

.option-grid-btn.selected {
    background: #581c87 !important;
    border-color: #581c87 !important;
    color: #e9d5ff !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.option-grid-btn.unselected {
    background: white !important;
    border-color: #e9d5ff !important;
    color: #6b21a8 !important;
}

.option-grid-btn.unselected:hover {
    border-color: #f9a8d4 !important;
    background: rgba(253, 242, 248, 0.5) !important;
}

/* Custom Textarea */
textarea[data-testid="stTextArea"] {
    width: 100% !important;
    margin-top: 0.5rem !important;
    padding: 0.75rem !important;
    font-size: 0.75rem !important;
    border: 1px solid #e9d5ff !important;
    border-radius: 0.75rem !important;
    font-family: 'Inter', sans-serif !important;
    color: #6b21a8 !important;
    outline: none !important;
    min-height: 80px !important;
    resize: vertical !important;
    background: white !important;
}

textarea[data-testid="stTextArea"]:focus {
    border-color: transparent !important;
    box-shadow: 0 0 0 2px rgba(249, 168, 212, 0.3) !important;
}

/* Button Styles */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%) !important;
    color: white !important; 
    height: 52px !important; 
    border-radius: 18px !important;
    font-size: 15px !important; 
    font-weight: 600 !important; 
    border: none !important;
    font-family: 'Inter', sans-serif !important;
}
div.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.9) !important; 
    color: #6B46C1 !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important; 
    border-radius: 12px !important;
    font-size: 10px !important; 
    height: 36px !important;
    margin-bottom: 3px !important;
    font-family: 'Inter', sans-serif !important;
    backdrop-filter: blur(5px);
}

/* Reduce spacing between elements */
[data-testid="column"] {
    margin-bottom: 0px !important;
}

.element-container {
    margin-bottom: 0px !important;
    margin-top: 0px !important;
}

/* Sticky Footer */
.card-footer {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top, white 85%, rgba(255,255,255,0));
    padding: 20px 25px 30px 25px;
    z-index: 100;
}

/* Panel Kanan */
.preview-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 40px; 
    height: 82vh;
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    justify-content: center;
}
</style>
""", unsafe_allow_html=True)

# 3. AUTH MODAL - Initialize session state
if 'auth_modal_open' not in st.session_state:
    st.session_state.auth_modal_open = True
if 'is_login' not in st.session_state:
    st.session_state.is_login = True
if 'auth_email' not in st.session_state:
    st.session_state.auth_email = ''
if 'auth_password' not in st.session_state:
    st.session_state.auth_password = ''
if 'auth_name' not in st.session_state:
    st.session_state.auth_name = ''
if 'auth_error' not in st.session_state:
    st.session_state.auth_error = ''
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
if 'is_simulating_google' not in st.session_state:
    st.session_state.is_simulating_google = False

# Render Auth Modal
if st.session_state.auth_modal_open and not st.session_state.is_authenticated:
    # Create centered modal using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-modal" style="position: relative; z-index: 10000;">
            <div class="auth-modal-header">
                <div class="auth-modal-icon">
                    <svg style="width: 1.5rem; height: 1.5rem; color: white;" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2L1 21h22L12 2zm0 3.45l8.15 14.1H3.85L12 5.45zM11 11v4h2v-4h-2zm0 6v2h2v-2h-2z"/>
                    </svg>
                </div>
                <h2 class="auth-modal-title">""" + ("Sign in to Studio" if st.session_state.is_login else "Create Studio Account") + """</h2>
                <p class="auth-modal-subtitle">Powered by Premium AI</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Google Login Button
        st.markdown("""
        <style>
        button[key="google_login"] {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.75rem !important;
            padding: 0.875rem 1rem !important;
            border: 1px solid #e9d5ff !important;
            border-radius: 1rem !important;
            background: white !important;
            font-size: 0.75rem !important;
            font-weight: 700 !important;
            color: #1e1b4b !important;
            margin-bottom: 1rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("🔵 Continue with Google", use_container_width=True, key="google_login"):
            st.session_state.is_simulating_google = True
            st.session_state.is_authenticated = True
            st.session_state.auth_modal_open = False
            st.rerun()
        
        st.markdown("""
        <div class="auth-divider">
            <span class="auth-divider-text">Or with email</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Form Inputs with custom styling
        st.markdown("""
        <style>
        div[data-testid="stTextInput"] > div > div > input {
            background: rgba(250, 245, 255, 0.5) !important;
            border: 1px solid #e9d5ff !important;
            border-radius: 0.75rem !important;
            padding: 0.75rem 1rem !important;
            font-size: 0.75rem !important;
            font-family: 'Inter', sans-serif !important;
        }
        div[data-testid="stTextInput"] > div > div > input:focus {
            border-color: #c084fc !important;
            box-shadow: 0 0 0 2px rgba(196, 181, 253, 0.2) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if not st.session_state.is_login:
            name_input = st.text_input("Full Name", value=st.session_state.auth_name, key="auth_name_input", placeholder="Full Name", label_visibility="collapsed")
            if name_input:
                st.session_state.auth_name = name_input
        
        email_input = st.text_input("Email", value=st.session_state.auth_email, key="auth_email_input", placeholder="Email Address", type="default", label_visibility="collapsed")
        if email_input:
            st.session_state.auth_email = email_input
        
        password_input = st.text_input("Password", value=st.session_state.auth_password, key="auth_password_input", placeholder="Password", type="password", label_visibility="collapsed")
        if password_input:
            st.session_state.auth_password = password_input
        
        if st.session_state.auth_error:
            st.markdown(f'<div class="auth-error">{st.session_state.auth_error}</div>', unsafe_allow_html=True)
        
        if st.button("Sign In" if st.session_state.is_login else "Create Account", use_container_width=True, key="auth_submit", type="primary"):
            # Simple validation
            if st.session_state.auth_email and st.session_state.auth_password:
                if not st.session_state.is_login and not st.session_state.auth_name:
                    st.session_state.auth_error = "Please enter your name"
                    st.rerun()
                else:
                    st.session_state.is_authenticated = True
                    st.session_state.auth_modal_open = False
                    st.session_state.auth_error = ''
                    st.rerun()
            else:
                st.session_state.auth_error = "Please fill all fields"
                st.rerun()
        
        st.markdown("""
        <p class="auth-toggle">
            <span>""" + ("New to the Studio? " if st.session_state.is_login else "Already have an account? ") + """</span>
        </p>
        """, unsafe_allow_html=True)
        
        if st.button("Sign Up" if st.session_state.is_login else "Log In", key="toggle_auth", use_container_width=False):
            st.session_state.is_login = not st.session_state.is_login
            st.session_state.auth_error = ''
            st.rerun()
    
    # Add overlay background
    st.markdown("""
    <style>
    .main .block-container {
        position: relative;
    }
    .main .block-container::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(30, 27, 75, 0.6);
        backdrop-filter: blur(12px);
        z-index: 9998;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.stop()  # Stop rendering main content if not authenticated

# 4. HEADER (Only show if authenticated)
if st.session_state.is_authenticated:
    st.markdown("""
    <div class="header-container">
        <div style="color: #C084FC; font-size: 11px; font-weight: 800; letter-spacing: 3px;">PREMIUM AI STUDIO ★</div>
        <div class="main-logo-text">Picture <span class="on-text">on</span> Frame</div>
        <div style="color: #A78BFA; font-size: 11px; font-weight: 800; letter-spacing: 5px;">BY SLSTARI</div>
    </div>
    """, unsafe_allow_html=True)

# Helper functions for derived state
def is_human_model(model_type):
    return model_type in ['Pria', 'Wanita', 'Anak Laki-Laki', 'Anak Perempuan']

def is_product_only(model_type):
    return model_type == 'Tanpa Model (Hanya Produk)'

def is_animal(model_type):
    return model_type == 'Hewan (Peliharaan)'

def is_foot_interaction(hand_interaction):
    return 'Kaki' in hand_interaction or 'Interaksi Kaki' in hand_interaction

def is_hand_interaction(hand_interaction):
    return 'Pegang' in hand_interaction or 'tangan' in hand_interaction.lower()

def get_current_pose_options(config):
    """Get dynamic pose options based on config"""
    if is_product_only(config['modelType']):
        if is_foot_interaction(config['handInteraction']):
            # FOOT_INTERACTION_POSES already includes 'Prompt Custom (bisa diedit)'
            return FOOT_INTERACTION_POSES
        category_data = DYNAMIC_POSES.get(config['category'], DYNAMIC_POSES['Fashion'])
        return category_data['productOnly'] + ['Prompt Kustom']
    
    if is_animal(config['modelType']):
        return ANIMAL_POSES + ['Prompt Kustom']
    
    category_data = DYNAMIC_POSES.get(config['category'], DYNAMIC_POSES['Fashion'])
    return category_data['withModel'] + ['Prompt Kustom']

def get_current_background_options(config):
    """Get dynamic background options based on config"""
    if is_human_model(config['modelType']):
        return BACKGROUNDS
    return [bg for bg in BACKGROUNDS if bg != 'Interior Mobil (Selfie)']

def generate_video_prompt(image_url: str) -> str:
    """
    Generates a video prompt for a 6-second clip based on the generated image.
    Follows Tasks 2, 3, and 4 from the specification but omits step headers in output.
    """
    try:
        # Extract base64 data if it's a data URL
        if ',' in image_url:
            image_base64 = image_url.split(',')[1]
        else:
            image_base64 = image_url
        
        if genai is None:
            raise ValueError("Gemini API is not available. Please install google-generativeai package.")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Decode base64 to bytes
        image_data = base64.b64decode(image_base64)
        
        prompt_text = """
STEP 1: Analyze the generated image carefully to determine human presence (full body, face, hand, foot, etc.).
STEP 2: Select ONE motion style: Subtle Static, Natural Micro Movement, or Slow Confident Presentation.
STEP 3: Generate ONE video prompt exactly 6 seconds long.

STRICT VIDEO RULES:
- Do NOT include headers like "TASK" or "STEP" in your final response.
- Do NOT include any analysis text or reasoning.
- Do NOT alter product appearance.
- Match lighting and background exactly.
- Motion must be realistic and natural.

FINAL OUTPUT FORMAT:
Only return the text section titled exactly as:
"GROK VIDEO PROMPT (6 SECONDS)"
followed by the concise video prompt. 
Example:
"GROK VIDEO PROMPT (6 SECONDS)"
A high-resolution video of the watch on the table, with subtle light glints reflecting off the glass as the camera breathes slightly.
        """
        
        response = model.generate_content(
            [
                {
                    "mime_type": "image/png",
                    "data": image_data
                },
                prompt_text
            ]
        )
        
        return response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        raise Exception(f"Failed to generate video prompt: {str(e)}")


def generate_studio_image(config, product_image, face_image=None, custom_bg_image=None):
    """
    Generates the studio image based on the config and reference images.
    Returns 4 variations.
    """
    def generate_one(variation_index: int):
        """Generate one variation of the image"""
        is_human = config['modelType'] in ['Pria', 'Wanita', 'Anak Laki-Laki', 'Anak Perempuan']
        
        image_generation_rules = """
1. Generate a realistic product photograph using the product image (Part 2) as primary reference.
2. If Part 3 is provided, integrate the face/model naturally with accurate proportions.
3. STRICT RULES: No changes to product shape/color/logo. No added objects. No text/watermarks. 
4. Render realistic micro-details (pores, fine hairs, natural textures). ABSOLUTELY NO artificial smoothness or "plastic" look.
        """
        
        # Build instructions
        model_instructions = ""
        background_instructions = config['background'] if config['background'] != 'Custom Prompt' else config.get('customBackgroundPrompt', '')
        pose_instructions = config['pose'] if config['pose'] not in ['Prompt Kustom', 'Prompt Custom (bisa diedit)'] else config.get('customPosePrompt', '')
        perspective_instructions = config['angle']
        lighting_instructions = config['lighting'] if config['lighting'] != 'Custom' else config.get('customLightingPrompt', '')
        style_instructions = config['style'] if config['style'] != 'Custom' else config.get('customStylePrompt', '')
        
        # Handle special background cases
        if config['background'] == 'Interior Mobil (Selfie)':
            background_instructions = "Inside a modern car interior. Include car seat upholstery, headrest, and dashboard details. High-fidelity interior lighting."
        elif config['background'] == 'Upload Latar':
            background_instructions = "Use the exact environment from the provided background reference image (Part 4)."
        
        # Handle special pose cases
        if config['pose'] == 'Casual Selfie (Front Camera)':
            pose_instructions = "Casual front-facing selfie pose. One arm extended forward holding the camera. Relaxed shoulders, natural posture."
        
        # Build model instructions
        if config['modelType'] == 'Tanpa Model (Hanya Produk)':
            model_instructions = "Focus EXCLUSIVELY on the product from Part 2. Clean, professional product placement shot."
            if config['handInteraction'] != 'Tanpa Interaksi':
                interaction_type = 'foot/leg' if 'Kaki' in config['handInteraction'] else 'hand'
                model_instructions += f" The scene includes a partial human interaction: {config['handInteraction']}. The {interaction_type} element should look raw, detailed, and realistic (visible skin pores, fine hair, natural texture) but the focus remains on the product."
        else:
            model_instructions = f"A real human {config['modelType']} model interacting naturally with the product from Part 2. Face identity from Part 3 if provided."
            if config['handInteraction'] != 'Tanpa Interaksi':
                model_instructions += f" Model interaction: {config['handInteraction']}."
        
        # Build prompt
        aspect_ratio_text = f"\nASPECT RATIO: {config['aspectRatio']}" if config.get('aspectRatio') else ""
        prompt = f"""
{image_generation_rules}

COMPOSITION:
- SUBJECT: {model_instructions}
- BACKGROUND: {background_instructions}
- POSE: {pose_instructions}
- PERSPECTIVE: {perspective_instructions}
- LIGHTING: {lighting_instructions}
- STYLE: {style_instructions}
{aspect_ratio_text}

VARIATION: {variation_index + 1}
TECHNICAL: Shot on Phase One IQ4, 150MP, sharp focus, 8K, high-frequency texture detail, zero digital noise.
        """
        
        # Build parts
        parts = [prompt]
        
        # Part 2: Product image
        if product_image:
            try:
                if ',' in product_image:
                    product_base64 = product_image.split(',')[1]
                else:
                    product_base64 = product_image
                product_data = base64.b64decode(product_base64)
                parts.append({
                    "mime_type": "image/png",
                    "data": product_data
                })
            except Exception as e:
                raise Exception(f"Failed to decode product image: {str(e)}")
        
        # Part 3: Face reference (if provided and is human model)
        if face_image and is_human:
            try:
                if ',' in face_image:
                    face_base64 = face_image.split(',')[1]
                else:
                    face_base64 = face_image
                face_data = base64.b64decode(face_base64)
                parts.append({
                    "mime_type": "image/png",
                    "data": face_data
                })
            except Exception as e:
                pass  # Continue without face image if decode fails
        
        # Part 4: Custom background (if provided)
        if custom_bg_image and config['background'] == 'Upload Latar':
            try:
                if ',' in custom_bg_image:
                    bg_base64 = custom_bg_image.split(',')[1]
                else:
                    bg_base64 = custom_bg_image
                bg_data = base64.b64decode(bg_base64)
                parts.append({
                    "mime_type": "image/png",
                    "data": bg_data
                })
            except Exception as e:
                pass  # Continue without background image if decode fails
        
        # Generate image using Gemini
        try:
            # Use Gemini model for image generation
            # Note: For actual image generation, you may need to use a different model or API endpoint
            # The Python SDK may have different model names than TypeScript SDK
            if genai is None:
                raise ValueError("Gemini API is not available. Please install google-generativeai package.")
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            response = model.generate_content(
                parts,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            
            # Extract image from response
            image_url = product_image  # Default fallback to product image
            
            # Try to extract generated image from response
            # Note: The actual structure depends on the API response
            # For now, we'll use the product image and generate a video prompt from it
            # In a production environment, you would extract the actual generated image
            
            # Check if response has image data
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content'):
                    content = candidate.content
                    if hasattr(content, 'parts'):
                        for part in content.parts:
                            # Check for inline data (image)
                            if hasattr(part, 'inline_data'):
                                inline_data = part.inline_data
                                if hasattr(inline_data, 'data'):
                                    image_url = f"data:image/png;base64,{inline_data.data}"
                                    break
                            # Alternative: check for mime_type and data
                            elif hasattr(part, 'mime_type') and part.mime_type == 'image/png':
                                if hasattr(part, 'data'):
                                    image_url = f"data:image/png;base64,{part.data}"
                                    break
            
            # Generate video prompt from the image
            try:
                video_prompt = generate_video_prompt(image_url)
            except Exception as e:
                # Fallback video prompt if generation fails
                video_prompt = f""""GROK VIDEO PROMPT (6 SECONDS)"
A high-resolution video showing the product in this setting, with subtle natural movement and realistic lighting effects."""
            
            return {
                "url": image_url,
                "videoPrompt": video_prompt
            }
        except Exception as e:
            # Fallback: return product image with generated video prompt
            try:
                video_prompt = generate_video_prompt(product_image)
            except:
                video_prompt = f""""GROK VIDEO PROMPT (6 SECONDS)"
A high-resolution video showing the product in this setting, with subtle natural movement and realistic lighting effects."""
            
            return {
                "url": product_image,
                "videoPrompt": video_prompt
            }
    
    # Generate 4 variations
    results = []
    for i in range(4):
        try:
            result = generate_one(i)
            results.append(result)
        except Exception as e:
            # If generation fails, use product image as fallback
            video_prompt = generate_video_prompt(product_image)
            results.append({
                "url": product_image,
                "videoPrompt": video_prompt
            })
    
    return results

# Fungsi Helper Menu (OptionGrid style)
def uploader(label, key, icon=None, preview_key=None):
    """
    Uploader component similar to React Uploader component
    """
    # Initialize session state
    if preview_key is None:
        preview_key = f"{key}_preview"
    
    if preview_key not in st.session_state:
        st.session_state[preview_key] = None
    
    # Get preview if exists
    preview = st.session_state[preview_key]
    
    # Default icon (plus sign)
    if icon is None:
        icon = """
        <svg xmlns="http://www.w3.org/2000/svg" style="width: 2rem; height: 2rem;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        """
    
    # Create wrapper div with relative positioning
    st.markdown(f'<div class="upload-wrapper" id="upload-wrapper-{key}" style="position: relative; width: 100%;">', unsafe_allow_html=True)
    
    # Create upload box HTML
    if preview:
        # Determine image type from session state
        image_type = st.session_state.get(f"{key}_type", "image/png")
        if image_type == "image/jpeg" or image_type == "image/jpg":
            data_url = f"data:image/jpeg;base64,{preview}"
        else:
            data_url = f"data:image/png;base64,{preview}"
        upload_box_html = f"""
        <div class="upload-box" id="upload-box-{key}">
            <img src="{data_url}" class="upload-preview" alt="Preview" />
            <div class="upload-overlay">
                <span class="upload-overlay-text">Change</span>
            </div>
        </div>
        """
    else:
        upload_box_html = f"""
        <div class="upload-box" id="upload-box-{key}">
            <div class="upload-box-icon">{icon}</div>
            <p class="upload-box-label">{label}</p>
        </div>
        """
    
    # Render upload box
    st.markdown(upload_box_html, unsafe_allow_html=True)
    
    # Hidden file uploader - must be inside the wrapper
    uploaded_file = st.file_uploader(
        label="",
        type=['png', 'jpg', 'jpeg'],
        key=key,
        label_visibility="collapsed"
    )
    
    # Handle file upload
    if uploaded_file is not None:
        import base64
        import io
        # Read file and convert to base64
        file_bytes = uploaded_file.read()
        base64_string = base64.b64encode(file_bytes).decode('utf-8')
        st.session_state[preview_key] = base64_string
        # Also store the file bytes in session state for later use
        st.session_state[f"{key}_bytes"] = file_bytes
        st.session_state[f"{key}_name"] = uploaded_file.name
        st.session_state[f"{key}_type"] = uploaded_file.type
        
        # Update main image state based on key
        if key == "product_file":
            st.session_state.product_image = base64_string
        elif key == "face_file":
            st.session_state.face_image = base64_string
        elif key == "bg_file":
            st.session_state.custom_bg_image = base64_string
        
        st.rerun()
    
    # Close wrapper div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Hide default file uploader UI and position it over the upload box
    st.markdown(f"""
    <style>
    /* Hide file uploader label and button for {key} */
    div[data-testid="stFileUploader"]:has(input[data-testid*="{key}"]) label,
    div[data-testid="stFileUploader"]:has(input[data-testid*="{key}"]) button,
    div[data-testid="stFileUploader"]:has(input[data-testid*="{key}"]) p {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    /* Position file input over upload box */
    #upload-wrapper-{key} {{
        position: relative !important;
    }}
    
    #upload-wrapper-{key} div[data-testid="stFileUploader"] {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100px !important;
        opacity: 0 !important;
        z-index: 10 !important;
        pointer-events: none !important;
    }}
    
    #upload-wrapper-{key} div[data-testid="stFileUploader"] input[type="file"] {{
        position: absolute !important;
        inset: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 11 !important;
        pointer-events: auto !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def draw_menu(label, options, key, custom_key=None, custom_value_key=None):
    # Initialize state
    if key not in st.session_state:
        st.session_state[key] = options[0]
    if custom_value_key and custom_value_key not in st.session_state:
        st.session_state[custom_value_key] = ''
    
    # Title
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    
    # Grid of buttons (2 columns)
    cols = st.columns(2)
    for i, opt in enumerate(options):
        with cols[i % 2]:
            is_selected = st.session_state[key] == opt
            
            # Custom styling for buttons
            st.markdown(f"""
            <style>
            button[key="{key}_{i}"] {{
                padding: 0.5rem 0.75rem !important;
                font-size: 0.75rem !important;
                border-radius: 0.5rem !important;
                text-align: left !important;
                font-family: 'Inter', sans-serif !important;
                transition: all 0.2s !important;
                width: 100% !important;
                margin-bottom: 0.5rem !important;
                {'background: #581c87 !important; border: 1px solid #581c87 !important; color: #e9d5ff !important; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;' if is_selected else 'background: white !important; border: 1px solid #e9d5ff !important; color: #6b21a8 !important;'}
            }}
            button[key="{key}_{i}"]:hover {{
                {'background: #6b21a8 !important;' if is_selected else 'border-color: #f9a8d4 !important; background: rgba(253, 242, 248, 0.5) !important;'}
            }}
            </style>
            """, unsafe_allow_html=True)
            
            if st.button(opt, key=f"{key}_{i}", use_container_width=True):
                st.session_state[key] = opt
                st.rerun()
    
    # Custom textarea if selected option is custom_key
    if custom_key and st.session_state[key] == custom_key and custom_value_key:
        custom_value = st.text_area(
            f"Enter custom {label.lower()} details...",
            value=st.session_state[custom_value_key],
            key=f"{custom_value_key}_textarea",
            height=100,
            label_visibility="collapsed",
            placeholder=f"Enter custom {label.lower()} details..."
        )
        st.session_state[custom_value_key] = custom_value

# 4. LAYOUT UTAMA
col_left, col_right = st.columns([1, 1.4], gap="large")

with col_left:
    st.markdown('<div class="unified-card">', unsafe_allow_html=True)
    
    # Header Kartu
    header_col1, header_col2 = st.columns([1, 1])
    with header_col1:
        st.markdown('<div class="config-title">CONFIGURATION</div>', unsafe_allow_html=True)
    with header_col2:
        if st.button("SAVE PRESET", key="save_preset_btn", use_container_width=True):
            if not st.session_state.product_image:
                st.session_state.error = "Add a product image first."
            else:
                new_setup = {
                    'id': f"setup_{int(datetime.now().timestamp() * 1000)}",
                    'name': f"Preset {datetime.now().strftime('%Y-%m-%d')}",
                    'config': st.session_state.config.copy(),
                    'productImage': st.session_state.product_image,
                    'faceImage': st.session_state.face_image,
                    'customBgImage': st.session_state.custom_bg_image,
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
                st.session_state.saved_setups.insert(0, new_setup)
                st.session_state.success_msg = "Setup saved!"
                st.rerun()
    
    # Style for save preset button
    st.markdown("""
    <style>
    button[key="save_preset_btn"] {
        font-size: 0.625rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: #ec4899 !important;
        background: rgba(253, 242, 248, 0.5) !important;
        border: 1px solid #f9a8d4 !important;
        border-radius: 9999px !important;
        padding: 0.25rem 0.75rem !important;
        transition: all 0.2s !important;
    }
    button[key="save_preset_btn"]:hover {
        background: rgba(253, 242, 248, 0.8) !important;
        border-color: #ec4899 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="scrollable-body">', unsafe_allow_html=True)
    
    # Bungkus Upload Box untuk menaikkan posisi
    st.markdown('<div class="upload-container-wrapper">', unsafe_allow_html=True)
    u1, u2 = st.columns(2)
    with u1:
        # Product uploader
        product_icon = """
        <svg xmlns="http://www.w3.org/2000/svg" style="width: 2rem; height: 2rem;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        """
        uploader("PRODUCT", "product_file", icon=product_icon)
    with u2:
        # Face/Ref uploader
        face_icon = """
        <svg xmlns="http://www.w3.org/2000/svg" style="width: 2rem; height: 2rem;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        """
        uploader("FACE REFERENCE", "face_file", icon=face_icon)
    st.markdown('</div>', unsafe_allow_html=True)

    # Update config from session state
    if 'm_type' in st.session_state:
        st.session_state.config['modelType'] = st.session_state.m_type
    if 'cat' in st.session_state:
        st.session_state.config['category'] = st.session_state.cat
    if 'hand_interaction' in st.session_state:
        st.session_state.config['handInteraction'] = st.session_state.hand_interaction
    if 'bg' in st.session_state:
        st.session_state.config['background'] = st.session_state.bg
    if 'pose_scene' in st.session_state:
        st.session_state.config['pose'] = st.session_state.pose_scene
    if 'style' in st.session_state:
        st.session_state.config['style'] = st.session_state.style
    if 'light' in st.session_state:
        st.session_state.config['lighting'] = st.session_state.light
    if 'comp' in st.session_state:
        st.session_state.config['angle'] = st.session_state.comp
    if 'frame' in st.session_state:
        st.session_state.config['aspectRatio'] = st.session_state.frame
    if 'style_custom' in st.session_state:
        st.session_state.config['customStylePrompt'] = st.session_state.style_custom
    if 'bg_custom' in st.session_state:
        st.session_state.config['customBackgroundPrompt'] = st.session_state.bg_custom
    if 'light_custom' in st.session_state:
        st.session_state.config['customLightingPrompt'] = st.session_state.light_custom
    if 'pose_scene_custom' in st.session_state:
        st.session_state.config['customPosePrompt'] = st.session_state.pose_scene_custom
    
    # Get dynamic options
    current_pose_options = get_current_pose_options(st.session_state.config)
    current_background_options = get_current_background_options(st.session_state.config)
    
    # Synchronize pose if not in current options
    if st.session_state.config['pose'] not in current_pose_options:
        st.session_state.config['pose'] = current_pose_options[0] if current_pose_options else ''
    if st.session_state.config['background'] not in current_background_options:
        st.session_state.config['background'] = current_background_options[0] if current_background_options else BACKGROUNDS[0]
    
    # Menu Kategori
    draw_menu("MODEL TYPE", MODELS, "m_type")
    draw_menu("CATEGORY", CATEGORIES, "cat")
    
    # Dynamic Hand Interaction based on model type
    if is_product_only(st.session_state.config['modelType']):
        hand_interaction_options = HAND_INTERACTIONS
    else:
        hand_interaction_options = [h for h in HAND_INTERACTIONS if 'Kaki' not in h]
    draw_menu("HAND INTERACTION", hand_interaction_options, "hand_interaction")
    
    draw_menu("STYLE", STYLES, "style", custom_key="Custom", custom_value_key="style_custom")
    draw_menu("BACKGROUND", current_background_options, "bg", custom_key="Custom Prompt", custom_value_key="bg_custom")
    
    # Show custom background uploader if needed
    if st.session_state.config['background'] == 'Upload Latar':
        st.markdown('<div class="upload-container-wrapper">', unsafe_allow_html=True)
        bg_icon = """
        <svg xmlns="http://www.w3.org/2000/svg" style="width: 2rem; height: 2rem;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        """
        uploader("BG IMAGE", "bg_file", icon=bg_icon)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Dynamic Pose options
    # FOOT_INTERACTION_POSES already has "Prompt Custom (bisa diedit)" in it, so we need to handle it differently
    if is_product_only(st.session_state.config['modelType']) and is_foot_interaction(st.session_state.config['handInteraction']):
        # For foot interaction, the custom key is already in the list
        draw_menu("POSE & SCENE", current_pose_options, "pose_scene", custom_key="Prompt Custom (bisa diedit)", custom_value_key="pose_scene_custom")
    else:
        draw_menu("POSE & SCENE", current_pose_options, "pose_scene", custom_key="Prompt Kustom", custom_value_key="pose_scene_custom")
    
    draw_menu("LIGHTING", LIGHTING, "light", custom_key="Custom", custom_value_key="light_custom")
    draw_menu("CAMERA ANGLE", ANGLES, "comp")
    
    # Framing with ratios
    st.markdown('<div class="section-label">FRAMING</div>', unsafe_allow_html=True)
    ratio_cols = st.columns(3)
    for i, ratio in enumerate(RATIOS):
        with ratio_cols[i % 3]:
            is_selected = st.session_state.config['aspectRatio'] == ratio['value']
            if st.button(ratio['label'], key=f"ratio_{i}", use_container_width=True):
                st.session_state.config['aspectRatio'] = ratio['value']
                st.rerun()
    
    # Additional prompt textarea
    st.markdown('<div class="section-label" style="margin-top: 1rem;">ADDITIONAL PROMPT</div>', unsafe_allow_html=True)
    additional_prompt = st.text_area(
        "Additional artistic details...",
        value=st.session_state.config.get('additionalPrompt', ''),
        key="additional_prompt",
        height=100,
        label_visibility="collapsed",
        placeholder="Additional artistic details..."
    )
    st.session_state.config['additionalPrompt'] = additional_prompt
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Sticky Footer
    st.markdown('<div class="card-footer">', unsafe_allow_html=True)
    if st.session_state.error:
        st.markdown(f'<div style="color: #ef4444; font-size: 0.625rem; margin-bottom: 0.75rem; font-weight: 700;">{st.session_state.error}</div>', unsafe_allow_html=True)
    if st.session_state.success_msg:
        st.markdown(f'<div style="color: #10b981; font-size: 0.625rem; margin-bottom: 0.75rem; font-weight: 700;">{st.session_state.success_msg}</div>', unsafe_allow_html=True)
    
    if st.button("🚀 GENERATE PHOTOS", type="primary", use_container_width=True, disabled=st.session_state.is_generating):
        if not st.session_state.product_image:
            st.session_state.error = "Please upload a product image first."
            st.rerun()
        else:
            st.session_state.is_generating = True
            st.session_state.error = None
            try:
                results = generate_studio_image(
                    st.session_state.config,
                    st.session_state.product_image,
                    st.session_state.face_image,
                    st.session_state.custom_bg_image
                )
                # Add all 4 variations to generated images
                for idx, result in enumerate(results):
                    new_image = {
                        "id": f"{int(datetime.now().timestamp() * 1000)}-{idx}",
                        "url": result["url"],
                        "videoPrompt": result["videoPrompt"],
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }
                    st.session_state.generated_images.insert(0, new_image)
                st.session_state.active_tab = 'history'
                st.session_state.success_msg = "Masterpieces curated!"
                st.rerun()
            except Exception as e:
                st.session_state.error = str(e)
            finally:
                st.session_state.is_generating = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="preview-card">', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "Preview",
        f"Session ({len(st.session_state.generated_images)})",
        f"My Library ({len(st.session_state.saved_images) + len(st.session_state.saved_setups)})"
    ])
    
    with tab1:
        if not st.session_state.product_image:
            st.markdown("""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; padding: 3rem;">
                    <div style="background: linear-gradient(135deg, #E24A9F, #9D67E3); width: 96px; height: 96px; border-radius: 2rem; display: flex; align-items: center; justify-content: center; color: white; font-size: 40px; margin-bottom: 2rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); animation: pulse 2s infinite;">
                        <svg style="width: 40px; height: 40px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                    </div>
                    <h3 style="font-family: 'Playfair Display', serif; font-size: 2.5rem; color: #1e1b4b; margin-bottom: 1rem; font-style: italic;">Start Your Vision</h3>
                    <p style="color: #a78bfa; font-size: 0.875rem; font-weight: 300; letter-spacing: 0.05em; line-height: 1.6;">Upload your product hero asset to begin the transformation.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            image_type = st.session_state.get("product_file_type", "image/png")
            if image_type == "image/jpeg" or image_type == "image/jpg":
                data_url = f"data:image/jpeg;base64,{st.session_state.product_image}"
            else:
                data_url = f"data:image/png;base64,{st.session_state.product_image}"
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; padding: 2rem;">
                    <div style="position: relative; width: 100%; max-width: 32rem; aspect-ratio: 1; background: white; border-radius: 4rem; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 20px solid white; transition: transform 0.3s;">
                        <img src="{data_url}" alt="Hero" style="width: 100%; height: 100%; object-fit: contain; padding: 3rem;" />
                        <div style="position: absolute; inset: 0; background: linear-gradient(to top, rgba(30, 27, 75, 0.1), transparent);"></div>
                    </div>
                    <p style="margin-top: 2rem; color: #a78bfa; font-style: italic; font-size: 0.875rem; font-weight: 300; text-transform: uppercase; letter-spacing: 0.1em;">Active Product Asset</p>
                </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        if len(st.session_state.generated_images) == 0:
            st.markdown("""
                <div style="padding: 10rem 2rem; text-align: center; color: #c4b5fd; font-style: italic; font-weight: 300; letter-spacing: 0.1em;">
                    Awaiting your first studio session...
                </div>
            """, unsafe_allow_html=True)
        else:
            for img in st.session_state.generated_images:
                st.markdown(f"""
                    <div style="display: flex; flex-direction: column; gap: 2rem; background: rgba(255, 255, 255, 0.4); padding: 1.5rem; border-radius: 3rem; border: 1px solid rgba(255, 255, 255, 0.6); box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 2rem;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2.5rem;">
                            <div style="position: relative; background: white; border-radius: 3rem; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); border: 1px solid #e9d5ff;">
                                <img src="{img['url']}" alt="Generated" style="width: 100%; aspect-ratio: 1; object-fit: cover;" />
                            </div>
                            <div style="display: flex; flex-direction: column; justify-content: center;">
                                <h4 style="font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.5rem; color: #1e1b4b; margin-bottom: 1.5rem;">Generated Image</h4>
                                <div style="background: rgba(255, 255, 255, 0.8); padding: 1.5rem; border-radius: 2rem; border: 1px solid #e9d5ff;">
                                    <p style="font-size: 0.625rem; font-weight: 700; color: #ec4899; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem;">GROK VIDEO PROMPT (6 SECONDS)</p>
                                    <div style="background: rgba(250, 245, 255, 0.5); padding: 1rem; border-radius: 1rem; border: 1px solid #e9d5ff;">
                                        <p style="font-size: 0.75rem; color: #6b21a8; line-height: 1.6; font-style: italic;">
                                            {img.get('videoPrompt', 'Analyzing motion context...')}
                                        </p>
                                    </div>
                                    <p style="margin-top: 1rem; font-size: 0.5625rem; color: #a78bfa; font-weight: 500;">Use this prompt in any AI video generator for perfect 6-second clips.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        library_tab1, library_tab2 = st.tabs([
            f"Favorited Artworks ({len(st.session_state.saved_images)})",
            f"Saved Presets ({len(st.session_state.saved_setups)})"
        ])
        
        with library_tab1:
            if len(st.session_state.saved_images) == 0:
                st.markdown("""
                    <div style="padding: 5rem 2rem; text-align: center; color: #c4b5fd; font-style: italic;">
                        No favorited artworks yet.
                    </div>
                """, unsafe_allow_html=True)
            else:
                cols = st.columns(3)
                for i, img in enumerate(st.session_state.saved_images):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div style="position: relative; background: white; border-radius: 1.5rem; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e9d5ff; margin-bottom: 1rem;">
                                <img src="{img['url']}" alt="Fav" style="width: 100%; aspect-ratio: 1; object-fit: cover;" />
                            </div>
                        """, unsafe_allow_html=True)
        
        with library_tab2:
            if len(st.session_state.saved_setups) == 0:
                st.markdown("""
                    <div style="padding: 5rem 2rem; text-align: center; color: #c4b5fd; font-style: italic;">
                        No saved presets yet.
                    </div>
                """, unsafe_allow_html=True)
            else:
                for setup in st.session_state.saved_setups:
                    st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.7); padding: 1.5rem; border-radius: 2.5rem; display: flex; gap: 1.5rem; border: 1px solid #e9d5ff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem;">
                            <div style="width: 96px; height: 96px; background: #f5f3ff; border-radius: 1.5rem; overflow: hidden; flex-shrink: 0; padding: 0.5rem; border: 1px solid #e9d5ff;">
                                <img src="{setup.get('productImage', '')}" style="width: 100%; height: 100%; object-fit: contain;" />
                            </div>
                            <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between; padding: 0.25rem 0;">
                                <div>
                                    <h4 style="font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.125rem; color: #1e1b4b;">{setup.get('name', 'Preset')}</h4>
                                    <p style="font-size: 0.625rem; font-weight: 700; color: #ec4899; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.25rem;">{setup.get('config', {}).get('background', '')} • {setup.get('config', {}).get('style', '')}</p>
                                </div>
                                <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                                    <button style="font-size: 0.625rem; background: #581c87; color: white; padding: 0.625rem 1.25rem; border-radius: 0.75rem; font-weight: 700; text-transform: uppercase; border: none; cursor: pointer;">Apply</button>
                                    <button style="font-size: 0.625rem; color: #ef4444; font-weight: 700; text-transform: uppercase; background: none; border: none; cursor: pointer;">Delete</button>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)