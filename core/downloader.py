import os
import re
from pathlib import Path
import yt_dlp

class VideoDownloader:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_url(path_or_url: str) -> bool:
        return bool(re.match(r'^https?://', path_or_url.strip()))

    def prepare_video(self, source: str, progress_callback=None) -> tuple[str, str]:
        """
        If source is URL -> Download via yt-dlp to local file.
        If source is local path -> Return validated absolute path.
        Returns: (video_path, video_title)
        """
        source = source.strip()
        if not self.is_url(source):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File video tidak ditemukan: {source}")
            video_title = path.stem.replace("_", " ").title()
            return str(path.absolute()), video_title

        # It's a URL
        output_template = str(self.download_dir / "%(title)s_%(id)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        if progress_callback:
            def ydl_hook(d):
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').strip()
                    progress_callback(f"Downloading video... {p}")
                elif d['status'] == 'finished':
                    progress_callback("Download selesai, mengolah video...")
            ydl_opts['progress_hooks'] = [ydl_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source, download=True)
            video_title = info.get('title', 'YouTube Video')
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                base, _ = os.path.splitext(filename)
                if os.path.exists(base + ".mp4"):
                    filename = base + ".mp4"
            return str(Path(filename).absolute()), video_title
