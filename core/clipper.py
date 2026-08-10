import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from core.auto_reframe import AutoReframe
from core.subtitle_burner import SubtitleBurner

class VideoClipper:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.subtitle_burner = SubtitleBurner()

    def sanitize_filename(self, text: str) -> str:
        import re
        s = re.sub(r'[^\w\s-]', '', text).strip().lower()
        return re.sub(r'[-\s]+', '_', s)[:30]

    def cut_clip(
        self,
        video_path: str,
        clip_info: dict,
        clip_index: int,
        aspect_ratio: str = "9:16",
        subtitle_settings: dict = None,
        progress_callback=None
    ) -> str:
        start_time = clip_info.get('start', 0)
        end_time = clip_info.get('end', 30)
        title = clip_info.get('title', '')
        
        title_slug = self.sanitize_filename(title) if title else f"clip_{clip_index}"
        output_name = f"clip_{clip_index:02d}_{title_slug}.mp4"
        output_path = self.output_dir / output_name

        if progress_callback:
            progress_callback(f"Processing Clip #{clip_index}: {title}...")

        duration = max(1.0, end_time - start_time)

        # Get video dimensions
        cap_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                   "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", video_path]
        try:
            res = subprocess.run(cap_cmd, stdout=subprocess.PIPE, text=True, check=True)
            w, h = map(int, res.stdout.strip().split('x'))
        except:
            w, h = 1920, 1080

        filter_complex = []
        
        target_w, target_h = w, h
        
        # 1. Auto-Reframe (Crop)
        if aspect_ratio == "9:16":
            reframe = AutoReframe("9:16")
            crop_filter = reframe.calculate_crop_window(video_path, start_time, end_time)
            if crop_filter:
                filter_complex.append(crop_filter)
                filter_complex.append("scale=1080:1920")
                target_w, target_h = 1080, 1920
            else:
                filter_complex.append("crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920")
                target_w, target_h = 1080, 1920
        elif aspect_ratio == "1:1":
            filter_complex.append("crop=ih:ih:(iw-ow)/2:0,scale=1080:1080")
            target_w, target_h = 1080, 1080

        # Anti-copyright: Mirror video horizontally
        filter_complex.append("hflip")

        # 2. Subtitles
        if subtitle_settings:
            ass_file = self.subtitle_burner.generate_ass_file(clip_info, subtitle_settings, clip_index, target_w, target_h)
            # escape path for ffmpeg filter
            escaped_ass = ass_file.replace('\\', '\\\\').replace(':', '\\:')
            filter_complex.append(f"ass='{escaped_ass}'")

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", video_path,
            "-t", str(duration)
        ]

        if filter_complex:
            cmd.extend([
                "-vf", ",".join(filter_complex),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k"
            ])
        else:
            cmd.extend([
                "-c:v", "copy",
                "-c:a", "copy"
            ])

        cmd.append(str(output_path))

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[Clipper Error] FFmpeg cut error: {e}. Trying fallback copy.")
            fallback_cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-i", video_path,
                "-t", str(duration),
                "-c", "copy",
                str(output_path)
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Embed judul & deskripsi sebagai metadata MP4
        self._embed_metadata(str(output_path), clip_info)
        return str(output_path)

    def _embed_metadata(self, video_path: str, clip_info: dict):
        """Embed title and description into MP4 metadata tags via ffmpeg."""
        title = clip_info.get('title', '')
        description = clip_info.get('description', clip_info.get('reason', ''))
        score = clip_info.get('score', '')
        start = clip_info.get('start', 0)
        end = clip_info.get('end', 0)

        if not (title or description):
            return

        # Write to a temp file then rename
        tmp_path = video_path + ".tmp.mp4"
        meta_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-c", "copy",
            "-map_metadata", "0",
        ]
        if title:
            meta_cmd += ["-metadata", f"title={title}"]
        if description:
            meta_cmd += ["-metadata", f"comment={description}"]
        if score:
            meta_cmd += ["-metadata", f"description=Viral Score: {score}/100 | {description}"]
        meta_cmd += ["-metadata", f"artist=Clipper AI Desktop"]
        meta_cmd += ["-metadata", f"album_artist=Auto-generated clip | {start:.1f}s - {end:.1f}s"]
        meta_cmd.append(tmp_path)

        try:
            subprocess.run(meta_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            import shutil
            shutil.move(tmp_path, video_path)
        except Exception as e:
            print(f"[Clipper] Metadata embed gagal (non-critical): {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def process_all_clips(
        self,
        video_path: str,
        clips: List[Dict[str, Any]],
        aspect_ratio: str = "9:16",
        subtitle_settings: dict = None,
        progress_callback=None
    ) -> List[str]:
        output_files = []
        for i, clip in enumerate(clips, 1):
            out_file = self.cut_clip(
                video_path=video_path,
                clip_info=clip,
                clip_index=i,
                aspect_ratio=aspect_ratio,
                subtitle_settings=subtitle_settings,
                progress_callback=progress_callback
            )
            output_files.append(out_file)
        return output_files
