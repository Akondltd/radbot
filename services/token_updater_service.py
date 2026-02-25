"""
Token Updater Service

Fetches the latest token list from Astrolescent API and updates the local database.
Runs once daily to keep token information current (prices, volumes, metadata).
"""

import logging
import time
import threading
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from PySide6.QtCore import QTimer, QThreadPool
from services.qt_base_service import QtBaseService, Worker
from config.database_config import get_db_connection
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)

ASTROLESCENT_TOKENS_URL = "https://api.astrolescent.com/partner/akond/tokens"


class QtTokenUpdaterService(QtBaseService):
    """Qt-based service to periodically fetch and update token information from Astrolescent."""
    
    def __init__(self, interval_ms=86400000):  # Default to 24 hours
        """
        Initialize the token updater service.
        
        Args:
            interval_ms: Milliseconds between updates (default 24 hours = 86400000ms)
        """
        super().__init__('qt_token_updater')
        self._work_lock = threading.Lock()  # Prevent concurrent token DB writes
        self.timer = QTimer()
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.trigger_run)
        self.days_since_pair_update = 0  # Counter for 7-day pair refresh
        self.last_run_timestamp = self._get_last_run_timestamp()
    
    def start(self):
        """Starts the service timer."""
        self.logger.info(f"Starting Qt Token Updater Service. Run interval: {self.timer.interval() / 1000}s")
        
        # Check if we need to run (only if >24 hours since last run)
        if self._should_run_update():
            self.logger.info("Token update needed - scheduling initial run in 60 seconds")
            QTimer.singleShot(60 * 1000, self.trigger_run)
        else:
            self.logger.info(f"Token update not needed - last run: {self.last_run_timestamp}")
        
        # Start timer for periodic checks
        self.timer.start()
    
    def stop(self):
        """Stops the service timer."""
        self.logger.info("Stopping Qt Token Updater Service.")
        self.timer.stop()
    
    def trigger_run(self):
        """Creates a worker to perform the token update on a background thread."""
        # Double-check if update is needed before running
        if not self._should_run_update():
            self.logger.info(f"Skipping token update - last run was recent: {self.last_run_timestamp}")
            return
        
        self.logger.info("Triggering token update worker.")
        worker = Worker(self._do_work)
        QThreadPool.globalInstance().start(worker)
    
    def force_run(self):
        """Force a token update regardless of last run time. Used when new tokens are discovered."""
        if self._work_lock.locked():
            self.logger.info("Token update already in progress — skipping force_run to avoid DB corruption.")
            return
        self.logger.info("Force triggering token update worker (new tokens detected).")
        worker = Worker(self._do_work)
        QThreadPool.globalInstance().start(worker)
    
    def _do_work(self, **kwargs):
        """The main logic for token updating, executed by the worker."""
        if not self._work_lock.acquire(blocking=False):
            self.logger.warning("Token update already running — skipping to avoid DB corruption.")
            return
        self.logger.info("Token update worker started.")
        start_time = time.time()
        try:
            # Fetch tokens from API
            tokens = self._fetch_tokens_from_api()
            
            if not tokens:
                self.logger.warning("No tokens received from Astrolescent API")
                return
            
            self.logger.info(f"Fetched {len(tokens)} tokens from Astrolescent")
            
            # Update database
            updated_count = self._update_tokens_in_database(tokens)
            
            # Increment day counter
            self.days_since_pair_update += 1
            
            # Every 7 days, refresh the auto-suggested trade pairs
            if self.days_since_pair_update >= 7:
                self.logger.info("7 days elapsed - refreshing auto-suggested trade pairs...")
                self._refresh_auto_suggested_pairs()
                self.days_since_pair_update = 0  # Reset counter
            
            end_time = time.time()
            self.logger.info(f"Token update worker finished successfully. {updated_count}/{len(tokens)} tokens updated. Duration: {end_time - start_time:.2f} seconds.")
            
            # Save timestamp after successful update
            self._save_last_run_timestamp()
            
        except Exception as e:
            self.logger.error(f"Error in token update worker: {e}", exc_info=True)
        finally:
            self._work_lock.release()
    
    def _fetch_tokens_from_api(self) -> List[Dict[str, Any]]:
        """
        Fetch token list from Astrolescent API.
        
        Returns:
            List of token dictionaries
        """
        try:
            self.logger.debug(f"Fetching tokens from {ASTROLESCENT_TOKENS_URL}")
            
            api_tracker.record('astrolescent')
            response = requests.get(ASTROLESCENT_TOKENS_URL, timeout=30)
            response.raise_for_status()
            
            tokens = response.json()
            
            if not isinstance(tokens, list):
                self.logger.error(f"Unexpected API response format: expected list, got {type(tokens)}")
                return []
            
            self.logger.debug(f"Successfully fetched {len(tokens)} tokens from API")
            return tokens
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch tokens from Astrolescent API: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing Astrolescent API response: {e}", exc_info=True)
            return []
    
    def _update_tokens_in_database(self, tokens: List[Dict[str, Any]]) -> int:
        """
        Update tokens in the database using TokenManager.
        
        Args:
            tokens: List of token dictionaries from API
            
        Returns:
            Number of tokens successfully updated
        """
        updated_count = 0
        conn = None
        
        try:
            # Get database connection
            conn = get_db_connection()
            
            # Import here to avoid circular imports
            from database.tokens import TokenManager
            token_manager = TokenManager(conn)
            
            for token in tokens:
                try:
                    # Astrolescent API returns camelCase fields, need conversion
                    # Ensure we have the required address field
                    if not token.get('address'):
                        self.logger.warning(f"Skipping token without address: {token.get('symbol', 'UNKNOWN')}")
                        continue
                    
                    # Icon downloading is handled by qt_icon_cache_service.
                    # This service only updates token metadata (prices, volumes, etc.).
                    # The icon cache service will pick up any token with icon_url but no icon_local_path.
                    
                    # Use Astrolescent-specific method that handles camelCase → snake_case conversion
                    success = token_manager.insert_or_update_token_from_astrolescent(token)
                    
                    if success:
                        updated_count += 1
                    else:
                        self.logger.warning(f"Failed to update token: {token.get('address')} ({token.get('symbol')})")
                        
                except Exception as e:
                    self.logger.error(f"Error updating token {token.get('address', 'UNKNOWN')}: {e}")
                    continue
            
            return updated_count
            
        finally:
            if conn:
                conn.close()
    
    def _refresh_auto_suggested_pairs(self):
        """
        Refresh auto-suggested trade pairs based on high-volume tokens.
        Creates simple Token/XRD pairs for tokens meeting minimum volume threshold.
        """
        conn = None
        try:
            from config.config_loader import config
            from database.trade_pairs import TradePairManager
            
            # Get minimum volume threshold from config
            min_volume_7d = config.min_volume_7d
            self.logger.info(f"Refreshing pairs for tokens with volume_7d >= {min_volume_7d} XRD")
            
            # Get database connection
            conn = get_db_connection()
            trade_pair_manager = TradePairManager(conn)
            
            # Get XRD address (standard Radix XRD)
            XRD_ADDRESS = "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd"
            
            # Query high-volume tokens (excluding XRD itself)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT address, symbol, volume_7d 
                FROM tokens 
                WHERE volume_7d >= ? 
                AND address != ?
                AND volume_7d IS NOT NULL
                ORDER BY volume_7d DESC""",
                (min_volume_7d, XRD_ADDRESS)
            )
            
            high_volume_tokens = cursor.fetchall()
            cursor.close()
            
            self.logger.info(f"Found {len(high_volume_tokens)} tokens with volume >= {min_volume_7d} XRD")
            
            # First, cleanup old auto-suggested pairs that no longer meet threshold
            removed_count = trade_pair_manager.cleanup_auto_suggested_pairs(min_volume_7d)
            
            # Add one pair per token: TOKEN/XRD (pool lookup will check both directions)
            pairs_added = 0
            for token_address, token_symbol, volume_7d in high_volume_tokens:
                try:
                    # Add TOKEN/XRD pair (base=token, quote=XRD)
                    success = trade_pair_manager.add_auto_suggested_pair(
                        base_token=token_address,
                        quote_token=XRD_ADDRESS,
                        volume_7d_usd=float(volume_7d)  # Store XRD volume
                    )
                    
                    if success:
                        pairs_added += 1
                    
                except Exception as e:
                    self.logger.error(f"Error adding auto pair for {token_symbol}: {e}")
                    continue
            
            self.logger.info(f"Auto-suggested pairs refresh complete: {pairs_added} tokens added, {removed_count} old pairs removed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing auto-suggested pairs: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()
    
    def _get_last_run_timestamp(self) -> datetime:
        """
        Get the last run timestamp from the database settings table.
        
        Returns:
            Last run datetime, or None if never run
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # First ensure the column exists
            cursor.execute("PRAGMA table_info(settings)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'token_updater_last_run' not in columns:
                cursor.execute("ALTER TABLE settings ADD COLUMN token_updater_last_run TEXT")
                conn.commit()
                self.logger.info("Added token_updater_last_run column to settings table")
            
            cursor.execute("SELECT token_updater_last_run FROM settings WHERE id = 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                return datetime.fromisoformat(result[0])
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not get last run timestamp: {e}")
            return None
    
    def _save_last_run_timestamp(self):
        """Save the current timestamp as the last run time in settings table."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Ensure settings row exists
            cursor.execute("SELECT id FROM settings WHERE id = 1")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (id) VALUES (1)")
            
            # Update the timestamp
            cursor.execute(
                "UPDATE settings SET token_updater_last_run = ? WHERE id = 1",
                (now,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            self.last_run_timestamp = datetime.now()
            self.logger.info(f"Saved last run timestamp: {now}")
            
        except Exception as e:
            self.logger.error(f"Could not save last run timestamp: {e}")
    
    def _should_run_update(self) -> bool:
        """
        Check if token update should run based on last run time.
        
        Returns:
            True if update should run (>24 hours since last run or never run)
        """
        if self.last_run_timestamp is None:
            self.logger.info("No previous run found - update needed")
            return True
        
        time_since_last_run = datetime.now() - self.last_run_timestamp
        hours_since_last_run = time_since_last_run.total_seconds() / 3600
        
        if hours_since_last_run >= 24:
            self.logger.info(f"Update needed - {hours_since_last_run:.1f} hours since last run")
            return True
        else:
            self.logger.info(f"Update not needed - only {hours_since_last_run:.1f} hours since last run")
            return False
