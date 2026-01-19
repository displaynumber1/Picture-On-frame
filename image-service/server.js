import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { GoogleGenAI } from "@google/genai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: "20mb" }));

const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY,
});

app.post("/generate-image", async (req, res) => {
  try {
    const { contents, aspectRatio } = req.body;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-image",
      contents,
      config: {
        imageConfig: {
          aspectRatio: aspectRatio || "1:1",
        },
      },
    });

    const parts = response.candidates?.[0]?.content?.parts;

    if (!parts) {
      return res.status(500).json({ error: "No image generated" });
    }

    const imagePart = parts.find(p => p.inlineData);

    if (!imagePart) {
      return res.status(500).json({ error: "Image not found in response" });
    }

    res.json({
      image: `data:${imagePart.inlineData.mimeType};base64,${imagePart.inlineData.data}`,
    });

  } catch (err) {
    console.error("Generate image error:", err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(5050, () => {
  console.log("🚀 Image service running at http://localhost:5050");
});
