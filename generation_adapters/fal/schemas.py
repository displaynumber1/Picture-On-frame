"""Typed schemas for fal.ai adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


OptionsDict = Dict[str, Any]


@dataclass(frozen=True)
class FaceIdOptions:
    """Options for FaceID generation."""

    extra: OptionsDict = field(default_factory=dict)


@dataclass(frozen=True)
class FluxLoraOptions:
    """Options for Flux LoRA edit."""

    loras: List[str]
    strength: float
    extra: OptionsDict = field(default_factory=dict)


@dataclass(frozen=True)
class StyleEditConfig:
    """Configuration for optional style editing."""

    loras: List[str]
    strength: float
    options: Optional[OptionsDict] = None
