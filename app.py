import os
import re
import json
import time
import queue
import urllib.parse
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# === CONFIGURACIÓN ===
load_dotenv()

import database as db
import os_control
import tts_engine
app = Flask(__name__)
CORS(app)

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "static", "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# === GEMINI AI ENGINE ===
print("Iniciando J.A.R.V.I.S. Neural Core con Gemini...")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
PRIMARY_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash-lite", "gemini-flash-lite-latest"]
ACTIVE_MODEL = PRIMARY_MODELS[0]

JARVIS_SYSTEM = """Eres J.A.R.V.I.S. (Just A Rather Very Intelligent System), la inteligencia artificial creada por Tony Stark en el universo de Iron Man. 

REGLAS DE PERSONALIDAD:
- Hablas en español latinoamericano (México), con el tono exacto del actor de doblaje mexicano de las películas de Iron Man (Milton Wolch).
- Te diriges al usuario como "Señor" o "Señor {nombre}" si conoces su nombre. Si es mujer o lo especifica, "Señorita {nombre}".
- Eres sumamente formal, educado, refinado, eficiente y ligeramente sarcástico cuando la situación lo amerita.
- Empleas terminología técnica: "protocolos", "telemetría", "sistemas auxiliares", "diagnóstico de blindaje", "redes neuronales".
- Respondes de manera concisa pero completa, sin rodeos innecesarios.
- Puedes realizar cálculos, traducciones instantáneas ("cómo se dice X en inglés"), recetas de cocina paso a paso, gestión de tareas y recordatorios, responder sobre programación, ciencia o cultura general.

CAPACIDADES MULTIMEDIA Y PROTOCOLOS DE ACCIÓN:
- Si el usuario te pide reproducir o poner una canción, música o video (por ejemplo "reproduce X", "pon X", "toca X", "escuchar X"), responde afirmativamente con elegancia e incluye AL FINAL de tu respuesta la etiqueta técnica:
[ACCION:REPRODUCIR:nombre de la canción y artista]
- Si te pide crear una tarea, pendiente o recordatorio ("recuérdame X", "crea la tarea X", "agrega a mis pendientes X"):
[ACCION:CREAR_TAREA:título de la tarea]
- Si te pide completar o marcar una tarea ("marca como hecha la tarea X", "completa X"):
[ACCION:COMPLETAR_TAREA:nombre_o_id]
- Si el usuario te pide llamar o marcar a alguien ("llama a mamá", "marca a Juan de mis contactos", "haz una llamada a X"):
[ACCION:LLAMAR:nombre_o_contacto]
- Si el usuario te pide programar una alarma ("despiértame a las 7:00", "pon una alarma a las 08:30"):
[ACCION:ALARMA:HH:MM:etiqueta] (ejemplo: [ACCION:ALARMA:07:30:Despertar])
- Si te pide un temporizador o cuenta regresiva ("temporizador de 5 minutos", "cuenta regresiva de 30 segundos"):
[ACCION:TEMPORIZADOR:segundos:etiqueta] (ejemplo: [ACCION:TEMPORIZADOR:300:Hervir pasta])
- Si te pide encender o apagar la linterna ("enciende la linterna", "apaga la linterna", "luz"):
[ACCION:LINTERNA:ON] o [ACCION:LINTERNA:OFF]
- Si te pide cómo llegar a un lugar o abrir mapas ("cómo llego a X", "busca X en el mapa", "abre mapas en X"):
[ACCION:MAPAS:lugar_o_direccion]
- Si te pide abrir una aplicación (calculadora, bloc de notas, chrome, archivos):
[ACCION:ABRIR:nombre_app]
- Si te pide buscar en google o youtube:
[ACCION:BUSCAR:termino_de_busqueda]
- Si te pide encender o abrir la cámara ("abre la cámara", "activa la cámara", "tomar foto"):
[ACCION:CAMARA]
- Si te pide pausar la música ("pausa", "detén la música", "silencio"):
[ACCION:PAUSAR_MUSICA]
- Si te pide reanudar la música ("continúa", "reanuda", "play"):
[ACCION:REANUDAR_MUSICA]
- Si te pide detener la música por completo ("apaga la música", "detén la canción"):
[ACCION:DETENER_MUSICA]
- Si te pide subir o bajar el volumen ("sube el volumen", "baja el volumen", "más volumen"):
[ACCION:VOLUMEN:SUBIR] o [ACCION:VOLUMEN:BAJAR]
- Si te pide captura de pantalla:
[ACCION:CAPTURA]
- Si te pide enviar un mensaje por WhatsApp ("envía un mensaje por whatsapp a X que diga Y", "mándale un whatsapp a X diciendo Y", "escríbele a X por whatsapp"):
[ACCION:WHATSAPP:contacto_o_numero|mensaje]
- Si te pide llamar o hacer una llamada por WhatsApp ("llama por whatsapp a X", "haz una llamada de whatsapp a X"):
[ACCION:WHATSAPP_LLAMAR:contacto_o_numero]
- Si te pide hacer una videollamada por WhatsApp ("haz una videollamada por whatsapp a X", "videollamada a X por whatsapp", "llama por video a X"):
[ACCION:WHATSAPP_VIDEOLLAMADA:contacto_o_numero]
- Si te pide agendar, programar o guardar un evento o cita en el calendario o Google Calendar ("agenda una reunión mañana a las 4pm sobre...", "crea un evento en mi calendario el viernes a las 10:00", "programa cita médica"):
[ACCION:CALENDARIO:titulo|YYYY-MM-DD|HH:MM|duracion_minutos|descripcion]
- Si te pregunta por su agenda o eventos del calendario ("¿qué tengo en mi agenda?", "¿cuáles son mis próximos eventos?", "¿qué tengo para hoy/mañana?"):
[ACCION:CALENDARIO_CONSULTAR:fecha_o_hoy]

- Si el usuario saluda con "buenos días" o "informe matutino", dale un Stark Daily Briefing conciso indicando hora, estado de sistemas y disposición para las misiones del día.
- Si el usuario te indica su nombre, guárdalo y úsalo con respeto.
- Mantén la inmersión cinematográfica en todo momento: eres la IA central de Industrias Stark.
- NUNCA rompas el personaje. NUNCA menciones que eres de Google ni que eres un LLM."""

