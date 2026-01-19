# Image Generation Service Setup

A new Node.js service has been created for image generation using `gemini-2.5-flash-image`. This service runs separately from the FastAPI backend.

## Architecture

- **FastAPI Backend** (`backend/main.py`): Handles authentication, business logic, and other endpoints
- **Node.js Image Service** (`image-service/`): Dedicated service for image generation using `gemini-2.5-flash-image`
- **Frontend**: Can call either service directly or via FastAPI proxy

## Setup Instructions

### 1. Install Node.js Service Dependencies

```bash
cd image-service
npm install
```

### 2. Environment Variables

The service reads `GEMINI_API_KEY` from `../config.env` (parent directory). Make sure it's set:

```env
GEMINI_API_KEY=your_api_key_here
```

Optional: Set `IMAGE_SERVICE_PORT` (default: 3002)

### 3. Start the Services

**Terminal 1 - FastAPI Backend:**
```bash
cd backend
# Activate virtual environment if needed
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Node.js Image Service:**
```bash
cd image-service
npm start
# or for development with auto-reload:
npm run dev
```

## API Endpoints

### Direct Node.js Service

**POST** `http://localhost:3002/generate-image`

Request:
```json
{
  "prompt": "Generate a realistic product photograph...",
  "productImages": [
    {
      "base64": "data:image/png;base64,iVBORw0KG...",
      "mimeType": "image/png"
    }
  ],
  "faceImage": {
    "base64": "data:image/png;base64,...",
    "mimeType": "image/png"
  },
  "backgroundImage": {
    "base64": "data:image/png;base64,...",
    "mimeType": "image/png"
  }
}
```

Response:
```json
{
  "success": true,
  "image": "data:image/png;base64,iVBORw0KG...",
  "mimeType": "image/png"
}
```

### FastAPI Proxy Endpoint

**POST** `http://localhost:8000/api/generate-image`

Same request/response format as above. The FastAPI backend proxies the request to the Node.js service.

## Usage Options

### Option 1: Frontend calls Node.js service directly

Update frontend to call `http://localhost:3002/generate-image` directly.

### Option 2: Frontend calls FastAPI proxy

Frontend calls `http://localhost:8000/api/generate-image`, which proxies to the Node.js service.

## Health Check

**GET** `http://localhost:3002/health`

Returns:
```json
{
  "status": "ok",
  "service": "image-generation-service"
}
```

## Notes

- The Node.js service uses `gemini-2.5-flash-image` which supports multimodal input (text + images)
- FastAPI backend continues to handle all other endpoints (auth, business logic, etc.)
- Both services can run independently
- CORS is configured to allow requests from `localhost:3000` and `localhost:3001`

