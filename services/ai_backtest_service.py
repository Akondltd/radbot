import logging
import numpy as np
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import itertools

from database.database import Database
from models.data_models import Candle

logger = logging.getLogger(__name__)

class AIBacktestService:
    """Service for backtesting AI trading strategies and optimizing parameters."""
    
    def __init__(self, db: Database):
        """
        Initialize backtest service.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.ai_manager = db.get_ai_strategy_manager()
    
    def run_backtest_for_trade(self, trade_id: int, pool_address: str, 
                               lookback_days: int = 90) -> Dict[str, Any]:
        """
        Run a backtest for a specific trade using historical data.
        
        Args:
            trade_id: Trade ID
            pool_address: Pool address for price data
            lookback_days: Days of historical data to use
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest for trade {trade_id}")
        
        # Get historical price data
        candles = self._get_historical_candles(pool_address, lookback_days)
        if len(candles) < 100:
            logger.warning(f"Insufficient data for backtest: {len(candles)} candles")
            return None
        
        # Get trade details for accumulation goal
        trade_manager = self.db.get_trade_manager()
        trade = trade_manager.get_trade_by_id(trade_id)
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return None
        
        trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
        accumulating_base = trade['accumulation_token_address'] == trade_pair['base_token']
        
        # Get current parameters or use defaults
        current_params = self.ai_manager.get_parameters(trade_id)
        if not current_params:
            current_params = self._get_default_parameters()
        
        # Run backtest with current parameters
        result = self._simulate_trades(candles, current_params, accumulating_base)
        
        # Add metadata
        result['trade_id'] = trade_id
        result['pool_address'] = pool_address
        result['start_timestamp'] = int(candles[0].timestamp)
        result['end_timestamp'] = int(candles[-1].timestamp)
        result['parameters'] = current_params
        
        # Save to database
        self.ai_manager.save_backtest_result(trade_id, pool_address, result)
        
        logger.info(f"Backtest complete: {result['win_rate_percent']:.1f}% win rate, "
                   f"{result['total_return_percent']:.2f}% total return")
        
        return result
    
    def optimize_parameters(self, trade_id: int, pool_address: str,
                           lookback_days: int = 90) -> Dict[str, Any]:
        """
        Optimize indicator parameters using grid search.
        
        Args:
            trade_id: Trade ID
            pool_address: Pool address for price data
            lookback_days: Days of historical data to use
        
        Returns:
            Dictionary with optimal parameters and performance
        """
        logger.info(f"Starting parameter optimization for trade {trade_id}")
        
        # Get historical data
        candles = self._get_historical_candles(pool_address, lookback_days)
        if len(candles) < 100:
            logger.warning(f"Insufficient data for optimization")
            return None
        
        # Get trade details
        trade_manager = self.db.get_trade_manager()
        trade = trade_manager.get_trade_by_id(trade_id)
        trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
        accumulating_base = trade['accumulation_token_address'] == trade_pair['base_token']
        
        # Define parameter search space
        param_combinations = self._generate_parameter_combinations()
        
        best_score = -float('inf')
        best_params = None
        best_result = None
        
        logger.info(f"Testing {len(param_combinations)} parameter combinations...")
        
        for i, params in enumerate(param_combinations):
            if i % 10 == 0:
                logger.debug(f"Testing combination {i+1}/{len(param_combinations)}")
            
            result = self._simulate_trades(candles, params, accumulating_base)
            
            # Calculate optimization score (weighted combination of metrics)
            score = self._calculate_optimization_score(result)
            
            if score > best_score:
                best_score = score
                best_params = params
                best_result = result
        
        logger.info(f"Optimization complete. Best score: {best_score:.2f}")
        logger.info(f"Best params - win rate: {best_result['win_rate_percent']:.1f}%, "
                   f"return: {best_result['total_return_percent']:.2f}%")
        
        # Save optimal parameters
        self.ai_manager.save_parameters(trade_id, best_params, best_score)
        
        # Save best backtest result
        best_result['trade_id'] = trade_id
        best_result['pool_address'] = pool_address
        best_result['start_timestamp'] = int(candles[0].timestamp)
        best_result['end_timestamp'] = int(candles[-1].timestamp)
        best_result['parameters'] = best_params
        self.ai_manager.save_backtest_result(trade_id, pool_address, best_result)
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'best_result': best_result
        }
    
    def _get_historical_candles(self, pool_address: str, lookback_days: int) -> List[Candle]:
        """Get historical candle data from database."""
        trade_manager = self.db.get_trade_manager()
        cursor = trade_manager.conn.cursor()
        
        # Calculate timestamp limit
        current_time = datetime.now().timestamp()
        start_timestamp = current_time - (lookback_days * 24 * 60 * 60)
        
        cursor.execute("""
            SELECT timestamp, open_price, high_price, low_price, close_price, volume
            FROM price_history
            WHERE pair = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (pool_address, start_timestamp))
        
        rows = cursor.fetchall()
        candles = []
        
        for row in rows:
            candles.append(Candle(
                timestamp=row[0],
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5])
            ))
        
        logger.debug(f"Retrieved {len(candles)} historical candles")
        return candles
    
    def _simulate_trades(self, candles: List[Candle], parameters: Dict[str, Any],
                        accumulating_base: bool) -> Dict[str, Any]:
        """
        Simulate trading with given parameters.
        
        Returns:
            Dictionary with performance metrics
        """
        from indicators.enhanced_ai_indicator import EnhancedAIIndicator
        
        # Initialize indicator with parameters
        indicator = EnhancedAIIndicator(parameters)
        
        # Track trading state
        position = 'holding_base'  # Start with base token
        entry_price = None
        entry_index = None
        trades = []
        equity_curve = [1.0]  # Start with 1.0 (100%)
        current_equity = 1.0
        
        # Need enough data for indicators
        min_lookback = 100
        
        for i in range(min_lookback, len(candles)):
            lookback_candles = candles[max(0, i-min_lookback):i+1]
            current_price = candles[i].close
            
            # Get signal from indicator
            signal_score, confidence, regime = indicator.generate_signal(lookback_candles)
            
            # Determine if we should trade based on accumulation goal
            should_trade = False
            trade_action = None
            
            # Signal-to-action mapping is the same regardless of accumulation token:
            #   Bearish signal (< -0.6) + holding base → sell base (exit before drop)
            #   Bullish signal (> 0.6) + holding quote → buy base (enter before rise)
            # Accumulation token only affects profit accounting, not trade timing.
            if position == 'holding_base' and signal_score < -0.6 and confidence > 0.7:
                # Strong sell signal - sell base before price drops
                should_trade = True
                trade_action = 'sell'
            elif position == 'holding_quote' and signal_score > 0.6 and confidence > 0.7:
                # Strong buy signal - buy base before price rises
                should_trade = True
                trade_action = 'buy'
            
            if should_trade:
                if entry_price is not None:
                    # Close previous trade
                    if trade_action == 'buy':
                        # We were holding quote, now buying base
                        # P/L = (entry_price / current_price) - 1
                        pnl_percent = ((entry_price / current_price) - 1) * 100
                    else:
                        # We were holding base, now selling to quote
                        # P/L = (current_price / entry_price) - 1
                        pnl_percent = ((current_price / entry_price) - 1) * 100
                    
                    # Update equity
                    current_equity *= (1 + pnl_percent / 100)
                    equity_curve.append(current_equity)
                    
                    trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_percent': pnl_percent,
                        'holding_periods': i - entry_index
                    })
                
                # Open new position
                entry_price = current_price
                entry_index = i
                position = 'holding_quote' if trade_action == 'sell' else 'holding_base'
        
        # Calculate metrics
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_percent': 0,
                'total_return_percent': 0,
                'sharpe_ratio': 0,
                'max_drawdown_percent': 0,
                'avg_trade_duration_minutes': 0,
                'market_regime': 'unknown',
                'indicator_weights': parameters.get('weights', {})
            }
        
        winning_trades = [t for t in trades if t['pnl_percent'] > 0]
        losing_trades = [t for t in trades if t['pnl_percent'] <= 0]
        
        total_return_percent = (current_equity - 1.0) * 100
        
        # Calculate Sharpe ratio
        returns = [t['pnl_percent'] for t in trades]
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Calculate max drawdown
        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (np.array(equity_curve) - running_max) / running_max * 100
        max_drawdown_percent = abs(np.min(drawdowns))
        
        # Average trade duration (in 10-minute periods, convert to minutes)
        avg_duration_periods = np.mean([t['holding_periods'] for t in trades])
        avg_duration_minutes = int(avg_duration_periods * 10)  # 10 minutes per candle
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_percent': (len(winning_trades) / len(trades)) * 100,
            'total_return_percent': total_return_percent,
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown_percent': max_drawdown_percent,
            'avg_trade_duration_minutes': avg_duration_minutes,
            'market_regime': parameters.get('market_regime', 'unknown'),
            'indicator_weights': parameters.get('weights', {})
        }
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default AI strategy parameters."""
        return {
            'execution_threshold': 0.6,
            'confidence_threshold': 0.7,
            'weights': {
                'rsi': 1.0,
                'macd': 1.0,
                'bb': 1.0,
                'ma_cross': 1.0,
                'stoch_rsi': 1.0,
                'obv': 1.0,
                'roc': 1.0,
                'ichimoku': 1.0
            }
        }
    
    def _generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """Generate parameter combinations for grid search."""
        # Limited grid to keep optimization reasonable
        execution_thresholds = [0.5, 0.6, 0.7]
        confidence_thresholds = [0.6, 0.7, 0.8]
        
        # Weight multipliers to test
        weight_sets = [
            {'rsi': 1.0, 'macd': 1.0, 'bb': 1.0, 'ma_cross': 1.0, 'stoch_rsi': 1.0, 'obv': 1.0, 'roc': 1.0, 'ichimoku': 1.0},
            {'rsi': 1.2, 'macd': 1.3, 'bb': 0.8, 'ma_cross': 1.2, 'stoch_rsi': 1.1, 'obv': 1.0, 'roc': 1.2, 'ichimoku': 1.0},
            {'rsi': 0.8, 'macd': 0.9, 'bb': 1.3, 'ma_cross': 0.8, 'stoch_rsi': 1.2, 'obv': 0.9, 'roc': 0.9, 'ichimoku': 1.1},
        ]
        
        combinations = []
        for exec_thresh, conf_thresh, weights in itertools.product(
            execution_thresholds, confidence_thresholds, weight_sets
        ):
            combinations.append({
                'execution_threshold': exec_thresh,
                'confidence_threshold': conf_thresh,
                'weights': weights
            })
        
        return combinations
    
    def _calculate_optimization_score(self, result: Dict[str, Any]) -> float:
        """
        Calculate optimization score from backtest result.
        
        Weighted combination of:
        - Win rate (30%)
        - Total return (30%)
        - Sharpe ratio (20%)
        - Low drawdown (20%)
        """
        win_rate = result['win_rate_percent'] / 100  # 0 to 1
        total_return = max(-1, min(result['total_return_percent'] / 100, 2))  # Clamp to -100% to +200%
        sharpe = max(-2, min(result['sharpe_ratio'] / 2, 2))  # Normalize Sharpe
        drawdown_penalty = 1 - (result['max_drawdown_percent'] / 100)  # Lower drawdown = higher score
        
        score = (
            win_rate * 0.3 +
            total_return * 0.3 +
            sharpe * 0.2 +
            drawdown_penalty * 0.2
        )
        
        return float(score)