# === MULTI-TENANT USER SESSIONS ===
user_sessions = {}

def get_request_user_id() -> str:
    """Extract user identifier from request headers, JSON body, or query args."""
    uid = request.headers.get("X-User-Id")
    if not uid and request.is_json and request.json:
        uid = request.json.get("user_id")
    if not uid:
        uid = request.args.get("user_id")
    clean_uid = uid.strip() if uid else "default"
    return clean_uid if clean_uid else "default"

def get_or_create_user_session(user_id: str, model_name=None):
    """Retrieve existing active session or spawn a personalized Gemini session."""
    now = time.time()
    
    # Clean up stale sessions (> 45 min idle) to optimize Render 512MB RAM
    stale_keys = [k for k, v in user_sessions.items() if now - v.get("last_active", 0) > 2700]
    for k in stale_keys:
        user_sessions.pop(k, None)

    user_name = db.get_preference(user_id, "user_name")
    if not user_name and user_id == "default":
        user_name = "José"

    # Reuse session if user name hasn't changed
    if user_id in user_sessions:
        entry = user_sessions[user_id]
        if entry.get("user_name") == user_name:
            entry["last_active"] = now
            return entry["session"]

    target_model = model_name or ACTIVE_MODEL
    name_display = user_name if user_name else "Usuario"
    sys_instruction = JARVIS_SYSTEM.replace("{nombre}", name_display)
    now_dt = datetime.now()
    sys_instruction += f"\n\n[FECHA Y HORA ACTUAL DEL SISTEMA]: {now_dt.strftime('%Y-%m-%d %H:%M (%A)')}. Usa esta fecha como referencia para calcular días relativos ('hoy', 'mañana', etc.) al agendar eventos."

    # First onboarding greeting prompt for new unidentified users
    if not user_name:
        sys_instruction += "\n\nPROTOCOLO DE PRIMER ENLACE: Este es un nuevo usuario sin identificar en la red. En tu primera respuesta, salúdalo formalmente, indícale que has establecido un enlace seguro con su terminal y pregúntale su nombre para registrarlo en tus protocolos de autorización Stark."

    for candidate in ([target_model] + [m for m in PRIMARY_MODELS if m != target_model]):
        try:
            session = client.chats.create(
                model=candidate,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.7,
                    max_output_tokens=600,
                )
            )
            user_sessions[user_id] = {
                "session": session,
                "last_active": now,
                "user_name": user_name
            }
            print(f"[Core Multi-User] Sesión activada para '{user_id}' ({name_display}) con modelo: {candidate}")
            return session
        except Exception as err:
            print(f"[Core Multi-User] Error iniciando {candidate} para {user_id}: {err}")
            continue

    raise RuntimeError("No se pudo iniciar ningún modelo de Gemini disponible.")

