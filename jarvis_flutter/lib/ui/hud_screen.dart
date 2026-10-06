import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:just_audio/just_audio.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:youtube_explode_dart/youtube_explode_dart.dart';
import '../constants.dart';
import '../core/api_service.dart';
import '../core/device_relay_service.dart';
import '../hardware/device_controller.dart';
import 'arc_reactor.dart';

class ChatMessage {
  final String role; // 'user' or 'jarvis'
  String content;
  final Map<String, dynamic>? action;
  final DateTime timestamp;

  ChatMessage({
    required this.role,
    required this.content,
    this.action,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

class HudScreen extends StatefulWidget {
  const HudScreen({super.key});

  @override
  State<HudScreen> createState() => _HudScreenState();
}

class _HudScreenState extends State<HudScreen> {
  final ApiService _api = ApiService();
  final DeviceRelayService _relay = DeviceRelayService();
  
  // Dedicated audio player for Jarvis TTS Voice
  final AudioPlayer _voicePlayer = AudioPlayer();
  // Dedicated background audio player for In-App Music
  final AudioPlayer _musicPlayer = AudioPlayer();

  final stt.SpeechToText _speech = stt.SpeechToText();

  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessage> _messages = [];
  bool _isSpeaking = false;
  bool _isListening = false;
  bool _isProcessing = false;
  bool _speechAvailable = false;
  bool _torchActive = false;
  
  // In-App Music HUD state
  String? _currentSongTitle;
  bool _isMusicPlaying = false;
  String? _lastActionKey;
  DateTime? _lastActionTime;
  bool _handsFree = false;
  Timer? _telemetryTimer;

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    await _api.init();
    _initSpeech();
    _initAudio();
    _loadHistory();
    DeviceController.requestCallPermission();

    // Start background relay for PC remote control
    _restartRelay();
    _startTelemetrySync();

    DeviceController.showNotification(
      title: 'J.A.R.V.I.S. NEURAL CORE v1.1',
      content: 'Sistemas activos • En línea',
      isPlaying: false,
    );
  }

  void _startTelemetrySync() {
    _telemetryTimer?.cancel();
    _telemetryTimer = Timer.periodic(const Duration(seconds: 15), (_) => _syncTelemetry());
    _syncTelemetry();
  }

  Future<void> _syncTelemetry() async {
    try {
      final batt = await DeviceController.getBatteryStatus();
      await _api.sendDeviceTelemetry({
        'battery': batt['level'],
        'charging': batt['isCharging'],
        'torch': _torchActive,
        'music': _currentSongTitle,
        'is_playing': _isMusicPlaying,
      });
    } catch (_) {}
  }

  void _restartRelay() {
    _relay.stopListening();
    _relay.startListening(onAction: _handleRemoteAction);
  }

  void _handleRemoteAction(Map<String, dynamic> action) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: StarkConstants.panelBg,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: StarkConstants.primaryCyan),
          ),
          content: Row(
            children: [
              const Icon(Icons.sync_alt, color: StarkConstants.primaryCyan, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'ORDEN REMOTA DESDE PC: ${action['action']}',
                  style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 11),
                ),
              ),
            ],
          ),
        ),
      );
      setState(() {
        if (action['action'] == 'toggle_flashlight') {
          _torchActive = action['enable'] == true;
        }
      });
      // Execute the action natively inside the phone
      _handleAction(action);
    }
  }

  Future<void> _initSpeech() async {
    try {
      _speechAvailable = await _speech.initialize(
        onError: (err) {
          if (mounted) setState(() => _isListening = false);
          if (_handsFree && mounted) {
            Future.delayed(const Duration(seconds: 1), () {
              if (mounted && _handsFree && !_isSpeaking && !_isProcessing) {
                _startContinuousListening();
              }
            });
          }
        },
        onStatus: (status) {
          if (status == 'done' || status == 'notListening') {
            if (mounted) setState(() => _isListening = false);
            if (_handsFree && mounted) {
              Future.delayed(const Duration(milliseconds: 500), () {
                if (mounted && _handsFree && !_isSpeaking && !_isProcessing) {
                  _startContinuousListening();
                }
              });
            }
          }
        },
      );
      setState(() {});
    } catch (_) {}
  }

  void _toggleHandsFree() {
    setState(() {
      _handsFree = !_handsFree;
    });
    if (_handsFree) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: StarkConstants.panelBg,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: StarkConstants.starkGold),
          ),
          content: Text(
            'AUTO-ESCUCHA ACTIVA: Diga "Hey Jarvis" o "Jarvis" para dar órdenes',
            style: GoogleFonts.shareTechMono(color: StarkConstants.starkGold, fontSize: 11),
          ),
        ),
      );
      _startContinuousListening();
    } else {
      _speech.stop();
      setState(() => _isListening = false);
    }
  }

  void _startContinuousListening() {
    if (!_speechAvailable || !_handsFree || _isSpeaking || _isProcessing) return;
    try {
      _speech.listen(
        listenOptions: stt.SpeechListenOptions(
          cancelOnError: false,
          partialResults: true,
          listenMode: stt.ListenMode.dictation,
        ),
        onResult: (result) {
          final words = result.recognizedWords.trim();
          if (words.isNotEmpty && result.finalResult) {
            final lower = words.toLowerCase();
            if (lower.contains('jarvis') || lower.contains('oye jarvis') || lower.contains('hey jarvis')) {
              final clean = words.replaceAll(RegExp(r'\b(hey|oye|ok)?\s*jarvis\b[,:]?', caseSensitive: false), '').trim();
              if (clean.isNotEmpty) {
                _sendMessage(clean);
              }
            }
          }
        },
      );
      if (mounted) setState(() => _isListening = true);
    } catch (_) {}
  }

  void _initAudio() {
    _voicePlayer.playerStateStream.listen((state) {
      if (mounted) {
        final speaking = state.playing && state.processingState != ProcessingState.completed;
        setState(() {
          _isSpeaking = speaking;
        });
        if (speaking) {
          // Duck music to 15% volume while Jarvis speaks
          _musicPlayer.setVolume(0.15);
        } else {
          // Restore full volume
          _musicPlayer.setVolume(1.0);
          // If a song is loaded, resume playback automatically
          if (_currentSongTitle != null &&
              !_musicPlayer.playing &&
              _musicPlayer.processingState != ProcessingState.idle &&
              _musicPlayer.processingState != ProcessingState.completed) {
            _musicPlayer.play();
          }
          if (_handsFree && mounted) {
            Future.delayed(const Duration(milliseconds: 600), () {
              if (mounted && _handsFree && !_isSpeaking && !_isProcessing) {
                _startContinuousListening();
              }
            });
          }
        }
      }
    });

    _musicPlayer.playerStateStream.listen((state) {
      if (mounted) {
        final playing = state.playing && state.processingState != ProcessingState.completed;
        setState(() {
          _isMusicPlaying = playing;
        });
        if (_currentSongTitle != null) {
          DeviceController.showNotification(
            title: playing ? 'J.A.R.V.I.S. • REPRODUCIENDO' : 'J.A.R.V.I.S. • EN ESPERA',
            content: _currentSongTitle!,
            isPlaying: playing,
          );
        }
        _syncTelemetry();
      }
    });

    _musicPlayer.playbackEventStream.listen(
      (event) {},
      onError: (Object e, StackTrace st) {
        debugPrint('[MusicPlayer] Stream event error: $e');
      },
    );
  }

  Future<void> _loadHistory() async {
    final history = await _api.fetchHistory();
    if (mounted && history.isNotEmpty) {
      setState(() {
        _messages.clear();
        for (final m in history) {
          _messages.add(ChatMessage(
            role: m['role'] == 'jarvis' ? 'jarvis' : 'user',
            content: m['content'] ?? '',
          ));
        }
      });
      _scrollToBottom();
    }
  }

  @override
  void dispose() {
    _telemetryTimer?.cancel();
    DeviceController.cancelNotification();
    _textController.dispose();
    _scrollController.dispose();
    _voicePlayer.dispose();
    _musicPlayer.dispose();
    _speech.stop();
    _relay.stopListening();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOutQuad,
        );
      }
    });
  }

  Future<void> _sendMessage([String? overrideText]) async {
    final text = (overrideText ?? _textController.text).trim();
    if (text.isEmpty || _isProcessing) return;

    _textController.clear();
    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text));
      _isProcessing = true;
    });
    _scrollToBottom();

    final botMessage = ChatMessage(role: 'jarvis', content: '');
    setState(() {
      _messages.add(botMessage);
    });

    try {
      final stream = _api.sendChatMessageStream(
        message: text,
        onAction: (action) {
          _handleAction(action);
        },
        onAudio: (audioUrl) {
          _playAudio(audioUrl);
        },
      );

      await for (final chunk in stream) {
        setState(() {
          botMessage.content += chunk;
        });
        _scrollToBottom();
      }
    } catch (e) {
      setState(() {
        botMessage.content = 'Interferencia en la señal neuronal: $e';
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
      _scrollToBottom();
    }
  }

  Future<void> _playAudio(String url) async {
    try {
      await _voicePlayer.setUrl(url);
      await _voicePlayer.play();
    } catch (e) {
      debugPrint('[VoiceAudio] Play error: $e');
    }
  }

  Future<void> _handleAction(Map<String, dynamic> action) async {
    final type = action['action'] as String?;
    if (type == null) return;

    // Evitar doble ejecución si la orden llegó concurrentemente desde SSE y Relay
    final actionKey = '$type:${action['video_id'] ?? action['target'] ?? action['query'] ?? action['title'] ?? action['hour']}';
    final now = DateTime.now();
    if (_lastActionKey == actionKey && _lastActionTime != null && now.difference(_lastActionTime!).inMilliseconds < 4000) {
      debugPrint('[Action] Ignorando acción duplicada concurrente: $actionKey');
      return;
    }
    _lastActionKey = actionKey;
    _lastActionTime = now;

    switch (type) {
      case 'open_camera':
        await DeviceController.openCamera();
        break;

      case 'pause_music':
        await _musicPlayer.pause();
        break;

      case 'resume_music':
        await _musicPlayer.play();
        break;

      case 'stop_music':
        await _musicPlayer.stop();
        setState(() {
          _isMusicPlaying = false;
          _currentSongTitle = null;
        });
        DeviceController.showNotification(
          title: 'J.A.R.V.I.S. NEURAL CORE',
          content: 'Pista de audio detenida',
          isPlaying: false,
        );
        _syncTelemetry();
        break;

      case 'volume_control':
        final dir = action['direction'] as String? ?? 'up';
        final curr = _musicPlayer.volume;
        final next = dir == 'up' ? (curr + 0.25).clamp(0.0, 1.0) : (curr - 0.25).clamp(0.0, 1.0);
        await _musicPlayer.setVolume(next);
        break;

      case 'toggle_flashlight':
        final enable = action['enable'] == true;
        await DeviceController.toggleFlashlight(enable);
        setState(() => _torchActive = enable);
        _syncTelemetry();
        break;

      case 'set_alarm':
        final hour = (action['hour'] as num?)?.toInt() ?? 7;
        final minute = (action['minute'] as num?)?.toInt() ?? 0;
        final msg = action['message'] as String? ?? 'Alarma';
        await DeviceController.setAlarm(hour: hour, minute: minute, message: msg);
        break;

      case 'set_timer':
        final secs = (action['seconds'] as num?)?.toInt() ?? 300;
        final msg = action['message'] as String? ?? 'Temporizador';
        await DeviceController.setTimer(seconds: secs, message: msg);
        break;

      case 'open_maps':
        final loc = action['location'] as String? ?? '';
        if (loc.isNotEmpty) await DeviceController.openMaps(loc);
        break;

      case 'call':
        final target = action['target'] as String? ?? '';
        if (target.isNotEmpty) await DeviceController.makeCall(target);
        break;

      case 'play_music':
        final videoId = action['video_id'] as String?;
        final title = action['title'] as String? ?? 'Pista de Audio';
        final query = action['query'] as String? ?? title;

        setState(() {
          _currentSongTitle = title;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: StarkConstants.panelBg,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: const BorderSide(color: StarkConstants.primaryCyan),
              ),
              content: Row(
                children: [
                  const Icon(Icons.graphic_eq, color: StarkConstants.primaryCyan, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'SINTONIZANDO EN J.A.R.V.I.S.: $title',
                      style: GoogleFonts.shareTechMono(color: StarkConstants.primaryCyan, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        final yt = YoutubeExplode();
        try {
          String? vid = videoId;
          if (vid == null || vid.isEmpty) {
            final searchResults = await yt.search.search(query);
            if (searchResults.isNotEmpty) {
              vid = searchResults.first.id.value;
            }
          }

          if (vid != null && vid.isNotEmpty) {
            final manifest = await yt.videos.streamsClient.getManifest(vid);
            final audioStreams = manifest.audioOnly;
            
            const streamHeaders = {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
              'Range': 'bytes=0-',
            };

            bool started = false;
            final candidates = <AudioStreamInfo>[
              ...audioStreams.where((s) => s.container.name.toLowerCase() == 'webm'),
              ...audioStreams.where((s) => s.container.name.toLowerCase() == 'mp4' || s.container.name.toLowerCase() == 'm4a'),
              ...audioStreams,
              ...manifest.muxed,
            ];

            for (final streamInfo in candidates) {
              try {
                final directStreamUrl = streamInfo.url.toString();
                await _musicPlayer.stop();
                await _musicPlayer.setUrl(
                  directStreamUrl,
                  headers: streamHeaders,
                );
                await _musicPlayer.setVolume(_isSpeaking ? 0.15 : 1.0);
                await _musicPlayer.play();
                started = true;
                break;
              } catch (candidateErr) {
                debugPrint('[MusicPlayer] Stream (${streamInfo.container.name}) falló: $candidateErr, probando siguiente...');
              }
            }

            if (!started) {
              throw Exception('Ningún canal de audio respondió favorablemente');
            }
          }
        } catch (e) {
          debugPrint('[MusicPlayer] Error extrayendo audio en app: $e');
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                backgroundColor: StarkConstants.panelBg,
                content: Text(
                  'Error al sintonizar audio: $e',
                  style: GoogleFonts.shareTechMono(color: StarkConstants.starkRed, fontSize: 11),
                ),
              ),
            );
          }
        } finally {
          yt.close();
        }
        break;
    }
  }

  void _toggleListening() {
    if (!_speechAvailable) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reconocimiento de voz no disponible en este dispositivo')),
      );
      return;
    }

    if (_isListening) {
      _speech.stop();
      setState(() => _isListening = false);
    } else {
      _speech.listen(
        listenOptions: stt.SpeechListenOptions(
          cancelOnError: true,
          partialResults: false,
        ),
        onResult: (result) {
          if (result.finalResult) {
            setState(() => _isListening = false);
            _sendMessage(result.recognizedWords);
          }
        },
      );
      setState(() => _isListening = true);
      DeviceController.vibrate(50);
    }
  }

  void _openSettingsDialog() {
    final urlCtrl = TextEditingController(text: _api.serverUrl);
    final uidCtrl = TextEditingController(text: _api.userId);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: StarkConstants.panelBg,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: StarkConstants.primaryCyan),
        ),
        title: Text(
          'CONFIGURACIÓN DE ENLACE STARK',
          style: GoogleFonts.orbitron(color: StarkConstants.primaryCyan, fontSize: 13, fontWeight: FontWeight.bold),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('URL del Servidor (Render o Local):', style: GoogleFonts.shareTechMono(color: StarkConstants.textDim, fontSize: 11)),
            const SizedBox(height: 4),
            TextField(
              controller: urlCtrl,
              style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 12),
              decoration: InputDecoration(
                filled: true,
                fillColor: Colors.black26,
                border: OutlineInputBorder(borderSide: const BorderSide(color: StarkConstants.borderCyan)),
                focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: StarkConstants.primaryCyan)),
              ),
            ),
            const SizedBox(height: 12),
            Text('Terminal User ID (Compartido con PC):', style: GoogleFonts.shareTechMono(color: StarkConstants.textDim, fontSize: 11)),
            const SizedBox(height: 4),
            TextField(
              controller: uidCtrl,
              style: GoogleFonts.shareTechMono(color: StarkConstants.starkGold, fontSize: 12),
              decoration: InputDecoration(
                filled: true,
                fillColor: Colors.black26,
                border: OutlineInputBorder(borderSide: const BorderSide(color: StarkConstants.borderCyan)),
                focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: StarkConstants.primaryCyan)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('CANCELAR', style: GoogleFonts.shareTechMono(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: StarkConstants.primaryCyan),
            onPressed: () async {
              await _api.setServerUrl(urlCtrl.text);
              await _api.setUserId(uidCtrl.text);
              _restartRelay();
              if (ctx.mounted) {
                Navigator.pop(ctx);
              }
              if (mounted) {
                setState(() {});
                _loadHistory();
              }
            },
            child: Text('CONECTAR', style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 11)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) {
          DeviceController.minimizeApp();
        }
      },
      child: Scaffold(
        backgroundColor: StarkConstants.bgDark,
        body: SafeArea(
          child: Column(
            children: [
              // TOP STATUS BAR
              _buildTopBar(),

              // ARC REACTOR & TELEMETRY
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: GestureDetector(
                  onTap: _toggleListening,
                  child: ArcReactorWidget(
                    isSpeaking: _isSpeaking || _isMusicPlaying,
                    isListening: _isListening,
                    size: 140,
                  ),
                ),
              ),

              // QUICK HARDWARE BUTTONS
              _buildQuickActionsRow(),

              // STARK HUD IN-APP MUSIC PLAYER BAR
              _buildMusicPlayerBar(),

              const SizedBox(height: 6),

              // CHAT AREA WITH 120FPS SMOOTH SCROLLING
              Expanded(
                child: _buildChatArea(),
              ),

              // INPUT BAR
              _buildInputBar(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: const BoxDecoration(
        color: StarkConstants.panelBg,
        border: Border(bottom: BorderSide(color: StarkConstants.borderCyan)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: StarkConstants.starkGreen,
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: StarkConstants.starkGreen, blurRadius: 6)],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'J.A.R.V.I.S. OS',
                    style: GoogleFonts.orbitron(
                      color: StarkConstants.primaryCyan,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                  Text(
                    'MARK VII • v1.1.0',
                    style: GoogleFonts.shareTechMono(
                      color: StarkConstants.textDim,
                      fontSize: 8,
                      letterSpacing: 0.8,
                    ),
                  ),
                ],
              ),
            ],
          ),
          Row(
            children: [
              // Hands-Free Auto-Listen Badge
              GestureDetector(
                onTap: _toggleHandsFree,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),
                  decoration: BoxDecoration(
                    color: _handsFree
                        ? StarkConstants.starkGold.withValues(alpha: 0.15)
                        : Colors.white.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: _handsFree ? StarkConstants.starkGold : Colors.white24,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _handsFree ? Icons.mic : Icons.mic_off,
                        color: _handsFree ? StarkConstants.starkGold : Colors.white54,
                        size: 11,
                      ),
                      const SizedBox(width: 3),
                      Text(
                        _handsFree ? 'VOZ ON' : 'VOZ OFF',
                        style: GoogleFonts.shareTechMono(
                          color: _handsFree ? StarkConstants.starkGold : Colors.white54,
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 6),
              // PC Sync Relay Badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),
                decoration: BoxDecoration(
                  color: StarkConstants.primaryCyan.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: StarkConstants.primaryCyan.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.sync, color: StarkConstants.primaryCyan, size: 10),
                    const SizedBox(width: 3),
                    Text(
                      'PC RELAY',
                      style: GoogleFonts.shareTechMono(color: StarkConstants.primaryCyan, fontSize: 9, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 4),
              IconButton(
                icon: const Icon(Icons.remove, color: StarkConstants.primaryCyan, size: 20),
                onPressed: () => DeviceController.minimizeApp(),
                tooltip: 'Minimizar en segundo plano',
              ),
              IconButton(
                icon: const Icon(Icons.tune, color: StarkConstants.primaryCyan, size: 18),
                onPressed: _openSettingsDialog,
                tooltip: 'Ajustes de Servidor / Terminal ID',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionsRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _quickBtn(
            icon: _torchActive ? Icons.flashlight_on : Icons.flashlight_off,
            label: _torchActive ? 'Luz ON' : 'Luz OFF',
            color: _torchActive ? StarkConstants.starkGold : StarkConstants.primaryCyan,
            onTap: () async {
              final newState = !_torchActive;
              await DeviceController.toggleFlashlight(newState);
              setState(() => _torchActive = newState);
              _syncTelemetry();
            },
          ),
          _quickBtn(
            icon: Icons.camera_alt,
            label: 'Cámara',
            color: StarkConstants.primaryCyan,
            onTap: () => DeviceController.openCamera(),
          ),
          _quickBtn(
            icon: Icons.alarm,
            label: 'Alarma',
            color: StarkConstants.primaryCyan,
            onTap: () => _sendMessage('Pon una alarma para las 07:00'),
          ),
          _quickBtn(
            icon: Icons.timer,
            label: '5 Min',
            color: StarkConstants.primaryCyan,
            onTap: () => _sendMessage('Pon un temporizador de 5 minutos'),
          ),
          _quickBtn(
            icon: Icons.music_note,
            label: 'Música',
            color: StarkConstants.primaryCyan,
            onTap: () => _sendMessage('Reproduce música de Iron Man'),
          ),
        ],
      ),
    );
  }

  Widget _quickBtn({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: color.withValues(alpha: 0.4)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 14),
            const SizedBox(width: 6),
            Text(label, style: GoogleFonts.shareTechMono(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildMusicPlayerBar() {
    if (_currentSongTitle == null) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: StarkConstants.panelBg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: StarkConstants.primaryCyan.withValues(alpha: 0.6)),
        boxShadow: [
          BoxShadow(
            color: StarkConstants.primaryCyan.withValues(alpha: 0.15),
            blurRadius: 8,
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(
            _isMusicPlaying ? Icons.graphic_eq : Icons.music_note,
            color: StarkConstants.primaryCyan,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _currentSongTitle!,
                  style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  _isMusicPlaying ? 'REPRODUCIENDO EN J.A.R.V.I.S.' : 'PAUSADO',
                  style: GoogleFonts.shareTechMono(color: StarkConstants.primaryCyan, fontSize: 9),
                ),
              ],
            ),
          ),
          const SizedBox(width: 6),
          EqualizerBarsWidget(isPlaying: _isMusicPlaying),
          IconButton(
            icon: Icon(
              _isMusicPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled,
              color: StarkConstants.primaryCyan,
              size: 24,
            ),
            onPressed: () {
              if (_isMusicPlaying) {
                _musicPlayer.pause();
              } else {
                _musicPlayer.play();
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.stop_circle, color: StarkConstants.starkRed, size: 22),
            onPressed: () {
              _musicPlayer.stop();
              setState(() {
                _isMusicPlaying = false;
                _currentSongTitle = null;
              });
            },
          ),
        ],
      ),
    );
  }

  Widget _buildChatArea() {
    if (_messages.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.terminal, color: StarkConstants.primaryCyan.withValues(alpha: 0.3), size: 40),
            const SizedBox(height: 8),
            Text(
              '[ENLACE NEURONAL ESTABLECIDO]\nToque el reactor o el micrófono para ordenar.',
              textAlign: TextAlign.center,
              style: GoogleFonts.shareTechMono(color: StarkConstants.textDim, fontSize: 11),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final msg = _messages[index];
        final isUser = msg.role == 'user';

        return Align(
          alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.84),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isUser
                  ? StarkConstants.primaryCyan.withValues(alpha: 0.15)
                  : StarkConstants.panelBg,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: isUser ? StarkConstants.primaryCyan : StarkConstants.borderCyan,
                width: 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: (isUser ? StarkConstants.primaryCyan : Colors.black).withValues(alpha: 0.1),
                  blurRadius: 8,
                )
              ],
            ),
            child: Text(
              msg.content,
              style: GoogleFonts.shareTechMono(
                color: isUser ? Colors.white : StarkConstants.primaryCyan,
                fontSize: 12.5,
                height: 1.4,
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: const BoxDecoration(
        color: StarkConstants.panelBg,
        border: Border(top: BorderSide(color: StarkConstants.borderCyan)),
      ),
      child: Row(
        children: [
          // Voice Mic Button
          IconButton(
            icon: Icon(
              _isListening ? Icons.mic : Icons.mic_none,
              color: _isListening ? StarkConstants.starkRed : StarkConstants.primaryCyan,
            ),
            onPressed: _toggleListening,
          ),
          const SizedBox(width: 4),
          // Text Input
          Expanded(
            child: TextField(
              controller: _textController,
              style: GoogleFonts.shareTechMono(color: Colors.white, fontSize: 13),
              decoration: InputDecoration(
                hintText: _isListening ? 'Escuchando orden vocal...' : 'Escriba un comando a JARVIS...',
                hintStyle: GoogleFonts.shareTechMono(color: StarkConstants.textDim, fontSize: 12),
                filled: true,
                fillColor: Colors.black38,
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                  borderSide: const BorderSide(color: StarkConstants.borderCyan),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                  borderSide: const BorderSide(color: StarkConstants.primaryCyan),
                ),
              ),
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 8),
          // Send Button
          InkWell(
            onTap: _isProcessing ? null : () => _sendMessage(),
            borderRadius: BorderRadius.circular(20),
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: _isProcessing ? Colors.white12 : StarkConstants.primaryCyan,
                shape: BoxShape.circle,
              ),
              child: _isProcessing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: StarkConstants.primaryCyan),
                    )
                  : const Icon(Icons.send, color: Colors.black, size: 18),
            ),
          ),
        ],
      ),
    );
  }
}

