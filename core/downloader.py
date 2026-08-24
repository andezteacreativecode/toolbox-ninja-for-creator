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
            # Format: prefer mp4 with audio, fallback ke format apapun yg tersedia
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            # Anti-403: retry dan throttle handling
            'retries': 5,
            'fragment_retries': 5,
            'http_chunk_size': 10485760,  # 10MB chunks
            # Anti-403: header supaya terlihat seperti browser biasa
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            # Anti-403: bypass YouTube throttling via po_token / innertube
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android'],
                    'skip': ['dash', 'hls'],
                }
            },
            # Merge video+audio ke mp4
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        # Anti-403: coba pakai cookies dari browser yang terinstall
        for browser in ('chrome', 'chromium', 'firefox', 'edge', 'brave', 'opera'):
            try:
                test_opts = dict(ydl_opts)
                test_opts['cookiesfrombrowser'] = (browser, None, None, None)
                test_opts['quiet'] = True
                with yt_dlp.YoutubeDL(test_opts) as ydl_test:
                    ydl_test.extract_info(source, download=False)
                # Berhasil extract info -> pakai browser ini
                ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
                break
            except Exception:
                continue

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
            # Cari file hasil download (bisa berubah ekstensi karena merge)
            if not os.path.exists(filename):
                base, _ = os.path.splitext(filename)
                for ext in ('.mp4', '.mkv', '.webm'):
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break
            return str(Path(filename).absolute()), video_title