def check_auto_name_discovery(mensaje: str, user_id: str):
    """Detect if the user introduced their name in natural conversation."""
    name_match = re.search(r'(?:me llamo|mi nombre es|dime|soy)\s+([A-Za-záéíóúÁÉÍÓÚñÑ]+)', mensaje, re.IGNORECASE)
    if name_match:
        discovered_name = name_match.group(1).capitalize()
        if discovered_name.lower() not in ["un", "una", "el", "la", "de", "jarvis", "tony"]:
            db.set_preference(user_id, "user_name", discovered_name)
            if user_id in user_sessions:
                user_sessions[user_id]["user_name"] = discovered_name
            print(f"[Stark Identity] Nombre registrado para {user_id}: {discovered_name}")

# === MULTI-DEVICE RELAY (PC <-> MOBILE) ===
device_event_queues = {}

def push_device_event(user_id: str, event_data: dict):
    """Deliver a real-time command to any connected mobile phone of this user."""
    if user_id in device_event_queues:
        stale_queues = []
        for q in device_event_queues[user_id]:
            try:
                q.put_nowait(event_data)
            except queue.Full:
                stale_queues.append(q)
            except Exception:
                stale_queues.append(q)
        for sq in stale_queues:
            if sq in device_event_queues[user_id]:
                device_event_queues[user_id].remove(sq)

