from enum import Enum
from typing import Final


class StrategyType(Enum):
    """Enumeration of available trading strategies."""
    
    PING_PONG = "Ping Pong"
    MANUAL = "Manual"
    AI_STRATEGY = "AI_Strategy"
    
    @classmethod
    def from_string(cls, strategy_name: str) -> 'StrategyType':
        """
        Convert a string to a StrategyType enum.
        
        Args:
            strategy_name: String representation of the strategy
            
        Returns:
            Corresponding StrategyType enum value
            
        Raises:
            ValueError: If strategy_name doesn't match any known strategy
        """
        # Normalize the input
        normalized = strategy_name.strip()
        
        # Try direct match first
        for strategy in cls:
            if strategy.value == normalized:
                return strategy
        
        # Try case-insensitive match for common variations
        normalized_lower = normalized.lower()
        if normalized_lower == "ping pong" or normalized_lower == "pingpong":
            return cls.PING_PONG
        elif normalized_lower == "manual":
            return cls.MANUAL
        elif "ai" in normalized_lower:
            return cls.AI_STRATEGY
            
        raise ValueError(f"Unknown strategy type: {strategy_name}")
    
    def is_ai_strategy(self) -> bool:
        """Check if this strategy is the AI Strategy."""
        return self == StrategyType.AI_STRATEGY
    
    def is_ping_pong(self) -> bool:
        """Check if this strategy is Ping Pong."""
        return self == StrategyType.PING_PONG
    
    def is_manual(self) -> bool:
        """Check if this strategy is Manual."""
        return self == StrategyType.MANUAL
    
    def uses_indicators(self) -> bool:
        """Check if strategy uses technical indicators."""
        return self in (StrategyType.MANUAL, StrategyType.AI_STRATEGY)
    
    def uses_kelly_sizing(self) -> bool:
        """Check if strategy uses Kelly criterion position sizing."""
        return self == StrategyType.AI_STRATEGY


# Legacy string constants for backward compatibility during migration
# TODO: Remove these once all code is migrated to use StrategyType enum
STRATEGY_PING_PONG: Final[str] = "Ping Pong"
STRATEGY_MANUAL: Final[str] = "Manual"
STRATEGY_AI: Final[str] = "AI_Strategy"


# Indicator type constants
class IndicatorType(Enum):
    """Enumeration of available technical indicators."""
    
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER_BANDS = "BB"
    MA_CROSS = "MA_CROSS"
    
    def get_display_name(self) -> str:
        """Get human-readable name for display."""
        display_names = {
            IndicatorType.RSI: "RSI",
            IndicatorType.MACD: "MACD",
            IndicatorType.BOLLINGER_BANDS: "Bollinger Bands",
            IndicatorType.MA_CROSS: "Moving Average Crossover"
        }
        return display_names.get(self, self.value)


# Signal constants
class SignalType(Enum):
    """Trade signal types."""
    
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    
    def __str__(self) -> str:
        return self.value
