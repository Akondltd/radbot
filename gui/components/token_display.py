from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QHBoxLayout, QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDoubleValidator, QPixmap
from radix_engine_toolkit import Decimal as RETDecimal
from config.app_config import get_absolute_path
from decimal import Decimal
from utils.decimal_utils import DecimalUtils
import logging

logger = logging.getLogger(__name__)

class TokenDisplayWidget(QWidget):
    max_clicked = Signal(str)  # Emits token_rri when Max button clicked
    
    def __init__(self, token_name: str, token_symbol: str, token_amount: float, token_rri: str, divisibility: int, icon_local_path: str = None, parent=None):
        super().__init__(parent)
        self.token_name = token_name
        self.token_symbol = token_symbol
        self.balance = token_amount  # Store the balance
        self.token_rri = token_rri
        self.divisibility = divisibility
        self.icon_local_path = icon_local_path
        self.setup_ui()
        self.update_balance(token_amount)

    def setup_ui(self):
        # Create main layout
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        layout.addWidget(self.icon_label)

        # Load icon pixmap
        if self.icon_local_path:
            absolute_path = get_absolute_path(self.icon_local_path)
            if absolute_path and absolute_path.is_file():
                pixmap = QPixmap(str(absolute_path))
                if not pixmap.isNull():
                    self.icon_label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    logger.warning(f"Failed to load icon for {self.token_symbol} from path: {absolute_path}")
            else:
                logger.debug(f"Icon file not found for {self.token_symbol} at path: {absolute_path}")

        # Token label - show symbol, tooltip shows full name
        self.token_label = QLabel(self.token_symbol)
        self.token_label.setToolTip(self.token_name)  # Full name on hover
        self.token_label.setMinimumWidth(60)  # Fixed width for alignment
        token_font = QFont("Arial", 10)
        token_font.setBold(True)
        self.token_label.setFont(token_font)
        self.token_label.setStyleSheet("color: #FFFFFF;") # Default white text
        layout.addWidget(self.token_label)

        # Balance label
        self.balance_label = QLabel()
        self.balance_label.setMinimumWidth(120)  # Fixed width for alignment
        self.balance_label.setFont(QFont("Arial", 10))
        self.balance_label.setStyleSheet("color: #FFFFFF;") # Default white text
        layout.addWidget(self.balance_label)

        # Withdrawal input
        self.withdraw_input = QLineEdit()
        self.withdraw_input.setPlaceholderText("Withdraw amount")
        self.withdraw_input.setMaximumWidth(150)
        self.withdraw_input.setValidator(QDoubleValidator(0.0, 999999999.99999999, 8))
        # Use RRI or symbol for unique object name if needed, symbol is likely fine
        self.withdraw_input.setObjectName(f"withdraw_{self.token_symbol}")
        self.withdraw_input.setStyleSheet(
            "border: 1px solid #1e293b; "         # Theme border
            "color: #ffffff; "                    # White text
            "background-color: #0a0e27; "         # Theme background
            "border-radius: 6px; "                # Rounded corners
            "padding: 2px 4px;"                   # Better padding
        )
        layout.addWidget(self.withdraw_input)
        
        # Max button - now uses theme QSS gradient styling
        self.max_button = QPushButton("Max")
        self.max_button.setMaximumWidth(50)
        # Remove hardcoded styling to use theme QSS blue→cyan gradient
        self.max_button.clicked.connect(self._on_max_clicked)
        layout.addWidget(self.max_button)

    def update_balance(self, amount: float):
        self.balance = amount  # Update the stored balance
        
        # Convert to Decimal for precise formatting
        amount_decimal = Decimal(str(amount))
        
        # Use DecimalUtils for consistent formatting
        # Show 8 decimals for most tokens, but respect divisibility
        display_decimals = min(8, self.divisibility)
        formatted_balance = DecimalUtils.format_for_display(amount_decimal, display_decimals)
        
        # Add thousands separator
        parts = formatted_balance.split('.')
        parts[0] = f"{int(parts[0]):,}"
        formatted_balance = '.'.join(parts)
        
        self.balance_label.setText(formatted_balance)

    def get_withdraw_amount(self) -> RETDecimal:
        try:
            text = self.withdraw_input.text().strip()
            return RETDecimal(text) if text else RETDecimal("0.0")
        except Exception: 
            return RETDecimal("0.0")

    def set_withdraw_amount(self, amount: float):
        self.withdraw_input.setText(f"{amount:.8f}")
    
    def get_withdraw_amount_text(self) -> str:
        """Get the raw text from withdraw input field"""
        return self.withdraw_input.text().strip()
    
    def set_withdraw_amount_text(self, text: str):
        """Set the withdraw input field to exact text (preserves user format)"""
        self.withdraw_input.setText(text)
    
    def _on_max_clicked(self):
        """Handle Max button click - emit signal for parent to handle"""
        self.max_clicked.emit(self.token_rri)
