import os
import time
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QComboBox,
    QPushButton, QSlider, QCheckBox, QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from core.tts_engine import TTSEngine
from core.audio_mixer import AudioMixer
from config.settings import SettingsManager
from gui.widgets.dark_combo_box import DarkComboBox


class TTSWorkerThread(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, provider_idx: int, text: str, voice_code: str, rate_str: str, api_key: str, base_url: str):
        super().__init__()
        self.provider_idx = provider_idx
        self.text = text
        self.voice_code = voice_code
        self.rate_str = rate_str
        self.api_key = api_key
        self.base_url = base_url

    def run(self):
        try:
            out_dir = os.path.join(os.getcwd(), "output_audio")
            os.makedirs(out_dir, exist_ok=True)
            timestamp = int(time.time())
            out_path = os.path.join(out_dir, f"voice_{timestamp}.mp3")

            if self.provider_idx == 0:
                TTSEngine.generate_edge_tts_sync(
                    text=self.text,
                    voice=self.voice_code,
                    rate=self.rate_str,
                    output_path=out_path
                )
            else:
                TTSEngine.generate_openai_tts(
                    text=self.text,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    output_path=out_path
                )
            self.finished_signal.emit(out_path)
        except Exception as e:
            self.error_signal.emit(str(e))


class AudioExportWorkerThread(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, voice_path: str, bgm_path: str, video_path: str, bgm_vol: float, use_ducking: bool):
        super().__init__()
        self.voice_path = voice_path
        self.bgm_path = bgm_path
        self.video_path = video_path
        self.bgm_vol = bgm_vol
        self.use_ducking = use_ducking

    def run(self):
        try:
            out_dir = os.path.join(os.getcwd(), "output_audio")
            os.makedirs(out_dir, exist_ok=True)
            timestamp = int(time.time())

            if self.bgm_path and os.path.exists(self.bgm_path):
                mixed_audio = os.path.join(out_dir, f"mixed_voice_{timestamp}.mp3")
                AudioMixer.mix_voice_and_bgm(
                    voice_path=self.voice_path,
                    bgm_path=self.bgm_path,
                    output_path=mixed_audio,
                    bgm_vol=self.bgm_vol,
                    enable_ducking=self.use_ducking
                )
            else:
                mixed_audio = self.voice_path

            if self.video_path and os.path.exists(self.video_path):
                final_video = os.path.join(out_dir, f"voiceover_video_{timestamp}.mp4")
                AudioMixer.merge_audio_with_video(
                    video_path=self.video_path,
                    audio_path=mixed_audio,
                    output_path=final_video,
                    replace_original_audio=True
                )
                out_res = final_video
            else:
                out_res = mixed_audio

            self.finished_signal.emit(out_res)
        except Exception as e:
            self.error_signal.emit(str(e))


class VoiceoverWorkspaceWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_mgr = SettingsManager()
        self.generated_voice_path = ""
        self.bgm_file_path = ""
        self.video_file_path = ""
        self.tts_thread = None
        self.export_thread = None

        # Audio Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.init_ui()
        self.setup_player_events()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(139, 92, 246, 0.2);
                color: #a78bfa;
                font-weight: bold;
                border: 1px solid rgba(139, 92, 246, 0.4);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #8b5cf6;
                color: white;
            }
        """)
        back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(back_btn)

        title_lbl = QLabel("🎙️ Voiceover & Audio Studio")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # ── Scroll Area ──────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # ── LEFT COLUMN: Text-to-Speech Generator ─────────────────────────
        left_card = QFrame()
        left_card.setStyleSheet("background-color: #1a1a2e; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)

        sec1_title = QLabel("1. 📝 Text Script & AI Voice")
        sec1_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #a78bfa;")
        left_layout.addWidget(sec1_title)

        # Provider Selector
        prov_layout = QHBoxLayout()
        prov_lbl = QLabel("TTS Engine:")
        prov_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.provider_combo = DarkComboBox()
        self.provider_combo.addItems(["Edge Neural TTS (Free / Offline)", "OpenAI TTS (API Key)"])
        self.provider_combo.setStyleSheet("background-color: #0f0f1e; color: #e2e8f0; padding: 6px; border-radius: 6px;")
        prov_layout.addWidget(prov_lbl)
        prov_layout.addWidget(self.provider_combo, stretch=1)
        left_layout.addLayout(prov_layout)

        # Voice Selector
        voice_layout = QHBoxLayout()
        voice_lbl = QLabel("Voice:")
        voice_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.voice_combo = DarkComboBox()
        self.populate_voices()
        self.voice_combo.setStyleSheet("background-color: #0f0f1e; color: #e2e8f0; padding: 6px; border-radius: 6px;")
        voice_layout.addWidget(voice_lbl)
        voice_layout.addWidget(self.voice_combo, stretch=1)
        left_layout.addLayout(voice_layout)

        # Speed / Rate Slider
        rate_layout = QHBoxLayout()
        rate_title_lbl = QLabel("Speech Speed:")
        rate_title_lbl.setStyleSheet("color: #94a3b8;")
        self.rate_val_lbl = QLabel("1.0x (Normal)")
        self.rate_val_lbl.setStyleSheet("color: #38bdf8; font-weight: 600;")
        rate_layout.addWidget(rate_title_lbl)
        rate_layout.addStretch()
        rate_layout.addWidget(self.rate_val_lbl)
        left_layout.addLayout(rate_layout)

        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_slider.valueChanged.connect(self.on_rate_changed)
        left_layout.addWidget(self.rate_slider)

        # Script Text Edit
        script_lbl = QLabel("Script Text:")
        script_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        left_layout.addWidget(script_lbl)

        self.script_edit = QTextEdit()
        self.script_edit.setPlaceholderText("Type or paste your text script here to convert into AI speech...")
        self.script_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0f0f1e;
                color: #f8fafc;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        left_layout.addWidget(self.script_edit, stretch=1)

        # Generate Button
        self.gen_btn = QPushButton("✨ Generate Voiceover")
        self.gen_btn.setMinimumHeight(42)
        self.gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                font-weight: 700;
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.gen_btn.clicked.connect(self.generate_voiceover)
        left_layout.addWidget(self.gen_btn)

        self.status_lbl = QLabel("Status: Ready")
        self.status_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
        left_layout.addWidget(self.status_lbl)

        content_layout.addWidget(left_card, stretch=1)

        # ── RIGHT COLUMN: Audio Studio, BGM & Export ──────────────────────
        right_card = QFrame()
        right_card.setStyleSheet("background-color: #1a1a2e; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(14)

        sec2_title = QLabel("2. 🎛️ Audio Mixing & BGM Studio")
        sec2_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        right_layout.addWidget(sec2_title)

        # Player & Download Box
        player_box = QFrame()
        player_box.setStyleSheet("background-color: #0f0f1e; border-radius: 8px; padding: 12px;")
        player_box_layout = QVBoxLayout(player_box)
        player_box_layout.setSpacing(10)

        player_btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶️ Play Audio")
        self.play_btn.setEnabled(False)
        self.play_btn.setMinimumHeight(38)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        player_btn_layout.addWidget(self.play_btn, stretch=1)

        self.save_voice_btn = QPushButton("💾 Download Voice MP3")
        self.save_voice_btn.setEnabled(False)
        self.save_voice_btn.setMinimumHeight(38)
        self.save_voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.save_voice_btn.clicked.connect(self.save_voiceover_file)
        player_btn_layout.addWidget(self.save_voice_btn)

        player_box_layout.addLayout(player_btn_layout)

        self.audio_pos_lbl = QLabel("00:00 / 00:00")
        self.audio_pos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_pos_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        player_box_layout.addWidget(self.audio_pos_lbl)

        right_layout.addWidget(player_box)

        # Background Music Selector
        bgm_lbl = QLabel("Background Music (Optional):")
        bgm_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        right_layout.addWidget(bgm_lbl)

        bgm_row = QHBoxLayout()
        self.bgm_path_lbl = QLabel("No BGM selected")
        self.bgm_path_lbl.setStyleSheet("color: #64748b; background: #0f0f1e; padding: 6px; border-radius: 6px;")
        bgm_btn = QPushButton("📁 Browse BGM")
        bgm_btn.setStyleSheet("background-color: rgba(255,255,255,0.08); color: #e2e8f0; border-radius: 6px; padding: 6px 12px;")
        bgm_btn.clicked.connect(self.browse_bgm)
        bgm_row.addWidget(self.bgm_path_lbl, stretch=1)
        bgm_row.addWidget(bgm_btn)
        right_layout.addLayout(bgm_row)

        # BGM Volume & Ducking
        bgm_vol_layout = QHBoxLayout()
        bgm_vol_layout.addWidget(QLabel("BGM Volume:"))
        self.bgm_vol_lbl = QLabel("25%")
        self.bgm_vol_lbl.setStyleSheet("color: #facc15; font-weight: bold;")
        bgm_vol_layout.addStretch()
        bgm_vol_layout.addWidget(self.bgm_vol_lbl)
        right_layout.addLayout(bgm_vol_layout)

        self.bgm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bgm_slider.setRange(0, 100)
        self.bgm_slider.setValue(25)
        self.bgm_slider.valueChanged.connect(lambda v: self.bgm_vol_lbl.setText(f"{v}%"))
        right_layout.addWidget(self.bgm_slider)

        self.ducking_chk = QCheckBox("⚡ Smart Auto-Ducking (Dampen BGM when voice plays)")
        self.ducking_chk.setChecked(True)
        self.ducking_chk.setStyleSheet("color: #4ade80; font-weight: 600;")
        right_layout.addWidget(self.ducking_chk)

        # Video Merge Options
        video_lbl = QLabel("Merge to Video File (Optional):")
        video_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        right_layout.addWidget(video_lbl)

        vid_row = QHBoxLayout()
        self.video_path_lbl = QLabel("No Video selected")
        self.video_path_lbl.setStyleSheet("color: #64748b; background: #0f0f1e; padding: 6px; border-radius: 6px;")
        vid_btn = QPushButton("🎬 Browse Video")
        vid_btn.setStyleSheet("background-color: rgba(255,255,255,0.08); color: #e2e8f0; border-radius: 6px; padding: 6px 12px;")
        vid_btn.clicked.connect(self.browse_video)
        vid_row.addWidget(self.video_path_lbl, stretch=1)
        vid_row.addWidget(vid_btn)
        right_layout.addLayout(vid_row)

        right_layout.addStretch()

        # Final Export Button
        self.export_btn = QPushButton("💾 Mix & Export Audio / Video")
        self.export_btn.setMinimumHeight(44)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.export_btn.clicked.connect(self.mix_and_export)
        right_layout.addWidget(self.export_btn)

        content_layout.addWidget(right_card, stretch=1)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def populate_voices(self):
        self.voice_combo.clear()
        voices = TTSEngine.list_popular_voices()
        for v in voices:
            self.voice_combo.addItem(v["name"], v["short_name"])

    def on_rate_changed(self, val):
        mult = val / 100.0
        self.rate_val_lbl.setText(f"{mult:.1f}x")

    def generate_voiceover(self):
        text = self.script_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter a text script first!")
            return

        # Stop player and clear source before generating new audio
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.play_btn.setText("▶️ Play Audio")
        self.play_btn.setEnabled(False)
        self.save_voice_btn.setEnabled(False)

        voice_code = self.voice_combo.currentData()
        rate_val = self.rate_slider.value()
        rate_str = f"{rate_val - 100:+d}%"
        prov_idx = self.provider_combo.currentIndex()
        router_cfg = self.settings_mgr.data.get("providers", {}).get("9router", {})
        api_key = router_cfg.get("api_key", "")
        base_url = router_cfg.get("base_url", "https://openrouter.ai/api/v1")

        self.gen_btn.setEnabled(False)
        self.status_lbl.setText("Generating AI Voiceover...")

        # Run via QThread to safely execute without threading/Qt crashes
        self.tts_thread = TTSWorkerThread(
            provider_idx=prov_idx,
            text=text,
            voice_code=voice_code,
            rate_str=rate_str,
            api_key=api_key,
            base_url=base_url
        )
        self.tts_thread.finished_signal.connect(self.on_tts_finished)
        self.tts_thread.error_signal.connect(self.on_tts_error)
        self.tts_thread.start()

    def on_tts_finished(self, out_path: str):
        self.gen_btn.setEnabled(True)
        self.generated_voice_path = out_path
        self.status_lbl.setText("✅ Voiceover generated successfully!")
        self.play_btn.setEnabled(True)
        self.save_voice_btn.setEnabled(True)

        # Set media source safely on main thread
        self.media_player.setSource(QUrl.fromLocalFile(out_path))

    def on_tts_error(self, err_msg: str):
        self.gen_btn.setEnabled(True)
        self.status_lbl.setText(f"❌ Error: {err_msg}")
        QMessageBox.critical(self, "TTS Error", f"Failed to generate voiceover:\n{err_msg}")

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶️ Play Audio")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸️ Pause Audio")

    def save_voiceover_file(self):
        if not self.generated_voice_path or not os.path.exists(self.generated_voice_path):
            QMessageBox.warning(self, "Warning", "No voiceover file has been generated yet!")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Voiceover MP3",
            "voiceover_ai.mp3",
            "Audio Files (*.mp3)"
        )
        if save_path:
            try:
                shutil.copy2(self.generated_voice_path, save_path)
                QMessageBox.information(self, "Success", f"Voiceover file saved successfully to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def setup_player_events(self):
        def _pos_changed(pos):
            dur = self.media_player.duration()
            if dur > 0:
                cur_sec = pos // 1000
                tot_sec = dur // 1000
                self.audio_pos_lbl.setText(f"{cur_sec//60:02d}:{cur_sec%60:02d} / {tot_sec//60:02d}:{tot_sec%60:02d}")

        self.media_player.positionChanged.connect(_pos_changed)

    def browse_bgm(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select BGM Audio", "", "Audio Files (*.mp3 *.wav *.m4a *.aac)")
        if file_path:
            self.bgm_file_path = file_path
            self.bgm_path_lbl.setText(os.path.basename(file_path))

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.mov *.avi)")
        if file_path:
            self.video_file_path = file_path
            self.video_path_lbl.setText(os.path.basename(file_path))

    def mix_and_export(self):
        if not self.generated_voice_path or not os.path.exists(self.generated_voice_path):
            QMessageBox.warning(self, "Warning", "Please generate a voiceover first!")
            return

        self.export_btn.setEnabled(False)
        self.status_lbl.setText("Mixing and exporting audio/video...")

        bgm_vol = self.bgm_slider.value() / 100.0
        use_ducking = self.ducking_chk.isChecked()

        self.export_thread = AudioExportWorkerThread(
            voice_path=self.generated_voice_path,
            bgm_path=self.bgm_file_path,
            video_path=self.video_file_path,
            bgm_vol=bgm_vol,
            use_ducking=use_ducking
        )
        self.export_thread.finished_signal.connect(self.on_export_finished)
        self.export_thread.error_signal.connect(self.on_export_error)
        self.export_thread.start()

    def on_export_finished(self, out_res: str):
        self.export_btn.setEnabled(True)
        self.status_lbl.setText(f"✅ Exported: {os.path.basename(out_res)}")
        QMessageBox.information(self, "Success", f"File exported successfully to:\n{out_res}")

    def on_export_error(self, err_msg: str):
        self.export_btn.setEnabled(True)
        self.status_lbl.setText(f"❌ Export Error: {err_msg}")
        QMessageBox.critical(self, "Export Error", f"Failed to export file:\n{err_msg}")
