import os
import sys
import pathlib
import datetime
import traceback
import logging
import faulthandler

# Add project root to Python path (before any local imports)
project_root = str(pathlib.Path(__file__).parent)
sys.path.insert(0, project_root)

# Centralised logging — must be set up before any log calls
from utils.log_config import setup_logging, get_crash_log_path, get_faulthandler_path

# Enable faulthandler for catching segfaults and other fatal errors
_faulthandler_file = open(get_faulthandler_path(), 'a')
faulthandler.enable(file=_faulthandler_file, all_threads=True)

os.environ["QT_OPENGL"] = "software"

# Lightweight Qt imports only — heavy app imports are deferred to show splash fast
from PySide6.QtWidgets import QApplication

# Global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Catches unhandled exceptions, logs them, and shows a user-friendly message."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Unhandled exception caught", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Also write to a dedicated crash log for easy access
    crash_log = get_crash_log_path()
    with open(crash_log, "a") as f:
        f.write(f"--- CRASH REPORT: {datetime.datetime.now()} ---\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        f.write("\n")

    print(f"A critical error occurred. A crash report has been saved to {crash_log}.")

# Install the global exception handler
sys.excepthook = handle_exception

def main():
    setup_logging()
    logging.info("--- main() function entered ---")
    logging.info("App started")

    try:
        app = QApplication(sys.argv)
        
        # Set App User Model ID for Windows taskbar icon
        # This prevents Python apps from being grouped under the Python icon
        try:
            import ctypes
            myappid = 'radixdlt.radbot.dexbot.1.0'  # Arbitrary string (company.product.subproduct.version)
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            logging.debug(f"Could not set AppUserModelID (non-Windows or error): {e}")

        # Load and apply the global dark theme stylesheet
        try:
            from config.paths import PACKAGE_ROOT
            style_file = PACKAGE_ROOT / "gui" / "styling" / "dark_theme.qss"
            with open(style_file, "r") as f:
                app.setStyleSheet(f.read())
        except FileNotFoundError:
            logging.warning("Stylesheet not found, using default style.")

        # Show splash screen immediately (before heavy imports)
        from gui.splash_screen import RadBotSplashScreen
        splash = RadBotSplashScreen()
        splash.show()
        splash.update_status("Running security checks...")

        # Run lightweight security check (non-blocking)
        try:
            from security.startup_check import DependencyVerifier
            verifier = DependencyVerifier()
            if not verifier.verify_packages():
                logging.warning("Package verification detected changes. Run 'python security/startup_check.py --reset' if you updated packages.")
        except Exception as e:
            logging.debug(f"Security check skipped: {e}")

        splash.update_status("Loading application modules...")

        # Heavy import — triggers loading of all GUI tabs, services, database modules
        from gui.main_window import TradingBotMainWindow

        splash.update_status("Initializing main window...")

        window = TradingBotMainWindow()

        splash.update_status("Starting services...")
        app.processEvents()

        window.show()
        splash.finish(window)

        sys.exit(app.exec())
    except Exception:
        logging.exception("Exception occurred")
        print("A fatal exception occurred. See logs/radbot.log and logs/error.log for details.")
        input("Press Enter to exit...")
    finally:
        # Close the faulthandler's log file on application exit
        if not _faulthandler_file.closed:
            logging.debug("Closing faulthandler log file")
            _faulthandler_file.close()

if __name__ == "__main__":
    main()