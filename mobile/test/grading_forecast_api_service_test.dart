import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:pepper_care/features/grading_forecast/services/grading_forecast_api_service.dart';

void main() {
  test('rejects an empty image before making a request', () async {
    var called = false;
    final client = MockClient((_) async {
      called = true;
      return http.Response('{}', 200);
    });
    final service = GradingForecastApiService(
      baseUrlOverride: 'https://example.test',
      client: client,
    );

    await expectLater(
      service.analyzeBytes(Uint8List(0), 'empty.jpg'),
      throwsA(isA<GradingForecastApiException>()),
    );
    expect(called, isFalse);
  });

  test('rejects an oversized image before making a request', () async {
    var called = false;
    final client = MockClient((_) async {
      called = true;
      return http.Response('{}', 200);
    });
    final service = GradingForecastApiService(
      baseUrlOverride: 'https://example.test',
      client: client,
    );

    await expectLater(
      service.analyzeBytes(
        Uint8List(GradingForecastApiService.maxImageBytes + 1),
        'large.jpg',
      ),
      throwsA(
        isA<GradingForecastApiException>().having(
          (error) => error.statusCode,
          'statusCode',
          413,
        ),
      ),
    );
    expect(called, isFalse);
  });

  test('maps a hosted 503 without JSON to an availability message', () async {
    final client = MockClient(
      (_) async => http.Response('<html>unavailable</html>', 503),
    );
    final service = GradingForecastApiService(
      baseUrlOverride: 'https://example.test',
      client: client,
    );

    await expectLater(
      service.analyzeBytes(Uint8List.fromList([1]), 'image.jpg'),
      throwsA(
        isA<GradingForecastApiException>()
            .having((error) => error.statusCode, 'statusCode', 503)
            .having(
              (error) => error.message,
              'message',
              contains('temporarily unavailable'),
            ),
      ),
    );
  });

  test('preserves a safe backend validation detail', () async {
    final client = MockClient(
      (_) async => http.Response(
        '{"detail":"Use a non-animated JPEG, PNG, or WEBP image."}',
        415,
        headers: {'content-type': 'application/json'},
      ),
    );
    final service = GradingForecastApiService(
      baseUrlOverride: 'https://example.test',
      client: client,
    );

    await expectLater(
      service.analyzeBytes(Uint8List.fromList([1]), 'image.gif'),
      throwsA(
        isA<GradingForecastApiException>().having(
          (error) => error.message,
          'message',
          'Use a non-animated JPEG, PNG, or WEBP image.',
        ),
      ),
    );
  });
}
