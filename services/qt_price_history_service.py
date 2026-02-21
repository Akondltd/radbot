import time
from PySide6.QtCore import QTimer, QThreadPool, Signal

from services.astrolescent_price_service import get_price_service
from services.pair_price_history_service import get_pair_history_service
from services.qt_base_service import QtBaseService, Worker

class QtPriceHistoryService(QtBaseService):
    """A service to update price history for tracked pairs using Astrolescent prices."""
    
    # Signal emitted after trade monitor completes (forwarded from trade monitor)
    monitoring_cycle_completed = Signal()

    def __init__(self, interval_ms=600000, db_path="data/radbot.db"):  # Default to 10 minutes
        super().__init__('qt_price_history_updater')
        self.db_path = db_path
        self.timer = QTimer()
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.trigger_run)
        
        # Trade monitor will be set by main window after wallet is loaded
        self.trade_monitor = None

    def set_trade_monitor(self, trade_monitor):
        """Set the trade monitor instance to run after price updates."""
        self.trade_monitor = trade_monitor
        self.logger.info("Trade monitor set for execution after price updates")

    def start(self):
        """Starts the service timer."""
        self.logger.info(f"Starting Qt Price History Service. Run interval: {self.timer.interval() / 1000}s")
        # Initial 10-second delay before the first run
        QTimer.singleShot(10 * 1000, self.trigger_run)
        self.timer.start()

    def stop(self):
        """Stops the service timer."""
        self.logger.info("Stopping Qt Price History Service.")
        self.timer.stop()

    def trigger_run(self):
        """Creates a worker to perform the price history update on a background thread."""
        import time
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.logger.info(f"========== Triggering price history worker at {current_time} ==========")
        worker = Worker(self._do_work)
        QThreadPool.globalInstance().start(worker)

    def _do_work(self, **kwargs):
        """The main logic for the price history update, executed by the worker."""
        self.logger.info("Price history worker started - updating prices from Astrolescent...")
        start_time = time.time()
        try:
            # Step 1: Refresh Astrolescent price cache (650+ tokens)
            price_service = get_price_service()
            price_service.get_all_prices(force_refresh=True)
            
            # Step 2: Record current prices for all selected trade pairs
            pair_history = get_pair_history_service(self.db_path)
            recorded_count = pair_history.record_all_active_pairs()
            
            end_time = time.time()
            self.logger.info(f"Price history update completed. Recorded {recorded_count} pairs. Duration: {end_time - start_time:.2f} seconds")
            
            # Step 2: Run trade monitor with fresh price data
            if self.trade_monitor:
                self.logger.info("Running trade monitor with updated price data...")
                trade_start_time = time.time()
                try:
                    self.trade_monitor.run()
                    trade_end_time = time.time()
                    self.logger.info(f"Trade monitor completed. Duration: {trade_end_time - trade_start_time:.2f} seconds")
                    self.logger.info("========== Price update & trade monitoring cycle complete ==========")
                    
                    # Emit signal to refresh GUI after trade monitoring cycle completes
                    self.monitoring_cycle_completed.emit()
                    
                except Exception as e:
                    self.logger.error(f"Error in trade monitor execution: {e}", exc_info=True)
            else:
                self.logger.info("No trade monitor set, skipping trade monitoring")
                self.logger.info("========== Price update cycle complete ==========")
                
        except Exception as e:
            self.logger.error(f"An error occurred in the price history worker: {e}", exc_info=True)
