import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle

from .trade_pairs_gui import OverlappingIconWidget

logger = logging.getLogger(__name__)

# Security: Icons should be loaded from local cache only
# All icons are pre-downloaded and sanitized by token_updater_service.py
# Runtime downloads from URLs are disabled for security


class AvailablePairWidget(QWidget):
    """A widget for displaying an available trade pair in the left panel."""
    # Emits: base_token_rri, quote_token_rri, base_token_symbol, self (the widget instance)
    add_pair_requested = Signal(str, str, str, QWidget)
    delete_pair_requested = Signal(str, str, QWidget)  # base_token_rri, quote_token_rri, self

    ICON_SIZE = 16

    def __init__(self,
                 base_token_rri: str,
                 base_token_symbol: str,
                 base_token_icon_url: Optional[str],
                 base_token_icon_local_path: Optional[str],
                 quote_token_rri: str,
                 quote_token_symbol: str,
                 quote_token_icon_url: Optional[str],
                 quote_token_icon_local_path: Optional[str],
                 is_suggestion: bool = False, # This was also passed
                 parent=None):
        super().__init__(parent)
        self.base_token_rri = base_token_rri
        self.base_token_symbol = base_token_symbol
        self.base_token_icon_url = base_token_icon_url
        self.base_token_icon_local_path = base_token_icon_local_path

        self.quote_token_rri = quote_token_rri
        self.quote_token_symbol = quote_token_symbol
        self.quote_token_icon_url = quote_token_icon_url
        self.quote_token_icon_local_path = quote_token_icon_local_path
        
        self.is_suggestion = is_suggestion # Store this if needed

        # --- UI Setup ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(10)

        # Delete button with built-in trash icon
        self.delete_button = QPushButton()
        self.delete_button.setFixedSize(15, 15)
        trash_icon = self.style().standardIcon(QStyle.SP_DialogCancelButton)
        self.delete_button.setIcon(trash_icon)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border-radius: 3px;
            }
        """)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        
        # Overlapping token icons
        self.icon_widget = OverlappingIconWidget(icon_size=self.ICON_SIZE) 
        self.pair_label = QLabel(f"{self.base_token_symbol}/{self.quote_token_symbol}")

        # Layout: [Delete] [SPACE] [Icons] [SPACE] [Pair Label]
        layout.addWidget(self.delete_button)
        layout.addSpacing(5)
        layout.addWidget(self.icon_widget)
        layout.addStretch() 
        layout.addWidget(self.pair_label)

        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("AvailablePairWidget { border-radius: 4px; } AvailablePairWidget:hover { background-color: #4a4a4a; }")

        # --- Network and Icon Loading ---
        self.network_manager = QNetworkAccessManager(self) # For fetching from URL if local fails
        self.pixmap_base: Optional[QPixmap] = None
        self.pixmap_quote: Optional[QPixmap] = None
        self._load_icons() # This method will also need to be updated

    def _on_delete_clicked(self):
        """Handle delete button click - emit delete signal."""
        logger.debug(f"Delete button clicked for {self.base_token_symbol}/{self.quote_token_symbol}")
        self.delete_pair_requested.emit(self.base_token_rri, self.quote_token_rri, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            logger.debug(f"AvailablePairWidget clicked for {self.base_token_symbol}/{self.quote_token_symbol}")
            self.add_pair_requested.emit(self.base_token_rri, self.quote_token_rri, self.base_token_symbol, self)
        super().mousePressEvent(event)

    def _load_icons(self):
        self._load_icon(self.base_token_icon_local_path, self.base_token_icon_url, self.base_token_symbol, is_base=True)
        self._load_icon(self.quote_token_icon_local_path, self.quote_token_icon_url, self.quote_token_symbol, is_base=False)

    def _update_icons(self):
        if self.pixmap_base and self.pixmap_quote:
            self.icon_widget.set_icons(self.pixmap_base, self.pixmap_quote)

    def _load_icon(self, icon_local_path: Optional[str], icon_url: Optional[str], token_symbol: str, is_base: bool):
        default_pixmap = QPixmap(':/images/images/default_token_icon.png').scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap_loaded_locally = False
        pixmap = default_pixmap # Initialize pixmap with default

        if icon_local_path and os.path.exists(icon_local_path):
            try:
                temp_pixmap = QPixmap(icon_local_path)
                if not temp_pixmap.isNull():
                    pixmap = temp_pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    logger.debug(f"Successfully loaded icon for {token_symbol} from local path: {icon_local_path}")
                    pixmap_loaded_locally = True
                else:
                    logger.warning(f"Failed to load icon for {token_symbol} from local path (Pixmap isNull): {icon_local_path}")
            except Exception as e:
                logger.error(f"Error loading icon for {token_symbol} from local path {icon_local_path}: {e}")

        if pixmap_loaded_locally:
            # pixmap is already set from local load
            pass
        else:
            # SECURITY: No runtime downloads from URLs
            # All icons should be pre-downloaded and sanitized by token_updater_service.py
            # If local file doesn't exist, use default icon (no network requests)
            logger.debug(
                f"Icon not cached locally for {token_symbol}. Using default icon. "
                f"(Runtime downloads disabled for security)"
            )
            # pixmap is already default_pixmap

        # This part runs for sync cases (local load, default, or invalid URL before async)
        if is_base:
            self.pixmap_base = pixmap
        else:
            self.pixmap_quote = pixmap
        self._update_icons()

    def _on_icon_loaded(self, reply: QNetworkReply, token_symbol: str, is_base: bool):
        default_pixmap = QPixmap(':/images/images/default_token_icon.png').scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap = default_pixmap

        if reply.error() == QNetworkReply.NetworkError.NoError:
            image_data = reply.readAll()
            loaded_pixmap = QPixmap()
            if loaded_pixmap.loadFromData(image_data):
                pixmap = loaded_pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                logger.warning(f"Failed to load pixmap from data for {token_symbol}. URL: {reply.url().toString()}")
        else:
            logger.error(f"Network error loading icon for {token_symbol} (URL: {reply.url().toString()}): {reply.errorString()}")

        if is_base:
            self.pixmap_base = pixmap
        else:
            self.pixmap_quote = pixmap
        
        self._update_icons()
        reply.deleteLater()
