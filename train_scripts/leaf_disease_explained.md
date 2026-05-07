# Leaf Disease Classifier — Complete Training Script Explanation

> **Who is this for?** Someone with zero deep learning knowledge. Every technical term is explained with plain English and real-world analogies.

---

## What Does This Script Do?

This notebook trains a computer to look at a photograph of a pepper leaf and classify it into one of **four categories**:

1. **Healthy** — the leaf is fine
2. **Leaf blight disease** — a fungal/bacterial disease causing brown spots and wilting
3. **Little Leaf Disease** — a disease caused by phytoplasmas making leaves shrink abnormally
4. **Quick Wilt disease** — a vascular disease causing sudden wilting and death of the plant

This is **multi-class classification** — one image, four possible answers. It is harder than binary (two-answer) classification.

The model is built using **EfficientNetV2B3**, a powerful image recognition network pre-trained on millions of general photos. We adapt it to recognise pepper leaf conditions through **transfer learning** and **fine-tuning**.

**Output:** A saved model file (`leaf_dicease.keras`) that can be used via a Flask API to classify new leaf photos in real time.

---

## How This Differs From the Berry Disease Script

The berry script classifies **2 classes** (binary). The leaf script classifies **4 classes** (multi-class). This difference cascades through several technical choices:

| Aspect | Berry (Binary) | Leaf (Multi-class) |
|--------|---------------|-------------------|
| Output neurons | 1 | 4 |
| Output activation | `sigmoid` | `softmax` |
| Loss function | `binary_crossentropy` | `categorical_crossentropy` |
| Label format | 0 or 1 | one-hot vector [0,1,0,0] |
| Decision rule | probability > 0.5 | `argmax` (pick highest probability) |

Everything else — data pipeline, augmentation, EfficientNetV2B3, two-phase training, evaluation — is identical in structure.

---

## The 16-Section Pipeline at a Glance

```
1.  Connect Google Drive
2.  Markdown header
3.  Markdown: Section 1 - Configuration
4.  Move Healthy folder (data cleanup)
5.  Configuration cell (set all parameters here)
6.  Data Splitting (60% train / 10% val / 30% test)
7–8. Verify split counts
9.  Fix nested subfolder in Healthy class
10. Section 2 header (markdown)
11. Import libraries
12. Section 3 header (markdown)
13. Load & inspect dataset (class detection + counts)
14. Verify Healthy folder contents
15. Section 4 header (markdown)
16. Visualise sample images
17. Directory listing (debugging)
18. Section 5 header (markdown)
19. Build data pipeline + augmentation
20. Section 5b header (markdown)
21. Visualise augmented images
22. Section 6 header (markdown)
23. Build EfficientNetV2B3 model
24. Section 7 header (markdown)
25. Phase 1: Feature extraction training
26. Section 8 header (markdown)
27. Phase 2: Fine-tuning
28. Section 9 header (markdown)
29. Plot training history
30. Section 10 header (markdown)
31. Evaluate on test set
32. Section 11 header (markdown)
33. Confusion matrix
34. Section 12 header (markdown)
35. Classification report
36. Section 13 header (markdown)
37. ROC curves
38. Section 14 header (markdown)
39. Correct & incorrect prediction samples
40. Section 15 header (markdown)
41. Save & export model
42. Alternative: MobileNetV3Small
43. Class weights for imbalanced data
44. Train MobileNet with weights
45. Reinitialise pipelines (simplified augmentation)
46. Plot MobileNet results
47. Save MobileNet model
48. Load & show random predictions
49. Flask API wrapper
```

---

## Cell-by-Cell Explanation

---

### Cell 0 — Connect to Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

**What it does:** Connects Google Drive so the Colab session can read your dataset files. After mounting, files are accessible at `/content/drive/MyDrive/`.

**Why it's needed:** Google Colab runs in a temporary cloud computer with no files. Your dataset lives in Drive. This bridges the two.

**Analogy:** Plugging a USB drive into your laptop so your laptop can read the files on it.

---

### Cells 1–2 — Markdown Headers

Decorative HTML/markdown section titles with styled purple boxes. No code effect — purely visual for notebook readability.

---

### Cell 3 — Move Healthy Folder (Data Cleanup)

```python
source_path = os.path.join(BASE_DATA_DIR, 'Healthy')
destination_parent = '/content/drive/MyDrive/PEPPER/leaf_disease/Component01-Leaf disease detection'
shutil.move(source_path, destination_path)
```

**What it does:** Moves the `Healthy` folder from a different location into the leaf disease dataset directory. A one-time dataset organisation step.

**Why it's needed:** During initial data preparation, the "Healthy" class images may have been stored in the wrong place. This corrects the folder structure so the data loader finds all four classes.

**`shutil.move`** — moves a folder (and all its contents) from source to destination. Unlike `shutil.copy`, the original is deleted after moving.

---

### Cell 4 — Configuration: The Control Panel

```python
BASE_DATA_DIR       = '/content/drive/MyDrive/PEPPER/leaf_disease/Component01-Leaf disease detection'
TRAIN_SPLIT_RATIO   = 0.6     # 60% for training
VAL_SPLIT_RATIO     = 0.1     # 10% for validation
TEST_SPLIT_RATIO    = 0.3     # 30% for testing
CLASS_NAMES         = None    # auto-detected
NUM_CLASSES         = None    # auto-detected
DOWNSAMPLE_TO_MIN_CLASS = True
IMG_SIZE            = (224, 224)
BATCH_SIZE          = 16
EPOCHS_FROZEN       = 25
EPOCHS_FINETUNE     = 30
LEARNING_RATE       = 3e-4
FINETUNE_LR         = 1e-6
UNFREEZE_LAYERS     = 10
SEED                = 42
MODEL_SAVE_PATH     = 'best_model.h5'
```

