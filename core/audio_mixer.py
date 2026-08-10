import os
import subprocess
from typing import Optional


class AudioMixer:
    @staticmethod
    def mix_voice_and_bgm(
        voice_path: str,
        bgm_path: str,
        output_path: str,
        voice_vol: float = 1.0,
        bgm_vol: float = 0.25,
        enable_ducking: bool = True
    ) -> str:
        """
        Mix voiceover audio with background music.
        If enable_ducking is True, background music volume drops automatically during voiceover speech.
        """
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voiceover file not found: {voice_path}")
        if not os.path.exists(bgm_path):
            raise FileNotFoundError(f"Background music file not found: {bgm_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if enable_ducking:
            # Sidechain compression filter graph for auto-ducking BGM
            filter_complex = (
                f"[0:a]volume={voice_vol}[voice];"
                f"[1:a]volume={bgm_vol},aloop=loop=-1:size=2e+09[bgm_loop];"
                f"[bgm_loop][voice]sidechaincompress=threshold=0.08:ratio=5:attack=50:release=400[ducked_bgm];"
                f"[voice][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
            )
        else:
            filter_complex = (
                f"[0:a]volume={voice_vol}[voice];"
                f"[1:a]volume={bgm_vol},aloop=loop=-1:size=2e+09[bgm_loop];"
                f"[voice][bgm_loop]amix=inputs=2:duration=first:dropout_transition=2[outa]"
            )

        cmd = [
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", bgm_path,
            "-filter_complex", filter_complex,
            "-map", "[outa]",
            "-ac", "2",
            "-ar", "44100",
            output_path
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            # Fallback simple amix if sidechain fails
            fallback_cmd = [
                "ffmpeg", "-y",
                "-i", voice_path,
                "-i", bgm_path,
                "-filter_complex", f"[0:a]volume={voice_vol}[v];[1:a]volume={bgm_vol}[b];[v][b]amix=inputs=2:duration=first[outa]",
                "-map", "[outa]",
                output_path
            ]
            res_fb = subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_fb.returncode != 0:
                raise RuntimeError(f"FFmpeg audio mixing failed: {res.stderr}")

        return output_path

    @staticmethod
    def merge_audio_with_video(
        video_path: str,
        audio_path: str,
        output_path: str,
        replace_original_audio: bool = True
    ) -> str:
        """
        Merge an audio track with a video file.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if replace_original_audio:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_path
            ]
        else:
            # Mix video audio with new audio track
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[outa]",
                "-map", "0:v:0",
                "-map", "[outa]",
                "-c:v", "copy",
                "-c:a", "aac",
                output_path
            ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            # Fallback re-encode video if stream copy fails
            fallback_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_path
            ]
            res_fb = subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_fb.returncode != 0:
                raise RuntimeError(f"FFmpeg video audio merge failed: {res.stderr}\nFallback error: {res_fb.stderr}")

        return output_path

    @staticmethod
    def normalize_audio(audio_path: str, output_path: str) -> str:
        """Apply dynamic audio normalization."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-af", "dynaudnorm=p=0.9:s=5",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio normalization failed: {res.stderr}")
        return output_path
