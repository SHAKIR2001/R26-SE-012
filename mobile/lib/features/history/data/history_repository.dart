import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite/sqflite.dart';

import '../models/history_record.dart';
import 'history_database.dart';
import 'history_image_store.dart';

const historyAutoDeletePreferenceKey = 'history_auto_delete_14_days';
const _historyLastCleanupPreferenceKey = 'history_last_cleanup_utc_ms';

class HistoryDeletionResult {
  const HistoryDeletionResult({required this.deleted, required this.pending});
  final int deleted;
  final int pending;
  bool get isComplete => pending == 0;
}

class HistoryRepository extends ChangeNotifier {
  HistoryRepository({
    required Database database,
    required HistoryImageStore imageStore,
    required SharedPreferences preferences,
    DateTime Function()? nowUtc,
  }) : _database = database,
       _imageStore = imageStore,
       _preferences = preferences,
       _nowUtc = nowUtc ?? (() => DateTime.now().toUtc());

  final Database _database;
  final HistoryImageStore _imageStore;
  final SharedPreferences _preferences;
  final DateTime Function() _nowUtc;
  Future<void> _operationTail = Future<void>.value();
  bool _closed = false;

  static Future<HistoryRepository> openDefault() async {
    final results = await Future.wait<Object>([
      HistoryDatabase.open(),
      HistoryImageStore.openDefault(),
      SharedPreferences.getInstance(),
    ]);
    return HistoryRepository(
      database: results[0] as Database,
      imageStore: results[1] as HistoryImageStore,
      preferences: results[2] as SharedPreferences,
    );
  }

  bool get autoDeleteEnabled =>
      _preferences.getBool(historyAutoDeletePreferenceKey) ?? false;

  File imageFile(HistoryRecord record) =>
      _imageStore.resolve(record.imageRelativePath);

  Future<HistoryRecord?> findByKey(String recordKey) async {
    final rows = await _database.query(
      'history_records',
      where: 'record_key = ?',
      whereArgs: [recordKey],
      limit: 1,
    );
    return rows.isEmpty ? null : HistoryRecord.fromMap(rows.single);
  }

  Future<HistoryPage> fetchPage({
    int limit = 20,
    HistoryCursor? before,
    HistoryFeature? feature,
  }) async {
    final clauses = <String>['delete_pending = 0'];
    final args = <Object?>[];
    if (feature != null) {
      clauses.add('feature_type = ?');
      args.add(feature.code);
    }
    if (before != null) {
      clauses.add(
        '(created_at_utc_ms < ? OR (created_at_utc_ms = ? AND id < ?))',
      );
      args.addAll([before.createdAtUtcMs, before.createdAtUtcMs, before.id]);
    }
    final rows = await _database.query(
      'history_records',
      where: clauses.join(' AND '),
      whereArgs: args,
      orderBy: 'created_at_utc_ms DESC, id DESC',
      limit: limit + 1,
    );
    final hasMore = rows.length > limit;
    final records = rows
        .take(limit)
        .map(HistoryRecord.fromMap)
        .toList(growable: false);
    return HistoryPage(
      records: records,
      nextCursor: hasMore && records.isNotEmpty ? records.last.cursor : null,
    );
  }

  Future<void> saveNew({
    required String recordKey,
    required HistoryFeature feature,
    required HistoryAnalysisStage stage,
    required String outcomeCode,
    required String? primaryClassCode,
    required Uint8List imageBytes,
    required int resultSchemaVersion,
    required String resultJson,
    required String? localeCode,
  }) => _exclusive(() async {
    if (await findByKey(recordKey) != null) return;
    final now = _nowUtc().toUtc();
    final stored = await _imageStore.write(
      recordKey: recordKey,
      feature: feature,
      bytes: imageBytes,
      createdAtUtc: now,
    );
    try {
      await _database.insert('history_records', {
        'record_key': recordKey,
        'feature_type': feature.code,
        'created_at_utc_ms': now.millisecondsSinceEpoch,
        'updated_at_utc_ms': now.millisecondsSinceEpoch,
        'analysis_stage': stage.code,
        'outcome_code': outcomeCode,
        'primary_class_code': primaryClassCode,
        'image_relative_path': stored.relativePath,
        'image_mime_type': stored.mimeType,
        'image_byte_length': stored.byteLength,
        'result_schema_version': resultSchemaVersion,
        'result_json': resultJson,
        'locale_code': localeCode,
        'delete_pending': 0,
      });
    } catch (_) {
      await _imageStore.delete(stored.relativePath);
      rethrow;
    }
    notifyListeners();
  });

