import os
import base64
import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from fastapi import HTTPException

# Helper function to extract base64 and mime_type from data URL
def extract_base64_and_mime_type(data_url_or_base64: str, default_mime: str = "image/png") -> tuple[str, str]:
    """
    Extract pure base64 string and mime_type from data URL or base64 string.
    
    Args:
        data_url_or_base64: Can be:
            - Data URL format: "data:image/jpeg;base64,/9j/4AAQ..."
            - Pure base64: "/9j/4AAQ..."
        default_mime: Default mime type if not found in data URL
    
    Returns:
        tuple: (pure_base64_string, mime_type)
    """
    if not data_url_or_base64:
        return "", default_mime
    
    # Check if it's a data URL
    if ',' in data_url_or_base64:
        # Format: "data:image/jpeg;base64,/9j/4AAQ..."
        parts = data_url_or_base64.split(',', 1)
        header = parts[0]  # "data:image/jpeg;base64"
        base64_data = parts[1]  # Pure base64 string
        
        # Extract mime_type from header
        if 'data:' in header:
            mime_part = header.split('data:')[1]
            if ';' in mime_part:
                mime_type = mime_part.split(';')[0].strip()
            else:
                mime_type = mime_part.strip()
            
            # Validate mime_type
            if mime_type and mime_type.startswith('image/'):
                return base64_data, mime_type
        
        # If mime_type extraction failed, use default
        return base64_data, default_mime
    else:
        # Pure base64 string, use default mime_type
        return data_url_or_base64, default_mime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / 'config.env'
if not env_path.exists():
    env_path = Path(__file__).parent / 'config.env'
load_dotenv(env_path)

# Initialize Gemini API Client (lazy initialization)
api_key = os.getenv('GEMINI_API_KEY')
client = None

def get_gemini_client():
    """Get Gemini client, initialize if needed"""
    global client
    if client is None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY tidak ditemukan. Pastikan file config.env ada di root project dengan format: GEMINI_API_KEY=your_key_here")
        client = genai.Client(api_key=api_key)
    return client

async def enhance_prompt_with_multiple_images(
    prompt: str,
    product_images: Optional[List[str]] = None,
    face_image: Optional[str] = None,
    background_image: Optional[str] = None
) -> str:
    """
    Enhance prompt with multiple images using Gemini Vision API
    
    Args:
        prompt: Original text prompt
        product_images: List of product images (base64 atau data URL)
        face_image: Face image (base64 atau data URL)
        background_image: Background image (base64 atau data URL)
    
    Returns:
        Enhanced prompt with all image descriptions
    """
    try:
        enhanced_prompt = prompt
        descriptions = []
        
        # Process product images
        if product_images:
            for i, img in enumerate(product_images, 1):
                if img:
                    try:
                        desc = await _extract_image_description(img, f"product image {i}")
                        if desc:
                            descriptions.append(f"Product {i}: {desc}")
                    except Exception as e:
                        logger.warning(f"Failed to process product image {i}: {str(e)}")
        
        # Process face image
        if face_image:
            try:
                desc = await _extract_image_description(face_image, "face/reference model")
                if desc:
                    descriptions.append(f"Face/Model reference: {desc}")
            except Exception as e:
                logger.warning(f"Failed to process face image: {str(e)}")
        
        # Process background image
        if background_image:
            try:
                desc = await _extract_image_description(background_image, "background/environment")
                if desc:
                    descriptions.append(f"Background/Environment: {desc}")
            except Exception as e:
                logger.warning(f"Failed to process background image: {str(e)}")
        
        # Combine all descriptions with better structure
        if descriptions:
            combined_description = " | ".join(descriptions)
            
            # Build enhanced prompt with more emphasis on reference images
            enhanced_prompt = f"{prompt}. IMPORTANT REFERENCE DETAILS: {combined_description}. Generate images that ACCURATELY match the products, model face, and background from the reference images. The generated images must show the EXACT products from the reference images with accurate colors, materials, and design details. The model's face should match the reference face features. The background should match the reference background style and environment."
            
            logger.info(f"✅ Enhanced prompt with {len(descriptions)} image description(s)")
            logger.info(f"   Original prompt: {prompt[:150]}...")
            logger.info(f"   Combined descriptions: {combined_description[:200]}...")
            logger.debug(f"   Full enhanced prompt: {enhanced_prompt}")
            return enhanced_prompt
        
        return prompt
    
    except Exception as e:
        logger.error(f"Error enhancing prompt with multiple images: {str(e)}", exc_info=True)
        return prompt


