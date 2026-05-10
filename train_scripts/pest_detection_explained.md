Pest Detection Model: Complete Code Explanation
What This Script Does
This notebook trains a deep learning model to automatically identify four types of pests and healthy
conditions on mango plants. The model learns from labeled training images and can predict whether a
new mango plant leaf image shows:
Diconocoris distanti (a specific pest species)
Gynaikothrips karny (another pest species)
Healthy (no pests present)
Pterolopha annulata (a third pest species)
Think of this like training a specialized eye doctor: you show them many examples of different eye
conditions with labels, they learn the patterns that distinguish each condition, and then they can
diagnose new patients they've never seen before.
Complete Pipeline Overview
The training process follows this sequence:
1. Setup & Configuration → Set parameters and data paths
2. Data Splitting → Divide your images into training (60%), validation (10%), and test (30%) sets
while maintaining class balance
3. Import Libraries → Load TensorFlow, Keras, and analysis tools
4. Load & Inspect Data → Verify images are correctly organized
5. Visualize Samples → Show example images from each pest category
6. Data Augmentation → Artificially create variations of training images
7. Build Model → Create a neural network architecture using EfficientNetV2B3
8. Phase 1 Training → Train with frozen backbone (25 epochs, learning rate 3e-4)
9. Phase 2 Fine-Tuning → Unlock and train top layers (30 epochs, learning rate 1e-6)
10. Evaluate Results → Test the model on unseen images
11. Visualize Performance → Generate confusion matrices, ROC curves, sample predictions
12. Export Model → Save trained model for deployment
Cell-by-Cell Code Explanation
CELL 0: Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')
What it does: Connects Google Colab (a free cloud environment) to your Google Drive, allowing the
notebook to access image datasets stored in the cloud.
Why it's needed: You likely stored your pest images in Google Drive. This cell grants the notebook
permission to read those files.
How it works:
from google.colab import drive imports Google Colab's drive module
drive.mount('/content/drive') creates a link from Colab to your Drive; you'll see a prompt to
click "Allow"
After this, you can reference your files using paths like
/content/drive/MyDrive/PEPPER/pest_detection/...
Line-by-line:
1. Import the Colab drive library
2. Mount (connect) your Google Drive at 
Parameters: None (the mount point 
Alternatives:
/content/drive
/content/drive is standard)
If using local machine: Skip this cell entirely
If using AWS/Azure: Use their respective storage mount commands
If running locally: Just use absolute file paths to your dataset
CELLS 1, 5, 7, 9: Data Splitting (Repeated Cells)
These cells are identical and perform the same data splitting operation. The notebook includes
duplicates as debugging remnants. You would typically run only one of these.
[See the leaf_disease_explained.md equivalent section for detailed line-by-line explanation of data
splitting logic. The pest notebook uses identical data splitting code to divide images into train/val/test
sets with stratified sampling.]
What it does: Takes all your pest images from one folder and splits them into three separate folders:
training (60%), validation (10%), and test (30%).
Why it's needed:
Training set teaches the model
Validation set helps us adjust the training process
Test set measures final performance on completely unseen data
Using all data for training would be cheating—the model would memorize specific images instead of
learning general patterns.
Configuration (CELL 4):
import os
BASE_DATA_DIR = '/content/drive/MyDrive/PEPPER/pest_detection/pest detection'
TRAIN_DIR = ''
VAL_DIR   = ''
TEST_DIR  = ''
TRAIN_SPLIT_RATIO = 0.6
VAL_SPLIT_RATIO   = 0.1
TEST_SPLIT_RATIO  = 0.3
CLASS_NAMES = None  # Will be auto-detected
NUM_CLASSES = None  # Will be auto-detected
DOWNSAMPLE_TO_MIN_CLASS = True
IMG_SIZE    = (224, 224)
BATCH_SIZE  = 16
EPOCHS_FROZEN    = 25
EPOCHS_FINETUNE  = 30
LEARNING_RATE    = 3e-4
FINETUNE_LR      = 1e-6
UNFREEZE_LAYERS  = 10
SEED             = 42
MODEL_SAVE_PATH  = 'best_model.h5'
print('Configuration updated for dynamic data splitting!')
What it does: Centralizes all configurable parameters in one place, making the notebook easy to
customize without editing code later.
Why it's needed: Training parameters significantly affect model performance. Changing one value
here affects all dependent calculations throughout the notebook.
Key parameters explained:
BASE_DATA_DIR : Path where your original pest images are stored
IMG_SIZE = (224, 224) : Resize all images to 224×224 pixels (EfficientNetV2B3 standard)
BATCH_SIZE = 16 : Process 16 images at a time
LEARNING_RATE = 3e-4 : Initial learning rate (0.0003)
FINETUNE_LR = 1e-6 : Much smaller learning rate for fine-tuning
SEED = 42 : Random seed for reproducibility
CELL 6, 8, 10: Dataset Configuration Check (Repeated)
[Similar verification cells that check CLASS_NAMES, NUM_CLASSES, and image counts per split.
Refer to CELL 25 below for detailed explanation—these cells are identical.]
CELL 11: Clean Up Malformed Folder Structure
import os
import shutil
HEALTHY_CLASS_DIR = os.path.join(BASE_DATA_DIR, 'Healthy')
SUBFOLDER_PATH = os.path.join(HEALTHY_CLASS_DIR, 'black_pepper_healthy')
if os.path.isdir(SUBFOLDER_PATH):
    print(f"Detected problematic subfolder: {SUBFOLDER_PATH}")
    
    for item_name in os.listdir(SUBFOLDER_PATH):
        source_path = os.path.join(SUBFOLDER_PATH, item_name)
        destination_path = os.path.join(HEALTHY_CLASS_DIR, item_name)
        if os.path.isfile(source_path):
            shutil.move(source_path, destination_path)
            print(f"Moved: {item_name}")
    try:
        os.rmdir(SUBFOLDER_PATH)
        print(f"Removed empty subfolder: {SUBFOLDER_PATH}")
    except OSError as e:
        print(f"Error removing subfolder: {e}")
