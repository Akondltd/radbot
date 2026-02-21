"""
Splash screen shown during RadBot startup.
Displays the logo, app name, and progress messages while the
main window and services are being initialized.
"""

from PySide6.QtWidgets import QSplashScreen, QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics
from PySide6.QtCore import Qt
from pathlib import Path
import logging
from version import __app_name__, __version__, __subtitle__
from config.paths import PACKAGE_ROOT

logger = logging.getLogger(__name__)


class RadBotSplashScreen(QSplashScreen):
    """Dark-themed splash screen with logo and status messages."""

    # Splash dimensions
    WIDTH = 420
    HEIGHT = 320

    def __init__(self):
        # Build the splash pixmap
        pixmap = self._create_splash_pixmap()
        super().__init__(pixmap)

        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Style the status message (shown at the bottom)
        self.setStyleSheet("""
            QSplashScreen {
                color: #aaaaaa;
                font-size: 11px;
            }
        """)

    def _create_splash_pixmap(self) -> QPixmap:
        """Render the splash background with logo and title."""
        pixmap = QPixmap(self.WIDTH, self.HEIGHT)
        pixmap.fill(QColor("#1e293b"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw subtle border
        painter.setPen(QColor("#0078D4"))
        painter.drawRect(0, 0, self.WIDTH - 1, self.HEIGHT - 1)

        # Load and draw logo
        logo_path = PACKAGE_ROOT / "images" / "Radbot256.png"
        if logo_path.exists():
            logo = QPixmap(str(logo_path))
            logo_size = 128
            logo_scaled = logo.scaled(logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_x = (self.WIDTH - logo_scaled.width()) // 2
            logo_y = 30
            painter.drawPixmap(logo_x, logo_y, logo_scaled)

        # Draw app name
        title_font = QFont("Segoe UI", 22, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#f0f0f0"))
        painter.drawText(0, 175, self.WIDTH, 40, Qt.AlignCenter, __app_name__)

        # Draw subtitle
        sub_font = QFont("Segoe UI", 10)
        painter.setFont(sub_font)
        painter.setPen(QColor("#888888"))
        painter.drawText(0, 210, self.WIDTH, 25, Qt.AlignCenter, __subtitle__)

        # Draw version
        ver_font = QFont("Segoe UI", 9)
        painter.setFont(ver_font)
        painter.setPen(QColor("#555555"))
        painter.drawText(0, 232, self.WIDTH, 20, Qt.AlignCenter, f"v{__version__}")

        painter.end()
        return pixmap

    def update_status(self, message: str):
        """Update the status message and process events so it renders immediately."""
        logger.debug(f"Splash: {message}")
        self.showMessage(
            f"  {message}",
            Qt.AlignBottom | Qt.AlignLeft,
            QColor("#aaaaaa")
        )
        QApplication.processEvents()
