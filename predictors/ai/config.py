import os

from predictors.berry import config as berry_cfg
from predictors.leaf import config as leaf_cfg
from predictors.pest import config as pest_cfg

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

# Maps model_name → { class_label: subfolder_path }
DATA_MAP = {
    "berry": {
        "berries without diseases": os.path.join(BASE_DIR, "berry", "healthy"),
        "lace bug damage":          os.path.join(BASE_DIR, "berry", "lace"),
    },
    "leaf": {
        "Healthy":            os.path.join(BASE_DIR, "leaf", "healthy"),
        "Leaf blight disease": os.path.join(BASE_DIR, "leaf", "blight"),
        "Little_Leaf_Disease": os.path.join(BASE_DIR, "leaf", "little"),
        "Quick_Wilt_disease":  os.path.join(BASE_DIR, "leaf", "quick"),
    },
    "pest": {
        "Diconocoris distanti":  os.path.join(BASE_DIR, "phest", "diconocoris"),
        "Gynaikothrips karny":   os.path.join(BASE_DIR, "phest", "gynaikothrips"),
        "Healthy":               os.path.join(BASE_DIR, "phest", "healthy"),
        "Pterolopha annulata":   os.path.join(BASE_DIR, "phest", "pterolopha"),
    },
}

MODEL_REGISTRY = {
    "berry": berry_cfg,
    "leaf":  leaf_cfg,
    "pest":  pest_cfg,
}

GPT_MODEL  = "gpt-4o"
MAX_TOKENS = 600
