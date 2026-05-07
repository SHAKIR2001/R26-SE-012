# Berry Disease Classifier — Complete Training Script Explanation

> **Who is this for?** Someone with zero deep learning knowledge. Every technical term is explained with plain English and real-world analogies.

---

## What Does This Script Do?

This notebook trains a computer to look at a photograph of a pepper berry and decide: **is it healthy, or does it have lace bug damage?** That is a **binary classification** problem — exactly two possible answers.

Think of it like training a very experienced fruit inspector. You show them thousands of photos of berries — some healthy, some damaged — and they gradually learn the visual differences. This script automates that learning process using a technique called **deep learning**.

The specific model used is called **EfficientNetV2B3**, a powerful image-recognition network that was already pre-trained on millions of general images (cats, dogs, cars, etc.), and we adapt it to recognize pepper berry conditions. This approach is called **transfer learning**.

**Output:** A saved model file (`berry_dicease.keras`) that can later be loaded into a server and used to classify new berry photos in real time.

**Classes:** `berries without diseases` vs `lace bug damage`

---

## The 15-Section Pipeline at a Glance

```
1. Connect Google Drive
2. Unzip Dataset
3. Data Cleanup (fix folder structure)
4. Configuration (set all knobs here)
5. Data Splitting (60% train / 10% val / 30% test)
6–9. Verify split worked correctly
10. Fix subfolder issues
11. Import Libraries
12–14. Load & inspect data
15. Visualize sample images
16. List directories (debug)
17. Build data pipeline + augmentation
18. Visualize augmented images
19. Build EfficientNetV2B3 model
20. Phase 1: Train with frozen backbone
21. Phase 2: Fine-tune unfrozen layers
22. Plot training history
23. Evaluate on test set
24. Draw confusion matrix
25. Classification report
26. ROC curves
27. Show correct/incorrect predictions
28. Save & export model
29. (Alternative) MobileNetV3Small model
30. Class weights for imbalanced data
31. Train MobileNet with weights
32. Visualize MobileNet results
33. Save MobileNet model
34. Load model and show random predictions
35. Flask API wrapper for deployment
```

---

## Cell-by-Cell Explanation

---

### Cell 0 — Connect to Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

**What it does:**
This mounts (connects) your Google Drive into the Colab environment, making your files accessible at the path `/content/drive/MyDrive/`.

**Why it's needed:**
Google Colab gives you a temporary computer in the cloud. That computer has no files on it by default. Your dataset (photos of berries) lives in Google Drive. This cell bridges the gap.

**Analogy:** It's like plugging a USB drive into your laptop. After this, the Colab session can read files from your Drive just like files on its own disk.

**Line by line:**
- `from google.colab import drive` — imports the Colab tool that knows how to connect to Google Drive
- `drive.mount('/content/drive')` — makes your Drive appear at `/content/drive/`. The `/content/drive/MyDrive/` path is where your files live.

**Parameters:**
- `'/content/drive'` — the mount point, the folder where Drive files will appear. You can change this, but `/content/drive` is the standard convention.

