import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';
import '../../../shared/models/scanner_model_config.dart';
import '../../../shared/widgets/scanner_view.dart';

// Defines the leaf-disease model and the labels displayed for its predictions.
// Keep [classNames] and [classColors] in the same order as the model's output
// classes so that each detection receives the correct label and color.
const _leafConfig = ScannerModelConfig(
  id: 'leaf',
  label: 'Leaf',
  assetPath: 'assets/models/new_leaf_yolo_model_int8.tflite',
  classNames: ['Healthy leaves', 'Leaf Blight', 'Little Leaf', 'Quick Wilt'],
  classColors: [
    Color(0xFF2ECC71),
    Color(0xFFE74C3C),
    Color(0xFFE67E22),
    Color(0xFF9B59B6),
  ],
);

/// Displays the shared scanner UI configured for leaf-disease detection.
class LeafScannerScreen extends StatelessWidget {
  const LeafScannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScannerView(
      modelConfig: _leafConfig,
      title: AppLocalizations.of(context).homeLeafHealth,
    );
  }
}
