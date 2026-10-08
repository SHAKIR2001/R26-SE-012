# Phase 7 — ONNX/TFLite + Backend/Mobile Results

**Status:** `COMPLETE WITH LIMITATIONS`
**Experiment:** `PHASE7-ONNX-BACKEND-MOBILE-001`  
**Date:** 2026-10-07

## 1. Phase 7 objective

Convert the frozen Phase 3 grading/rejection model and Phase 6 grade-price decision layer into an executable backend/mobile research pipeline without retraining, changing thresholds, inventing a price model checkpoint, or beginning Phase 8.

## 2. Implementation scope

Phase 7 implements a reproducible YOLO-to-ONNX export, ONNX Runtime backend grading, frozen Phase 5 record selection, authoritative Phase 6 fusion, a structured FastAPI response, and Flutter API consumption. The active path is backend inference. No application-wide redesign, deployment, field collection, or model training occurred.

## 3. Frozen artifacts used

- Phase 3 follow-up checkpoint SHA-256: `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca`.
- Frozen decision configuration SHA-256: `39ca99a7e0049fb620a141cde80d539700945b2f812cc6cf7b15f289f8e158b8`.
- Phase 4 canonical EAC dataset SHA-256: `ea800ea576817f07ad54d50317dbd68254fc5dc824447380e58688b6b711c0f6`.
- Phase 5 frozen external predictions SHA-256: `0b3e5a4ede8f6839f831f008a4655114413c6369a1b9549dca240cc685288c4a`.
- The Phase 6 configuration and four authoritative decision modules were hash-pinned and passed integrity validation.

## 4. Grading deployment strategy

The frozen YOLO11n detector is executed by ONNX Runtime on the backend. OpenCV decoding, Ultralytics-compatible letterboxing, RGB conversion, float32 `/255` normalization, and BCHW layout are preserved. The runtime then applies the unchanged minimum dimension, brightness, blur, detected-area, detection confidence, grade confidence, and class-margin rules from the frozen Phase 3 configuration.

## 5. ONNX export details

The source `.pt` was not overwritten. `best.onnx` is a 10,636,719-byte fixed-shape graph with NMS embedded:

- input: `images`, `[1,3,640,640]`;
- output: `output0`, `[1,300,6]` containing `x1,y1,x2,y2,confidence,class_id` rows;
- opset: 20;
- Ultralytics: 8.4.174;
- PyTorch: 2.14.1+cu130;
- ONNX: 1.23.2;
- ONNX SHA-256: `f8bb36b3ce9c354fd0707f555dbff88bc4f24606b4b93be99a74b03e6db54d38`.

The export was run twice after deterministic metadata normalization and reproduced the same SHA-256.

## 6. ONNX equivalence results

Five fixed cases covered Grade 1, Grade 2, non-pepper, poor quality, and uncertain grade. Tolerances were declared before evaluation: confidence absolute difference at most `0.0001` and original-image box-coordinate difference at most `1.0` pixel.

- model load and inference: PASS;
- cases passing numeric and decision checks: 5/5;
- class agreement: 5/5;
- decision agreement: 5/5;
- rejection agreement: 5/5;
- maximum confidence difference: `1.78813934326172e-07`;
- maximum box-coordinate difference: `0.000823974609375` pixel.

An initial run correctly failed because Pillow and OpenCV handled EXIF-oriented phone pixels differently. The deployed decoder was corrected to the frozen OpenCV path; tolerances were not loosened.

## 7. TFLite conversion result

V3 TFLite conversion was not attempted or claimed. The bundled mobile TFLite asset is an older three-class MobileNet model and is not equivalent to the frozen V3 YOLO detector. Forcing a cross-framework conversion would add an unverified preprocessing/postprocessing path. The legacy offline service now fails explicitly rather than using that model for Phase 7 decisions.

## 8. Selected mobile runtime

`BACKEND_ONNX_RUNTIME` was selected. ONNX Runtime Mobile was considered but not selected because the existing Flutter feature already has an HTTP boundary, while on-device execution would duplicate quality gates, NMS/postprocessing, frozen price evidence, and Phase 6 rules. Flutter consumes the backend response and does not claim local V3 inference.

## 9. Backend architecture

