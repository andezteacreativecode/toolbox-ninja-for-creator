from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAIProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "").rstrip("/")
        self.model = config.get("model", "")
        self.api_key = config.get("api_key", "")

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Returns (is_success, status_message)"""
        pass

    @abstractmethod
    def analyze_transcript(
        self,
        segments: List[Dict[str, Any]],
        num_clips: int,
        target_duration: int = 30,
        topic: str = "",
        source_video_title: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Input: list of transcript segments [{'start': 0.0, 'end': 5.0, 'text': '...'}]
        Output: list of viral moments [{'start': float, 'end': float, 'title': str, 'reason': str, 'score': float}]
        """
        pass

    def build_prompt(
        self,
        segments: List[Dict[str, Any]],
        num_clips: int,
        target_duration: int,
        topic: str = "",
        source_video_title: str = ""
    ) -> str:
        transcript_text = ""
        for seg in segments:
            start_m = int(seg['start'] // 60)
            start_s = int(seg['start'] % 60)
            transcript_text += f"[{start_m:02d}:{start_s:02d}] (detik {seg['start']:.1f} - {seg['end']:.1f}): {seg['text']}\n"

        context_instructions = []
        if source_video_title and source_video_title.strip():
            context_instructions.append(f"JUDUL ASLI VIDEO YOUTUBE (SUMBER ORIGINAL): \"{source_video_title.strip()}\"")
            context_instructions.append(f"PENTING: Pastikan semua judul klip dan deskripsi yang kamu buat SANGAT RELEVAN, AKURAT, dan BERHUBUNGAN ERAT dengan Judul Utama Video YouTube Asli di atas.")

        if topic and topic.strip() and topic.strip().lower() not in ["auto", "umum", "auto / sesuai isi video"]:
            context_instructions.append(f"FOKUS TOPIK / NICHE TARGET: {topic.strip()}")

        context_block = "\n".join(context_instructions) + "\n" if context_instructions else ""

        prompt = f"""Kamu adalah pakar video editor dan sosial media strategist viral (TikTok/Reels/Shorts).
Tugasmu adalah menganalisis transkrip video berikut dan menemukan {num_clips} potongan momen paling menarik/viral/emosional/lucu/penuh kejutan dengan durasi sekitar {target_duration} detik per klip.
{context_block}
Transkrip Video:
{transcript_text}

Kembalikan jawaban HANYA dalam format JSON array yang valid (tanpa teks penjelasan ekstra, tanpa markdown codeblock ``` json):
[
  {{
    "start": float_detik_mulai,
    "end": float_detik_selesai,
    "title": "Judul Menarik & Catchy Untuk Klip (maks 60 karakter)",
    "description": "Deskripsi singkat 1-2 kalimat tentang isi klip ini untuk caption sosmed",
    "reason": "Alasan singkat kenapa bagian ini viral",
    "score": float_skor_0_sampai_100
  }}
]

Aturan:
1. Pastikan durasi (end - start) mendekati {target_duration} detik (toleransi 20 - 45 detik).
2. Momen tidak boleh saling tumpang tindih (overlapping).
3. Hasilkan tepat {num_clips} klip terbaik.
4. Field "title" harus catchy, relevan dengan judul video YouTube asli, dan menarik perhatian penonton sosmed.
5. Field "description" digunakan sebagai caption dan metadata video, tulis dalam bahasa yang sama dengan konten video.
"""
        return prompt

    def build_single_caption_prompt(
        self,
        title: str,
        text: str,
        reason: str = "",
        topic: str = "",
        source_video_title: str = ""
    ) -> str:
        context_instructions = []
        if source_video_title and source_video_title.strip():
            context_instructions.append(f"JUDUL UTAMA VIDEO YOUTUBE (SUMBER ORIGINAL): \"{source_video_title.strip()}\"")
            context_instructions.append(f"PENTING: Judul klip dan caption HARUS 100% selaras dan mencerminkan topik dari Judul Utama Video YouTube di atas.")

        if topic and topic.strip() and topic.strip().lower() not in ["auto", "umum", "auto / sesuai isi video"]:
            context_instructions.append(f"FOKUS TOPIK / NICHE TARGET: {topic.strip()}")

        context_block = "\n".join(context_instructions) + "\n" if context_instructions else ""

        return f"""Kamu adalah pakar viral social media strategist (TikTok, Instagram Reels, YouTube Shorts).
Berdasarkan informasi klip video berikut:
- Judul Klip: {title}
- Alasan Viral: {reason}
- Transkrip Klip: {text}
{context_block}
Tugasmu:
1. Buat 1 JUDUL VIRAL yang sangat menarik perhatian penonton (hooking title, max 60 karakter, tambahkan emoji menarik di awal, dan selaras dengan Judul Video Utama YouTube).
2. Buat 1 CAPTION/DESKRIPSI SOSIAL MEDIA LENGKAP dengan Hook di awal, 2-3 kalimat penjelasan menarik yang menghubungkan klip ini dengan konteks video YouTube utamanya, Call to Action (CTA) ramah, dan 6-8 hashtag viral (#fyp #viral #trending #shorts #reels).

Kembalikan HANYA format JSON valid tanpa penjelasan markdown:
{{
  "title": "🔥 Judul Viral Di Sini",
  "description": "🔥 Judul Viral\\n\\nHook menarik! Isi deskripsi video yang membuat penasaran.\\n\\n👉 Follow & share untuk video menarik lainnya!\\n\\n#fyp #viral #trending #shorts #reels #foryou"
}}
"""
