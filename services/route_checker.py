"""
Route Checker Service - Validates trading routes via Astrolescent
Checks if a token pair can be traded even without direct Ociswap pool
"""
import requests
import logging
from decimal import Decimal
from typing import Dict, Optional

from config.fee_config import get_fee_percentage, get_fee_component_address
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)

ASTRO_API_URL = "https://api.astrolescent.com/partner/akond/swap"
FEE_PERCENTAGE = get_fee_percentage()
FEE_COMPONENT_ADDRESS = get_fee_component_address()
MOCK_TRADE_USD = 500  # Standard test amount


class RouteChecker:
    """Service to check if Astrolescent can route between two tokens."""
    
    def __init__(self, token_manager, wallet_address: str = None):
        """
        Initialize route checker.
        
        Args:
            token_manager: TokenManager instance to get token prices
            wallet_address: Wallet address for API calls (optional for route checking)
        """
        self.token_manager = token_manager
        self.wallet_address = wallet_address or "account_rdx12yy8n09a0w907vrjyj4hws2yptrm3rdjv84l9sr24e3w7pk7nuxst8"  # Dummy for checking
        
    def check_route_exists(self, token_a_address: str, token_b_address: str) -> Dict:
        """
        Check if Astrolescent can route between two tokens.
        Uses a $500 mock trade to test viability.
        
        Args:
            token_a_address: First token address
            token_b_address: Second token address
            
        Returns:
            {
                'route_exists': bool,
                'price_impact': float,  # Percentage
                'output_amount': float,
                'feasible': bool,  # True if impact <= 5%
                'error': str  # If route_exists is False
            }
        """
        try:
            # Get token A details
            token_a = self.token_manager.get_token_by_address(token_a_address)
            if not token_a:
                logger.error(f"Token A not found: {token_a_address}")
                return {
                    'route_exists': False,
                    'error': 'Token A not found in database'
                }
            
            # Calculate mock trade amount (convert $500 to token amount)
            price_usd = token_a.get('token_price_usd', 0)
            if price_usd <= 0:
                logger.warning(f"Token A has no USD price: {token_a.get('symbol')}")
                # Use 1 token as fallback
                input_amount = 1.0
            else:
                input_amount = MOCK_TRADE_USD / price_usd
            
            token_b = self.token_manager.get_token_by_address(token_b_address)
            token_b_symbol = token_b.get('symbol', 'Unknown') if token_b else 'Unknown'
            
            logger.info(f"Checking Astrolescent route: {token_a.get('symbol')} -> {token_b_symbol} (amount: {input_amount:.4f})")
            
            # Call Astrolescent API
            api_params = {
                'inputToken': token_a_address,
                'outputToken': token_b_address,
                'inputAmount': float(input_amount),
                'fromAddress': self.wallet_address,
                'feeComponent': FEE_COMPONENT_ADDRESS,
                'fee': float(FEE_PERCENTAGE)
            }
            
            # Log the actual API call for debugging
            logger.debug(f"Astrolescent API params: {api_params}")
            
            api_tracker.record('astrolescent')
            response = requests.post(ASTRO_API_URL, json=api_params, timeout=30)
            response.raise_for_status()
            swap_data = response.json()
            
            logger.debug(f"Astrolescent API response received: {list(swap_data.keys())}")
            
            # Check if we got a valid response
            if not swap_data or 'manifest' not in swap_data:
                logger.warning(f"Astrolescent returned no manifest for {token_a.get('symbol')} pair")
                return {
                    'route_exists': False,
                    'error': 'No route found'
                }
            
            # Extract price impact
            price_impact = float(swap_data.get('priceImpact', 101))
            output_amount = float(swap_data.get('outputAmount', 0))
            
            # Determine feasibility (2.5% threshold for "feasible")
            feasible = price_impact <= 2.5
            
            logger.info(f"Route found! Price impact: {price_impact:.2f}%, Feasible: {feasible}")
            
            return {
                'route_exists': True,
                'price_impact': price_impact,
                'output_amount': output_amount,
                'feasible': feasible,
                'error': None
            }
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Astrolescent API timeout after 30 seconds: {e}")
            logger.error(f"Request was for: {token_a.get('symbol')} -> {token_b_symbol}, amount: {input_amount}")
            return {
                'route_exists': False,
                'error': 'API timeout - the route may be too complex or API is busy'
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"Astrolescent API HTTP error: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:500]}")  # First 500 chars
                
                # Check if it's a "no route" error vs other errors
                if e.response.status_code == 400:
                    return {
                        'route_exists': False,
                        'error': 'No viable route'
                    }
                return {
                    'route_exists': False,
                    'error': f'API error: {e.response.status_code}'
                }
            return {
                'route_exists': False,
                'error': 'API error: unknown'
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Astrolescent API connection error: {e}")
            return {
                'route_exists': False,
                'error': 'Connection error - check network'
            }
        except Exception as e:
            logger.error(f"Error checking route: {e}", exc_info=True)
            return {
                'route_exists': False,
                'error': f'Unexpected error: {str(e)}'
            }
