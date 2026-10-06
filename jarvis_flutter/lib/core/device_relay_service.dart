import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../hardware/device_controller.dart';
import 'api_service.dart';

class DeviceRelayService {
  static final DeviceRelayService _instance = DeviceRelayService._internal();
  factory DeviceRelayService() => _instance;
  DeviceRelayService._internal();

  bool _isRunning = false;
  http.Client? _client;
  Function(Map<String, dynamic>)? onRemoteActionReceived;

  bool get isConnected => _isRunning;

  /// Start background stream listening for PC commands
  void startListening({Function(Map<String, dynamic>)? onAction}) {
    if (_isRunning) return;
    _isRunning = true;
    onRemoteActionReceived = onAction;
    _listenLoop();
  }

  void stopListening() {
    _isRunning = false;
    _client?.close();
  }

  Future<void> _listenLoop() async {
    while (_isRunning) {
      try {
        final api = ApiService();
        final url = '${api.serverUrl}/device-stream';
        _client = http.Client();

        final request = http.Request('GET', Uri.parse(url));
        request.headers['X-User-Id'] = api.userId;

        debugPrint('[DeviceRelay] Conectando canal de órdenes remotas PC -> Móvil: $url');
        final response = await _client!.send(request);

        final stream = response.stream.transform(utf8.decoder).transform(const LineSplitter());

        await for (final line in stream) {
          if (!_isRunning) break;
          if (line.startsWith('data: ')) {
            final jsonStr = line.substring(6).trim();
            if (jsonStr.isEmpty) continue;

            try {
              final event = jsonDecode(jsonStr) as Map<String, dynamic>;
              debugPrint('[DeviceRelay] Evento remoto recibido desde PC: $event');

              if (event['type'] == 'remote_action' && event['action'] != null) {
                final action = event['action'] as Map<String, dynamic>;
                await _executeRemoteAction(action);
                onRemoteActionReceived?.call(action);
              }
            } catch (e) {
              debugPrint('[DeviceRelay] Error parseando evento: $e');
            }
          }
        }
      } catch (e) {
        debugPrint('[DeviceRelay] Interrupción en túnel remoto: $e. Reintentando en 5s...');
      } finally {
        _client?.close();
      }

      if (_isRunning) {
        await Future.delayed(const Duration(seconds: 5));
      }
    }
  }

  /// Execute received action natively on the phone
  Future<void> _executeRemoteAction(Map<String, dynamic> action) async {
    final actType = action['action'] as String?;
    if (actType == null) return;

    // Wake the screen up upon receiving command
    await DeviceController.wakeScreen();
    await DeviceController.vibrate(150);

    switch (actType) {
      case 'toggle_flashlight':
        final enable = action['enable'] == true;
        await DeviceController.toggleFlashlight(enable);
        break;

      case 'set_alarm':
        final hour = (action['hour'] as num?)?.toInt() ?? 7;
        final minute = (action['minute'] as num?)?.toInt() ?? 0;
        final message = action['message'] as String? ?? 'Alarma J.A.R.V.I.S.';
        await DeviceController.setAlarm(hour: hour, minute: minute, message: message);
        break;

      case 'set_timer':
        final seconds = (action['seconds'] as num?)?.toInt() ?? 300;
        final message = action['message'] as String? ?? 'Temporizador J.A.R.V.I.S.';
        await DeviceController.setTimer(seconds: seconds, message: message);
        break;

      case 'open_maps':
        final location = action['location'] as String? ?? '';
        if (location.isNotEmpty) {
          await DeviceController.openMaps(location);
        }
        break;

      case 'call':
        final target = action['target'] as String? ?? '';
        if (target.isNotEmpty) {
          await DeviceController.makeCall(target);
        }
        break;

      default:
        debugPrint('[DeviceRelay] Acción no manejada directamente: $actType');
    }
  }
}
