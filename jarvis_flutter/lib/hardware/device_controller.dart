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

  /// Program and automatically activate an Android system alarm
  static Future<bool> setAlarm({
    required int hour,
    required int minute,
    String message = 'Alarma J.A.R.V.I.S.',
    bool skipUi = true,
  }) async {
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.SET_ALARM',
        arguments: <String, dynamic>{
          'android.intent.extra.alarm.HOUR': hour,
          'android.intent.extra.alarm.MINUTES': minute,
          'android.intent.extra.alarm.MESSAGE': message,
          'android.intent.extra.alarm.SKIP_UI': true,
        },
        flags: const <int>[flagActivityNewTask],
      );
      await intent.launch();
      vibrate(100);
      return true;
    } catch (e) {
      debugPrint('[DeviceController] Error setting alarm: $e');
      return false;
    }
  }

  /// Program and automatically start a countdown timer
  static Future<bool> setTimer({
    required int seconds,
    String message = 'Temporizador J.A.R.V.I.S.',
    bool skipUi = true,
  }) async {
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.SET_TIMER',
        arguments: <String, dynamic>{
          'android.intent.extra.alarm.LENGTH': seconds,
          'android.intent.extra.alarm.MESSAGE': message,
          'android.intent.extra.alarm.SKIP_UI': true,
        },
        flags: const <int>[flagActivityNewTask],
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

  /// Request all essential runtime permissions (Contacts, Calendar, Call, Notifications, Camera)
  static Future<void> requestEssentialPermissions() async {
    try {
      await _appChannel.invokeMethod('requestPermissions');
    } catch (e) {
      debugPrint('[DeviceController] Error requesting essential permissions: $e');
    }
  }

  /// Request call permission from Android OS
  static Future<bool> requestCallPermission() async {
    try {
      final res = await _appChannel.invokeMethod<bool>('requestCallPermission');
      return res ?? false;
    } catch (_) {
      return false;
    }
  }

  /// Initiate and execute phone call immediately
  static Future<bool> makeCall(String target) async {
    try {
      final cleanDigits = target.replaceAll(RegExp(r'[^0-9+*#]'), '');
      if (cleanDigits.isNotEmpty) {
        // 1. Direct native call with automatic runtime permission prompt
        try {
          final res = await _appChannel.invokeMethod<bool>('makeDirectCall', {'number': cleanDigits});
          if (res == true) return true;
        } catch (e) {
          debugPrint('[DeviceController] Native makeDirectCall error: $e');
        }
      }

      // 2. Fallback to DIAL
      final dialIntent = AndroidIntent(
        action: 'android.intent.action.DIAL',
        data: 'tel:${target.replaceAll(' ', '')}',
        flags: const <int>[flagActivityNewTask],
      );
      await dialIntent.launch();
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

  /// Launch Android system Camera app
  static Future<bool> openCamera() async {
    try {
      final res = await _appChannel.invokeMethod<bool>('openCamera');
      return res ?? false;
    } catch (e) {
      debugPrint('[DeviceController] Error opening camera: $e');
      return false;
    }
  }

  /// Get phone battery level and charging state
  static Future<Map<String, dynamic>> getBatteryStatus() async {
    try {
      final res = await _appChannel.invokeMapMethod<String, dynamic>('getBatteryStatus');
      return res ?? {'level': 100, 'isCharging': false};
    } catch (e) {
      debugPrint('[DeviceController] Error getting battery: $e');
      return {'level': 100, 'isCharging': false};
    }
  }

  /// Display persistent Stark status / media notification in Android shade and lock screen
  static Future<void> showNotification({
    required String title,
    required String content,
    bool isPlaying = false,
  }) async {
    try {
      await _appChannel.invokeMethod('showNotification', {
        'title': title,
        'content': content,
        'isPlaying': isPlaying,
      });
    } catch (e) {
      debugPrint('[DeviceController] Error showing notification: $e');
    }
  }

  /// Cancel status notification
  static Future<void> cancelNotification() async {
    try {
      await _appChannel.invokeMethod('cancelNotification');
    } catch (e) {
      debugPrint('[DeviceController] Error canceling notification: $e');
    }
  }

  /// Send WhatsApp message to contact name or phone number
  static Future<bool> sendWhatsApp({
    required String target,
    required String message,
  }) async {
    try {
      final res = await _appChannel.invokeMethod<bool>('sendWhatsApp', {
        'target': target,
        'message': message,
      });
      vibrate(60);
      return res ?? false;
    } catch (e) {
      debugPrint('[DeviceController] Error sending WhatsApp: $e');
      return false;
    }
  }

  /// Initiate WhatsApp VoIP voice call to contact name or phone number
  static Future<bool> makeWhatsAppCall({
    required String target,
  }) async {
    try {
      final res = await _appChannel.invokeMethod<bool>('makeWhatsAppCall', {
        'target': target,
      });
      vibrate(80);
      return res ?? false;
    } catch (e) {
      debugPrint('[DeviceController] Error making WhatsApp call: $e');
      return false;
    }
  }

  /// Add event to Google Calendar / Android native calendar
  static Future<bool> addCalendarEvent({
    required String title,
    String? description,
    required DateTime startTime,
    required DateTime endTime,
    String? location,
  }) async {
    try {
      final res = await _appChannel.invokeMethod<bool>('addCalendarEvent', {
        'title': title,
        'description': description,
        'startTimeMs': startTime.millisecondsSinceEpoch,
        'endTimeMs': endTime.millisecondsSinceEpoch,
        'location': location,
      });
      vibrate(60);
      return res ?? false;
    } catch (e) {
      debugPrint('[DeviceController] Error adding calendar event: $e');
      return false;
    }
  }
}
