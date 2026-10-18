// Used for handling image data as bytes.

import 'dart:typed_data';

// Flutter Material UI package.
import 'package:flutter/material.dart';

// Icon library used throughout the UI.
import 'package:iconly/iconly.dart';

import '../../l10n/app_localizations.dart';
import '../../shared/class_labels.dart';
import '../history/history_scope.dart';
import '../history/serialization/history_payload_codec.dart';
import 'analysis_ui.dart';

// Handles and converts AI-related errors into user-friendly messages.
import 'ai_errors.dart';

// AI service responsible for analysing the pest image.
import 'ai_pest_service.dart';
import 'pest_analysis.dart';
import 'pest_treatment_engine.dart';
import 'remediation_engine.dart' show Market;

/// Captures a pepper-plant photo, runs AI pest vision, then shows IPM +
/// export-aware treatment from the deterministic [PestTreatmentEngine].
class PestAnalysisScreen extends StatefulWidget {
  final Uint8List imageBytes;
  final Future<PestAnalysis>? prefetch;
  final String? detectedClass;
  final String? historyRecordKey;
  const PestAnalysisScreen({
    super.key,
    required this.imageBytes,
    this.prefetch,
    this.detectedClass,
    this.historyRecordKey,
  });

  @override
  State<PestAnalysisScreen> createState() => _PestAnalysisScreenState();
}

