"""
Constants package for RadBot.

Centralizes all constant values, enums, and configuration-related
types to ensure consistency across the application.
"""

from .strategy_types import (
    StrategyType,
    IndicatorType,
    SignalType,
    STRATEGY_PING_PONG,
    STRATEGY_MANUAL,
    STRATEGY_AI,
)

__all__ = [
    'StrategyType',
    'IndicatorType',
    'SignalType',
    'STRATEGY_PING_PONG',
    'STRATEGY_MANUAL',
    'STRATEGY_AI',
]
