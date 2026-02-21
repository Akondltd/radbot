from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QListWidget, QListWidgetItem, QPushButton, QLabel)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont, QIcon
from typing import List, Dict, Optional, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# XRD address constant
RADIX_XRD_ADDRESS = "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd"
from config.paths import PACKAGE_ROOT
DEFAULT_ICON_PATH = PACKAGE_ROOT / 'images' / 'default_token_icon.png'


class TokenSelectionDialog(QDialog):
    """Dialog for selecting a token from the database."""
    
    token_selected = Signal(dict)  # Emits the selected token dict
    
    def __init__(self, tokens: List[Dict], parent=None, exclude_symbols: Optional[Set[str]] = None, xrd_first: bool = True):
        """
        Initialize the token selection dialog.
        
        Args:
            tokens: List of token dictionaries
            parent: Parent widget
            exclude_symbols: Set of token symbols to exclude (e.g., {'XRD'} to exclude XRD)
            xrd_first: If True, sort XRD to the top of the list
        """
        super().__init__(parent)
        self.exclude_symbols = {s.upper() for s in (exclude_symbols or set())}
        
        # Filter out excluded symbols
        filtered_tokens = [t for t in tokens if t.get('symbol', '').upper() not in self.exclude_symbols]
        
        # Prioritize XRD at the top (if not excluded), then sort rest alphabetically
        self.tokens = self._sort_tokens_with_xrd_first(filtered_tokens) if xrd_first else filtered_tokens
        self.selected_token = None
        
        self.setWindowTitle("Select Token")
        self.setMinimumSize(400, 500)
        
        self._setup_ui()
        self._populate_tokens()
        
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Search box
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by symbol or name...")
        self.search_field.textChanged.connect(self._filter_tokens)
        layout.addWidget(self.search_field)
        
        # Token list
        self.token_list = QListWidget()
        self.token_list.itemDoubleClicked.connect(self._on_token_double_clicked)
        layout.addWidget(self.token_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self._on_select_clicked)
        self.select_button.setEnabled(False)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect selection change
        self.token_list.itemSelectionChanged.connect(self._on_selection_changed)
        
    def _sort_tokens_with_xrd_first(self, tokens: List[Dict]) -> List[Dict]:
        """
        Sort tokens with XRD at the top, then alphabetically by symbol.
        """
        xrd_tokens = []
        other_tokens = []
    
        for token in tokens:
            symbol = token.get('symbol', '').upper()
            address = token.get('address', '')
        
            is_radix_xrd = (symbol == 'XRD' and address == RADIX_XRD_ADDRESS)
        
            if is_radix_xrd:
                xrd_tokens.append(token)
            else:
                other_tokens.append(token)
    
        # Sort other tokens alphabetically by symbol
        other_tokens.sort(key=lambda t: t.get('symbol', '').upper())
    
        return xrd_tokens + other_tokens
    
    def _populate_tokens(self):
        """Populate the token list with icons."""
        self.token_list.clear()
        self.token_list.setIconSize(QSize(24, 24))  # Set icon size for list items
        
        for token in self.tokens:
            # Skip tokens without valid price data (too cheap = likely junk, too expensive = bad data)
            price_usd = token.get('price_usd')
            if not price_usd or price_usd <= 0.00005 or price_usd >= 1_000_000_000:
                continue
            
            item = QListWidgetItem()
            
            # Format display text
            symbol = token.get('symbol', 'Unknown')
            name = token.get('name', '')
            display_text = f"{symbol} - {name} (${price_usd:.4f})"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, token)  # Store full token data
            
            # Set icon for the token
            icon_path = token.get('icon_local_path')
            if icon_path:
                full_path = Path(icon_path)
                if not full_path.is_absolute():
                    # Relative path - resolve from project root
                    full_path = PACKAGE_ROOT / icon_path
                if full_path.exists():
                    item.setIcon(QIcon(str(full_path)))
                else:
                    item.setIcon(QIcon(str(DEFAULT_ICON_PATH)))
            else:
                item.setIcon(QIcon(str(DEFAULT_ICON_PATH)))
            
            # Highlight XRD for easy identification
            if symbol.upper() == 'XRD':
                font = QFont()
                font.setBold(True)
                item.setFont(font)
            
            self.token_list.addItem(item)
            
    def _filter_tokens(self, search_text: str):
        """Filter tokens based on search text."""
        search_text = search_text.lower()
        
        for i in range(self.token_list.count()):
            item = self.token_list.item(i)
            token = item.data(Qt.UserRole)
            
            # Search in symbol and name
            symbol = token.get('symbol', '').lower()
            name = token.get('name', '').lower()
            
            matches = search_text in symbol or search_text in name
            item.setHidden(not matches)
            
    def _on_selection_changed(self):
        """Handle selection change."""
        selected_items = self.token_list.selectedItems()
        self.select_button.setEnabled(len(selected_items) > 0)
        
    def _on_token_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on token."""
        self.selected_token = item.data(Qt.UserRole)
        self.accept()
        
    def _on_select_clicked(self):
        """Handle select button click."""
        selected_items = self.token_list.selectedItems()
        if selected_items:
            self.selected_token = selected_items[0].data(Qt.UserRole)
            self.accept()
            
    def get_selected_token(self) -> Optional[Dict]:
        """Get the selected token after dialog closes."""
        return self.selected_token
