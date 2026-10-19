import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

class HistoryDatabase {
  HistoryDatabase._();

  static const int schemaVersion = 1;

  static Future<Database> open({String? databasePath}) async {
    final path =
        databasePath ??
        p.join(await getDatabasesPath(), 'pepper_care_history.db');
    return openDatabase(
      path,
      version: schemaVersion,
      onConfigure: (database) async {
        await database.execute('PRAGMA foreign_keys = ON');
      },
      onCreate: (database, version) => createSchema(database),
      onUpgrade: migrate,
    );
  }

  static Future<void> createSchema(DatabaseExecutor database) async {
    await database.execute('''
      CREATE TABLE history_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_key TEXT NOT NULL UNIQUE,
        feature_type TEXT NOT NULL CHECK(feature_type IN (
          'grading_forecast', 'pest_detection',
          'leaf_disease', 'berry_disease'
        )),
        created_at_utc_ms INTEGER NOT NULL,
        updated_at_utc_ms INTEGER NOT NULL,
        analysis_stage TEXT NOT NULL CHECK(analysis_stage IN ('detection', 'detailed')),
        outcome_code TEXT NOT NULL,
        primary_class_code TEXT,
        image_relative_path TEXT NOT NULL UNIQUE,
        image_mime_type TEXT NOT NULL,
        image_byte_length INTEGER NOT NULL CHECK(image_byte_length >= 0),
        result_schema_version INTEGER NOT NULL,
        result_json TEXT NOT NULL,
        locale_code TEXT,
        delete_pending INTEGER NOT NULL DEFAULT 0 CHECK(delete_pending IN (0, 1))
      )
    ''');
    await database.execute('''
      CREATE INDEX history_records_page_idx
      ON history_records(delete_pending, created_at_utc_ms DESC, id DESC)
    ''');
    await database.execute('''
      CREATE INDEX history_records_feature_page_idx
      ON history_records(feature_type, delete_pending, created_at_utc_ms DESC, id DESC)
    ''');
  }

  static Future<void> migrate(
    Database database,
    int oldVersion,
    int newVersion,
  ) async {
    if (oldVersion < 1) await createSchema(database);
  }
}
