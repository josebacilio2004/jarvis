import os
import re
import json
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

import database as db
import os_control
import tts_engine

# === CONFIGURACIÓN ===
load_dotenv()
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
- Hablas en español latinoamericano (México), con el tono exacto del actor de doblaje mexicano de las películas de Iron Man.
- Te diriges al usuario como "Señor" o "Señor {nombre}" si conoces su nombre.
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
- Si te pide abrir una aplicación (calculadora, bloc de notas, chrome, archivos):
[ACCION:ABRIR:nombre_app]
- Si te pide buscar en google o youtube:
[ACCION:BUSCAR:termino_de_busqueda]
- Si te pide captura de pantalla:
[ACCION:CAPTURA]

- Si el usuario saluda con "buenos días" o "informe matutino", dale un Stark Daily Briefing conciso indicando hora, estado de sistemas y disposición para las misiones del día.
- Si el usuario te indica su nombre, guárdalo y úsalo con respeto.
- Mantén la inmersión cinematográfica en todo momento: eres la IA central de Industrias Stark.
- NUNCA rompas el personaje. NUNCA menciones que eres de Google ni que eres un LLM."""

def execute_embedded_actions(text: str):
    """Detect and execute [ACCION:TIPO:OBJETO] tags embedded in Gemini response."""
    action_match = re.search(r'\[ACCION:(\w+)(?::([^\]]+))?\]', text)
    clean_text = re.sub(r'\[ACCION:.*?\]', '', text).strip()
    action_result = None
    if action_match:
        act_type = action_match.group(1).upper()
        act_target = (action_match.group(2) or "").strip()
        print(f"[JARVIS Protocol] Acción detectada: {act_type} -> '{act_target}'")
        if act_type == "REPRODUCIR":
            action_result = os_control.play_music(act_target)
        elif act_type == "CREAR_TAREA":
            task_id = db.add_task(act_target)
            action_result = {"action": "create_task", "id": task_id, "title": act_target, "tasks": db.get_tasks()}
        elif act_type == "COMPLETAR_TAREA":
            success = db.complete_task(act_target)
            action_result = {"action": "complete_task", "success": success, "target": act_target, "tasks": db.get_tasks()}
        elif act_type == "LLAMAR":
            action_result = {"action": "call", "target": act_target, "message": f"Iniciando enlace telefónico con {act_target}, Señor."}
        elif act_type == "ABRIR":
            action_result = os_control.open_application(act_target)
        elif act_type == "BUSCAR":
            action_result = os_control.web_search(act_target)
        elif act_type == "CAPTURA":
            action_result = os_control.take_screenshot()
    return clean_text, action_result

def create_chat_session(model_name=None):
    global ACTIVE_MODEL
    target_model = model_name or ACTIVE_MODEL
    user_name = db.get_preference("user_name", "José")
    sys_instruction = JARVIS_SYSTEM.replace("{nombre}", user_name)
    
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
            ACTIVE_MODEL = candidate
            print(f"[Core] Sesión activa con modelo: {candidate}")
            return session
        except Exception as err:
            print(f"[Core] Error iniciando {candidate}: {err}")
            continue
            
    raise RuntimeError("No se pudo iniciar ningún modelo de Gemini disponible.")

chat_session = create_chat_session()
print(f"J.A.R.V.I.S. Online con modelo: {ACTIVE_MODEL}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/telemetry')
def telemetry():
    """Live system telemetry for HUD gauges."""
    return jsonify(os_control.get_system_telemetry())

@app.route('/history')
def history():
    """Retrieve stored messages from SQLite database."""
    messages = db.get_recent_messages(limit=30)
    return jsonify({"messages": messages})

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if request.method == 'POST':
        data = request.json or {}
        for k, v in data.items():
            db.set_preference(k, v)
        return jsonify({"status": "ok"})
    return jsonify({
        "user_name": db.get_preference("user_name", "José"),
        "combat_mode": db.get_preference("combat_mode", "false"),
        "hands_free": db.get_preference("hands_free", "false"),
    })

@app.route('/tts', methods=['POST'])
def tts():
    """Generate or retrieve speech audio for given text."""
    data = request.json or {}
    text = data.get("text", "")
    audio_url = tts_engine.generate_tts_audio(text)
    return jsonify({"audio_url": audio_url})

@app.route('/chat', methods=['POST'])
def chat():
    """Standard non-streaming chat endpoint."""
    global chat_session
    data = request.json or {}
    mensaje = data.get("message", "").strip()

    if not mensaje:
        return jsonify({"response": "No he detectado ningún comando, Señor."})

    # 1. Save user message to database
    db.add_message("user", mensaje)

    # 2. Check for native OS command
    os_result = os_control.parse_and_execute_os_command(mensaje)
    if os_result:
        reply = os_result["message"]
        db.add_message("jarvis", reply)
        audio_url = tts_engine.generate_tts_audio(reply)
        return jsonify({
            "response": reply,
            "os_action": os_result,
            "audio_url": audio_url
        })

    # 3. Gemini multi-turn response
    try:
        resp = chat_session.send_message(mensaje)
        reply, action_result = execute_embedded_actions(resp.text)
        db.add_message("jarvis", reply)
        audio_url = tts_engine.generate_tts_audio(reply)
        return jsonify({
            "response": reply,
            "os_action": action_result,
            "audio_url": audio_url
        })
    except Exception as e:
        print(f"Error Gemini chat: {e}")
        try:
            chat_session = create_chat_session()
            resp = chat_session.send_message(mensaje)
            reply, action_result = execute_embedded_actions(resp.text)
            db.add_message("jarvis", reply)
            audio_url = tts_engine.generate_tts_audio(reply)
            return jsonify({
                "response": reply,
                "os_action": action_result,
                "audio_url": audio_url
            })
        except Exception as e2:
            err_msg = f"Señor, detecto interferencia en la red central: {str(e2)[:80]}"
            return jsonify({"response": err_msg, "audio_url": None})

@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Server-Sent Events streaming endpoint for real-time typewriter effect."""
    global chat_session
    data = request.json or {}
    mensaje = data.get("message", "").strip()

    if not mensaje:
        def empty_gen():
            yield f"data: {json.dumps({'chunk': 'No he detectado comando, Señor.', 'done': True})}\n\n"
        return Response(stream_with_context(empty_gen()), mimetype='text/event-stream')

    # Save user message to database
    db.add_message("user", mensaje)

    # Check for direct OS action
    os_result = os_control.parse_and_execute_os_command(mensaje)
    if os_result:
        reply = os_result["message"]
        db.add_message("jarvis", reply)
        audio_url = tts_engine.generate_tts_audio(reply)

        def os_gen():
            yield f"data: {json.dumps({'chunk': reply, 'action': os_result})}\n\n"
            yield f"data: {json.dumps({'done': True, 'audio_url': audio_url, 'action': os_result})}\n\n"

        return Response(stream_with_context(os_gen()), mimetype='text/event-stream')

    # Stream from Gemini
    def stream_generator():
        nonlocal mensaje
        global chat_session
        full_text = ""
        try:
            stream = chat_session.send_message_stream(mensaje)
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    # Strip action tags from display stream
                    display_chunk = re.sub(r'\[ACCION:.*?\]?', '', chunk.text)
                    if display_chunk:
                        yield f"data: {json.dumps({'chunk': display_chunk})}\n\n"

            # Execute any embedded action (e.g. music playback, app launch)
            clean_reply, action_result = execute_embedded_actions(full_text)
            db.add_message("jarvis", clean_reply)
            
            # Generate TTS audio for clean speech
            audio_url = tts_engine.generate_tts_audio(clean_reply)
            yield f"data: {json.dumps({'done': True, 'audio_url': audio_url, 'action': action_result})}\n\n"

        except Exception as e:
            print(f"Error in stream: {e}")
            try:
                chat_session = create_chat_session()
                stream = chat_session.send_message_stream(mensaje)
                for chunk in stream:
                    if chunk.text:
                        full_text += chunk.text
                        display_chunk = re.sub(r'\[ACCION:.*?\]?', '', chunk.text)
                        if display_chunk:
                            yield f"data: {json.dumps({'chunk': display_chunk})}\n\n"
                clean_reply, action_result = execute_embedded_actions(full_text)
                db.add_message("jarvis", clean_reply)
                audio_url = tts_engine.generate_tts_audio(clean_reply)
                yield f"data: {json.dumps({'done': True, 'audio_url': audio_url, 'action': action_result})}\n\n"
            except Exception as e2:
                err_text = f"Interferencia detectada en el flujo neuronal: {str(e2)[:60]}"
                yield f"data: {json.dumps({'chunk': err_text, 'done': True})}\n\n"

    return Response(stream_with_context(stream_generator()), mimetype='text/event-stream')

