# Pending Work Plan — Berry Grading & Price Forecasting

## Overall objective

Bring your already-trained research models into the actual application, make the backend use the correct research artifacts, verify the decision-support logic, harden the backend, and then manually integrate/test the remaining application-level pieces.

```text
PHASE 7
Existing Implementation Audit
        ↓
PHASE 8
Berry V2 Runtime Integration
        ↓
PHASE 9
Price Forecasting Runtime Integration
        ↓
PHASE 10
Recommendation & Decision Logic
        ↓
PHASE 11
Backend Reliability & Error Handling
        ↓
PHASE 12
Firebase / Persistence
        ↓
PHASE 13
Manual Cross-Component Integration
        ↓
PHASE 14
Manual Flutter E2E Validation
        ↓
PHASE 15
UI/UX Improvement
        ↓
PHASE 16
Final Component Validation & Documentation
```

I would use this order.

---

# Phase 7 — Existing Implementation Audit

Status: COMPLETE

### Objective

Understand exactly how your current component works before changing anything.

### Why first?

You already tested the application and it works technically, but the runtime is using:

* legacy berry model
* `demo_baseline` forecasting

So we need to know **where those are selected and loaded**.

### Tasks

Inspect:

* FastAPI routes
* FastAPI request/response schemas
* grading service
* forecasting service
* model loading code
* inference code
* recommendation logic
* Firebase/storage code
* configuration/environment variables
* Flutter API service
* existing grading/forecast screens

Trace:

```text
Flutter
  ↓
API request
  ↓
FastAPI route
  ↓
Service
  ↓
Berry model
  ↓
Forecast
  ↓
Recommendation
  ↓
Storage
  ↓
API response
  ↓
Flutter
```

### Deliverable

Create a short implementation map:

| Area | Current implementation | Required implementation | Status |
| --- | --- | --- | --- |
| Berry model | At Phase 7 audit time, runtime used legacy/root ONNX: `ml/grading_forecast/berry_grading/models/berry_mobilenetv2_best.onnx` | Integrate selected V2 ONNX if required for final runtime | Completed in Phase 8 |
| Berry V2 research artifact | V2 ONNX exists separately: `ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx` | Keep distinct from runtime until integration is intentionally performed | Verified |
| Forecast | Runtime now uses `naive_persistence` with `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv` | Keep forecasting decision documented; validate recommendation using real outputs next | Completed in Phase 9 |
| Forecast V2 research artifacts | V2 RF and Phase 4 RF artifacts exist separately under `models/v2/` and `models/v2_phase4/` | Do not claim runtime use until wired and validated | Verified |
| Strongest research forecast | Naive Persistence is strongest on the V2 test period | Runtime selected Naive Persistence after requirement check | Completed in Phase 9 |
| Recommendation | Existing rule logic is implemented and validated with Phase 8/9 runtime outputs | Continue to backend hardening and later full E2E checks | Completed in Phase 10 |
| Storage | Firebase storage is implemented as required result-history persistence, with fail-safe behavior when credentials are unavailable | Live Firebase validation still requires configured credentials | Completed in Phase 12; live write not validated |
| API | Existing endpoints and fallback/error behavior identified | Harden only after model/runtime decisions | Completed in Phase 11 |
| Flutter | API service and relevant screens exist | End-to-end Flutter validation still pending | Pending Phase 14 |

### Validation

Phase 7 was completed as an audit-only pass. No application code, model artifacts, datasets, backend configuration, or Flutter files were changed.

This phase should be cheap and should prevent unnecessary Codex work.

---

# Phase 8 — Berry V2 Runtime Integration

Status: COMPLETE

### Objective

Make the actual application use your **selected PP2 berry model**.

Your selected model is:

```text
BERRY-V2-MNV2
```

Artifact:

```text
ml/grading_forecast/berry_grading/models/v2/
    berry_mobilenetv2_v2_best.onnx
```

### Tasks

1. Identify current legacy model-loading code.
2. Change the PP2 runtime path to V2.
3. Load the correct:

   * ONNX model
   * class names
   * metadata if required.
4. Prevent accidental use of the legacy model.
5. Preserve existing API contract unless a change is genuinely necessary.
6. Ensure inference preprocessing matches the training pipeline:

   * 224×224
   * RGB
   * MobileNetV2 preprocessing
   * correct class ordering.

### Critical validation

Use one or more known images from:

```text
berry_split_v2/test
```

and verify:

```text
Image
 ↓
Backend
 ↓
V2 ONNX
 ↓
Prediction
```

The response should identify the **V2 runtime model**, not the legacy artifact.