**Alternatives:**
- Upload files directly to Colab (doesn't persist between sessions)
- Use `gdown` to download files from a shared Google Drive link
- Use cloud storage (AWS S3, Google Cloud Storage)

---

### Cell 1 — Unzip the Dataset

```python
!unzip -q '/content/drive/MyDrive/PEPPER_BERRY/OneDrive_2026-05-05.zip' -d '/content/pepper_dataset'
```

**What it does:**
Extracts a ZIP file from Google Drive into the `/content/pepper_dataset` folder.

**Why it's needed:**
A ZIP file is a compressed archive. The dataset (hundreds of berry photos) is stored as a single ZIP to keep it manageable on Drive. We need to unpack it before we can use the images.

**Line by line:**
- `!` — runs this as a shell (terminal) command, not Python
- `unzip` — the decompression program
- `-q` — "quiet" mode, suppresses verbose output. Remove it to see every file being extracted.
- `'/content/drive/MyDrive/PEPPER_BERRY/OneDrive_2026-05-05.zip'` — the source ZIP file
- `-d '/content/pepper_dataset'` — destination folder where files land

**What changes if you tweak parameters:**
- Change the ZIP path to match your file's actual location
- Change the destination to organise your workspace differently

**Alternatives:**
- Store the dataset already extracted in Drive (wastes Drive space)
- Use `zipfile` Python library for more control over extraction

---

### Cell 2 & 3 — Decorative Markdown Headers

These are visual section dividers with styled HTML. They produce nice-looking titles in the Colab notebook (purple boxes with gradient backgrounds). They contain no runnable code and have no effect on training.

---

### Cell 4 — Move the "Healthy" Folder (Data Cleanup)

```python
import os, shutil
source_path = os.path.join(BASE_DATA_DIR, 'Healthy')
destination_parent = '/content/drive/MyDrive/PEPPER/leaf_disease/...'
...
shutil.move(source_path, destination_path)
```

**What it does:**
Moves a folder called `Healthy` from the berry dataset directory to a different location (the leaf disease dataset). This is a one-time data reorganisation step.

**Why it's needed:**
During dataset preparation, the `Healthy` class images for berries may have been accidentally placed in the wrong folder. This cell corrects that by moving them to the right place.

**Analogy:** Like filing a paper in the wrong cabinet drawer and then moving it to the correct one.

**Line by line:**
- `os.path.join(BASE_DATA_DIR, 'Healthy')` — builds the full path to the Healthy folder
- `os.path.exists(source_path)` — checks if the folder actually exists before trying to move it
- `os.makedirs(destination_parent, exist_ok=True)` — creates destination folders if missing
- `shutil.move(source_path, destination_path)` — physically moves the folder

**Note:** If `BASE_DATA_DIR` is not yet defined when this cell runs, it will fail. This cell should only run once during initial data setup.

---

### Cell 5 — Configuration: The Control Panel

```python
BASE_DATA_DIR       = '/content/pepper_dataset/Component 04 - Pepper berry disease detection'
TRAIN_SPLIT_RATIO   = 0.6
VAL_SPLIT_RATIO     = 0.1
TEST_SPLIT_RATIO    = 0.3
CLASS_NAMES         = None
NUM_CLASSES         = None
DOWNSAMPLE_TO_MIN_CLASS = True
IMG_SIZE            = (224, 224)
BATCH_SIZE          = 16
EPOCHS_FROZEN       = 25
EPOCHS_FINETUNE     = 30
LEARNING_RATE       = 3e-4
FINETUNE_LR         = 1e-6
UNFREEZE_LAYERS     = 10
SEED                = 42
MODEL_SAVE_PATH     = 'berry_disease_model.h5'
```

**What it does:**
Defines all the "knobs and dials" that control training in one place. Every other cell reads from these variables.

**Why it's needed:**
Having all settings in one cell means you only need to edit one place to customise training. You never have to hunt through the notebook.

**Every parameter explained:**

| Parameter | Default | What it means | What happens if you change it |
|-----------|---------|---------------|-------------------------------|
| `BASE_DATA_DIR` | path | Where your berry photos live | Must match your actual folder path |
| `TRAIN_SPLIT_RATIO` | 0.6 | 60% of images used for training | Increase → more training data, less test data |
| `VAL_SPLIT_RATIO` | 0.1 | 10% used for validation (tuning) | Increase → better tuning signal, less training data |
| `TEST_SPLIT_RATIO` | 0.3 | 30% held out for final evaluation | Must sum to 1.0 with the others |
| `CLASS_NAMES` | None | Auto-detected from folder names | Set manually if auto-detection fails |
| `NUM_CLASSES` | None | Auto-detected (becomes 2 for berry) | Set manually only if needed |
| `DOWNSAMPLE_TO_MIN_CLASS` | True | Balance classes by trimming the larger one | False → use all images, but biased toward larger class |
| `IMG_SIZE` | (224, 224) | Resize all images to 224×224 pixels | EfficientNetV2B3 expects 224×224; changing breaks the model |
| `BATCH_SIZE` | 16 | How many images to show the model at once per step | Larger = faster but needs more GPU memory; smaller = slower but more stable |
| `EPOCHS_FROZEN` | 25 | How many full passes through training data in Phase 1 | More = potentially better but risks overfitting |
| `EPOCHS_FINETUNE` | 30 | How many passes in Phase 2 fine-tuning | Same trade-off |
| `LEARNING_RATE` | 3e-4 (0.0003) | How big a step to take when updating the model in Phase 1 | Too high → unstable training; too low → too slow |
| `FINETUNE_LR` | 1e-6 (0.000001) | Learning rate for Phase 2 | Must be very small to not destroy pre-trained weights |
| `UNFREEZE_LAYERS` | 10 | How many layers at the top of EfficientNet to re-train in Phase 2 | More = adapt more of the network; risk destroying generalisation |
| `SEED` | 42 | Random number seed for reproducibility | Change to get different random splits; 42 is convention |
| `MODEL_SAVE_PATH` | `berry_disease_model.h5` | Where to save the trained model | Change filename/path as needed |

---

### Cell 6 — Data Splitting

```python
CLASS_NAMES = sorted([d for d in os.listdir(BASE_DATA_DIR) if os.path.isdir(...)])
...
X_train, X_temp, y_train, y_temp = train_test_split(
    all_image_paths, all_image_labels,
    train_size=TRAIN_SPLIT_RATIO,
    random_state=SEED,
    stratify=all_image_labels
)
val_size_relative_to_temp = VAL_SPLIT_RATIO / (VAL_SPLIT_RATIO + TEST_SPLIT_RATIO)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, ...)
```

**What it does:**
Takes all the berry images and divides them into three separate buckets: training, validation, and test.

**Why it's needed:**
Think of it like preparing for an exam:
- **Training set:** the practice problems you study with
- **Validation set:** mock exams you take while studying to check your progress
- **Test set:** the real exam — the model has never seen these images during training

If you trained and tested on the same images, you'd get misleadingly high scores (the model memorised the answers rather than truly learning).

**Line by line:**

`CLASS_NAMES = sorted([d for d in os.listdir(BASE_DATA_DIR) if os.path.isdir(...)])`
— reads the folder names inside the dataset directory. Each folder = one class. For berry: `['berries without diseases', 'lace bug damage']`

`LABEL_MODE = 'binary' if NUM_CLASSES == 2 else 'categorical'`
— since there are 2 classes, use binary mode. If there were 3+, it would switch to categorical.

`DOWNSAMPLE_TO_MIN_CLASS = True` logic:
— counts images per class, finds the smallest, and randomly trims the larger class down to match. This prevents the model from "cheating" by always guessing the majority class.

`train_test_split(..., stratify=all_image_labels)`
— `stratify` ensures each split has roughly the same proportion of each class (e.g., if 60% are healthy overall, then 60% of training images are also healthy).

`val_size_relative_to_temp = VAL_SPLIT_RATIO / (VAL_SPLIT_RATIO + TEST_SPLIT_RATIO)`
— a two-step split: first take 60% for training; then of the remaining 40%, take 25% as validation (= 10% of total) and 75% as test (= 30% of total).

The images are then **copied** into temporary folders `/tmp/temp_dataset_split/train/`, `/val/`, `/test/` so Keras can read them.

**Alternatives:**
- Manual split (move files by hand — error-prone)
- `tf.data` splitting (split at load time rather than pre-copying)

---

### Cells 7, 8, 9 — Dataset Verification (Repeated)

These three cells are duplicates of each other. They print image counts per class per split. They were kept from iterative debugging — each time the developer ran them to verify the split worked. They are safe to run multiple times (read-only).

---

### Cell 10 — Fix Nested Subfolder Problem

```python
SUBFOLDER_PATH = os.path.join(HEALTHY_CLASS_DIR, 'black_pepper_healthy')
if os.path.isdir(SUBFOLDER_PATH):
    for item_name in os.listdir(SUBFOLDER_PATH):
        shutil.move(source_path, destination_path)
    os.rmdir(SUBFOLDER_PATH)
```

**What it does:**
Fixes a dataset organisation problem. Instead of images sitting directly in the `Healthy/` folder, some are in a nested subfolder `Healthy/black_pepper_healthy/`. Keras's image loader expects images to be in the class folder directly, not a subfolder of it.

**Analogy:** Your filing cabinet drawer (Healthy) should contain documents directly, not a cardboard box (black_pepper_healthy) stuffed inside the drawer.

**Line by line:**
- `os.path.isdir(SUBFOLDER_PATH)` — only runs the fix if the bad subfolder exists
- Loops over every file in the subfolder and moves it up one level
- `os.rmdir(SUBFOLDER_PATH)` — removes the now-empty subfolder

---

### Cell 11 — Section 2 Header (Markdown)

Decorative HTML header saying "Section 2 - Import Libraries". No code effect.

---

### Cell 12 — Import Libraries

```python
import os, warnings, numpy as np, pandas as pd
import matplotlib.pyplot as plt, matplotlib.image as mpimg
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, GlobalAveragePooling2D
from tensorflow.keras.applications import EfficientNetV2B3
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, TensorBoard
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc

warnings.filterwarnings('ignore')
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)
```

**What it does:**
Loads all the software tools (libraries) the rest of the notebook will use.

**Why it's needed:**
Python doesn't include image processing or machine learning tools by default. Libraries are pre-built toolboxes you import.

**Each library explained:**

| Library | What it provides |
|---------|-----------------|
| `numpy` | Fast math on arrays of numbers |
| `pandas` | Tables (DataFrames) for displaying results |
| `matplotlib` | Drawing charts and displaying images |
| `seaborn` | Prettier charts, especially heatmaps |
| `tensorflow` | The main deep learning engine |
| `keras` | A friendlier API on top of TensorFlow |
| `EfficientNetV2B3` | The pre-trained image recognition model |
| `Adam` | The optimiser — decides how to update model weights |
| `EarlyStopping` | Stops training automatically if no improvement |
| `ModelCheckpoint` | Saves the best model version during training |
| `ReduceLROnPlateau` | Automatically reduces the learning rate when stuck |
| `classification_report` | Prints precision, recall, F1 per class |
| `confusion_matrix` | Shows how often the model confused each class |
| `roc_curve, auc` | Generates ROC curves and AUC score |

**Reproducibility block:**
```python
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)
```
Sets all random number generators to use the same starting value. Without this, you'd get slightly different results every run. With SEED=42, results are reproducible.

---

### Cells 13 & 14 — Section Header + Dataset Inspection

Cell 13 is a decorative header. Cell 14 re-runs the class detection and prints image counts per split — same as cells 7–9. This is another debugging remnant.

---

### Cells 15 & 16 — Inspect the "Healthy" Folder

Cell 15 is a markdown explanation. Cell 16 lists image files inside the `Healthy` class folder to verify they're present and readable. Purely diagnostic — safe to skip.

---

### Cell 17 (Section 4 Header) & Cell 18 — Visualise Sample Images

```python
num_cols = min(NUM_CLASSES, 6)
num_rows = 3
fig, axes = plt.subplots(num_rows, num_cols, ...)
for col_idx, cls in enumerate(CLASS_NAMES):
    images = [f for f in os.listdir(cls_path) if f.endswith(...)][:num_rows]
    for row_idx, img_file in enumerate(images):
        img = mpimg.imread(...)
        ax.imshow(img)
```

**What it does:**
Creates a grid of sample images from the training set — 3 rows × (number of classes) columns — to visually confirm the dataset loaded correctly.

**Why it's needed:**
Always sanity-check your data before training. A wrong folder path would load blank or wrong images. Better to catch this now than after 30 minutes of training.

**Line by line:**
- `plt.subplots(num_rows, num_cols)` — creates a grid of sub-plots
- `mpimg.imread(path)` — reads an image file as a NumPy array
- `ax.imshow(img)` — renders the image in a plot cell
- `ax.axis('off')` — hides x/y axis numbers (not useful for photos)
- `plt.savefig('sample_images.png')` — saves the grid as a PNG file

---

### Cell 19 (Markdown) & Cell 20 — List Directory Contents

Debugging cell that prints what's inside TRAIN_DIR, VAL_DIR, TEST_DIR. Kept from troubleshooting. Safe to skip.

---

### Cell 21 (Section Header) & Cell 22 — Build Data Pipeline + Augmentation

```python
AUTOTUNE = tf.data.AUTOTUNE

def load_split(directory, shuffle=True, label_mode=LABEL_MODE):
    return tf.keras.utils.image_dataset_from_directory(
        directory=directory,
        labels='inferred',
        label_mode=label_mode,
        class_names=CLASS_NAMES,
        color_mode='rgb',
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
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
], name='augmentation')

train_ds = (
    train_ds_raw
    .map(augment_and_normalize, num_parallel_calls=AUTOTUNE)
    .cache()
    .shuffle(buffer_size=1000, seed=SEED)
    .prefetch(AUTOTUNE)
)
```

**What it does:**
Builds three efficient data pipelines (train, validation, test) that feed images to the model during training. Also defines random image augmentation applied only to training images.

**Why it's needed:**
Loading raw images from disk every epoch would be slow. TensorFlow's data pipeline loads, transforms, and queues images in parallel with training. Augmentation artificially multiplies your dataset by showing the model slightly modified versions of each image.

**`image_dataset_from_directory` parameters:**

| Parameter | Value | What it does |
|-----------|-------|-------------|
| `labels='inferred'` | — | Reads class labels from folder names automatically |
| `label_mode='binary'` | for 2 classes | Returns 0 or 1 as labels. `'categorical'` returns one-hot vectors for 3+ classes |
| `class_names=CLASS_NAMES` | — | Fixes the order of classes (important for consistent indexing) |
| `color_mode='rgb'` | — | Load as 3-channel colour image. `'grayscale'` for black-and-white |
| `batch_size=16` | 16 | Group images into batches of 16 |
| `image_size=(224,224)` | — | Resize every image to this size |
| `shuffle=True` for train | — | Mix images in random order each epoch |
| `seed=SEED` | 42 | Reproducible shuffling |

**Data augmentation explained:**

Think of augmentation as a photo editing pipeline. For each training image, the model gets to see a slightly modified version. This teaches it that a berry looks the same whether flipped, rotated, or slightly darker.

| Augmentation | What it does | Real-world interpretation |
|---|---|---|
| `RandomFlip('horizontal')` | Mirrors the image left-right | A disease looks the same from either side |
| `RandomRotation(0.15)` | Rotates ±15% of 360° = ±54° | Berry can be at different angles when photographed |
| `RandomZoom(0.15)` | Zooms in/out by up to 15% | Camera distance varies |
| `RandomContrast(0.15)` | Changes colour contrast ±15% | Lighting conditions differ |
| `RandomBrightness(0.1)` | Changes brightness ±10% | Time of day, shadow |
| `RandomTranslation(0.1, 0.1)` | Shifts image by up to 10% | Subject isn't always centred |

**Only training data gets augmented** — validation and test stay untouched so you get consistent evaluation.

**Pipeline optimisation:**

| Pipeline step | What it does |
|---|---|
| `.map(..., num_parallel_calls=AUTOTUNE)` | Applies augmentation on multiple CPU cores in parallel |
| `.cache()` | Stores the processed images in RAM after the first epoch — avoids re-reading disk |
| `.shuffle(buffer_size=1000)` | Randomly mixes 1000 images in a buffer each epoch |
| `.prefetch(AUTOTUNE)` | Pre-loads the next batch while the model trains on the current one |

**Alternatives:**
- `ImageDataGenerator` (older Keras API — slower but simpler)
- `albumentations` library (more augmentation options)
- No augmentation (simpler but risks overfitting on small datasets)

---

### Cell 23 (Section Header) & Cell 24 — Visualise Augmentation

```python
for images, labels in train_ds_raw.take(1):
    sample_img = images[0:1]
aug_imgs = [data_augmentation(sample_img, training=True)[0].numpy().astype('uint8') for _ in range(8)]
```

**What it does:**
Takes one image from the training set and generates 8 augmented versions of it, then displays them side-by-side so you can visually confirm augmentation is working correctly.

**Why it's needed:**
A sanity check. If augmentation is misconfigured (e.g., rotation so extreme the berry is no longer recognisable), you'd catch it here before wasting training time.

---

### Cell 25 (Section Header) & Cell 26 — Build the Model

```python
def build_model(num_classes, img_size, learning_rate, base_trainable=False):
    base_model = EfficientNetV2B3(
        include_top=False,
        weights='imagenet',
        input_shape=(*img_size, 3),
        include_preprocessing=True
    )
    base_model.trainable = base_trainable

    inputs = keras.Input(shape=(*img_size, 3))
    x = base_model(inputs, training=base_trainable)
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.4)(x)
    outputs = Dense(1, activation='sigmoid')(x)  # binary: 1 unit, sigmoid

    model = Model(inputs, outputs)
    model.compile(optimizer=Adam(lr), loss='binary_crossentropy', metrics=['accuracy'])
    return model, base_model
```

**What it does:**
Assembles the neural network. It stacks a pre-trained image feature extractor (EfficientNetV2B3) with a custom decision-making "head" on top.

**Analogy:** EfficientNetV2B3 is like hiring an expert who has already studied millions of photos. They can describe what they see ("there are brown spots, a fuzzy texture, curved edges"). Your custom head is the part that takes those descriptions and makes the final decision: "diseased or healthy?"

**EfficientNetV2B3 parameters:**

| Parameter | Value | Meaning |
|---|---|---|
| `include_top=False` | — | Removes the original ImageNet classification layer (1000 classes). We only want the feature extraction layers. |
| `weights='imagenet'` | — | Load weights learned from 1.2 million ImageNet images. This is the "knowledge" we're borrowing. |
| `input_shape=(*img_size, 3)` | (224, 224, 3) | Images are 224×224 pixels, 3 colour channels (RGB) |
| `include_preprocessing=True` | — | EfficientNetV2 has its own pixel normalisation built in. This activates it. |

`base_model.trainable = False` — freezes all EfficientNet layers. They cannot change during Phase 1. We only train the custom head.

**The custom head layer by layer:**

`GlobalAveragePooling2D()` — EfficientNetV2B3 outputs a 3D grid of numbers (width × height × features). GAP collapses this into a single flat vector by averaging across the spatial dimensions.
*Analogy: Instead of examining every pixel, GAP says "on average, what does this image look like?"*

`BatchNormalization()` — Normalises the numbers so they don't become too large or too small. Keeps training stable.
*Analogy: Like adjusting the volume — keeping everything in a reasonable range.*

`Dense(512, activation='relu')` — A layer of 512 artificial neurons. Each neuron looks at all 1,536 features from GAP and decides if it should fire. `relu` is the activation function: it sets any negative value to zero.
*Analogy: 512 specialists each vote: "yes I see something relevant" or "no, nothing here for me."*

`Dropout(0.5)` — Randomly disables 50% of neurons during each training step. Forces the network to not rely too heavily on any one neuron.
*Analogy: Like studying with someone who randomly covers answers — you learn the material properly instead of memorising tricks.*

`BatchNormalization()` — Another stabilising layer between the two Dense blocks.

`Dense(256, activation='relu')` — Another layer with 256 neurons, narrowing further toward a decision.

`Dropout(0.4)` — Randomly disables 40% of neurons.

`Dense(1, activation='sigmoid')` — The final decision layer. For binary classification: 1 output neuron. `sigmoid` squashes output to between 0 and 1.
- Output close to 0 → "berries without diseases"
- Output close to 1 → "lace bug damage"

`model.compile(optimizer=Adam(...), loss='binary_crossentropy', metrics=['accuracy'])`
- `Adam` — the optimiser. Decides how to adjust weights after seeing each batch. Adam is adaptive — it automatically tunes its own internal learning rate.
- `binary_crossentropy` — the loss function. Measures how wrong the prediction was. For binary problems (0/1), this is the standard choice.
- `metrics=['accuracy']` — also track what percentage of predictions are correct.

**Alternatives:**

| Component | Alternative | Trade-off |
|---|---|---|
| `EfficientNetV2B3` | `ResNet50`, `MobileNetV3`, `VGG16` | MobileNetV3 is faster but less accurate; ResNet50 is classic but older |
| `Adam` | `SGD`, `RMSprop`, `AdamW` | SGD is simpler but needs more hand-tuning; AdamW adds weight decay (regularisation) |
| `binary_crossentropy` | `hinge` loss | Different mathematical formulation, rarely better for binary image tasks |
| `Dropout(0.5)` | `SpatialDropout2D`, `L2 regularisation` | L2 adds a penalty on large weights instead of randomly dropping them |

---

### Cell 27 (Section Header) & Cell 28 — Phase 1: Feature Extraction Training

```python
callbacks_phase1 = [
    EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7),
    ModelCheckpoint('checkpoint_phase1.h5', monitor='val_accuracy', save_best_only=True)
]

history1 = model.fit(
    train_ds,
    epochs=EPOCHS_FROZEN,
    validation_data=val_ds,
    callbacks=callbacks_phase1,
    verbose=1
)
```

**What it does:**
Trains only the custom head (the Dense/Dropout layers) while EfficientNetV2B3 stays completely frozen. The model learns to make decisions using the features EfficientNet already knows how to detect.

**Analogy:** A student (custom head) sits in lectures taught by an expert professor (EfficientNetV2B3). The professor doesn't change their knowledge — they just explain what they see. The student learns to interpret the professor's descriptions.

**`model.fit` parameters:**

| Parameter | Value | Meaning |
|---|---|---|
| `train_ds` | — | The training data pipeline |
| `epochs=25` | — | Maximum number of full passes through all training images |
| `validation_data=val_ds` | — | After each epoch, evaluate on validation data |
| `callbacks=...` | — | List of actions to take at the end of each epoch |
| `verbose=1` | — | Print a progress bar for each epoch |

**Callbacks explained:**

`EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True)`
- Watches validation accuracy after each epoch
- If it doesn't improve for 5 consecutive epochs, training stops automatically
- `restore_best_weights=True` — rolls back to the weights from the best epoch, not the last one
- *Analogy: If your student's mock exam score stops improving for 5 weeks in a row, stop studying and use the best version of their notes.*

`ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-7)`
- If validation loss doesn't improve for 3 epochs, reduce the learning rate by half (`factor=0.5`)
- `min_lr=1e-7` — never go below this floor
- *Analogy: If you're stuck on a problem and smaller steps aren't helping, try even tinier steps until something works.*

`ModelCheckpoint('checkpoint_phase1.h5', monitor='val_accuracy', save_best_only=True)`
- Saves the model to disk whenever validation accuracy improves
- `save_best_only=True` — overwrites the file only if the new version is better than the saved one

**Why two phases?**
Training in phases prevents catastrophic forgetting. If you immediately fine-tuned EfficientNet, the randomly-initialised head weights would generate huge errors that would destroy EfficientNet's carefully learned knowledge.

---

### Cell 29 (Section Header) & Cell 30 — Phase 2: Fine-Tuning

```python
base_model.trainable = True
for layer in base_model.layers[:-UNFREEZE_LAYERS]:
    layer.trainable = False

model.compile(optimizer=Adam(learning_rate=FINETUNE_LR), ...)
history2 = model.fit(train_ds, epochs=EPOCHS_FINETUNE, ...)
```

**What it does:**
Unlocks the top 10 layers of EfficientNetV2B3 and allows them to adjust slightly for berry disease detection specifically. The rest of EfficientNet stays frozen.

**Why it's needed:**
EfficientNetV2B3 learned features from photos of everyday objects. Some of those high-level features (textures, colour patterns) might not perfectly match what matters for berry disease. Fine-tuning lets those final layers adapt.

**Analogy:** The expert professor now also takes feedback from the student. They adjust the last few things they teach based on what the student finds most confusing or irrelevant for the specific exam topic.

**Line by line:**
`base_model.trainable = True` — unlocks all layers (must do this before selectively re-freezing)
`for layer in base_model.layers[:-UNFREEZE_LAYERS]: layer.trainable = False`
— re-freezes everything **except** the last 10 layers. `base_model.layers[:-10]` means "all layers except the last 10."

`Adam(learning_rate=FINETUNE_LR)` — uses a much smaller learning rate (1e-6 vs 3e-4). Why?
- EfficientNet's weights are already good. Tiny changes = small improvements.
- Large changes = you'd destroy everything it already learned.

**Callbacks for Phase 2:**
- `patience=7` for EarlyStopping (more patient than Phase 1 — fine-tuning converges slowly)
- `factor=0.3` for ReduceLROnPlateau (reduce LR more aggressively: 30% of current)
- `min_lr=1e-8` (lower floor — fine-tuning can go very small)
- Saves the final model to `MODEL_SAVE_PATH` (best_model.h5)

---

### Cell 31 (Section Header) & Cell 32 — Training History Plots

```python
history_all = merge_histories(history1, history2)
...
ax.plot(history_all['accuracy'], ...)
ax.plot(history_all['val_accuracy'], ...)
ax.axvline(x=phase1_end - 1, color='red', ...)
```

**What it does:**
Plots accuracy and loss curves for both training phases side-by-side on a single chart. A red vertical line marks where Phase 1 ended and Phase 2 began.

**Why it's needed:**
These charts tell you if training went well:
- **Good:** Training and validation accuracy both rise and converge
- **Overfitting:** Training accuracy keeps rising but validation accuracy plateaus or falls
- **Underfitting:** Both accuracies are low and not improving

**Reading the chart:**
- **X-axis:** Epoch number (each tick = one full pass through training data)
- **Y-axis:** Accuracy (left chart) or loss (right chart)
- **Blue line:** Training performance
- **Orange line:** Validation performance (this is the honest score)
- **Red dashed line:** Boundary between Phase 1 and Phase 2

---

### Cell 33 (Section Header) & Cell 34 — Evaluate on Test Set

```python
best_model = keras.models.load_model(MODEL_SAVE_PATH)
test_loss, test_acc = best_model.evaluate(test_ds, verbose=1)
y_pred_proba = best_model.predict(test_ds, verbose=1)
y_pred = (y_pred_proba > 0.5).astype(int).flatten()  # binary threshold
y_true = np.concatenate([y.numpy().astype(int).flatten() for _, y in test_ds])
```

**What it does:**
Loads the best saved model and evaluates it on the test set — images the model has never seen at all.

**Why it's needed:**
The test set is the true measure of the model's real-world performance. Training accuracy is biased because the model trained on those images. Validation accuracy is less biased but still influenced training (early stopping used it). Test accuracy is completely unbiased.

**Line by line:**
`keras.models.load_model(MODEL_SAVE_PATH)` — loads the saved `.h5` model file

`best_model.evaluate(test_ds)` — runs images through the model and computes overall accuracy and loss

`best_model.predict(test_ds)` — generates raw probability scores (0 to 1) for each test image

`(y_pred_proba > 0.5).astype(int)` — converts probabilities to class labels:
- Probability > 0.5 → predicted class 1 ("lace bug damage")
- Probability ≤ 0.5 → predicted class 0 ("berries without diseases")
- 0.5 is the decision threshold. You could change it (e.g., to 0.7 if you want to be more conservative about flagging disease).

`y_true` collects the actual correct labels from the test dataset for comparison.

---

### Cell 35 (Section Header) & Cell 36 — Confusion Matrix

```python
cm = confusion_matrix(y_true, y_pred)
cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ...)
```

**What it does:**
Creates a 2×2 grid showing how the model performed on each class.

**Reading a confusion matrix (for binary classification):**

```
                  Predicted: Healthy    Predicted: Diseased
Actual: Healthy       True Negative        False Positive
Actual: Diseased     False Negative        True Positive
```

- **True Positive:** Model correctly said "diseased" for a diseased berry
- **True Negative:** Model correctly said "healthy" for a healthy berry
- **False Positive:** Model wrongly said "diseased" for a healthy berry (false alarm)
- **False Negative:** Model wrongly said "healthy" for a diseased berry (missed detection — most dangerous!)

`cm_norm` divides each row by its total — converts to percentages (0.0 to 1.0). The normalised version shows the proportion correctly classified per class.

**Alternatives:**
- `ConfusionMatrixDisplay` from sklearn (simpler but less customisable)
- Look at F1 score instead if classes are very imbalanced

---

### Cell 37 (Section Header) & Cell 38 — Classification Report

```python
report = classification_report(y_true, y_pred, target_names=CLASS_NAMES)
```

**What it does:**
Prints a table with three metrics for each class.

**The three metrics explained:**

| Metric | Formula | Meaning |
|---|---|---|
| **Precision** | True Positives / (True Positives + False Positives) | "Of everything I called diseased, how many actually were?" |
| **Recall** | True Positives / (True Positives + False Negatives) | "Of everything that was actually diseased, how many did I find?" |
| **F1-Score** | 2 × Precision × Recall / (Precision + Recall) | Balanced average of Precision and Recall |

For disease detection, **Recall** is usually more important — missing a disease (false negative) is more costly than a false alarm (false positive).

---

### Cell 39 (Section Header) & Cell 40 — ROC Curves

```python
fpr, tpr, _ = roc_curve(y_true, y_pred_proba.flatten())
roc_auc = auc(fpr, tpr)
ax.plot(fpr, tpr, label=f'AUC = {roc_auc:.3f}')
ax.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
```

**What it does:**
Draws the Receiver Operating Characteristic (ROC) curve and calculates the Area Under the Curve (AUC).

**What the ROC curve shows:**
The ROC curve plots True Positive Rate vs False Positive Rate at every possible decision threshold (not just 0.5). It answers: "If I make the model more sensitive, how many false alarms will I get?"

- **AUC = 1.0** → perfect classifier
- **AUC = 0.5** → random guessing (the diagonal dashed line)
- **AUC > 0.9** → excellent
- **AUC 0.7–0.9** → good
- **AUC < 0.7** → poor

The dashed black line represents a classifier that just guesses randomly — your model should be far above it.

---

### Cell 41 (Section Header) & Cell 42 — Show Correct & Incorrect Predictions

```python
correct_idx   = np.where(y_pred == y_true)[0]
incorrect_idx = np.where(y_pred != y_true)[0]
plot_samples(correct_idx, 'Correct Predictions')
plot_samples(incorrect_idx, 'Incorrect Predictions')
```

**What it does:**
Displays a grid of images that the model got right (green titles) and images it got wrong (red titles), showing the true label and the predicted label.

**Why it's needed:**
Looking at failure cases teaches you a lot. If all the wrong predictions share a common trait (e.g., blurry photos, unusual angles, very small berries), you know what to improve.

---

### Cell 43 (Section Header) & Cell 44 — Save & Export Model

```python
best_model.save(MODEL_SAVE_PATH)             # saves as .h5
best_model.export('best_model_savedmodel')   # saves as SavedModel format
json.dump({i: name for i, name in enumerate(CLASS_NAMES)}, f)  # saves class map
```

**What it does:**
Saves the final trained model in two formats and writes a JSON file mapping index numbers to class names.

**Two formats:**
- **`.h5`** (HDF5) — single file, compatible with Keras load. Convenient.
- **SavedModel** — folder format, compatible with TensorFlow Serving and deployment. Better for production.

**`class_names.json`** — essential for the API wrapper. Without it, the model outputs `0` or `1` but you wouldn't know which is "healthy" and which is "diseased." The JSON maps: `{0: "berries without diseases", 1: "lace bug damage"}`.

---

### Cells 45 & 46 — Alternative: MobileNetV3Small

```python
from tensorflow.keras.applications import MobileNetV3Small
base_model_alt = MobileNetV3Small(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
```

**What it does:**
Builds an alternative model using MobileNetV3Small instead of EfficientNetV2B3.

**When to use MobileNetV3:**
- Deploying on a mobile phone or embedded device
- When prediction speed matters more than peak accuracy
- When you have very limited computational resources

**Trade-off vs EfficientNetV2B3:**
MobileNetV3Small is ~3x smaller and ~2x faster but generally achieves lower accuracy.

---

### Cells 47 & 48 — Class Weights for Imbalanced Data

```python
weights = class_weight.compute_class_weight(
    class_weight='balanced',
    classes=unique_classes,
    y=y_train
)
class_weight_dict = {i: weights[i] for i in range(len(unique_classes))}
```

**What it does:**
Calculates penalty weights that make the model pay more attention to the smaller class.

**Why it's needed:**
If "lace bug damage" has only 11 images and "healthy" has 16, the model might learn to always predict "healthy" and get 59% accuracy without actually learning anything. Class weights punish errors on the minority class more heavily.

**`compute_class_weight('balanced', ...)` formula:**
`weight_for_class = total_samples / (num_classes × count_of_class)`
Smaller class → larger weight → model penalised more for missing it.

---

### Cell 49 — Train MobileNet with Class Weights

```python
history_alt = alt_model.fit(
    train_ds,
    epochs=EPOCHS_FROZEN,
    validation_data=val_ds,
    class_weight=class_weight_dict
)
```

Same as the Phase 1 training but using the MobileNetV3 model and class weights. `class_weight=class_weight_dict` passes the weights into the training loop.

---

### Cells 50, 51, 52 — Reinitialise Pipelines, Plot MobileNet Results, Save MobileNet

Cell 50 rebuilds the data pipelines (same as Cell 22 — reinitialised because some pipeline state may have been consumed). Cell 51 plots MobileNet's accuracy and confusion matrix. Cell 52 saves the MobileNet model as `berry_diceas.keras`.

---

### Cells 53 & 54 — Load Saved Model and Show Random Predictions

```python
loaded_model = tf.keras.models.load_model('leaf_dicease.keras')
def plot_random_predictions(model, dataset, class_names, num_images=8):
    ...
    pred_probs = model.predict(np.expand_dims(img, axis=0), verbose=0)
    pred_label = class_names[np.argmax(pred_probs)]
```

**What it does:**
Reloads the saved model from disk and runs it on 8 random test images, displaying the actual and predicted labels (green = correct, red = wrong).

**Note:** Cell 53 loads `leaf_dicease.keras` — this appears to be a copy-paste mistake in the notebook (should be `berry_diceas.keras`). It tests the loaded model works correctly.

**`np.expand_dims(img, axis=0)`** — a single image has shape (224, 224, 3). The model expects a batch: (1, 224, 224, 3). `expand_dims` adds the batch dimension.

---

### Cell 54 — Flask API Wrapper

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    file = request.files['file']
    image_bytes = file.read()
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize(IMG_SIZE)
    img_array = tf.cast(np.array(img), tf.float32)
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_array)
    ...
    return jsonify({'prediction': predicted_class_name, 'confidence': conf})