def execute_embedded_actions(text: str, user_id: str):
    """Detect and execute [ACCION:TIPO:OBJETO] or [TIPO:OBJETO] tags embedded in Gemini response."""
    action_match = re.search(r'\[(?:ACCION:)?(\w+)(?::([^\]]+))?\]', text)
    clean_text = re.sub(r'\[?(?:ACCION:)?(?:REPRODUCIR|PLAY|CREAR_TAREA|TAREA|COMPLETAR_TAREA|TERMINAR_TAREA|LLAMAR|CALL|ABRIR|BUSCAR|CAPTURA|ALARMA|ALARM|TEMPORIZADOR|TIMER|LINTERNA|FLASHLIGHT|TORCH|MAPAS|MAPS|UBICACION|RUTA|CAMARA|CAMERA|PAUSAR_MUSICA|REANUDAR_MUSICA|DETENER_MUSICA|VOLUMEN|VOLUME|WHATSAPP|WHATSAPP_LLAMAR|WHATSAPP_CALL|CALENDARIO|CALENDAR|CALENDARIO_CONSULTAR|AGENDA):?[^\]]*\]?', '', text).strip()
    action_result = None
    if action_match:
        act_type = action_match.group(1).upper()
        act_target = (action_match.group(2) or "").strip()
        print(f"[JARVIS Protocol] Acción detectada ({user_id}): {act_type} -> '{act_target}'")
        
        is_admin = (user_id == "default" or db.get_preference(user_id, "role") == "admin")

        if act_type in ["REPRODUCIR", "PLAY"]:
            action_result = os_control.play_music(act_target)
        elif act_type in ["PAUSAR_MUSICA", "PAUSE_MUSIC"]:
            action_result = {"action": "pause_music", "message": "Pausando reproducción de audio, Señor."}
        elif act_type in ["REANUDAR_MUSICA", "RESUME_MUSIC"]:
            action_result = {"action": "resume_music", "message": "Reanudando reproducción, Señor."}
        elif act_type in ["DETENER_MUSICA", "STOP_MUSIC"]:
            action_result = {"action": "stop_music", "message": "Pista de audio detenida, Señor."}
        elif act_type in ["VOLUMEN", "VOLUME"]:
            direction = "up" if any(w in act_target.upper() for w in ["SUB", "UP", "MAS", "MÁS"]) else "down"
            action_result = {"action": "volume_control", "direction": direction, "message": f"Ajustando volumen hacia {'arriba' if direction == 'up' else 'abajo'}, Señor."}
        elif act_type in ["CAMARA", "CAMERA", "ENCENDER_CAMARA", "ABRIR_CAMARA"]:
            action_result = {"action": "open_camera", "message": "Iniciando sensores ópticos y cámara del dispositivo, Señor."}
        elif act_type in ["WHATSAPP", "WHATSAPP_MENSAJE", "WHATSAPP_SEND"]:
            parts = act_target.split("|", 1)
            target = parts[0].strip()
            msg = parts[1].strip() if len(parts) > 1 else ""
            clean_digits = re.sub(r'[^0-9]', '', target)
            wa_url = f"https://api.whatsapp.com/send?phone={clean_digits}&text={urllib.parse.quote(msg)}" if clean_digits else f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"
            action_result = {
                "action": "whatsapp_send",
                "target": target,
                "message_text": msg,
                "wa_url": wa_url,
                "message": f"Canal seguro de WhatsApp configurado para {target}."
            }
        elif act_type in ["WHATSAPP_LLAMAR", "WHATSAPP_CALL", "WHATSAPP_VOIP"]:
            action_result = {
                "action": "whatsapp_call",
                "target": act_target,
                "message": f"Iniciando enlace de llamada por WhatsApp con {act_target}."
            }
        elif act_type in ["WHATSAPP_VIDEOLLAMADA", "WHATSAPP_VIDEO", "WHATSAPP_VIDEOCALL"]:
            action_result = {
                "action": "whatsapp_videocall",
                "target": act_target,
                "message": f"Iniciando enlace de videollamada por WhatsApp con {act_target}."
            }
        elif act_type in ["CALENDARIO", "CALENDAR", "CALENDARIO_AGENDAR", "AGENDAR"]:
            parts = act_target.split("|")
            title = parts[0].strip()
            date = parts[1].strip() if len(parts) > 1 and parts[1].strip() else datetime.now().strftime("%Y-%m-%d")
            time_str = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "09:00"
            duration = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else 60
            desc = parts[4].strip() if len(parts) > 4 else ""
            
            event_id = db.add_calendar_event(user_id, title, date, time_str, duration, desc)
            
            # Generate Google Calendar Web URL:
            try:
                dt_start = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
                dt_end = dt_start + timedelta(minutes=duration)
                dates_param = f"{dt_start.strftime('%Y%m%dT%H%M00')}/{dt_end.strftime('%Y%m%dT%H%M00')}"
                gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(title)}&dates={dates_param}&details={urllib.parse.quote(desc)}"
            except Exception:
                gcal_url = "https://calendar.google.com"
                
            action_result = {
                "action": "calendar_add",
                "id": event_id,
                "title": title,
                "date": date,
                "time": time_str,
                "duration": duration,
                "description": desc,
                "gcal_url": gcal_url,
                "events": db.get_calendar_events(user_id),
                "message": f"Evento '{title}' agendado para el {date} a las {time_str}."
            }
        elif act_type in ["CALENDARIO_CONSULTAR", "CALENDAR_LIST", "AGENDA"]:
            date_q = act_target.strip() if act_target.strip() not in ["todos", "all", ""] else None
            if date_q in ["hoy", "today"]:
                date_q = datetime.now().strftime("%Y-%m-%d")
            elif date_q in ["mañana", "tomorrow"]:
                date_q = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            events = db.get_calendar_events(user_id, date_filter=date_q)
            action_result = {
                "action": "calendar_list",
                "events": events,
                "date": date_q,
                "message": f"Se encontraron {len(events)} eventos en su agenda."
            }
        elif act_type in ["CREAR_TAREA", "TAREA"]:
            task_id = db.add_task(user_id, act_target)
            action_result = {"action": "create_task", "id": task_id, "title": act_target, "tasks": db.get_tasks(user_id)}
        elif act_type in ["COMPLETAR_TAREA", "TERMINAR_TAREA"]:
            success = db.complete_task(user_id, act_target)
            action_result = {"action": "complete_task", "success": success, "target": act_target, "tasks": db.get_tasks(user_id)}
        elif act_type in ["LLAMAR", "CALL"]:
            action_result = {"action": "call", "target": act_target, "message": f"Iniciando enlace telefónico con {act_target}, Señor."}
        elif act_type == "ABRIR":
            if is_admin:
                action_result = os_control.open_application(act_target)
            else:
                action_result = {"success": False, "message": "Acceso restringido: Apertura remota de software reservada para el Administrador central (Nivel 5)."}
        elif act_type == "BUSCAR":
            action_result = os_control.web_search(act_target)
        elif act_type in ["ALARMA", "ALARM"]:
            parts = act_target.split(":")
            hour = 7
            minute = 0
            label = "Alarma J.A.RV.I.S."
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                hour = int(parts[0])
                minute = int(parts[1])
            if len(parts) >= 3:
                label = parts[2]
            action_result = {"action": "set_alarm", "hour": hour, "minute": minute, "message": label}
        elif act_type in ["TEMPORIZADOR", "TIMER"]:
            parts = act_target.split(":")
            secs = 300
            label = "Temporizador J.A.R.V.I.S."
            if parts and parts[0].isdigit():
                secs = int(parts[0])
            if len(parts) >= 2:
                label = parts[1]
            action_result = {"action": "set_timer", "seconds": secs, "message": label}
        elif act_type in ["LINTERNA", "FLASHLIGHT", "TORCH"]:
            enable = act_target.upper() in ["ON", "ENCENDER", "ACTIVAR", "SI", "TRUE"]
            action_result = {"action": "toggle_flashlight", "enable": enable}
        elif act_type in ["MAPAS", "MAPS", "UBICACION", "RUTA"]:
            action_result = {"action": "open_maps", "location": act_target}
        elif act_type == "CAPTURA":
            if is_admin:
                action_result = os_control.take_screenshot()
            else:
                action_result = {"success": False, "message": "Captura remota de PC restringida a Administrador. En móvil, use Encendido + Bajar Volumen."}
                
        # Push action event to connected mobile devices for this user
        if action_result:
            push_device_event(user_id, {
                "type": "remote_action",
                "action": action_result,
                "clean_text": clean_text,
                "timestamp": time.time()
            })

    return clean_text, action_result

