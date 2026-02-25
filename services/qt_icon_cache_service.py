import time
import io
import requests
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from PySide6.QtCore import QTimer, QThreadPool, QBuffer, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtCore import QByteArray

from config.database_config import get_db_connection
from services.qt_base_service import QtBaseService, Worker
from utils.api_tracker import api_tracker

# No recheck — icons are fetched once and kept permanently
from config.paths import PACKAGE_ROOT, USER_DATA_DIR
DEFAULT_ICON_PATH = PACKAGE_ROOT / 'images' / 'default_token_icon.png'
PLACEHOLDER_DB_PATH = 'images/default_token_icon.png'

class QtIconCacheService(QtBaseService):
    """
    A robust service to cache token icons using Qt's threading model.
    - Validates that downloaded files are actual images.
    - Assigns a placeholder for failed/invalid icons.
    - Periodically re-checks icons for updates with intelligent backoff.
    """

    def __init__(self, interval_ms=3600000):  # Default to 1 hour
        super().__init__('qt_icon_cacher')
        self.icon_cache_dir = USER_DATA_DIR / 'images' / 'icons'
        self.icon_cache_dir.mkdir(parents=True, exist_ok=True)
        self.timer = QTimer()
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.trigger_run)

    def start(self):
        self.logger.info(f"Starting Qt Icon Cache Service. Run interval: {self.timer.interval() / 1000}s")
        self.logger.info(f"Icon cache directory: {self.icon_cache_dir}")
        QTimer.singleShot(10 * 1000, self.trigger_run)  # Initial 10s delay
        self.timer.start()

    def stop(self):
        self.logger.info("Stopping Qt Icon Cache Service.")
        self.timer.stop()

    def trigger_run(self):
        self.logger.info("Triggering icon cache worker.")
        worker = Worker(self._do_work)
        QThreadPool.globalInstance().start(worker)

    def _do_work(self, **kwargs):
        self.logger.info("Icon cache worker started.")
        try:
            # First, set default icons for tokens with empty icon_url
            self._set_default_icons_for_empty_urls()
            
            # Then process tokens with actual icon URLs
            tokens_to_check = self._get_tokens_to_check()
            if not tokens_to_check:
                self.logger.info("No icons need checking at this time. Worker run complete.")
                return

            self.logger.info(f"Found {len(tokens_to_check)} icons to process.")
            
            chunk_size = 50
            for i in range(0, len(tokens_to_check), chunk_size):
                chunk = tokens_to_check[i:i + chunk_size]
                self.logger.info(f"Processing chunk {i//chunk_size + 1}/{(len(tokens_to_check) + chunk_size - 1)//chunk_size}...")
                
                db_updates = []
                for token in chunk:
                    local_path = self._fetch_and_validate_one_icon(token)
                    db_updates.append((local_path, token['address']))

                if db_updates:
                    self._update_database_batch(db_updates)

            self.logger.info("Icon caching worker finished successfully.")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred in the icon cache worker: {e}", exc_info=True)

    def _set_default_icons_for_empty_urls(self):
        """Set default icon path for tokens with empty icon_url."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            now = int(time.time())
            
            # Update tokens with empty icon_url to use default icon
            cursor.execute(
                """UPDATE tokens 
                   SET icon_local_path = ?, icon_last_checked_timestamp = ? 
                   WHERE (icon_url IS NULL OR icon_url = '') 
                   AND (icon_local_path IS NULL OR icon_local_path = '')""",
                (PLACEHOLDER_DB_PATH, now)
            )
            
            updated_count = cursor.rowcount
            if updated_count > 0:
                conn.commit()
                self.logger.info(f"Set default icon for {updated_count} tokens with empty icon_url")
            
        except Exception as e:
            self.logger.error(f"Failed to set default icons for empty URLs: {e}", exc_info=True)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def _update_database_batch(self, db_updates):
        """Updates the database with a batch of icon paths."""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            now = int(time.time())
            
            update_tuples = [(path, now, address) for path, address in db_updates]
            
            cursor.executemany(
                "UPDATE tokens SET icon_local_path = ?, icon_last_checked_timestamp = ? WHERE address = ?",
                update_tuples
            )
            conn.commit()
            self.logger.info(f"Successfully updated {cursor.rowcount} token icon records in the database.")
        except Exception as db_e:
            self.logger.error(f"Database batch update failed: {db_e}", exc_info=True)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def _load_image_with_qt_fallback(self, image_data):
        """
        Load image data using Qt (handles SVG natively) with PIL fallback.
        Returns a PIL Image or None if loading fails.
        """
        # Try Qt first - handles SVG, PNG, JPG, etc. robustly
        qimage = QImage()
        qt_loaded = qimage.loadFromData(QByteArray(image_data))
        
        if qt_loaded:
            # Convert QImage to PIL via PNG buffer
            buffer = QBuffer()
            buffer.open(QIODevice.ReadWrite)
            qimage.save(buffer, "PNG")
            try:
                return Image.open(io.BytesIO(buffer.data().data()))
            except Exception as e:
                self.logger.warning(f"Failed to convert Qt image to PIL: {e}")
                return None
        
        # Fallback: Try PIL directly (for WEBP if Qt plugin missing)
        try:
            return Image.open(io.BytesIO(image_data))
        except Exception:
            return None

    def _get_tokens_to_check(self):
        """
        Fetches tokens from the DB that still need an icon downloaded.
        Only selects tokens with no local icon path set yet — existing
        icons are never re-downloaded or overwritten.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT rowid, address, icon_url FROM tokens
            WHERE icon_url IS NOT NULL AND icon_url != ''
            AND (icon_local_path IS NULL OR icon_local_path = '')
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0].lower() for description in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def _fetch_and_validate_one_icon(self, token):
        """
        Downloads, validates, processes (resize/round), and saves a single icon file.
        Returns the relative path for the DB, or a placeholder path on failure.
        Uses Qt for image loading (handles SVG natively) with PIL for processing.
        """
        token_address = token['address']
        icon_url = token['icon_url']
        
        # If the icon file already exists on disk, keep it — never overwrite
        local_filename = f"{token['rowid']}.png"
        local_filepath = self.icon_cache_dir / local_filename
        if local_filepath.exists():
            relative_path = (Path('images') / 'icons' / local_filename).as_posix()
            self.logger.debug(f"Icon already exists for {token_address}, skipping download")
            return relative_path
        
        try:
            # Download image data to memory
            api_tracker.record('icon_cdn')
            response = requests.get(icon_url, timeout=15)
            response.raise_for_status()
            image_data = response.content
            
            # Load image using Qt (handles SVG, PNG, JPG, etc.)
            img = self._load_image_with_qt_fallback(image_data)
            
            if img is None:
                self.logger.warning(f"Failed to load image for {token_address} from {icon_url}. Using placeholder.")
                return PLACEHOLDER_DB_PATH
            
            try:
                # Convert to RGBA to support transparency
                img_rgba = img.convert("RGBA")
                img.close()
                
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
                
                # Define final filename (ALWAYS PNG)
                local_filename = f"{token['rowid']}.png"
                local_filepath = self.icon_cache_dir / local_filename
                
                # Clean up any existing files with different extensions for this ID
                for ext in ['.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']:
                    old_file = self.icon_cache_dir / f"{token['rowid']}{ext}"
                    if old_file.exists():
                        try:
                            old_file.unlink()
                            self.logger.info(f"Removed old duplicate icon: {old_file}")
                        except OSError:
                            pass

                # Save processed image
                output.save(local_filepath, "PNG", optimize=True)
                
                # Clean up PIL images
                output.close()
                mask.close()
                img_rgba.close()

                relative_path = (Path('images') / 'icons' / local_filename).as_posix()
                self.logger.info(f"Successfully prepared round icon for {token_address} at {relative_path}")
                return relative_path

            except (IOError, SyntaxError, Exception) as e:
                self.logger.warning(f"Failed to process image for {token_address}: {e}. Using placeholder.")
                return PLACEHOLDER_DB_PATH

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to download icon for {token_address} from {icon_url}: {e}. Using placeholder.")
            return PLACEHOLDER_DB_PATH
        except Exception as e:
            self.logger.error(f"Unexpected error processing icon for {token_address}: {e}", exc_info=True)
            return PLACEHOLDER_DB_PATH
