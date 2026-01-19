"""
Video Configuration: Fake motion presets per product category
Each category has 3 different fake motion variations
"""

from typing import Dict, List, Tuple

# Fake motion configuration per category
# Each category has 3 variations with different:
# - Zoom settings (zoom_start, zoom_end, zoom_speed)
# - Text positions and timing
# - Motion effects

VIDEO_PRESETS: Dict[str, List[Dict]] = {
    "Fashion": [
        {
            "name": "Elegant Zoom",
            "zoom_start": 1.0,
            "zoom_end": 1.08,
            "zoom_speed": 0.0015,  # Gradual zoom
            "hook_text": "New Collection",
            "hook_position": "top",  # top, center, bottom
            "hook_timing": (0.0, 1.2),
            "cta_text": "Shop Now",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Smooth elegant zoom for fashion products"
        },
        {
            "name": "Dynamic Pan",
            "zoom_start": 1.0,
            "zoom_end": 1.12,
            "zoom_speed": 0.002,  # Faster zoom
            "hook_text": "Trending Now",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "Discover More",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Dynamic zoom with longer hook text"
        },
        {
            "name": "Subtle Focus",
            "zoom_start": 1.0,
            "zoom_end": 1.06,
            "zoom_speed": 0.001,  # Slower, subtle zoom
            "hook_text": "Premium Quality",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "Buy Now",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Subtle zoom for premium fashion"
        }
    ],
    "Beauty": [
        {
            "name": "Close-Up Reveal",
            "zoom_start": 1.0,
            "zoom_end": 1.15,
            "zoom_speed": 0.002,
            "hook_text": "Beauty Essentials",
            "hook_position": "top",
            "hook_timing": (0.0, 1.2),
            "cta_text": "Try Now",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Close-up zoom for beauty products"
        },
        {
            "name": "Glow Effect",
            "zoom_start": 1.0,
            "zoom_end": 1.10,
            "zoom_speed": 0.0015,
            "hook_text": "Radiant Beauty",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "Shop Beauty",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Smooth zoom for beauty glow"
        },
        {
            "name": "Product Focus",
            "zoom_start": 1.0,
            "zoom_end": 1.08,
            "zoom_speed": 0.0012,
            "hook_text": "New Arrival",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "Explore",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Focused zoom on beauty product"
        }
    ],
    "Tas": [
        {
            "name": "Bag Showcase",
            "zoom_start": 1.0,
            "zoom_end": 1.10,
            "zoom_speed": 0.0015,
            "hook_text": "Stylish Bags",
            "hook_position": "top",
            "hook_timing": (0.0, 1.2),
            "cta_text": "Shop Bags",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Showcase zoom for bags"
        },
        {
            "name": "Detail Reveal",
            "zoom_start": 1.0,
            "zoom_end": 1.12,
            "zoom_speed": 0.002,
            "hook_text": "Premium Design",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "View Details",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Detail reveal for bag features"
        },
        {
            "name": "Lifestyle Zoom",
            "zoom_start": 1.0,
            "zoom_end": 1.08,
            "zoom_speed": 0.001,
            "hook_text": "Everyday Essential",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "Get Yours",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Lifestyle zoom for bags"
        }
    ],
    "Sandal/Sepatu": [
        {
            "name": "Footwear Focus",
            "zoom_start": 1.0,
            "zoom_end": 1.12,
            "zoom_speed": 0.002,
            "hook_text": "Step in Style",
            "hook_position": "top",
            "hook_timing": (0.0, 1.2),
            "cta_text": "Shop Shoes",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Focus zoom on footwear"
        },
        {
            "name": "Comfort Zoom",
            "zoom_start": 1.0,
            "zoom_end": 1.10,
            "zoom_speed": 0.0015,
            "hook_text": "Comfort & Style",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "Try On",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Comfort-focused zoom"
        },
        {
            "name": "Design Highlight",
            "zoom_start": 1.0,
            "zoom_end": 1.08,
            "zoom_speed": 0.001,
            "hook_text": "Unique Design",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "Discover",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Design highlight zoom"
        }
    ],
    "Aksesoris": [
        {
            "name": "Accessory Spotlight",
            "zoom_start": 1.0,
            "zoom_end": 1.15,
            "zoom_speed": 0.002,
            "hook_text": "Must Have",
            "hook_position": "top",
            "hook_timing": (0.0, 1.2),
            "cta_text": "Shop Accessories",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Spotlight zoom for accessories"
        },
        {
            "name": "Elegant Reveal",
            "zoom_start": 1.0,
            "zoom_end": 1.10,
            "zoom_speed": 0.0015,
            "hook_text": "Elegant Touch",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "Explore",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Elegant reveal for accessories"
        },
        {
            "name": "Detail Close-Up",
            "zoom_start": 1.0,
            "zoom_end": 1.12,
            "zoom_speed": 0.0018,
            "hook_text": "Fine Details",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "View Collection",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Detail close-up for accessories"
        }
    ],
    "Home Living": [
        {
            "name": "Home Showcase",
            "zoom_start": 1.0,
            "zoom_end": 1.10,
            "zoom_speed": 0.0015,
            "hook_text": "Home Essentials",
            "hook_position": "top",
            "hook_timing": (0.0, 1.2),
            "cta_text": "Shop Home",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Showcase zoom for home products"
        },
        {
            "name": "Comfort Zoom",
            "zoom_start": 1.0,
            "zoom_end": 1.08,
            "zoom_speed": 0.001,
            "hook_text": "Comfort Living",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "Discover",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Comfort zoom for home"
        },
        {
            "name": "Lifestyle View",
            "zoom_start": 1.0,
            "zoom_end": 1.12,
            "zoom_speed": 0.002,
            "hook_text": "Lifestyle",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "Shop Now",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Lifestyle view for home"
        }
    ],
    "Food & Beverage": [
        {
            "name": "Appetizing Zoom",
            "zoom_start": 1.0,
            "zoom_end": 1.15,
            "zoom_speed": 0.002,
            "hook_text": "Delicious",
            "hook_position": "top",
            "hook_timing": (0.0, 1.2),
            "cta_text": "Order Now",
            "cta_position": "bottom",
            "cta_timing": (3.0, 5.0),
            "description": "Appetizing zoom for food"
        },
        {
            "name": "Fresh Reveal",
            "zoom_start": 1.0,
            "zoom_end": 1.10,
            "zoom_speed": 0.0015,
            "hook_text": "Fresh & Tasty",
            "hook_position": "center",
            "hook_timing": (0.0, 1.5),
            "cta_text": "Try It",
            "cta_position": "bottom",
            "cta_timing": (3.5, 5.0),
            "description": "Fresh reveal for food"
        },
        {
            "name": "Mouth-Watering",
            "zoom_start": 1.0,
            "zoom_end": 1.12,
            "zoom_speed": 0.0018,
            "hook_text": "Taste It",
            "hook_position": "top",
            "hook_timing": (0.0, 1.0),
            "cta_text": "Order",
            "cta_position": "center",
            "cta_timing": (3.0, 5.0),
            "description": "Mouth-watering zoom"
        }
    ]
}

# Default preset if category not found
DEFAULT_PRESETS = VIDEO_PRESETS["Fashion"]


def get_video_presets(category: str) -> List[Dict]:
    """
    Get 3 video presets for a given category.
    
    Args:
        category: Product category (e.g., "Fashion", "Beauty", etc.)
    
    Returns:
        List of 3 video preset configurations
    """
    return VIDEO_PRESETS.get(category, DEFAULT_PRESETS)


def get_video_preset(category: str, preset_index: int = 0) -> Dict:
    """
    Get a specific video preset by index.
    
    Args:
        category: Product category
        preset_index: Index of preset (0, 1, or 2)
    
    Returns:
        Video preset configuration
    """
    presets = get_video_presets(category)
    if 0 <= preset_index < len(presets):
        return presets[preset_index]
    return presets[0]  # Return first preset if index out of range