async def _extract_image_description(image_base64: str, image_type: str) -> Optional[str]:
    """
    Extract description from a single image using Gemini Vision
    
    Args:
        image_base64: Base64 image string (can be data URL or pure base64)
        image_type: Type of image (for logging)
    
    Returns:
        Image description or None if extraction fails
    """
    try:
        # Extract pure base64 and mime type
        pure_base64, mime_type = extract_base64_and_mime_type(image_base64)
        if not pure_base64:
            return None
        
        # Get Gemini client
        gemini_client = get_gemini_client()
        
        # Create prompt for Gemini Vision - More detailed for better product matching
        if "product" in image_type.lower():
            vision_prompt = f"""Analyze this product image in detail and provide a comprehensive description for image generation.

Focus on these critical details:
1. PRODUCT TYPE: What is the product? (e.g., "brown leather bucket bag with drawstring", "light blue straight-leg jeans", "beige peplum blouse")
2. COLORS: Exact colors and shades (e.g., "brown leather", "light blue denim", "beige/cream fabric")
3. MATERIALS & TEXTURES: Materials visible (e.g., "leather", "denim", "cotton", "knit")
4. STYLE & DESIGN: Design features (e.g., "bucket bag with drawstring closure", "straight-leg fit", "peplum hem with ruffles")
5. DETAILS: Key visual details that must be preserved (patterns, logos, hardware, stitching, buttons, zippers, etc.)
6. SHAPE & FORM: Overall shape and silhouette

IMPORTANT: Be very specific about product appearance. This description will be used to generate images of models wearing/using this exact product. Focus on accuracy and detail."""
        elif "face" in image_type.lower() or "model" in image_type.lower():
            vision_prompt = f"""Analyze this face/reference model image and provide a detailed description for image generation.

Focus on these critical details:
1. FACE FEATURES: Face shape, eye color, hair color and style, skin tone
2. HAIR: Hair color, length, texture, style (e.g., "medium-length wavy brown hair", "light pink hijab")
3. SKIN TONE: Accurate skin tone description
4. DISTINCTIVE FEATURES: Any unique facial features that should be preserved
5. CLOTHING VISIBLE: What clothing is visible in the reference (e.g., "dark ribbed top", "light pink hijab")
6. EXPRESSION: Facial expression and pose

IMPORTANT: Be specific about facial features and appearance. This will be used as reference for model generation."""
        elif "background" in image_type.lower():
            vision_prompt = f"""Analyze this background/environment image and provide a detailed description for image generation.

Focus on:
1. ENVIRONMENT TYPE: What is the setting? (e.g., "studio", "room", "outdoor", "cafe")
2. COLORS & LIGHTING: Background colors and lighting conditions
3. ELEMENTS: Objects, furniture, decorations visible in background
4. STYLE: Overall style and mood (e.g., "minimalist", "modern", "aesthetic")
5. TEXTURES: Surface textures and materials (e.g., "white textured surface", "wooden floor", "brick wall")

IMPORTANT: Be specific about the environment. This will be used as background reference for product images."""
        else:
            vision_prompt = f"""Analyze this {image_type} image and provide a detailed description focusing on:
1. Key visual elements (colors, textures, materials, style)
2. Composition and layout
3. Distinctive characteristics

Be specific and detailed for accurate image generation."""
        
        # Call Gemini Vision API
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model="gemini-2.0-flash-exp",
            contents=[{
                "role": "user",
                "parts": [
                    {"text": vision_prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": pure_base64
                        }
                    }
                ]
            }],
            config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
            }
        )
        
        # Extract description from response
        description = None
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content'):
                content = candidate.content
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            description = part.text.strip()
                            logger.debug(f"✅ Extracted description from {image_type}: {description[:200]}...")
                            return description
        
        logger.warning(f"⚠️  Could not extract description from {image_type}")
        return None
    
    except Exception as e:
        logger.error(f"Error extracting description from {image_type}: {str(e)}", exc_info=True)
        return None


