from PyQt6.QtWidgets import QComboBox, QFrame
from PyQt6.QtGui import QPalette, QColor

_DARK_VIEW_SS = (
    "QAbstractItemView {"
    "  background-color: #1a1a2e;"
    "  color: #e2e8f0;"
    "  selection-background-color: #8b5cf6;"
    "  selection-color: #ffffff;"
    "  border: 1px solid rgba(139, 92, 246, 0.4);"
    "  border-radius: 8px;"
    "  padding: 4px;"
    "  outline: none;"
    "}"
    "QAbstractItemView::item {"
    "  background-color: #1a1a2e;"
    "  color: #e2e8f0;"
    "  padding: 6px 12px;"
    "  min-height: 24px;"
    "  border-radius: 4px;"
    "}"
    "QAbstractItemView::item:selected {"
    "  background-color: #8b5cf6;"
    "  color: #ffffff;"
    "}"
    "QAbstractItemView::item:hover:!selected {"
    "  background-color: rgba(139, 92, 246, 0.25);"
    "  color: #ffffff;"
    "}"
    "QAbstractItemView::item:disabled {"
    "  background-color: #0f0f1e;"
    "  color: #a78bfa;"
    "  font-weight: bold;"
    "}"
)

_DARK_CONTAINER_SS = (
    "background-color: #1a1a2e;"
    "border: 1px solid rgba(139, 92, 246, 0.55);"
    "border-radius: 8px;"
)


class DarkComboBox(QComboBox):
    """
    QComboBox subclass that forces dark popup styling and removes
    the default white container frame around the popup menu.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_palette()

    def _setup_palette(self):
        pal = QPalette()
        dark = QColor("#1a1a2e")
        pal.setColor(QPalette.ColorRole.Base, dark)
        pal.setColor(QPalette.ColorRole.AlternateBase, dark)
        pal.setColor(QPalette.ColorRole.Window, dark)
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#e2e8f0"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#e2e8f0"))
        pal.setColor(QPalette.ColorRole.Highlight, QColor("#8b5cf6"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.setPalette(pal)
        self.view().setPalette(pal)
        self.view().setStyleSheet(_DARK_VIEW_SS)
        vp = self.view().viewport()
        vp.setAutoFillBackground(True)
        vp.setPalette(pal)

    def showPopup(self):
        super().showPopup()
        container = self.view().parentWidget()
        if container:
            container.setStyleSheet(_DARK_CONTAINER_SS)
            for child in container.findChildren(QFrame):
                child.setStyleSheet(
                    "QFrame { background-color: #1a1a2e; border: none; }"
                )
