import requests
import sqlite3
from decimal import Decimal
from typing import List, Optional, Tuple
import time
import os

from models.data_models import Candle
from utils.api_tracker import api_tracker

class DataSource:
    """Handles fetching market data from Ociswap and syncing it with the local database."""

    def __init__(self, db_path=None):
        """
        Initializes the data source, connects to the database, and ensures
        necessary tables are created.
        """
        self.api_base_url = "https://api.ociswap.com"
        if db_path is None:
            from config.paths import DATABASE_PATH, ensure_dirs
            ensure_dirs()
            self.db_path = str(DATABASE_PATH)
        else:
            self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        """Returns a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        """Creates/updates the necessary tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ociswap_pools (
                    pool_address TEXT PRIMARY KEY,
                    token_a_address TEXT NOT NULL,
                    token_b_address TEXT NOT NULL,
                    last_updated INTEGER
                )
            ''')
            # Add liquidity column if it doesn't exist, for backwards compatibility
            try:
                cursor.execute('ALTER TABLE ociswap_pools ADD COLUMN liquidity_usd REAL')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' not in str(e):
                    raise # Re-raise if it's not the expected error
            
            # Create price_history table with user-friendly pricing columns
            cursor.execute('''
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
                    UNIQUE (exchange, pair, timestamp)
                )
            ''')
            
            # Add user-friendly pricing columns for GUI display
            try:
                cursor.execute('ALTER TABLE price_history ADD COLUMN base_token_usd_price REAL')
                cursor.execute('ALTER TABLE price_history ADD COLUMN quote_token_usd_price REAL')
                cursor.execute('ALTER TABLE price_history ADD COLUMN user_friendly_price REAL')  # e.g., 0.0082 xUSDC per XRD
                cursor.execute('ALTER TABLE price_history ADD COLUMN base_token_symbol TEXT')
                cursor.execute('ALTER TABLE price_history ADD COLUMN quote_token_symbol TEXT')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' not in str(e):
                    raise # Re-raise if it's not the expected error
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_pair_timestamp ON price_history (pair, timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_exchange_pair_timestamp ON price_history (exchange, pair, timestamp DESC)')
            
            conn.commit()

    def sync_ociswap_pools(self):
        """
        Fetches all liquidity pools from the Ociswap API and caches them in the
        local ociswap_pools table. This should be run periodically to discover new pools.
        """
        print("Starting Ociswap pool synchronization...")
        try:
            # Ociswap API uses cursor-based pagination
            cursor_val = None
            limit = 100  # Fetch in batches of 100
            pools_fetched = 0

            with self._get_connection() as conn:
                db_cursor = conn.cursor()
                while True:
                    url = f"{self.api_base_url}/pools"
                    params = {'limit': limit}
                    if cursor_val:
                        params['cursor'] = cursor_val

                    api_tracker.record('ociswap')
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    response_data = response.json()
                    pools_data = response_data.get('data', [])

                    if not pools_data:
                        break  # No more pools to fetch

                    pools_to_insert = []
                    for pool in pools_data:
                        # In the general /pools endpoint, the tokens are in x and y
                        token_a = pool.get('x', {})
                        token_b = pool.get('y', {})
                        
                        if not all([pool.get('address'), token_a.get('token'), token_b.get('token')]):
                            continue
                        
                        pools_to_insert.append((
                            pool['address'],
                            token_a['token']['address'],
                            token_b['token']['address'],
                            float(pool.get('liquidity_usd', '0')), # Store liquidity
                            int(time.time())
                        ))
                    
                    if pools_to_insert:
                        db_cursor.executemany('''
                            INSERT OR REPLACE INTO ociswap_pools (pool_address, token_a_address, token_b_address, liquidity_usd, last_updated)
                            VALUES (?, ?, ?, ?, ?)
                        ''', pools_to_insert)
                        conn.commit()
                        pools_fetched += len(pools_to_insert)

                    cursor_val = response_data.get('next_cursor')
                    if not cursor_val:
                        break # End of data

                    time.sleep(1.00) # Respect API rate limits
            
            print(f"Successfully synchronized {pools_fetched} pools from Ociswap.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching pools from Ociswap API: {e}")
        except sqlite3.Error as e:
            print(f"Database error during pool sync: {e}")

    def _find_pool_for_pair(self, cursor, token_a: str, token_b: str) -> Optional[str]:
        """
        Finds the pool address for a given token pair from the local cache,
        selecting the one with the highest liquidity.
        """
        cursor.execute('''
            SELECT pool_address FROM ociswap_pools
            WHERE (token_a_address = ? AND token_b_address = ?)
               OR (token_a_address = ? AND token_b_address = ?)
            ORDER BY liquidity_usd DESC
            LIMIT 1
        ''', (token_a, token_b, token_b, token_a))
        result = cursor.fetchone()
        return result[0] if result else None

    def update_price_history_from_ociswap(self):
        """
        Iterates through user-selected trade pairs, finds their corresponding Ociswap pool
        with the highest liquidity, and fetches the latest price data,
        storing it in the price_history table.
        """
        print("Starting price history update from Ociswap for selected pairs...")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get only the trade pairs the user has selected
            try:
                # Join selected_pairs with trade_pairs to get the token addresses
                cursor.execute("""
                    SELECT tp.base_token, tp.quote_token
                    FROM trade_pairs tp
                    JOIN selected_pairs sp ON tp.trade_pair_id = sp.trade_pair_id
                """)
                trade_pairs = cursor.fetchall()
            except sqlite3.OperationalError as e:
                print(f"Could not query selected pairs (check 'selected_pairs' table exists?). Skipping update. Error: {e}")
                return

            if not trade_pairs:
                print("No pairs selected for tracking. Skipping price history update.")
                return

            print(f"Found {len(trade_pairs)} selected pairs. Checking for price history updates...")
            
            for idx, (token_a_address, token_b_address) in enumerate(trade_pairs):
                pair_name = f"{token_a_address}/{token_b_address}"
                pool_address = None # Ensure pool_address is defined
                
                # Get trade_pair_id for this pair
                cursor.execute("""
                    SELECT trade_pair_id
                    FROM trade_pairs
                    WHERE (base_token = ? AND quote_token = ?)
                       OR (base_token = ? AND quote_token = ?)
                    LIMIT 1
                """, (token_a_address, token_b_address, token_b_address, token_a_address))
                pair_id_result = cursor.fetchone()
                pair_id = pair_id_result[0] if pair_id_result else None
                
                try:
                    pool_address = self._find_pool_for_pair(cursor, token_a_address, token_b_address)
                    
                    if not pool_address:
                        # No Ociswap pool - use Astrolescent
                        print(f"No Ociswap pool for {pair_name}, checking Astrolescent...")
                        if pair_id:
                            time.sleep(1.00) # Respect API rate limits
                            self._update_astrolescent_price(cursor, conn, pair_id, token_a_address, token_b_address)
                        else:
                            print(f"  Could not find pair_id for {pair_name}. Skipping.")
                        continue

                    time.sleep(1.00) # Respect API rate limits

                    # Fetch current pool data instead of history
                    url = f"{self.api_base_url}/pools/{pool_address}"
                    api_tracker.record('ociswap')
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    pool_data = response.json()

                    # Update USD prices for both tokens in the pair
                    try:
                        # Extract USD prices for both tokens
                        x_token_address = pool_data.get('x', {}).get('token', {}).get('address')
                        y_token_address = pool_data.get('y', {}).get('token', {}).get('address')
                        x_usd_price = Decimal(pool_data.get('x', {}).get('price', {}).get('usd', {}).get('now', '0'))
                        y_usd_price = Decimal(pool_data.get('y', {}).get('price', {}).get('usd', {}).get('now', '0'))
                        
                        # Update tokens table with current USD prices
                        if x_token_address and x_usd_price > 0:
                            cursor.execute(
                                "UPDATE tokens SET token_price_usd = ? WHERE address = ?",
                                (float(x_usd_price), x_token_address)
                            )
                            print(f"Updated USD price for {x_token_address}: ${x_usd_price}")
                        
                        if y_token_address and y_usd_price > 0:
                            cursor.execute(
                                "UPDATE tokens SET token_price_usd = ? WHERE address = ?",
                                (float(y_usd_price), y_token_address)
                            )
                            print(f"Updated USD price for {y_token_address}: ${y_usd_price}")
                            
                    except Exception as e:
                        print(f"Error updating token USD prices for pair {pair_name}: {e}")

                    # Determine which token in the response is our token_a (base token)
                    if pool_data.get('x', {}).get('token', {}).get('address') == token_a_address:
                        # token_a is in 'x' position (base token)
                        base_token_symbol = pool_data['x']['token'].get('symbol', 'Unknown')
                        quote_token_symbol = pool_data['y']['token'].get('symbol', 'Unknown')
                        base_usd_price = Decimal(pool_data['x']['price']['usd']['now'])
                        quote_usd_price = Decimal(pool_data['y']['price']['usd']['now'])
                        token_volume = Decimal(pool_data['x']['volume'].get('24h', '0'))
                        
                        # Special case: if base token IS XRD, x.price.xrd.now is always 1 (useless)
                        # Instead, use the inverse of y.price.xrd.now to get quote per base
                        if base_token_symbol == 'XRD':
                            y_price_xrd = Decimal(pool_data['y']['price']['xrd']['now'])
                            if y_price_xrd > 0:
                                price = Decimal('1') / y_price_xrd  # quote per XRD
                                print(f"DEBUG - Base is XRD, using 1/y.price.xrd.now = 1/{y_price_xrd} = {price} for {pair_name}")
                            else:
                                price = Decimal('1')
                                print(f"WARNING - y.price.xrd.now is 0 for {pair_name}, using price=1")
                        else:
                            # Normal case: base is not XRD, use x.price.xrd.now
                            price = Decimal(pool_data['x']['price']['xrd']['now'])
                            print(f"DEBUG - Using x.price.xrd.now={price} for {pair_name}")
                        
                    elif pool_data.get('y', {}).get('token', {}).get('address') == token_a_address:
                        # token_a is in 'y' position (base token)
                        base_token_symbol = pool_data['y']['token'].get('symbol', 'Unknown')
                        quote_token_symbol = pool_data['x']['token'].get('symbol', 'Unknown')
                        base_usd_price = Decimal(pool_data['y']['price']['usd']['now'])
                        quote_usd_price = Decimal(pool_data['x']['price']['usd']['now'])
                        token_volume = Decimal(pool_data['y']['volume'].get('24h', '0'))
                        
                        # Special case: if base token IS XRD, y.price.xrd.now is always 1 (useless)
                        # Instead, use the inverse of x.price.xrd.now to get quote per base
                        if base_token_symbol == 'XRD':
                            x_price_xrd = Decimal(pool_data['x']['price']['xrd']['now'])
                            if x_price_xrd > 0:
                                price = Decimal('1') / x_price_xrd  # quote per XRD
                                print(f"DEBUG - Base is XRD, using 1/x.price.xrd.now = 1/{x_price_xrd} = {price} for {pair_name}")
                            else:
                                price = Decimal('1')
                                print(f"WARNING - x.price.xrd.now is 0 for {pair_name}, using price=1")
                        else:
                            # Normal case: base is not XRD, use y.price.xrd.now
                            price = Decimal(pool_data['y']['price']['xrd']['now'])
                            print(f"DEBUG - Using y.price.xrd.now={price} for {pair_name}")
                        
                    else:
                        print(f"Could not match tokens for pair {pair_name} in pool {pool_address}. Skipping.")
                        continue

                    # Get USD volume for the pair
                    volume_1h = Decimal(pool_data.get('volume', {}).get('usd', {}).get('1h', '0'))
                    volume_24h = Decimal(pool_data.get('volume', {}).get('usd', {}).get('24h', '0'))
                    
                    # Update ociswap_pools table with 24h volume
                    try:
                        cursor.execute(
                            "UPDATE ociswap_pools SET volume_24h_usd = ?, last_updated = ? WHERE pool_address = ?",
                            (float(volume_24h), int(time.time()), pool_address)
                        )
                        print(f"Updated 24h volume for pool {pool_address}: ${volume_24h:,.2f}")
                    except Exception as e:
                        print(f"Error updating pool volume: {e}")
                    
                    # Calculate user-friendly price by putting MORE EXPENSIVE token in denominator
                    # This ensures we always get decimal format (< 1 for most pairs)
                    # OHLC candles will be stored in this format
                    if base_usd_price > 0 and quote_usd_price > 0:
                        if base_usd_price > quote_usd_price:
                            # Base is more expensive - put it in denominator (quote/base gives decimal)
                            user_friendly_price = quote_usd_price / base_usd_price
                        else:
                            # Quote is more expensive - put it in denominator (base/quote gives decimal)
                            user_friendly_price = base_usd_price / quote_usd_price
                    else:
                        user_friendly_price = Decimal('0')
                    
                    # Use user_friendly_price for OHLC storage (not XRD price)
                    close_price = user_friendly_price
                    
                    # Debug specific pool issue
                    if 'component_rdx1czy2naejcqx8gv46zdsex2syuxrs4jnqzug58e66zr8wglxzvu97qr' in pool_address:
                        print(f"*** DEBUG POOL {pool_address} ***")
                        print(f"  Base token: {base_token_symbol}, USD price: {base_usd_price}")
                        print(f"  Quote token: {quote_token_symbol}, USD price: {quote_usd_price}")
                        print(f"  Raw price from API: {price}")
                        print(f"  XRD price (close_price): {close_price}")
                        print(f"  User friendly price (quote/base): {user_friendly_price}")
                        print(f"  Inverted (base/quote): {1/user_friendly_price if user_friendly_price > 0 else 0}")

                    # Create a candle for the last completed 10-minute interval
                    now = int(time.time())
                    candle_timestamp = now - (now % 600)  # Round to 10-minute intervals (600 seconds)

                    # Check if we already have a candle for this timestamp
                    cursor.execute(
                        "SELECT close_price, timestamp FROM price_history WHERE pair = ? AND timestamp = ?",
                        (pool_address, candle_timestamp)
                    )
                    existing_candle = cursor.fetchone()
                    
                    if existing_candle:
                        # Update existing candle with fresh data if price changed
                        old_price = Decimal(existing_candle[0])
                        if abs(close_price - old_price) > Decimal('0.000001'):  # Price changed
                            print(f"Updating existing candle for {pool_address} at {candle_timestamp}")
                            print(f"  Old price: {old_price}, New price: {close_price}")
                            
                            # Get the open price from the existing candle
                            cursor.execute(
                                "SELECT open_price, high_price, low_price FROM price_history WHERE pair = ? AND timestamp = ?",
                                (pool_address, candle_timestamp)
                            )
                            candle_data = cursor.fetchone()
                            open_price = Decimal(candle_data[0])
                            existing_high = Decimal(candle_data[1])
                            existing_low = Decimal(candle_data[2])
                            
                            # Update high/low if needed
                            high_price = max(existing_high, close_price)
                            low_price = min(existing_low, close_price)
                            
                            cursor.execute('''
                                UPDATE price_history 
                                SET high_price = ?, low_price = ?, close_price = ?,
                                    volume = ?, base_token_usd_price = ?, quote_token_usd_price = ?,
                                    user_friendly_price = ?
                                WHERE pair = ? AND timestamp = ?
                            ''', (
                                str(high_price), str(low_price), str(close_price),
                                str(volume_1h), str(base_usd_price), str(quote_usd_price),
                                str(user_friendly_price), pool_address, candle_timestamp
                            ))
                            conn.commit()
                            print(f"  Updated candle: O={open_price}, H={high_price}, L={low_price}, C={close_price}")
                        else:
                            print(f"Candle for {pool_address} at {candle_timestamp} unchanged (price: {close_price})")
                        continue  # Move to next pair

                    # Get the last close price to use as the open for the new candle
                    cursor.execute(
                        "SELECT close_price FROM price_history WHERE pair = ? ORDER BY timestamp DESC LIMIT 1",
                        (pool_address,)
                    )
                    last_candle = cursor.fetchone()
                    open_price = Decimal(last_candle[0]) if last_candle else close_price

                    high_price = max(open_price, close_price)
                    low_price = min(open_price, close_price)

                    # No scaling factor needed anymore - prices are already in proper decimal format
                    # Convert Decimals to strings for sqlite compatibility
                    candle_to_insert = (
                        'ociswap',
                        pool_address,  # Use the pool_address, not the token address
                        candle_timestamp,
                        str(open_price),
                        str(high_price),
                        str(low_price),
                        str(close_price),
                        str(volume_1h),  # 1h volume for the candle
                        str(base_usd_price), # base_token_usd_price
                        str(quote_usd_price), # quote_token_usd_price
                        str(user_friendly_price), # user_friendly_price
                        base_token_symbol, # base_token_symbol
                        quote_token_symbol # quote_token_symbol
                    )

                    cursor.execute('''
                        INSERT INTO price_history (exchange, pair, timestamp, open_price, high_price, low_price, close_price, volume, base_token_usd_price, quote_token_usd_price, user_friendly_price, base_token_symbol, quote_token_symbol)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', candle_to_insert)
                    conn.commit()
                    print(f"Inserted NEW price candle for {pool_address} at timestamp {candle_timestamp}.")
                    print(f"  Candle data: O={open_price}, H={high_price}, L={low_price}, C={close_price}")
                    print(f"  Traditional price: {close_price} XRD per {quote_token_symbol}")
                    print(f"  User-friendly price: {user_friendly_price} {quote_token_symbol} per {base_token_symbol}")

                except requests.exceptions.RequestException as e:
                    print(f"Could not fetch data for {pair_name} (Pool: {pool_address}): {e}")
                except (KeyError, IndexError) as e:
                    print(f"Error parsing pool data response for {pair_name}: {e}")
                except sqlite3.Error as e:
                    print(f"Database error for pair {pair_name}: {e}")
        print("Finished updating price history.")

    def _update_astrolescent_price(self, cursor, conn, pair_id, base_token_address, quote_token_address):
        """
        Update price history for an Astrolescent pair by querying their API.
        Extracts volume from component Ociswap pools in the route.
        
        Args:
            cursor: Database cursor
            conn: Database connection  
            pair_id: trade_pair_id from database
            base_token_address: Base token address
            quote_token_address: Quote token address
        """
        try:
            # Get token details
            cursor.execute("SELECT symbol, token_price_usd FROM tokens WHERE address = ?", (base_token_address,))
            base_token_info = cursor.fetchone()
            cursor.execute("SELECT symbol, token_price_usd FROM tokens WHERE address = ?", (quote_token_address,))
            quote_token_info = cursor.fetchone()
            
            if not base_token_info or not quote_token_info:
                print(f"Missing token data for Astrolescent pair ID {pair_id}")
                return
            
            base_symbol, base_usd_price = base_token_info
            quote_symbol, quote_usd_price = quote_token_info
            
            print(f"Polling Astrolescent for {base_symbol}/{quote_symbol}...")
            
            # Calculate test amount ($100 worth or 1 token minimum)
            test_amount = 100.0 / float(base_usd_price) if base_usd_price and base_usd_price > 0 else 1.0
            
            # Query Astrolescent API
            api_tracker.record('astrolescent')
            astro_response = requests.post(
                "https://api.astrolescent.com/partner/akond/swap",
                json={
                    'inputToken': base_token_address,
                    'outputToken': quote_token_address,
                    'inputAmount': test_amount,
                    'fromAddress': 'account_rdx12yy8n09a0w907vrjyj4hws2yptrm3rdjv84l9sr24e3w7pk7nuxst8',
                    'feeComponent': 'component_rdx1czrwlclg9p5h4p50yhkfqhgn3uqsyfmup29xt2f20c5jsa55ef0xv4',
                    'fee': 0.001
                },
                timeout=30
            ).json()
            
            # Extract price from response
            output_amount = float(astro_response.get('outputTokens', 0))
            if output_amount <= 0:
                print(f"  Invalid output amount for {base_symbol}/{quote_symbol}")
                return
            
            current_price = Decimal(str(output_amount)) / Decimal(str(test_amount))
            
            # Extract volume from routes
            volume_24h = self._extract_volume_from_astrolescent_routes(cursor, astro_response)
            
            # Create unique pair identifier for Astrolescent
            astro_pair_id = f"astro_{pair_id}"
            
            # Create candle timestamp (10-minute intervals)
            now = int(time.time())
            candle_timestamp = now - (now % 600)
            
            # Check if candle already exists
            cursor.execute(
                "SELECT 1 FROM price_history WHERE pair = ? AND timestamp = ?",
                (astro_pair_id, candle_timestamp)
            )
            if cursor.fetchone():
                print(f"  Candle already exists for {base_symbol}/{quote_symbol} at {candle_timestamp}")
                return
            
            # Calculate user-friendly price by putting MORE EXPENSIVE token in denominator
            # This ensures we always get decimal format (< 1 for most pairs)
            base_usd_decimal = Decimal(str(base_usd_price)) if base_usd_price else Decimal('0')
            quote_usd_decimal = Decimal(str(quote_usd_price)) if quote_usd_price else Decimal('0')
            
            if base_usd_decimal > 0 and quote_usd_decimal > 0:
                if base_usd_decimal > quote_usd_decimal:
                    # Base is more expensive - put it in denominator (quote/base gives decimal)
                    user_friendly_price = quote_usd_decimal / base_usd_decimal
                else:
                    # Quote is more expensive - put it in denominator (base/quote gives decimal)
                    user_friendly_price = base_usd_decimal / quote_usd_decimal
            else:
                user_friendly_price = Decimal('0')
            
            # Get last close price for open (fallback to current user_friendly_price)
            cursor.execute(
                "SELECT close_price FROM price_history WHERE pair = ? ORDER BY timestamp DESC LIMIT 1",
                (astro_pair_id,)
            )
            last_candle = cursor.fetchone()
            open_price = Decimal(last_candle[0]) if last_candle else user_friendly_price
            
            # Use user_friendly_price for OHLC (not route-calculated price)
            close_price = user_friendly_price
            high_price = max(open_price, close_price)
            low_price = min(open_price, close_price)
            
            # Insert candle
            cursor.execute('''
                INSERT INTO price_history (
                    exchange, pair, timestamp,
                    open_price, high_price, low_price, close_price,
                    volume,
                    base_token_usd_price, quote_token_usd_price, user_friendly_price,
                    base_token_symbol, quote_token_symbol
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'astrolescent',
                astro_pair_id,
                candle_timestamp,
                str(open_price),
                str(high_price),
                str(low_price),
                str(close_price),
                str(volume_24h) if volume_24h else '0',
                str(base_usd_price),
                str(quote_usd_price),
                str(user_friendly_price),
                base_symbol,
                quote_symbol
            ))
            conn.commit()
            
            print(f"Inserted Astrolescent candle for {base_symbol}/{quote_symbol}")
            print(f"  Price: {close_price:.6f}, Volume: ${volume_24h:,.2f}" if volume_24h else f"  Price: {close_price:.6f}, Volume: N/A")
            
        except requests.exceptions.Timeout:
            print(f"  Astrolescent API timeout for pair ID {pair_id}")
        except requests.exceptions.RequestException as e:
            print(f"  Error querying Astrolescent for pair ID {pair_id}: {e}")
        except Exception as e:
            print(f"  Error updating Astrolescent price for pair ID {pair_id}: {e}")

    def _extract_volume_from_astrolescent_routes(self, cursor, astro_response):
        """
        Extract volume from Astrolescent route by querying component Ociswap pools.
        Uses conservative bottleneck approach (minimum volume).
        
        Returns:
            Float volume in USD, or None if unavailable
        """
        try:
            ociswap_pool_volumes = []
            
            for route in astro_response.get('routes', []):
                for pool in route.get('pools', []):
                    pool_type = pool.get('type', '')
                    
                    # Only query Ociswap pools (Simple and Precision)
                    if pool_type in ['OciSimple', 'OciPrecision']:
                        pool_address = pool.get('pool', '')
                        
                        if pool_address:
                            # Query our database for this pool's volume
                            cursor.execute("""
                                SELECT volume_24h_usd
                                FROM ociswap_pools
                                WHERE pool_address = ?
                            """, (pool_address,))
                            
                            result = cursor.fetchone()
                            if result and result[0]:
                                ociswap_pool_volumes.append(float(result[0]))
                                print(f"  Found Ociswap pool {pool_address[:20]}... with volume: ${result[0]:,.2f}")
            
            if not ociswap_pool_volumes:
                print("  No Ociswap pool volumes found in routes")
                return None
            
            # Use minimum volume (bottleneck principle - most conservative)
            min_volume = min(ociswap_pool_volumes)
            print(f"  Effective volume (bottleneck): ${min_volume:,.2f}")
            
            return min_volume
            
        except Exception as e:
            print(f"  Error extracting volume from routes: {e}")
            return None

    def get_historical_data(self, token_a_address: str, token_b_address: str, limit: int = 1000) -> List[Candle]:
        """Fetches historical price data for a given pair from the local database."""
        pair_name_v1 = f"{token_a_address}/{token_b_address}"
        pair_name_v2 = f"{token_b_address}/{token_a_address}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Query for both possible pair name combinations
                cursor.execute(f"""
                    SELECT timestamp, open_price, high_price, low_price, close_price, volume
                    FROM price_history
                    WHERE pair IN (?, ?)
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (pair_name_v1, pair_name_v2, limit))
                
                rows = cursor.fetchall()
                if not rows:
                    return []

                # The Candle model expects Decimal types, but sqlite returns float/int
                candles = [
                    Candle(
                        timestamp=row[0],
                        open=Decimal(str(row[1])),
                        high=Decimal(str(row[2])),
                        low=Decimal(str(row[3])),
                        close=Decimal(str(row[4])),
                        volume=Decimal(str(row[5]))
                    )
                    for row in reversed(rows) # Reverse to return in chronological order
                ]
                return candles

            except sqlite3.Error as e:
                print(f"Database error fetching historical data: {e}")
                return []
