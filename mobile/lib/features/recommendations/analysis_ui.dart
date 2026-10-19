import 'dart:typed_data';
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:iconly/iconly.dart';

import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
export '../../core/theme/app_theme.dart' show kBrand, AppStatusColors;

/// Shared, animated building blocks for the three AI analysis screens (leaf,
/// berry, pest). Colors are theme-aware getters so the screens follow the
/// global light/dark toggle. [kBrand] is re-exported from app_theme.

// ---- theme-aware palette (follows the global light/dark toggle) ----
Color get kBg => isDarkMode ? const Color(0xFF0F1713) : const Color(0xFFF6F8F5);
Color get kCard => isDarkMode ? const Color(0xFF15201A) : Colors.white;
Color get kBorder =>
    isDarkMode ? const Color(0xFF3F4D45) : const Color(0xFFC7D2CA);
Color get kText =>
    isDarkMode ? const Color(0xFFE5EEE8) : const Color(0xFF17201B);
Color get kTextSub =>
    isDarkMode ? const Color(0xFFC3CEC6) : const Color(0xFF45524A);

const _heroTag = 'analysis-hero-photo';

Color bandColor(BuildContext context, String band) => switch (band) {
  'severe' => AppStatusColors.of(context).danger,
  'moderate' => AppStatusColors.of(context).warning,
  'mild' => AppStatusColors.of(context).warning,
  _ => AppStatusColors.of(context).success,
};

// ---- collapsing scaffold with a Hero photo header ----
class AnalysisScaffold extends StatelessWidget {
  final Uint8List imageBytes;
  final String title;
  final IconData titleIcon;
  final List<Widget> children;

  const AnalysisScaffold({
    super.key,
    required this.imageBytes,
    required this.title,
    required this.titleIcon,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            stretch: true,
            backgroundColor: Theme.of(context).colorScheme.primary,
            foregroundColor: Colors.white,
            leading: Padding(
              padding: const EdgeInsets.all(8),
              child: _CircleButton(
                icon: IconlyLight.arrow_left,
                onTap: () => Navigator.of(context).maybePop(),
              ),
            ),
            flexibleSpace: FlexibleSpaceBar(
              stretchModes: const [
                StretchMode.zoomBackground,
                StretchMode.blurBackground,
              ],
              titlePadding: const EdgeInsetsDirectional.only(
                start: 20,
                bottom: 16,
                end: 20,
              ),
              title: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(titleIcon, size: 18, color: Colors.white),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      title,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 18,
                      ),
                    ),
                  ),
                ],
              ),
              background: GestureDetector(
                onTap: () => _openPhoto(context, imageBytes),
                child: Hero(
                  tag: _heroTag,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Image.memory(imageBytes, fit: BoxFit.cover),
                      const DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.center,
                            end: Alignment.bottomCenter,
                            colors: [Colors.transparent, Colors.black54],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.fromLTRB(
                20,
                24,
                20,
                36 + MediaQuery.of(context).padding.bottom,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: stagger(children),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Wraps each child in a staggered fade + slide-up entrance.
List<Widget> stagger(List<Widget> items) => [
  for (int i = 0; i < items.length; i++)
    FadeSlideIn(delayMs: i * 70, child: items[i]),
];

class FadeSlideIn extends StatefulWidget {
  final int delayMs;
  final Widget child;
  const FadeSlideIn({super.key, required this.child, this.delayMs = 0});

  @override
  State<FadeSlideIn> createState() => _FadeSlideInState();
}

class _FadeSlideInState extends State<FadeSlideIn>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 420),
  );

  @override
  void initState() {
    super.initState();
    Future.delayed(Duration(milliseconds: widget.delayMs), () {
      if (mounted) _c.forward();
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _c,
      builder: (_, child) {
        final t = Curves.easeOut.transform(_c.value);
        return Opacity(
          opacity: t,
          child: Transform.translate(
            offset: Offset(0, (1 - t) * 18),
            child: child,
          ),
        );
      },
      child: widget.child,
    );
  }
}

// ---- animated primitives ----
class CountUp extends StatelessWidget {
  final double value;
  final String suffix;
  final int decimals;
  final TextStyle style;
  const CountUp(
    this.value, {
    super.key,
    this.suffix = '',
    this.decimals = 0,
    required this.style,
  });

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: value),
      duration: const Duration(milliseconds: 900),
      curve: Curves.easeOutCubic,
      builder: (_, v, _) =>
          Text('${v.toStringAsFixed(decimals)}$suffix', style: style),
    );
  }
}

