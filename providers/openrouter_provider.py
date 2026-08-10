import json
import httpx
from typing import List, Dict, Any
from providers.base_provider import BaseAIProvider

class OpenRouter9RouterProvider(BaseAIProvider):
    def test_connection(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "API Key belum diisi. Silakan masukkan API key 9router/OpenRouter di Settings."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/clipper-desktop",
            "X-Title": "Clipper Desktop"
        }
        url = f"{self.base_url}/models"
        try:
            resp = httpx.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                return True, "9router / OpenRouter API terhubung secara sukses!"
            elif resp.status_code in (401, 403):
                return False, "API Key tidak valid atau unauthorized."
            else:
                return False, f"HTTP Error status: {resp.status_code}"
        except Exception as e:
            return False, f"Gagal terhubung ke 9router/OpenRouter: {str(e)}"

    def analyze_transcript(
        self,
        segments: List[Dict[str, Any]],
        num_clips: int,
        target_duration: int = 30,
        topic: str = "",
        source_video_title: str = ""
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            print("[OpenRouter9RouterProvider Warning] API key kosong.")
            return []

        prompt = self.build_prompt(
            segments, num_clips, target_duration, topic=topic, source_video_title=source_video_title
        )
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/clipper-desktop",
            "X-Title": "Clipper Desktop"
        }
        
        model_name = self.model or "meta-llama/llama-3.1-8b-instruct:free"
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You analyze video transcripts and return viral highlight clip timestamp ranges in JSON array format strictly."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_json = response.json()
                content = res_json['choices'][0]['message']['content'].strip()
                
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and "clips" in data:
                        data = data["clips"]
                    if isinstance(data, list):
                        return data
                except Exception:
                    import re
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            print(f"[OpenRouter9RouterProvider Error] {e}")

        return []

    def generate_caption(
        self,
        title: str,
        text: str,
        reason: str = "",
        topic: str = "",
        source_video_title: str = ""
    ) -> dict:
        if not self.api_key:
            print("[OpenRouter9RouterProvider Warning] API key kosong.")
            topic_tag = f" #{topic.replace(' ', '')}" if topic else ""
            return {
                "title": f"🔥 {title}",
                "description": f"🔥 {title}\n\n{reason}\n\n👉 Follow & Share untuk konten menarik lainnya!\n\n#viral #fyp #trending #shorts #reels{topic_tag}"
            }

        prompt = self.build_single_caption_prompt(
            title, text, reason, topic=topic, source_video_title=source_video_title
        )
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/clipper-desktop",
            "X-Title": "Clipper Desktop"
        }
        model_name = self.model or "meta-llama/llama-3.1-8b-instruct:free"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a social media viral caption generator. Output strictly JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_json = response.json()
                content = res_json['choices'][0]['message']['content'].strip()

                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                data = json.loads(content)
                if isinstance(data, dict) and "title" in data:
                    return data
        except Exception as e:
            print(f"[OpenRouter9RouterProvider generate_caption Error] {e}")

        topic_tag = f" #{topic.replace(' ', '')}" if topic else ""
        return {
            "title": f"🔥 {title}",
            "description": f"🔥 {title}\n\n{reason}\n\n👉 Follow & Share untuk konten menarik lainnya!\n\n#viral #fyp #trending #shorts #reels{topic_tag}"
        }
