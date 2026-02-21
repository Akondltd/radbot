import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class OBVIndicator:
    """On-Balance Volume - Volume-based momentum indicator."""
    
    def __init__(self, signal_period: int = 21):
        """
        Initialize OBV indicator.
        
        Args:
            signal_period: Period for signal line EMA (default: 21)
        """
        self.signal_period = signal_period
    
    def calculate(self, candles: List[Candle]) -> pd.Series:
        """
        Calculate OBV values.
        
        Returns:
            Series of OBV values
        """
        df = candles_to_dataframe(candles)
        if df.empty:
            return pd.Series(dtype='float64')
        
        # Calculate OBV
        obv = pd.Series(0.0, index=df.index)
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def generate_signal(self, candles: List[Candle]) -> float:
        """
        Generate trading signal based on OBV trend.
        
        Returns:
            Signal score from -1 (strong sell) to 1 (strong buy)
        """
        obv = self.calculate(candles)
        if obv.empty or len(obv) < self.signal_period + 5:
            return 0.0
        
        # Calculate signal line (EMA of OBV)
        signal = obv.ewm(span=self.signal_period, adjust=False).mean()
        
        # Get recent values
        current_obv = obv.iloc[-1]
        current_signal = signal.iloc[-1]
        prev_obv = obv.iloc[-2]
        prev_signal = signal.iloc[-2]
        
        # Check for crossovers
        if current_obv > current_signal and prev_obv <= prev_signal:
            return 1.0  # Bullish crossover
        elif current_obv < current_signal and prev_obv >= prev_signal:
            return -1.0  # Bearish crossover
        
        # Generate score based on divergence
        obv_slope = (obv.iloc[-1] - obv.iloc[-5]) / 5
        signal_slope = (signal.iloc[-1] - signal.iloc[-5]) / 5
        
        # Normalize slopes
        max_slope = max(abs(obv_slope), abs(signal_slope), 1)
        norm_obv_slope = obv_slope / max_slope
        norm_signal_slope = signal_slope / max_slope
        
        # Average of the two slopes
        score = (norm_obv_slope + norm_signal_slope) / 2
        
        return max(-1, min(1, score))