### Completion criteria

You can demonstrate:

> "The backend is using the PP2 V2 MobileNetV2 artifact."

### Phase 8 completion evidence

Runtime berry grading now resolves the selected PP2 model:

```text
BERRY-V2-MNV2
ml/grading_forecast/berry_grading/models/v2/berry_mobilenetv2_v2_best.onnx
```

Validation used one existing V2 test image:

```text
data/processed/grading_forecast/berry_split_v2/test/grade_1/sample_002/20260508_152537.jpg
```

Service-level runtime validation returned a valid prediction and identified `BERRY-V2-MNV2` with the V2 ONNX path in the grading explanation. The legacy/root ONNX filename is no longer selected by the berry grading service. No dataset, model artifact, forecasting code, Firebase code, Flutter code, or recommendation logic was changed during Phase 8.

---

# Phase 9 — Price Forecasting Runtime Integration

Status: COMPLETE

### Objective

Remove the `demo_baseline` runtime behavior and connect the application to your actual forecasting methodology.

This phase requires an important research/engineering decision.

Your results are:

```text
Naive Persistence
MAE = 16.4094
R² = 0.9045
```

versus:

```text
Random Forest
MAE = 82.4179
R² = -0.4736
```

and:

```text
Extended-Lag Random Forest
MAE = 78.1641
R² = -0.3566
```

Therefore **Naive Persistence is your strongest current forecasting method**.

### Recommended implementation

Use:

```text
Latest available price
        ↓
Naive Persistence
        ↓
Next-period predicted price
```

rather than forcing Random Forest into the application merely because it is a trained ML model.

However, there is one thing to check against your official project/TAF requirements:

> If the final project explicitly requires the application itself to use a trained ML forecasting model, then you may need to use the Random Forest artifact despite Naive Persistence being the stronger benchmark.

So **Phase 9 should begin by checking that requirement**, rather than making an assumption.

### Tasks

* Remove/disable `demo_baseline` for the real application path.
* Implement the selected forecasting method.
* Load the correct V2 data/artifact if applicable.
* Make forecast output deterministic and reproducible.
* Return:

  * current/latest price
  * predicted price
  * trend/direction if already part of your design
  * forecasting method/model identifier.

### Completion criteria

The API no longer returns:

```text
demo_baseline
```

for the real application flow.

It returns a genuine research-backed forecast.

### Phase 9 completion evidence

Requirement decision:

The checked project documents require short-term price forecasting using machine-learning/time-series techniques, but no inspected requirement explicitly forced the application runtime to use a trained RandomForest artifact when a validated time-series baseline performs better. Naive Persistence was selected because it is the strongest validated forecasting method on the V2 test period.

Runtime forecast configuration:

```text
Method: naive_persistence
Target data: data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv
Metrics source: ml/grading_forecast/price_forecasting/models/v2/naive_persistence_metrics.json
```

Focused service-level validation returned:

```text
model: naive_persistence
current_price_lkr_per_kg: 1886
predicted_price_lkr_per_kg: 1886
trend: stable
metrics.mae: 16.4094
metrics.rmse: 22.5208
deterministic repeat: true
```

Missing-file validation returned `model: forecast_unavailable` instead of fabricated demo values. The real application forecasting path no longer returns `demo_baseline`. No berry grading, recommendation-rule, Firebase, Flutter, dataset, training, evaluation, or model-artifact changes were made during Phase 9.

---

# Phase 10 — Recommendation & Decision Logic

Status: COMPLETE

### Objective

Ensure the final recommendation is based on **real grading + real forecasting outputs**.

Your component's actual purpose isn't just:

```text
Image → Grade
```

or:

```text
Price → Forecast
```

It is:

```text
Berry Grade
      +
Price Forecast
      ↓
Decision Support
      ↓
Sell / Wait / Process
```

### Tasks

Audit the existing recommendation logic.

Determine:

* What inputs does it use?
* Is it using the actual predicted grade?
* Is it using the actual forecast?
* Does it use fallback/demo values?
* Are thresholds hard-coded?
* Are edge cases handled?
* Are recommendation rules consistent with your project's existing requirements?

### Important

**Don't invent new recommendation rules during this phase.**

First preserve the rules already defined in your project.

If the existing rules are incomplete or ambiguous, identify that explicitly.

### Test cases

Create representative cases such as:

```text
Grade 1 + favorable price trend
Grade 1 + unfavorable price trend
Grade 2 + favorable trend
Grade 2 + unfavorable trend
Grade 3 + favorable trend
Grade 3 + unfavorable trend
```