@app.route('/download/jarvis.apk')
def download_apk():
    apk_path = os.path.join(DOWNLOADS_DIR, "jarvis.apk")
    if not os.path.exists(apk_path):
        return jsonify({"error": "El paquete APK está siendo compilado por los ingenieros de Stark, Señor."}), 404
    return send_from_directory(DOWNLOADS_DIR, "jarvis.apk", as_attachment=True, download_name="JARVIS-StarkOS.apk")

@app.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    if request.method == 'POST':
        data = request.json or {}
        title = data.get("title", "").strip()
        due_date = data.get("due_date")
        if not title:
            return jsonify({"error": "Título requerido"}), 400
        task_id = db.add_task(title, due_date)
        return jsonify({"status": "created", "id": task_id, "tasks": db.get_tasks()})
    return jsonify({"tasks": db.get_tasks()})

@app.route('/tasks/complete', methods=['POST'])
def complete_task_endpoint():
    data = request.json or {}
    identifier = data.get("id") or data.get("title")
    if not identifier:
        return jsonify({"error": "Identificador requerido"}), 400
    success = db.complete_task(identifier)
    return jsonify({"status": "ok" if success else "not_found", "tasks": db.get_tasks()})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_endpoint(task_id):
    success = db.delete_task(task_id)
    return jsonify({"status": "ok" if success else "not_found", "tasks": db.get_tasks()})

@app.route('/reset', methods=['POST'])
def reset():
    global chat_session
    chat_session = create_chat_session()
    db.clear_messages()
    return jsonify({"status": "ok", "message": "Memoria y registros reiniciados, Señor."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("\n==========================================")
    print("   J.A.R.V.I.S. NEURAL OPERATING SYSTEM   ")
    print("==========================================")
    print(f"Modelo IA: {ACTIVE_MODEL}")
    print("Motor TTS: ElevenLabs + Edge-TTS Mexican Neural")
    print("Base de Datos: SQLite (jarvis.db)")
    print("Telemetría OS: Activa")
    print(f"Puerto:        {port}")
    print("==========================================\n")
    app.run(debug=False, port=port, host='0.0.0.0')
