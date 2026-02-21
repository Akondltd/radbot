import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from models.data_models import Candle

from indicators.rsi import RSIIndicator
from indicators.macd import MACDIndicator
from indicators.bollinger_bands import BollingerBandsIndicator
from indicators.moving_average_crossover import MovingAverageCrossoverIndicator
from indicators.atr import ATRIndicator
from indicators.stochastic_rsi import StochasticRSIIndicator
from indicators.roc import ROCIndicator
from indicators.ichimoku import IchimokuIndicator
from indicators.market_regime import MarketRegimeDetector

class EnhancedAIIndicator:
    """Enhanced AI trading indicator with adaptive learning."""
    
    def __init__(self, parameters: Dict = None):
        """
        Initialize enhanced AI indicator.
        
        Args:
            parameters: Dict with execution_threshold, confidence_threshold, and weights
        """
        self.parameters = parameters or self._get_default_parameters()
        
        # Initialize all indicators
        self.rsi = RSIIndicator()
        self.macd = MACDIndicator()
        self.bb = BollingerBandsIndicator()
        self.ma_cross = MovingAverageCrossoverIndicator()
        self.atr = ATRIndicator()
        self.stoch_rsi = StochasticRSIIndicator()
        self.roc = ROCIndicator()
        self.ichimoku = IchimokuIndicator()
        self.regime_detector = MarketRegimeDetector()
        
        # Extract parameters
        self.execution_threshold = self.parameters.get('execution_threshold', 0.6)
        self.confidence_threshold = self.parameters.get('confidence_threshold', 0.7)
        self.base_weights = self.parameters.get('weights', {})
    
    def generate_signal(self, candles: List[Candle]) -> Tuple[float, float, str]:
        """
        Generate trading signal with enhanced indicators.
        
        Returns:
            Tuple of (composite_score, confidence, market_regime)
        """
        if len(candles) < 100:
            return 0.0, 0.0, 'unknown'
        
        # Detect market regime
        regime = self.regime_detector.detect_regime(candles)
        
        # Get regime-adjusted weights
        regime_weights = self.regime_detector.get_regime_weights(regime)
        
        # Combine base weights with regime weights
        final_weights = {}
        for indicator in ['rsi', 'macd', 'bb', 'ma_cross', 'stoch_rsi', 'roc', 'ichimoku']:
            base_weight = self.base_weights.get(indicator, 1.0)
            regime_weight = regime_weights.get(indicator, 1.0)
            final_weights[indicator] = base_weight * regime_weight
        
        # Calculate scores from each indicator
        indicator_scores = {}
        
        try:
            # RSI
            rsi_vals = self.rsi.calculate(candles)
            if not rsi_vals.empty:
                rsi_val = rsi_vals.iloc[-1]
                if rsi_val < 30:
                    indicator_scores['rsi'] = 1.0
                elif rsi_val > 70:
                    indicator_scores['rsi'] = -1.0
                else:
                    indicator_scores['rsi'] = (50 - rsi_val) / 20
            else:
                indicator_scores['rsi'] = 0.0
        except Exception:
            indicator_scores['rsi'] = 0.0
        
        try:
            # MACD
            macd_df = self.macd.calculate(candles)
            if not macd_df.empty:
                hist = macd_df['histogram'].iloc[-1]
                # Normalize histogram
                indicator_scores['macd'] = np.tanh(hist * 10)
            else:
                indicator_scores['macd'] = 0.0
        except Exception:
            indicator_scores['macd'] = 0.0
        
        try:
            # Bollinger Bands
            bb_df = self.bb.calculate(candles)
            if not bb_df.empty:
                current_price = candles[-1].close
                upper = bb_df['upper_band'].iloc[-1]
                lower = bb_df['lower_band'].iloc[-1]
                middle = bb_df['middle_band'].iloc[-1]
                
                # Check for valid band width (avoid division by zero)
                band_width = upper - middle
                if band_width < 0.0001:  # Bands are collapsed
                    indicator_scores['bb'] = 0.0
                elif current_price < lower:
                    indicator_scores['bb'] = 1.0  # Oversold
                elif current_price > upper:
                    indicator_scores['bb'] = -1.0  # Overbought
                else:
                    # Distance from middle normalized
                    indicator_scores['bb'] = -(current_price - middle) / band_width
            else:
                indicator_scores['bb'] = 0.0
        except Exception:
            indicator_scores['bb'] = 0.0
        
        try:
            # Moving Average Crossover
            ma_signal = self.ma_cross.generate_signals(candles)
            if ma_signal:
                indicator_scores['ma_cross'] = ma_signal.iloc[-1] if hasattr(ma_signal, 'iloc') else 0.0
            else:
                indicator_scores['ma_cross'] = 0.0
        except Exception:
            indicator_scores['ma_cross'] = 0.0
        
        try:
            # Stochastic RSI
            indicator_scores['stoch_rsi'] = self.stoch_rsi.generate_signal(candles)
        except Exception:
            indicator_scores['stoch_rsi'] = 0.0
        
        try:
            # ROC
            indicator_scores['roc'] = self.roc.generate_signal(candles)
        except Exception:
            indicator_scores['roc'] = 0.0
        
        try:
            # Ichimoku
            indicator_scores['ichimoku'] = self.ichimoku.generate_signal(candles)
        except Exception:
            indicator_scores['ichimoku'] = 0.0
        
        # Calculate weighted composite score
        total_weight = sum(final_weights.values())
        composite_score = sum(
            indicator_scores.get(name, 0) * final_weights.get(name, 0)
            for name in final_weights.keys()
        ) / total_weight if total_weight > 0 else 0.0
        
        # Check for NaN in composite score
        if np.isnan(composite_score) or np.isinf(composite_score):
            composite_score = 0.0
        
        # Calculate confidence based on indicator agreement
        scores = [s for s in indicator_scores.values() if not np.isnan(s) and not np.isinf(s)]
        if scores and len(scores) > 1:
            # Confidence is higher when indicators agree
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # Lower std = higher agreement = higher confidence
            confidence = 1.0 - min(std_score / 2.0, 1.0)
            
            # Check for NaN in confidence
            if np.isnan(confidence) or np.isinf(confidence):
                confidence = 0.0
        else:
            confidence = 0.0
        
        return float(composite_score), float(confidence), regime
    
    def _get_default_parameters(self) -> Dict:
        """Get default parameters."""
        return {
            'execution_threshold': 0.6,
            'confidence_threshold': 0.7,
            'weights': {
                'rsi': 1.0,
                'macd': 1.0,
                'bb': 1.0,
                'ma_cross': 1.0,
                'stoch_rsi': 1.0,
                'roc': 1.0,
                'ichimoku': 1.0
            }
        }