Then verify the recommendation.

### Completion criteria

You can explain:

> "The recommendation is generated from the actual grading and forecasting outputs."

### Phase 10 completion evidence

Recommendation service:

```text
backend/app/services/grading_forecast/recommendation_service.py
```

The `analyze` route passes `grading.predicted_grade`, `grading.quality_score`, `forecast.trend`, `forecast.current_price_lkr_per_kg`, and `forecast.predicted_price_lkr_per_kg` into the existing recommendation logic.

Focused validation confirmed:

```text
BERRY-V2-MNV2 -> Grade 1 / quality score 82.3
naive_persistence -> current 1886 / predicted 1886 / stable
recommendation -> SELL_EXPORT
```

Representative rule checks passed for Grade 1/2/3 with upward and downward trends, stable trend, missing optional quality/price fields, and invalid schema values. Invalid grade values are rejected by the API schema before reaching the service. No recommendation business rules were changed during Phase 10.

---

# Phase 11 — Backend Reliability & Error Handling

Status: COMPLETE

### Objective

Make your component robust enough for real application usage.

This is separate from model accuracy.

### Handle

#### Image errors

* missing image
* invalid format
* corrupted image
* excessively large image
* unreadable image

#### Model errors

* model file missing
* model cannot load
* inference failure
* invalid class mapping

#### Forecast errors

* insufficient historical data
* malformed price data
* missing latest observation
* invalid prediction

#### API errors

* malformed request
* timeout
* internal exception
* dependency failure

### Important rule

Do **not** silently fall back to demo/heuristic behavior if the final application is supposed to show research results.

A dangerous situation is:

```text
V2 model unavailable
       ↓
silently use legacy/demo model
       ↓
user sees result
```

That makes evaluation difficult and can produce misleading research evidence.

Prefer an explicit error or clearly labeled fallback.

### Completion criteria

The backend fails **safely and transparently**.

### Phase 11 completion evidence

Backend reliability hardening was completed for the grading-forecast API path.

Files changed:

```text
backend/app/api/routes/grading_forecast.py
backend/app/services/grading_forecast/grading_service.py
```

Validated behavior:

* Valid V2 grading uses `BERRY-V2-MNV2` and does not expose an absolute model path to the client.
* Valid forecasting uses `naive_persistence` with real V2 price data and does not return `demo_baseline`.
* Valid analyze combines V2 grading, `naive_persistence` forecasting, existing recommendation rules, and optional storage.
* Missing, empty, unsupported, corrupt, and oversized image uploads return safe HTTP errors.
* Corrective validation on 2026-08-30 fixed a Flutter multipart compatibility defect: valid JPEG/PNG/WEBP bytes are now accepted even when the client MIME value is missing or `application/octet-stream`; Pillow byte validation remains authoritative and the 10 MB limit remains enforced.
* Missing V2 model artifacts raise explicit grading failure and do not load the legacy/root ONNX model.
* Missing or malformed forecast data returns `forecast_unavailable` instead of fabricated prices.
* Invalid recommendation schema values return FastAPI/Pydantic validation errors.
* Unexpected grading or recommendation service failures return safe JSON errors without client-facing stack traces.

No datasets, model artifacts, Flutter code, Firebase configuration, recommendation rules, or forecasting method selection were changed during Phase 11 or its corrective upload-validation fix.

---

# Phase 12 — Firebase / Persistence

Status: COMPLETE

### Objective

Decide and implement the required storage behavior.

Current state:

```text
Firebase not configured
saved_to_firebase: false
```

### First task

Determine whether Firebase storage is:

**A. Required final functionality**

or

**B. Optional supporting functionality**

If required:

1. Configure credentials securely.
2. Configure environment variables.
3. Test save operation.
4. Test retrieval if applicable.
5. Verify stored result structure.
6. Verify failures don't crash analysis.

If optional:

> Document it as optional and don't spend significant time on it before the core model/runtime integration.

### Phase 12 implementation and validation

Decision: **REQUIRED FINAL FUNCTIONALITY** for application-level result history, based on the updated Phase 12 requirement and project/proposal persistence expectation.

Evidence:

* Existing component code already used `backend/app/services/grading_forecast/result_storage_service.py` and `backend/app/db/firebase.py`.
* `docs/guidelines_with_steps.md` identifies Firebase result storage as part of the component while also saying Firebase credentials must not be required for the local demo.
* The current implementation therefore treats Firebase as required persistence functionality when credentials are configured, but non-blocking for live grading/forecast/recommendation output when credentials are absent.

Implementation:

* Each successful persisted analysis uses a generated Firestore document ID and `analysis_id`.
* Collection: `grading_forecast_results`, or `FIREBASE_RESULTS_COLLECTION` if configured.
* Persisted records include application-level metadata, image identifier, V2 grading result, `naive_persistence` forecast result, recommendation result, runtime identifiers, and timestamp.
* Current records are application-level/non-user-scoped because no existing authenticated user identity was found for this component.
* No raw image bytes, model binaries, credentials, or secrets are stored.
* No Firebase credentials were configured, invented, or committed.

Validated behavior:

* With Firebase unconfigured, `/api/v1/grading-forecast/analyze` still returned valid V2 grading, `naive_persistence` forecast, recommendation, and `saved_to_firebase: false`.
* With a simulated Firebase save failure, analyze still returned valid grading/forecast/recommendation and `saved_to_firebase: false`, `document_id: null`.
* A mocked successful Firebase save returned `saved_to_firebase: true` and a generated document ID.
* A mocked successful save writes metadata/results to `grading_forecast_results`; no raw image bytes are stored by the current component code.
* Firebase initialization failure and document serialization failure safely returned non-persisted status without breaking the analysis result.
* Environment variables checked by code are `FIREBASE_SERVICE_ACCOUNT_PATH`, `FIREBASE_PROJECT_ID`, and optional `FIREBASE_RESULTS_COLLECTION`.
* Retrieval is not implemented or required by the inspected component requirements.
* Live Firebase write validation was not performed because credentials are not configured in the environment.

### Security

Never hard-code:

* service account keys
* Firebase secrets
* credentials

into the repository.

---

# Phase 12.5 — Runtime Diagnostic Validation

Status: COMPLETE

This diagnostic phase was triggered by manual application testing that showed suspicious berry predictions and identical price forecasts across different berry grades. No application code, Flutter code, datasets, model artifacts, preprocessing, class mappings, forecasting logic, recommendation rules, or Firebase code were changed.

Findings:

* Direct ONNX inference and backend service inference agreed on all 9 selected V2 test images, so no direct ONNX-vs-backend class mapping disagreement was confirmed.
* The 9-image diagnostic sample was 6/9 correct: Grade 1 = 3/3, Grade 2 = 0/3, Grade 3 = 3/3. This is diagnostic only and does not replace the saved full-test metrics.
* Class order is Grade 1, Grade 2, Grade 3.
* ONNX input is float tensor `image` with shape `[None, 224, 224, 3]`; output is `probs` with shape `[None, 3]`.
* Confirmed issue for later review: training used direct Keras resize to 224x224, while backend runtime uses RGB letterbox to 224x224 before ONNX inference.
* ONNX graph contains arithmetic preprocessing operations, so runtime supplies raw 0..255 float32 RGB input.
* Forecast runtime uses one National Grade 1 average weekly target from `data/processed/grading_forecast/price_v2/national_grade1_average_weekly.csv`.
* Latest observed runtime price was 2026-08-18, 1886.14 LKR/kg, rounded to `1886`; `naive_persistence` predicts `1886` with stable trend.
* Identical forecasts across berry grades are expected under the current single-series runtime design.
* Incorrect berry grading can propagate into recommendation output because recommendation consumes the actual runtime grade.

Recommended next implementation review:

* Decide whether runtime berry preprocessing should match training-time direct resize or whether the model should be retrained/exported with letterbox preprocessing.
* Decide in a later forecasting phase whether grade-specific price forecasting is required; do not change the current single-series `naive_persistence` runtime without a documented design decision.

---

# Phase 13 — Manual Cross-Component Integration

**You said you will do this manually later.**

So this phase is intentionally outside the immediate Codex work.

### Objective

Integrate your completed component with the other members' components.

Verify:

```text
Other component
      ↓
Shared backend
      ↓
Your grading/forecasting
      ↓
Recommendation
```

Check:

* API contracts
* DTOs
* endpoint paths
* authentication
* response structures
* database/storage dependencies
* error handling
* naming consistency

### Completion criteria

Your component works with the **actual integrated project**, not only in isolation.

---

# Phase 14 — Manual Flutter End-to-End Validation

Again, you will handle this manually.

### Objective

Validate the complete real-world flow.

```text
Flutter
   ↓
Select/capture image
   ↓
Upload
   ↓
FastAPI
   ↓
V2 Berry Model
   ↓
Forecast
   ↓
Recommendation
   ↓
Response
   ↓
Flutter
```

Test:

* successful analysis
* invalid image
* slow network
* backend unavailable
* retry
* different berry grades
* forecast response
* recommendation response

