import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:iconly/iconly.dart';

import '../../l10n/app_localizations.dart';
import '../../shared/class_labels.dart';
import '../history/history_scope.dart';
import '../history/serialization/history_payload_codec.dart';
import 'analysis_ui.dart';
import 'ai_errors.dart';
import 'ai_leaf_service.dart';
import 'leaf_analysis.dart';

/// Runs an AI leaf analysis on a captured photo and shows the result.
///
/// [prefetch] lets the scanner start the analysis in the background the moment
/// a problem is detected, so the result is often ready by the time the user
/// opens this screen. If null (or after a retry), it runs its own call.
class LeafAnalysisScreen extends StatefulWidget {
  final Uint8List imageBytes;
  final Future<LeafAnalysis>? prefetch;
  final String? detectedClass;
  final String? historyRecordKey;

  const LeafAnalysisScreen({
    super.key,
    required this.imageBytes,
    this.prefetch,
    this.detectedClass,
    this.historyRecordKey,
  });

  @override
  State<LeafAnalysisScreen> createState() => _LeafAnalysisScreenState();
}

// Holds and manages the changing state of the analysis screen
class _LeafAnalysisScreenState extends State<LeafAnalysisScreen> {
  final _service = AiLeafService();
  late Future<LeafAnalysis>? _pending = widget.prefetch;
  bool _loading = true;
  LeafAnalysis? _result;
  String? _error;

  // Starts the leaf analysis as soon as the screen state is initialized.
  @override
  void initState() {
    super.initState();
    _run();
  }

  // Runs the AI analysis and updates the UI with its result or an error.
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
                knownDisease: widget.detectedClass,
              ));
      _pending =
          null; // a retry re-calls the service instead of the dead future
      if (!mounted) return;
      if (!mounted) return;
      setState(() {
        _result = r;
        _loading = false;
      });
      await _saveHistory(r);
    } catch (e, st) {
      logAiError('leaf-analysis', e, st);
      if (!mounted) return;
      setState(() {
        _error = friendlyAiMessage(e, AppLocalizations.of(context));
        _loading = false;
      });
    }
  }

  Future<void> _saveHistory(LeafAnalysis result) async {
    final key = widget.historyRecordKey;
    final repository = HistoryScope.maybeOf(context);
    if (key == null || repository == null) return;
    try {
      await repository.enrich(
        recordKey: key,
        outcomeCode: !result.isPepperLeaf
            ? 'not_target'
            : result.healthy
            ? 'healthy'
            : 'detected',
        primaryClassCode: result.diseaseType,
        resultSchemaVersion: HistoryPayloadCodec.schemaVersion,
        resultJson: HistoryPayloadCodec.leaf(result),
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
      title: AppLocalizations.of(context).leafAnalysisTitle,
      titleIcon: IconlyBold.activity,
      children: _body(),
    );
  }

  // Selects the appropriate content for the current loading, error, or result state.
  List<Widget> _body() {
    final t = AppLocalizations.of(context);
    if (_loading) {
      return [LoadingView(message: t.analysingLeaf)];
    }
    if (_error != null) {
      return [ErrorView(message: _error!, onRetry: _run)];
    }
    return _result == null ? const [] : _resultBody(_result!);
  }

  // Builds the appropriate result widgets from the completed leaf analysis.
  List<Widget> _resultBody(LeafAnalysis r) {
    final t = AppLocalizations.of(context);
    if (!r.isPepperLeaf) {
      return [
        RetakeView(
          title: t.notPepperLeaf,
          message: r.summary.isNotEmpty ? r.summary : t.leafRetryHint,
          onRetake: () => Navigator.of(context).pop(),
        ),
      ];
    }

    final accent = r.healthy
        ? Theme.of(context).colorScheme.primary
        : bandColor(context, r.severityBand);
    final sev = r.severityPercentage ?? 0;
    final infoColor = AppStatusColors.of(context).info;

    // Assemble the diagnosis summary and supporting detail sections.
    return [
      // headline
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
                      ? t.healthyLeaf
                      : localizedClassName(r.diseaseType, t),
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
      Row(
        children: [
          Expanded(
            child: StatTile(
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
                      sev,
                      suffix: '%',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: accent,
                      ),
                    ),
              sub: r.severityBand.toUpperCase(),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: StatTile(
              icon: IconlyBold.activity,
              label: t.confidence,
              color: infoColor,
              value: CountUp(
                r.confidence * 100,
                suffix: '%',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: infoColor,
                ),
              ),
              sub: _conf(r.confidence, t),
            ),
          ),
        ],
      ),

      if (!r.healthy && sev > 0) ...[
        const SizedBox(height: 18),
        AnimatedBar(fraction: sev / 100, color: accent),
      ],

      // =====================================================
      // AFFECTED REGIONS
      // =====================================================

      // Display where the AI detected visible symptoms
      if (r.affectedRegions.isNotEmpty)
        SectionCard(
          icon: IconlyBold.show,
          title: t.whatWeSee,
          child: Text(
            r.affectedRegions,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: kTextSub, height: 1.48),
          ),
        ),

      // =====================================================
      // TREATMENT RECOMMENDATIONS
      // =====================================================

      // Display treatment suggestions only when treatments exist

      if (r.treatments.isNotEmpty)
        SectionCard(
          icon: IconlyBold.shield_done,
          title: t.recommendedTreatment,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (int i = 0; i < r.treatments.length; i++)
                Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 26,
                        height: 26,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: accent.withValues(
                            alpha:
                                Theme.of(context).brightness == Brightness.dark
                                ? 0.25
                                : 0.15,
                          ),
                          shape: BoxShape.circle,
                        ),
                        child: Text(
                          '${i + 1}',
                          style: TextStyle(
                            fontSize: 13,
                            color: accent,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Text(
                          r.treatments[i],
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(height: 1.45, color: kText),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),

      InfoCard(
        icon: IconlyBold.info_circle,
        color: Theme.of(context).colorScheme.outline,
        text: t.leafDisclaimer,
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

  String _conf(double c, AppLocalizations t) =>
      c >= 0.75 ? t.high : (c >= 0.5 ? t.medium : t.low);
}
