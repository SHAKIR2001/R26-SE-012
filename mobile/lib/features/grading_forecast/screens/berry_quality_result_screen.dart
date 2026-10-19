import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:pepper_care/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/farmer_ui.dart';
import '../../recommendations/analysis_ui.dart' show FadeSlideIn;
import '../grading_forecast_localizations.dart';
import '../models/grading_forecast_result.dart';
import 'price_forecast_screen.dart';

/// Presents the farmer-facing grading outcome without exposing internal
/// research trace fields as the primary result.
///
/// Rejected and uncertain outcomes intentionally have no price action. Only an
/// accepted response with available, grade-matched market evidence can open the
/// price-outlook screen.
class BerryQualityResultScreen extends StatelessWidget {
  const BerryQualityResultScreen({
    super.key,
    required this.imageBytes,
    required this.result,
  });

  final Uint8List imageBytes;
  final GradingForecastResult result;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final status = AppStatusColors.of(context);
    final accepted = result.grading.status == 'ACCEPTED';
    final rejected = result.grading.status == 'REJECTED';
    final accent = accepted
        ? status.success
        : rejected
        ? status.danger
        : status.warning;
    final icon = accepted
        ? Icons.workspace_premium_rounded
        : rejected
        ? Icons.image_not_supported_outlined
        : Icons.help_outline_rounded;

    return Scaffold(
      appBar: AppBar(
        title: Text(t.berryQualityResult),
        actions: [
          IconButton(
            tooltip: t.backToHome,
            onPressed: () => popToHome(context),
            icon: const Icon(Icons.home_outlined),
          ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          children: [
            FadeSlideIn(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(kCardRadius),
                child: AspectRatio(
                  aspectRatio: 16 / 9,
                  child: Image.memory(imageBytes, fit: BoxFit.cover),
                ),
              ),
            ),
            const SizedBox(height: 20),
            FadeSlideIn(
              delayMs: 70,
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Container(
                        width: 68,
                        height: 68,
                        decoration: BoxDecoration(
                          color: accent.withValues(
                            alpha: theme.brightness == Brightness.dark
                                ? 0.20
                                : 0.12,
                          ),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(icon, color: accent, size: 34),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        farmerResultTitle(t, result),
                        textAlign: TextAlign.center,
                        style: theme.textTheme.headlineMedium?.copyWith(
                          color: accent,
                          fontWeight: FontWeight.w900,
                          height: 1.15,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        farmerResultExplanation(t, result),
                        textAlign: TextAlign.center,
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                          height: 1.45,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 18),
            if (!accepted)
              FadeSlideIn(
                delayMs: 140,
                child: FarmerNoticeCard(
                  icon: Icons.photo_camera_outlined,
                  message: farmerRetakeGuidance(t, result),
                  color: accent,
                ),
              )
            else
              FadeSlideIn(
                delayMs: 140,
                child: FarmerNoticeCard(
                  icon: Icons.verified_user_outlined,
                  message: t.farmerGradeNotice,
                ),
              ),
            const SizedBox(height: 22),
            if (result.market.isAvailable)
              FilledButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => PriceForecastScreen(result: result),
                  ),
                ),
                icon: const Icon(Icons.trending_up_rounded),
                label: Text(t.farmerViewPriceOutlook),
              ),
            if (result.market.isAvailable) const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Icons.refresh_rounded),
              label: Text(t.farmerAnalyzeAnother),
            ),
            const SizedBox(height: 4),
            TextButton.icon(
              onPressed: () => popToHome(context),
              icon: const Icon(Icons.home_outlined),
              label: Text(t.backToHome),
            ),
          ],
        ),
      ),
    );
  }
}
