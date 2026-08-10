import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QStyle
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, pyqtSignal

class VideoPlayerWidget(QWidget):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        self.layout.addWidget(self.video_widget, stretch=1)
        
        self.setup_controls()
        
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        
    def setup_controls(self):
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)
        
        self.time_lbl = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_lbl)
        
        self.layout.addLayout(controls_layout)
        
    def load_video(self, file_path):
        if os.path.exists(file_path):
            abs_path = os.path.abspath(file_path)
            self.media_player.setSource(QUrl.fromLocalFile(abs_path))
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.media_player.play()

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            
    def on_position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_time_label(position, self.media_player.duration())
        self.position_changed.emit(position)
        
    def on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_label(self.media_player.position(), duration)
        self.duration_changed.emit(duration)
        
    def set_position(self, position):
        self.media_player.setPosition(position)
        
    def update_time_label(self, position, duration):
        def format_time(ms):
            s = (ms // 1000) % 60
            m = (ms // 60000) % 60
            return f"{m:02}:{s:02}"
        self.time_lbl.setText(f"{format_time(position)} / {format_time(duration)}")
