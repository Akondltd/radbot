import logging
import random
from datetime import datetime, timedelta
from PySide6.QtGui import QColor
from database.database import Database

logger = logging.getLogger(__name__)

class DashboardDataService:
    """Service for retrieving dashboard data"""
    
    def __init__(self):
        """Initialize the dashboard data service"""
        self.mock_mode = False
        self.db = Database()
        logger.info(f"Dashboard service initialized (mock_mode={self.mock_mode})")
        
    def get_dashboard_data(self, wallet_id=None):
        """
        Get data for the dashboard
        
        Args:
            wallet_id: Optional wallet ID to filter data
            
        Returns:
            Dictionary with all dashboard data
        """
        if self.mock_mode:
            return self._get_mock_data()
        
        try:
            # Start building the dashboard data
            dashboard_data = {}
            
            # Get active wallet if none provided
            if wallet_id is None:
                wallet_id = self._get_active_wallet_id()
                if wallet_id is None:
                    logger.warning("No active wallet found, using mock data")
                    return self._get_mock_data()
            
            # Get wallet token data
            token_data = self._get_wallet_tokens(wallet_id)
            dashboard_data.update(token_data)
            
            # Get profit history (mock for now)
            profit_data = self._get_profit_history()
            dashboard_data.update(profit_data)
            
            # Get volume data (mock for now)
            volume_data = self._get_volume_data()
            dashboard_data.update(volume_data)
            
            # Get trade statistics
            stats_data = self._get_trade_statistics()
            dashboard_data.update(stats_data)
            
            return dashboard_data
            
        except Exception as e:
            logger.exception(f"Error getting dashboard data: {e}")
            # Fallback to mock data if database queries fail
            return self._get_mock_data()
    
    def _get_active_wallet_id(self):
        """Get the active wallet ID from settings"""
        try:
            cursor = self.db._cursor
            cursor.execute("SELECT active_wallet_id FROM settings WHERE id = 1")
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            return None
        except Exception as e:
            logger.exception(f"Error getting active wallet ID: {e}")
            return None
    
    def _get_wallet_tokens(self, wallet_id):
        """Get wallet token distribution and values
        
        Args:
            wallet_id: Wallet ID to filter data
            
        Returns:
            Dictionary with token distribution and wallet value data
        """
        try:
            cursor = self.db._cursor
            
            # Query for token balances with token info
            query = """
                SELECT tb.balance, t.address, t.symbol, t.name, t.token_price_xrd 
                FROM token_balances tb
                JOIN tokens t ON tb.token_address = t.address
                WHERE tb.wallet_id = ?
            """
            
            cursor.execute(query, (wallet_id,))
            token_balances = cursor.fetchall()
            
            # Process token balances into distribution data
            token_distribution = []
            total_value_xrd = 0
            
            # Vibrant token colors - each token gets a unique bright color
            colors = {
                "XRD": QColor(46, 204, 113),     # Emerald Green
                "xUSDC": QColor(39, 174, 96),    # Sea Green  
                "xUSDT": QColor(26, 188, 156),   # Turquoise
                "HUG": QColor(243, 156, 18),     # Orange
                "FLOOP": QColor(230, 126, 34),   # Pumpkin
                "DFP2": QColor(231, 76, 60),     # Alizarin Red
                "ASTRL": QColor(192, 57, 43),    # Pomegranate
                "hETH": QColor(155, 89, 182),    # Amethyst Purple
                "hUSDC": QColor(142, 68, 173),   # Wisteria Purple
                "hUSDT": QColor(41, 128, 185),   # Peter River Blue
                "OCI": QColor(52, 152, 219),     # Dodger Blue
                "xwBTC": QColor(241, 196, 15),   # Sun Flower Yellow
                "xwETH": QColor(149, 165, 166),  # Asbestos Gray
                "xBTC": QColor(127, 140, 141),   # Concrete Gray
                "xETH": QColor(52, 73, 94),      # Wet Asphalt
            }
            
            # Vibrant fallback colors for unknown tokens (rotating palette)
            fallback_colors = [
                QColor(231, 76, 60),    # Red
                QColor(52, 152, 219),   # Blue
                QColor(46, 204, 113),   # Green
                QColor(155, 89, 182),   # Purple
                QColor(241, 196, 15),   # Yellow
                QColor(230, 126, 34),   # Orange
                QColor(26, 188, 156),   # Cyan
                QColor(22, 160, 133),   # Teal
            ]
            
            # Calculate total XRD value of each token
            token_values = {}
            for token in token_balances:
                balance = float(token[0]) if token[0] else 0
                symbol = token[2]
                price_xrd = float(token[4]) if token[4] else 0
                value_xrd = balance * price_xrd
                
                if symbol in token_values:
                    token_values[symbol] += value_xrd
                else:
                    token_values[symbol] = value_xrd
                    
                total_value_xrd += value_xrd
            
            # Group tokens: Top 5 by value get individual colors, rest go to "Others"
            # Sort tokens by value (descending)
            sorted_tokens = sorted(token_values.items(), key=lambda x: x[1], reverse=True)
            
            grouped_tokens = {}
            others_value = 0
            
            for i, (symbol, value) in enumerate(sorted_tokens):
                if i < 5:  # Top 5 tokens
                    grouped_tokens[symbol] = value
                else:  # Everything else goes to "Others"
                    others_value += value
            
            # Add "Others" if there are tokens beyond top 5
            if others_value > 0:
                grouped_tokens["Others"] = others_value
            
            # Convert to percentage and create color-coded data
            # Maintain order: sorted by value (already sorted when we created grouped_tokens)
            color_index = 0
            
            # Need to iterate in order - rebuild from sorted_tokens for top 5, then Others
            for i, (symbol, value) in enumerate(sorted_tokens):
                if i >= 5:
                    break  # We'll add "Others" separately
                    
                if total_value_xrd > 0:
                    percentage = (value / total_value_xrd) * 100
                else:
                    percentage = 0
                    
                # Get color from predefined list or use rotating fallback
                if symbol in colors:
                    color = colors[symbol]
                else:
                    color = fallback_colors[color_index % len(fallback_colors)]
                    color_index += 1
                    
                token_distribution.append((symbol, percentage, color))
            
            # Add "Others" at the end if it exists
            if others_value > 0:
                others_percentage = (others_value / total_value_xrd * 100) if total_value_xrd > 0 else 0
                # Use gray for "Others"
                token_distribution.append(("Others", others_percentage, QColor(149, 165, 166)))
            
            return {
                "wallet_value": f"{int(total_value_xrd)} XRD",
                "token_distribution": token_distribution
            }
        except Exception as e:
            logger.exception(f"Error getting wallet tokens: {e}")
            return {
                "wallet_value": "N/A",
                "token_distribution": [
                    ("XRD", 65, QColor(46, 204, 113)),
                    ("BTC", 20, QColor(52, 152, 219)),
                    ("ETH", 10, QColor(155, 89, 182)),
                    ("Others", 5, QColor(149, 165, 166))
                ]
            }
    
    def _get_profit_history(self, wallet_address=None):
        """Get profit history data for the chart
        
        Returns:
            Dictionary with profit history data (30 days of cumulative profit/loss)
        """
        try:
            # Get active wallet address if not provided
            if wallet_address is None:
                cursor = self.db._cursor
                cursor.execute("""
                    SELECT w.wallet_address 
                    FROM wallets w
                    JOIN settings s ON s.active_wallet_id = w.wallet_id
                    LIMIT 1
                """)
                wallet_row = cursor.fetchone()
                if not wallet_row:
                    # No active wallet, return zeros
                    return {"profit_history": [0] * 30}
                wallet_address = wallet_row[0]
            
            # Fetch daily statistics for last 30 days
            daily_stats = self.db.get_daily_statistics(wallet_address, days=30)
            
            # Create a complete 30-day range
            from datetime import datetime, timedelta
            today = datetime.now().date()
            date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
            date_range.reverse()  # Oldest first
            
            # Build dict from daily_stats
            stats_by_date = {stat['date']: stat['profit_loss_xrd'] for stat in daily_stats}
            
            # Fill profit history with values, using 0 for missing dates
            # Calculate cumulative profit
            profit_history = []
            cumulative = 0
            for date in date_range:
                daily_profit = stats_by_date.get(date, 0)
                cumulative += daily_profit
                profit_history.append(cumulative)
            
            return {"profit_history": profit_history}
            
        except Exception as e:
            logger.error(f"Error getting profit history: {e}", exc_info=True)
            # Return zeros on error
            return {"profit_history": [0] * 30}
    
    def _get_volume_data(self, wallet_address=None):
        """Get trading volume data for the chart
        
        Returns:
            Dictionary with volume data (30 days of trading volume in XRD)
        """
        try:
            # Get active wallet address if not provided
            if wallet_address is None:
                cursor = self.db._cursor
                cursor.execute("""
                    SELECT w.wallet_address 
                    FROM wallets w
                    JOIN settings s ON s.active_wallet_id = w.wallet_id
                    LIMIT 1
                """)
                wallet_row = cursor.fetchone()
                if not wallet_row:
                    # No active wallet, return zeros
                    return {"volume_data": [(str(i), 0) for i in range(1, 31)]}
                wallet_address = wallet_row[0]
            
            # Fetch daily statistics for last 30 days
            daily_stats = self.db.get_daily_statistics(wallet_address, days=30)
            
            # Create a complete 30-day range
            from datetime import datetime, timedelta
            today = datetime.now().date()
            date_range = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
            date_range.reverse()  # Oldest first
            
            # Build dict from daily_stats
            stats_by_date = {stat['date']: stat['volume_xrd'] for stat in daily_stats}
            
            # Fill volume data with values, using 0 for missing dates
            # Use day numbers (1-30) as labels for x-axis
            volume_data = []
            for idx, date in enumerate(date_range, 1):
                volume = stats_by_date.get(date, 0)
                volume_data.append((str(idx), volume))
            
            return {"volume_data": volume_data}
            
        except Exception as e:
            logger.error(f"Error getting volume data: {e}", exc_info=True)
            # Return zeros on error
            return {"volume_data": [(str(i), 0) for i in range(1, 31)]}
    
    def _get_trade_statistics(self):
        """Get trade statistics from database
        
        Returns:
            Dictionary with trade statistics
        """
        try:
            cursor = self.db._cursor
            statistics_manager = self.db.get_statistics_manager()
            
            # Get active wallet ID
            cursor.execute("SELECT active_wallet_id FROM settings LIMIT 1")
            wallet_row = cursor.fetchone()
            
            # Initialize defaults
            stats_data = {
                "active_trades": 0,
                "win_ratio": "0.00 %",
                "trades_created": 0,
                "trades_cancelled": 0,
                "profitable_trades": 0, 
                "unprofitable_trades": 0,
                "tokens_traded": 0,
                "trade_pairs": 0,
                "most_profitable": "N/A",
                "profit": "0 XRD"
            }
            
            # Get statistics from statistics table
            if wallet_row and wallet_row[0] is not None:
                active_wallet_id = wallet_row[0]
                
                # Ensure statistics entry exists for this wallet
                statistics_manager.ensure_statistics_entry(active_wallet_id)
                
                stats = statistics_manager.get_statistics(active_wallet_id)
                logger.info(f"Stats for wallet {active_wallet_id}: {stats}")
                
                if stats:
                    # Update from statistics table
                    stats_data["trades_created"] = stats['total_trades_created']
                    stats_data["trades_cancelled"] = stats['total_trades_deleted']
                    stats_data["profitable_trades"] = stats['winning_trades']
                    stats_data["unprofitable_trades"] = stats['losing_trades']
                    stats_data["win_ratio"] = f"{stats['win_rate_percentage']:.2f} %"
                    
                    # Format profit/loss - prefer XRD columns, fallback to USD columns
                    total_profit_xrd = stats.get('total_profit_xrd', 0) or 0
                    total_loss_xrd = stats.get('total_loss_xrd', 0) or 0
                    
                    # If XRD columns exist and have data, use them
                    if total_profit_xrd != 0 or total_loss_xrd != 0:
                        net_profit = total_profit_xrd - total_loss_xrd
                        logger.debug(f"Using XRD columns: profit_xrd={total_profit_xrd:.2f}, loss_xrd={total_loss_xrd:.2f}, net={net_profit:.2f}")
                    else:
                        # Fallback to USD columns (old schema or no trades yet)
                        total_profit = stats.get('total_profit', 0) or 0
                        total_loss = stats.get('total_loss', 0) or 0
                        net_profit = total_profit - total_loss
                        logger.debug(f"Using USD columns (fallback): profit={total_profit:.2f}, loss={total_loss:.2f}, net={net_profit:.2f}")
                    
                    if net_profit >= 0:
                        stats_data["profit"] = f"+{net_profit:.2f} XRD"
                    else:
                        stats_data["profit"] = f"{net_profit:.2f} XRD"

            # Count active trades from trades table for the active wallet
            if wallet_row and wallet_row[0] is not None:
                active_wallet_id = wallet_row[0]
                # Get wallet address for the active wallet
                cursor.execute("SELECT wallet_address FROM wallets WHERE wallet_id = ?", (active_wallet_id,))
                wallet_addr_row = cursor.fetchone()
                if wallet_addr_row and wallet_addr_row[0]:
                    wallet_address = wallet_addr_row[0]
                    cursor.execute("SELECT COUNT(*) FROM trades WHERE wallet_address = ?", (wallet_address,))
                    stats_data["active_trades"] = cursor.fetchone()[0]
                else:
                    stats_data["active_trades"] = 0
            else:
                stats_data["active_trades"] = 0
            
            # Count trade pairs from selected_pairs table
            cursor.execute("SELECT COUNT(*) FROM selected_pairs")
            trade_pairs_count = cursor.fetchone()[0]
            stats_data["trade_pairs"] = trade_pairs_count
            logger.debug(f"Trade pairs selected: {trade_pairs_count}")
            
            # Count unique tokens traded across all trade pairs for this wallet
            if wallet_row and wallet_row[0] is not None:
                active_wallet_id = wallet_row[0]
                cursor.execute("SELECT wallet_address FROM wallets WHERE wallet_id = ?", (active_wallet_id,))
                wallet_addr_row = cursor.fetchone()
                if wallet_addr_row and wallet_addr_row[0]:
                    wallet_address = wallet_addr_row[0]
                    cursor.execute("""
                        SELECT COUNT(*) FROM (
                            SELECT tp.base_token AS token FROM trades t
                            JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                            WHERE t.wallet_address = ?
                            UNION
                            SELECT tp.quote_token AS token FROM trades t
                            JOIN trade_pairs tp ON t.trade_pair_id = tp.trade_pair_id
                            WHERE t.wallet_address = ?
                        )
                    """, (wallet_address, wallet_address))
                    tokens_traded_count = cursor.fetchone()[0]
                    stats_data["tokens_traded"] = tokens_traded_count
                    logger.debug(f"Unique tokens traded for wallet {wallet_address}: {tokens_traded_count}")
                else:
                    stats_data["tokens_traded"] = 0
            else:
                stats_data["tokens_traded"] = 0
            
            # Find most profitable strategy from trades table (based on total_profit column)
            try:
                cursor.execute("""
                    SELECT strategy_name, SUM(total_profit) as total_profit
                    FROM trades
                    WHERE total_profit IS NOT NULL
                    GROUP BY strategy_name
                    ORDER BY total_profit DESC
                    LIMIT 1
                """)
                strategy_row = cursor.fetchone()
                if strategy_row and strategy_row[0]:
                    stats_data["most_profitable"] = strategy_row[0].title()
            except sqlite3.Error as e:
                logger.debug(f"Could not determine most profitable strategy: {e}")
                stats_data["most_profitable"] = "N/A"
            
            return stats_data
            
        except Exception as e:
            logger.exception(f"Error getting trade statistics: {e}")
            # Return zeros for statistics if query fails
            return {
                "active_trades": 0,
                "win_ratio": "0.00 %",
                "trades_created": 0,
                "trades_cancelled": 0,
                "profitable_trades": 0, 
                "unprofitable_trades": 0,
                "tokens_traded": 0,
                "trade_pairs": 0,
                "most_profitable": "N/A",
                "profit": "0 XRD"
            }
    
    def _get_mock_data(self):
        """Generate mock data for testing"""
        # Generate random profit history (last 30 days)
        profit_history = []
        base_value = 100
        for i in range(30):
            change = random.uniform(-20, 30)
            base_value += change
            # Ensure value doesn't go below 0
            base_value = max(base_value, 10)
            profit_history.append(base_value)
            
        # Generate token distribution data
        token_distribution = [
            ("XRD", 65, QColor(46, 204, 113)),    # Green
            ("BTC", 20, QColor(52, 152, 219)),    # Blue
            ("ETH", 10, QColor(155, 89, 182)),    # Purple
            ("Others", 5, QColor(149, 165, 166))  # Gray
        ]
        
        # Generate volume data (last 7 days)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        volume_data = []
        for day in days:
            volume = random.randint(50, 250)
            volume_data.append((day, volume))
        
        # Summary data
        wallet_value = f"{random.randint(1000, 5000)} XRD"
        profit = f"{random.randint(100, 1000)} XRD"
        active_trades = random.randint(0, 10)
        win_ratio = f"{random.uniform(50.0, 95.0):.2f} %"
        
        return {
            # Summary data
            "wallet_value": wallet_value,
            "profit": profit,
            "active_trades": active_trades,
            "win_ratio": win_ratio,
            
            # Chart data
            "profit_history": profit_history,
            "token_distribution": token_distribution,
            "volume_data": volume_data,
            
            # Additional stats (not used in current UI)
            "trades_created": 42,
            "trades_cancelled": 5,
            "profitable_trades": 30, 
            "unprofitable_trades": 7,
            "tokens_traded": 4,
            "trade_pairs": 6,  
            "most_profitable": "RSI-14",
            "total_volume": "1850 XRD",
            "total_deposit": "1250 XRD",
            "total_withdraw": "350 XRD"
        }
