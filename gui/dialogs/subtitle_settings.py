from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, 
    QSpinBox, QPushButton, QLabel, QColorDialog, QCheckBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

class SubtitleSettingsDialog(QDialog):
    def __init__(self, current_settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Subtitle Settings")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background-color: #0F0C1C; color: #ECE9F7;")
        
        if current_settings is None:
            self.settings = {
                "language": "id",
                "font_family": "Arial",
                "font_size": 48,
                "text_color": "#ffffff",
                "highlight_color": "#ffea00",
                "bg_color": "transparent",
                "position": "center",
                "style_bold": True,
                "style_italic": False,
                "stroke": True,
                "animation": "word_highlight"
            }
        else:
            self.settings = current_settings.copy()

        layout = QVBoxLayout(self)
        
        title = QLabel("Subtitle / Captions Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        form = QFormLayout()
        
        # Language
        self.lang_cb = QComboBox()
        self.lang_cb.addItems(["Auto Detect", "Indonesia (id)", "English (en)", "Japanese (ja)"])
        lang_code = self.settings.get("language", "auto")
        if lang_code == "auto":
            self.lang_cb.setCurrentIndex(0)
        elif lang_code == "id":
            self.lang_cb.setCurrentIndex(1)
        elif lang_code == "en":
            self.lang_cb.setCurrentIndex(2)
        elif lang_code == "ja":
            self.lang_cb.setCurrentIndex(3)
        else:
            self.lang_cb.setCurrentIndex(0)
        form.addRow("Language:", self.lang_cb)
        
        # Font Family
        self.font_cb = QComboBox()
        self.font_cb.addItems(["Arial", "Helvetica", "Inter", "Poppins", "Impact", "Montserrat"])
        self.font_cb.setCurrentText(self.settings.get("font_family", "Arial"))
        form.addRow("Font Family:", self.font_cb)
        
        # Font Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(20, 120)
        self.size_spin.setValue(self.settings.get("font_size", 48))
        form.addRow("Font Size:", self.size_spin)
        
        # Text Color
        self.btn_text_color = QPushButton("Pick Color")
        self.btn_text_color.setStyleSheet(f"background-color: {self.settings.get('text_color')}; color: black;")
        self.btn_text_color.clicked.connect(lambda: self.pick_color("text_color", self.btn_text_color))
        form.addRow("Text Color:", self.btn_text_color)
        
        # Highlight Color
        self.btn_hl_color = QPushButton("Pick Color")
        self.btn_hl_color.setStyleSheet(f"background-color: {self.settings.get('highlight_color')}; color: black;")
        self.btn_hl_color.clicked.connect(lambda: self.pick_color("highlight_color", self.btn_hl_color))
        form.addRow("Highlight Color:", self.btn_hl_color)
        
        # Position
        self.pos_cb = QComboBox()
        self.pos_cb.addItems(["Top", "Center", "Bottom"])
        self.pos_cb.setCurrentText(self.settings.get("position", "center").capitalize())
        form.addRow("Position:", self.pos_cb)
        
        # Animation
        self.anim_cb = QComboBox()
        self.anim_cb.addItems(["Word Highlight (Opus Style)", "Fade In", "Pop", "None"])
        anim = self.settings.get("animation", "word_highlight")
        if anim == "word_highlight": self.anim_cb.setCurrentIndex(0)
        elif anim == "fade": self.anim_cb.setCurrentIndex(1)
        elif anim == "pop": self.anim_cb.setCurrentIndex(2)
        else: self.anim_cb.setCurrentIndex(3)
        form.addRow("Animation:", self.anim_cb)

        # Styling checkboxes
        style_layout = QHBoxLayout()
        self.chk_bold = QCheckBox("Bold")
        self.chk_bold.setChecked(self.settings.get("style_bold", True))
        self.chk_italic = QCheckBox("Italic")
        self.chk_italic.setChecked(self.settings.get("style_italic", False))
        self.chk_stroke = QCheckBox("Outline/Stroke")
        self.chk_stroke.setChecked(self.settings.get("stroke", True))
        style_layout.addWidget(self.chk_bold)
        style_layout.addWidget(self.chk_italic)
        style_layout.addWidget(self.chk_stroke)
        form.addRow("Style:", style_layout)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def pick_color(self, key, button):
        initial = QColor(self.settings.get(key, "#ffffff"))
        color = QColorDialog.getColor(initial, self, "Pick Color")
        if color.isValid():
            hex_color = color.name()
            self.settings[key] = hex_color
            button.setStyleSheet(f"background-color: {hex_color}; color: black;")

    def save_settings(self):
        self.settings["font_family"] = self.font_cb.currentText()
        self.settings["font_size"] = self.size_spin.value()
        self.settings["position"] = self.pos_cb.currentText().lower()
        
        anim_text = self.anim_cb.currentText()
        if "Word Highlight" in anim_text: self.settings["animation"] = "word_highlight"
        elif "Fade" in anim_text: self.settings["animation"] = "fade"
        elif "Pop" in anim_text: self.settings["animation"] = "pop"
        else: self.settings["animation"] = "none"
        
        lang_text = self.lang_cb.currentText()
        if "Auto" in lang_text: self.settings["language"] = "auto"
        elif "Indonesia" in lang_text: self.settings["language"] = "id"
        elif "English" in lang_text: self.settings["language"] = "en"
        elif "Japanese" in lang_text: self.settings["language"] = "ja"
        
        self.settings["style_bold"] = self.chk_bold.isChecked()
        self.settings["style_italic"] = self.chk_italic.isChecked()
        self.settings["stroke"] = self.chk_stroke.isChecked()
        
        self.accept()
        
    def get_settings(self):
        return self.settings
