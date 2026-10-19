import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:iconly/iconly.dart';

import '../../l10n/app_localizations.dart';
import '../../shared/class_labels.dart';
import '../history/history_scope.dart';
import '../history/serialization/history_payload_codec.dart';
import 'analysis_ui.dart';
import 'berry_analysis.dart';
import 'ai_berry_service.dart';
import 'ai_errors.dart';
import 'remediation_engine.dart';

/// Captures a berry cluster, runs AI vision, then shows export-aware
/// remediation from the deterministic [RemediationEngine].
class BerryAnalysisScreen extends StatefulWidget {
  final Uint8List imageBytes;
  final Future<BerryAnalysis>? prefetch;
  final String? historyRecordKey;
  const BerryAnalysisScreen({
    super.key,
    required this.imageBytes,
    this.prefetch,
    this.historyRecordKey,
  });

  @override
  State<BerryAnalysisScreen> createState() => _BerryAnalysisScreenState();
}

class _BerryAnalysisScreenState extends State<BerryAnalysisScreen> {
  final _service = AiBerryService();
  late Future<BerryAnalysis>? _pending = widget.prefetch;
  bool _loading = true;
  BerryAnalysis? _result;
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
      final r = await (_pending ?? _service.analyze(widget.imageBytes));
      _pending = null;
      if (!mounted) return;
      setState(() {
        _result = r;
        _loading = false;
      });
      await _saveHistory(r);
    } catch (e, st) {
      logAiError('berry-analysis', e, st);
      if (!mounted) return;
      setState(() {
        _error = friendlyAiMessage(e, AppLocalizations.of(context));
        _loading = false;
      });
    }
  }

  Future<void> _saveHistory(BerryAnalysis result) async {
    final key = widget.historyRecordKey;
    final repository = HistoryScope.maybeOf(context);
    if (key == null || repository == null) return;
    try {
      final remediation = RemediationEngine.forAnalysis(result, _market);
      await repository.enrich(
        recordKey: key,
        outcomeCode: !result.isBerryCluster
            ? 'not_target'
            : result.healthy
            ? 'healthy'
            : 'detected',
        primaryClassCode: result.problemType,
        resultSchemaVersion: HistoryPayloadCodec.schemaVersion,
        resultJson: HistoryPayloadCodec.berry(result, remediation, _market),
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
      title: AppLocalizations.of(context).berryGradingTitle,
      titleIcon: IconlyBold.category,
      children: _body(),
    );
  }

  List<Widget> _body() {
    final t = AppLocalizations.of(context);
    if (_loading) {
      return [LoadingView(message: t.analysingBerry)];
    }
    if (_error != null) {
      return [ErrorView(message: _error!, onRetry: _run)];
    }
    return _result == null ? const [] : _resultBody(_result!);
  }

  List<Widget> _resultBody(BerryAnalysis r) {
    final t = AppLocalizations.of(context);
    if (!r.isBerryCluster) {
      return [
        RetakeView(
          title: t.notBerryCluster,
          message: r.summary.isNotEmpty ? r.summary : t.berryRetryHint,
          onRetake: () => Navigator.of(context).pop(),
        ),
      ];
    }

    final rem = RemediationEngine.forAnalysis(r, _market);
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
                      ? t.exportCleanCluster
                      : localizedClassName(r.problemType, t),
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

      MarketRow(dropdown: _marketDropdown()),

      SectionCard(
        icon: IconlyBold.shield_done,
        title: t.safeRemediation,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              rem.action,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w700,
                color: kText,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 14),
            for (final o in rem.options)
              OptionTile(
                name: o.name,
                mix: o.mix,
                method: o.method,
                allowed: o.allowedInMarket,
                restriction: o.restriction,
                phiNote: o.phi,
                isChemical: o.isChemical,
              ),
            for (final w in rem.warnings) _warning(w),
          ],
        ),
      ),

      if (rem.exportNote.isNotEmpty)
        InfoCard(
          icon: IconlyBold.bag,
          color: AppStatusColors.of(context).info,
          text: rem.exportNote,
        ),

      InfoCard(
        icon: IconlyBold.info_circle,
        color: Theme.of(context).colorScheme.outline,
        text: t.berryDisclaimer,
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
