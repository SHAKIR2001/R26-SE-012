import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/home/screens/home_screen.dart';
import 'package:pepper_care/l10n/app_localizations.dart';

Widget wrap(Widget child, {Locale locale = const Locale('en')}) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: child,
);

void main() {
  group('HomeScreen', () {
    Future<void> usePhoneViewport(WidgetTester tester) async {
      await tester.binding.setSurfaceSize(const Size(800, 1000));
      addTearDown(() => tester.binding.setSurfaceSize(null));
    }

    testWidgets('renders the combined plant card and protected features', (
      tester,
    ) async {
      await usePhoneViewport(tester);
      await tester.pumpWidget(wrap(const HomeScreen()));

      expect(find.text('Leaf & Pest'), findsOneWidget);
      expect(find.text('Pests'), findsNothing);
      expect(find.text('Leaf Health'), findsNothing);
      expect(find.text('Berry Disease'), findsOneWidget);
      expect(find.text('Quality &\nPrice'), findsOneWidget);
    });

    testWidgets('every card is tappable', (tester) async {
      await usePhoneViewport(tester);
      await tester.pumpWidget(wrap(const HomeScreen()));

      for (final label in const [
        'Leaf & Pest',
        'Berry Disease',
        'Quality &\nPrice',
      ]) {
        final inkWell = tester.widget<InkWell>(
          find.ancestor(of: find.text(label), matching: find.byType(InkWell)),
        );
        expect(inkWell.onTap, isNotNull);
      }
    });

    testWidgets('lays the feature cards out in one vertical column', (
      tester,
    ) async {
      await usePhoneViewport(tester);
      await tester.pumpWidget(wrap(const HomeScreen()));

      expect(find.byType(GridView), findsNothing);
      Rect cardRect(String label) => tester.getRect(
        find.ancestor(of: find.text(label), matching: find.byType(Card)).first,
      );
      final plant = cardRect('Leaf & Pest');
      final berry = cardRect('Berry Disease');
      final grading = cardRect('Quality &\nPrice');

      expect(plant.left, closeTo(berry.left, 0.01));
      expect(berry.left, closeTo(grading.left, 0.01));
      expect(plant.right, closeTo(berry.right, 0.01));
      expect(berry.right, closeTo(grading.right, 0.01));
      expect(plant.top, lessThan(berry.top));
      expect(berry.top, lessThan(grading.top));
    });

    testWidgets('removes fabricated status, recent results and capture CTA', (
      tester,
    ) async {
      await tester.pumpWidget(wrap(const HomeScreen()));

      expect(find.text('FARM STATUS'), findsNothing);
      expect(find.text('Recent Results'), findsNothing);
      expect(find.text('Take Photo'), findsNothing);
      expect(find.text('Capture'), findsNothing);
      expect(find.text('Pepper Care'), findsOneWidget);
    });

    testWidgets('uses useful Home, History and Guide destinations', (
      tester,
    ) async {
      await tester.pumpWidget(wrap(const HomeScreen()));

      expect(find.byType(NavigationBar), findsOneWidget);
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('History'), findsOneWidget);
      expect(find.text('Guide'), findsOneWidget);

      await tester.tap(find.text('History'));
      await tester.pumpAndSettle();
      expect(find.text('History is unavailable'), findsOneWidget);

      await tester.tap(find.text('Guide'));
      await tester.pumpAndSettle();
      expect(find.text('Berry quality guide'), findsOneWidget);
    });

    testWidgets('all feature cards open a consistent information sheet', (
      tester,
    ) async {
      await usePhoneViewport(tester);
      await tester.pumpWidget(wrap(const HomeScreen()));

      for (final pair in const [
        ('Leaf & Pest', 'Leaf Health & Pest Check'),
        ('Berry Disease', 'Berry Disease Check'),
        ('Quality &\nPrice', 'Berry Quality and Price Outlook'),
      ]) {
        final card = find.ancestor(
          of: find.text(pair.$1),
          matching: find.byType(InkWell),
        );
        await tester.ensureVisible(card);
        await tester.tap(card);
        await tester.pumpAndSettle();
        expect(find.text(pair.$2), findsOneWidget);
        Navigator.of(tester.element(find.text(pair.$2))).pop();
        await tester.pumpAndSettle();
      }
    });
  });
}