`POST /api/v1/grading-forecast/analyze` validates a JPEG, PNG, or WEBP upload; assigns a non-personal analysis UUID; runs the frozen ONNX grader; selects price evidence only for an accepted grade; calls Phase 6; and returns its structured result. Images are processed in memory and not logged or permanently stored by this path. Logs contain only analysis ID and final category.

The legacy `grade-only`, `price-forecast`, and `recommend` paths return HTTP 410. This prevents the older three-grade, Grade 2 discount, and trading-style recommendation behavior from bypassing Phase 7.

## 10. Price runtime strategy

Option A, `FROZEN_FORECAST_RECORD_SERVICE`, was selected. Phase 5 deliberately has no single serialized fitted checkpoint. The service selects the latest approved external forecast record for the exact routed grade and labels it as frozen evidence. It does not refit Ridge, imply live forecasting, discount Grade 1 to create Grade 2, interpolate prices, or fabricate a missing record.

## 11. Phase 6 integration

Phase 7 wraps the existing Phase 6 `grading_adapter`, `price_router`, `decision_rules`, and `decision_engine`. It does not reproduce or alter their categories. Multi-image support calls the Phase 6 sample aggregator and routes only an agreed accepted sample grade.

## 12. API contract

The stable response retains `grading`, `market`, `decision_support`, and `trace`, plus an explicit runtime block. Latest reference and frozen forecast prices have separate fields. Unavailable market fields remain null/unavailable. Scores are labelled as model scores, not calibrated probabilities.

## 13. Rejection/uncertainty behavior

`NO_PEPPER` and `POOR_IMAGE` produce `REJECT`. `UNCERTAIN_GRADE` and `CONFLICTING_SAMPLE_VIEWS` cannot select a price series. Missing price or forecast evidence fails closed through the existing Phase 6 categories. Controlled verification confirmed that all three non-accepted single-image cases stopped before pricing.

## 14. Mobile integration

Flutter now defaults to the API path and parses the Phase 6 schema. It presents loading, error, rejection, uncertainty, accepted grade, source-labelled reference price, frozen forecast, interval, persistence comparison, limitations, and research trace states. It no longer formats model score as a probability or displays sell/wait recommendations.

Focused Flutter analysis reported no issues and two response-parser tests passed. Eight focused backend/API tests passed. The original automated run did not complete an Android emulator execution.

On 2026-10-08, a researcher-operated emulator run exercised the five controlled files. The first run passed Grade 1, Grade 2, and non-pepper behavior, but the poor-image file became `NO_PEPPER` with a passed quality gate and the uncertainty file became an accepted Grade 2 with price output. Investigation found that the Flutter picker was resizing images to at most `1280x1280` and recompressing them at quality 75 before upload. That changed the pixels presented to the frozen quality, detection, and class-margin gates. The picker preprocessing was removed so the selected file bytes are passed through without application-requested resizing or recompression.

The researcher then rebuilt the client and reran all five cases. The corrected emulator path passed 5/5: Grade 1 and Grade 2 used their exact grade-specific price records, non-pepper and poor-image cases were rejected without pricing, and the uncertain case returned `UNCERTAIN_GRADE` without pricing. This closes the Phase 7 mobile preprocessing acceptance gate.

During the first Railway Linux deployment on 2026-10-08, rejected inputs worked but accepted grades returned HTTP 500 before pricing. The frozen Phase 5 CSV had been hash-pinned as Windows CRLF bytes; Git materialized the same tracked text with LF endings on Linux. Deployment now records and verifies a canonical LF-normalized text hash in addition to retaining the original raw frozen hash. This accepts only the same text across platform line-ending representations and still rejects content changes. Startup and `/ready` now validate both the ONNX runtime and frozen forecast source. Hosted accepted-grade verification remains required after redeployment; this correction does not alter forecast values or decision rules.

## 15. End-to-end verification

The backend-controlled five-case set produced:

| Role | Grading result | Price route | Final category |
|---|---|---|---|
| Grade 1 | `GRADE_1` | Grade 1 | `HIGH_UNCERTAINTY_OUTLOOK` |
| Grade 2 | `GRADE_2` | Grade 2 | `HIGH_UNCERTAINTY_OUTLOOK` |
| Non-pepper | `NO_PEPPER` | none | `REJECT` |
| Poor quality | `POOR_IMAGE` | none | `REJECT` |
| Uncertain | `UNCERTAIN_GRADE` | none | `UNCERTAIN_GRADE` |

