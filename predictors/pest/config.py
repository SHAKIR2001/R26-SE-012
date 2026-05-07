import os

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "best_mobilenet_model_phest_v2.keras"))
CLASSES = ["Diconocoris distanti", "Gynaikothrips karny", "Healthy", "Pterolopha annulata"]
DESCRIPTION = "Pepper pest detection"
