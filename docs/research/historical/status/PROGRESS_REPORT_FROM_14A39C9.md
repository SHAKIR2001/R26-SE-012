# Progress Report From Commit `14a39c9` to `39592c628ff5b432a8b8d18bedd4ae65b1e1a3b9`

**Reporting scope:** `14a39c9f04e937d81ce50c2b5776f3217cb9870c` through `39592c628ff5b432a8b8d18bedd4ae65b1e1a3b9`, inclusive  
**Period covered:** 2026-10-06 to 2026-10-07  
**Prepared:** 2026-10-07  
**Scope boundary:** research, data reconstruction, model training, controlled evaluation, and integrity validation. This range does not establish production deployment, mobile/backend integration, official commercial grading, live market pricing, or field robustness.

## 1. Executive summary

Seven commits transformed the grading/forecasting work from a research-definition checkpoint into two experimentally evaluated research tracks:

1. **V3 pepper grading and rejection:** the work defined a defensible image-level task, reconstructed a leakage-resistant sample-group split, trained and evaluated a YOLO11n detector/classifier, measured its failure on non-pepper content, and then ran a controlled hard-negative follow-up. The follow-up rejected all 49 images in a new sealed negative holdout, versus 71.43% for the frozen control on the same images, while retaining 98.33% coverage and 95.83% all-image accuracy on the original 120-image positive test. The hard-negative hypothesis is supported under this controlled experiment.
2. **Price reconstruction and forecasting:** the work replaced the weakly evidenced local price foundation with 16,903 source-observed EAC pepper-price records and explicit page-level provenance. A leakage-controlled, expanding-window Phase 5 experiment found that a small grade-specific Ridge model improved on persistence in validation and the main final test, especially for direction, but was fractionally worse on the ten newest observations. Consistent forecasting superiority is therefore not established.

The current evidence is strong enough to support separately authorized, controlled next-stage research. It is not sufficient for an unqualified production claim. The principal remaining risks are real-world camera/domain shift and semantic negative diversity for grading, and sparse/irregular Grade 2 history, absent exogenous variables, wide uncertainty intervals, and a very small external period for forecasting.

## 2. Commit-by-commit progress

| Commit | Date | Main contribution | Outcome |
|---|---|---|---|
| `14a39c9` | 2026-10-06 | V3 Phase 0 research decision record | Locked the task, labels, sample-level meaning, rejection requirement, claim boundaries, and validation-first threshold policy. |
| `6b03e16` | 2026-10-06 | V2 saliency diagnostics and V3 Phase 1 audit tooling | Reconstructed the 775-image/194-sample dataset, completed blind review and shortcut-risk analysis, and established a group-aware split. |
| `3651c83` | 2026-10-07 | V3 Phase 2 YOLO training, dataset preparation, evaluation, and frozen artifacts | Trained YOLO11n and produced validation, sealed-test, sample-aggregation, integrity, model, and figure artifacts. |
| `8301141` | 2026-10-07 | V3 Phase 3 rejection and quality-gating pipeline | Built an external 80-image negative dataset, selected gates on calibration/validation data, and demonstrated that vegetation/crop false acceptance remained too high. |
| `831cb1a` | 2026-10-07 | Phase 4 EAC price reconstruction and forecasting foundation | Reconstructed dated source data with provenance, defined next-observation targets, and showed that the initial Ridge candidate did not consistently beat persistence. |
| `614296e` | 2026-10-07 | Phase 5 price-movement experiment and integrity validation | Evaluated feature groups, targets, baselines, statistical/ML candidates, intervals, final test, and an external newest-period check. |
| `39592c6` | 2026-10-07 | V3 Phase 3 controlled hard-negative follow-up | Added 250 source-controlled negatives, fine-tuned one treatment model, froze the threshold using validation only, and improved the controlled rejection gate. |

Across this range, the repository gained the versioned data manifests, source snapshots, model-ready datasets, training/evaluation code, frozen model specifications/checkpoints, metrics, figures, integrity records, and research reports needed to reproduce and audit these conclusions. Historical V1/V2 artifacts were retained as baselines rather than overwritten.

