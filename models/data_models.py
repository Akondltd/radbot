from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from decimal import Decimal

@dataclass
class Candle:
    """Represents a single OHLCV candle."""
    timestamp: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

@dataclass
class Signal:
    timestamp: int
    signal: str  # 'BUY', 'SELL', or 'NEUTRAL'
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Trade:
    """Represents an active trade managed by the bot."""
    trade_id: str
    pair: str
    start_token: str
    start_amount: Decimal
    is_active: bool = True
    strategy: str = "AI_Strategy"
    # Further fields for tracking P/L, current holdings, etc. to be added here.