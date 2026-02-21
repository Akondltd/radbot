import sqlite3
from typing import Optional, Dict, List
import logging
import threading
from datetime import datetime
from pathlib import Path

from .settings import SettingsManager
from .wallets import WalletManager
from .trade_pairs import TradePairManager
from .tokens import TokenManager
from .balance_manager import BalanceManager
from .trade_manager import TradeManager
from .statistics_manager import StatisticsManager
from .ai_strategy_manager import AIStrategyManager
from .pool_manager import PoolManager

logger = logging.getLogger(__name__)

from config.paths import DATABASE_PATH, ensure_dirs

# Database configuration
TOKENS_TABLE_NAME = "tokens"
TRADE_PAIRS_TABLE_NAME = "trade_pairs"
SELECTED_PAIRS_TABLE_NAME = "selected_pairs"
SETTINGS_TABLE_NAME = "settings"


class Database:
    _instances = {}

    def __new__(cls, db_path: Optional[str] = None):
        """Create or get an existing database instance."""
        # Determine the key for the _instances dictionary, ensuring it's a resolved Path object
        if db_path is None:
            key = DATABASE_PATH.resolve()
        elif isinstance(db_path, str):
            key = Path(db_path).resolve()
        elif isinstance(db_path, Path):
            key = db_path.resolve()
        else:
            logger.error(f"Database.__new__: Unexpected db_path type '{type(db_path)}'. Using default.")
            key = DATABASE_PATH.resolve()

        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._init_db_path_key = key  # Pass resolved key to __init__
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database connection."""
        # Determine the actual_db_path for this instance, ensuring it's a resolved Path object
        if hasattr(self, '_init_db_path_key'): # Use key from __new__ if available
            actual_db_path = self._init_db_path_key
            del self._init_db_path_key # Clean up temporary attribute
        elif db_path is None:
            actual_db_path = DATABASE_PATH.resolve()
        elif isinstance(db_path, str):
            actual_db_path = Path(db_path).resolve()
        elif isinstance(db_path, Path):
            actual_db_path = db_path.resolve()
        else:
            logger.error(f"Database.__init__: Unexpected db_path type '{type(db_path)}'. Using default.")
            actual_db_path = DATABASE_PATH.resolve()

        # Ensure lock is present on the instance. This is crucial because __init__ 
        # can be called multiple times on a singleton instance returned by __new__.
        if not hasattr(self, 'lock'):
            self.lock = threading.Lock()

        # Determine the actual_db_path for this instance, ensuring it's a resolved Path object
        # This logic is repeated from __new__ to ensure __init__ operates on the correct path context
        # if it's called independently or if _init_db_path_key was not used/cleaned up.
        if hasattr(self, '_init_db_path_key') and self._init_db_path_key is not None:
            actual_db_path = self._init_db_path_key
            # Optionally clean up: del self._init_db_path_key, but be careful if __init__ is called multiple times
        elif db_path is None:
            actual_db_path = DATABASE_PATH.resolve()
        elif isinstance(db_path, str):
            actual_db_path = Path(db_path).resolve()
        elif isinstance(db_path, Path):
            actual_db_path = db_path.resolve()
        else: # Fallback, should ideally not happen if __new__ is always used
            actual_db_path = DATABASE_PATH.resolve()
            logger.warning(f"Database.__init__: Unexpected db_path type '{type(db_path)}', falling back to resolved default.")

        # Standard singleton __init__ guard for connection: if already initialized for this path, return.
        if hasattr(self, '_db_path') and self._db_path == actual_db_path and hasattr(self, '_conn') and self._conn is not None:
            return
        
        self._db_path = actual_db_path # Store the resolved Path object
        
        # Connection initialization (lock is already ensured to exist)
        self._conn = None 
        self._cursor = None
        self._initialize_database()

        # Initialize manager instances
        self.settings_manager = SettingsManager(self._conn)
        self.wallet_manager = WalletManager(self._conn)
        self.trade_pair_manager = TradePairManager(self._conn)
        self.token_manager = TokenManager(self._conn)
        self.trade_manager = TradeManager(self._conn)
        self.statistics_manager = StatisticsManager(self._conn)
        self.ai_strategy_manager = AIStrategyManager(self._conn)
        self.pool_manager = PoolManager(self._conn)

    def _initialize_database(self):
        """Initialize the database tables."""
        try:
            ensure_dirs()
            self._conn = sqlite3.connect(self._db_path, timeout=10.0, check_same_thread=False) # Added timeout
            self._cursor = self._conn.cursor()

            # Create wallets table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_name TEXT NOT NULL,
                    wallet_address TEXT NOT NULL,
                    wallet_file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(wallet_address, wallet_file_path)
                )
            """)

            # Create settings table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    active_wallet_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    token_updater_last_run TEXT,
                    FOREIGN KEY (active_wallet_id) REFERENCES wallets(wallet_id)
                )
            """)

            # Create tokens table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    address TEXT PRIMARY KEY,
                    symbol TEXT,
                    name TEXT,
                    description TEXT,
                    icon_url TEXT,
                    info_url TEXT,
                    divisibility INTEGER,
                    token_price_xrd REAL,
                    token_price_usd REAL,
                    diff_24h REAL,
                    diff_24h_usd REAL,
                    diff_7_days REAL,
                    diff_7_days_usd REAL,
                    volume_24h REAL,
                    volume_7d REAL,
                    total_supply REAL,
                    circ_supply REAL,
                    tvl REAL,
                    type TEXT,
                    tags TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    order_index TEXT,
                    icon_local_path TEXT,
                    icon_last_checked_timestamp INTEGER DEFAULT 0,
                    UNIQUE(address)
                )
            """)

            # Create trade_pairs table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_pairs (
                    trade_pair_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_token TEXT NOT NULL,
                    quote_token TEXT NOT NULL,
                    price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(base_token, quote_token)
                )
            """)

            # Create selected_pairs table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS selected_pairs (
                    selected_pair_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_pair_id INTEGER NOT NULL,
                    wallet_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trade_pair_id) REFERENCES trade_pairs(trade_pair_id),
                    FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id),
                    UNIQUE(trade_pair_id, wallet_id)
                )
            """)

            # Create token_balances table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_balances (
                    balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    token_address TEXT NOT NULL,
                    balance TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id),
                    FOREIGN KEY (token_address) REFERENCES tokens(address),
                    UNIQUE(wallet_id, token_address)
                )
            """)
            
            # Create index for token_balances
            self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_balances_wallet_id ON token_balances (wallet_id)")

            # Create daily_statistics table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_statistics  (
                  stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  wallet_id INTEGER NOT NULL,
                  date TEXT NOT NULL,  -- 'YYYY-MM-DD'
                  profit_loss_xrd REAL DEFAULT 0.0,
                  profit_loss_usd REAL DEFAULT 0.0,
                  volume_xrd REAL DEFAULT 0.0,
                  volume_usd REAL DEFAULT 0.0,
                  created_at INTEGER NOT NULL,
                  updated_at INTEGER NOT NULL,
                  UNIQUE(wallet_id, date),
                  FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id)
                )
            """)

            # Create statistics table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL UNIQUE,
                    total_trades_created INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    win_rate_percentage REAL DEFAULT 0.0,
                    total_profit_loss_quote REAL DEFAULT 0.0,
                    average_profit_per_trade_quote REAL DEFAULT 0.0,
                    average_loss_per_trade_quote REAL DEFAULT 0.0,
                    profit_factor REAL DEFAULT 0.0,
                    max_drawdown_percentage REAL DEFAULT 0.0,
                    sharpe_ratio REAL,
                    longest_winning_streak INTEGER DEFAULT 0,
                    longest_losing_streak INTEGER DEFAULT 0,
                    last_calculated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    total_trades_deleted INTEGER DEFAULT 0,
                    total_profit REAL DEFAULT 0.0,
                    total_loss REAL DEFAULT 0.0,
                    total_profit_xrd REAL DEFAULT 0.0,
                    total_loss_xrd REAL DEFAULT 0.0,
                    FOREIGN KEY (wallet_id) REFERENCES wallets (wallet_id) ON DELETE CASCADE
                )
            """)

            # Create price_history table
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL DEFAULT 'RadixNetwork_Astrolescent',
                    pair TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL,
                    base_token_usd_price REAL,
                    quote_token_usd_price REAL,
                    user_friendly_price REAL,
                    base_token_symbol TEXT,
                    quote_token_symbol TEXT,
                    UNIQUE (exchange, pair, timestamp)
                )
            """)
            
            # Create indexes for price_history
            self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_pair_timestamp ON price_history (pair, timestamp DESC)")
            self._cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_exchange_pair_timestamp ON price_history (exchange, pair, timestamp DESC)")

            # Create ociswap_pools table (Legacy support to prevent crashes)
            self._cursor.execute("""
                CREATE TABLE IF NOT EXISTS ociswap_pools (
                    pool_address TEXT PRIMARY KEY,
                    token_a_address TEXT NOT NULL,
                    token_b_address TEXT NOT NULL,
                    liquidity_usd REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_a_address, token_b_address)
                )
            """)

            # Note: 'trades' and 'trade_history' tables are managed by TradeManager to ensure
            # schema consistency (TEXT fields for amounts) and migration handling.
            # We rely on TradeManager initialization to create them.
            
            # Create initial settings record if it doesn't exist
            self._cursor.execute("SELECT COUNT(*) FROM settings")
            count = self._cursor.fetchone()[0]
            if count == 0:
                self._cursor.execute("""
                    INSERT INTO settings (id) VALUES (1)
                """)

            self._conn.commit()
            logger.debug(f"Successfully initialized database at {self._db_path}")

        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            raise

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._cursor = None

    def __del__(self):
        """Ensure the connection is closed when the object is destroyed."""
        self.close()

    def get_settings_manager(self) -> SettingsManager:
        """Get the settings manager."""
        return self.settings_manager

    def get_wallet_manager(self) -> WalletManager:
        """Get the wallet manager."""
        return self.wallet_manager

    def get_trade_pair_manager(self) -> TradePairManager:
        """Get the trade pair manager."""
        return self.trade_pair_manager

    def get_token_manager(self) -> TokenManager:
        """Get the token manager."""
        return self.token_manager

    def get_balance_manager(self) -> 'BalanceManager':
        """Get the balance manager."""
        # Forward reference for BalanceManager if it causes circular import issues,
        # otherwise direct import is fine.
        # BalanceManager expects (wallet, db_path) for its __init__.
        # It manages its own database connection using the db_path.
        return BalanceManager(wallet=None, conn=self._conn) # Wallet will be set later by the caller

    def get_trade_manager(self) -> 'TradeManager':
        """Get the trade manager."""
        return self.trade_manager

    def get_statistics_manager(self) -> 'StatisticsManager':
        """Get the statistics manager."""
        return self.statistics_manager

    def get_ai_strategy_manager(self) -> 'AIStrategyManager':
        """Get the AI strategy manager."""
        return self.ai_strategy_manager

    def get_pool_manager(self) -> 'PoolManager':
        """Get the pool manager."""
        return self.pool_manager

    def get_trades_by_wallet_address(self, wallet_address):
        return self.trade_manager.get_trades_by_wallet_address(wallet_address)

    def get_active_trades(self):
        """Delegates to TradeManager to get all active trades for the monitor service."""
        return self.trade_manager.get_all_active_trades_for_monitor()

    def get_trade_history(self, wallet_address: str = None, start_timestamp: int = None, end_timestamp: int = None, limit: int = 1000):
        return self.trade_manager.get_trade_history(wallet_address, start_timestamp, end_timestamp, limit)

    def get_trade_history_summary(self, wallet_address: str = None, start_timestamp: int = None, end_timestamp: int = None):
        return self.trade_manager.get_trade_history_summary(wallet_address, start_timestamp, end_timestamp)

    def get_trade_pair_by_id(self, trade_pair_id):
        return self.trade_pair_manager.get_trade_pair_by_id(trade_pair_id)

    def get_daily_statistics(self, wallet_address: str, days: int = 30) -> List[Dict]:
        """
        Get daily statistics for charting (profit/loss and volume).
        Returns up to 'days' most recent records for the wallet.
        """
        try:
            cursor = self._conn.cursor()
            
            # Get wallet_id
            cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
            wallet_row = cursor.fetchone()
            if not wallet_row:
                logger.warning(f"No wallet found for address {wallet_address}")
                return []
            
            wallet_id = wallet_row[0]
            
            # Fetch daily statistics
            cursor.execute("""
                SELECT date, profit_loss_xrd, profit_loss_usd, volume_xrd, volume_usd
                FROM daily_statistics
                WHERE wallet_id = ?
                ORDER BY date DESC
                LIMIT ?
            """, (wallet_id, days))
            
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append({
                    'date': row[0],
                    'profit_loss_xrd': row[1],
                    'profit_loss_usd': row[2],
                    'volume_xrd': row[3],
                    'volume_usd': row[4]
                })
            
            logger.debug(f"Retrieved {len(results)} daily statistics records for wallet {wallet_address}")
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get daily statistics: {e}", exc_info=True)
            return []
