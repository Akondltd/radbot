"""
Pair Price History Service - Stores and retrieves historical price data for token pairs
Uses Astrolescent prices instead of pool-specific data for more reliable indicators
"""
import sqlite3
import logging
import time
from typing import List, Dict, Optional
from decimal import Decimal
from config.paths import DATABASE_PATH
from services.astrolescent_price_service import get_price_service

logger = logging.getLogger(__name__)

class PairPriceHistoryService:
    """
    Service to store and retrieve historical price data for token pairs.
    Replaces pool-based price history with pair-based history using Astrolescent prices.
    """
    
    def __init__(self):
        """Initialize the price history service using the canonical DATABASE_PATH."""
        self.db_path = str(DATABASE_PATH)
        self._initialize_tables()
    
    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def _initialize_tables(self):
        """Create pair_price_history table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # New table for token pair history (not pool-based)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pair_price_history (
                    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_token TEXT NOT NULL,
                    quote_token TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL DEFAULT 0,
                    base_token_symbol TEXT,
                    quote_token_symbol TEXT,
                    UNIQUE (base_token, quote_token, timestamp)
                )
            ''')
            
            # Create indexes for fast lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pair_history_tokens_timestamp 
                ON pair_price_history (base_token, quote_token, timestamp DESC)
            ''')
            
            conn.commit()
            logger.info("Pair price history table initialized")
    
    def _normalize_pair(self, base_token: str, quote_token: str) -> tuple[str, str, bool]:
        """
        Normalize token pair using deterministic lexicographic ordering.
        
        The alphabetically smaller address is always base, the larger is always
        quote.  This is completely independent of live prices, so stablecoin
        pairs (e.g. xUSDT/hUSDC) can never flip-flop between recording and
        querying.
        
        Args:
            base_token: Base token address
            quote_token: Quote token address
            
        Returns:
            Tuple of (normalized_base, normalized_quote, was_swapped)
        """
        if base_token <= quote_token:
            return base_token, quote_token, False
        else:
            return quote_token, base_token, True
    
    def record_current_price(self, base_token: str, quote_token: str) -> bool:
        """
        Record the current price for a token pair as a data point.
        Uses Astrolescent price service to get current price.
        Automatically normalizes pair using deterministic address ordering.
        
        Args:
            base_token: Base token address
            quote_token: Quote token address
            
        Returns:
            True if successfully recorded, False otherwise
        """
        try:
            price_service = get_price_service()
            
            # Normalize the pair (deterministic address ordering)
            norm_base, norm_quote, was_swapped = self._normalize_pair(base_token, quote_token)
            
            # Get current price for the NORMALIZED pair
            current_price = price_service.get_pair_price(norm_base, norm_quote)
            if current_price is None:
                logger.warning(f"Could not get price for {norm_base}/{norm_quote}")
                return False
            
            # Get token info for symbols
            base_token_data = price_service.get_token_price(norm_base)
            quote_token_data = price_service.get_token_price(norm_quote)
            
            base_symbol = base_token_data.get('symbol', 'UNKNOWN') if base_token_data else 'UNKNOWN'
            quote_symbol = quote_token_data.get('symbol', 'UNKNOWN') if quote_token_data else 'UNKNOWN'
            
            # Current timestamp (minute granularity)
            current_time = int(time.time() // 60) * 60  # Round to minute
            
            # Aggregate price updates into OHLC candles
            price_float = float(current_price)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if a candle already exists for this timestamp
                cursor.execute('''
                    SELECT open_price, high_price, low_price, close_price
                    FROM pair_price_history
                    WHERE base_token = ? AND quote_token = ? AND timestamp = ?
                ''', (norm_base, norm_quote, current_time))
                
                existing_candle = cursor.fetchone()
                
                if existing_candle:
                    # Update existing candle: keep Open, update High/Low/Close
                    open_price = existing_candle[0]  # Keep original open
                    high_price = max(existing_candle[1], price_float)  # Update high
                    low_price = min(existing_candle[2], price_float)   # Update low
                    close_price = price_float  # Always update close to latest
                    
                    cursor.execute('''
                        UPDATE pair_price_history
                        SET high_price = ?,
                            low_price = ?,
                            close_price = ?
                        WHERE base_token = ? AND quote_token = ? AND timestamp = ?
                    ''', (high_price, low_price, close_price, norm_base, norm_quote, current_time))
                    
                    conn.commit()
                    swap_note = " (swapped)" if was_swapped else ""
                    logger.debug(
                        f"Updated candle for {base_symbol}/{quote_symbol}: "
                        f"O:{open_price:.6f} H:{high_price:.6f} L:{low_price:.6f} C:{close_price:.6f}{swap_note}"
                    )
                    return True
                else:
                    # Create new candle: Open = previous candle's Close, Close = current price
                    # Get the most recent previous candle to link open price
                    cursor.execute('''
                        SELECT close_price
                        FROM pair_price_history
                        WHERE base_token = ? AND quote_token = ? AND timestamp < ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ''', (norm_base, norm_quote, current_time))
                    
                    prev_candle = cursor.fetchone()
                    
                    if prev_candle:
                        # Open = previous candle's close
                        open_price = prev_candle[0]
                        close_price = price_float
                        # High and Low are max/min of open and close
                        high_price = max(open_price, close_price)
                        low_price = min(open_price, close_price)
                    else:
                        # First candle ever for this pair: all values = current price
                        open_price = price_float
                        high_price = price_float
                        low_price = price_float
                        close_price = price_float
                    
                    cursor.execute('''
                        INSERT INTO pair_price_history 
                        (base_token, quote_token, timestamp, open_price, high_price, low_price, 
                         close_price, volume, base_token_symbol, quote_token_symbol)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (norm_base, norm_quote, current_time, 
                          open_price, high_price, low_price, close_price, 
                          0, base_symbol, quote_symbol))
                    
                    conn.commit()
                    swap_note = " (swapped)" if was_swapped else ""
                    if prev_candle:
                        logger.debug(
                            f"New candle for {base_symbol}/{quote_symbol}: "
                            f"O:{open_price:.6f} (prev close) H:{high_price:.6f} L:{low_price:.6f} C:{close_price:.6f}{swap_note}"
                        )
                    else:
                        logger.debug(
                            f"First candle for {base_symbol}/{quote_symbol}: "
                            f"O:{open_price:.6f} (first ever){swap_note}"
                        )
                    return True
                    
        except Exception as e:
            logger.error(f"Error recording price for {base_token}/{quote_token}: {e}", exc_info=True)
            return False
    
    def get_price_history(self, base_token: str, quote_token: str, limit: int = 1000) -> List[Dict]:
        """
        Get historical price data for a token pair.
        Returns data in chronological order (oldest to newest).
        Automatically normalizes pair to match how data was stored.
        
        Args:
            base_token: Base token address
            quote_token: Quote token address
            limit: Maximum number of candles to return
            
        Returns:
            List of price candles as dictionaries
        """
        try:
            # Normalize the pair to match storage
            norm_base, norm_quote, was_swapped = self._normalize_pair(base_token, quote_token)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.row_factory = sqlite3.Row
                
                # Get most recent data in reverse, then flip order (using NORMALIZED pair)
                cursor.execute('''
                    SELECT * FROM (
                        SELECT timestamp, 
                               open_price AS open,
                               high_price AS high,
                               low_price AS low,
                               close_price AS close,
                               volume,
                               base_token_symbol,
                               quote_token_symbol
                        FROM pair_price_history
                        WHERE base_token = ? AND quote_token = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ) ORDER BY timestamp ASC
                ''', (norm_base, norm_quote, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows] if rows else []
                
        except Exception as e:
            logger.error(f"Error fetching price history for {base_token}/{quote_token}: {e}", exc_info=True)
            return []
    
    def get_latest_price(self, base_token: str, quote_token: str) -> Optional[Decimal]:
        """
        Get the most recent price for a token pair from history.
        Automatically normalizes pair to match how data was stored.
        
        Args:
            base_token: Base token address
            quote_token: Quote token address
            
        Returns:
            Latest price as Decimal, or None if no history exists
        """
        try:
            # Normalize the pair to match storage
            norm_base, norm_quote, was_swapped = self._normalize_pair(base_token, quote_token)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT close_price
                    FROM pair_price_history
                    WHERE base_token = ? AND quote_token = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (norm_base, norm_quote))
                
                result = cursor.fetchone()
                return Decimal(str(result[0])) if result else None
                
        except Exception as e:
            logger.error(f"Error fetching latest price for {base_token}/{quote_token}: {e}", exc_info=True)
            return None
    
    def get_data_point_count(self, base_token: str, quote_token: str) -> int:
        """
        Get the number of historical data points available for a pair.
        Automatically normalizes pair to match how data was stored.
        
        Args:
            base_token: Base token address
            quote_token: Quote token address
            
        Returns:
            Number of data points
        """
        try:
            # Normalize the pair to match storage
            norm_base, norm_quote, was_swapped = self._normalize_pair(base_token, quote_token)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM pair_price_history
                    WHERE base_token = ? AND quote_token = ?
                ''', (norm_base, norm_quote))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error counting data points for {base_token}/{quote_token}: {e}", exc_info=True)
            return 0
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Remove historical data older than specified days.
        
        Args:
            days_to_keep: Number of days of history to retain
        """
        try:
            cutoff_time = int(time.time()) - (days_to_keep * 24 * 60 * 60)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM pair_price_history
                    WHERE timestamp < ?
                ''', (cutoff_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old price history records (older than {days_to_keep} days)")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old price data: {e}", exc_info=True)
    
    def record_all_active_pairs(self) -> int:
        """
        Record current prices for all selected trade pairs in the database.
        Uses selected_pairs table so history builds as soon as a user adds a pair,
        even before they create an active trade.
        
        Returns:
            Number of pairs successfully recorded
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get distinct pairs from selected_pairs (all user-selected pairs)
                cursor.execute('''
                    SELECT DISTINCT tp.base_token, tp.quote_token
                    FROM trade_pairs tp
                    INNER JOIN selected_pairs sp ON sp.trade_pair_id = tp.trade_pair_id
                ''')
                
                pairs = cursor.fetchall()
            
            if not pairs:
                logger.info("No selected trade pairs to record prices for")
                return 0
            
            recorded_count = 0
            for base_token, quote_token in pairs:
                if self.record_current_price(base_token, quote_token):
                    recorded_count += 1
            
            logger.info(f"Recorded prices for {recorded_count}/{len(pairs)} selected pairs")
            return recorded_count
            
        except Exception as e:
            logger.error(f"Error recording prices for selected pairs: {e}", exc_info=True)
            return 0


# Global singleton instance
_pair_history_service = None

def get_pair_history_service() -> PairPriceHistoryService:
    """Get the global pair history service instance."""
    global _pair_history_service
    if _pair_history_service is None:
        _pair_history_service = PairPriceHistoryService()
    return _pair_history_service
