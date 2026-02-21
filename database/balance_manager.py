"""
Balance manager for RadBot application.
Handles token balances, active trades, and database synchronization.
"""

import sqlite3
import logging
from decimal import Decimal, InvalidOperation
import json
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any

from core.wallet import RadixWallet
from utils.decimal_utils import from_ledger, is_displayable


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BalanceManager:
    def __init__(self, wallet: RadixWallet, conn: sqlite3.Connection):
        """
        Initialize BalanceManager.

        Args:
            wallet: RadixWallet instance
            conn: SQLite database connection
        """
        self.wallet = wallet
        self._conn = conn # Use passed connection
        self._balances: Dict[str, Dict[str, Any]] = {}
        self._active_trades: Dict[str, float] = {}
        self._last_update: Optional[datetime] = None

        self._update_in_progress = False

    def update_balances_from_api_data(self, raw_api_data: Dict[str, Dict[str, Any]]) -> tuple[bool, int]:
        """
        Update token balances in the database from raw API data,
        ensure tokens exist, and then update internal state.

        Args:
            raw_api_data: A dictionary where keys are token RRIs and values are
                          dictionaries containing 'amount' (str), 'decimals' (int),
                          'symbol' (str), and optionally 'name' (str).
                          Example: {'xrd_rr1...': {'amount': '123450000000000000000', 'decimals': 18, 'symbol': 'XRD', 'name': 'Radix'}}

        Returns:
            tuple[bool, int]: (success, new_tokens_count) - True if successful with count of newly added tokens
        """
        if not raw_api_data:
            logger.info("No raw API data provided to update_balances_from_api_data.")
            self._load_active_trades()
            self._update_internal_state()
            self._last_update = datetime.now(timezone.utc)
            return (True, 0)  # No new tokens

        if self._update_in_progress:
            logger.warning("Balance update already in progress. Skipping.")
            return (False, 0)
            
        if not hasattr(self.wallet, 'public_address') or not self.wallet.public_address:
            logger.error("No valid public_address in wallet. Cannot update balances.")
            return (False, 0)

        self._update_in_progress = True
        new_tokens_count = 0  # Track newly added tokens
        logger.info(f"Starting balance update for wallet: {self.wallet.public_address}")
        cursor = None
        try:
            from database.tokens import TokenManager
            token_manager = TokenManager(conn=self._conn)
            cursor = self._conn.cursor()

            wallet_id = getattr(self.wallet, 'wallet_id', None)
            if wallet_id is None:
                cursor.execute(
                    "SELECT wallet_id FROM wallets WHERE wallet_address = ?",
                    (self.wallet.public_address,)
                )
                wallet_row = cursor.fetchone()
                if not wallet_row:
                    if hasattr(self.wallet, 'name') and self.wallet.name:
                        wallet_name = self.wallet.name
                    else:
                        wallet_name = f"Wallet {self.wallet.public_address[:8]}"
                    wallet_file_path = str(self.wallet.wallet_file) if hasattr(self.wallet, 'wallet_file') and self.wallet.wallet_file else None
                    cursor.execute(
                        "INSERT INTO wallets (wallet_name, wallet_address, wallet_file_path) VALUES (?, ?, ?)",
                        (wallet_name, self.wallet.public_address, wallet_file_path)
                    )
                    wallet_id = cursor.lastrowid
                    if wallet_id is None:
                        self._conn.rollback()
                        logger.error(f"Failed to create and retrieve wallet_id for {self.wallet.public_address}")
                        self._update_in_progress = False  # Reset flag on error
                        return (False, 0)
                    logger.info(f"Created new wallet entry for {self.wallet.public_address} with wallet_id: {wallet_id}")
                    if hasattr(self.wallet, 'wallet_id'): # Update wallet instance if it has the attribute
                        self.wallet.wallet_id = wallet_id
                else:
                    wallet_id = wallet_row[0]
                    if hasattr(self.wallet, 'wallet_id'): self.wallet.wallet_id = wallet_id
            
            if wallet_id is None: # Should not happen
                logger.critical(f"CRITICAL: wallet_id is None for {self.wallet.public_address} before processing balances.")
                self._update_in_progress = False  # Reset flag on error
                return (False, 0)

            for rri, token_data in raw_api_data.items():
                raw_amount_str = token_data.get('amount')
                decimals = token_data.get('decimals')
                # Extract metadata from first API call (now includes explicit_metadata via opt_ins)
                symbol = token_data.get('symbol') if token_data.get('symbol') != 'UNKNOWN' else None
                name = token_data.get('name') if token_data.get('name') != 'Unknown Token' else None

                if raw_amount_str is None or decimals is None:
                    logger.warning(f"Skipping token {rri} due to missing amount or decimals. Data: {token_data}")
                    continue

                try:
                    # Check if token already exists with complete metadata
                    cursor.execute("SELECT symbol, name FROM tokens WHERE address = ?", (rri,))
                    token_row = cursor.fetchone()
                    token_existed = token_row is not None
                    has_complete_metadata = token_existed and token_row[0] and token_row[1]
                    
                    # Only fetch from gateway if we're missing metadata AND it wasn't in the first API call
                    # (opt_ins should now provide metadata, eliminating most gateway fetches)
                    fetch_needed = not has_complete_metadata and (not symbol or not name)
                    token_manager.ensure_token_exists(rri, symbol, name, int(decimals), fetch_from_gateway=fetch_needed)
                    
                    # If token didn't exist before, it's new
                    if not token_existed:
                        new_tokens_count += 1
                        logger.info(f"New token detected: {rri} ({symbol or 'unknown'})")
                except Exception as e_token:
                    logger.error(f"Failed to ensure token {rri} ({symbol}) exists: {e_token}", exc_info=True)
                    continue

                try:  # This is the try block for amount processing
                    if not isinstance(raw_amount_str, str):
                        raw_amount_str = str(raw_amount_str)
                
                    current_decimals = int(decimals)
                    
                    # Normalize ledger balance to respect divisibility and eliminate phantom precision
                    amount_decimal = from_ledger(raw_amount_str, current_decimals)
                
                    # Store as TEXT to preserve full precision (up to divisibility limit)
                    formatted_balance_str = str(amount_decimal)
                    
                    logger.debug(
                        f"Upserting balance for wallet {wallet_id}, token {rri} ({symbol}): "
                        f"{formatted_balance_str} (Raw Gateway: {raw_amount_str}, Decimals: {current_decimals})"
                    )

                    # Corrected SQL query to use 'balance' column and REMOVE 'token_symbol'
                    # Retry logic for database lock scenarios
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            cursor.execute(
                                """INSERT INTO token_balances (wallet_id, token_address, balance, last_updated)
                                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                   ON CONFLICT(wallet_id, token_address) DO UPDATE SET
                                   balance = excluded.balance,
                                   last_updated = CURRENT_TIMESTAMP""",
                                (wallet_id, rri, formatted_balance_str) # Removed 'symbol' from here
                            )
                            self._conn.commit()
                            break  # Success, exit retry loop
                        except sqlite3.OperationalError as db_err:
                            if "database is locked" in str(db_err) and attempt < max_retries - 1:
                                logger.debug(f"Database locked, retry {attempt + 1}/{max_retries} for token {rri}")
                                import time
                                time.sleep(0.1 * (attempt + 1))  # Exponential backoff: 0.1s, 0.2s, 0.3s
                            else:
                                raise  # Re-raise if not a lock error or final attempt

                except InvalidOperation:
                    logger.error(f"Raw amount for token {rri} ({symbol}) is not a valid number for Decimal conversion: {raw_amount_str}", exc_info=True)
                    continue 
                except Exception as e_calc: 
                    logger.error(f"Error processing balance for token {rri} ({symbol}): {e_calc}", exc_info=True)
                    continue

            current_api_rris = set(raw_api_data.keys())
            cursor.execute("SELECT token_address FROM token_balances WHERE wallet_id = ?", (wallet_id,))
            db_rris_for_wallet = {row[0] for row in cursor.fetchall()}
            rris_to_delete = db_rris_for_wallet - current_api_rris

            if rris_to_delete:
                for rri_del in rris_to_delete:
                    cursor.execute(
                        "DELETE FROM token_balances WHERE wallet_id = ? AND token_address = ?",
                        (wallet_id, rri_del)
                    )
                    logger.info(f"Deleted stale balance for wallet {wallet_id}, token {rri_del}")

            self._conn.commit()
            logger.info(f"Successfully updated database balances for wallet {self.wallet.public_address}")

            self._load_active_trades()
            self._update_internal_state()

            self._last_update = datetime.now(timezone.utc)
            
            if new_tokens_count > 0:
                logger.info(f"Balance update completed with {new_tokens_count} new token(s) added")
            
            return (True, new_tokens_count)

        except sqlite3.Error as e_sqlite:
            logger.error(f"SQLite error during balance update for {self.wallet.public_address}: {e_sqlite}", exc_info=True)
            if self._conn and cursor:
                try: self._conn.rollback()
                except sqlite3.Error as e_rb: logger.error(f"Error during rollback after SQLite error: {e_rb}")
            self._update_in_progress = False  # Reset flag on error
            return (False, 0)
        except Exception as e_general:
            logger.error(f"Unexpected error during balance update for {self.wallet.public_address}: {e_general}", exc_info=True)
            if self._conn and cursor:
                try: self._conn.rollback()
                except sqlite3.Error as e_rb_gen: logger.error(f"Error during rollback after general error: {e_rb_gen}")
            self._update_in_progress = False  # Reset flag on error
            return (False, 0)
        finally:
            if cursor: 
                try: cursor.close()
                except sqlite3.Error as e_cursor_close: logger.error(f"Error closing cursor after balance update: {e_cursor_close}")
            
            if self._update_in_progress:
                self._update_in_progress = False
                logger.info(f"Finished balance update for wallet: {self.wallet.public_address}")

    def _load_active_trades(self):
        """
        Load active trades from the database for the active wallet.
        Populates self._active_trades with {token_rri: locked_amount_float}.
        """
        cursor = None
        try:
            self._active_trades.clear()  # Clear previous trades before loading
            cursor = self._conn.cursor()

            # Get the active wallet ID from settings
            cursor.execute("SELECT active_wallet_id FROM settings WHERE id = 1")
            settings_row = cursor.fetchone()
            if not settings_row or not settings_row[0]:
                logger.warning("No active wallet set in settings. No active trades will be loaded.")
                return
                
            active_wallet_id = settings_row[0]
            
            # Get the wallet address for this wallet_id to query trades
            cursor.execute("SELECT wallet_address FROM wallets WHERE wallet_id = ?", (active_wallet_id,))
            wallet_row = cursor.fetchone()
            if not wallet_row:
                logger.warning(f"Active wallet ID {active_wallet_id} not found in wallets table.")
                return
                
            wallet_address = wallet_row[0]

            # Use the wallet's public address to query the trades table.
            # ALL trades (active or paused) represent locked (earmarked) funds.
            # Trades are perpetual loops - funds remain committed even when paused.
            cursor.execute(
                "SELECT trade_amount, trade_token_address FROM trades WHERE wallet_address = ?",
                (wallet_address,)
            )
            active_trades_rows = cursor.fetchall()
            
            logger.debug(f"Loading locked funds for {len(active_trades_rows) if active_trades_rows else 0} trade(s)")

            for trade_row in active_trades_rows:
                (amount_val, locked_token_rri) = trade_row

                # Skip if amount or token address is None/NULL
                if amount_val is None or locked_token_rri is None:
                    logger.warning(f"Skipping trade with NULL amount ({amount_val}) or token ({locked_token_rri})")
                    continue

                trade_amount_float = 0.0
                try:
                    # The amount is stored as TEXT, so it needs conversion.
                    trade_amount_float = float(amount_val)
                except (ValueError, TypeError) as e:
                    logger.error(f"Could not convert trade amount '{amount_val}' to float for token {locked_token_rri}: {e}. Skipping this trade's contribution to locked balance.")
                    continue

                current_locked_amount = self._active_trades.get(locked_token_rri, 0.0)
                self._active_trades[locked_token_rri] = current_locked_amount + trade_amount_float
                logger.debug(
                    f"Earmarked funds from trade: {trade_amount_float} of {locked_token_rri} "
                    f"(Total locked for this token: {current_locked_amount + trade_amount_float})"
                )

        except sqlite3.Error as e:
            logger.error(
                f"SQLite error loading active trades for active wallet: {e}",
                exc_info=True
            )
        except Exception as e_gen:
            logger.error(
                f"Unexpected error loading active trades for active wallet: {e_gen}",
                exc_info=True
            )
        finally:
            if cursor:
                cursor.close()

    def _update_internal_state(self):
        """
        Update internal _balances by fetching from the database
        for the active wallet. Balances in DB are stored as precise strings.
        This reflects the true state after considering API balances
        and active trades.
        """
        cursor = None
        try:
            self._balances.clear()  # Clear previous balances
            cursor = self._conn.cursor()

            # Get the active wallet ID from settings - this is the source of truth
            cursor.execute("SELECT active_wallet_id FROM settings WHERE id = 1")
            settings_row = cursor.fetchone()
            if not settings_row or not settings_row[0]:
                logger.warning("No active wallet set in settings. Balances will be empty.")
                return
                
            wallet_id = settings_row[0]
            logger.debug(f"Using active wallet ID {wallet_id} from settings")

            cursor.execute("""
                SELECT tb.token_address, tb.balance, 
                       t.symbol, t.name, t.divisibility
                FROM token_balances tb
                JOIN tokens t ON tb.token_address = t.address
                WHERE tb.wallet_id = ?
            """, (wallet_id,))

            db_balance_rows = cursor.fetchall()

            for token_rri, total_balance_str, symbol, name, divisibility_val in db_balance_rows:
                divisibility = int(divisibility_val) if divisibility_val is not None else 18
                
                total_balance_float = 0.0
                try:
                    total_balance_float = float(total_balance_str)
                except ValueError:
                    logger.error(
                        f"Could not convert balance string '{total_balance_str}' to float "
                        f"for token {token_rri} ({symbol}). Using 0.0 as total."
                    )
                
                locked_amount_float = self._active_trades.get(token_rri, 0.0)
                if not isinstance(locked_amount_float, float):
                    try:
                        locked_amount_float = float(locked_amount_float)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert locked amount {locked_amount_float} to float for {token_rri}. Defaulting to 0.0.")
                        locked_amount_float = 0.0

                available_balance_float = total_balance_float - locked_amount_float
                
                # CRITICAL: Check for negative balance (external wallet transaction)
                # If ledger balance < locked amounts, deactivate all trades with this token
                # Add tolerance for floating point precision errors (0.01 threshold)
                NEGATIVE_BALANCE_THRESHOLD = -0.00001
                if available_balance_float < NEGATIVE_BALANCE_THRESHOLD:
                    # Possible race condition: trade might be mid-execution
                    # Re-check locked amounts after brief delay to confirm this is real
                    import time
                    time.sleep(0.5)  # Wait for any in-flight trade updates to commit
                    
                    # Re-load active trades to get latest locked amounts
                    self._load_active_trades()
                    locked_amount_float = float(self._active_trades.get(token_rri, 0.0))
                    available_balance_float = total_balance_float - locked_amount_float
                    
                    # Check again - if still negative, it's a real problem
                if available_balance_float < NEGATIVE_BALANCE_THRESHOLD:
                    logger.critical(
                        f"NEGATIVE BALANCE DETECTED for {symbol} ({token_rri})! "
                        f"Ledger: {total_balance_float}, Locked: {locked_amount_float}, "
                        f"Deficit: {available_balance_float}. "
                        f"This indicates external wallet activity (e.g., Radix Mobile Wallet). "
                        f"Deactivating all trades with this token."
                    )
                    
                    # Deactivate all trades that involve this token
                    try:
                        deactivate_cursor = self._conn.cursor()
                        
                        # Find all active trades where this token is in the pair
                        deactivate_cursor.execute("""
                            SELECT t.trade_id, tp.base_token, tp.quote_token
                            FROM trades t
                            JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                            WHERE t.is_active = 1
                            AND (tp.base_token = ? OR tp.quote_token = ?)
                        """, (token_rri, token_rri))
                        
                        affected_trades = deactivate_cursor.fetchall()
                        
                        if affected_trades:
                            trade_ids = [row[0] for row in affected_trades]
                            # Build pair names from base/quote tokens
                            pair_names = set([f"{row[1]}/{row[2]}" for row in affected_trades])
                            
                            logger.warning(
                                f"Deactivating {len(trade_ids)} trade(s) due to insufficient balance: "
                                f"Trade IDs: {trade_ids}, Pairs: {', '.join(pair_names)}"
                            )
                            
                            # Deactivate all affected trades
                            placeholders = ','.join(['?'] * len(trade_ids))
                            deactivate_cursor.execute(
                                f"UPDATE trades SET is_active = 0 WHERE trade_id IN ({placeholders})",
                                trade_ids
                            )
                            self._conn.commit()
                            
                            logger.info(f"Successfully deactivated {len(trade_ids)} trade(s)")
                        else:
                            logger.info(f"No active trades found for {symbol} to deactivate")
                            
                        deactivate_cursor.close()
                        
                    except sqlite3.Error as e:
                        logger.error(f"Database error while deactivating trades for {symbol}: {e}")
                        self._conn.rollback()
                    except Exception as e:
                        logger.error(f"Error deactivating trades for {symbol}: {e}", exc_info=True)
                
                # Check if balance is displayable (not dust)
                balance_decimal = Decimal(str(total_balance_float))
                if not is_displayable(balance_decimal, divisibility):
                    logger.debug(f"Skipping dust balance for {symbol}: {total_balance_float}")
                    continue
                
                self._balances[token_rri] = {
                    'total': total_balance_float,
                    'locked': locked_amount_float,
                    'available': available_balance_float,
                    'symbol': symbol,
                    'name': name,
                    'divisibility': divisibility
                }
            logger.info(
                f"Internal balances updated for active wallet ID {wallet_id}. "
                f"Found {len(db_balance_rows)} token(s)."
            )

        except sqlite3.Error as e:
            logger.error(
                f"SQLite error updating internal state for active wallet: {e}", exc_info=True
            )
        except Exception as e_gen:
            logger.error(
                f"Unexpected error updating internal state for active wallet: {e_gen}",
                exc_info=True
            )
        finally:
            if cursor:
                cursor.close()

    def get_balance(self, token_rri: str) -> Optional[Dict[str, Any]]:
        """
        Get balance for a specific token.

        Args:
            token_rri: Token RRI string

        Returns:
            Dict or None: Balance details or None if not found
        """
        return self._balances.get(token_rri)

    def get_last_update_time(self) -> Optional[datetime]:
        """Returns the timestamp of the last successful balance update."""
        return self._last_update

    def get_all_balances(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all token balances.

        Returns:
            Dict: All token balances
        """
        return self._balances

    def get_active_trades(self) -> List[Dict[str, Any]]:
        """
        Get all active trades.

        Returns:
            List[Dict[str, Any]]: List of active trades with their details.
        """
        return self._active_trades

    def check_sufficient_balance(
        self, token_address: str, required_amount: float
    ) -> bool:
        """
        Check if there is sufficient available balance for a token.

        Args:
            token_address: The RRI of the token.
            required_amount: The amount required.

        Returns:
            bool: True if sufficient balance is available, False otherwise.
        """
        balance_info = self.get_balance(token_address)
        if balance_info and balance_info['available'] >= required_amount:
            return True
        logger.warning(
            "Insufficient available balance for %s. "
            "Required: %s, Available: %s",
            token_address,
            required_amount,
            balance_info.get('available', 0) if balance_info else 0
        )
        return False

    def lock_balance(
        self, token_address: str, amount: float, strategy_name: str,
        indicator_settings: Dict, entry_price: float
    ) -> Optional[int]:
        """
        Lock a certain amount of a token for a trade and record it
        in active_trades.

        Args:
            token_address: The RRI of the token to lock.
            amount: The amount of the token to lock.
            strategy_name: Name of the trading strategy initiating the lock.
            indicator_settings: Dictionary of indicator settings for the trade.
            entry_price: The price at which the trade was entered.

        Returns:
            Optional[int]: The trade_id if successful, None otherwise.
        """
        cursor = None
        try:
            if not self.check_sufficient_balance(token_address, amount):
                # Insufficient balance, logged by check_sufficient_balance
                return None

            cursor = self._conn.cursor()

            # Get wallet_id for the current wallet
            cursor.execute(
                "SELECT wallet_id FROM wallets WHERE wallet_address = ?",
                (self.wallet.address,)
            )
            wallet_row = cursor.fetchone()
            if not wallet_row:
                logger.error(
                    f"Wallet {self.wallet.address} not found in database. "
                    f"Cannot lock balance."
                )
                return None
            wallet_id = wallet_row[0]

            # Serialize indicator_settings to JSON string
            indicator_settings_json = json.dumps(indicator_settings)

            cursor.execute(
                """
                INSERT INTO active_trades (
                    wallet_id, token_address, amount,
                    entry_price, status, strategy_name,
                    indicator_settings_json, entry_time
                )
                VALUES (
                    ?, ?, ?, ?, 'OPEN',
                    ?, ?, CURRENT_TIMESTAMP
                )
                """,
                (
                    wallet_id, token_address, amount,
                    entry_price, strategy_name,
                    indicator_settings_json
                ),
            )

            trade_id = cursor.lastrowid
            self._conn.commit()
            logger.info(
                f"Successfully locked {amount} of {token_address} "
                f"for trade {trade_id}. Strategy: {strategy_name}"
            )

            # Update internal state to reflect the new lock
            self._load_active_trades()  # Reload trades with new one
            # Update available balances
            self._update_internal_state()

            return trade_id

        except json.JSONDecodeError as e_json:
            logger.error(
                "Error serializing indicator_settings to JSON "
                "for locking balance: %s",
                e_json,
                exc_info=True
            )
            # Check if connection and cursor exist before trying to rollback
            if self._conn and cursor:
                try: self._conn.rollback()
                # nested try-except for rollback
                except sqlite3.Error as e_rb_json:
                    logger.error(
                        "Error during rollback after JSON error: %s",
                        e_rb_json
                    )
            return None
        except sqlite3.Error as e_sqlite:
            logger.error(
                "SQLite error locking balance for %s: %s",
                token_address,
                e_sqlite,
                exc_info=True
            )
            # Check if connection and cursor exist
            if self._conn and cursor:
                try:
                    self._conn.rollback()
                # nested try-except for rollback
                except sqlite3.Error as e_rb_sqlite:
                    logger.error(
                        "Error during rollback after SQLite error: %s",
                        e_rb_sqlite
                    )
            return None
        except Exception as e_general:
            logger.error(
                "Unexpected error locking balance for %s: %s",
                token_address,
                e_general,
                exc_info=True
            )
            # Check if connection and cursor exist
            if self._conn and cursor:
                try:
                    self._conn.rollback()
                # nested try-except for rollback
                except sqlite3.Error as e_rb_general:
                    logger.error(
                        "Error during rollback after general error: %s",
                        e_rb_general
                    )
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except sqlite3.Error as e_cursor_close:
                    logger.error(
                        "Error closing cursor after attempting to "
                        "lock balance: %s",
                        e_cursor_close
                    )

    def unlock_balance(self, trade_id: int) -> bool:
        """
        Unlock a previously locked balance by closing the trade.

        Args:
            trade_id: The ID of the trade to unlock/close.

        Returns:
            bool: True if successful, False otherwise.
        """
        cursor = None
        try:
            cursor = self._conn.cursor()

            # Fetch the trade details to ensure it exists and is OPEN
            cursor.execute(
                "SELECT token_address, amount, status "
                "FROM active_trades WHERE trade_id = ?",
                (trade_id,)
            )
            trade_row = cursor.fetchone()

            if not trade_row:
                logger.warning(
                    "Trade ID %s not found. Cannot unlock balance.",
                    trade_id
                )
                return False

            token_address, amount, status = trade_row
            if status != 'OPEN':
                logger.warning(
                    "Trade ID %s is not 'OPEN' (status: %s). Cannot unlock.",
                    trade_id,
                    status
                )
                return False

            # Close the trade by updating its status and setting exit_time
            cursor.execute(
                "UPDATE active_trades "
                "SET status = 'CLOSED', exit_time = CURRENT_TIMESTAMP "
                "WHERE trade_id = ?",
                (trade_id,)
            )
            self._conn.commit()
            logger.info(
                "Successfully unlocked balance for trade ID %s "
                "(Token: %s, Amount: %s).",
                trade_id,
                token_address,
                amount
            )

            # Update internal state to reflect the change
            # Reload active trades (this one will now be closed)
            self._load_active_trades()
            # Update available balances
            self._update_internal_state()
            return True

        except sqlite3.Error as e_sqlite:
            logger.error(
                "SQLite error unlocking balance for trade ID %s: %s",
                trade_id,
                e_sqlite,
                exc_info=True
            )
            if self._conn and cursor:
                try:
                    self._conn.rollback()
                except sqlite3.Error as e_rb_sqlite:
                    logger.error(
                        "Error during rollback after SQLite error in "
                        "unlock_balance: %s",
                        e_rb_sqlite
                    )
            return False
        except Exception as e_general:
            logger.error(
                "Unexpected error unlocking balance for trade ID %s: %s",
                trade_id,
                e_general,
                exc_info=True
            )
            if self._conn and cursor:
                try:
                    self._conn.rollback()
                except sqlite3.Error as e_rb_general:
                    logger.error(
                        "Error during rollback after "
                        "general error in "
                        "unlock_balance: %s",
                        e_rb_general
                    )
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except sqlite3.Error as e_cursor_close:
                    logger.error(
                        "Error closing cursor after attempting to "
                        "unlock balance: %s",
                        e_cursor_close
                    )
