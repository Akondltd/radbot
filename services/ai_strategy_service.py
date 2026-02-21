import logging
import threading
import time
import json
from typing import Dict, Any, List
import inspect

from database.trade_manager import TradeManager
from services.data_source import DataSource
from models.data_models import Candle
from indicators.rsi import RSIIndicator
from indicators.macd import MACDIndicator
from indicators.bollinger_bands import BollingerBandsIndicator
from indicators.moving_average_crossover import MovingAverageCrossoverIndicator

logger = logging.getLogger(__name__)

class AIStrategyService:
    def __init__(self, trade_manager: TradeManager, interval_seconds: int = 300):
        logger.info("AI Strategy Service Initializing")
        self.trade_manager = trade_manager
        self.data_source = DataSource()
        self.interval = interval_seconds
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            logger.warning("AI Strategy Service is already running.")
            return
        logger.info("AI Strategy Service Started")
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        logger.info("AI Strategy Service Stopping")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()
        logger.info("AI Strategy Service Stopped")

    def _run(self):
        while self.running:
            logger.info("AI Strategy Service running analysis cycle...")
            try:
                active_ai_trades = self.trade_manager.get_active_ai_trades()
                logger.info(f"Found {len(active_ai_trades)} active AI trades to analyze.")
                for trade in active_ai_trades:
                    self._process_trade(trade)
            except Exception as e:
                logger.error(f"Error in AI Strategy Service analysis cycle: {e}", exc_info=True)
            
            # Wait for the next interval
            time.sleep(self.interval)

    def _process_trade(self, trade: Dict[str, Any]):
        trade_id = trade['trade_id']
        trade_pair_id = trade['trade_pair_id']
        logger.info(f"Processing trade_id: {trade_id} for trade_pair_id: {trade_pair_id}")
        final_signal = 'ERROR'  # Default signal in case of unexpected failure

        try:
            indicator_settings = json.loads(trade['indicator_settings_json'])

            price_candles = self._get_price_history(trade_pair_id)
            if not price_candles or len(price_candles) < 50:  # Need enough data for longest MA
                logger.warning(f"Not enough price history for trade_pair_id {trade_pair_id} to calculate indicators. Found {len(price_candles)} candles.")
                final_signal = 'INSUFFICIENT_DATA'
            else:
                indicator_signals = self._calculate_indicators(price_candles, indicator_settings)
                if not indicator_signals:
                    logger.warning(f"No signals generated for trade_id {trade_id}. Defaulting to HOLD.")
                    final_signal = 'HOLD'
                else:
                    final_signal = self._aggregate_signals(indicator_signals)

            # Always update the signal and timestamp to provide a heartbeat.
            self.trade_manager.update_trade_signal(trade_id, final_signal)
            logger.info(f"Updated trade {trade_id} with signal: {final_signal}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse indicator settings for trade_id {trade_id}: {e}")
            self.trade_manager.update_trade_signal(trade_id, 'CONFIG_ERROR')
        except Exception as e:
            logger.error(f"Failed to process trade_id {trade_id}: {e}", exc_info=True)
            self.trade_manager.update_trade_signal(trade_id, 'PROCESS_ERROR')

    def _get_price_history(self, trade_pair_id: int) -> List[Candle]:
        """Fetches price history for a trade pair from the database."""
        logger.debug(f"Fetching price history for trade_pair_id: {trade_pair_id}")
        trade_pair_details = self.trade_manager.get_trade_pair_by_id(trade_pair_id)
        if not trade_pair_details:
            logger.error(f"Could not find trade pair details for trade_pair_id: {trade_pair_id}")
            return []

        token_a = trade_pair_details['base_token']
        token_b = trade_pair_details['quote_token']

        # Fetch last 200 candles to ensure enough data for indicators
        return self.data_source.get_historical_data(token_a, token_b, limit=200)

    def _calculate_indicators(self, price_candles: List[Candle], settings: Dict[str, Any]) -> Dict[str, str]:
        """Calculates all required indicators and returns their latest signals."""
        signals = {}
        indicator_map = {
            'RSI': RSIIndicator,
            'MACD': MACDIndicator,
            'BB': BollingerBandsIndicator,
            'MA_CROSS': MovingAverageCrossoverIndicator
        }

        for name, params in settings.items():
            if name in indicator_map:
                try:
                    indicator_class = indicator_map[name]
                    sig = inspect.signature(indicator_class.__init__)
                    valid_params = {k: v for k, v in params.items() if k in sig.parameters}

                    indicator = indicator_class(**valid_params)
                    signal_series = indicator.generate_signals(price_candles)

                    if not signal_series.empty:
                        last_signal_val = signal_series.iloc[-1]
                        if last_signal_val == 1:
                            signals[name] = 'BUY'
                        elif last_signal_val == -1:
                            signals[name] = 'SELL'
                        else:
                            signals[name] = 'HOLD'
                    else:
                        signals[name] = 'HOLD'  # Default to HOLD if no signal generated
                except Exception as e:
                    logger.error(f"Failed to calculate indicator {name}: {e}", exc_info=True)
                    signals[name] = 'ERROR'

        logger.debug(f"Calculated signals: {signals}")
        return signals

    def _aggregate_signals(self, indicator_signals: Dict[str, str]) -> str:
        """Aggregates multiple indicator signals into one using a simple vote."""
        logger.debug(f"Aggregating signals: {indicator_signals}")

        vote_map = {'BUY': 1, 'SELL': -1, 'HOLD': 0, 'ERROR': 0}
        votes = [vote_map.get(signal, 0) for signal in indicator_signals.values()]

        total_vote = sum(votes)

        if total_vote > 0:
            return 'BUY'
        elif total_vote < 0:
            return 'SELL'
        else:
            return 'HOLD'
