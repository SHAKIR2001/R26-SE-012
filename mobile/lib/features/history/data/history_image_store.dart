import 'dart:io';
import 'dart:typed_data';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/history_record.dart';

class StoredHistoryImage {
  const StoredHistoryImage({
    required this.relativePath,
    required this.mimeType,
    required this.byteLength,
  });

  final String relativePath;
  final String mimeType;
  final int byteLength;
}

class HistoryImageStore {
  HistoryImageStore(this.rootDirectory);

  final Directory rootDirectory;

  static Future<HistoryImageStore> openDefault() async {
    final support = await getApplicationSupportDirectory();
    final root = Directory(p.join(support.path, 'pepper_care', 'history'));
    await root.create(recursive: true);
    return HistoryImageStore(root);
  }

  Future<StoredHistoryImage> write({
    required String recordKey,
    required HistoryFeature feature,
    required Uint8List bytes,
    DateTime? createdAtUtc,
  }) async {
    if (bytes.isEmpty) throw const FileSystemException('Image is empty.');
    final created = (createdAtUtc ?? DateTime.now().toUtc()).toUtc();
    final format = _imageFormat(bytes);
    final relative = p.join(
      'images',
      feature.code,
      created.year.toString().padLeft(4, '0'),
      created.month.toString().padLeft(2, '0'),
      '$recordKey.${format.extension}',
    );
    final target = resolve(relative);
    await target.parent.create(recursive: true);
    final temporary = File(
      '${target.path}.tmp-${DateTime.now().toUtc().microsecondsSinceEpoch}',
    );
    try {
      await temporary.writeAsBytes(bytes, flush: true);
      if (await target.exists()) await target.delete();
      await temporary.rename(target.path);
    } catch (_) {
      try {
        if (await temporary.exists()) await temporary.delete();
      } catch (_) {}
      rethrow;
    }
    return StoredHistoryImage(
      relativePath: relative,
      mimeType: format.mimeType,
      byteLength: bytes.length,
    );
  }

  File resolve(String relativePath) {
    final normalized = p.normalize(relativePath);
    if (p.isAbsolute(normalized) ||
        normalized == '..' ||
        normalized.startsWith('..${p.separator}')) {
      throw const FileSystemException('Unsafe history image path.');
    }
    final root = p.normalize(rootDirectory.absolute.path);
    final resolved = p.normalize(p.join(root, normalized));
    if (resolved != root && !p.isWithin(root, resolved)) {
      throw const FileSystemException('History image path escaped its root.');
    }
    return File(resolved);
  }

  Future<bool> delete(String relativePath) async {
    final file = resolve(relativePath);
    try {
      if (await file.exists()) await file.delete();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> reconcile(Set<String> referencedPaths) async {
    final imageRoot = Directory(p.join(rootDirectory.path, 'images'));
    if (!await imageRoot.exists()) return;
    final cutoff = DateTime.now().toUtc().subtract(const Duration(hours: 1));
    await for (final entity in imageRoot.list(recursive: true)) {
      if (entity is! File) continue;
      final relative = p.relative(entity.path, from: rootDirectory.path);
      final isTemporary = p.basename(entity.path).contains('.tmp-');
      if (!isTemporary && referencedPaths.contains(relative)) continue;
      try {
        final modified = (await entity.stat()).modified.toUtc();
        if (modified.isBefore(cutoff)) await entity.delete();
      } catch (_) {
        // Best-effort recovery is retried on a later maintenance pass.
      }
    }
  }
}

class _ImageFormat {
  const _ImageFormat(this.extension, this.mimeType);
  final String extension;
  final String mimeType;
}

_ImageFormat _imageFormat(Uint8List bytes) {
  if (bytes.length >= 3 &&
      bytes[0] == 0xff &&
      bytes[1] == 0xd8 &&
      bytes[2] == 0xff) {
    return const _ImageFormat('jpg', 'image/jpeg');
  }
  if (bytes.length >= 8 &&
      bytes[0] == 0x89 &&
      bytes[1] == 0x50 &&
      bytes[2] == 0x4e &&
      bytes[3] == 0x47) {
    return const _ImageFormat('png', 'image/png');
  }
  if (bytes.length >= 12 &&
      String.fromCharCodes(bytes.sublist(0, 4)) == 'RIFF' &&
      String.fromCharCodes(bytes.sublist(8, 12)) == 'WEBP') {
    return const _ImageFormat('webp', 'image/webp');
  }
  // Some platform pickers return HEIC/other decodable formats. Keep the exact
  // bytes under a neutral extension rather than altering them.
  return const _ImageFormat('img', 'application/octet-stream');
}