```

**What it does:**
Wraps the trained model in a web API. Other programs (like a mobile app or the WebSocket server) can send an image file via HTTP POST and receive a JSON response with the predicted class and confidence score.

**How it works:**
1. Client sends a POST request to `/predict` with an image file
2. Flask receives the file
3. Image is opened, resized to 224×224, converted to a float array
4. Model predicts probabilities
5. For binary: probability > 0.5 → class 1, otherwise class 0
6. JSON response sent back: `{"prediction": "lace bug damage", "confidence": 0.92}`

**The API response includes:**
- `prediction` — class name ("berries without diseases" or "lace bug damage")
- `confidence` — how sure the model is (0.0 to 1.0)
- `raw_output` — the raw sigmoid probability before thresholding

---

## Key Concepts Glossary

**Accuracy** — The percentage of predictions that are correct. `(correct predictions) / (total predictions)`. Misleading when classes are imbalanced.

**Activation Function** — A mathematical function applied to each neuron's output to introduce non-linearity. Common ones: `relu` (sets negatives to zero), `sigmoid` (squashes to 0–1), `softmax` (squashes multi-class outputs to sum to 1).

**AUC (Area Under the Curve)** — A number from 0 to 1 summarising the ROC curve. Higher is better. AUC = 0.5 means random guessing.

**Backbone / Base Model** — The pre-trained image feature extractor (EfficientNetV2B3 here) that provides the foundation knowledge. "Backbone" because everything else is built on top of it.

**Batch** — A small group of images processed together in one training step. With `BATCH_SIZE=16`, 16 images are shown at once before the model updates its weights.

**Batch Normalization** — A technique that normalises the outputs of a layer so they have a mean of ~0 and standard deviation of ~1. Keeps training numerically stable and often speeds up convergence.

**Binary Classification** — A task with exactly two possible outputs (yes/no, healthy/diseased).

**Callback** — A function that runs automatically at certain points during training (end of each epoch, end of training). Used for early stopping, saving checkpoints, etc.

**Class Weights** — Multipliers that make the loss function penalise mistakes on minority classes more heavily. Helps with imbalanced datasets.

**Confusion Matrix** — A table showing correct and incorrect predictions per class. Rows = actual class, Columns = predicted class. Diagonal = correct.

**Data Augmentation** — Creating modified versions of training images (flipped, rotated, brightened) to artificially expand the dataset and improve generalisation.

**Dense Layer (Fully Connected)** — A layer where every neuron connects to every neuron in the previous layer. Used for final decision-making.

**Dropout** — A regularisation technique that randomly sets some neurons to zero during training. Prevents overfitting.

**Early Stopping** — Stops training automatically if the metric being monitored (e.g., validation accuracy) doesn't improve for `patience` epochs.

**Epoch** — One complete pass through the entire training dataset. If you have 1000 images and batch size 16, one epoch = ~63 training steps.

**EfficientNetV2B3** — A state-of-the-art image classification model designed to be efficient (good accuracy per computation). "B3" refers to the scale (B0 is smallest, B7 is largest). Pre-trained on ImageNet.

**F1-Score** — The harmonic mean of Precision and Recall. A balanced metric that accounts for both false positives and false negatives.

**Fine-Tuning** — Phase 2 of transfer learning: unfreezing some pre-trained layers and re-training them at a very small learning rate to adapt them for the specific task.

**Frozen / Unfrozen** — A frozen layer's weights cannot change during training. Unfreezing allows weights to be updated.

**GlobalAveragePooling2D (GAP)** — Reduces a 3D feature map (H×W×C) to a 1D vector (C) by computing the average of each channel spatially. Used to transition from convolutional to Dense layers.

**Learning Rate** — How big a step the model takes when updating its weights. Too large → training is unstable (oscillates). Too small → training is slow or gets stuck.

**Loss Function** — A mathematical measure of how wrong the model's predictions are. The training process minimises this. Binary crossentropy for 2-class problems; categorical crossentropy for 3+ classes.

**Overfitting** — When a model memorises the training data instead of learning general patterns. Signs: training accuracy is high but validation accuracy is much lower.

**Precision** — "Of all images predicted as class X, what fraction actually are class X?" High precision = few false alarms.

**Recall** — "Of all actual class X images, what fraction did I correctly identify?" High recall = few missed detections. Critical for disease detection.

**Reduce LR on Plateau** — Automatically reduces the learning rate when training progress stalls. Helps the model escape local minima.

**ROC Curve** — A graph of True Positive Rate vs False Positive Rate at all decision thresholds. Shows the trade-off between sensitivity and specificity.

**Seed (SEED)** — A starting number for random number generation. Using the same seed ensures reproducible results across runs.

**Sigmoid** — An activation function that maps any number to a value between 0 and 1. Used for binary classification output.

**Softmax** — An activation function that converts multiple numbers into probabilities that sum to 1. Used for multi-class classification output.

**Stratified Split** — Splitting data such that each subset has the same proportion of each class as the original dataset.

**Transfer Learning** — Using a model pre-trained on one large dataset (ImageNet) and adapting it for a different but related task (berry disease classification). Saves time and data.

**Underfitting** — When a model is too simple to capture the patterns in data. Signs: both training and validation accuracy are low.

**Validation Set** — A subset of data used to tune training (e.g., for early stopping). Separate from the test set.