**What it does:** Defines every tunable parameter in one place. All other cells read from these variables. You should only ever edit this cell — nothing else needs to change.

**Parameter deep-dive:**

**`BASE_DATA_DIR`** — The root folder containing four sub-folders, one per disease class. The folder names become the class names.

**`TRAIN_SPLIT_RATIO = 0.6`** — 60% of images go to training. The model actually learns from these.
- Increase to 0.75 → more training data, but smaller test evaluation
- Decrease to 0.5 → better test coverage, but less training data

**`VAL_SPLIT_RATIO = 0.1`** — 10% used for validation during training (guides early stopping, LR reduction).
- This split watches for overfitting but never directly trains the model.

**`TEST_SPLIT_RATIO = 0.3`** — 30% held completely aside until the very end. The final honest measure of model quality.

**`DOWNSAMPLE_TO_MIN_CLASS = True`** — "Quick Wilt disease" has the fewest images (11 in the notebook's comment). Setting this to `True` trims all other classes to match that count. Prevents the model from gaming accuracy by guessing the majority class.
- Set to `False` if you want to use all available images (but then use class weights to compensate for imbalance)

**`IMG_SIZE = (224, 224)`** — EfficientNetV2B3 was designed for 224×224 pixel inputs. Changing this breaks compatibility.

**`BATCH_SIZE = 16`** — 16 images processed together before the model updates its weights.
- Larger (32, 64): faster training but requires more GPU memory
- Smaller (8, 4): more memory-efficient but noisier gradient updates
- With very small datasets (as here), 8 or 16 is appropriate

**`EPOCHS_FROZEN = 25`** — Maximum full passes through training data in Phase 1. Early stopping typically stops before this limit.

**`EPOCHS_FINETUNE = 30`** — Maximum for Phase 2. Fine-tuning typically converges faster with very small LR.

**`LEARNING_RATE = 3e-4`** — Step size for Phase 1 (= 0.0003).
- Too large: training accuracy jumps around, never converges
- Too small: training is very slow or gets stuck

**`FINETUNE_LR = 1e-6`** — Step size for Phase 2 (= 0.000001). Must be 100-1000× smaller than Phase 1 to avoid destroying EfficientNet's pre-learned features.

**`UNFREEZE_LAYERS = 10`** — In Phase 2, the top 10 layers of EfficientNetV2B3 are unlocked for adaptation.
- More layers → more adaptation, more risk of forgetting
- Fewer layers → safer but less adaptation to leaf images specifically

**`SEED = 42`** — Standard convention for reproducibility. Any integer works; 42 is tradition.

---

### Cell 5 — Data Splitting

```python
# 1. Auto-detect classes
CLASS_NAMES = sorted([
    d for d in os.listdir(BASE_DATA_DIR)
    if os.path.isdir(os.path.join(BASE_DATA_DIR, d))
    and d.lower() not in ['train', 'val', 'test']
])

# 2. Pick label mode
LABEL_MODE = 'binary' if NUM_CLASSES == 2 else 'categorical'
ACTIVATION = 'sigmoid' if NUM_CLASSES == 2 else 'softmax'
LOSS       = 'binary_crossentropy' if NUM_CLASSES == 2 else 'categorical_crossentropy'

# 3. Gather image paths
class_image_paths = {cls: [] for cls in CLASS_NAMES}
for cls in CLASS_NAMES:
    for img in os.listdir(os.path.join(BASE_DATA_DIR, cls)):
        if img.lower().endswith(('.jpg', '.jpeg', '.png')):
            class_image_paths[cls].append(...)

# 4. Optional downsampling
if DOWNSAMPLE_TO_MIN_CLASS:
    min_size = min(len(paths) for paths in class_image_paths.values())
    for cls in class_image_paths:
        if len(class_image_paths[cls]) > min_size:
            class_image_paths[cls] = random.sample(class_image_paths[cls], min_size)

# 5. Two-stage split
X_train, X_temp, y_train, y_temp = train_test_split(..., train_size=0.6, stratify=labels)
X_val, X_test, y_val, y_test     = train_test_split(X_temp, ..., stratify=y_temp)

# 6. Copy files into /tmp/temp_dataset_split/
```

**What it does:** Divides all leaf images into three buckets (train/val/test), then physically copies them into temporary folders that Keras can read.

**Why splitting matters:**

Think of training a student (the model) for an exam:
- **Training set** — the practice problems they solve every day
- **Validation set** — weekly mock exams during the study period (used for early stopping)
- **Test set** — the real exam on exam day (never seen before)

If the student practiced on the exam questions (trained and tested on same data), they'd score 100% without actually learning anything. The split prevents this.

**Auto-detect classes:**
`d.lower() not in ['train', 'val', 'test']` — ignores any pre-existing split folders inside `BASE_DATA_DIR`. Only picks up disease class folders.

**Four detected classes:**
```
['Healthy', 'Leaf blight disease', 'Little_Leaf_Disease', 'Quick_Wilt_disease']
```

**`categorical` mode:** Because there are 4 classes (not 2), labels are one-hot encoded:
- Healthy → `[1, 0, 0, 0]`
- Leaf blight → `[0, 1, 0, 0]`
- Little Leaf → `[0, 0, 1, 0]`
- Quick Wilt → `[0, 0, 0, 1]`

**`stratify=labels`** — Ensures each split preserves the original class proportions. If "Quick Wilt" is 15% of all images, then it's 15% of training, 15% of validation, and 15% of test.

**Two-stage split:**
`val_size_relative_to_temp = 0.1 / (0.1 + 0.3) = 0.25`
First split: 60% train, 40% "temp". Then split temp 25/75: → 10% val, 30% test. This correctly achieves the 60/10/30 split.

---

### Cells 6, 7, 8 — Dataset Verification (Repeated)

These three cells are identical — they print image counts per class per split. They exist because the developer ran the verification multiple times during debugging. Safe to run; read-only.

---

### Cell 9 — Fix Nested Subfolder in Healthy

```python
SUBFOLDER_PATH = os.path.join(HEALTHY_CLASS_DIR, 'black_pepper_healthy')
if os.path.isdir(SUBFOLDER_PATH):
    for item_name in os.listdir(SUBFOLDER_PATH):
        shutil.move(source_path, destination_path)
    os.rmdir(SUBFOLDER_PATH)
```

**What it does:** Checks if images in the `Healthy` class are accidentally stored in a sub-folder (`Healthy/black_pepper_healthy/`) instead of directly in `Healthy/`. If so, moves them up one level and removes the empty sub-folder.

**Why it breaks things:** Keras's `image_dataset_from_directory` expects `Healthy/*.jpg` — images directly in the class folder. If images are in `Healthy/black_pepper_healthy/*.jpg`, Keras either ignores them or incorrectly treats `black_pepper_healthy` as a sub-class.

**`os.rmdir`** — only works on empty directories. After all files are moved out, this removes the now-empty sub-folder.

---

### Cell 10 (Section Header) & Cell 11 — Import Libraries

```python
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import seaborn as sns, tensorflow as tf
from tensorflow.keras import layers, Model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, GlobalAveragePooling2D
from tensorflow.keras.applications import EfficientNetV2B3
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

warnings.filterwarnings('ignore')
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)
```

**What it does:** Loads all necessary software toolboxes. Sets random seeds for reproducibility.

**Key libraries:**

| Library | Role |
|---------|------|
| `numpy` | Numerical arrays — the underlying data format for images and predictions |
| `pandas` | Tables for displaying metrics |
| `matplotlib` + `seaborn` | Visualisations: charts, confusion matrix heatmaps |
| `tensorflow` / `keras` | The deep learning framework — builds, trains, and evaluates the model |
| `EfficientNetV2B3` | Pre-trained image classification model (the backbone) |
| `Adam` | Optimiser — decides how to update weights after each training step |
| `EarlyStopping` | Stops training early if validation accuracy stops improving |
| `ModelCheckpoint` | Saves the model whenever validation accuracy improves |
| `ReduceLROnPlateau` | Halves the learning rate when training gets stuck |
| `sklearn.metrics` | Tools for computing accuracy, confusion matrix, classification report |

**Reproducibility seeds:** Three seeds must be set for fully reproducible results:
- `np.random.seed(SEED)` — NumPy random operations (data shuffling)
- `tf.random.set_seed(SEED)` — TensorFlow random operations (weight initialisation, dropout)
- `os.environ['PYTHONHASHSEED'] = str(SEED)` — Python's built-in hash randomness

---

### Cells 12–15 — Dataset Loading, Inspection, and Healthy Folder Check

These cells auto-detect classes, print image counts per split, and verify the Healthy folder. These are safeguards and debugging tools — they produce no model changes.

**What you're looking for when reading their output:**
- All 4 class names detected correctly
- Roughly equal image counts across classes (if downsampling is on)
- All three splits (train/val/test) have images in them

---

### Cells 16 & 17 — Visualise Sample Images

```python
num_cols = min(NUM_CLASSES, 6)  # up to 6 columns (one per class)
num_rows = 3                    # 3 sample images per class
fig, axes = plt.subplots(num_rows, num_cols, ...)

for col_idx, cls in enumerate(CLASS_NAMES[:num_cols]):
    images = [f for f in os.listdir(cls_path) if f.endswith(('.jpg',...))][:num_rows]
    for row_idx, img_file in enumerate(images):
        ax.imshow(mpimg.imread(path))
```

**What it does:** Creates a 3×4 grid of sample training images, one column per disease class. Each image is displayed with its class name as the column title.

**Why it's needed:** A visual sanity check before training begins. If a folder is empty, wrong, or corrupted, you see it immediately in the grid instead of discovering it 30 minutes into training.

---

### Cell 18 (Debug) & Cell 19 (Section Header) — Directory Listing

Cell 18 lists contents of TRAIN_DIR, VAL_DIR, TEST_DIR — debugging only. Cell 19 is a markdown header "Section 5 - Data Pipelines & Augmentation".

---

### Cell 20 (Section 5) — Build Data Pipeline + Augmentation

```python
AUTOTUNE = tf.data.AUTOTUNE

def load_split(directory, shuffle=True, label_mode=LABEL_MODE):
    return tf.keras.utils.image_dataset_from_directory(
        directory=directory,
        labels='inferred',
        label_mode='categorical',   # 4-class one-hot labels
        class_names=CLASS_NAMES,
        color_mode='rgb',
        batch_size=BATCH_SIZE,      # 16
        image_size=IMG_SIZE,        # (224, 224)
        shuffle=shuffle,
        seed=SEED
    )

train_ds_raw = load_split(TRAIN_DIR, shuffle=True)
val_ds_raw   = load_split(VAL_DIR,   shuffle=False)
test_ds_raw  = load_split(TEST_DIR,  shuffle=False)

data_augmentation = keras.Sequential([
    layers.RandomFlip('horizontal'),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.15),
    layers.RandomContrast(0.15),
    layers.RandomBrightness(0.1),
    layers.RandomTranslation(height_factor=0.1, width_factor=0.1),
])

train_ds = (
    train_ds_raw
    .map(augment_and_normalize, num_parallel_calls=AUTOTUNE)
    .cache()
    .shuffle(buffer_size=1000, seed=SEED)
    .prefetch(AUTOTUNE)
)
```

**What it does:** Builds three highly optimised data pipelines for training, validation, and test. Defines six random augmentation transformations applied only to training images.

**`image_dataset_from_directory` — how it works:**
Keras scans the directory. Each sub-folder name becomes a class. It assigns integer indices alphabetically (Healthy=0, Leaf blight=1, Little Leaf=2, Quick Wilt=3). With `label_mode='categorical'`, each label is a one-hot vector.

**Key difference from berry script:**
`label_mode='categorical'` instead of `'binary'`. This produces labels like `[0, 0, 1, 0]` instead of `0` or `1`. The model outputs 4 probabilities (one per class) summing to 1.0 via softmax.

**Augmentation pipeline — what each transformation does:**

| Transformation | Example | Why it helps |
|---|---|---|
| `RandomFlip('horizontal')` | Mirror left-right | A diseased leaf looks the same from either side |
| `RandomRotation(0.15)` | Rotate ±54° | Leaves are photographed at various angles |
| `RandomZoom(0.15)` | Zoom in/out 15% | Camera distance varies |
| `RandomContrast(0.15)` | Increase/decrease contrast 15% | Lighting conditions change |
| `RandomBrightness(0.1)` | Brighten/darken 10% | Sun angle, shadow |
| `RandomTranslation(0.1, 0.1)` | Shift up/down/left/right by 10% | Leaf not always centred |

**Only training data gets augmented.** Validation and test images go through only `tf.cast(image, tf.float32)` — converting pixel values to the float format EfficientNet expects (no normalisation needed because `include_preprocessing=True` handles it inside the model).

**Pipeline optimisation chain:**

```
train_ds_raw
  .map(augment_and_normalize, num_parallel_calls=AUTOTUNE)  ← parallel CPU augmentation
  .cache()           ← store in RAM after epoch 1, skip disk reads
  .shuffle(1000)     ← mix 1000 images in a buffer
  .prefetch(AUTOTUNE) ← prepare next batch while GPU trains
```

`AUTOTUNE` means TensorFlow automatically chooses the optimal number of parallel workers based on available CPU cores.

**Alternatives:**
- `ImageDataGenerator` (older Keras API — simpler but slower)
- `albumentations` (more augmentation options, e.g., elastic distortion)
- No augmentation (risks overfitting with small datasets)

---

### Cell 22 & Cell 23 — Visualise Augmentation

```python
for images, labels in train_ds_raw.take(1):
    sample_img = images[0:1]  # take first image from first batch

aug_imgs = [data_augmentation(sample_img, training=True)[0].numpy().astype('uint8') for _ in range(8)]
```

**What it does:** Takes one leaf image and generates 8 different augmented versions, displayed in a 2×4 grid.

**`training=True`** in `data_augmentation(sample_img, training=True)` is critical — augmentation layers only apply randomness when `training=True`. With `training=False`, they pass images through unchanged (which is what happens during validation/testing).

---

### Cells 24 & 25 — Build the EfficientNetV2B3 Model

```python
def build_model(num_classes, img_size, learning_rate, base_trainable=False):
    base_model = EfficientNetV2B3(
        include_top=False,
        weights='imagenet',
        input_shape=(224, 224, 3),
        include_preprocessing=True
    )
    base_model.trainable = False  # freeze during Phase 1

    inputs = keras.Input(shape=(224, 224, 3))
    x = base_model(inputs, training=False)
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.4)(x)
    outputs = Dense(4, activation='softmax')(x)  # 4 classes, softmax

    model.compile(optimizer=Adam(lr), loss='categorical_crossentropy', metrics=['accuracy'])
```

**What it does:** Constructs the full neural network — a pre-trained feature extractor (EfficientNetV2B3) with a custom classification head on top.

**Analogy:** EfficientNetV2B3 is like a skilled botanist who can describe exactly what they see in a leaf photo ("round spots, yellowing at edges, fuzzy white growth"). Your custom head is the diagnostic system that takes those descriptions and outputs: "67% Leaf Blight, 20% Little Leaf, 8% Quick Wilt, 5% Healthy."

**Layer-by-layer breakdown:**

**`EfficientNetV2B3(include_top=False, weights='imagenet')`**
The backbone. Trained on 1.2 million ImageNet images. Without `include_top`, it outputs a 7×7×1536 feature map (7×7 spatial grid, 1536 feature channels).

**`GlobalAveragePooling2D()`**
Collapses the 7×7×1536 feature map to a 1536-element flat vector by averaging each of the 1536 feature channels across the 7×7 grid.
*Analogy: Instead of reporting what you see in every square of a 7×7 grid, report the average colour/texture across all squares.*

**`BatchNormalization()`**
Normalises the 1536 values to have zero mean and unit variance. Speeds up training and reduces sensitivity to learning rate.

**`Dense(512, activation='relu')`**
512 artificial neurons, each connected to all 1536 inputs. `relu` activation: any negative value becomes 0. This layer learns high-level combinations of features.
*Analogy: 512 specialists each asking "do I see something relevant in this combination of features?"*

**`Dropout(0.5)`**
During each training step, randomly disables 50% of the 512 neurons. Prevents over-reliance on any single neuron. Reduces overfitting.
*Analogy: If half your specialists are unavailable for each practice session, the team learns to function without relying on specific individuals.*

**`BatchNormalization()`**
Another normalising layer between the two Dense blocks.

**`Dense(256, activation='relu')`**
Narrowing the 512 features further to 256 by another learned combination.

**`Dropout(0.4)`**
Randomly disables 40% of 256 neurons.

**`Dense(4, activation='softmax')`** ← KEY DIFFERENCE from berry script
4 output neurons — one per disease class. `softmax` converts raw scores to probabilities summing to 1.0:
- e.g., `[0.67, 0.20, 0.08, 0.05]` → "67% Leaf Blight, 20% Little Leaf, 8% Quick Wilt, 5% Healthy"

**`loss='categorical_crossentropy'`** — measures how wrong the 4-probability prediction is compared to the one-hot true label. Standard choice for multi-class classification.

**Why different activations for binary vs multi-class?**

| Task | Output neurons | Activation | Loss |
|------|---------------|------------|------|
| Binary (berry) | 1 | sigmoid → 0 to 1 | binary_crossentropy |
| Multi-class (leaf) | 4 | softmax → 4 probabilities summing to 1 | categorical_crossentropy |

**Alternatives:**

| Component | Alternatives |
|---|---|
| EfficientNetV2B3 | ResNet50V2, DenseNet121, ConvNeXt, ViT |
| Adam optimiser | SGD with momentum, RMSprop, AdamW |
| relu activation | leaky_relu, elu, gelu |
| Dropout | SpatialDropout2D, GaussianDropout, L2 regularisation |

---

### Cells 26 & 27 — Phase 1: Feature Extraction Training

```python
callbacks_phase1 = [
    EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7),
    ModelCheckpoint('checkpoint_phase1.h5', monitor='val_accuracy', save_best_only=True)
]

history1 = model.fit(
    train_ds,
    epochs=25,
    validation_data=val_ds,
    callbacks=callbacks_phase1
)
```

**What it does:** Trains only the custom head (Dense/Dropout layers) while EfficientNetV2B3 is completely frozen. The model learns to interpret EfficientNet's features for leaf disease categories.

**The two-phase approach explained:**

**Why not train everything at once?**
EfficientNetV2B3's weights were carefully tuned on 1.2 million images. The custom head starts with random weights. In the first steps of training, the head generates terrible predictions → huge errors → large gradient updates. If EfficientNet was unfrozen, those large updates would scramble its carefully learned features in the very first epoch.

**Phase 1 (frozen):** Only the head learns. EfficientNet acts like a fixed feature extractor. The head learns which features matter for leaf diseases. This is fast (few parameters to update) and stable.

**Phase 2 (fine-tuning):** Once the head has reasonable weights and produces smaller errors, we gently unfreeze the top layers of EfficientNet and let them adapt slightly.

**Callback details:**

`EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True)`:
- Watches validation accuracy after every epoch
- If 5 consecutive epochs pass with no improvement → stop training
- `restore_best_weights=True` → reverts to the epoch with highest val_accuracy, not the last epoch

`ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7)`:
- Watches validation loss
- If no improvement for 3 epochs → multiply learning rate by 0.5
- `min_lr=1e-7` → never reduce below this floor
- *Analogy: If you're not making progress with your current step size, try smaller steps.*

`ModelCheckpoint('checkpoint_phase1.h5', save_best_only=True)`:
- Saves model to `checkpoint_phase1.h5` whenever val_accuracy improves
- At end of Phase 1, this file contains the best Phase 1 weights

**Reading the progress output:**
```
Epoch 5/25 - loss: 0.4521 - accuracy: 0.8142 - val_loss: 0.6231 - val_accuracy: 0.7500
```
- `loss` / `accuracy` → training set performance (seen data)
- `val_loss` / `val_accuracy` → validation set performance (unseen data — the honest score)

---

### Cells 28 & 29 — Phase 2: Fine-Tuning

```python
base_model.trainable = True
for layer in base_model.layers[:-10]:  # freeze everything except last 10 layers
    layer.trainable = False

model.compile(optimizer=Adam(learning_rate=1e-6), loss='categorical_crossentropy', ...)

callbacks_phase2 = [
    EarlyStopping(monitor='val_accuracy', patience=7, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=3, min_lr=1e-8),
    ModelCheckpoint(MODEL_SAVE_PATH, monitor='val_accuracy', save_best_only=True)
]
history2 = model.fit(train_ds, epochs=30, validation_data=val_ds, callbacks=callbacks_phase2)
```

**What it does:** Unlocks the top 10 layers of EfficientNetV2B3 and allows them to adapt to leaf disease images, while keeping the remaining (lower) layers frozen.

**Why only the top 10 layers?**
Neural networks learn features hierarchically:
- **Low layers** (bottom of the network) → edges, colours, simple textures → universal to all images
- **High layers** (top of the network) → complex patterns like "spotted texture on green surface" → more specific

Only the high-level layers need to change for leaf disease. Low-level edge detection is already perfect and doesn't need modification.

**`base_model.layers[:-10]`** — Python list slicing: "all layers except the last 10". These are re-frozen. Only the last 10 EfficientNet layers + the entire custom head are trainable.

**`Adam(learning_rate=1e-6)`** — 300× smaller than Phase 1 learning rate. Tiny steps prevent destroying EfficientNet's existing knowledge while still allowing gradual adaptation.

**Phase 2 callbacks vs Phase 1:**
| | Phase 1 | Phase 2 |
|--|--|--|
| EarlyStopping patience | 5 | 7 (more patient — fine-tuning is slower) |
| ReduceLROnPlateau factor | 0.5 (halve) | 0.3 (reduce to 30% — more aggressive) |
| ReduceLROnPlateau patience | 3 | 3 |
| min_lr | 1e-7 | 1e-8 (lower floor for Phase 2) |
| ModelCheckpoint file | checkpoint_phase1.h5 | MODEL_SAVE_PATH (best_model.h5) |

---

### Cells 30 & 31 — Training History Plots

```python
history_all = merge_histories(history1, history2)
ax.plot(history_all['accuracy'], label='Train Accuracy')
ax.plot(history_all['val_accuracy'], label='Val Accuracy')
ax.axvline(x=phase1_end - 1, color='red', linestyle='--', label='Fine-tune start')
```

**What it does:** Merges Phase 1 and Phase 2 training logs and draws two charts:
1. **Accuracy over epochs** — train accuracy (blue) vs validation accuracy (orange)
2. **Loss over epochs** — train loss (blue) vs validation loss (orange)

A red dashed vertical line marks where Phase 1 ended and Phase 2 began.

**Interpreting the charts:**

Healthy training (what you want to see):
- Both accuracy curves rise together and converge at high values
- After the red line (fine-tuning), there may be a small dip then improvement

Signs of overfitting:
- Training accuracy keeps rising but validation accuracy plateaus or drops after some point
- Gap between train and validation accuracy widens over time

Signs of underfitting:
- Both curves are low and flat — the model is not learning

The red dashed line reveals whether fine-tuning (Phase 2) actually helped.

---

### Cells 32 & 33 — Evaluate on Test Set

```python
best_model = keras.models.load_model(MODEL_SAVE_PATH)
test_loss, test_acc = best_model.evaluate(test_ds)
y_pred_proba = best_model.predict(test_ds)

# Multi-class: pick the class with highest probability
y_pred = np.argmax(y_pred_proba, axis=1)
y_true = np.concatenate([np.argmax(y.numpy(), axis=1) for _, y in test_ds])
```

**What it does:** Loads the best saved model and evaluates it on completely unseen test images.

**`keras.models.load_model(MODEL_SAVE_PATH)`** — reloads the model from disk. Important: ModelCheckpoint saved the best version during training. This ensures we evaluate the best model, not necessarily the final epoch's model.

**`best_model.evaluate(test_ds)`** — runs all test images through the model. Returns overall loss and accuracy. This is the most honest performance number.

**`best_model.predict(test_ds)`** — returns raw softmax probabilities for each test image. Shape: `(num_test_images, 4)`. Each row sums to 1.0.

**Multi-class decision:**
`np.argmax(y_pred_proba, axis=1)` — for each image, pick the class index with the highest probability.
- e.g., `[0.05, 0.72, 0.15, 0.08]` → argmax = 1 → "Leaf blight disease"

`np.argmax(y.numpy(), axis=1)` for true labels — converts one-hot `[0,1,0,0]` back to index 1.

---

### Cells 34 & 35 — Confusion Matrix

```python
cm = confusion_matrix(y_true, y_pred)
cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
sns.heatmap(cm, annot=True, xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
```

**What it does:** Creates a 4×4 grid showing how often each class was predicted correctly or confused with another class.

**Reading the confusion matrix:**

```
                  Predicted:  Healthy  Blight  LittleLeaf  QuickWilt
Actual: Healthy      [15]       [1]      [0]       [0]
Actual: Blight        [2]      [12]      [1]       [0]
Actual: LittleLeaf    [0]       [0]     [14]       [2]
Actual: QuickWilt     [1]       [0]      [0]      [10]
```
- Numbers on the diagonal = correct predictions
- Numbers off the diagonal = errors (what the true class was vs what was predicted)
- A large off-diagonal number shows two classes the model confuses

`cm_norm` normalises each row so values show the fraction of each actual class correctly classified (0.0 to 1.0). This is useful when classes have different numbers of images.

**`sns.heatmap`** — renders the matrix as a colour-coded grid. Dark blue = large number, light = small. `annot=True` writes the actual numbers inside each cell.

**What to look for:**
- Are there specific pairs of diseases the model confuses? (Off-diagonal hot spots)
- Is one class consistently misclassified? (Entire row has low diagonal value)
- Does "Quick Wilt" perform worse because it had fewer training images?

---

### Cells 36 & 37 — Classification Report

```python
report = classification_report(y_true, y_pred, target_names=CLASS_NAMES)
print(report)
```

**What it does:** Prints a table with Precision, Recall, and F1-Score for each of the four leaf disease classes.

**The three metrics explained:**

**Precision** = True Positives / (True Positives + False Positives)
"Of all images I predicted as 'Leaf Blight', what percentage actually had Leaf Blight?"
High precision = low false alarm rate.

**Recall** = True Positives / (True Positives + False Negatives)
"Of all images that actually had 'Leaf Blight', what percentage did I correctly identify?"
High recall = low missed detection rate.

**F1-Score** = harmonic mean of Precision and Recall
The balanced metric when both matter. Formula: `2 × P × R / (P + R)`.

**For disease detection, recall typically matters more:**
Missing a diseased plant (false negative) means it goes untreated and potentially spreads. A false alarm (false positive) just means an extra inspection.

**Example output:**
```
                     precision  recall  f1-score  support
Healthy                  0.88    0.94     0.91      16
Leaf blight disease      0.85    0.80     0.82      15
Little_Leaf_Disease      0.93    0.88     0.90      16
Quick_Wilt_disease       0.91    0.82     0.86      11
```

Low recall for "Quick Wilt" (fewest samples) is common and why class weights help.

---

### Cells 38 & 39 — ROC Curves

```python
# Multi-class: one ROC curve per class (one-vs-rest)
y_true_bin = np.eye(NUM_CLASSES)[y_true]  # convert to one-hot
for i, cls in enumerate(CLASS_NAMES):
    fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_pred_proba[:, i])
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, label=f'{cls} (AUC = {roc_auc:.3f})')
ax.plot([0,1],[0,1], 'k--', label='Random Classifier')
```

**What it does:** For each of the 4 classes, draws a separate ROC curve showing the trade-off between sensitivity and false alarms at every possible decision threshold. Also computes AUC.

**Multi-class ROC — one-vs-rest:**
For 4 classes, we can't draw a single ROC curve. Instead we draw one curve per class: "Is this image Healthy or not? Is this image Leaf Blight or not?" etc. Each curve is independent.

**AUC interpretation:**
- AUC = 1.0 → perfect
- AUC = 0.5 → random guessing
- Typically want AUC > 0.85 for plant disease detection

**`np.eye(NUM_CLASSES)[y_true]`** — converts integer labels (e.g., 2) to one-hot vectors `[0,0,1,0]`. `np.eye` creates an identity matrix; indexing it by class index extracts the corresponding row.

**The dashed diagonal** represents random guessing — your curves should be far above it (toward the top-left corner).

---

### Cells 40 & 41 — Correct & Incorrect Prediction Samples

```python
correct_idx   = np.where(y_pred == y_true)[0]
incorrect_idx = np.where(y_pred != y_true)[0]
plot_samples(correct_idx,   'Correct Predictions')   # green titles
plot_samples(incorrect_idx, 'Incorrect Predictions') # red titles
```

**What it does:** Randomly selects and displays 8 correctly predicted images and 8 incorrectly predicted images, with the true and predicted class as the image title.

**Why look at failure cases?**
Error analysis often reveals systematic problems:
- Is the model always wrong on blurry photos?
- Does it confuse two specific diseases (their visual patterns are similar)?
- Are incorrect images from one particular class almost all?

These insights guide what to fix: more data? Better augmentation? Merge similar classes?

---

### Cells 42 & 43 — Save & Export Model

```python
best_model.save(MODEL_SAVE_PATH)             # best_model.h5
best_model.export('best_model_savedmodel')   # SavedModel folder
class_map = {i: name for i, name in enumerate(CLASS_NAMES)}
with open('class_names.json', 'w') as f:
    json.dump(class_map, f, indent=2)
```

**What it does:** Saves the trained model in two formats and writes a JSON class index file.

**Why two formats?**
- **`.h5`** — HDF5 format. One file, easy to share and load with `keras.models.load_model()`.
- **SavedModel folder** — TensorFlow's native format. Required for TensorFlow Serving, deployment on Google Cloud, and mobile/edge deployment.

**`class_names.json` contents:**
```json
{
  "0": "Healthy",
  "1": "Leaf blight disease",
  "2": "Little_Leaf_Disease",
  "3": "Quick_Wilt_disease"
}
```
This file is essential for the inference API — without it, the model would output `2` but you wouldn't know that means "Little_Leaf_Disease".

**Final summary printout** lists test accuracy, model file names, and checks whether all output files exist.

---

### Cells 44 & 45 — Alternative: MobileNetV3Small

```python
from tensorflow.keras.applications import MobileNetV3Small
base_model_alt = MobileNetV3Small(weights='imagenet', include_top=False, input_shape=(224,224,3))
x = GlobalAveragePooling2D()(base_model_alt.output)
predictions = Dense(NUM_CLASSES, activation='softmax')(x)
alt_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
```

**What it does:** Builds an alternative, lighter model using MobileNetV3Small instead of EfficientNetV2B3.

**MobileNetV3Small vs EfficientNetV2B3:**

| | MobileNetV3Small | EfficientNetV2B3 |
|---|---|---|
| Model size | ~6MB | ~45MB |
| Speed | ~3-5× faster | Slower |
| Accuracy | Lower | Higher |
| Best for | Mobile/edge devices | Server inference |

This alternative model has a simpler head (just GAP + Dense(4) — no dropout or extra Dense layers) because MobileNet is already more regularised by design.

---

### Cell 46 — Class Weights for Quick Wilt

```python
y_train = np.concatenate([np.argmax(y.numpy(), axis=1) for _, y in train_ds_raw])
weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = dict(enumerate(weights))
```

**What it does:** Calculates per-class penalty weights to compensate for class imbalance. "Quick Wilt" has the fewest samples, so it gets the highest weight.

**`compute_class_weight('balanced', ...)`** formula:
`weight = total_images / (num_classes × count_of_this_class)`

Example: 4 classes, 60 total images, Quick Wilt has 11 images:
`weight_quick_wilt = 60 / (4 × 11) = 1.36`

A higher weight means mistakes on Quick Wilt images cost more in the loss function, forcing the model to pay more attention to those rare examples.

**Getting labels from dataset:**
`np.argmax(y.numpy(), axis=1)` — converts one-hot vectors to class indices. The loop collects all training labels.

---

### Cell 47 — Train MobileNet with Class Weights

```python
history_alt = alt_model.fit(
    train_ds,
    epochs=EPOCHS_FROZEN,
    validation_data=val_ds,
    class_weight=class_weight_dict
)
```

Trains the MobileNetV3 model for `EPOCHS_FROZEN` epochs with class weights applied. `class_weight` parameter is passed directly to `.fit()`.

---

### Cells 48, 49, 50 — Reinitialise Pipelines, Plot MobileNet Results, Save

Cell 48 rebuilds the data pipelines with simplified augmentation (only flip and rotation). Cell 49 plots MobileNet accuracy curves and confusion matrix. Cell 50 saves the model as `leaf_dicease.keras`.

The simplified augmentation in cell 48:
```python
data_augmentation = keras.Sequential([
    layers.RandomFlip('horizontal'),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.15),
])
```
Three transformations instead of six — faster, potentially more stable for a lighter model.

---

### Cell 51 — Load Model and Show Random Predictions

```python
loaded_model = tf.keras.models.load_model('leaf_dicease.keras')

def plot_random_predictions(model, dataset, class_names, num_images=8):
    pred_probs = model.predict(np.expand_dims(img, axis=0), verbose=0)
    pred_label = class_names[np.argmax(pred_probs)]
```

**What it does:** Reloads the saved MobileNet model, runs it on 8 random test images, and displays results with green/red colour-coded titles.

**`np.expand_dims(img, axis=0)`** — adds a batch dimension. A single image has shape `(224, 224, 3)`. The model expects `(batch, 224, 224, 3)`. With batch=1: shape becomes `(1, 224, 224, 3)`.

**`np.argmax(pred_probs)`** — picks the index of the highest probability score across 4 classes. That index maps to a class name via `class_names[index]`.

---

### Cell 52 — Flask API Wrapper

```python
app = Flask(__name__)
CLASS_NAMES = ['Healthy', 'Leaf blight disease', 'Little_Leaf_Disease', 'Quick_Wilt_disease']

@app.route('/predict', methods=['POST'])
def predict():
    image_bytes = request.files['file'].read()
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    img_array = tf.cast(np.array(img), tf.float32) / 255.0  # normalise to [0,1]
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_array)
    predicted_class_idx = np.argmax(predictions)
    return jsonify({
        'prediction': CLASS_NAMES[predicted_class_idx],
        'confidence': float(predictions[0][predicted_class_idx]),
        'all_confidences': {name: float(pred) for name, pred in zip(CLASS_NAMES, predictions[0])}
    })
```

**What it does:** Wraps the trained model in a web API. A client (mobile app, WebSocket server, etc.) can POST a leaf image and receive a JSON prediction.

**Key difference from berry API:**
The leaf API returns `all_confidences` — the probability for all four classes, not just the top prediction:
```json
{
    "prediction": "Leaf blight disease",
    "confidence": 0.72,
    "all_confidences": {
        "Healthy": 0.05,
        "Leaf blight disease": 0.72,
        "Little_Leaf_Disease": 0.15,
        "Quick_Wilt_disease": 0.08
    }
}
```

This is more informative for users — they can see if the model is confident or uncertain.

**Note on normalisation:** This API cell divides by 255.0 (`tf.cast(img_array, tf.float32) / 255.0`) to scale pixels to [0,1]. The training pipeline used `include_preprocessing=True` in EfficientNetV2B3 which handles normalisation internally. There may be a slight mismatch — ideally both should normalise the same way. For EfficientNetV2 models, the recommended approach is to NOT manually normalise and let `include_preprocessing=True` handle it.

---

## Key Concepts Glossary

**Accuracy** — Percentage of predictions that are correct. Can be misleading when class sizes are unequal.

**Activation Function** — Mathematical function applied to a neuron's output. `relu`: max(0, x). `sigmoid`: maps to [0,1]. `softmax`: maps multiple values to probabilities summing to 1.

**AUC (Area Under the ROC Curve)** — Summarises classifier quality in one number. 1.0 = perfect; 0.5 = random.

**Backbone** — The pre-trained feature extraction network (EfficientNetV2B3 here) that the custom head is built on top of.

**Batch** — A group of images processed together in one forward/backward pass. BATCH_SIZE=16 → 16 images per step.

**Batch Normalization** — Normalises layer outputs to zero mean and unit variance. Stabilises training.

**Binary Classification** — Task with exactly 2 output classes (healthy/diseased). The berry script.

**Callback** — A function called automatically during training events (after each epoch, etc.). Used for early stopping, checkpointing, LR reduction.

**Categorical Crossentropy** — Loss function for multi-class classification. Measures distance between predicted probability distribution and true one-hot label.

**Class Weights** — Multipliers applied to loss function per class. Compensates for class imbalance by penalising errors on minority classes more.

**Confusion Matrix** — Table of correct/incorrect predictions per class. Rows = actual, Columns = predicted. Diagonal = correct.

**Data Augmentation** — Creating modified copies of training images (flip, rotate, zoom, brightness). Artificially expands the dataset.

**Dense Layer** — Fully connected neural network layer. Every output neuron connects to every input neuron.

**Dropout** — Randomly zeroes a fraction of neurons each training step. Prevents overfitting.

**Early Stopping** — Stops training if validation metric doesn't improve for `patience` epochs. Prevents overfitting and saves time.

**Epoch** — One complete pass through the entire training dataset.

**EfficientNetV2B3** — Google's efficient image classification model. Pre-trained on ImageNet. "B3" is the scale (medium-large). Achieves high accuracy with reasonable computation.

**F1-Score** — Harmonic mean of precision and recall. Balanced metric for each class.

**Fine-Tuning** — Phase 2: unfreeze top backbone layers and train with very small learning rate to adapt them for the specific task.

**Frozen Layers** — Layers whose weights cannot change during training. Used to preserve pre-trained knowledge.

**GlobalAveragePooling2D** — Reduces a 3D feature map to a 1D vector by spatial averaging. Bridges convolutional and Dense parts.

**ImageNet** — Dataset of 1.2 million labelled images across 1000 categories. EfficientNetV2B3's pre-training source.

**Learning Rate** — Step size for weight updates. Too large → unstable. Too small → slow convergence.

**Loss Function** — Measures prediction error. Training minimises this. Categorical crossentropy for multi-class; binary crossentropy for 2-class.

**Model Checkpoint** — Saves model to disk whenever a monitored metric improves. Protects against training interruption.

**Multi-class Classification** — Task with 3+ possible output classes. The leaf script (4 classes).

**One-Hot Encoding** — Represents class label as a vector of all zeros except a 1 at the class index. `[0, 1, 0, 0]` = class 1.

**Overfitting** — Model memorises training data instead of learning generalisable patterns. Validation accuracy lower than training accuracy.

**Precision** — Of all predictions for class X, what fraction are correct. Measures false alarm rate.

**Recall** — Of all actual class X examples, what fraction are correctly found. Measures missed detection rate.

**ReduceLROnPlateau** — Reduces learning rate when training stalls on a metric.

**ROC Curve** — Plots True Positive Rate vs False Positive Rate at all decision thresholds. Visualises the sensitivity/specificity trade-off.

**Seed** — Starting value for random number generators. Same seed → reproducible results.

**Softmax** — Activation for multi-class output. Converts raw scores to probabilities summing to 1.

**Stratified Split** — Each subset preserves the original class proportion distribution.

**Transfer Learning** — Using a model pre-trained on one task (ImageNet classification) and adapting it for a different task (leaf disease classification). Dramatically reduces the data and time needed.

**Underfitting** — Model too simple to capture patterns. Both training and validation accuracy are low.

**Validation Set** — Images used during training to monitor overfitting and guide callbacks. Never used to update weights directly.
