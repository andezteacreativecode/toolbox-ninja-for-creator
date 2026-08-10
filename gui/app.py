import sys
from PyQt6.QtWidgets import QApplication
from gui.styles import Styles

class ClipperApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setStyleSheet(Styles.get_qss())
        # Set app-wide font if needed here
