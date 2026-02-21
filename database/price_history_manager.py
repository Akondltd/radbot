import logging
import sqlite3

logger = logging.getLogger(__name__)

class PriceHistoryManager:
    """Manages database operations for the price_history table."""

    def __init__(self, conn):
        """Initializes the PriceHistoryManager with a database connection."""
        self.conn = conn

    def get_price_history_by_pool_address(self, pool_address: str, limit: int = 1000) -> list[dict]:
        """
        Retrieves the most recent price history for a specific Ociswap pool,
        sorted chronologically (oldest to newest).

        Args:
            pool_address: The address of the Ociswap pool.
            limit: The maximum number of records to retrieve.

        Returns:
            A list of dictionaries, where each dictionary represents a price candle.
        """
        try:
            cursor = self.conn.cursor()
            cursor.row_factory = sqlite3.Row
            # To get the MOST RECENT 'limit' records in chronological order, we need a subquery.
            # Return raw OHLC plus user_friendly_price for conversion
            # Chart will scale and convert based on trade's pricing_token preference
            sub_query = f"SELECT * FROM price_history WHERE pair = ? ORDER BY timestamp DESC LIMIT ?"
            final_query = f"""SELECT timestamp, 
                open_price AS open,
                high_price AS high,
                low_price AS low,
                close_price AS close,
                volume,
                user_friendly_price,
                base_token_usd_price,
                quote_token_usd_price
                FROM ({sub_query}) ORDER BY timestamp ASC"""

            cursor.execute(final_query, (pool_address, limit))
            rows = cursor.fetchall()

            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logger.error(f"Error fetching price history for pool_address {pool_address}: {e}", exc_info=True)
            return []