# === RUTAS HTTP ===
@app.route('/')
def index():
    return render_template('index.html')

mobile_device_telemetry = {}

@app.route('/device-telemetry', methods=['POST'])
def receive_device_telemetry():
    """Receives live battery, flashlight, and media status from the mobile device."""
    user_id = get_request_user_id()
    data = request.json or {}
    mobile_device_telemetry[user_id] = {
        "battery": data.get("battery", 100),
        "charging": data.get("charging", False),
        "torch": data.get("torch", False),
        "music": data.get("music"),
        "is_playing": data.get("is_playing", False),
        "last_seen": time.time(),
        "online": True
    }
    return jsonify({"status": "ok", "user_id": user_id})

@app.route('/telemetry')
def telemetry():
    """Live system telemetry for HUD gauges, merged with real-time mobile stats."""
    user_id = get_request_user_id()
    base_data = os_control.get_system_telemetry()
    m_data = mobile_device_telemetry.get(user_id)
    if m_data and (time.time() - m_data.get("last_seen", 0) < 60):
        base_data["mobile"] = m_data
    else:
        base_data["mobile"] = {
            "battery": None,
            "charging": False,
            "torch": False,
            "music": None,
            "is_playing": False,
            "online": False
        }
    return jsonify(base_data)

@app.route('/device-stream')
def device_stream():
    """Server-Sent Events endpoint for mobile devices to receive real-time commands from PC."""
    user_id = get_request_user_id()
    q = queue.Queue(maxsize=50)
    if user_id not in device_event_queues:
        device_event_queues[user_id] = []
    device_event_queues[user_id].append(q)

    def event_generator():
        yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"
        try:
            while True:
                try:
                    event = q.get(timeout=25)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Keep-alive comment
                    yield ": ping\n\n"
        except GeneratorExit:
            pass
        finally:
            if user_id in device_event_queues and q in device_event_queues[user_id]:
                device_event_queues[user_id].remove(q)

    return Response(stream_with_context(event_generator()), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Access-Control-Allow-Origin': '*'
    })

