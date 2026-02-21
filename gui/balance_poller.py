import logging
from typing import Optional
from datetime import datetime, timedelta
import time
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from core.wallet import RadixWallet
from database.balance_manager import BalanceManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BalancePoller(QObject):
    """Worker class to periodically poll wallet balances."""
    
    # Signals
    balance_updated = Signal(str)  # Signal emitted when balances are updated
    error_occurred = Signal(str)   # Signal emitted when an error occurs
    
    def __init__(self, wallet: RadixWallet, db_path: str, parent=None):
        super().__init__(parent)
        self.wallet = wallet
        self.db_path = db_path
        self.balance_manager = BalanceManager(wallet, db_path)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_balances)
        self.last_poll_time: Optional[datetime] = None
        self.poll_interval = 180  # 3 minutes in seconds
        
    def start(self):
        """Start the balance polling."""
        logger.info("Starting balance polling...")
        self.timer.start(self.poll_interval * 1000)  # Convert to milliseconds
        
    def stop(self):
        """Stop the balance polling."""
        logger.info("Stopping balance polling...")
        self.timer.stop()
        
    @Slot()
    def poll_balances(self):
        """Poll wallet balances from Radix network."""
        try:
            if not self.wallet:
                logger.warning("No wallet loaded, skipping balance poll")
                return
                
            current_time = datetime.utcnow()
            if self.last_poll_time and (current_time - self.last_poll_time) < timedelta(seconds=self.poll_interval):
                logger.debug("Poll interval not reached, skipping poll")
                return
                
            logger.info("Polling wallet balances...")
            
            # Get current balances from Radix API
            api_balances = self.wallet.get_token_balances()
            
            # Update database with new balances
            success = self.balance_manager.load_balances()
            
            if success:
                self.last_poll_time = current_time
                logger.info("Balance poll completed successfully")
                self.balance_updated.emit("Balances updated successfully")
            else:
                logger.warning("Failed to update balances")
                self.error_occurred.emit("Failed to update balances")
                
        except Exception as e:
            logger.error(f"Error in balance polling: {e}", exc_info=True)
            self.error_occurred.emit(f"Error polling balances: {str(e)}")
