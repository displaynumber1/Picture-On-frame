
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


@dataclass
class VariantMetadata:
    title: str
    hook_text: str
    cta_text: str
    hashtags: str
    hook_pattern: str
    cta_pattern: str
    hashtag_pattern: str


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


def _weighted_choice(options: List[tuple[str, str]], weights: Dict[str, float]) -> tuple[str, str]:
    if not options:
        return ("", "")
    weight_values = [max(0.1, float(weights.get(key, 1.0))) for key, _ in options]
    total = sum(weight_values)
    pick = random.uniform(0, total)
    cumulative = 0.0
    for (key, text), weight in zip(options, weight_values):
        cumulative += weight
        if pick <= cumulative:
            return (key, text)
    return options[-1]


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
        "lebih hemat waktu",
        "lebih stand out",
        "lebih premium",
        "lebih clean"
    ]
    benefit = random.choice(benefit_phrases)

    niche_key = _slugify(niche_text)

    title_templates_generic = [
        f"{niche_text} yang bikin kamu terlihat {benefit}",
        f"Rahasia {niche_text} biar kelihatan {benefit}",
        f"{niche_text} favorit yang lagi ramai dicari",
        f"{niche_text} yang bikin penampilan makin {benefit}",
        f"{niche_text} viral yang dipakai banyak orang",
        f"{niche_text} yang bikin look kamu naik level"
    ]

    title_templates_by_niche = {
        "fashion": [
            f"Outfit {niche_text} yang bikin look kamu {benefit}",
            f"{niche_text} ini bikin OOTD makin {benefit}",
            f"{niche_text} favorit buat look simpel tapi {benefit}"
        ],
        "beauty": [
            f"{niche_text} yang bikin look kamu {benefit}",
            f"{niche_text} favorit biar hasil lebih {benefit}",
            f"{niche_text} yang bikin hasil makin {benefit}"
        ],
        "sandal": [
            f"Sandal ini bikin langkahmu lebih {benefit}",
            f"Sandal favorit yang bikin kaki kelihatan {benefit}",
            f"Sandal ini bikin OOTD makin {benefit}"
        ],
        "sepatu": [
            f"Sepatu ini bikin gaya makin {benefit}",
            f"Sepatu favorit yang bikin look {benefit}",
            f"Sepatu ini bikin penampilan lebih {benefit}"
        ],
        "tas": [
            f"Tas ini bikin penampilan makin {benefit}",
            f"Tas favorit yang bikin gaya {benefit}",
            f"Tas ini bikin outfit naik level"
        ]
    }

    title_pool = title_templates_by_niche.get(niche_key, title_templates_generic)

    hook_templates_generic = [
        "Stop scroll! Ini bikin look kamu langsung beda.",
        "Aku baru sadar detail kecil ini bikin hasil beda banget.",
        "Biar kelihatan lebih rapi, coba ini dulu.",
        "Stop scroll! Lihat ini sebelum kamu checkout.",
        "Aku baru sadar kenapa banyak yang cari yang ini.",
        "Kecil, tapi efeknya bikin beda besar."
    ]

    hook_templates_by_niche = {
        "fashion": [
            "Stop scroll! OOTD kamu bakal naik level dengan ini.",
            "Aku baru sadar item ini bikin outfit langsung {benefit}.",
            "Biar OOTD keliatan {benefit}, coba item ini."
        ],
        "beauty": [
            "Stop scroll! Hasil makeup jadi lebih {benefit} pakai ini.",
            "Aku baru sadar ini bikin hasil jadi {benefit}.",
            "Biar hasil makeup lebih {benefit}, coba ini dulu."
        ],
        "sandal": [
            "Stop scroll! Sandal ini bikin langkahmu lebih {benefit}.",
            "Aku baru sadar sandal ini bikin kaki kelihatan {benefit}.",
            "Biar kaki keliatan {benefit}, pilih sandal ini."
        ],
        "sepatu": [
            "Stop scroll! Sepatu ini bikin look kamu lebih {benefit}.",
            "Aku baru sadar sepatu ini bikin gaya {benefit}.",
            "Biar gaya makin {benefit}, coba sepatu ini."
        ],
        "tas": [
            "Stop scroll! Tas ini bikin outfit langsung {benefit}.",
            "Aku baru sadar tas ini bikin look lebih {benefit}.",
            "Biar outfit keliatan {benefit}, pilih tas ini."
        ]
    }

    hook_pool = [
        template.format(benefit=benefit)
        for template in hook_templates_by_niche.get(niche_key, hook_templates_generic)
    ]

    cta_templates = [
        "Komen MAU",
        "Ketik MAU di komen",
        "Tag teman kamu",
        "Save dulu biar nggak lupa",
        "Share ke bestie kamu",
        "DM kalau mau detailnya"
    ]

    resolved_title = _normalize_text(title) or random.choice(title_pool)
    resolved_hook = _normalize_text(hook_text) or random.choice(hook_pool)
    resolved_cta = _normalize_text(cta_text) or random.choice(cta_templates)

    resolved_hashtags = _normalize_text(hashtags)
    if not resolved_hashtags:
        niche_tag = _slugify(niche_text)
        category_tag = _slugify(category or niche_text)
        trend_clean = _slugify(trend_tag.replace("#", "")) if trend_tag else "viral"
        general_pool = ["fyp", "foryou", "viral", "trending"]
        tags = _unique_hashtags([
            niche_tag,
            category_tag,
            trend_clean,
            random.choice(general_pool)
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


def generate_variants(
    category: Optional[str],
    trend_tag: Optional[str],
    weights: Dict[str, Dict[str, float]],
    count: int = 5
) -> List[VariantMetadata]:
    niche_text = _normalize_text(category) or "produk"
    niche_key = _slugify(niche_text)

    benefit_phrases = [
        "lebih rapi",
        "lebih percaya diri",
        "lebih elegan",
        "lebih aesthetic",
        "lebih hemat waktu",
        "lebih stand out",
        "lebih premium",
        "lebih clean"
    ]

    title_templates_generic = [
        f"{niche_text} yang bikin kamu terlihat {{benefit}}",
        f"Rahasia {niche_text} biar kelihatan {{benefit}}",
        f"{niche_text} favorit yang lagi ramai dicari",
        f"{niche_text} yang bikin penampilan makin {{benefit}}",
        f"{niche_text} viral yang dipakai banyak orang",
        f"{niche_text} yang bikin look kamu naik level"
    ]

    title_templates_by_niche = {
        "fashion": [
            f"Outfit {niche_text} yang bikin look kamu {{benefit}}",
            f"{niche_text} ini bikin OOTD makin {{benefit}}",
            f"{niche_text} favorit buat look simpel tapi {{benefit}}"
        ],
        "beauty": [
            f"{niche_text} yang bikin look kamu {{benefit}}",
            f"{niche_text} favorit biar hasil lebih {{benefit}}",
            f"{niche_text} yang bikin hasil makin {{benefit}}"
        ],
        "sandal": [
            "Sandal ini bikin langkahmu lebih {benefit}",
            "Sandal favorit yang bikin kaki kelihatan {benefit}",
            "Sandal ini bikin OOTD makin {benefit}"
        ],
        "sepatu": [
            "Sepatu ini bikin gaya makin {benefit}",
            "Sepatu favorit yang bikin look {benefit}",
            "Sepatu ini bikin penampilan lebih {benefit}"
        ],
        "tas": [
            "Tas ini bikin penampilan makin {benefit}",
            "Tas favorit yang bikin gaya {benefit}",
            "Tas ini bikin outfit naik level"
        ]
    }

    hook_templates_by_pattern: Dict[str, List[str]] = {
        "stop_scroll": [
            "Stop scroll! OOTD kamu bakal naik level dengan ini.",
            "Stop scroll! Ini bikin look kamu langsung beda.",
            "Stop scroll! Lihat ini sebelum kamu checkout.",
            "Stop scroll! Ini lagi viral banget."
        ],
        "realization": [
            "Aku baru sadar item ini bikin outfit langsung {benefit}.",
            "Aku baru sadar kenapa banyak yang cari yang ini.",
            "Aku baru sadar detail kecil ini bikin beda besar."
        ],
        "benefit": [
            "Biar OOTD keliatan {benefit}, coba item ini.",
            "Biar keliatan lebih rapi, coba ini dulu.",
            "Biar hasil makin {benefit}, pilih yang ini."
        ],
        "other": [
            "Kecil, tapi efeknya bikin beda besar.",
            "Detail simpel yang bikin look naik level."
        ]
    }

    cta_templates_by_pattern: Dict[str, List[str]] = {
        "comment": ["Komen MAU", "Ketik MAU di komen"],
        "tag": ["Tag teman kamu", "Tag bestie kamu"],
        "save": ["Save dulu biar nggak lupa", "Save sekarang dulu"],
        "dm": ["DM kalau mau detailnya", "DM untuk info lengkap"],
        "follow": ["Follow biar nggak ketinggalan", "Follow ya"],
        "other": ["Lihat detailnya sekarang"]
    }

    hashtag_patterns = ["fyp", "viral", "trending", "foryou", "other"]

    hook_weights = weights.get("hook", {})
    cta_weights = weights.get("cta", {})
    hashtag_weights = weights.get("hashtag", {})

    title_pool = title_templates_by_niche.get(niche_key, title_templates_generic)
    trend_clean = _slugify(trend_tag.replace("#", "")) if trend_tag else "viral"

    variants: List[VariantMetadata] = []
    for _ in range(max(1, min(count, 5))):
        benefit = random.choice(benefit_phrases)
        title_template = random.choice(title_pool)
        title = title_template.format(benefit=benefit)

        hook_pattern, hook_template = _weighted_choice(
            [(key, random.choice(templates)) for key, templates in hook_templates_by_pattern.items()],
            hook_weights
        )
        hook = hook_template.format(benefit=benefit)

        cta_pattern, cta_template = _weighted_choice(
            [(key, random.choice(templates)) for key, templates in cta_templates_by_pattern.items()],
            cta_weights
        )
        cta = cta_template

        hashtag_pattern, _ = _weighted_choice([(key, key) for key in hashtag_patterns], hashtag_weights)
        general_tag = hashtag_pattern if hashtag_pattern != "other" else random.choice(["fyp", "viral", "trending"])

        tags = _unique_hashtags([
            _slugify(niche_text),
            _slugify(category or niche_text),
            trend_clean,
            general_tag
        ])
        hashtags = " ".join(tags[:5])

        variants.append(
            VariantMetadata(
                title=title,
                hook_text=hook,
                cta_text=cta,
                hashtags=hashtags,
                hook_pattern=hook_pattern,
                cta_pattern=cta_pattern,
                hashtag_pattern=hashtag_pattern
            )
        )

    return variants