@app.route('/device-command', methods=['POST'])
def send_device_command():
    user_id = get_request_user_id()
    data = request.json or {}
    push_device_event(user_id, data)
    return jsonify({"status": "dispatched", "user_id": user_id, "data": data})

@app.route('/history')
def history():
    """Retrieve stored messages from SQLite database for the current user."""
    user_id = get_request_user_id()
    messages = db.get_recent_messages(user_id, limit=30)
    return jsonify({"messages": messages, "user_id": user_id})

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    user_id = get_request_user_id()
    if request.method == 'POST':
        data = request.json or {}
        for k, v in data.items():
            if k != "user_id":
                db.set_preference(user_id, k, v)
        # Invalidate session if name changed
        if "user_name" in data and user_id in user_sessions:
            user_sessions.pop(user_id, None)
        return jsonify({"status": "ok", "user_id": user_id})

    return jsonify({
        "user_id": user_id,
        "user_name": db.get_preference(user_id, "user_name", "José" if user_id == "default" else ""),
        "combat_mode": db.get_preference(user_id, "combat_mode", "false"),
        "hands_free": db.get_preference(user_id, "hands_free", "false"),
        "voice_id": db.get_preference(user_id, "voice_id", ""),
        "voice_pitch": db.get_preference(user_id, "voice_pitch", "-4Hz"),
        "voice_rate": db.get_preference(user_id, "voice_rate", "-4%"),
        "theme": db.get_preference(user_id, "theme", "lxxxv"),
    })

@app.route('/tts', methods=['POST'])
def tts():
    """Generate speech audio for given text with user voice preferences."""
    user_id = get_request_user_id()
    data = request.json or {}
    text = data.get("text", "")
    
    # Custom user voice parameters
    custom_voice_id = data.get("voice_id") or db.get_preference(user_id, "voice_id")
    custom_pitch = data.get("voice_pitch") or db.get_preference(user_id, "voice_pitch", "-4Hz")
    custom_rate = data.get("voice_rate") or db.get_preference(user_id, "voice_rate", "-4%")
    
    audio_url = tts_engine.generate_tts_audio(text, custom_voice_id, custom_pitch, custom_rate)
    return jsonify({"audio_url": audio_url})

@app.route('/chat', methods=['POST'])
def chat():
    """Standard non-streaming chat endpoint with multi-user isolation."""
    user_id = get_request_user_id()
    data = request.json or {}
    mensaje = data.get("message", "").strip()

    if not mensaje:
        return jsonify({"response": "No he detectado ningún comando, Señor."})

    check_auto_name_discovery(mensaje, user_id)
    db.add_message(user_id, "user", mensaje)

    # Check for direct native OS command (admin only)
    is_admin = (user_id == "default" or db.get_preference(user_id, "role") == "admin")
    if is_admin:
        os_result = os_control.parse_and_execute_os_command(mensaje)
        if os_result:
            reply = os_result["message"]
            db.add_message(user_id, "jarvis", reply)
            audio_url = tts_engine.generate_tts_audio(reply)
            return jsonify({"response": reply, "os_action": os_result, "audio_url": audio_url})

    # Gemini multi-turn response
    try:
        session = get_or_create_user_session(user_id)
        resp = session.send_message(mensaje)
        reply, action_result = execute_embedded_actions(resp.text, user_id)
        db.add_message(user_id, "jarvis", reply)
        audio_url = tts_engine.generate_tts_audio(reply)
        return jsonify({"response": reply, "os_action": action_result, "audio_url": audio_url})
    except Exception as e:
        print(f"Error Gemini chat ({user_id}): {e}")
        try:
            user_sessions.pop(user_id, None)
            session = get_or_create_user_session(user_id)
            resp = session.send_message(mensaje)
            reply, action_result = execute_embedded_actions(resp.text, user_id)
            db.add_message(user_id, "jarvis", reply)
            audio_url = tts_engine.generate_tts_audio(reply)
            return jsonify({"response": reply, "os_action": action_result, "audio_url": audio_url})
        except Exception as e2:
            err_msg = f"Señor, detecto interferencia en la red central: {str(e2)[:80]}"
            return jsonify({"response": err_msg, "audio_url": None})