async def enhance_prompt_with_image(prompt: str, image_base64: str) -> str:
    """
    Enhance prompt with image description using Gemini Vision API
    
    Args:
        prompt: Original text prompt
        image_base64: Base64 image string (can be data URL or pure base64)
    
    Returns:
        Enhanced prompt with image description
    """
    try:
        # Extract pure base64 and mime type
        pure_base64, mime_type = extract_base64_and_mime_type(image_base64)
        if not pure_base64:
            logger.warning("Image base64 is empty, returning original prompt")
            return prompt
        
        # Get Gemini client
        gemini_client = get_gemini_client()
        
        # Create prompt for Gemini Vision to describe the image
        vision_prompt = f"""Analyze this product image and provide a detailed description that can be used to enhance the following prompt for image generation.

Original prompt: {prompt}

Please provide:
1. Product type and key features visible in the image
2. Colors, textures, and materials
3. Style and composition
4. Any distinctive characteristics

Format your response as a concise description that will enhance the original prompt for generating similar product images. Focus on visual elements that should be preserved or referenced."""

        # Call Gemini Vision API (gemini-2.0-flash-exp or gemini-1.5-pro)
        # Wrap blocking call in asyncio.to_thread for async compatibility
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model="gemini-2.0-flash-exp",  # Fast model with vision support
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": vision_prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": pure_base64
                            }
                        }
                    ]
                }
            ],
            config={
                "temperature": 0.3,  # Lower temperature for more factual descriptions
                "top_p": 0.95,
                "top_k": 40,
            }
        )
        
        # Extract description from response
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content'):
                content = candidate.content
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            image_description = part.text.strip()
                            
                            # Enhance the original prompt with image description
                            enhanced_prompt = f"{prompt}. Reference image details: {image_description}. Generate images that match the style, colors, and key visual elements from the reference image while following the original prompt requirements."
                            logger.info(f"✅ Enhanced prompt with image description ({len(image_description)} chars)")
                            return enhanced_prompt
        
        # Fallback: return original prompt with generic enhancement
        logger.warning("Could not extract description from Gemini Vision, using generic enhancement")
        return f"{prompt}. Use the provided reference image as visual guidance for style, colors, composition, and product appearance."
    
    except Exception as e:
        logger.error(f"Error enhancing prompt with Gemini Vision: {str(e)}", exc_info=True)
        # Fallback: return original prompt with generic enhancement
        return f"{prompt}. Use the provided reference image as visual guidance for style, colors, composition, and product appearance."


