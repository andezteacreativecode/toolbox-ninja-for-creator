import os
import subprocess
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from providers.base_provider import BaseAIProvider

class MomentDetector:
    def __init__(self, ai_provider: BaseAIProvider):
        self.ai_provider = ai_provider

    def detect_audio_energy_peaks(self, video_path: str, window_sec: float = 2.0) -> List[tuple[float, float]]:
        """Extract audio volume RMS to find peak moments"""
        try:
            cmd = [
                "ffmpeg", "-i", video_path,
                "-af", "astats=metadata=1:reset=1",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
            peaks = []
            for line in res.stderr.split("\n"):
                if "pts_time:" in line and "RMS level" in line:
                    match_t = re.search(r'pts_time:([\d\.]+)', line)
                    match_rms = re.search(r'RMS level.*: ([\-\d\.]+)', line)
                    if match_t and match_rms:
                        t = float(match_t.group(1))
                        rms = float(match_rms.group(1))
                        peaks.append((t, rms))
            return peaks
        except Exception:
            return []

    def detect_scene_cuts(self, video_path: str, threshold: float = 0.3) -> List[float]:
        """Detect scene change timestamps using FFmpeg select filter"""
        try:
            cmd = [
                "ffmpeg", "-i", video_path,
                "-filter_complex", f"select='gt(scene,{threshold})',metadata=print:file=-",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            timestamps = []
            for line in res.stdout.split("\n"):
                if "pts_time:" in line:
                    match = re.search(r'pts_time:([\d\.]+)', line)
                    if match:
                        timestamps.append(float(match.group(1)))
            return timestamps
        except Exception:
            return []

    def _extract_clip_text(self, start: float, end: float, segments: List[Dict[str, Any]]):
        clip_words = []
        clip_text = ""
        for seg in segments:
            if seg['end'] > start and seg['start'] < end:
                if 'words' in seg and seg['words']:
                    for w in seg['words']:
                        if w['start'] >= start - 1.0 and w['end'] <= end + 1.0:
                            clip_words.append(w)
                else:
                    clip_text += seg.get('text', '') + " "
        return clip_words, clip_text.strip()

    def detect_viral_moments(
        self,
        video_path: str,
        segments: List[Dict[str, Any]],
        num_clips: int = 3,
        target_duration: int = 30,
        topic: str = "",
        source_video_title: str = "",
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Full moment detection pipeline combining AI LLM analysis + Audio/Visual heuristic scoring.
        """
        if progress_callback:
            topic_str = f" Topik: '{topic}'" if topic else ""
            title_str = f" | Judul YouTube: '{source_video_title}'" if source_video_title else ""
            progress_callback(f"Analyzing transcript with AI ({self.ai_provider.config.get('name', 'AI')}){topic_str}{title_str}...")

        # 1. AI Analysis via LLM
        ai_candidates = []
        try:
            ai_candidates = self.ai_provider.analyze_transcript(
                segments,
                num_clips=num_clips + 2,
                target_duration=target_duration,
                topic=topic,
                source_video_title=source_video_title
            )
        except Exception as e:
            print(f"[MomentDetector Warning] AI provider failed: {e}")

        # Determine video total duration from segments or ffmpeg
        video_duration = 300.0
        if segments:
            video_duration = max(seg['end'] for seg in segments)

        # 2. Audio & Visual features detection
        if progress_callback:
            progress_callback("Analyzing audio energy & scene cuts...")
        
        scene_cuts = self.detect_scene_cuts(video_path)

        # If AI generated valid candidates, refine them with video bounds
        results = []
        if ai_candidates and isinstance(ai_candidates, list):
            for item in ai_candidates:
                try:
                    start = float(item.get("start", 0))
                    end = float(item.get("end", start + target_duration))
                    
                    dur = end - start
                    if dur < 10 or dur > 60:
                        end = start + target_duration
                    
                    start = max(0.0, start)
                    end = min(video_duration, end)

                    title = str(item.get("title", f"Viral Moment @ {int(start)}s"))
                    reason = str(item.get("reason", item.get("description", "Detected by AI")))
                    score = float(item.get("score", 85.0))

                    near_cut = any(abs(cut - start) < 3.0 for cut in scene_cuts)
                    if near_cut:
                        score += 5.0

                    cw, ct = self._extract_clip_text(start, end, segments)
                    results.append({
                        "start": round(start, 2),
                        "end": round(end, 2),
                        "duration": round(end - start, 2),
                        "title": title,
                        "description": item.get("description", reason),
                        "reason": reason,
                        "score": round(min(100.0, score), 1),
                        "words": cw,
                        "text": ct,
                        "source_video_title": source_video_title
                    })
                except Exception as e:
                    print(f"[Candidate Parse Error] {e}")

        # 3. Fallback heuristic if AI candidates returned empty or insufficient
        if len(results) < num_clips:
            if progress_callback:
                progress_callback("Using Fallback Smart Heuristic Clipper...")
            
            needed = num_clips - len(results)
            step = max(5.0, (video_duration - target_duration) / max(1, needed))
            cur = 0.0
            clip_idx = 1
            while len(results) < num_clips:
                if cur >= video_duration:
                    cur = 0.0
                
                end = min(cur + target_duration, video_duration)
                cw, ct = self._extract_clip_text(cur, end, segments)
                title_prefix = f"Highlight {source_video_title}" if source_video_title else (f"Highlight {topic}" if topic else "Highlight Clip")
                results.append({
                    "start": round(cur, 2),
                    "end": round(end, 2),
                    "duration": round(end - cur, 2),
                    "title": f"🔥 {title_prefix[:35]} #{clip_idx}",
                    "description": f"Momen terbaik dari '{source_video_title if source_video_title else 'video ini'}'.",
                    "reason": "Recommended viral moment",
                    "score": round(75.0 + clip_idx, 1),
                    "words": cw,
                    "text": ct,
                    "source_video_title": source_video_title
                })
                clip_idx += 1
                cur += step

        # Sort by score descending and take top N clips
        results.sort(key=lambda x: x['score'], reverse=True)
        final_clips = results[:num_clips]
        
        # Sort chronologically by start time for display
        final_clips.sort(key=lambda x: x['start'])
        return final_clips
