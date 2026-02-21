from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class TradeStatistics(QFrame):
    """Component for displaying trade statistics in a clean, minimal layout"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumSize(350, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Store label references for dynamic font sizing
        self.all_labels = []
        
        # Main layout - small top margin to position content higher
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title - font will be set dynamically
        self.title = QLabel("Trade Statistics")
        self.title.setStyleSheet("color: white; font-weight: bold;")
        self.title.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title)
        
        # Grid for statistics with minimal spacing
        self.stats_grid = QGridLayout()
        self.stats_grid.setVerticalSpacing(3)
        self.stats_grid.setHorizontalSpacing(5)
        layout.addLayout(self.stats_grid)
        
        # Add stretch to push everything upward
        layout.addStretch(1)
        
        # Set up statistics in two columns
        left_stats = [
            ("trades_created", "Trades Created:", "0"),
            ("profitable_trades", "Profitable Trades:", "0"),
            ("most_profitable_strategy", "Most Profitable:", "None"),
            ("tokens_traded", "Tokens Traded:", "0"),
        ]
        
        right_stats = [
            ("trades_cancelled", "Trades Deleted:", "0"),
            ("unprofitable_trades", "Unprofitable Trades:", "0"),
            ("completed_trades", "Completed Trades:", "0"),
            ("trade_pairs", "Trade Pairs Selected:", "0"),
        ]
        
        # Add left column
        for row, (key, label_text, value_text) in enumerate(left_stats):
            self._add_stat_item(row, 0, key, label_text, value_text)
        
        # Add right column
        for row, (key, label_text, value_text) in enumerate(right_stats):
            self._add_stat_item(row, 2, key, label_text, value_text)
    
    def _add_stat_item(self, row, col, key, label_text, value_text):
        """Helper method to add a statistic item to the grid"""
        label = QLabel(label_text)
        label.setStyleSheet("color: #aaaaaa;")
        self.stats_grid.addWidget(label, row, col)
        self.all_labels.append(label)
        
        value = QLabel(value_text)
        value.setObjectName(f"value_{key}")
        value.setStyleSheet("color: white;")
        self.stats_grid.addWidget(value, row, col + 1)
        self.all_labels.append(value)
    
    def resizeEvent(self, event):
        """Handle resize to scale fonts dynamically"""
        super().resizeEvent(event)
        
        # Calculate font sizes based on widget height
        widget_height = self.height()
        
        # Base sizes: title=14px, stats=10px at 250px height
        base_height = 250.0
        scale_factor = max(0.7, min(1.5, widget_height / base_height))  # Constrain scaling
        
        title_size = max(10, int(14 * scale_factor))
        stats_size = max(8, int(10 * scale_factor))
        
        # Update title font
        title_font = self.title.font()
        title_font.setPointSize(title_size)
        title_font.setBold(True)
        self.title.setFont(title_font)
        
        # Update all stat label fonts
        for label in self.all_labels:
            font = label.font()
            font.setPointSize(stats_size)
            label.setFont(font)
    
    def update_stats(self, stats_dict):
        """Update the statistics with new values"""
        for key, value in stats_dict.items():
            value_label = self.findChild(QLabel, f"value_{key}")
            if value_label:
                value_label.setText(str(value))