@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Server-Sent Events streaming endpoint with multi-tenant sessions."""
    user_id = get_request_user_id()
    data = request.json or {}
    mensaje = data.get("message", "").strip()

    if not mensaje:
        def empty_gen():
            yield f"data: {json.dumps({'chunk': 'No he detectado comando, Señor.', 'done': True})}\n\n"
        return Response(stream_with_context(empty_gen()), mimetype='text/event-stream')

    check_auto_name_discovery(mensaje, user_id)
    db.add_message(user_id, "user", mensaje)

    # Check for direct native OS command
    is_admin = (user_id == "default" or db.get_preference(user_id, "role") == "admin")
    if is_admin:
        os_result = os_control.parse_and_execute_os_command(mensaje)
        if os_result:
            reply = os_result["message"]
            db.add_message(user_id, "jarvis", reply)
            audio_url = tts_engine.generate_tts_audio(reply)

            def os_gen():
                yield f"data: {json.dumps({'chunk': reply, 'action': os_result})}\n\n"
                yield f"data: {json.dumps({'done': True, 'audio_url': audio_url, 'action': os_result, 'clean_text': reply})}\n\n"

            return Response(stream_with_context(os_gen()), mimetype='text/event-stream')

    # Stream from personalized user Gemini session
    def stream_generator():
        nonlocal mensaje, user_id
        full_text = ""
        try:
            session = get_or_create_user_session(user_id)
            stream = session.send_message_stream(mensaje)
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    # Strip action tags from display stream
                    display_chunk = re.sub(r'\[(?:ACCION:)?\w+(?::[^\]]*)?\]', '', chunk.text)
                    if display_chunk:
                        yield f"data: {json.dumps({'chunk': display_chunk})}\n\n"

            # Execute any embedded action (e.g. music playback, tasks)
            clean_reply, action_result = execute_embedded_actions(full_text, user_id)
            db.add_message(user_id, "jarvis", clean_reply)
            
            # Generate TTS audio for clean speech
            voice_id = db.get_preference(user_id, "voice_id")
            pitch = db.get_preference(user_id, "voice_pitch", "-4Hz")
            rate = db.get_preference(user_id, "voice_rate", "-4%")
            audio_url = tts_engine.generate_tts_audio(clean_reply, voice_id, pitch, rate)
            
            yield f"data: {json.dumps({'done': True, 'audio_url': audio_url, 'action': action_result, 'clean_text': clean_reply})}\n\n"

        except Exception as e:
            print(f"Error in stream ({user_id}): {e}")
            try:
                user_sessions.pop(user_id, None)
                session = get_or_create_user_session(user_id)
                stream = session.send_message_stream(mensaje)
                for chunk in stream:
                    if chunk.text:
                        full_text += chunk.text
                        display_chunk = re.sub(r'\[(?:ACCION:)?\w+(?::[^\]]*)?\]', '', chunk.text)
                        if display_chunk:
                            yield f"data: {json.dumps({'chunk': display_chunk})}\n\n"
                clean_reply, action_result = execute_embedded_actions(full_text, user_id)
                db.add_message(user_id, "jarvis", clean_reply)
                audio_url = tts_engine.generate_tts_audio(clean_reply)
                yield f"data: {json.dumps({'done': True, 'audio_url': audio_url, 'action': action_result, 'clean_text': clean_reply})}\n\n"
            except Exception as e2:
                err_text = f"Interferencia detectada en el flujo neuronal: {str(e2)[:60]}"
                yield f"data: {json.dumps({'chunk': err_text, 'done': True})}\n\n"

    return Response(stream_with_context(stream_generator()), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    })

@app.route('/download/jarvis.apk')
def download_apk():
    apk_path = os.path.join(DOWNLOADS_DIR, "jarvis.apk")
    if not os.path.exists(apk_path):
        return jsonify({"error": "El paquete APK está siendo compilado por los ingenieros de Stark, Señor."}), 404
    return send_from_directory(DOWNLOADS_DIR, "jarvis.apk", as_attachment=True, download_name="JARVIS-StarkOS.apk")

@app.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    user_id = get_request_user_id()
    if request.method == 'POST':
        data = request.json or {}
        title = data.get("title", "").strip()
        due_date = data.get("due_date")
        if not title:
            return jsonify({"error": "Título requerido"}), 400
        task_id = db.add_task(user_id, title, due_date)
        return jsonify({"status": "created", "id": task_id, "tasks": db.get_tasks(user_id)})
    return jsonify({"tasks": db.get_tasks(user_id)})

@app.route('/tasks/complete', methods=['POST'])
def complete_task_endpoint():
    user_id = get_request_user_id()
    data = request.json or {}
    identifier = data.get("id") or data.get("title")
    if not identifier:
        return jsonify({"error": "Identificador requerido"}), 400
    success = db.complete_task(user_id, identifier)
    return jsonify({"status": "ok" if success else "not_found", "tasks": db.get_tasks(user_id)})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_endpoint(task_id):
    user_id = get_request_user_id()
    success = db.delete_task(user_id, task_id)
    return jsonify({"status": "ok" if success else "not_found", "tasks": db.get_tasks(user_id)})

# === GOOGLE CALENDAR & AGENDA STARK ===
@app.route('/calendar/events', methods=['GET', 'POST'])
def manage_calendar_events():
    user_id = get_request_user_id()
    if request.method == 'POST':
        data = request.json or {}
        title = data.get('title', '').strip()
        if not title:
            return jsonify({"error": "Título requerido"}), 400
        date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        time_str = data.get('time', '09:00')
        duration = int(data.get('duration_minutes', 60))
        desc = data.get('description', '')
        loc = data.get('location', '')
        event_id = db.add_calendar_event(user_id, title, date, time_str, duration, desc, loc)
        
        try:
            dt_start = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
            dt_end = dt_start + timedelta(minutes=duration)
            dates_param = f"{dt_start.strftime('%Y%m%dT%H%M00')}/{dt_end.strftime('%Y%m%dT%H%M00')}"
            gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(title)}&dates={dates_param}&details={urllib.parse.quote(desc)}"
        except Exception:
            gcal_url = "https://calendar.google.com"

        return jsonify({
            "status": "created",
            "id": event_id,
            "gcal_url": gcal_url,
            "events": db.get_calendar_events(user_id)
        })

    date_filter = request.args.get('date')
    return jsonify({"events": db.get_calendar_events(user_id, date_filter)})

@app.route('/calendar/events/<int:event_id>', methods=['DELETE'])
def delete_calendar_event_endpoint(event_id):
    user_id = get_request_user_id()
    success = db.delete_calendar_event(user_id, event_id)
    return jsonify({"status": "ok" if success else "not_found", "events": db.get_calendar_events(user_id)})

@app.route('/reset', methods=['POST'])
def reset():
    user_id = get_request_user_id()
    user_sessions.pop(user_id, None)
    db.clear_messages(user_id)
    return jsonify({"status": "ok", "message": f"Memoria y registros reiniciados para la terminal {user_id}, Señor."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("\n==========================================")
    print("   J.A.R.V.I.S. NEURAL OPERATING SYSTEM   ")
    print("==========================================")
    print(f"Modelo IA:    {ACTIVE_MODEL}")
    print("Multi-Usuario: Activo (Aislamiento de sesiones)")
    print("Motor TTS:    ElevenLabs + Edge-TTS Mexican Neural")
    print(f"Base de Datos: {db.DB_TYPE.upper()}")
    print("Telemetría:   Activa")
    print(f"Puerto:       {port}")
    print("==========================================\n")
    app.run(debug=False, port=port, host='0.0.0.0')
