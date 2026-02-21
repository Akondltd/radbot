import sqlite3
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PoolManager:
    """Manages Ociswap pool data from the database."""
    
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
    
    def search_pools_for_pair(self, token_a_address: str, token_b_address: str) -> List[Dict]:
        """
        Search for all Ociswap pools containing both tokens (in either order).
        Returns pools sorted by liquidity (highest first).
        
        Args:
            token_a_address: First token address
            token_b_address: Second token address
            
        Returns:
            List of pool dictionaries with pool info and token symbols
        """
        cursor = None
        try:
            cursor = self._conn.cursor()
            
            # Query pools where tokens match in either order
            cursor.execute("""
                SELECT 
                    p.pool_address,
                    p.token_a_address,
                    p.token_b_address,
                    p.liquidity_usd,
                    p.last_updated,
                    ta.symbol AS token_a_symbol,
                    ta.name AS token_a_name,
                    ta.icon_url AS token_a_icon_url,
                    tb.symbol AS token_b_symbol,
                    tb.name AS token_b_name,
                    tb.icon_url AS token_b_icon_url
                FROM ociswap_pools p
                LEFT JOIN tokens ta ON p.token_a_address = ta.address
                LEFT JOIN tokens tb ON p.token_b_address = tb.address
                WHERE 
                    (p.token_a_address = ? AND p.token_b_address = ?)
                    OR (p.token_a_address = ? AND p.token_b_address = ?)
                ORDER BY p.liquidity_usd DESC NULLS LAST
            """, (token_a_address, token_b_address, token_b_address, token_a_address))
            
            rows = cursor.fetchall()
            pools = []
            
            for row in rows:
                pool = {
                    'pool_address': row[0],
                    'token_a_address': row[1],
                    'token_b_address': row[2],
                    'liquidity_usd': row[3],
                    'last_updated': row[4],
                    'token_a_symbol': row[5] or 'Unknown',
                    'token_a_name': row[6] or 'Unknown',
                    'token_a_icon_url': row[7],
                    'token_b_symbol': row[8] or 'Unknown',
                    'token_b_name': row[9] or 'Unknown',
                    'token_b_icon_url': row[10]
                }
                pools.append(pool)
            
            logger.info(f"Found {len(pools)} pools for pair {token_a_address[:8]}.../{token_b_address[:8]}...")
            return pools
            
        except sqlite3.Error as e:
            logger.error(f"Error searching pools for pair: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
    
    def get_highest_liquidity_pool(self, token_a_address: str, token_b_address: str) -> Optional[Dict]:
        """
        Get the pool with highest liquidity for a given token pair.
        
        Args:
            token_a_address: First token address
            token_b_address: Second token address
            
        Returns:
            Pool dictionary or None if no pools found
        """
        pools = self.search_pools_for_pair(token_a_address, token_b_address)
        return pools[0] if pools else None
