import os
import hashlib
import asyncio
import requests
import edge_tts
from dotenv import load_dotenv

load_dotenv()

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "onwK4e9ZLuTAKqWW03F9")
EDGE_TTS_VOICE = "es-MX-JorgeNeural"  # Authentic Mexican Spanish dub style

def get_text_hash(text: str) -> str:
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()[:16]

def generate_tts_audio(text: str) -> str | None:
    """
    Generate audio for given text.
    1. Check if cached.
    2. Try ElevenLabs API if configured.
    3. Fallback to Edge-TTS Neural (es-MX-JorgeNeural).
    Returns relative web path to MP3 (e.g. '/static/audio/speech_xxx.mp3').
    """
    clean_text = (
        text.replace("**", "")
        .replace("*", "")
        .replace("#", "")
        .replace("`", "")
        .strip()
    )
    if not clean_text:
        return None

    file_hash = get_text_hash(clean_text)
    filename = f"speech_{file_hash}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    # Return cached if exists
    if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
        return f"/static/audio/{filename}"

    # Try ElevenLabs first if key exists
    if ELEVENLABS_API_KEY:
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": clean_text[:1000],  # Limit text to avoid quota waste
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.65,
                    "similarity_boost": 0.85,
                    "style": 0.15,
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                print(f"[TTS] Generated with ElevenLabs: {filename}")
                return f"/static/audio/{filename}"
            else:
                print(f"[TTS] ElevenLabs returned {resp.status_code}, falling back to Edge-TTS.")
        except Exception as e:
            print(f"[TTS] ElevenLabs error: {e}, falling back to Edge-TTS.")

    # Fallback to Edge-TTS (es-MX-JorgeNeural - Mexican Dub)
    try:
        async def run_edge_tts():
            # pitch -3Hz, rate -4% for calm, collected, technical JARVIS cadence
            communicate = edge_tts.Communicate(
                clean_text,
                EDGE_TTS_VOICE,
                pitch="-3Hz",
                rate="-4%"
            )
            await communicate.save(filepath)

        asyncio.run(run_edge_tts())
        print(f"[TTS] Generated with Edge-TTS ({EDGE_TTS_VOICE}): {filename}")
        return f"/static/audio/{filename}"
    except Exception as e:
        print(f"[TTS] Edge-TTS error: {e}")
        return None
