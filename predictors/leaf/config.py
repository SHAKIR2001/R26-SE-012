import os

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "leaf_dicease.keras"))
CLASSES = ["Healthy", "Leaf blight disease", "Little_Leaf_Disease", "Quick_Wilt_disease"]
DESCRIPTION = "Pepper leaf disease classification"
