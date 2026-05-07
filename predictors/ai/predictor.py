from __future__ import annotations

import base64
import io
import json
import os

from openai import OpenAI
from PIL import Image

from predictors.ai.config import DATA_MAP, GPT_MODEL, MAX_TOKENS
from predictors.ai.data_loader import load_all_references

# ---------------------------------------------------------------------------
# Image pipeline lambdas
# ---------------------------------------------------------------------------
_to_b64    = lambda b: base64.b64encode(b).decode()
_to_uri    = lambda b: f"data:image/jpeg;base64,{_to_b64(b)}"
_img_block = lambda b, detail="low": {"type": "image_url", "image_url": {"url": _to_uri(b), "detail": detail}}
_txt_block = lambda t: {"type": "text", "text": t}

# Reference section: class label header + all its sample images
_ref_section  = lambda cls, imgs: [_txt_block(f'[ Class: "{cls}" — {len(imgs)} reference image(s) ]'), *map(_img_block, imgs)]
_flatten      = lambda xss: [x for xs in xss for x in xs]

# Convert any uploaded image bytes → JPEG bytes (handles HEIC, PNG, etc.)
_normalise    = lambda raw: _encode_jpeg(Image.open(io.BytesIO(raw)).convert("RGB"))


def _encode_jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()
# ---------------------------------------------------------------------------


SYSTEM_PROMPT = """\
You are a senior plant pathologist with deep expertise in pepper (Piper nigrum) diseases and pests.

Your classification method:
1. OBSERVE — Study the reference images for each class and note their distinguishing visual characteristics
   (colour patterns, texture, lesion shape, structural deformities, insect morphology, etc.)
2. ANALYSE — Examine the target image and describe what you actually see: colour, texture, any abnormalities,
   affected areas, visible organisms, etc.
3. MATCH — Compare your observations of the target against the characteristics of each reference class.
4. CONCLUDE — Select the class whose visual characteristics best match the target. Be honest about uncertainty.

Always ground your conclusion in specific visual evidence. Never guess without reasoning.\
"""


def _build_content(classes: list[str], references: dict[str, list[bytes]], target: bytes) -> list[dict]:
    class_list = ", ".join(f'"{c}"' for c in classes)

    return [
        _txt_block(
            f"POSSIBLE CLASSES: {class_list}\n\n"
            "=== STEP 1: REFERENCE IMAGES ===\n"
            "Study the following reference images carefully. "
            "Note the key visual traits that define each class."
        ),
        *_flatten(_ref_section(cls, references[cls]) for cls in classes),
        _txt_block(
            "=== STEP 2: TARGET IMAGE ===\n"
            "Examine the image below. Describe what you observe, then classify it.\n\n"
            "Respond with ONLY valid JSON — no markdown, no extra text:\n"
            "{\n"
            '  "predicted_class": "<must be one of the POSSIBLE CLASSES exactly>",\n'
            '  "probabilities": { "<class_name>": <float 0.0-1.0>, ... } (all classes, must sum to 1.0)\n'
            "}"
        ),
        _img_block(target, detail="high"),
    ]


class OpenAIVisionPredictor:
    def __init__(self):
        self._client: OpenAI | None = None
        # Cache: model_name → {class_label: [jpeg_bytes]}
        self._references: dict[str, dict[str, list[bytes]]] = {}

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY environment variable is not set")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def _get_references(self, model_name: str) -> dict[str, list[bytes]]:
        if model_name not in self._references:
            self._references[model_name] = load_all_references(DATA_MAP[model_name])
        return self._references[model_name]

    def predict(self, model_name: str, classes: list[str], target_bytes: bytes) -> dict:
        references = self._get_references(model_name)
        target_jpeg = _normalise(target_bytes)
        content = _build_content(classes, references, target_jpeg)

        response = self.client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": content},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0,
        )

        raw = response.choices[0].message.content.strip()
        # Strip accidental markdown fences
        if "```" in raw:
            raw = raw[raw.index("{") : raw.rindex("}") + 1]

        parsed = json.loads(raw)
        probabilities = {k: round(float(v), 4) for k, v in parsed.get("probabilities", {}).items()}
        predicted_class = parsed.get("predicted_class")
        return {
            "predicted_class": predicted_class,
            "confidence":      probabilities.get(predicted_class, 0.0),
            "probabilities":   probabilities,
        }


predictor = OpenAIVisionPredictor()
