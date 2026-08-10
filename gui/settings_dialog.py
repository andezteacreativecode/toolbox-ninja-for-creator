import customtkinter as ctk
from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory
from gui import theme


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings_mgr: SettingsManager):
        super().__init__(parent)
        self.settings_mgr = settings_mgr
        self.title("Pengaturan AI Service & Klip")
        self.geometry("520x620")
        self.resizable(False, False)

        self.configure(fg_color=theme.BG)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.data = self.settings_mgr.data

        self.create_widgets()

    def create_widgets(self):
        # TabView
        self.tabview = ctk.CTkTabView(
            self,
            width=480,
            height=520,
            corner_radius=8,
            fg_color=theme.SURFACE,
            text_color=theme.TEXT,
            segmented_button_fg_color=theme.SURFACE_ALT,
            segmented_button_selected_color=theme.ACCENT,
            segmented_button_selected_hover_color=theme.ACCENT_HOVER,
            segmented_button_unselected_color=theme.SURFACE_ALT,
            segmented_button_unselected_hover_color=theme.HOVER,
            border_width=1,
            border_color=theme.BORDER
        )
        self.tabview.pack(padx=20, pady=14, fill="both", expand=True)

        self.tab_ai = self.tabview.add("AI Providers")
        self.tab_clip = self.tabview.add("Klip & Format")

        self.build_ai_tab()
        self.build_clip_tab()

        # Bottom Action Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.status_lbl = ctk.CTkLabel(
            btn_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        )
        self.status_lbl.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Simpan Pengaturan",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=6,
            fg_color=theme.ACCENT,
            text_color=theme.ACCENT_TEXT,
            hover_color=theme.ACCENT_HOVER,
            command=self.save_settings
        )
        save_btn.pack(side="right")

    def _label(self, master, text, bold=False, **kwargs):
        kwargs.setdefault("text_color", theme.TEXT_MUTED)
        weight = "bold" if bold else "normal"
        return ctk.CTkLabel(master, text=text, font=ctk.CTkFont(size=12, weight=weight), **kwargs)

    def _entry(self, master, **kwargs):
        kwargs.setdefault("fg_color", theme.SURFACE_ALT)
        kwargs.setdefault("border_color", theme.BORDER)
        kwargs.setdefault("text_color", theme.TEXT)
        kwargs.setdefault("corner_radius", 6)
        kwargs.setdefault("font", ctk.CTkFont(size=13))
        return ctk.CTkEntry(master, **kwargs)

    def _card(self, master):
        return ctk.CTkFrame(
            master,
            fg_color=theme.SURFACE_ALT,
            corner_radius=8,
            border_width=1,
            border_color=theme.BORDER
        )

    def build_ai_tab(self):
        ctk.CTkLabel(
            self.tab_ai,
            text="Pilih Active AI Service",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.TEXT
        ).pack(anchor="w", pady=(12, 6))

        self.provider_var = ctk.StringVar(value=self.data.get("active_provider", "ollama"))
        self.provider_combo = ctk.CTkOptionMenu(
            self.tab_ai,
            values=["ollama", "9router"],
            variable=self.provider_var,
            command=self.on_provider_changed,
            height=36,
            corner_radius=6,
            fg_color=theme.SURFACE_ALT,
            button_color=theme.SURFACE_ALT,
            button_hover_color=theme.HOVER,
            text_color=theme.TEXT,
            dropdown_fg_color=theme.SURFACE_ALT,
            dropdown_hover_color=theme.HOVER,
            dropdown_text_color=theme.TEXT,
            font=ctk.CTkFont(size=13)
        )
        self.provider_combo.pack(fill="x", pady=(0, 12))

        # Ollama Group
        self.ollama_frame = self._card(self.tab_ai)
        self.ollama_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            self.ollama_frame,
            text="Ollama (Lokal)",
            font=ctk.CTkFont(weight="bold", size=13),
            text_color=theme.TEXT
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self._label(self.ollama_frame, "Base URL").pack(anchor="w", padx=12)
        self.ollama_url_entry = self._entry(self.ollama_frame)
        self.ollama_url_entry.insert(0, self.data['providers']['ollama'].get('base_url', 'http://localhost:11434'))
        self.ollama_url_entry.pack(fill="x", padx=12, pady=(2, 6))

        self._label(self.ollama_frame, "Model Name").pack(anchor="w", padx=12)
        self.ollama_model_entry = self._entry(self.ollama_frame)
        self.ollama_model_entry.insert(0, self.data['providers']['ollama'].get('model', 'llama3.2'))
        self.ollama_model_entry.pack(fill="x", padx=12, pady=(2, 12))

        # 9router Group
        self.router_frame = self._card(self.tab_ai)
        self.router_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            self.router_frame,
            text="9router / OpenRouter API",
            font=ctk.CTkFont(weight="bold", size=13),
            text_color=theme.TEXT
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self._label(self.router_frame, "Base URL").pack(anchor="w", padx=12)
        self.router_url_entry = self._entry(self.router_frame)
        self.router_url_entry.insert(0, self.data['providers']['9router'].get('base_url', 'https://openrouter.ai/api/v1'))
        self.router_url_entry.pack(fill="x", padx=12, pady=(2, 6))

        self._label(self.router_frame, "API Key").pack(anchor="w", padx=12)
        self.router_key_entry = self._entry(self.router_frame, show="\u2022")
        self.router_key_entry.insert(0, self.data['providers']['9router'].get('api_key', ''))
        self.router_key_entry.pack(fill="x", padx=12, pady=(2, 6))

        self._label(self.router_frame, "Model Name").pack(anchor="w", padx=12)
        self.router_model_entry = self._entry(self.router_frame)
        self.router_model_entry.insert(0, self.data['providers']['9router'].get('model', 'meta-llama/llama-3.1-8b-instruct:free'))
        self.router_model_entry.pack(fill="x", padx=12, pady=(2, 12))

        # Test Connection Button
        test_btn = ctk.CTkButton(
            self.tab_ai,
            text="Tes Koneksi Active Provider",
            height=36,
            corner_radius=6,
            fg_color="transparent",
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.TEXT,
            hover_color=theme.HOVER,
            command=self.test_connection
        )
        test_btn.pack(fill="x", pady=12)

    def build_clip_tab(self):
        clip_conf = self.data.get("clip_settings", {})

        self._label(self.tab_clip, "Target Durasi per Klip (detik)", bold=True).pack(anchor="w", pady=(12, 4))
        self.dur_entry = self._entry(self.tab_clip)
        self.dur_entry.insert(0, str(clip_conf.get("target_duration", 30)))
        self.dur_entry.pack(fill="x", pady=(0, 12))

        self._label(self.tab_clip, "Default Jumlah Klip", bold=True).pack(anchor="w", pady=(4, 4))
        self.num_entry = self._entry(self.tab_clip)
        self.num_entry.insert(0, str(clip_conf.get("num_clips", 3)))
        self.num_entry.pack(fill="x", pady=(0, 12))

        self._label(self.tab_clip, "Aspect Ratio Output", bold=True).pack(anchor="w", pady=(4, 4))
        self.ratio_var = ctk.StringVar(value=clip_conf.get("aspect_ratio", "9:16"))
        self.ratio_combo = ctk.CTkOptionMenu(
            self.tab_clip,
            values=["9:16 (TikTok/Reels Vertikal)", "1:1 (Square)", "Asli (Original)"],
            variable=self.ratio_var,
            height=36,
            corner_radius=6,
            fg_color=theme.SURFACE_ALT,
            button_color=theme.SURFACE_ALT,
            button_hover_color=theme.HOVER,
            text_color=theme.TEXT,
            dropdown_fg_color=theme.SURFACE_ALT,
            dropdown_hover_color=theme.HOVER,
            dropdown_text_color=theme.TEXT,
            font=ctk.CTkFont(size=13)
        )
        self.ratio_combo.pack(fill="x", pady=(0, 12))

        self._label(self.tab_clip, "Folder Hasil Export", bold=True).pack(anchor="w", pady=(4, 4))
        self.out_entry = self._entry(self.tab_clip)
        self.out_entry.insert(0, clip_conf.get("output_dir", ""))
        self.out_entry.pack(fill="x", pady=(0, 12))

    def on_provider_changed(self, choice):
        self.status_lbl.configure(text=f"Active provider diubah ke: {choice}", text_color=theme.TEXT_MUTED)

    def test_connection(self):
        active = self.provider_var.get()
        # Temp collect config
        if active == "ollama":
            cfg = {
                "name": "Ollama",
                "base_url": self.ollama_url_entry.get().strip(),
                "model": self.ollama_model_entry.get().strip()
            }
        else:
            cfg = {
                "name": "9router",
                "base_url": self.router_url_entry.get().strip(),
                "api_key": self.router_key_entry.get().strip(),
                "model": self.router_model_entry.get().strip()
            }

        try:
            prov = ProviderFactory.get_provider(active, cfg)
            ok, msg = prov.test_connection()
            if ok:
                self.status_lbl.configure(text=msg, text_color=theme.SUCCESS)
            else:
                self.status_lbl.configure(text=msg, text_color=theme.DANGER)
        except Exception as e:
            self.status_lbl.configure(text=f"Error: {str(e)}", text_color=theme.DANGER)

    def save_settings(self):
        active = self.provider_var.get()
        self.data["active_provider"] = active
        self.data["providers"]["ollama"]["base_url"] = self.ollama_url_entry.get().strip()
        self.data["providers"]["ollama"]["model"] = self.ollama_model_entry.get().strip()

        self.data["providers"]["9router"]["base_url"] = self.router_url_entry.get().strip()
        self.data["providers"]["9router"]["api_key"] = self.router_key_entry.get().strip()
        self.data["providers"]["9router"]["model"] = self.router_model_entry.get().strip()

        ratio_raw = self.ratio_var.get()
        ratio = "9:16" if "9:16" in ratio_raw else ("1:1" if "1:1" in ratio_raw else "original")

        try:
            dur = int(self.dur_entry.get())
            num = int(self.num_entry.get())
        except ValueError:
            dur = 30
            num = 3

        self.data["clip_settings"]["target_duration"] = dur
        self.data["clip_settings"]["num_clips"] = num
        self.data["clip_settings"]["aspect_ratio"] = ratio
        self.data["clip_settings"]["output_dir"] = self.out_entry.get().strip()

        self.settings_mgr.save(self.data)
        self.destroy()
