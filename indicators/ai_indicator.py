import pandas as pd
from typing import Dict, List, Tuple
from models.data_models import Candle, Signal
from utils import candles_to_dataframe
from indicators.rsi import RSIIndicator
from indicators.macd import MACDIndicator
from indicators.bollinger_bands import BollingerBandsIndicator
from indicators.moving_average_crossover import MovingAverageCrossoverIndicator

class AIIndicator:
    def __init__(self,
                 rsi_params=None,
                 macd_params=None,
                 bb_params=None,
                 mac_params=None,
                 weights=None,
                 smoothing_period=5):
        self.rsi = RSIIndicator(**(rsi_params or {}))
        self.macd = MACDIndicator(**(macd_params or {}))
        self.bb = BollingerBandsIndicator(**(bb_params or {}))
        self.mac = MovingAverageCrossoverIndicator(**(mac_params or {}))
        self.weights = weights or {'rsi':1.0, 'macd':1.0, 'bb':1.0, 'mac':1.0}
        self.smoothing_period = smoothing_period

    def _normalize_signal(self, series: pd.Series) -> pd.Series:
        # Scale signals to between -1 and 1
        if series.empty:
            return series
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series(0, index=series.index)
        return 2 * (series - min_val) / (max_val - min_val) - 1

    def calculate(self, candles: List[Candle]) -> Tuple[pd.Series, pd.DataFrame]:
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.Series(dtype='float64'), pd.DataFrame()
        price_series = df['close']

        signals = {}

        # RSI normalized: buy=1 when RSI low, sell=-1 when high
        rsi_vals = self.rsi.calculate(candles)
        rsi_signal = pd.Series(0, index=price_series.index)
        rsi_signal[rsi_vals < self.rsi.buy_threshold] = 1
        rsi_signal[rsi_vals > self.rsi.sell_threshold] = -1
        signals['rsi'] = self._normalize_signal(rsi_signal)

        # MACD normalized histogram
        macd_df = self.macd.calculate(candles)
        hist = macd_df['histogram'].fillna(0)
        signals['macd'] = self._normalize_signal(hist)

        # Bollinger Bands distance normalized: positive when price > middle band, negative when below
        bb_df = self.bb.calculate(candles)
        dist = (price_series - bb_df['middle_band']).fillna(0)
        signals['bb'] = self._normalize_signal(dist)

        # Moving Average Crossover signal
        mac_signal = self.mac.generate_signals(candles)
        signals['mac'] = mac_signal

        signals_df = pd.DataFrame(signals)

        # Weighted sum combined
        combined = sum(self.weights[name] * sig for name, sig in signals_df.items())

        # Smooth combined signal
        smoothed = combined.ewm(span=self.smoothing_period, adjust=False).mean()

        return smoothed.fillna(0), signals_df.fillna(0)

    def generate_signals(self, candles: List[Candle]) -> List[Signal]:
        composite, individual_signals_df = self.calculate(candles)
        if composite.empty:
            return []

        final_signals = []
        for timestamp, score in composite.items():
            signal_str = 'NEUTRAL'
            if score > 0.5:
                signal_str = 'BUY'
            elif score < -0.5:
                signal_str = 'SELL'

            metadata = individual_signals_df.loc[timestamp].to_dict() if timestamp in individual_signals_df.index else {}

            final_signals.append(
                Signal(
                    timestamp=int(timestamp.timestamp()),
                    signal=signal_str,
                    score=float(score),
                    metadata=metadata
                )
            )
        return final_signals