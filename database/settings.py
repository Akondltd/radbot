import sqlite3
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def update_settings(self, settings_data: Dict[str, any]) -> bool:
        """Update multiple settings in the database."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Update each setting in the dictionary
            for key, value in settings_data.items():
                cursor.execute(
                    """UPDATE settings
                    SET {key} = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1""".format(key=key),
                    (value,)
                )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating settings: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_settings(self) -> Dict[str, any]:
        """Get all settings from the database."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute("""SELECT * FROM settings WHERE id = 1""")
            result = cursor.fetchone()
            if result:
                # Create a dictionary of all settings
                settings = {}
                columns = [col[0] for col in cursor.description]
                for i, value in enumerate(result):
                    settings[columns[i]] = value
                return settings
            return {}
        except sqlite3.Error as e:
            logger.error(f"Error getting settings: {e}", exc_info=True)
            return {}
        finally:
            if cursor:
                cursor.close()
            logger.error(f"Error getting settings: {e}", exc_info=True)
            return {}
