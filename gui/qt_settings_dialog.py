import httpx
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, QLineEdit,
    QComboBox, QPushButton, QFormLayout, QGroupBox, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont, QPalette
from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory

from gui.widgets.dark_combo_box import DarkComboBox


# ─── Background thread untuk fetch model list ──────────────────────────────────
class ModelFetchThread(QThread):
    done = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, provider: str, base_url: str, api_key: str = ""):
        super().__init__()
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def run(self):
        try:
            if self.provider == "ollama":
                resp = httpx.get(f"{self.base_url}/api/tags", timeout=8.0)
                resp.raise_for_status()
                data = resp.json()
                models = data.get("models", [])
                names = [m.get("name", "") for m in models if m.get("name")]
                self.done.emit(names)
                return

            elif self.provider == "9router":
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/clipper-desktop",
                    "X-Title": "Clipper Desktop"
                }
                resp = httpx.get(f"{self.base_url}/models", headers=headers, timeout=12.0)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", data) if isinstance(data, dict) else data
                names = sorted(set(
                    m.get("id", m.get("name", ""))
                    for m in items
                    if m.get("id") or m.get("name")
                ))
                self.done.emit([n for n in names if n])
                return

        except httpx.ConnectError as e:
            self.error.emit(f"Tidak bisa terhubung: {e}")
        except httpx.HTTPStatusError as e:
            self.error.emit(f"HTTP {e.response.status_code}: {e.response.text[:120]}")
        except Exception as e:
            self.error.emit(str(e))


# ─── Full QSS ─────────────────────────────────────────────────────────────────
DIALOG_STYLE = """
QDialog {
    background-color: #0F0C1C;
    color: #ECE9F7;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
}
* {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
QTabWidget::pane {
    border: 1px solid rgba(255,255,255,0.09);
    background-color: #161226;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background-color: #1E1832;
    color: #A7A0C4;
    padding: 9px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid rgba(255,255,255,0.09);
    border-bottom: none;
    margin-right: 3px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #161226;
    color: #8B5CF6;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #2A2247;
    color: #ECE9F7;
}
QWidget {
    background-color: transparent;
    color: #ECE9F7;
}
QLabel {
    color: #B9B3D6;
    background: transparent;
    border: none;
}
QLineEdit {
    background-color: #1E1832;
    color: #ECE9F7;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 7px 11px;
    font-size: 13px;
    selection-background-color: #8B5CF6;
    selection-color: #140F24;
}
QLineEdit:focus {
    border: 1px solid #8B5CF6;
    background-color: #161226;
}
/* ── Provider selector ── */
QComboBox#provider_select {
    background-color: #1E1832;
    color: #ECE9F7;
    border: 1px solid rgba(139,92,246,0.4);
    border-radius: 8px;
    padding: 8px 36px 8px 12px;
    font-size: 13px;
    font-weight: 600;
    min-width: 160px;
}
QComboBox#provider_select:hover {
    border: 1px solid #8B5CF6;
    background-color: #161226;
}
QComboBox#provider_select::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 28px;
    border-left: 1px solid rgba(255,255,255,0.09);
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: #241D3E;
}
/* ── Generic combobox ── */
QComboBox {
    background-color: #1E1832;
    color: #ECE9F7;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 7px 36px 7px 11px;
    font-size: 13px;
}
QComboBox:focus {
    border: 1px solid #8B5CF6;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 26px;
    border-left: 1px solid rgba(255,255,255,0.09);
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #2A2247;
}
/* ── Dropdown popup ── */
QComboBox QAbstractItemView {
    background-color: #1E1832;
    color: #ECE9F7;
    selection-background-color: #8B5CF6;
    selection-color: #140F24;
    border: 1px solid rgba(139,92,246,0.4);
    border-radius: 6px;
    padding: 4px;
    outline: none;
    show-decoration-selected: 1;
}
QComboBox QAbstractItemView::item {
    background-color: #1E1832;
    color: #ECE9F7;
    padding: 6px 12px;
    min-height: 24px;
    border-radius: 3px;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #8B5CF6;
    color: #140F24;
}
QComboBox QAbstractItemView::item:hover {
    background-color: rgba(139,92,246,0.25);
    color: #ECE9F7;
}
/* Section header items in model list */
QComboBox QAbstractItemView::item:disabled {
    background-color: #161226;
    color: #A7A0C4;
    font-weight: bold;
    padding: 4px 8px;
    min-height: 20px;
}
QGroupBox {
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 8px;
    font-weight: bold;
    color: #8B5CF6;
    font-size: 13px;
    background-color: rgba(255,255,255,0.01);
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background-color: #161226;
}
QPushButton#btn_test {
    background-color: #1E1832;
    color: #A7A0C4;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#btn_test:hover {
    background-color: #2A2247;
    color: #ECE9F7;
    border: 1px solid #8B5CF6;
}
QPushButton#btn_save {
    background-color: #8B5CF6;
    color: #140F24;
    border: none;
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#btn_save:hover {
    background-color: #A78BFA;
}
QPushButton#btn_refresh {
    background-color: transparent;
    border: 1px solid rgba(139,92,246,0.35);
    color: #8B5CF6;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 600;
    min-width: 64px;
}
QPushButton#btn_refresh:hover {
    background-color: #241D3E;
    border: 1px solid #8B5CF6;
    color: #A78BFA;
}
QPushButton#btn_refresh:disabled {
    color: #6C6690;
    border-color: rgba(255,255,255,0.06);
}
QScrollBar:vertical {
    border: none;
    background: #0F0C1C;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4A4265;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}
"""


