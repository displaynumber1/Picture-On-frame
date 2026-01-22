from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import re
import random


@dataclass
class GeneratedMetadata:
    title: Optional[str]
    hook_text: Optional[str]
    cta_text: Optional[str]
    hashtags: Optional[str]
    sources: Dict[str, str]


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", "", value)
    return value or "produk"


def _unique_hashtags(tags: List[str]) -> List[str]:
    seen = set()
    results: List[str] = []
    for tag in tags:
        clean = tag.strip()
        if not clean:
            continue
        if not clean.startswith("#"):
            clean = f"#{clean}"
        if clean.lower() in seen:
            continue
        seen.add(clean.lower())
        results.append(clean)
    return results


def generate_metadata(
    title: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str],
    niche: Optional[str] = None,
    trend_tag: Optional[str] = None
) -> GeneratedMetadata:
    """
    Rule-based metadata generator. Only fills missing fields.
    """
    sources = {
        "title_source": "user" if _normalize_text(title) else "ai_generated",
        "hook_source": "user" if _normalize_text(hook_text) else "ai_generated",
        "cta_source": "user" if _normalize_text(cta_text) else "ai_generated",
        "hashtags_source": "user" if _normalize_text(hashtags) else "ai_generated",
    }

    niche_text = _normalize_text(niche) or _normalize_text(category) or "produk"

    benefit_phrases = [
        "lebih rapi",
        "lebih percaya diri",
        "lebih elegan",
        "lebih aesthetic",
        "lebih hemat waktu"
    ]
    benefit = random.choice(benefit_phrases)

    title_templates = [
        f"{niche_text} yang bikin kamu terlihat {benefit}",
        f"Rahasia {niche_text} biar kelihatan {benefit}",
        f"{niche_text} favorit yang lagi ramai dicari",
        f"{niche_text} yang bikin penampilan makin {benefit}",
    ]

    hook_templates = [
        "Stop scroll! Ini rahasia biar tampil lebih percaya diri.",
        "Aku baru sadar kalau detail kecil ini bikin beda besar!",
        "Biar kelihatan lebih rapi, coba ini dulu.",
        "Stop scroll! Lihat dulu sebelum kamu pilih yang lain.",
        "Aku baru sadar kenapa banyak yang suka yang ini!"
    ]

    cta_templates = [
        "Komen MAU",
        "Tag teman kamu",
        "Save dulu"
    ]

    resolved_title = _normalize_text(title) or random.choice(title_templates)
    resolved_hook = _normalize_text(hook_text) or random.choice(hook_templates)
    resolved_cta = _normalize_text(cta_text) or random.choice(cta_templates)

    resolved_hashtags = _normalize_text(hashtags)
    if not resolved_hashtags:
        niche_tag = _slugify(niche_text)
        category_tag = _slugify(category or niche_text)
        trend_clean = _slugify(trend_tag.replace("#", "")) if trend_tag else "trend"
        tags = _unique_hashtags([
            niche_tag,
            category_tag,
            trend_clean,
            "fyp"
        ])
        # Keep 3-5 hashtags
        resolved_hashtags = " ".join(tags[:5])

    return GeneratedMetadata(
        title=resolved_title,
        hook_text=resolved_hook,
        cta_text=resolved_cta,
        hashtags=resolved_hashtags,
        sources=sources
    )
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class GeneratedMetadata:
    title: Optional[str]
    hook_text: Optional[str]
    cta_text: Optional[str]
    hashtags: Optional[str]
    sources: Dict[str, str]


def _pick_template(templates: List[str], seed: str) -> str:
    if not templates:
        return ""
    idx = abs(hash(seed)) % len(templates)
    return templates[idx]


def _normalize_hashtag(tag: str) -> str:
    cleaned = "".join(ch for ch in tag.lower() if ch.isalnum() or ch == "_")
    if not cleaned:
        return ""
    return cleaned if cleaned.startswith("#") else f"#{cleaned}"


def _build_hashtags(niche: str, keyword: str, trend: str) -> str:
    tags = [
        _normalize_hashtag(niche),
        _normalize_hashtag(keyword),
        _normalize_hashtag(trend),
        "#fyp",
    ]
    tags = [t for t in tags if t]
    # De-duplicate while preserving order
    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return " ".join(unique[:5])


def generate_metadata(
    title: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str],
    trend_tag: Optional[str] = None,
) -> GeneratedMetadata:
    niche = (category or "produk").strip().lower()
    seed = category or "default"

    hook_templates = [
        "Stop scroll! {niche} ini bikin hasil beda.",
        "Aku baru sadar kalau {niche} ini bisa begini.",
        "Biar keliatan lebih premium, coba ini dulu.",
    ]
    cta_templates = [
        "Komen MAU",
        "Tag teman kamu",
        "Save dulu",
    ]

    sources: Dict[str, str] = {
        "title_source": "user" if title else "ai_generated",
        "hook_source": "user" if hook_text else "ai_generated",
        "cta_source": "user" if cta_text else "ai_generated",
        "hashtags_source": "user" if hashtags else "ai_generated",
    }

    generated_title = title or f"{niche.title()} yang lagi dicari banyak orang"
    generated_hook = hook_text or _pick_template(hook_templates, seed).format(niche=niche)
    generated_cta = cta_text or _pick_template(cta_templates, seed)

    if hashtags:
        generated_hashtags = hashtags
    else:
        trend = trend_tag or "viral"
        keyword = niche.split()[0] if niche else "produk"
        generated_hashtags = _build_hashtags(niche, keyword, trend)

    return GeneratedMetadata(
        title=generated_title,
        hook_text=generated_hook,
        cta_text=generated_cta,
        hashtags=generated_hashtags,
        sources=sources,
    )
