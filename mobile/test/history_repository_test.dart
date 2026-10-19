import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/history/data/history_database.dart';
import 'package:pepper_care/features/history/data/history_image_store.dart';
import 'package:pepper_care/features/history/data/history_repository.dart';
import 'package:pepper_care/features/history/models/history_record.dart';
import 'package:pepper_care/features/history/serialization/history_payload_codec.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();

  late Directory temporaryDirectory;
  late Database database;
  late SharedPreferences preferences;
  late DateTime clock;
  late HistoryRepository repository;

  Future<HistoryRepository> makeRepository({
    HistoryImageStore? imageStore,
  }) async {
    database = await databaseFactoryFfi.openDatabase(
      inMemoryDatabasePath,
      options: OpenDatabaseOptions(
        version: HistoryDatabase.schemaVersion,
        onCreate: (db, version) => HistoryDatabase.createSchema(db),
        onUpgrade: HistoryDatabase.migrate,
      ),
    );
    return HistoryRepository(
      database: database,
      imageStore: imageStore ?? HistoryImageStore(temporaryDirectory),
      preferences: preferences,
      nowUtc: () => clock,
    );
  }

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    preferences = await SharedPreferences.getInstance();
    temporaryDirectory = await Directory.systemTemp.createTemp(
      'pepper-history-',
    );
    clock = DateTime.utc(2026, 10, 15, 12);
    repository = await makeRepository();
  });

  tearDown(() async {
    await repository.close();
    if (await temporaryDirectory.exists()) {
      await temporaryDirectory.delete(recursive: true);
    }
  });

  test('creates the versioned table and indexes', () async {
    final tables = await database.rawQuery(
      "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'history_records'",
    );
    final indexes = await database.rawQuery(
      "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'history_records_%_idx'",
    );
    expect(tables, hasLength(1));
    expect(
      indexes.map((row) => row['name']),
      containsAll([
        'history_records_page_idx',
        'history_records_feature_page_idx',
      ]),
    );
  });

  test(
    'saves and retrieves all four feature types with exact image bytes',
    () async {
      final bytes = Uint8List.fromList([0xff, 0xd8, 0xff, 1, 2, 3, 4]);
      for (final feature in HistoryFeature.values) {
        await repository.saveNew(
          recordKey: 'record-${feature.code}',
          feature: feature,
          stage: HistoryAnalysisStage.detailed,
          outcomeCode: feature == HistoryFeature.gradingForecast
              ? 'accepted'
              : 'detected',
          primaryClassCode: 'test-class',
          imageBytes: bytes,
          resultSchemaVersion: HistoryPayloadCodec.schemaVersion,
          resultJson:
              '{"history_payload_version":1,"kind":"detection","detections":[]}',
          localeCode: 'en',
        );
        clock = clock.add(const Duration(milliseconds: 1));
      }

      final page = await repository.fetchPage();
      expect(
        page.records.map((record) => record.feature).toSet(),
        HistoryFeature.values.toSet(),
      );
      for (final record in page.records) {
        expect(await repository.imageFile(record).readAsBytes(), bytes);
      }
    },
  );

  test('duplicate scanner save enriches one stable record', () async {
    final bytes = Uint8List.fromList([0x89, 0x50, 0x4e, 0x47, 1, 2, 3, 4]);
    Future<void> save() => repository.saveNew(
      recordKey: 'same-attempt',
      feature: HistoryFeature.leafDisease,
      stage: HistoryAnalysisStage.detection,
      outcomeCode: 'detected',
      primaryClassCode: 'Leaf Blight',
      imageBytes: bytes,
      resultSchemaVersion: 1,
      resultJson:
          '{"history_payload_version":1,"kind":"detection","detections":[]}',
      localeCode: 'en',
    );

    await save();
    await save();
    final enriched = await repository.enrich(
      recordKey: 'same-attempt',
      outcomeCode: 'detected',
      primaryClassCode: 'Quick Wilt',
      resultSchemaVersion: 1,
      resultJson:
          '{"history_payload_version":1,"kind":"leaf_detail","analysis":{}}',
    );

    final page = await repository.fetchPage();
    expect(enriched, isTrue);
    expect(page.records, hasLength(1));
    expect(page.records.single.analysisStage, HistoryAnalysisStage.detailed);
    expect(page.records.single.primaryClassCode, 'Quick Wilt');
  });

  test(
    'cursor pagination returns 20, 20 and 5 newest-first without duplicates',
    () async {
      final firstCreated = clock;
      for (var index = 0; index < 45; index++) {
        await repository.saveNew(
          recordKey: 'page-$index',
          feature: HistoryFeature.berryDisease,
          stage: HistoryAnalysisStage.detection,
          outcomeCode: 'detected',
          primaryClassCode: 'lace_bug_damage',
          imageBytes: Uint8List.fromList([0xff, 0xd8, 0xff, index]),
          resultSchemaVersion: 1,
          resultJson:
              '{"history_payload_version":1,"kind":"detection","detections":[]}',
          localeCode: 'en',
        );
        clock = clock.add(const Duration(milliseconds: 1));
      }

      final first = await repository.fetchPage(limit: 20);
      final second = await repository.fetchPage(
        limit: 20,
        before: first.nextCursor,
      );
      final third = await repository.fetchPage(
        limit: 20,
        before: second.nextCursor,
      );
      final all = [...first.records, ...second.records, ...third.records];

      expect(first.records, hasLength(20));
      expect(second.records, hasLength(20));
      expect(third.records, hasLength(5));
      expect(all.map((record) => record.id).toSet(), hasLength(45));
      expect(
        all.first.createdAtUtcMs,
        firstCreated
            .add(const Duration(milliseconds: 44))
            .millisecondsSinceEpoch,
      );
      for (var index = 1; index < all.length; index++) {
        expect(
          all[index - 1].createdAtUtcMs >= all[index].createdAtUtcMs,
          isTrue,
        );
      }
    },
  );

  test(
    'automatic deletion defaults off and uses a strict fourteen-day cutoff',
    () async {
      final cleanupTime = clock;
      Future<void> saveAt(String key, DateTime time) async {
        clock = time;
        await repository.saveNew(
          recordKey: key,
          feature: HistoryFeature.pestDetection,
          stage: HistoryAnalysisStage.detection,
          outcomeCode: 'detected',
          primaryClassCode: 'pest',
          imageBytes: Uint8List.fromList([0xff, 0xd8, 0xff, key.length]),
          resultSchemaVersion: 1,
          resultJson:
              '{"history_payload_version":1,"kind":"detection","detections":[]}',
          localeCode: 'en',
        );
      }

      await saveAt(
        'older',
        cleanupTime.subtract(const Duration(days: 14, milliseconds: 1)),
      );
      await saveAt('boundary', cleanupTime.subtract(const Duration(days: 14)));
      await saveAt('newer', cleanupTime.subtract(const Duration(days: 13)));
      clock = cleanupTime;

      expect(repository.autoDeleteEnabled, isFalse);
      await repository.runRetentionCleanup(force: true);
      expect((await repository.fetchPage()).records, hasLength(3));

      final result = await repository.setAutoDeleteEnabled(true);
      final keys = (await repository.fetchPage()).records
          .map((record) => record.recordKey)
          .toSet();
      expect(result.deleted, 1);
      expect(keys, {'boundary', 'newer'});
    },
  );

  test(
    'clear all removes rows and app-owned images; missing files count as removed',
    () async {
      await repository.saveNew(
        recordKey: 'clear-one',
        feature: HistoryFeature.gradingForecast,
        stage: HistoryAnalysisStage.detailed,
        outcomeCode: 'uncertain',
        primaryClassCode: null,
        imageBytes: Uint8List.fromList([0xff, 0xd8, 0xff, 1]),
        resultSchemaVersion: 1,
        resultJson:
            '{"history_payload_version":1,"kind":"grading_forecast","result":{}}',
        localeCode: 'en',
      );
      final record = (await repository.fetchPage()).records.single;
      await repository.imageFile(record).delete();

      final result = await repository.clearAll();
      expect(result.isComplete, isTrue);
      expect((await repository.fetchPage()).records, isEmpty);
    },
  );

  test('failed file deletion remains pending and succeeds on retry', () async {
    await repository.close();
    final store = _FailingImageStore(temporaryDirectory);
    repository = await makeRepository(imageStore: store);
    await repository.saveNew(
      recordKey: 'pending-delete',
      feature: HistoryFeature.leafDisease,
      stage: HistoryAnalysisStage.detection,
      outcomeCode: 'healthy',
      primaryClassCode: 'Healthy leaves',
      imageBytes: Uint8List.fromList([0xff, 0xd8, 0xff, 1]),
      resultSchemaVersion: 1,
      resultJson:
          '{"history_payload_version":1,"kind":"detection","detections":[]}',
      localeCode: 'en',
    );

    store.failDeletes = true;
    final first = await repository.clearAll();
    expect(first.pending, 1);
    expect((await repository.fetchPage()).records, isEmpty);

    store.failDeletes = false;
    final retry = await repository.retryPendingDeletions();
    expect(retry.deleted, 1);
    expect(await repository.findByKey('pending-delete'), isNull);
  });

  test('payload codec rejects corrupt and unsupported snapshots', () {
    expect(HistoryPayloadCodec.tryDecode('not json'), isNull);
    expect(
      HistoryPayloadCodec.tryDecode(
        '{"history_payload_version":999,"kind":"detection"}',
      ),
      isNull,
    );
    expect(
      HistoryPayloadCodec.tryDecode(
        '{"history_payload_version":1,"kind":"detection","detections":[]}',
      ),
      isNotNull,
    );
  });
}

class _FailingImageStore extends HistoryImageStore {
  _FailingImageStore(super.rootDirectory);
  bool failDeletes = false;

  @override
  Future<bool> delete(String relativePath) async {
    if (failDeletes) return false;
    return super.delete(relativePath);
  }
}
