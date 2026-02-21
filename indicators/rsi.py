import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class RSIIndicator:
    def __init__(self, period: int = 14, buy_threshold: float = 30.0, sell_threshold: float = 70.0):
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def calculate(self, candles: List[Candle]) -> pd.Series:
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.Series(dtype='float64')
        price_series = df['close']

        delta = price_series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(0)

    def generate_signals(self, candles: List[Candle]) -> pd.Series:
        rsi_values = self.calculate(candles)
        if rsi_values.empty:
            return pd.Series(dtype='int64')

        signals = pd.Series(0, index=rsi_values.index)
        signals[rsi_values < self.buy_threshold] = 1
        signals[rsi_values > self.sell_threshold] = -1
        return signals.fillna(0)