## 3. V3 pepper grading and rejection

### 3.1 Phase 0 — research definition

The task was explicitly defined as analysis of a smartphone image of a harvested black-pepper sample or batch. The system should locate valid pepper material, classify it as the project-specific **V3 Grade 1** or **V3 Grade 2**, and reject invalid, poor-quality, or uncertain inputs.

Important claim boundaries were fixed:

- the labels describe the project dataset and are not proven equivalent to an official SLS specification or buyer grade;
- the broad annotations represent a sample/batch region, not reliable per-berry localization;
- thresholds must be selected on validation evidence, not invented or tuned on the final test;
- V1 and V2 remain unchanged historical baselines;
- application integration and deployment are outside the evaluated research phases.

### 3.2 Phase 1 — data audit, split reconstruction, and shortcut diagnosis

The full V3 dataset contains **775 images from 194 physical samples**, with broad sample/batch boxes and two classes. A group-aware split keeps every physical sample in exactly one partition:

| Partition | Physical samples | Images | Grade 1 | Grade 2 |
|---|---:|---:|---:|---:|
| Train | 135 | 539 | 312 | 227 |
| Validation | 29 | 116 | 68 | 48 |
| Test | 30 | 120 | 68 | 52 |
| **Total** | **194** | **775** | **448** | **327** |

Integrity checks accounted for every image and sample and found no sample-group leakage.

A blinded 40-image review achieved **80% primary agreement** overall: 18/20 (90%) for Grade 1 and 14/20 (70%) for Grade 2. Four responses were `Uncertain`; agreement among the 36 decisive responses was 32/36 (88.9%). Cohen's kappa was 0.636 when `Uncertain` was retained as a third response category, and the supplementary binary kappa excluding uncertain responses was 0.778. The review supported continuing the experiment but also showed that Grade 2 is the less visually reliable class.

Shortcut risk was assessed as **high**. Camera/resolution and grade are partially confounded. A V2 saliency review found 3 pepper-focused and 6 mixed examples, with none judged purely background-focused, but this small diagnostic could not eliminate shortcut concerns.

### 3.3 Phase 2 — YOLO11n training and positive-pepper evaluation

The experiment used pretrained YOLO11n with Ultralytics 8.4.174 and PyTorch 2.14.1+cu130. Key settings were image size 640, batch size 4, AdamW, seed 42, deterministic execution, and a 75-epoch maximum. Early stopping ended after epoch 57 and selected epoch 45. Training ran on an NVIDIA RTX 2050 4 GB GPU. The frozen best checkpoint is approximately 5.21 MiB.

Validation results:

| Metric | Result |
|---|---:|
| Classification accuracy | 95.69% |
| Macro F1 | 0.9562 |
| Balanced accuracy | 0.9632 |
| Coverage | 100% |
| Detection precision | 0.9479 |
| Detection recall | 0.9682 |
| mAP50 | 0.9879 |
| mAP50-95 | 0.8617 |

Sealed positive-test results:

| Metric | Result |
|---|---:|
| Correct images | 115/120 |
| Accuracy | 95.83% |
| Macro F1 | 0.9578 |
| Weighted F1 | 0.9584 |
| Balanced accuracy | 0.9610 |
| Grade 1 F1 | 0.9624 |
| Grade 2 F1 | 0.9533 |
| Detection precision | 0.9402 |
| Detection recall | 0.9552 |
| mAP50 | 0.9791 |
| mAP50-95 | 0.8505 |

Both majority-vote and confidence-weighted sample aggregation classified all **30/30 physical test samples** correctly. That result is encouraging, but the test contains only valid pepper images and therefore says nothing about non-pepper rejection.

All five image-level test errors occurred on the SM-A127F device subset, while the Galaxy A06 subset is confounded with Grade 1. The experiment therefore did not resolve device/background shortcut risk.

### 3.4 Phase 3 — initial non-pepper rejection and quality gates

