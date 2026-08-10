import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class VideoTranscriber:
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio(self, video_path: str) -> str:
        audio_path = self.temp_dir / f"extracted_{Path(video_path).stem}.wav"
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            str(audio_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(audio_path)

    def transcribe(self, video_path: str, model_size: str = "base", progress_callback=None) -> List[Dict[str, Any]]:
        """
        Extract audio and run Whisper transcription.
        Returns list of dict: [{'start': 0.0, 'end': 4.5, 'text': 'Hello world'}]
        """
        if progress_callback:
            progress_callback("Mengekstrak audio dari video...")
        audio_path = self.extract_audio(video_path)

        if progress_callback:
            progress_callback("Menjalankan Whisper Speech-to-Text...")

        try:
            import whisper
            model = whisper.load_model(model_size)
            result = model.transcribe(audio_path, language="id", fp16=False)
            
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": round(float(seg["start"]), 2),
                    "end": round(float(seg["end"]), 2),
                    "text": seg["text"].strip()
                })
            return segments
        except Exception as e:
            print(f"[Transcriber Warning] Whisper model error: {e}. Generating fallback time windows.")
            # Fallback timestamp segments every 10s if transcript fails
            return self._generate_fallback_segments(audio_path)

    def _generate_fallback_segments(self, audio_path: str) -> List[Dict[str, Any]]:
        import wave
        try:
            with wave.open(audio_path, 'r') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
        except Exception:
            duration = 300.0

        segments = []
        step = 10.0
        current = 0.0
        while current < duration:
            end_t = min(current + step, duration)
            segments.append({
                "start": round(current, 2),
                "end": round(end_t, 2),
                "text": f"[Video Audio Audio-Peak Window {int(current)}s-{int(end_t)}s]"
            })
            current += step
        return segments
