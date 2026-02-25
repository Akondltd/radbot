import requests
import logging
import json
from decimal import Decimal
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject
from core.wallet import RadixWallet
from core.transaction_builder import RadixTransactionBuilder
from database.database import Database
import time
import re
from radix_engine_toolkit import Decimal as RETDecimal
from services.task_coordinator import TaskPriority

# Import strategy constants and config
from constants import StrategyType
from config.config_loader import config
from config.fee_config import get_fee_percentage, get_fee_component_address, verify_fee_integrity, verify_manifest_contains_fee
from services.technical_indicators import TechnicalIndicators
from services.signal_generator import SignalGenerator
from services.trade_validator import TradeValidator
from services.astrolescent_price_service import get_price_service
from services.pair_price_history_service import get_pair_history_service

logger = logging.getLogger(__name__)
trade_logger = logging.getLogger('radbot.trades')

ASTRO_API_URL = "https://api.astrolescent.com/partner/akond/swap"
XRD_TOKEN_ADDRESS = "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd"
# Fee configuration loaded from obfuscated config (tamper-resistant)
FEE_PERCENTAGE = get_fee_percentage()
FEE_COMPONENT_ADDRESS = get_fee_component_address()
# Price impact threshold loaded from config
MAX_PRICE_IMPACT_PERCENT = Decimal(str(config.max_price_impact))