else:
    print(f"No problematic subfolder found.")
What it does: Fixes a specific data organization issue—some 'Healthy' images were nested in a
subfolder ('black_pepper_healthy'), but the data loader expects images to be directly in the class folder.
This cell moves nested images to the correct location.
Why it's needed: Deep learning requires consistent data organization. Unexpected folder nesting
breaks automatic data loading.
CELL 23: Import Libraries
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Dense, Dropout, BatchNormalization,
    GlobalAveragePooling2D
)
from tensorflow.keras.applications import EfficientNetV2B3
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping, ModelCheckpoint,
    ReduceLROnPlateau, TensorBoard
)
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_curve, auc
)
from itertools import cycle
warnings.filterwarnings('ignore')
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)
gpus = tf.config.list_physical_devices('GPU')
print(f'Libraries imported | TF version: {tf.__version__}')
print(f'   GPU(s) available: {[g.name for g in gpus] if gpus else "None - running on 
CPU"}')
What it does: Loads all required libraries and checks for GPU availability.
Why it's needed:
NumPy/Pandas for numerical operations
Matplotlib/Seaborn for visualization
TensorFlow/Keras for deep learning
Scikit-learn for metrics
Key libraries:
Library Purpose
NumPy Numerical arrays and operations
Pandas Data tables and analysis
Matplotlib Create plots and visualizations
TensorFlow/Keras Deep learning framework
Scikit-learn Machine learning utilities (metrics)
Seaborn Statistical visualization
CELL 25: Verify Dataset Configuration
[Checks that data split created correct structure and counts images in each split.]
CELL 29: Visualize Sample Images
num_cols = min(NUM_CLASSES, 6)
num_rows = 3
fig, axes = plt.subplots(num_rows, num_cols, figsize=(4 * num_cols, 4 * num_rows))
fig.suptitle('Sample Images from Training Set', fontsize=18, fontweight='bold', 
color='#6C63FF')
for col_idx, cls in enumerate(CLASS_NAMES[:num_cols]):
    cls_path = os.path.join(TRAIN_DIR, cls)
    if not os.path.isdir(cls_path):
        continue
    images = [f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', 
'.jpeg', '.png', '.bmp'))][:num_rows]
    for row_idx, img_file in enumerate(images):
        img = mpimg.imread(os.path.join(cls_path, img_file))
        ax = axes[row_idx][col_idx]
        ax.imshow(img)
        ax.axis('off')
        if row_idx == 0:
            ax.set_title(cls.upper(), fontsize=13, fontweight='bold', 
color='#6C63FF')
plt.tight_layout()
plt.savefig('sample_images.png', dpi=150, bbox_inches='tight')
plt.show()
print('Sample images displayed')
What it does: Displays a grid of sample images (3 per class) from your training set to visually verify
the data looks correct.
Why it's needed: Before training, ensure images are properly loaded. This sanity check reveals data
organization issues.
CELL 33: Load Data & Create Augmentation Pipeline
AUTOTUNE = tf.data.AUTOTUNE
def load_split(directory, shuffle=True, label_mode=LABEL_MODE):
    """Load a dataset split from a directory."""
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
def augment_and_normalize(image, label):
    image = data_augmentation(image, training=True)
    return image, label
