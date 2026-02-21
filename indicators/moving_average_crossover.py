import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class MovingAverageCrossoverIndicator:
    def __init__(self, short_period: int = 20, long_period: int = 50):
        self.short_period = short_period
        self.long_period = long_period

    def calculate(self, candles: List[Candle]) -> pd.DataFrame:
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.DataFrame({'short_ma': [], 'long_ma': []})
        price_series = df['close']

        short_ma = price_series.rolling(window=self.short_period).mean()
        long_ma = price_series.rolling(window=self.long_period).mean()
        return pd.DataFrame({'short_ma': short_ma, 'long_ma': long_ma})

    def generate_signals(self, candles: List[Candle]) -> pd.Series:
        ma_df = self.calculate(candles)
        if ma_df.empty:
            return pd.Series(dtype='int64')

        signals = pd.Series(0, index=ma_df.index)
        # Golden cross (buy signal)
        signals[(ma_df['short_ma'] > ma_df['long_ma']) & (ma_df['short_ma'].shift(1) < ma_df['long_ma'].shift(1))] = 1
        # Death cross (sell signal)
        signals[(ma_df['short_ma'] < ma_df['long_ma']) & (ma_df['short_ma'].shift(1) > ma_df['long_ma'].shift(1))] = -1
        return signals.fillna(0)