import pandas as pd

class PingPongIndicator:
    def __init__(self, window: int = 14, threshold: float = 0.01):
        self.window = window
        self.threshold = threshold

    def generate_signals(self, price_series: pd.Series) -> pd.Series:
        rolling_max = price_series.rolling(window=self.window).max()
        rolling_min = price_series.rolling(window=self.window).min()
        signals = pd.Series(0, index=price_series.index)
        buy_zone = rolling_min * (1 + self.threshold)
        sell_zone = rolling_max * (1 - self.threshold)
        signals[price_series <= buy_zone] = 1
        signals[price_series >= sell_zone] = -1
        return signals.fillna(0)