def normalize(image, label):
    return tf.cast(image, tf.float32), label
train_ds = (
    train_ds_raw
    .map(augment_and_normalize, num_parallel_calls=AUTOTUNE)
    .cache()
    .shuffle(buffer_size=1000, seed=SEED)
    .prefetch(AUTOTUNE)
)
val_ds = (
    val_ds_raw
    .map(normalize, num_parallel_calls=AUTOTUNE)
    .cache()
    .prefetch(AUTOTUNE)
)
test_ds = (
test_ds_raw
.map(normalize, num_parallel_calls=AUTOTUNE)
.prefetch(AUTOTUNE)
)
print('Data pipelines built:')
print(f'   Train batches : {len(train_ds_raw)}')
print(f'   Val batches   : {len(val_ds_raw)}')
print(f'   Test batches  : {len(test_ds_raw)}')
What it does: Loads images from disk, applies data augmentation to training images, and creates
optimized pipelines for feeding data to the model.
Why it's needed:
Data loading: Keras needs images loaded into memory batches
Data augmentation: Artificially creates variations to prevent overfitting
Pipeline optimization: Prefetching and caching speed up training
Data augmentation explained:
RandomFlip('horizontal') : Flip image left-right
RandomRotation(0.15) : Rotate ±15 degrees
RandomZoom(0.15) : Zoom ±15%
RandomContrast(0.15) : Adjust contrast ±15%
RandomBrightness(0.1) : Adjust brightness ±10%
RandomTranslation() : Shift ±10%
These variations help the model learn general pest patterns instead of memorizing specific images.
CELL 35: Visualize Augmentation Effects
[Shows 8 augmented versions of one sample pest image to verify augmentation is working and
producing realistic variations.]
CELL 37: Build Model (EfficientNetV2B3 with Custom Head)
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
    out_units = 1 if num_classes == 2 else num_classes
    outputs = Dense(out_units, activation=ACTIVATION)(x)
    model = Model(inputs, outputs)
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss=LOSS,
        metrics=['accuracy']
    )
    return model, base_model
