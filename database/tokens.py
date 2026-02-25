import sqlite3
import json
from typing import Dict, List, Optional, Any
import logging
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def insert_or_update_token(self, token_data: Dict[str, any]) -> bool:
        """
        Insert or update a token in the database (NON-DESTRUCTIVE).
        Expects token_data with snake_case keys matching database schema.
        Used for Ociswap and Gateway API responses.
        
        Important: Uses INSERT ... ON CONFLICT DO UPDATE to preserve locally-managed fields:
        - icon_local_path (set by IconCacheService)
        - icon_last_checked_timestamp (set by IconCacheService)
        - order_index (can be manually set)
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Convert all values to their appropriate types
            token_data = {
                k: (v if k not in ['divisibility', 'token_price_xrd', 'token_price_usd', 
                                'diff_24h', 'diff_24h_usd', 'diff_7_days', 'diff_7_days_usd',
                                'volume_24h', 'volume_7d', 'total_supply', 'circ_supply', 'tvl'] 
                       else float(v) if v is not None else None)
                for k, v in token_data.items()
            }

            # Insert new token, or update ONLY the API fields if it already exists
            # This preserves icon_local_path, icon_last_checked_timestamp, and order_index
            cursor.execute(
                """INSERT INTO tokens (
                    address, symbol, name, description, icon_url, info_url,
                    divisibility, token_price_xrd, token_price_usd,
                    diff_24h, diff_24h_usd, diff_7_days, diff_7_days_usd,
                    volume_24h, volume_7d, total_supply, circ_supply,
                    tvl, type, tags, created_at, updated_at, order_index, icon_local_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    symbol = excluded.symbol,
                    name = excluded.name,
                    description = excluded.description,
                    icon_url = excluded.icon_url,
                    info_url = excluded.info_url,
                    divisibility = excluded.divisibility,
                    token_price_xrd = excluded.token_price_xrd,
                    token_price_usd = excluded.token_price_usd,
                    diff_24h = excluded.diff_24h,
                    diff_24h_usd = excluded.diff_24h_usd,
                    diff_7_days = excluded.diff_7_days,
                    diff_7_days_usd = excluded.diff_7_days_usd,
                    volume_24h = excluded.volume_24h,
                    volume_7d = excluded.volume_7d,
                    total_supply = excluded.total_supply,
                    circ_supply = excluded.circ_supply,
                    tvl = excluded.tvl,
                    type = excluded.type,
                    tags = excluded.tags,
                    updated_at = CURRENT_TIMESTAMP,
                    icon_local_path = COALESCE(excluded.icon_local_path, tokens.icon_local_path)
                    -- NOTE: icon_last_checked_timestamp, order_index NOT updated (preserved)
                """,
                (
                    token_data.get('address'),
                    token_data.get('symbol'),
                    token_data.get('name'),
                    token_data.get('description'),
                    token_data.get('icon_url'),
                    token_data.get('info_url'),
                    token_data.get('divisibility'),
                    token_data.get('token_price_xrd'),
                    token_data.get('token_price_usd'),
                    token_data.get('diff_24h'),
                    token_data.get('diff_24h_usd'),
                    token_data.get('diff_7_days'),
                    token_data.get('diff_7_days_usd'),
                    token_data.get('volume_24h'),
                    token_data.get('volume_7d'),
                    token_data.get('total_supply'),
                    token_data.get('circ_supply'),
                    token_data.get('tvl'),
                    token_data.get('type'),
                    token_data.get('tags'),
                    token_data.get('order_index'),
                    token_data.get('icon_local_path')
                )
            )
            
            self._conn.commit()
            logger.debug(f"Successfully inserted/updated token: {token_data.get('address')}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting/updating token {token_data.get('address')}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def insert_or_update_token_from_astrolescent(self, token_data: Dict[str, any]) -> bool:
        """
        Insert or update a token from Astrolescent API response.
        Converts camelCase keys from Astrolescent to snake_case for database.
        
        Args:
            token_data: Token data from Astrolescent API (camelCase format)
            
        Returns:
            True if successful, False otherwise
        """
        # Convert Astrolescent camelCase format to database snake_case format
        # Also convert list fields to JSON strings for SQLite compatibility
        tags = token_data.get('tags')
        tags_json = json.dumps(tags) if isinstance(tags, list) else tags
        
        converted_data = {
            'address': token_data.get('address'),
            'symbol': token_data.get('symbol'),
            'name': token_data.get('name'),
            'description': token_data.get('description'),
            'icon_url': token_data.get('iconUrl'), 
            'info_url': token_data.get('infoUrl'), 
            'divisibility': token_data.get('divisibility'),
            'token_price_xrd': token_data.get('tokenPriceXRD'), 
            'token_price_usd': token_data.get('tokenPriceUSD'), 
            'diff_24h': token_data.get('diff24H'), 
            'diff_24h_usd': token_data.get('diff24HUSD'), 
            'diff_7_days': token_data.get('diff7Days'), 
            'diff_7_days_usd': token_data.get('diff7DaysUSD'), 
            'volume_24h': token_data.get('volume24H'), 
            'volume_7d': token_data.get('volume7D'), 
            'total_supply': token_data.get('totalSupply'), 
            'circ_supply': token_data.get('circSupply'),  
            'tvl': token_data.get('tvl'),
            'type': token_data.get('type'),
            'tags': tags_json,  # Convert list to JSON string
            'created_at': token_data.get('createdAt'),  
            'updated_at': token_data.get('updatedAt'),  
            'order_index': token_data.get('orderIndex'),
            'icon_local_path': token_data.get('iconLocalPath')
        }
        
        # Use the existing insert method with converted data
        return self.insert_or_update_token(converted_data)

    def get_token_by_rri(self, rri: str) -> Optional[Dict[str, Any]]:
        """Fetches a single token's details by its RRI."""
        sql = "SELECT address, symbol, name, divisibility, icon_url, icon_local_path FROM tokens WHERE address = ?"
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (rri,))
            row = cursor.fetchone()
            if row:
                return {
                    "address": row[0],
                    "symbol": row[1],
                    "name": row[2],
                    "divisibility": row[3],
                    "icon_url": row[4],
                    "icon_local_path": row[5]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error in get_token_by_rri for rri {rri}: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()

    def _fetch_ociswap_metadata(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive token metadata from Ociswap API.
        
        Args:
            token_address: The resource address of the token
            
        Returns:
            Dictionary with token metadata or None if fetch fails
        """
        try:
            import requests
            logger.debug(f"Fetching Ociswap metadata for token: {token_address}")
            
            url = f"https://api.ociswap.com/tokens/{token_address}"
            headers = {"accept": "application/json"}
            
            api_tracker.record('ociswap')
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 404:
                logger.info(f"Token {token_address} not found on Ociswap (not traded)")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Extract metadata
            metadata = {
                'symbol': data.get('symbol'),
                'name': data.get('name'),
                'description': data.get('description'),
                'icon_url': data.get('icon_url'),
                'divisibility': data.get('supply', {}).get('divisbility'),  # Note: API has typo "divisbility"
                'token_price_xrd': float(data.get('price', {}).get('xrd', {}).get('now', 0)),
                'token_price_usd': float(data.get('price', {}).get('usd', {}).get('now', 0)),
                'diff_24h': float(data.get('price', {}).get('xrd', {}).get('24h', 0)) - float(data.get('price', {}).get('xrd', {}).get('now', 0)),
                'diff_24h_usd': float(data.get('price', {}).get('usd', {}).get('24h', 0)) - float(data.get('price', {}).get('usd', {}).get('now', 0)),
                'diff_7d': float(data.get('price', {}).get('xrd', {}).get('7d', 0)) - float(data.get('price', {}).get('xrd', {}).get('now', 0)),
                'diff_7d_usd': float(data.get('price', {}).get('usd', {}).get('7d', 0)) - float(data.get('price', {}).get('usd', {}).get('now', 0)),
                'volume_24h': float(data.get('volume', {}).get('xrd', {}).get('24h', 0)),
                'volume_7d': float(data.get('volume', {}).get('xrd', {}).get('7d', 0)),
                'total_supply': float(data.get('supply', {}).get('total', 0)),
                'circ_supply': None,  # Ociswap doesn't provide circulating supply separately
                'tvl': float(data.get('total_value_locked', {}).get('xrd', {}).get('now', 0))
            }
            
            logger.info(f"Fetched Ociswap metadata for {token_address}: {metadata.get('symbol')} - {metadata.get('name')}")
            return metadata
            
        except requests.RequestException as e:
            logger.warning(f"Could not fetch Ociswap metadata for {token_address}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Ociswap metadata for {token_address}: {e}", exc_info=True)
            return None

    def ensure_token_exists(self, rri: str, symbol: Optional[str], name: Optional[str], decimals: Optional[int], fetch_from_gateway: bool = True) -> bool:
        """Ensures a token exists with basic details. If not, inserts it.
        
        Args:
            rri: Token resource address
            symbol: Token symbol (optional)
            name: Token name (optional)
            decimals: Token divisibility (optional)
            fetch_from_gateway: If True, fetch missing metadata from Radix Gateway
        """
        if not rri:
            logger.error("RRI is required to ensure token exists.")
            return False
        
        # If metadata is missing and fetch_from_gateway is enabled, fetch from Gateway only
        # Note: Token prices/metadata are kept fresh by QtTokenUpdaterService (runs every 24h)
        # so we only need basic on-chain data here for new/unknown tokens
        icon_url = None  # Will be fetched from Gateway if available
        description = None
        info_url = None
        
        # Check if we need to fetch from Gateway:
        # - If basic fields (symbol, name, decimals) are missing
        # - OR if we need icon_url (always check for new tokens)
        needs_basic_fields = not symbol or not name or decimals is None
        
        if fetch_from_gateway:
            # Fetch metadata from Radix Gateway (on-chain data)
            # This is especially important for icon_url which might not be in Astrolescent
            try:
                from core.radix_network import RadixNetwork
                network = RadixNetwork()
                gateway_metadata = network.get_token_metadata(rri)
                
                if gateway_metadata:
                    # Use Gateway data for basic fields
                    if not symbol:
                        symbol = gateway_metadata.get('symbol')
                    if not name:
                        name = gateway_metadata.get('name')
                    if decimals is None:
                        decimals = gateway_metadata.get('divisibility')
                    # Also grab icon_url and other metadata from Gateway
                    icon_url = gateway_metadata.get('icon_url')
                    description = gateway_metadata.get('description')
                    info_url = gateway_metadata.get('info_url')
                    logger.info(f"Fetched metadata from Gateway for {rri}: {symbol} ({name}), icon_url={icon_url is not None}")
            except Exception as e:
                logger.warning(f"Could not fetch metadata from Gateway for {rri}: {e}")
        
        cursor = None
        try:
            cursor = self._conn.cursor()
            
            # Retry logic for database locks
            max_retries = 3
            retry_delay = 0.1  # 100ms
            for attempt in range(max_retries):
                try:
                    cursor.execute("SELECT address FROM tokens WHERE address = ?", (rri,))
                    break
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        import time
                        logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise
            
            if cursor.fetchone():
                # Token already exists, update with new metadata if available
                final_update_fields = []
                final_params = []
                
                # Basic fields - only update if current is empty
                cursor.execute("SELECT rowid, symbol, name, divisibility, icon_url, description, info_url, order_index FROM tokens WHERE address = ?", (rri,))
                current_data = cursor.fetchone()
                current_rowid, current_symbol, current_name, current_decimals, current_icon_url, current_description, current_info_url, current_order_index = (None, None, None, None, None, None, None, None) if not current_data else current_data

                if symbol is not None and (current_symbol is None or current_symbol == ""):
                    final_update_fields.append("symbol = ?")
                    final_params.append(symbol)
                if name is not None and (current_name is None or current_name == ""):
                    final_update_fields.append("name = ?")
                    final_params.append(name)
                if decimals is not None and current_decimals is None: 
                    final_update_fields.append("divisibility = ?")
                    final_params.append(decimals)
                # Update icon_url if we fetched one from Gateway and current is empty
                if icon_url is not None and (current_icon_url is None or current_icon_url == ""):
                    final_update_fields.append("icon_url = ?")
                    final_params.append(icon_url)
                if description is not None and (current_description is None or current_description == ""):
                    final_update_fields.append("description = ?")
                    final_params.append(description)
                if info_url is not None and (current_info_url is None or current_info_url == ""):
                    final_update_fields.append("info_url = ?")
                    final_params.append(info_url)
                # Set order_index to rowid if not already set (for consistent icon naming)
                if current_order_index is None and current_rowid is not None:
                    final_update_fields.append("order_index = ?")
                    final_params.append(current_rowid)
                
                # Price/metadata fields are updated by QtTokenUpdaterService
                # Only basic fields updated here when token is discovered

                if final_update_fields:
                    query = f"UPDATE tokens SET {', '.join(final_update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE address = ?"
                    final_params.append(rri)
                    
                    # Retry logic for UPDATE
                    for attempt in range(max_retries):
                        try:
                            cursor.execute(query, tuple(final_params))
                            self._conn.commit()
                            logger.debug(f"Updated token {rri} with Gateway metadata.")
                            break
                        except sqlite3.OperationalError as e:
                            if "database is locked" in str(e) and attempt < max_retries - 1:
                                import time
                                logger.warning(f"Database locked on UPDATE, retrying in {retry_delay}s")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                raise
                return True # Token exists

            # Token does not exist, insert with all available info
            insert_symbol = symbol if symbol is not None else ""
            insert_name = name if name is not None else ""
            insert_decimals = decimals if decimals is not None else 18 # Default to 18 if not provided
            
            # Insert with basic metadata + icon_url from Gateway
            # QtTokenUpdaterService will add prices/extended metadata on next run
            # Retry logic for INSERT
            for attempt in range(max_retries):
                try:
                    cursor.execute(
                        "INSERT INTO tokens (address, symbol, name, divisibility, icon_url, description, info_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                        (rri, insert_symbol, insert_name, insert_decimals, icon_url, description, info_url)
                    )
                    
                    # Get the rowid of the newly inserted token
                    new_rowid = cursor.lastrowid
                    
                    # Set order_index to rowid for consistent icon naming
                    # This ensures tokens not in Astrolescent still get proper icon filenames
                    cursor.execute(
                        "UPDATE tokens SET order_index = ? WHERE rowid = ?",
                        (new_rowid, new_rowid)
                    )
                    
                    logger.info(f"Inserted new token {rri}: {insert_symbol} - {insert_name}, order_index={new_rowid}, icon_url={icon_url is not None}")
                    
                    self._conn.commit()
                    break
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        import time
                        logger.warning(f"Database locked on INSERT, retrying in {retry_delay}s")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            return True
        except sqlite3.Error as e:
            logger.error(f"Error ensuring token {rri} exists: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_tradeable_tokens(self) -> List[Dict[str, Any]]:
        """
        Get tokens that are considered tradeable (e.g., volume_7d_usd >= 50000)
        and have a valid icon_url. These will be paired with XRD.
        """
        sql = """
            SELECT address, symbol, name, icon_url, icon_local_path 
            FROM tokens 
            WHERE volume_7d >= 50000 
              AND icon_url IS NOT NULL 
              AND icon_url != '' 
              AND symbol != 'XRD'
            ORDER BY volume_7d DESC NULLS LAST, symbol ASC
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            tokens = [
                {"address": row[0], "symbol": row[1], "name": row[2], "icon_url": row[3], "icon_local_path": row[4]}
                for row in rows
            ]
            logger.info(f"Found {len(tokens)} tokens with volume_7d >= 50000 and an icon_url to suggest as tradeable.")
            return tokens
        except sqlite3.Error as e:
            logger.error(f"Database error in get_tradeable_tokens: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()

    def get_all_tokens_for_selection(self) -> List[Dict[str, Any]]:
        """
        Get all tokens from database for user selection.
        Returns tokens sorted by symbol alphabetically.
        """
        sql = """
            SELECT address, symbol, name, icon_url, icon_local_path, token_price_usd
            FROM tokens 
            WHERE symbol IS NOT NULL 
              AND symbol != ''
            ORDER BY symbol ASC
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            tokens = [
                {
                    "address": row[0], 
                    "symbol": row[1], 
                    "name": row[2], 
                    "icon_url": row[3], 
                    "icon_local_path": row[4],
                    "price_usd": row[5]
                }
                for row in rows
            ]
            logger.info(f"Found {len(tokens)} tokens for selection dialog.")
            return tokens
        except sqlite3.Error as e:
            logger.error(f"Database error in get_all_tokens_for_selection: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()

    def get_token_by_address(self, address: str) -> Optional[Dict[str, any]]:
        """Get a single token by its address (RRI)."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM tokens WHERE address = ?", (address,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting token by address {address}: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()

    def get_token_by_symbol(self, symbol: str) -> Optional[dict]:
        """Retrieves a token's details by its symbol.

        Args:
            symbol: The token symbol (e.g., "XRD", "CAVIAR").

        Returns:
            A dictionary containing token details (address, symbol, name, divisibility)
            or None if not found or an error occurs.
        """
        query = "SELECT address, symbol, name, divisibility, icon_url, icon_local_path FROM tokens WHERE TRIM(UPPER(symbol)) = TRIM(UPPER(?));"
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, (symbol,))
            row = cursor.fetchone()
            if row:
                return {
                    "address": row[0],
                    "symbol": row[1],
                    "name": row[2],
                    "divisibility": row[3],
                    "icon_url": row[4],
                    "icon_local_path": row[5]
            }
            logger.debug(f"Token with symbol '{symbol}' not found.")
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error in get_token_by_symbol for symbol {symbol}: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()

    def associate_token_with_wallet(self, token_address: str, wallet_id: int) -> bool:
        """Associate a token with a wallet."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            # Check if token is already associated with this wallet
            cursor.execute(
                """SELECT COUNT(*) FROM wallet_tokens 
                WHERE token_address = ? AND wallet_id = ?""",
                (token_address, wallet_id)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                logger.debug(f"Token {token_address} already associated with wallet {wallet_id}.")
                return True

            # Associate token with wallet
            cursor.execute(
                """INSERT INTO wallet_tokens (token_address, wallet_id)
                VALUES (?, ?)""",
                (token_address, wallet_id)
            )
            self._conn.commit()
            logger.info(f"Successfully associated token {token_address} with wallet {wallet_id}.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error associating token {token_address} with wallet {wallet_id}: {e}", exc_info=True)
            if self._conn:
                self._conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_wallet_tokens(self, wallet_id: int) -> List[Dict[str, any]]:
        """Get all tokens associated with a wallet."""
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT t.* FROM tokens t
                JOIN wallet_tokens wt ON t.address = wt.token_address
                WHERE wt.wallet_id = ?
                ORDER BY t.symbol ASC""",
                (wallet_id,)
            )
            rows = cursor.fetchall()
            tokens = []
            if rows:
                columns = [description[0] for description in cursor.description]
                for row in rows:
                    tokens.append(dict(zip(columns, row)))
            return tokens
        except sqlite3.Error as e:
            logger.error(f"Error getting wallet {wallet_id} tokens: {e}", exc_info=True)
            # No rollback needed for a SELECT query
            return []
        finally:
            if cursor:
                cursor.close()

    def get_token_icon_path(self, token_address: str) -> Optional[str]:
        """Get the local icon path for a token if it exists."""
        try:
            from pathlib import Path
            from config.paths import USER_DATA_DIR
            
            icon_dir = USER_DATA_DIR / 'images' / 'icons'
        
            # Check for cached icon in images/icons folder
            if token_address:
                # Try different icon formats
                for ext in ['.png', '.jpeg', '.jpg', '.webp', '.gif']:
                    icon_path = icon_dir / f"{token_address}{ext}"
                    if icon_path.exists():
                        return (Path('images') / 'icons' / f"{token_address}{ext}").as_posix()
                    
                # Try using symbol as filename
                cursor = self._conn.cursor()
                cursor.execute("SELECT symbol FROM tokens WHERE address = ?", (token_address,))
                row = cursor.fetchone()
                if row and row[0]:
                    symbol = row[0]
                    for ext in ['.png', '.jpeg', '.jpg', '.webp', '.gif']:
                        icon_path = icon_dir / f"{symbol}{ext}"
                        if icon_path.exists():
                            return (Path('images') / 'icons' / f"{symbol}{ext}").as_posix()
        
            return None
        except Exception as e:
            logger.error(f"Error getting token icon path: {e}")
            return None