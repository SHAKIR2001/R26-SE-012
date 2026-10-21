// =============================================================================
// File: price_forecast_screen.dart
// Purpose: Presents the price forecast screen mobile interface and user flow.
// =============================================================================
import 'package:flutter/material.dart';
import 'package:pepper_care/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/farmer_ui.dart';
import '../../recommendations/analysis_ui.dart' show FadeSlideIn;
import '../grading_forecast_localizations.dart';
import '../models/grading_forecast_result.dart';

/// Shows the frozen, grade-specific EAC farm-gate research outlook.
///
/// The forecast date is the target date of the saved forecast record. The
/// reference date is the latest historical price observation used as context;
/// neither value represents a live buyer offer or a guaranteed price.
class PriceForecastScreen extends StatelessWidget {
  const PriceForecastScreen({super.key, required this.result});

  final GradingForecastResult result;

  @override
  Widget build(BuildContext context) {
    // Build and return this widget's current interface.
    final t = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final status = AppStatusColors.of(context);
    // Read the grade-matched market result returned by the backend.
    final market = result.market;
    final direction = market.forecastDirection;
    final directionColor = switch (direction) {
      'UP' => status.success,
      'DOWN' => status.danger,
      _ => status.info,
    };
    final directionIcon = switch (direction) {
      'UP' => Icons.trending_up_rounded,
      'DOWN' => Icons.trending_down_rounded,
      _ => Icons.trending_flat_rounded,
    };

    return Scaffold(
      appBar: AppBar(
        title: Text(t.farmerPriceOutlookTitle),
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
              child: Container(
                padding: const EdgeInsets.all(26),
                decoration: BoxDecoration(
                  color: scheme.primary,
                  borderRadius: BorderRadius.circular(kCardRadius),
                ),
                child: Column(
                  children: [
                    Text(
                      t.farmerEstimatedPrice,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: scheme.onPrimary.withValues(alpha: 0.86),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 14),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      // Show the forecast price for the accepted grade only.
                      child: Text(
                        _price(t, market.forecastPrice),
                        style: theme.textTheme.displaySmall?.copyWith(
                          color: scheme.onPrimary,
                          fontWeight: FontWeight.w900,
                          letterSpacing: -1,
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 9,
                      ),
                      decoration: BoxDecoration(
                        color: scheme.onPrimary.withValues(alpha: 0.13),
                        borderRadius: BorderRadius.circular(22),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            directionIcon,
                            color: scheme.onPrimary,
                            size: 23,
                          ),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              farmerDirectionLabel(t, direction),
                              style: TextStyle(
                                color: scheme.onPrimary,
                                fontSize: 16,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 18),
            FadeSlideIn(
              delayMs: 70,
              child: FarmerNoticeCard(
                icon: market.forecastSignal == 'HIGH_UNCERTAINTY'
                    ? Icons.warning_amber_rounded
                    : Icons.info_outline_rounded,
                message: farmerPriceConfidenceMessage(t, market.forecastSignal),
                color: market.forecastSignal == 'HIGH_UNCERTAINTY'
                    ? status.warning
                    : directionColor,
              ),
            ),
            const SizedBox(height: 18),
            FadeSlideIn(
              delayMs: 140,
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t.farmerPriceDetails,
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 14),
                      _DetailRow(
                        icon: Icons.workspace_premium_outlined,
                        label: t.phase7ProjectGrade,
                        value: localizedGrade(t, market.priceGrade),
                      ),
                      _DetailRow(
                        icon: Icons.event_outlined,
                        label: t.farmerOutlookDate,
                        value:
                            market.forecastTargetDate ?? t.phase7NotAvailable,
                      ),
                      _DetailRow(
                        icon: Icons.receipt_long_outlined,
                        label: t.farmerReferencePrice,
                        value: _price(t, market.latestReferencePrice),
                      ),
                      _DetailRow(
                        icon: Icons.calendar_today_outlined,
                        label: t.farmerReferenceDate,
                        value:
                            market.latestReferenceDate ?? t.phase7NotAvailable,
                        secondary: true,
                        showDivider: false,
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 18),
            FarmerNoticeCard(
              icon: Icons.eco_outlined,
              message: t.farmerForecastNotice,
              color: scheme.primary,
            ),
            const SizedBox(height: 22),
            FilledButton.icon(
              onPressed: () => popToHome(context),
              icon: const Icon(Icons.home_outlined),
              label: Text(t.backToHome),
            ),
          ],
        ),
      ),
    );
  }

  // Process price for this flow.
  static String _price(AppLocalizations t, double? value) => value == null
      ? t.phase7NotAvailable
      : t.phase7PriceValue(value.toStringAsFixed(2));
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
    this.showDivider = true,
    this.secondary = false,
  });

  final IconData icon;
  final String label;
  final String value;
  final bool showDivider;
  final bool secondary;

  @override
  Widget build(BuildContext context) {
    // Build and return this widget's current interface.
    final theme = Theme.of(context);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                icon,
                color: secondary
                    ? theme.colorScheme.outline
                    : theme.colorScheme.primary,
                size: secondary ? 20 : 22,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  label,
                  style: (secondary
                          ? theme.textTheme.bodySmall
                          : theme.textTheme.bodyMedium)
                      ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
              ),
              const SizedBox(width: 12),
              Flexible(
                child: Text(
                  value,
                  textAlign: TextAlign.end,
                  style: (secondary
                          ? theme.textTheme.bodySmall
                          : theme.textTheme.bodyMedium)
                      ?.copyWith(
                        color: secondary
                            ? theme.colorScheme.onSurfaceVariant
                            : theme.colorScheme.onSurface,
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1),
      ],
    );
  }
}
