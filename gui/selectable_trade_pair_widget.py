from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QUrl, Slot
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import Optional
from pathlib import Path
from config.app_config import get_absolute_path

from .overlapping_icon_widget import OverlappingIconWidget
import logging

logger = logging.getLogger(__name__)

class SelectableTradePairWidget(QWidget):
    """A widget to display a trade pair in a list, making it selectable."""
    # Signal emitted when the widget is clicked, passing its own instance
    clicked = Signal(object)
    ICON_SIZE = 16  # Consistent icon size

    def __init__(self, trade_pair_id: int, 
                 base_token_symbol: str, quote_token_symbol: str, 
                 base_token_rri: str, quote_token_rri: str, 
                 base_token_icon_url: Optional[str], quote_token_icon_url: Optional[str],
                 base_token_icon_local_path: Optional[str] = None, 
                 quote_token_icon_local_path: Optional[str] = None,
                 parent=None):
        super().__init__(parent)
        self._network_manager = QNetworkAccessManager(self)
        self._base_icon_pixmap: Optional[QPixmap] = None
        self._quote_icon_pixmap: Optional[QPixmap] = None
        self.trade_pair_id = trade_pair_id
        self.base_token_symbol = base_token_symbol
        self.quote_token_symbol = quote_token_symbol
        self.base_token_rri = base_token_rri
        self.quote_token_rri = quote_token_rri
        self.base_token_icon_local_path = base_token_icon_local_path
        self.quote_token_icon_local_path = quote_token_icon_local_path
        self.is_selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoFillBackground(True)  # Important for background color changes

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.icon_widget = OverlappingIconWidget(icon_size=self.ICON_SIZE)
        layout.addWidget(self.icon_widget)
        layout.addSpacing(5) # Add some space between icon and label

        self.pair_label = QLabel(f"{self.base_token_symbol}/{self.quote_token_symbol}")
        self.pair_label.setStyleSheet("color: white;") # Set default text color to white
        layout.addWidget(self.pair_label)
        layout.addStretch() # Push label to the right if needed, or keep it compact

        self.deselect()
        self._load_icons(base_token_icon_url, quote_token_icon_url, self.base_token_icon_local_path, self.quote_token_icon_local_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def select(self):
        """Styles the widget to appear selected."""
        self.is_selected = True
        palette = self.palette()
        # A nice blue for selection, e.g., from a color palette site
        palette.setColor(self.backgroundRole(), QColor("#4a69bd"))
        palette.setColor(self.foregroundRole(), Qt.GlobalColor.white)
        self.setPalette(palette)

    def deselect(self):
        """Styles the widget to appear deselected."""
        self.is_selected = False
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.GlobalColor.transparent)  # Default background
        palette.setColor(self.foregroundRole(), Qt.GlobalColor.white)  # Ensure text is white when deselected
        self.setPalette(palette)

    def _load_icons(self, base_icon_url: Optional[str], quote_icon_url: Optional[str],
                    base_icon_local_path: Optional[str], quote_icon_local_path: Optional[str]):
        
        base_requires_network = True # Assume network request is needed
        # --- Base Icon --- 
        if base_icon_local_path:
            absolute_path = get_absolute_path(base_icon_local_path)
            if absolute_path and absolute_path.is_file():
                pixmap = QPixmap(str(absolute_path))
                if not pixmap.isNull():
                    self._base_icon_pixmap = pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    logger.debug(f"Base icon for {self.base_token_symbol} loaded locally from {absolute_path}")
                    base_requires_network = False # Loaded locally, no network needed
                else:
                    logger.warning(f"Failed to load base icon locally from {absolute_path} for {self.base_token_symbol}. Attempting URL.")
            else:
                logger.debug(f"Local base icon path does not exist: {absolute_path}")
        
        if base_requires_network: # If not loaded locally, try URL
            if base_icon_url:
                request = QNetworkRequest(QUrl(base_icon_url))
                reply = self._network_manager.get(request)
                reply.finished.connect(lambda r=reply: self._on_base_icon_loaded(r))
            else: # No local path and no URL
                logger.debug(f"No base icon URL or usable local path for {self.base_token_symbol}. Using default.")
                self._base_icon_pixmap = QPixmap(":/assets/icons/default_icon.png")
                base_requires_network = False # Defaulted, no network needed

        quote_requires_network = True # Assume network request is needed
        # --- Quote Icon --- 
        if quote_icon_local_path:
            absolute_path = get_absolute_path(quote_icon_local_path)
            if absolute_path and absolute_path.is_file():
                pixmap = QPixmap(str(absolute_path))
                if not pixmap.isNull():
                    self._quote_icon_pixmap = pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    logger.debug(f"Quote icon for {self.quote_token_symbol} loaded locally from {absolute_path}")
                    quote_requires_network = False # Loaded locally, no network needed
            else:
                logger.warning(f"Failed to load quote icon locally from {absolute_path} for {self.quote_token_symbol}. Attempting URL.")
        else:
            logger.debug(f"Local quote icon path does not exist: {quote_icon_local_path}")

        if quote_requires_network: # If not loaded locally, try URL
            if quote_icon_url:
                request = QNetworkRequest(QUrl(quote_icon_url))
                reply = self._network_manager.get(request)
                reply.finished.connect(lambda r=reply: self._on_quote_icon_loaded(r))
            else: # No local path and no URL
                logger.debug(f"No quote icon URL or usable local path for {self.quote_token_symbol}. Using default.")
                self._quote_icon_pixmap = QPixmap(":/assets/icons/default_icon.png")
                quote_requires_network = False # Defaulted, no network needed
        
        # If neither icon requires a network request at this point, it means:
        # 1. Both were loaded locally successfully.
        # 2. One was loaded locally, the other had no URL/local_path and was defaulted.
        # 3. Both had no URL/local_path and were defaulted.
        # In these cases, we can try to set the icons.
        # If any icon *did* require a network request, its _on_..._loaded slot will call _check_and_set_icons.
        if not base_requires_network and not quote_requires_network:
            self._check_and_set_icons()

    @Slot(QNetworkReply)
    def _on_base_icon_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._base_icon_pixmap = pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                logger.warning(f"Failed to load base icon data for {self.base_token_symbol} from {reply.url().toString()}")
                self._base_icon_pixmap = QPixmap(":/assets/icons/default_icon.png") # Fallback
        else:
            logger.error(f"Network error loading base icon for {self.base_token_symbol}: {reply.errorString()} from {reply.url().toString()}")
            self._base_icon_pixmap = QPixmap(":/assets/icons/default_icon.png") # Fallback
        reply.deleteLater()
        self._check_and_set_icons()

    @Slot(QNetworkReply)
    def _on_quote_icon_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._quote_icon_pixmap = pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                logger.warning(f"Failed to load quote icon data for {self.quote_token_symbol} from {reply.url().toString()}")
                self._quote_icon_pixmap = QPixmap(":/assets/icons/default_icon.png") # Fallback
        else:
            logger.error(f"Network error loading quote icon for {self.quote_token_symbol}: {reply.errorString()} from {reply.url().toString()}")
            self._quote_icon_pixmap = QPixmap(":/assets/icons/default_icon.png") # Fallback
        reply.deleteLater()
        self._check_and_set_icons()

    def _check_and_set_icons(self):
        if self._base_icon_pixmap and self._quote_icon_pixmap:
            self.icon_widget.set_icons(self._base_icon_pixmap, self._quote_icon_pixmap)
            logger.debug(f"Icons set for {self.base_token_symbol}/{self.quote_token_symbol}")
