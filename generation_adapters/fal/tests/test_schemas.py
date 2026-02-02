from dataclasses import asdict
from typing import Dict, List, Optional

from pydantic import BaseModel

from generation_adapters.fal.schemas import FaceIdOptions, FluxLoraOptions, StyleEditConfig


def _validate(model_cls, data):
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    return model_cls.parse_obj(data)


class FaceIdOptionsModel(BaseModel):
    extra: Dict[str, object] = {}


class FluxLoraOptionsModel(BaseModel):
    loras: List[str]
    strength: float
    extra: Dict[str, object] = {}


class StyleEditConfigModel(BaseModel):
    loras: List[str]
    strength: float
    options: Optional[Dict[str, object]] = None


def test_pydantic_schema_validation() -> None:
    face = FaceIdOptions(extra={"seed": 42})
    flux = FluxLoraOptions(loras=["lora-a"], strength=0.7, extra={"foo": "bar"})
    style = StyleEditConfig(loras=["lora-b"], strength=0.5, options={"tone": "warm"})

    validated_face = _validate(FaceIdOptionsModel, asdict(face))
    validated_flux = _validate(FluxLoraOptionsModel, asdict(flux))
    validated_style = _validate(StyleEditConfigModel, asdict(style))

    assert validated_face.extra["seed"] == 42
    assert validated_flux.loras == ["lora-a"]
    assert validated_style.options == {"tone": "warm"}
