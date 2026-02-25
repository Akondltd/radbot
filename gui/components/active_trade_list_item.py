import logging
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap, Qt
from pathlib import Path
from config.paths import PACKAGE_ROOT
from config.app_config import get_absolute_path
from ..overlapping_icon_widget import OverlappingIconWidget
from database.tokens import TokenManager

logger = logging.getLogger(__name__)

class ActiveTradeListItemWidget(QWidget):
    """A widget representing a single active trade in a list."""
    info_requested = Signal(int)
    edit_requested = Signal(int)
    pause_toggle_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, trade_data: dict, token_manager: TokenManager, parent=None, index=0):
        super().__init__(parent)
        self.setAutoFillBackground(True) # Required for background styling
        self.trade_id = trade_data['trade_id']
        self.token_manager = token_manager
        self.is_active = trade_data.get('is_active', 1) == 1

        # --- Prepare data for display ---
        base_symbol = trade_data.get('base_token_symbol', '???')
        quote_symbol = trade_data.get('quote_token_symbol', '???')
        tickers_text = f"{base_symbol}-{quote_symbol}"

        # Show current trade position (not starting position)
        trade_amount = trade_data.get('trade_amount', '0')
        trade_token_address = trade_data.get('trade_token_address')
        trade_token_info = self.token_manager.get_token_by_address(trade_token_address) if trade_token_address else None
        trade_token_symbol = trade_token_info.get('symbol', '') if trade_token_info else ''
        
        # Format amount to max 8 decimal places, strip trailing zeros
        try:
            amount_float = float(trade_amount)
            amount_formatted = f"{amount_float:.8f}".rstrip('0').rstrip('.')
        except (ValueError, TypeError):
            amount_formatted = str(trade_amount)
        
        amount_text = f"{amount_formatted} {trade_token_symbol}"

        strategy_text = trade_data.get('strategy_name', 'N/A')
        state_text = "ACTIVE" if self.is_active else "PAUSED"
        
        # Calculate and format profit display
        total_profit = trade_data.get('total_profit', '0')
        try:
            profit_float = float(total_profit)
            # Format with appropriate precision, strip trailing zeros
            if abs(profit_float) < 0.0001 and profit_float != 0:
                profit_formatted = f"{profit_float:.8f}".rstrip('0').rstrip('.')
            else:
                profit_formatted = f"{profit_float:.4f}".rstrip('0').rstrip('.')
            
            # Add + prefix for positive profits
            if profit_float > 0:
                profit_text = f"+{profit_formatted}"
                profit_color = "#22c55e"  # Green
            elif profit_float < 0:
                profit_text = profit_formatted  # Already has minus sign
                profit_color = "#ef4444"  # Red
            else:
                profit_text = "0"
                profit_color = "#94a3b8"  # Gray/neutral
        except (ValueError, TypeError):
            profit_text = "N/A"
            profit_color = "#94a3b8"

        # --- Create Widgets ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5) # Add padding
        layout.setSpacing(10) # Add spacing between elements

        self.trade_id_label = QLabel(f"#{self.trade_id}")
        self.icon_widget = OverlappingIconWidget()
        self._set_token_icons(trade_data.get('base_token'), trade_data.get('quote_token'))

        self.tickers_label = QLabel(tickers_text)
        self.amount_label = QLabel(amount_text)
        self.strategy_label = QLabel(strategy_text)
        
        # Profit label with color coding
        self.profit_label = QLabel(profit_text)
        self.profit_label.setStyleSheet(f"color: {profit_color}; font-weight: bold;")
        self.profit_label.setToolTip(f"Total profit: {profit_text} {trade_token_symbol}")
        
        self.state_label = QLabel(state_text)
        
        # Add LED status indicator
        self.led_label = QLabel()
        self.update_status_led()

        self.info_button = QPushButton("Info")
        self.edit_button = QPushButton("Edit")
        self.pause_button = QPushButton(" Pause " if self.is_active else "Restart")
        self.delete_button = QPushButton("Delete")
        
        # Apply text-only styling with background on hover (reduces eye strain)
        text_button_style = """
            QPushButton {
                background: transparent;
                border: none;
                color: #FFFFFF;
                padding: 4px 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #0D6EFD, stop:1 #00D4FF);
                border-radius: 4px;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #0a5dd6, stop:1 #00b8dd);
                border-radius: 4px;
            }
        """
        
        self.info_button.setStyleSheet(text_button_style)
        self.edit_button.setStyleSheet(text_button_style)
        self.pause_button.setStyleSheet(text_button_style)
        self.delete_button.setStyleSheet(text_button_style)

        # --- Connect Signals ---
        self.info_button.clicked.connect(lambda: self.info_requested.emit(self.trade_id))
        self.edit_button.clicked.connect(lambda: self.edit_requested.emit(self.trade_id))
        self.pause_button.clicked.connect(lambda: self.pause_toggle_requested.emit(self.trade_id))
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.trade_id))

        # --- Arrange Layout ---
        layout.addWidget(self.trade_id_label, 0)
        layout.addWidget(self.icon_widget, 0)
        layout.addWidget(self.tickers_label, 2)
        layout.addWidget(self.amount_label, 3)
        layout.addWidget(self.strategy_label, 2)
        layout.addWidget(self.profit_label, 2)  # Profit with color coding
        layout.addWidget(self.state_label, 1)
        layout.addWidget(self.led_label, 1)  # Add LED label next to state text
        #  layout.addStretch(1)
        layout.addWidget(self.info_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

        # --- Styling for alternating colors and rounded corners ---
        # Use theme colors: #0f172a (primary) and #0a0e27 (secondary)
        if index % 2 == 0:
            self.setStyleSheet("background-color: #0f172a; border-radius: 5px;")
        else:
            self.setStyleSheet("background-color: #0a0e27; border-radius: 5px;")
            
    def update_status_led(self):
        """Update the LED status indicator based on trade active state."""
        if self.is_active:
            led_path = PACKAGE_ROOT / "images" / "greenLED.png"
        else:
            led_path = PACKAGE_ROOT / "images" / "redLED.png"
            
        if led_path.is_file():
            pixmap = QPixmap(str(led_path))
            # Resize to 20x20 as specified
            pixmap = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
            self.led_label.setPixmap(pixmap)
        else:
            logger.warning(f"LED image not found at {led_path}")
            self.led_label.setText("●")  # Fallback to text bullet
            
    def update_active_state(self, is_active):
        """Update the widget to reflect the new active state."""
        self.is_active = is_active
        self.state_label.setText("ACTIVE" if is_active else "PAUSED")
        self.pause_button.setText(" Pause " if is_active else "Restart")
        self.update_status_led()

    def _set_token_icons(self, base_token_address, quote_token_address):
        pixmap1 = self._load_pixmap_for_token(base_token_address)
        pixmap2 = self._load_pixmap_for_token(quote_token_address)
        self.icon_widget.set_icons(pixmap1, pixmap2)

    def _load_pixmap_for_token(self, token_address: str) -> QPixmap:
        """Loads a QPixmap for a token, using a default if not found."""
        default_icon_path = PACKAGE_ROOT / "images" / "default_token_icon.png"
        pixmap = QPixmap(str(default_icon_path))

        if not token_address:
            return pixmap

        try:
            token_info = self.token_manager.get_token_by_address(token_address)
            if token_info and token_info.get('icon_local_path'):
                icon_path = get_absolute_path(token_info['icon_local_path'])
                if icon_path and icon_path.is_file():
                    loaded_pixmap = QPixmap(str(icon_path))
                    if not loaded_pixmap.isNull():
                        pixmap = loaded_pixmap
                else:
                    logger.warning(f"Icon path in DB for {token_address} does not exist: {icon_path}")
        except Exception as e:
            logger.error(f"Error loading icon for {token_address}: {e}", exc_info=True)
        
        return pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def update_signal(self, new_signal: str):
        """Updates the displayed signal text."""
        self.signal_label.setText(new_signal)
