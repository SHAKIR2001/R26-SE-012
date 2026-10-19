import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_si.dart';
import 'app_localizations_ta.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('si'),
    Locale('ta'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'Pepper Care'**
  String get appTitle;

  /// No description provided for @chooseLanguage.
  ///
  /// In en, this message translates to:
  /// **'Choose your language'**
  String get chooseLanguage;

  /// No description provided for @chooseLanguageSubtitle.
  ///
  /// In en, this message translates to:
  /// **'You can change this anytime from the menu.'**
  String get chooseLanguageSubtitle;

  /// No description provided for @languageEnglish.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get languageEnglish;

  /// No description provided for @languageSinhala.
  ///
  /// In en, this message translates to:
  /// **'සිංහල'**
  String get languageSinhala;

  /// No description provided for @languageTamil.
  ///
  /// In en, this message translates to:
  /// **'தமிழ்'**
  String get languageTamil;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @homeLeafPest.
  ///
  /// In en, this message translates to:
  /// **'Leaf & Pest'**
  String get homeLeafPest;

  /// No description provided for @homeBerryScan.
  ///
  /// In en, this message translates to:
  /// **'Berry Scan'**
  String get homeBerryScan;

  /// No description provided for @homeGradingForecast.
  ///
  /// In en, this message translates to:
  /// **'Grading & Forecast'**
  String get homeGradingForecast;

  /// No description provided for @homePests.
  ///
  /// In en, this message translates to:
  /// **'Pests'**
  String get homePests;

  /// No description provided for @homeLeafHealth.
  ///
  /// In en, this message translates to:
  /// **'Leaf Health'**
  String get homeLeafHealth;

  /// No description provided for @homeBerryDisease.
  ///
  /// In en, this message translates to:
  /// **'Berry Disease'**
  String get homeBerryDisease;

  /// No description provided for @homeQualityPrice.
  ///
  /// In en, this message translates to:
  /// **'Quality &\nPrice'**
  String get homeQualityPrice;

  /// No description provided for @lightMode.
  ///
  /// In en, this message translates to:
  /// **'Light mode'**
  String get lightMode;

  /// No description provided for @darkMode.
  ///
  /// In en, this message translates to:
  /// **'Dark mode'**
  String get darkMode;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navHistory.
  ///
  /// In en, this message translates to:
  /// **'History'**
  String get navHistory;

  /// No description provided for @navGuide.
  ///
  /// In en, this message translates to:
  /// **'Guide'**
  String get navGuide;

  /// No description provided for @homeWelcomeTitle.
  ///
  /// In en, this message translates to:
  /// **'How can we help your crop today?'**
  String get homeWelcomeTitle;

  /// No description provided for @homeWelcomeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Choose the task you need. We will guide you through the photo and results.'**
  String get homeWelcomeSubtitle;

  /// No description provided for @homeChooseTaskHint.
  ///
  /// In en, this message translates to:
  /// **'Choose a task before taking a photo so the app can use the right crop check.'**
  String get homeChooseTaskHint;

  /// No description provided for @featurePlantHealth.
  ///
  /// In en, this message translates to:
  /// **'Plant health'**
  String get featurePlantHealth;

  /// No description provided for @featurePlantTitle.
  ///
  /// In en, this message translates to:
  /// **'Leaf Health & Pest Check'**
  String get featurePlantTitle;

  /// No description provided for @featurePlantCardDescription.
  ///
  /// In en, this message translates to:
  /// **'Check for leaf disease and pepper pests'**
  String get featurePlantCardDescription;

  /// No description provided for @featurePlantDescription.
  ///
  /// In en, this message translates to:
  /// **'Take a clear photo of a pepper leaf, stem or berry area to check for visible leaf disease and common pepper pests, then receive practical guidance.'**
  String get featurePlantDescription;

  /// No description provided for @featureBerryCare.
  ///
  /// In en, this message translates to:
  /// **'Berry care'**
  String get featureBerryCare;

  /// No description provided for @featureQualityAndPrice.
  ///
  /// In en, this message translates to:
  /// **'Quality and price'**
  String get featureQualityAndPrice;

  /// No description provided for @featurePestTitle.
  ///
  /// In en, this message translates to:
  /// **'Pest Detection'**
  String get featurePestTitle;

  /// No description provided for @featurePestCardDescription.
  ///
  /// In en, this message translates to:
  /// **'Check leaves, stems and berries'**
  String get featurePestCardDescription;

  /// No description provided for @featurePestDescription.
  ///
  /// In en, this message translates to:
  /// **'Take a clear photo to look for common pepper pests and receive practical treatment guidance.'**
  String get featurePestDescription;

  /// No description provided for @featureLeafTitle.
  ///
  /// In en, this message translates to:
  /// **'Leaf Health Check'**
  String get featureLeafTitle;

  /// No description provided for @featureLeafCardDescription.
  ///
  /// In en, this message translates to:
  /// **'Look for leaf disease signs'**
  String get featureLeafCardDescription;

  /// No description provided for @featureLeafDescription.
  ///
  /// In en, this message translates to:
  /// **'Photograph a pepper leaf to check for visible disease signs and understand how serious they may be.'**
  String get featureLeafDescription;

  /// No description provided for @featureBerryDiseaseTitle.
  ///
  /// In en, this message translates to:
  /// **'Berry Disease Check'**
  String get featureBerryDiseaseTitle;

  /// No description provided for @featureBerryDiseaseCardDescription.
  ///
  /// In en, this message translates to:
  /// **'Inspect berry clusters for damage'**
  String get featureBerryDiseaseCardDescription;

  /// No description provided for @featureBerryDiseaseDescription.
  ///
  /// In en, this message translates to:
  /// **'Photograph a pepper berry cluster to check for visible disease or pest damage and receive care guidance.'**
  String get featureBerryDiseaseDescription;

  /// No description provided for @featureGradingTitle.
  ///
  /// In en, this message translates to:
  /// **'Berry Quality and Price Outlook'**
  String get featureGradingTitle;

  /// No description provided for @featureGradingCardDescription.
  ///
  /// In en, this message translates to:
  /// **'Check grade and price outlook'**
  String get featureGradingCardDescription;

  /// No description provided for @featureGradingDescription.
  ///
  /// In en, this message translates to:
  /// **'Take a clear pepper sample photo to receive a project quality grade. When a grade is clear, you can also view a grade-matched EAC price outlook.'**
  String get featureGradingDescription;

  /// No description provided for @startScan.
  ///
  /// In en, this message translates to:
  /// **'Start scan'**
  String get startScan;

  /// No description provided for @historyEmptyTitle.
  ///
  /// In en, this message translates to:
  /// **'No analysis history yet'**
  String get historyEmptyTitle;

  /// No description provided for @historyEmptyMessage.
  ///
  /// In en, this message translates to:
  /// **'Completed analyses will appear here and remain available offline.'**
  String get historyEmptyMessage;

  /// No description provided for @historyIntro.
  ///
  /// In en, this message translates to:
  /// **'Your saved crop checks are stored privately on this device.'**
  String get historyIntro;

  /// No description provided for @historyAllTypes.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get historyAllTypes;

  /// No description provided for @historyLoadMore.
  ///
  /// In en, this message translates to:
  /// **'Load more'**
  String get historyLoadMore;

  /// No description provided for @historyLoadingMore.
  ///
  /// In en, this message translates to:
  /// **'Loading more…'**
  String get historyLoadingMore;

  /// No description provided for @historySettings.
  ///
  /// In en, this message translates to:
  /// **'History settings'**
  String get historySettings;

  /// No description provided for @historyFilter.
  ///
  /// In en, this message translates to:
  /// **'Filter history'**
  String get historyFilter;

  /// No description provided for @historyDeleteOptions.
  ///
  /// In en, this message translates to:
  /// **'Manage and delete history'**
  String get historyDeleteOptions;

  /// No description provided for @historyAutoDeleteTitle.
  ///
  /// In en, this message translates to:
  /// **'Delete history after 14 days'**
  String get historyAutoDeleteTitle;

  /// No description provided for @historyAutoDeleteDescription.
  ///
  /// In en, this message translates to:
  /// **'Optional and off by default. Expired history is removed when the app next opens or resumes.'**
  String get historyAutoDeleteDescription;

  /// No description provided for @historyClearAll.
  ///
  /// In en, this message translates to:
  /// **'Clear all history'**
  String get historyClearAll;

  /// No description provided for @historyClearConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Clear all history?'**
  String get historyClearConfirmTitle;

  /// No description provided for @historyClearConfirmMessage.
  ///
  /// In en, this message translates to:
  /// **'This permanently removes every saved result and its stored image from this device.'**
  String get historyClearConfirmMessage;

  /// No description provided for @historyCancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get historyCancel;

  /// No description provided for @historyClearConfirmAction.
  ///
  /// In en, this message translates to:
  /// **'Clear all'**
  String get historyClearConfirmAction;

  /// No description provided for @historyClearSuccess.
  ///
  /// In en, this message translates to:
  /// **'All history and stored images were removed.'**
  String get historyClearSuccess;

  /// No description provided for @historyClearPartial.
  ///
  /// In en, this message translates to:
  /// **'Some files could not be removed. They will be retried when the app next opens.'**
  String get historyClearPartial;

  /// No description provided for @historySaveFailed.
  ///
  /// In en, this message translates to:
  /// **'The result is ready, but it could not be saved to History.'**
  String get historySaveFailed;

  /// No description provided for @historyUnavailableTitle.
  ///
  /// In en, this message translates to:
  /// **'History is unavailable'**
  String get historyUnavailableTitle;

  /// No description provided for @historyUnavailableMessage.
  ///
  /// In en, this message translates to:
  /// **'Local storage could not be opened. Your other analysis features still work.'**
  String get historyUnavailableMessage;

  /// No description provided for @historyImageUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Saved image unavailable'**
  String get historyImageUnavailable;

  /// No description provided for @historyResultUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Stored result details are unavailable or from an unsupported version.'**
  String get historyResultUnavailable;

  /// No description provided for @historyDetailsTitle.
  ///
  /// In en, this message translates to:
  /// **'Saved analysis'**
  String get historyDetailsTitle;

  /// No description provided for @historyRecordedOn.
  ///
  /// In en, this message translates to:
  /// **'Recorded on'**
  String get historyRecordedOn;

  /// No description provided for @historySavedOffline.
  ///
  /// In en, this message translates to:
  /// **'This is a saved result. Opening it does not run analysis or use the internet.'**
  String get historySavedOffline;

  /// No description provided for @historyDetectedItems.
  ///
  /// In en, this message translates to:
  /// **'Detected items'**
  String get historyDetectedItems;

  /// No description provided for @historyNoDetectedItems.
  ///
  /// In en, this message translates to:
  /// **'No detected items were stored.'**
  String get historyNoDetectedItems;

  /// No description provided for @historyLowConfidence.
  ///
  /// In en, this message translates to:
  /// **'Low-confidence detection'**
  String get historyLowConfidence;

  /// No description provided for @historyDetectionOnly.
  ///
  /// In en, this message translates to:
  /// **'Detection saved. Detailed guidance was not opened for this scan.'**
  String get historyDetectionOnly;

  /// No description provided for @historyOutcome.
  ///
  /// In en, this message translates to:
  /// **'Result'**
  String get historyOutcome;

  /// No description provided for @historyAccepted.
  ///
  /// In en, this message translates to:
  /// **'Accepted'**
  String get historyAccepted;

  /// No description provided for @historyRejected.
  ///
  /// In en, this message translates to:
  /// **'Could not assess'**
  String get historyRejected;

  /// No description provided for @historyUncertain.
  ///
  /// In en, this message translates to:
  /// **'Uncertain result'**
  String get historyUncertain;

  /// No description provided for @historyTreatmentAction.
  ///
  /// In en, this message translates to:
  /// **'Recommended action'**
  String get historyTreatmentAction;

  /// No description provided for @historyWarnings.
  ///
  /// In en, this message translates to:
  /// **'Important notes'**
  String get historyWarnings;

  /// No description provided for @historyPriceSnapshot.
  ///
  /// In en, this message translates to:
  /// **'Saved price outlook'**
  String get historyPriceSnapshot;

  /// No description provided for @historyAutoDeleteUpdated.
  ///
  /// In en, this message translates to:
  /// **'History cleanup setting updated.'**
  String get historyAutoDeleteUpdated;

  /// No description provided for @guideTitle.
  ///
  /// In en, this message translates to:
  /// **'Berry quality guide'**
  String get guideTitle;

  /// No description provided for @guideSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Follow these simple steps for a clearer berry grade and price outlook.'**
  String get guideSubtitle;

  /// No description provided for @guidePhotoTitle.
  ///
  /// In en, this message translates to:
  /// **'Choose a good sample'**
  String get guidePhotoTitle;

  /// No description provided for @guidePhotoBody.
  ///
  /// In en, this message translates to:
  /// **'Use a representative pepper berry sample. Keep leaves, hands and other objects from covering the berries.'**
  String get guidePhotoBody;

  /// No description provided for @guideLightingTitle.
  ///
  /// In en, this message translates to:
  /// **'Use even daylight'**
  String get guideLightingTitle;

  /// No description provided for @guideLightingBody.
  ///
  /// In en, this message translates to:
  /// **'Photograph in bright, even light. Avoid deep shadows, glare and direct flash on the berries.'**
  String get guideLightingBody;

  /// No description provided for @guidePositionTitle.
  ///
  /// In en, this message translates to:
  /// **'Fill the frame'**
  String get guidePositionTitle;

  /// No description provided for @guidePositionBody.
  ///
  /// In en, this message translates to:
  /// **'Keep the full sample clearly visible and close enough to see the berries without cutting off important parts.'**
  String get guidePositionBody;

  /// No description provided for @guideGradesTitle.
  ///
  /// In en, this message translates to:
  /// **'Understand the grades'**
  String get guideGradesTitle;

  /// No description provided for @guideGradesBody.
  ///
  /// In en, this message translates to:
  /// **'Grade 1 and Grade 2 are project quality groups based on visible features. They are not official SLS, buyer, laboratory or export-certification grades.'**
  String get guideGradesBody;

  /// No description provided for @guidePriceTitle.
  ///
  /// In en, this message translates to:
  /// **'Understand the price outlook'**
  String get guidePriceTitle;

  /// No description provided for @guidePriceBody.
  ///
  /// In en, this message translates to:
  /// **'The shown price is a grade-matched research estimate based on EAC farm-gate reference data. It is not a live buyer offer or guaranteed selling price.'**
  String get guidePriceBody;

  /// No description provided for @guideRetryTitle.
  ///
  /// In en, this message translates to:
  /// **'If we cannot assess it'**
  String get guideRetryTitle;

  /// No description provided for @guideRetryBody.
  ///
  /// In en, this message translates to:
  /// **'Retake the photo in better light, hold the phone steady, move closer and make sure pepper berries are clearly visible.'**
  String get guideRetryBody;

  /// No description provided for @guideLimitation.
  ///
  /// In en, this message translates to:
  /// **'Use the result as supporting information. Confirm important grading and selling decisions with a trusted buyer, extension officer or other qualified person.'**
  String get guideLimitation;

  /// No description provided for @berryLabel.
  ///
  /// In en, this message translates to:
  /// **'Berry'**
  String get berryLabel;

  /// No description provided for @leafLabel.
  ///
  /// In en, this message translates to:
  /// **'Leaf'**
  String get leafLabel;

  /// No description provided for @pestLabel.
  ///
  /// In en, this message translates to:
  /// **'Pest'**
  String get pestLabel;

  /// No description provided for @plantLabel.
  ///
  /// In en, this message translates to:
  /// **'Plant Health'**
  String get plantLabel;

  /// No description provided for @statusThinking.
  ///
  /// In en, this message translates to:
  /// **'Thinking…'**
  String get statusThinking;

  /// No description provided for @statusValidating.
  ///
  /// In en, this message translates to:
  /// **'Validating the photo…'**
  String get statusValidating;

  /// No description provided for @statusInspecting.
  ///
  /// In en, this message translates to:
  /// **'Inspecting the leaves…'**
  String get statusInspecting;

  /// No description provided for @statusMatching.
  ///
  /// In en, this message translates to:
  /// **'Matching against known patterns…'**
  String get statusMatching;

  /// No description provided for @statusCloserLook.
  ///
  /// In en, this message translates to:
  /// **'Hmm, this one needs a closer look…'**
  String get statusCloserLook;

  /// No description provided for @statusAlmostThere.
  ///
  /// In en, this message translates to:
  /// **'Almost there…'**
  String get statusAlmostThere;

  /// No description provided for @preparing.
  ///
  /// In en, this message translates to:
  /// **'Preparing…'**
  String get preparing;

  /// No description provided for @scanHint.
  ///
  /// In en, this message translates to:
  /// **'Scan a {label} — tap the shutter or pick from gallery'**
  String scanHint(String label);

  /// No description provided for @cameraUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Camera unavailable'**
  String get cameraUnavailable;

  /// No description provided for @modelLoadFailed.
  ///
  /// In en, this message translates to:
  /// **'Couldn\'t load the \"{label}\" model'**
  String modelLoadFailed(String label);

  /// No description provided for @otherScanTypesUnaffected.
  ///
  /// In en, this message translates to:
  /// **'The other scan types are unaffected.'**
  String get otherScanTypesUnaffected;

  /// No description provided for @couldNotReadImage.
  ///
  /// In en, this message translates to:
  /// **'That photo couldn\'t be read. Please try another photo.'**
  String get couldNotReadImage;

  /// No description provided for @errSetup.
  ///
  /// In en, this message translates to:
  /// **'The scanner isn\'t set up correctly. Please contact support.'**
  String get errSetup;

  /// No description provided for @errOffline.
  ///
  /// In en, this message translates to:
  /// **'No internet connection. Check your network and try again.'**
  String get errOffline;

  /// No description provided for @errBusy.
  ///
  /// In en, this message translates to:
  /// **'The scanner is busy right now. Please try again in a moment.'**
  String get errBusy;

  /// No description provided for @errGeneric.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get errGeneric;

  /// No description provided for @nothingDetected.
  ///
  /// In en, this message translates to:
  /// **'Nothing detected'**
  String get nothingDetected;

  /// No description provided for @findingsCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, one{1 finding} other{{count} findings}}'**
  String findingsCount(int count);

  /// No description provided for @noMatchesHint.
  ///
  /// In en, this message translates to:
  /// **'No matches above the confidence threshold. Try moving closer, steadying the shot, or improving the lighting.'**
  String get noMatchesHint;

  /// No description provided for @lowConfidenceNotice.
  ///
  /// In en, this message translates to:
  /// **'Low confidence. Nothing met the usual bar, so weaker matches are shown instead — treat these as a hint, not a diagnosis, and retake in better light if you can.'**
  String get lowConfidenceNotice;

  /// No description provided for @showRecommendations.
  ///
  /// In en, this message translates to:
  /// **'Show recommendations'**
  String get showRecommendations;

  /// No description provided for @takeAnotherPhoto.
  ///
  /// In en, this message translates to:
  /// **'Take another photo'**
  String get takeAnotherPhoto;

  /// No description provided for @looksHealthy.
  ///
  /// In en, this message translates to:
  /// **'Looks healthy — no treatment needed.'**
  String get looksHealthy;

  /// No description provided for @camera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get camera;

  /// No description provided for @gallery.
  ///
  /// In en, this message translates to:
  /// **'Gallery'**
  String get gallery;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @tryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgain;

  /// No description provided for @retakePhoto.
  ///
  /// In en, this message translates to:
  /// **'Retake photo'**
  String get retakePhoto;

  /// No description provided for @analyze.
  ///
  /// In en, this message translates to:
  /// **'Analyze'**
  String get analyze;

  /// No description provided for @captureAndScan.
  ///
  /// In en, this message translates to:
  /// **'Capture and scan'**
  String get captureAndScan;

  /// No description provided for @gradingHomeTitle.
  ///
  /// In en, this message translates to:
  /// **'Berry Grading and Export Price Forecasting'**
  String get gradingHomeTitle;

  /// No description provided for @gradingHomeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Capture a pepper berry image to estimate berry quality and get a simple price forecast.'**
  String get gradingHomeSubtitle;

  /// No description provided for @checkBerryQuality.
  ///
  /// In en, this message translates to:
  /// **'Check Berry Quality'**
  String get checkBerryQuality;

  /// No description provided for @captureBerryTitle.
  ///
  /// In en, this message translates to:
  /// **'Capture Pepper Berry Image'**
  String get captureBerryTitle;

  /// No description provided for @noImageSelected.
  ///
  /// In en, this message translates to:
  /// **'No image selected yet.'**
  String get noImageSelected;

  /// No description provided for @captureTip.
  ///
  /// In en, this message translates to:
  /// **'Tip: use a clear, well-lit photo and avoid blur.'**
  String get captureTip;

  /// No description provided for @captureGuideTitle.
  ///
  /// In en, this message translates to:
  /// **'Take a clear sample photo'**
  String get captureGuideTitle;

  /// No description provided for @captureGuideSubtitle.
  ///
  /// In en, this message translates to:
  /// **'A good photo helps the app assess the visible berry quality more reliably.'**
  String get captureGuideSubtitle;

  /// No description provided for @captureAvoidBlurTitle.
  ///
  /// In en, this message translates to:
  /// **'Keep the phone steady'**
  String get captureAvoidBlurTitle;

  /// No description provided for @captureAvoidBlurBody.
  ///
  /// In en, this message translates to:
  /// **'Hold still while taking the photo. If the berries look blurred, retake it before analysis.'**
  String get captureAvoidBlurBody;

  /// No description provided for @gotIt.
  ///
  /// In en, this message translates to:
  /// **'Got it'**
  String get gotIt;

  /// No description provided for @captureFarmerPrompt.
  ///
  /// In en, this message translates to:
  /// **'Add one clear photo of your pepper berry sample.'**
  String get captureFarmerPrompt;

  /// No description provided for @captureChooseSource.
  ///
  /// In en, this message translates to:
  /// **'Use the camera or choose an original photo from your gallery.'**
  String get captureChooseSource;

  /// No description provided for @analyzeBerrySample.
  ///
  /// In en, this message translates to:
  /// **'Check berry quality'**
  String get analyzeBerrySample;

  /// No description provided for @couldNotOpenCameraGallery.
  ///
  /// In en, this message translates to:
  /// **'Could not open camera/gallery. Please try again.'**
  String get couldNotOpenCameraGallery;

  /// No description provided for @processing.
  ///
  /// In en, this message translates to:
  /// **'Processing'**
  String get processing;

  /// No description provided for @analyzingBerryQuality.
  ///
  /// In en, this message translates to:
  /// **'Analyzing berry quality...'**
  String get analyzingBerryQuality;

  /// No description provided for @analyzeFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed to analyze the image. Please try again.'**
  String get analyzeFailed;

  /// No description provided for @backendError.
  ///
  /// In en, this message translates to:
  /// **'Backend error. Please try again.'**
  String get backendError;

  /// No description provided for @processingFarmerTitle.
  ///
  /// In en, this message translates to:
  /// **'Checking your berry sample'**
  String get processingFarmerTitle;

  /// No description provided for @processingErrorTitle.
  ///
  /// In en, this message translates to:
  /// **'We could not complete the check'**
  String get processingErrorTitle;

  /// No description provided for @backToHome.
  ///
  /// In en, this message translates to:
  /// **'Back to home'**
  String get backToHome;

  /// No description provided for @phase7GradingHomeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Capture a pepper sample image for project-specific grading and a limited frozen EAC price outlook.'**
  String get phase7GradingHomeSubtitle;

  /// No description provided for @phase7ProcessingMessage.
  ///
  /// In en, this message translates to:
  /// **'Running frozen grading and price decision support...'**
  String get phase7ProcessingMessage;

  /// No description provided for @phase7EmptyImage.
  ///
  /// In en, this message translates to:
  /// **'The selected image is empty. Choose another image.'**
  String get phase7EmptyImage;

  /// No description provided for @phase7ImageTooLarge.
  ///
  /// In en, this message translates to:
  /// **'The selected image exceeds the 10 MB upload limit.'**
  String get phase7ImageTooLarge;

  /// No description provided for @phase7InvalidBackendAddress.
  ///
  /// In en, this message translates to:
  /// **'The research backend address is invalid.'**
  String get phase7InvalidBackendAddress;

  /// No description provided for @phase7InvalidImage.
  ///
  /// In en, this message translates to:
  /// **'The selected file is not a readable image.'**
  String get phase7InvalidImage;

  /// No description provided for @phase7UnsupportedImage.
  ///
  /// In en, this message translates to:
  /// **'Use a non-animated JPEG, PNG, or WEBP image.'**
  String get phase7UnsupportedImage;

  /// No description provided for @phase7MalformedRequest.
  ///
  /// In en, this message translates to:
  /// **'The image request is malformed.'**
  String get phase7MalformedRequest;

  /// No description provided for @phase7ServiceBusy.
  ///
  /// In en, this message translates to:
  /// **'The hosted service is busy. Please wait and retry.'**
  String get phase7ServiceBusy;

  /// No description provided for @phase7ServiceUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The research backend is temporarily unavailable. Please retry later.'**
  String get phase7ServiceUnavailable;

  /// No description provided for @phase7Timeout.
  ///
  /// In en, this message translates to:
  /// **'Analysis timed out. Please retry.'**
  String get phase7Timeout;

  /// No description provided for @phase7Unreachable.
  ///
  /// In en, this message translates to:
  /// **'Cannot reach the research backend.'**
  String get phase7Unreachable;

  /// No description provided for @phase7MalformedResponse.
  ///
  /// In en, this message translates to:
  /// **'The backend returned malformed data.'**
  String get phase7MalformedResponse;

  /// No description provided for @phase7AnalysisFailed.
  ///
  /// In en, this message translates to:
  /// **'Analysis failed on the research backend.'**
  String get phase7AnalysisFailed;

  /// No description provided for @phase7DecisionSupportTitle.
  ///
  /// In en, this message translates to:
  /// **'Pepper Decision Support'**
  String get phase7DecisionSupportTitle;

  /// No description provided for @phase7GradingDecision.
  ///
  /// In en, this message translates to:
  /// **'Grading decision'**
  String get phase7GradingDecision;

  /// No description provided for @phase7ProjectGrade.
  ///
  /// In en, this message translates to:
  /// **'Project grade'**
  String get phase7ProjectGrade;

  /// No description provided for @phase7QualityGate.
  ///
  /// In en, this message translates to:
  /// **'Quality gate'**
  String get phase7QualityGate;

  /// No description provided for @phase7ModelScore.
  ///
  /// In en, this message translates to:
  /// **'Model score'**
  String get phase7ModelScore;

  /// No description provided for @phase7ConfidenceInterpretation.
  ///
  /// In en, this message translates to:
  /// **'Model score; not a calibrated probability'**
  String get phase7ConfidenceInterpretation;

  /// No description provided for @phase7Reason.
  ///
  /// In en, this message translates to:
  /// **'Reason'**
  String get phase7Reason;

  /// No description provided for @phase7ResearchLimitations.
  ///
  /// In en, this message translates to:
  /// **'Research limitations'**
  String get phase7ResearchLimitations;

  /// No description provided for @phase7ViewPriceOutlook.
  ///
  /// In en, this message translates to:
  /// **'View grade-specific price outlook'**
  String get phase7ViewPriceOutlook;

  /// No description provided for @phase7PriceOutlookTitle.
  ///
  /// In en, this message translates to:
  /// **'Price Outlook'**
  String get phase7PriceOutlookTitle;

  /// No description provided for @phase7PriceSeries.
  ///
  /// In en, this message translates to:
  /// **'Price series'**
  String get phase7PriceSeries;

  /// No description provided for @phase7Source.
  ///
  /// In en, this message translates to:
  /// **'Source'**
  String get phase7Source;

  /// No description provided for @phase7LatestReferenceDate.
  ///
  /// In en, this message translates to:
  /// **'Latest reference date'**
  String get phase7LatestReferenceDate;

  /// No description provided for @phase7LatestReferencePrice.
  ///
  /// In en, this message translates to:
  /// **'Latest reference price'**
  String get phase7LatestReferencePrice;

  /// No description provided for @phase7FrozenForecastTarget.
  ///
  /// In en, this message translates to:
  /// **'Frozen forecast target'**
  String get phase7FrozenForecastTarget;

  /// No description provided for @phase7FrozenForecastPrice.
  ///
  /// In en, this message translates to:
  /// **'Frozen forecast price'**
  String get phase7FrozenForecastPrice;

  /// No description provided for @phase7Direction.
  ///
  /// In en, this message translates to:
  /// **'Direction'**
  String get phase7Direction;

  /// No description provided for @phase7Signal.
  ///
  /// In en, this message translates to:
  /// **'Signal'**
  String get phase7Signal;

  /// No description provided for @phase7PersistenceComparison.
  ///
  /// In en, this message translates to:
  /// **'Persistence comparison'**
  String get phase7PersistenceComparison;

  /// No description provided for @phase7ForecastInterval.
  ///
  /// In en, this message translates to:
  /// **'Validation-derived forecast interval'**
  String get phase7ForecastInterval;

  /// No description provided for @phase7ForecastDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'This is a frozen EAC farm-gate research forecast, not a live buyer offer, guaranteed price, or buy/sell instruction.'**
  String get phase7ForecastDisclaimer;

  /// No description provided for @phase7ResearchTrace.
  ///
  /// In en, this message translates to:
  /// **'Research trace'**
  String get phase7ResearchTrace;

  /// No description provided for @phase7NotAvailable.
  ///
  /// In en, this message translates to:
  /// **'Not available'**
  String get phase7NotAvailable;

  /// No description provided for @phase7NullValue.
  ///
  /// In en, this message translates to:
  /// **'null'**
  String get phase7NullValue;

  /// No description provided for @phase7PriceValue.
  ///
  /// In en, this message translates to:
  /// **'LKR {value} / kg'**
  String phase7PriceValue(String value);

  /// No description provided for @phase7CategoryReject.
  ///
  /// In en, this message translates to:
  /// **'REJECT'**
  String get phase7CategoryReject;

  /// No description provided for @phase7CategoryUncertainGrade.
  ///
  /// In en, this message translates to:
  /// **'UNCERTAIN GRADE'**
  String get phase7CategoryUncertainGrade;

  /// No description provided for @phase7CategoryConflictingViews.
  ///
  /// In en, this message translates to:
  /// **'CONFLICTING SAMPLE VIEWS'**
  String get phase7CategoryConflictingViews;

  /// No description provided for @phase7CategoryPriceUnavailable.
  ///
  /// In en, this message translates to:
  /// **'PRICE DATA UNAVAILABLE'**
  String get phase7CategoryPriceUnavailable;

  /// No description provided for @phase7CategoryForecastUnavailable.
  ///
  /// In en, this message translates to:
  /// **'FORECAST UNAVAILABLE'**
  String get phase7CategoryForecastUnavailable;

  /// No description provided for @phase7CategoryUpwardOutlook.
  ///
  /// In en, this message translates to:
  /// **'UPWARD PRICE OUTLOOK'**
  String get phase7CategoryUpwardOutlook;

  /// No description provided for @phase7CategoryDownwardOutlook.
  ///
  /// In en, this message translates to:
  /// **'DOWNWARD PRICE OUTLOOK'**
  String get phase7CategoryDownwardOutlook;

  /// No description provided for @phase7CategoryFlatOutlook.
  ///
  /// In en, this message translates to:
  /// **'FLAT PRICE OUTLOOK'**
  String get phase7CategoryFlatOutlook;

  /// No description provided for @phase7CategoryHighUncertainty.
  ///
  /// In en, this message translates to:
  /// **'HIGH UNCERTAINTY OUTLOOK'**
  String get phase7CategoryHighUncertainty;

  /// No description provided for @phase7DecisionGrade1.
  ///
  /// In en, this message translates to:
  /// **'GRADE 1'**
  String get phase7DecisionGrade1;

  /// No description provided for @phase7DecisionGrade2.
  ///
  /// In en, this message translates to:
  /// **'GRADE 2'**
  String get phase7DecisionGrade2;

  /// No description provided for @phase7DecisionNoPepper.
  ///
  /// In en, this message translates to:
  /// **'NO PEPPER'**
  String get phase7DecisionNoPepper;

  /// No description provided for @phase7DecisionPoorImage.
  ///
  /// In en, this message translates to:
  /// **'POOR IMAGE'**
  String get phase7DecisionPoorImage;

  /// No description provided for @phase7ProjectGrade1.
  ///
  /// In en, this message translates to:
  /// **'V3 Grade 1'**
  String get phase7ProjectGrade1;

  /// No description provided for @phase7ProjectGrade2.
  ///
  /// In en, this message translates to:
  /// **'V3 Grade 2'**
  String get phase7ProjectGrade2;

  /// No description provided for @phase7PriceGrade1.
  ///
  /// In en, this message translates to:
  /// **'Grade 1'**
  String get phase7PriceGrade1;

  /// No description provided for @phase7PriceGrade2.
  ///
  /// In en, this message translates to:
  /// **'Grade 2'**
  String get phase7PriceGrade2;

  /// No description provided for @phase7Passed.
  ///
  /// In en, this message translates to:
  /// **'PASSED'**
  String get phase7Passed;

  /// No description provided for @phase7Failed.
  ///
  /// In en, this message translates to:
  /// **'FAILED'**
  String get phase7Failed;

  /// No description provided for @phase7ReasonNoDetection.
  ///
  /// In en, this message translates to:
  /// **'No detection above the threshold'**
  String get phase7ReasonNoDetection;

  /// No description provided for @phase7ReasonBlur.
  ///
  /// In en, this message translates to:
  /// **'Image sharpness is below the minimum'**
  String get phase7ReasonBlur;

  /// No description provided for @phase7ReasonTooDark.
  ///
  /// In en, this message translates to:
  /// **'Image brightness is below the minimum'**
  String get phase7ReasonTooDark;

  /// No description provided for @phase7ReasonTooBright.
  ///
  /// In en, this message translates to:
  /// **'Image brightness is above the maximum'**
  String get phase7ReasonTooBright;

  /// No description provided for @phase7ReasonSmallArea.
  ///
  /// In en, this message translates to:
  /// **'Detected pepper area is below the minimum'**
  String get phase7ReasonSmallArea;

  /// No description provided for @phase7ReasonLowConfidence.
  ///
  /// In en, this message translates to:
  /// **'Grade score is below the minimum'**
  String get phase7ReasonLowConfidence;

  /// No description provided for @phase7ReasonLowMargin.
  ///
  /// In en, this message translates to:
  /// **'Grade margin is below the minimum'**
  String get phase7ReasonLowMargin;

  /// No description provided for @phase7DirectionUp.
  ///
  /// In en, this message translates to:
  /// **'UP'**
  String get phase7DirectionUp;

  /// No description provided for @phase7DirectionDown.
  ///
  /// In en, this message translates to:
  /// **'DOWN'**
  String get phase7DirectionDown;

  /// No description provided for @phase7DirectionFlat.
  ///
  /// In en, this message translates to:
  /// **'FLAT'**
  String get phase7DirectionFlat;

  /// No description provided for @phase7SignalHighUncertainty.
  ///
  /// In en, this message translates to:
  /// **'HIGH UNCERTAINTY'**
  String get phase7SignalHighUncertainty;

  /// No description provided for @phase7SignalLimited.
  ///
  /// In en, this message translates to:
  /// **'LIMITED SIGNAL'**
  String get phase7SignalLimited;

  /// No description provided for @phase7RidgeBetter.
  ///
  /// In en, this message translates to:
  /// **'RIDGE BETTER'**
  String get phase7RidgeBetter;

  /// No description provided for @phase7PersistenceBetter.
  ///
  /// In en, this message translates to:
  /// **'PERSISTENCE BETTER'**
  String get phase7PersistenceBetter;

  /// No description provided for @phase7PersistenceTie.
  ///
  /// In en, this message translates to:
  /// **'TIE'**
  String get phase7PersistenceTie;

  /// No description provided for @phase7SummaryReject.
  ///
  /// In en, this message translates to:
  /// **'Valid pepper was not established; no grade-specific market outlook was generated.'**
  String get phase7SummaryReject;

  /// No description provided for @phase7SummaryUncertain.
  ///
  /// In en, this message translates to:
  /// **'A reliable grade was not established; no grade-specific market outlook was generated.'**
  String get phase7SummaryUncertain;

  /// No description provided for @phase7SummaryPriceUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The grade was accepted, but the required grade-specific reference price is unavailable.'**
  String get phase7SummaryPriceUnavailable;

  /// No description provided for @phase7SummaryForecastUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The grade-specific reference price is available, but no frozen Phase 5 forecast is available.'**
  String get phase7SummaryForecastUnavailable;

  /// No description provided for @phase7SummaryAccepted.
  ///
  /// In en, this message translates to:
  /// **'Accepted as {grade}. The frozen {priceGrade} forecast indicates {direction} movement, with signal classified as {signal}. This is a limited research outlook, not a buy/sell instruction.'**
  String phase7SummaryAccepted(
    String grade,
    String priceGrade,
    String direction,
    String signal,
  );

  /// No description provided for @phase7LimitationProjectGrade.
  ///
  /// In en, this message translates to:
  /// **'V3 grades are project-specific and are not official SLS, buyer, export-certification, or laboratory grades.'**
  String get phase7LimitationProjectGrade;

  /// No description provided for @phase7LimitationResearchOnly.
  ///
  /// In en, this message translates to:
  /// **'This is research decision support, not an autonomous trading recommendation.'**
  String get phase7LimitationResearchOnly;

  /// No description provided for @phase7LimitationMixedForecast.
  ///
  /// In en, this message translates to:
  /// **'The Phase 5 price signal is limited/mixed and persistence remains a strong baseline.'**
  String get phase7LimitationMixedForecast;

  /// No description provided for @phase7EacReferencePrice.
  ///
  /// In en, this message translates to:
  /// **'EAC farm-gate reference price'**
  String get phase7EacReferencePrice;

  /// No description provided for @farmerBerryGrade1.
  ///
  /// In en, this message translates to:
  /// **'Berry Grade 1'**
  String get farmerBerryGrade1;

  /// No description provided for @farmerBerryGrade2.
  ///
  /// In en, this message translates to:
  /// **'Berry Grade 2'**
  String get farmerBerryGrade2;

  /// No description provided for @farmerNoPepperTitle.
  ///
  /// In en, this message translates to:
  /// **'Pepper berries were not found'**
  String get farmerNoPepperTitle;

  /// No description provided for @farmerPoorImageTitle.
  ///
  /// In en, this message translates to:
  /// **'Please take a clearer photo'**
  String get farmerPoorImageTitle;

  /// No description provided for @farmerUncertainTitle.
  ///
  /// In en, this message translates to:
  /// **'We could not confidently assess this sample'**
  String get farmerUncertainTitle;

  /// No description provided for @farmerConflictingViewsTitle.
  ///
  /// In en, this message translates to:
  /// **'The sample photos do not agree'**
  String get farmerConflictingViewsTitle;

  /// No description provided for @farmerGrade1Explanation.
  ///
  /// In en, this message translates to:
  /// **'The visible features of this sample match the project\'s Grade 1 quality group.'**
  String get farmerGrade1Explanation;

  /// No description provided for @farmerGrade2Explanation.
  ///
  /// In en, this message translates to:
  /// **'The visible features of this sample match the project\'s Grade 2 quality group.'**
  String get farmerGrade2Explanation;

  /// No description provided for @farmerAcceptedExplanation.
  ///
  /// In en, this message translates to:
  /// **'A clear project quality grade was found for this sample.'**
  String get farmerAcceptedExplanation;

  /// No description provided for @farmerNoPepperExplanation.
  ///
  /// In en, this message translates to:
  /// **'The photo did not show enough recognizable pepper berries for grading, so no price outlook was produced.'**
  String get farmerNoPepperExplanation;

  /// No description provided for @farmerPoorImageExplanation.
  ///
  /// In en, this message translates to:
  /// **'The image quality was not good enough for a reliable grade, so no price outlook was produced.'**
  String get farmerPoorImageExplanation;

  /// No description provided for @farmerUncertainExplanation.
  ///
  /// In en, this message translates to:
  /// **'The visible grade signs were too close to make a reliable choice, so the app stopped before showing a price.'**
  String get farmerUncertainExplanation;

  /// No description provided for @farmerConflictingViewsExplanation.
  ///
  /// In en, this message translates to:
  /// **'Different sample photos suggested different grades, so the app stopped before showing a price.'**
  String get farmerConflictingViewsExplanation;

  /// No description provided for @farmerRetakeBlur.
  ///
  /// In en, this message translates to:
  /// **'Retake the photo while holding the phone steady and make sure the berries are sharp.'**
  String get farmerRetakeBlur;

  /// No description provided for @farmerRetakeLighting.
  ///
  /// In en, this message translates to:
  /// **'Retake the photo in bright, even light without glare or deep shadows.'**
  String get farmerRetakeLighting;

  /// No description provided for @farmerRetakePosition.
  ///
  /// In en, this message translates to:
  /// **'Move closer and place the pepper berry sample clearly in the center of the photo.'**
  String get farmerRetakePosition;

  /// No description provided for @farmerRetakeGeneral.
  ///
  /// In en, this message translates to:
  /// **'Retake the photo in good light, hold the phone steady and keep the full pepper sample visible.'**
  String get farmerRetakeGeneral;

  /// No description provided for @farmerGradeNotice.
  ///
  /// In en, this message translates to:
  /// **'This is an AI-supported project estimate, not an official quality or export certificate.'**
  String get farmerGradeNotice;

  /// No description provided for @farmerViewPriceOutlook.
  ///
  /// In en, this message translates to:
  /// **'View price outlook'**
  String get farmerViewPriceOutlook;

  /// No description provided for @farmerAnalyzeAnother.
  ///
  /// In en, this message translates to:
  /// **'Check another sample'**
  String get farmerAnalyzeAnother;

  /// No description provided for @farmerPriceOutlookTitle.
  ///
  /// In en, this message translates to:
  /// **'Price Outlook'**
  String get farmerPriceOutlookTitle;

  /// No description provided for @farmerEstimatedPrice.
  ///
  /// In en, this message translates to:
  /// **'Estimated price outlook'**
  String get farmerEstimatedPrice;

  /// No description provided for @farmerExpectedRise.
  ///
  /// In en, this message translates to:
  /// **'Expected to rise'**
  String get farmerExpectedRise;

  /// No description provided for @farmerExpectedFall.
  ///
  /// In en, this message translates to:
  /// **'Expected to fall'**
  String get farmerExpectedFall;

  /// No description provided for @farmerExpectedSimilar.
  ///
  /// In en, this message translates to:
  /// **'Expected to remain similar'**
  String get farmerExpectedSimilar;

  /// No description provided for @farmerPriceHighUncertainty.
  ///
  /// In en, this message translates to:
  /// **'This price outlook has high uncertainty. The actual price may be meaningfully higher or lower.'**
  String get farmerPriceHighUncertainty;

  /// No description provided for @farmerPriceLimitedSignal.
  ///
  /// In en, this message translates to:
  /// **'This is a limited research outlook. Use it as supporting information rather than a firm price expectation.'**
  String get farmerPriceLimitedSignal;

  /// No description provided for @farmerPriceDetails.
  ///
  /// In en, this message translates to:
  /// **'Outlook details'**
  String get farmerPriceDetails;

  /// No description provided for @farmerOutlookDate.
  ///
  /// In en, this message translates to:
  /// **'Outlook date'**
  String get farmerOutlookDate;

  /// No description provided for @farmerReferencePrice.
  ///
  /// In en, this message translates to:
  /// **'Latest reference price'**
  String get farmerReferencePrice;

  /// No description provided for @farmerReferenceDate.
  ///
  /// In en, this message translates to:
  /// **'Reference date'**
  String get farmerReferenceDate;

  /// No description provided for @farmerForecastNotice.
  ///
  /// In en, this message translates to:
  /// **'This frozen EAC farm-gate research outlook is not a live buyer offer, guaranteed price or instruction to buy or sell.'**
  String get farmerForecastNotice;

  /// No description provided for @berryQualityResult.
  ///
  /// In en, this message translates to:
  /// **'Berry Quality Result'**
  String get berryQualityResult;

  /// No description provided for @predictedGrade.
  ///
  /// In en, this message translates to:
  /// **'Predicted Grade'**
  String get predictedGrade;

  /// No description provided for @confidence.
  ///
  /// In en, this message translates to:
  /// **'Confidence'**
  String get confidence;

  /// No description provided for @qualityScore.
  ///
  /// In en, this message translates to:
  /// **'Quality Score'**
  String get qualityScore;

  /// No description provided for @explanation.
  ///
  /// In en, this message translates to:
  /// **'Explanation'**
  String get explanation;

  /// No description provided for @noExplanation.
  ///
  /// In en, this message translates to:
  /// **'No additional explanation available.'**
  String get noExplanation;

  /// No description provided for @visualFactors.
  ///
  /// In en, this message translates to:
  /// **'Visual Factors Detected'**
  String get visualFactors;

  /// No description provided for @colorUniformity.
  ///
  /// In en, this message translates to:
  /// **'Color uniformity'**
  String get colorUniformity;

  /// No description provided for @darkBerryRatio.
  ///
  /// In en, this message translates to:
  /// **'Dark berry ratio'**
  String get darkBerryRatio;

  /// No description provided for @lightBerryRatio.
  ///
  /// In en, this message translates to:
  /// **'Light berry ratio'**
  String get lightBerryRatio;

  /// No description provided for @textureScore.
  ///
  /// In en, this message translates to:
  /// **'Texture score'**
  String get textureScore;

  /// No description provided for @defectRatio.
  ///
  /// In en, this message translates to:
  /// **'Defect ratio'**
  String get defectRatio;

  /// No description provided for @cleanlinessScore.
  ///
  /// In en, this message translates to:
  /// **'Cleanliness score'**
  String get cleanlinessScore;

  /// No description provided for @viewPriceForecast.
  ///
  /// In en, this message translates to:
  /// **'View Price Forecast'**
  String get viewPriceForecast;

  /// No description provided for @qualityGrade.
  ///
  /// In en, this message translates to:
  /// **'QUALITY GRADE'**
  String get qualityGrade;

  /// No description provided for @visualEstimateDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'Camera-based visual estimate only. Chemical requirements and bulk density are not measured.'**
  String get visualEstimateDisclaimer;

  /// No description provided for @priceForecast.
  ///
  /// In en, this message translates to:
  /// **'Price Forecast'**
  String get priceForecast;

  /// No description provided for @predictedGradeShort.
  ///
  /// In en, this message translates to:
  /// **'Predicted grade'**
  String get predictedGradeShort;

  /// No description provided for @useGradeForRecommendation.
  ///
  /// In en, this message translates to:
  /// **'Use grade for recommendation (optional)'**
  String get useGradeForRecommendation;

  /// No description provided for @currentPrice.
  ///
  /// In en, this message translates to:
  /// **'Current price (LKR/kg)'**
  String get currentPrice;

  /// No description provided for @predictedPrice.
  ///
  /// In en, this message translates to:
  /// **'Predicted price (LKR/kg)'**
  String get predictedPrice;

  /// No description provided for @trend.
  ///
  /// In en, this message translates to:
  /// **'Trend'**
  String get trend;

  /// No description provided for @modelLabelPrefix.
  ///
  /// In en, this message translates to:
  /// **'Model: {model}'**
  String modelLabelPrefix(String model);

  /// No description provided for @recommendation.
  ///
  /// In en, this message translates to:
  /// **'Recommendation'**
  String get recommendation;

  /// No description provided for @decisionLabel.
  ///
  /// In en, this message translates to:
  /// **'Decision: {value}'**
  String decisionLabel(String value);

  /// No description provided for @urgencyLabel.
  ///
  /// In en, this message translates to:
  /// **'Urgency: {value}'**
  String urgencyLabel(String value);

  /// No description provided for @suggestedAction.
  ///
  /// In en, this message translates to:
  /// **'Suggested action'**
  String get suggestedAction;

  /// No description provided for @whyThisRecommendation.
  ///
  /// In en, this message translates to:
  /// **'Why this recommendation?'**
  String get whyThisRecommendation;

  /// No description provided for @analyzeAnotherImage.
  ///
  /// In en, this message translates to:
  /// **'Analyze Another Image'**
  String get analyzeAnotherImage;

  /// No description provided for @gradeSpecificNote.
  ///
  /// In en, this message translates to:
  /// **'Grade-specific forecasting will be improved after grade-wise market data is available.'**
  String get gradeSpecificNote;

  /// No description provided for @couldNotUpdateRecShowingPrevious.
  ///
  /// In en, this message translates to:
  /// **'Could not update recommendation. Showing previous recommendation.'**
  String get couldNotUpdateRecShowingPrevious;

  /// No description provided for @couldNotUpdateRec.
  ///
  /// In en, this message translates to:
  /// **'Could not update recommendation. Please try again.'**
  String get couldNotUpdateRec;

  /// No description provided for @grade1.
  ///
  /// In en, this message translates to:
  /// **'Grade 1'**
  String get grade1;

  /// No description provided for @grade2.
  ///
  /// In en, this message translates to:
  /// **'Grade 2'**
  String get grade2;

  /// No description provided for @grade3.
  ///
  /// In en, this message translates to:
  /// **'Grade 3'**
  String get grade3;

  /// No description provided for @urgencyHigh.
  ///
  /// In en, this message translates to:
  /// **'High'**
  String get urgencyHigh;

  /// No description provided for @urgencyMedium.
  ///
  /// In en, this message translates to:
  /// **'Medium'**
  String get urgencyMedium;

  /// No description provided for @urgencyLow.
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get urgencyLow;

  /// No description provided for @trendRising.
  ///
  /// In en, this message translates to:
  /// **'Rising'**
  String get trendRising;

  /// No description provided for @trendFalling.
  ///
  /// In en, this message translates to:
  /// **'Falling'**
  String get trendFalling;

  /// No description provided for @trendStable.
  ///
  /// In en, this message translates to:
  /// **'Stable'**
  String get trendStable;

  /// No description provided for @decisionWaitExport.
  ///
  /// In en, this message translates to:
  /// **'Wait / Target export buyer'**
  String get decisionWaitExport;

  /// No description provided for @decisionSellExport.
  ///
  /// In en, this message translates to:
  /// **'Sell (export)'**
  String get decisionSellExport;

  /// No description provided for @decisionSellSoon.
  ///
  /// In en, this message translates to:
  /// **'Sell soon'**
  String get decisionSellSoon;

  /// No description provided for @decisionWaitShortly.
  ///
  /// In en, this message translates to:
  /// **'Wait shortly'**
  String get decisionWaitShortly;

  /// No description provided for @decisionMonitor.
  ///
  /// In en, this message translates to:
  /// **'Monitor'**
  String get decisionMonitor;

  /// No description provided for @decisionSortProcess.
  ///
  /// In en, this message translates to:
  /// **'Sort or process'**
  String get decisionSortProcess;

  /// No description provided for @decisionProcessLocal.
  ///
  /// In en, this message translates to:
  /// **'Process locally'**
  String get decisionProcessLocal;

  /// No description provided for @decisionProcessOrSellNow.
  ///
  /// In en, this message translates to:
  /// **'Process or sell now'**
  String get decisionProcessOrSellNow;

  /// No description provided for @severity.
  ///
  /// In en, this message translates to:
  /// **'Severity'**
  String get severity;

  /// No description provided for @high.
  ///
  /// In en, this message translates to:
  /// **'High'**
  String get high;

  /// No description provided for @medium.
  ///
  /// In en, this message translates to:
  /// **'Medium'**
  String get medium;

  /// No description provided for @whatWeSee.
  ///
  /// In en, this message translates to:
  /// **'What we see'**
  String get whatWeSee;

  /// No description provided for @recommendedTreatment.
  ///
  /// In en, this message translates to:
  /// **'Recommended treatment'**
  String get recommendedTreatment;

  /// No description provided for @safeRemediation.
  ///
  /// In en, this message translates to:
  /// **'Safe remediation'**
  String get safeRemediation;

  /// No description provided for @exportMarket.
  ///
  /// In en, this message translates to:
  /// **'Export market'**
  String get exportMarket;

  /// No description provided for @leafAnalysisTitle.
  ///
  /// In en, this message translates to:
  /// **'Leaf analysis'**
  String get leafAnalysisTitle;

  /// No description provided for @healthyLeaf.
  ///
  /// In en, this message translates to:
  /// **'Healthy leaf'**
  String get healthyLeaf;

  /// No description provided for @leafRetryHint.
  ///
  /// In en, this message translates to:
  /// **'Fill the frame with a single leaf in good light and try again.'**
  String get leafRetryHint;

  /// No description provided for @leafDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'AI estimate from one photo. Confirm with a local agronomist before applying any treatment.'**
  String get leafDisclaimer;

  /// No description provided for @pestAnalysisTitle.
  ///
  /// In en, this message translates to:
  /// **'Pest analysis'**
  String get pestAnalysisTitle;

  /// No description provided for @noPestsFound.
  ///
  /// In en, this message translates to:
  /// **'No pests found'**
  String get noPestsFound;

  /// No description provided for @pestUncertainTitle.
  ///
  /// In en, this message translates to:
  /// **'We could not confirm the pest'**
  String get pestUncertainTitle;

  /// No description provided for @pestUncertainMessage.
  ///
  /// In en, this message translates to:
  /// **'Take a closer photo in good light before applying any treatment. If the problem continues, ask a local agronomist to inspect the plant.'**
  String get pestUncertainMessage;

  /// No description provided for @aboveTreatmentThreshold.
  ///
  /// In en, this message translates to:
  /// **'Above treatment threshold'**
  String get aboveTreatmentThreshold;

  /// No description provided for @pestRetryHint.
  ///
  /// In en, this message translates to:
  /// **'Get closer to the leaf/stem/berry in good light and retry.'**
  String get pestRetryHint;

  /// No description provided for @pestDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'AI estimate from one photo. Confirm the pest, economic threshold, and exact product and dose with a local agronomist before spraying.'**
  String get pestDisclaimer;

  /// No description provided for @berryGradingTitle.
  ///
  /// In en, this message translates to:
  /// **'Berry grading'**
  String get berryGradingTitle;

  /// No description provided for @exportCleanCluster.
  ///
  /// In en, this message translates to:
  /// **'Export-clean cluster'**
  String get exportCleanCluster;

  /// No description provided for @berryRetryHint.
  ///
  /// In en, this message translates to:
  /// **'Fill the frame with a berry cluster in good light and retry.'**
  String get berryRetryHint;

  /// No description provided for @berryDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'AI estimate from one photo. Confirm the diagnosis, exact dose, MRL and pre-harvest interval with a local agronomist before applying.'**
  String get berryDisclaimer;

  /// No description provided for @low.
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get low;

  /// No description provided for @analysingLeaf.
  ///
  /// In en, this message translates to:
  /// **'Analysing leaf with AI…'**
  String get analysingLeaf;

  /// No description provided for @analysingBerry.
  ///
  /// In en, this message translates to:
  /// **'Grading berries with AI…'**
  String get analysingBerry;

  /// No description provided for @analysingPest.
  ///
  /// In en, this message translates to:
  /// **'Inspecting for pests with AI…'**
  String get analysingPest;

  /// No description provided for @notPepperLeaf.
  ///
  /// In en, this message translates to:
  /// **'This doesn\'t look like a pepper leaf'**
  String get notPepperLeaf;

  /// No description provided for @notBerryCluster.
  ///
  /// In en, this message translates to:
  /// **'This doesn\'t look like a berry cluster'**
  String get notBerryCluster;

  /// No description provided for @notPepperPlant.
  ///
  /// In en, this message translates to:
  /// **'This doesn\'t look like a pepper plant'**
  String get notPepperPlant;

  /// No description provided for @recommendedActionIpm.
  ///
  /// In en, this message translates to:
  /// **'Recommended action (IPM)'**
  String get recommendedActionIpm;

  /// No description provided for @belowThreshold.
  ///
  /// In en, this message translates to:
  /// **'Below treatment threshold — monitor only'**
  String get belowThreshold;

  /// No description provided for @clsHealthy.
  ///
  /// In en, this message translates to:
  /// **'Healthy'**
  String get clsHealthy;

  /// No description provided for @clsHealthyLeaves.
  ///
  /// In en, this message translates to:
  /// **'Healthy leaves'**
  String get clsHealthyLeaves;

  /// No description provided for @clsHealthyBerry.
  ///
  /// In en, this message translates to:
  /// **'Healthy berry'**
  String get clsHealthyBerry;

  /// No description provided for @clsLeafBlight.
  ///
  /// In en, this message translates to:
  /// **'Leaf Blight'**
  String get clsLeafBlight;

  /// No description provided for @clsLittleLeaf.
  ///
  /// In en, this message translates to:
  /// **'Little Leaf'**
  String get clsLittleLeaf;

  /// No description provided for @clsQuickWilt.
  ///
  /// In en, this message translates to:
  /// **'Quick Wilt'**
  String get clsQuickWilt;

  /// No description provided for @clsLaceBugDamage.
  ///
  /// In en, this message translates to:
  /// **'Lace bug damage'**
  String get clsLaceBugDamage;

  /// No description provided for @clsNutrientDeficiency.
  ///
  /// In en, this message translates to:
  /// **'Nutrient deficiency'**
  String get clsNutrientDeficiency;

  /// No description provided for @clsOtherDisease.
  ///
  /// In en, this message translates to:
  /// **'Other disease'**
  String get clsOtherDisease;

  /// No description provided for @clsOtherDamage.
  ///
  /// In en, this message translates to:
  /// **'Other damage'**
  String get clsOtherDamage;

  /// No description provided for @clsUncertain.
  ///
  /// In en, this message translates to:
  /// **'Uncertain'**
  String get clsUncertain;

  /// No description provided for @scanInstructionsTitle.
  ///
  /// In en, this message translates to:
  /// **'How to scan'**
  String get scanInstructionsTitle;

  /// No description provided for @scanInstructionsStep1.
  ///
  /// In en, this message translates to:
  /// **'Point the camera at the {object} and tap the shutter button.'**
  String scanInstructionsStep1(String object);

  /// No description provided for @scanInstructionsStep2.
  ///
  /// In en, this message translates to:
  /// **'Hold steady in good light and fill the frame with the subject.'**
  String get scanInstructionsStep2;

  /// No description provided for @scanInstructionsStep3.
  ///
  /// In en, this message translates to:
  /// **'Check what we found, then tap Show recommendations to see treatment advice.'**
  String get scanInstructionsStep3;

  /// No description provided for @scanInstructionsStart.
  ///
  /// In en, this message translates to:
  /// **'Got it, start scanning'**
  String get scanInstructionsStart;

  /// No description provided for @howToScan.
  ///
  /// In en, this message translates to:
  /// **'How to scan'**
  String get howToScan;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'si', 'ta'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'si':
      return AppLocalizationsSi();
    case 'ta':
      return AppLocalizationsTa();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
