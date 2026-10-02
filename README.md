# 🛡️ J.A.R.V.I.S. Neural Operating System - Stark Industries Edition

> **Just A Rather Very Intelligent System**  
> Interfaz interactiva HUD Stark con IA multimodal, síntesis de voz neuronal mexicana, streaming de música en segundo plano, matriz de tareas SQLite y cliente APK nativo para Android.

---

## ⚡ Características Principales

- **🧠 Núcleo de IA Multimodal**: Impulsado por Google Gemini 2.5 / 3.5 con personalidad refinada del doblaje mexicano de Iron Man ("A su servicio, Señor").
- **🔊 Síntesis de Voz Híbrida (TTS)**: Enlace primario con ElevenLabs con conmutación por fallo automática a Edge-TTS (`es-MX-JorgeNeural`).
- **🎵 Reproducción Musical en Segundo Plano**: Extracción nativa de flujos de audio sin anuncios ni bloqueos mediante `yt-dlp`. Compatible con `MediaSession` y `WakeLock` en Android (la música no se detiene al minimizar la app).
- **📱 Cliente Android Nativo (APK)**: Aplicación Android con `BackgroundAudioWebView`, soporte de permisos de micrófono, puente de marcación telefónica (`[ACCION:LLAMAR:...]` -> `AndroidBridge.makePhoneCall`), y botón flotante de activación rápida de voz.
- **📋 Matriz de Protocolos Stark (To-Do)**: Gestión de tareas persistente en SQLite con comandos de voz directos ("recuérdame X", "completa la tarea X") y modal interactivo HUD.
- **🌐 Despliegue en la Nube (Render / Railway)**: Listo para producción con `gunicorn`, `Procfile` y variables de entorno dinámicas.

---

## 🚀 Despliegue Paso a Paso en Render.com

Desplegar JARVIS en **Render** permite tener tu asistente disponible las **24 horas del día** desde cualquier lugar del mundo sin necesidad de tener tu computadora encendida.

### Pasos:

1. **Crear cuenta en Render**: Ingresa a [https://render.com/](https://render.com/) y regístrate con tu cuenta de GitHub.
2. **Crear Nuevo Web Service**:
   - En el Dashboard de Render, haz clic en **New +** y selecciona **Web Service**.
   - Conecta tu repositorio de GitHub: `https://github.com/josebacilio2004/jarvis.git`.
3. **Configurar el Servicio**:
   - **Name**: `jarvis-core` (o el nombre que elijas).
   - **Region**: Selecciona la más cercana (ej. `Ohio (US East)` u `Oregon`).
   - **Branch**: `main`.
   - **Runtime**: `Python 3`.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 4 --timeout 120`
   - **Instance Type**: `Free`.
4. **Configurar Variables de Entorno (Environment Variables)**:
   - Añade:
     - `GEMINI_API_KEY`: Tu clave de Google AI Studio.
     - `ELEVENLABS_API_KEY`: (Opcional) Tu clave de ElevenLabs.
5. **Crear Servicio**: Haz clic en **Create Web Service**.
   - En 1-2 minutos tu servidor estará activo con una URL pública HTTPS:  
     `https://jarvis-core-xxxx.onrender.com`

### 📱 Vincular el APK de Android a Render:
1. Abre la aplicación JARVIS en tu celular Android.
2. **Mantén presionado cualquier parte de la pantalla** durante 1 segundo para abrir el diálogo de configuración de red.
3. Ingresa tu URL de Render: `https://jarvis-core-xxxx.onrender.com`.
4. ¡Listo! JARVIS responderá desde la nube con voz, música y tareas 24/7.

---

## 📱 ¿Cómo usar JARVIS en el móvil si no hay servidor encendido?

Si tu PC está apagada y no deseas usar la nube de Render:

1. **Modo Cloud Gratuito (Recomendado)**: Render o Railway gratuitos ejecutan el backend y la app móvil se conecta directamente vía datos móviles o Wi-Fi.
2. **Ejecutar Backend localmente en Android con Termux**:
   - Instala **Termux** desde F-Droid en tu celular Android.
   - Clona este repositorio en Termux:
     ```bash
     pkg update && pkg install python git
     git clone https://github.com/josebacilio2004/jarvis.git
     cd jarvis
     pip install -r requirements.txt
     python app.py
     ```
   - Abre la app APK o el navegador en `http://127.0.0.1:5000` y JARVIS correrá 100% dentro del hardware del celular.
3. **Modelos On-Device (Gemma 2B / MediaPipe)**:
   - Para ejecutar la IA completamente sin conexión a internet, se integran modelos compactos cuantizados (Gemma 2B INT4) mediante Google MediaPipe LLM Inference en Java/Kotlin dentro del APK nativo.

---

## 🛠️ Instalación y Ejecución Local en PC

```bash
# 1. Clonar repositorio
git clone https://github.com/josebacilio2004/jarvis.git
cd jarvis

# 2. Crear y activar entorno virtual
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env y agrega tu GEMINI_API_KEY

# 5. Iniciar JARVIS OS
python app.py
```

Acceso web local: `http://127.0.0.1:5000`  
Descarga del APK: `http://127.0.0.1:5000/download/jarvis.apk`

---

## 🤖 Comandos de Ejemplo para JARVIS

- **Traducciones**: *"JARVIS, quiero que me digas cómo se dice '¿Cómo estás?' en inglés"*.
- **Marcación telefónica**: *"Jarvis, marca a mamá de mis contactos"* o *"Jarvis, llama al 987654321"*.
- **Música ambiental**: *"Jarvis, reproduce AC/DC Back in Black"* o *"Pon música relajante"*.
- **Gestión de tareas**: *"Jarvis, crea la tarea preparar informe trimestral"* o *"Completa la tarea informe"*.
- **Informe matutino**: *"Buenos días, Jarvis"* (ejecuta el Stark Daily Briefing).
