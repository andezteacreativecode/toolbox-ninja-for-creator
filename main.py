import sys
import os
import traceback
from pathlib import Path

# Add project root to sys.path for both normal execution and PyInstaller frozen executable
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    bundle_dir = Path(sys._MEIPASS)
else:
    bundle_dir = Path(__file__).parent.absolute()

sys.path.insert(0, str(bundle_dir))

def main():
    try:
        from core.utils.system_checker import ensure_bin_path, SystemChecker
        ensure_bin_path()

        from gui.app import ClipperApp
        from gui.main_window_v2 import MainWindowV2
        from gui.dialogs.setup_wizard_dialog import SetupWizardDialog
        from PyQt6.QtWidgets import QMessageBox

        app = ClipperApp(sys.argv)

        # First Launch / Dependency Check
        has_ffmpeg = SystemChecker.is_ffmpeg_installed()
        has_model = SystemChecker.has_ollama_model("gemma2:2b")

        if not (has_ffmpeg and has_model):
            wizard = SetupWizardDialog()
            wizard.exec()

        window = MainWindowV2()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"[Fatal Error] Gagal menjalankan Clipper AI Desktop:\n\n{e}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            if not QApplication.instance():
                app = QApplication(sys.argv)
            QMessageBox.critical(None, "Error Fatal - Clipper AI", f"Aplikasi mengalami masalah:\n{e}")
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
