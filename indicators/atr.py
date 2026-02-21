import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class ATRIndicator:
    """Average True Range - Measures market volatility."""
    
    def __init__(self, period: int = 14):
        """
        Initialize ATR indicator.
        
        Args:
            period: Period for ATR calculation (default: 14)
        """
        self.period = period
    
    def calculate(self, candles: List[Candle]) -> pd.Series:
        """
        Calculate ATR values.
        
        Returns:
            Series of ATR values
        """
        df = candles_to_dataframe(candles)
        if df.empty or len(df) < self.period:
            return pd.Series(dtype='float64')
        
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATR using exponential moving average
        atr = true_range.ewm(span=self.period, adjust=False).mean()
        
        return atr
    
    def get_volatility_score(self, candles: List[Candle]) -> float:
        """
        Get normalized volatility score (-1 to 1).
        
        Returns:
            Volatility score where higher values = higher volatility
        """
        atr = self.calculate(candles)
        if atr.empty:
            return 0.0
        
        df = candles_to_dataframe(candles)
        current_price = df['close'].iloc[-1]
        current_atr = atr.iloc[-1]
        
        # ATR as percentage of price
        atr_percent = (current_atr / current_price) * 100
        
        # Normalize to -1 to 1 range
        # Typical ATR% ranges from 1% (low volatility) to 10% (high volatility)
        normalized = (atr_percent - 1) / 9
        return max(-1, min(1, normalized))
