# Image Generation Service

Node.js service for generating images using Google's `gemini-2.5-flash-image` model.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Ensure `GEMINI_API_KEY` is set in `../config.env` (parent directory)

3. Start the service:
```bash
npm start
# or for development with auto-reload:
npm run dev
```

## API Endpoints

### POST /generate-image

Generate an image using multimodal input (text + images).

**Request Body:**
```json
{
  "prompt": "Generate a realistic product photograph...",
  "images": [
    {
      "base64": "data:image/png;base64,iVBORw0KG...",
      "mimeType": "image/png"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "image": "data:image/png;base64,iVBORw0KG...",
  "mimeType": "image/png"
}
```

### GET /health

Health check endpoint.

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `IMAGE_SERVICE_PORT`: Port to run the service on (default: 3002)