An external dataset of **80 open-license Wikimedia images** was created across ten strata and split into 40 calibration and 40 held-out evaluation images. Provenance, licenses, hashes, and overlap checks were recorded.

The frozen Phase 2 model rejected 58/80 negatives at confidence 0.05 and 65/80 at confidence 0.25 before the full operational gate. Validation-only selection froze these controls:

- blur score at least 10;
- brightness at least 50;
- minimum image dimension at least 320 pixels;
- detected box area ratio at least 0.20;
- detection confidence at least 0.55;
- grade confidence at least 0.05;
- class-confidence margin at least 0.30.

Combined validation and held-out results were:

| Measure | Result |
|---|---:|
| Valid-pepper coverage | 111/116 = 95.69% |
| Valid-pepper false rejection | 5/116 = 4.31% |
| Accepted-pepper accuracy | 108/111 = 97.30% |
| Accepted-pepper macro F1 | 0.9725 |
| Held-out negative rejection | 35/40 = 87.50% |
| Held-out negative false acceptance | 5/40 = 12.50% |

All five false accepts were vegetation/crop images; one aerial-crop example was accepted with confidence as high as 0.943. The operational rejection gate therefore **did not pass**, and this evidence motivated a controlled hard-negative experiment.

### 3.5 Phase 3 follow-up — controlled hard-negative fine-tuning

The follow-up assembled **250 usable Wikimedia Commons images** with creator, license, source page, media URL, dimensions, retrieval information, and SHA-256 hashes. The pool contained:

- 90 vegetation/leaves images;
- 75 agricultural-crop images;
- 11 aerial-crop images;
- 27 agricultural-material images;
- 24 other spice/food images;
- 10 ordinary-object images;
- 13 background-scene images.

There were 172 creator/source groups, no exact hash duplicates, and no overlap with the 775 V3 images or frozen 80-image Phase 3 dataset. Groups were isolated to one partition. The split was **152 train / 49 validation / 49 sealed final holdout**, with every category represented in every partition.

Collection stopped below the nominal 300-image target because repeated Wikimedia transfer failures dominated progress. The resumable record contains 199 failed attempts and four rejected downloads; the final 250 accepted files remained source-controlled and hash-verified.

One treatment model was initialized from the frozen Phase 2 checkpoint. Training used only:

- 539 Phase 1 TRAIN pepper positives;
- 152 empty-label training negatives;
- 116 Phase 1 VALIDATION pepper positives for validation;
- 49 validation negatives.

No third class or fabricated box was introduced. The run used 640-pixel images, batch 4, AdamW, learning rate 0.0001, weight decay 0.0005, seed 42, deterministic execution, 30 maximum epochs, and patience 8. It stopped after epoch 27 and selected epoch 19. Cumulative training time was 2,620.8 seconds.

The detection-confidence threshold was selected only from validation candidates 0.05 to 0.90. The selection rule required at least 95% valid-pepper coverage and then prioritized negative rejection, accepted-pepper macro F1, coverage, and the lowest threshold. The selected threshold was **0.05**; the earlier quality and margin gates were retained.

#### Follow-up results

| Measure | Frozen control/baseline | Follow-up | Change |
|---|---:|---:|---:|
| Validation valid-pepper coverage | 95.69% | 98.28% | +2.59 pp |
| Validation false rejection | 4.31% | 1.72% | -2.59 pp |
| Validation accepted accuracy | 97.30% | 95.61% | -1.68 pp |
| Validation accepted macro F1 | 0.9725 | 0.9539 | -0.0186 |
| New sealed negative rejection | 71.43% | 100.00% | +28.57 pp |
| New vegetation/crop/aerial rejection | 60.00% | 100.00% | +40.00 pp |
| Original Phase 3 negative rejection | 87.50% | 100.00% | +12.50 pp |

The treatment rejected **49/49** images in the new sealed holdout with zero false accepts. On the once-accessed original Phase 2 positive test, it produced:

| Measure | Follow-up result |
|---|---:|
| Coverage | 118/120 = 98.33% |
| False rejection | 2/120 = 1.67% |
| All-image accuracy | 115/120 = 95.83% |
| Accepted-subset accuracy | 115/118 = 97.46% |
| Macro F1 | 0.9643 |
| Weighted F1 | 0.9661 |
| Grade 1 F1 | 0.9781 |
| Grade 2 F1 | 0.9505 |

The predefined support rule required at least a ten-percentage-point same-holdout rejection gain, at least 95% positive-test coverage, and no more than 0.02 absolute macro-F1 loss. The experiment met these conditions. Its result is therefore **SUPPORTED**, with the decision **COMPLETE — OPERATIONAL GATE IMPROVED**.

This is an improvement in a controlled gate, not proof of field or production reliability.

## 4. EAC price reconstruction and forecasting

### 4.1 Starting problem

The previous local artifact covered only 2021-02-22 to 2026-08-18 despite a broader filename claim, contained 7,742 rows over 232 dates, and stored only the index URL rather than each dated source page. Its V2 Random Forest was substantially worse than persistence: MAE/RMSE 82.42/88.45 LKR/kg versus 16.41/22.52 for persistence. Runtime therefore returned the latest Grade 1 observation, while Grade 2 depended on an observed gap and a hard-coded 113 LKR/kg fallback discount.

### 4.2 Phase 4 — reconstructed data foundation

Phase 4 rebuilt the data from public Department of Export Agriculture Economic Research Unit dated pages. Of 495 dated links, 493 pepper pages were parsed; the broken 2023-04-25 and 2026-06-23 links were explicitly retained as missing rather than inferred.

The canonical dataset contains:

| Measure | Result |
|---|---:|
| Canonical pepper observations | 16,903 |
| Date range | 2016-10-04 to 2026-09-29 |
| National Grade 1 observations | 493 |
| National Grade 2 observations | 358 |
| Dates with both national grades | 358 |
| Grade 2 missing dates relative to union | 135 |

Each observation retains its date, market, commodity, grade, price type, price, source organization, exact dated-page URL, source date, retrieval date, page hash, table type, and market level. Missing values remained missing: no interpolation, forward fill, fixed Grade 2 discount, resampling, or model-generated replacement was used.

The target became the return to the **next actual EAC observation**, retaining the actual elapsed days. Features and targets were chronological, with expanding-window fitting and per-window scaling. The frozen partitions were:

| Partition | Target-date range | Grade 1 | Grade 2 |
|---|---|---:|---:|
| Train | 2016-10-11 to 2023-09-19 | 340 | 213 |
| Validation | 2023-09-26 to 2025-02-25 | 73 | 66 |
| Final test | 2025-03-04 to 2026-08-18 | 74 | 73 |
| External newest | 2026-08-25 to 2026-09-29 | 5 | 5 |

The best initial ML candidate was separate Grade 1/Grade 2 Ridge regression. It did not beat persistence on validation macro-grade RMSE: **0.04434 versus 0.04319**. On the 147-forecast final test, Ridge improved return RMSE (0.02954 versus 0.03187), price RMSE (54.55 versus 58.12 LKR/kg), and direction accuracy (46.26% versus 10.20%), but persistence retained lower return MAE (0.01858 versus 0.01989), price MAE (34.62 versus 37.29), and price MAPE (1.85% versus 1.98%). Ridge was also worse on all principal error measures across the ten newest observations.

Phase 4 therefore completed the data and evaluation foundation but did not demonstrate a superior forecasting model.

### 4.3 Phase 5 — controlled price-movement forecasting

Phase 5 retained the frozen Phase 4 data and temporal partitions. It evaluated persistence, last-return, expanding-mean, and historical-drift baselines; Ridge, Lasso, Elastic Net, Random Forest, gradient boosting, and conditional ARIMA-style candidates; separate and shared grade formulations; and controlled feature/target ablations.

Validation selected the smallest feature group and target:

- separate Grade 1 and Grade 2 Ridge models;
- next-observation **log return**;
- four completed-return lags plus days since the previous observation;
- minimum 50 completed target observations;
- expanding walk-forward refitting with per-window scaling.