The result was identical on a deterministic repeat. A real Grade 1 multipart API test also completed the backend path. This is controlled backend integration evidence, not an independent field test.

The first manual emulator pass, performed before removal of picker preprocessing, produced 3/5 expected outcomes:

| Role | Emulator result | Acceptance |
|---|---|---|
| Grade 1 | `GRADE_1`, Grade 1 evidence | PASS |
| Grade 2 | `GRADE_2`, Grade 2 evidence | PASS |
| Non-pepper | `NO_PEPPER`, no market output | PASS |
| Poor quality | `NO_PEPPER`, quality gate passed | FAIL: expected `POOR_IMAGE` |
| Uncertain | accepted `GRADE_2` with market output | FAIL: expected `UNCERTAIN_GRADE` |

`UNCERTAIN_GRADE` is a grading stop state and is not equivalent to `HIGH_UNCERTAINTY_OUTLOOK`, which is a price-outlook category after an accepted grade. Passing all five cases was the condition for Phase 7 final mobile acceptance; the corrected rerun below satisfied it.

The corrected researcher-operated emulator rerun produced:

| Role | Corrected emulator result | Market behavior | Acceptance |
|---|---|---|---|
| Grade 1 | `GRADE_1`, score `0.9238`, quality passed | Grade 1 evidence only | PASS |
| Grade 2 | `GRADE_2`, score `0.9046`, quality passed | Grade 2 evidence only | PASS |
| Non-pepper | `NO_PEPPER`, score `0.0000`, quality passed | no market output | PASS |
| Poor quality | `POOR_IMAGE`, score `0.0000`, quality failed, `blur_variance_below_minimum` | no market output | PASS |
| Uncertain | `UNCERTAIN_GRADE`, score `0.7011`, quality passed, `grade_margin_below_minimum` | no market output | PASS |

The corrected emulator result is 5/5 and agrees with the frozen decision-level expectations. Scores displayed by the client remain model scores, not calibrated probabilities.

## 16. Integrity checks

Phase 7 integrity passed 22/22 checks. It verified frozen Phase 3, Phase 4, Phase 5, and Phase 6 hashes; ONNX graph/hash; `.pt` preservation; ONNX equivalence; exact routing; rejection-first behavior; deterministic output; frozen-record pricing; no false TFLite claim; and absence of hidden composite/trading logic in the integrated path.

## 17. Limitations

- Field, device, camera, lighting, and domain-shift performance remain unknown.
- Grading confidence is uncalibrated.
- V3 Grade 1/2 are project-specific, not official grades.
- Phase 5 forecasting evidence remains limited/mixed; persistence is a strong baseline.
- Grade 2 price performance is weaker and its intervals are much wider.
- Validation-derived intervals are uncertainty diagnostics, not guaranteed probability ranges.
- The runtime exposes frozen historical forecast records, not live prices or newly generated forecasts.
- The initial emulator run exposed client-side image mutation and passed only 3/5 controlled cases; the corrected full rerun passed 5/5.
- No physical-device test, independent end-to-end field dataset, user-usefulness study, or hosted deployment was completed.

## 18. What Phase 7 proves

It proves that the frozen grading model can be exported to ONNX with decision-level and strict numeric equivalence on the controlled set, and that the verified runtime can drive exact grade routing and the authoritative Phase 6 schema through FastAPI into Flutter code.

## 19. What Phase 7 does not prove

Successful integration does not imply field robustness, production-grade accuracy, official grade equivalence, reliable future price prediction, economic profitability, calibrated confidence, user usefulness, or safety of financial decisions. It creates deployment/integration evidence, not new predictive accuracy.

## 20. Phase 8 readiness

Phase 8 is `READY WITH LIMITATIONS` for separately authorized prospective field/domain-shift evaluation using the existing protocol. The Phase 7 mobile gate is closed by the corrected 5/5 emulator rerun. Phase 8 was not started and no field or internet-image validation claim was made.
