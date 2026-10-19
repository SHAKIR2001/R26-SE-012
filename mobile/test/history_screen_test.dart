import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/history/data/history_database.dart';
import 'package:pepper_care/features/history/data/history_image_store.dart';
import 'package:pepper_care/features/history/data/history_repository.dart';
import 'package:pepper_care/features/history/history_scope.dart';
import 'package:pepper_care/features/history/models/history_record.dart';
import 'package:pepper_care/features/history/screens/history_screen.dart';
import 'package:pepper_care/l10n/app_localizations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();

  late Directory temporaryDirectory;
  late HistoryRepository repository;

  Widget app() => HistoryScope(
    repository: repository,
    child: const MaterialApp(
      locale: Locale('en'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(body: HistoryScreen()),
    ),
  );

  Future<void> saveRecord(String key) => repository.saveNew(
    recordKey: key,
    feature: HistoryFeature.leafDisease,
    stage: HistoryAnalysisStage.detection,
    outcomeCode: 'detected',
    primaryClassCode: 'Leaf Blight',
    imageBytes: Uint8List.fromList([
      0x89,
      0x50,
      0x4e,
      0x47,
      0x0d,
      0x0a,
      0x1a,
      0x0a,
    ]),
    resultSchemaVersion: 1,
    resultJson:
        '{"history_payload_version":1,"kind":"detection","detections":[{"class_name":"Leaf Blight","score":0.9}]}',
    localeCode: 'en',
  );

  Future<void> settleHistory(WidgetTester tester) async {
    for (var attempt = 0; attempt < 30; attempt++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 50)),
      );
      await tester.pump();
      if (find.byType(CircularProgressIndicator).evaluate().isEmpty) return;
    }
  }

  Future<void> disposeApp(WidgetTester tester) async {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.runAsync(repository.close);
  }

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    final preferences = await SharedPreferences.getInstance();
    temporaryDirectory = await Directory.systemTemp.createTemp('history-ui-');
    final database = await databaseFactoryFfiNoIsolate.openDatabase(
      inMemoryDatabasePath,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (db, version) => HistoryDatabase.createSchema(db),
      ),
    );
    repository = HistoryRepository(
      database: database,
      imageStore: HistoryImageStore(temporaryDirectory),
      preferences: preferences,
    );
  });

  tearDown(() async {
    await repository.close();
    for (var attempt = 0; attempt < 3; attempt++) {
      try {
        if (await temporaryDirectory.exists()) {
          await temporaryDirectory.delete(recursive: true);
        }
        break;
      } on FileSystemException {
        await Future<void>.delayed(const Duration(milliseconds: 100));
      }
    }
  });

  testWidgets('fresh history is empty and automatic cleanup is disabled', (
    tester,
  ) async {
    await tester.pumpWidget(app());
    await settleHistory(tester);

    expect(find.text('No analysis history yet'), findsOneWidget);
    expect(find.byType(ChoiceChip), findsNothing);
    expect(find.byType(SwitchListTile), findsNothing);
    await tester.tap(find.byKey(const ValueKey('historyDeleteButton')));
    await tester.pumpAndSettle();
    final toggle = tester.widget<SwitchListTile>(find.byType(SwitchListTile));
    expect(toggle.value, isFalse);
    await disposeApp(tester);
  });

  testWidgets('saved detail opens offline and tolerates a missing image', (
    tester,
  ) async {
    await tester.runAsync(() => saveRecord('offline-detail'));
    final record = await tester.runAsync(
      () async => (await repository.fetchPage()).records.single,
    );
    await tester.runAsync(() => repository.imageFile(record!).delete());

    await tester.pumpWidget(app());
    await settleHistory(tester);
    try {
      await tester.tap(find.text('Leaf Blight').first);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 350));
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 100)),
      );
      await tester.pump();

      expect(find.text('Saved analysis'), findsOneWidget);
      expect(find.text('Saved image unavailable'), findsOneWidget);
      final offlineNotice = find.text(
        'This is a saved result. Opening it does not run analysis or use the internet.',
      );
      await tester.scrollUntilVisible(
        offlineNotice,
        180,
        scrollable: find.byType(Scrollable).last,
      );
      expect(offlineNotice, findsOneWidget);
    } finally {
      await disposeApp(tester);
    }
  });

  testWidgets(
    'clear all requires confirmation and cancellation changes nothing',
    (tester) async {
      await tester.runAsync(() => saveRecord('clear-confirmation'));
      await tester.pumpWidget(app());
      await settleHistory(tester);
      try {
        await tester.tap(find.byKey(const ValueKey('historyDeleteButton')));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 250));
        await tester.tap(find.text('Clear all history'));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 350));
        await tester.tap(find.text('Cancel'));
        await tester.pump(const Duration(milliseconds: 250));
        final recordsAfterCancel = await tester.runAsync(
          () async => (await repository.fetchPage()).records,
        );
        expect(recordsAfterCancel, hasLength(1));

        await tester.tap(find.byKey(const ValueKey('historyDeleteButton')));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 250));
        await tester.tap(find.text('Clear all history'));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 350));
        await tester.tap(find.text('Clear all').last);
        await tester.pump();
        await tester.runAsync(
          () => Future<void>.delayed(const Duration(milliseconds: 150)),
        );
        await settleHistory(tester);
        final recordsAfterClear = await tester.runAsync(
          () async => (await repository.fetchPage()).records,
        );
        expect(recordsAfterClear, isEmpty);
        expect(find.text('No analysis history yet'), findsOneWidget);
      } finally {
        await disposeApp(tester);
      }
    },
  );

  testWidgets('filter options stay hidden until the filter icon is tapped', (
    tester,
  ) async {
    await tester.runAsync(() => saveRecord('filter-menu'));
    await tester.pumpWidget(app());
    await settleHistory(tester);
    try {
      expect(find.text('All'), findsNothing);
      expect(find.text('Leaf Health Check'), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('historyFilterButton')));
      await tester.pumpAndSettle();

      expect(find.text('All'), findsOneWidget);
      expect(find.text('Pest Detection'), findsOneWidget);
      expect(find.text('Berry Disease Check'), findsOneWidget);
    } finally {
      await disposeApp(tester);
    }
  });
}
