# Design System and QSS Stylesheet for Clipper Desktop v2
#
# Refined editorial palette: warm charcoal surfaces with a single muted
# brass accent. Flat fills, hairline borders, no gradients — a deliberate
# departure from the saturated violet "AI look".

class Styles:
    COLORS = {
        "bg_main": "#0F0C1C",
        "bg_surface": "#161226",
        "bg_input": "#1E1832",
        "hover": "#2A2247",
        "glass": "rgba(255, 255, 255, 0.045)",
        "glass_hover": "rgba(255, 255, 255, 0.08)",
        "border": "rgba(255, 255, 255, 0.09)",
        "border_focus": "rgba(139, 92, 246, 0.55)",
        "accent": "#8B5CF6",          # muted brass
        "accent_hover": "#A78BFA",
        "accent_soft": "#241D3E",     # subtle brass tint for badges
        "accent_text": "#140F24",     # text placed on accent fills
        "success": "#8AC9A0",
        "danger": "#E58A7E",
        "text_main": "#ECE9F7",
        "text_muted": "#A7A0C4",
        "text_faint": "#6C6690"
    }

    @staticmethod
    def get_qss():
        return f"""
        QMainWindow {{
            background-color: {Styles.COLORS['bg_main']};
            color: {Styles.COLORS['text_main']};
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}

        QWidget {{
            background-color: {Styles.COLORS['bg_main']};
            color: {Styles.COLORS['text_main']};
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}

        QFrame {{
            background-color: {Styles.COLORS['bg_surface']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 10px;
        }}

        QFrame#glass_panel {{
            background-color: {Styles.COLORS['bg_surface']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 10px;
        }}

        QLabel {{
            border: none;
            background-color: transparent;
        }}

        QLabel#heading {{
            font-size: 16px;
            font-weight: 700;
        }}

        QLabel#subheading {{
            font-size: 13px;
            font-weight: 400;
            color: {Styles.COLORS['text_muted']};
        }}

        QPushButton {{
            background-color: {Styles.COLORS['bg_input']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 7px;
            padding: 8px 16px;
            font-weight: 600;
            color: {Styles.COLORS['text_main']};
        }}

        QPushButton:hover {{
            background-color: {Styles.COLORS['hover']};
            border: 1px solid {Styles.COLORS['border_focus']};
        }}

        QPushButton:disabled {{
            background-color: {Styles.COLORS['bg_input']};
            color: {Styles.COLORS['text_faint']};
        }}

        QPushButton#primary_btn {{
            background-color: {Styles.COLORS['accent']};
            color: {Styles.COLORS['accent_text']};
            border: none;
            border-radius: 7px;
            font-weight: 700;
            padding: 10px 20px;
        }}

        QPushButton#primary_btn:hover {{
            background-color: {Styles.COLORS['accent_hover']};
        }}

        QPushButton#primary_btn:disabled {{
            background-color: {Styles.COLORS['bg_input']};
            color: {Styles.COLORS['text_faint']};
        }}

        QLineEdit, QSpinBox, QComboBox {{
            background-color: {Styles.COLORS['bg_input']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 6px;
            padding: 8px 12px;
            color: {Styles.COLORS['text_main']};
            selection-background-color: {Styles.COLORS['accent']};
            selection-color: {Styles.COLORS['accent_text']};
        }}

        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid {Styles.COLORS['accent']};
            background-color: {Styles.COLORS['bg_surface']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {Styles.COLORS['bg_input']};
            color: {Styles.COLORS['text_main']};
            selection-background-color: {Styles.COLORS['accent']};
            selection-color: {Styles.COLORS['accent_text']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 4px;
        }}

        QProgressBar {{
            background-color: {Styles.COLORS['bg_input']};
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 3px;
            text-align: center;
            height: 8px;
        }}

        QProgressBar::chunk {{
            background-color: {Styles.COLORS['accent']};
            border-radius: 3px;
        }}

        QScrollBar:vertical {{
            border: none;
            background: {Styles.COLORS['bg_main']};
            width: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {Styles.COLORS['hover']};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}

        QScrollArea {{
            border: none;
            background-color: transparent;
        }}

        QTabWidget::pane {{
            border: 1px solid {Styles.COLORS['border']};
            background-color: {Styles.COLORS['bg_surface']};
            border-radius: 8px;
            top: -1px;
        }}

        QTabBar::tab {{
            background-color: {Styles.COLORS['bg_main']};
            color: {Styles.COLORS['text_muted']};
            padding: 8px 16px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border: 1px solid {Styles.COLORS['border']};
            border-bottom: none;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {Styles.COLORS['bg_surface']};
            color: {Styles.COLORS['accent']};
            font-weight: 700;
        }}

        QTabBar::tab:hover:!selected {{
            color: {Styles.COLORS['text_main']};
        }}

        QSlider::groove:horizontal {{
            border: 1px solid {Styles.COLORS['border']};
            height: 6px;
            background: {Styles.COLORS['bg_input']};
            margin: 2px 0;
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background: {Styles.COLORS['accent']};
            border: 1px solid {Styles.COLORS['accent']};
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}

        QGroupBox {{
            border: 1px solid {Styles.COLORS['border']};
            border-radius: 8px;
            margin-top: 14px;
            padding-top: 8px;
            font-weight: 700;
            color: {Styles.COLORS['accent']};
            background-color: transparent;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 6px;
        }}
        """
