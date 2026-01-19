## Ringkas: Fitur Auto-Posting

Dokumentasi singkat ini merangkum fitur utama Auto-Posting di backend.

### Fitur Utama
- Scoring AI (LLM) + fallback heuristik, dilindungi cache dan rate limit.
- RAG tren viral (CSV + Qdrant vector search) untuk relevansi hashtag/tren.
- Feedback loop Level-4: performa sebelumnya memengaruhi threshold keputusan.
- Compliance gate anti pelanggaran (promo tanpa konteks, teks berlebihan, statis, blur, relevansi produk).
- Scene analysis ringan (sampling) berjalan di background.
- Deteksi audio & voice‑over lokal (ffprobe + VAD) + bonus/penalty.
- Autopost queue + recheck otomatis + WebSocket real‑time update.
- Logging detail score (hook/CTA/trend/feedback/compliance).
- Temp file cleanup setelah post/failed.

### Keputusan Autopost (Ringkas)
- Skor dihitung dari metadata + tren + feedback + compliance.
- Compliance gate dapat memaksa status ke WAITING_RECHECK.
- Jika skor >= threshold → QUEUED, selain itu WAITING_RECHECK.

### Konfigurasi Utama (ENV)
- AUTPOST_LLM_PROVIDER, AUTPOST_LLM_MODEL
- AUTPOST_SCORE_THRESHOLD, AUTPOST_SCORE_CACHE_TTL
- AUTPOST_RATE_LIMIT_PER_MIN
- AUTPOST_SCENE_PROVIDER, AUTPOST_SCENE_LIGHT_MODE
- AUTPOST_SCENE_SAMPLE_SECONDS, AUTPOST_SCENE_SAMPLE_FPS, AUTPOST_SCENE_SAMPLE_SCALE
- AUTPOST_VOICE_SAMPLE_SECONDS, AUTPOST_VOICE_VAD_MODE
- AUTPOST_SCENE_ENDPOINT (jika pakai HTTP)