class _PestAnalysisScreenState extends State<PestAnalysisScreen> {
  final _service = AiPestService();
  late Future<PestAnalysis>? _pending = widget.prefetch;
  bool _loading = true;
  PestAnalysis? _result;
  String? _error;
  Market _market = Market.eu;

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });
    try {
      final r =
          await (_pending ??
              _service.analyze(
                widget.imageBytes,
                knownPest: widget.detectedClass,
              ));
      _pending = null;
      if (!mounted) return;
      setState(() {
        _result = r;
        _loading = false;
      });
      await _saveHistory(r);
    } catch (e, st) {
      logAiError('pest-analysis', e, st);
      if (!mounted) return;
      setState(() {
        _error = friendlyAiMessage(e, AppLocalizations.of(context));
        _loading = false;
      });
    }
  }

  Future<void> _saveHistory(PestAnalysis result) async {
    final key = widget.historyRecordKey;
    final repository = HistoryScope.maybeOf(context);
    if (key == null || repository == null) return;
    try {
      final treatment = PestTreatmentEngine.forAnalysis(result, _market);
      await repository.enrich(
        recordKey: key,
        outcomeCode: !result.isPepperPlant
            ? 'not_target'
            : result.isUncertain
            ? 'uncertain'
            : result.healthy
            ? 'healthy'
            : 'detected',
        primaryClassCode: result.pestType,
        resultSchemaVersion: HistoryPayloadCodec.schemaVersion,
        resultJson: HistoryPayloadCodec.pest(result, treatment, _market),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).historySaveFailed)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnalysisScaffold(
      imageBytes: widget.imageBytes,
      title: AppLocalizations.of(context).pestAnalysisTitle,
      titleIcon: IconlyBold.scan,
      children: _body(),
    );
  }

  List<Widget> _body() {
    final t = AppLocalizations.of(context);
    if (_loading) {
      return [LoadingView(message: t.analysingPest)];
    }
    if (_error != null) {
      return [ErrorView(message: _error!, onRetry: _run)];
    }
    return _result == null ? const [] : _resultBody(_result!);
  }

  List<Widget> _resultBody(PestAnalysis r) {
    final t = AppLocalizations.of(context);
    if (!r.isPepperPlant) {
      return [
        RetakeView(
          title: t.notPepperPlant,
          message: r.summary.isNotEmpty ? r.summary : t.pestRetryHint,
          onRetake: () => Navigator.of(context).pop(),
        ),
      ];
    }

    if (r.isUncertain) {
      return [
        RetakeView(
          title: t.pestUncertainTitle,
          message: t.pestUncertainMessage,
          onRetake: () => Navigator.of(context).pop(),
        ),
      ];
    }

    final plan = PestTreatmentEngine.forAnalysis(r, _market);
    final accent = r.healthy
        ? Theme.of(context).colorScheme.primary
        : bandColor(context, r.severityBand);

    return [
      Row(
        children: [
          Icon(
            r.healthy ? IconlyBold.shield_done : IconlyBold.danger,
            color: accent,
            size: 32,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  r.healthy
                      ? t.noPestsFound
                      : localizedClassName(r.pestType, t),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: kText,
                  ),
                ),
                if (r.summary.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      r.summary,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: kTextSub,
                        height: 1.4,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),

      const SizedBox(height: 20),
      StatTile(
        icon: IconlyBold.chart,
        label: t.severity,
        color: accent,
        value: r.healthy
            ? Text(
                '—',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Theme.of(context).colorScheme.primary,
                ),
              )
            : CountUp(
                r.severityPercentage,
                suffix: '%',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: accent,
                ),
              ),
        sub: r.severityBand.toUpperCase(),
      ),

      // Economic Threshold badge — the key pest decision.
      _thresholdBadge(plan.aboveThreshold),

      MarketRow(dropdown: _marketDropdown()),

      SectionCard(
        icon: IconlyBold.shield_done,
        title: t.recommendedActionIpm,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              plan.action,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w700,
                color: kText,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 14),
            for (final o in plan.options)
              OptionTile(
                name: o.name,
                mix: o.mix,
                method: o.method,
                allowed: o.allowedInMarket,
                restriction: o.restriction,
                phiNote: o.phi,
                isChemical: o.isChemical,
              ),
            for (final w in plan.warnings) _warning(w),
          ],
        ),
      ),

      if (plan.note.isNotEmpty)
        InfoCard(
          icon: IconlyBold.bag,
          color: AppStatusColors.of(context).info,
          text: plan.note,
        ),

      InfoCard(
        icon: IconlyBold.info_circle,
        color: Theme.of(context).colorScheme.outline,
        text: t.pestDisclaimer,
      ),

      const SizedBox(height: 20),
      FilledButton.icon(
        onPressed: () => Navigator.of(context).pop(),
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: const StadiumBorder(),
        ),
        icon: const Icon(IconlyLight.camera, size: 20),
        label: Text(t.takeAnotherPhoto),
      ),
    ];
  }

  Widget _thresholdBadge(bool above) {
    final t = AppLocalizations.of(context);
    final status = AppStatusColors.of(context);
    final color = above
        ? status.warning
        : Theme.of(context).colorScheme.primary;
    return Container(
      margin: const EdgeInsets.only(top: 18),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      decoration: BoxDecoration(
        color: color.withValues(
          alpha: Theme.of(context).brightness == Brightness.dark ? 0.18 : 0.10,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withValues(
            alpha: Theme.of(context).brightness == Brightness.dark
                ? 0.45
                : 0.35,
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(
            above ? IconlyBold.danger : IconlyBold.show,
            size: 22,
            color: color,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              above ? t.aboveTreatmentThreshold : t.belowThreshold,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: kText,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _marketDropdown() => DropdownButton<Market>(
    value: _market,
    underline: const SizedBox.shrink(),
    borderRadius: BorderRadius.circular(12),
    dropdownColor: Theme.of(context).colorScheme.surfaceContainerHigh,
    style: Theme.of(
      context,
    ).textTheme.titleSmall?.copyWith(color: kText, fontWeight: FontWeight.w700),
    icon: Icon(IconlyLight.arrow_down, size: 18, color: kText),
    onChanged: (m) => setState(() => _market = m ?? _market),
    items: [
      for (final m in Market.values)
        DropdownMenuItem(value: m, child: Text(m.label)),
    ],
  );

  Widget _warning(String w) {
    final warningColor = AppStatusColors.of(context).warning;
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(IconlyBold.danger, size: 16, color: warningColor),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              w,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: warningColor,
                height: 1.4,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
