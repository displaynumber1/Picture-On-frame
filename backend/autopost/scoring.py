from __future__ import annotations

from typing import Any, Dict, List, Optional
import re


def _count_words(text: Optional[str]) -> int:
    if not text:
        return 0
    return len([t for t in re.split(r"\s+", text.strip()) if t])


def _extract_hashtags(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return re.findall(r"#\w+", text.lower())


def build_score_reasons(
    details: Dict[str, Any],
    title: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str]
) -> List[str]:
    """
    Build explainable reasons for scoring.
    """
    reasons: List[str] = []
    score = float(details.get("score") or 0.0)
    threshold = details.get("threshold")
    trend_similarity = float(details.get("trend_similarity") or 0.0)
    signals = set(details.get("signals") or [])

    hook_words = _count_words(hook_text)
    if hook_words > 0 and hook_words <= 10:
        reasons.append("Hook pendek dan kuat (<=10 kata).")
    elif hook_words > 10:
        reasons.append("Hook cukup panjang, bisa dibuat lebih ringkas.")
    else:
        reasons.append("Hook belum ada, perlu dibuat lebih kuat.")

    if cta_text:
        if any(k in cta_text.lower() for k in ["komen", "comment", "tag", "save"]):
            reasons.append("CTA memicu komentar/engagement.")
        else:
            reasons.append("CTA ada, tapi belum cukup interaktif.")
    else:
        reasons.append("CTA belum ada, sebaiknya tambahkan ajakan.")

    hashtag_list = _extract_hashtags(hashtags)
    if len(hashtag_list) >= 3:
        reasons.append("Hashtag cukup lengkap (>=3).")
    else:
        reasons.append("Hashtag kurang lengkap (min 3).")

    if category and category.lower() in ("fashion", "beauty", "sandal/sepatu", "sandal", "sepatu"):
        reasons.append("Kategori populer untuk konten promo.")

    if trend_similarity >= 0.6 or "trend_hashtag_match" in signals:
        reasons.append("Trend similarity tinggi.")
    elif trend_similarity <= 0.2:
        reasons.append("Trend similarity rendah.")

    compliance = details.get("compliance") or {}
    if compliance.get("blocked"):
        reasons.append("Risiko compliance tinggi, perlu revisi konten.")

    if "audio_present" in signals:
        reasons.append("Audio terdeteksi, meningkatkan engagement.")
    if "voice_missing" in signals:
        reasons.append("Audio tanpa voice, bisa menurunkan engagement.")

    if threshold is not None:
        if score >= float(threshold):
            reasons.append("Skor di atas threshold, siap antre posting.")
        else:
            reasons.append("Skor di bawah threshold, butuh perbaikan metadata.")

    # Ensure uniqueness while keeping order
    seen = set()
    unique_reasons = []
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        unique_reasons.append(reason)
    return unique_reasons
