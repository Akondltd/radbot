from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QTimer
from .token_display import TokenDisplayWidget
from core.radix_network import RadixNetwork
import logging

logger = logging.getLogger(__name__)

class TokenBalancesManager:
    def __init__(self, parent: QWidget, scroll_area: QScrollArea, wallet: 'RadixWallet'):
        self.parent = parent
        self.scroll_area = scroll_area
        self.wallet = wallet
        self.radix_network = RadixNetwork()
        self.setup_layout()
        self.setup_timer()

    def setup_layout(self):
        """Set up the layout for token balances."""
        self.scroll_area.setWidgetResizable(True)
        self.widget = self.scroll_area.widget()
        self.layout = QVBoxLayout(self.widget)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(10, 10, 10, 10)

    def setup_timer(self):
        """Set up the refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(30000)  # 30 seconds
        self.refresh_timer.timeout.connect(self.refresh_balances)
        self.refresh_timer.start()

    def refresh_balances(self):
        """Refresh the token balances display."""
        if not self.wallet:
            return

        try:
            balances = self.radix_network.get_token_balances(self.wallet.public_address)
            self.update_display(balances)
            logger.debug(f"Refreshed token balances for wallet {self.wallet.public_address[:8]}...")
        except Exception as e:
            logger.error(f"Error refreshing token balances: {e}")
            self.show_error(f"Failed to refresh token balances: {str(e)}")

    def update_display(self, balances: dict):
        """Update the display with new balances."""
        # Clear existing widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new token display widgets
        for token, balance in balances.items():
            widget = TokenDisplayWidget(token, balance)
            self.layout.addWidget(widget)

    def show_error(self, message: str):
        """Show an error message."""
        QMessageBox.critical(self.parent, "Akond Rad Bot", message)

    def stop_timer(self):
        """Stop the refresh timer."""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
