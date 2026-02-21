import sqlite3
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get_or_create_wallet_entry(self, wallet_name: str, wallet_address: str, wallet_file_path: str) -> Optional[int]:
        """Get or create a wallet entry in the database.
        
        Wallet addresses are unique - if the address already exists but with a different
        file path, the file path will be updated rather than creating a duplicate entry.
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Check if wallet exists by address (addresses are unique)
            cursor.execute(
                """SELECT wallet_id, wallet_file_path, wallet_name FROM wallets 
                WHERE wallet_address = ?""",
                (wallet_address,)
            )
            row = cursor.fetchone()
            if row:
                wallet_id = row[0]
                existing_path = row[1]
                existing_name = row[2]
                
                # Update file path and/or name if they've changed
                if existing_path != wallet_file_path or existing_name != wallet_name:
                    cursor.execute(
                        """UPDATE wallets SET wallet_file_path = ?, wallet_name = ? 
                        WHERE wallet_id = ?""",
                        (wallet_file_path, wallet_name, wallet_id)
                    )
                    self._conn.commit()
                    logger.info(f"Updated wallet entry {wallet_id}: path='{wallet_file_path}', name='{wallet_name}'")
                
                return wallet_id

            # Create new wallet (address doesn't exist)
            cursor.execute(
                """INSERT INTO wallets (wallet_name, wallet_address, wallet_file_path)
                VALUES (?, ?, ?)""",
                (wallet_name, wallet_address, wallet_file_path)
            )
            self._conn.commit()
            logger.info(f"Created new wallet entry for address {wallet_address}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error getting/creating wallet entry: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()

    def get_wallet_by_id(self, wallet_id: int) -> Optional[Dict[str, any]]:
        """Get wallet details by ID."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT * FROM wallets WHERE wallet_id = ?""",
                (wallet_id,)
            )
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting wallet by ID: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()

    def get_wallet_by_file_path(self, file_path: str) -> Optional[int]:
        """Get wallet ID by file path."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT wallet_id FROM wallets WHERE wallet_file_path = ?""",
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting wallet by file path: {e}", exc_info=True)
            return None

    def get_wallet_by_address(self, wallet_address: str) -> Optional[Dict[str, any]]:
        """Get wallet details by address."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT * FROM wallets WHERE wallet_address = ?""",
                (wallet_address,)
            )
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting wallet by address: {e}", exc_info=True)
            return None
