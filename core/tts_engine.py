import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False


# Presets for popular voices
POPULAR_VOICES = [
    {"name": "Gadis (Indonesian - Female)", "short_name": "id-ID-GadisNeural", "lang": "id-ID", "gender": "Female"},
    {"name": "Ardi (Indonesian - Male)", "short_name": "id-ID-ArdiNeural", "lang": "id-ID", "gender": "Male"},
    {"name": "Ava (English US - Female)", "short_name": "en-US-AvaNeural", "lang": "en-US", "gender": "Female"},
    {"name": "Andrew (English US - Male)", "short_name": "en-US-AndrewNeural", "lang": "en-US", "gender": "Male"},
    {"name": "Emma (English US - Female)", "short_name": "en-US-EmmaNeural", "lang": "en-US", "gender": "Female"},
    {"name": "Brian (English UK - Male)", "short_name": "en-GB-BrianNeural", "lang": "en-GB", "gender": "Male"},
    {"name": "Sonia (English UK - Female)", "short_name": "en-GB-SoniaNeural", "lang": "en-GB", "gender": "Female"},
]


class TTSEngine:
    @staticmethod
    def list_popular_voices() -> List[Dict[str, str]]:
        return POPULAR_VOICES

    @staticmethod
    def fetch_all_edge_voices_sync() -> List[Dict[str, Any]]:
        """Fetch all available Edge TTS voices asynchronously wrapped in sync call."""
        if not HAS_EDGE_TTS:
            return POPULAR_VOICES

        async def _fetch():
            try:
                voices = await edge_tts.list_voices()
                return [
                    {
                        "name": f"{v.get('FriendlyName', v['ShortName'])} ({v.get('Locale', '')})",
                        "short_name": v['ShortName'],
                        "lang": v.get('Locale', ''),
                        "gender": v.get('Gender', '')
                    }
                    for v in voices
                ]
            except Exception as e:
                print(f"[TTSEngine] Error fetching voices: {e}")
                return POPULAR_VOICES

        try:
            return asyncio.run(_fetch())
        except Exception:
            return POPULAR_VOICES

    @staticmethod
    def generate_edge_tts_sync(
        text: str,
        voice: str = "id-ID-GadisNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        output_path: str = "output_voice.mp3"
    ) -> str:
        """Generate audio using Microsoft Edge Neural TTS."""
        if not HAS_EDGE_TTS:
            raise RuntimeError("edge-tts library is not installed.")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        async def _generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            await communicate.save(output_path)

        asyncio.run(_generate())
        return output_path

    @staticmethod
    def generate_openai_tts(
        text: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "tts-1",
        voice: str = "alloy",
        output_path: str = "output_voice.mp3"
    ) -> str:
        """Generate audio using OpenAI / OpenRouter TTS API."""
        if not api_key:
            raise ValueError("API Key is required for OpenAI TTS.")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        url = f"{base_url.rstrip('/')}/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI TTS API Error ({resp.status_code}): {resp.text}")
            
            with open(output_path, "wb") as f:
                f.write(resp.content)

        return output_path
