"""
Configuration loader for RadBot.

Loads and provides access to configuration values from advanced_config.json.
Handles JSON with comments (JSONC format) by stripping comments before parsing.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from config.paths import USER_CONFIG

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages application configuration."""
    
    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        """Singleton pattern to ensure one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize config loader if not already initialized."""
        if not self._config:
            self.reload()
    
    def reload(self) -> None:
        """(Re)load configuration from file."""
        config_path = USER_CONFIG
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Strip comments (lines starting with //) to support JSONC format
            content = self._strip_comments(content)
            
            self._config = json.loads(content)
            logger.info(f"Configuration loaded from {config_path}")
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = self._get_default_config()
    
    @staticmethod
    def _strip_comments(json_content: str) -> str:
        """
        Remove // style comments from JSON content.
        
        Args:
            json_content: JSON string potentially containing comments
            
        Returns:
            JSON string with comments removed
        """
        # Remove // comments but preserve URLs (http://, https://)
        # This regex matches // not preceded by : (to keep URLs)
        pattern = r'(?<!:)//.*?$'
        return re.sub(pattern, '', json_content, flags=re.MULTILINE)
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            *keys: Path to the config value (e.g., 'strategies', 'kelly', 'fractional_multiplier')
            default: Default value if key path not found
            
        Returns:
            Configuration value or default
            
        Example:
            config.get('strategies', 'kelly', 'fractional_multiplier')  # Returns 0.25
        """
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            "trade_pairs": {
                "min_volume_7d": 50000,
                "min_price_impact": 5,
                "test_amount_xrd": 2000,
                "update_interval": 10
            },
            "api": {
                "rate_limit": 10,
                "retry_attempts": 3,
                "retry_delay": 5
            },
            "logging": {
                "level": "INFO",
                "max_size": 10000000,
                "backup_count": 5
            },
            "stops": {
                "stop_loss_percentage": 5.0,
                "trailing_stop_percentage": 3.0
            },
            "strategies": {
                "kelly": {
                    "fractional_multiplier": 0.25,
                    "min_position_size": 0.10,
                    "max_position_size": 1.0,
                    "min_trades_required": 10,
                    "lookback_trades": 20
                },
                "manual": {
                    "adx_threshold": 25,
                    "adx_period": 14
                },
                "ping_pong": {
                    "price_tolerance": 0.00
                }
            }
        }
    
    # Convenience properties for commonly accessed values
    
    @property
    def kelly_fractional_multiplier(self) -> float:
        """Kelly criterion fractional multiplier."""
        return self.get('strategies', 'kelly', 'fractional_multiplier', default=0.25)
    
    @property
    def kelly_min_position_size(self) -> float:
        """Minimum Kelly position size."""
        return self.get('strategies', 'kelly', 'min_position_size', default=0.10)
    
    @property
    def kelly_max_position_size(self) -> float:
        """Maximum Kelly position size."""
        return self.get('strategies', 'kelly', 'max_position_size', default=1.0)
    
    @property
    def kelly_min_trades_required(self) -> int:
        """Minimum trades required for Kelly calculation."""
        return self.get('strategies', 'kelly', 'min_trades_required', default=10)
    
    @property
    def kelly_lookback_trades(self) -> int:
        """Number of trades to analyze for Kelly calculation."""
        return self.get('strategies', 'kelly', 'lookback_trades', default=20)
    
    @property
    def adx_threshold(self) -> int:
        """ADX threshold for trend detection."""
        return self.get('strategies', 'manual', 'adx_threshold', default=25)
    
    @property
    def adx_period(self) -> int:
        """Period for ADX calculation."""
        return self.get('strategies', 'manual', 'adx_period', default=14)
    
    @property
    def ai_execution_threshold(self) -> float:
        """AI Strategy minimum signal strength to execute (0-1)."""
        return self.get('strategies', 'ai_strategy', 'execution_threshold', default=0.6)
    
    @property
    def ai_confidence_threshold(self) -> float:
        """AI Strategy minimum confidence level required (0-1)."""
        return self.get('strategies', 'ai_strategy', 'confidence_threshold', default=0.7)
    
    @property
    def ai_min_flip_interval_minutes(self) -> int:
        """AI Strategy cooldown period between flips in minutes."""
        return self.get('strategies', 'ai_strategy', 'min_flip_interval_minutes', default=60)
    
    @property
    def min_volume_7d(self) -> int:
        """Minimum 7-day volume for token pairs."""
        return self.get('trade_pairs', 'min_volume_7d', default=50000)
    
    @property
    def max_price_impact(self) -> float:
        """Maximum price impact percentage."""
        return self.get('trade_pairs', 'min_price_impact', default=5.0)
    
    @property
    def stop_loss_percentage(self) -> float:
        """Stop loss percentage."""
        return self.get('stops', 'stop_loss_percentage', default=5.0)
    
    @property
    def trailing_stop_percentage(self) -> float:
        """Trailing stop percentage."""
        return self.get('stops', 'trailing_stop_percentage', default=3.0)
    
    # Network Fee Configuration
    @property
    def trade_fee_lock_xrd(self) -> float:
        """XRD to lock for trade transactions. Radix refunds unused portion."""
        return self.get('network_fees', 'trade_fee_lock_xrd', default=5.0)
    
    @property
    def trade_fee_multiplier(self) -> float:
        """Safety multiplier applied to trade fee preview estimate."""
        return self.get('network_fees', 'trade_fee_multiplier', default=2.5)
    
    @property
    def withdrawal_fee_multiplier(self) -> float:
        """Safety multiplier for withdrawal fee estimation."""
        return self.get('network_fees', 'withdrawal_fee_multiplier', default=1.75)
    
    @property
    def min_profit_threshold_xrd(self) -> float:
        """Minimum expected profit in XRD to justify executing a trade."""
        return self.get('network_fees', 'min_profit_threshold_xrd', default=1.0)


# Global config instance
config = ConfigLoader()
