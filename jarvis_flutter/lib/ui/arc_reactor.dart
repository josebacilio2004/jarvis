import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants.dart';

class ArcReactorWidget extends StatefulWidget {
  final bool isSpeaking;
  final bool isListening;
  final double size;

  const ArcReactorWidget({
    super.key,
    this.isSpeaking = false,
    this.isListening = false,
    this.size = 175,
  });

  @override
  State<ArcReactorWidget> createState() => _ArcReactorWidgetState();
}

class _ArcReactorWidgetState extends State<ArcReactorWidget> with TickerProviderStateMixin {
  late AnimationController _rotationController;
  late AnimationController _pulseController;
  late AnimationController _waveController;

  @override
  void initState() {
    super.initState();
    _rotationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);

    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();
  }

  @override
  void dispose() {
    _rotationController.dispose();
    _pulseController.dispose();
    _waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final activeColor = widget.isListening
        ? StarkConstants.starkRed
        : (widget.isSpeaking ? StarkConstants.primaryCyan : StarkConstants.primaryCyan);

    return AnimatedBuilder(
      animation: Listenable.merge([_rotationController, _pulseController, _waveController]),
      builder: (context, child) {
        final pulseVal = _pulseController.value;
        final waveVal = _waveController.value;
        final scale = widget.isSpeaking ? 1.0 + (0.05 * math.sin(pulseVal * math.pi)) : 1.0;

        return Transform.scale(
          scale: scale,
          child: SizedBox(
            width: widget.size,
            height: widget.size,
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Custom Painted Arc Reactor Rings & Speech Spectrum
                CustomPaint(
                  size: Size(widget.size, widget.size),
                  painter: ArcReactorPainter(
                    rotation: _rotationController.value * 2 * math.pi,
                    pulseValue: pulseVal,
                    waveValue: waveVal,
                    isSpeaking: widget.isSpeaking,
                    isListening: widget.isListening,
                    themeColor: activeColor,
                  ),
                ),

                // Center Holographic Core Badge with "J.A.R.V.I.S."
                Container(
                  width: widget.size * 0.46,
                  height: widget.size * 0.46,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        widget.isSpeaking
                            ? StarkConstants.primaryCyan.withValues(alpha: 0.35)
                            : (widget.isListening
                                ? StarkConstants.starkRed.withValues(alpha: 0.35)
                                : Colors.black.withValues(alpha: 0.85)),
                        Colors.black.withValues(alpha: 0.95),
                      ],
                    ),
                    border: Border.all(
                      color: widget.isListening
                          ? StarkConstants.starkRed.withValues(alpha: 0.8)
                          : (widget.isSpeaking ? Colors.white : StarkConstants.primaryCyan.withValues(alpha: 0.7)),
                      width: widget.isSpeaking ? 2.0 : 1.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: activeColor.withValues(alpha: widget.isSpeaking ? 0.6 : 0.25),
                        blurRadius: widget.isSpeaking ? 16 : 8,
                        spreadRadius: widget.isSpeaking ? 3 : 1,
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'J.A.R.V.I.S.',
                        style: GoogleFonts.orbitron(
                          color: widget.isListening
                              ? StarkConstants.starkRed
                              : (widget.isSpeaking ? Colors.white : StarkConstants.primaryCyan),
                          fontSize: 11.5,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2.2,
                          shadows: [
                            Shadow(
                              color: activeColor,
                              blurRadius: widget.isSpeaking ? 12 : 6,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 4,
                            height: 4,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: widget.isListening
                                  ? StarkConstants.starkRed
                                  : (widget.isSpeaking ? StarkConstants.primaryCyan : StarkConstants.starkGreen),
                              boxShadow: [
                                BoxShadow(
                                  color: activeColor,
                                  blurRadius: 4,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            widget.isSpeaking
                                ? 'HABLANDO'
                                : (widget.isListening ? 'ESCUCHANDO' : 'ONLINE'),
                            style: GoogleFonts.shareTechMono(
                              color: widget.isSpeaking
                                  ? StarkConstants.primaryCyan
                                  : (widget.isListening ? StarkConstants.starkRed : Colors.white70),
                              fontSize: 7.5,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.0,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class ArcReactorPainter extends CustomPainter {
  final double rotation;
  final double pulseValue;
  final double waveValue;
  final bool isSpeaking;
  final bool isListening;
  final Color themeColor;

  ArcReactorPainter({
    required this.rotation,
    required this.pulseValue,
    required this.waveValue,
    required this.isSpeaking,
    required this.isListening,
    required this.themeColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // 1. Reactive Acoustic Ripple Waves (Expanding when speaking)
    if (isSpeaking || isListening) {
      final waveRadius = (radius * 0.48) + ((radius * 0.50) * waveValue);
      final waveAlpha = (1.0 - waveValue).clamp(0.0, 1.0) * 0.5;
      final wavePaint = Paint()
        ..color = themeColor.withValues(alpha: waveAlpha)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0;
      canvas.drawCircle(center, waveRadius, wavePaint);

      final secondWave = (waveValue + 0.5) % 1.0;
      final waveRadius2 = (radius * 0.48) + ((radius * 0.50) * secondWave);
      final waveAlpha2 = (1.0 - secondWave).clamp(0.0, 1.0) * 0.35;
      final wavePaint2 = Paint()
        ..color = themeColor.withValues(alpha: waveAlpha2)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      canvas.drawCircle(center, waveRadius2, wavePaint2);
    }

    // 2. Outer Halo Glow
    final glowPaint = Paint()
      ..color = themeColor.withValues(alpha: isSpeaking ? 0.35 : 0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = isSpeaking ? 4.0 : 2.5
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, isSpeaking ? 12 : 6);
    canvas.drawCircle(center, radius - 4, glowPaint);

    // 3. Outer HUD Circular Grid
    final outerRing = Paint()
      ..color = themeColor.withValues(alpha: 0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    canvas.drawCircle(center, radius - 8, outerRing);

    // 4. Radial Audio Equalizer Spikes / Blades
    final spikeCount = 24;
    final baseInnerR = radius - 26;
    final maxSpikeLen = 14.0;

    for (int i = 0; i < spikeCount; i++) {
      final angle = (i * (2 * math.pi / spikeCount)) + (rotation * 0.25);
      double spikeLen = 5.0;
      if (isSpeaking) {
        // Dynamic simulated audio frequency spectrum
        final harmonic = math.sin((i * 1.5) + (waveValue * math.pi * 4)).abs();
        spikeLen = 5.0 + (harmonic * maxSpikeLen);
      } else if (isListening) {
        spikeLen = 4.0 + (math.sin((i * 2.0) + (pulseValue * math.pi * 3)).abs() * 8.0);
      }

      final startX = center.dx + baseInnerR * math.cos(angle);
      final startY = center.dy + baseInnerR * math.sin(angle);
      final endX = center.dx + (baseInnerR + spikeLen) * math.cos(angle);
      final endY = center.dy + (baseInnerR + spikeLen) * math.sin(angle);

      final spikePaint = Paint()
        ..color = themeColor.withValues(alpha: isSpeaking ? 0.85 : 0.45)
        ..strokeWidth = 2.0
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(Offset(startX, startY), Offset(endX, endY), spikePaint);
    }

    // 5. Rotating Turbine Segmented Ring (Mark VII Blades)
    final segmentPaint = Paint()
      ..color = themeColor.withValues(alpha: isSpeaking ? 0.95 : 0.75)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.5;

    final segmentCount = 10;
    final sweepAngle = (2 * math.pi) / segmentCount * 0.55;
    for (int i = 0; i < segmentCount; i++) {
      final startAngle = rotation + (i * (2 * math.pi / segmentCount));
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - 28),
        startAngle,
        sweepAngle,
        false,
        segmentPaint,
      );
    }

    // 6. Counter-Rotating Inner Blades
    final innerSegmentPaint = Paint()
      ..color = (isSpeaking ? Colors.white : themeColor).withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final innerSegmentCount = 6;
    final innerSweep = (2 * math.pi) / innerSegmentCount * 0.40;
    for (int i = 0; i < innerSegmentCount; i++) {
      final startAngle = -rotation * 1.6 + (i * (2 * math.pi / innerSegmentCount));
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - 44),
        startAngle,
        innerSweep,
        false,
        innerSegmentPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant ArcReactorPainter oldDelegate) {
    return oldDelegate.rotation != rotation ||
        oldDelegate.pulseValue != pulseValue ||
        oldDelegate.waveValue != waveValue ||
        oldDelegate.isSpeaking != isSpeaking ||
        oldDelegate.isListening != isListening ||
        oldDelegate.themeColor != themeColor;
  }
}
