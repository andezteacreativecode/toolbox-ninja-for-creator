import os
import subprocess
from pathlib import Path

class FasterWhisperTranscriber:
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

    def transcribe(self, video_path: str, model_size: str = "base", progress_callback=None):
        if progress_callback:
            progress_callback("Mengekstrak audio dari video...")
        audio_path = self.extract_audio(video_path)

        if progress_callback:
            progress_callback("Menjalankan faster-whisper Speech-to-Text (dengan word timestamps)...")

        try:
            from faster_whisper import WhisperModel
            # Run on CPU with INT8 for wider compatibility, or GPU if available
            # In a real app, we'd detect CUDA
            device = "cpu" 
            compute_type = "int8"
            
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    compute_type = "float16"
            except:
                pass

            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)

            formatted_segments = []
            for segment in segments:
                words = []
                for word in segment.words:
                    words.append({
                        "start": round(word.start, 2),
                        "end": round(word.end, 2),
                        "text": word.word.strip()
                    })
                
                formatted_segments.append({
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip(),
                    "words": words
                })
            
            return formatted_segments
        except Exception as e:
            print(f"[FasterWhisper Warning] Model error: {e}. Generating fallback.")
            return self._generate_fallback_segments(audio_path)

    def _generate_fallback_segments(self, audio_path: str):
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
                "text": f"[Audio Window {int(current)}s-{int(end_t)}s]",
                "words": []
            })
            current += step
        return segments
