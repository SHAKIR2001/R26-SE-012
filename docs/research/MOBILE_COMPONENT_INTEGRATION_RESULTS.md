# Four-Component Mobile Integration Results

Date: 2026-10-08

## Objective

Integrate the separately supplied Pest Detection, Leaf Disease Detection, and
Berry Disease Detection Flutter implementation into the current application
without replacing or weakening the authoritative Phase 7 Berry Grading and
Export Price Forecasting workflow.

This is application integration evidence. It is not model training, predictive
evaluation, field validation, or a claim of production readiness.

## Source and authority boundary

The supplied `other members components - mobile` directory is a complete older
Flutter application rather than three isolated packages. Its pest, leaf, and
berry-disease code was treated as authoritative for those domains. The current
repository remained authoritative for:

- the application dashboard structure and theme;
- everything under `mobile/lib/features/grading_forecast/`;
- the Phase 7 FastAPI/ONNX integration and Phase 6 response contract;
- grading rejection, uncertainty, and exact grade-price routing;
- all frozen research artifacts and model binaries.

The imported grading/forecast screens, model, API client, Grade 3 behavior,
quality-score presentation, recommendation rules, and legacy price behavior
were not copied.

## Component inventory

Pest and leaf health use one combined `PlantHealthScannerScreen`, matching the
imported application's public entry point. It uses the shared `ScannerView`,
Gemini detection service, Claude crop refinement, and pest/leaf recommendation
screens. The cloud-failure path now runs both supplied local TFLite models
(`new_leaf_yolo_model_int8.tflite` and `new_pest_yolo_model_int8.tflite`) and
merges their detections. Berry disease uses the corresponding berry scanner and
berry recommendation flow through the same shared runtime.

The current Phase 7 grading feature continues to use its existing capture,
strict response model, API service, result screen, frozen forecast presentation,
and backend URL configuration.

## Conflicts resolved

- The imported screen styling was not used. Its combined Leaf & Pest entry was
  adapted into the current dashboard UI, alongside Berry Disease and the
  protected Berry Grading and Price Forecasting entry.
- The imported `berry_disease/screens` path was adapted to the existing
  `berry_disease/berry_scanner_screen.dart` path, avoiding duplicate screens.
- Imported background-isolate inference was retained on native targets. A
  direct-execution web fallback was added so the browser grading path continues
  to compile where worker-isolate/native-interpreter behavior differs.
- Imported on-demand recommendations replaced the older recommendation
  prefetch behavior for pest, leaf, and berry-disease scans.
- The imported Anthropic v7 client contract and `claude-haiku-4-5` selection
  were retained for the outsourced components.
- The current `ScannerModelConfig` safeguards, theme, Android SDK settings,
  broad asset declarations, and Phase 7 grading source were retained.
- Localization keys describing the legacy grader remain inert catalog entries;
  they were not attached to the current grading screens. A later scoped
  implementation added new Phase 7-specific English, Sinhala, and Tamil text
  while preserving the current scientific workflow and stable API values.

## Implemented integration

- Added persisted English, Sinhala, and Tamil language selection.
- Added localized shell labels, scanner instructions, progress states, safe
  errors, findings, class labels, and recommendation/result screens for the
  three imported domains.
- Kept scientific class identifiers and internal routing values in English;
  localization occurs only at presentation boundaries.
- Added background JPEG decoding, TFLite inference, exemplar preparation, and
  crop preparation for native mobile targets.
- Added imported Gemini structured-response handling and Claude crop refinement.
- Preserved safe TFLite fallback when cloud configuration is absent or fails.
  The combined plant scanner loads and runs both original leaf and pest models;
  it does not silently degrade to leaf-only classification.
- Added the imported source directory to `.gitignore`; it remains untouched as
  a local comparison source and is not part of the built app.

## Dependency and configuration changes

Flutter localization, `intl`, and `shared_preferences` were added.
`anthropic_sdk_dart` was updated to the imported v7 contract and the `image`
dependency was aligned with the imported runtime. Existing model/data/logo
asset declarations were preserved. Flutter regenerated the macOS plugin
registrant for `shared_preferences`; Android SDK settings were not changed.

The combined mobile runtime recognizes:

```text
PEPPER_API_BASE_URL
GEMINI_API_KEY
ANTHROPIC_API_KEY
```

Values are supplied through ignored build-time configuration. No `.env` file or
secret was copied, inspected, logged, or committed.

## Integrity evidence

The current and imported projects contained 37 overlapping pest/leaf/berry
model/reference assets, all byte-identical before integration. No asset was
replaced. Post-integration important hashes are:

