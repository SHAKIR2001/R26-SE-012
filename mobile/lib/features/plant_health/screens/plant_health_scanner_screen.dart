import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';
import '../../../shared/models/scanner_model_config.dart';
import '../../../shared/widgets/scanner_view.dart';

/// Combined leaf-disease + pest scanner. The AI (see AiDetectionService, domain
/// 'plant') decides leaf-vs-pest and the specific class from the merged
/// vocabulary; recommendations then route to the leaf or pest flow.
///
/// Gemini is the primary path and covers both leaf and pest. If cloud
/// classification is unavailable, the scanner runs both original on-device
/// models so the fallback still covers leaf disease and pests.
const _plantConfig = ScannerModelConfig(
  id: 'plant',
  label: 'Plant Health',
  assetPath: 'assets/models/new_leaf_yolo_model_int8.tflite',
  classNames: ['Healthy leaves', 'Leaf Blight', 'Little Leaf', 'Quick Wilt'],
  classColors: [
    Color(0xFF2ECC71),
    Color(0xFFE74C3C),
    Color(0xFFE67E22),
    Color(0xFF9B59B6),
  ],
);

// This is the unchanged pest model contract from PestScannerScreen. Keeping it
// as an additional fallback lets the combined screen remain useful offline
// without changing either model's classes, thresholds, or preprocessing.
const _plantPestFallbackConfig = ScannerModelConfig(
  id: 'pest',
  label: 'Pest',
  assetPath: 'assets/models/new_pest_yolo_model_int8.tflite',
  classNames: [
    'Diconocoris distanti',
    'Gynaikothrips karny',
    'Pterolopha annulata',
    'healthy',
  ],
  classColors: [
    Color(0xFFE74C3C),
    Color(0xFFE67E22),
    Color(0xFF9B59B6),
    Color(0xFF2ECC71),
  ],
);

class PlantHealthScannerScreen extends StatelessWidget {
  const PlantHealthScannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScannerView(
      modelConfig: _plantConfig,
      additionalFallbackConfigs: const [_plantPestFallbackConfig],
      title: AppLocalizations.of(context).homeLeafPest,
    );
  }
}
