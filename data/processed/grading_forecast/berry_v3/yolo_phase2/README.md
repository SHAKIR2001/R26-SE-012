# Phase 2 YOLO dataset definition

This directory defines the leakage-free V3 YOLO experiment dataset. It does not replace the canonical Roboflow export.

```text
canonical V3 images and YOLO labels
        +
v3_image_sample_manifest.csv (research partitions and physical-sample IDs)
        |
        v
prepare_yolo_dataset.py
        |
        +-- data.yaml
        +-- train.txt / validation.txt / test.txt
        +-- dataset_integrity.json
        `-- materialized/ (generated, git-ignored working copies)
```

The working copies are required because Ultralytics may repair JPEG end markers while scanning a dataset. Keeping this generated layer prevents framework preprocessing from writing into the canonical V3 export. Images and labels are copied unchanged before scanning; training still uses the original Roboflow YOLO annotations.

Rebuild and verify the derived dataset from the repository root:

```powershell
$env:YOLO_CONFIG_DIR = (Resolve-Path '.ultralytics')
.\.venv-yolo\Scripts\python.exe ml\grading_forecast\berry_grading\training\v3_yolo\prepare_yolo_dataset.py
```

The preparation script refuses inconsistent class IDs, missing labels, duplicate image assignment, sample leakage, or a split other than 539/116/120 images.