| Artifact | SHA-256 |
|---|---|
| Frozen Phase 3 `best.pt` | `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca` |
| Phase 7 `best.onnx` | `f8bb36b3ce9c354fd0707f555dbff88bc4f24606b4b93be99a74b03e6db54d38` |
| Berry-disease TFLite | `48207a4189a4b33ea74e4669203b75d1d7295972f17129d677c3d4a9ac58fe1f` |
| Leaf TFLite | `285f31bd32094a21b4a7c86d90cadcff9c51f325bf1b58d31f599418d69beaf0` |
| Pest TFLite | `fa9e343a5d9df0799dc0e4c81391936ffe3d999240774d1678c29c7baa0886b9` |

At the time of the four-component merge, `git diff` reported no change under
`mobile/lib/features/grading_forecast/`. The later localization work changed
only Phase 7 presentation and safe mobile error classification; it did not
change the backend contract, models, thresholds, routes, or scientific rules.
Backend Phase 7 focused verification passed 15/15 tests after the original
mobile integration.

## Automated verification

- Direct Dart analysis of `mobile/lib` and `mobile/test`: no issues found.
- Focused Phase 7 backend/API/startup verification: 15 passed.
- Added locale persistence, localized class-label, four-component navigation,
  current Phase 7 route, and legacy Grade 3 absence checks.
- Existing YOLO geometry/NMS, overlay, scan-result, Phase 7 parser, and API tests
  remain in the suite.
- The later Phase 7 localization/API/contract suite passed 12/12 tests, and
  direct Dart analysis reported no issues.
- `flutter test` and the bounded debug APK build produced no output while local
  Flutter/Dart/Gradle processes remained occupied. Both were stopped; no test or
  build pass is claimed from those attempts.

## Manual acceptance still required

On an emulator or physical Android device:

1. verify first-launch and later language selection;
2. exercise camera/gallery pest, leaf, and berry-disease scans;
3. verify TFLite fallback without cloud keys;
4. verify authorized Gemini/Claude development-key behavior;
5. verify camera recovery after gallery/background transitions;
6. rerun the five established Phase 7 grading cases.

## Limitations

- Gemini and Anthropic keys embedded in an APK or browser bundle are
  recoverable. The current direct-provider design is suitable only for
  controlled development; public deployment requires a protected backend proxy.
- Direct provider behavior on Flutter web is not accepted by this integration.
- Device tests, live cloud calls, Flutter widget-test execution, and APK build
  completion are not claimed in this run.
- The localization has not received independent linguistic review.
- No component received new model training, predictive evaluation, calibration,
  domain-shift evidence, or field validation.

## Status

`IMPLEMENTED; STATIC AND BACKEND VERIFICATION PASSED; DEVICE/FLUTTER-RUNNER ACCEPTANCE PENDING`.

## 2026-10-15 outsourced-component update

### Purpose and authority

A newer copy of the outsourced Pest Detection, Leaf Disease Detection, and
Berry Disease Detection implementation was supplied in the ignored
`other members components - mobile` directory. The update was merged at the
inference and recommendation boundaries while the current application remained
authoritative for UI/UX, navigation, accessibility, localization, browser
compatibility, and Berry Grading and Export Price Forecasting.

No imported grading/forecast source, application shell, theme, platform
configuration, generated build output, cache, `.env`, or provider credential
was copied. The imported source directory remained untouched.

### Functional update

- TFLite and Gemini detection now execute concurrently, sharing one local-model
  future with Claude priors and the offline/failure fallback.
- Reference exemplars are prepared in advance and cached. Limits are 10 images
  per class for the combined plant scanner, 15 for standalone leaf/pest, and 6
  for berry disease.
- The supplied correction mapping Leaf Blight to `leaf/quick/` and Quick Wilt
  to `leaf/blight/` was retained because the imported project documents those
  source folders as mislabeled.
- The newer disease, pest, and berry prompts, crop limit, evidence-aware Claude
  refinement, reusable Anthropic client, 20-second timeout, and
  `claude-opus-5-5` selection were integrated.
- The optional Gemini/TFLite agreement gate remains disabled pending a labeled
  calibration study, exactly as supplied.
- Recommendation routing uses the strongest non-healthy detection. A leaf
  recommendation is anchored to the scanner's detected disease so the second
  analysis supplies severity and treatment without silently choosing a
  different disease.
- Native preprocessing continues off the UI isolate. The current direct web
  fallback was preserved instead of importing mobile-only isolate assumptions.

### Insufficient-evidence behavior

The supplied parser converted a positive Claude label with no cited visual
evidence to `None`. That could silently present a diseased or pest-affected
object as healthy. The integrated parser instead uses its existing
`Uncertain` verdict. A crop with missing or uncertain evidence is omitted from
the refined detections; a healthy plant result is produced only when both plant
aspects explicitly return `None`.

The scanner result model has no separate public detection-row state for
`INSUFFICIENT_EVIDENCE`. Consequently, an abstained crop may produce no finding
rather than a dedicated uncertainty card. This interface limitation is recorded
instead of changing the shared result schema or fabricating a healthy label.

### Reference assets and integrity

Only JPG/JPEG/PNG reference exemplars were copied from the supplied source:

