import logging
from datetime import datetime
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from database.trade_manager import TradeManager
from gui.active_trades_ui import Ui_ActiveTradesTabMain

logger = logging.getLogger(__name__)

class ActiveTradeDeletePage(QWidget):
    """Manages the 'Delete' page of the Active Trades tab."""
    trade_deleted = Signal()

    def __init__(self, ui: Ui_ActiveTradesTabMain, trade_manager: TradeManager, parent=None):
        super().__init__(parent)
        self.ui = ui
        self.trade_manager = trade_manager
        self.current_trade_id = None

        # Setup connections for the delete page buttons
        self.ui.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton.clicked.connect(self.go_back_to_info)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton.clicked.connect(self.confirm_delete)

    def prepare_for_delete(self, trade_id: int):
        """Stores the trade_id and displays trade details for confirmation."""
        self.current_trade_id = trade_id
        logger.info(f"Delete confirmation page prepared for trade_id: {trade_id}")
        
        # Fetch and display trade details so user can verify
        try:
            trade_data = self.trade_manager.get_trade_by_id(trade_id)
            if trade_data:
                self._update_delete_page_content(trade_data)
            else:
                logger.warning(f"Could not fetch trade data for trade_id {trade_id}")
                self._show_minimal_delete_page(trade_id)
        except Exception as e:
            logger.error(f"Error fetching trade data for delete page: {e}", exc_info=True)
            self._show_minimal_delete_page(trade_id)
    
    def _update_delete_page_content(self, trade_data: dict):
        """Update the delete page with trade details."""
        # Extract trade information
        trade_id = trade_data.get('trade_id', 'N/A')
        base_symbol = trade_data.get('base_token_symbol', '???')
        quote_symbol = trade_data.get('quote_token_symbol', '???')
        pair_display = f"{base_symbol}/{quote_symbol}"
        
        strategy_name = trade_data.get('strategy_name', 'Unknown')
        start_amount = trade_data.get('start_amount', 0)
        start_token_symbol = trade_data.get('start_token_symbol', '')
        
        # Format creation date
        creation_timestamp = trade_data.get('created_at')
        if creation_timestamp:
            try:
                creation_date = datetime.fromtimestamp(creation_timestamp).strftime('%d %b %Y at %H:%M')
            except:
                creation_date = 'Unknown'
        else:
            creation_date = 'Unknown'
        
        # Format start amount
        try:
            start_amount_formatted = f"{float(start_amount):,.8f}".rstrip('0').rstrip('.')
        except:
            start_amount_formatted = str(start_amount)
        
        # Get current value if available
        current_holdings = trade_data.get('current_holdings_amount', 0)
        current_token = trade_data.get('current_token_symbol', '')
        try:
            current_holdings_formatted = f"{float(current_holdings):,.8f}".rstrip('0').rstrip('.')
        except:
            current_holdings_formatted = str(current_holdings)
        
        # Build detailed confirmation message
        details_html = f"""<html><head/><body>
<p style="font-size: 11pt; margin-bottom: 10px;"><b>You are about to delete the following trade:</b></p>
<table style="margin-left: 20px; font-size: 10pt;">
<tr><td style="padding-right: 15px;"><b>Trade ID:</b></td><td>#{trade_id}</td></tr>
<tr><td style="padding-right: 15px;"><b>Pair:</b></td><td>{pair_display}</td></tr>
<tr><td style="padding-right: 15px;"><b>Strategy:</b></td><td>{strategy_name}</td></tr>
<tr><td style="padding-right: 15px;"><b>Created:</b></td><td>{creation_date}</td></tr>
<tr><td style="padding-right: 15px;"><b>Starting Amount:</b></td><td>{start_amount_formatted} {start_token_symbol}</td></tr>
<tr><td style="padding-right: 15px;"><b>Current Holdings:</b></td><td>{current_holdings_formatted} {current_token}</td></tr>
</table>
<p style="margin-top: 15px; color: #ff6b6b;"><b>⚠ Warning:</b> This action cannot be undone. All trade history and statistics for this trade will be permanently lost.</p>
</body></html>"""
        
        self.ui.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setText(details_html)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setText(f"Delete Trade #{trade_id}")
        
    def _show_minimal_delete_page(self, trade_id: int):
        """Show minimal delete page when trade data can't be fetched."""
        self.ui.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setText(f"Delete Trade #{trade_id}")
        self.ui.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setText(
            "<html><head/><body><p>Are you sure you would like to delete this trade? "
            "Once deleted it cannot be undone. All trade data will be lost.</p></body></html>"
        )

    def confirm_delete(self):
        """Proceeds with deleting the trade from the database."""
        if self.current_trade_id is None:
            logger.error("confirm_delete called with no active trade_id.")
            return

        try:
            self.trade_manager.delete_trade(self.current_trade_id)
            logger.info(f"Successfully deleted trade {self.current_trade_id}")
            print(f"Trade {self.current_trade_id} has been deleted and funds returned to wallet")
            self.trade_deleted.emit()
            self.go_to_list() # Go back to the main list after deletion

        except Exception as e:
            logger.error(f"Failed to delete trade {self.current_trade_id}: {e}", exc_info=True)
            print(f"Failed to delete trade {self.current_trade_id}: {e}")

    def go_back_to_info(self):
        """Switches the stacked widget back to the info view (index 1)."""
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0)

    def go_to_list(self):
        """Switches the stacked widget back to the list view (index 0)."""
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0)
