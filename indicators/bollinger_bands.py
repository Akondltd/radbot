import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class BollingerBandsIndicator:
    def __init__(self, period: int = 20, std_dev_multiplier: float = 2.0):
        self.period = period
        self.std_dev_multiplier = std_dev_multiplier

    def calculate(self, candles: List[Candle]) -> pd.DataFrame:
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.DataFrame({'middle_band': [], 'upper_band': [], 'lower_band': []})
        price_series = df['close']

        middle_band = price_series.rolling(window=self.period).mean()
        rolling_std = price_series.rolling(window=self.period).std()
        upper_band = middle_band + (rolling_std * self.std_dev_multiplier)
        lower_band = middle_band - (rolling_std * self.std_dev_multiplier)
        return pd.DataFrame({'middle_band': middle_band, 'upper_band': upper_band, 'lower_band': lower_band})

    def generate_signals(self, candles: List[Candle]) -> pd.Series:
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.Series(dtype='int64')
        price_series = df['close']

        bb_df = self.calculate(candles)
        if bb_df.empty:
            return pd.Series(dtype='int64')

        signals = pd.Series(0, index=price_series.index)
        signals[price_series < bb_df['lower_band']] = 1
        signals[price_series > bb_df['upper_band']] = -1
        return signals.fillna(0)