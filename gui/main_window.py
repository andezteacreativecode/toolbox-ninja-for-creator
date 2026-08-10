import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory
from core.downloader import VideoDownloader
from core.transcriber import VideoTranscriber
from core.moment_detector import MomentDetector
from core.clipper import VideoClipper
from gui.settings_dialog import SettingsDialog
from gui.clip_card import ClipCardWidget
from gui import theme

ctk.set_appearance_mode("Dark")


class ClipperMainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Clipper — Auto Viral Clip Detector")
        self.geometry("900x720")
        self.minsize(800, 600)

        self.configure(fg_color=theme.BG)

        self.settings_mgr = SettingsManager()

        self.is_processing = False

        self.create_widgets()
        self.update_provider_badge()

    def create_widgets(self):
        # ---- Header ----
        header_frame = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.pack(side="left", padx=20, pady=14)

        ctk.CTkLabel(
            title_block,
            text="Clipper",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=theme.TEXT
        ).pack(side="left")

        ctk.CTkLabel(
            title_block,
            text="  Auto Viral Clip Detector",
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED
        ).pack(side="left", pady=(6, 0))

        self.badge_lbl = ctk.CTkLabel(
            header_frame,
            text="AI: Ollama",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=theme.ACCENT_SOFT,
            corner_radius=999,
            padx=10,
            pady=4,
            text_color=theme.ACCENT
        )
        self.badge_lbl.pack(side="left", padx=10)

        settings_btn = ctk.CTkButton(
            header_frame,
            text="Pengaturan AI Service",
            width=170,
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.TEXT_MUTED,
            hover_color=theme.HOVER,
            command=self.open_settings
        )
        settings_btn.pack(side="right", padx=20)

        ctk.CTkFrame(self, fg_color=theme.BORDER, height=1).pack(fill="x")

        # ---- Main Scrollable Container ----
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Input Section
        self._section_header(main_container, "01", "Sumber Video")
        input_card = ctk.CTkFrame(
            main_container,
            fg_color=theme.SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=theme.BORDER
        )
        input_card.pack(fill="x", pady=(8, 18))

        input_row = ctk.CTkFrame(input_card, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=14)

        self.source_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Pilih file video atau tempel URL YouTube / TikTok...",
            placeholder_text_color=theme.TEXT_FAINT,
            fg_color=theme.SURFACE_ALT,
            border_color=theme.BORDER,
            text_color=theme.TEXT,
            font=ctk.CTkFont(size=13),
            height=38,
            corner_radius=6
        )
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            input_row,
            text="Browse Video",
            width=120,
            height=38,
            fg_color="transparent",
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.TEXT,
            hover_color=theme.HOVER,
            corner_radius=6,
            command=self.browse_file
        )
        browse_btn.pack(side="right")

        # 2. Options Section
        self._section_header(main_container, "02", "Konfigurasi Klip")
        opts_card = ctk.CTkFrame(
            main_container,
            fg_color=theme.SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=theme.BORDER
        )
        opts_card.pack(fill="x", pady=(8, 18))

        opts_row = ctk.CTkFrame(opts_card, fg_color="transparent")
        opts_row.pack(fill="x", padx=14, pady=14)

        ctk.CTkLabel(
            opts_row,
            text="Jumlah Klip",
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))
        self.num_clips_spin = self._entry(opts_row, width=70)
        self.num_clips_spin.insert(0, str(self.settings_mgr.data['clip_settings'].get('num_clips', 3)))
        self.num_clips_spin.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(
            opts_row,
            text="Durasi (detik)",
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))
        self.duration_spin = self._entry(opts_row, width=70)
        self.duration_spin.insert(0, str(self.settings_mgr.data['clip_settings'].get('target_duration', 30)))
        self.duration_spin.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(
            opts_row,
            text="Aspect Ratio",
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))
        self.ratio_var = ctk.StringVar(value=self.settings_mgr.data['clip_settings'].get('aspect_ratio', '9:16'))
        ctk.CTkOptionMenu(
            opts_row,
            values=["9:16", "1:1", "original"],
            variable=self.ratio_var,
            width=110,
            height=36,
            corner_radius=6,
            fg_color=theme.SURFACE_ALT,
            button_color=theme.SURFACE_ALT,
            button_hover_color=theme.HOVER,
            text_color=theme.TEXT,
            dropdown_fg_color=theme.SURFACE_ALT,
            dropdown_hover_color=theme.HOVER,
            dropdown_text_color=theme.TEXT,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        # 3. Action Button
        self.process_btn = ctk.CTkButton(
            main_container,
            text="Proses & Cari Momen Viral",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=6,
            fg_color=theme.ACCENT,
            text_color=theme.ACCENT_TEXT,
            hover_color=theme.ACCENT_HOVER,
            command=self.start_processing
        )
        self.process_btn.pack(fill="x", pady=(0, 18))

        # 4. Status Card
        status_card = ctk.CTkFrame(
            main_container,
            fg_color=theme.SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=theme.BORDER
        )
        status_card.pack(fill="x", pady=(0, 18))

        self.progress_bar = ctk.CTkProgressBar(
            status_card,
            height=4,
            fg_color=theme.SURFACE_ALT,
            progress_color=theme.ACCENT,
            corner_radius=2
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=14, pady=(14, 10))

        self.status_lbl = ctk.CTkLabel(
            status_card,
            text="Masukkan file video atau tempel URL, lalu klik Proses.",
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED
        )
        self.status_lbl.pack(padx=14, pady=(0, 12), anchor="w")

        # 5. Results Section
        self._section_header(main_container, "03", "Hasil Klip")
        self.results_scroll = ctk.CTkScrollableFrame(
            main_container,
            fg_color=theme.SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=theme.BORDER,
            height=220
        )
        self.results_scroll.pack(fill="both", expand=True, pady=(8, 0))

    # ---- Helpers ----

    def _section_header(self, master, number: str, title: str):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(
            row,
            text=number,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.ACCENT
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            row,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme.TEXT
        ).pack(side="left")

    def _entry(self, master, width: int):
        return ctk.CTkEntry(
            master,
            width=width,
            height=36,
            justify="center",
            fg_color=theme.SURFACE_ALT,
            border_color=theme.BORDER,
            text_color=theme.TEXT,
            corner_radius=6,
            font=ctk.CTkFont(size=13)
        )

    # ---- Behavior ----

    def update_provider_badge(self):
        active = self.settings_mgr.data.get("active_provider", "ollama")
        prov_name = self.settings_mgr.data.get("providers", {}).get(active, {}).get("name", active)
        self.badge_lbl.configure(text=f"AI: {prov_name}")

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings_mgr)
        self.wait_window(dialog)
        self.update_provider_badge()

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Pilih File Video Input",
            filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi *.webm"), ("All Files", "*.*")]
        )
        if filename:
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, filename)

    def set_status(self, message: str, progress: float = None):
        self.status_lbl.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress)

    def start_processing(self):
        if self.is_processing:
            return

        source = self.source_entry.get().strip()
        if not source:
            messagebox.showwarning("Peringatan", "Silakan masukkan path file video atau URL video terlebih dahulu!")
            return

        try:
            num_clips = int(self.num_clips_spin.get())
            duration = int(self.duration_spin.get())
        except ValueError:
            messagebox.showerror("Error", "Jumlah klip dan durasi harus berupa angka integer valid!")
            return

        self.is_processing = True
        self.process_btn.configure(state="disabled", fg_color=theme.SURFACE_ALT, text_color=theme.TEXT_FAINT)

        for child in self.results_scroll.winfo_children():
            child.destroy()

        thread = threading.Thread(
            target=self._run_pipeline,
            args=(source, num_clips, duration, self.ratio_var.get()),
            daemon=True
        )
        thread.start()

    def _run_pipeline(self, source: str, num_clips: int, duration: int, aspect_ratio: str):
        try:
            self.set_status("Menyiapkan video...", 0.05)
            downloader = VideoDownloader()
            video_path = downloader.prepare_video(
                source,
                progress_callback=lambda msg: self.set_status(msg, 0.15)
            )

            self.set_status("Mengekstrak audio dan membuat transkrip...", 0.25)
            transcriber = VideoTranscriber()
            segments = transcriber.transcribe(
                video_path,
                model_size="base",
                progress_callback=lambda msg: self.set_status(msg, 0.40)
            )

            self.set_status("Menganalisis momen viral...", 0.55)
            active_prov_key = self.settings_mgr.data.get("active_provider", "ollama")
            prov_cfg = self.settings_mgr.get_active_provider_config()
            ai_provider = ProviderFactory.get_provider(active_prov_key, prov_cfg)

            detector = MomentDetector(ai_provider)
            detected_clips = detector.detect_viral_moments(
                video_path=video_path,
                segments=segments,
                num_clips=num_clips,
                target_duration=duration,
                progress_callback=lambda msg: self.set_status(msg, 0.70)
            )

            self.set_status("Memotong dan meng-export klip...", 0.85)
            out_dir = self.settings_mgr.data['clip_settings'].get('output_dir', 'output_clips')
            clipper = VideoClipper(output_dir=out_dir)

            output_files = clipper.process_all_clips(
                video_path=video_path,
                clips=detected_clips,
                aspect_ratio=aspect_ratio,
                progress_callback=lambda msg: self.set_status(msg, 0.90)
            )

            self.set_status(f"Selesai. {len(output_files)} video klip berhasil dibuat di folder output.", 1.0)

            self.after(0, lambda: self._display_results(detected_clips, output_files))

        except Exception as e:
            self.set_status(f"Error selama pemrosesan: {str(e)}", 0.0)
            self.after(0, lambda: messagebox.showerror("Pipeline Error", str(e)))
        finally:
            self.is_processing = False
            self.after(0, lambda: self.process_btn.configure(
                state="normal", fg_color=theme.ACCENT, text_color=theme.ACCENT_TEXT
            ))

    def _display_results(self, clips: list, output_files: list):
        for i, clip in enumerate(clips):
            file_path = output_files[i] if i < len(output_files) else ""
            card = ClipCardWidget(self.results_scroll, clip_info=clip, file_path=file_path)
            card.pack(fill="x", pady=6, padx=6)
