import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.waveform_data = []
        self.current_position = 0.0 # 0.0 to 1.0

    def set_waveform_data(self, data):
        """
        Set waveform data (normalized 0.0 to 1.0)
        """
        self.waveform_data = data
        self.update()

    def set_position(self, pos):
        """
        Set playback position (0.0 to 1.0)
        """
        self.current_position = pos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#161226"))
        
        if not self.waveform_data:
            return
            
        width = self.width()
        height = self.height()
        
        # Draw waveform
        pen_played = QPen(QColor("#8B5CF6")) # Played color
        pen_played.setWidth(2)
        
        pen_unplayed = QPen(QColor("#4A4265")) # Unplayed color
        pen_unplayed.setWidth(2)
        
        num_points = min(width // 3, len(self.waveform_data))
        if num_points == 0:
            return
            
        step_x = width / num_points
        
        # Simple resampling for visual display
        indices = np.linspace(0, len(self.waveform_data) - 1, num_points, dtype=int)
        sampled_data = [self.waveform_data[i] for i in indices]
        
        split_x = width * self.current_position

        for i, val in enumerate(sampled_data):
            x = int(i * step_x)
            bar_height = int(val * height)
            y = (height - bar_height) // 2
            
            if x <= split_x:
                painter.setPen(pen_played)
            else:
                painter.setPen(pen_unplayed)
                
            painter.drawLine(x, y, x, y + bar_height)