class AnimatedBar extends StatelessWidget {
  final double fraction; // 0..1
  final Color color;
  const AnimatedBar({super.key, required this.fraction, required this.color});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: fraction.clamp(0, 1)),
        duration: const Duration(milliseconds: 900),
        curve: Curves.easeOutCubic,
        builder: (_, v, _) => LinearProgressIndicator(
          value: v,
          minHeight: 10,
          backgroundColor: Theme.of(context).colorScheme.surfaceContainerHigh,
          valueColor: AlwaysStoppedAnimation(color),
        ),
      ),
    );
  }
}

// ---- cards & tiles ----
class StatTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Widget value;
  final String sub;
  final Color color;
  const StatTile({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    required this.sub,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: _cardDecoration(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 19, color: color),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: kTextSub,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          value,
          const SizedBox(height: 2),
          Text(
            sub,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: kTextSub,
            ),
          ),
        ],
      ),
    );
  }
}

class SectionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget child;
  const SectionCard({
    super.key,
    required this.icon,
    required this.title,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 18),
      padding: const EdgeInsets.all(18),
      decoration: _cardDecoration(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 21, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: kText,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}

class InfoCard extends StatelessWidget {
  final IconData icon;
  final String text;
  final Color color;
  const InfoCard({
    super.key,
    required this.icon,
    required this.text,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 18),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: isDarkMode ? 0.17 : 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withValues(alpha: isDarkMode ? 0.40 : 0.25),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, size: 21, color: color),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                height: 1.48,
                color: kText,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// A treatment / remediation tile (used by berry & pest).
class OptionTile extends StatelessWidget {
  final String name;
  final String? mix;
  final String method;
  final bool allowed;
  final String? restriction;
  final String? phiNote;
  final bool isChemical;

  const OptionTile({
    super.key,
    required this.name,
    required this.method,
    required this.allowed,
    this.mix,
    this.restriction,
    this.phiNote,
    this.isChemical = true,
  });

  @override
  Widget build(BuildContext context) {
    final banned = !allowed;
    final status = AppStatusColors.of(context);
    final scheme = Theme.of(context).colorScheme;
    final leadColor = banned
        ? status.danger
        : (isChemical ? status.warning : status.success);
    final leadIcon = banned
        ? IconlyBold.close_square
        : (isChemical ? IconlyBold.danger : IconlyBold.shield_done);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: banned
            ? status.dangerContainer
            : scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: banned ? status.danger.withValues(alpha: 0.55) : kBorder,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(leadIcon, size: 18, color: leadColor),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  name + (mix != null ? '  ·  $mix' : ''),
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: banned ? status.onDangerContainer : kText,
                    decoration: banned ? TextDecoration.lineThrough : null,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            method,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              height: 1.45,
              color: banned ? status.onDangerContainer : kTextSub,
            ),
          ),
          if (banned && restriction != null) ...[
            const SizedBox(height: 6),
            Text(
              restriction!,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: status.onDangerContainer,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
          if (!banned && isChemical && phiNote != null) ...[
            const SizedBox(height: 6),
            Text(
              phiNote!,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: status.warning,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class MarketRow extends StatelessWidget {
  final Widget dropdown;
  const MarketRow({super.key, required this.dropdown});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 18),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: _cardDecoration(context),
      child: Row(
        children: [
          Icon(
            IconlyLight.location,
            size: 21,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              AppLocalizations.of(context).exportMarket,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: kText,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          dropdown,
        ],
      ),
    );
  }
}

// ---- state views ----
class LoadingView extends StatelessWidget {
  final String message;
  const LoadingView({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 48),
      child: Column(
        children: [
          const SizedBox(
            width: 34,
            height: 34,
            child: CircularProgressIndicator(strokeWidth: 3, color: kBrand),
          ),
          const SizedBox(height: 20),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: kTextSub,
            ),
          ),
        ],
      ),
    );
  }
}

class ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const ErrorView({super.key, required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SizedBox(height: 20),
        Icon(
          IconlyBold.danger,
          color: AppStatusColors.of(context).danger,
          size: 48,
        ),
        const SizedBox(height: 12),
        Text(
          message,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: kTextSub,
          ),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: onRetry,
          icon: const Icon(IconlyLight.arrow_right, size: 18),
          label: Text(AppLocalizations.of(context).tryAgain),
        ),
      ],
    );
  }
}

