# Mobile Farmer UI/UX Refinement Results

Date: 2026-10-08
Status: **IMPLEMENTED; MANUAL DEVICE ACCEPTANCE PENDING**

## 1. Objective

Refine the integrated Flutter application into a consistent, farmer-first
experience without changing any detector, preprocessing step, threshold,
backend contract, Phase 6 decision rule, Phase 7 grading/forecast behavior, or
price route. This work changes presentation and navigation only.

## 2. Pre-implementation analysis

The inspected application used route-based navigation from `HomeScreen` after
first-run language selection. Pest and leaf checks shared the plant-health
scanner, berry disease used its dedicated scanner, and all three entered through
an explanatory action sheet. Berry grading instead opened an additional landing
page before capture.

The dashboard repeated the Pepper Care identity, displayed static farm-status
and recent-result content, exposed a redundant Take Photo action, and used a
Home/Capture/History bar in which Capture duplicated contextual capture and
History did not render a real destination. Grading and price result pages also
gave internal research fields the same visual importance as the farmer's result.

Reusable foundations already existed in `AppTheme`, `ScannerView`,
`ScanResultView`, the recommendation presentation widgets, and generated
English/Sinhala/Tamil localization. Those foundations were retained and extended
instead of introducing a second application shell.

## 3. Navigation and dashboard

The dashboard now has one application header and four task cards:

- Pest Detection
- Leaf Health
- Berry Disease Detection
- Berry Grading and Price Outlook

Every card opens the same reusable feature-introduction sheet. The grading card
starts `BerryCaptureScreen` directly after its sheet; the obsolete grading
landing screen and its normal route were removed.

The standalone Take Photo action, fabricated farm status, mock recent results,
and Capture navigation item were removed. The bottom navigation is now:

- Home: four contextual agricultural tasks;
- History: an honest empty state until real persistence is implemented;
- Guide: practical berry photo, grade, price-outlook, retry, and limitation
  guidance.

Capture remains contextual to the chosen task. Focused scanner and result pages
retain normal back navigation. Grading and price result pages also provide an
explicit Home action.

## 4. Shared design language

`farmer_ui.dart` provides reusable section headers, notices, empty states,
feature sheets, guide steps, and safe return-to-home navigation. Theme updates
standardize button sizes, card radii, bottom sheets, navigation, surface colors,
and light/dark presentation.

Pest, leaf, berry-disease, and grading entry points now share the same card,
sheet, button, spacing, and page-header language while retaining their
domain-specific scanner and result content. Detector class identifiers remain
unchanged internally; recognized class labels are localized only for display.
Raw model paths and provider/runtime errors are not exposed in the normal
scanner UI.

## 5. Farmer-facing grading result

The accepted result is led by **Berry Grade 1** or **Berry Grade 2**, followed by
a short explanation and a plain notice that the project result is not an
official certification. A single primary action opens the price outlook when
and only when the parsed market object is available.

Rejection and grade uncertainty retain the backend decision exactly but are
presented as an understandable retry state. `UNCERTAIN_GRADE` continues to block
all price output and is not confused with an accepted grade whose price outlook
has high uncertainty.

The normal UI no longer displays the technical grading table, V3/Phase labels,
quality-gate internals, calibration wording, raw rejection identifiers, or
research trace. Those fields remain unchanged in the response model and API for
research and debugging.

## 6. Farmer-facing price outlook

The frozen forecast price is the single dominant price and is labelled as an
estimated outlook. Direction is translated into plain language: expected to
rise, fall, or remain similar. High outlook uncertainty is explained separately
from grading uncertainty.

Grade, forecast date, and the latest EAC farm-gate reference price are compact
secondary context. Ridge, persistence comparison, raw interval bounds, internal
series identifiers, research trace, and Phase terminology are hidden from the
farmer UI but retained in the parsed API object. The page states that the value
is not a guaranteed buyer price or buying/selling instruction.

## 7. Guide, localization, accessibility, and responsiveness

The Guide destination and capture help sheet explain lighting, framing,
visibility, blur avoidance, project Grade 1/Grade 2 meaning, frozen price
outlook meaning, retry behavior, and limitations without ML terminology.

All new presentation text is available in English, Sinhala, and Tamil through
the existing generated localization architecture. The dashboard adapts to one
column below 340 logical pixels and otherwise uses two columns. Scrollable
pages/sheets, SafeArea use, flexible text, bounded card text, and minimum
52-pixel primary actions support small screens and longer localized strings.
Independent linguistic review and real-device large-text checks remain pending.

## 8. Preserved functionality and scientific boundary

Unchanged by this work:

- backend endpoints and response schemas;
- the strict Phase 7 response parser and local request validation;
- original-image grading upload behavior;
- ONNX and TFLite model files;
- grading and scanner preprocessing;
- model thresholds, NMS, and class vocabularies;
- Phase 6 categories, rejection-first behavior, and grade-specific routing;
- frozen Phase 5 records and forecast calculations;
- imported pest, leaf, and berry-disease scanner/recommendation behavior.

The API still contains the full scientific trace. Hiding it in the normal UI
does not delete or reinterpret it.

## 9. Automated verification

Executed from `mobile/`:

```powershell
& "C:\test-by-me\flutter\flutter\bin\flutter.bat" analyze
& "C:\test-by-me\flutter\flutter\bin\flutter.bat" test --concurrency=1 --reporter compact
```

Results:

- Flutter analyzer: **no issues found**.
- Flutter tests: **75/75 passed**.
- Covered dashboard/navigation, all four component routes, first-run locale,
  English/Sinhala/Tamil grading entry, farmer grading and price hierarchy,
  uncertainty price blocking, strict Phase 7 contracts, API-client validation,
  shared scanner result behavior, detector geometry, thresholds, and NMS.
- Repository diff check found no changed files under `backend/`,
  `ml/`, or `data/`.

An Android debug build configured with the hosted Railway URL reached Gradle but
did not complete or fail within the bounded run. It was stopped after remaining
silent; the pre-existing APK on disk predates this UI work and is not counted as
verification.

## 10. Remaining manual acceptance

Rebuild and test on an emulator and at least one physical Android phone:

1. verify first-run and later language changes in all three languages;
2. inspect small-screen, large-text, Sinhala, and Tamil overflow;
3. open all four feature sheets and their direct task routes;
4. exercise camera/gallery return and scanner instruction sheets;
5. confirm missing cloud keys fail safely for outsourced features;
6. rerun Phase 7 Grade 1, Grade 2, non-pepper, poor-image, and uncertain cases;
7. confirm rejected/uncertain grading never shows price output;
8. confirm result Back and Home actions are obvious and correct;
9. confirm the price screen emphasizes only the frozen forecast price while
   keeping its guarantee/trading disclaimer visible.

This UI work provides implementation and automated presentation-regression
evidence only. It does not establish field robustness, official grade
equivalence, calibrated confidence, forecast reliability, economic benefit, or
farmer usability. Those require separate prospective evaluation.
