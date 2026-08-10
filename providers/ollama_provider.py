import json
import httpx
from typing import List, Dict, Any
from providers.base_provider import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    def test_connection(self) -> tuple[bool, str]:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m.get("name") for m in models]
                if not model_names:
                    return True, "Ollama terhubung (Belum ada model terinstall. Jalankan: ollama pull llama3.2)"
                return True, f"Ollama terhubung! Model tersedia: {', '.join(model_names[:5])}"
            return False, f"Ollama HTTP error status: {resp.status_code}"
        except httpx.ConnectError:
            return False, "Tidak dapat terhubung ke Ollama. Pastikan 'ollama serve' sedang berjalan di background."
        except Exception as e:
            return False, f"Error koneksi Ollama: {str(e)}"

    def analyze_transcript(
        self,
        segments: List[Dict[str, Any]],
        num_clips: int,
        target_duration: int = 30,
        topic: str = "",
        source_video_title: str = ""
    ) -> List[Dict[str, Any]]:
        prompt = self.build_prompt(
            segments, num_clips, target_duration, topic=topic, source_video_title=source_video_title
        )
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model or "gemma2:2b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                res_json = response.json()
                raw_response = res_json.get("response", "").strip()
                
                try:
                    data = json.loads(raw_response)
                    if isinstance(data, dict) and "clips" in data:
                        data = data["clips"]
                    if isinstance(data, list):
                        return data
                except Exception:
                    import re
                    match = re.search(r'\[.*\]', raw_response, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            print(f"[OllamaProvider Error] {e}")
        
        return []

    def generate_caption(
        self,
        title: str,
        text: str,
        reason: str = "",
        topic: str = "",
        source_video_title: str = ""
    ) -> dict:
        prompt = self.build_single_caption_prompt(
            title, text, reason, topic=topic, source_video_title=source_video_title
        )
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model or "gemma2:2b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                res_json = response.json()
                raw_response = res_json.get("response", "").strip()
                data = json.loads(raw_response)
                if isinstance(data, dict) and "title" in data:
                    return data
        except Exception as e:
            print(f"[OllamaProvider generate_caption Error] {e}")

        topic_tag = f" #{topic.replace(' ', '')}" if topic else ""
        return {
            "title": f"🔥 {title}",
            "description": f"🔥 {title}\n\n{reason}\n\n👉 Follow & Share untuk konten menarik lainnya!\n\n#viral #fyp #trending #shorts #reels{topic_tag}"
        }
