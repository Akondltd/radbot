import sqlite3
import logging
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

class StatisticsManager:
    """Manages statistics data in the database."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def ensure_statistics_entry(self, wallet_id: int):
        """
        Ensures that a statistics entry exists for the given wallet_id.
        If it doesn't exist, a new one is created with default values.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM statistics WHERE wallet_id = ?", (wallet_id,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute("INSERT INTO statistics (wallet_id) VALUES (?)", (wallet_id,))
                self.conn.commit()
                logger.info(f"Created statistics entry for wallet_id: {wallet_id}")
        except sqlite3.Error as e:
            logger.error(f"Database error in ensure_statistics_entry for wallet_id {wallet_id}: {e}", exc_info=True)
            self.conn.rollback()
    
    def record_trade_flip(self, wallet_id: int, profit_loss_usd: Decimal, profit_loss_xrd: Decimal, is_profitable: bool):
        """
        Record a completed trade flip and update statistics.
        
        Args:
            wallet_id: The wallet ID
            profit_loss_usd: Profit or loss in USD at time of trade (positive or negative)
            profit_loss_xrd: Profit or loss in XRD at time of trade (positive or negative)
            is_profitable: True if this flip made profit
        """
        try:
            cursor = self.conn.cursor()
            
            # Ensure statistics entry exists
            self.ensure_statistics_entry(wallet_id)
            
            # Get current statistics - try new schema first, fallback to old
            try:
                cursor.execute("""
                    SELECT winning_trades, losing_trades, total_profit_loss_quote,
                           longest_winning_streak, longest_losing_streak,
                           total_profit, total_loss, total_profit_xrd, total_loss_xrd
                    FROM statistics WHERE wallet_id = ?
                """, (wallet_id,))
                
                stats = cursor.fetchone()
                if not stats:
                    logger.error(f"No statistics entry found for wallet_id {wallet_id} after ensure")
                    return
                    
                winning_trades, losing_trades, total_profit_loss, win_streak, lose_streak, total_profit, total_loss, total_profit_xrd, total_loss_xrd = stats
                has_xrd_columns = True
            except sqlite3.OperationalError:
                # XRD columns don't exist, use old schema
                logger.warning(f"XRD columns not found, using old schema for wallet_id {wallet_id}")
                cursor.execute("""
                    SELECT winning_trades, losing_trades, total_profit_loss_quote,
                           longest_winning_streak, longest_losing_streak,
                           total_profit, total_loss
                    FROM statistics WHERE wallet_id = ?
                """, (wallet_id,))
                
                stats = cursor.fetchone()
                if not stats:
                    logger.error(f"No statistics entry found for wallet_id {wallet_id} after ensure")
                    return
                    
                winning_trades, losing_trades, total_profit_loss, win_streak, lose_streak, total_profit, total_loss = stats
                total_profit_xrd = Decimal('0')
                total_loss_xrd = Decimal('0')
                has_xrd_columns = False
            
            winning_trades = winning_trades or 0
            losing_trades = losing_trades or 0
            total_profit_loss = Decimal(str(total_profit_loss)) if total_profit_loss else Decimal('0')
            total_profit = Decimal(str(total_profit)) if total_profit else Decimal('0')
            total_loss = Decimal(str(total_loss)) if total_loss else Decimal('0')
            total_profit_xrd = Decimal(str(total_profit_xrd)) if total_profit_xrd else Decimal('0')
            total_loss_xrd = Decimal(str(total_loss_xrd)) if total_loss_xrd else Decimal('0')
            win_streak = win_streak or 0
            lose_streak = lose_streak or 0
            
            # Update counters
            if is_profitable:
                winning_trades += 1
                win_streak += 1
                lose_streak = 0  # Reset losing streak
                # Add to profit (both USD and XRD at time of trade)
                total_profit += profit_loss_usd
                total_profit_xrd += profit_loss_xrd
            else:
                losing_trades += 1
                lose_streak += 1
                win_streak = 0  # Reset winning streak
                # Add to loss (store as positive value, both USD and XRD at time of trade)
                total_loss += abs(profit_loss_usd)
                total_loss_xrd += abs(profit_loss_xrd)
            
            # Update total profit/loss (net)
            total_profit_loss += profit_loss_usd
            
            # Calculate win rate
            total_flips = winning_trades + losing_trades
            win_rate = (winning_trades / total_flips * 100) if total_flips > 0 else 0.0
            
            # Calculate average profit/loss per trade
            avg_profit = (total_profit / total_flips) if total_flips > 0 else Decimal('0')
            
            # Update statistics - use appropriate query based on schema
            if has_xrd_columns:
                cursor.execute("""
                    UPDATE statistics SET
                        winning_trades = ?,
                        losing_trades = ?,
                        total_profit_loss_quote = ?,
                        total_profit = ?,
                        total_loss = ?,
                        total_profit_xrd = ?,
                        total_loss_xrd = ?,
                        win_rate_percentage = ?,
                        average_profit_per_trade_quote = ?,
                        longest_winning_streak = MAX(longest_winning_streak, ?),
                        longest_losing_streak = MAX(longest_losing_streak, ?),
                        last_calculated = CURRENT_TIMESTAMP
                    WHERE wallet_id = ?
                """, (
                    winning_trades,
                    losing_trades,
                    float(total_profit_loss),
                    float(total_profit),
                    float(total_loss),
                    float(total_profit_xrd),
                    float(total_loss_xrd),
                    win_rate,
                    float(avg_profit),
                    win_streak,
                    lose_streak,
                    wallet_id
                ))
            else:
                # Old schema without XRD columns
                cursor.execute("""
                    UPDATE statistics SET
                        winning_trades = ?,
                        losing_trades = ?,
                        total_profit_loss_quote = ?,
                        total_profit = ?,
                        total_loss = ?,
                        win_rate_percentage = ?,
                        average_profit_per_trade_quote = ?,
                        longest_winning_streak = MAX(longest_winning_streak, ?),
                        longest_losing_streak = MAX(longest_losing_streak, ?),
                        last_calculated = CURRENT_TIMESTAMP
                    WHERE wallet_id = ?
                """, (
                    winning_trades,
                    losing_trades,
                    float(total_profit_loss),
                    float(total_profit),
                    float(total_loss),
                    win_rate,
                    float(avg_profit),
                    win_streak,
                    lose_streak,
                    wallet_id
                ))
            
            self.conn.commit()
            logger.info(f"Recorded trade flip for wallet {wallet_id}: profit_usd={profit_loss_usd:.2f}, profit_xrd={profit_loss_xrd:.4f}, profitable={is_profitable}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error recording trade flip for wallet_id {wallet_id}: {e}", exc_info=True)
            self.conn.rollback()
    
    def get_statistics(self, wallet_id: int) -> Optional[dict]:
        """
        Get all statistics for a wallet.
        
        Args:
            wallet_id: The wallet ID
            
        Returns:
            Dictionary with all statistics or None if not found
        """
        try:
            cursor = self.conn.cursor()
            
            # Try to query with XRD columns first (new schema)
            try:
                cursor.execute("""
                    SELECT winning_trades, losing_trades, win_rate_percentage,
                           total_profit_loss_quote, average_profit_per_trade_quote,
                           longest_winning_streak, longest_losing_streak,
                           total_trades_created, total_trades_deleted,
                           total_profit, total_loss, total_profit_xrd, total_loss_xrd
                    FROM statistics WHERE wallet_id = ?
                """, (wallet_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return {
                    'winning_trades': row[0] or 0,
                    'losing_trades': row[1] or 0,
                    'win_rate_percentage': row[2] or 0.0,
                    'total_profit_loss': row[3] or 0.0,
                    'average_profit_per_trade': row[4] or 0.0,
                    'longest_winning_streak': row[5] or 0,
                    'longest_losing_streak': row[6] or 0,
                    'total_trades_created': row[7] or 0,
                    'total_trades_deleted': row[8] or 0,
                    'total_profit': row[9] or 0.0,
                    'total_loss': row[10] or 0.0,
                    'total_profit_xrd': row[11] or 0.0,
                    'total_loss_xrd': row[12] or 0.0
                }
            except sqlite3.OperationalError as e:
                # XRD columns don't exist yet, fall back to old schema
                logger.warning(f"XRD columns not found in statistics table, using old schema: {e}")
                cursor.execute("""
                    SELECT winning_trades, losing_trades, win_rate_percentage,
                           total_profit_loss_quote, average_profit_per_trade_quote,
                           longest_winning_streak, longest_losing_streak,
                           total_trades_created, total_trades_deleted,
                           total_profit, total_loss
                    FROM statistics WHERE wallet_id = ?
                """, (wallet_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return {
                    'winning_trades': row[0] or 0,
                    'losing_trades': row[1] or 0,
                    'win_rate_percentage': row[2] or 0.0,
                    'total_profit_loss': row[3] or 0.0,
                    'average_profit_per_trade': row[4] or 0.0,
                    'longest_winning_streak': row[5] or 0,
                    'longest_losing_streak': row[6] or 0,
                    'total_trades_created': row[7] or 0,
                    'total_trades_deleted': row[8] or 0,
                    'total_profit': row[9] or 0.0,
                    'total_loss': row[10] or 0.0,
                    'total_profit_xrd': 0.0,  # Default to 0 if columns don't exist
                    'total_loss_xrd': 0.0     # Default to 0 if columns don't exist
                }
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting statistics for wallet_id {wallet_id}: {e}", exc_info=True)
            return None
