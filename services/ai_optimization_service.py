import logging
import time
from typing import List, Dict, Any
from PySide6.QtCore import QTimer, QThreadPool
from services.qt_base_service import QtBaseService, Worker
from services.ai_backtest_service import AIBacktestService
from database.database import Database
from config.database_config import DATABASE_PATH

logger = logging.getLogger(__name__)

class QtAIOptimizationService(QtBaseService):
    """
    Qt-based service that runs weekly backtests and optimizes AI strategy parameters.
    Uses Qt's thread pool for non-blocking optimization work.
    """
    
    def __init__(self, interval_ms: int = 604800000):  # Default: 7 days in milliseconds
        """
        Initialize AI optimization service.
        
        Args:
            interval_ms: Milliseconds between optimization runs (default: 604800000 = 7 days)
        """
        super().__init__('qt_ai_optimizer')
        self.db = Database(DATABASE_PATH)
        self.backtest_service = AIBacktestService(self.db)
        
        self.timer = QTimer()
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.trigger_run)
        self.logger.info(f"AI Optimization Service initialized with {interval_ms/1000/60/60/24:.1f} day interval")
    
    def start(self):
        """Start the periodic optimization timer."""
        self.logger.info(f"Starting AI Optimization Service. Interval: {self.timer.interval() / 1000 / 60 / 60 / 24:.1f} days")
        # Initial delay of 1 hour before first run
        QTimer.singleShot(3600 * 1000, self.trigger_run)
        self.timer.start()
    
    def stop(self):
        """Stop the periodic optimization timer."""
        self.logger.info("Stopping AI Optimization Service.")
        self.timer.stop()
    
    def trigger_run(self):
        """Trigger the optimization worker in a background thread."""
        self.logger.info("Triggering AI optimization worker.")
        worker = Worker(self._do_work)
        QThreadPool.globalInstance().start(worker)
    
    def _do_work(self, **kwargs):
        """Main optimization workflow (runs in background thread)."""
        self.logger.info("=== AI Optimization worker started ===")
        
        try:
            # Get all active AI strategy trades
            ai_trades = self._get_ai_strategy_trades()
            
            if not ai_trades:
                self.logger.info("No AI strategy trades found for optimization")
                return
            
            self.logger.info(f"Found {len(ai_trades)} AI strategy trades to optimize")
            
            for trade in ai_trades:
                try:
                    self._optimize_trade(trade)
                    time.sleep(5)  # Small delay between optimizations
                except Exception as e:
                    self.logger.error(f"Error optimizing trade {trade['trade_id']}: {e}", exc_info=True)
            
            self.logger.info("=== AI Optimization worker completed ===")
            
        except Exception as e:
            self.logger.error(f"Error in AI optimization cycle: {e}", exc_info=True)
    
    def _get_ai_strategy_trades(self) -> List[Dict[str, Any]]:
        """Get all active trades using AI strategy."""
        try:
            trade_manager = self.db.get_trade_manager()
            all_trades = trade_manager.get_all_active_trades_for_monitor()
            
            # Filter for AI strategy trades
            ai_trades = [
                trade for trade in all_trades
                if trade.get('strategy_name', '').lower() in ['ai_strategy', 'ai strategy']
            ]
            
            return ai_trades
            
        except Exception as e:
            logger.error(f"Error getting AI strategy trades: {e}", exc_info=True)
            return []
    
    def _optimize_trade(self, trade: Dict[str, Any]):
        """
        Optimize parameters for a single trade.
        
        Args:
            trade: Trade dictionary
        """
        trade_id = trade['trade_id']
        pool_address = trade.get('ociswap_pool_address')
        
        if not pool_address:
            logger.warning(f"Trade {trade_id} has no pool address, skipping optimization")
            return
        
        logger.info(f"Optimizing parameters for trade {trade_id}")
        
        # Run parameter optimization (tests multiple parameter combinations)
        result = self.backtest_service.optimize_parameters(
            trade_id=trade_id,
            pool_address=pool_address,
            lookback_days=90
        )
        
        if result:
            best_result = result['best_result']
            logger.info(f"Trade {trade_id} optimization complete:")
            logger.info(f"  - Win rate: {best_result['win_rate_percent']:.1f}%")
            logger.info(f"  - Total return: {best_result['total_return_percent']:.2f}%")
            logger.info(f"  - Sharpe ratio: {best_result['sharpe_ratio']:.2f}")
            logger.info(f"  - Max drawdown: {best_result['max_drawdown_percent']:.2f}%")
            
            # Update indicator performance tracking
            self._update_indicator_performance(trade_id, best_result)
        else:
            logger.warning(f"Optimization failed for trade {trade_id}")
    
    def _update_indicator_performance(self, trade_id: int, backtest_result: Dict[str, Any]):
        """
        Update per-indicator performance metrics based on backtest results.
        
        Args:
            trade_id: Trade ID
            backtest_result: Backtest result dictionary
        """
        try:
            ai_manager = self.db.get_ai_strategy_manager()
            indicator_weights = backtest_result.get('indicator_weights', {})
            
            # Calculate performance for each indicator
            # This is simplified - in production you'd track individual indicator accuracy
            for indicator_name, weight in indicator_weights.items():
                performance_data = {
                    'total_signals': backtest_result.get('total_trades', 0),
                    'correct_signals': backtest_result.get('winning_trades', 0),
                    'false_signals': backtest_result.get('losing_trades', 0),
                    'accuracy_percent': backtest_result.get('win_rate_percent', 0),
                    'avg_profit_per_signal': backtest_result.get('total_return_percent', 0) / max(backtest_result.get('total_trades', 1), 1),
                    'current_weight': weight,
                    'recommended_weight': weight  # Could be adjusted based on performance
                }
                
                ai_manager.update_indicator_performance(trade_id, indicator_name, performance_data)
            
            logger.debug(f"Updated indicator performance for trade {trade_id}")
            
        except Exception as e:
            logger.error(f"Error updating indicator performance: {e}", exc_info=True)


if __name__ == "__main__":
    # This service is now managed by ServiceCoordinator in main_window.py
    # For standalone testing:
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    service = QtAIOptimizationService(interval_ms=60000)  # 1 minute for testing
    service.start()
    
    logger.info("AI Optimization Service running standalone (Ctrl+C to stop)")
    sys.exit(app.exec())
