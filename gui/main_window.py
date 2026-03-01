from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from typing import Optional, Dict
from core.wallet import RadixWallet

# Tab indices for visibility management
class TabIndex:
    DASHBOARD = 0
    ACTIVE_TRADES = 1
    CREATE_TRADE = 2
    WALLET = 3
    INDICATORS = 4
    TRADE_HISTORY = 5
    HELP = 6
    
# Tabs visible when no wallet is loaded
TABS_WITHOUT_WALLET = {TabIndex.WALLET, TabIndex.HELP}
# All tabs (for when wallet is loaded)
ALL_TABS = {TabIndex.DASHBOARD, TabIndex.ACTIVE_TRADES, TabIndex.CREATE_TRADE, 
            TabIndex.WALLET, TabIndex.INDICATORS, TabIndex.TRADE_HISTORY, TabIndex.HELP}
from services.qt_icon_cache_service import QtIconCacheService
from services.qt_price_history_service import QtPriceHistoryService
from services.qt_ui_refresh_service import QtUIRefreshService
from services.ai_optimization_service import QtAIOptimizationService
from services.token_updater_service import QtTokenUpdaterService
from services.trade_monitor import TradeMonitor
from services.web_dashboard_service import WebDashboardService
from services.service_coordinator import ServiceCoordinator, ServiceCategory
from services.task_coordinator import TaskPriority
from database.database import Database
from gui.main_window_ui import Ui_AkondRadBotMainWindow as Ui_MainWindow
from gui.dashboard_gui import DashboardTabMain
from gui.active_trades_gui import ActiveTradesTabMain
from gui.create_trade_gui import CreateTradeTabMain
from gui.wallet_gui import WalletTabMain
from gui.indicators_gui import IndicatorsTabMain
from gui.trade_history_gui import TradeHistoryTabMain
from gui.help_gui import HelpTabMain
from config.database_config import DATABASE_PATH
from utils.sleep_inhibitor import SleepInhibitor
import logging
import sys
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

