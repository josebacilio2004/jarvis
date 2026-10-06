import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:torch_light/torch_light.dart';
import 'package:android_intent_plus/android_intent.dart';
import 'package:vibration/vibration.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

class DeviceController {
  static const MethodChannel _appChannel = MethodChannel('com.starkindustries.jarvis/app_control');
  static const int flagActivityNewTask = 0x10000000;
  static bool isTorchOn = false;

  /// Minimize the app to the Android background without terminating
  static Future<void> minimizeApp() async {
    try {
      await _appChannel.invokeMethod('minimizeApp');
    } catch (e) {
      debugPrint('[DeviceController] Error minimizing app: $e');
    }
  }

  /// Control the phone's physical flashlight / LED
  static Future<bool> toggleFlashlight(bool enable) async {
    try {
      if (enable) {
        await TorchLight.enableTorch();
        isTorchOn = true;
      } else {
        await TorchLight.disableTorch();
        isTorchOn = false;
      }
      vibrate(50);
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error toggling torch: $e');
      return false;
    }
  }

  /// Program an Android system alarm
  static Future<bool> setAlarm({
    required int hour,
    required int minute,
    String message = 'Alarma J.A.R.V.I.S.',
    bool skipUi = false,
  }) async {
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.SET_ALARM',
        arguments: <String, dynamic>{
          'android.intent.extra.alarm.HOUR': hour,
          'android.intent.extra.alarm.MINUTES': minute,
          'android.intent.extra.alarm.MESSAGE': message,
          'android.intent.extra.alarm.SKIP_UI': skipUi,
        },
      );
      await intent.launch();
      vibrate(100);
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error setting alarm: $e');
      return false;
    }
  }

  /// Program a countdown timer
  static Future<bool> setTimer({
    required int seconds,
    String message = 'Temporizador J.A.R.V.I.S.',
    bool skipUi = false,
  }) async {
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.SET_TIMER',
        arguments: <String, dynamic>{
          'android.intent.extra.alarm.LENGTH': seconds,
          'android.intent.extra.alarm.MESSAGE': message,
          'android.intent.extra.alarm.SKIP_UI': skipUi,
        },
      );
      await intent.launch();
      vibrate(100);
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error setting timer: $e');
      return false;
    }
  }

  /// Open Google Maps navigation to a query/location
  static Future<bool> openMaps(String location) async {
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.VIEW',
        data: 'geo:0,0?q=${Uri.encodeComponent(location)}',
      );
      await intent.launch();
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error opening maps: $e');
      return false;
    }
  }

  /// Open external URL (e.g. YouTube watch URL or browser)
  static Future<bool> openUrl(String url) async {
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.VIEW',
        data: url,
        flags: const <int>[flagActivityNewTask],
      );
      await intent.launch();
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error opening URL: $e');
      return false;
    }
  }

  /// Launch song directly into YouTube App with fallback to browser
  static Future<bool> openYouTube({String? videoId, String? watchUrl}) async {
    try {
      final vid = videoId?.trim();
      final targetUrl = (vid != null && vid.isNotEmpty)
          ? 'https://www.youtube.com/watch?v=$vid'
          : (watchUrl != null && watchUrl.isNotEmpty ? watchUrl : null);

      if (vid != null && vid.isNotEmpty) {
        // 1. Native YouTube App intent via vnd.youtube scheme
        try {
          final appIntent = AndroidIntent(
            action: 'android.intent.action.VIEW',
            data: 'vnd.youtube:$vid',
            flags: const <int>[flagActivityNewTask],
          );
          await appIntent.launch();
          return true;
        } catch (e) {
          debugPrint('[DeviceController] vnd.youtube scheme failed: $e');
        }

        // 2. Direct intent with YouTube package name
        try {
          final pkgIntent = AndroidIntent(
            action: 'android.intent.action.VIEW',
            data: 'https://www.youtube.com/watch?v=$vid',
            package: 'com.google.android.youtube',
            flags: const <int>[flagActivityNewTask],
          );
          await pkgIntent.launch();
          return true;
        } catch (e) {
          debugPrint('[DeviceController] com.google.android.youtube failed: $e');
        }
      }

      // 3. Fallback to generic URL VIEW intent
      if (targetUrl != null && targetUrl.isNotEmpty) {
        final intent = AndroidIntent(
          action: 'android.intent.action.VIEW',
          data: targetUrl,
          flags: const <int>[flagActivityNewTask],
        );
        await intent.launch();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('[DeviceController] Error opening YouTube: $e');
      if (watchUrl != null && watchUrl.isNotEmpty) {
        return await openUrl(watchUrl);
      }
      return false;
    }
  }

  /// Initiate phone call or dialer
  static Future<bool> makeCall(String target) async {
    try {
      final cleanTarget = target.replaceAll(' ', '');
      final intent = AndroidIntent(
        action: 'android.intent.action.DIAL',
        data: 'tel:$cleanTarget',
      );
      await intent.launch();
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error dialing call: $e');
      return false;
    }
  }

  /// Wake up phone screen remotely
  static Future<void> wakeScreen() async {
    try {
      await WakelockPlus.enable();
      await Future.delayed(const Duration(seconds: 15));
      await WakelockPlus.disable();
    } catch (e) {
      debugPrint('[DeviceController] Error waking screen: $e');
    }
  }

  /// Haptic feedback
  static Future<void> vibrate([int milliseconds = 100]) async {
    try {
      final hasVibrator = await Vibration.hasVibrator();
      if (hasVibrator == true) {
        await Vibration.vibrate(duration: milliseconds);
      }
    } catch (_) {}
  }
}
