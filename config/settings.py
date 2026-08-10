import os
import json
import sys
from pathlib import Path

def get_user_config_dir() -> Path:
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))
        cfg_dir = Path(base) / 'ClipperDesktop'
    else:
        cfg_dir = Path.home() / '.clipper_desktop'
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir

CONFIG_PATH = get_user_config_dir() / "settings.json"

DEFAULT_SETTINGS = {
    "active_provider": "ollama",
    "providers": {
        "ollama": {
            "name": "Ollama (Lokal)",
            "base_url": "http://localhost:11434",
            "model": "llama3.2"
        },
        "9router": {
            "name": "9router / OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "",
            "model": "meta-llama/llama-3.1-8b-instruct:free"
        }
    },
    "clip_settings": {
        "target_duration": 30,
        "num_clips": 3,
        "output_format": "mp4",
        "output_dir": str(Path.home() / "Videos" / "ClipperOutput"),
        "aspect_ratio": "9:16",
        "add_subtitles": True
    }
}

class SettingsManager:
    def __init__(self, config_file: Path = CONFIG_PATH):
        self.config_file = config_file
        self.data = self.load()

    def load(self) -> dict:
        if not self.config_file.exists():
            self.save(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # merge defaults if keys missing
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return DEFAULT_SETTINGS

    def save(self, data: dict = None):
        if data is None:
            data = self.data
        else:
            self.data = data
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def get_active_provider_config(self) -> dict:
        active = self.data.get("active_provider", "ollama")
        return self.data.get("providers", {}).get(active, {})

    def set_active_provider(self, provider_key: str):
        if provider_key in self.data.get("providers", {}):
            self.data["active_provider"] = provider_key
            self.save()