class TradingBotMainWindow(QMainWindow):
    # Signals for thread-safe UI updates
    trade_executed_signal = Signal()  # Emitted when trades are executed
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)  # Apply window title
        self.current_wallet: Optional[RadixWallet] = None
        self.trade_monitor: Optional[TradeMonitor] = None
        
        # Prevent system sleep/hibernate while RadBot is running
        self.sleep_inhibitor = SleepInhibitor()
        self.sleep_inhibitor.inhibit()
        
        # Initialize ServiceCoordinator for task management
        self.service_coordinator = ServiceCoordinator(self)
        
        # Connect signal for thread-safe UI updates
        self.trade_executed_signal.connect(self._refresh_ui_after_trade_execution, Qt.QueuedConnection)

        # Initialize database connection for trade history
        try:
            self.database = Database(DATABASE_PATH)
            logger.info("Database connection established for main window")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            self.database = None

        # Create tab instances
        self.dashboard_tab = DashboardTabMain()
        self.active_trades_tab = ActiveTradesTabMain()
        self.create_trade_tab = CreateTradeTabMain()
        self.wallet_tab = WalletTabMain(db_path=DATABASE_PATH, main_window=self, service_coordinator=self.service_coordinator)
        self.indicators_tab = IndicatorsTabMain()
        self.trade_history_tab = TradeHistoryTabMain(database=self.database)
        self.help_tab = HelpTabMain()

        # Add tabs dynamically to the main tab widget
        self.ui.RadBotMainTabMenu.addTab(self.dashboard_tab, "Dashboard")
        self.ui.RadBotMainTabMenu.addTab(self.active_trades_tab, "Active Trades")
        self.ui.RadBotMainTabMenu.addTab(self.create_trade_tab, "Create Trade")
        self.ui.RadBotMainTabMenu.addTab(self.wallet_tab, "Wallet")
        self.ui.RadBotMainTabMenu.addTab(self.indicators_tab, "Indicators")
        self.ui.RadBotMainTabMenu.addTab(self.trade_history_tab, "Trade History")
        self.ui.RadBotMainTabMenu.addTab(self.help_tab, "Help")

        # Optionally set the default tab index
        self.ui.RadBotMainTabMenu.setCurrentIndex(3)  # e.g., Wallet tab

        # Connect signals for cross-tab communication
        self.create_trade_tab.trade_created.connect(self.active_trades_tab.handle_trade_created)
        self.wallet_tab.wallet_loaded.connect(self.active_trades_tab.handle_wallet_loaded)
        self.wallet_tab.wallet_unloaded.connect(self.active_trades_tab.handle_wallet_unloaded)
        
        # Connect trade operations to wallet balance refresh
        self.active_trades_tab.trade_operation_completed.connect(self._update_wallet_balances)

        # Any further initialization
        self.init_logic()

        # --- Initialize and start background services ---
        self.icon_cache_service = QtIconCacheService()
        self.price_history_service = QtPriceHistoryService()
        self.token_updater_service = QtTokenUpdaterService(interval_ms=86400000)  # 24 hours
        ui_refresh_service = QtUIRefreshService(interval_ms=600000)  # 10 minutes
        ai_optimization_service = QtAIOptimizationService(interval_ms=604800000)  # 7 days
        
        # Register all services with ServiceCoordinator
        self.service_coordinator.register_service(self.icon_cache_service, category=ServiceCategory.UI)
        self.service_coordinator.register_service(self.price_history_service, category=ServiceCategory.DATA_FETCH)
        self.service_coordinator.register_service(self.token_updater_service, category=ServiceCategory.DATA_FETCH)
        self.service_coordinator.register_service(ui_refresh_service, category=ServiceCategory.UI)
        self.service_coordinator.register_service(ai_optimization_service, category=ServiceCategory.BACKGROUND)
        
        # Connect active trades tab to refresh service
        self.active_trades_tab.connect_refresh_service(ui_refresh_service)
        
        # Start all registered services
        self.service_coordinator.start_all()
        
        logger.info("ServiceCoordinator initialized with %d services", len(self.service_coordinator.services))
        
        # Start web dashboard (independent of ServiceCoordinator — runs its own aiohttp server)
        self.web_dashboard = WebDashboardService()
        self.web_dashboard.start()

    def init_logic(self):
        # Connect wallet update signals
        self.wallet_tab.wallet_loaded.connect(self.on_wallet_loaded)
        self.wallet_tab.wallet_unloaded.connect(self.on_wallet_unloaded)
        
        # Set initial tab visibility (only Wallet and Help until wallet is loaded)
        self._set_tab_visibility(wallet_loaded=False)

    def on_wallet_loaded(self, wallet: Optional[RadixWallet]):
        """Handle wallet being loaded."""
        # Stop any existing trade monitor service
        if self.trade_monitor:
            self.trade_monitor.stop()
            self.trade_monitor = None

        if wallet:
            self.current_wallet = wallet
            # Update create trade tab with wallet
            self.create_trade_tab.set_wallet(wallet)
            # Start the new trade monitor service with thread-safe callback
            self.trade_monitor = TradeMonitor(
                wallet=self.current_wallet, 
                db_path=DATABASE_PATH,
                on_trades_executed_callback=self._emit_trade_executed_signal,  # Thread-safe
                service_coordinator=self.service_coordinator  # NEW: For coordinated execution
            )
            
            # Register with ServiceCoordinator
            self.service_coordinator.register_service(
                self.trade_monitor,
                category=ServiceCategory.EXECUTION
            )
            logger.info("TradeMonitor registered with ServiceCoordinator")
            
            # TradeMonitor is driven by QtPriceHistoryService (not its own thread)
            self.price_history_service.set_trade_monitor(self.trade_monitor)
            
            # Show all tabs when wallet is loaded
            self._set_tab_visibility(wallet_loaded=True)
            logger.info("All tabs now visible (wallet loaded)")
        else:
            self.current_wallet = None

    @Slot()
    def on_wallet_unloaded(self):
        """Handle wallet being unloaded (e.g., password changed)."""
        logger.info("Wallet unloaded - hiding restricted tabs")
        
        # Stop trade monitor if running
        if self.trade_monitor:
            self.trade_monitor.stop()
            self.trade_monitor = None
            logger.info("Trade monitor stopped due to wallet unload")
        
        self.current_wallet = None
        
        # Hide tabs that require wallet
        self._set_tab_visibility(wallet_loaded=False)
        
        # Switch to wallet tab
        self.ui.RadBotMainTabMenu.setCurrentIndex(TabIndex.WALLET)
        logger.info("Switched to Wallet tab, restricted tabs hidden")

    def _set_tab_visibility(self, wallet_loaded: bool):
        """
        Set tab visibility based on wallet loaded state.
        
        Args:
            wallet_loaded: If True, show all tabs. If False, show only Wallet and Help.
        """
        visible_tabs = ALL_TABS if wallet_loaded else TABS_WITHOUT_WALLET
        
        for tab_index in ALL_TABS:
            is_visible = tab_index in visible_tabs
            self.ui.RadBotMainTabMenu.setTabVisible(tab_index, is_visible)
        
        logger.debug(f"Tab visibility updated: wallet_loaded={wallet_loaded}, visible_tabs={visible_tabs}")

    def _emit_trade_executed_signal(self):
        """Thread-safe method to emit signal from worker thread."""
        self.trade_executed_signal.emit()
    
    @Slot()
    def _update_wallet_balances(self):
        if self.current_wallet:
            logger.debug("Refreshing wallet balances UI.")
            self.wallet_tab._render_balances_from_manager()
    
    @Slot()
    def _refresh_ui_after_trade_execution(self):
        """Refresh Active Trades and Trade History tabs after trades are executed."""
        try:
            logger.info("Refreshing UI after trade execution...")
            
            # Refresh Active Trades tab
            if self.current_wallet:
                self.active_trades_tab.load_active_trades(self.current_wallet.public_address)
                logger.info("Active Trades tab refreshed")
            
            # Refresh Trade History tab
            self.trade_history_tab.refresh_data()
            logger.info("Trade History tab refreshed")
            
            # Delay wallet balance UI update to allow balance refresh to complete
            # This prevents showing "No balance found" while balance is being fetched
            logger.info("Scheduling wallet balance UI update (2 second delay)")
            QTimer.singleShot(2000, self._update_wallet_balances)  # 2 second delay
            
        except Exception as e:
            logger.error(f"Error refreshing UI after trade execution: {e}", exc_info=True)

    def closeEvent(self, event):
        """Handle the window close event to stop background services."""
        logger.info("Application closing, stopping all services...")
        
        # Stop web dashboard
        if hasattr(self, 'web_dashboard') and self.web_dashboard:
            self.web_dashboard.stop()
        
        # Stop trade monitor first
        if self.trade_monitor:
            self.trade_monitor.stop()
        
        # Stop all services
        if hasattr(self, 'service_coordinator'):
            self.service_coordinator.stop_all()
        
        # Release sleep inhibitor
        if hasattr(self, 'sleep_inhibitor'):
            self.sleep_inhibitor.release()
        
        logger.info("All services stopped")
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TradingBotMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()