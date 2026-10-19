import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:pepper_care/l10n/app_localizations.dart';

import '../../../shared/widgets/farmer_ui.dart';
import 'processing_screen.dart';

class BerryCaptureScreen extends StatefulWidget {
  const BerryCaptureScreen({super.key});

  @override
  State<BerryCaptureScreen> createState() => _BerryCaptureScreenState();
}

/// Collects one original pepper sample image before backend analysis.
///
/// Capture is deliberately separate from inference: the screen only validates
/// the local file and forwards its bytes to the processing route.
class _BerryCaptureScreenState extends State<BerryCaptureScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _selected;
  Uint8List? _selectedBytes;

  Future<void> _pick(ImageSource source) async {
    try {
      // Preserve the selected bytes for the frozen Phase 7 backend pipeline.
      // Resizing or JPEG recompression here changes the blur, detection, and
      // class-margin inputs used by the frozen rejection/uncertainty gates.
      final picked = await _picker.pickImage(source: source);
      if (!mounted) return;
      if (picked == null) {
        setState(() {
          _selected = null;
          _selectedBytes = null;
        });
        return;
      }
      // Keep the exact picker output. The backend applies the frozen quality
      // and model preprocessing rules, so the mobile client must not resize or
      // recompress the sample first.
      final bytes = await picked.readAsBytes();
      if (!mounted) return;
      if (bytes.isEmpty) {
        _showSelectionError(AppLocalizations.of(context).phase7EmptyImage);
        return;
      }
      if (bytes.length > 10 * 1024 * 1024) {
        _showSelectionError(AppLocalizations.of(context).phase7ImageTooLarge);
        return;
      }
      setState(() {
        _selected = picked;
        _selectedBytes = bytes;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context).couldNotOpenCameraGallery),
        ),
      );
    }
  }

  void _showSelectionError(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  void _analyze() {
    final selected = _selected;
    final bytes = _selectedBytes;
    if (selected == null) return;
    if (bytes == null || bytes.isEmpty) return;

    // The processing route owns the asynchronous request and result transition
    // so this capture screen remains focused on image selection.
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) =>
            ProcessingScreen(imageBytes: bytes, imageName: selected.name),
      ),
    );
  }

  void _showPhotoGuide() {
    final t = AppLocalizations.of(context);
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              FarmerSectionHeader(
                title: t.captureGuideTitle,
                subtitle: t.captureGuideSubtitle,
              ),
              const SizedBox(height: 20),
              GuideStepCard(
                number: 1,
                icon: Icons.light_mode_outlined,
                title: t.guideLightingTitle,
                body: t.guideLightingBody,
              ),
              GuideStepCard(
                number: 2,
                icon: Icons.center_focus_strong,
                title: t.guidePositionTitle,
                body: t.guidePositionBody,
              ),
              GuideStepCard(
                number: 3,
                icon: Icons.motion_photos_off_outlined,
                title: t.captureAvoidBlurTitle,
                body: t.captureAvoidBlurBody,
              ),
              const SizedBox(height: 8),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text(t.gotIt),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final imageBytes = _selectedBytes;
    final canAnalyze = imageBytes != null && imageBytes.isNotEmpty;

    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(t.captureBerryTitle),
        actions: [
          IconButton(
            tooltip: t.howToScan,
            onPressed: _showPhotoGuide,
            icon: const Icon(Icons.help_outline_rounded),
          ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                t.captureFarmerPrompt,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: Card(
                  clipBehavior: Clip.antiAlias,
                  child: Padding(
                    padding: EdgeInsets.all(imageBytes == null ? 24 : 0),
                    child: imageBytes == null
                        ? Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Container(
                                  width: 72,
                                  height: 72,
                                  decoration: BoxDecoration(
                                    color: theme.colorScheme.primaryContainer,
                                    shape: BoxShape.circle,
                                  ),
                                  child: Icon(
                                    Icons.add_photo_alternate_outlined,
                                    color: theme.colorScheme.onPrimaryContainer,
                                    size: 34,
                                  ),
                                ),
                                const SizedBox(height: 18),
                                Text(
                                  t.noImageSelected,
                                  textAlign: TextAlign.center,
                                  style: theme.textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  t.captureChooseSource,
                                  textAlign: TextAlign.center,
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                          )
                        : ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: Image.memory(
                              imageBytes,
                              fit: BoxFit.contain,
                              width: double.infinity,
                            ),
                          ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _pick(ImageSource.camera),
                      icon: const Icon(Icons.photo_camera),
                      label: Text(t.camera),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _pick(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: Text(t.gallery),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              FilledButton(
                onPressed: canAnalyze ? _analyze : null,
                child: Text(t.analyzeBerrySample),
              ),
              const SizedBox(height: 12),
              Text(
                t.captureTip,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
