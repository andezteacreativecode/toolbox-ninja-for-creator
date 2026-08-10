import os
import subprocess
import customtkinter as ctk
from gui import theme


class ClipCardWidget(ctk.CTkFrame):
    def __init__(self, master, clip_info: dict, file_path: str = "", **kwargs):
        super().__init__(master, **kwargs)

        self.clip_info = clip_info
        self.file_path = file_path

        self.configure(
            fg_color=theme.SURFACE_ALT,
            corner_radius=8,
            border_width=1,
            border_color=theme.BORDER
        )

        title_text = clip_info.get('title', 'Clip')
        score = clip_info.get('score', 85.0)

        # Top row: Title + Score badge
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            title_row,
            text=title_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            text_color=theme.TEXT
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_row,
            text=f"Skor {score:.0f}",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=theme.ACCENT_SOFT,
            corner_radius=999,
            padx=8,
            pady=2,
            text_color=theme.ACCENT
        ).pack(side="right")

        # Time range & duration
        start = clip_info.get('start', 0)
        end = clip_info.get('end', 30)
        dur = clip_info.get('duration', end - start)

        def fmt(seconds):
            seconds = int(seconds)
            return f"{seconds // 60:02d}:{seconds % 60:02d}"

        info_str = f"{fmt(start)} \u2013 {fmt(end)}  \u00b7  {dur:.1f} dtk"
        ctk.CTkLabel(
            self,
            text=info_str,
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color=theme.TEXT_MUTED
        ).pack(fill="x", padx=12, pady=(0, 4))

        # Reason
        reason = clip_info.get('reason', '')
        if reason:
            ctk.CTkLabel(
                self,
                text=reason,
                font=ctk.CTkFont(size=11, slant="italic"),
                anchor="w",
                text_color=theme.TEXT_FAINT,
                wraplength=460,
                justify="left"
            ).pack(fill="x", padx=12, pady=(0, 8))

        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        if self.file_path and os.path.exists(self.file_path):
            play_btn = ctk.CTkButton(
                btn_frame,
                text="Putar Video",
                width=110,
                height=30,
                corner_radius=6,
                fg_color="transparent",
                border_width=1,
                border_color=theme.ACCENT,
                text_color=theme.ACCENT,
                hover_color=theme.ACCENT_SOFT,
                command=self.open_video
            )
            play_btn.pack(side="left", padx=(0, 8))

            folder_btn = ctk.CTkButton(
                btn_frame,
                text="Buka Folder",
                width=110,
                height=30,
                corner_radius=6,
                fg_color="transparent",
                border_width=1,
                border_color=theme.BORDER,
                text_color=theme.TEXT_MUTED,
                hover_color=theme.HOVER,
                command=self.open_folder
            )
            folder_btn.pack(side="left")

    def open_video(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                subprocess.Popen(["xdg-open", self.file_path])
            except Exception as e:
                print(f"Error opening video: {e}")

    def open_folder(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                folder = os.path.dirname(self.file_path)
                subprocess.Popen(["xdg-open", folder])
            except Exception as e:
                print(f"Error opening folder: {e}")
