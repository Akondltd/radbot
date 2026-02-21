import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from gui.components.profit_loss_chart import ProfitLossChart
from gui.components.token_distribution_chart import TokenDistributionChart
from gui.components.volume_chart import VolumeChart
from gui.components.trade_statistics import TradeStatistics
from services.dashboard_service import DashboardDataService

logger = logging.getLogger(__name__)

class DashboardTabMain(QWidget):
    """Main dashboard tab displaying all charts and statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data service for fetching dashboard data
        self.data_service = DashboardDataService()
        
        # Store references to labels for dynamic font sizing
        self.summary_title_labels = []
        self.summary_value_labels = []
        
        # Create and setup UI
        self.setup_ui()
        
        # Setup refresh timer (update every hour)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(60000)  # 1 minute
        
        # Initial data load
        self.refresh_dashboard()

    def setup_ui(self):
        """Set up the dashboard UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create our custom widgets
        self.profit_loss_chart = ProfitLossChart(self)
        self.token_distribution_chart = TokenDistributionChart(self)
        self.volume_chart = VolumeChart(self)
        self.trade_stats = TradeStatistics(self)
        
        # Create our main container widget that will hold everything
        container = QWidget(self)
        # Make container transparent so parent background shows through
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background-color: transparent;")
        
        # Create the layout for our container
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        
        # Top row - Summary widgets
        self.summary_frame = QFrame(self)
        # Background from theme QSS (QFrame styling)
        self.summary_frame.setMinimumHeight(80)  # Minimum height for readability
        # Removed max height and fixed policy - let it scale naturally
        self.summary_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        summary_layout = QGridLayout(self.summary_frame)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create summary widgets
        summary_items = [
            ("Total Wallet Value", "0 XRD", "wallet_value"),
            ("Total Profit", "0 XRD", "profit"),
            ("Active Trades", "0", "active_trades"),
            ("Win Ratio", "0.00 %", "win_ratio")
        ]
        
        for col, (title, value, obj_name) in enumerate(summary_items):
            item_layout = QVBoxLayout()
            item_layout.setSpacing(5)
            
            # Title label - font will be set dynamically in resizeEvent
            title_label = QLabel(title)
            title_label.setObjectName("secondary_text")  # Theme secondary text
            title_label.setAlignment(Qt.AlignCenter)
            self.summary_title_labels.append(title_label)
            
            # Value label - font will be set dynamically in resizeEvent
            value_label = QLabel(value)
            value_label.setObjectName(f"summary_{obj_name}")
            value_label.setStyleSheet("font-weight: bold;")
            value_label.setAlignment(Qt.AlignCenter)
            self.summary_value_labels.append(value_label)
            
            item_layout.addWidget(title_label)
            item_layout.addWidget(value_label)
            summary_layout.addLayout(item_layout, 0, col)
        
        # Add summary frame to container
        container_layout.addWidget(self.summary_frame)
        
        # Middle row - Profit/Loss Chart and Token Distribution
        middle_row = QHBoxLayout()
        middle_row.addWidget(self.profit_loss_chart)
        middle_row.addWidget(self.token_distribution_chart)
        container_layout.addLayout(middle_row)
        
        # Bottom row - Volume Chart and Trade Statistics
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.volume_chart)
        bottom_row.addWidget(self.trade_stats)
        container_layout.addLayout(bottom_row)
        
        # Add the container to the main layout
        main_layout.addWidget(container)
        
    def resizeEvent(self, event):
        """Handle window resize to scale fonts dynamically"""
        super().resizeEvent(event)
        
        # Calculate font sizes based on widget height
        widget_height = self.height()
        
        # Scale summary frame height (10-15% of total height)
        summary_height = max(80, min(150, int(widget_height * 0.12)))
        self.summary_frame.setMaximumHeight(summary_height)
        
        # Calculate font sizes (scale with widget size)
        # Base sizes: title=9pt, value=14pt at 569px height
        base_height = 569.0
        scale_factor = widget_height / base_height
        
        title_size = max(8, int(9 * scale_factor))
        value_size = max(12, int(14 * scale_factor))
        
        # Update all summary title fonts
        for label in self.summary_title_labels:
            font = label.font()
            font.setPointSize(title_size)
            label.setFont(font)
        
        # Update all summary value fonts
        for label in self.summary_value_labels:
            font = label.font()
            font.setPointSize(value_size)
            font.setBold(True)
            label.setFont(font)
    
    def cleanup(self):
        """Clean up resources"""
        # Stop the refresh timer
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        try:
            logger.debug("Refreshing dashboard data...")
            
            # Get dashboard data from service
            dashboard_data = self.data_service.get_dashboard_data()
            
            # Update summary widgets
            self.findChild(QLabel, "summary_wallet_value").setText(dashboard_data["wallet_value"])
            self.findChild(QLabel, "summary_profit").setText(dashboard_data["profit"])
            self.findChild(QLabel, "summary_active_trades").setText(str(dashboard_data["active_trades"]))
            self.findChild(QLabel, "summary_win_ratio").setText(dashboard_data["win_ratio"])
            
            # Update charts
            self.profit_loss_chart.set_data(dashboard_data["profit_history"])
            
            token_data = [
                (name, amount, color) 
                for name, amount, color in dashboard_data["token_distribution"]
            ]
            self.token_distribution_chart.set_token_data(token_data)
            
            self.volume_chart.set_volume_data(dashboard_data["volume_data"])
            
            # Create trade statistics from dashboard data
            profitable = dashboard_data.get("profitable_trades", 0)
            unprofitable = dashboard_data.get("unprofitable_trades", 0)
            completed = profitable + unprofitable
            
            trade_stats = {
                "trades_created": dashboard_data.get("trades_created", 0),
                "trades_cancelled": dashboard_data.get("trades_cancelled", 0),
                "profitable_trades": profitable,
                "unprofitable_trades": unprofitable,
                "most_profitable_strategy": dashboard_data.get("most_profitable", "N/A"),
                "tokens_traded": dashboard_data.get("tokens_traded", 0),
                "trade_pairs": dashboard_data.get("trade_pairs", 0),
                "completed_trades": completed
            }
            
            # Update the Trade Statistics component
            self.trade_stats.update_stats(trade_stats)
            
            logger.debug("Dashboard data refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing dashboard data: {e}")