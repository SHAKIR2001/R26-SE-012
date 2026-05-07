# PEPPER API Documentation

Base URL: `http://localhost:5005`

---

## Overview

PEPPER exposes two families of endpoints:

| Family | Prefix | Engine | Use case |
|---|---|---|---|
| Local model | `/predict/*` | EfficientNetV2B3 (Keras) | Fast, offline inference |
| Vision AI | `/vision/*` | GPT-4o (OpenAI) | Explainable, characteristics-first classification |

- All prediction endpoints accept `multipart/form-data`
- Supported image formats: `jpg`, `jpeg`, `png`, `webp`, `heic`
- Maximum image size: **10 MB**
- All responses are `application/json`

---

## Endpoints

### GET `/health`

Liveness check.

**Response `200`**
```json
{ "status": "ok" }
```

---

## Local Model Endpoints — `/predict/*`

Fast inference using on-device Keras models. No internet required.

---

### POST `/predict/berry`

Classifies a pepper berry image as healthy or lace-bug-damaged.

**Request**

| Field | Type | Required | Description |
|---|---|---|---|
| `image` | file | yes | Berry image |

**Example**
```bash
curl -X POST http://localhost:5005/predict/berry \
  -F "image=@berry.jpg"
```

**Response `200`**
```json
{
  "model": "berry",
  "description": "Pepper berry disease detection",
  "predicted_class": "berries without diseases",
  "confidence": 0.9321,
  "probabilities": {
    "berries without diseases": 0.9321,
    "lace bug damage": 0.0679
  }
}
```

**Classes**

| Class | Description |
|---|---|
| `berries without diseases` | Healthy berry — no visible damage |
| `lace bug damage` | Berry damaged by lace bug (*Diconocoris distanti*) feeding |

---

### POST `/predict/leaf`

Classifies a pepper leaf image across four disease categories.

**Request**

| Field | Type | Required | Description |
|---|---|---|---|
| `image` | file | yes | Leaf image |

**Example**
```bash
curl -X POST http://localhost:5005/predict/leaf \
  -F "image=@leaf.jpg"
```

**Response `200`**
```json
{
  "model": "leaf",
  "description": "Pepper leaf disease classification",
  "predicted_class": "Healthy",
  "confidence": 0.8812,
  "probabilities": {
    "Healthy": 0.8812,
    "Leaf blight disease": 0.0621,
    "Little_Leaf_Disease": 0.0341,
    "Quick_Wilt_disease": 0.0226
  }
}
```

**Classes**

| Class | Description |
|---|---|
| `Healthy` | No disease detected |
| `Leaf blight disease` | Fungal / bacterial blight causing leaf necrosis |
| `Little_Leaf_Disease` | Phytoplasma infection — stunted, yellowed, clustered leaves |
| `Quick_Wilt_disease` | Bacterial wilt — sudden wilting and vascular browning |

---

### POST `/predict/pest`

Identifies pests on a pepper plant image.

**Request**

| Field | Type | Required | Description |
|---|---|---|---|
| `image` | file | yes | Plant image |

**Example**
```bash
curl -X POST http://localhost:5005/predict/pest \
  -F "image=@plant.jpg"
```

**Response `200`**
```json
{
  "model": "pest",
  "description": "Pepper pest detection",
  "predicted_class": "Healthy",
  "confidence": 0.9874,
  "probabilities": {
    "Diconocoris distanti": 0.0042,
    "Gynaikothrips karny": 0.0061,
    "Healthy": 0.9874,
    "Pterolopha annulata": 0.0023
  }
}
```

**Classes**

| Class | Description |
|---|---|
| `Healthy` | No pest detected |
| `Diconocoris distanti` | Lace bug — piercing-sucking pest on berries and leaves |
| `Gynaikothrips karny` | Thrips — causes leaf curling and gall formation |
| `Pterolopha annulata` | Longhorn beetle — bores into stems |

---

### Local Model Response Schema

```
{
  "model":           string  — berry | leaf | pest
  "description":     string  — human-readable task label
  "predicted_class": string  — top predicted class label
  "confidence":      float   — probability of predicted class (0.0 – 1.0)
  "probabilities":   object  — { class_label: probability } for all classes
}
```

### Local Model Details

