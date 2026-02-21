from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                                QScrollArea, QSizePolicy, QMessageBox, QSpacerItem)
from PySide6.QtCore import Qt, QSize, Signal, QUrl, Slot # Slot might be useful later
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSslConfiguration, QSslSocket
# from .create_trade_ui import Ui_CreateTradeTabMain # Not used directly by these classes
from database.database import Database
from database.trade_pairs import TradePairManager as DbTradePairManager # Alias to avoid confusion
from typing import Optional, List, Dict, Any
from core.wallet import RadixWallet
# from gui.components.token_display import TokenDisplayWidget # Not directly used here, manager might pass data
from functools import partial
from pathlib import Path
from config.app_config import get_absolute_path

import logging

# Configure a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust as needed

from .overlapping_icon_widget import OverlappingIconWidget

class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)



class TradePairItemWidget(QWidget):
    ICON_SIZE = 16 # New icon size

    """A widget to display a single trade pair item with its details."""
    # Signal to indicate removal request, passing its own RRI and symbol
    removal_requested = Signal(str, str, QWidget)

    def __init__(self, base_token_symbol: str, quote_token_symbol: str, 
                 base_token_rri: str, quote_token_rri: str, 
                 base_token_icon_url: Optional[str], quote_token_icon_url: Optional[str],
                 base_token_icon_local_path: Optional[str] = None, quote_token_icon_local_path: Optional[str] = None,
                 parent=None):
        super().__init__(parent)
        self.base_token_symbol = base_token_symbol
        self.quote_token_symbol = quote_token_symbol
        self.base_token_rri = base_token_rri
        self.quote_token_rri = quote_token_rri
        self.base_token_icon_url = base_token_icon_url
        self.quote_token_icon_url = quote_token_icon_url
        self.base_token_icon_local_path = base_token_icon_local_path
        self.quote_token_icon_local_path = quote_token_icon_local_path
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.network_manager = QNetworkAccessManager(self)

        # Overlapping Icons first
        self.icon_widget = OverlappingIconWidget(icon_size=self.ICON_SIZE)
        layout.addWidget(self.icon_widget) # Add icons first

        # Then the pair text label
        self.pair_text_label = ClickableLabel(f" {self.base_token_symbol} / {self.quote_token_symbol}")
        # self.pair_text_label.setStyleSheet("font-weight: bold;") # Removed bold style
        self.pair_text_label.setToolTip(f"Click to remove {self.base_token_symbol}/{self.quote_token_symbol}")
        self.pair_text_label.clicked.connect(self._emit_removal_request)
        layout.addStretch() # Add stretch to push text to the right
        layout.addWidget(self.pair_text_label) # Add text label second

        # Load icons and set them on the custom widget
        self.pixmap_base = None
        self.pixmap_quote = None
        self._load_icon(self.base_token_icon_url, self.base_token_icon_local_path, self.base_token_symbol, is_base=True)
        self._load_icon(self.quote_token_icon_url, self.quote_token_icon_local_path, self.quote_token_symbol, is_base=False)
        
        self.setLayout(layout)

    def _emit_removal_request(self):
        # Emit with base_token_rri, base_token_symbol, and self (the widget instance)
        self.removal_requested.emit(self.base_token_rri, self.base_token_symbol, self)

    def _update_icons(self):
        # Ensure both pixmaps are loaded before setting them
        logger.debug(f"_update_icons for {self.base_token_symbol}/{self.quote_token_symbol}: base_pixmap_is_None={self.pixmap_base is None}, quote_pixmap_is_None={self.pixmap_quote is None}")
        if self.pixmap_base and self.pixmap_quote:
            # Set icons in base/quote order
            logger.debug(f"_update_icons: Setting icons for {self.base_token_symbol}/{self.quote_token_symbol} on OverlappingIconWidget.")
            self.icon_widget.set_icons(self.pixmap_base, self.pixmap_quote)

    def _load_icon(self, icon_url: Optional[str], icon_local_path: Optional[str], token_symbol: str, is_base: bool):
        logger.debug(f"_load_icon for {token_symbol} (is_base={is_base}): LocalPath='{icon_local_path}', URL='{icon_url}'")
        default_pixmap = QPixmap(':/images/images/default_token_icon.png').scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Try loading from local cache first
        if icon_local_path:
            absolute_path = get_absolute_path(icon_local_path)
            if absolute_path and absolute_path.is_file():
                pixmap = QPixmap(str(absolute_path))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    if is_base:
                        self.pixmap_base = scaled_pixmap
                    else:
                        self.pixmap_quote = scaled_pixmap
                    self._update_icons()
                    logger.debug(f"Loaded icon for {token_symbol} from local cache: {absolute_path}")
                    return  # Success, no need to download
                else:
                    logger.warning(f"Failed to load pixmap from cached file for {token_symbol} at {absolute_path}. Will fall back to URL if available, or default.")
            else:
                logger.debug(f"Local icon path for {token_symbol} does not exist or is not a file: {absolute_path}. Will fall back to URL if available, or default.")

        # Fallback to default
        if not icon_url or not icon_url.startswith('http'):
            logger.debug(f"No valid icon URL for {token_symbol} (or local cache failed/unavailable), using default icon.")
            if is_base:
                self.pixmap_base = default_pixmap
            else:
                self.pixmap_quote = default_pixmap
            self._update_icons()
            return

        try:
            url = QUrl(icon_url)
            if url.isValid():
                request = QNetworkRequest(url)
                # SSL Configuration for bypassing errors
                ssl_config = QSslConfiguration.defaultConfiguration()
                ssl_config.setPeerVerifyMode(QSslSocket.VerifyNone) # Bypass SSL verification
                request.setSslConfiguration(ssl_config)

                reply = self.network_manager.get(request)
                reply.finished.connect(lambda r=reply, ts=token_symbol, base=is_base: self._on_icon_loaded(r, ts, base))
            else: # If URL is not valid after all
                logger.warning(f"Invalid icon URL '{icon_url}' for token {token_symbol} after local cache check. Using default icon.")
                if is_base:
                    self.pixmap_base = default_pixmap
                else:
                    self.pixmap_quote = default_pixmap
                self._update_icons()
        except Exception as e: # Catch any other errors during URL processing
            logger.error(f"Error processing URL '{icon_url}' for {token_symbol}: {e}. Using default icon.", exc_info=True)
            if is_base:
                self.pixmap_base = default_pixmap
            else:
                self.pixmap_quote = default_pixmap
            self._update_icons()
    def _on_icon_loaded(self, reply, token_symbol: str, is_base: bool):
        default_pixmap = QPixmap(':/images/images/default_token_icon.png').scaled(self.ICON_SIZE, self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
#         logger.debug(f"_on_icon_loaded for {token_symbol} (is_base={is_base}): reply.error={reply.error()}")
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

    


class TradePairsManager(QWidget):
    """Manages the display and interaction of selected trade pairs for a wallet."""
    # Signal to parent (CreateTradeTabMain) when a pair is requested to be moved back (deselected)
    # Passes base_token_rri, base_token_symbol
    pair_deselection_requested = Signal(str, str)
    pairs_changed = Signal()  # Emitted when a pair is added or removed

    def __init__(self, db_instance: 'Database', parent=None):
        super().__init__(parent)
        self.wallet: Optional[RadixWallet] = None
        self.db = db_instance
        self.active_wallet_id: Optional[int] = None
        self.xrd_icon_url: Optional[str] = None
        self.xrd_icon_local_path: Optional[str] = None
        self.db_trade_pair_manager: DbTradePairManager = self.db.get_trade_pair_manager()
        self.balance_manager = self.db.get_balance_manager()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        # Permanent placeholder label
        self.placeholder_label = QLabel("No trade pairs configured. Add pairs from the left panel.")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("font-style: italic; color: grey;")
        self.main_layout.addWidget(self.placeholder_label)
        self.placeholder_label.show() # Show by default

        # List to track only the trade pair widgets
        self.trade_pair_widgets: List[TradePairItemWidget] = []

        # Permanent stretch item to push everything to the top
        self.stretch_item = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addSpacerItem(self.stretch_item)
        
        self.xrd_rri: str = "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd"
        self.xrd_symbol: str = "XRD"
        self._fetch_xrd_details()

    def set_wallet_context(self, wallet: Optional[RadixWallet]):
        """Sets the wallet context, updates active_wallet_id, loads pairs, and emits signal."""
        logger.info(f"TradePairsManager: Setting wallet context. Wallet: {'Provided' if wallet else 'None'}")
        self.wallet = wallet
        if self.wallet and hasattr(self.wallet, 'wallet_id') and self.wallet.wallet_id is not None:
            self.active_wallet_id = self.wallet.wallet_id
            logger.info(f"TradePairsManager: Active wallet ID set to: {self.active_wallet_id}")
            # If balance_manager needs the wallet object, update it here:
            if self.balance_manager and hasattr(self.balance_manager, 'wallet'):
                 self.balance_manager.wallet = self.wallet
        else:
            self.active_wallet_id = None
            logger.info("TradePairsManager: Active wallet ID set to None (no wallet or no wallet_id).")
            # Clear wallet from balance_manager if applicable:
            if self.balance_manager and hasattr(self.balance_manager, 'wallet'):
                 self.balance_manager.wallet = None

        # self.xrd_icon_url is an attribute of TradePairsManager, 
        # expected to be set by CreateTradeTabMain via direct attribute access.

        self.load_trade_pairs() # This will use self.active_wallet_id. load_trade_pairs now emits pairs_changed.
        logger.debug("TradePairsManager: pairs_changed signal emitted after wallet context update.")

    def load_trade_pairs(self):
        self.clear_trade_pairs_ui()

        if self.active_wallet_id is None:
            logger.info("TradePairsManager: No active wallet ID set.")
            self._update_placeholder_visibility() # Ensure placeholder is shown
            return

        try:
            logger.info(f"TradePairsManager: Loading selected trade pairs for wallet ID: {self.active_wallet_id}")
            selected_pairs_data = self.db_trade_pair_manager.get_selected_trade_pairs(self.active_wallet_id)
            logger.debug(f"TradePairsManager.load_trade_pairs: Fetched selected_pairs_data from DB: {selected_pairs_data}")
            
            if not selected_pairs_data:
                logger.info(f"TradePairsManager: No trade pairs selected for wallet ID {self.active_wallet_id}.")
                self._update_placeholder_visibility() # Ensure placeholder is shown
                return

            displayed_pairs_set = set()

            for pair_data in selected_pairs_data:
                base_rri = pair_data.get('base_token_rri')
                quote_rri = pair_data.get('quote_token_rri')
                base_sym = pair_data.get('base_token_symbol', 'N/A')
                quote_sym = pair_data.get('quote_token_symbol', 'N/A')

                if not base_rri or not quote_rri:
                    logger.warning(f"Skipping pair with missing RRI: {pair_data}")
                    continue

                current_pair_tuple = tuple(sorted((base_rri, quote_rri)))
                if current_pair_tuple in displayed_pairs_set:
                    logger.debug(f"Skipping duplicate pair during load: {base_sym}/{quote_sym}")
                    continue
                displayed_pairs_set.add(current_pair_tuple)

                # Use icon URLs directly from pair_data
                base_icon_url = pair_data.get('base_token_icon_url')
                quote_icon_url = pair_data.get('quote_token_icon_url')

                # If base_icon_url is missing, try to fetch it fresh
                if not base_icon_url and base_rri:
                    logger.info(f"Base icon URL missing for {base_sym} ({base_rri}) from DB query in load_trade_pairs. Attempting fresh fetch.")
                    token_manager = self.db.get_token_manager()
                    base_token_info = token_manager.get_token_by_address(base_rri)
                    if base_token_info:
                        base_icon_url = base_token_info.get('icon_url')
                        logger.info(f"Fresh base_icon_url for {base_sym} from token_manager: {base_icon_url}")
                    else:
                        logger.warning(f"Could not fetch fresh token info for {base_sym} ({base_rri}) in load_trade_pairs.")
                
                # If quote_icon_url is missing.
                if quote_rri == self.xrd_rri and not quote_icon_url:
                    quote_icon_url = self.xrd_icon_url # Ensure XRD icon is used if appropriate
                    logger.debug(f"Ensuring XRD icon URL for {quote_sym} in load_trade_pairs: {quote_icon_url}")
                elif not quote_icon_url and quote_rri: # For non-XRD quote tokens
                    logger.info(f"Quote icon URL missing for {quote_sym} ({quote_rri}) from DB query in load_trade_pairs. Attempting fresh fetch.")
                    token_manager = self.db.get_token_manager()
                    quote_token_info = token_manager.get_token_by_address(quote_rri)
                    if quote_token_info:
                        quote_icon_url = quote_token_info.get('icon_url')
                        logger.info(f"Fresh quote_icon_url for {quote_sym} from token_manager: {quote_icon_url}")
                    else:
                        logger.warning(f"Could not fetch fresh token info for {quote_sym} ({quote_rri}) in load_trade_pairs.")

                # Fetch local paths as well
                token_manager = self.db.get_token_manager() # Ensure token_manager is available
                base_icon_local_path = pair_data.get('base_token_icon_local_path')
                base_token_info = None # Initialize to avoid NameError if not set by earlier logic
                if not base_icon_local_path and base_rri: # If missing from selected_pairs_data, try fresh
                    # Check if base_token_info was already fetched when base_icon_url was checked
                    # This assumes 'base_token_info' might have been defined earlier in the loop if base_icon_url was missing
                    # To be safe, we re-fetch or ensure it's defined.
                    if not 'base_token_info' in locals() or not base_token_info or base_token_info.get('address') != base_rri:
                         base_token_info = token_manager.get_token_by_address(base_rri)
                    if base_token_info:
                         base_icon_local_path = base_token_info.get('icon_local_path')

                quote_icon_local_path = None
                quote_token_info = None # Initialize
                if quote_rri == self.xrd_rri:
                    quote_icon_local_path = self.xrd_icon_local_path
                elif quote_rri: # For non-XRD quote tokens
                    # Similar logic for quote_token_info as for base_token_info
                    if not 'quote_token_info' in locals() or not quote_token_info or quote_token_info.get('address') != quote_rri:
                        quote_token_info = token_manager.get_token_by_address(quote_rri)
                    if quote_token_info:
                        quote_icon_local_path = quote_token_info.get('icon_local_path')
                
                logger.debug(f"TradePairsManager.load_trade_pairs: For {base_sym}/{quote_sym}, BaseIconURL: '{base_icon_url}', QuoteIconURL: '{quote_icon_url}', BaseIconLocal: '{base_icon_local_path}', QuoteIconLocal: '{quote_icon_local_path}' before creating widget.")

                item_widget = TradePairItemWidget(
                    base_token_symbol=base_sym,
                    quote_token_symbol=quote_sym,
                    base_token_rri=base_rri,
                    quote_token_rri=quote_rri,
                    base_token_icon_url=base_icon_url,
                    quote_token_icon_url=quote_icon_url,
                    base_token_icon_local_path=base_icon_local_path,
                    quote_token_icon_local_path=quote_icon_local_path
                )
                item_widget.removal_requested.connect(self._handle_pair_deselection_request)
                
                # Insert widget before the permanent stretch item
                self.main_layout.insertWidget(self.main_layout.count() - 1, item_widget)
                self.trade_pair_widgets.append(item_widget)

            self._update_placeholder_visibility()
            self.pairs_changed.emit() # Notify that pairs have been loaded/changed

        except Exception as e:
            logger.error(f"TradePairsManager: Error loading trade pairs: {e}", exc_info=True)
            self.placeholder_label.show() # Show placeholder on error

    def _handle_pair_deselection_request(self, base_token_rri: str, base_token_symbol: str, item_widget: QWidget):
        """Handles the removal_requested signal from a TradePairItemWidget."""
        # Read the actual quote token from the widget instead of assuming XRD
        quote_token_rri = getattr(item_widget, 'quote_token_rri', self.xrd_rri)
        quote_token_symbol = getattr(item_widget, 'quote_token_symbol', 'XRD')
        pair_label = f"{base_token_symbol}/{quote_token_symbol}"
        
        logger.info(f"Deselection requested for {pair_label} (base={base_token_rri}, quote={quote_token_rri}).")
        
        if self.active_wallet_id is None:
            logger.error("Cannot deselect pair: active_wallet_id not found.")
            QMessageBox.warning(self, "Error", "Wallet ID not found. Cannot deselect pair.")
            return
        
        if not quote_token_rri:
            logger.error("Cannot deselect pair: quote token RRI not available.")
            QMessageBox.warning(self, "Error", "Quote token not found. Cannot deselect pair.")
            return

        # Check if there are any trades using this pair before allowing deselection
        trade_pair_id = self.db_trade_pair_manager.get_trade_pair_id(base_token_rri, quote_token_rri)
        if trade_pair_id:
            trade_manager = self.db.get_trade_manager()
            trades_count = trade_manager.get_trades_count_for_pair(trade_pair_id)
            if trades_count > 0:
                logger.warning(f"Cannot deselect {pair_label}: {trades_count} trade(s) exist for this pair.")
                QMessageBox.warning(
                    self, 
                    "Cannot Remove Pair",
                    f"Cannot remove {pair_label} from Radbot Trading Pairs.\n\n"
                    f"There {'is' if trades_count == 1 else 'are'} {trades_count} trade{'s' if trades_count != 1 else ''} "
                    f"using this pair. Price history is only collected for pairs in this list.\n\n"
                    f"Please delete all trades for this pair first from the Active Trades tab."
                )
                return

        success = self.db_trade_pair_manager.deselect_trade_pair(base_token_rri, quote_token_rri, self.active_wallet_id)
        if success:
            logger.info(f"Successfully deselected {pair_label} from database.")
            self.main_layout.removeWidget(item_widget)
            item_widget.deleteLater()
            if item_widget in self.trade_pair_widgets:
                self.trade_pair_widgets.remove(item_widget)
            self._update_placeholder_visibility()
            # Emit signal to notify parent (CreateTradeTabMain) to re-add to left panel
            self.pair_deselection_requested.emit(base_token_rri, base_token_symbol)
            self.pairs_changed.emit()
        else:
            logger.error(f"Failed to deselect {pair_label} from database.")
            QMessageBox.warning(self, "Database Error", f"Could not deselect {pair_label}.")

    def clear_trade_pairs_ui(self):
        # Only remove TradePairItemWidget instances, leave placeholder and stretch
        for widget in self.trade_pair_widgets:
            self.main_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.trade_pair_widgets.clear()
        self._update_placeholder_visibility() # Update visibility based on the now-empty list

    def add_trade_pair(self, base_token_rri: str, base_token_symbol: str) -> bool:
        if not self.wallet:
            logger.error("TradePairsManager: Cannot add trade pair, no wallet is active.")
            QMessageBox.critical(self, "Wallet Error", "No wallet is active.")
            return False

        if self.active_wallet_id is None:
            logger.error("TradePairsManager: No active wallet ID set.")
            QMessageBox.critical(self, "Wallet Error", "No active wallet ID set.")
            return False
        
        if not self.xrd_rri:
            logger.error("TradePairsManager: XRD RRI not available.")
            QMessageBox.critical(self, "Configuration Error", "XRD token details missing.")
            return False

        quote_token_rri = self.xrd_rri
        quote_token_symbol = self.xrd_symbol

        if base_token_rri == quote_token_rri:
            logger.info(f"Attempt to add self-pair {base_token_symbol}/{quote_token_symbol}. Preventing.")
            QMessageBox.warning(self, "Invalid Pair", f"Cannot add a trade pair of a token against itself ({base_token_symbol}/{quote_token_symbol}).")
            return False

        try:
            logger.info(f"TradePairsManager: Adding {base_token_symbol}/{quote_token_symbol} for wallet ID {self.active_wallet_id}")
            
            for widget in self.trade_pair_widgets:
                if widget.base_token_rri == base_token_rri and widget.quote_token_rri == quote_token_rri:
                    logger.info(f"Pair {base_token_symbol}/{quote_token_symbol} already in UI. Skipping add.")
                    QMessageBox.information(self, "Already Added", f"The pair {base_token_symbol}/{quote_token_symbol} is already selected.")
                    return True

            db_ensure_success = self.db_trade_pair_manager.add_trade_pair(base_token_rri, quote_token_rri, price=None)
            if not db_ensure_success:
                logger.error(f"DB error ensuring pair {base_token_rri}/{quote_token_rri} exists.")
                QMessageBox.warning(self, "Database Error", "Could not ensure trade pair exists in DB.")
                return False 

            select_success = self.db_trade_pair_manager.select_trade_pair(base_token_rri, quote_token_rri, self.active_wallet_id)
            if not select_success:
                logger.error(f"Failed to select pair {base_token_symbol}/{quote_token_symbol} for wallet {self.active_wallet_id}.")
                QMessageBox.warning(self, "Database Error", "Could not select the trade pair.")
                return False
            
            # Fetch base token details for its icon URL using its RRI for reliability
            token_manager = self.db.get_token_manager()
            base_token_info = token_manager.get_token_by_address(base_token_rri)
            base_icon_url = base_token_info.get('icon_url') if base_token_info else None

            base_icon_local_path = base_token_info.get('icon_local_path') if base_token_info else None

            new_widget = TradePairItemWidget(
                base_token_symbol=base_token_symbol,
                quote_token_symbol=quote_token_symbol,
                base_token_rri=base_token_rri,
                quote_token_rri=quote_token_rri,
                base_token_icon_url=base_icon_url,
                quote_token_icon_url=self.xrd_icon_url,  # Use fetched XRD icon URL
                base_token_icon_local_path=base_icon_local_path,
                quote_token_icon_local_path=self.xrd_icon_local_path # Use fetched XRD local path
            )
            new_widget.removal_requested.connect(self._handle_pair_deselection_request)
            
            # Insert widget before the permanent stretch item
            self.main_layout.insertWidget(self.main_layout.count() - 1, new_widget)
            self.trade_pair_widgets.append(new_widget)
            self._update_placeholder_visibility()
            self.pairs_changed.emit()
            
            logger.info(f"Trade pair {base_token_symbol}/{quote_token_symbol} added to manager.")
            return True

        except Exception as e:
            logger.error(f"TradePairsManager: Error adding trade pair {base_token_symbol}: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Error", f"Error adding trade pair: {e}")
            return False

    def _update_placeholder_visibility(self):
        if self.trade_pair_widgets:
            self.placeholder_label.hide()
        else:
            self.placeholder_label.show()

    def update_balances_in_ui(self):
        """Iterates through displayed trade pair widgets. Currently no dynamic data to update other than what's set at creation."""
        if not self.wallet:
            logger.debug("Cannot update UI elements: Wallet not available.")
        # If other dynamic non-balance elements were to be updated on the widgets, that logic would go here.
        # For now, this method can be a placeholder or removed if no other updates are foreseen.
        logger.debug("update_balances_in_ui called, but no balance-specific updates are currently performed on TradePairItemWidget.")

    def _fetch_xrd_details(self):
        logger.debug("TradePairsManager: Attempting to fetch XRD details (RRI and Symbol).")
        if not self.db:
            logger.warning("TradePairsManager: No DB instance, cannot fetch XRD details.")
            return
        try:
            token_manager = self.db.get_token_manager()
            if not token_manager:
                logger.warning("TradePairsManager: TokenManager not available from DB.")
                return
            xrd_info = token_manager.get_token_by_rri(self.xrd_rri)
            if xrd_info:
                # Ensure we use the correct key for RRI and icon_url from your xrd_info dictionary
                self.xrd_rri = xrd_info.get('address') 
                self.xrd_symbol = xrd_info.get('symbol', self.xrd_symbol)
                self.xrd_icon_url = xrd_info.get('icon_url') # Fetch the icon URL
                self.xrd_icon_local_path = xrd_info.get('icon_local_path') # Fetch the local icon path
                logger.info(f"TradePairsManager: XRD details fetched. RRI={self.xrd_rri}, Symbol={self.xrd_symbol}, IconURL={self.xrd_icon_url}, LocalPath={self.xrd_icon_local_path}")
            else:
                logger.warning(f"TradePairsManager: Could not find details for XRD symbol '{self.xrd_symbol}'. Icon URL will remain None.")
                self.xrd_icon_url = None # Ensure it's None if not found
        except Exception as e:
            logger.error(f"TradePairsManager: Error fetching XRD RRI/Symbol details: {e}", exc_info=True)

    def get_selected_base_token_rris(self) -> List[str]:
        """Returns a list of RRIs for all base tokens currently in selected trade pairs."""
        return [widget.base_token_rri for widget in self.trade_pair_widgets]

    def get_configured_pairs_data(self) -> List[Dict[str, Any]]:
        """Returns data for all configured trade pairs for the current wallet."""
        if self.active_wallet_id is None:
            logger.warning("TradePairsManager: Cannot get configured pairs data, no active wallet ID set.")
            return []

        try:
            # The db_trade_pair_manager.get_selected_trade_pairs now correctly calls the function
            # that returns all necessary data, including trade_pair_id, symbols, and icons for both tokens.
            # We can just return this data directly.
            configured_pairs = self.db_trade_pair_manager.get_selected_trade_pairs(self.active_wallet_id)
            logger.debug(f"TradePairsManager: get_configured_pairs_data returning {len(configured_pairs)} pairs directly from the database manager.")
            return configured_pairs
        except Exception as e:
            logger.error(f"TradePairsManager: Error in get_configured_pairs_data: {e}", exc_info=True)
            return []

    def get_pool_address_for_pair(self, trade_pair_id: int) -> Optional[str]:
        """Fetches the Ociswap pool address for a given trade pair ID."""
        if self.active_wallet_id is None:
            logger.warning("TradePairsManager: Cannot get pool address, no active wallet ID set.")
            return None
        try:
            pool_address = self.db_trade_pair_manager.get_pool_address_for_pair(trade_pair_id)
            if not pool_address:
                logger.warning(f"No Ociswap pool address found for trade_pair_id: {trade_pair_id}")
            return pool_address
        except Exception as e:
            logger.error(f"Error fetching pool address for trade_pair_id {trade_pair_id}: {e}", exc_info=True)
            return None