Larger technical/calendar feature groups worsened validation macro-grade RMSE (0.04633 and 0.04645 versus 0.04188 for simple return lags). Adding same-date grade-relationship features also worsened the common-cohort score from 0.04182 to 0.06090. This suggests that the available signal is weak and concentrated in recent returns.

#### Main final-test results

| Method | Return MAE | Return RMSE | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|
| Selected log-return Ridge | **0.01820** | **0.02985** | **52.38%** | **33.996** | **54.728** |
| ARIMA(1,0,0) conditional OLS | 0.01898 | 0.03037 | 46.94% | 35.56 | 56.11 |
| Persistence | 0.01858 | 0.03187 | 10.20% | 34.62 | 58.12 |
| Expanding mean return | 0.01924 | 0.03202 | 45.58% | 35.96 | 58.77 |
| Last observed return | 0.02991 | 0.05428 | 47.62% | 55.49 | 98.29 |

Selected-model price MAPE was 1.815%, compared with 1.853% for persistence. Non-flat directional accuracy was 58.33%. The continuous model never predicted an exact source-resolution FLAT value, and its UP recall (70.15%) was substantially stronger than its DOWN recall (46.15%).

Grade-specific results show a major reliability difference:

| Grade | Return MAE | Return RMSE | R2 | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Grade 1 | 0.00770 | 0.01066 | 0.0005 | 54.05% | 15.19 | 20.84 |
| Grade 2 | 0.02884 | 0.04098 | 0.1276 | 50.68% | 53.06 | 74.77 |

A validation-calibrated empirical interval covered 96.60% of final-test observations, but its mean width was 275.18 LKR/kg. The Grade 2 mean width was **456.56 LKR/kg**, compared with 96.26 for Grade 1, so the interval is diagnostic rather than operationally precise.

#### External newest-period check

The five later target dates per grade were kept out of selection:

| Method | Return MAE | Return RMSE | Direction accuracy | Price MAE | Price RMSE |
|---|---:|---:|---:|---:|---:|
| Selected Ridge | 0.02330 | 0.03259 | **70%** | 42.83 | 58.54 |
| Persistence | **0.02305** | **0.03259** | 10% | **42.33** | **58.22** |

Ridge correctly predicted four of the five later Grade 1 directions, improving the Phase 4 directional failure, but remained fractionally worse than persistence on external return and price errors. The forecasting conclusion is therefore **MIXED**: limited evidence of useful short-horizon signal exists, but consistent ML superiority is not established. Phase 5 is **READY WITH LIMITATIONS** for a separately authorized controlled Phase 6 experiment, not deployment.

The latest verified source observation in this dataset is 2026-09-29. It is a dated EAC reference, not today's price, a live buyer quote, or a guaranteed transaction value.

## 5. Reproducibility and integrity evidence

The work added explicit safeguards against the most important forms of leakage and artifact drift:

- physical sample groups are isolated across berry train, validation, and test partitions;
- negative creator/source groups are isolated across negative partitions;
- exact hashes prevent overlap with V3 positives and earlier negatives;
- hard-negative threshold selection uses validation only, and final sets are opened after model/threshold freeze;
- the Phase 3 follow-up integrity suite passed all **24/24 checks**;
- all 775 V3 images and annotations remained unchanged against recorded hashes/values;
- Phase 4 source/canonical identity, duplicate checks, observed-value flags, chronological targets, backward-looking lags, and broken-link handling passed focused validation;
- Phase 5 verified that Phase 4 artifacts remained unchanged, selection was validation-only, scaling was not fit on the full dataset, persistence was included everywhere, and required artifacts existed;
- the complete Phase 5 walk-forward prediction artifact was reproduced byte-for-byte with seed 42 and deterministic single-threaded execution.

These checks support experiment traceability. They do not substitute for independent replication on a new field/camera dataset or a longer future price period.

## 6. What is complete

### Berry-grading research

