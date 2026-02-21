import pandas as pd
from typing import List, Tuple
from models.data_models import Candle
from utils import candles_to_dataframe

class StochasticRSIIndicator:
    """Stochastic RSI - More sensitive momentum indicator combining RSI and Stochastic."""
    
    def __init__(self, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3):
        """
        Initialize Stochastic RSI indicator.
        
        Args:
            rsi_period: Period for RSI calculation (default: 14)
            stoch_period: Period for Stochastic calculation (default: 14)
            k_period: Period for %K smoothing (default: 3)
            d_period: Period for %D smoothing (default: 3)
        """
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.k_period = k_period
        self.d_period = d_period
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI values."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=self.rsi_period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=self.rsi_period, adjust=False).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate(self, candles: List[Candle]) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic RSI values.
        
        Returns:
            Tuple of (%K, %D) Series
        """
        df = candles_to_dataframe(candles)
        if df.empty or len(df) < self.rsi_period + self.stoch_period:
            return pd.Series(dtype='float64'), pd.Series(dtype='float64')
        
        # Calculate RSI
        rsi = self._calculate_rsi(df['close'])
        
        # Calculate Stochastic of RSI
        rsi_min = rsi.rolling(window=self.stoch_period).min()
        rsi_max = rsi.rolling(window=self.stoch_period).max()
        
        stoch_rsi = 100 * (rsi - rsi_min) / (rsi_max - rsi_min)
        
        # Smooth with %K
        k = stoch_rsi.rolling(window=self.k_period).mean()
        
        # Calculate %D (signal line)
        d = k.rolling(window=self.d_period).mean()
        
        return k, d
    
    def generate_signal(self, candles: List[Candle], oversold: float = 20, overbought: float = 80) -> float:
        """
        Generate trading signal based on Stochastic RSI.
        
        Args:
            oversold: Oversold threshold (default: 20)
            overbought: Overbought threshold (default: 80)
        
        Returns:
            Signal score from -1 (strong sell) to 1 (strong buy)
        """
        k, d = self.calculate(candles)
        if k.empty or d.empty:
            return 0.0
        
        current_k = k.iloc[-1]
        current_d = d.iloc[-1]
        
        # Check for crossovers
        if len(k) >= 2:
            prev_k = k.iloc[-2]
            prev_d = d.iloc[-2]
            
            # Bullish crossover in oversold territory
            if current_k > current_d and prev_k <= prev_d and current_k < oversold:
                return 1.0
            
            # Bearish crossover in overbought territory
            if current_k < current_d and prev_k >= prev_d and current_k > overbought:
                return -1.0
        
        # Generate score based on position
        if current_k < oversold:
            # Oversold - buy signal
            return 0.5 + (oversold - current_k) / oversold * 0.5
        elif current_k > overbought:
            # Overbought - sell signal
            return -0.5 - (current_k - overbought) / (100 - overbought) * 0.5
        else:
            # Neutral zone - interpolate
            mid = 50
            if current_k < mid:
                return (current_k - oversold) / (mid - oversold) * 0.5
            else:
                return -(current_k - mid) / (overbought - mid) * 0.5
