import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../core/services/yolo_detector.dart';
import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../class_labels.dart';
import '../models/detection.dart';
import 'detection_overlay.dart';

/// Shows a captured photo with detection boxes drawn on it, plus a readable
/// summary of what was found.
///
/// The photo is displayed with [BoxFit.contain] so nothing is cropped away —
/// the overlay uses [OverlayFit.contain] to match.
class ScanResultView extends StatelessWidget {
  final Uint8List photo;
  final DetectionResult result;

  /// Label of the model that produced [result], e.g. "Berry".
  final String modelLabel;

  final VoidCallback onRetake;

  /// Opens the AI recommendation screen for the captured photo. Null hides
  /// the "Show recommendations" button (e.g. when nothing was detected).
  final VoidCallback? onShowRecommendations;

  const ScanResultView({
    super.key,
    required this.photo,
    required this.result,
    required this.modelLabel,
    required this.onRetake,
    this.onShowRecommendations,
  });

  @override
  Widget build(BuildContext context) {
    final detections = result.detections;

    return Column(
      children: [
        Expanded(
          child: Container(
            color: Colors.black,
            width: double.infinity,
            child: Stack(
              fit: StackFit.expand,
              children: [
                Image.memory(photo, fit: BoxFit.contain),
                CustomPaint(
                  painter: DetectionOverlay(detections, result.frameSize),
                ),
              ],
            ),
          ),
        ),
        _Summary(
          detections: detections,
          lowConfidence: result.lowConfidence,
          onRetake: onRetake,
          onShowRecommendations: onShowRecommendations,
        ),
      ],
    );
  }
}

class _Summary extends StatelessWidget {
  final List<Detection> detections;
  final bool lowConfidence;
  final VoidCallback onRetake;
  final VoidCallback? onShowRecommendations;

  const _Summary({
    required this.detections,
    required this.lowConfidence,
    required this.onRetake,
    required this.onShowRecommendations,
  });

  @override
  Widget build(BuildContext context) {
    // Only offer recommendations when there's an actual problem. If everything
    // detected is a "healthy" class, hide the button — no AI call needed.
    final hasProblem = detections.any(
      (d) => !d.className.toLowerCase().contains('healthy'),
    );
    final cs = Theme.of(context).colorScheme;
    final t = AppLocalizations.of(context);
    return Container(
      width: double.infinity,
      color: cs.surface,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              detections.isEmpty
                  ? t.nothingDetected
                  : t.findingsCount(detections.length),
              style: TextStyle(
                color: cs.onSurface,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (lowConfidence) ...[
              const SizedBox(height: 12),
              const _LowConfidenceNotice(),
            ],
            const SizedBox(height: 12),
            if (detections.isEmpty)
              Text(
                t.noMatchesHint,
                style: TextStyle(color: cs.onSurfaceVariant, height: 1.4),
              )
            else
              ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 160),
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: detections.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (_, i) => _DetectionRow(detections[i]),
                ),
              ),
            const SizedBox(height: 16),
            if (hasProblem && onShowRecommendations != null) ...[
              FilledButton.icon(
                onPressed: onShowRecommendations,
                style: FilledButton.styleFrom(
                  backgroundColor: cs.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                icon: const Icon(Icons.auto_awesome),
                label: Text(t.showRecommendations),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: onRetake,
                style: OutlinedButton.styleFrom(
                  foregroundColor: cs.onSurface,
                  side: BorderSide(color: cs.outlineVariant),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                icon: const Icon(Icons.photo_camera_outlined),
                label: Text(t.takeAnotherPhoto),
              ),
            ] else ...[
              if (detections.isNotEmpty && !hasProblem)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle, color: cs.primary, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          t.looksHealthy,
                          style: TextStyle(
                            color: cs.primary,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              FilledButton.icon(
                onPressed: onRetake,
                icon: const Icon(Icons.photo_camera_outlined),
                label: Text(t.takeAnotherPhoto),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Shown when the results came from the relaxed second pass. Without this the
/// user cannot tell a confident match from a marginal one.
class _LowConfidenceNotice extends StatelessWidget {
  const _LowConfidenceNotice();

  @override
  Widget build(BuildContext context) {
    final status = AppStatusColors.of(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: status.warningContainer,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: status.warning.withValues(alpha: 0.45),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.warning_amber_rounded,
            color: status.warning,
            size: 22,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              AppLocalizations.of(context).lowConfidenceNotice,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: status.onWarningContainer,
                height: 1.45,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DetectionRow extends StatelessWidget {
  final Detection detection;

  const _DetectionRow(this.detection);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: detection.color,
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            localizedClassName(
              detection.className,
              AppLocalizations.of(context),
            ),
            style: TextStyle(color: cs.onSurface, fontSize: 15),
            overflow: TextOverflow.ellipsis,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '${(detection.score * 100).toStringAsFixed(0)}%',
          style: TextStyle(
            color: cs.onSurfaceVariant,
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
