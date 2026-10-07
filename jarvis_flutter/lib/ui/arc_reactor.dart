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
    this.size = 150,
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
      duration: const Duration(seconds: 12),
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

        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Transform.scale(
              scale: scale,
              child: SizedBox(
                width: widget.size,
                height: widget.size,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // 1. Outer Holographic Shockwaves & Spectrum Rings
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

                    // 2. Glowing Halo Backlight
                    Container(
                      width: widget.size * 0.72,
                      height: widget.size * 0.72,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: activeColor.withValues(
                              alpha: widget.isSpeaking ? 0.45 : (widget.isListening ? 0.40 : 0.20),
                            ),
                            blurRadius: widget.isSpeaking ? 28 : (widget.isListening ? 22 : 14),
                            spreadRadius: widget.isSpeaking ? 6 : (widget.isListening ? 4 : 1),
                          ),
                        ],
                      ),
                    ),

                    // 3. Official Holographic J.A.R.V.I.S. Core Emblem Image
                    SizedBox(
                      width: widget.size * 0.78,
                      height: widget.size * 0.78,
                      child: widget.isListening
                          ? ColorFiltered(
                              colorFilter: const ColorFilter.mode(
                                StarkConstants.starkRed,
                                BlendMode.srcATop,
                              ),
                              child: Image.asset(
                                'assets/images/jarvis_core.png',
                                fit: BoxFit.contain,
                              ),
                            )
                          : Image.asset(
                              'assets/images/jarvis_core.png',
                              fit: BoxFit.contain,
                            ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 5),
            // 4. Sleek Stark Status Badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.75),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: activeColor.withValues(alpha: widget.isSpeaking || widget.isListening ? 0.7 : 0.35),
                  width: 1.0,
                ),
                boxShadow: [
                  BoxShadow(
                    color: activeColor.withValues(alpha: widget.isSpeaking ? 0.3 : 0.1),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 5,
                    height: 5,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: widget.isListening
                          ? StarkConstants.starkRed
                          : (widget.isSpeaking ? StarkConstants.primaryCyan : StarkConstants.starkGreen),
                      boxShadow: [
                        BoxShadow(
                          color: activeColor,
                          blurRadius: 5,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    widget.isSpeaking
                        ? 'HABLANDO'
                        : (widget.isListening ? 'ESCUCHANDO' : 'SISTEMA ONLINE'),
                    style: GoogleFonts.shareTechMono(
                      color: widget.isSpeaking
                          ? StarkConstants.primaryCyan
                          : (widget.isListening ? StarkConstants.starkRed : Colors.white70),
                      fontSize: 8.5,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
            ),
          ],
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

    // 1. Reactive Acoustic Ripple Waves (Expanding outward when speaking/listening)
    if (isSpeaking || isListening) {
      final waveRadius = (radius * 0.70) + ((radius * 0.30) * waveValue);
      final waveAlpha = (1.0 - waveValue).clamp(0.0, 1.0) * 0.55;
      final wavePaint = Paint()
        ..color = themeColor.withValues(alpha: waveAlpha)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0;
      canvas.drawCircle(center, waveRadius, wavePaint);

      final secondWave = (waveValue + 0.5) % 1.0;
      final waveRadius2 = (radius * 0.70) + ((radius * 0.30) * secondWave);
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
      ..strokeWidth = isSpeaking ? 3.5 : 2.0
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, isSpeaking ? 10 : 5);
    canvas.drawCircle(center, radius - 2, glowPaint);

    // 3. Outer HUD Circular Grid
    final outerRing = Paint()
      ..color = themeColor.withValues(alpha: 0.35)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawCircle(center, radius - 4, outerRing);

    // 4. Radial Audio Equalizer Spikes
    final spikeCount = 28;
    final baseInnerR = radius - 15;
    final maxSpikeLen = 12.0;

    for (int i = 0; i < spikeCount; i++) {
      final angle = (i * (2 * math.pi / spikeCount)) + (rotation * 0.2);
      double spikeLen = 4.0;
      if (isSpeaking) {
        final harmonic = math.sin((i * 1.5) + (waveValue * math.pi * 4)).abs();
        spikeLen = 4.0 + (harmonic * maxSpikeLen);
      } else if (isListening) {
        spikeLen = 3.5 + (math.sin((i * 2.0) + (pulseValue * math.pi * 3)).abs() * 7.0);
      }

      final startX = center.dx + baseInnerR * math.cos(angle);
      final startY = center.dy + baseInnerR * math.sin(angle);
      final endX = center.dx + (baseInnerR + spikeLen) * math.cos(angle);
      final endY = center.dy + (baseInnerR + spikeLen) * math.sin(angle);

      final spikePaint = Paint()
        ..color = themeColor.withValues(alpha: isSpeaking ? 0.9 : 0.4)
        ..strokeWidth = 1.8
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(Offset(startX, startY), Offset(endX, endY), spikePaint);
    }

    // 5. Rotating Turbine Segmented Ring (Mark VII Outer Blades)
    final segmentPaint = Paint()
      ..color = themeColor.withValues(alpha: isSpeaking ? 0.9 : 0.65)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    final segmentCount = 12;
    final sweepAngle = (2 * math.pi) / segmentCount * 0.45;
    for (int i = 0; i < segmentCount; i++) {
      final startAngle = rotation + (i * (2 * math.pi / segmentCount));
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - 12),
        startAngle,
        sweepAngle,
        false,
        segmentPaint,
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
