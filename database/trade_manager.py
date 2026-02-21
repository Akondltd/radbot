import logging
import sqlite3
import time
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

class TradeManager:
    """Manages trade data in the database."""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self._create_table_if_not_exists()
        self._create_trade_flips_table_if_not_exists()
        self._create_trade_history_table_if_not_exists()

    def _add_column_if_not_exists(self, cursor, table_name, column_name, column_type):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            logger.info(f"Adding column '{column_name}' to table '{table_name}'.")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    def _create_table_if_not_exists(self):
        """
        Creates the 'trades' table in the database if it doesn't already exist,
        using the new, approved schema. Also renames the old 'active_trades' table
        to 'active_trades_old' to prevent data loss and conflicts.
        """
        try:
            cursor = self.conn.cursor()
            
            # Rename old table if it exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='active_trades'")
            if cursor.fetchone():
                logger.info("Found old 'active_trades' table. Renaming to 'active_trades_old'.")
                try:
                    cursor.execute("ALTER TABLE active_trades RENAME TO active_trades_old;")
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e):
                        logger.warning("Table 'active_trades_old' already exists. Skipping rename.")
                    else:
                        raise e

            # Create new trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_pair_id INTEGER NOT NULL,
                    wallet_address TEXT NOT NULL,
                    start_token_address TEXT NOT NULL,
                    start_token_symbol TEXT,
                    start_amount TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    is_compounding BOOLEAN NOT NULL DEFAULT 0,
                    strategy_name TEXT NOT NULL,
                    indicator_settings_json TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    current_signal TEXT,
                    last_signal_updated_at INTEGER,
                    times_flipped REAL DEFAULT 0,
                    profitable_flips INTEGER NOT NULL DEFAULT 0,
                    unprofitable_flips INTEGER NOT NULL DEFAULT 0,
                    total_profit TEXT NOT NULL DEFAULT '0',
                    trade_volume TEXT NOT NULL DEFAULT '0',
                    ociswap_pool_address TEXT,
                    trade_amount TEXT,
                    trade_token_address TEXT,
                    trade_token_symbol TEXT,
                    accumulation_token_symbol TEXT,
                    accumulation_token_address TEXT,
                    FOREIGN KEY (trade_pair_id) REFERENCES trade_pairs (trade_pair_id) ON DELETE CASCADE
                );            """)

            # Add new columns if they don't exist (for backward compatibility)
            self._add_column_if_not_exists(cursor, 'trades', 'is_active', 'BOOLEAN DEFAULT TRUE')
            self._add_column_if_not_exists(cursor, 'trades', 'current_signal', 'TEXT')
            self._add_column_if_not_exists(cursor, 'trades', 'last_signal_updated_at', 'INTEGER')
            self._add_column_if_not_exists(cursor, 'trades', 'ociswap_pool_address', 'TEXT')
            self._add_column_if_not_exists(cursor, 'trades', 'times_flipped', 'REAL DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'trades', 'profitable_flips', 'INTEGER DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'trades', 'unprofitable_flips', 'INTEGER DEFAULT 0')
            
            # CRITICAL FIX: Migrate trade_amount from REAL to TEXT for precision
            # REAL (float) loses precision for tokens with high divisibility (e.g., hUSDC with 6 decimals)
            # This causes negative balances and rounding errors
            try:
                cursor.execute("PRAGMA table_info(trades)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}  # {name: type}
                
                if 'trade_amount' in columns and columns['trade_amount'].upper() == 'REAL':
                    logger.info("Migrating trade_amount column from REAL to TEXT for precision...")
                    
                    # SQLite doesn't support ALTER COLUMN TYPE, so we need to:
                    # 1. Add temp column as TEXT
                    # 2. Copy data (converting REAL to TEXT)
                    # 3. Drop old column
                    # 4. Rename temp column
                    
                    # Check if temp column already exists (from previous failed migration)
                    cursor.execute("PRAGMA table_info(trades)")
                    columns = [col[1] for col in cursor.fetchall()]
                    if 'trade_amount_temp' not in columns:
                        cursor.execute("ALTER TABLE trades ADD COLUMN trade_amount_temp TEXT")
                    else:
                        logger.info("trade_amount_temp column already exists from previous migration attempt")
                    
                    # Always populate temp column with data (in case previous migration was interrupted)
                    cursor.execute("UPDATE trades SET trade_amount_temp = CAST(trade_amount AS TEXT) WHERE trade_amount_temp IS NULL OR trade_amount_temp = ''")
                    
                    # SQLite also doesn't support DROP COLUMN in older versions, so recreate table
                    # Get all data first
                    cursor.execute("SELECT * FROM trades")
                    all_trades = cursor.fetchall()
                    
                    # Get column names (excluding trade_amount)
                    cursor.execute("PRAGMA table_info(trades)")
                    old_cols = cursor.fetchall()
                    
                    # Drop and recreate with correct schema
                    cursor.execute("DROP TABLE IF EXISTS trades_old_backup")
                    cursor.execute("ALTER TABLE trades RENAME TO trades_old_backup")
                    
                    # Recreate with correct schema (trade_amount as TEXT)
                    cursor.execute("""
                        CREATE TABLE trades (
                            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            trade_pair_id INTEGER NOT NULL,
                            wallet_address TEXT NOT NULL,
                            start_token_address TEXT NOT NULL,
                            start_token_symbol TEXT,
                            start_amount TEXT NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT 1,
                            is_compounding BOOLEAN NOT NULL DEFAULT 0,
                            strategy_name TEXT NOT NULL,
                            indicator_settings_json TEXT,
                            created_at INTEGER NOT NULL,
                            updated_at INTEGER NOT NULL,
                            current_signal TEXT,
                            last_signal_updated_at INTEGER,
                            times_flipped REAL DEFAULT 0,
                            profitable_flips INTEGER NOT NULL DEFAULT 0,
                            unprofitable_flips INTEGER NOT NULL DEFAULT 0,
                            total_profit TEXT NOT NULL DEFAULT '0',
                            trade_volume TEXT NOT NULL DEFAULT '0',
                            ociswap_pool_address TEXT,
                            trade_amount TEXT,
                            trade_token_address TEXT,
                            trade_token_symbol TEXT,
                            accumulation_token_symbol TEXT,
                            accumulation_token_address TEXT,
                            reserved_amount TEXT DEFAULT '0',
                            FOREIGN KEY (trade_pair_id) REFERENCES trade_pairs (trade_pair_id) ON DELETE CASCADE
                        )
                    """)
                    
                    # Copy data back (using trade_amount_temp for trade_amount)
                    cursor.execute("""
                        INSERT INTO trades SELECT 
                            trade_id, trade_pair_id, wallet_address, start_token_address, 
                            start_token_symbol, start_amount, is_active, is_compounding, 
                            strategy_name, indicator_settings_json, created_at, updated_at, 
                            current_signal, last_signal_updated_at, times_flipped, 
                            profitable_flips, unprofitable_flips, total_profit, trade_volume, 
                            ociswap_pool_address, trade_amount_temp, trade_token_address, 
                            trade_token_symbol, accumulation_token_symbol, accumulation_token_address,
                            COALESCE(reserved_amount, '0')
                        FROM trades_old_backup
                    """)
                    
                    self.conn.commit()
                    logger.info("Successfully migrated trade_amount to TEXT type")
                    
                    # Keep backup table for safety
                    logger.info("Backup table 'trades_old_backup' preserved for safety")
                    
            except Exception as e:
                logger.error(f"Error during trade_amount migration: {e}", exc_info=True)
                self.conn.rollback()
                # Continue anyway - worst case is we keep using REAL type
            self._add_column_if_not_exists(cursor, 'trades', 'total_profit', 'REAL DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'trades', 'trade_volume', 'REAL DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'trades', 'accumulation_token_symbol', 'TEXT')
            self._add_column_if_not_exists(cursor, 'trades', 'accumulation_token_address', 'TEXT')
            self._add_column_if_not_exists(cursor, 'trades', 'peak_profit_xrd', 'REAL DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'trades', 'reserved_amount', 'TEXT DEFAULT "0"')  # For Kelly criterion partial positions
            self._add_column_if_not_exists(cursor, 'trades', 'start_token_symbol', 'TEXT')  # Symbol of the starting token
            
            # Fix trade_token_symbol if it was created as REAL instead of TEXT
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trades'")
                schema = cursor.fetchone()
                if schema and 'trade_token_symbol' in schema[0]:
                    if 'trade_token_symbol" REAL' in schema[0] or 'trade_token_symbol REAL' in schema[0]:
                        logger.warning("Detected trade_token_symbol with incorrect REAL type. Migrating to TEXT...")
                        # SQLite doesn't support ALTER COLUMN, so we need to:
                        # 1. Create temp column
                        # 2. Copy data
                        # 3. Drop old column
                        # 4. Rename temp column
                        cursor.execute("ALTER TABLE trades ADD COLUMN trade_token_symbol_temp TEXT")
                        cursor.execute("UPDATE trades SET trade_token_symbol_temp = CAST(trade_token_symbol AS TEXT)")
                        cursor.execute("ALTER TABLE trades DROP COLUMN trade_token_symbol")
                        cursor.execute("ALTER TABLE trades RENAME COLUMN trade_token_symbol_temp TO trade_token_symbol")
                        logger.info("Successfully migrated trade_token_symbol to TEXT type")
                else:
                    # Column doesn't exist, add it
                    self._add_column_if_not_exists(cursor, 'trades', 'trade_token_symbol', 'TEXT')
            except sqlite3.OperationalError as e:
                # If DROP COLUMN not supported (older SQLite), just add the column if missing
                logger.warning(f"Could not migrate trade_token_symbol type: {e}")
                self._add_column_if_not_exists(cursor, 'trades', 'trade_token_symbol', 'TEXT')

            self.conn.commit()
            logger.info("Ensured 'trades' table exists with the correct schema.")
        except sqlite3.Error as e:
            logger.error(f"Database error while creating/checking 'trades' table: {e}")
            raise

    def _create_trade_flips_table_if_not_exists(self):
        """Creates the trade_flips table if it doesn't exist."""
        query = '''
        CREATE TABLE IF NOT EXISTS trade_flips (
            flip_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            flip_type TEXT NOT NULL CHECK(flip_type IN ('BUY', 'SELL')),
            amount_in TEXT NOT NULL,
            token_in_address TEXT NOT NULL,
            amount_out TEXT NOT NULL,
            token_out_address TEXT NOT NULL,
            price REAL NOT NULL,
            transaction_id TEXT UNIQUE,
            FOREIGN KEY(trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
        );
        '''
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()

    def _create_trade_history_table_if_not_exists(self):
        """Creates the trade_history table if it doesn't exist."""
        query = '''
        CREATE TABLE IF NOT EXISTS trade_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id_original INTEGER NOT NULL,
            wallet_address TEXT NOT NULL,
            pair TEXT NOT NULL,
            side TEXT NOT NULL CHECK(side IN ('BUY', 'SELL')),
            amount_base TEXT NOT NULL,
            amount_quote TEXT NOT NULL,
            price REAL NOT NULL,
            usd_value REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'FAILED')),
            strategy_name TEXT NOT NULL,
            transaction_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            profit TEXT DEFAULT NULL,
            profit_usd REAL DEFAULT NULL,
            profit_xrd REAL DEFAULT NULL
        );
        '''
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        # Migrate existing databases: add columns if they don't exist
        try:
            cursor.execute("PRAGMA table_info(trade_history)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            if 'profit_usd' not in existing_columns:
                cursor.execute("ALTER TABLE trade_history ADD COLUMN profit_usd REAL DEFAULT NULL")
                logger.info("Migrated trade_history: added profit_usd column")
            if 'profit_xrd' not in existing_columns:
                cursor.execute("ALTER TABLE trade_history ADD COLUMN profit_xrd REAL DEFAULT NULL")
                logger.info("Migrated trade_history: added profit_xrd column")
        except sqlite3.Error as e:
            logger.warning(f"trade_history migration check: {e}")
        
        self.conn.commit()
        
    def get_active_ai_trades(self) -> list[dict[str, Any]]:
        """
        Retrieves all active trades managed by the AI strategy.

        Returns:
            A list of dictionaries, where each dictionary represents an active AI trade.
        """
        sql = "SELECT * FROM trades WHERE is_active = 1 AND strategy_name = 'AI_Strategy'"
        try:
            cursor = self.conn.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute(sql)
            rows = cursor.fetchall()
            trades = [dict(row) for row in rows]
            logger.debug(f"Found {len(trades)} active AI trades.")
            return trades
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch active AI trades. Error: {e}")
            return []

    def get_trade_pair_by_id(self, trade_pair_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves details for a specific trade pair by its ID.

        Args:
            trade_pair_id: The ID of the trade pair to retrieve.

        Returns:
            A dictionary containing the trade pair details, or None if not found.
        """
        sql = """
            SELECT
                tp.*, -- Select all columns from the trade_pairs table
                base.symbol AS base_token_symbol,
                quote.symbol AS quote_token_symbol
            FROM
                trade_pairs tp
            JOIN
                tokens base ON tp.base_token = base.address
            JOIN
                tokens quote ON tp.quote_token = quote.address
            WHERE
                tp.trade_pair_id = ?
        """
        try:
            cursor = self.conn.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute(sql, (trade_pair_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch trade pair for ID {trade_pair_id}. Error: {e}")
            return None

    def get_all_active_trades(self, wallet_address: str) -> list:
        """
        Retrieves all trades (both active and paused) for a specific wallet.
        
        Note: Despite the name, this returns both active (is_active=1) and paused (is_active=0) 
        trades so users can view and manage all their trades in the GUI.

        Args:
            wallet_address: The wallet address to filter trades by.

        Returns:
            A list of dictionaries, where each dictionary represents a trade.
        """
        sql = """
            SELECT
                t.*, -- Select all columns from the trades table
                tp.base_token,
                tp.quote_token,
                base.symbol AS base_token_symbol,
                quote.symbol AS quote_token_symbol,
                start_token.symbol AS start_token_symbol
            FROM
                trades t
            JOIN
                trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
            JOIN
                tokens base ON tp.base_token = base.address
            JOIN
                tokens quote ON tp.quote_token = quote.address
            JOIN
                tokens start_token ON t.start_token_address = start_token.address
            WHERE
                t.wallet_address = ?
            ORDER BY
                t.created_at DESC
        """
        try:
            cursor = self.conn.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute(sql, (wallet_address,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch active trades for wallet {wallet_address}. Error: {e}")
            return []

    def get_trade_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves all details for a specific trade by its ID."""
        sql = """
            SELECT
                t.*, -- Select all columns from the trades table
                tp.base_token,
                tp.quote_token,
                base.symbol AS base_token_symbol,
                quote.symbol AS quote_token_symbol,
                start_token.symbol AS start_token_symbol
            FROM
                trades t
            JOIN
                trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
            JOIN
                tokens base ON tp.base_token = base.address
            JOIN
                tokens quote ON tp.quote_token = quote.address
            JOIN
                tokens start_token ON t.start_token_address = start_token.address
            WHERE
                t.trade_id = ?
        """
        try:
            cursor = self.conn.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute(sql, (trade_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                logger.warning(f"No trade found for ID: {trade_id}")
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch trade for ID {trade_id}. Error: {e}")
            return None

    def update_trade(self, trade_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Updates a trade with the given data.

        Args:
            trade_id: The ID of the trade to update.
            update_data: A dictionary of column names and their new values.
        
        Returns:
            True if update was successful, False otherwise.
        """
        if not update_data:
            logger.warning("update_trade called with no data to update.")
            return False

        # Automatically update the timestamp
        update_data['updated_at'] = int(time.time())

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(trade_id)

        sql = f"UPDATE trades SET {set_clause} WHERE trade_id = ?"

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(values))
            self.conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Attempted to update non-existent trade_id: {trade_id}")
                return False
            else:
                logger.info(f"Successfully updated trade_id {trade_id}.")
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to update trade_id {trade_id}. Error: {e}")
            self.conn.rollback()
            return False

    def update_trade_signal(self, trade_id: int, signal: str):
        """
        Updates the current signal for a specific trade.

        Args:
            trade_id: The ID of the trade to update.
            signal: The new signal string (e.g., 'BUY', 'SELL', 'HOLD').
        """
        sql = "UPDATE trades SET current_signal = ?, last_signal_updated_at = ? WHERE trade_id = ?"
        try:
            current_timestamp = int(time.time())
            cursor = self.conn.cursor()
            cursor.execute(sql, (signal, current_timestamp, trade_id))
            self.conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"Attempted to update signal for non-existent trade_id: {trade_id}")
            else:
                logger.debug(f"Successfully updated signal for trade_id {trade_id} to '{signal}'.")
        except sqlite3.Error as e:
            logger.error(f"Failed to update signal for trade_id {trade_id}. Error: {e}")
            self.conn.rollback()

    def toggle_trade_active_state(self, trade_id: int) -> bool:
        """
        Toggles the is_active state of a trade.
        
        Args:
            trade_id: The ID of the trade to toggle.
            
        Returns:
            True if the operation was successful, False otherwise.
        """
        # First, get the current state
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT is_active FROM trades WHERE trade_id = ?", (trade_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Attempted to toggle state for non-existent trade_id: {trade_id}")
                return False
                
            current_state = result[0]
            # Toggle the state (0 -> 1, 1 -> 0)
            new_state = 0 if current_state else 1
            
            # Update the record
            cursor.execute(
                "UPDATE trades SET is_active = ?, updated_at = ? WHERE trade_id = ?", 
                (new_state, int(time.time()), trade_id)
            )
            self.conn.commit()
            
            if cursor.rowcount == 0:
                logger.warning(f"No rows affected when toggling state for trade_id: {trade_id}")
                return False
                
            logger.info(f"Successfully toggled active state for trade_id {trade_id} to {new_state}.")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to toggle active state for trade_id {trade_id}. Error: {e}")
            self.conn.rollback()
            return False

    def add_trade_flip(self, flip_data: dict):
        """Adds a new flip record to the trade_flips table."""
        keys = ', '.join(flip_data.keys())
        placeholders = ', '.join(['?'] * len(flip_data))
        query = f"INSERT INTO trade_flips ({keys}) VALUES ({placeholders})"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, tuple(flip_data.values()))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database error while adding trade flip: {e}")
            self.conn.rollback()
            return None

    def get_flips_for_trade(self, trade_id: int) -> list[dict]:
        """Retrieves all flip records for a given trade_id, ordered by timestamp."""
        query = "SELECT * FROM trade_flips WHERE trade_id = ? ORDER BY timestamp ASC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (trade_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows] if rows else []
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving flips for trade {trade_id}: {e}")
            return []

    def delete_trade(self, trade_id: int) -> bool:
        """
        Deletes a trade and its associated flip records from the database.
        
        Args:
            trade_id: The ID of the trade to delete.
            
        Returns:
            True if the operation was successful, False otherwise.
        """
        try:
            cursor = self.conn.cursor()

            # Begin transaction
            self.conn.execute("BEGIN")

            # Get the wallet_id from the trade being deleted for statistics.
            cursor.execute("SELECT wallet_address FROM trades WHERE trade_id = ?", (trade_id,))
            trade_row = cursor.fetchone()
            if not trade_row:
                logger.warning(f"Attempted to delete non-existent trade_id: {trade_id}")
                self.conn.execute("ROLLBACK")
                return False
            wallet_address = trade_row[0]

            cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
            wallet_row = cursor.fetchone()
            wallet_id = wallet_row[0] if wallet_row else None
            
            if not wallet_id:
                logger.warning(f"Could not find wallet_id for wallet_address {wallet_address} when deleting trade {trade_id}")

            # Delete associated flip records first (foreign key constraint)
            cursor.execute("DELETE FROM trade_flips WHERE trade_id = ?", (trade_id,))
            logger.info(f"Deleted {cursor.rowcount} flip records for trade_id {trade_id}")
            
            # Now delete the trade
            cursor.execute("DELETE FROM trades WHERE trade_id = ?", (trade_id,))
            
            # If the trade was deleted and we have a wallet_id, update statistics
            if cursor.rowcount > 0 and wallet_id:
                # Ensure statistics row exists before updating
                from database.statistics_manager import StatisticsManager
                statistics_manager = StatisticsManager(self.conn)
                statistics_manager.ensure_statistics_entry(wallet_id)
                
                cursor.execute(
                    "UPDATE statistics SET total_trades_deleted = COALESCE(total_trades_deleted, 0) + 1 WHERE wallet_id = ?",
                    (wallet_id,)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated total_trades_deleted for wallet_id {wallet_id}")
                else:
                    logger.warning(f"Failed to update total_trades_deleted for wallet_id {wallet_id} - no rows affected")
            
            # Commit transaction
            self.conn.commit()
            logger.info(f"Successfully deleted trade_id {trade_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to delete trade_id {trade_id}. Error: {e}")
            self.conn.rollback()
            return False

    def get_active_trades(self) -> list[dict[str, any]]:
        """Fetches all active trades from the database."""
        trades = []
        try:
            # Set row_factory before creating cursor
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            # Handle both boolean True and integer 1 for is_active
            cursor.execute("SELECT * FROM trades WHERE is_active = 1 OR is_active = 'True' OR is_active = 'true'")
            rows = cursor.fetchall()
            # Convert rows to plain dicts
            trades = [dict(row) for row in rows]
            logger.debug(f"Found {len(trades)} active trades")
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch active trades: {e}", exc_info=True)
        finally:
            # Reset row_factory to default
            self.conn.row_factory = None
        return trades

    def get_trades_count_for_pair(self, trade_pair_id: int) -> int:
        """
        Returns the count of all trades (active and inactive) for a given trade_pair_id.
        Used to check if a trade pair can be safely removed from the Radbot Trading Pairs list.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades WHERE trade_pair_id = ?", (trade_pair_id,))
            result = cursor.fetchone()
            count = result[0] if result else 0
            logger.debug(f"Found {count} trades for trade_pair_id {trade_pair_id}")
            return count
        except sqlite3.Error as e:
            logger.error(f"Failed to count trades for trade_pair_id {trade_pair_id}: {e}")
            return 0

    def update_trade_after_swap(self, trade_id: int, new_trade_token_address: str, new_trade_amount: float):
        """Updates a trade's token and amount after a successful swap."""
        query = """
            UPDATE trades
            SET trade_token_address = ?, trade_amount = ?, updated_at = ?
            WHERE trade_id = ?
        """
        try:
            cursor = self.conn.cursor()
            current_timestamp = int(time.time())
            cursor.execute(query, (new_trade_token_address, str(new_trade_amount), current_timestamp, trade_id))
            self.conn.commit()
            if cursor.rowcount == 0:
                logger.warning(f"No trade found with ID {trade_id} to update after swap.")
                return False
            logger.info(f"Successfully updated trade {trade_id} after swap.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to update trade {trade_id} after swap: {e}", exc_info=True)
            self.conn.rollback()
            return False

    def add_trade(self, trade_data):
        """Adds a new trade to the database."""
        keys = ', '.join(trade_data.keys())
        placeholders = ', '.join(['?'] * len(trade_data))
        query = f"INSERT INTO trades ({keys}) VALUES ({placeholders})"
        
        try:
            cursor = self.conn.cursor()
            
            # Get wallet_id from wallet_address for statistics update
            wallet_address = trade_data.get('wallet_address')
            wallet_id = None
            if wallet_address:
                cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
                wallet_row = cursor.fetchone()
                wallet_id = wallet_row[0] if wallet_row else None
            
            if not wallet_id:
                logger.warning(f"Could not find wallet_id for wallet_address {wallet_address} when adding trade")
            
            # Add record for statistics data
            if wallet_id:
                # Ensure statistics row exists before updating
                from database.statistics_manager import StatisticsManager
                statistics_manager = StatisticsManager(self.conn)
                statistics_manager.ensure_statistics_entry(wallet_id)
                
                cursor.execute(
                    "UPDATE statistics SET total_trades_created = total_trades_created + 1 WHERE wallet_id = ?",
                    (wallet_id,)
                )
                
                if cursor.rowcount > 0:
                    logger.debug(f"Updated total_trades_created for wallet_id {wallet_id}")
                else:
                    logger.warning(f"Failed to update total_trades_created for wallet_id {wallet_id} - no rows affected")
                
                self.conn.commit()
            
            # Add trade
            cursor.execute(query, tuple(trade_data.values()))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database error while adding trade: {e}")
            self.conn.rollback()
            return None

    def get_all_active_trades_for_monitor(self):
        """Fetches all active trades from the database, for the global monitor service."""
        query = "SELECT * FROM trades WHERE is_active = 1"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            trades = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, trade)) for trade in trades]
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching all active trades for monitor: {e}")
            return []

    def get_trades_by_signal(self, signal: str) -> list[dict[str, any]]:
        """Fetches all active trades with a specific current_signal."""
        trades = []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE is_active = 1 AND current_signal = ?", (signal,))
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Convert rows to dictionaries
            trades = [dict(zip(column_names, row)) for row in rows]
            logger.debug(f"Found {len(trades)} trades with signal '{signal}'")
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch trades with signal '{signal}': {e}", exc_info=True)
        return trades

    def get_token_usd_price(self, token_address: str) -> Decimal:
        """Get the current USD price for a token."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT token_price_usd FROM tokens WHERE address = ?", (token_address,))
            result = cursor.fetchone()
            usd_price = Decimal(str(result[0])) if result and result[0] else Decimal('0')
            logger.debug(f"USD price lookup for {token_address}: {usd_price}")
            return usd_price
        except sqlite3.Error as e:
            logger.error(f"Failed to get USD price for token {token_address}: {e}", exc_info=True)
            return Decimal('0')

    def record_trade_history(self, flip_data: dict) -> None:
        """Record a trade flip in the trade_history table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trade_history (
                    trade_id_original, wallet_address, pair, side, amount_base, amount_quote,
                    price, usd_value, timestamp, status, strategy_name, transaction_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                flip_data['trade_id_original'],
                flip_data['wallet_address'],
                flip_data['pair'],
                flip_data['side'],
                flip_data['amount_base'],
                flip_data['amount_quote'],
                flip_data['price'],
                flip_data['usd_value'],
                flip_data['timestamp'],
                flip_data['status'],
                flip_data['strategy_name'],
                flip_data['transaction_hash'],
                flip_data['created_at']
            ))
            self.conn.commit()
            logger.debug(f"Recorded trade history entry for trade {flip_data['trade_id_original']}")
            
            # Update trade statistics after recording the flip
            self.update_trade_statistics_after_flip(flip_data['trade_id_original'], flip_data['usd_value'])
        except sqlite3.Error as e:
            logger.error(f"Failed to record trade history: {e}", exc_info=True)

    def update_trade_statistics_after_flip(self, trade_id: int, current_flip_usd: float) -> None:
        """Update trade statistics after recording a flip, with proper profit calculation."""
        try:
            cursor = self.conn.cursor()
            
            # Get current trade data
            cursor.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
            trade_data = cursor.fetchone()
            if not trade_data:
                logger.warning(f"No trade found with ID {trade_id} for statistics update.")
                return
            
            column_names = [description[0] for description in cursor.description]
            trade = dict(zip(column_names, trade_data))
            
            current_times_flipped = float(trade.get('times_flipped', 0))
            
            # Get wallet_id for statistics manager
            wallet_address = trade.get('wallet_address')
            wallet_id = None
            if wallet_address:
                cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
                wallet_row = cursor.fetchone()
                wallet_id = wallet_row[0] if wallet_row else None
            
            # Determine when to calculate profit based on accumulation token
            # If start_token == accumulation_token: Calculate at 1.0, 2.0, 3.0...
            # If start_token != accumulation_token: Calculate at 1.5, 2.5, 3.5...
            # CRITICAL: Use ADDRESS comparison, not SYMBOL (symbols can be NULL or duplicate)
            start_token_address = trade.get('start_token_address')
            accumulation_token_address = trade.get('accumulation_token_address')
            accumulation_token_symbol = trade.get('accumulation_token_symbol', 'Unknown')
            
            # Log token info for debugging
            logger.debug(f"Trade {trade_id}: start_token_address={start_token_address}, "
                        f"accumulation_token_address={accumulation_token_address}, "
                        f"accumulation_symbol={accumulation_token_symbol}")
            
            should_calculate_profit = False
            same_token = (start_token_address == accumulation_token_address)
            
            if same_token:
                # Same token: Calculate at integer flips (1.0, 2.0, 3.0...)
                should_calculate_profit = (current_times_flipped % 1.0 == 0.0 and current_times_flipped >= 1.0)
            else:
                # Different tokens: Calculate at half flips (1.5, 2.5, 3.5...)
                should_calculate_profit = (current_times_flipped % 1.0 == 0.5 and current_times_flipped >= 1.5)
            
            # Log when we skip profit calculation for opposite accumulation tokens
            if not should_calculate_profit and current_times_flipped >= 1.0:
                if not same_token and current_times_flipped % 1.0 == 0.0:
                    logger.debug(f"Trade {trade_id}: Skipping profit calculation at flip {current_times_flipped} "
                                f"(different accumulation token). Will calculate at flip {current_times_flipped + 0.5}")
            
            if should_calculate_profit:
                # Get the last two flips from trade_history to calculate profit
                # We need amount_base (Token) and amount_quote (XRD) to calculate profit correctly
                # depending on what we are accumulating
                cursor.execute("""
                    SELECT amount_quote, side, usd_value, amount_base FROM trade_history 
                    WHERE trade_id_original = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 2
                """, (trade_id,))
                recent_flips = cursor.fetchall()
                
                if len(recent_flips) >= 2:
                    # Extract amounts from the last two flips
                    current_flip = recent_flips[0]
                    penultimate_flip = recent_flips[1]
                    
                    current_quote = float(current_flip[0]) if current_flip[0] else 0.0
                    current_side = current_flip[1]
                    current_usd = float(current_flip[2]) if current_flip[2] else 0.0
                    current_base = float(current_flip[3]) if current_flip[3] else 0.0
                    
                    penultimate_quote = float(penultimate_flip[0]) if penultimate_flip[0] else 0.0
                    penultimate_side = penultimate_flip[1]
                    penultimate_usd = float(penultimate_flip[2]) if penultimate_flip[2] else 0.0
                    penultimate_base = float(penultimate_flip[3]) if penultimate_flip[3] else 0.0
                    
                    profit_amount = 0.0
                    
                    # Get trade pair to determine base/quote for proper profit calculation
                    trade_pair_id = trade.get('trade_pair_id')
                    cursor.execute("""
                        SELECT base_token, quote_token FROM trade_pairs 
                        WHERE trade_pair_id = ?
                    """, (trade_pair_id,))
                    pair_row = cursor.fetchone()
                    
                    if not pair_row:
                        logger.error(f"Trade {trade_id}: Could not find trade pair {trade_pair_id} for profit calculation")
                    else:
                        base_token_addr = pair_row[0]
                        quote_token_addr = pair_row[1]
                        
                        # Determine if accumulation token is base or quote
                        accumulation_is_base = (accumulation_token_address == base_token_addr)
                        accumulation_is_quote = (accumulation_token_address == quote_token_addr)
                        
                        logger.debug(f"Trade {trade_id}: Accumulation is BASE={accumulation_is_base}, QUOTE={accumulation_is_quote}")
                        logger.debug(f"Trade {trade_id}: Flip sides: penultimate={penultimate_side}, current={current_side}")
                        logger.debug(f"Trade {trade_id}: Amounts: penultimate_base={penultimate_base:.8f}, current_base={current_base:.8f}")
                        logger.debug(f"Trade {trade_id}: Amounts: penultimate_quote={penultimate_quote:.8f}, current_quote={current_quote:.8f}")
                        
                        # Calculate profit based on which token is being accumulated
                        if accumulation_is_base:
                            # Accumulating BASE token
                            # Profit = BASE received in current flip - BASE given in penultimate flip
                            if current_side == 'BUY':
                                # BUY means we received base token
                                profit_amount = current_base - penultimate_base
                            else:
                                # SELL means we gave base token - this is giving away accumulation token
                                # The previous flip must have been a BUY where we received base
                                profit_amount = penultimate_base - current_base
                            
                            logger.info(f"Trade {trade_id}: Profit in {accumulation_token_symbol} (BASE) = {profit_amount:.8f}")
                            
                        elif accumulation_is_quote:
                            # Accumulating QUOTE token (e.g., XRD)
                            # Profit = QUOTE received in current flip - QUOTE given in penultimate flip
                            if current_side == 'SELL':
                                # SELL means we received quote token
                                profit_amount = current_quote - penultimate_quote
                            else:
                                # BUY means we gave quote token - this is giving away accumulation token
                                # The previous flip must have been a SELL where we received quote
                                profit_amount = penultimate_quote - current_quote
                            
                            logger.info(f"Trade {trade_id}: Profit in {accumulation_token_symbol} (QUOTE) = {profit_amount:.8f}")
                        else:
                            logger.error(f"Trade {trade_id}: Accumulation token {accumulation_token_address} "
                                        f"doesn't match base {base_token_addr} or quote {quote_token_addr}")

                    # Determine if the cycle was profitable (allow small tolerance for float issues)
                    is_profitable = profit_amount > 0.00000001
                    
                    # Update profitable/unprofitable counts
                    profitable_flips = int(trade.get('profitable_flips', 0))
                    unprofitable_flips = int(trade.get('unprofitable_flips', 0))
                    
                    if is_profitable:
                        profitable_flips += 1
                    else:
                        unprofitable_flips += 1
                    
                    # Update total profit 
                    # Note: This sums up raw amounts. If mixing tokens, this total might be weird,
                    # but for a consistent strategy it sums the accumulation token amount.
                    current_total_profit = float(trade.get('total_profit', 0))
                    new_total_profit = current_total_profit + profit_amount
                    
                    # Update the trade record with new statistics
                    cursor.execute("""
                        UPDATE trades 
                        SET profitable_flips = ?,
                            unprofitable_flips = ?,
                            total_profit = ?
                        WHERE trade_id = ?
                    """, (profitable_flips, unprofitable_flips, new_total_profit, trade_id))
                    
                    # Calculate profit in USD and XRD for trade_history and wallet stats
                    # profit_amount is ALWAYS in accumulation token units
                    # We convert to XRD and USD using the token's prices
                    profit_usd = 0.0
                    profit_xrd = 0.0
                    
                    XRD_ADDRESS = "resource_rdx1tknxxxxxxxxxradaborxxxxxxxxxxx007685388597"
                    
                    token_price_xrd = 0.0
                    token_price_usd = 0.0
                    
                    if accumulation_token_address:
                        cursor.execute("SELECT token_price_xrd, token_price_usd FROM tokens WHERE address = ?", (accumulation_token_address,))
                        price_row = cursor.fetchone()
                        if price_row:
                            token_price_xrd = float(price_row[0]) if price_row[0] else 0.0
                            token_price_usd = float(price_row[1]) if price_row[1] else 0.0
                    
                    accumulation_is_xrd = (accumulation_token_address == XRD_ADDRESS)
                    
                    if accumulation_is_xrd:
                        profit_xrd = profit_amount
                        if token_price_usd > 0:
                            profit_usd = profit_amount * token_price_usd
                        else:
                            profit_usd = current_usd - penultimate_usd
                        logger.debug(f"Accumulating XRD: profit_xrd={profit_xrd:.8f}, profit_usd={profit_usd:.4f}")
                        
                    elif token_price_xrd > 0 and token_price_usd > 0:
                        profit_xrd = profit_amount * token_price_xrd
                        profit_usd = profit_amount * token_price_usd
                        logger.debug(f"Accumulating {accumulation_token_symbol}: {profit_amount:.8f} * {token_price_xrd} XRD = {profit_xrd:.8f} XRD")
                        
                    else:
                        profit_usd = current_usd - penultimate_usd
                        if quote_token_addr == XRD_ADDRESS and current_quote > 0:
                            xrd_price_usd = current_usd / current_quote if current_quote > 0 else 0.0
                            profit_xrd = profit_usd / xrd_price_usd if xrd_price_usd > 0 else 0.0
                        else:
                            profit_xrd = 0.0
                        logger.warning(f"Using fallback for stats - no prices for {accumulation_token_symbol}")
                    
                    # Update the most recent trade_history record with profit (token, USD, XRD)
                    profit_string = f"{profit_amount:.8f} {accumulation_token_symbol}"
                    
                    cursor.execute("""
                        UPDATE trade_history 
                        SET profit = ?, profit_usd = ?, profit_xrd = ?
                        WHERE history_id = (
                            SELECT history_id FROM trade_history 
                            WHERE trade_id_original = ? 
                            ORDER BY timestamp DESC 
                            LIMIT 1
                        )
                    """, (profit_string, profit_usd, profit_xrd, trade_id))
                    
                    self.conn.commit()
                    
                    logger.debug(f"Updated trade {trade_id} cycle statistics at flip {current_times_flipped}: "
                               f"profitable={profitable_flips}, unprofitable={unprofitable_flips}, "
                               f"cycle_profit={profit_amount:.8f} {accumulation_token_symbol}, "
                               f"profit_usd={profit_usd:.2f}, profit_xrd={profit_xrd:.4f}")
                    
                    # Update wallet-level statistics via StatisticsManager
                    if wallet_id:
                        from database.statistics_manager import StatisticsManager
                        from decimal import Decimal
                        
                        statistics_manager = StatisticsManager(self.conn)

                        statistics_manager.record_trade_flip(
                            wallet_id=wallet_id,
                            profit_loss_usd=Decimal(str(profit_usd)),
                            profit_loss_xrd=Decimal(str(profit_xrd)),
                            is_profitable=is_profitable
                        )
                        
                        logger.info(f"Recorded wallet statistics: profit_usd={profit_usd:.2f}, profit_xrd={profit_xrd:.4f}, profitable={is_profitable}")
                        
                        # Update daily statistics for charting
                        if quote_token_addr == XRD_ADDRESS:
                            volume_xrd = current_quote
                        elif token_price_xrd > 0:
                            volume_xrd = current_base * token_price_xrd
                        else:
                            volume_xrd = 0.0
                        volume_usd = current_usd
                        
                        self.update_daily_statistics(
                            wallet_address=wallet_address,
                            profit_loss_xrd=profit_xrd,
                            profit_loss_usd=profit_usd,
                            volume_xrd=volume_xrd,
                            volume_usd=volume_usd
                        )
                    
        except sqlite3.Error as e:
            logger.error(f"Failed to update trade statistics for trade {trade_id}: {e}", exc_info=True)
            self.conn.rollback()

    def update_daily_statistics(self, wallet_address: str, profit_loss_xrd: float, profit_loss_usd: float, 
                                volume_xrd: float, volume_usd: float) -> None:
        """Update daily statistics for charting. Upserts today's record and cleans up old data."""
        try:
            cursor = self.conn.cursor()
            
            # Get wallet_id
            cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
            wallet_row = cursor.fetchone()
            if not wallet_row:
                logger.warning(f"No wallet found for address {wallet_address}")
                return
            
            wallet_id = wallet_row[0]
            
            # Get today's date in YYYY-MM-DD format
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            current_timestamp = int(time.time())
            
            # Check if record exists for today
            cursor.execute("""
                SELECT profit_loss_xrd, profit_loss_usd, volume_xrd, volume_usd 
                FROM daily_statistics 
                WHERE wallet_id = ? AND date = ?
            """, (wallet_id, today))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record (add to cumulative values)
                new_profit_xrd = existing[0] + profit_loss_xrd
                new_profit_usd = existing[1] + profit_loss_usd
                new_volume_xrd = existing[2] + volume_xrd
                new_volume_usd = existing[3] + volume_usd
                
                cursor.execute("""
                    UPDATE daily_statistics 
                    SET profit_loss_xrd = ?,
                        profit_loss_usd = ?,
                        volume_xrd = ?,
                        volume_usd = ?,
                        updated_at = ?
                    WHERE wallet_id = ? AND date = ?
                """, (new_profit_xrd, new_profit_usd, new_volume_xrd, new_volume_usd, 
                      current_timestamp, wallet_id, today))
                
                logger.debug(f"Updated daily statistics for {today}: profit_xrd={new_profit_xrd:.4f}, volume_xrd={new_volume_xrd:.4f}")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO daily_statistics (
                        wallet_id, date, profit_loss_xrd, profit_loss_usd,
                        volume_xrd, volume_usd, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (wallet_id, today, profit_loss_xrd, profit_loss_usd,
                      volume_xrd, volume_usd, current_timestamp, current_timestamp))
                
                logger.debug(f"Created daily statistics for {today}: profit_xrd={profit_loss_xrd:.4f}, volume_xrd={volume_xrd:.4f}")
            
            # Clean up records older than 30 days
            cursor.execute("""
                DELETE FROM daily_statistics 
                WHERE wallet_id = ? 
                AND date < date('now', '-30 days')
            """, (wallet_id,))
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.debug(f"Cleaned up {deleted_count} old daily statistics records")
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Failed to update daily statistics: {e}", exc_info=True)
            self.conn.rollback()

    def update_trade_after_execution(self, trade_id: int, new_token_address: str, new_amount, amount_traded: Decimal, price_impact: Decimal) -> None:
        """Update trade record after successful execution - flip to new token, reset signal, and update basic statistics."""
        try:
            cursor = self.conn.cursor()
            current_timestamp = int(time.time())
            
            # Convert new_amount to Decimal if it's a string
            if isinstance(new_amount, str):
                new_amount = Decimal(new_amount)
            
            # Get current trade data including trade pair info and reserved amount
            cursor.execute("""
                SELECT t.times_flipped, t.trade_volume, t.trade_token_address, 
                       tp.base_token, tp.quote_token, t.start_token_address,
                       t.start_amount, t.is_compounding, t.accumulation_token_address,
                       t.reserved_amount, t.strategy_name
                FROM trades t
                JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                WHERE t.trade_id = ?
            """, (trade_id,))
            trade_data = cursor.fetchone()
            if not trade_data:
                logger.warning(f"No trade found with ID {trade_id} to update after execution.")
                return
            
            # Unpack trade data
            current_times_flipped = float(trade_data[0]) if trade_data[0] else 0.0
            current_volume = float(trade_data[1]) if trade_data[1] else 0.0
            old_token_address = trade_data[2]
            base_token = trade_data[3]
            quote_token = trade_data[4]
            start_token_address = trade_data[5]
            start_amount = float(trade_data[6]) if trade_data[6] else 0.0
            is_compounding = bool(trade_data[7])
            accumulation_token_address = trade_data[8]
            reserved_amount_str = trade_data[9] if trade_data[9] else "0"
            strategy_name = trade_data[10] if trade_data[10] else ""
            
            times_flipped = current_times_flipped + 0.5  # Each flip is 0.5
            
            # Get token manager for price lookups and symbol
            from database.tokens import TokenManager
            token_manager = TokenManager(self.conn)
            
            # Get quote token symbol from tokens table
            quote_token_info = token_manager.get_token_by_address(quote_token)
            quote_symbol = quote_token_info.get('symbol', 'XRD') if quote_token_info else 'XRD'
            
            # Calculate volume in XRD
            # For XRD pairs, quote_token is always XRD
            if quote_symbol.upper() == 'XRD':
                # Determine which token was sold
                if old_token_address == base_token:
                    # Sold base token → received XRD (new_amount is XRD)
                    volume_xrd = float(new_amount)
                elif old_token_address == quote_token:
                    # Sold XRD → received base token (amount_traded is XRD)
                    volume_xrd = float(amount_traded)
                else:
                    logger.warning(f"Unexpected token addresses in trade {trade_id}")
                    volume_xrd = 0.0
            else:
                # Non-XRD pair (e.g., xUSDC/xUSDT) - convert to XRD using token price
                # Get the price of the token that was sold
                old_token_info = token_manager.get_token_by_address(old_token_address)
                
                if old_token_info and old_token_info.get('token_price_xrd'):
                    old_token_price_xrd = float(old_token_info['token_price_xrd'])
                    # Volume in XRD = amount traded × price in XRD
                    volume_xrd = float(amount_traded) * old_token_price_xrd
                    logger.info(f"Non-XRD pair: Converted {amount_traded} {old_token_info.get('symbol')} "
                               f"@ {old_token_price_xrd:.6f} XRD = {volume_xrd:.4f} XRD")
                else:
                    logger.warning(f"Trade {trade_id}: No XRD price found for {old_token_address}, volume may be inaccurate")
                    volume_xrd = 0.0
            
            new_volume = current_volume + volume_xrd
            
            # Look up the symbol for the new token
            new_token_info = token_manager.get_token_by_address(new_token_address)
            new_token_symbol = new_token_info.get('symbol', 'Unknown') if new_token_info else 'Unknown'
            
            # Example 1: Cap amount for non-compounding trades when returning to start token
            # (This handles the case where accumulation token = start token)
            if not is_compounding and new_token_address == start_token_address:
                if accumulation_token_address == start_token_address:
                    if float(new_amount) > start_amount:
                        profit = float(new_amount) - start_amount
                        new_amount = Decimal(str(start_amount))
                        logger.info(f"Non-compounding trade capped: {new_amount} {new_token_symbol} (profit {profit:.6f} {new_token_symbol} retained in wallet)")
            
            # Kelly Criterion: Recover reserved amount if new token matches
            # For AI Strategy with Kelly sizing, the reserved amount stays in the same token
            # When flipping back to that token, add the reserved amount to the new position
            reserved_amount = Decimal(reserved_amount_str)
            new_reserved_amount = Decimal('0')
            
            if reserved_amount > 0 and 'ai' in strategy_name.lower():
                # Check if new token is the same as the token that had reserved amount
                # Reserved amount is always in the token we DIDN'T trade (old token)
                if new_token_address == old_token_address:
                    # Flipping back to the token with reserved amount - add it to position
                    new_amount = new_amount + reserved_amount
                    logger.info(f"Kelly Recovery: Added reserved {reserved_amount} {new_token_symbol} back to position")
                    logger.info(f"  New total position: {new_amount} {new_token_symbol}")
                    new_reserved_amount = Decimal('0')  # No more reserved
                else:
                    # Flipped to different token - reserved amount stays in old token (in wallet)
                    # Keep tracking it for when we flip back
                    new_reserved_amount = reserved_amount
                    logger.info(f"Kelly: Reserved {reserved_amount} remains in wallet as {old_token_address}")
            
            # Log BEFORE update to confirm parameters
            logger.info(f"=== TRADE FLIP UPDATE (Trade {trade_id}) ===")
            logger.info(f"  New token address: {new_token_address}")
            logger.info(f"  New token symbol: {new_token_symbol}")
            logger.info(f"  New amount: {new_amount}")
            logger.info(f"  Times flipped: {times_flipped}")
            logger.info(f"  Volume (XRD): +{volume_xrd:.4f} XRD (total: {new_volume:.4f} XRD)")
            
            # Update the trade record: flip trade_token to new position
            # accumulation_token stays the same (user's target token)
            # Note: current_signal is already set to 'hold' before transaction submission (race condition fix)
            # This update is redundant but provides a safety net
            cursor.execute("""
                UPDATE trades 
                SET trade_token_address = ?, 
                    trade_amount = ?, 
                    trade_token_symbol = ?,
                    current_signal = 'hold',
                    last_signal_updated_at = ?,
                    updated_at = ?,
                    times_flipped = ?,
                    trade_volume = ?,
                    reserved_amount = ?
                WHERE trade_id = ?
            """, (new_token_address, str(new_amount), new_token_symbol, current_timestamp, current_timestamp, 
                  times_flipped, new_volume, str(new_reserved_amount), trade_id))
            
            self.conn.commit()
            
            if cursor.rowcount == 0:
                logger.warning(f"No trade found with ID {trade_id} to update after execution.")
                return
            else:
                logger.info(f"Successfully updated {cursor.rowcount} trade record(s) for trade {trade_id}")
                
            # Verify the update worked - read back what's actually in the database
            cursor.execute("""
                SELECT trade_token_address, trade_token_symbol, trade_amount, current_signal 
                FROM trades WHERE trade_id = ?
            """, (trade_id,))
            result = cursor.fetchone()
            if result:
                logger.info(f"=== VERIFICATION: Database now shows ===")
                logger.info(f"  trade_token_address: {result[0]}")
                logger.info(f"  trade_token_symbol: {result[1]}")
                logger.info(f"  trade_amount: {result[2]}")
                logger.info(f"  current_signal: {result[3]}")
            else:
                logger.error(f"Could not verify trade {trade_id} update - trade not found")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to update trade {trade_id} after execution: {e}", exc_info=True)
            self.conn.rollback()

    def get_latest_price(self, pair: str) -> Optional[float]:
        """Get the latest price for a trading pair from price_history table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT close_price 
                FROM price_history 
                WHERE pair = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (pair,))
            
            result = cursor.fetchone()
            if result:
                return float(result[0])
            else:
                logger.warning(f"No price data found for pair '{pair}'")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get latest price for pair '{pair}': {e}", exc_info=True)
            return None

    def rollback_trade_execution(self, trade_id: int, original_trade_state: Dict[str, Any]) -> bool:
        """
        Rollback trade changes if transaction was rejected by the network.
        
        Note: We do NOT restore current_signal - it remains 'hold'. The trade monitor
        will re-evaluate the trade in the next cycle and set it back to 'execute' if
        the conditions are still met. This prevents race conditions while allowing
        automatic retry of failed trades.
        
        Args:
            trade_id (int): The trade ID to rollback
            original_trade_state (dict): The original trade state before execution
            
        Returns:
            bool: True if rollback successful, False otherwise
        """
        try:
            logger.info(f"Rolling back trade {trade_id} due to transaction rejection")
            logger.info(f"Signal will remain 'hold' - trade monitor will re-evaluate in next cycle")
            
            # Restore original trade state (but NOT the signal - see note above)
            query = """
                UPDATE trades 
                SET trade_token_address = ?, 
                    trade_amount = ?, 
                    times_flipped = ?, 
                    trade_volume = ?
                WHERE trade_id = ?
            """
            
            params = (
                original_trade_state.get('trade_token_address'),
                str(original_trade_state.get('trade_amount', '0')),
                original_trade_state.get('times_flipped', 0.0),
                str(original_trade_state.get('trade_volume', '0')),
                trade_id
            )
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            # Remove the last trade history entry for this trade
            delete_query = """
                DELETE FROM trade_history 
                WHERE trade_id_original = ? 
                AND history_id = (
                    SELECT MAX(history_id) 
                    FROM trade_history 
                    WHERE trade_id_original = ?
                )
            """
            cursor.execute(delete_query, (trade_id, trade_id))
            
            self.conn.commit()
            
            logger.info(f"Successfully rolled back trade {trade_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback trade {trade_id}: {e}", exc_info=True)
            self.conn.rollback()
            return False

    def get_trade_state_snapshot(self, trade_id: int) -> Dict[str, Any]:
        """
        Get current trade state for rollback purposes.
        
        Note: Does NOT include current_signal - signal is never rolled back
        to prevent race conditions. Trade monitor will re-evaluate instead.
        
        Args:
            trade_id (int): The trade ID to snapshot
            
        Returns:
            dict: Current trade state (without signal)
        """
        try:
            query = """
                SELECT trade_token_address, trade_amount, times_flipped, 
                       trade_volume
                FROM trades 
                WHERE trade_id = ?
            """
            
            cursor = self.conn.cursor()
            cursor.execute(query, (trade_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'trade_token_address': result[0],
                    'trade_amount': Decimal(str(result[1])) if result[1] else Decimal('0'),
                    'times_flipped': float(result[2]) if result[2] is not None else 0.0,
                    'trade_volume': Decimal(str(result[3])) if result[3] else Decimal('0')
                }
            else:
                logger.warning(f"No trade found with ID {trade_id} for snapshot")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get trade state snapshot for trade {trade_id}: {e}", exc_info=True)
            return {}

    def get_trade_history(self, wallet_address: str = None, start_timestamp: int = None, end_timestamp: int = None, limit: int = 1000) -> list:
        """
        Retrieve trade history records with optional filtering.
        
        Args:
            wallet_address (str, optional): Filter by wallet address
            start_timestamp (int, optional): Filter by start timestamp (Unix timestamp)
            end_timestamp (int, optional): Filter by end timestamp (Unix timestamp)
            limit (int): Maximum number of records to return (default: 1000)
            
        Returns:
            list: List of trade history records as dictionaries
        """
        try:
            query = """
                SELECT history_id, trade_id_original, wallet_address, pair, side, 
                       amount_base, amount_quote, price, usd_value, timestamp, 
                       status, strategy_name, transaction_hash, created_at, profit,
                       profit_usd, profit_xrd
                FROM trade_history
                WHERE 1=1
            """
            params = []
            
            # Add filters
            if wallet_address:
                query += " AND wallet_address = ?"
                params.append(wallet_address)
                
            if start_timestamp:
                query += " AND timestamp >= ?"
                params.append(start_timestamp)
                
            if end_timestamp:
                query += " AND timestamp <= ?"
                params.append(end_timestamp)
            
            # Order by timestamp descending (most recent first)
            query += " ORDER BY timestamp DESC"
            
            # Add limit
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            trade_history = []
            for row in results:
                trade_history.append({
                    'history_id': row[0],
                    'trade_id_original': row[1],
                    'wallet_address': row[2],
                    'pair': row[3],
                    'side': row[4],
                    'amount_base': row[5],
                    'amount_quote': row[6],
                    'price': row[7],
                    'usd_value': row[8],
                    'timestamp': row[9],
                    'status': row[10],
                    'strategy_name': row[11],
                    'transaction_hash': row[12],
                    'created_at': row[13],
                    'profit': row[14],  # Profit string like "5.234 XRD" or None
                    'profit_usd': row[15],  # USD profit/loss (float or None)
                    'profit_xrd': row[16]   # XRD profit/loss (float or None)
                })
            
            logger.debug(f"Retrieved {len(trade_history)} trade history records")
            return trade_history
            
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve trade history: {e}", exc_info=True)
            return []

    def get_trade_history_summary(self, wallet_address: str = None, start_timestamp: int = None, end_timestamp: int = None) -> Dict[str, Any]:
        """
        Get summary statistics for trade history.
        
        Args:
            wallet_address (str, optional): Filter by wallet address
            start_timestamp (int, optional): Filter by start timestamp
            end_timestamp (int, optional): Filter by end timestamp
            
        Returns:
            dict: Summary statistics including total trades, volume, profit/loss
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(usd_value) as total_volume,
                    COUNT(CASE WHEN side = 'BUY' THEN 1 END) as buy_trades,
                    COUNT(CASE WHEN side = 'SELL' THEN 1 END) as sell_trades,
                    AVG(usd_value) as avg_trade_size,
                    MIN(timestamp) as first_trade_time,
                    MAX(timestamp) as last_trade_time
                FROM trade_history
                WHERE 1=1
            """
            params = []
            
            if wallet_address:
                query += " AND wallet_address = ?"
                params.append(wallet_address)
                
            if start_timestamp:
                query += " AND timestamp >= ?"
                params.append(start_timestamp)
                
            if end_timestamp:
                query += " AND timestamp <= ?"
                params.append(end_timestamp)
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if result:
                return {
                    'total_trades': result[0] or 0,
                    'total_volume': result[1] or 0.0,
                    'buy_trades': result[2] or 0,
                    'sell_trades': result[3] or 0,
                    'avg_trade_size': result[4] or 0.0,
                    'first_trade_time': result[5],
                    'last_trade_time': result[6]
                }
            else:
                return {
                    'total_trades': 0,
                    'total_volume': 0.0,
                    'buy_trades': 0,
                    'sell_trades': 0,
                    'avg_trade_size': 0.0,
                    'first_trade_time': None,
                    'last_trade_time': None
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get trade history summary: {e}", exc_info=True)
            return {
                'total_trades': 0,
                'total_volume': 0.0,
                'buy_trades': 0,
                'sell_trades': 0,
                'avg_trade_size': 0.0,
                'first_trade_time': None,
                'last_trade_time': None
            }

    def reset_trade_signal_to_hold(self, trade_id: int) -> None:
        """Reset trade signal to 'hold' after failed transaction to prevent infinite retry."""
        try:
            cursor = self.conn.cursor()
            current_timestamp = int(time.time())
            
            cursor.execute("""
                UPDATE trades 
                SET current_signal = 'hold',
                    last_signal_updated_at = ?
                WHERE trade_id = ?
            """, (current_timestamp, trade_id))
            
            self.conn.commit()
            
            if cursor.rowcount == 0:
                logger.warning(f"No trade found with ID {trade_id} to reset signal.")
            else:
                logger.debug(f"Successfully reset trade {trade_id} signal to 'hold'")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to reset trade {trade_id} signal: {e}", exc_info=True)
            self.conn.rollback()
