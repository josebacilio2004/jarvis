import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../constants.dart';

class ArcReactorWidget extends StatefulWidget {
  final bool isSpeaking;
  final bool isListening;
  final double size;

  const ArcReactorWidget({
    super.key,
    this.isSpeaking = false,
    this.isListening = false,
    this.size = 180,
  });

  @override
  State<ArcReactorWidget> createState() => _ArcReactorWidgetState();
}

class _ArcReactorWidgetState extends State<ArcReactorWidget> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final activeColor = widget.isListening
        ? StarkConstants.starkRed
        : StarkConstants.primaryCyan;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: ArcReactorPainter(
            rotation: _controller.value * 2 * math.pi,
            isSpeaking: widget.isSpeaking,
            isListening: widget.isListening,
            themeColor: activeColor,
          ),
        );
      },
    );
  }
}

class ArcReactorPainter extends CustomPainter {
  final double rotation;
  final bool isSpeaking;
  final bool isListening;
  final Color themeColor;

  ArcReactorPainter({
    required this.rotation,
    required this.isSpeaking,
    required this.isListening,
    required this.themeColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // Outer Glow Circle
    final glowPaint = Paint()
      ..color = themeColor.withValues(alpha: 0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
    canvas.drawCircle(center, radius - 4, glowPaint);

    // Outer Thin Ring
    final outerRing = Paint()
      ..color = themeColor.withValues(alpha: 0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    canvas.drawCircle(center, radius - 8, outerRing);

    // Rotating Segmented Ring
    final segmentPaint = Paint()
      ..color = themeColor.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.5;

    final segmentCount = 10;
    final sweepAngle = (2 * math.pi) / segmentCount * 0.55;
    for (int i = 0; i < segmentCount; i++) {
      final startAngle = rotation + (i * (2 * math.pi / segmentCount));
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - 20),
        startAngle,
        sweepAngle,
        false,
        segmentPaint,
      );
    }

    // Counter-Rotating Inner Ring
    final innerSegmentPaint = Paint()
      ..color = themeColor.withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    final innerSegmentCount = 6;
    final innerSweep = (2 * math.pi) / innerSegmentCount * 0.4;
    for (int i = 0; i < innerSegmentCount; i++) {
      final startAngle = -rotation * 1.5 + (i * (2 * math.pi / innerSegmentCount));
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - 38),
        startAngle,
        innerSweep,
        false,
        innerSegmentPaint,
      );
    }

    // Glowing Central Core
    final coreGlow = Paint()
      ..color = themeColor.withValues(alpha: isSpeaking || isListening ? 0.9 : 0.45)
      ..style = PaintingStyle.fill
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, isSpeaking ? 16 : 8);
    canvas.drawCircle(center, radius - 55, coreGlow);

    final coreWhite = Paint()
      ..color = Colors.white.withValues(alpha: isSpeaking || isListening ? 0.95 : 0.7)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, (radius - 55) * 0.65, coreWhite);
  }

  @override
  bool shouldRepaint(covariant ArcReactorPainter oldDelegate) {
    return oldDelegate.rotation != rotation ||
        oldDelegate.isSpeaking != isSpeaking ||
        oldDelegate.isListening != isListening ||
        oldDelegate.themeColor != themeColor;
  }
}
