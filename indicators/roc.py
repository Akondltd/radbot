import pandas as pd
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class ROCIndicator:
    """Rate of Change - Momentum indicator measuring price change percentage."""
    
    def __init__(self, period: int = 12):
        """
        Initialize ROC indicator.
        
        Args:
            period: Lookback period for ROC calculation (default: 12)
        """
        self.period = period
    
    def calculate(self, candles: List[Candle]) -> pd.Series:
        """
        Calculate ROC values.
        
        Returns:
            Series of ROC percentage values
        """
        df = candles_to_dataframe(candles)
        if df.empty or len(df) < self.period + 1:
            return pd.Series(dtype='float64')
        
        # ROC = ((Close - Close[n periods ago]) / Close[n periods ago]) * 100
        roc = ((df['close'] - df['close'].shift(self.period)) / df['close'].shift(self.period)) * 100
        
        return roc
    
    def generate_signal(self, candles: List[Candle], threshold: float = 5.0) -> float:
        """
        Generate trading signal based on ROC.
        
        Args:
            threshold: ROC threshold for strong signals (default: 5.0%)
        
        Returns:
            Signal score from -1 (strong sell) to 1 (strong buy)
        """
        roc = self.calculate(candles)
        if roc.empty:
            return 0.0
        
        current_roc = roc.iloc[-1]
        
        # Check for zero crossovers (momentum shift)
        if len(roc) >= 2:
            prev_roc = roc.iloc[-2]
            
            # Bullish crossover (negative to positive)
            if current_roc > 0 and prev_roc <= 0:
                return 0.8
            
            # Bearish crossover (positive to negative)
            if current_roc < 0 and prev_roc >= 0:
                return -0.8
        
        # Generate score based on ROC magnitude
        if abs(current_roc) <= threshold:
            # Within threshold - weak signal
            score = current_roc / threshold * 0.5
        else:
            # Beyond threshold - strong signal
            if current_roc > 0:
                score = 0.5 + min((current_roc - threshold) / threshold * 0.5, 0.5)
            else:
                score = -0.5 - min((abs(current_roc) - threshold) / threshold * 0.5, 0.5)
        
        return max(-1, min(1, score))
