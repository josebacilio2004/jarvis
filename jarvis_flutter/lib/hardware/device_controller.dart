import 'package:flutter/foundation.dart';
import 'package:torch_light/torch_light.dart';
import 'package:android_intent_plus/android_intent.dart';
import 'package:vibration/vibration.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

class DeviceController {
  static bool isTorchOn = false;

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
