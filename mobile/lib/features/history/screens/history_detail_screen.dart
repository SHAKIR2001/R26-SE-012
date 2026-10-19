import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/class_labels.dart';
import '../../../shared/widgets/farmer_ui.dart';
import '../../grading_forecast/grading_forecast_localizations.dart';
import '../../grading_forecast/models/grading_forecast_result.dart';
import '../history_scope.dart';
import '../models/history_record.dart';
import '../serialization/history_payload_codec.dart';
import '../widgets/history_labels.dart';

class HistoryDetailScreen extends StatelessWidget {
  const HistoryDetailScreen({super.key, required this.record});

  final HistoryRecord record;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final repository = HistoryScope.maybeOf(context);
    final image = repository?.imageFile(record);
    final payload = HistoryPayloadCodec.tryDecode(record.resultJson);
    final locale = Localizations.localeOf(context).toLanguageTag();
    final recorded = DateFormat.yMMMMd(
      locale,
    ).add_jm().format(record.createdAtLocal);
    return Scaffold(
      appBar: AppBar(title: Text(t.historyDetailsTitle)),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(kCardRadius),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: _StoredHistoryImage(
                  image: image,
                  fallback: _missingImage(context, t),
                ),
              ),
            ),
            const SizedBox(height: 18),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      historyFeatureLabel(t, record.feature),
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 10),
                    _labelValue(
                      context,
                      t.historyOutcome,
                      historyOutcomeLabel(t, record),
                    ),
                    _labelValue(context, t.historyRecordedOn, recorded),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            FarmerNoticeCard(
              icon: Icons.offline_pin_outlined,
              message: t.historySavedOffline,
            ),
            const SizedBox(height: 14),
            if (payload == null)
              FarmerNoticeCard(
                icon: Icons.warning_amber_rounded,
                message: t.historyResultUnavailable,
                color: AppStatusColors.of(context).warning,
              )
            else
              ..._payloadWidgets(context, t, payload),
          ],
        ),
      ),
    );
  }

  Widget _missingImage(BuildContext context, AppLocalizations t) => Container(
    color: Theme.of(context).colorScheme.surfaceContainerHighest,
    alignment: Alignment.center,
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.broken_image_outlined, size: 42),
        const SizedBox(height: 8),
        Text(t.historyImageUnavailable),
      ],
    ),
  );

  List<Widget> _payloadWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> payload,
  ) {
    try {
      return switch (payload['kind']) {
        'grading_forecast' => _gradingWidgets(context, t, payload),
        'leaf_detail' => _leafWidgets(context, t, payload),
        'pest_detail' => _pestWidgets(context, t, payload),
        'berry_detail' => _berryWidgets(context, t, payload),
        'detection' => _detectionWidgets(context, t, payload),
        _ => [
          FarmerNoticeCard(
            icon: Icons.warning_amber_rounded,
            message: t.historyResultUnavailable,
            color: AppStatusColors.of(context).warning,
          ),
        ],
      };
    } catch (_) {
      return [
        FarmerNoticeCard(
          icon: Icons.warning_amber_rounded,
          message: t.historyResultUnavailable,
          color: AppStatusColors.of(context).warning,
        ),
      ];
    }
  }

  List<Widget> _gradingWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> payload,
  ) {
    final resultMap = _map(payload['result']);
    final result = GradingForecastResult.fromJson(resultMap);
    final widgets = <Widget>[
      _section(
        context,
        title: farmerResultTitle(t, result),
        icon: Icons.workspace_premium_outlined,
        children: [Text(farmerResultExplanation(t, result))],
      ),
    ];
    if (result.market.isAvailable) {
      widgets.add(
        _section(
          context,
          title: t.historyPriceSnapshot,
          icon: Icons.trending_up_rounded,
          children: [
            _labelValue(
              context,
              t.farmerEstimatedPrice,
              result.market.forecastPrice == null
                  ? t.phase7NotAvailable
                  : t.phase7PriceValue(
                      result.market.forecastPrice!.toStringAsFixed(2),
                    ),
            ),
            _labelValue(
              context,
              t.phase7ProjectGrade,
              localizedGrade(t, result.market.priceGrade),
            ),
            _labelValue(
              context,
              t.farmerOutlookDate,
              result.market.forecastTargetDate ?? t.phase7NotAvailable,
            ),
            _labelValue(
              context,
              t.farmerReferenceDate,
              result.market.latestReferenceDate ?? t.phase7NotAvailable,
            ),
          ],
        ),
      );
    }
    return widgets;
  }

  List<Widget> _leafWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> payload,
  ) {
    final analysis = _map(payload['analysis']);
    return [
      _analysisSummary(
        context,
        t,
        title: analysis['healthy'] == true
            ? t.healthyLeaf
            : localizedClassName(_text(analysis['disease_type']), t),
        summary: _text(analysis['summary']),
        severity: analysis['severity_percentage'],
        confidence: analysis['confidence'],
        affectedRegions: _text(analysis['affected_regions']),
      ),
      if (_strings(analysis['treatments']).isNotEmpty)
        _section(
          context,
          title: t.recommendedTreatment,
          icon: Icons.health_and_safety_outlined,
          children: [
            for (final treatment in _strings(analysis['treatments']))
              _bullet(context, treatment),
          ],
        ),
    ];
  }

  List<Widget> _pestWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> payload,
  ) {
    final analysis = _map(payload['analysis']);
    final decision = _map(payload['decision']);
    return [
      _analysisSummary(
        context,
        t,
        title: analysis['healthy'] == true
            ? t.noPestsFound
            : localizedClassName(_text(analysis['pest_type']), t),
        summary: _text(analysis['summary']),
        severity: analysis['severity_percentage'],
        confidence: analysis['confidence'],
        affectedRegions: _text(analysis['affected_regions']),
      ),
      ..._decisionWidgets(context, t, decision, noteKey: 'note'),
    ];
  }

  List<Widget> _berryWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> payload,
  ) {
    final analysis = _map(payload['analysis']);
    final decision = _map(payload['decision']);
    return [
      _analysisSummary(
        context,
        t,
        title: analysis['healthy'] == true
            ? t.exportCleanCluster
            : localizedClassName(_text(analysis['problem_type']), t),
        summary: _text(analysis['summary']),
        severity: analysis['severity_percentage'],
        confidence: analysis['confidence'],
        affectedRegions: _text(analysis['affected_regions']),
      ),
      ..._decisionWidgets(context, t, decision, noteKey: 'export_note'),
    ];
  }

  List<Widget> _detectionWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> payload,
  ) {
    final detections = _maps(payload['detections']);
    return [
      FarmerNoticeCard(
        icon: Icons.info_outline_rounded,
        message: t.historyDetectionOnly,
      ),
      if (payload['low_confidence'] == true)
        FarmerNoticeCard(
          icon: Icons.warning_amber_rounded,
          message: t.historyLowConfidence,
          color: AppStatusColors.of(context).warning,
        ),
      _section(
        context,
        title: t.historyDetectedItems,
        icon: Icons.center_focus_strong,
        children: detections.isEmpty
            ? [Text(t.historyNoDetectedItems)]
            : [
                for (final detection in detections)
                  _labelValue(
                    context,
                    localizedClassName(_text(detection['class_name']), t),
                    _percent(detection['score']),
                  ),
              ],
      ),
    ];
  }

  Widget _analysisSummary(
    BuildContext context,
    AppLocalizations t, {
    required String title,
    required String summary,
    required Object? severity,
    required Object? confidence,
    required String affectedRegions,
  }) => _section(
    context,
    title: title,
    icon: Icons.analytics_outlined,
    children: [
      if (summary.isNotEmpty) Text(summary),
      _labelValue(
        context,
        t.severity,
        _percent(severity, alreadyPercent: true),
      ),
      _labelValue(context, t.confidence, _percent(confidence)),
      if (affectedRegions.isNotEmpty)
        _labelValue(context, t.whatWeSee, affectedRegions),
    ],
  );

  List<Widget> _decisionWidgets(
    BuildContext context,
    AppLocalizations t,
    Map<String, dynamic> decision, {
    required String noteKey,
  }) {
    final options = _maps(decision['options']);
    final warnings = _strings(decision['warnings']);
    final note = _text(decision[noteKey]);
    return [
      if (_text(decision['action']).isNotEmpty)
        _section(
          context,
          title: t.historyTreatmentAction,
          icon: Icons.health_and_safety_outlined,
          children: [
            Text(_text(decision['action'])),
            for (final option in options) ...[
              const Divider(height: 24),
              Text(
                _text(option['name']),
                style: Theme.of(
                  context,
                ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              if (_text(option['mix']).isNotEmpty) Text(_text(option['mix'])),
              if (_text(option['method']).isNotEmpty)
                Text(_text(option['method'])),
              if (_text(option['restriction']).isNotEmpty)
                Text(
                  _text(option['restriction']),
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              if (_text(option['phi']).isNotEmpty) Text(_text(option['phi'])),
            ],
          ],
        ),
      if (warnings.isNotEmpty)
        _section(
          context,
          title: t.historyWarnings,
          icon: Icons.warning_amber_rounded,
          children: [for (final warning in warnings) _bullet(context, warning)],
        ),
      if (note.isNotEmpty)
        FarmerNoticeCard(icon: Icons.info_outline_rounded, message: note),
    ];
  }

  Widget _section(
    BuildContext context, {
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 14),
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ...children,
          ],
        ),
      ),
    ),
  );

  Widget _labelValue(BuildContext context, String label, String value) =>
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Flexible(
              child: Text(
                value,
                textAlign: TextAlign.end,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
      );

  Widget _bullet(BuildContext context, String value) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(top: 6),
          child: Icon(Icons.circle, size: 7),
        ),
        const SizedBox(width: 10),
        Expanded(child: Text(value)),
      ],
    ),
  );

  static Map<String, dynamic> _map(Object? value) {
    if (value is! Map) throw const FormatException('Expected map.');
    return value.map((key, item) => MapEntry(key.toString(), item));
  }

  static List<Map<String, dynamic>> _maps(Object? value) => value is List
      ? value.whereType<Map>().map((item) => _map(item)).toList()
      : const [];

  static List<String> _strings(Object? value) => value is List
      ? value
            .map((item) => item.toString())
            .where((item) => item.isNotEmpty)
            .toList()
      : const [];

  static String _text(Object? value) => value?.toString() ?? '';

  static String _percent(Object? value, {bool alreadyPercent = false}) {
    final number = value is num ? value.toDouble() : double.tryParse('$value');
    if (number == null || !number.isFinite) return '—';
    final percent = alreadyPercent ? number : number * 100;
    return '${percent.toStringAsFixed(0)}%';
  }
}

class _StoredHistoryImage extends StatefulWidget {
  const _StoredHistoryImage({required this.image, required this.fallback});

  final File? image;
  final Widget fallback;

  @override
  State<_StoredHistoryImage> createState() => _StoredHistoryImageState();
}

class _StoredHistoryImageState extends State<_StoredHistoryImage> {
  late Future<bool> _exists;

  @override
  void initState() {
    super.initState();
    _exists = widget.image?.exists() ?? Future<bool>.value(false);
  }

  @override
  void didUpdateWidget(covariant _StoredHistoryImage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.image?.path != widget.image?.path) {
      _exists = widget.image?.exists() ?? Future<bool>.value(false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final file = widget.image;
    if (file == null) return widget.fallback;
    return FutureBuilder<bool>(
      future: _exists,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.data != true) return widget.fallback;
        return Image.file(
          file,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => widget.fallback,
        );
      },
    );
  }
}