  Future<bool> enrich({
    required String recordKey,
    required String outcomeCode,
    required String? primaryClassCode,
    required int resultSchemaVersion,
    required String resultJson,
  }) => _exclusive(() async {
    final count = await _database.update(
      'history_records',
      {
        'updated_at_utc_ms': _nowUtc().toUtc().millisecondsSinceEpoch,
        'analysis_stage': HistoryAnalysisStage.detailed.code,
        'outcome_code': outcomeCode,
        'primary_class_code': primaryClassCode,
        'result_schema_version': resultSchemaVersion,
        'result_json': resultJson,
      },
      where: 'record_key = ? AND delete_pending = 0',
      whereArgs: [recordKey],
    );
    if (count > 0) notifyListeners();
    return count > 0;
  });

  Future<HistoryDeletionResult> clearAll() =>
      _deleteWhere('1 = 1', const <Object?>[]);

  Future<HistoryDeletionResult> deleteOlderThan(DateTime cutoffUtc) =>
      _deleteWhere('created_at_utc_ms < ?', [
        cutoffUtc.toUtc().millisecondsSinceEpoch,
      ]);

  Future<HistoryDeletionResult> retryPendingDeletions() =>
      _deleteWhere('delete_pending = 1', const <Object?>[], markPending: false);

  Future<HistoryDeletionResult> _deleteWhere(
    String where,
    List<Object?> whereArgs, {
    bool markPending = true,
  }) => _exclusive(() async {
    final rows = await _database.query(
      'history_records',
      where: where,
      whereArgs: whereArgs,
    );
    if (rows.isEmpty) {
      return const HistoryDeletionResult(deleted: 0, pending: 0);
    }
    final ids = rows.map((row) => row['id'] as int).toList(growable: false);
    if (markPending) {
      await _database.update(
        'history_records',
        {'delete_pending': 1},
        where: 'id IN (${List.filled(ids.length, '?').join(',')})',
        whereArgs: ids,
      );
    }
    final removed = <int>[];
    for (final row in rows) {
      final ok = await _imageStore.delete(row['image_relative_path'] as String);
      if (ok) removed.add(row['id'] as int);
    }
    if (removed.isNotEmpty) {
      await _database.delete(
        'history_records',
        where: 'id IN (${List.filled(removed.length, '?').join(',')})',
        whereArgs: removed,
      );
    }
    notifyListeners();
    return HistoryDeletionResult(
      deleted: removed.length,
      pending: rows.length - removed.length,
    );
  });

  Future<HistoryDeletionResult> setAutoDeleteEnabled(bool enabled) async {
    await _preferences.setBool(historyAutoDeletePreferenceKey, enabled);
    notifyListeners();
    if (!enabled) {
      return const HistoryDeletionResult(deleted: 0, pending: 0);
    }
    return runRetentionCleanup(force: true);
  }

  Future<HistoryDeletionResult> runRetentionCleanup({
    bool force = false,
  }) async {
    if (!autoDeleteEnabled) {
      return const HistoryDeletionResult(deleted: 0, pending: 0);
    }
    final now = _nowUtc().toUtc();
    final lastMs = _preferences.getInt(_historyLastCleanupPreferenceKey);
    if (!force && lastMs != null) {
      final last = DateTime.fromMillisecondsSinceEpoch(lastMs, isUtc: true);
      if (now.difference(last) < const Duration(hours: 24)) {
        return const HistoryDeletionResult(deleted: 0, pending: 0);
      }
    }
    final result = await deleteOlderThan(
      now.subtract(const Duration(days: 14)),
    );
    await _preferences.setInt(
      _historyLastCleanupPreferenceKey,
      now.millisecondsSinceEpoch,
    );
    return result;
  }

  Future<void> runMaintenance({bool forceRetention = false}) async {
    await retryPendingDeletions();
    await runRetentionCleanup(force: forceRetention);
    final rows = await _database.query(
      'history_records',
      columns: ['image_relative_path'],
    );
    await _imageStore.reconcile(
      rows.map((row) => row['image_relative_path'] as String).toSet(),
    );
  }

  Future<T> _exclusive<T>(Future<T> Function() action) {
    final completer = Completer<T>();
    _operationTail = _operationTail.then((_) async {
      try {
        completer.complete(await action());
      } catch (error, stackTrace) {
        completer.completeError(error, stackTrace);
      }
    });
    return completer.future;
  }

  Future<void> close() async {
    if (_closed) return;
    _closed = true;
    await _operationTail;
    await _database.close();
  }
}
