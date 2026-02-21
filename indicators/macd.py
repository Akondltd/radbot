import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class MACDIndicator:
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, candles: List[Candle]) -> pd.DataFrame:
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.DataFrame({'macd': [], 'signal': [], 'histogram': []})
        price_series = df['close']

        ema_fast = price_series.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = price_series.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        return pd.DataFrame({'macd': macd_line, 'signal': signal_line, 'histogram': histogram})

    def generate_signals(self, candles: List[Candle]) -> pd.Series:
        macd_df = self.calculate(candles)
        if macd_df.empty:
            return pd.Series(dtype='int64')

        signals = pd.Series(0, index=macd_df.index)
        # Buy signal: MACD line crosses above signal line
        signals[(macd_df['macd'] > macd_df['signal']) & (macd_df['macd'].shift(1) < macd_df['signal'].shift(1))] = 1
        # Sell signal: MACD line crosses below signal line
        signals[(macd_df['macd'] < macd_df['signal']) & (macd_df['macd'].shift(1) > macd_df['signal'].shift(1))] = -1
        return signals.fillna(0)