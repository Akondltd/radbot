"""
Astrolescent Price Service - Fetches and caches token prices from Astrolescent API
Uses the /prices endpoint which provides liquidity-weighted averages across DefiPlaza, Ociswap, and CaviarNine
"""
import requests
import logging
from typing import Dict, Optional
from decimal import Decimal
import time
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)

class AstrolescentPriceService:
    """
    Service to fetch and cache token prices from Astrolescent /prices endpoint.
    Prices are liquidity-weighted averages updated every 10 minutes by Astrolescent.
    """
    
    PRICES_ENDPOINT = "https://api.astrolescent.com/prices"
    CACHE_DURATION_SECONDS = 600  # 10 minutes (matches Astrolescent update frequency)
    
    def __init__(self):
        self._price_cache: Dict[str, Dict] = {}
        self._last_fetch_time: float = 0
        self._fetch_in_progress = False
    
    def get_all_prices(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Get all token prices from Astrolescent.
        Uses cached data if fresh (< 10 minutes old), otherwise fetches new data.
        
        Args:
            force_refresh: If True, bypasses cache and forces new API call
            
        Returns:
            Dictionary mapping token address to price data:
            {
                "resource_rdx1...": {
                    "address": "resource_rdx1...",
                    "symbol": "HUG",
                    "name": "HUG",
                    "tokenPriceXRD": 0.000404,
                    "tokenPriceUSD": 0.0038,
                    "divisibility": 18,
                    ...
                }
            }
        """
        current_time = time.time()
        cache_age = current_time - self._last_fetch_time
        
        # Return cached data if fresh
        if not force_refresh and self._price_cache and cache_age < self.CACHE_DURATION_SECONDS:
            logger.debug(f"Using cached prices (age: {cache_age:.1f}s)")
            return self._price_cache
        
        # Prevent concurrent fetches
        if self._fetch_in_progress:
            logger.debug("Price fetch already in progress, returning cached data")
            return self._price_cache
        
        try:
            self._fetch_in_progress = True
            logger.info(f"Fetching fresh prices from Astrolescent (cache age: {cache_age:.1f}s)")
            
            api_tracker.record('astrolescent')
            response = requests.get(self.PRICES_ENDPOINT, timeout=30)
            response.raise_for_status()
            
            prices_data = response.json()
            
            if not isinstance(prices_data, dict):
                logger.error(f"Unexpected response format from prices endpoint: {type(prices_data)}")
                return self._price_cache  # Return stale cache on error
            
            # Update cache
            self._price_cache = prices_data
            self._last_fetch_time = current_time
            
            logger.info(f"Successfully fetched {len(prices_data)} token prices from Astrolescent")
            return self._price_cache
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching prices from Astrolescent: {e}")
            return self._price_cache  # Return stale cache on error
            
        finally:
            self._fetch_in_progress = False
    
    def get_token_price(self, token_address: str) -> Optional[Dict]:
        """
        Get price data for a specific token.
        
        Args:
            token_address: Token resource address (e.g., "resource_rdx1...")
            
        Returns:
            Price data dictionary or None if token not found
        """
        prices = self.get_all_prices()
        return prices.get(token_address)
    
    def get_token_price_xrd(self, token_address: str) -> Optional[Decimal]:
        """
        Get token price in XRD.
        
        Args:
            token_address: Token resource address
            
        Returns:
            Price in XRD as Decimal, or None if token not found
        """
        token_data = self.get_token_price(token_address)
        if token_data and 'tokenPriceXRD' in token_data:
            return Decimal(str(token_data['tokenPriceXRD']))
        return None
    
    def get_token_price_usd(self, token_address: str) -> Optional[Decimal]:
        """
        Get token price in USD.
        
        Args:
            token_address: Token resource address
            
        Returns:
            Price in USD as Decimal, or None if token not found
        """
        token_data = self.get_token_price(token_address)
        if token_data and 'tokenPriceUSD' in token_data:
            return Decimal(str(token_data['tokenPriceUSD']))
        return None
    
    def get_pair_price(self, base_token: str, quote_token: str) -> Optional[Decimal]:
        """
        Calculate price of base token in terms of quote token.
        Same logic as exotic pairs.
        
        Args:
            base_token: Base token address
            quote_token: Quote token address
            
        Returns:
            Price as Decimal (quote per base), or None if either token not found
        """
        base_price_xrd = self.get_token_price_xrd(base_token)
        quote_price_xrd = self.get_token_price_xrd(quote_token)
        
        if base_price_xrd is None or quote_price_xrd is None:
            return None
        
        if base_price_xrd == 0:
            logger.warning(f"Base token {base_token} has zero XRD price")
            return None
        
        # Price = quote_per_base = base_value_in_xrd / quote_value_in_xrd
        # Example: HUG/XRD where HUG=0.0004 XRD, XRD=1 XRD
        # Price = 0.0004 / 1 = 0.0004 XRD per HUG
        return base_price_xrd / quote_price_xrd
    
    def clear_cache(self):
        """Force cache to be refreshed on next request."""
        self._last_fetch_time = 0
        logger.debug("Price cache cleared")


# Global singleton instance
_price_service_instance = None

def get_price_service() -> AstrolescentPriceService:
    """Get the global price service instance."""
    global _price_service_instance
    if _price_service_instance is None:
        _price_service_instance = AstrolescentPriceService()
    return _price_service_instance
