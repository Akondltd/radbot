import sqlite3
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TradePairManager:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add_trade_pair(self, base_token: str, quote_token: str, price: Optional[float] = None) -> bool:
        """Add a new trade pair to the database. Ignores if already exists."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Insert trade pair, ignore if it already exists
            cursor.execute(
                """INSERT OR IGNORE INTO trade_pairs (
                    base_token, quote_token, price
                ) VALUES (?, ?, ?)""",
                (base_token, quote_token, price)
            )
            self._conn.commit()
            # For INSERT OR IGNORE, this will return True even if the row was ignored (already existed).
            # If specific feedback on insertion vs. ignore is needed, self._cursor.rowcount could be checked (for sqlite3)
            # or changes() for the connection. For now, True indicates the operation was accepted by the DB.
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding trade pair: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_all_trade_pairs(self, wallet_id: int) -> List[Dict[str, any]]:
        """Get all trade pairs for a wallet, including token symbols and icon URLs."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT 
                    tp.trade_pair_id, 
                    tp.base_token, 
                    bt.symbol AS base_token_symbol, 
                    bt.icon_url AS base_token_icon_url,
                    bt.icon_local_path AS base_token_icon_local_path,
                    tp.quote_token, 
                    qt.symbol AS quote_token_symbol,
                    qt.icon_url AS quote_token_icon_url,
                    qt.icon_local_path AS quote_token_icon_local_path,
                    tp.price, 
                    tp.created_at, 
                    tp.updated_at
                FROM trade_pairs tp
                JOIN selected_pairs sp ON tp.trade_pair_id = sp.trade_pair_id
                JOIN tokens bt ON tp.base_token = bt.address
                JOIN tokens qt ON tp.quote_token = qt.address
                WHERE sp.wallet_id = ?
                ORDER BY tp.created_at DESC""",
                (wallet_id,)
            )
            
            rows = cursor.fetchall()
            pairs = []
            column_names = [description[0] for description in cursor.description]
            for row in rows:
                pair = dict(zip(column_names, row))
                # Ensure keys match what TradePairItemWidget expects by renaming 'base_token' and 'quote_token'
                pair['base_token_rri'] = pair.pop('base_token')
                pair['quote_token_rri'] = pair.pop('quote_token')
                pairs.append(pair)
            
            logger.info(f"Found {len(pairs)} selected trade pairs for wallet_id {wallet_id}.")
            return pairs
        except sqlite3.Error as e:
            logger.error(f"Error getting trade pairs for wallet {wallet_id}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return []
        finally:
            if cursor:
                cursor.close()

    def get_selected_trade_pairs(self, wallet_id: int) -> List[Dict[str, any]]:
        """Get selected trade pairs for a wallet."""
        return self.get_all_trade_pairs(wallet_id)

    def get_available_trade_pairs(self, wallet_id: int) -> List[Dict[str, any]]:
        """Get all available trade pairs for a wallet based on its tokens."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Get all tokens for this wallet
            cursor.execute(
                """SELECT t.* FROM tokens t
                JOIN wallet_tokens wt ON t.address = wt.token_address
                WHERE wt.wallet_id = ?
                ORDER BY t.symbol ASC""",
                (wallet_id,)
            )
            
            tokens = cursor.fetchall()
            if not tokens:
                return []

            # Get all possible trade pairs
            pairs = []
            for i in range(len(tokens)):
                for j in range(i + 1, len(tokens)):
                    token1 = tokens[i]
                    token2 = tokens[j]
                    
                    # Create trade pair in both directions
                    pairs.append({
                        'base_token': token1[0],  # token address
                        'quote_token': token2[0],
                        'price': None,  # Will be updated when selected
                        'created_at': None,
                        'updated_at': None
                    })
                    pairs.append({
                        'base_token': token2[0],
                        'quote_token': token1[0],
                        'price': None,
                        'created_at': None,
                        'updated_at': None
                    })

            return pairs
        except sqlite3.Error as e:
            logger.error(f"Error getting available trade pairs: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return []

    def select_trade_pair(self, base_token: str, quote_token: str, wallet_id: int) -> bool:
        """Select a trade pair for a wallet."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Get trade pair ID
            cursor.execute(
                """SELECT trade_pair_id FROM trade_pairs
                WHERE base_token = ? AND quote_token = ?""",
                (base_token, quote_token)
            )
            row = cursor.fetchone()
            if not row:
                logger.error(f"Trade pair not found: {base_token}/{quote_token}")
                return False

            trade_pair_id = row[0]

            # Insert or update selected_pairs record
            cursor.execute(
                """INSERT OR REPLACE INTO selected_pairs (
                    trade_pair_id, wallet_id, created_at
                ) VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (trade_pair_id, wallet_id)
            )

            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error selecting trade pair: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False

    def deselect_trade_pair(self, base_token: str, quote_token: str, wallet_id: int) -> bool:
        """Deselects a trade pair for a wallet by removing it from the selected_pairs table."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            # First, find the trade_pair_id for the given tokens
            cursor.execute(
                """SELECT trade_pair_id FROM trade_pairs
                WHERE base_token = ? AND quote_token = ?""",
                (base_token, quote_token)
            )
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Attempted to deselect a non-existent trade pair: {base_token}/{quote_token}")
                return False

            trade_pair_id = row[0]

            # Now, delete the entry from the selected_pairs table
            cursor.execute(
                """DELETE FROM selected_pairs
                WHERE trade_pair_id = ? AND wallet_id = ?""",
                (trade_pair_id, wallet_id)
            )
            
            self._conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Successfully deselected trade pair ID {trade_pair_id} for wallet ID {wallet_id}.")
                return True
            else:
                logger.warning(f"No trade pair ID {trade_pair_id} was selected for wallet ID {wallet_id}. Nothing to deselect.")
                return True

        except sqlite3.Error as e:
            logger.error(f"Error deselecting trade pair {base_token}/{quote_token}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_trade_pair_by_id(self, trade_pair_id: int) -> Optional[Dict[str, any]]:
        """Retrieves a specific trade pair by its ID."""
        cursor = None
        try:
            self._conn.row_factory = sqlite3.Row
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM trade_pairs WHERE trade_pair_id = ?",
                (trade_pair_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching trade pair with ID {trade_pair_id}: {e}", exc_info=True)
            return None
        finally:
            self._conn.row_factory = None  # Reset row factory
            if cursor:
                cursor.close()

    def get_trade_pair_id(self, base_token: str, quote_token: str) -> Optional[int]:
        """Gets the trade_pair_id for a given base/quote token pair."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT trade_pair_id FROM trade_pairs WHERE base_token = ? AND quote_token = ?",
                (base_token, quote_token)
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            logger.error(f"Error getting trade_pair_id for {base_token}/{quote_token}: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()

    def get_unselected_trade_pairs(self, wallet_id: int) -> List[Dict[str, any]]:
        """
        Get all trade pairs that exist in trade_pairs table but are NOT yet selected for this wallet.
        This is for the "Pairs of Interest" middle scroll area.
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT 
                    tp.trade_pair_id,
                    tp.base_token,
                    bt.symbol AS base_token_symbol,
                    bt.icon_url AS base_token_icon_url,
                    bt.icon_local_path AS base_token_icon_local_path,
                    tp.quote_token,
                    qt.symbol AS quote_token_symbol,
                    qt.icon_url AS quote_token_icon_url,
                    qt.icon_local_path AS quote_token_icon_local_path,
                    tp.price,
                    tp.created_at,
                    tp.updated_at
                FROM trade_pairs tp
                JOIN tokens bt ON tp.base_token = bt.address
                JOIN tokens qt ON tp.quote_token = qt.address
                WHERE tp.trade_pair_id NOT IN (
                    SELECT trade_pair_id FROM selected_pairs WHERE wallet_id = ?
                )
                ORDER BY tp.created_at DESC""",
                (wallet_id,)
            )
            
            rows = cursor.fetchall()
            pairs = []
            column_names = [description[0] for description in cursor.description]
            for row in rows:
                pair = dict(zip(column_names, row))
                # Rename for consistency with other methods
                pair['base_token_rri'] = pair.pop('base_token')
                pair['quote_token_rri'] = pair.pop('quote_token')
                pairs.append(pair)
            
            logger.info(f"Found {len(pairs)} unselected trade pairs for wallet_id {wallet_id}.")
            return pairs
        except sqlite3.Error as e:
            logger.error(f"Error getting unselected trade pairs for wallet {wallet_id}: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()

    def delete_trade_pair(self, base_token: str, quote_token: str) -> bool:
        """
        Completely deletes a trade pair from the trade_pairs table.
        Also removes any selected_pairs entries that reference this pair.
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            
            # First, get the trade_pair_id
            cursor.execute(
                """SELECT trade_pair_id FROM trade_pairs
                WHERE base_token = ? AND quote_token = ?""",
                (base_token, quote_token)
            )
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Attempted to delete non-existent trade pair: {base_token}/{quote_token}")
                return False
            
            trade_pair_id = row[0]
            
            # Delete from selected_pairs first (foreign key constraint)
            cursor.execute(
                """DELETE FROM selected_pairs WHERE trade_pair_id = ?""",
                (trade_pair_id,)
            )
            
            # Delete from trade_pairs
            cursor.execute(
                """DELETE FROM trade_pairs WHERE trade_pair_id = ?""",
                (trade_pair_id,)
            )
            
            self._conn.commit()
            logger.info(f"Successfully deleted trade pair {base_token}/{quote_token} (ID: {trade_pair_id})")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting trade pair {base_token}/{quote_token}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def add_auto_suggested_pair(self, base_token: str, quote_token: str, volume_7d_usd: float, price_impact: Optional[float] = None) -> bool:
        """
        Add a trade pair from automatic volume-based suggestions.
        Sets source='auto' to distinguish from user-added pairs.
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """INSERT OR IGNORE INTO trade_pairs (
                    base_token, quote_token, source, volume_7d_usd, price_impact, last_checked
                ) VALUES (?, ?, 'auto', ?, ?, CURRENT_TIMESTAMP)""",
                (base_token, quote_token, volume_7d_usd, price_impact)
            )
            self._conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Added auto-suggested pair: {base_token}/{quote_token} (volume: ${volume_7d_usd:,.2f})")
                return True
            return True  # Already exists, not an error
            
        except sqlite3.Error as e:
            logger.error(f"Error adding auto-suggested pair {base_token}/{quote_token}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def cleanup_auto_suggested_pairs(self, min_volume_7d: float) -> int:
        """
        Remove auto-suggested pairs that no longer meet the minimum volume requirement.
        Only removes pairs with source='auto', preserves user-added pairs.
        
        Args:
            min_volume_7d: Minimum 7-day USD volume threshold
            
        Returns:
            Number of pairs removed
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            
            # Delete auto pairs below threshold
            cursor.execute(
                """DELETE FROM trade_pairs 
                WHERE source = 'auto' 
                AND (volume_7d_usd IS NULL OR volume_7d_usd < ?)""",
                (min_volume_7d,)
            )
            
            removed_count = cursor.rowcount
            self._conn.commit()
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} auto-suggested pairs below ${min_volume_7d:,.2f} volume threshold")
            
            return removed_count
            
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up auto-suggested pairs: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()

    def update_pair_volume(self, base_token: str, quote_token: str, volume_7d_usd: float) -> bool:
        """Update the 7-day volume for a trade pair."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """UPDATE trade_pairs 
                SET volume_7d_usd = ?, last_checked = CURRENT_TIMESTAMP 
                WHERE base_token = ? AND quote_token = ?""",
                (volume_7d_usd, base_token, quote_token)
            )
            self._conn.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            logger.error(f"Error updating volume for pair {base_token}/{quote_token}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_pool_address_for_pair(self, trade_pair_id: int) -> Optional[str]:
        """Finds the highest liquidity Ociswap pool address for a given trade_pair_id."""
        sql = """
            SELECT op.pool_address
            FROM trade_pairs tp
            JOIN ociswap_pools op ON (op.token_a_address = tp.base_token AND op.token_b_address = tp.quote_token) OR (op.token_a_address = tp.quote_token AND op.token_b_address = tp.base_token)
            WHERE tp.trade_pair_id = ?
            ORDER BY op.liquidity_usd DESC
            LIMIT 1
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (trade_pair_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching pool address for trade_pair_id {trade_pair_id}: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()