- V3 research question and claim boundaries are documented.
- The 775-image dataset is audited and split by physical sample.
- Blind label review and saliency/shortcut diagnostics are recorded.
- A frozen YOLO11n positive-pepper baseline is trained and evaluated.
- An independently sourced initial non-pepper benchmark exists.
- Quality, confidence, and uncertainty gates are explicit and reproducible.
- The vegetation/crop false-acceptance failure was documented rather than hidden.
- A controlled hard-negative treatment was trained from the frozen checkpoint.
- Validation, a new sealed negative holdout, the original Phase 3 negatives, and the original Phase 2 positive test were evaluated under a frozen protocol.
- The hard-negative hypothesis met its predefined support criteria.

### Price research

- The deficient earlier local data and runtime behavior were audited.
- A source-provenanced 2016-2026 EAC dataset was reconstructed without inventing missing Grade 2 values.
- Next-observation return, direction, and derived-price targets are explicit.
- Chronological train, validation, final-test, and external periods are frozen.
- Persistence and multiple statistical/ML candidates were compared through expanding walk-forward evaluation.
- Feature, target, formulation, grade-sharing, uncertainty, and error analyses are recorded.
- A selected research specification exists, while the mixed persistence comparison is retained honestly.

## 7. Limitations and remaining gaps

### 7.1 Berry grading/rejection

- **No field validation:** internet negatives and controlled dataset images do not represent farms, warehouses, markets, lighting extremes, hands, containers, mixed produce, video frames, or all phone cameras.
- **Small negative holdout:** 49 unseen negatives are useful but insufficient to claim a universally reliable 100% rejection rate.
- **Finite semantic coverage:** exact-hash deduplication was performed, but semantic near-duplicate detection was not established.
- **Device/shortcut confounding:** grade, phone model, resolution, and capture setting remain partially confounded; all original Phase 2 image-level errors occurred on one device subset.
- **Confidence is not probability:** detector/class scores are not calibrated probabilities.
- **Validation trade-off:** accepted validation accuracy and macro F1 fell by 1.68 percentage points and 0.0186 respectively, even though coverage and rejection improved.
- **Two positive rejects remain:** the follow-up rejected two Grade 2 images in the positive test.
- **Collection target shortfall:** the negative pool froze at 250 rather than the nominal 300 because of repeated remote transfer failures.
- **No official-grade evidence:** V3 Grade 1/2 prediction is not proven equivalent to SLS, buyer, laboratory, moisture, density, contamination, or transaction-grade assessment.
- **No deployment evidence:** no mobile latency, model conversion, memory/power, offline behavior, UX, API, or end-to-end field workflow has been evaluated in this range.

### 7.2 Price forecasting

- **Sparse Grade 2 history:** only 358 observations exist, with major gaps and a maximum historical gap of 231 days.
- **Irregular horizon:** the target is the next actual observation, not a fixed seven-, fourteen-, or twenty-eight-day horizon.
- **Tiny external check:** only ten external predictions were available.
- **Inconsistent advantage:** the selected model beat persistence in validation and final test but not on external error.
- **Weak absolute signal:** R2 is near zero for Grade 1 and low overall; direction accuracy remains modest.
- **FLAT prediction failure:** the continuous model did not reproduce exact source-resolution flat outcomes.
- **Wide uncertainty:** Grade 2 empirical intervals are too broad for confident operational guidance.
- **Missing drivers:** weather, supply, demand, exports, policy, buyer, location, quality, moisture, and other causal/exogenous factors are absent.
- **Reference-price boundary:** EAC observations are dated public market references, not live offers or guaranteed farm-gate transaction prices.
- **No single deployed model:** the selected specification refits its scaler and estimator at each expanding origin; it is a research protocol, not a production checkpoint.

### 7.3 System-level gaps

- Grading and price outputs have not been fused into a validated decision rule.
- No calibrated end-to-end uncertainty policy determines when to abstain, request another image, defer to a human, or show persistence instead of the learned forecast.
- No independent future-data replication, prospective study, field pilot, or user study has been completed.
- No backend/mobile integration or deployment was performed in this commit range.
- No evidence yet supports automated buying, selling, pricing, or official quality decisions.

