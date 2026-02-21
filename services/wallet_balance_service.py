from typing import Optional
from datetime import datetime
import logging
import threading
from PySide6.QtCore import Signal, QTimer, QThreadPool
from services.qt_base_service import QtBaseService, Worker
from core.wallet import RadixWallet
from database.balance_manager import BalanceManager
from config.service_config import SERVICE_INTERVALS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WalletBalanceService(QtBaseService):
    """Service to periodically update wallet balances."""
    
    balance_updated = Signal(dict)  # Signal emitted when balances are updated with the new balances
    error_occurred = Signal(str)   # Signal emitted when an error occurs
    
    def __init__(self, wallet: Optional[RadixWallet] = None, balance_manager: Optional[BalanceManager] = None, icon_cache_service=None, token_updater_service=None, service_coordinator=None):
        """
        Initialize the wallet balance service.
        
        Args:
            wallet: Optional RadixWallet instance
            balance_manager: Optional BalanceManager instance
            icon_cache_service: Optional QtIconCacheService instance for triggering icon downloads
            token_updater_service: Optional QtTokenUpdaterService instance for fetching full token metadata
            service_coordinator: Unused, kept for backward-compatible call signatures
        """
        super().__init__('wallet_balance')
        self._work_lock = threading.Lock()  # Prevent overlapping balance updates
        interval_s = SERVICE_INTERVALS['wallet_balance']
        self.timer = QTimer()
        self.timer.setInterval(interval_s * 1000)  # Convert to milliseconds
        self.timer.timeout.connect(self._trigger_run)
        self.wallet = wallet
        self.balance_manager = balance_manager
        self.icon_cache_service = icon_cache_service
        self.token_updater_service = token_updater_service  # For fetching full token data including icon_url
        self.logger.debug(f"WalletBalanceService __init__: self.wallet is {'set' if self.wallet else 'None'}. Wallet Addr: {self.wallet.public_address if self.wallet and hasattr(self.wallet, 'public_address') else 'N/A'}")
        self.logger.debug(f"WalletBalanceService __init__: self.balance_manager is {'set' if self.balance_manager else 'None'}. BM ID: {id(self.balance_manager) if self.balance_manager else 'N/A'}")
        
    def start(self):
        """Start the periodic balance update timer."""
        self.logger.info(f"Starting WalletBalanceService. Interval: {self.timer.interval() / 1000}s")
        QTimer.singleShot(5000, self._trigger_run)  # Initial run after 5s
        self.timer.start()

    def stop(self):
        """Stop the periodic balance update timer."""
        self.logger.info("Stopping WalletBalanceService.")
        self.timer.stop()

    def set_wallet(self, wallet: RadixWallet):
        """Set the wallet instance for the service and its balance manager."""
        self.wallet = wallet
        if self.balance_manager:
            self.balance_manager.wallet = self.wallet # Update wallet in the provided BalanceManager
            if self.wallet:
                self.logger.info(f"Wallet set in WalletBalanceService and its BalanceManager: {self.wallet.public_address if self.wallet and hasattr(self.wallet, 'public_address') else 'None'}")
            else:
                self.logger.warning("Wallet cleared in WalletBalanceService and its BalanceManager.")
        else:
            self.logger.warning("BalanceManager not provided to WalletBalanceService, cannot set wallet in manager.")
    
    def trigger_refresh(self):
        """Manually trigger an immediate balance refresh in a background thread."""
        self.logger.info("Manual balance refresh triggered")
        self._trigger_run()
    
    def _trigger_run(self):
        """Run balance update on QThreadPool."""
        if self._work_lock.locked():
            self.logger.debug("Balance update already in progress, skipping")
            return
        worker = Worker(self._run_balance_update)
        QThreadPool.globalInstance().start(worker)

    def _run_balance_update(self, **kwargs):
        """Balance update entry point — runs on worker thread."""
        if not self._work_lock.acquire(blocking=False):
            self.logger.debug("Balance update already running, skipping")
            return
        try:
            self.logger.debug(f"WalletBalanceService run() entered. Wallet Addr: {self.wallet.public_address if self.wallet and hasattr(self.wallet, 'public_address') else 'N/A'}")
            
            if not self.wallet:
                self.logger.warning("No wallet loaded, skipping balance update")
                return
                
            if not hasattr(self.wallet, 'public_address') or not self.wallet.public_address:
                self.logger.warning("Wallet has no public_address, skipping balance update")
                return
            
            self._do_balance_update()
        finally:
            self._work_lock.release()
    
    def _do_balance_update(self):
        """Actual balance update logic (extracted for task coordination)."""
        try:
            self.logger.info("Executing balance update...")
            
            # Get current balances from Radix API
            raw_api_data = self.wallet.fetch_raw_token_data() # Changed to fetch detailed raw data
            
            if not self.balance_manager:
                self.logger.error("Balance manager not initialized")
                self.error_occurred.emit("Balance manager not available.")
                return
            
            if not raw_api_data:
                self.logger.warning("Received no data from fetch_raw_token_data. Skipping balance update.")
                # Optionally emit a signal or log that data was empty but not necessarily an error
                # self.error_occurred.emit("No token data received from API.") # Or a different signal
                return
                
            # Update database with new balances using the fetched raw_api_data
            # Returns (success, new_tokens_count)
            success, new_tokens_count = self.balance_manager.update_balances_from_api_data(raw_api_data)
            
            if success:
                self.logger.info("Balance update completed successfully")
                updated_balances = self.balance_manager.get_all_balances()
                self.balance_updated.emit(updated_balances)
                
                # Trigger services ONLY if new tokens were detected
                if new_tokens_count > 0:
                    # First, trigger token updater to fetch full metadata (including icon_url) from Astrolescent
                    if self.token_updater_service and hasattr(self.token_updater_service, 'force_run'):
                        self.logger.info(f"Triggering token updater service for {new_tokens_count} new token(s)")
                        try:
                            self.token_updater_service.force_run()
                        except Exception as token_error:
                            self.logger.warning(f"Error triggering token updater service: {token_error}")
                    else:
                        self.logger.debug("Token updater service not available, skipping metadata fetch")
                    
                    # Then trigger icon cache to download icons (needs icon_url from token updater)
                    # Note: We use a simple delay here since we're in a worker thread (can't use QTimer)
                    if self.icon_cache_service and hasattr(self.icon_cache_service, 'trigger_run'):
                        self.logger.info(f"Triggering icon cache service for {new_tokens_count} new token(s)")
                        try:
                            import time
                            time.sleep(5)  # Wait 5 seconds for token updater to populate icon_url
                            self.icon_cache_service.trigger_run()
                        except Exception as icon_error:
                            self.logger.warning(f"Error triggering icon cache service: {icon_error}")
                    else:
                        self.logger.debug("Icon cache service not available, skipping icon download")
            else:
                self.logger.warning("Failed to update balances")
                self.error_occurred.emit("Failed to update balances")
                
        except ConnectionError as ce:
            self.logger.error(f"Network connection error updating wallet balances: {ce}", exc_info=True)
            self.error_occurred.emit(f"Network error: {str(ce)}")
        except TimeoutError as te:
            self.logger.error(f"Network timeout updating wallet balances: {te}", exc_info=True)
            self.error_occurred.emit(f"Network timeout: {str(te)}")
        except Exception as e:
            self.logger.error(f"Error updating wallet balances: {e}", exc_info=True)
            self.error_occurred.emit(f"Error updating balances: {str(e)}")
            raise  # Re-raise so task coordinator knows it failed