class RetakeView extends StatelessWidget {
  final String title;
  final String message;
  final VoidCallback onRetake;
  const RetakeView({
    super.key,
    required this.title,
    required this.message,
    required this.onRetake,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SizedBox(height: 12),
        Icon(
          IconlyBold.hide,
          color: AppStatusColors.of(context).warning,
          size: 48,
        ),
        const SizedBox(height: 14),
        Text(
          title,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
            color: kText,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          message,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: kTextSub,
            height: 1.48,
          ),
        ),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: onRetake,
          icon: const Icon(IconlyLight.camera, size: 18),
          label: Text(AppLocalizations.of(context).retakePhoto),
        ),
      ],
    );
  }
}

// ---- helpers ----
BoxDecoration _cardDecoration(BuildContext context) => BoxDecoration(
  color: kCard,
  borderRadius: BorderRadius.circular(18),
  border: Border.all(color: kBorder),
  boxShadow: Theme.of(context).brightness == Brightness.dark
      ? const []
      : const [
          BoxShadow(
            color: Color(0x0A000000),
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
);

class _CircleButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _CircleButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black.withValues(alpha: 0.28),
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: SizedBox(
          width: 40,
          height: 40,
          child: Icon(icon, color: Colors.white, size: 20),
        ),
      ),
    );
  }
}

// ---- fullscreen Hero photo viewer ----
void _openPhoto(BuildContext context, Uint8List bytes) {
  Navigator.of(context).push(
    PageRouteBuilder(
      opaque: false,
      barrierColor: Colors.black,
      transitionDuration: const Duration(milliseconds: 300),
      pageBuilder: (_, _, _) => _PhotoViewer(bytes: bytes),
    ),
  );
}

class _PhotoViewer extends StatelessWidget {
  final Uint8List bytes;
  const _PhotoViewer({required this.bytes});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: () => Navigator.of(context).pop(),
        child: Stack(
          children: [
            Center(
              child: Hero(
                tag: _heroTag,
                child: InteractiveViewer(
                  child: Image.memory(bytes, fit: BoxFit.contain),
                ),
              ),
            ),
            Positioned(
              top: MediaQuery.of(context).padding.top + 8,
              right: 12,
              child: _CircleButton(
                icon: IconlyLight.close_square,
                onTap: () => Navigator.of(context).pop(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A fade + scale route used when opening an analysis screen from the scanner.
Route<T> fadeScaleRoute<T>(Widget page) => PageRouteBuilder<T>(
  transitionDuration: const Duration(milliseconds: 350),
  reverseTransitionDuration: const Duration(milliseconds: 250),
  pageBuilder: (_, _, _) => page,
  transitionsBuilder: (_, anim, _, child) {
    final curved = CurvedAnimation(parent: anim, curve: Curves.easeOutCubic);
    return FadeTransition(
      opacity: curved,
      child: Transform.scale(
        scale: lerpDouble(0.96, 1.0, curved.value)!,
        child: child,
      ),
    );
  },
);
