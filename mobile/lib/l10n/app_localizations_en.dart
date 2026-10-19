// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Pepper Care';

  @override
  String get chooseLanguage => 'Choose your language';

  @override
  String get chooseLanguageSubtitle =>
      'You can change this anytime from the menu.';

  @override
  String get languageEnglish => 'English';

  @override
  String get languageSinhala => 'සිංහල';

  @override
  String get languageTamil => 'தமிழ்';

  @override
  String get language => 'Language';

  @override
  String get homeLeafPest => 'Leaf & Pest';

  @override
  String get homeBerryScan => 'Berry Scan';

  @override
  String get homeGradingForecast => 'Grading & Forecast';

  @override
  String get homePests => 'Pests';

  @override
  String get homeLeafHealth => 'Leaf Health';

  @override
  String get homeBerryDisease => 'Berry Disease';

  @override
  String get homeQualityPrice => 'Quality &\nPrice';

  @override
  String get lightMode => 'Light mode';

  @override
  String get darkMode => 'Dark mode';

  @override
  String get navHome => 'Home';

  @override
  String get navHistory => 'History';

  @override
  String get navGuide => 'Guide';

  @override
  String get homeWelcomeTitle => 'How can we help your crop today?';

  @override
  String get homeWelcomeSubtitle =>
      'Choose the task you need. We will guide you through the photo and results.';

  @override
  String get homeChooseTaskHint =>
      'Choose a task before taking a photo so the app can use the right crop check.';

  @override
  String get featurePlantHealth => 'Plant health';

  @override
  String get featurePlantTitle => 'Leaf Health & Pest Check';

  @override
  String get featurePlantCardDescription =>
      'Check for leaf disease and pepper pests';

  @override
  String get featurePlantDescription =>
      'Take a clear photo of a pepper leaf, stem or berry area to check for visible leaf disease and common pepper pests, then receive practical guidance.';

  @override
  String get featureBerryCare => 'Berry care';

  @override
  String get featureQualityAndPrice => 'Quality and price';

  @override
  String get featurePestTitle => 'Pest Detection';

  @override
  String get featurePestCardDescription => 'Check leaves, stems and berries';

  @override
  String get featurePestDescription =>
      'Take a clear photo to look for common pepper pests and receive practical treatment guidance.';

  @override
  String get featureLeafTitle => 'Leaf Health Check';

  @override
  String get featureLeafCardDescription => 'Look for leaf disease signs';

  @override
  String get featureLeafDescription =>
      'Photograph a pepper leaf to check for visible disease signs and understand how serious they may be.';

  @override
  String get featureBerryDiseaseTitle => 'Berry Disease Check';

  @override
  String get featureBerryDiseaseCardDescription =>
      'Inspect berry clusters for damage';

  @override
  String get featureBerryDiseaseDescription =>
      'Photograph a pepper berry cluster to check for visible disease or pest damage and receive care guidance.';

  @override
  String get featureGradingTitle => 'Berry Quality and Price Outlook';

  @override
  String get featureGradingCardDescription => 'Check grade and price outlook';

  @override
  String get featureGradingDescription =>
      'Take a clear pepper sample photo to receive a project quality grade. When a grade is clear, you can also view a grade-matched EAC price outlook.';

  @override
  String get startScan => 'Start scan';

  @override
  String get historyEmptyTitle => 'No analysis history yet';

  @override
  String get historyEmptyMessage =>
      'Completed analyses will appear here and remain available offline.';

  @override
  String get historyIntro =>
      'Your saved crop checks are stored privately on this device.';

  @override
  String get historyAllTypes => 'All';

  @override
  String get historyLoadMore => 'Load more';

  @override
  String get historyLoadingMore => 'Loading more…';

  @override
  String get historySettings => 'History settings';

  @override
  String get historyFilter => 'Filter history';

  @override
  String get historyDeleteOptions => 'Manage and delete history';

  @override
  String get historyAutoDeleteTitle => 'Delete history after 14 days';

  @override
  String get historyAutoDeleteDescription =>
      'Optional and off by default. Expired history is removed when the app next opens or resumes.';

  @override
  String get historyClearAll => 'Clear all history';

  @override
  String get historyClearConfirmTitle => 'Clear all history?';

  @override
  String get historyClearConfirmMessage =>
      'This permanently removes every saved result and its stored image from this device.';

  @override
  String get historyCancel => 'Cancel';

  @override
  String get historyClearConfirmAction => 'Clear all';

  @override
  String get historyClearSuccess =>
      'All history and stored images were removed.';

  @override
  String get historyClearPartial =>
      'Some files could not be removed. They will be retried when the app next opens.';

  @override
  String get historySaveFailed =>
      'The result is ready, but it could not be saved to History.';

  @override
  String get historyUnavailableTitle => 'History is unavailable';

  @override
  String get historyUnavailableMessage =>
      'Local storage could not be opened. Your other analysis features still work.';

  @override
  String get historyImageUnavailable => 'Saved image unavailable';

  @override
  String get historyResultUnavailable =>
      'Stored result details are unavailable or from an unsupported version.';

  @override
  String get historyDetailsTitle => 'Saved analysis';

  @override
  String get historyRecordedOn => 'Recorded on';

  @override
  String get historySavedOffline =>
      'This is a saved result. Opening it does not run analysis or use the internet.';

  @override
  String get historyDetectedItems => 'Detected items';

  @override
  String get historyNoDetectedItems => 'No detected items were stored.';

  @override
  String get historyLowConfidence => 'Low-confidence detection';

  @override
  String get historyDetectionOnly =>
      'Detection saved. Detailed guidance was not opened for this scan.';

  @override
  String get historyOutcome => 'Result';

  @override
  String get historyAccepted => 'Accepted';

  @override
  String get historyRejected => 'Could not assess';

  @override
  String get historyUncertain => 'Uncertain result';

  @override
  String get historyTreatmentAction => 'Recommended action';

  @override
  String get historyWarnings => 'Important notes';

  @override
  String get historyPriceSnapshot => 'Saved price outlook';

  @override
  String get historyAutoDeleteUpdated => 'History cleanup setting updated.';

  @override
  String get guideTitle => 'Berry quality guide';

  @override
  String get guideSubtitle =>
      'Follow these simple steps for a clearer berry grade and price outlook.';

  @override
  String get guidePhotoTitle => 'Choose a good sample';

  @override
  String get guidePhotoBody =>
      'Use a representative pepper berry sample. Keep leaves, hands and other objects from covering the berries.';

  @override
  String get guideLightingTitle => 'Use even daylight';

  @override
  String get guideLightingBody =>
      'Photograph in bright, even light. Avoid deep shadows, glare and direct flash on the berries.';

  @override
  String get guidePositionTitle => 'Fill the frame';

  @override
  String get guidePositionBody =>
      'Keep the full sample clearly visible and close enough to see the berries without cutting off important parts.';

  @override
  String get guideGradesTitle => 'Understand the grades';

  @override
  String get guideGradesBody =>
      'Grade 1 and Grade 2 are project quality groups based on visible features. They are not official SLS, buyer, laboratory or export-certification grades.';

  @override
  String get guidePriceTitle => 'Understand the price outlook';

  @override
  String get guidePriceBody =>
      'The shown price is a grade-matched research estimate based on EAC farm-gate reference data. It is not a live buyer offer or guaranteed selling price.';

  @override
  String get guideRetryTitle => 'If we cannot assess it';

  @override
  String get guideRetryBody =>
      'Retake the photo in better light, hold the phone steady, move closer and make sure pepper berries are clearly visible.';

  @override
  String get guideLimitation =>
      'Use the result as supporting information. Confirm important grading and selling decisions with a trusted buyer, extension officer or other qualified person.';

  @override
  String get berryLabel => 'Berry';

  @override
  String get leafLabel => 'Leaf';

  @override
  String get pestLabel => 'Pest';

  @override
  String get plantLabel => 'Plant Health';

  @override
  String get statusThinking => 'Thinking…';

  @override
  String get statusValidating => 'Validating the photo…';

  @override
  String get statusInspecting => 'Inspecting the leaves…';

  @override
  String get statusMatching => 'Matching against known patterns…';

  @override
  String get statusCloserLook => 'Hmm, this one needs a closer look…';

  @override
  String get statusAlmostThere => 'Almost there…';

  @override
  String get preparing => 'Preparing…';

  @override
  String scanHint(String label) {
    return 'Scan a $label — tap the shutter or pick from gallery';
  }

  @override
  String get cameraUnavailable => 'Camera unavailable';

  @override
  String modelLoadFailed(String label) {
    return 'Couldn\'t load the \"$label\" model';
  }

  @override
  String get otherScanTypesUnaffected => 'The other scan types are unaffected.';

  @override
  String get couldNotReadImage =>
      'That photo couldn\'t be read. Please try another photo.';

  @override
  String get errSetup =>
      'The scanner isn\'t set up correctly. Please contact support.';

  @override
  String get errOffline =>
      'No internet connection. Check your network and try again.';

  @override
  String get errBusy =>
      'The scanner is busy right now. Please try again in a moment.';

  @override
  String get errGeneric => 'Something went wrong. Please try again.';

  @override
  String get nothingDetected => 'Nothing detected';

  @override
  String findingsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count findings',
      one: '1 finding',
    );
    return '$_temp0';
  }

  @override
  String get noMatchesHint =>
      'No matches above the confidence threshold. Try moving closer, steadying the shot, or improving the lighting.';

  @override
  String get lowConfidenceNotice =>
      'Low confidence. Nothing met the usual bar, so weaker matches are shown instead — treat these as a hint, not a diagnosis, and retake in better light if you can.';

  @override
  String get showRecommendations => 'Show recommendations';

  @override
  String get takeAnotherPhoto => 'Take another photo';

  @override
  String get looksHealthy => 'Looks healthy — no treatment needed.';

  @override
  String get camera => 'Camera';

  @override
  String get gallery => 'Gallery';

  @override
  String get retry => 'Retry';

  @override
  String get tryAgain => 'Try again';

  @override
  String get retakePhoto => 'Retake photo';

  @override
  String get analyze => 'Analyze';

  @override
  String get captureAndScan => 'Capture and scan';

  @override
  String get gradingHomeTitle => 'Berry Grading and Export Price Forecasting';

  @override
  String get gradingHomeSubtitle =>
      'Capture a pepper berry image to estimate berry quality and get a simple price forecast.';

  @override
  String get checkBerryQuality => 'Check Berry Quality';

  @override
  String get captureBerryTitle => 'Capture Pepper Berry Image';

  @override
  String get noImageSelected => 'No image selected yet.';

  @override
  String get captureTip => 'Tip: use a clear, well-lit photo and avoid blur.';

  @override
  String get captureGuideTitle => 'Take a clear sample photo';

  @override
  String get captureGuideSubtitle =>
      'A good photo helps the app assess the visible berry quality more reliably.';

  @override
  String get captureAvoidBlurTitle => 'Keep the phone steady';

  @override
  String get captureAvoidBlurBody =>
      'Hold still while taking the photo. If the berries look blurred, retake it before analysis.';

  @override
  String get gotIt => 'Got it';

  @override
  String get captureFarmerPrompt =>
      'Add one clear photo of your pepper berry sample.';

  @override
  String get captureChooseSource =>
      'Use the camera or choose an original photo from your gallery.';

  @override
  String get analyzeBerrySample => 'Check berry quality';

  @override
  String get couldNotOpenCameraGallery =>
      'Could not open camera/gallery. Please try again.';

  @override
  String get processing => 'Processing';

  @override
  String get analyzingBerryQuality => 'Analyzing berry quality...';

  @override
  String get analyzeFailed => 'Failed to analyze the image. Please try again.';

  @override
  String get backendError => 'Backend error. Please try again.';

  @override
  String get processingFarmerTitle => 'Checking your berry sample';

  @override
  String get processingErrorTitle => 'We could not complete the check';

  @override
  String get backToHome => 'Back to home';

  @override
  String get phase7GradingHomeSubtitle =>
      'Capture a pepper sample image for project-specific grading and a limited frozen EAC price outlook.';

  @override
  String get phase7ProcessingMessage =>
      'Running frozen grading and price decision support...';

  @override
  String get phase7EmptyImage =>
      'The selected image is empty. Choose another image.';

  @override
  String get phase7ImageTooLarge =>
      'The selected image exceeds the 10 MB upload limit.';

  @override
  String get phase7InvalidBackendAddress =>
      'The research backend address is invalid.';

  @override
  String get phase7InvalidImage => 'The selected file is not a readable image.';

  @override
  String get phase7UnsupportedImage =>
      'Use a non-animated JPEG, PNG, or WEBP image.';

  @override
  String get phase7MalformedRequest => 'The image request is malformed.';

  @override
  String get phase7ServiceBusy =>
      'The hosted service is busy. Please wait and retry.';

  @override
  String get phase7ServiceUnavailable =>
      'The research backend is temporarily unavailable. Please retry later.';

  @override
  String get phase7Timeout => 'Analysis timed out. Please retry.';

  @override
  String get phase7Unreachable => 'Cannot reach the research backend.';

  @override
  String get phase7MalformedResponse => 'The backend returned malformed data.';

  @override
  String get phase7AnalysisFailed => 'Analysis failed on the research backend.';

  @override
  String get phase7DecisionSupportTitle => 'Pepper Decision Support';

  @override
  String get phase7GradingDecision => 'Grading decision';

  @override
  String get phase7ProjectGrade => 'Project grade';

  @override
  String get phase7QualityGate => 'Quality gate';

  @override
  String get phase7ModelScore => 'Model score';

  @override
  String get phase7ConfidenceInterpretation =>
      'Model score; not a calibrated probability';

  @override
  String get phase7Reason => 'Reason';

  @override
  String get phase7ResearchLimitations => 'Research limitations';

  @override
  String get phase7ViewPriceOutlook => 'View grade-specific price outlook';

  @override
  String get phase7PriceOutlookTitle => 'Price Outlook';

  @override
  String get phase7PriceSeries => 'Price series';

  @override
  String get phase7Source => 'Source';

  @override
  String get phase7LatestReferenceDate => 'Latest reference date';

  @override
  String get phase7LatestReferencePrice => 'Latest reference price';

  @override
  String get phase7FrozenForecastTarget => 'Frozen forecast target';

  @override
  String get phase7FrozenForecastPrice => 'Frozen forecast price';

  @override
  String get phase7Direction => 'Direction';

  @override
  String get phase7Signal => 'Signal';

  @override
  String get phase7PersistenceComparison => 'Persistence comparison';

  @override
  String get phase7ForecastInterval => 'Validation-derived forecast interval';

  @override
  String get phase7ForecastDisclaimer =>
      'This is a frozen EAC farm-gate research forecast, not a live buyer offer, guaranteed price, or buy/sell instruction.';

  @override
  String get phase7ResearchTrace => 'Research trace';

  @override
  String get phase7NotAvailable => 'Not available';

  @override
  String get phase7NullValue => 'null';

  @override
  String phase7PriceValue(String value) {
    return 'LKR $value / kg';
  }

  @override
  String get phase7CategoryReject => 'REJECT';

  @override
  String get phase7CategoryUncertainGrade => 'UNCERTAIN GRADE';

  @override
  String get phase7CategoryConflictingViews => 'CONFLICTING SAMPLE VIEWS';

  @override
  String get phase7CategoryPriceUnavailable => 'PRICE DATA UNAVAILABLE';

  @override
  String get phase7CategoryForecastUnavailable => 'FORECAST UNAVAILABLE';

  @override
  String get phase7CategoryUpwardOutlook => 'UPWARD PRICE OUTLOOK';

  @override
  String get phase7CategoryDownwardOutlook => 'DOWNWARD PRICE OUTLOOK';

  @override
  String get phase7CategoryFlatOutlook => 'FLAT PRICE OUTLOOK';

  @override
  String get phase7CategoryHighUncertainty => 'HIGH UNCERTAINTY OUTLOOK';

  @override
  String get phase7DecisionGrade1 => 'GRADE 1';

  @override
  String get phase7DecisionGrade2 => 'GRADE 2';

  @override
  String get phase7DecisionNoPepper => 'NO PEPPER';

  @override
  String get phase7DecisionPoorImage => 'POOR IMAGE';

  @override
  String get phase7ProjectGrade1 => 'V3 Grade 1';

  @override
  String get phase7ProjectGrade2 => 'V3 Grade 2';

  @override
  String get phase7PriceGrade1 => 'Grade 1';

  @override
  String get phase7PriceGrade2 => 'Grade 2';

  @override
  String get phase7Passed => 'PASSED';

  @override
  String get phase7Failed => 'FAILED';

  @override
  String get phase7ReasonNoDetection => 'No detection above the threshold';

  @override
  String get phase7ReasonBlur => 'Image sharpness is below the minimum';

  @override
  String get phase7ReasonTooDark => 'Image brightness is below the minimum';

  @override
  String get phase7ReasonTooBright => 'Image brightness is above the maximum';

  @override
  String get phase7ReasonSmallArea =>
      'Detected pepper area is below the minimum';

  @override
  String get phase7ReasonLowConfidence => 'Grade score is below the minimum';

  @override
  String get phase7ReasonLowMargin => 'Grade margin is below the minimum';

  @override
  String get phase7DirectionUp => 'UP';

  @override
  String get phase7DirectionDown => 'DOWN';

  @override
  String get phase7DirectionFlat => 'FLAT';

  @override
  String get phase7SignalHighUncertainty => 'HIGH UNCERTAINTY';

  @override
  String get phase7SignalLimited => 'LIMITED SIGNAL';

  @override
  String get phase7RidgeBetter => 'RIDGE BETTER';

  @override
  String get phase7PersistenceBetter => 'PERSISTENCE BETTER';

  @override
  String get phase7PersistenceTie => 'TIE';

  @override
  String get phase7SummaryReject =>
      'Valid pepper was not established; no grade-specific market outlook was generated.';

  @override
  String get phase7SummaryUncertain =>
      'A reliable grade was not established; no grade-specific market outlook was generated.';

  @override
  String get phase7SummaryPriceUnavailable =>
      'The grade was accepted, but the required grade-specific reference price is unavailable.';

  @override
  String get phase7SummaryForecastUnavailable =>
      'The grade-specific reference price is available, but no frozen Phase 5 forecast is available.';

  @override
  String phase7SummaryAccepted(
    String grade,
    String priceGrade,
    String direction,
    String signal,
  ) {
    return 'Accepted as $grade. The frozen $priceGrade forecast indicates $direction movement, with signal classified as $signal. This is a limited research outlook, not a buy/sell instruction.';
  }

  @override
  String get phase7LimitationProjectGrade =>
      'V3 grades are project-specific and are not official SLS, buyer, export-certification, or laboratory grades.';

  @override
  String get phase7LimitationResearchOnly =>
      'This is research decision support, not an autonomous trading recommendation.';

  @override
  String get phase7LimitationMixedForecast =>
      'The Phase 5 price signal is limited/mixed and persistence remains a strong baseline.';

  @override
  String get phase7EacReferencePrice => 'EAC farm-gate reference price';

  @override
  String get farmerBerryGrade1 => 'Berry Grade 1';

  @override
  String get farmerBerryGrade2 => 'Berry Grade 2';

  @override
  String get farmerNoPepperTitle => 'Pepper berries were not found';

  @override
  String get farmerPoorImageTitle => 'Please take a clearer photo';

  @override
  String get farmerUncertainTitle =>
      'We could not confidently assess this sample';

  @override
  String get farmerConflictingViewsTitle => 'The sample photos do not agree';

  @override
  String get farmerGrade1Explanation =>
      'The visible features of this sample match the project\'s Grade 1 quality group.';

  @override
  String get farmerGrade2Explanation =>
      'The visible features of this sample match the project\'s Grade 2 quality group.';

  @override
  String get farmerAcceptedExplanation =>
      'A clear project quality grade was found for this sample.';

  @override
  String get farmerNoPepperExplanation =>
      'The photo did not show enough recognizable pepper berries for grading, so no price outlook was produced.';

  @override
  String get farmerPoorImageExplanation =>
      'The image quality was not good enough for a reliable grade, so no price outlook was produced.';

  @override
  String get farmerUncertainExplanation =>
      'The visible grade signs were too close to make a reliable choice, so the app stopped before showing a price.';

  @override
  String get farmerConflictingViewsExplanation =>
      'Different sample photos suggested different grades, so the app stopped before showing a price.';

  @override
  String get farmerRetakeBlur =>
      'Retake the photo while holding the phone steady and make sure the berries are sharp.';

  @override
  String get farmerRetakeLighting =>
      'Retake the photo in bright, even light without glare or deep shadows.';

  @override
  String get farmerRetakePosition =>
      'Move closer and place the pepper berry sample clearly in the center of the photo.';

  @override
  String get farmerRetakeGeneral =>
      'Retake the photo in good light, hold the phone steady and keep the full pepper sample visible.';

  @override
  String get farmerGradeNotice =>
      'This is an AI-supported project estimate, not an official quality or export certificate.';

  @override
  String get farmerViewPriceOutlook => 'View price outlook';

  @override
  String get farmerAnalyzeAnother => 'Check another sample';

  @override
  String get farmerPriceOutlookTitle => 'Price Outlook';

  @override
  String get farmerEstimatedPrice => 'Estimated price outlook';

  @override
  String get farmerExpectedRise => 'Expected to rise';

  @override
  String get farmerExpectedFall => 'Expected to fall';

  @override
  String get farmerExpectedSimilar => 'Expected to remain similar';

  @override
  String get farmerPriceHighUncertainty =>
      'This price outlook has high uncertainty. The actual price may be meaningfully higher or lower.';

  @override
  String get farmerPriceLimitedSignal =>
      'This is a limited research outlook. Use it as supporting information rather than a firm price expectation.';

  @override
  String get farmerPriceDetails => 'Outlook details';

  @override
  String get farmerOutlookDate => 'Outlook date';

  @override
  String get farmerReferencePrice => 'Latest reference price';

  @override
  String get farmerReferenceDate => 'Reference date';

  @override
  String get farmerForecastNotice =>
      'This frozen EAC farm-gate research outlook is not a live buyer offer, guaranteed price or instruction to buy or sell.';

  @override
  String get berryQualityResult => 'Berry Quality Result';

  @override
  String get predictedGrade => 'Predicted Grade';

  @override
  String get confidence => 'Confidence';

  @override
  String get qualityScore => 'Quality Score';

  @override
  String get explanation => 'Explanation';

  @override
  String get noExplanation => 'No additional explanation available.';

  @override
  String get visualFactors => 'Visual Factors Detected';

  @override
  String get colorUniformity => 'Color uniformity';

  @override
  String get darkBerryRatio => 'Dark berry ratio';

  @override
  String get lightBerryRatio => 'Light berry ratio';

  @override
  String get textureScore => 'Texture score';

  @override
  String get defectRatio => 'Defect ratio';

  @override
  String get cleanlinessScore => 'Cleanliness score';

  @override
  String get viewPriceForecast => 'View Price Forecast';

  @override
  String get qualityGrade => 'QUALITY GRADE';

  @override
  String get visualEstimateDisclaimer =>
      'Camera-based visual estimate only. Chemical requirements and bulk density are not measured.';

  @override
  String get priceForecast => 'Price Forecast';

  @override
  String get predictedGradeShort => 'Predicted grade';

  @override
  String get useGradeForRecommendation =>
      'Use grade for recommendation (optional)';

  @override
  String get currentPrice => 'Current price (LKR/kg)';

  @override
  String get predictedPrice => 'Predicted price (LKR/kg)';

  @override
  String get trend => 'Trend';

  @override
  String modelLabelPrefix(String model) {
    return 'Model: $model';
  }

  @override
  String get recommendation => 'Recommendation';

  @override
  String decisionLabel(String value) {
    return 'Decision: $value';
  }

  @override
  String urgencyLabel(String value) {
    return 'Urgency: $value';
  }

  @override
  String get suggestedAction => 'Suggested action';

  @override
  String get whyThisRecommendation => 'Why this recommendation?';

  @override
  String get analyzeAnotherImage => 'Analyze Another Image';

  @override
  String get gradeSpecificNote =>
      'Grade-specific forecasting will be improved after grade-wise market data is available.';

  @override
  String get couldNotUpdateRecShowingPrevious =>
      'Could not update recommendation. Showing previous recommendation.';

  @override
  String get couldNotUpdateRec =>
      'Could not update recommendation. Please try again.';

  @override
  String get grade1 => 'Grade 1';

  @override
  String get grade2 => 'Grade 2';

  @override
  String get grade3 => 'Grade 3';

  @override
  String get urgencyHigh => 'High';

  @override
  String get urgencyMedium => 'Medium';

  @override
  String get urgencyLow => 'Low';

  @override
  String get trendRising => 'Rising';

  @override
  String get trendFalling => 'Falling';

  @override
  String get trendStable => 'Stable';

  @override
  String get decisionWaitExport => 'Wait / Target export buyer';

  @override
  String get decisionSellExport => 'Sell (export)';

  @override
  String get decisionSellSoon => 'Sell soon';

  @override
  String get decisionWaitShortly => 'Wait shortly';

  @override
  String get decisionMonitor => 'Monitor';

  @override
  String get decisionSortProcess => 'Sort or process';

  @override
  String get decisionProcessLocal => 'Process locally';

  @override
  String get decisionProcessOrSellNow => 'Process or sell now';

  @override
  String get severity => 'Severity';

  @override
  String get high => 'High';

  @override
  String get medium => 'Medium';

  @override
  String get whatWeSee => 'What we see';

  @override
  String get recommendedTreatment => 'Recommended treatment';

  @override
  String get safeRemediation => 'Safe remediation';

  @override
  String get exportMarket => 'Export market';

  @override
  String get leafAnalysisTitle => 'Leaf analysis';

  @override
  String get healthyLeaf => 'Healthy leaf';

  @override
  String get leafRetryHint =>
      'Fill the frame with a single leaf in good light and try again.';

  @override
  String get leafDisclaimer =>
      'AI estimate from one photo. Confirm with a local agronomist before applying any treatment.';

  @override
  String get pestAnalysisTitle => 'Pest analysis';

  @override
  String get noPestsFound => 'No pests found';

  @override
  String get pestUncertainTitle => 'We could not confirm the pest';

  @override
  String get pestUncertainMessage =>
      'Take a closer photo in good light before applying any treatment. If the problem continues, ask a local agronomist to inspect the plant.';

  @override
  String get aboveTreatmentThreshold => 'Above treatment threshold';

  @override
  String get pestRetryHint =>
      'Get closer to the leaf/stem/berry in good light and retry.';

  @override
  String get pestDisclaimer =>
      'AI estimate from one photo. Confirm the pest, economic threshold, and exact product and dose with a local agronomist before spraying.';

  @override
  String get berryGradingTitle => 'Berry grading';

  @override
  String get exportCleanCluster => 'Export-clean cluster';

  @override
  String get berryRetryHint =>
      'Fill the frame with a berry cluster in good light and retry.';

  @override
  String get berryDisclaimer =>
      'AI estimate from one photo. Confirm the diagnosis, exact dose, MRL and pre-harvest interval with a local agronomist before applying.';

  @override
  String get low => 'Low';

  @override
  String get analysingLeaf => 'Analysing leaf with AI…';

  @override
  String get analysingBerry => 'Grading berries with AI…';

  @override
  String get analysingPest => 'Inspecting for pests with AI…';

  @override
  String get notPepperLeaf => 'This doesn\'t look like a pepper leaf';

  @override
  String get notBerryCluster => 'This doesn\'t look like a berry cluster';

  @override
  String get notPepperPlant => 'This doesn\'t look like a pepper plant';

  @override
  String get recommendedActionIpm => 'Recommended action (IPM)';

  @override
  String get belowThreshold => 'Below treatment threshold — monitor only';

  @override
  String get clsHealthy => 'Healthy';

  @override
  String get clsHealthyLeaves => 'Healthy leaves';

  @override
  String get clsHealthyBerry => 'Healthy berry';

  @override
  String get clsLeafBlight => 'Leaf Blight';

  @override
  String get clsLittleLeaf => 'Little Leaf';

  @override
  String get clsQuickWilt => 'Quick Wilt';

  @override
  String get clsLaceBugDamage => 'Lace bug damage';

  @override
  String get clsNutrientDeficiency => 'Nutrient deficiency';

  @override
  String get clsOtherDisease => 'Other disease';

  @override
  String get clsOtherDamage => 'Other damage';

  @override
  String get clsUncertain => 'Uncertain';

  @override
  String get scanInstructionsTitle => 'How to scan';

  @override
  String scanInstructionsStep1(String object) {
    return 'Point the camera at the $object and tap the shutter button.';
  }

  @override
  String get scanInstructionsStep2 =>
      'Hold steady in good light and fill the frame with the subject.';

  @override
  String get scanInstructionsStep3 =>
      'Check what we found, then tap Show recommendations to see treatment advice.';

  @override
  String get scanInstructionsStart => 'Got it, start scanning';

  @override
  String get howToScan => 'How to scan';
}
