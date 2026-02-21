"""
Technical Indicator Calculations

Pure functions for calculating technical indicators from price data.
Extracted from TradeMonitor to reduce complexity and improve testability.

All functions are stateless and side-effect free.
"""

import logging
from decimal import Decimal
from typing import List, Optional

from config.config_loader import config

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Technical indicator calculations for trading signals.
    
    All methods are stateless calculations that take price data
    and return indicator scores or values.
    """
    
    @staticmethod
    def calculate_rsi(prices: List[Decimal], period: int = 14, 
                      buy_threshold: float = 30, sell_threshold: float = 70) -> float:
        """
        Calculate RSI (Relative Strength Index) score.
        
        Args:
            prices: List of price data (most recent last)
            period: RSI period (default: 14)
            buy_threshold: Buy signal threshold - RSI below this = buy (default: 30)
            sell_threshold: Sell signal threshold - RSI above this = sell (default: 70)
            
        Returns:
            Score from -1 to 1, where:
            -1 = strong sell (above sell_threshold)
            0 = neutral
            1 = strong buy (below buy_threshold)
        """
        try:
            if len(prices) < period + 1:
                logger.debug(f"Insufficient data for RSI: {len(prices)} prices, need {period + 1}")
                return 0.0
            
            # Calculate price changes
            changes = [float(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            
            # Separate gains and losses
            gains = [max(change, 0) for change in changes]
            losses = [abs(min(change, 0)) for change in changes]
            
            # Calculate average gain and loss over period
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            # Prevent division by zero
            if avg_loss == 0:
                rsi = 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Convert RSI to score (-1 to 1)
            if rsi <= buy_threshold:
                # Below buy threshold = buy signal (positive score)
                score = (buy_threshold - rsi) / buy_threshold
                score = min(score, 1.0)
            elif rsi >= sell_threshold:
                # Above sell threshold = sell signal (negative score)
                score = -(rsi - sell_threshold) / (100 - sell_threshold)
                score = max(score, -1.0)
            else:
                # Neutral zone
                if rsi < 50:
                    score = (rsi - buy_threshold) / (50 - buy_threshold) * 0.5
                else:
                    score = -(rsi - 50) / (sell_threshold - 50) * 0.5
            
            logger.debug(f"RSI calculation: {rsi:.2f} -> score {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def calculate_macd(prices: List[Decimal], fast_period: int = 12, 
                       slow_period: int = 26, signal_period: int = 9) -> float:
        """
        Calculate MACD (Moving Average Convergence Divergence) score.
        
        Args:
            prices: List of price data (most recent last)
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
            
        Returns:
            Score from -1 to 1, where:
            -1 = strong sell (bearish divergence)
            0 = neutral
            1 = strong buy (bullish convergence)
        """
        try:
            if len(prices) < slow_period:
                logger.debug(f"Insufficient data for MACD: {len(prices)} prices, need {slow_period}")
                return 0.0
            
            prices_float = [float(p) for p in prices]
            
            # Calculate EMAs
            fast_ema = TechnicalIndicators._calculate_ema(prices_float, fast_period)
            slow_ema = TechnicalIndicators._calculate_ema(prices_float, slow_period)
            
            # MACD line
            macd_line = fast_ema - slow_ema
            
            # Calculate signal line (EMA of MACD)
            # For simplicity, use SMA approximation
            recent_prices_len = min(signal_period, len(prices))
            recent_fast = [TechnicalIndicators._calculate_ema(prices_float[:i+1], fast_period) 
                          for i in range(len(prices) - recent_prices_len, len(prices))]
            recent_slow = [TechnicalIndicators._calculate_ema(prices_float[:i+1], slow_period) 
                          for i in range(len(prices) - recent_prices_len, len(prices))]
            recent_macd = [f - s for f, s in zip(recent_fast, recent_slow)]
            signal_line = sum(recent_macd) / len(recent_macd)
            
            # MACD histogram
            histogram = macd_line - signal_line
            
            # Convert to score
            # Normalize by recent price volatility
            price_range = max(prices_float[-20:]) - min(prices_float[-20:])
            if price_range > 0:
                normalized_histogram = histogram / price_range
                score = max(-1.0, min(1.0, normalized_histogram * 10))
            else:
                score = 0.0
            
            logger.debug(f"MACD calculation: histogram {histogram:.4f} -> score {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def calculate_moving_average(prices: List[Decimal], current_price: Decimal = None,
                                  short_period: int = None, long_period: int = None,
                                  period: int = 20) -> float:
        """
        Calculate Moving Average or MA Crossover score.
        
        If both short_period and long_period provided: MA Crossover (compares two MAs)
        If only period provided: Simple MA (compares price to MA)
        
        Args:
            prices: List of price data (most recent last)
            current_price: Current price (required for simple MA, optional for crossover)
            short_period: Short MA period for crossover (from MA_CROSS settings)
            long_period: Long MA period for crossover (from MA_CROSS settings)
            period: Single MA period for simple MA (default: 20)
            
        Returns:
            Score from -1 to 1, where:
            For MA Crossover:
                -1 = strong bearish (short MA below long MA)
                0 = neutral (MAs converging)
                1 = strong bullish (short MA above long MA)
            For Simple MA:
                -1 = price significantly below MA (sell)
                0 = price at MA (neutral)
                1 = price significantly above MA (buy)
        """
        try:
            # MA Crossover mode
            if short_period is not None and long_period is not None:
                if len(prices) < long_period:
                    logger.debug(f"Insufficient data for MA Cross: {len(prices)} prices, need {long_period}")
                    return 0.0
                
                prices_float = [float(p) for p in prices]
                
                # Calculate short and long MAs
                short_ma = sum(prices_float[-short_period:]) / short_period
                long_ma = sum(prices_float[-long_period:]) / long_period
                
                # Calculate percentage difference
                diff_pct = ((short_ma - long_ma) / long_ma) * 100
                
                # Convert to score (-1 to 1)
                # ±2% = full score
                score = diff_pct / 2.0
                score = max(-1.0, min(1.0, score))
                
                logger.debug(f"MA Cross: short_MA({short_period})={short_ma:.4f}, long_MA({long_period})={long_ma:.4f}, diff={diff_pct:.2f}% -> score {score:.2f}")
                return score
            
            # Simple MA mode (backward compatibility)
            else:
                if current_price is None:
                    logger.warning("Simple MA mode requires current_price")
                    return 0.0
                
                if len(prices) < period:
                    logger.debug(f"Insufficient data for MA: {len(prices)} prices, need {period}")
                    return 0.0
                
                # Calculate SMA
                ma = sum(float(p) for p in prices[-period:]) / period
                current = float(current_price)
                
                # Calculate percentage difference
                diff_pct = ((current - ma) / ma) * 100
                
                # Convert to score (-1 to 1)
                # ±2% = full score
                score = diff_pct / 2.0
                score = max(-1.0, min(1.0, score))
                
                logger.debug(f"MA calculation: current={current:.4f}, MA={ma:.4f}, diff={diff_pct:.2f}% -> score {score:.2f}")
                return score
            
        except Exception as e:
            logger.error(f"Error calculating MA: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[Decimal], current_price: Decimal,
                                   period: int = 20, std_dev: float = 2.0) -> float:
        """
        Calculate Bollinger Bands score.
        
        Args:
            prices: List of price data (most recent last)
            current_price: Current price to compare against bands
            period: Period for MA and std dev (default: 20)
            std_dev: Standard deviation multiplier (default: 2.0)
            
        Returns:
            Score from -1 to 1, where:
            -1 = price at/above upper band (sell)
            0 = price at middle band (neutral)
            1 = price at/below lower band (buy)
        """
        try:
            if len(prices) < period:
                logger.debug(f"Insufficient data for BB: {len(prices)} prices, need {period}")
                return 0.0
            
            recent_prices = [float(p) for p in prices[-period:]]
            
            # Calculate middle band (SMA)
            middle_band = sum(recent_prices) / period
            
            # Calculate standard deviation
            variance = sum((p - middle_band) ** 2 for p in recent_prices) / period
            std = variance ** 0.5
            
            # Calculate bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            current = float(current_price)
            
            # Calculate position within bands
            if std == 0:
                score = 0.0
            elif current <= lower_band:
                # At or below lower band = buy signal
                score = 1.0
            elif current >= upper_band:
                # At or above upper band = sell signal
                score = -1.0
            elif current < middle_band:
                # Between lower band and middle = partial buy
                score = (middle_band - current) / (middle_band - lower_band)
            else:
                # Between middle and upper band = partial sell
                score = -(current - middle_band) / (upper_band - middle_band)
            
            logger.debug(f"BB calculation: current={current:.4f}, bands=[{lower_band:.4f}, {middle_band:.4f}, {upper_band:.4f}] -> score {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def calculate_adx(prices: List[Decimal], period: int = None) -> Optional[float]:
        """
        Calculate ADX (Average Directional Index) to measure trend strength.
        
        ADX is a non-directional indicator that measures trend strength:
        - 0-25: Weak trend or ranging market
        - 25-50: Strong trend
        - 50-75: Very strong trend
        - 75-100: Extremely strong trend
        
        Args:
            prices: List of price data (most recent last)
            period: Period for ADX calculation (default from config)
            
        Returns:
            ADX value (0-100) or None if calculation fails
        """
        try:
            if period is None:
                period = config.adx_period
            
            min_data_points = period * 2
            if len(prices) < min_data_points:
                logger.debug(f"Insufficient data for ADX: {len(prices)} prices, need {min_data_points}")
                return None
            
            prices_float = [float(p) for p in prices]
            
            # Calculate directional movements
            plus_dm = []
            minus_dm = []
            
            for i in range(1, len(prices_float)):
                high_diff = prices_float[i] - prices_float[i-1]
                low_diff = prices_float[i-1] - prices_float[i]
                
                # +DM and -DM
                if high_diff > low_diff and high_diff > 0:
                    plus_dm.append(high_diff)
                    minus_dm.append(0)
                elif low_diff > high_diff and low_diff > 0:
                    plus_dm.append(0)
                    minus_dm.append(low_diff)
                else:
                    plus_dm.append(0)
                    minus_dm.append(0)
            
            # Calculate smoothed +DM and -DM
            smoothed_plus_dm = sum(plus_dm[-period:]) / period
            smoothed_minus_dm = sum(minus_dm[-period:]) / period
            
            # Calculate Average True Range (ATR) approximation
            true_ranges = [abs(prices_float[i] - prices_float[i-1]) for i in range(1, len(prices_float))]
            atr = sum(true_ranges[-period:]) / period
            
            if atr == 0:
                logger.debug(f"ADX returning 0.0: ATR is zero (no price movement in {period} periods)")
                logger.debug(f"  True ranges: {true_ranges[-5:] if len(true_ranges) >= 5 else true_ranges}")
                logger.debug(f"  Prices (last 5): {prices_float[-5:]}")
                return 0.0
            
            # Calculate +DI and -DI
            plus_di = (smoothed_plus_dm / atr) * 100
            minus_di = (smoothed_minus_dm / atr) * 100
            
            # Calculate DX for multiple periods to properly smooth ADX
            dx_values = []
            skipped_zero_tr = 0
            skipped_zero_di_sum = 0
            
            # Calculate DX for each period window
            for i in range(period, len(plus_dm) + 1):
                # Get smoothed values for this window
                window_plus_dm = sum(plus_dm[i-period:i]) / period
                window_minus_dm = sum(minus_dm[i-period:i]) / period
                window_tr = sum(true_ranges[i-period:i]) / period
                
                if window_tr == 0:
                    skipped_zero_tr += 1
                    continue
                
                # Calculate +DI and -DI for this window
                window_plus_di = (window_plus_dm / window_tr) * 100
                window_minus_di = (window_minus_dm / window_tr) * 100
                
                # Calculate DX for this window
                di_sum = window_plus_di + window_minus_di
                if di_sum > 0:
                    dx = (abs(window_plus_di - window_minus_di) / di_sum) * 100
                    dx_values.append(dx)
                else:
                    skipped_zero_di_sum += 1
            
            # Log if we skipped windows
            if skipped_zero_tr > 0 or skipped_zero_di_sum > 0:
                logger.debug(f"ADX calculation skipped {skipped_zero_tr} windows (zero TR), "
                            f"{skipped_zero_di_sum} windows (zero DI sum)")
            
            # Need at least 'period' DX values to calculate ADX
            if len(dx_values) < period:
                logger.debug(f"Insufficient DX values for ADX smoothing: {len(dx_values)}, need {period}")
                logger.debug(f"  plus_dm length: {len(plus_dm)}, minus_dm length: {len(minus_dm)}")
                logger.debug(f"  Calculated {len(dx_values)} DX values from {len(plus_dm)} DM values")
                if len(dx_values) > 0:
                    logger.debug(f"  DX values: {dx_values}")
                return None
            
            # Apply Wilder's smoothing to DX values
            # First ADX = simple average of first 'period' DX values
            adx = sum(dx_values[:period]) / period
            
            # Subsequent ADX values use Wilder's smoothing
            # ADX = ((prior ADX × (period - 1)) + current DX) / period
            for dx in dx_values[period:]:
                adx = ((adx * (period - 1)) + dx) / period
            
            # Calculate final +DI and -DI for logging (using most recent window)
            plus_di = (smoothed_plus_dm / atr) * 100
            minus_di = (smoothed_minus_dm / atr) * 100
            
            # Diagnostic logging for debugging ADX issues
            dx_stats = {
                'count': len(dx_values),
                'min': min(dx_values),
                'max': max(dx_values),
                'avg': sum(dx_values) / len(dx_values),
                'recent_5': dx_values[-5:] if len(dx_values) >= 5 else dx_values
            }
            logger.debug(f"ADX calculation: +DI={plus_di:.2f}, -DI={minus_di:.2f}, ADX={adx:.2f}")
            logger.debug(f"  DX values: count={dx_stats['count']}, min={dx_stats['min']:.2f}, "
                        f"max={dx_stats['max']:.2f}, avg={dx_stats['avg']:.2f}, "
                        f"recent_5={[f'{v:.1f}' for v in dx_stats['recent_5']]}")
            return float(adx)
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}", exc_info=True)
            return None
    
    @staticmethod
    def check_market_trending(prices: List[Decimal], threshold: float = None) -> bool:
        """
        Check if market is trending based on ADX.
        
        Args:
            prices: List of price data
            threshold: ADX threshold for trending (default from config)
            
        Returns:
            True if market is trending (ADX >= threshold), False otherwise
        """
        if threshold is None:
            threshold = config.adx_threshold
        
        adx = TechnicalIndicators.calculate_adx(prices)
        
        if adx is None:
            return True  # Allow trade if calculation fails (fail open)
        
        is_trending = adx >= threshold
        logger.debug(f"Market trending check: ADX={adx:.2f}, threshold={threshold} -> {'trending' if is_trending else 'ranging'}")
        
        return is_trending
    
    @staticmethod
    def _calculate_ema(prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: List of prices (most recent last)
            period: EMA period
            
        Returns:
            EMA value
        """
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
