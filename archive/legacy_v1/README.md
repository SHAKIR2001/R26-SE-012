# Legacy V1 Berry Label Artifacts

This directory preserves the first folder-to-label berry dataset workflow as
historical research evidence.

## Preserved files

- `original/generate_grading_labels.py` is the unchanged original script from
  `scripts/generate_grading_labels.py`.
- `artifacts/berry_grading_labels.csv` is the unchanged 360-row V1 manifest
  formerly stored under `data/annotations/grading_forecast/`.
- `artifacts/berry_dataset_summary.json` is the matching 120/120/120 V1 count
  summary.

The archived script is preserved byte-for-byte and is not a current command.
Because its repository-root calculation depends on its original location, do
not execute it from this archive. Restore it to its original path only when
deliberately reproducing the historical V1 workflow in an isolated working
tree.

Current V2/V3 preparation lives under `ml/grading_forecast/`. Active tools must
receive an explicit dataset path rather than silently selecting these V1 files.

## Preservation hashes

```text
generate_grading_labels.py
21FCCD2B47EA2EC43C07809895ED259009235F06F14F7F823698214F249668E2

berry_grading_labels.csv
14D9526B18638757A00B001E21DD65DEC172882559DB7D469928FF0DE90170F8

berry_dataset_summary.json
FB7B7037B94241E048EB2231C116C05263E7652AD406EC605409FCF2184C1CAD
```
