import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../constants.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String _serverUrl = StarkConstants.defaultServerUrl;
  String _userId = '';

  String get serverUrl => _serverUrl;
  String get userId => _userId;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _serverUrl = prefs.getString('server_url') ?? StarkConstants.defaultServerUrl;
    _userId = prefs.getString('user_id') ?? '';
    if (_userId.isEmpty) {
      _userId = 'stark_${DateTime.now().millisecondsSinceEpoch.toRadixString(36)}';
      await prefs.setString('user_id', _userId);
    }
  }

  Future<void> setServerUrl(String url) async {
    _serverUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', _serverUrl);
  }

  Future<void> setUserId(String uid) async {
    _userId = uid.trim();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_id', _userId);
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'X-User-Id': _userId,
  };

  /// Send chat message with SSE streaming support
  Stream<String> sendChatMessageStream({
    required String message,
    required Function(Map<String, dynamic> action) onAction,
    required Function(String audioUrl) onAudio,
  }) async* {
    final client = http.Client();
    try {
      final request = http.Request('POST', Uri.parse('$_serverUrl/chat-stream'));
      request.headers.addAll(_headers);
      request.body = jsonEncode({'message': message});

      final response = await client.send(request);
      final stream = response.stream.transform(utf8.decoder).transform(const LineSplitter());

      await for (final line in stream) {
        if (line.startsWith('data: ')) {
          final jsonStr = line.substring(6).trim();
          if (jsonStr.isEmpty) continue;
          try {
            final data = jsonDecode(jsonStr) as Map<String, dynamic>;
            if (data.containsKey('chunk')) {
              yield data['chunk'] as String;
            }
            if (data.containsKey('action') && data['action'] != null) {
              onAction(data['action'] as Map<String, dynamic>);
            }
            if (data.containsKey('audio_url') && data['audio_url'] != null) {
              String audioUrl = data['audio_url'] as String;
              if (audioUrl.startsWith('/')) {
                audioUrl = '$_serverUrl$audioUrl';
              }
              onAudio(audioUrl);
            }
          } catch (_) {}
        }
      }
    } catch (e) {
      debugPrint('[ApiService] Stream error: $e');
      yield 'Error al conectar con la red Stark: $e';
    } finally {
      client.close();
    }
  }

  /// Load message history
  Future<List<Map<String, dynamic>>> fetchHistory() async {
    try {
      final res = await http.get(Uri.parse('$_serverUrl/history'), headers: _headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final raw = data['messages'] as List?;
        if (raw != null) {
          return raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        }
      }
    } catch (e) {
      debugPrint('[ApiService] History error: $e');
    }
    return [];
  }

  /// Reset memory
  Future<bool> resetMemory() async {
    try {
      final res = await http.post(Uri.parse('$_serverUrl/reset'), headers: _headers);
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Fetch tasks
  Future<List<Map<String, dynamic>>> fetchTasks() async {
    try {
      final res = await http.get(Uri.parse('$_serverUrl/tasks'), headers: _headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final raw = data['tasks'] as List?;
        if (raw != null) {
          return raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        }
      }
    } catch (_) {}
    return [];
  }
}