def generate_product_photo(
    product_images: List[Optional[Dict[str, str]]],
    face_image: Optional[Dict[str, str]],
    background_image: Optional[Dict[str, str]],
    options: Dict[str, Any]
) -> Dict[str, str]:
    """
    Generate product photo with two video prompts (Version A and B)
    Equivalent to generateProductPhoto in geminiService.tsx
    """
    
    # 1. BACKGROUND LOGIC
    background_desc = options.get('customBackgroundPrompt') or options.get('background', '')
    
    if options.get('background') == "Warna (Custom)" and options.get('backgroundColor'):
        background_desc = f"a flawless solid {options['backgroundColor']} luxury studio backdrop"
    elif options.get('background') == "Hapus Latar":
        background_desc = "pure solid white professional studio isolation"
    elif options.get('background') == "Upload Background" and background_image:
        background_desc = "the exact environment, objects, and lighting shown in the uploaded background reference image. DO NOT modify any objects in the background."
    
    # 2. CORE CONSTRAINTS
    is_non_model = options.get('contentType') == "Non Model"
    is_tanpa_interaksi = options.get('interactionType') == "Tanpa Interaksi"
    
    # 3. CATEGORY & POSE LOGIC
    category_context = ""
    composition_detail = ""
    interaction_desc = ""
    
    category = options.get('category', '')
    switch_map = {
        "Fashion": "high-end editorial fashion photography, textile excellence",
        "Beauty": "luxury cosmetic campaign, skin radiance, vanity aesthetics",
        "Tas": "premium leather goods showcase, boutique lighting",
        "Sandal/Sepatu": "designer footwear campaign, dynamic textures, urban luxury",
        "Aksesoris": "jewelry macro photography, diamond refraction, sparkles",
        "Home Living": "architectural digest interior, cozy lifestyle vibes",
        "Food & Beverage": "professional culinary art, appetizing freshness, gourmet lighting"
    }
    category_context = switch_map.get(category, "")
    
    if is_non_model:
        interaction = options.get('interactionType', '')
        
        if is_tanpa_interaksi:
            interaction_desc = "A PURE inanimate product shot. CRITICAL: NO hands, NO feet, NO humans, NO skin, and NO body parts of any kind. The product stands alone or with supporting props."
        elif "Tangan" in interaction:
            type_str = "elegant manicured female" if "Wanita" in interaction else "sophisticated well-groomed male"
            count_str = "a single" if "1" in interaction else "two"
            interaction_desc = f"Featuring {count_str} {type_str} hand(s) interacting with the product. CRITICAL: ONLY the hand(s) and forearm are visible. NO faces or full bodies. Focus on the product and the hand's grip."
        elif "Kaki" in interaction:
            type_str = "graceful female" if "Wanita" in interaction else "professional male"
            interaction_desc = f"Featuring {type_str} feet and lower legs interacting with the product. CRITICAL: NO faces or upper bodies. Focus on the product as worn or placed."
        elif interaction == "Pegang Hanger dengan Produk":
            interaction_desc = "A close-up of an elegant hand holding a high-quality hanger with the product. NO face visible."
        
        pose_text = options.get('customPosePrompt') or options.get('pose', '')
        composition_detail = f"SCENE COMPOSITION: {interaction_desc} The specific pose or arrangement is: {pose_text}."
    else:
        model_type = options.get('modelType', '')
        model_base_map = {
            "Wanita": "an elegant female model",
            "Pria": "a sophisticated male model",
            "Anak LakiLaki": "a cheerful young boy",
            "Anak Perempuan": "a graceful young girl",
            "Hewan": "a well-groomed animal model",
            "Cartoon": "a 3D stylized luxury character"
        }
        model_base = model_base_map.get(model_type, "a professional model")
        
        pose_text = options.get('customPosePrompt') or options.get('pose', '')
        composition_detail = f"SCENE COMPOSITION: Featuring {model_base} in a {pose_text} pose. The model is integrated naturally into the {category_context} setting."
    
    # 4. FINAL PROMPT CONSTRUCTION
    prompt_parts = [
        "DIRECTIVE: You are a world-class commercial advertising photographer. Create a highly realistic product visual using the uploaded image as the main reference.",
        "STRICT RULES (NON-NEGOTIABLE):",
        "- Do NOT change the product shape, size, proportions, or structure.",
        "- Do NOT change product color, material, texture, or finish.",
        "- Do NOT change, recreate, stylize, distort, or remove the brand, logo, text, or markings.",
        "- If a brand or logo is visible, preserve it exactly as uploaded.",
        "- Do NOT change the uploaded face or background.",
        "- Do NOT add or remove any objects.",
        "- No AI artifacts, no stylization.",
        "- Natural lighting, clean commercial look.",
        "ANALYZE REFERENCE:",
        f"- Category: {category}",
        f"- Human presence: {interaction_desc if is_non_model else options.get('modelType', '')}",
        "- Focus: Preserve all branding elements.",
        "PHOTOGRAPHY STYLE:",
        f"- {category_context}",
        f"- {composition_detail}",
        f"- ENVIRONMENT: {background_desc}",
        f"- LIGHTING: {options.get('lighting', '')}",
        f"- CAMERA: {options.get('cameraAngle', '')}",
        "TASK 1: Generate the high-fidelity image described above.",
        "TASK 2: Generate exactly two 6-second video prompts in the following text format after the image:",
        "GROK VIDEO PROMPT (6 SECONDS) - VERSION A: [Prompt for natural soft motion, no zoom, stable camera]",
        "GROK VIDEO PROMPT (6 SECONDS) - VERSION B: [Prompt for detail focus, slow natural zoom-in on branding/texture]"
    ]
    
    if not is_non_model and face_image and options.get('modelType') not in ["Hewan", "Cartoon"]:
        prompt_parts.append("FACIAL IDENTITY: Preserve the exact identity from the face reference.")
    
    prompt = '\n'.join(prompt_parts)
    
    # Build contents array
    contents = []
    
    # Add product images
    active_products = [p for p in product_images if p is not None]
    for p in active_products:
        if p:
            try:
                # Extract pure base64 and mime_type from data URL
                # Use mimeType from request if available, otherwise extract from data URL
                base64_str = p.get('base64', '')
                mime_type_from_request = p.get('mimeType', '')
                
                # Extract pure base64 (remove data URL prefix if present)
                pure_base64, extracted_mime = extract_base64_and_mime_type(base64_str, mime_type_from_request or "image/png")
                
                # Use mimeType from request if valid, otherwise use extracted
                final_mime = mime_type_from_request if mime_type_from_request and mime_type_from_request.startswith('image/') else extracted_mime
                
                if not pure_base64:
                    raise ValueError("Product image base64 is empty")
                
                # Validate base64
                try:
                    base64.b64decode(pure_base64)
                except Exception as decode_error:
                    raise ValueError(f"Invalid base64 data: {str(decode_error)}")
                
                # Store for later conversion to inline_data format
                contents.append({
                    "mime_type": final_mime,
                    "data": pure_base64  # Store as string, will be converted to inline_data later
                })
                logger.info(f"Added product image with mime_type: {final_mime}")
            except Exception as e:
                logger.error(f"Failed to process product image: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Failed to decode product image: {str(e)}")
    
    # Add face image
    if face_image:
        try:
            # Extract pure base64 and mime_type
            base64_str = face_image.get('base64', '')
            mime_type_from_request = face_image.get('mimeType', '')
            
            pure_base64, extracted_mime = extract_base64_and_mime_type(base64_str, mime_type_from_request or "image/png")
            final_mime = mime_type_from_request if mime_type_from_request and mime_type_from_request.startswith('image/') else extracted_mime
            
            if not pure_base64:
                logger.warning("Face image base64 is empty, skipping")
            else:
                # Validate base64
                try:
                    base64.b64decode(pure_base64)
                except Exception:
                    logger.warning("Invalid face image base64, skipping")
                else:
                    contents.append({
                        "mime_type": final_mime,
                        "data": pure_base64
                    })
                    logger.info(f"Added face image with mime_type: {final_mime}")
        except Exception as e:
            logger.warning(f"Failed to process face image: {str(e)}, continuing without it")
    
    # Add background image
    if background_image and options.get('background') == "Upload Background":
        try:
            # Extract pure base64 and mime_type
            base64_str = background_image.get('base64', '')
            mime_type_from_request = background_image.get('mimeType', '')
            
            pure_base64, extracted_mime = extract_base64_and_mime_type(base64_str, mime_type_from_request or "image/png")
            final_mime = mime_type_from_request if mime_type_from_request and mime_type_from_request.startswith('image/') else extracted_mime
            
            if not pure_base64:
                logger.warning("Background image base64 is empty, skipping")
            else:
                # Validate base64
                try:
                    base64.b64decode(pure_base64)
                except Exception:
                    logger.warning("Invalid background image base64, skipping")
                else:
                    contents.append({
                        "mime_type": final_mime,
                        "data": pure_base64
                    })
                    logger.info(f"Added background image with mime_type: {final_mime}")
        except Exception as e:
            logger.warning(f"Failed to process background image: {str(e)}, continuing without it")
    
    # Add text prompt
    contents.append({"text": prompt})
    
    try:
        # Convert contents to proper format for new Gemini API SDK
        parts_list = []
        for content in contents:
            if "mime_type" in content:
                # For images, data is already pure base64 string (no data URL prefix)
                # Use it directly in inline_data format
                image_base64 = content["data"]  # Already pure base64 string
                parts_list.append({
                    "inline_data": {
                        "mime_type": content["mime_type"],
                        "data": image_base64  # Pure base64 string, no prefix
                    }
                })
                logger.debug(f"Added image part with mime_type: {content['mime_type']}, base64 length: {len(image_base64)}")
            else:
                parts_list.append({"text": content["text"]})
        
        # Build contents in new SDK format
        request_contents = [
            {
                "role": "user",
                "parts": parts_list
            }
        ]
        
        logger.info(f"Generating product photo with {len(parts_list)} parts")
        
        # Convert multimodal input to text-only prompt for imagen-3.0-generate-001
        # imagen is text-to-image only, so we need to enhance the text prompt
        # to describe the images that were provided
        enhanced_prompt = prompt
        
        # Add descriptions of provided images to the prompt
        if contents:
            image_descriptions = []
            for content in contents:
                if "mime_type" in content:
                    image_descriptions.append("Reference image provided (product/face/background)")
            
            if image_descriptions:
                enhanced_prompt = f"{enhanced_prompt}\n\nIMPORTANT: Use the provided reference images as exact visual guides. Match the product appearance, model features, and background environment precisely from the reference images."
        
        # Use imagen-3.0-generate-001 for image generation (text-to-image model)
        # Note: imagen doesn't support multimodal input, so we use enhanced text prompt
        # WARNING: imagen-3.0-generate-001 may require Vertex AI SDK instead of google.genai
        # If this fails, consider using Node.js backend with gemini-2.5-flash-image
        try:
            gemini_client = get_gemini_client()
            response = gemini_client.models.generate_content(
                model="imagen-3.0-generate-001",
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": enhanced_prompt}]
                    }
                ],
                config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg or "imagen" in error_msg.lower():
                logger.error(f"imagen-3.0-generate-001 may not be available through google.genai SDK. Error: {error_msg}")
                logger.error("Consider using Node.js backend with gemini-2.5-flash-image instead, or switch to Vertex AI SDK for imagen models.")
            raise
        
        # Extract response data
        image_url = ""
        prompt_a = "Generating prompt A..."
        prompt_b = "Generating prompt B..."
        
        # Handle new SDK response structure
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content'):
                content = candidate.content
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Extract image data
                            image_data = part.inline_data.data
                            mime_type = part.inline_data.mime_type
                            image_url = f"data:{mime_type};base64,{image_data}"
                        elif hasattr(part, 'text') and part.text:
                            text = part.text
                            import re
                            # Try to extract VERSION A and B prompts
                            match_a = re.search(r'VERSION A:\s*(.*?)(?:\n|VERSION B|$)', text, re.IGNORECASE | re.DOTALL)
                            match_b = re.search(r'VERSION B:\s*(.*?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
                            if match_a:
                                prompt_a = match_a.group(1).strip()
                            if match_b:
                                prompt_b = match_b.group(1).strip()
        elif hasattr(response, 'text'):
            # Fallback: if response has direct text attribute
            import re
            text = response.text
            match_a = re.search(r'VERSION A:\s*(.*?)(?:\n|VERSION B|$)', text, re.IGNORECASE | re.DOTALL)
            match_b = re.search(r'VERSION B:\s*(.*?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
            if match_a:
                prompt_a = match_a.group(1).strip()
            if match_b:
                prompt_b = match_b.group(1).strip()
        
        if not image_url:
            logger.error("No image found in response")
            raise HTTPException(status_code=500, detail="Hasil gambar tidak ditemukan dalam response.")
        
        # If prompts were not extracted properly, provide defaults
        if prompt_a == "Generating prompt A...":
            prompt_a = f"A 6-second commercial shot of {category} in a {background_desc} setting. Subtle, natural micro-movements of the product and environment. Stable camera, zero zoom. Focus on branding integrity."
        
        if prompt_b == "Generating prompt B...":
            prompt_b = f"A 6-second detail-focused shot of {category}. Slow, cinematic zoom-in highlighting the {category} texture, material, and brand logo. Natural professional lighting."
        
        logger.info("Product photo generated successfully")
        return {
            "url": image_url,
            "promptA": prompt_a,
            "promptB": prompt_b
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating product photo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate product photo: {str(e)}")


def generate_product_video(
    base64_image: str,
    options: Dict[str, Any]
) -> str:
    """
    Generate product video from image
    Equivalent to generateProductVideo in geminiService.tsx
    Note: Video generation API may not be available in Python SDK yet
    This is a placeholder implementation
    """
    
    is_non_model = options.get('contentType') == "Non Model"
    is_tanpa_interaksi = options.get('interactionType') == "Tanpa Interaksi"
    category = options.get('category', '')
    
    visual_direction = ""
    
    if category == "Fashion":
        visual_direction = (
            "The fashion product is elegantly presented. Focus on the fabric's soft sway and high-end texture."
            if is_non_model
            else "The model is in a relaxed pose. Focus on natural presence and garment flow."
        )
    elif category == "Beauty":
        visual_direction = (
            "The product sits on an aesthetic vanity. Focus on packaging radiance and texture."
            if is_non_model
            else "Close-up of the model with the product. Focus on natural skin glowing."
        )
    elif category == "Tas":
        visual_direction = (
            "The bag is placed on a luxury surface. Focus on leather grain and hardware sheen."
            if is_non_model
            else "Lifestyle shot of the model carrying the bag. Focus on organic movement."
        )
    elif category == "Sandal/Sepatu":
        if is_non_model:
            visual_direction = (
                "The footwear is placed naturally on a high-end floor. Slow macro zoom."
                if is_tanpa_interaksi
                else "Hands or feet are elegantly showing the footwear."
            )
        else:
            visual_direction = "The model is walking or standing naturally wearing the shoes."
    elif category == "Home Living":
        visual_direction = "Focus on function and detail in a cozy interior. Gentle light shifts."
    elif category == "Food & Beverage":
        visual_direction = "Focus on appetizing textures. Subtle steam or condensation."
    
    video_prompt = '\n'.join([
        "GOAL: A realistic 6-second commercial product video using the provided image as the absolute starting point.",
        "STRICT FIDELITY RULES:",
        "- DO NOT change the shape, color, proportions, logos, or details of the product.",
        "- DO NOT distort or warp any elements.",
        "- NO AI artifacts or flickering.",
        "MOVEMENT & CAMERA:",
        "- Add SOFT, NATURAL micro-movements only (subtle sway, gentle breathing).",
        "- Gentle, steady camera zoom towards product details.",
        "- Focus remains sharp and locked on the product.",
        f"VISUAL: {visual_direction}",
        "RESULT: It must look like a professional high-speed camera shot with no AI giveaway."
    ])
    
    # Note: Video generation API (veo-3.1-fast-generate-preview) may not be available in Python SDK
    # This is a placeholder that returns an error message
    # In production, you would need to use the REST API directly or wait for SDK support
    
    raise HTTPException(
        status_code=501,
        detail="Video generation is not yet fully supported in Python SDK. Please use the REST API directly or the video prompts provided with each image."
    )
    
    # Placeholder code for when video API is available:
    # try:
    #     # Extract base64 data
    #     if ',' in base64_image:
    #         image_base64 = base64_image.split(',')[1]
    #         mime_type = base64_image.split(';')[0].split(':')[1]
    #     else:
    #         image_base64 = base64_image
    #         mime_type = "image/png"
    #     
    #     # Use REST API for video generation
    #     # This would require using requests library to call the Gemini API directly
    #     # as the Python SDK may not have video generation support yet
    #     
    #     pass
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")

