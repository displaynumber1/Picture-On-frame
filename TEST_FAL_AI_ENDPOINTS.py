"""
Script untuk Test fal Endpoints dan Verifikasi Model yang Tersedia
"""
import os
import sys
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
env_path = Path(__file__).parent.parent / 'config.env'
if not env_path.exists():
    env_path = Path(__file__).parent / 'config.env'
load_dotenv(env_path)

FAL_KEY = os.getenv('FAL_KEY')
FAL_API_BASE = "https://fal.run"

# Model endpoints untuk test
MODELS_TO_TEST = [
    {
        "name": "flux/schnell (current)",
        "endpoint": "/fal-ai/flux/schnell",
        "params": {
            "prompt": "a beautiful sunset over mountains",
            "image_size": "square_hd",
            "num_inference_steps": 4,
            "guidance_scale": 3.5
        }
    },
    {
        "name": "flux (standard)",
        "endpoint": "/fal-ai/flux",
        "params": {
            "prompt": "a beautiful sunset over mountains",
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 3.5
        }
    },
    {
        "name": "flux-pro (premium)",
        "endpoint": "/fal-ai/flux-pro",
        "params": {
            "prompt": "a beautiful sunset over mountains",
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 3.5
        }
    }
]

async def test_model(model_config):
    """Test satu model endpoint"""
    if not FAL_KEY:
        print("❌ FAL_KEY not found in config.env")
        return None
    
    print(f"\n{'='*60}")
    print(f"Testing Model: {model_config['name']}")
    print(f"Endpoint: {FAL_API_BASE}{model_config['endpoint']}")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{FAL_API_BASE}{model_config['endpoint']}",
                headers={
                    "Authorization": f"Key {FAL_KEY}",
                    "Content-Type": "application/json"
                },
                json=model_config['params']
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"✅ SUCCESS!")
                    print(f"Response keys: {list(result.keys())[:5]}")
                    
                    # Check for image URL
                    image_url = None
                    if "images" in result:
                        if isinstance(result["images"], list) and len(result["images"]) > 0:
                            img_data = result["images"][0]
                            image_url = img_data.get("url") if isinstance(img_data, dict) else img_data
                    elif "image" in result:
                        img_data = result["image"]
                        image_url = img_data.get("url") if isinstance(img_data, dict) else img_data
                    elif "url" in result:
                        image_url = result["url"]
                    
                    if image_url:
                        print(f"✅ Image URL found: {image_url[:80]}...")
                        return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "available", "image_url": image_url}
                    elif "request_id" in result or "job_id" in result:
                        print(f"⚠️ Async job detected (request_id/job_id present)")
                        return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "async", "request_id": result.get("request_id") or result.get("job_id")}
                    else:
                        print(f"⚠️ Response received but no image URL found")
                        print(f"Response sample: {json.dumps(result, indent=2)[:500]}")
                        return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "unknown", "response": result}
                except Exception as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Response text: {response.text[:500]}")
                    return None
                    
            elif response.status_code == 403:
                error_text = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                print(f"❌ 403 Forbidden - Access denied")
                print(f"Error: {error_text[:300]}")
                print(f"   -> Model mungkin tidak tersedia atau API key tidak memiliki permission")
                return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "forbidden", "error": error_text[:300]}
                
            elif response.status_code == 401:
                error_text = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                print(f"❌ 401 Unauthorized - Invalid API key")
                print(f"Error: {error_text[:300]}")
                return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "unauthorized", "error": error_text[:300]}
                
            elif response.status_code == 404:
                error_text = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                print(f"❌ 404 Not Found - Endpoint tidak ditemukan")
                print(f"Error: {error_text[:300]}")
                print(f"   -> Endpoint mungkin salah atau model sudah deprecated")
                return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "not_found", "error": error_text[:300]}
                
            else:
                error_text = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                print(f"❌ Error {response.status_code}")
                print(f"Error: {error_text[:300]}")
                return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": f"error_{response.status_code}", "error": error_text[:300]}
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"model": model_config['name'], "endpoint": model_config['endpoint'], "status": "exception", "error": str(e)}

async def main():
    print("="*60)
    print("FAL.AI MODEL VERIFICATION TEST")
    print("="*60)
    print(f"FAL_KEY: {'SET' if FAL_KEY else 'NOT SET'}")
    if FAL_KEY:
        print(f"FAL_KEY Preview: {FAL_KEY[:30]}...{FAL_KEY[-10:]}")
    print("="*60)
    
    results = []
    
    for model_config in MODELS_TO_TEST:
        result = await test_model(model_config)
        if result:
            results.append(result)
        await asyncio.sleep(1)  # Small delay between requests
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    available_models = [r for r in results if r.get("status") == "available"]
    forbidden_models = [r for r in results if r.get("status") == "forbidden"]
    not_found_models = [r for r in results if r.get("status") == "not_found"]
    
    if available_models:
        print(f"\n✅ AVAILABLE MODELS ({len(available_models)}):")
        for model in available_models:
            print(f"   - {model['name']}: {model['endpoint']}")
            if 'image_url' in model:
                print(f"     Image URL: {model['image_url'][:60]}...")
    
    if forbidden_models:
        print(f"\n❌ FORBIDDEN (403) - Need Permission ({len(forbidden_models)}):")
        for model in forbidden_models:
            print(f"   - {model['name']}: {model['endpoint']}")
    
    if not_found_models:
        print(f"\n❌ NOT FOUND (404) - Deprecated or Wrong Endpoint ({len(not_found_models)}):")
        for model in not_found_models:
            print(f"   - {model['name']}: {model['endpoint']}")
    
    print(f"\n{'='*60}")
    print("RECOMMENDATION:")
    print(f"{'='*60}")
    
    if available_models:
        recommended = available_models[0]
        print(f"✅ Use model: {recommended['name']}")
        print(f"   Endpoint: {recommended['endpoint']}")
        print(f"\n   Update backend/fal_service.py line 51:")
        print(f"   f\"{FAL_API_BASE}{recommended['endpoint']}\"")
    elif forbidden_models:
        print(f"⚠️ All tested models return 403 Forbidden")
        print(f"   Possible solutions:")
        print(f"   1. Check fal dashboard for available models")
        print(f"   2. Upgrade API key permissions")
        print(f"   3. Verify FAL_KEY is correct")
    else:
        print(f"❌ No models available. Check fal documentation for correct endpoints.")

if __name__ == "__main__":
    asyncio.run(main())