def _make_grouped_model(names: list) -> QStandardItemModel:
    """
    Build a QStandardItemModel with group headers (disabled items)
    based on the prefix before '/' in each model ID.
    """
    model = QStandardItemModel()
    from collections import defaultdict
    groups = defaultdict(list)
    for name in names:
        prefix = name.split("/")[0] if "/" in name else "other"
        groups[prefix].append(name)

    for prefix in sorted(groups.keys()):
        # Header
        header = QStandardItem(f"  \u2014\u2014 {prefix.upper()} \u2014\u2014")
        header.setEnabled(False)
        header.setForeground(QColor("#8B5CF6"))
        f = header.font()
        f.setBold(True)
        f.setPointSize(9)
        header.setFont(f)
        header.setBackground(QColor("#161226"))
        model.appendRow(header)

        for m in sorted(groups[prefix]):
            item = QStandardItem(f"  {m}")
            item.setForeground(QColor("#ECE9F7"))
            item.setBackground(QColor("#1E1832"))
            item.setData(m, Qt.ItemDataRole.UserRole)  # store raw id
            model.appendRow(item)

    return model


class QtSettingsDialog(QDialog):
    def __init__(self, settings_mgr: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_mgr = settings_mgr
        self.data = self.settings_mgr.data
        self._fetch_thread = None

        self.setWindowTitle("Settings \u2014 Clipper")
        self.setFixedSize(580, 580)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 14)
        root.setSpacing(10)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.tab_ai = QWidget()
        self.tab_ai.setStyleSheet("background-color: #161226;")
        self.tab_clip = QWidget()
        self.tab_clip.setStyleSheet("background-color: #161226;")

        self.tabs.addTab(self.tab_ai, "AI Providers")
        self.tabs.addTab(self.tab_clip, "Clips & Format")

        self.build_ai_tab()
        self.build_clip_tab()

        # Status bar
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #A7A0C4; font-size: 11px; padding: 0 2px;")
        self.status_lbl.setFixedHeight(18)
        root.addWidget(self.status_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        test_btn = QPushButton("Test Koneksi")
        test_btn.setObjectName("btn_test")
        test_btn.setFixedHeight(38)
        test_btn.clicked.connect(self.test_connection)
        btn_row.addWidget(test_btn)

        save_btn = QPushButton("Simpan")
        save_btn.setObjectName("btn_save")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self.save_settings)
        btn_row.addWidget(save_btn)

        root.addLayout(btn_row)

        # Auto-fetch Ollama models after all widgets are initialized
        self.fetch_ollama_models()

    # ──────────────────────────────────────────────────────────────────────────
    def build_ai_tab(self):
        outer = QVBoxLayout(self.tab_ai)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(10)

        # ── Provider selector ──────────────────────────────────────────────
        prov_frame = QFrame()
        prov_frame.setStyleSheet(
            "QFrame { background-color: #241D3E; "
            "border: 1px solid rgba(139,92,246,0.25); border-radius: 8px; }")
        pf_layout = QHBoxLayout(prov_frame)
        pf_layout.setContentsMargins(14, 10, 14, 10)

        prov_lbl = QLabel("Active Provider")
        prov_lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #ECE9F7; border:none;")
        pf_layout.addWidget(prov_lbl)
        pf_layout.addStretch()

        self.provider_combo = DarkComboBox()
        self.provider_combo.setObjectName("provider_select")
        self.provider_combo.addItems(["ollama", "9router"])
        self.provider_combo.setCurrentText(self.data.get("active_provider", "ollama"))
        self.provider_combo.setFixedHeight(36)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        pf_layout.addWidget(self.provider_combo)

        outer.addWidget(prov_frame)

        # ── Ollama panel ───────────────────────────────────────────────────
        self.ollama_group = QGroupBox("Ollama (Local)")
        o_form = QFormLayout(self.ollama_group)
        o_form.setSpacing(9)
        o_form.setContentsMargins(14, 20, 14, 14)

        self.ollama_url = QLineEdit(
            self.data['providers']['ollama'].get('base_url', 'http://localhost:11434'))
        self.ollama_url.setFixedHeight(34)
        o_form.addRow("Base URL:", self.ollama_url)

        model_row = QHBoxLayout()
        self.ollama_model_combo = DarkComboBox()
        self.ollama_model_combo.setEditable(True)
        self.ollama_model_combo.setFixedHeight(34)
        saved = self.data['providers']['ollama'].get('model', 'gemma2:2b')
        self.ollama_model_combo.addItem(saved)
        self.ollama_model_combo.setCurrentText(saved)
        model_row.addWidget(self.ollama_model_combo, stretch=1)

        self.btn_refresh_ollama = QPushButton("Refresh")
        self.btn_refresh_ollama.setObjectName("btn_refresh")
        self.btn_refresh_ollama.setFixedHeight(30)
        self.btn_refresh_ollama.clicked.connect(self.fetch_ollama_models)
        model_row.addWidget(self.btn_refresh_ollama)

        mw = QWidget()
        mw.setLayout(model_row)
        o_form.addRow("Model:", mw)
        outer.addWidget(self.ollama_group)

        # ── 9router panel ──────────────────────────────────────────────────
        self.router_group = QGroupBox("9router / OpenRouter API")
        r_form = QFormLayout(self.router_group)
        r_form.setSpacing(9)
        r_form.setContentsMargins(14, 20, 14, 14)

        self.router_url = QLineEdit(
            self.data['providers']['9router'].get('base_url', 'https://openrouter.ai/api/v1'))
        self.router_url.setFixedHeight(34)
        r_form.addRow("Base URL:", self.router_url)

        self.router_key = QLineEdit(self.data['providers']['9router'].get('api_key', ''))
        self.router_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.router_key.setPlaceholderText("sk-or-v1-...")
        self.router_key.setFixedHeight(34)
        r_form.addRow("API Key:", self.router_key)

        rmodel_row = QHBoxLayout()
        self.router_model_combo = DarkComboBox()
        self.router_model_combo.setEditable(True)
        self.router_model_combo.setFixedHeight(34)
        saved_r = self.data['providers']['9router'].get(
            'model', 'meta-llama/llama-3.1-8b-instruct:free')
        self.router_model_combo.addItem(saved_r)
        self.router_model_combo.setCurrentText(saved_r)
        rmodel_row.addWidget(self.router_model_combo, stretch=1)

        self.btn_refresh_router = QPushButton("Refresh")
        self.btn_refresh_router.setObjectName("btn_refresh")
        self.btn_refresh_router.setFixedHeight(30)
        self.btn_refresh_router.clicked.connect(self.fetch_router_models)
        rmodel_row.addWidget(self.btn_refresh_router)

        rw = QWidget()
        rw.setLayout(rmodel_row)
        r_form.addRow("Model:", rw)
        outer.addWidget(self.router_group)

        outer.addStretch()

        # Apply initial visibility
        self._on_provider_changed(self.provider_combo.currentText())

    def build_clip_tab(self):
        layout = QFormLayout(self.tab_clip)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        clip_conf = self.data.get("clip_settings", {})

        self.dur_input = QLineEdit(str(clip_conf.get("target_duration", 30)))
        self.dur_input.setFixedHeight(34)

        self.num_input = QLineEdit(str(clip_conf.get("num_clips", 3)))
        self.num_input.setFixedHeight(34)

        self.ratio_combo = DarkComboBox()
        self.ratio_combo.setFixedHeight(34)
        self.ratio_combo.addItems([
            "9:16  —  TikTok / Reels / Shorts (Vertical)",
            "1:1  —  Square (Instagram)",
            "Original  —  No Crop",
        ])
        cur_ratio = clip_conf.get("aspect_ratio", "9:16")
        if "1:1" in cur_ratio:
            self.ratio_combo.setCurrentIndex(1)
        elif "original" in cur_ratio:
            self.ratio_combo.setCurrentIndex(2)

        self.out_dir_input = QLineEdit(clip_conf.get("output_dir", ""))
        self.out_dir_input.setPlaceholderText("output_clips/  (default)")
        self.out_dir_input.setFixedHeight(34)

        layout.addRow("Target Duration per Clip (sec):", self.dur_input)
        layout.addRow("Default Number of Clips:", self.num_input)
        layout.addRow("Output Aspect Ratio:", self.ratio_combo)
        layout.addRow("Export Directory Path:", self.out_dir_input)

    # ── Provider toggle ────────────────────────────────────────────────────────
    def _on_provider_changed(self, provider: str):
        is_ollama = provider == "ollama"
        self.ollama_group.setVisible(is_ollama)
        self.router_group.setVisible(not is_ollama)

    # ── Fetch Ollama models ────────────────────────────────────────────────────
    def fetch_ollama_models(self):
        url = self.ollama_url.text().strip() or "http://localhost:11434"
        self._set_status("Fetching Ollama model list...", "#A7A0C4")
        self.btn_refresh_ollama.setEnabled(False)
        self.btn_refresh_ollama.setText("...")

        self._fetch_thread = ModelFetchThread("ollama", url)
        self._fetch_thread.done.connect(self._on_ollama_models)
        self._fetch_thread.error.connect(self._on_ollama_error)
        self._fetch_thread.start()

    def _on_ollama_models(self, names: list):
        self.btn_refresh_ollama.setEnabled(True)
        self.btn_refresh_ollama.setText("Refresh")
        current = self.ollama_model_combo.currentText()
        self.ollama_model_combo.clear()
        if names:
            self.ollama_model_combo.addItems(names)
            if current in names:
                self.ollama_model_combo.setCurrentText(current)
            else:
                self.ollama_model_combo.setCurrentIndex(0)
            self._set_status(f"{len(names)} Ollama models available", "#8AC9A0")
        else:
            self.ollama_model_combo.addItem(current or "gemma2:2b")
            self._set_status("Ollama connected but no models found — run: ollama pull <model>", "#A78BFA")

    def _on_ollama_error(self, err: str):
        self.btn_refresh_ollama.setEnabled(True)
        self.btn_refresh_ollama.setText("Refresh")
        current = self.ollama_model_combo.currentText()
        if not current:
            self.ollama_model_combo.addItem("gemma2:2b")
        self._set_status(f"Ollama unreachable — ensure 'ollama serve' is running  ({err})", "#E58A7E")

    # ── Fetch 9router models ───────────────────────────────────────────────────
    def fetch_router_models(self):
        url = self.router_url.text().strip() or "https://openrouter.ai/api/v1"
        key = self.router_key.text().strip()
        if not key:
            self._set_status("Enter an API key first, then click Refresh", "#A78BFA")
            return
        self._set_status("Fetching 9router / OpenRouter models...", "#A7A0C4")
        self.btn_refresh_router.setEnabled(False)
        self.btn_refresh_router.setText("...")

        self._fetch_thread = ModelFetchThread("9router", url, key)
        self._fetch_thread.done.connect(self._on_router_models)
        self._fetch_thread.error.connect(self._on_router_error)
        self._fetch_thread.start()

    def _on_router_models(self, names: list):
        self.btn_refresh_router.setEnabled(True)
        self.btn_refresh_router.setText("Refresh")
        current = self.router_model_combo.currentText()

        if names:
            # Build grouped model with section headers
            grouped_model = _make_grouped_model(names)
            self.router_model_combo.setModel(grouped_model)
            # Restore selection
            if current in names:
                self.router_model_combo.setCurrentText(current)
            else:
                # Set first non-header item
                for row in range(grouped_model.rowCount()):
                    item = grouped_model.item(row)
                    if item and item.isEnabled():
                        self.router_model_combo.setCurrentIndex(row)
                        break
            self._set_status(f"{len(names)} 9router/OpenRouter models available", "#8AC9A0")
        else:
            self._set_status("No models found from 9router", "#A78BFA")

    def _on_router_error(self, err: str):
        self.btn_refresh_router.setEnabled(True)
        self.btn_refresh_router.setText("Refresh")
        self._set_status(f"Failed to fetch 9router models: {err}", "#E58A7E")

    def _set_status(self, msg: str, color: str = "#A7A0C4"):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; padding: 0 2px;")

    # ── Test & Save ───────────────────────────────────────────────────────────
    def test_connection(self):
        active = self.provider_combo.currentText()
        if active == "ollama":
            cfg = {
                "name": "Ollama",
                "base_url": self.ollama_url.text().strip(),
                "model": self.ollama_model_combo.currentText().strip()
            }
        else:
            raw = self.router_model_combo.currentText().strip()
            # strip leading spaces added by grouping
            model_id = raw.strip()
            cfg = {
                "name": "9router",
                "base_url": self.router_url.text().strip(),
                "api_key": self.router_key.text().strip(),
                "model": model_id
            }
        try:
            prov = ProviderFactory.get_provider(active, cfg)
            ok, msg = prov.test_connection()
            if ok:
                self._set_status(msg, "#8AC9A0")
            else:
                self._set_status(msg, "#E58A7E")
        except Exception as e:
            self._set_status(str(e), "#E58A7E")

    def save_settings(self):
        active = self.provider_combo.currentText()
        self.data["active_provider"] = active

        self.data["providers"]["ollama"]["base_url"] = self.ollama_url.text().strip()
        self.data["providers"]["ollama"]["model"] = self.ollama_model_combo.currentText().strip()

        raw_rmodel = self.router_model_combo.currentText().strip()
        self.data["providers"]["9router"]["base_url"] = self.router_url.text().strip()
        self.data["providers"]["9router"]["api_key"] = self.router_key.text().strip()
        self.data["providers"]["9router"]["model"] = raw_rmodel

        ratio_txt = self.ratio_combo.currentText()
        if "9:16" in ratio_txt:
            ratio = "9:16"
        elif "1:1" in ratio_txt:
            ratio = "1:1"
        else:
            ratio = "original"

        try:
            dur = int(self.dur_input.text().strip())
            num = int(self.num_input.text().strip())
        except ValueError:
            dur = 30
            num = 3

        self.data["clip_settings"]["target_duration"] = dur
        self.data["clip_settings"]["num_clips"] = num
        self.data["clip_settings"]["aspect_ratio"] = ratio
        self.data["clip_settings"]["output_dir"] = self.out_dir_input.text().strip()

        self.settings_mgr.save(self.data)
        self.accept()
