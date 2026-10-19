// Imports Flutter Material package for UI components

import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';
import '../../../shared/models/scanner_model_config.dart';

// Imports the reusable scanner UI that performs the scanning process
import '../../../shared/widgets/scanner_view.dart';

// Configuration details for the pest detection YOLO model
const _pestConfig = ScannerModelConfig(
  // Unique ID used to identify this scanner/model
  id: 'pest',

  // Display name of the model
  label: 'Pest',

  // Path to the trained TensorFlow Lite pest detection model
  assetPath: 'assets/models/new_pest_yolo_model_int8.tflite',

  // Pest classes that the AI model can detect
  // The order must match the class order used during model training
  classNames: [
    'Diconocoris distanti',
    'Gynaikothrips karny',
    'Pterolopha annulata',
    'healthy',
  ],

    // Bounding box/display color for each detected class
  // Each color corresponds to the class at the same index above
  classColors: [
    Color(0xFFE74C3C),
    Color(0xFFE67E22),
    Color(0xFF9B59B6),
    Color(0xFF2ECC71),
  ],
);

class PestScannerScreen extends StatelessWidget {
  const PestScannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScannerView(
      modelConfig: _pestConfig,
      title: AppLocalizations.of(context).homePests,
    );
  }
}
