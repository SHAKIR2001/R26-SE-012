// =============================================================================
// File: grading_forecast_api_service.dart
// Purpose: Provides the grading forecast api service application service.
// =============================================================================
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/grading_forecast_result.dart';

/// Safe, typed errors exposed to the UI instead of raw provider/network text.
class GradingForecastApiException implements Exception {
  const GradingForecastApiException(
    this.message, {
    this.kind = GradingForecastApiErrorKind.analysisFailed,
    this.statusCode,
    this.cause,
  });
  final String message;
  final GradingForecastApiErrorKind kind;
  final int? statusCode;
  final Object? cause;
  @override
  // Return a readable description of this value.
  String toString() => 'GradingForecastApiException($statusCode): $message';
}

enum GradingForecastApiErrorKind {
  emptyImage,
  imageTooLarge,
  invalidBackendAddress,
  invalidImage,
  unsupportedImage,
  malformedRequest,
  serviceBusy,
  serviceUnavailable,
  timeout,
  unreachable,
  malformedResponse,
  analysisFailed,
}

/// Sends the original selected image to the Phase 7 backend.
///
/// Grading runs through the frozen backend ONNX pipeline. There is no local
/// prediction fallback here, because a fallback could silently change the
/// approved preprocessing, thresholds, model, or Phase 6 decision semantics.
class GradingForecastApiService {
  GradingForecastApiService({String? baseUrlOverride, http.Client? client})
    : _baseUrl = _resolveBaseUrl(baseUrlOverride),
      _client = client ?? http.Client(),
      _ownsClient = client == null;
  static const int maxImageBytes = 10 * 1024 * 1024;
  static const Duration requestTimeout = Duration(seconds: 120);
  final String _baseUrl;
  final http.Client _client;
  final bool _ownsClient;
  // Return the configured backend base URL.
  String get baseUrl => _baseUrl;

  /// Validates the upload locally, then strictly parses the complete response
  /// contract returned by the backend.
  Future<GradingForecastResult> analyzeBytes(
    Uint8List bytes,
    String filename,
  ) async {
    // Analyze the supplied image bytes.
    if (bytes.isEmpty) {
      throw const GradingForecastApiException(
        'The selected image is empty.',
        kind: GradingForecastApiErrorKind.emptyImage,
      );
    }
    if (bytes.length > maxImageBytes) {
      throw const GradingForecastApiException(
        'The selected image exceeds the 10 MB upload limit.',
        kind: GradingForecastApiErrorKind.imageTooLarge,
        statusCode: 413,
      );
    }
    final endpoint = Uri.tryParse('$_baseUrl/api/v1/grading-forecast/analyze');
    if (endpoint == null ||
        !endpoint.hasScheme ||
        (endpoint.scheme != 'http' && endpoint.scheme != 'https')) {
      throw const GradingForecastApiException(
        'The research backend address is invalid.',
        kind: GradingForecastApiErrorKind.invalidBackendAddress,
      );
    }
    // Put the selected image in the multipart field expected by the backend.
    final request = http.MultipartRequest('POST', endpoint)
      ..files.add(
        http.MultipartFile.fromBytes('image', bytes, filename: filename),
      );
    try {
      // Send the image request from the frontend to the backend.
      final streamed = await _client.send(request).timeout(requestTimeout);
      // Receive the analysis response returned by the backend.
      final response = await http.Response.fromStream(
        streamed,
      ).timeout(requestTimeout);
      Object? decoded;
      if (response.body.isNotEmpty) {
        try {
          // Convert the backend response into data the frontend can read.
          decoded = json.decode(response.body);
        } on FormatException {
          if (response.statusCode >= 200 && response.statusCode < 300) {
            rethrow;
          }
        }
      }
      // HTTP failures are mapped to safe, localized UI messages below; raw
      // backend details are never displayed as an untrusted fallback.
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final detail = _responseDetail(decoded);
        throw GradingForecastApiException(
          detail ?? _messageForStatus(response.statusCode),
          kind: _kindForStatus(response.statusCode),
          statusCode: response.statusCode,
        );
      }
      if (decoded is! Map) {
        throw const GradingForecastApiException(
          'Unexpected response format.',
          kind: GradingForecastApiErrorKind.malformedResponse,
        );
      }
      // Pass the validated backend data to the frontend application layer.
      return GradingForecastResult.fromJson(decoded.cast<String, dynamic>());
    } on GradingForecastApiException {
      rethrow;
    } on TimeoutException catch (e) {
      throw GradingForecastApiException(
        'Analysis timed out. Please retry.',
        kind: GradingForecastApiErrorKind.timeout,
        cause: e,
      );
    } on SocketException catch (e) {
      throw GradingForecastApiException(
        'Cannot reach the research backend.',
        kind: GradingForecastApiErrorKind.unreachable,
        cause: e,
      );
    } on http.ClientException catch (e) {
      throw GradingForecastApiException(
        'Cannot reach the research backend.',
        kind: GradingForecastApiErrorKind.unreachable,
        cause: e,
      );
    } on FormatException catch (e) {
      throw GradingForecastApiException(
        'Backend returned malformed data.',
        kind: GradingForecastApiErrorKind.malformedResponse,
        cause: e,
      );
    }
  }

  void close() {
    // Close the owned client or database resources.
    if (_ownsClient) _client.close();
  }

  static String? _responseDetail(Object? decoded) {
    // Validation details are accepted only as a short backend-provided string;
    // structured error lists receive a generic message to keep the UI stable.
    if (decoded is! Map) return null;
    final detail = decoded['detail'];
    if (detail is String && detail.trim().isNotEmpty) return detail;
    if (detail is List && detail.isNotEmpty) {
      return 'The request was rejected because one or more fields are invalid.';
    }
    return null;
  }

  // Process message for status for this flow.
  static String _messageForStatus(int statusCode) => switch (statusCode) {
    400 => 'The selected file is not a readable image.',
    413 => 'The selected image exceeds the safe upload or processing limit.',
    415 => 'Use a non-animated JPEG, PNG, or WEBP image.',
    422 => 'The image request is malformed.',
    429 => 'The hosted service is busy. Please wait and retry.',
    502 || 503 || 504 =>
      'The research backend is temporarily unavailable. Please retry later.',
    _ => 'Analysis failed on the research backend.',
  };

  // Process kind for status for this flow.
  static GradingForecastApiErrorKind _kindForStatus(int statusCode) =>
      switch (statusCode) {
        400 => GradingForecastApiErrorKind.invalidImage,
        413 => GradingForecastApiErrorKind.imageTooLarge,
        415 => GradingForecastApiErrorKind.unsupportedImage,
        422 => GradingForecastApiErrorKind.malformedRequest,
        429 => GradingForecastApiErrorKind.serviceBusy,
        502 || 503 || 504 => GradingForecastApiErrorKind.serviceUnavailable,
        _ => GradingForecastApiErrorKind.analysisFailed,
      };

  static String _resolveBaseUrl(String? override) {
    // Build-time configuration is preferred. Platform defaults are local
    // development addresses only and are not claims about a hosted service.
    if (override != null && override.trim().isNotEmpty) {
      return override.replaceAll(RegExp(r'/$'), '');
    }
    const configured = String.fromEnvironment('PEPPER_API_BASE_URL');
    if (configured.isNotEmpty) return configured.replaceAll(RegExp(r'/$'), '');
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }
}
