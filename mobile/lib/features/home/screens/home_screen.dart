import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import '../../../shared/widgets/farmer_ui.dart';
import '../../berry_disease/berry_scanner_screen.dart';
import '../../grading_forecast/screens/berry_capture_screen.dart';
import '../../history/screens/history_screen.dart';
import '../../onboarding/language_picker_screen.dart';
import '../../plant_health/screens/plant_health_scanner_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  void _push(Widget page) {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }

  void _showFeature(_FeatureItem item) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) => FeatureIntroSheet(
        icon: item.icon,
        accent: item.accent,
        eyebrow: item.eyebrow,
        title: item.title,
        description: item.description,
        actionLabel: item.actionLabel,
        onStart: () {
          Navigator.of(sheetContext).pop();
          _push(item.destination);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final pages = [
      const _Dashboard(),
      const HistoryScreen(),
      const _FarmerGuidePage(),
    ];
    final titles = [t.appTitle, t.navHistory, t.navGuide];

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const _AppLogo(size: 34),
            const SizedBox(width: 10),
            Flexible(
              child: Text(
                titles[_selectedIndex],
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: t.language,
            icon: const Icon(Icons.language_rounded),
            onPressed: () => _push(const LanguagePickerScreen()),
          ),
          IconButton(
            tooltip: isDarkMode ? t.lightMode : t.darkMode,
            icon: Icon(
              isDarkMode ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
            ),
            onPressed: () => setState(toggleTheme),
          ),
        ],
      ),
      body: IndexedStack(index: _selectedIndex, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() => _selectedIndex = index);
        },
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: const Icon(Icons.home_rounded),
            label: t.navHome,
          ),
          NavigationDestination(
            icon: const Icon(Icons.history_outlined),
            selectedIcon: const Icon(Icons.history_rounded),
            label: t.navHistory,
          ),
          NavigationDestination(
            icon: const Icon(Icons.menu_book_outlined),
            selectedIcon: const Icon(Icons.menu_book_rounded),
            label: t.navGuide,
          ),
        ],
      ),
    );
  }
}

class _Dashboard extends StatelessWidget {
  const _Dashboard();

  @override
  Widget build(BuildContext context) {
    final state = context.findAncestorStateOfType<_HomeScreenState>()!;
    final t = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final status = AppStatusColors.of(context);
    final dark = theme.brightness == Brightness.dark;
    final features = [
      _FeatureItem(
        icon: Icons.health_and_safety_outlined,
        accent: status.success,
        eyebrow: t.featurePlantHealth,
        title: t.featurePlantTitle,
        cardTitle: t.homeLeafPest,
        cardDescription: t.featurePlantCardDescription,
        description: t.featurePlantDescription,
        actionLabel: t.startScan,
        destination: const PlantHealthScannerScreen(),
      ),
      _FeatureItem(
        icon: Icons.grain_rounded,
        accent: dark ? const Color(0xFFF28AB6) : const Color(0xFF91345F),
        eyebrow: t.featureBerryCare,
        title: t.featureBerryDiseaseTitle,
        cardTitle: t.homeBerryDisease,
        cardDescription: t.featureBerryDiseaseCardDescription,
        description: t.featureBerryDiseaseDescription,
        actionLabel: t.startScan,
        destination: const BerryScannerScreen(),
      ),
      _FeatureItem(
        icon: Icons.workspace_premium_outlined,
        accent: status.warning,
        eyebrow: t.featureQualityAndPrice,
        title: t.featureGradingTitle,
        cardTitle: t.homeQualityPrice,
        cardDescription: t.featureGradingCardDescription,
        description: t.featureGradingDescription,
        actionLabel: t.checkBerryQuality,
        destination: const BerryCaptureScreen(),
      ),
    ];

    return SafeArea(
      top: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(kPagePadding, 20, kPagePadding, 24),
        children: [
          FarmerSectionHeader(
            title: t.homeWelcomeTitle,
            subtitle: t.homeWelcomeSubtitle,
          ),
          const SizedBox(height: 28),
          for (var index = 0; index < features.length; index++) ...[
            _FeatureCard(
              item: features[index],
              onTap: () => state._showFeature(features[index]),
            ),
            if (index < features.length - 1) const SizedBox(height: 14),
          ],
          const SizedBox(height: 20),
          FarmerNoticeCard(
            icon: Icons.tips_and_updates_outlined,
            message: t.homeChooseTaskHint,
          ),
        ],
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  const _FeatureCard({required this.item, required this.onTap});

  final _FeatureItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: item.accent.withValues(
                        alpha: theme.brightness == Brightness.dark
                            ? 0.20
                            : 0.12,
                      ),
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: Icon(item.icon, color: item.accent, size: 25),
                  ),
                  const Spacer(),
                  Icon(
                    Icons.arrow_outward_rounded,
                    color: theme.colorScheme.outline,
                    size: 20,
                  ),
                ],
              ),
              const SizedBox(height: 18),
              Text(
                item.cardTitle,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  height: 1.15,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                item.cardDescription,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FarmerGuidePage extends StatelessWidget {
  const _FarmerGuidePage();

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return SafeArea(
      top: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(kPagePadding, 12, kPagePadding, 32),
        children: [
          FarmerSectionHeader(title: t.guideTitle, subtitle: t.guideSubtitle),
          const SizedBox(height: 20),
          GuideStepCard(
            number: 1,
            icon: Icons.photo_camera_outlined,
            title: t.guidePhotoTitle,
            body: t.guidePhotoBody,
          ),
          GuideStepCard(
            number: 2,
            icon: Icons.light_mode_outlined,
            title: t.guideLightingTitle,
            body: t.guideLightingBody,
          ),
          GuideStepCard(
            number: 3,
            icon: Icons.center_focus_strong,
            title: t.guidePositionTitle,
            body: t.guidePositionBody,
          ),
          GuideStepCard(
            number: 4,
            icon: Icons.workspace_premium_outlined,
            title: t.guideGradesTitle,
            body: t.guideGradesBody,
          ),
          GuideStepCard(
            number: 5,
            icon: Icons.trending_up_rounded,
            title: t.guidePriceTitle,
            body: t.guidePriceBody,
          ),
          GuideStepCard(
            number: 6,
            icon: Icons.refresh_rounded,
            title: t.guideRetryTitle,
            body: t.guideRetryBody,
          ),
          const SizedBox(height: 8),
          FarmerNoticeCard(
            icon: Icons.info_outline_rounded,
            message: t.guideLimitation,
            color: AppStatusColors.of(context).warning,
          ),
        ],
      ),
    );
  }
}

class _FeatureItem {
  const _FeatureItem({
    required this.icon,
    required this.accent,
    required this.eyebrow,
    required this.title,
    required this.cardTitle,
    required this.cardDescription,
    required this.description,
    required this.actionLabel,
    required this.destination,
  });

  final IconData icon;
  final Color accent;
  final String eyebrow;
  final String title;
  final String cardTitle;
  final String cardDescription;
  final String description;
  final String actionLabel;
  final Widget destination;
}

class _AppLogo extends StatelessWidget {
  const _AppLogo({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(size * 0.24),
      child: Image.asset(
        'assets/images/logo.png',
        width: size,
        height: size,
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => Icon(
          Icons.agriculture_rounded,
          color: Theme.of(context).colorScheme.primary,
          size: size,
        ),
      ),
    );
  }
}
