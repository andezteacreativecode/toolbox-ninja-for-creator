from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, Qt

class InputPanel(QFrame):
    # Emit hanya untuk file lokal (local path), bukan URL
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glass_panel")
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title_lbl = QLabel("Source Video & Target Topic")
        title_lbl.setObjectName("heading")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel("Select a local video file or paste a YouTube / TikTok link, then click 'Find Viral Moments'")
        desc_lbl.setObjectName("subheading")
        layout.addWidget(desc_lbl)

        input_layout = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Drag & drop a video file here, or paste YouTube / TikTok URL...")
        # Tidak emit file_selected saat teks berubah — hanya valid untuk local file
        input_layout.addWidget(self.source_input, stretch=1)

        browse_btn = QPushButton("Browse File")
        browse_btn.clicked.connect(self.browse_file)
        input_layout.addWidget(browse_btn)

        layout.addLayout(input_layout)

        # Topic / Niche input
        topic_layout = QHBoxLayout()
        topic_lbl = QLabel("Topik / Niche (Opsional):")
        topic_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #8B5CF6;")
        topic_layout.addWidget(topic_lbl)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Contoh: Edukasi Bisnis, Komedi, Motivasi, Tech Review, Kripto...")
        topic_layout.addWidget(self.topic_input, stretch=1)

        layout.addLayout(topic_layout)

    def get_topic(self) -> str:
        return self.topic_input.text().strip()

    def get_source(self) -> str:
        """Kembalikan path file lokal atau URL yang diketik user."""
        return self.source_input.text().strip()

    def browse_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.mov *.avi *.webm);;All Files (*)"
        )
        if fname:
            self.source_input.setText(fname)
            self.file_selected.emit(fname)  # load ke video player hanya untuk local file

    # Drag and Drop support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            self.source_input.setText(file_path)
            self.file_selected.emit(file_path)  # local file → load ke video player