### Important

Compare:

**Backend response**

against

**Flutter displayed result**

to ensure the UI isn't transforming values incorrectly.

---

# Phase 15 — UI/UX Improvement

Do this **after the backend is stable**.

Otherwise you're polishing a broken pipeline.

### Main screens

#### 1. Input

* camera/gallery
* image preview
* clear image
* analyze button
* validation

#### 2. Processing

Show:

> Analyzing berry quality...

rather than leaving the user wondering whether the application is frozen.

#### 3. Results

Display:

```text
Berry Grade
Grade 2

Price Forecast
Current: Rs. XXXX/kg
Forecast: Rs. XXXX/kg

Trend
Increasing / Decreasing / Stable

Recommendation
WAIT
```

Use the existing project design system rather than unnecessarily redesigning everything.

#### 4. Error state

Provide:

> Analysis failed. Please try again.

instead of a raw exception.

### Completion criteria

A user can understand:

1. What grade was predicted?
2. What price is expected?
3. What should they do?
4. Why was that recommendation given?

---

# Phase 16 — Final Component Validation

This is your final gate.

## Berry grading

Verify:

* V2 model is actually loaded.
* Correct preprocessing.
* Correct class mapping.
* Multiple images tested.
* Predictions returned successfully.
* No unintended legacy fallback.
* Inference latency recorded if useful.

## Forecasting

Verify:

* No `demo_baseline`.
* Correct forecasting method.
* Correct input data.
* Prediction generated successfully.
* Trend calculation works.
* No future-data leakage in runtime.

## Recommendation

Verify:

* Real grade used.
* Real forecast used.
* Correct rule applied.
* Edge cases handled.

## Backend

Verify:

* endpoints
* validation
* errors
* model loading
* response schema

## Firebase

If required:

* save
* retrieve/verify
* failure handling

## Flutter

You will manually verify:

* API call
* loading
* results
* errors
* retry
* UI consistency

---

# The phases you should give Codex

Since you specifically want to **save tokens/credits**, I would **not give Codex all 10 phases at once**.

Use it incrementally.

### Codex Task 1

**Phase 7 — Audit only**

> Inspect the existing FastAPI and Flutter implementation for the berry grading and price forecasting component. Trace the complete request flow, identify the current berry model-loading path, current forecasting implementation, recommendation logic, Firebase/storage behavior, and relevant configuration. Compare the current implementation against the PP2 research artifacts documented in `docs/research/EXPERIMENT_LOG.md`, `PROJECT_STATUS.md`, and `PP2_LIMITATIONS.md`. Do not modify any files. Do not train models. Do not run the project. Do not modify datasets. Return a concise file-by-file implementation map and identify exactly what must change to make the application use the selected PP2 research artifacts.

That's the **only task I'd run first**.

Then:

### Codex Task 2

Phase 8 — Berry runtime.

### Codex Task 3

Phase 9 — Forecast runtime.

### Codex Task 4

Phase 10 — Recommendation audit/fix.

### Codex Task 5

Phase 11 — Error handling/hardening.

### Codex Task 6

Phase 12 — Firebase, **only if required**.

Then **you manually handle**:

```text
Phase 13 → Cross-component integration
Phase 14 → Flutter E2E
Phase 15 → UI/UX
```

Finally:

```text
Phase 16 → Final validation
```

---

# Your current status in one table

| Phase  | Work                             | Status                      |
| ------ | -------------------------------- | --------------------------- |
| 1      | Dataset V2                       | ✅ Complete                  |
| 2      | Berry V2 model                   | ✅ Complete                  |
| 3      | Forecasting V2                   | ✅ Complete                  |
| 4      | Limited improvements             | ✅ Complete                  |
| 5      | Initial integration validation   | ✅ Complete with limitations |
| 6      | PP2 documentation                | ✅ Complete                  |
| **7**  | **Implementation audit**         | ✅ Complete                  |
| **8**  | **Berry V2 runtime integration** | ✅ Complete                  |
| **9**  | **Forecast runtime integration** | ✅ Complete                  |
| **10** | **Recommendation verification**  | ✅ Complete                  |
| **11** | **Backend error handling**       | ✅ Complete                  |
| **12** | **Firebase**                     | ✅ Implementation complete; live write not validated |
| **13** | **Other-component integration**  | 🔵 You will do manually     |
| **14** | **Flutter E2E**                  | 🔵 You will do manually     |
| **15** | **UI/UX**                        | 🔵 You will do manually     |
| **16** | **Final validation**             | ⏳ After everything          |
