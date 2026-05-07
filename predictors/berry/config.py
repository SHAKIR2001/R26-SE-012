import os

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "berry_diceas.keras"))
CLASSES = ["berries without diseases", "lace bug damage"]
DESCRIPTION = "Pepper berry disease detection"