class TradeMonitor(QObject):
    def __init__(self, wallet: RadixWallet, db_path: str, on_trades_executed_callback=None, service_coordinator=None):
        logger.info(f"TradeMonitor initializing with wallet: {wallet.public_address if wallet else 'None'}")
        logger.info(f"Database path: {db_path}")
        
        super().__init__()
        self.name = 'trade_monitor'  # For ServiceCoordinator registration
        if not isinstance(wallet, RadixWallet):
            raise TypeError("TradeMonitor requires a valid RadixWallet instance.")
        self.wallet = wallet
        self.on_trades_executed_callback = on_trades_executed_callback
        self.service_coordinator = service_coordinator  # NEW: For task coordination
        self.execution_counter = 0  # For unique task names
        
        try:
            self.db = Database(db_path)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            raise
            
        try:
            self.tx_builder = RadixTransactionBuilder(wallet=self.wallet)
            logger.info("Transaction builder created")
        except Exception as e:
            logger.error(f"Failed to create transaction builder: {e}", exc_info=True)
            raise
        
        # Initialize SignalGenerator with adapters
        self.signal_generator = SignalGenerator(
            database=self.db,
            price_fetcher=self,  # TradeMonitor has price history methods
            indicator_calculator=self,  # TradeMonitor has indicator wrappers
            market_trending_checker=self._check_market_trending
        )
        logger.info("SignalGenerator initialized")
        
        # Initialize TradeValidator
        self.trade_validator = TradeValidator(
            database=self.db,
            wallet=self.wallet,
            astro_api_url=ASTRO_API_URL,
            fee_component=FEE_COMPONENT_ADDRESS,
            fee_percentage=FEE_PERCENTAGE,
            max_price_impact=MAX_PRICE_IMPACT_PERCENT
        )
        logger.info("TradeValidator initialized")
            
        logger.info("TradeMonitor initialization complete")

    def stop(self):
        """No-op — TradeMonitor is driven by QtPriceHistoryService, not its own thread."""
        logger.info("TradeMonitor stopped")

    def run(self):
        """Main trade monitoring workflow with 3 phases."""
        logger.info("=== TradeMonitor.run() starting ===")
        trades_were_executed = False  # Initialize before any early returns
        try:
            # Phase 1: Signal Analysis
            logger.info("Phase 1: Starting signal analysis...")
            active_trades = self._get_active_trades()
            if not active_trades:
                logger.info("No active trades found.")
                return

            logger.info(f"Analyzing signals for {len(active_trades)} active trades...")
            self._analyze_trade_signals(active_trades)

            # Phase 2: Get trades marked for execution and validate them
            logger.info("Phase 2: Getting trades marked for execution...")
            execute_trades = self._get_trades_to_execute()
            if not execute_trades:
                logger.info("No trades marked for execution.")
                return

            logger.info(f"Validating {len(execute_trades)} trades marked for execution...")
            validated_trades = self._validate_trades_for_execution(execute_trades)

            # Phase 3: Execute validated trades (coordinated if coordinator available)
            logger.info("Phase 3: Executing validated trades...")
            if validated_trades:
                logger.info(f"Executing {len(validated_trades)} validated trades...")
                
                # If we have a coordinator, submit as coordinated task
                if self.service_coordinator:
                    self.execution_counter += 1
                    try:
                        from services.service_coordinator import ServiceCategory
                        
                        logger.info("Submitting coordinated trade execution...")
                        task = self.service_coordinator.submit_task(
                            name=f"trade_execution_{self.execution_counter}",
                            func=self._execute_validated_trades,
                            args=(validated_trades,),
                            priority=TaskPriority.NORMAL,
                            category=ServiceCategory.EXECUTION,
                            blocks_category=ServiceCategory.EXECUTION,  # Only one trade execution at a time
                            max_retries=0  # Don't retry failed executions
                        )
                        logger.info(f"Trade execution task submitted: {task.name}")
                        trades_were_executed = True
                    except Exception as e:
                        logger.error(f"Error submitting coordinated execution: {e}", exc_info=True)
                        # Fallback to direct execution
                        self._execute_validated_trades(validated_trades)
                        trades_were_executed = True
                else:
                    # No coordinator - execute directly (backward compatible)
                    self._execute_validated_trades(validated_trades)
                    trades_were_executed = True
            else:
                logger.info("No trades passed validation for execution.")

        except Exception as e:
            logger.error(f"Error during trade monitoring cycle: {e}", exc_info=True)
        finally:
            logger.info("=== TradeMonitor.run() completed ===")
            # Trigger UI refresh callback if trades were executed
            if trades_were_executed and self.on_trades_executed_callback:
                try:
                    logger.info("Triggering UI refresh callback after trade execution")
                    self.on_trades_executed_callback()
                except Exception as e:
                    logger.error(f"Error calling UI refresh callback: {e}", exc_info=True)

    def _get_active_trades(self) -> List[Dict[str, Any]]:
        """Get all active trades from database for the current wallet."""
        try:
            trade_manager = self.db.get_trade_manager()
            all_active_trades = trade_manager.get_active_trades()
            
            # Filter trades to only those for the current wallet
            wallet_address = self.wallet.public_address
            filtered_trades = [
                trade for trade in all_active_trades 
                if trade.get('wallet_address') == wallet_address
            ]
            
            if len(all_active_trades) != len(filtered_trades):
                logger.info(f"Filtered {len(all_active_trades)} active trades to {len(filtered_trades)} for wallet {wallet_address}")
            
            return filtered_trades
        except Exception as e:
            logger.error(f"Error fetching active trades: {e}", exc_info=True)
            return []

    def _analyze_trade_signals(self, trades: List[Dict[str, Any]]) -> None:
        """Phase 1: Analyze each trade and update current_signal column."""
        for trade in trades:
            try:
                trade_id = trade['trade_id']
                strategy_name = trade.get('strategy_name', '')
                indicator_settings_json = trade.get('indicator_settings_json')
                
                logger.debug(f"Analyzing trade {trade_id} with strategy '{strategy_name}'")
                
                # Determine signal based on strategy
                signal = self._determine_trade_signal(trade, strategy_name, indicator_settings_json)
                
                # Update current_signal in database
                self._update_trade_signal(trade_id, signal)
                
                logger.debug(f"Trade {trade_id} signal updated to: {signal}")
                
            except Exception as e:
                logger.error(f"Error analyzing trade {trade.get('trade_id', 'unknown')}: {e}", exc_info=True)

    def _determine_trade_signal(self, trade: Dict[str, Any], strategy_name: str, indicator_settings_json: str) -> str:
        """Determine if trade should execute based on strategy and current market conditions."""
        try:
            # Get current price data for the trade pair
            current_price = self._get_current_price(trade)
            if current_price is None:
                logger.warning(f"Could not get current price for trade {trade['trade_id']}")
                return "hold"
            
            # Check stop loss and trailing stop BEFORE strategy signals
            stop_signal = self._check_stop_conditions(trade, current_price)
            
            # Use SignalGenerator service
            return self.signal_generator.determine_trade_signal(
                trade=trade,
                strategy_name=strategy_name,
                indicator_settings_json=indicator_settings_json,
                current_price=current_price,
                stop_signal=stop_signal
            )
                
        except Exception as e:
            logger.error(f"Error determining signal for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"

    def _check_stop_conditions(self, trade: Dict[str, Any], current_price: Decimal) -> str:
        """
        Check stop loss and trailing stop conditions.
        Returns 'execute' if either condition is met, 'hold' otherwise.
        Only applies when holding the non-accumulation token (risky position).
        """
        try:
            # Load stop settings from trade's indicator_settings_json
            import json
            indicator_settings = {}
            try:
                indicator_settings_json = trade.get('indicator_settings_json', '{}')
                indicator_settings = json.loads(indicator_settings_json) if indicator_settings_json else {}
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Trade {trade.get('trade_id')}: Failed to parse indicator_settings_json: {e}")
            
            stop_loss_pct = float(indicator_settings.get('stop_loss_percentage', 0.0))
            trailing_stop_pct = float(indicator_settings.get('trailing_stop_percentage', 0.0))
            
            # If both are disabled (0), skip checks
            if stop_loss_pct == 0 and trailing_stop_pct == 0:
                return "hold"
            
            # Get trade details
            trade_id = trade['trade_id']
            accumulation_token_address = trade.get('accumulation_token_address')
            current_token_address = trade.get('trade_token_address')
            trade_amount = Decimal(str(trade.get('trade_amount', 0)))
            
            # Only check stops when holding NON-accumulation token (risky position)
            if current_token_address == accumulation_token_address:
                logger.debug(f"Trade {trade_id}: Holding accumulation token, skipping stop checks")
                return "hold"
            
            # Get trade pair info
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            # Determine what we'd get if we sold back to accumulation token
            # current_price is always in quote/base format
            if current_token_address == base_token:
                # We're holding base, accumulation is quote
                # If we sell: we give 'trade_amount' base, we get 'trade_amount * current_price' quote
                current_value_in_accumulation = trade_amount * current_price
            else:
                # We're holding quote, accumulation is base
                # If we sell: we give 'trade_amount' quote, we get 'trade_amount / current_price' base
                current_value_in_accumulation = trade_amount / current_price if current_price > 0 else Decimal('0')
            
            # Get the original amount we started with (what we paid to get into this position)
            # This is stored in the last trade_history entry
            trade_manager = self.db.get_trade_manager()
            cursor = self.db._conn.cursor()
            cursor.execute("""
                SELECT amount_quote, side FROM trade_history 
                WHERE trade_id_original = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (trade_id,))
            last_trade = cursor.fetchone()
            
            if not last_trade:
                logger.debug(f"Trade {trade_id}: No trade history found, skipping stop checks")
                return "hold"
            
            # Determine what we paid to enter this position
            last_amount_quote = Decimal(str(last_trade[0]))
            last_side = last_trade[1]
            
            # Figure out what we paid in accumulation token
            if accumulation_token_address == quote_token:
                # Accumulation is quote (XRD)
                if last_side == 'BUY':
                    # We bought base with quote, so we paid last_amount_quote
                    original_amount_in_accumulation = last_amount_quote
                else:
                    # We sold base for quote, we received last_amount_quote
                    # This shouldn't happen since we should be holding base now
                    original_amount_in_accumulation = last_amount_quote
            else:
                # Accumulation is base
                if last_side == 'SELL':
                    # We sold base for quote, received quote, now holding quote
                    # Original base amount would be in amount_base from history
                    cursor.execute("""
                        SELECT amount_base FROM trade_history 
                        WHERE trade_id_original = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (trade_id,))
                    last_base = cursor.fetchone()
                    original_amount_in_accumulation = Decimal(str(last_base[0])) if last_base else Decimal('0')
                else:
                    # We bought base with quote
                    cursor.execute("""
                        SELECT amount_base FROM trade_history 
                        WHERE trade_id_original = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (trade_id,))
                    last_base = cursor.fetchone()
                    original_amount_in_accumulation = Decimal(str(last_base[0])) if last_base else Decimal('0')
            
            if original_amount_in_accumulation == 0:
                logger.debug(f"Trade {trade_id}: Could not determine original amount, skipping stop checks")
                return "hold"
            
            # Calculate profit/loss as percentage and absolute amount
            profit_loss_amount = current_value_in_accumulation - original_amount_in_accumulation
            profit_loss_pct = (profit_loss_amount / original_amount_in_accumulation) * 100
            
            # Get accumulation token symbol for clear logging
            accumulation_symbol = trade.get('accumulation_token_symbol', 'tokens')
            
            # Check stop loss
            if stop_loss_pct > 0 and profit_loss_pct <= -stop_loss_pct:
                # Calculate USD value if possible
                try:
                    cursor.execute("""
                        SELECT token_price_usd FROM tokens 
                        WHERE address = ?
                    """, (accumulation_token_address,))
                    token_usd_price_row = cursor.fetchone()
                    token_usd_price = float(token_usd_price_row[0]) if token_usd_price_row and token_usd_price_row[0] else 0.0
                    loss_usd = float(profit_loss_amount) * token_usd_price
                except Exception:
                    loss_usd = 0.0
                
                logger.info(f"STOP LOSS TRIGGERED - Trade {trade_id}")
                logger.info(f"  Loss: {profit_loss_pct:.2f}% (threshold: -{stop_loss_pct}%)")
                logger.info(f"  Original value: {original_amount_in_accumulation:.4f} {accumulation_symbol}")
                logger.info(f"  Current value:  {current_value_in_accumulation:.4f} {accumulation_symbol}")
                logger.info(f"  Loss amount:    {abs(profit_loss_amount):.4f} {accumulation_symbol}" + 
                           (f" (${abs(loss_usd):.2f} USD)" if loss_usd > 0 else ""))
                logger.info(f"  Executing trade to cut losses...")
                return "execute"
            
            # Check trailing stop
            if trailing_stop_pct > 0:
                # Get peak profit from database
                cursor.execute("SELECT peak_profit_xrd FROM trades WHERE trade_id = ?", (trade_id,))
                peak_row = cursor.fetchone()
                peak_profit = Decimal(str(peak_row[0])) if peak_row and peak_row[0] else Decimal('0')
                
                # Calculate current profit (not percentage, absolute profit in accumulation token)
                current_profit = current_value_in_accumulation - original_amount_in_accumulation
                
                # Update peak if current profit is higher
                if current_profit > peak_profit:
                    peak_profit = current_profit
                    cursor.execute("""
                        UPDATE trades 
                        SET peak_profit_xrd = ? 
                        WHERE trade_id = ?
                    """, (float(peak_profit), trade_id))
                    self.db._conn.commit()
                    logger.debug(f"Trade {trade_id}: Updated peak profit to {peak_profit:.4f}")
                
                # Check if profit has dropped from peak by more than trailing_stop_pct
                if peak_profit > 0:
                    # Calculate percentage drop from peak
                    drop_from_peak_pct = ((peak_profit - current_profit) / original_amount_in_accumulation) * 100
                    
                    if drop_from_peak_pct >= trailing_stop_pct:
                        # Calculate USD value if possible
                        try:
                            cursor.execute("""
                                SELECT token_price_usd FROM tokens 
                                WHERE address = ?
                            """, (accumulation_token_address,))
                            token_usd_price_row = cursor.fetchone()
                            token_usd_price = float(token_usd_price_row[0]) if token_usd_price_row and token_usd_price_row[0] else 0.0
                            peak_profit_usd = float(peak_profit) * token_usd_price
                            current_profit_usd = float(current_profit) * token_usd_price
                            drop_usd = peak_profit_usd - current_profit_usd
                        except Exception:
                            peak_profit_usd = 0.0
                            current_profit_usd = 0.0
                            drop_usd = 0.0
                        
                        logger.info(f" TRAILING STOP TRIGGERED - Trade {trade_id}")
                        logger.info(f"  Drop from peak: {drop_from_peak_pct:.2f}% (threshold: {trailing_stop_pct}%)")
                        logger.info(f"  Peak profit:    {peak_profit:.8f} {accumulation_symbol}" +
                                   (f" (${peak_profit_usd:.2f} USD)" if peak_profit_usd > 0 else ""))
                        logger.info(f"  Current profit: {current_profit:.8f} {accumulation_symbol}" +
                                   (f" (${current_profit_usd:.2f} USD)" if current_profit_usd > 0 else ""))
                        logger.info(f"  Profit given up: {peak_profit - current_profit:.8f} {accumulation_symbol}" +
                                   (f" (${drop_usd:.2f} USD)" if drop_usd > 0 else ""))
                        logger.info(f"  Executing trade to lock in remaining profit...")
                        return "execute"
            
            logger.debug(f"Trade {trade_id}: P/L: {profit_loss_pct:.2f}%, no stop conditions met")
            return "hold"
            
        except Exception as e:
            logger.error(f"Error checking stop conditions for trade {trade.get('trade_id', 'unknown')}: {e}", exc_info=True)
            return "hold"

    def _get_current_price(self, trade: Dict[str, Any]) -> Optional[Decimal]:
        """
        Get current price for the trade pair from Astrolescent liquidity-weighted prices.
        Uses live prices from DefiPlaza, Ociswap, and CaviarNine.
        """
        try:
            # Get trade pair info
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token_address = trade_pair['base_token']
            quote_token_address = trade_pair['quote_token']
            
            # Get current price from Astrolescent price service
            price_service = get_price_service()
            current_price = price_service.get_pair_price(base_token_address, quote_token_address)
            
            if current_price is None:
                logger.warning(f"Could not get price for trade {trade['trade_id']} ({trade.get('trade_token_symbol')}/{trade.get('accumulation_token_symbol')})")
                return None
            
            logger.debug(f"Got current price for trade {trade['trade_id']}: {current_price:.8f}")
            return current_price
                
        except Exception as e:
            logger.error(f"Error getting current price for trade {trade['trade_id']}: {e}", exc_info=True)
            return None

    def _calculate_rsi_score_for_trade(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> float:
        """Calculate RSI score for a trade using user's settings."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)
            if len(price_data) < 20:
                return 0.0
            
            # Extract user's RSI settings
            rsi_settings = settings.get('RSI', {})
            period = int(rsi_settings.get('period', 14))
            buy_threshold = float(rsi_settings.get('buy_threshold', 30.0))
            sell_threshold = float(rsi_settings.get('sell_threshold', 70.0))
            
            # Use TechnicalIndicators service with user's settings
            return TechnicalIndicators.calculate_rsi(
                price_data,
                period=period,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold
            )
        except Exception as e:
            logger.error(f"Error calculating RSI score for trade: {e}", exc_info=True)
            return 0.0
    
    def _calculate_macd_score_for_trade(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> float:
        """Calculate MACD score for a trade using user's settings."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)
            if len(price_data) < 26:
                return 0.0
            
            # Extract user's MACD settings
            macd_settings = settings.get('MACD', {})
            fast_period = int(macd_settings.get('fast_period', 12))
            slow_period = int(macd_settings.get('slow_period', 26))
            signal_period = int(macd_settings.get('signal_period', 9))
            
            # Use TechnicalIndicators service with user's settings
            return TechnicalIndicators.calculate_macd(
                price_data,
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period
            )
        except Exception as e:
            logger.error(f"Error calculating MACD score for trade: {e}", exc_info=True)
            return 0.0
    
    def _calculate_ma_score_for_trade(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> float:
        """Calculate Moving Average or MA Crossover score using user's settings."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)
            if len(price_data) < 21:
                return 0.0
            
            # Extract user's MA_CROSS settings (new format)
            ma_settings = settings.get('MA_CROSS', {})
            
            # If MA_CROSS settings exist, use crossover mode
            if ma_settings:
                short_period = int(ma_settings.get('short_period', 20))
                long_period = int(ma_settings.get('long_period', 50))
                
                # Use TechnicalIndicators service in crossover mode
                return TechnicalIndicators.calculate_moving_average(
                    price_data,
                    short_period=short_period,
                    long_period=long_period
                )
            else:
                # Fallback to simple MA mode (backward compatibility)
                return TechnicalIndicators.calculate_moving_average(
                    price_data,
                    current_price=current_price,
                    period=20
                )
        except Exception as e:
            logger.error(f"Error calculating MA score for trade: {e}", exc_info=True)
            return 0.0
    
    def _calculate_bb_score_for_trade(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> float:
        """Calculate Bollinger Bands score using user's settings."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)
            if len(price_data) < 20:
                return 0.0
            
            # Extract user's Bollinger Bands settings
            bb_settings = settings.get('BOLLINGER_BANDS', settings.get('BB', {}))
            period = int(bb_settings.get('period', 20))
            std_dev = float(bb_settings.get('std_dev', 2.0))
            
            # Use TechnicalIndicators service with user's settings
            return TechnicalIndicators.calculate_bollinger_bands(
                price_data,
                current_price,
                period=period,
                std_dev=std_dev
            )
        except Exception as e:
            logger.error(f"Error calculating BB score for trade: {e}", exc_info=True)
            return 0.0

    def _get_price_history(self, base_token: str, quote_token: str, periods: int = 50) -> List[Decimal]:
        """Get historical price data for technical analysis from pair history."""
        try:
            pair_history = get_pair_history_service()
            history_data = pair_history.get_price_history(base_token, quote_token, limit=periods)
            
            if history_data:
                prices = [Decimal(str(candle['close'])) for candle in history_data]
                logger.debug(f"Retrieved {len(prices)} price points for technical analysis")
                return prices
            else:
                logger.warning(f"No price history found for pair {base_token}/{quote_token}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting price history for pair {base_token}/{quote_token}: {e}", exc_info=True)
            return []

    def _get_price_history_candles(self, base_token: str, quote_token: str, periods: int = 100) -> List:
        """Get historical candle data for enhanced AI analysis from pair history."""
        try:
            from models.data_models import Candle
            
            pair_history = get_pair_history_service()
            history_data = pair_history.get_price_history(base_token, quote_token, limit=periods)
            
            if history_data:
                # Convert to Candle objects (data already in chronological order)
                candles = []
                for candle_data in history_data:
                    candles.append(Candle(
                        timestamp=candle_data['timestamp'],
                        open=float(candle_data['open']),
                        high=float(candle_data['high']),
                        low=float(candle_data['low']),
                        close=float(candle_data['close']),
                        volume=float(candle_data.get('volume', 0))
                    ))
                logger.debug(f"Retrieved {len(candles)} candles for AI analysis")
                return candles
            else:
                logger.warning(f"No price history found for pair {base_token}/{quote_token}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting price history candles for pair {base_token}/{quote_token}: {e}", exc_info=True)
            return []

    def _check_market_trending(self, trade: Dict[str, Any], adx_threshold: float = None) -> bool:
        """
        Check if market is trending using ADX (Average Directional Index).
        
        ADX measures trend strength regardless of direction:
        - ADX < threshold: Weak/no trend (ranging market) - avoid trading
        - ADX >= threshold: Strong trend - safe to trade with indicators
        
        Args:
            trade: Trade dictionary
            adx_threshold: Minimum ADX value to consider market trending (default from config)
            
        Returns:
            True if market is trending (ADX >= threshold), False otherwise
        """
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            # Get price data
            price_data = self._get_price_history(base_token, quote_token, periods=50)
            if len(price_data) < 28:
                logger.debug(f"Trade {trade['trade_id']}: Insufficient data for ADX ({len(price_data)} periods)")
                return True  # Allow trade if insufficient data
            
            # Use TechnicalIndicators service for ADX check
            is_trending = TechnicalIndicators.check_market_trending(
                price_data,
                threshold=adx_threshold
            )
            
            logger.debug(f"Trade {trade['trade_id']}: Market is {'trending' if is_trending else 'ranging'}")
            return is_trending
            
        except Exception as e:
            logger.error(f"Error checking market trend for trade {trade['trade_id']}: {e}", exc_info=True)
            return True  # Allow trade on error (fail open)

    def _calculate_ema(self, prices: List[Decimal], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        try:
            if len(prices) < period:
                return []
            
            multiplier = 2.0 / (period + 1)
            ema = [float(prices[0])]  # Start with first price
            
            for price in prices[1:]:
                ema_value = (float(price) * multiplier) + (ema[-1] * (1 - multiplier))
                ema.append(ema_value)
            
            return ema
            
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}", exc_info=True)
            return []

    def _analyze_rsi_signal(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> str:
        """Analyze RSI indicator signal."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)  # Get 50 periods for analysis
            if len(price_data) < 20:  # Need minimum data for technical analysis
                logger.warning(f"Insufficient price data for RSI analysis for trade {trade['trade_id']}: {len(price_data)} periods")
                return "hold"
            
            # Calculate RSI score
            rsi_score = self._calculate_rsi_score(price_data)
            
            # Determine signal based on RSI score
            if rsi_score > 0.5:
                signal = "execute"
                logger.info(f"RSI EXECUTE signal for trade {trade['trade_id']}: score {rsi_score:.2f}")
            elif rsi_score < -0.5:
                signal = "execute"
                logger.info(f"RSI EXECUTE signal for trade {trade['trade_id']}: score {rsi_score:.2f}")
            else:
                signal = "hold"
                logger.debug(f"RSI HOLD signal for trade {trade['trade_id']}: score {rsi_score:.2f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in RSI analysis for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"

    def _analyze_macd_signal(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> str:
        """Analyze MACD indicator signal."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)  # Get 50 periods for analysis
            if len(price_data) < 20:  # Need minimum data for technical analysis
                logger.warning(f"Insufficient price data for MACD analysis for trade {trade['trade_id']}: {len(price_data)} periods")
                return "hold"
            
            # Calculate MACD score
            macd_score = self._calculate_macd_score(price_data)
            
            # Determine signal based on MACD score
            if macd_score > 0.5:
                signal = "execute"
                logger.info(f"MACD EXECUTE signal for trade {trade['trade_id']}: score {macd_score:.2f}")
            elif macd_score < -0.5:
                signal = "execute"
                logger.info(f"MACD EXECUTE signal for trade {trade['trade_id']}: score {macd_score:.2f}")
            else:
                signal = "hold"
                logger.debug(f"MACD HOLD signal for trade {trade['trade_id']}: score {macd_score:.2f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in MACD analysis for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"

    def _analyze_ma_signal(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> str:
        """Analyze Moving Average signal."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)  # Get 50 periods for analysis
            if len(price_data) < 20:  # Need minimum data for technical analysis
                logger.warning(f"Insufficient price data for MA analysis for trade {trade['trade_id']}: {len(price_data)} periods")
                return "hold"
            
            # Calculate MA score
            ma_score = self._calculate_ma_score(price_data, current_price)
            
            # Determine signal based on MA score
            if ma_score > 0.5:
                signal = "execute"
                logger.info(f"MA EXECUTE signal for trade {trade['trade_id']}: score {ma_score:.2f}")
            elif ma_score < -0.5:
                signal = "execute"
                logger.info(f"MA EXECUTE signal for trade {trade['trade_id']}: score {ma_score:.2f}")
            else:
                signal = "hold"
                logger.debug(f"MA HOLD signal for trade {trade['trade_id']}: score {ma_score:.2f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in MA analysis for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"

    def _analyze_bollinger_signal(self, trade: Dict[str, Any], settings: Dict, current_price: Decimal) -> str:
        """Analyze Bollinger Bands signal."""
        try:
            # Get token pair from trade
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            base_token = trade_pair['base_token']
            quote_token = trade_pair['quote_token']
            
            price_data = self._get_price_history(base_token, quote_token, periods=50)  # Get 50 periods for analysis
            if len(price_data) < 20:  # Need minimum data for technical analysis
                logger.warning(f"Insufficient price data for Bollinger Bands analysis for trade {trade['trade_id']}: {len(price_data)} periods")
                return "hold"
            
            # Calculate Bollinger Bands score
            bb_score = self._calculate_bollinger_score(price_data, current_price)
            
            # Determine signal based on Bollinger Bands score
            if bb_score > 0.5:
                signal = "execute"
                logger.info(f"Bollinger Bands EXECUTE signal for trade {trade['trade_id']}: score {bb_score:.2f}")
            elif bb_score < -0.5:
                signal = "execute"
                logger.info(f"Bollinger Bands EXECUTE signal for trade {trade['trade_id']}: score {bb_score:.2f}")
            else:
                signal = "hold"
                logger.debug(f"Bollinger Bands HOLD signal for trade {trade['trade_id']}: score {bb_score:.2f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in Bollinger Bands analysis for trade {trade['trade_id']}: {e}", exc_info=True)
            return "hold"

    def _update_trade_signal(self, trade_id: int, signal: str) -> None:
        """Update the current_signal column for a trade."""
        try:
            trade_manager = self.db.get_trade_manager()
            # Only update if signal has changed to avoid unnecessary DB writes
            current_trade = trade_manager.get_trade_by_id(trade_id)
            if current_trade and current_trade.get('current_signal') != signal:
                trade_manager.update_trade_signal(trade_id, signal)
                logger.debug(f"Updated trade {trade_id} signal from '{current_trade.get('current_signal')}' to '{signal}'")
            else:
                logger.debug(f"Trade {trade_id} signal already '{signal}', no update needed")
        except Exception as e:
            logger.error(f"Error updating signal for trade {trade_id}: {e}", exc_info=True)

    def _get_trades_to_execute(self) -> List[Dict[str, Any]]:
        """Get all trades marked with current_signal = 'execute'."""
        try:
            trade_manager = self.db.get_trade_manager()
            return trade_manager.get_trades_by_signal('execute')
        except Exception as e:
            logger.error(f"Error fetching trades to execute: {e}", exc_info=True)
            return []

    def _validate_trades_for_execution(self, trades: List[Dict[str, Any]]) -> List[tuple[Dict[str, Any], Dict[str, Any]]]:
        """Phase 2: Validate trades for sufficient volume and acceptable price impact."""
        # Use TradeValidator service
        return self.trade_validator.validate_trades_for_execution(trades)

    def _execute_validated_trades(self, trades: List[tuple[Dict[str, Any], Dict[str, Any]]]) -> None:
        """Phase 3: Execute all validated trades with dynamic price re-validation.
        
        CRITICAL: Re-validates price after each execution to prevent race conditions
        where multiple trades on the same pair execute based on stale prices.
        """
        executed_pairs = {}  # Track {pair_id: last_execution_time}
        
        for trade, swap_data in trades:
            try:
                trade_id = trade.get('trade_id', 'unknown')
                pair_id = trade.get('trade_pair_id')
                
                # Check if we recently executed a trade on this same pair
                if pair_id in executed_pairs:
                    logger.warning(
                        f"Trade {trade_id}: Another trade on pair {pair_id} was just executed. "
                        f"Re-validating price to prevent race condition..."
                    )
                    
                    # Re-check if trade should still execute given potential price movement
                    strategy_name = trade.get('strategy_name', 'Manual')
                    indicator_settings_json = trade.get('indicator_settings_json', '{}')
                    current_signal = self._determine_trade_signal(trade, strategy_name, indicator_settings_json)
                    
                    if current_signal != "execute":
                        logger.warning(
                            f"Trade {trade_id}: SKIPPED - Signal changed from 'execute' to '{current_signal}' "
                            f"after previous trade execution moved the market. Preventing whale self-harpoon!"
                        )
                        # Update signal in database to reflect reality
                        self._update_trade_signal(trade_id, current_signal)
                        continue
                    
                    # Also re-validate price impact with fresh data
                    logger.info(f"Trade {trade_id}: Re-validating price impact after pair activity...")
                    is_valid, fresh_swap_data = self.trade_validator.validate_price_impact(trade)
                    
                    if not is_valid:
                        logger.warning(
                            f"Trade {trade_id}: SKIPPED - Price impact validation failed after "
                            f"market movement from previous execution"
                        )
                        self._update_trade_signal(trade_id, "hold")
                        continue
                    
                    # Use fresh swap data
                    if fresh_swap_data:
                        logger.info(f"Trade {trade_id}: Using fresh manifest after re-validation")
                        swap_data = fresh_swap_data
                
                # Execute the trade
                self._execute_single_trade(trade, swap_data)
                
                # Mark this pair as recently executed
                executed_pairs[pair_id] = True
                
            except Exception as e:
                logger.error(f"Error executing trade {trade.get('trade_id', 'unknown')}: {e}", exc_info=True)

    def _execute_single_trade(self, trade: Dict[str, Any], swap_data: Dict[str, Any]) -> None:
        """Execute a single trade by calling the swap API and updating the database."""
        trade_id = trade['trade_id']
        trade_amount = Decimal(trade['trade_amount'])
        logger.info(f"Executing trade {trade_id}")
        trade_logger.info(f"TRADE START | id={trade_id} | amount={trade_amount} | strategy={trade.get('strategy_name', 'unknown')}")

        try:
            # Get trade pair information
            trade_pair = self.db.get_trade_pair_by_id(trade['trade_pair_id'])
            if not trade_pair:
                logger.error(f"Trade pair not found for trade ID: {trade['trade_id']}")
                trade_logger.error(f"TRADE FAILED | id={trade_id} | reason=trade_pair_not_found")
                return

            # Determine trade direction based on which token we're currently holding
            trade_token_address = trade.get('trade_token_address') or trade['start_token_address']
            
            # Compare against the trade pair to determine which direction we're trading
            if trade_token_address == trade_pair['base_token']:
                # We're holding base token, sell base for quote
                token_from_address = trade_pair['base_token']   # What we're selling
                token_to_address = trade_pair['quote_token']    # What we're buying
            elif trade_token_address == trade_pair['quote_token']:
                # We're holding quote token, sell quote for base
                token_from_address = trade_pair['quote_token']  # What we're selling
                token_to_address = trade_pair['base_token']     # What we're buying
            else:
                logger.error(f"Trade {trade_id}: trade_token_address {trade_token_address} doesn't match base or quote in pair")
                trade_logger.error(f"TRADE FAILED | id={trade_id} | reason=token_mismatch | token={trade_token_address}")
                return

            # Example 2: For non-compounding trades where accumulation != start token,
            # calculate exact amount needed to get back to start_amount using the ratio from validation
            is_compounding = trade.get('is_compounding', False)
            start_token_address = trade.get('start_token_address')
            start_amount = Decimal(str(trade.get('start_amount', 0)))
            accumulation_token_address = trade.get('accumulation_token_address')
            
            # Get expected output from validation swap_data
            expected_output_from_validation = Decimal(str(swap_data.get('outputTokens', 0))) if 'outputTokens' in swap_data else None
            
            if not is_compounding and accumulation_token_address != start_token_address and expected_output_from_validation:
                # Check if we're trading back to start token
                if token_to_address == start_token_address:
                    # Use the ratio from validation to calculate required input
                    # validation showed: trade_amount input -> expected_output_from_validation output
                    # we want: required_input -> start_amount output
                    # So: required_input = start_amount * (trade_amount / expected_output_from_validation)
                    
                    if expected_output_from_validation > start_amount:
                        # We would get more than we need, calculate how much less to trade
                        required_amount = (start_amount * trade_amount) / expected_output_from_validation
                        
                        logger.info(f"Trade {trade_id}: Non-compounding adjustment")
                        logger.info(f"  Validation showed: {trade_amount} -> {expected_output_from_validation}")
                        logger.info(f"  Would exceed start_amount of {start_amount}")
                        logger.info(f"  Adjusted to: {required_amount} -> ~{start_amount}")
                        
                        # Update for execution
                        trade_amount = required_amount
                        trade['trade_amount'] = str(required_amount)
                        
                        # Re-fetch swap data with adjusted amount (ONE additional API call)
                        logger.debug(f"Trade {trade_id}: Fetching manifest for adjusted amount")
                        is_valid, new_swap_data = self.trade_validator.validate_price_impact(trade)
                        if is_valid and new_swap_data:
                            swap_data = new_swap_data
                            logger.info(f"Trade {trade_id}: Using adjusted manifest")
                        else:
                            logger.error(f"Trade {trade_id}: Failed to get manifest with adjusted amount")
                            return
                    else:
                        logger.debug(f"Trade {trade_id}: Output {expected_output_from_validation} <= start_amount {start_amount}, no adjustment needed")

            # Validate all parameters before API call
            wallet_address = self.wallet.get_active_address()
            
            # Check for None/empty values
            if not token_from_address:
                logger.error(f"Trade {trade['trade_id']}: token_from_address is None/empty")
                return False
            if not token_to_address:
                logger.error(f"Trade {trade['trade_id']}: token_to_address is None/empty")
                return False
            if not wallet_address:
                logger.error(f"Trade {trade['trade_id']}: wallet_address is None/empty")
                return False
            if trade_amount <= 0:
                logger.error(f"Trade {trade['trade_id']}: invalid trade_amount: {trade_amount}")
                return False

            # Extract expected output amount from swap response
            # Astrolescent API returns 'outputTokens' field
            if 'outputTokens' in swap_data:
                expected_output = Decimal(str(swap_data['outputTokens']))
                logger.debug(f"Expected output amount: {expected_output} tokens")
            else:
                logger.warning(f"'outputTokens' field not found in swap response for trade {trade_id}. Using input amount as fallback. {swap_data}")
                expected_output = trade_amount

            # Take snapshot of trade state before execution
            trade_manager = self.db.get_trade_manager()
            original_trade_state = trade_manager.get_trade_state_snapshot(trade_id)
            
            # CRITICAL FIX: Set signal to 'hold' IMMEDIATELY to prevent double execution
            # This prevents parallel monitor cycles from picking up the same trade during the 9-15 second transaction verification window
            try:
                cursor = self.db._conn.cursor()
                cursor.execute("""
                    UPDATE trades 
                    SET current_signal = 'hold',
                        last_signal_updated_at = ?
                    WHERE trade_id = ?
                """, (int(time.time()), trade_id))
                self.db._conn.commit()
                logger.info(f"Trade {trade_id}: Signal set to 'hold' before transaction submission (prevents race condition)")
            except Exception as signal_error:
                logger.error(f"Failed to set signal to 'hold' for trade {trade_id}: {signal_error}")
                # Don't abort - transaction will still proceed, but log the issue
            
            # Log raw Astrolescent manifest for debugging
            logger.debug(f"=== RAW ASTROLESCENT MANIFEST (Trade {trade_id}) ===\n{swap_data['manifest']}\n=== END RAW MANIFEST ===")
            
            # Sanitize manifest to ensure all decimals have max 18 places
            sanitized_manifest = self._sanitize_manifest_decimals(swap_data['manifest'])
            
            # Re-verify fee integrity before every trade (catches runtime tampering)
            try:
                verify_fee_integrity()
            except RuntimeError as e:
                logger.critical(f"Trade {trade_id}: Fee integrity check FAILED — {e}")
                trade_logger.error(f"TRADE FAILED | id={trade_id} | reason=fee_integrity_check_failed")
                return
            
            # Verify Astrolescent's manifest includes our fee component before signing
            if not verify_manifest_contains_fee(sanitized_manifest):
                logger.error(f"Trade {trade_id}: Manifest fee verification FAILED — aborting trade to protect fee integrity")
                trade_logger.error(f"TRADE FAILED | id={trade_id} | reason=manifest_fee_verification_failed")
                return
            
            # Dynamically estimate fee via preview, fall back to static config
            estimated_fee = self._preview_trade_fee(sanitized_manifest)
            
            if estimated_fee is not None:
                # Check if wallet can actually afford this fee
                available_xrd = self._get_available_xrd_for_fees()
                if available_xrd < float(estimated_fee):
                    self._pause_all_trades_insufficient_xrd(available_xrd, float(estimated_fee))
                    trade_logger.critical(f"TRADES PAUSED | reason=insufficient_xrd | available={available_xrd:.2f} | required={float(estimated_fee):.4f}")
                    return
                fee_lock = float(estimated_fee)
                logger.info(f"Trade {trade_id}: Using previewed fee lock: {fee_lock:.4f} XRD")
                trade_logger.info(f"TRADE FEE | id={trade_id} | fee_lock={fee_lock:.4f} XRD | source=preview")
            else:
                fee_lock = config.trade_fee_lock_xrd
                logger.warning(f"Trade {trade_id}: Fee preview failed, using static fallback: {fee_lock} XRD")
                trade_logger.warning(f"TRADE FEE | id={trade_id} | fee_lock={fee_lock} XRD | source=static_fallback")
            
            # Add fee locking to Astrolescent's manifest
            manifest_string = self._add_fee_lock_to_manifest(sanitized_manifest, fee_lock_amount=fee_lock)
            success, intent_hash = self._execute_trade_transaction(manifest_string)
            
            if not success:
                logger.error(f"Failed to execute trade transaction for trade {trade_id}")
                trade_logger.error(f"TRADE FAILED | id={trade_id} | reason=transaction_submission_failed")
                return

            # Verify transaction status
            transaction_builder = RadixTransactionBuilder(wallet=self.wallet)
            verification_result = transaction_builder.verify_transaction_status(intent_hash)
            status = verification_result.get('status', 'Unknown')
            
            if not verification_result.get('committed', False):
                logger.error(f"Trade {trade_id} transaction not committed. Status: {status}")
                
                # Log detailed error information if available
                if 'error' in verification_result:
                    logger.error(f"Transaction error details: {verification_result['error']}")
                if 'error_message' in verification_result:
                    logger.error(f"Error message: {verification_result['error_message']}")
                    
                # Rollback trade state if transaction was rejected
                if status == 'Rejected':
                    logger.info(f"Rolling back trade {trade_id} due to rejected transaction")
                    trade_manager.rollback_trade_execution(trade_id, original_trade_state)
                trade_logger.error(
                    f"TRADE FAILED | id={trade_id} | reason=not_committed | status={status} | tx={intent_hash}"
                )
                return

            trade_logger.info(
                f"TRADE COMMITTED | id={trade_id} | tx={intent_hash} | "
                f"sold={trade_amount} {token_from_address[:20]}... | "
                f"bought={expected_output} {token_to_address[:20]}... | "
                f"fee_lock={fee_lock}"
            )
            logger.info(f"Trade {trade_id} transaction committed successfully: {intent_hash}")
            
            # Update trade state in database (only after successful transaction)
            try:
                # Log the trade flip parameters BEFORE calling the update
                logger.debug(f"=== CALLING update_trade_after_execution for Trade {trade_id} ===")
                logger.debug(f"  token_from_address (sold): {token_from_address}")
                logger.debug(f"  token_to_address (bought): {token_to_address}")
                logger.debug(f"  amount_traded (sold): {trade_amount}")
                logger.debug(f"  expected_output (bought): {expected_output}")
                
                # Update basic trade information
                trade_manager.update_trade_after_execution(
                    trade_id=trade_id,
                    new_token_address=token_to_address,
                    new_amount=expected_output,
                    amount_traded=trade_amount,
                    price_impact=Decimal('0.02')  # Placeholder - should be calculated from swap_data
                )

                # Record trade flip
                history_recorded = False
                try:
                    # Debug trade_pair data to identify missing fields
                    logger.debug(f"Trade pair data for trade {trade_id}: {trade_pair}")
                    
                    # Extract token addresses from trade_pair
                    base_token = trade_pair['base_token']
                    quote_token = trade_pair['quote_token']
                    
                    # Look up actual token symbols from database
                    base_token_info = self.db.get_token_manager().get_token_by_address(base_token)
                    quote_token_info = self.db.get_token_manager().get_token_by_address(quote_token)
                    
                    base_symbol = base_token_info.get('symbol', 'Unknown') if base_token_info else 'Unknown'
                    quote_symbol = quote_token_info.get('symbol', 'Unknown') if quote_token_info else 'Unknown'
                    
                    logger.debug(f"Token symbols for trade_pair {trade['trade_pair_id']}: base={base_symbol}, quote={quote_symbol}")
                    
                    # Determine trade direction and amounts
                    # Base token is first in pair, quote token is second in pair
                    if token_to_address == trade_pair['base_token']:
                        # Trading quote -> base (e.g., XRD -> TOKEN)
                        side = 'BUY'
                        amount_base = float(expected_output)  # Amount of base token received
                        amount_quote = float(trade_amount)    # Amount of quote token spent
                        token_sold_address = quote_token
                        token_sold_amount = float(trade_amount)
                    else:
                        # Trading base -> quote (e.g., TOKEN -> XRD)
                        side = 'SELL'
                        amount_base = float(trade_amount)     # Amount of base token spent
                        amount_quote = float(expected_output) # Amount of quote token received
                        token_sold_address = base_token
                        token_sold_amount = float(trade_amount)
                    
                    # Calculate USD value based on the token being sold
                    usd_value = 0.0
                    try:
                        token_sold_info = self.db.get_token_manager().get_token_by_address(token_sold_address)
                        if token_sold_info and token_sold_info.get('token_price_usd'):
                            token_price_usd = float(token_sold_info['token_price_usd'])
                            usd_value = token_sold_amount * token_price_usd
                            logger.debug(f"USD value calculated: {token_sold_amount} tokens x ${token_price_usd} = ${usd_value:.2f}")
                        else:
                            logger.warning(f"No USD price available for token {token_sold_address}")
                    except Exception as price_error:
                        logger.error(f"Failed to calculate USD value: {price_error}", exc_info=True)
                    
                    # Calculate trade price (quote token per base token)
                    trade_price = 0.0
                    if amount_base > 0:
                        trade_price = amount_quote / amount_base
                        logger.debug(f"Trade price calculated: {amount_quote} quote / {amount_base} base = {trade_price:.6f} {quote_symbol}/{base_symbol}")
                    
                    trade_manager.record_trade_history({
                        'trade_id_original': trade_id,
                        'wallet_address': trade['wallet_address'],
                        'pair': f"{base_symbol}/{quote_symbol}",
                        'side': side,
                        'amount_base': amount_base,
                        'amount_quote': amount_quote,
                        'price': trade_price,
                        'usd_value': usd_value,
                        'timestamp': int(time.time()),
                        'status': 'SUCCESS',
                        'strategy_name': trade['strategy_name'],
                        'transaction_hash': intent_hash,
                        'created_at': int(time.time())
                    })
                    history_recorded = True
                    logger.info(f"Trade history recorded successfully for trade {trade_id}")
                except Exception as history_error:
                    logger.error(f"Failed to record trade history for trade {trade_id}: {history_error}", exc_info=True)
                    # Don't let history recording failure stop the trade update
                
                if history_recorded:
                    logger.info(f"Trade {trade_id} executed successfully and recorded in database")
                else:
                    logger.warning(f"Trade {trade_id} executed successfully but history recording failed")
                
            except Exception as e:
                logger.error(f"Failed to update database after successful trade {trade_id}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error executing trade {trade_id}: {e}", exc_info=True)
            trade_logger.error(f"TRADE FAILED | id={trade_id} | reason=unhandled_exception | error={e}")

    def _sanitize_manifest_decimals(self, manifest_string: str) -> str:
        """
        Sanitize manifest by truncating all decimal numbers to max 18 decimal places.
        Radix Engine only supports 18 decimal places maximum.
        """
        import re
        
        def truncate_decimal(match):
            """Truncate a decimal number to 18 places."""
            full_number = match.group(0)
            
            # Split into integer and decimal parts
            if '.' in full_number:
                parts = full_number.split('.')
                integer_part = parts[0]
                decimal_part = parts[1].rstrip('"')  # Remove trailing quote if present
                
                # Truncate to 18 decimal places
                if len(decimal_part) > 18:
                    decimal_part = decimal_part[:18]
                    logger.warning(f"Truncated decimal from {full_number} to {integer_part}.{decimal_part}")
                
                # Reconstruct
                result = f"{integer_part}.{decimal_part}"
                
                # Add back quote if it was there
                if full_number.endswith('"'):
                    result += '"'
                    
                return result
            else:
                return full_number
        
        # Match decimal numbers in Decimal("...") format
        # Matches: Decimal("0.00016078061270432991") or similar
        pattern = r'\d+\.\d+'
        sanitized = re.sub(pattern, truncate_decimal, manifest_string)
        
        return sanitized

    def _get_available_xrd_for_fees(self) -> float:
        """
        Calculate unallocated XRD available for transaction fees.
        
        Returns the wallet's XRD ledger balance minus XRD locked in trades.
        Uses the database (cached from last balance sync) to avoid extra network calls.
        """
        try:
            wallet_address = self.wallet.public_address
            cursor = self.db._conn.cursor()
            
            # Get wallet_id for this wallet
            cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
            wallet_row = cursor.fetchone()
            if not wallet_row:
                logger.warning("Could not find wallet_id for available XRD calculation")
                return 0.0
            wallet_id = wallet_row[0]
            
            # Get XRD ledger balance from token_balances (updated by balance sync service)
            cursor.execute(
                "SELECT balance FROM token_balances WHERE wallet_id = ? AND token_address = ?",
                (wallet_id, XRD_TOKEN_ADDRESS)
            )
            balance_row = cursor.fetchone()
            xrd_total = float(balance_row[0]) if balance_row else 0.0
            
            # Get XRD locked in trades (all trades — active or paused — represent committed funds)
            cursor.execute(
                "SELECT COALESCE(SUM(CAST(trade_amount AS REAL)), 0) FROM trades "
                "WHERE wallet_address = ? AND trade_token_address = ?",
                (wallet_address, XRD_TOKEN_ADDRESS)
            )
            locked_row = cursor.fetchone()
            xrd_locked = float(locked_row[0]) if locked_row else 0.0
            
            available = xrd_total - xrd_locked
            logger.debug(f"XRD for fees: total={xrd_total:.2f}, locked={xrd_locked:.2f}, available={available:.2f}")
            return available
            
        except Exception as e:
            logger.error(f"Error calculating available XRD for fees: {e}", exc_info=True)
            return 0.0

    def _preview_trade_fee(self, sanitized_manifest: str) -> Optional[Decimal]:
        """
        Preview the trade manifest to estimate the actual network fee.
        
        Uses the wallet's unallocated XRD (minus 10 XRD buffer, capped at 500 XRD)
        as the temporary fee lock for the preview. Applies the configured safety
        multiplier to the preview result.
        
        Args:
            sanitized_manifest: The Astrolescent manifest after decimal sanitization.
            
        Returns:
            Estimated safe fee lock amount (Decimal), or None if preview fails.
        """
        try:
            available_xrd = self._get_available_xrd_for_fees()
            
            # Keep 10 XRD buffer in wallet (shard state costs make zero-balance expensive)
            preview_lock = min(available_xrd - 10.0, 500.0)
            
            if preview_lock < 1.0:
                logger.warning(
                    f"Insufficient XRD for fee preview: available={available_xrd:.2f}, "
                    f"need at least 11 XRD (10 buffer + 1 minimum lock)"
                )
                return None
            
            # Build manifest with temporary fee lock for preview
            preview_manifest = self._add_fee_lock_to_manifest(sanitized_manifest, fee_lock_amount=preview_lock)
            
            # Preview the transaction
            from core.radix_network import RadixNetwork
            rn = RadixNetwork(network_id=self.tx_builder.network_id)
            
            current_epoch = rn.get_current_epoch()
            if current_epoch is None:
                logger.error("Could not get current epoch for fee preview")
                return None
            
            header = self.tx_builder.build_transaction_header(
                wallet=self.wallet,
                network_id=self.tx_builder.network_id,
                start_epoch=current_epoch
            )
            
            preview_response = rn.preview_transaction(preview_manifest, header)
            
            # Extract fee from preview response (same parsing as get_transaction_fee)
            receipt = preview_response.get('receipt', {})
            fee_source = receipt.get('fee_source', {})
            if not fee_source:
                logger.warning("No fee_source in preview response")
                return None
            
            from_vaults = fee_source.get('from_vaults', [])
            total_fee = Decimal('0')
            for vault in from_vaults:
                if isinstance(vault, dict):
                    xrd_amount = vault.get('xrd_amount', '0')
                    try:
                        total_fee += Decimal(str(xrd_amount))
                    except Exception as e:
                        logger.error(f"Error parsing preview fee xrd_amount '{xrd_amount}': {e}")
            
            if total_fee <= 0:
                logger.warning(f"Preview returned zero or negative fee: {total_fee}")
                return None
            
            # Apply safety multiplier
            multiplier = Decimal(str(config.trade_fee_multiplier))
            safe_fee = total_fee * multiplier
            
            logger.info(
                f"Trade fee preview: network_fee={total_fee:.4f} XRD × {multiplier} = {safe_fee:.4f} XRD "
                f"(available={available_xrd:.2f} XRD)"
            )
            
            return safe_fee
            
        except Exception as e:
            logger.error(f"Trade fee preview failed: {e}", exc_info=True)
            return None

    def _pause_all_trades_insufficient_xrd(self, available_xrd: float, required_fee: float):
        """
        Pause all active trades for this wallet when XRD is insufficient for fees.
        """
        wallet_address = self.wallet.public_address
        try:
            cursor = self.db._conn.cursor()
            cursor.execute(
                "UPDATE trades SET is_active = 0 WHERE wallet_address = ? AND is_active = 1",
                (wallet_address,)
            )
            paused_count = cursor.rowcount
            self.db._conn.commit()
            
            logger.critical(
                f"INSUFFICIENT XRD FOR FEES — ALL TRADES PAUSED. "
                f"Available: {available_xrd:.2f} XRD, Required fee: {required_fee:.4f} XRD. "
                f"Paused {paused_count} trade(s). "
                f"Top up XRD and reactivate trades manually."
            )
        except Exception as e:
            logger.error(f"Failed to pause trades due to insufficient XRD: {e}", exc_info=True)

    def _add_fee_lock_to_manifest(self, manifest_string: str, fee_lock_amount: float = None) -> str:
        """
        Add a fee lock to Astrolescent's manifest.
        Radix refunds any excess locked XRD back to the wallet.
        
        Args:
            manifest_string: The manifest to prepend the fee lock to.
            fee_lock_amount: XRD to lock. If None, falls back to config.trade_fee_lock_xrd.
        """
        account_address = self.wallet.get_active_address()
        
        if fee_lock_amount is None:
            fee_lock_amount = config.trade_fee_lock_xrd
        
        # Format matches Astrolescent's exactly: tabs, semicolon with space, blank line
        lock_fee_instruction = (
            f'CALL_METHOD\n'
            f'\tAddress("{account_address}")\n'
            f'\t"lock_fee"\n'
            f'\tDecimal("{fee_lock_amount}")\n'
            f'; \n\n'
        )
        
        # Prepend to Astrolescent's manifest
        return lock_fee_instruction + manifest_string

    def _execute_trade_transaction(self, manifest_string: str) -> tuple[bool, Optional[str]]:
        """
        Execute a trade transaction using the same pattern as withdrawals.
        Returns (success, intent_hash).
        """
        try:
            # Create notarized transaction like withdrawals do
            notarized_transaction, _, _ = self.tx_builder.create_notarized_transaction_for_manifest(
                manifest_string=manifest_string,
                sender_address=self.wallet.get_active_address()
            )
            
            # Submit transaction like withdrawals do
            from core.radix_network import RadixNetwork
            compiled_tx = notarized_transaction.to_payload_bytes().hex()
            logger.debug(f"Submitting compiled trade transaction: {compiled_tx}")

            rn = RadixNetwork(network_id=self.tx_builder.network_id)
            submission_response = rn.submit_transaction(compiled_tx)
            logger.info(f"Trade submission response: {submission_response}")

            if not submission_response or submission_response.get('duplicate'):
                intent_hash = notarized_transaction.intent_hash().as_str()
                if submission_response.get('duplicate'):
                    logger.warning(f"Trade transaction already submitted. TxID: {intent_hash}")
                    return True, intent_hash  # Still consider success if duplicate
                else:
                    logger.error("Trade submission failed: Unknown error")
                    return False, None

            intent_hash = notarized_transaction.intent_hash().as_str()
            logger.info(f"Trade transaction submitted successfully: {intent_hash}")
            return True, intent_hash

        except Exception as e:
            logger.error(f"Failed to execute trade transaction: {e}", exc_info=True)
            return False, None

    def _detect_market_regime(self, prices: List[Decimal]) -> str:
        """Detect if market is trending or ranging using price volatility and trend strength."""
        try:
            if len(prices) < 30:
                return "unknown"
            
            # Calculate recent volatility (last 20 periods)
            recent_prices = prices[-20:]
            price_changes = [abs(recent_prices[i] - recent_prices[i-1]) for i in range(1, len(recent_prices))]
            
            avg_volatility = sum(price_changes) / len(price_changes)
            
            # Calculate trend strength using linear regression slope
            x_values = list(range(len(recent_prices)))
            n = len(recent_prices)
            sum_x = sum(x_values)
            sum_y = sum(recent_prices)
            sum_xy = sum(x * float(y) for x, y in zip(x_values, recent_prices))
            sum_x2 = sum(x * x for x in x_values)
            
            # Linear regression slope
            slope = (n * sum_xy - sum_x * float(sum_y)) / (n * sum_x2 - sum_x * sum_x)
            
            # Normalize slope by average price
            avg_price = sum_y / n
            normalized_slope = abs(slope) / float(avg_price)
            
            # Determine regime based on trend strength and volatility
            if normalized_slope > 0.01 and avg_volatility > float(avg_price) * 0.02:
                return "trending"
            elif normalized_slope < 0.005 and avg_volatility < float(avg_price) * 0.015:
                return "ranging"
            else:
                return "transitional"
                
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return "unknown"

    def _calculate_signal_confidence(self, signals: List[float]) -> float:
        """Calculate confidence based on how much indicators agree."""
        try:
            if not signals:
                return 0.0
            
            # Count signals in same direction
            positive_signals = sum(1 for s in signals if s > 0.1)
            negative_signals = sum(1 for s in signals if s < -0.1)
            neutral_signals = len(signals) - positive_signals - negative_signals
            
            # Calculate agreement percentage
            max_agreement = max(positive_signals, negative_signals)
            agreement_ratio = max_agreement / len(signals)
            
            # Weight by signal strength
            avg_strength = sum(abs(s) for s in signals) / len(signals)
            
            # Confidence is agreement * strength
            confidence = agreement_ratio * avg_strength
            
            return min(confidence, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating signal confidence: {e}")
            return 0.0

    def _ai_calculate_rsi_signal(self, prices: List[Decimal], period: int, oversold: float, overbought: float) -> float:
        """Calculate RSI signal for AI strategy with custom parameters."""
        try:
            if len(prices) < period + 1:
                return 0.0
            
            # Calculate price changes (ensure all Decimal operations)
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            # Separate gains and losses (keep as Decimal)
            gains = [delta if delta > Decimal('0') else Decimal('0') for delta in deltas]
            losses = [-delta if delta < Decimal('0') else Decimal('0') for delta in deltas]
            
            # Calculate average gains and losses (convert to float for RSI calculation)
            avg_gain = float(sum(gains[-period:]) / period)
            avg_loss = float(sum(losses[-period:]) / period)
            
            # Calculate RSI
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Convert to signal (-1 to 1)
            if rsi <= oversold:
                return 1.0  # Oversold = buy signal
            elif rsi >= overbought:
                return -1.0  # Overbought = sell signal
            else:
                # Linear interpolation
                if rsi < 50:
                    return (oversold - rsi) / (oversold - 50)
                else:
                    return (overbought - rsi) / (overbought - 50)
                    
        except Exception as e:
            logger.error(f"Error calculating AI RSI signal: {e}")
            return 0.0

    def _ai_calculate_macd_signal(self, prices: List[Decimal], fast: int, slow: int, signal_period: int) -> float:
        """Calculate MACD signal for AI strategy with custom parameters."""
        try:
            if len(prices) < slow + signal_period:
                return 0.0
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(prices, fast)
            ema_slow = self._calculate_ema(prices, slow)
            
            if not ema_fast or not ema_slow:
                return 0.0
            
            # MACD line
            macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast, ema_slow)]
            
            # Signal line (EMA of MACD)
            macd_decimals = [Decimal(str(val)) for val in macd_line]
            signal_line = self._calculate_ema(macd_decimals, signal_period)
            
            if not signal_line or len(signal_line) < 2:
                return 0.0
            
            # Current MACD and signal values
            current_macd = macd_line[-1]
            current_signal = float(signal_line[-1])
            prev_macd = macd_line[-2] if len(macd_line) > 1 else current_macd
            prev_signal = float(signal_line[-2]) if len(signal_line) > 1 else current_signal
            
            # MACD crossover signal
            if current_macd > current_signal and prev_macd <= prev_signal:
                return 1.0  # Bullish crossover
            elif current_macd < current_signal and prev_macd >= prev_signal:
                return -1.0  # Bearish crossover
            else:
                # Momentum signal based on MACD position relative to signal
                diff = current_macd - current_signal
                # Normalize by average price for scaling
                avg_price = float(sum(prices[-10:]) / 10)
                normalized_diff = diff / avg_price
                return max(-1.0, min(1.0, normalized_diff * 10))  # Scale and clamp
                
        except Exception as e:
            logger.error(f"Error calculating AI MACD signal: {e}")
            return 0.0

    def _ai_calculate_ma_signal(self, prices: List[Decimal], current_price: Decimal, short_period: int, long_period: int) -> float:
        """Calculate Moving Average signal for AI strategy with custom parameters."""
        try:
            if len(prices) < long_period:
                return 0.0
            
            # Calculate short and long moving averages
            ma_short = sum(prices[-short_period:]) / short_period
            ma_long = sum(prices[-long_period:]) / long_period
            
            # Price position relative to MAs
            price_vs_short = (current_price - ma_short) / ma_short
            price_vs_long = (current_price - ma_long) / ma_long
            
            # MA crossover signal
            ma_cross = (ma_short - ma_long) / ma_long
            
            # Combine signals
            signal = float(price_vs_short + price_vs_long + ma_cross) / 3.0
            
            # Scale and clamp to [-1, 1]
            return max(-1.0, min(1.0, signal * 20))
            
        except Exception as e:
            logger.error(f"Error calculating AI MA signal: {e}")
            return 0.0

    def _ai_calculate_bb_signal(self, prices: List[Decimal], current_price: Decimal, period: int, std_dev: float) -> float:
        """Calculate Bollinger Bands signal for AI strategy with custom parameters."""
        try:
            if len(prices) < period:
                return 0.0
            
            # Calculate moving average and standard deviation
            recent_prices = prices[-period:]
            ma = sum(recent_prices) / period
            
            # Calculate standard deviation
            variance = sum((price - ma) ** 2 for price in recent_prices) / period
            std = variance ** Decimal('0.5')
            
            # Bollinger Bands
            upper_band = ma + (Decimal(str(std_dev)) * std)
            lower_band = ma - (Decimal(str(std_dev)) * std)
            
            # Position within bands
            if current_price <= lower_band:
                return 1.0  # Oversold, buy signal
            elif current_price >= upper_band:
                return -1.0  # Overbought, sell signal
            else:
                # Linear interpolation within bands
                band_width = upper_band - lower_band
                if band_width == 0:
                    return 0.0
                position = (current_price - ma) / (band_width / 2)
                return -float(position)  # Negative because higher = sell signal
                
        except Exception as e:
            logger.error(f"Error calculating AI BB signal: {e}")
            return 0.0
