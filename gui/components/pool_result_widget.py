from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PoolResultWidget(QWidget):
    """Widget displaying a single pool search result."""
    
    pool_clicked = Signal(dict)  # Emits pool data when clicked
    
    def __init__(self, pool_data: Dict, parent=None):
        super().__init__(parent)
        self.pool_data = pool_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Top row: Token pair
        pair_layout = QHBoxLayout()
        
        token_a_symbol = self.pool_data.get('token_a_symbol', 'Unknown')
        token_b_symbol = self.pool_data.get('token_b_symbol', 'Unknown')
        
        pair_label = QLabel(f"{token_a_symbol} / {token_b_symbol}")
        pair_font = QFont()
        pair_font.setBold(True)
        pair_font.setPointSize(11)
        pair_label.setFont(pair_font)
        pair_layout.addWidget(pair_label)
        
        pair_layout.addStretch()
        layout.addLayout(pair_layout)
        
        # Middle row: Liquidity
        liquidity_usd = self.pool_data.get('liquidity_usd')
        if liquidity_usd:
            liquidity_label = QLabel(f"Liquidity: ${liquidity_usd:,.2f}")
            liquidity_label.setStyleSheet("color: #666;")
            layout.addWidget(liquidity_label)
        else:
            liquidity_label = QLabel("Liquidity: Unknown")
            liquidity_label.setStyleSheet("color: #999;")
            layout.addWidget(liquidity_label)
        
        # Bottom row: Pool address (truncated)
        pool_address = self.pool_data.get('pool_address', '')
        if len(pool_address) > 20:
            pool_display = f"{pool_address[:12]}...{pool_address[-8:]}"
        else:
            pool_display = pool_address
            
        address_label = QLabel(f"Pool: {pool_display}")
        address_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(address_label)
        
        # Make widget clickable
        self.setStyleSheet("""
            QWidget {
                background-color: #3c3c3c;
                border: 1px solid #666;
                border-radius: 5px;
            }
            QWidget:hover {
                background-color: #0078d7;
                border: 1px solid #0078d7;
            }
        """)
        
        self.setCursor(Qt.PointingHandCursor)
        
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.LeftButton:
            logger.info(f"Pool clicked: {self.pool_data.get('token_a_symbol')}/{self.pool_data.get('token_b_symbol')}")
            self.pool_clicked.emit(self.pool_data)
        super().mousePressEvent(event)
