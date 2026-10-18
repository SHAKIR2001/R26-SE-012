// Imports the pest analysis model that contains the AI detection result.
import 'pest_analysis.dart';
import 'remediation_engine.dart' show Market, TreatmentOption;

/// Represents the final treatment recommendation generated
/// from the pest analysis result.
///
/// This model stores:
/// - Main recommended action
/// - Whether the economic treatment threshold is exceeded
/// - Available treatment options
/// - Safety/export warnings
/// - Additional treatment or export notes
class PestTreatment {
  final String action; // headline

  /// Indicates whether the pest infestation has crossed
  /// the economic treatment threshold.
  ///
  /// false = monitoring/prevention only.
  /// true = treatment may be required.
  final bool aboveThreshold; // false → monitoring only (below the ETL)

  /// Ordered list of treatment options.
  ///
  /// IPM principle is followed where possible:
  /// cultural → biological/botanical → chemical.
  final List<TreatmentOption>
  options; // ordered: cultural → biological → chemical
  final List<String> warnings;
  final String note; // ETL / export / traceability note

  /// Creates a pest treatment recommendation.
  const PestTreatment({
    required this.action,
    required this.aboveThreshold,
    required this.options,
    required this.warnings,
    required this.note,
  });
}

/// Turns a [PestAnalysis] + [Market] into IPM-first, export-compliant advice.
///
/// Two agronomic rules the spec was missing are encoded here:
///  1. **Economic Threshold Level (ETL)** — below a pest-density threshold the
///     advice is monitoring, NOT spraying. Spraying below threshold wastes money
///     and adds needless residue that can disqualify an export lot.
///  2. **IPM order** — cultural/biological controls first, chemicals only when
///     severity is high, and then filtered by destination market.
///
/// Exact per-species ETL counts and MRL/PHI values are location- and
/// formulation-specific; they are surfaced as "confirm locally" notes rather
/// than fabricated. The one hard regulatory fact encoded is the EU Fipronil ban.
class PestTreatmentEngine {
  static const String _confirmPhi =
      'Observe the pre-harvest interval — confirm the exact days with your agri '
      'authority before harvesting for export.';

  static const _sticky = TreatmentOption(
    name: 'Sticky traps + weekly scouting',
    method:
        'Hang yellow/blue sticky traps and count pests weekly to track whether '
        'the population is rising toward the treatment threshold.',
    allowedInMarket: true,
    phi: 'No residue — safe for export.',
    isChemical: false,
  );

  /// This is a non-chemical approach and is generally the
  /// first step when the infestation is low.

  static const _cultural = TreatmentOption(
    name: 'Remove infested parts + field hygiene',
    method:
        'Prune and destroy heavily infested leaves/shoots, remove weeds, and '
        'protect natural enemies (do not spray broadly).',
    allowedInMarket: true,
    phi: 'No residue — safe for export.',
    isChemical: false,
  );

  static const _neem = TreatmentOption(
    name: 'Neem oil (botanical)',
    mix: 'Per product label',
    method:
        'Spray a neem-based product in the early morning or evening. Effective '
        'on soft-bodied pests (thrips, bugs) and gentle on beneficials.',
    allowedInMarket: true,
    phi: 'Low residue, but still observe the label interval before harvest.',
    isChemical: false,
  );

  /// Market restrictions are applied later using [_marketFiltered].
  static const _fipronilBase = TreatmentOption(
    name: 'Fipronil',
    mix: '5 ml per 10 L water',
    method: 'Targeted spray on the affected part only, in the evening.',
    allowedInMarket: true, // overridden per market below
    phi: _confirmPhi,
  );

  /// Acetamiprid chemical treatment option.
  static const _acetamiprid = TreatmentOption(
    name: 'Acetamiprid',
    mix: '25 ml per 10 L water',
    method: 'Targeted spray on the affected part only, in the evening.',
    allowedInMarket: true,
    phi: _confirmPhi,
  );

