# PEPPER — Project Memory

## What is PEPPER?

PEPPER is a pepper plant health monitoring system that uses three separate image classification models to diagnose different types of plant problems. Each model targets a different part of the plant and a different category of issue.

---

## Models

All three models share the same foundation:

| Property | Value |
|---|---|
| Architecture | EfficientNetV2B3 (transfer learning) |
| Input size | 224 × 224 px |
| Training strategy | Two-stage: 25 frozen epochs → 30 fine-tune epochs |
| Batch size | 16 |
| Learning rate | 3e-4 |
| Format | Keras (`.keras`) |

---

### 1. Berry Disease

| | |
|---|---|
| **Script** | `train_scripts/berry_dicease.ipynb` |
| **Model file** | `models/berry_diceas.keras` |
| **Task** | Binary classification of pepper berries |
| **Classes** | `berries without diseases`, `lace bug damage` |
| **Val accuracy** | ~84.6% |

---

### 2. Leaf Disease

| | |
|---|---|
| **Script** | `train_scripts/leaf_dicease.ipynb` |
| **Model file** | `models/leaf_dicease.keras` |
| **Task** | Multi-class pepper leaf disease classification |
| **Classes** | `Healthy`, `Leaf blight disease`, `Little_Leaf_Disease`, `Quick_Wilt_disease` |
| **Val accuracy** | ~85.7% |

---

### 3. Pest Detection

| | |
|---|---|
| **Script** | `train_scripts/phest.ipynb` |
| **Model file** | `models/best_mobilenet_model_phest_v2.keras` |
| **Task** | Pest / insect classification on pepper plants |
| **Classes** | `Diconocoris distanti`, `Gynaikothrips karny`, `Healthy`, `Pterolopha annulata` |
| **Val accuracy** | ~100% |

> **Note:** The model filename references MobileNet because early experiments used MobileNet before switching to EfficientNetV2B3.

---

## Inference Notes

- All three models expect the same preprocessing: resize to **224×224**, apply **EfficientNet preprocessing** (not raw normalization).
- Route images to the correct model based on what part of the plant is photographed (berry vs leaf vs pest view).
- Load models with `keras.models.load_model('models/<filename>.keras')`.

---

## File Structure

```
PEPPER/
├── models/
│   ├── berry_diceas.keras
│   ├── leaf_dicease.keras
│   └── best_mobilenet_model_phest_v2.keras
├── train_scripts/
│   ├── berry_dicease.ipynb
│   ├── leaf_dicease.ipynb
│   └── phest.ipynb
└── MEMORY.md
```