## 8. Current conclusions

1. **The V3 positive-pepper classifier is strong on its leakage-controlled internal test**, with 95.83% image accuracy and perfect 30-sample aggregation, but camera and collection shortcuts remain plausible.
2. **The original rejection strategy was not sufficient.** A 12.5% held-out false-accept rate, concentrated in vegetation/crops, was an important failure.
3. **Controlled hard-negative training materially improved rejection.** On the same new unseen set, rejection rose from 71.43% to 100%, and the predefined safety/grading criteria were met. This supports the experimental hypothesis, not universal production performance.
4. **The price-data foundation is substantially more defensible than the prior artifact.** It is source-observed, page-provenanced, wider in time, grade-aware, and explicit about missingness.
5. **Price forecasting contains limited predictive signal, especially for direction, but does not consistently beat persistence.** Persistence must remain visible as a comparator and fallback.
6. **Neither research track is production-ready.** The next defensible step is controlled, separately authorized evaluation—not automatic deployment or an unqualified Phase 6 rollout.

## 9. Recommended next research gates

The following work would close the largest evidence gaps, in priority order:

1. Freeze a prospective field dataset before capture, spanning phones, lighting, backgrounds, containers, distances, and difficult non-pepper materials; include a genuinely untouched negative and valid-pepper test.
2. Add semantic near-duplicate checks and source-family analysis, then report rejection confidence intervals rather than a point estimate alone.
3. Obtain an independently reviewed grading reference, ideally tied to measurable quality attributes, before making any official-grade claim.
4. Calibrate abstention/confidence and explicitly test mixed samples, partial pepper, blur, low light, occlusion, tiny pepper regions, and adversarial vegetation.
5. Accumulate future EAC observations without retuning the frozen Phase 5 specification, and repeat the external comparison after a materially larger period.
6. Evaluate fixed-calendar horizons only through a separately documented treatment of irregular observations and missingness.
7. Add justified exogenous features only when their publication timing and historical availability can be proven leakage-free.
8. Design any future grading-plus-price decision experiment so that dated reference price, forecast uncertainty, persistence, grading uncertainty, and human override remain visible.

## 10. Principal artifacts

### Research records

- `docs/research/V3_DECISION_RECORD.md`
- `docs/research/V3_PHASE1_AUDIT.md`
- `docs/research/V3_PHASE2_YOLO_RESULTS.md`
- `docs/research/V3_PHASE3_REJECTION_RESULTS.md`
- `docs/research/V3_PHASE3_FOLLOWUP_REJECTION_RESULTS.md`
- `docs/research/PHASE4_PRICE_DATA_AUDIT.md`
- `docs/research/PHASE4_PRICE_FOUNDATION_RESULTS.md`
- `docs/research/PHASE5_PRICE_FORECASTING_RESULTS.md`
- `docs/research/EXPERIMENT_LOG.md`

### Major data/model locations

- `data/processed/grading_forecast/berry_v3/`
- `ml/grading_forecast/berry_grading/models/v3_yolo/`
- `ml/grading_forecast/berry_grading/models/v3_yolo_phase3_followup/`
- `ml/grading_forecast/berry_grading/evaluation/v3_yolo/`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3/`
- `ml/grading_forecast/berry_grading/evaluation/v3_phase3_followup/`
- `data/processed/grading_forecast/price/eac_reconstructed_v1/`
- `ml/grading_forecast/price_forecasting/phase4/`
- `ml/grading_forecast/price_forecasting/phase5/`

## 11. Evidence boundary at report preparation

At preparation time, Git reported no staged or unstaged tracked changes after HEAD `39592c6`. Git did emit access warnings for local test/temporary directories, so this statement applies to the tracked and accessible working-tree paths reported by Git. The numerical results in this report are taken from the committed experiment reports and their recorded machine-readable artifacts; this report does not claim that the full training and acquisition workflows were rerun during report preparation.
