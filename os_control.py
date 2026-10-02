import os
import subprocess
import webbrowser
import psutil
from datetime import datetime

try:
    import pyautogui
except Exception:
    pyautogui = None

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "static", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Common Windows applications mapping
APP_COMMANDS = {
    "calculadora": "calc.exe",
    "calculator": "calc.exe",
    "bloc de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "navegador": "start chrome || start msedge",
    "chrome": "start chrome",
    "edge": "start msedge",
    "explorador": "explorer.exe",
    "archivos": "explorer.exe",
    "terminal": "start powershell",
    "cmd": "start cmd",
    "spotify": "start spotify",
    "vscode": "code",
    "codigo": "code",
}

def get_system_telemetry():
    """Retrieve live CPU, RAM, Disk, and Battery telemetry from Windows."""
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        battery = psutil.sensors_battery()
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
            "battery_percent": round(battery.percent, 1) if battery else 100,
            "power_plugged": battery.power_plugged if battery else True,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
    except Exception as e:
        return {
            "cpu_percent": 15.0,
            "ram_percent": 45.0,
            "disk_percent": 60.0,
            "battery_percent": 100,
            "power_plugged": True,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "error": str(e)
        }

def open_application(app_name: str) -> dict:
    """Launch a Windows application by known name."""
    clean_name = app_name.lower().strip()
    cmd = APP_COMMANDS.get(clean_name)
    
    if not cmd:
        # Fallback to direct execution via shell
        cmd = f"start {clean_name}"
    
    try:
        subprocess.Popen(cmd, shell=True)
        return {"success": True, "message": f"Iniciando {app_name}, Señor."}
    except Exception as e:
        return {"success": False, "message": f"No fue posible ejecutar {app_name}: {str(e)}"}

def take_screenshot() -> dict:
    """Capture screen and return public static path."""
    if pyautogui is None:
        return {
            "success": False, 
            "message": "Señor, la captura del ordenador central no está disponible en servidor cloud. Si está desde su teléfono móvil, puede capturar la pantalla presionando simultáneamente Encendido + Bajar Volumen."
        }
    try:
        from PIL import ImageGrab
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        screenshot = ImageGrab.grab(all_screens=True)
        screenshot.save(filepath)
        return {
            "success": True,
            "filename": filename,
            "url": f"/static/screenshots/{filename}",
            "message": "Captura de pantalla del sistema central completada y archivada, Señor."
        }
    except Exception as e:
        return {
            "success": False, 
            "message": "Señor, no fue posible capturar la pantalla de la PC (el monitor o sesión gráfica puede estar suspendido). Para capturar la pantalla de su dispositivo móvil, presione los botones físicos de Encendido + Bajar Volumen."
        }

def resolve_song_audio_stream(query: str) -> dict:
    """Extract direct audio stream URL with yt-dlp for seamless native playback."""
    clean_query = query.strip()
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"ytsearch1:{clean_query}", download=False)
            if 'entries' in res and res['entries']:
                entry = res['entries'][0]
                return {
                    "success": True,
                    "title": entry.get("title", clean_query),
                    "audio_stream_url": entry.get("url"),
                    "watch_url": entry.get("webpage_url") or f"https://www.youtube.com/results?search_query={clean_query}",
                    "thumbnail": entry.get("thumbnail"),
                    "duration": entry.get("duration"),
                    "query": clean_query
                }
    except Exception as e:
        print(f"[yt-dlp Stream Error]: {e}")

    # Fallback to direct search URL
    import urllib.parse
    return {
        "success": True,
        "title": clean_query,
        "audio_stream_url": None,
        "watch_url": f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_query)}",
        "thumbnail": None,
        "duration": None,
        "query": clean_query
    }

def play_music(song_query: str) -> dict:
    """Resolve direct audio stream for subtle in-app ambient playback."""
    info = resolve_song_audio_stream(song_query)
    
    return {
        "success": True,
        "action": "play_music",
        "query": info["query"],
        "title": info["title"],
        "audio_stream_url": info["audio_stream_url"],
        "watch_url": info["watch_url"],
        "thumbnail": info["thumbnail"],
        "message": f"Sintonizando '{info['title']}' en el canal de audio ambiental, Señor."
    }

