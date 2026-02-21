import pandas as pd
import numpy as np
from typing import List
from models.data_models import Candle
from utils import candles_to_dataframe

class MarketRegimeDetector:
    """Detects current market regime (trending, ranging, volatile)."""
    
    def __init__(self, lookback_period: int = 50):
        """
        Initialize Market Regime Detector.
        
        Args:
            lookback_period: Number of candles to analyze (default: 50)
        """
        self.lookback_period = lookback_period
    
    def detect_regime(self, candles: List[Candle]) -> str:
        """
        Detect the current market regime.
        
        Returns:
            'trending_up', 'trending_down', 'ranging', or 'high_volatility'
        """
        df = candles_to_dataframe(candles)
        if df.empty or len(df) < self.lookback_period:
            return 'unknown'
        
        # Use recent data
        recent_df = df.tail(self.lookback_period)
        prices = recent_df['close']
        
        # Calculate metrics
        trend_strength = self._calculate_trend_strength(prices)
        volatility = self._calculate_volatility(recent_df)
        range_tightness = self._calculate_range_tightness(prices)
        
        # Classify regime
        if volatility > 0.7:
            return 'high_volatility'
        elif abs(trend_strength) > 0.6:
            return 'trending_up' if trend_strength > 0 else 'trending_down'
        elif range_tightness > 0.6:
            return 'ranging'
        else:
            # Mixed signals - default to trending if there's any trend
            if abs(trend_strength) > 0.3:
                return 'trending_up' if trend_strength > 0 else 'trending_down'
            return 'ranging'
    
    def _calculate_trend_strength(self, prices: pd.Series) -> float:
        """
        Calculate trend strength using linear regression.
        
        Returns:
            Value from -1 (strong downtrend) to 1 (strong uptrend)
        """
        if len(prices) < 10:
            return 0.0
        
        # Fit linear regression
        x = np.arange(len(prices))
        y = prices.values
        
        # Calculate slope
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared for confidence
        y_pred = slope * x + (y_mean - slope * x_mean)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Normalize slope to percentage change per period
        slope_percent = (slope / y_mean) * 100
        
        # Scale by R-squared (stronger trend = higher R-squared)
        trend_strength = np.tanh(slope_percent) * r_squared
        
        return float(np.clip(trend_strength, -1, 1))
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """
        Calculate normalized volatility.
        
        Returns:
            Value from 0 (low volatility) to 1 (high volatility)
        """
        if len(df) < 2:
            return 0.0
        
        # Calculate returns
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 2:
            return 0.0
        
        # Standard deviation of returns
        std_dev = returns.std()
        
        # Normalize (typical crypto std dev ranges from 0.01 to 0.10)
        normalized_vol = std_dev / 0.10
        
        return float(np.clip(normalized_vol, 0, 1))
    
    def _calculate_range_tightness(self, prices: pd.Series) -> float:
        """
        Calculate how tightly prices are ranging.
        
        Returns:
            Value from 0 (wide range) to 1 (tight range)
        """
        if len(prices) < 10:
            return 0.0
        
        # Calculate price range
        price_range = prices.max() - prices.min()
        mean_price = prices.mean()
        
        if mean_price == 0:
            return 0.0
        
        # Range as percentage of mean
        range_percent = (price_range / mean_price) * 100
        
        # Check how many times price crosses the middle
        middle = (prices.max() + prices.min()) / 2
        above_middle = (prices > middle).astype(int)
        crosses = (above_middle.diff().abs().sum())
        
        # More crosses + smaller range = tighter ranging
        cross_score = min(crosses / len(prices), 1.0)
        
        # Invert range percentage (smaller range = higher score)
        # Typical ranging markets have 5-15% range
        range_score = 1 - min(range_percent / 15, 1.0)
        
        # Combine both factors
        tightness = (cross_score * 0.6 + range_score * 0.4)
        
        return float(np.clip(tightness, 0, 1))
    
    def get_regime_weights(self, regime: str) -> dict:
        """
        Get recommended indicator weights for a given regime.
        
        Returns:
            Dictionary of indicator weights
        """
        if regime == 'trending_up' or regime == 'trending_down':
            return {
                'rsi': 0.8,
                'macd': 1.5,
                'bb': 0.7,
                'ma_cross': 1.4,
                'stoch_rsi': 0.9,
                'obv': 1.2,
                'roc': 1.3,
                'ichimoku': 1.1,
                'atr': 0.6
            }
        elif regime == 'ranging':
            return {
                'rsi': 1.4,
                'macd': 0.7,
                'bb': 1.5,
                'ma_cross': 0.6,
                'stoch_rsi': 1.3,
                'obv': 0.8,
                'roc': 0.7,
                'ichimoku': 0.9,
                'atr': 1.0
            }
        elif regime == 'high_volatility':
            return {
                'rsi': 1.0,
                'macd': 1.0,
                'bb': 1.2,
                'ma_cross': 0.8,
                'stoch_rsi': 1.0,
                'obv': 0.9,
                'roc': 1.1,
                'ichimoku': 1.0,
                'atr': 1.5
            }
        else:  # unknown or mixed
            return {
                'rsi': 1.0,
                'macd': 1.0,
                'bb': 1.0,
                'ma_cross': 1.0,
                'stoch_rsi': 1.0,
                'obv': 1.0,
                'roc': 1.0,
                'ichimoku': 1.0,
                'atr': 1.0
            }
