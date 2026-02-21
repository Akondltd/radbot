import pandas as pd
from typing import List, Dict
from models.data_models import Candle
from utils import candles_to_dataframe

class IchimokuIndicator:
    """Ichimoku Cloud - Comprehensive trend and momentum indicator."""
    
    def __init__(self, tenkan_period: int = 9, kijun_period: int = 26, 
                 senkou_b_period: int = 52, displacement: int = 26):
        """
        Initialize Ichimoku indicator.
        
        Args:
            tenkan_period: Conversion line period (default: 9)
            kijun_period: Base line period (default: 26)
            senkou_b_period: Leading span B period (default: 52)
            displacement: Cloud displacement (default: 26)
        """
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement
    
    def _calculate_line(self, high: pd.Series, low: pd.Series, period: int) -> pd.Series:
        """Calculate Ichimoku line (midpoint of high/low over period)."""
        period_high = high.rolling(window=period).max()
        period_low = low.rolling(window=period).min()
        return (period_high + period_low) / 2
    
    def calculate(self, candles: List[Candle]) -> Dict[str, pd.Series]:
        """
        Calculate all Ichimoku components.
        
        Returns:
            Dictionary with keys: tenkan, kijun, senkou_a, senkou_b, chikou
        """
        df = candles_to_dataframe(candles)
        if df.empty or len(df) < self.senkou_b_period:
            return {
                'tenkan': pd.Series(dtype='float64'),
                'kijun': pd.Series(dtype='float64'),
                'senkou_a': pd.Series(dtype='float64'),
                'senkou_b': pd.Series(dtype='float64'),
                'chikou': pd.Series(dtype='float64')
            }
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        tenkan = self._calculate_line(high, low, self.tenkan_period)
        
        # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        kijun = self._calculate_line(high, low, self.kijun_period)
        
        # Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted forward
        senkou_a = ((tenkan + kijun) / 2).shift(self.displacement)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted forward
        senkou_b = self._calculate_line(high, low, self.senkou_b_period).shift(self.displacement)
        
        # Chikou Span (Lagging Span): Close shifted backward
        chikou = close.shift(-self.displacement)
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }
    
    def generate_signal(self, candles: List[Candle]) -> float:
        """
        Generate trading signal based on Ichimoku Cloud.
        
        Returns:
            Signal score from -1 (strong sell) to 1 (strong buy)
        """
        components = self.calculate(candles)
        
        tenkan = components['tenkan']
        kijun = components['kijun']
        senkou_a = components['senkou_a']
        senkou_b = components['senkou_b']
        
        if tenkan.empty or kijun.empty:
            return 0.0
        
        df = candles_to_dataframe(candles)
        current_price = df['close'].iloc[-1]
        
        # Get current values (handling NaN from shifts)
        current_tenkan = tenkan.iloc[-1] if not pd.isna(tenkan.iloc[-1]) else current_price
        current_kijun = kijun.iloc[-1] if not pd.isna(kijun.iloc[-1]) else current_price
        
        # Find the latest valid cloud values
        senkou_a_valid = senkou_a.dropna()
        senkou_b_valid = senkou_b.dropna()
        
        if senkou_a_valid.empty or senkou_b_valid.empty:
            # No cloud data yet, use TK cross only
            if current_tenkan > current_kijun:
                return 0.5
            elif current_tenkan < current_kijun:
                return -0.5
            return 0.0
        
        current_senkou_a = senkou_a_valid.iloc[-1]
        current_senkou_b = senkou_b_valid.iloc[-1]
        
        # Determine cloud color
        cloud_top = max(current_senkou_a, current_senkou_b)
        cloud_bottom = min(current_senkou_a, current_senkou_b)
        is_bullish_cloud = current_senkou_a > current_senkou_b
        
        # Generate signal based on multiple factors
        signal_strength = 0.0
        
        # 1. TK Cross (weight: 0.3)
        if current_tenkan > current_kijun:
            signal_strength += 0.3
        elif current_tenkan < current_kijun:
            signal_strength -= 0.3
        
        # 2. Price vs Cloud (weight: 0.4)
        if current_price > cloud_top:
            signal_strength += 0.4
        elif current_price < cloud_bottom:
            signal_strength -= 0.4
        
        # 3. Cloud color (weight: 0.3)
        if is_bullish_cloud:
            signal_strength += 0.3
        else:
            signal_strength -= 0.3
        
        return max(-1, min(1, signal_strength))
