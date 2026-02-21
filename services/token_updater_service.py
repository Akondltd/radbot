"""
Token Updater Service

Fetches the latest token list from Astrolescent API and updates the local database.
Runs once daily to keep token information current (prices, volumes, metadata).
"""

import logging
import time
import threading
import requests
import shutil
import os
import io
from typing import List, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from PySide6.QtCore import QTimer, QThreadPool, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage
from services.qt_base_service import QtBaseService, Worker
from config.database_config import get_db_connection
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)

ASTROLESCENT_TOKENS_URL = "https://api.astrolescent.com/partner/akond/tokens"

# Security: Maximum icon download size (500KB should be plenty for icons)
# Prevents resource exhaustion attacks from huge image files
MAX_ICON_DOWNLOAD_SIZE_BYTES = 500 * 1024

# Security: Download timeout (seconds)
# Prevents hanging on slow/malicious servers
ICON_DOWNLOAD_TIMEOUT = 10


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
    
    @staticmethod
    def _sanitize_and_cache_icon(icon_url: str, token_address: str, order_index: int) -> str:
        """
        Download, sanitize, and cache a token icon from an untrusted URL.
        
        Security approach: "Hybrid Qt+PIL"
        1. Download image data (with size/timeout limits)
        2. Load with Qt (QImage) - Handles SVG, PNG, etc. robustly
        3. Transfer to PIL for standardizing (Resize to 128px, Round, PNG)
        4. Save as clean PNG to local cache
        
        Args:
            icon_url: URL to download icon from (can be any domain)
            token_address: Token address for cache filename
            order_index: Token order index for cache filename
            
        Returns:
            Path to sanitized local icon file, or None if download/sanitization failed
        """
        if not icon_url or not isinstance(icon_url, str):
            return None
        
        try:
            # Security: Only allow HTTPS to prevent MITM
            parsed = urlparse(icon_url)
            if parsed.scheme != 'https':
                logger.warning(f"Rejecting non-HTTPS icon URL: {icon_url}")
                return None
            
            # Download with size and timeout limits
            logger.debug(f"Downloading icon from: {icon_url}")
            api_tracker.record('icon_cdn')
            response = requests.get(
                icon_url,
                timeout=ICON_DOWNLOAD_TIMEOUT,
                stream=True  # Stream to check size before loading all
            )
            response.raise_for_status()
            
            # Security: Check content length before downloading
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > MAX_ICON_DOWNLOAD_SIZE_BYTES:
                logger.warning(f"Icon too large ({content_length} bytes): {icon_url}")
                return None
            
            # Download data to memory
            image_data = b""
            for chunk in response.iter_content(chunk_size=8192):
                image_data += chunk
                if len(image_data) > MAX_ICON_DOWNLOAD_SIZE_BYTES:
                    logger.warning(f"Icon download exceeded size limit: {icon_url}")
                    return None
            
            # Step 1: Load Image (Hybrid Qt/PIL approach)
            # Try Qt first (Handles SVG robustly)
            qimage = QImage()
            qt_loaded = qimage.loadFromData(QByteArray(image_data))
            
            img = None
            
            if qt_loaded:
                # Convert QImage to PIL via PNG buffer
                buffer = QBuffer()
                buffer.open(QIODevice.ReadWrite)
                qimage.save(buffer, "PNG")
                img = Image.open(io.BytesIO(buffer.data().data()))
            else:
                # Fallback: Try PIL directly (Handles WEBP if Qt plugin missing)
                try:
                    img = Image.open(io.BytesIO(image_data))
                    logger.debug(f"Qt failed to load, loaded with PIL (likely WEBP): {icon_url}")
                except Exception:
                    logger.warning(f"Failed to load image with both Qt and PIL from: {icon_url}")
                    return None

            # Step 2: Process with PIL
            try:
                # Convert to RGBA to support transparency
                # Note: .convert() returns a NEW image object
                img_rgba = img.convert("RGBA")
                img.close()  # Close original image from Qt buffer
                
                # Resize if larger than 128x128
                if img_rgba.width > 128 or img_rgba.height > 128:
                    img_rgba.thumbnail((128, 128), Image.Resampling.LANCZOS)
                
                # Create a circular mask for rounding
                size = (img_rgba.width, img_rgba.height)
                mask = Image.new('L', size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + size, fill=255)
                
                # Apply the mask
                output = ImageOps.fit(img_rgba, mask.size, centering=(0.5, 0.5))
                output.putalpha(mask)
                
                # Prepare cache directory
                cache_dir = Path("images/icons")
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                # Define final filename (ALWAYS PNG)
                cache_filename = f"{order_index}.png"
                cache_path = cache_dir / cache_filename
                
                # Clean up any existing files with different extensions for this ID
                for ext in ['.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']:
                    old_file = cache_dir / f"{order_index}{ext}"
                    if old_file.exists():
                        try:
                            old_file.unlink()
                            logger.info(f"Removed old duplicate icon: {old_file}")
                        except OSError:
                            pass

                # Save processed image
                output.save(cache_path, "PNG", optimize=True)
                
                # Clean up PIL images
                output.close()
                mask.close()
                img_rgba.close()
                
                logger.info(f"Sanitized and cached icon: {cache_path}")
                return str(cache_path)

            except (IOError, SyntaxError, Exception) as e:
                logger.warning(f"PIL failed to process image from {icon_url}: {e}")
                return None
            
        except requests.RequestException as e:
            logger.warning(f"Network error downloading icon from {icon_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sanitizing icon from {icon_url}: {e}", exc_info=True)
            return None
    
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
                    
                    # SECURITY: Download and sanitize icon from untrusted URL
                    # Only download if we don't already have it cached
                    icon_url = token.get('iconUrl')
                    order_index = token.get('orderIndex')
                    
                    if icon_url and order_index is not None:
                        # Check if already cached
                        expected_cache_path = f"images/icons/{order_index}.png"
                        import os
                        
                        # Always attempt to sanitize and cache the icon
                        # This ensures database always has the correct path, and allows for logo updates
                        self.logger.debug(f"Processing icon for {token.get('symbol', 'UNKNOWN')} (orderIndex={order_index})")
                        sanitized_path = self._sanitize_and_cache_icon(
                            icon_url,
                            token.get('address'),
                            order_index
                        )
                        
                        if sanitized_path:
                            self.logger.debug(f"Icon sanitized and cached: {sanitized_path}")
                            # Inject the local path into the token dict so TokenManager can save it
                            token['iconLocalPath'] = sanitized_path
                        else:
                            # Fallback: if file exists from previous run, use it
                            if os.path.exists(expected_cache_path):
                                self.logger.debug(f"Using existing cached icon for {token.get('symbol', 'UNKNOWN')}")
                                token['iconLocalPath'] = expected_cache_path
                            else:
                                self.logger.warning(
                                    f"Failed to sanitize icon for {token.get('symbol', 'UNKNOWN')} "
                                    f"from {icon_url}. Will use default icon."
                                )
                    
                    # Use Astrolescent-specific method that handles camelCase → snake_case conversion
                    success = token_manager.insert_or_update_token_from_astrolescent(token)
                    
                    if success:
                        updated_count += 1
                        # Stamp icon_last_checked_timestamp if we cached an icon
                        if token.get('iconLocalPath'):
                            try:
                                import time as _time
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE tokens SET icon_last_checked_timestamp = ? WHERE address = ?",
                                    (int(_time.time()), token.get('address'))
                                )
                                conn.commit()
                            except Exception as ts_err:
                                self.logger.debug(f"Could not stamp icon timestamp: {ts_err}")
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
