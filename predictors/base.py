from __future__ import annotations

import io
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input

from config import IMAGE_SIZE


# Keras resolves built-in layers by module path, bypassing custom_objects.
# Monkey-patch Dense.__init__ so the `quantization_config` kwarg introduced
# in newer Keras versions is silently ignored on older installs.
_orig_dense_init = tf.keras.layers.Dense.__init__

def _dense_init_compat(self, *args, quantization_config=None, **kwargs):
    _orig_dense_init(self, *args, **kwargs)

tf.keras.layers.Dense.__init__ = _dense_init_compat


class BasePredictor:
    """
    Subclass and set model_path, classes, description as class attributes.
    The model is lazy-loaded on the first predict() call.
    """

    model_path: str
    classes: list[str]
    description: str

    def __init__(self):
        self._model: tf.keras.Model | None = None

    def _load(self) -> tf.keras.Model:
        if self._model is None:
            self._model = tf.keras.models.load_model(self.model_path, compile=False)
        return self._model

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize(IMAGE_SIZE)
        array = np.array(image, dtype=np.float32)
        array = np.expand_dims(array, axis=0)
        return preprocess_input(array)

    def predict(self, image_bytes: bytes) -> dict:
        model = self._load()
        x = self._preprocess(image_bytes)
        raw = model.predict(x, verbose=0)[0]

        if len(raw) == 1:
            # binary sigmoid — convert to two-class probability list
            p = float(raw[0])
            probs = [round(1.0 - p, 4), round(p, 4)]
        else:
            probs = [round(float(v), 4) for v in raw]

        predicted_index = int(np.argmax(probs))
        return {
            "predicted_class": self.classes[predicted_index],
            "confidence": probs[predicted_index],
            "probabilities": dict(zip(self.classes, probs)),
        }
