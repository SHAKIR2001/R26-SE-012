import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:pepper_care/l10n/app_localizations.dart';

import '../../../shared/widgets/farmer_ui.dart';
import '../../history/history_scope.dart';
import '../../history/models/history_record.dart';
import '../../history/serialization/history_payload_codec.dart';
import '../grading_forecast_localizations.dart';
import '../models/grading_forecast_result.dart';
import '../services/grading_forecast_analysis_service.dart';
import '../services/grading_forecast_api_service.dart'
    show GradingForecastApiException;
import 'berry_quality_result_screen.dart';

class ProcessingScreen extends StatefulWidget {
  const ProcessingScreen({
    super.key,
    required this.imageBytes,
    required this.imageName,
  });

  final Uint8List imageBytes;
  final String imageName;

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

/// Runs one backend analysis and translates its outcome into a result screen.
///
/// A successful HTTP response is still subject to strict contract validation in
/// `GradingForecastResult`; a response that violates rejection-first or
/// grade-specific routing rules is treated as an error, not displayed.
class _ProcessingScreenState extends State<ProcessingScreen> {
  final _analysisService = GradingForecastAnalysisService();
  final String _historyRecordKey = newHistoryRecordKey();

  bool _isRunning = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _start();
  }

  Future<void> _start() async {
    setState(() {
      _isRunning = true;
      _errorMessage = null;
    });

    try {
      // The service performs upload validation and parses the frozen Phase 6
      // contract. No client-side prediction or price calculation is performed.
      final result = await _analysisService.analyzeBytes(
        widget.imageBytes,
        widget.imageName,
      );
      if (!mounted) return;
      // History is best-effort persistence; failure to save must not turn a
      // valid analysis into a fabricated error or alter the displayed result.
      unawaited(_saveHistory(result));
      Navigator.of(context).pushReplacement(
        MaterialPageRoute<void>(
          builder: (_) => BerryQualityResultScreen(
            imageBytes: widget.imageBytes,
            result: result,
          ),
        ),
      );
    } on GradingForecastApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _isRunning = false;
        _errorMessage = error.localizedMessage(AppLocalizations.of(context));
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isRunning = false;
        _errorMessage = AppLocalizations.of(context).analyzeFailed;
      });
    }
  }

  Future<void> _saveHistory(GradingForecastResult result) async {
    final repository = HistoryScope.maybeOf(context);
    if (repository == null) return;
    final messenger = ScaffoldMessenger.maybeOf(context);
    final failureMessage = AppLocalizations.of(context).historySaveFailed;
    try {
      await repository.saveNew(
        recordKey: _historyRecordKey,
        feature: HistoryFeature.gradingForecast,
        stage: HistoryAnalysisStage.detailed,
        outcomeCode: switch (result.grading.status) {
          'ACCEPTED' => 'accepted',
          'REJECTED' => 'rejected',
          _ => 'uncertain',
        },
        primaryClassCode: result.grading.grade ?? result.grading.decision,
        imageBytes: widget.imageBytes,
        resultSchemaVersion: HistoryPayloadCodec.schemaVersion,
        resultJson: HistoryPayloadCodec.grading(result),
        localeCode: Localizations.localeOf(context).languageCode,
      );
    } catch (_) {
      if (messenger?.mounted ?? false) {
        messenger!.showSnackBar(SnackBar(content: Text(failureMessage)));
      }
    }
  }

  @override
  void dispose() {
    _analysisService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: Text(t.processing)),
      body: SafeArea(
        top: false,
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(22),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(26),
                  child: _isRunning
                      ? Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 76,
                              height: 76,
                              decoration: BoxDecoration(
                                color: scheme.primaryContainer,
                                shape: BoxShape.circle,
                              ),
                              child: Padding(
                                padding: const EdgeInsets.all(20),
                                child: CircularProgressIndicator(
                                  strokeWidth: 3,
                                  color: scheme.onPrimaryContainer,
                                ),
                              ),
                            ),
                            const SizedBox(height: 22),
                            Text(
                              t.processingFarmerTitle,
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(height: 10),
                            Text(
                              t.phase7ProcessingMessage,
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodyLarge
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    height: 1.5,
                                  ),
                            ),
                          ],
                        )
                      : Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.cloud_off_outlined,
                              size: 48,
                              color: scheme.error,
                            ),
                            const SizedBox(height: 14),
                            Text(
                              t.processingErrorTitle,
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(height: 10),
                            Text(
                              _errorMessage ?? t.backendError,
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodyLarge
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    height: 1.5,
                                  ),
                            ),
                            const SizedBox(height: 22),
                            SizedBox(
                              width: double.infinity,
                              child: FilledButton(
                                onPressed: _start,
                                child: Text(t.retry),
                              ),
                            ),
                            TextButton(
                              onPressed: () => popToHome(context),
                              child: Text(t.backToHome),
                            ),
                          ],
                        ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