  /// Finally, it returns the appropriate [PestTreatment].
  static PestTreatment forAnalysis(PestAnalysis a, Market market) {
    if (!a.isPepperPlant) {
      return const PestTreatment(
        action: 'No advice — the image is not a pepper plant.',
        aboveThreshold: false,
        options: [],
        warnings: [],
        note: '',
      );
    }

    if (a.isUncertain) {
      return const PestTreatment(
        action: 'Pest identity is uncertain — confirm before treatment.',
        aboveThreshold: false,
        options: [_sticky],
        warnings: [
          'Do not apply a chemical treatment until the pest is confirmed.',
        ],
        note:
            'Retake a closer photo in good light or ask a local agronomist to '
            'inspect the affected plant.',
      );
    }

    if (a.healthy || a.severityBand == 'none') {
      return const PestTreatment(
        action: 'No pests detected — keep monitoring.',
        aboveThreshold: false,
        options: [_sticky],
        warnings: [],
        note:
            'Scout weekly; treat only if the population crosses the threshold.',
      );
    }

    // Below the economic threshold → monitor + prevent, do NOT spray.
    if (a.severityBand == 'mild') {
      return const PestTreatment(
        action: 'Low infestation — below the treatment threshold. Monitor.',
        aboveThreshold: false,
        options: [_sticky, _cultural],
        warnings: [
          'Do not spray yet — chemical treatment below the economic threshold '
              'wastes money and adds residue that can fail export limits.',
        ],
        note:
            'Re-check in a few days. The exact economic threshold for this pest '
            'is region-specific — confirm it with your agri authority.',
      );
    }
    // -----------------------------------------------------------------------
    // CASE 4: MODERATE INFESTATION
    // -----------------------------------------------------------------------
    // Moderate → IPM: cultural + biological first, chemical optional.
    if (a.severityBand == 'moderate') {
      return PestTreatment(
        action: 'Moderate infestation — start with IPM controls.',
        aboveThreshold: true,
        options: [
          _cultural,
          _neem,
          _marketFiltered(_fipronilBase, market),
          _acetamiprid,
        ],
        warnings: _chemWarnings(market),
        note: _exportNote(a, market),
      );
    }

    // Severe → chemical treatment warranted, still market-filtered + IPM.
    return PestTreatment(
      action: 'Severe infestation — targeted chemical treatment is warranted.',
      // Moderate infestation is considered above the treatment threshold.
      aboveThreshold: true,
      options: [
        _marketFiltered(_fipronilBase, market),
        _acetamiprid,
        _cultural,
      ],
      warnings: _chemWarnings(market),
      note: _exportNote(a, market),
    );
  }

  static TreatmentOption _marketFiltered(TreatmentOption o, Market market) {
    if (o.name == 'Fipronil' && market == Market.eu) {
      return TreatmentOption(
        name: o.name,
        mix: o.mix,
        method: o.method,
        allowedInMarket: false,
        restriction:
            'Banned/withdrawn in the EU — do not use for EU-bound export.',
        phi: o.phi,
        isChemical: o.isChemical,
      );
    }
    return o;
  }

  static List<String> _chemWarnings(Market market) => [
    'Wear protective equipment (gloves, mask) when mixing and spraying.',
    'Spray in the evening and avoid flowering to protect pollinators and '
        'natural enemies.',
    if (market == Market.eu)
      'For EU export use Acetamiprid, neem or cultural control only — '
          'Fipronil residues will fail EU limits.',
  ];

  static String _exportNote(PestAnalysis a, Market market) =>
      'Grading for ${market.label}: ~${a.pestCount} pests / '
      '${a.severityPercentage.toStringAsFixed(0)}% severity on the '
      '${a.plantPart}. A treated lot is only export-eligible once residues fall '
      'within ${market.short} limits — log the product, dose and date for '
      'traceability.';
}