- 209 imported reference images were reproduced byte-for-byte in the current
  asset tree;
- 183 were new paths and 26 replaced older same-path references;
- six current-only PNG reference variants were retained;
- the resulting 215 reference images occupy approximately 44.95 MB before APK
  packaging;
- `.DS_Store`, `.env`, `models.zip`, caches, Pods, and build output were excluded.

The three outsourced TFLite binaries were already identical and were not
replaced. Post-update protected hashes remain:

| Artifact | SHA-256 |
|---|---|
| Frozen Phase 3 `best.pt` | `e825278e0cf8eaff64cd05a2941cf96794e573027823a0ccd308bbc3f1a418ca` |
| Phase 7 `best.onnx` | `f8bb36b3ce9c354fd0707f555dbff88bc4f24606b4b93be99a74b03e6db54d38` |
| Berry grading MobileNet TFLite | `b0885ea82136718312549dbea4a5ec19908433bf61d3ad79d67f68f45752c90b` |
| Berry-disease TFLite | `48207a4189a4b33ea74e4669203b75d1d7295972f17129d677c3d4a9ac58fe1f` |
| Leaf TFLite | `285f31bd32094a21b4a7c86d90cadcff9c51f325bf1b58d31f599418d69beaf0` |
| Pest TFLite | `fa9e343a5d9df0799dc0e4c81391936ffe3d999240774d1678c29c7baa0886b9` |

There is no diff under `backend/`, `ml/`, or
`mobile/lib/features/grading_forecast/`. Phase 6 rules, Phase 7 contracts,
thresholds, price evidence, ONNX inference, and five-case grading expectations
remain outside this update.

### Verification

- Direct Dart analysis and official `flutter analyze`: no issues.
- New outsourced-update tests: 5/5 passed.
- Focused scanner/navigation/Phase 7 tests: 56/56 passed.
- Complete Flutter suite after regenerating Dart localization output from the
  existing ARB catalogs: 80/80 passed.
- The unchanged focused Phase 7 backend integration suite: 11/11 passed.
- Localization generation corrected a previously stale Sinhala generated file;
  no ARB catalog or localization interface was changed.
- Android debug build without API keys entered Gradle but produced no completion
  or error within the bounded run and was stopped. No APK-build pass is claimed.

### Remaining manual verification and risk

- Exercise pest, leaf, and berry camera/gallery paths on an emulator and a
  physical Android device, with and without authorized development keys.
- Confirm reference warm-up, camera lifecycle recovery, fallback behavior,
  recommendation routing, and long Sinhala/Tamil layouts on-device.
- Rerun the established five Phase 7 grading cases to provide device-level
  regression evidence after packaging the combined app.
- Gemini/Anthropic behavior and the supplied Opus model identifier require live
  provider verification. Automated tests do not establish cloud accuracy.
- Client-embedded provider keys remain recoverable and are suitable only for
  controlled development builds; public distribution requires a protected
  server-side provider proxy.

Updated status:

`IMPLEMENTED; STATIC AND FLUTTER TEST VERIFICATION PASSED; ANDROID BUILD AND LIVE DEVICE/CLOUD ACCEPTANCE PENDING`.

## Pest recommendation consistency correction (2026-10-18)

The Pest recommendation flow now follows the same trusted-result handoff used
by Leaf Health. When the scanner has a normal-confidence pest result, its class
is supplied to the detailed Gemini analysis. The second analysis remains
responsible for confirming the pepper plant and describing count, affected
plant part, severity, visible damage, and treatment context, but it cannot
silently replace the scanner's pest class with another species.

The handoff is deliberately fail closed:

- a normal-confidence `Pterolopha annulata` result remains Pterolopha throughout
  recommendation generation, even if the detail response names another pest;
- a relaxed low-confidence fallback result is not treated as a trusted class;
- a trusted positive detection followed by a healthy, empty, or inconclusive
  detail response becomes an explicit uncertain result;
- uncertain results ask for a clearer photograph or expert inspection and do
  not present chemical treatment instructions; and
- non-pepper results remain non-target results and are never overridden by the
  scanner class.

No pest model, threshold, preprocessing path, cloud provider, or treatment
calculation was changed. Offline dual-model Leaf Health & Pests detection is
also unchanged. Detailed recommendations still require the configured online
Gemini service.

Verification completed after this correction:

- localization generation passed;
- `flutter analyze` passed with no issues;
- 13/13 focused pest/fallback/component-integration tests passed;
- the complete Flutter suite passed 96/96; and
- the Android debug APK built successfully at
  `mobile/build/app/outputs/flutter-apk/app-debug.apk`.

The imported comparison project, Berry Disease, Berry Grading and Export Price
Forecasting, backend APIs, ML artifacts, Phase 6/7 behavior, and research data
were not modified. Live provider wording and the affected-pest image must still
be checked manually on an emulator or physical device; automated tests verify
the handoff and fail-closed reconciliation, not Gemini's real-world accuracy.