| Endpoint | Architecture | Input size | Classes | Val accuracy |
|---|---|---|---|---|
| `/predict/berry` | EfficientNetV2B3 | 224 × 224 | 2 | ~84.6% |
| `/predict/leaf` | EfficientNetV2B3 | 224 × 224 | 4 | ~85.7% |
| `/predict/pest` | EfficientNetV2B3 | 224 × 224 | 4 | ~100% |

---

## Vision AI Endpoints — `/vision/*`

GPT-4o powered classification. Reference images are auto-loaded from the project's `data/` folder — you only send the target image. GPT-4o first identifies visual characteristics of each class from the references, then analyses the target and matches it to the closest class.

**Requires:** `OPENAI_API_KEY` environment variable.

---

### POST `/vision/<model_name>`

Classify an image using GPT-4o few-shot vision. `model_name` is one of `berry`, `leaf`, `pest`.

**Request**

| Field | Type | Required | Description |
|---|---|---|---|
| `target` | file | yes | Image to classify (jpg / png / webp / heic) |

**Example**
```bash
curl -X POST http://localhost:5005/vision/leaf \
  -F "target=@unknown_leaf.jpg"
```

**Response `200`**
```json
{
  "model": "leaf",
  "description": "Pepper leaf disease classification",
  "predicted_class": "Leaf blight disease",
  "confidence": "high",
  "reasoning": "The irregular necrotic patches with yellowing halos on the target leaf closely match the blight reference images.",
  "target_observations": "The leaf shows irregular brown necrotic patches along the margins with yellowing halos and some tissue collapse.",
  "class_characteristics": {
    "Healthy": "Uniform deep green colour, smooth texture, no lesions or discolouration",
    "Leaf blight disease": "Brown to black irregular necrotic lesions often at margins, with yellow halos",
    "Little_Leaf_Disease": "Stunted, small, clustered leaves with pale yellow-green discolouration and curling",
    "Quick_Wilt_disease": "Sudden drooping, water-soaked appearance, brown vascular streaks when cut"
  },
  "method": "openai_vision_few_shot",
  "gpt_model": "gpt-4o"
}
```

**How GPT-4o reasons:**
1. **Observe** — studies reference images per class, notes distinguishing visual traits
2. **Analyse** — examines the target image and describes what it sees
3. **Match** — compares target observations against each class's characteristics
4. **Conclude** — selects the best-matching class with a confidence level

---

### GET `/vision/<model_name>/info`

Returns the classes and number of reference images loaded from disk for a model.

**Example**
```bash
curl http://localhost:5005/vision/leaf/info
```

**Response `200`**
```json
{
  "model": "leaf",
  "description": "Pepper leaf disease classification",
  "classes": {
    "Healthy": 3,
    "Leaf blight disease": 3,
    "Little_Leaf_Disease": 3,
    "Quick_Wilt_disease": 3
  },
  "usage": "POST /vision/leaf  — field: target (image file)"
}
```

---

### Vision AI Response Schema

```
{
  "model":                string  — berry | leaf | pest
  "description":          string  — human-readable task label
  "predicted_class":      string  — predicted class label
  "confidence":           string  — high | medium | low
  "reasoning":            string  — why the target matches the predicted class
  "target_observations":  string  — GPT-4o's description of the target image
  "class_characteristics": object — { class_label: visual traits from references }
  "method":               string  — "openai_vision_few_shot"
  "gpt_model":            string  — GPT model used
}
```

---

## Error Responses

All errors return `{ "error": "<message>" }`.

| Status | Cause |
|---|---|
| `400` | Missing or empty `image` / `target` field |
| `400` | Unsupported file type |
| `404` | Unknown `model_name` in `/vision/<model_name>` |
| `413` | Image exceeds 10 MB |
| `500` | Model inference or OpenAI API error |
| `503` | `OPENAI_API_KEY` not set, or reference data folder missing |

---

## Running the Server

```bash
# install dependencies
pip install -r requirements.txt

# set OpenAI key (required only for /vision/* endpoints)
export OPENAI_API_KEY="sk-..."

# development (auto-reload)
uvicorn app:create_app --factory --interface wsgi --host 0.0.0.0 --port 5005 --reload

# production
uvicorn app:create_app --factory --interface wsgi --host 0.0.0.0 --port 5005 --workers 1
```