class EqualizerBarsWidget extends StatefulWidget {
  final bool isPlaying;
  const EqualizerBarsWidget({super.key, required this.isPlaying});

  @override
  State<EqualizerBarsWidget> createState() => _EqualizerBarsWidgetState();
}

class _EqualizerBarsWidgetState extends State<EqualizerBarsWidget> with SingleTickerProviderStateMixin {
  late AnimationController _anim;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 650))..repeat(reverse: true);
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isPlaying) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: List.generate(
          5,
          (i) => Container(
            margin: const EdgeInsets.symmetric(horizontal: 1.5),
            width: 3,
            height: 4,
            decoration: BoxDecoration(
              color: StarkConstants.primaryCyan.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(1.5),
            ),
          ),
        ),
      );
    }

    return AnimatedBuilder(
      animation: _anim,
      builder: (context, child) {
        final val = _anim.value;
        final heights = [
          5.0 + 9.0 * math.sin(val * math.pi).abs(),
          14.0 - 7.0 * math.cos(val * math.pi).abs(),
          7.0 + 11.0 * math.sin((val + 0.3) * math.pi).abs(),
          15.0 - 9.0 * math.sin((val + 0.6) * math.pi).abs(),
          6.0 + 8.0 * math.cos((val + 0.2) * math.pi).abs(),
        ];
        return Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: List.generate(
            5,
            (i) => Container(
              margin: const EdgeInsets.symmetric(horizontal: 1.5),
              width: 3,
              height: heights[i].clamp(3.0, 18.0),
              decoration: BoxDecoration(
                color: StarkConstants.primaryCyan,
                borderRadius: BorderRadius.circular(1.5),
                boxShadow: const [
                  BoxShadow(color: StarkConstants.primaryCyan, blurRadius: 4),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
