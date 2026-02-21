import logging
from typing import Dict, Any, List, Tuple
from database.trade_manager import TradeManager
from database.price_history_manager import PriceHistoryManager
from database.tokens import TokenManager

logger = logging.getLogger(__name__)

class TradeStatsManager:
    """
    Manages the calculation of advanced statistics for a given trade.
    """
    def __init__(self, trade_manager: TradeManager, price_history_manager: PriceHistoryManager, token_manager: TokenManager):
        self.trade_manager = trade_manager
        self.price_history_manager = price_history_manager
        self.token_manager = token_manager

    def calculate_all_stats(self, trade_id: int) -> Dict[str, Any]:
        """
        Reads trade statistics from the database (already calculated during execution).
        """
        trade_data = self.trade_manager.get_trade_by_id(trade_id)
        if not trade_data:
            logger.warning(f"Could not calculate stats. No trade data found for trade_id: {trade_id}")
            return {}

        # Read statistics directly from database columns (already calculated by update_trade_statistics_after_flip)
        times_flipped = float(trade_data.get('times_flipped', 0))
        profitable_flips = int(trade_data.get('profitable_flips', 0))
        unprofitable_flips = int(trade_data.get('unprofitable_flips', 0))
        total_profit = float(trade_data.get('total_profit', 0))
        trade_volume = float(trade_data.get('trade_volume', 0))
        
        # Calculate win ratio from profitable/unprofitable counts
        total_completed_flips = profitable_flips + unprofitable_flips
        if total_completed_flips > 0:
            win_ratio = f"{(profitable_flips / total_completed_flips) * 100:.2f}%"
        else:
            win_ratio = "N/A"

        # Initialize stats with database values
        stats = {
            "times_flipped": times_flipped,
            "profitable_flips": profitable_flips,
            "unprofitable_flips": unprofitable_flips,
            "win_ratio": win_ratio,
            "total_profit": total_profit,  # Raw number for formatting in UI
            "trade_volume": trade_volume,  # Raw number for formatting in UI
            "current_value": "N/A",  # Calculated below
            "current_value_usd": "N/A",  # Calculated below
            "current_holdings_token": trade_data['trade_token_address'],
            "current_holdings_amount": float(trade_data['trade_amount']),
            "current_token_symbol": trade_data.get('trade_token_symbol', ''),
        }

        # --- Calculate Current Value (XRD and USD) ---
        try:
            # Determine which token we're currently holding
            holding_token = stats["current_holdings_token"]
            holding_amount = stats["current_holdings_amount"]
            
            # Get token price data from database
            token_info = self.token_manager.get_token_by_address(holding_token)
            
            if token_info:
                token_price_xrd = float(token_info.get('token_price_xrd', 0))
                token_price_usd = float(token_info.get('token_price_usd', 0))
                
                # Calculate XRD value
                current_value_xrd = holding_amount * token_price_xrd
                
                # Calculate USD value
                current_value_usd = holding_amount * token_price_usd
                
                stats["current_value"] = f"{current_value_xrd:,.4f} XRD"
                stats["current_value_usd"] = f"${current_value_usd:,.2f}"
                
                logger.debug(f"Calculated value: {holding_amount} {stats['current_token_symbol']} = {current_value_xrd:.4f} XRD = ${current_value_usd:.2f}")
            else:
                logger.warning(f"No token price data found for {holding_token}")
                stats["current_value"] = "N/A (No Price Data)"
                stats["current_value_usd"] = "N/A"

        except Exception as e:
            logger.error(f"Error calculating current value for trade {trade_id}: {e}", exc_info=True)
            stats["current_value"] = "Error"
            stats["current_value_usd"] = "Error"

        # Note: trade_volume and total_profit are kept as raw numbers for formatting in the UI
        return stats
