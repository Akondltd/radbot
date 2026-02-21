"""
Trade Validation Service

Extracted from TradeMonitor to separate concerns.
Handles:
- Price impact validation
- Strategy threshold validation (Ping Pong)
- Kelly sizing application
- Token amount sanitization
- API interaction for validation

Dependencies are injected to maintain flexibility.
"""

import logging
import json
import requests
import time
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple

from constants import StrategyType
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)


class TradeValidator:
    """
    Validates trades for execution based on price impact, strategy thresholds, and Kelly sizing.
    
    This service is stateless and receives dependencies via injection.
    """
    
    def __init__(self, database, wallet, astro_api_url: str, fee_component: str, 
                 fee_percentage: Decimal, max_price_impact: Decimal):
        """
        Initialize TradeValidator with injected dependencies.
        
        Args:
            database: Database instance for trade pair and token lookups
            wallet: Wallet instance for address retrieval
            astro_api_url: Astrolescent API endpoint
            fee_component: Fee component address
            fee_percentage: Trading fee percentage
            max_price_impact: Maximum acceptable price impact percentage
        """
        self.db = database
        self.wallet = wallet
        self.astro_api_url = astro_api_url
        self.fee_component = fee_component
        self.fee_percentage = fee_percentage
        self.max_price_impact = max_price_impact
        
        # Rate limiting: Track last API call time to prevent spam
        self._last_api_call_time = 0
        self._min_api_call_interval = 0.5  # Minimum 500ms between API calls
        self._consecutive_failures = 0
        self._backoff_until = 0  # Timestamp when backoff period ends
    
    def validate_trades_for_execution(self, trades: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Validate multiple trades for execution.
        
        Checks:
        1. Price impact via Astrolescent API
        2. Strategy threshold validation (Ping Pong only)
        3. Kelly sizing application (AI Strategy only)
        
        Args:
            trades: List of trade dictionaries with signal="execute"
            
        Returns:
            List of tuples: (trade_dict, swap_data_dict) for validated trades
        """
        validated_trades = []
        
        for trade in trades:
            try:
                trade_id = trade['trade_id']
                logger.debug(f"Validating trade {trade_id} for execution...")
                
                # Check price impact using Astrolescent API
                is_valid, swap_data = self.validate_price_impact(trade)
                
                if is_valid:
                    validated_trades.append((trade, swap_data))
                    logger.info(f"Trade {trade_id} passed validation")
                else:
                    logger.warning(f"Trade {trade_id} failed validation (API error or price impact too high)")
                    
            except Exception as e:
                logger.error(f"Error validating trade {trade.get('trade_id', 'unknown')}: {e}", exc_info=True)
    
        return validated_trades
    
    def validate_price_impact(self, trade: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if trade has acceptable price impact and return manifest data if valid.
        
        Process:
        1. Apply Kelly sizing if AI Strategy
        2. Sanitize amount to token divisibility
        3. Call Astrolescent API for manifest
        4. Check price impact
        5. Re-validate actual price against strategy threshold
        
        Args:
            trade: Trade dictionary
            
        Returns:
            tuple: (is_valid, swap_data) where swap_data contains manifest if valid
        """
        try:
            # Debug: Log trade data structure
            logger.debug(f"Trade {trade['trade_id']} data: {trade}")
            
            # Get trade pair information
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            if not trade_pair:
                logger.error(f"Could not find trade pair for trade ID: {trade['trade_id']}")
                return False, None

            # Debug: Log trade pair data
            logger.debug(f"Trade {trade['trade_id']} pair data: {trade_pair}")

            # Determine tokens for the potential swap
            token_from_address = trade.get('trade_token_address') or trade['start_token_address']
            full_amount = Decimal(str(trade.get('trade_amount') or trade['start_amount']))
            
            # Apply Kelly criterion position sizing for AI Strategy
            amount_to_trade = self._apply_kelly_sizing(trade, full_amount)

            if token_from_address == trade_pair['base_token']:
                token_to_address = trade_pair['quote_token']
            else:
                token_to_address = trade_pair['base_token']

            # Validate all parameters before API call
            wallet_address = self.wallet.get_active_address()
            
            # Check for None/empty values
            if not token_from_address:
                logger.error(f"Trade {trade['trade_id']}: token_from_address is None/empty")
                return False, None
            if not token_to_address:
                logger.error(f"Trade {trade['trade_id']}: token_to_address is None/empty")
                return False, None
            if not wallet_address:
                logger.error(f"Trade {trade['trade_id']}: wallet_address is None/empty")
                return False, None
            if amount_to_trade <= 0:
                logger.error(f"Trade {trade['trade_id']}: invalid amount_to_trade: {amount_to_trade}")
                return False, None
            
            # Sanitize amount to token divisibility
            amount_to_trade_sanitized = self._sanitize_amount_to_divisibility(
                trade, token_from_address, amount_to_trade
            )

            # Call Astrolescent API to get manifest and check price impact
            api_params = {
                'inputToken': token_from_address,
                'outputToken': token_to_address,
                'inputAmount': float(amount_to_trade_sanitized),
                'fromAddress': wallet_address,
                'feeComponent': self.fee_component,
                'fee': float(self.fee_percentage)
            }

            # Debug log the parameters being sent
            logger.debug(f"Trade {trade['trade_id']} API params: {api_params}")

            # RATE LIMITING: Prevent API spam when server has issues
            current_time = time.time()
            
            # Check if we're in exponential backoff period
            if current_time < self._backoff_until:
                wait_time = self._backoff_until - current_time
                logger.warning(f"Trade {trade['trade_id']}: In backoff period, waiting {wait_time:.1f}s before API call")
                return False, None
            
            # Enforce minimum interval between API calls
            time_since_last_call = current_time - self._last_api_call_time
            if time_since_last_call < self._min_api_call_interval:
                sleep_time = self._min_api_call_interval - time_since_last_call
                logger.debug(f"Rate limiting: Sleeping {sleep_time:.3f}s before API call")
                time.sleep(sleep_time)
            
            self._last_api_call_time = time.time()
            
            # Make the API call with timeout
            api_tracker.record('astrolescent')
            response = requests.post(self.astro_api_url, json=api_params, timeout=30)
            response.raise_for_status()
            swap_data = response.json()
            
            # Reset failure counter on success
            self._consecutive_failures = 0

            # Check if we got a valid manifest
            if not swap_data or 'manifest' not in swap_data:
                logger.error(f"Trade {trade['trade_id']}: API returned no manifest")
                return False, None

            # Check price impact
            price_impact = Decimal(swap_data.get('priceImpact', '101'))
            logger.debug(f"Trade {trade['trade_id']} price impact: {price_impact}%")
        
            # Validate price impact
            is_valid = price_impact <= self.max_price_impact
            if not is_valid:
                logger.warning(f"Trade {trade['trade_id']}: Price impact {price_impact}% exceeds maximum {self.max_price_impact}%")
                return False, None

            logger.info(f"Trade {trade['trade_id']}: Price impact {price_impact}% is acceptable")
            
            # Re-validate actual execution price against strategy thresholds
            output_amount = swap_data.get('outputTokens')
            if output_amount:
                output_amount_decimal = Decimal(str(output_amount))
                raw_price = output_amount_decimal / amount_to_trade_sanitized
                
                # Convert raw_price (output/input) to quote_per_base format to match
                # the signal generator. raw_price direction depends on trade direction:
                #   Selling base: raw = quote_output / base_input = quote_per_base ✓
                #   Selling quote: raw = base_output / quote_input = base_per_quote → invert
                trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
                if token_from_address == trade_pair['base_token']:
                    # Selling base → raw is already quote_per_base
                    actual_pair_price = raw_price
                else:
                    # Selling quote → raw is base_per_quote, invert to quote_per_base
                    actual_pair_price = Decimal('1') / raw_price if raw_price > 0 else Decimal('0')
                
                logger.info(
                    f"Trade {trade['trade_id']}: DEX raw={raw_price:.6f} (output/input), "
                    f"pair_price={actual_pair_price:.6f} (q/b)"
                )
                
                # Verify this price still meets the strategy's threshold
                if not self.check_price_meets_strategy_threshold(
                    trade, actual_pair_price, token_from_address, token_to_address
                ):
                    logger.warning(
                        f"Trade {trade['trade_id']}: Rejected - actual DEX price does not meet strategy threshold"
                    )
                    return False, None
            else:
                logger.warning(f"Trade {trade['trade_id']}: No outputTokens in API response, skipping price re-validation")
            
            return True, swap_data

        except requests.exceptions.HTTPError as e:
            # Increment failure counter and apply exponential backoff
            self._consecutive_failures += 1
            backoff_seconds = min(2 ** self._consecutive_failures, 300)  # Max 5 minutes
            self._backoff_until = time.time() + backoff_seconds
            
            logger.error(f"API error validating price impact for trade {trade['trade_id']}: {e}")
            logger.error(f"API response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            logger.warning(f"Consecutive API failures: {self._consecutive_failures}. Backing off for {backoff_seconds}s")
            return False, None
        except requests.exceptions.RequestException as e:
            # Network/timeout errors also trigger backoff
            self._consecutive_failures += 1
            backoff_seconds = min(2 ** self._consecutive_failures, 300)  # Max 5 minutes
            self._backoff_until = time.time() + backoff_seconds
            
            logger.error(f"Network error validating price impact for trade {trade['trade_id']}: {e}")
            logger.warning(f"Consecutive API failures: {self._consecutive_failures}. Backing off for {backoff_seconds}s")
            return False, None
        except Exception as e:
            logger.error(f"Error validating price impact for trade {trade['trade_id']}: {e}", exc_info=True)
            return False, None
    
    def _apply_kelly_sizing(self, trade: Dict[str, Any], full_amount: Decimal) -> Decimal:
        """
        Apply Kelly criterion position sizing for AI Strategy.
        
        Args:
            trade: Trade dictionary
            full_amount: Full position size
            
        Returns:
            Amount to trade after Kelly sizing
        """
        kelly_fraction = Decimal('1.0')  # Default to full position
        strategy_name = trade.get('strategy_name', '')
        
        # Check if strategy uses Kelly sizing
        try:
            strategy = StrategyType.from_string(strategy_name)
            uses_kelly = strategy.uses_kelly_sizing()
        except ValueError:
            uses_kelly = False
            logger.warning(f"Trade {trade['trade_id']}: Unknown strategy '{strategy_name}', not using Kelly sizing")
        
        if uses_kelly:
            try:
                ai_manager = self.db.get_ai_strategy_manager()
                kelly_fraction_float = ai_manager.calculate_kelly_fraction(trade['trade_id'])
                kelly_fraction = Decimal(str(kelly_fraction_float))
                
                # Calculate amount to trade (Kelly fraction of full position)
                amount_to_trade = full_amount * kelly_fraction
                
                # Calculate reserved amount (stays in wallet)
                reserved_amount = full_amount - amount_to_trade
                
                logger.info(f"Trade {trade['trade_id']}: Kelly sizing applied")
                logger.info(f"  Full position: {full_amount}")
                logger.info(f"  Kelly fraction: {kelly_fraction:.1%}")
                logger.info(f"  Amount to trade: {amount_to_trade}")
                logger.info(f"  Reserved amount: {reserved_amount}")
                
                # Store reserved amount in trade record for later recovery
                if reserved_amount > 0:
                    cursor = self.db.get_connection().cursor()
                    cursor.execute("""
                        UPDATE trades 
                        SET reserved_amount = ?
                        WHERE trade_id = ?
                    """, (str(reserved_amount), trade['trade_id']))
                    self.db.get_connection().commit()
                
                return amount_to_trade
                    
            except Exception as e:
                logger.error(f"Error applying Kelly sizing for trade {trade['trade_id']}: {e}", exc_info=True)
                return full_amount  # Fallback to full position
        else:
            # Non-AI strategies use full position
            return full_amount
    
    def _sanitize_amount_to_divisibility(self, trade: Dict[str, Any], token_address: str, 
                                         amount: Decimal) -> Decimal:
        """
        Truncate amount to token's actual divisibility to match Radix precision.
        
        Database floats can have precision corruption, causing InvalidAmount errors.
        
        Args:
            trade: Trade dictionary (for logging)
            token_address: Token address
            amount: Amount to sanitize
            
        Returns:
            Sanitized amount
        """
        # Get token divisibility from database
        token_manager = self.db.get_token_manager()
        token_info = token_manager.get_token_by_address(token_address)
        token_divisibility = int(token_info.get('divisibility', 18)) if token_info else 18
        
        amount_str = str(amount)
        if '.' in amount_str:
            integer_part, decimal_part = amount_str.split('.')
            if len(decimal_part) > token_divisibility:
                amount_str = f"{integer_part}.{decimal_part[:token_divisibility]}"
                logger.debug(f"Trade {trade['trade_id']}: Truncated amount from {amount} to {amount_str} (token divisibility: {token_divisibility})")
        
        return Decimal(amount_str)
    
    def check_price_meets_strategy_threshold(self, trade: Dict[str, Any], actual_price: Decimal, 
                                            token_from: str, token_to: str) -> bool:
        """
        Check if actual execution price meets the strategy's threshold requirements.
        
        Only applies to Ping Pong strategy. Other strategies don't have price thresholds.
        
        Args:
            trade: Trade dictionary
            actual_price: Actual execution price in quote_per_base format
            token_from: Address of token being sold
            token_to: Address of token being bought
            
        Returns:
            bool: True if price meets threshold, False otherwise
        """
        try:
            strategy_name = trade.get('strategy_name', '').lower()
            
            # Only validate for ping pong strategy (others don't have price thresholds)
            if strategy_name != 'ping pong':
                return True
            
            indicator_settings = json.loads(trade['indicator_settings_json'])
            buy_price = Decimal(str(indicator_settings['buy_price']))
            sell_price = Decimal(str(indicator_settings['sell_price']))
            pricing_token = indicator_settings.get('pricing_token', 'base')
            
            # Get trade pair info
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            # actual_price is in quote_per_base format (from validate_price_impact).
            # Convert user thresholds to the same format — same logic as signal_generator.
            if pricing_token == 'base':
                # User entered base_per_quote. Invert to quote_per_base (swaps buy/sell roles).
                effective_buy_price = Decimal('1') / sell_price if sell_price != 0 else Decimal('0')
                effective_sell_price = Decimal('1') / buy_price if buy_price != 0 else Decimal('0')
            else:
                effective_buy_price = buy_price
                effective_sell_price = sell_price
            
            effective_current_price = actual_price
            holding_base = token_from == base_token
            
            # Get token symbols for clear logging
            token_manager = self.db.get_token_manager()
            base_token_info = token_manager.get_token_by_address(base_token)
            quote_token_info = token_manager.get_token_by_address(quote_token)
            base_symbol = base_token_info.get('symbol', 'BASE') if base_token_info else 'BASE'
            quote_symbol = quote_token_info.get('symbol', 'QUOTE') if quote_token_info else 'QUOTE'
            
            # Universal buy-low/sell-high in quote_per_base format
            if holding_base:
                # Selling base — price must be high enough (base expensive)
                meets_threshold = effective_current_price >= effective_sell_price
                action_description = f"SELL {base_symbol}"
                price_requirement = f"q/b price must be >={effective_sell_price:.6f} to sell"
                price_status = "too LOW" if not meets_threshold else "acceptable"
            else:
                # Buying base — price must be low enough (base cheap)
                meets_threshold = effective_current_price <= effective_buy_price
                action_description = f"BUY {base_symbol}"
                price_requirement = f"q/b price must be <={effective_buy_price:.6f} to buy"
                price_status = "too HIGH" if not meets_threshold else "acceptable"
            
            if not meets_threshold:
                logger.warning(
                    f"Trade {trade['trade_id']}: Rejected - {action_description} but "
                    f"DEX price is {price_status} ({effective_current_price:.6f} q/b). "
                    f"Strategy requires {price_requirement}."
                )
            else:
                logger.info(
                    f"Trade {trade['trade_id']}: Price validation passed - {action_description} at "
                    f"{effective_current_price:.6f} (q/b) - {price_requirement}"
                )
            
            return meets_threshold
            
        except Exception as e:
            logger.error(f"Error checking price threshold for trade {trade['trade_id']}: {e}", exc_info=True)
            return False
