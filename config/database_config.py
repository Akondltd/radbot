import os
import sqlite3
from config.paths import DATABASE_PATH, DATA_DIR, PACKAGE_ROOT as PROJECT_ROOT, ensure_dirs

# Database configuration
DATABASE_NAME = 'radbot.db'

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    ensure_dirs()
    conn = sqlite3.connect(str(DATABASE_PATH))
    # Improve performance and handling of text data
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.text_factory = str
    return conn

# Table configuration
TOKENS_TABLE_NAME = 'tokens'
TOKENS_TABLE_COLUMNS = [
    'address TEXT PRIMARY KEY',
    'symbol TEXT',
    'name TEXT',
    'description TEXT',
    'icon_url TEXT',
    'info_url TEXT',
    'divisibility INTEGER',
    'token_price_xrd REAL',
    'token_price_usd REAL',
    'diff_24h REAL',
    'diff_24h_usd REAL',
    'diff_7d REAL',
    'diff_7d_usd REAL',
    'volume_24h REAL',
    'volume_7d REAL',
    'total_supply REAL',
    'circ_supply REAL',
    'tvl REAL',
    'type TEXT',
    'tags TEXT',  # Store as JSON string
    'created_at TEXT',
    'updated_at TEXT',
    'order_index INTEGER',
    'icon_local_path TEXT'
]

# Trade Pairs table configuration
TRADE_PAIRS_TABLE_NAME = 'trade_pairs'
TRADE_PAIRS_TABLE_COLUMNS = [
    'id INTEGER PRIMARY KEY AUTOINCREMENT',
    'base_token TEXT NOT NULL',  # Added NOT NULL for robustness
    'quote_token TEXT NOT NULL', # Added NOT NULL for robustness
    'price_impact REAL',
    'last_checked TIMESTAMP',
    'is_selected BOOLEAN DEFAULT 0', # We'll address this later
    'order_index INTEGER DEFAULT 0',
    'source TEXT DEFAULT "user"',  # "auto" for system-suggested, "user" for manually added
    'volume_7d_usd REAL',  # Track 7-day volume for auto-cleanup
    'UNIQUE (base_token, quote_token)' # <-- This is the key addition
]

# Selected Trade Pairs table configuration
SELECTED_PAIRS_TABLE_NAME = 'selected_pairs'
SELECTED_PAIRS_TABLE_COLUMNS = [
    'selection_id INTEGER PRIMARY KEY AUTOINCREMENT',
    'wallet_id INTEGER NOT NULL',
    'trade_pair_id INTEGER NOT NULL',
    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'FOREIGN KEY (wallet_id) REFERENCES wallets (wallet_id) ON DELETE CASCADE',
    'FOREIGN KEY (trade_pair_id) REFERENCES trade_pairs (id) ON DELETE CASCADE',
    'UNIQUE (wallet_id, trade_pair_id)'
]

# Trade Opportunities table configuration
TRADE_OPPORTUNITIES_TABLE_NAME = 'trade_opportunities'
TRADE_OPPORTUNITIES_TABLE_COLUMNS = [
    'opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT',
    'trade_pair_id INTEGER NOT NULL',
    'base_price REAL NOT NULL',
    'quote_price REAL NOT NULL',
    'profit_percentage REAL NOT NULL',
    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'FOREIGN KEY (trade_pair_id) REFERENCES trade_pairs (id) ON DELETE CASCADE'
]

# Settings table configuration
SETTINGS_TABLE_NAME = 'settings'
SETTINGS_TABLE_COLUMNS = [
    'id INTEGER PRIMARY KEY AUTOINCREMENT',
    'active_wallet_id INTEGER',
    'app_version TEXT',
    'last_update_version TEXT',
    'last_update_time TIMESTAMP',
    'update_status TEXT',  # pending/updated/failed
    'last_update_error TEXT',
    'ui_theme TEXT DEFAULT "fusion"',
    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
]