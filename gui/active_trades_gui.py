from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTextEdit
from PySide6.QtCore import Slot, Signal
from .active_trades_ui import Ui_ActiveTradesTabMain
from gui.components.active_trade_list_item import ActiveTradeListItemWidget
from gui.active_trades_info_page import ActiveTradeInfoPage
from gui.active_trades_edit_page import ActiveTradeEditPage
from gui.active_trades_delete_page import ActiveTradeDeletePage
from database.database import Database
from database.tokens import TokenManager
import logging

logger = logging.getLogger(__name__)

class ActiveTradesTabMain(QWidget):
    trade_operation_completed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ActiveTradesTabMain()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        
        self.db = Database()
        self.trade_manager = self.db.get_trade_manager()
        self.token_manager = self.db.get_token_manager()
        self.current_wallet_address = None
        self._is_refreshing = False  # Guard against concurrent refresh operations
        self.active_trades_widgets = {}  # Initialize widget dictionary

        # Page helpers
        self.info_page = ActiveTradeInfoPage(self.ui, self.trade_manager, self.token_manager)
        self.edit_page = ActiveTradeEditPage(self.ui, self.trade_manager)
        self.delete_page = ActiveTradeDeletePage(self.ui, self.trade_manager)

        # Set token manager for edit page
        self.edit_page.set_token_manager(self.token_manager)
        self.init_active_trades_ui()

        # Connections
        self.edit_page.trade_updated.connect(self.handle_trade_update)
        self.delete_page.trade_deleted.connect(self._refresh_active_trades)
        self.delete_page.trade_deleted.connect(self.trade_operation_completed.emit)

    def init_active_trades_ui(self):
        # Setup layout for the scroll area content widget
        self.scroll_layout = QVBoxLayout(self.ui.scrollAreaWidgetContents_7)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.addStretch() # Pushes items to the top

    def clear_trade_list(self):
        """Clears all trade widgets from the list."""
        # Disconnect signals from widgets being deleted to prevent dangling connections
        for trade_id, widget in self.active_trades_widgets.items():
            try:
                widget.info_requested.disconnect()
                widget.edit_requested.disconnect()
                widget.pause_toggle_requested.disconnect()
                widget.delete_requested.disconnect()
            except (RuntimeError, TypeError):
                # Widget already deleted or signals not connected
                pass
        
        # Remove and delete widgets
        for i in reversed(range(self.scroll_layout.count() -1)): # Exclude stretch
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                self.scroll_layout.removeWidget(widget)
                widget.deleteLater()
        
        # Clear the dictionary
        self.active_trades_widgets = {}
        
        # Process pending deletions before creating new widgets
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def load_active_trades(self, wallet_address: str):
        """Fetches active trades for a specific wallet and populates the list."""
        # Check wallet address before setting refresh flag
        if not wallet_address:
            logger.warning("load_active_trades called with no wallet address.")
            return
        
        # Prevent concurrent refresh operations
        if self._is_refreshing:
            logger.debug("Refresh already in progress, skipping concurrent refresh request")
            return
        
        self._is_refreshing = True
        
        try:
            self.clear_trade_list()
            trades = self.trade_manager.get_all_active_trades(wallet_address)
            logger.info(f"Found {len(trades)} active trades for wallet {wallet_address}.")

            for i, trade in enumerate(trades):
                trade_id = trade['trade_id']
                list_item = ActiveTradeListItemWidget(trade, self.token_manager, index=i)
                
                # Connect signals to handlers
                list_item.info_requested.connect(self.handle_info_request)
                list_item.edit_requested.connect(self.handle_edit_request)
                list_item.pause_toggle_requested.connect(self.handle_pause_toggle_request)
                list_item.delete_requested.connect(self.handle_delete_request)

                # Insert new widget at the top of the layout
                self.scroll_layout.insertWidget(0, list_item)
                self.active_trades_widgets[trade_id] = list_item

        except Exception as e:
            logger.error(f"Failed to load active trades: {e}", exc_info=True)
        finally:
            self._is_refreshing = False

    @Slot(object)
    def handle_wallet_loaded(self, wallet):
        """Slot to handle the wallet_loaded signal."""
        if wallet and hasattr(wallet, 'public_address'):
            wallet_address = wallet.public_address
            logger.info(f"ActiveTradesTab: Wallet loaded signal received for address: {wallet_address}")
            self.current_wallet_address = wallet_address
            self.load_active_trades(wallet_address)
        else:
            logger.error("ActiveTradesTab: Received invalid wallet object.")

    @Slot()
    def handle_wallet_unloaded(self):
        """Slot to handle the wallet_unloaded signal."""
        logger.info("ActiveTradesTab: Wallet unloaded signal received.")
        self.current_wallet_address = None
        self.clear_trade_list()
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0) # Go back to list view

    @Slot(int)
    def handle_info_request(self, trade_id):
        logger.info(f"Info requested for trade_id: {trade_id}")
        self.info_page.load_trade_info(trade_id)
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(2) # Switch to Info page 1

    @Slot(int)
    def handle_pause_toggle_request(self, trade_id):
        logger.info(f"Pause/Resume requested for trade_id: {trade_id}")
        try:
            # Toggle the trade's active state in the database
            success = self.trade_manager.toggle_trade_active_state(trade_id)
            
            if success and trade_id in self.active_trades_widgets:
                # Get the updated trade info to know the current state
                trade_info = self.trade_manager.get_trade_by_id(trade_id)
                if trade_info:
                    is_active = trade_info.get('is_active', 0) == 1
                    # Update the widget UI without reloading the entire list
                    self.active_trades_widgets[trade_id].update_active_state(is_active)
                    logger.info(f"Trade {trade_id} active state updated to: {'Active' if is_active else 'Paused'}")
                else:
                    logger.warning(f"Could not retrieve updated trade info for trade_id {trade_id}")
                    # Fallback to reloading the list
                    self.load_active_trades(self.current_wallet_address)
            else:
                logger.warning(f"Failed to toggle trade state or trade widget not found, reloading full list")
                # Fallback to reloading the list
                self.load_active_trades(self.current_wallet_address)
        except Exception as e:
            logger.error(f"Failed to toggle trade state for trade_id {trade_id}: {e}", exc_info=True)
            self.load_active_trades(self.current_wallet_address) # Reload as fallback

    @Slot(int)
    def handle_edit_request(self, trade_id):
        logger.info(f"Edit requested for trade_id: {trade_id}")
        self.edit_page.load_trade_for_edit(trade_id)
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(3) # Switch to Edit page 2

    @Slot(int)
    def handle_delete_request(self, trade_id):
        logger.info(f"Delete requested for trade_id: {trade_id}")
        self.delete_page.prepare_for_delete(trade_id)
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(1) # Switch to Delete page 3

    @Slot(int)
    def handle_trade_update(self, trade_id):
        """Called when a trade is updated, refreshes the list and info page."""
        logger.info(f"Refreshing UI for updated trade_id: {trade_id}")
        self.load_active_trades(self.current_wallet_address) # Reload the whole list to reflect changes
        self.info_page.load_trade_info(trade_id) # Refresh the info page as well

    @Slot()
    def handle_trade_created(self):
        """Called when a new trade is created, refreshes the active trades list."""
        if self.current_wallet_address:
            logger.info("New trade created, refreshing active trades list")
            self.load_active_trades(self.current_wallet_address)
        else:
            logger.warning("Cannot refresh active trades - no wallet address available")

    def _refresh_active_trades(self):
        """Refresh the active trades list using the current wallet address."""
        if self.current_wallet_address:
            logger.debug(f"Refreshing active trades for wallet {self.current_wallet_address}")
            self.load_active_trades(self.current_wallet_address)
        else:
            logger.debug("Cannot refresh active trades - no wallet address available")
    
    def connect_refresh_service(self, refresh_service):
        """
        Connect to the UI refresh service for automatic updates.
        
        Args:
            refresh_service: QtUIRefreshService instance
        """
        if refresh_service:
            refresh_service.refresh_active_trades.connect(self._refresh_active_trades)
            refresh_service.refresh_active_trades.connect(self.info_page.refresh_if_viewing)
            logger.info("Active trades list and info page connected to UI refresh service")

    # Add methods to manage trade widgets and bot threads as needed