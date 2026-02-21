"""
Simple Pair Result Widget - Displays tradeable pair from any source
Shows pair name and basic info, clickable to add to trade_pairs
"""
import logging
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class SimplePairResultWidget(QWidget):
    """
    Simplified widget to display a tradeable pair.
    Works for both Ociswap pools and Astrolescent routes.
    """
    
    pair_clicked = Signal(dict)  # Emits pair data when clicked
    
    def __init__(self, pair_data: Dict, parent=None):
        super().__init__(parent)
        self.pair_data = pair_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Top row: Token pair
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        
        token_a_symbol = self.pair_data.get('token_a_symbol', 'Unknown')
        token_b_symbol = self.pair_data.get('token_b_symbol', 'Unknown')
        
        pair_label = QLabel(f"{token_a_symbol} / {token_b_symbol}")
        pair_font = QFont()
        pair_font.setBold(True)
        pair_font.setPointSize(11)
        pair_label.setFont(pair_font)
        pair_layout.addWidget(pair_label)
        
        pair_layout.addStretch()
        layout.addLayout(pair_layout)
        
        # Bottom row: Source info
        source_type = self.pair_data.get('source', 'unknown')
        
        if source_type == 'ociswap':
            # Show Ociswap indicator
            source_label = QLabel("✓ Direct pool available")
            source_label.setStyleSheet("color: #4CAF50; font-size: 9pt;")  # Green
        elif source_type == 'astrolescent':
            # Show Astrolescent route info
            price_impact = self.pair_data.get('price_impact', 0)
            feasible = self.pair_data.get('feasible', False)
            
            if feasible:
                source_label = QLabel(f"✓ Route available ({price_impact:.1f}% impact)")
                source_label.setStyleSheet("color: #4CAF50; font-size: 9pt;")  # Green
            else:
                source_label = QLabel(f"⚠ Route available ({price_impact:.1f}% impact)")
                source_label.setStyleSheet("color: #FF9800; font-size: 9pt;")  # Orange
        else:
            source_label = QLabel("Available")
            source_label.setStyleSheet("color: #999; font-size: 9pt;")
            
        layout.addWidget(source_label)
        
        # Make widget clickable with hover effect
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0e27;
                border: 1px solid #1e293b;
                border-radius: 5px;
            }
            QWidget:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                stop:0 #2d7efb, stop:1 #20dcff);
                border: 1px solid #1e293b;
            }
        """)
        
        self.setCursor(Qt.PointingHandCursor)
        
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.LeftButton:
            token_a = self.pair_data.get('token_a_symbol', 'Unknown')
            token_b = self.pair_data.get('token_b_symbol', 'Unknown')
            source = self.pair_data.get('source', 'unknown')
            logger.info(f"Pair clicked: {token_a}/{token_b} (source: {source})")
            self.pair_clicked.emit(self.pair_data)
        super().mousePressEvent(event)
