import logging
from PySide6.QtCore import QTimer, Signal
from services.qt_base_service import QtBaseService

logger = logging.getLogger(__name__)

class QtUIRefreshService(QtBaseService):
    """
    Service for periodically refreshing UI components without blocking the UI thread.
    Emits signals that UI components can connect to for updates.
    """
    
    # Signals that UI components can connect to
    refresh_active_trades = Signal()
    
    def __init__(self, interval_ms=60000):  # Default to 60 seconds
        """
        Initialize UI refresh service.
        
        Args:
            interval_ms: Refresh interval in milliseconds (default: 60000 = 60 seconds)
        """
        super().__init__('qt_ui_refresher')
        self.timer = QTimer()
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._trigger_refresh)
        self.logger.info(f"UI Refresh Service initialized with {interval_ms/1000}s interval")
    
    def start(self):
        """Start the periodic refresh timer."""
        self.logger.info(f"Starting UI Refresh Service. Interval: {self.timer.interval() / 1000}s")
        self.timer.start()
    
    def stop(self):
        """Stop the periodic refresh timer."""
        self.logger.info("Stopping UI Refresh Service.")
        self.timer.stop()
    
    def _trigger_refresh(self):
        """Called by timer - emits refresh signals for UI components."""
        self.logger.debug("Triggering UI refresh cycle")
        self.refresh_active_trades.emit()
    
    def set_interval(self, interval_ms: int):
        """
        Change the refresh interval.
        
        Args:
            interval_ms: New interval in milliseconds
        """
        was_active = self.timer.isActive()
        if was_active:
            self.timer.stop()
        
        self.timer.setInterval(interval_ms)
        self.logger.info(f"UI refresh interval changed to {interval_ms/1000}s")
        
        if was_active:
            self.timer.start()
