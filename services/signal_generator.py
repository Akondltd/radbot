"""
Signal Generation for Trading Strategies

Extracted from TradeMonitor to separate concerns.
Handles strategy-specific signal analysis for:
- Ping Pong strategy
- AI Strategy
- Manual Strategy (individual indicators)

Dependencies are injected to maintain flexibility.
"""

import logging
import json
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Callable

from constants import StrategyType
from config.config_loader import config

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates trading signals based on strategy type and market conditions.
    
    This service is stateless and receives dependencies via injection.
    """
    
    def __init__(self, database, price_fetcher, indicator_calculator, market_trending_checker):
        """
        Initialize SignalGenerator with injected dependencies.
        
        Args:
            database: Database instance for trade pair and token lookups
            price_fetcher: Object with get_price_history() and get_price_history_candles() methods
            indicator_calculator: Object with calculate_*_for_trade() methods
            market_trending_checker: Callable that checks if market is trending
        """
        self.db = database
        self.price_fetcher = price_fetcher
        self.indicator_calculator = indicator_calculator
        self.market_trending_checker = market_trending_checker
    
    def determine_trade_signal(self, trade: Dict[str, Any], strategy_name: str, 
                                indicator_settings_json: str, current_price: Decimal,
                                stop_signal: str) -> str:
        """
        Determine if trade should execute based on strategy and current market conditions.
        
        Args:
            trade: Trade dictionary
            strategy_name: Strategy type string
            indicator_settings_json: JSON string of indicator settings
            current_price: Current market price
            stop_signal: Pre-computed stop loss signal ("execute" or "hold")
            
        Returns:
            "execute" if trade should execute, "hold" otherwise
        """
        try:
            if not indicator_settings_json:
                logger.warning(f"No indicator settings for trade {trade['trade_id']}")
                return "hold"
            
            settings = json.loads(indicator_settings_json)
            
            # Determine strategy type using enum
            try:
                strategy = StrategyType.from_string(strategy_name)
            except ValueError:
                logger.warning(f"Trade {trade['trade_id']}: Unknown strategy '{strategy_name}', defaulting to hold")
                return "hold"
            
            # Ping Pong strategies ONLY execute on buy/sell price thresholds - ignore trailing stops
            if strategy.is_ping_pong():
                return self.analyze_ping_pong_signal(trade, current_price)
            
            # For other strategies, stop loss takes priority
            if stop_signal == "execute":
                logger.info(f"Trade {trade['trade_id']}: Trailing stop triggered for {strategy.value} strategy")
                return "execute"
            
            # Route to appropriate strategy handler
            if strategy.is_ai_strategy():
                return self.analyze_ai_strategy_signal(trade, settings, current_price)
            elif strategy.is_manual():
                # Apply ADX trend filter to avoid whipsaw in ranging markets
                adx_threshold = config.adx_threshold
                if not self.market_trending_checker(trade, adx_threshold=adx_threshold):
                    logger.info(f"Trade {trade['trade_id']}: Market not trending (ADX < {adx_threshold}), holding to avoid whipsaw")
                    return "hold"
                
                # Market is trending, proceed with indicator voting
                return self.analyze_individual_indicators(trade, settings, current_price)
            else:
                logger.warning(f"Trade {trade['trade_id']}: Unhandled strategy type {strategy.value}")
                return "hold"
                
        except Exception as e:
            logger.error(f"Error determining signal for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"
    
    def analyze_ping_pong_signal(self, trade: Dict[str, Any], current_price: Decimal) -> str:
        """Analyze Ping Pong trading signals based on buy low/sell high logic."""
        try:
            indicator_settings = json.loads(trade['indicator_settings_json'])
            buy_price = Decimal(str(indicator_settings['buy_price']))
            sell_price = Decimal(str(indicator_settings['sell_price']))
            
            # Get pricing token info (which token the user entered prices in)
            pricing_token = indicator_settings.get('pricing_token', 'base')  # 'base' or 'quote'
            pricing_token_symbol = indicator_settings.get('pricing_token_symbol', '')
            
            # Get trade pair for token addresses
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            # Get accumulation token info (for logging only — doesn't affect trade timing)
            accumulation_token_address = trade.get('accumulation_token_address')
            accumulating_base = accumulation_token_address == base_token
            
            # Get what token we're currently holding
            current_token = trade.get('trade_token_address')
            holding_base = current_token == base_token
            
            # current_price from get_pair_price() is in quote_per_base format
            # (e.g., 11.16 XRD per ASTRL for ASTRL/XRD pair).
            # Higher value = base token is MORE expensive.
            #
            # Convert user thresholds to the same quote_per_base format so all
            # comparisons are consistent. The universal logic is always:
            #   Buy base when cheap (price <= buy_threshold)
            #   Sell base when expensive (price >= sell_threshold)
            # This is correct regardless of accumulation token — accumulation only
            # affects profit accounting, not when to trade.
            
            if pricing_token == 'base':
                # User entered prices in base_per_quote format (e.g., 0.089 ASTRL/XRD).
                # This format moves INVERSELY to the base token's value.
                # Convert to quote_per_base by inverting. Inverting swaps the ordering:
                #   User's buy_price (low in b/q) → high in q/b → our sell threshold
                #   User's sell_price (high in b/q) → low in q/b → our buy threshold
                effective_buy_price = Decimal('1') / sell_price if sell_price != 0 else Decimal('0')
                effective_sell_price = Decimal('1') / buy_price if buy_price != 0 else Decimal('0')
            else:
                # User entered prices in quote_per_base format — matches current_price directly
                effective_buy_price = buy_price
                effective_sell_price = sell_price
            
            effective_current_price = current_price  # Already quote_per_base
            
            # Get token symbols for clear logging
            token_manager = self.db.get_token_manager()
            base_token_info = token_manager.get_token_by_address(base_token)
            quote_token_info = token_manager.get_token_by_address(quote_token)
            base_symbol = base_token_info.get('symbol', 'BASE') if base_token_info else 'BASE'
            quote_symbol = quote_token_info.get('symbol', 'QUOTE') if quote_token_info else 'QUOTE'
            
            logger.info(f"Ping Pong analysis for trade {trade['trade_id']}:")
            logger.info(f"  Pair: {base_symbol}/{quote_symbol}")
            logger.info(f"  Pricing token: {pricing_token_symbol} ({pricing_token})")
            logger.info(f"  User prices: buy={buy_price:.6f}, sell={sell_price:.6f}")
            logger.info(f"  Effective thresholds (q/b): buy<={effective_buy_price:.6f}, sell>={effective_sell_price:.6f}")
            logger.info(f"  Current price (q/b): {effective_current_price:.6f} {quote_symbol}/{base_symbol}")
            logger.info(f"  Accumulating: {'base' if accumulating_base else 'quote'} ({base_symbol if accumulating_base else quote_symbol})")
            logger.info(f"  Currently holding: {'base' if holding_base else 'quote'} ({base_symbol if holding_base else quote_symbol})")
            
            # Universal buy-low/sell-high logic in quote_per_base format
            # Buy base when cheap (price low), sell base when expensive (price high)
            if holding_base:
                if effective_current_price >= effective_sell_price:
                    logger.info(f"Ping Pong EXECUTE: Sell {base_symbol} — price {effective_current_price:.6f} >= {effective_sell_price:.6f} ({base_symbol} is expensive)")
                    return "execute"
            else:
                if effective_current_price <= effective_buy_price:
                    logger.info(f"Ping Pong EXECUTE: Buy {base_symbol} — price {effective_current_price:.6f} <= {effective_buy_price:.6f} ({base_symbol} is cheap)")
                    return "execute"
            
            logger.info(f"Ping Pong HOLD: Price {effective_current_price:.6f} between buy({effective_buy_price:.6f}) and sell({effective_sell_price:.6f})")
            return "hold"
            
        except (KeyError, json.JSONDecodeError, InvalidOperation) as e:
            logger.error(f"Error in Ping Pong analysis: {e}")
            return "hold"
    
    def analyze_ai_strategy_signal(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> str:
        """Analyze AI strategy signal using enhanced adaptive learning."""
        try:
            # Get trade pair for token addresses
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            # Get accumulation token info
            accumulation_token_address = trade.get('accumulation_token_address')
            accumulating_base = accumulation_token_address == base_token
            
            # Get what token we're currently holding
            current_token = trade.get('trade_token_address')
            holding_base = current_token == base_token
            
            # Get historical price data for analysis (using pair-based history)
            # Get candle data (need more for enhanced indicators)
            candles = self.price_fetcher._get_price_history_candles(base_token, quote_token, periods=150)
            if len(candles) < 100:
                logger.warning(f"Insufficient price data for AI strategy trade {trade['trade_id']}: {len(candles)} candles")
                return "hold"
            
            # Get or create optimized parameters for this trade
            ai_manager = self.db.get_ai_strategy_manager()
            parameters = ai_manager.get_parameters(trade['trade_id'])
            
            if not parameters:
                logger.debug(f"No optimized parameters found for trade {trade['trade_id']}, using defaults")
                parameters = None  # EnhancedAIIndicator will use defaults
            
            # Use Enhanced AI Indicator
            from indicators.enhanced_ai_indicator import EnhancedAIIndicator
            
            ai_indicator = EnhancedAIIndicator(parameters)
            composite_score, confidence, market_regime = ai_indicator.generate_signal(candles)
            
            # Get thresholds from parameters or use config defaults
            execution_threshold = parameters.get('execution_threshold', config.ai_execution_threshold) if parameters else config.ai_execution_threshold
            confidence_threshold = parameters.get('confidence_threshold', config.ai_confidence_threshold) if parameters else config.ai_confidence_threshold
            
            logger.debug(f"AI Strategy for trade {trade['trade_id']}: Score={composite_score:.3f}, "
                        f"Confidence={confidence:.3f}, Regime={market_regime}")
            
            # Record AI trade entry for learning
            if abs(composite_score) >= execution_threshold and confidence >= confidence_threshold:
                # Strong signal - record this for outcome tracking
                ai_manager.record_trade_entry(
                    trade_id=trade['trade_id'],
                    entry_price=float(current_price),
                    composite_score=float(composite_score),
                    confidence_score=float(confidence),
                    market_regime=market_regime,
                    indicator_scores={}  # Can be populated later if needed
                )
            
            # Only execute if both score and confidence are high
            if abs(composite_score) >= execution_threshold and confidence >= confidence_threshold:
                # Check cooldown period to prevent rapid flipping
                import time
                last_signal_time = trade.get('last_signal_updated_at', 0)
                current_time = int(time.time())
                time_since_last_signal = (current_time - last_signal_time) / 60  # Convert to minutes
                min_interval = config.ai_min_flip_interval_minutes
                
                if time_since_last_signal < min_interval:
                    logger.info(f"AI Strategy COOLDOWN for trade {trade['trade_id']}: "
                               f"Only {time_since_last_signal:.1f} min since last signal (need {min_interval} min)")
                    return "hold"
                
                action = "BUY" if composite_score > 0 else "SELL"
                
                # Check if the signal aligns with current holdings
                # BUY = bullish for base (price expected to rise)
                # SELL = bearish for base (price expected to fall)
                # Logic is the same regardless of accumulation token:
                #   Sell base on SELL signal (exit before price drops)
                #   Buy base on BUY signal (enter before price rises)
                # Accumulation token only affects profit accounting, not trade timing.
                should_execute = False
                if holding_base and action == "SELL":
                    should_execute = True  # Sell base before price drops
                elif not holding_base and action == "BUY":
                    should_execute = True  # Buy base before price rises
                
                if should_execute:
                    signal = "execute"
                    logger.info(f"AI Strategy EXECUTE signal for trade {trade['trade_id']}: "
                               f"Score: {composite_score:.3f}, Confidence: {confidence:.3f}, "
                               f"Regime: {market_regime}, Action: {action}, "
                               f"Accumulating: {'base' if accumulating_base else 'quote'}, Holding: {'base' if holding_base else 'quote'}")
                else:
                    signal = "hold"
                    logger.debug(f"AI Strategy HOLD signal (action doesn't match holdings) for trade {trade['trade_id']}: "
                                f"Score: {composite_score:.3f}, Action: {action}, "
                                f"Accumulating: {'base' if accumulating_base else 'quote'}, Holding: {'base' if holding_base else 'quote'}")
            else:
                signal = "hold"
                logger.debug(f"AI Strategy HOLD signal for trade {trade['trade_id']}: "
                            f"Score: {composite_score:.3f}, Confidence: {confidence:.3f}, "
                            f"Regime: {market_regime} (thresholds not met)")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in AI strategy analysis for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"
    
    def analyze_individual_indicators(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> str:
        """Analyze individual indicators and use ≥50% voting logic."""
        try:
            # Get trade pair for token addresses
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            # Get accumulation token info
            accumulation_token_address = trade.get('accumulation_token_address')
            accumulating_base = accumulation_token_address == base_token
            
            # Get what token we're currently holding
            current_token = trade.get('trade_token_address')
            holding_base = current_token == base_token
            
            indicators_to_check = []
            buy_votes = 0
            sell_votes = 0
            hold_votes = 0
            total_votes = 0
            
            # Check which individual indicators are configured
            if 'RSI' in settings:
                indicators_to_check.append('RSI')
            if 'MACD' in settings:
                indicators_to_check.append('MACD')
            if 'MOVING_AVERAGE' in settings or 'MA' in settings or 'MA_CROSS' in settings:
                indicators_to_check.append('MA')
            if 'BOLLINGER_BANDS' in settings or 'BB' in settings:
                indicators_to_check.append('BB')
            
            if not indicators_to_check:
                logger.warning(f"No individual indicators configured for trade {trade['trade_id']}")
                return "hold"
            
            logger.info(f"Trade {trade['trade_id']} analyzing individual indicators: {indicators_to_check}")
            logger.info(f"  Current price: {current_price}")
            
            # Get vote from each indicator (returns composite score)
            indicator_scores = {}
            for indicator in indicators_to_check:
                if indicator == 'RSI':
                    score = self.indicator_calculator._calculate_rsi_score_for_trade(trade, settings, current_price)
                elif indicator == 'MACD':
                    score = self.indicator_calculator._calculate_macd_score_for_trade(trade, settings, current_price)
                elif indicator == 'MA':
                    score = self.indicator_calculator._calculate_ma_score_for_trade(trade, settings, current_price)
                elif indicator == 'BB':
                    score = self.indicator_calculator._calculate_bb_score_for_trade(trade, settings, current_price)
                else:
                    score = 0.0
                
                indicator_scores[indicator] = score
                total_votes += 1
                
                # Count votes based on score thresholds
                # Higher thresholds (0.65/-0.65) reduce sensitivity to noise in crypto markets
                vote_type = "HOLD"
                if score > 0.65:  # Very strong buy signal (was 0.5)
                    buy_votes += 1
                    vote_type = "BUY"
                elif score < -0.65:  # Very strong sell signal (was -0.5)
                    sell_votes += 1
                    vote_type = "SELL"
                else:  # Neutral/weak signal
                    hold_votes += 1
                    
                logger.info(f"  {indicator}: score={score:.2f}, vote={vote_type}")
            
            # Determine consensus action
            dominant_action = None
            if buy_votes > sell_votes and buy_votes >= total_votes * 0.5:
                dominant_action = "BUY"
            elif sell_votes > buy_votes and sell_votes >= total_votes * 0.5:
                dominant_action = "SELL"
            
            # Check if the consensus aligns with accumulation goal
            if dominant_action:
                should_execute = False
                
                # Get token symbols for clear logging
                token_manager = self.db.get_token_manager()
                base_token_info = token_manager.get_token_by_address(base_token)
                quote_token_info = token_manager.get_token_by_address(quote_token)
                accum_token_info = token_manager.get_token_by_address(accumulation_token_address)
                current_token_info = token_manager.get_token_by_address(current_token)
                
                base_symbol = base_token_info.get('symbol', 'BASE') if base_token_info else 'BASE'
                quote_symbol = quote_token_info.get('symbol', 'QUOTE') if quote_token_info else 'QUOTE'
                accum_symbol = accum_token_info.get('symbol', 'ACCUM') if accum_token_info else 'ACCUM'
                current_symbol = current_token_info.get('symbol', 'CURRENT') if current_token_info else 'CURRENT'
                
                logger.info(f"Trade {trade['trade_id']} indicator analysis:")
                logger.info(f"  Pair: {base_symbol}/{quote_symbol}")
                logger.info(f"  Accumulating: {accum_symbol} (base={accumulating_base})")
                logger.info(f"  Currently holding: {current_symbol} (holding_base={holding_base})")
                logger.info(f"  Indicator consensus: {dominant_action}")
                logger.info(f"  Votes - Buy: {buy_votes}, Sell: {sell_votes}, Hold: {hold_votes}")
                
                # Signal-to-action mapping is the same regardless of accumulation token:
                #   SELL signal (bearish) + holding base → sell base (exit before drop)
                #   BUY signal (bullish) + holding quote → buy base (enter before rise)
                # Accumulation token only affects profit accounting, not trade timing.
                if holding_base and dominant_action == "SELL":
                    should_execute = True  # Sell base at high price / before drop
                    logger.info(f"EXECUTE: Sell {base_symbol} — SELL signal while holding base")
                elif not holding_base and dominant_action == "BUY":
                    should_execute = True  # Buy base at low price / before rise
                    logger.info(f"EXECUTE: Buy {base_symbol} — BUY signal while holding quote")
                else:
                    logger.info(f"HOLD: {dominant_action} signal doesn't match holdings ({'base' if holding_base else 'quote'})")
                
                if should_execute:
                    logger.info(f"Trade {trade['trade_id']} individual indicators EXECUTE: "
                               f"Buy votes: {buy_votes}, Sell votes: {sell_votes}, Hold votes: {hold_votes}, "
                               f"Action: {dominant_action}, Accumulating: {accum_symbol}, "
                               f"Holding: {current_symbol}")
                    return "execute"
                else:
                    logger.debug(f"Trade {trade['trade_id']} individual indicators HOLD (action misaligned with accumulation): "
                                f"Action: {dominant_action}, Accumulating: {'base' if accumulating_base else 'quote'}, "
                                f"Holding: {'base' if holding_base else 'quote'}")
                    return "hold"
            else:
                logger.debug(f"Trade {trade['trade_id']} individual indicators HOLD (no consensus): "
                            f"Buy: {buy_votes}, Sell: {sell_votes}, Hold: {hold_votes}")
                return "hold"
            
        except Exception as e:
            logger.error(f"Error in individual indicator analysis: {e}", exc_info=True)
            return "hold"