def web_search(query: str, platform: str = "google") -> dict:
    """Perform a web search in default browser."""
    try:
        if platform == "youtube":
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return {"success": True, "message": f"Búsqueda de '{query}' ejecutada en el navegador, Señor."}
    except Exception as e:
        return {"success": False, "message": f"Error al abrir navegador: {str(e)}"}

def volume_control(action: str) -> dict:
    """Control system volume via simulated keys."""
    if pyautogui is None:
        return {"success": False, "message": "Control de volumen de hardware no disponible en entorno cloud."}
    try:
        if action == "up":
            for _ in range(5):
                pyautogui.press("volumeup")
            return {"success": True, "message": "Volumen incrementado, Señor."}
        elif action == "down":
            for _ in range(5):
                pyautogui.press("volumedown")
            return {"success": True, "message": "Volumen reducido, Señor."}
        elif action == "mute":
            pyautogui.press("volumemute")
            return {"success": True, "message": "Silencio de audio conmutado, Señor."}
        return {"success": False, "message": "Acción de volumen no reconocida."}
    except Exception as e:
        return {"success": False, "message": f"Error al ajustar volumen: {str(e)}"}

def parse_and_execute_os_command(text: str) -> dict | None:
    """Check if the user request is a direct OS system command."""
    t = text.lower().strip()
    
    # Screenshot
    if any(k in t for k in ["captura de pantalla", "toma una captura", "screenshot", "pantallazo"]):
        return take_screenshot()
    
    # Volume
    if any(k in t for k in ["sube el volumen", "subir volumen", "volumen arriba", "aumenta el volumen"]):
        return volume_control("up")
    if any(k in t for k in ["baja el volumen", "bajar volumen", "volumen abajo", "reduce el volumen"]):
        return volume_control("down")
    if any(k in t for k in ["silencia", "mute", "mutear", "silencio"]):
        return volume_control("mute")
        
    # Open apps with flexible matching
    if any(k in t for k in ["calculadora", "calc"]):
        if any(v in t for v in ["abre", "abrir", "inicia", "iniciar", "ejecuta", "lanza"]):
            return open_application("calculadora")
            
    if any(k in t for k in ["bloc de notas", "notepad"]):
        if any(v in t for v in ["abre", "abrir", "inicia", "iniciar", "ejecuta"]):
            return open_application("bloc de notas")

    if any(k in t for k in ["chrome", "navegador", "edge"]):
        if any(v in t for v in ["abre", "abrir", "inicia", "iniciar", "ejecuta"]):
            return open_application("chrome")

    if any(k in t for k in ["explorador", "archivos", "carpeta"]):
        if any(v in t for v in ["abre", "abrir", "inicia", "iniciar", "ejecuta"]):
            return open_application("explorador")

    if any(k in t for k in ["terminal", "powershell", "consola", "cmd"]):
        if any(v in t for v in ["abre", "abrir", "inicia", "iniciar", "ejecuta"]):
            return open_application("terminal")
            
    # Play music triggers
    for prefix in ["reproduce ", "reproducir ", "pon ", "poner ", "toca ", "tocar ", "escuchar "]:
        if t.startswith(prefix):
            song = t[len(prefix):].replace("la cancion ", "").replace("la canción ", "").replace("el tema ", "").replace("musica ", "").replace("música ", "").strip()
            if song:
                return play_music(song)
            
    # Search
    if t.startswith("busca en youtube ") or t.startswith("buscar en youtube "):
        q = t.replace("busca en youtube ", "").replace("buscar en youtube ", "").strip()
        return web_search(q, platform="youtube")
        
    if t.startswith("busca ") or t.startswith("buscar ") or t.startswith("googlea "):
        q = t.replace("busca en google ", "").replace("busca ", "").replace("buscar ", "").replace("googlea ", "").strip()
        return web_search(q, platform="google")
        
    return None
