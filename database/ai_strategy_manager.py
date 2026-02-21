import logging
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import config for Kelly parameters
from config.config_loader import config

logger = logging.getLogger(__name__)

class AIStrategyManager:
    """Manages database operations for AI Strategy learning and optimization."""

    def __init__(self, conn):
        """Initializes the AIStrategyManager with a database connection."""
        self.conn = conn
        self._create_tables()

    def _create_tables(self):
        """Create all AI strategy related tables."""
        self._create_ai_strategy_parameters_table()
        self._create_ai_backtest_results_table()
        self._create_ai_indicator_performance_table()
        self._create_ai_trade_outcomes_table()
        
    def _create_ai_strategy_parameters_table(self):
        """Store optimized parameters for each trade's AI strategy."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_strategy_parameters (
                param_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                parameter_value TEXT NOT NULL,
                optimization_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                performance_score REAL,
                FOREIGN KEY(trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,
                UNIQUE(trade_id, parameter_name)
            )
        """)
        self.conn.commit()
        logger.debug("AI strategy parameters table created/verified")

    def _create_ai_backtest_results_table(self):
        """Store results from backtesting runs."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_backtest_results (
                backtest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                pool_address TEXT NOT NULL,
                backtest_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_timestamp INTEGER NOT NULL,
                end_timestamp INTEGER NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_return_percent REAL DEFAULT 0.0,
                sharpe_ratio REAL,
                max_drawdown_percent REAL,
                avg_trade_duration_minutes INTEGER,
                win_rate_percent REAL,
                parameters_json TEXT,
                indicator_weights_json TEXT,
                market_regime TEXT,
                FOREIGN KEY(trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()
        logger.debug("AI backtest results table created/verified")

    def _create_ai_indicator_performance_table(self):
        """Track individual indicator performance over time."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_indicator_performance (
                performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                indicator_name TEXT NOT NULL,
                evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_signals INTEGER DEFAULT 0,
                correct_signals INTEGER DEFAULT 0,
                false_signals INTEGER DEFAULT 0,
                accuracy_percent REAL DEFAULT 0.0,
                avg_profit_per_signal REAL DEFAULT 0.0,
                current_weight REAL DEFAULT 1.0,
                recommended_weight REAL DEFAULT 1.0,
                FOREIGN KEY(trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()
        logger.debug("AI indicator performance table created/verified")

    def _create_ai_trade_outcomes_table(self):
        """Store outcomes of AI strategy executions for learning."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_trade_outcomes (
                outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                flip_id INTEGER,
                execution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                entry_price REAL NOT NULL,
                exit_price REAL,
                profit_loss_percent REAL,
                holding_duration_minutes INTEGER,
                composite_score REAL NOT NULL,
                confidence_score REAL NOT NULL,
                market_regime TEXT,
                indicator_scores_json TEXT,
                was_profitable BOOLEAN,
                is_closed BOOLEAN DEFAULT 0,
                FOREIGN KEY(trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,
                FOREIGN KEY(flip_id) REFERENCES trade_flips(flip_id) ON DELETE SET NULL
            )
        """)
        self.conn.commit()
        logger.debug("AI trade outcomes table created/verified")

    # ==================== Parameter Management ====================
    
    def save_parameters(self, trade_id: int, parameters: Dict[str, Any], performance_score: float = None):
        """Save optimized parameters for a trade."""
        cursor = self.conn.cursor()
        for param_name, param_value in parameters.items():
            cursor.execute("""
                INSERT OR REPLACE INTO ai_strategy_parameters 
                (trade_id, parameter_name, parameter_value, performance_score, optimization_date)
                VALUES (?, ?, ?, ?, ?)
            """, (trade_id, param_name, json.dumps(param_value), performance_score, datetime.now()))
        self.conn.commit()
        logger.debug(f"Saved {len(parameters)} parameters for trade {trade_id}")

    def get_parameters(self, trade_id: int) -> Dict[str, Any]:
        """Retrieve current parameters for a trade."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT parameter_name, parameter_value 
            FROM ai_strategy_parameters 
            WHERE trade_id = ?
        """, (trade_id,))
        
        params = {}
        for row in cursor.fetchall():
            try:
                params[row[0]] = json.loads(row[1])
            except json.JSONDecodeError:
                params[row[0]] = row[1]
        
        return params

    # ==================== Backtest Results ====================
    
    def save_backtest_result(self, trade_id: int, pool_address: str, result_data: Dict[str, Any]):
        """Save a backtest result."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ai_backtest_results (
                trade_id, pool_address, start_timestamp, end_timestamp,
                total_trades, winning_trades, losing_trades, total_return_percent,
                sharpe_ratio, max_drawdown_percent, avg_trade_duration_minutes,
                win_rate_percent, parameters_json, indicator_weights_json, market_regime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id, pool_address,
            result_data.get('start_timestamp'),
            result_data.get('end_timestamp'),
            result_data.get('total_trades', 0),
            result_data.get('winning_trades', 0),
            result_data.get('losing_trades', 0),
            result_data.get('total_return_percent', 0.0),
            result_data.get('sharpe_ratio'),
            result_data.get('max_drawdown_percent'),
            result_data.get('avg_trade_duration_minutes'),
            result_data.get('win_rate_percent'),
            json.dumps(result_data.get('parameters', {})),
            json.dumps(result_data.get('indicator_weights', {})),
            result_data.get('market_regime', 'unknown')
        ))
        self.conn.commit()
        logger.info(f"Saved backtest result for trade {trade_id}: {result_data.get('win_rate_percent', 0):.1f}% win rate")

    def get_latest_backtest(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent backtest result for a trade."""
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("""
            SELECT * FROM ai_backtest_results 
            WHERE trade_id = ? 
            ORDER BY backtest_date DESC 
            LIMIT 1
        """, (trade_id,))
        
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            if result.get('parameters_json'):
                result['parameters'] = json.loads(result['parameters_json'])
            if result.get('indicator_weights_json'):
                result['indicator_weights'] = json.loads(result['indicator_weights_json'])
            return result
        return None

    def get_backtest_history(self, trade_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get backtest history for a trade."""
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("""
            SELECT * FROM ai_backtest_results 
            WHERE trade_id = ? 
            ORDER BY backtest_date DESC 
            LIMIT ?
        """, (trade_id, limit))
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('parameters_json'):
                result['parameters'] = json.loads(result['parameters_json'])
            if result.get('indicator_weights_json'):
                result['indicator_weights'] = json.loads(result['indicator_weights_json'])
            results.append(result)
        
        return results

    # ==================== Indicator Performance ====================
    
    def update_indicator_performance(self, trade_id: int, indicator_name: str, 
                                     performance_data: Dict[str, Any]):
        """Update performance metrics for a specific indicator."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ai_indicator_performance (
                trade_id, indicator_name, total_signals, correct_signals,
                false_signals, accuracy_percent, avg_profit_per_signal,
                current_weight, recommended_weight
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id, indicator_name,
            performance_data.get('total_signals', 0),
            performance_data.get('correct_signals', 0),
            performance_data.get('false_signals', 0),
            performance_data.get('accuracy_percent', 0.0),
            performance_data.get('avg_profit_per_signal', 0.0),
            performance_data.get('current_weight', 1.0),
            performance_data.get('recommended_weight', 1.0)
        ))
        self.conn.commit()

    def get_indicator_performance(self, trade_id: int, indicator_name: str = None) -> List[Dict[str, Any]]:
        """Get performance data for indicators."""
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row
        
        if indicator_name:
            cursor.execute("""
                SELECT * FROM ai_indicator_performance 
                WHERE trade_id = ? AND indicator_name = ?
                ORDER BY evaluation_date DESC
                LIMIT 10
            """, (trade_id, indicator_name))
        else:
            cursor.execute("""
                SELECT * FROM ai_indicator_performance 
                WHERE trade_id = ?
                ORDER BY evaluation_date DESC
            """, (trade_id,))
        
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Trade Outcomes ====================
    
    def record_trade_entry(self, trade_id: int, entry_price: float, 
                          composite_score: float, confidence_score: float,
                          market_regime: str, indicator_scores: Dict[str, float],
                          flip_id: int = None) -> int:
        """Record when AI strategy enters a trade."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ai_trade_outcomes (
                trade_id, flip_id, entry_price, composite_score,
                confidence_score, market_regime, indicator_scores_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id, flip_id, entry_price, composite_score,
            confidence_score, market_regime, json.dumps(indicator_scores)
        ))
        self.conn.commit()
        return cursor.lastrowid

    def record_trade_exit(self, outcome_id: int, exit_price: float, 
                         holding_duration_minutes: int):
        """Record when AI strategy exits a trade."""
        cursor = self.conn.cursor()
        
        # Get entry price to calculate profit/loss
        cursor.execute("SELECT entry_price FROM ai_trade_outcomes WHERE outcome_id = ?", (outcome_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Outcome {outcome_id} not found")
            return
        
        entry_price = row[0]
        profit_loss_percent = ((exit_price - entry_price) / entry_price) * 100
        was_profitable = profit_loss_percent > 0
        
        cursor.execute("""
            UPDATE ai_trade_outcomes 
            SET exit_price = ?, profit_loss_percent = ?,
                holding_duration_minutes = ?, was_profitable = ?, is_closed = 1
            WHERE outcome_id = ?
        """, (exit_price, profit_loss_percent, holding_duration_minutes, was_profitable, outcome_id))
        self.conn.commit()
        
        logger.info(f"Recorded trade exit: {profit_loss_percent:.2f}% P/L")

    def get_recent_outcomes(self, trade_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trade outcomes for learning."""
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("""
            SELECT * FROM ai_trade_outcomes 
            WHERE trade_id = ? AND is_closed = 1
            ORDER BY execution_timestamp DESC 
            LIMIT ?
        """, (trade_id, limit))
        
        outcomes = []
        for row in cursor.fetchall():
            outcome = dict(row)
            if outcome.get('indicator_scores_json'):
                outcome['indicator_scores'] = json.loads(outcome['indicator_scores_json'])
            outcomes.append(outcome)
        
        return outcomes

    # ==================== Kelly Criterion Position Sizing ====================
    
    def calculate_kelly_fraction(self, trade_id: int, lookback: int = None, 
                                 fractional_kelly: float = None) -> float:
        """
        Calculate Kelly criterion position sizing from recent trade outcomes.
        
        Kelly Formula: K = (W * R - L) / R
        Where:
            W = Win rate (probability of winning)
            L = Loss rate (1 - W)
            R = Reward/Risk ratio (avg win size / avg loss size)
        
        Args:
            trade_id: Trade ID to calculate Kelly for
            lookback: Number of recent trades to analyze (default from config)
            fractional_kelly: Conservative multiplier (default from config)
            
        Returns:
            Position size fraction between min and max from config (default 10% to 100%)
        """
        try:
            # Load parameters from config if not provided
            if lookback is None:
                lookback = config.kelly_lookback_trades
            if fractional_kelly is None:
                fractional_kelly = config.kelly_fractional_multiplier
            
            min_trades_required = config.kelly_min_trades_required
            min_position_size = config.kelly_min_position_size
            max_position_size = config.kelly_max_position_size
            
            # Get recent closed trade outcomes
            outcomes = self.get_recent_outcomes(trade_id, limit=lookback)
            
            # Need minimum history to calculate Kelly
            if len(outcomes) < min_trades_required:
                logger.info(f"Trade {trade_id}: Insufficient Kelly history ({len(outcomes)}/{min_trades_required} trades), using full position")
                return max_position_size
            
            # Separate wins and losses
            wins = [o for o in outcomes if o['was_profitable']]
            losses = [o for o in outcomes if not o['was_profitable']]
            
            if not wins or not losses:
                # All wins or all losses - use conservative sizing
                if wins and not losses:
                    # All wins - use 80% of max position
                    conservative_size = max_position_size * 0.8
                    logger.info(f"Trade {trade_id}: All wins in history, using {conservative_size:.1%} position")
                    return conservative_size
                else:
                    # All losses - use minimum position
                    logger.info(f"Trade {trade_id}: All losses in history, using {min_position_size:.1%} position")
                    return min_position_size
            
            # Calculate win rate
            win_rate = len(wins) / len(outcomes)
            loss_rate = 1 - win_rate
            
            # Calculate average win and loss percentages
            avg_win_pct = sum(w['profit_loss_percent'] for w in wins) / len(wins)
            avg_loss_pct = abs(sum(l['profit_loss_percent'] for l in losses) / len(losses))
            
            # Prevent division by zero
            if avg_loss_pct == 0:
                logger.warning(f"Trade {trade_id}: Average loss is zero, using max position")
                return max_position_size
            
            # Calculate reward/risk ratio
            reward_risk_ratio = avg_win_pct / avg_loss_pct
            
            # Kelly formula: (W * R - L) / R
            kelly_full = (win_rate * reward_risk_ratio - loss_rate) / reward_risk_ratio
            
            # Apply fractional Kelly for safety
            kelly_fraction = kelly_full * fractional_kelly
            
            # Clamp between configured min and max
            kelly_clamped = max(min_position_size, min(kelly_fraction, max_position_size))
            
            logger.info(f"Trade {trade_id} Kelly Calculation:")
            logger.info(f"  History: {len(outcomes)} trades ({len(wins)}W / {len(losses)}L)")
            logger.info(f"  Win Rate: {win_rate:.1%}")
            logger.info(f"  Avg Win: +{avg_win_pct:.2f}% | Avg Loss: -{avg_loss_pct:.2f}%")
            logger.info(f"  R/R Ratio: {reward_risk_ratio:.2f}")
            logger.info(f"  Full Kelly: {kelly_full:.1%} -> Fractional ({fractional_kelly}x): {kelly_fraction:.1%}")
            logger.info(f"  Final Position Size: {kelly_clamped:.1%}")
            
            return float(kelly_clamped)
            
        except Exception as e:
            logger.error(f"Error calculating Kelly fraction for trade {trade_id}: {e}", exc_info=True)
            # Default to max position on error
            return config.kelly_max_position_size

    # ==================== Analytics ====================
    
    def get_ai_performance_summary(self, trade_id: int) -> Dict[str, Any]:
        """Get overall AI performance summary for a trade."""
        cursor = self.conn.cursor()
        
        # Get total outcomes
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN was_profitable = 1 THEN 1 ELSE 0 END) as winning_trades,
                AVG(profit_loss_percent) as avg_profit_percent,
                AVG(holding_duration_minutes) as avg_duration,
                MAX(profit_loss_percent) as best_trade,
                MIN(profit_loss_percent) as worst_trade
            FROM ai_trade_outcomes
            WHERE trade_id = ? AND is_closed = 1
        """, (trade_id,))
        
        row = cursor.fetchone()
        if row:
            total = row[0] or 0
            winning = row[1] or 0
            return {
                'total_trades': total,
                'winning_trades': winning,
                'losing_trades': total - winning,
                'win_rate_percent': (winning / total * 100) if total > 0 else 0,
                'avg_profit_percent': row[2] or 0,
                'avg_duration_minutes': row[3] or 0,
                'best_trade_percent': row[4] or 0,
                'worst_trade_percent': row[5] or 0
            }
        
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate_percent': 0,
            'avg_profit_percent': 0,
            'avg_duration_minutes': 0,
            'best_trade_percent': 0,
            'worst_trade_percent': 0
        }
