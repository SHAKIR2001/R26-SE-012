import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../shared/models/scanner_model_config.dart';
import '../../shared/widgets/scanner_view.dart';

const _berryConfig = ScannerModelConfig(
  id: 'berry',
  label: 'Berry',
  assetPath: 'assets/models/new_berry_yolo_model_int8.tflite',
  classNames: ['healthy_berry', 'lace_bug_damage'],
  classColors: [Color(0xFF2ECC71), Color(0xFFE67E22)],
);

class BerryScannerScreen extends StatelessWidget {
  const BerryScannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScannerView(
      modelConfig: _berryConfig,
      title: AppLocalizations.of(context).homeBerryScan,
    );
  }
}