model, base_model = build_model(NUM_CLASSES, IMG_SIZE, LEARNING_RATE, 
base_trainable=False)
print("\nModel Re-built with enhanced Dropout regularization.")
What it does: Creates neural network using transfer learning—takes pre-trained EfficientNetV2B3
and adds custom layers for pest detection.
Architecture:
EfficientNetV2B3 backbone (frozen initially)
GlobalAveragePooling2D → reduces to 1536-dimensional vector
BatchNormalization → stabilize
Dense(512) + ReLU → learn patterns
Dropout(0.5) → prevent overfitting
BatchNormalization → stabilize
Dense(256) + ReLU → learn higher-level patterns
Dropout(0.4) → prevent overfitting
Dense(4) + Softmax → output pest class probabilities
Why transfer learning: Using ImageNet pre-training saves weeks of training time and dramatically
improves accuracy on small datasets.
CELL 39: Phase 1 Training (Frozen Backbone)
callbacks_phase1 = [
    EarlyStopping(
        monitor='val_accuracy',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        verbose=1,
        min_lr=1e-7
    ),
    ModelCheckpoint(
        'checkpoint_phase1.h5',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]
print('Phase 1: Feature Extraction (frozen backbone)...')
history1 = model.fit(
    train_ds,
    epochs=EPOCHS_FROZEN,
    validation_data=val_ds,
    callbacks=callbacks_phase1,
    verbose=1
)
print('\nPhase 1 complete!')
print(f'   Best val accuracy: {max(history1.history["val_accuracy"]):.4f}')
What it does: Trains the custom head layers while keeping the pre-trained backbone frozen.
Why two phases:
Phase 1 stabilises the new head without damaging EfficientNet's ImageNet knowledge
Phase 2 carefully fine-tunes top layers to specialize in pest detection
Callbacks:
EarlyStopping: Stop if validation accuracy doesn't improve for 5 epochs
ReduceLROnPlateau: Divide learning rate by 2 if validation loss plateaus
ModelCheckpoint: Save best model automatically
CELL 41: Phase 2 Fine-Tuning
base_model.trainable = True
for layer in base_model.layers[:-UNFREEZE_LAYERS]:
    layer.trainable = False
trainable_count = sum([tf.size(w).numpy() for w in model.trainable_weights])
print(f'Unfroze top {UNFREEZE_LAYERS} layers of backbone')
print(f'   Trainable params now: {trainable_count:,}')
model.compile(
    optimizer=Adam(learning_rate=FINETUNE_LR),
    loss=LOSS,
    metrics=['accuracy']
)
callbacks_phase2 = [
    EarlyStopping(
        monitor='val_accuracy',
        patience=7,
        restore_best_weights=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.3,
        patience=3,
        verbose=1,
        min_lr=1e-8
    ),
    ModelCheckpoint(
        MODEL_SAVE_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]
print('\nPhase 2: Fine-Tuning (unfrozen top layers)...')
history2 = model.fit(
    train_ds,
    epochs=EPOCHS_FINETUNE,
    validation_data=val_ds,
    callbacks=callbacks_phase2,
    verbose=1
)
print('\nPhase 2 complete!')
print(f'   Best val accuracy: {max(history2.history["val_accuracy"]):.4f}')
print(f'   Model saved to   : {MODEL_SAVE_PATH}')
What it does: Unfreezes top 10 layers of backbone and continues training with much smaller learning
rate (1e-6).
Why small learning rate: Prevents backbone from "forgetting" ImageNet knowledge while adapting
to pest detection.
CELL 43: Merge Training Histories & Plot
[Combines Phase 1 and Phase 2 training logs and plots accuracy/loss curves with a vertical line marking
the transition between phases.]
CELL 45: Evaluate on Test Set
best_model = keras.models.load_model(MODEL_SAVE_PATH)
test_loss, test_acc = best_model.evaluate(test_ds, verbose=1)
print(f'\nTest Results:')
print(f'   Test Accuracy : {test_acc:.4f} ({test_acc*100:.2f}%)')
print(f'   Test Loss     : {test_loss:.4f}')
y_pred_proba = best_model.predict(test_ds, verbose=1)
if NUM_CLASSES == 2:
y_pred = (y_pred_proba > 0.5).astype(int).flatten()
y_true = np.concatenate([y.numpy().astype(int).flatten() for _, y in test_ds])
else:
y_pred = np.argmax(y_pred_proba, axis=1)
y_true = np.concatenate([np.argmax(y.numpy(), axis=1) for _, y in test_ds])
print(f'\nSamples predicted: {len(y_pred)}')
What it does: Loads the best trained model and evaluates it on completely unseen test images.
Why: Test set provides the true measure of model performance on real-world pest data.
CELL 47: Confusion Matrix
[Creates a 4×4 matrix showing which pest types the model confused with each other during testing.]
CELL 49: Classification Report & Per-Class Metrics
[Computes Precision, Recall, F1-Score per pest type to show which classes are harder to distinguish.]
CELL 51: ROC Curves
[Plots sensitivity vs. false alarm rate for each pest type, helping choose optimal classification
thresholds.]
CELL 53: Visualize Correct & Incorrect Predictions
[Shows example images the model got right and got wrong, revealing patterns in mistakes.]
CELL 55: Export Model & Create Summary
best_model.save(MODEL_SAVE_PATH)
best_model.export('best_model_savedmodel')
import json
class_map = {i: name for i, name in enumerate(CLASS_NAMES)}
with open('class_names.json', 'w') as f:
    json.dump(class_map, f, indent=2)
print('=' * 55)
print('  TRAINING COMPLETE - FINAL SUMMARY')
print('=' * 55)
print(f'  Dataset          : {NUM_CLASSES} classes - {CLASS_NAMES}')
print(f'  Backbone         : EfficientNetV2B3 (ImageNet weights)')
print(f'  Test Accuracy    : {test_acc * 100:.2f}%')
print(f'  Test Loss        : {test_loss:.4f}')
print(f'  Model saved      : {MODEL_SAVE_PATH}')
print(f'  SavedModel dir   : best_model_savedmodel/')
print(f'  Class map        : class_names.json')
print('=' * 55)
What it does: Saves the trained model in two formats and exports class mappings for deployment.
Output formats:
.h5 : Single file format for Keras
SavedModel : Directory format for production deployment
class_names.json : Maps numeric predictions to pest class names
CELL 57-62: Alternative MobileNetV3 Approach
The notebook includes an alternative simpler architecture using MobileNetV3Small (3× smaller, 2×
faster, slightly lower accuracy). Useful for mobile deployment.
CELL 65: Flask API for Deployment
from flask import Flask, request, jsonify
import io
from PIL import Image
IMG_SIZE = (224, 224)
CLASS_NAMES = ['Diconocoris distanti', 'Gynaikothrips karny', 'Healthy', 'Pterolopha 
annulata']
MODEL_PATH = 'best_mobilenet_model_phest_v2.keras'
model = tf.keras.models.load_model(MODEL_PATH)
def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize(IMG_SIZE)
    img_array = np.array(img)
    img_array = tf.cast(img_array, tf.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array
app = Flask(__name__)
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        image_bytes = file.read()
        processed_image = preprocess_image(image_bytes)
        predictions = model.predict(processed_image)
        predicted_class_idx = np.argmax(predictions, axis=1)[0]
        predicted_class_name = CLASS_NAMES[predicted_class_idx]
        confidence = float(predictions[0][predicted_class_idx])
        response = {
            'prediction': predicted_class_name,
            'confidence': confidence,
            'all_confidences': {name: float(pred) for name, pred in zip(CLASS_NAMES, 
predictions[0])}
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
print("Flask app ready. Run: python flask_app.py")
What it does: Creates a web API for farmers/tools to submit pest images and get predictions.
Usage:
curl -X POST -F "file=@pest_image.jpg" http://localhost:5000/predict
# Returns: {"prediction": "Diconocoris distanti", "confidence": 0.87, ...}
Glossary: Deep Learning & Neural Network Terms (Beginner-Friendly)
Foundational Concepts
Neural Network: A computational model inspired by biological brains. Arranged in layers of
interconnected "neurons" (variables). Each connection has a "weight" (a number) that transforms data
flowing through it.
Neuron: A simple computation unit that takes multiple inputs, multiplies each by a weight, sums
them, and applies an activation function.
Weight: A number multiplied by input, determining how much that input influences the output.
Weights are what the model learns during training.
Bias: A constant added to each neuron's output, allowing the neuron to shift its decision boundary.
Activation Function: A non-linear transformation applied after each neuron. Examples: ReLU,
sigmoid, softmax.
ReLU (Rectified Linear Unit): Activation function that outputs max(0, x). Keeps positive values,
zeros out negatives.
Sigmoid: Activation function that outputs values between 0 and 1, shaped like an S curve. Used for
binary classification.
Softmax: Activation that converts numbers to probabilities summing to 1. Used for multi-class
classification (4 pest classes in our case).
Training Concepts
Forward Pass: Data flows through the network from input to output, neuron by neuron.
Loss Function: Measures how wrong the model's predictions are compared to true labels. Lower loss
= better predictions.
Gradient: A vector of partial derivatives showing which direction to adjust weights to reduce loss.
Backpropagation: Algorithm that calculates gradients for all weights by chain rule, working
backwards from output to input.
Optimizer: Algorithm that updates weights based on gradients. Adam adapts learning rate per
parameter.
Learning Rate: Controls how much to update weights each step. Too high = diverges; too low =
slow/stuck.
Epoch: One complete pass through entire training dataset.
Batch: Subset of training data processed together before weight update.
Overfitting: Model memorizes training data instead of learning generalizable patterns. Signs: training
accuracy high, validation accuracy low.
Underfitting: Model too simple to capture patterns. Signs: both training and validation accuracy low.
Validation Set: Subset used to evaluate during training (not for weight updates).
Test Set: Held-out data never seen during training. True measure of model performance.
Architecture Concepts
Deep Learning: Neural networks with many layers (>2-3). Each layer learns increasingly abstract
features.
Transfer Learning: Using a model pre-trained on large dataset (ImageNet) as starting point, then
fine-tuning on smaller dataset. Dramatically reduces training time and data requirements.
Backbone/Base Model: The pre-trained core (EfficientNetV2B3 trained on ImageNet).
Fine-Tuning: Continuing training a pre-trained model on new data with smaller learning rate.
Dropout: Randomly disables neurons during training to prevent co-adaptation. Effective
regularization.
BatchNormalization: Normalizes layer inputs to have mean≈0 and std≈1. Stabilizes training.
EfficientNetV2B3: Pre-trained image classification model balancing accuracy, speed, size. Backbone
used in this notebook.
GlobalAveragePooling: Reduces spatial feature map to single vector by averaging. Transition
between spatial and fully-connected layers.
Data Concepts
Image Classification: Task of predicting single class label for each image.
Multi-class Classification: Multiple possible classes (4 in our case); each sample belongs to exactly
one.
Binary Classification: Two possible classes.
Categorical Classification: 3+ classes. Uses softmax and categorical crossentropy.
Label/Class: True category for a sample.
One-Hot Encoding: Represents categories as binary vectors. Example: 3 classes → [1,0,0], [0,1,0],
[0,0,1].
Data Augmentation: Artificially creating image variations (rotation, flip, zoom, brightness) to reduce
overfitting.
Stratified Splitting: Dividing data while maintaining class proportions. Ensures balanced
train/val/test.
Class Imbalance: When classes have very different numbers of samples.
Class Weights: Multipliers on loss for each class, reducing impact of imbalance.
Evaluation Concepts
Accuracy: Percentage of correct predictions.
Precision: Of predicted positives, what % were correct? High precision = few false alarms.
Recall: Of actual positives, what % did we find? High recall = few missed cases.
F1-Score: Harmonic mean of precision and recall. Balances both.
Confusion Matrix: Table showing true vs predicted labels. Reveals which classes are confused with
each other.
ROC Curve: Plots True Positive Rate vs False Positive Rate at different thresholds.
AUC: Area under ROC curve. 0.5 = random, 1.0 = perfect.
TP (True Positive): Predicted positive, actually positive. Correct detection.
TN (True Negative): Predicted negative, actually negative. Correct rejection.
FP (False Positive): Predicted positive, actually negative. False alarm.
FN (False Negative): Predicted negative, actually positive. Missed case.
How to Use This Notebook
1. Organize your dataset in the standard structure:
/PEPPER/pest_detection/pest detection/
├── Diconocoris distanti/
│   ├── img1.jpg
│   └── ...
├── Gynaikothrips karny/
│   ├── img1.jpg
│   └── ...
├── Healthy/
│   ├── img1.jpg
│   └── ...
└── Pterolopha annulata/
├── img1.jpg
└── ...
2. Upload to Google Drive at the path specified in BASE_DATA_DIR
3. Update CELL 4 (Configuration) with:
Correct BASE_DATA_DIR path
Hyperparameters if desired (usually default values work well)
4. Run cells in order (0-65). The repeated data-splitting cells can be safely run multiple times.
5. Download outputs after training:
best_model.h5 — trained model for deployment
class_names.json — pest type mappings
PNG charts for analysis
6. Deploy the Flask API (CELL 65) to classify new pest images in real time
7. Monitor metrics:
Confusion matrix: Which pest types are confused?
Classification report: Which classes perform worst?
ROC curves: What's the AUC for each pest type?
Key Strengths of This Pipeline
Pre-trained backbone saves 95% of training time
Two-phase training balances transfer learning principles
Data augmentation prevents overfitting on small datasets
Comprehensive evaluation (confusion matrix, ROC, per-class metrics)
Production-ready export for deployment
Flask API enables easy integration into farming tools
Summary
This pest detection model uses transfer learning with EfficientNetV2B3 to classify four pest
categories from mango leaf images. The two-phase training (frozen backbone then fine-tuning)
combined with data augmentation creates a robust model that generalizes well to new images. The Flask
API enables easy deployment for farmer-facing applications.
This same architecture and training process can be adapted for other agricultural image classification
tasks by simply changing the dataset path and class names.