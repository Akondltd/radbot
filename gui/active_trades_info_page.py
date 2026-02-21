import logging
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPixmap, QColor
from pathlib import Path
from config.paths import PACKAGE_ROOT
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from database.trade_manager import TradeManager
from database.tokens import TokenManager
from database.price_history_manager import PriceHistoryManager
from services.pair_price_history_service import PairPriceHistoryService
from services.trade_stats_manager import TradeStatsManager
from gui.active_trades_ui import Ui_ActiveTradesTabMain
from gui.components.trade_chart_widget import TradeChartWidget
from gui.overlapping_icon_widget import OverlappingIconWidget
import locale
import json

logger = logging.getLogger(__name__)

# Set locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, '')  # Use system default locale
except:
    logger.warning("Failed to set locale, falling back to default number formatting")

class ActiveTradeInfoPage(QWidget):
    """Manages the 'Information' page of the Active Trades tab."""

    def __init__(self, ui: Ui_ActiveTradesTabMain, trade_manager: TradeManager, token_manager: TokenManager, parent=None):
        super().__init__(parent)
        logger.info("========== ACTIVE TRADE INFO PAGE __init__ STARTED ==========")
        self.ui = ui
        self.trade_manager = trade_manager
        self.token_manager = token_manager
        self.price_history_manager = PriceHistoryManager(self.trade_manager.conn)  # Legacy - for old pool data
        
        # Initialize pair-based price history service (uses default "data/radbot.db")
        from services.pair_price_history_service import get_pair_history_service
        self.pair_price_history = get_pair_history_service()
        
        self.trade_stats_manager = TradeStatsManager(self.trade_manager, self.price_history_manager, self.token_manager)
        self.current_trade_id = None
        self.creation_timestamp = None
        
        # --- Create the TradeChartWidget ---
        # Check if we have a responsive layout chart placeholder or legacy mode
        self.chart_widget = None  # Initialize to None first
        
        if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder'):
            # Responsive mode: Replace the placeholder with the chart widget
            placeholder = self.ui.ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder
            
            # Find the layout that contains the placeholder by searching recursively
            def find_widget_in_layout(layout, widget):
                """Recursively search for widget in layout and return (layout, index)"""
                if layout is None:
                    return None, -1
                    
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item:
                        if item.widget() == widget:
                            return layout, i
                        # Check nested layouts
                        if item.layout():
                            found_layout, found_index = find_widget_in_layout(item.layout(), widget)
                            if found_layout:
                                return found_layout, found_index
                return None, -1
            
            parent_layout, index = find_widget_in_layout(self.ui.Information.layout(), placeholder)
            
            if parent_layout and index >= 0:
                # Replace the placeholder — hide it immediately to prevent
                # rendering artifacts between removal and deferred deletion
                parent_layout.removeWidget(placeholder)
                placeholder.hide()
                placeholder.setParent(None)
                placeholder.deleteLater()
                
                # Create and insert chart widget
                self.chart_widget = TradeChartWidget(parent=self.ui.Information)
                # Set size policy to allow scaling
                self.chart_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                parent_layout.insertWidget(index, self.chart_widget)
                logger.info("Replaced chart placeholder with TradeChartWidget in responsive layout")
            else:
                # Fallback if layout not found
                self.chart_widget = TradeChartWidget(parent=self.ui.Information)
                self.chart_widget.setGeometry(QRect(370, 30, 411, 311))
                logger.warning("Could not find chart placeholder layout, using fixed geometry")
        else:
            # Legacy mode: Use fixed geometry
            self.chart_widget = TradeChartWidget(parent=self.ui.Information)
            self.chart_widget.setGeometry(QRect(370, 30, 411, 311))
            logger.info("Using legacy fixed geometry for chart")

        # --- Create Trade Pair Icon and Label ---
        # For responsive layouts, add them to the button row. For legacy, use fixed positioning.
        if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetInformationIconPlaceholder'):
            logger.info("INFO PAGE: Using RESPONSIVE layout for icons in button row")
            # Responsive mode: Replace placeholder in button row with icon widget + label
            placeholder = self.ui.ActiveTradesTabMainListTradesStackedWidgetInformationIconPlaceholder
            parent_layout, index = find_widget_in_layout(self.ui.Information.layout(), placeholder)
            
            if parent_layout and index >= 0:
                # Remove placeholder
                parent_layout.removeWidget(placeholder)
                placeholder.deleteLater()
                
                # Create container for icons + label
                icon_label_container = QWidget(parent=self.ui.Information)
                container_layout = QHBoxLayout(icon_label_container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(8)
                
                # Add icon widget
                self.icon_widget = OverlappingIconWidget(parent=icon_label_container)
                self.icon_widget.setFixedSize(60, 30)
                container_layout.addWidget(self.icon_widget)
                
                # Add label next to icons
                self.pair_label = QLabel(parent=icon_label_container)
                self.pair_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                container_layout.addWidget(self.pair_label)
                
                # Insert into button row where placeholder was
                parent_layout.insertWidget(index, icon_label_container)
                logger.info("Replaced icon placeholder in button row")
            else:
                # Fallback: create widgets with fixed positioning
                self.icon_widget = OverlappingIconWidget(parent=self.ui.Information)
                self.pair_label = QLabel(parent=self.ui.Information)
                logger.warning("Could not find icon placeholder, using fixed positioning")
        else:
            logger.warning("INFO PAGE: Using LEGACY layout for icons (chart placeholder not found)")
            # Legacy mode: Fixed positioning
            self.icon_widget = OverlappingIconWidget(parent=self.ui.Information)
            self.pair_label = QLabel(parent=self.ui.Information)
            
            chart_geom = self.chart_widget.geometry()
            space_center_x = chart_geom.x() + chart_geom.width() / 3
            space_y_start = chart_geom.y() + chart_geom.height() + 120
            
            icon_width = 60
            icon_height = 30
            self.icon_widget.setGeometry(int(space_center_x - icon_width / 2), space_y_start, icon_width, icon_height)
            
            label_width = 150
            label_height = 20
            self.pair_label.setGeometry(int(space_center_x - label_width / 1.7), space_y_start + icon_height, label_width, label_height)
            self.pair_label.setAlignment(Qt.AlignCenter)
        font = self.pair_label.font()
        font.setPointSize(10)
        self.pair_label.setFont(font)

        # Make the creation date field a bit taller to accommodate two lines of text
        creation_date_field = self.ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea
        creation_date_field.setMinimumHeight(38)  # Increased height for two lines
        
        # Log actual widget geometries for debugging
        logger.info(f"Icon widget size: {self.icon_widget.size()}, pos: {self.icon_widget.pos()}")
        logger.info(f"Pair label size: {self.pair_label.size()}, pos: {self.pair_label.pos()}")
        logger.info(f"Chart widget size: {self.chart_widget.size()}, pos: {self.chart_widget.pos()}")
        
        self.icon_widget.show()
        self.pair_label.show()

        # Setup connections for the info page buttons
        self.ui.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton.clicked.connect(self.go_back_to_list)

        # Setup update timer for dynamic content
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dynamic_content)
        self.update_timer.start(1000)  # Update every second

    def go_back_to_list(self):
        """Switches the stacked widget back to the list view (index 0)."""
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0)
    
    def refresh_if_viewing(self):
        """Refreshes the current trade info if a trade is being viewed."""
        if self.current_trade_id is not None:
            logger.debug(f"Refreshing info page for trade_id: {self.current_trade_id}")
            self.load_trade_info(self.current_trade_id)

    def load_trade_info(self, trade_id: int):
        """Loads all data for a specific trade and populates the information page."""
        ui = self.ui
        self.current_trade_id = trade_id
        
        # Clear chart immediately when switching trades to prevent stickiness
        self.chart_widget.clear_chart()
        
        try:
            trade_data = self.trade_manager.get_trade_by_id(trade_id)
            if not trade_data:
                logger.warning(f"No trade data found for trade_id {trade_id}")
                return

            # --- Calculate all statistics using the new manager ---
            stats = self.trade_stats_manager.calculate_all_stats(trade_id)
            logger.debug(f"Calculated stats for trade {trade_id}: {stats}")

            # --- Populate UI with basic trade data and calculated stats ---
            # Basic Info
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea.setText(str(trade_id))
            
            # Store creation timestamp for dynamic updates
            self.creation_timestamp = trade_data.get('created_at')
            formatted_date = datetime.fromtimestamp(self.creation_timestamp).strftime('%dth %B %Y @ %H:%M') if self.creation_timestamp else "N/A"
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea.setText(f"{formatted_date}\n")  # Leave space for timer
            
            # Show trade status (active/paused)
            is_active = trade_data.get('is_active', False)
            status_text = "Active" if is_active else "Paused"
            
            # Set the label to display status
            strategy_name = trade_data.get('strategy_name', 'N/A')
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.setText(
                f"{strategy_name} ({status_text})"
            )
            # Use theme status classes instead of inline styles
            status_class = "status_active" if is_active else "status_paused"
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.setProperty("class", status_class)
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.style().unpolish(ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea)
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.style().polish(ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea)
            
            # Format initial values with locale - ensure numbers are converted properly
            try:
                start_amount = float(trade_data.get('start_amount', 0))
                start_amount_str = f"{start_amount:,.8f}"
            except (ValueError, TypeError):
                start_amount_str = str(trade_data.get('start_amount', '0'))
                
            start_token_symbol = trade_data.get('start_token_symbol', '???')
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea.setText(f"{start_amount_str} {start_token_symbol}")
            
            # Calculated Stats - Times Flipped (supports 0.5 increments)
            times_flipped = stats.get('times_flipped', 0)
            if isinstance(times_flipped, (int, float)) and times_flipped > 0:
                # Show 0.5 decimals for half-flips, whole numbers for full flips
                if times_flipped % 1 == 0:
                    ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setText(f"{int(times_flipped)}")
                else:
                    ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setText(f"{times_flipped:.1f}")
            else:
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setText("0")
                
            # Profitable Flips
            profitable_flips = stats.get('profitable_flips', 0)
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea.setText(str(int(profitable_flips)))
                
            # Unprofitable Flips (widget has typo 'UnprofitablFlips')
            unprofitable_flips = stats.get('unprofitable_flips', 0)
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea.setText(str(int(unprofitable_flips)))
            
            # Win Ratio (already formatted as percentage string from stats)
            win_ratio = stats.get('win_ratio', 'N/A')
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea.setText(win_ratio)
            
            # Total Profit with color coding (raw XRD value from database)
            total_profit = stats.get('total_profit', 0)
            if isinstance(total_profit, (int, float)):
                total_profit_formatted = f"{total_profit:,.2f} XRD"
                # Use theme profit classes instead of inline styles
                profit_class = "profit_positive" if total_profit > 0 else "profit_negative" if total_profit < 0 else "profit_neutral"
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setText(total_profit_formatted)
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setProperty("class", profit_class)
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.style().unpolish(ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea)
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.style().polish(ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea)
            else:
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setText("0.00 XRD")
            
            # Trade Volume (raw XRD value from database)
            trade_volume = stats.get('trade_volume', 0)
            if isinstance(trade_volume, (int, float)):
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea.setText(f"{trade_volume:,.2f} XRD")
            else:
                ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea.setText("0.00 XRD")
            
            # Current trade value with XRD (main) and USD (secondary) formatting
            current_value_xrd = stats.get('current_value', 'N/A')
            current_value_usd = stats.get('current_value_usd', 'N/A')
            current_token = stats.get('current_token_symbol', '')
            
            # Format display with XRD on top line, USD below with smaller font and 80% opacity
            # QLabel supports HTML via setText()
            value_display = f'<div style="line-height:1.0;">'
            value_display += f'<span style="font-size:14pt;">{current_value_xrd}</span><br>'
            value_display += f'<span style="font-size:10pt; color: rgba(255, 255, 255, 0.6);">{current_value_usd} USD</span>'
            value_display += '</div>'
            
            ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setText(value_display)
            
            # Set current token symbol (keep this simple)
            # ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setText(
            #     current_token if current_token else " "
            # )

            # --- Update Chart ---
            # Get token pair from trade data
            trade_pair_id = trade_data.get('trade_pair_id')
            if trade_pair_id:
                try:
                    # Get pair details
                    trade_pair = self.trade_manager.get_trade_pair_by_id(trade_pair_id)
                    base_token = trade_pair['base_token']
                    quote_token = trade_pair['quote_token']
                    
                    # Get price history for this token pair
                    price_history_data = self.pair_price_history.get_price_history(base_token, quote_token, limit=4500)
                    if price_history_data:
                        df = pd.DataFrame(price_history_data)
                        
                        # Debug logging to check dataframe format
                        logger.debug(f"Price history dataframe columns: {df.columns}")
                        logger.debug(f"Price history data size: {len(df)} points")
                        if not df.empty:
                            logger.debug(f"Price history data sample: {df.head(1).to_dict()}")
                        
                        # Extended debugging for price investigation
                        if not df.empty:
                            logger.debug(f"First price point raw data: {df.iloc[0].to_dict()}")
                            logger.debug(f"Last price point raw data: {df.iloc[-1].to_dict()}")
                            logger.debug(f"Price range - Min: {df['close'].min()}, Max: {df['close'].max()}, Mean: {df['close'].mean()}")
                            
                            # Check if there might be a scaling factor
                            current_pair = trade_data.get('pair', '')
                            base_token = trade_data.get('base_token', '')
                            quote_token = trade_data.get('quote_token', '')
                            logger.debug(f"Trade pair info: {current_pair}, Base: {base_token}, Quote: {quote_token}")
                            
                            # Try to find the expected price in the stats (skip if N/A)
                            try:
                                current_holdings_amount = float(stats.get('current_holdings_amount', 0))
                                current_value = stats.get('current_value', '0 XRD')
                                
                                # Only process if current_value is a valid number (not "N/A")
                                if isinstance(current_value, str) and not current_value.startswith('N/A'):
                                    current_value_float = float(current_value.split(' ')[0])
                                    
                                    if current_holdings_amount > 0 and current_value_float > 0:
                                        expected_price = current_value_float / current_holdings_amount
                                        actual_price = df['close'].iloc[-1]
                                        price_ratio = actual_price / expected_price if expected_price else 0
                                        
                                        logger.debug(f"Price comparison - Expected unit price: {expected_price}, Chart price: {actual_price}")
                                        logger.debug(f"Price ratio (Chart/Expected): {price_ratio}")
                                        
                                        if price_ratio > 100:
                                            logger.warning(f"Detected large price discrepancy. Chart prices may be in basis points or multiplied by a factor.")
                            except (ValueError, AttributeError, IndexError) as e:
                                logger.debug(f"Skipping price comparison (non-XRD pair or invalid data): {e}")
                        
                        # First, add all indicators to the dataframe
                        df, strategy_name = self._add_indicators_to_dataframe(df, trade_data)

                        # Convert prices based on trade's pricing_token preference
                        # Step 1: Scale from XRD-denominated to USD-ratio
                        # Step 2: Invert based on pricing_token preference
                        
                        base_symbol = trade_data.get('base_token_symbol', '')
                        quote_symbol = trade_data.get('quote_token_symbol', '')
                        
                        # OHLC candles are now stored in decimal format (expensive token in denominator)
                        # This format always matches what users see during trade creation
                        # No conversion or inversion needed!
                        
                        logger.debug(f"Chart display - Base: {base_symbol}, Quote: {quote_symbol}")
                        logger.debug(f"OHLC range (decimal format) - Min: {df['close'].min():.6f}, Max: {df['close'].max():.6f}")
                        
                        # Data collection stores OHLC with expensive token in denominator (always decimal)
                        # Trade creation also shows decimal (expensive token in denominator)
                        # These match perfectly, so no conversion needed - just display as-is!

                        # Now, with all data prepared, update the chart
                        try:
                            self.chart_widget.set_data(df, strategy_name=strategy_name)
                        except Exception as e:
                            logger.error(f"Error plotting final chart data: {e}", exc_info=True)

                    else:
                        logger.warning("No price history data available for plotting")
                        self.chart_widget.clear_chart()

                except Exception as e:
                    logger.error(f"Error processing price data: {e}", exc_info=True)

            # --- Update Icons and Pair Label ---
            base_token = trade_data.get('base_token', '')
            quote_token = trade_data.get('quote_token', '')

            pixmap1 = self._load_pixmap_for_token(base_token, size=25)
            pixmap2 = self._load_pixmap_for_token(quote_token, size=25)
            self.icon_widget.set_icons(pixmap1, pixmap2)

            base_symbol = trade_data.get('base_token_symbol', '???')
            quote_symbol = trade_data.get('quote_token_symbol', '???')
            self.pair_label.setText(f"{base_symbol}/{quote_symbol}")  # Changed from - to / for standard format
            
            # Force update of dynamic content immediately
            self.update_dynamic_content()

        except Exception as e:
            logger.error(f"Failed to load trade info for trade_id {trade_id}: {e}", exc_info=True)

    def _add_indicators_to_dataframe(self, df, trade_data):
        """Adds indicators to the dataframe based on the trade strategy."""
        logger.debug(f"=== STRATEGY DEBUG ===")
        logger.debug(f"Original strategy: '{trade_data.get('strategy_name', '')}'")
        logger.debug(f"Processed strategy: '{trade_data.get('strategy_name', '').lower()}'")
        logger.debug(f"Settings JSON: {trade_data.get('indicator_settings_json')}")
        
        strategy_name = trade_data.get('strategy_name', '').lower()
        indicator_settings_json = trade_data.get('indicator_settings_json')
        
        if indicator_settings_json:
            try:
                indicator_settings = json.loads(indicator_settings_json)
                logger.debug(f"Parsed settings: {indicator_settings}")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode indicator settings JSON: {indicator_settings_json}")
                return df, strategy_name
        else:
            logger.debug("No indicator settings JSON found")
            indicator_settings = None

        # Plot MA lines if available in settings
        if 'moving_average' in strategy_name or 'moving average' in strategy_name:
            if indicator_settings and 'ma_period' in indicator_settings:
                ma_period = indicator_settings.get('ma_period', 20)
                logger.debug(f"MA Period: {ma_period}, Data points: {len(df)}")
                
                # Adjust period if necessary
                usable_period = min(ma_period, max(2, len(df) // 2)) if len(df) < ma_period*2 else ma_period
                if usable_period != ma_period:
                    logger.info(f"Adjusted MA period from {ma_period} to {usable_period} due to limited data")
                
                # Calculate MA
                try:
                    df['ma'] = df['close'].rolling(window=usable_period).mean()
                    logger.debug(f"MA calculated with {df['ma'].count()} non-NaN values")
                except Exception as e:
                    logger.error(f"Failed to calculate MA: {e}", exc_info=True)
                    
        # Plot Bollinger Bands if available in settings
        elif 'bollinger' in strategy_name:
            if indicator_settings and 'bb_period' in indicator_settings:
                bb_period = indicator_settings.get('bb_period', 20)
                bb_std = indicator_settings.get('bb_std', 2)
                logger.debug(f"Bollinger Bands - Period: {bb_period}, Std: {bb_std}")
                
                # Adjust period if necessary
                usable_period = min(bb_period, max(2, len(df) // 2)) if len(df) < bb_period*2 else bb_period
                if usable_period != bb_period:
                    logger.info(f"Adjusted BB period from {bb_period} to {usable_period} due to limited data")
                
                # Calculate Bollinger Bands
                try:
                    df['bb_middle'] = df['close'].rolling(window=usable_period).mean()
                    bb_std_rolling = df['close'].rolling(window=usable_period).std()
                    df['bb_upper'] = df['bb_middle'] + (bb_std_rolling * bb_std)
                    df['bb_lower'] = df['bb_middle'] - (bb_std_rolling * bb_std)
                    
                    # Log results
                    non_nan_count = df['bb_middle'].count()
                    logger.debug(f"BB columns have {non_nan_count} non-NaN values out of {len(df)} rows")
                except Exception as e:
                    logger.error(f"Failed to calculate Bollinger Bands: {e}", exc_info=True)
                    
        elif 'rsi' in strategy_name:
            # Plot RSI for individual RSI strategy
            if indicator_settings and 'rsi_period' in indicator_settings:
                rsi_period = indicator_settings.get('rsi_period', 14)
                buy_threshold = indicator_settings.get('buy_threshold', 30)
                sell_threshold = indicator_settings.get('sell_threshold', 70)
                
                logger.debug(f"RSI Period: {rsi_period}, Buy threshold: {buy_threshold}, Sell threshold: {sell_threshold}")
                
                # Adjust period if necessary
                usable_period = min(rsi_period, max(2, len(df) // 2)) if len(df) < rsi_period*2 else rsi_period
                if usable_period != rsi_period:
                    logger.info(f"Adjusted RSI period from {rsi_period} to {usable_period} due to limited data")
                
                # Calculate RSI
                try:
                    delta = df['close'].diff()
                    gain = delta.copy()
                    loss = delta.copy()
                    gain[gain < 0] = 0
                    loss[loss > 0] = 0
                    loss = abs(loss)
                    
                    avg_gain = gain.rolling(window=usable_period).mean()
                    avg_loss = loss.rolling(window=usable_period).mean()
                    
                    rs = avg_gain / avg_loss
                    df['rsi'] = 100 - (100 / (1 + rs))
                    
                    # Add RSI thresholds as horizontal lines
                    df['rsi_buy_threshold'] = buy_threshold
                    df['rsi_sell_threshold'] = sell_threshold
                    
                    # Generate buy/sell signals based on RSI thresholds
                    buy_condition = (df['rsi'] < buy_threshold) & (df['rsi'].shift(1) >= buy_threshold)
                    sell_condition = (df['rsi'] > sell_threshold) & (df['rsi'].shift(1) <= sell_threshold)
                    
                    df['buy_signal'] = np.where(buy_condition, df['low'] * 0.995, np.nan)
                    df['sell_signal'] = np.where(sell_condition, df['high'] * 1.005, np.nan)
                    
                    logger.debug(f"RSI calculated with {df['rsi'].count()} non-NaN values")
                    
                except Exception as e:
                    logger.error(f"Failed to calculate RSI: {e}", exc_info=True)
                    
        elif 'macd' in strategy_name:
            # Plot MACD for individual MACD strategy
            if indicator_settings and 'fast_period' in indicator_settings and 'slow_period' in indicator_settings:
                fast_period = indicator_settings.get('fast_period', 12)
                slow_period = indicator_settings.get('slow_period', 26)
                signal_period = indicator_settings.get('signal_period', 9)
                
                logger.debug(f"MACD Periods - Fast: {fast_period}, Slow: {slow_period}, Signal: {signal_period}")
                  
                # Adjust periods if necessary
                usable_fast = min(fast_period, max(2, len(df) // 4)) if len(df) < fast_period*2 else fast_period
                usable_slow = min(slow_period, max(3, len(df) // 3)) if len(df) < slow_period*2 else slow_period
                usable_signal = min(signal_period, max(2, len(df) // 4)) if len(df) < signal_period*2 else signal_period
                
                try:
                    # Calculate MACD
                    ema_fast = df['close'].ewm(span=usable_fast).mean()
                    ema_slow = df['close'].ewm(span=usable_slow).mean()
                    df['macd'] = ema_fast - ema_slow
                    df['macd_signal'] = df['macd'].ewm(span=usable_signal).mean()
                    df['macd_histogram'] = df['macd'] - df['macd_signal']
                    
                    # Generate buy/sell signals based on MACD crossovers
                    buy_condition = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
                    sell_condition = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
                    
                    df['buy_signal'] = np.where(buy_condition, df['low'] * 0.995, np.nan)
                    df['sell_signal'] = np.where(sell_condition, df['high'] * 1.005, np.nan)
                    
                    logger.debug(f"MACD calculated with {df['macd'].count()} non-NaN values")
                    
                except Exception as e:
                    logger.error(f"Failed to calculate MACD: {e}", exc_info=True)
                    
        elif 'ping pong' in strategy_name or 'pingpong' in strategy_name:
            logger.debug(f"*** PING PONG DETECTED ***")
            logger.debug(f"Strategy name: '{strategy_name}'")
            logger.debug(f"Has settings: {indicator_settings is not None}")
            if indicator_settings:
                logger.debug(f"Settings keys: {list(indicator_settings.keys())}")
                logger.debug(f"Has buy_price: {'buy_price' in indicator_settings}")
                logger.debug(f"Has sell_price: {'sell_price' in indicator_settings}")
                
            if indicator_settings and 'buy_price' in indicator_settings and 'sell_price' in indicator_settings:
                buy_price = float(indicator_settings['buy_price'])
                sell_price = float(indicator_settings['sell_price'])
                pricing_token_symbol = indicator_settings.get('pricing_token_symbol', '')
                
                logger.debug(f"Ping Pong Strategy - Buy: {buy_price}, Sell: {sell_price}, Pricing token: {pricing_token_symbol}")

                # The buy/sell prices are stored in the user's intuitive format
                # They're already in terms of the pricing_token_symbol
                # Chart will be inverted if needed based on pricing_token_symbol match
                # So these levels should match the chart's format
                df['buy_level'] = buy_price
                df['sell_level'] = sell_price

                # Generate signals for markers when price crosses the levels
                buy_condition = (df['low'] <= buy_price) & (df['low'].shift(1) > buy_price)
                sell_condition = (df['high'] >= sell_price) & (df['high'].shift(1) < sell_price)

                df['buy_signal'] = np.where(buy_condition, buy_price * 0.998, np.nan)
                df['sell_signal'] = np.where(sell_condition, sell_price * 1.002, np.nan)
                
                logger.debug(f"*** PING PONG COLUMNS CREATED ***")
                logger.debug(f"Buy level sample: {df['buy_level'].iloc[:3].tolist()}")
                logger.debug(f"Sell level sample: {df['sell_level'].iloc[:3].tolist()}")
                logger.debug(f"DataFrame columns now: {list(df.columns)}")
            else:
                logger.warning(f"*** PING PONG MISSING SETTINGS ***")
                logger.warning(f"Settings: {indicator_settings}")

        elif 'manual' in strategy_name:
            # Manual strategy - check which indicators are selected
            logger.debug(f"*** MANUAL STRATEGY DETECTED ***")
            logger.debug(f"Indicator settings: {indicator_settings}")
            
            # Track signals from each indicator for quorum voting
            indicator_buy_signals = []
            indicator_sell_signals = []
            selected_indicator_count = 0
            
            if indicator_settings:
                # Check for RSI indicator (presence in JSON means it's selected)
                if 'RSI' in indicator_settings and isinstance(indicator_settings.get('RSI'), dict):
                    selected_indicator_count += 1
                    rsi_settings = indicator_settings.get('RSI', {})
                    rsi_period = rsi_settings.get('period', 14)
                    buy_threshold = rsi_settings.get('buy_threshold', 30)
                    sell_threshold = rsi_settings.get('sell_threshold', 70)
                    
                    logger.debug(f"Manual - RSI selected: Period={rsi_period}, Buy={buy_threshold}, Sell={sell_threshold}")
                    
                    # Calculate RSI
                    try:
                        usable_period = min(rsi_period, max(2, len(df) // 2)) if len(df) < rsi_period*2 else rsi_period
                        
                        delta = df['close'].diff()
                        gain = delta.copy()
                        loss = delta.copy()
                        gain[gain < 0] = 0
                        loss[loss > 0] = 0
                        loss = abs(loss)
                        
                        avg_gain = gain.rolling(window=usable_period).mean()
                        avg_loss = loss.rolling(window=usable_period).mean()
                        
                        rs = avg_gain / avg_loss
                        df['rsi'] = 100 - (100 / (1 + rs))
                        df['rsi_buy_threshold'] = buy_threshold
                        df['rsi_sell_threshold'] = sell_threshold
                        
                        # Track buy/sell signals from RSI for quorum voting
                        buy_condition = (df['rsi'] < buy_threshold) & (df['rsi'].shift(1) >= buy_threshold)
                        sell_condition = (df['rsi'] > sell_threshold) & (df['rsi'].shift(1) <= sell_threshold)
                        
                        indicator_buy_signals.append(buy_condition)
                        indicator_sell_signals.append(sell_condition)
                        
                        logger.debug(f"Manual RSI: {df['rsi'].count()} values, {buy_condition.sum()} buy signals, {sell_condition.sum()} sell signals")
                    except Exception as e:
                        logger.error(f"Failed to calculate Manual RSI: {e}", exc_info=True)
                
                # Check for MACD indicator (presence in JSON means it's selected)
                if 'MACD' in indicator_settings and isinstance(indicator_settings.get('MACD'), dict):
                    selected_indicator_count += 1
                    macd_settings = indicator_settings.get('MACD', {})
                    fast_period = macd_settings.get('fast_period', 12)
                    slow_period = macd_settings.get('slow_period', 26)
                    signal_period = macd_settings.get('signal_period', 9)
                    
                    logger.debug(f"Manual - MACD selected: Fast={fast_period}, Slow={slow_period}, Signal={signal_period}")
                    
                    try:
                        usable_fast = min(fast_period, max(2, len(df) // 4)) if len(df) < fast_period*2 else fast_period
                        usable_slow = min(slow_period, max(3, len(df) // 3)) if len(df) < slow_period*2 else slow_period
                        usable_signal = min(signal_period, max(2, len(df) // 4)) if len(df) < signal_period*2 else signal_period
                        
                        ema_fast = df['close'].ewm(span=usable_fast).mean()
                        ema_slow = df['close'].ewm(span=usable_slow).mean()
                        df['macd'] = ema_fast - ema_slow
                        df['macd_signal'] = df['macd'].ewm(span=usable_signal).mean()
                        df['macd_histogram'] = df['macd'] - df['macd_signal']
                        
                        # Track buy/sell signals from MACD for quorum voting
                        buy_condition = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
                        sell_condition = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
                        
                        indicator_buy_signals.append(buy_condition)
                        indicator_sell_signals.append(sell_condition)
                        
                        logger.debug(f"Manual MACD: {df['macd'].count()} values, {buy_condition.sum()} buy signals, {sell_condition.sum()} sell signals")
                    except Exception as e:
                        logger.error(f"Failed to calculate Manual MACD: {e}", exc_info=True)
                
                # Check for Bollinger Bands indicator (presence in JSON means it's selected)
                if 'BB' in indicator_settings and isinstance(indicator_settings.get('BB'), dict):
                    selected_indicator_count += 1
                    bb_settings = indicator_settings.get('BB', {})
                    bb_period = bb_settings.get('period', 20)
                    bb_std = bb_settings.get('std_dev_multiplier', 2)
                    
                    logger.debug(f"Manual - BB selected: Period={bb_period}, StdDev={bb_std}")
                    
                    try:
                        usable_period = min(bb_period, max(2, len(df) // 2)) if len(df) < bb_period*2 else bb_period
                        
                        df['bb_middle'] = df['close'].rolling(window=usable_period).mean()
                        bb_std_rolling = df['close'].rolling(window=usable_period).std()
                        df['bb_upper'] = df['bb_middle'] + (bb_std_rolling * bb_std)
                        df['bb_lower'] = df['bb_middle'] - (bb_std_rolling * bb_std)
                        
                        # Track buy/sell signals from BB for quorum voting
                        buy_condition = (df['low'] <= df['bb_lower']) & (df['low'].shift(1) > df['bb_lower'].shift(1))
                        sell_condition = (df['high'] >= df['bb_upper']) & (df['high'].shift(1) < df['bb_upper'].shift(1))
                        
                        indicator_buy_signals.append(buy_condition)
                        indicator_sell_signals.append(sell_condition)
                        
                        logger.debug(f"Manual BB: {df['bb_middle'].count()} values, {buy_condition.sum()} buy signals, {sell_condition.sum()} sell signals")
                    except Exception as e:
                        logger.error(f"Failed to calculate Manual BB: {e}", exc_info=True)
                
                # Check for MA Cross indicator (presence in JSON means it's selected)
                if 'MA_CROSS' in indicator_settings and isinstance(indicator_settings.get('MA_CROSS'), dict):
                    selected_indicator_count += 1
                    ma_settings = indicator_settings.get('MA_CROSS', {})
                    short_period = ma_settings.get('short_period', 9)
                    long_period = ma_settings.get('long_period', 21)
                    
                    logger.debug(f"Manual - MA Cross selected: Short={short_period}, Long={long_period}")
                    
                    try:
                        usable_short = min(short_period, max(2, len(df) // 4)) if len(df) < short_period*2 else short_period
                        usable_long = min(long_period, max(3, len(df) // 3)) if len(df) < long_period*2 else long_period
                        
                        df['ma_fast'] = df['close'].rolling(window=usable_short).mean()
                        df['ma_slow'] = df['close'].rolling(window=usable_long).mean()
                        
                        # Track buy/sell signals from MA Cross for quorum voting
                        buy_condition = (df['ma_fast'] > df['ma_slow']) & (df['ma_fast'].shift(1) <= df['ma_slow'].shift(1))
                        sell_condition = (df['ma_fast'] < df['ma_slow']) & (df['ma_fast'].shift(1) >= df['ma_slow'].shift(1))
                        
                        indicator_buy_signals.append(buy_condition)
                        indicator_sell_signals.append(sell_condition)
                        
                        logger.debug(f"Manual MA Cross: {df['ma_fast'].count()} values, {buy_condition.sum()} buy signals, {sell_condition.sum()} sell signals")
                    except Exception as e:
                        logger.error(f"Failed to calculate Manual MA Cross: {e}", exc_info=True)
                
                # === QUORUM VOTING: Calculate consensus signals ===
                if selected_indicator_count > 0 and len(indicator_buy_signals) > 0:
                    logger.debug(f"=== QUORUM VOTING ===")
                    logger.debug(f"Selected indicators: {selected_indicator_count}")
                    logger.debug(f"Signals collected: {len(indicator_buy_signals)} buy, {len(indicator_sell_signals)} sell")
                    
                    # Sum up votes from all indicators (True = 1, False = 0)
                    buy_votes = pd.DataFrame(indicator_buy_signals).sum(axis=0)
                    sell_votes = pd.DataFrame(indicator_sell_signals).sum(axis=0)
                    
                    # Calculate consensus percentage
                    buy_consensus = buy_votes / selected_indicator_count
                    sell_consensus = sell_votes / selected_indicator_count
                    
                    # Require >=50% consensus (quorum)
                    quorum_threshold = 0.5
                    final_buy_condition = buy_consensus >= quorum_threshold
                    final_sell_condition = sell_consensus >= quorum_threshold
                    
                    # Place triangles at consensus points
                    df['buy_signal'] = np.where(final_buy_condition, df['low'] * 0.995, np.nan)
                    df['sell_signal'] = np.where(final_sell_condition, df['high'] * 1.005, np.nan)
                    
                    logger.info(f"Manual strategy quorum: {final_buy_condition.sum()} buy signals, {final_sell_condition.sum()} sell signals "
                               f"(threshold: {quorum_threshold*100}%, {selected_indicator_count} indicators)")
            
        elif 'ai_strategy' in strategy_name or strategy_name == 'ai strategy':
            # Extract all AI strategy settings
            rsi_settings = indicator_settings.get('RSI', {}) if indicator_settings else {}
            macd_settings = indicator_settings.get('MACD', {}) if indicator_settings else {}
            bb_settings = indicator_settings.get('BB', {}) if indicator_settings else {}
            ma_cross_settings = indicator_settings.get('MA_CROSS', {}) if indicator_settings else {}
            
            logger.debug(f"AI Strategy settings - RSI: {rsi_settings}, MACD: {macd_settings}, BB: {bb_settings}, MA_CROSS: {ma_cross_settings}")
            
            # Check if this is a new AI Strategy (no stored indicator settings) 
            # If so, use default AIIndicator parameters
            has_legacy_settings = bool(rsi_settings or macd_settings or bb_settings or ma_cross_settings)
            
            if not has_legacy_settings:
                logger.info("AI Strategy with no stored indicator settings - using AIIndicator defaults")
                # Use default parameters that match indicator class defaults
                rsi_settings = {'period': 14, 'buy_threshold': 30, 'sell_threshold': 70}
                macd_settings = {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
                bb_settings = {'period': 20, 'std_dev_multiplier': 2.0}
                ma_cross_settings = {'short_period': 20, 'long_period': 50}
            
            # Plot MA Crossover
            if ma_cross_settings:
                short_period = ma_cross_settings.get('short_period', 9)
                long_period = ma_cross_settings.get('long_period', 21)
                
                # Adjust periods if necessary due to limited data
                usable_short_period = min(short_period, max(2, len(df) // 4)) if len(df) < short_period*2 else short_period
                usable_long_period = min(long_period, max(3, len(df) // 3)) if len(df) < long_period*2 else long_period
                
                if usable_short_period != short_period or usable_long_period != long_period:
                    logger.info(f"Adjusted MA periods from {short_period}/{long_period} to {usable_short_period}/{usable_long_period} due to limited data")
                
                # Calculate short and long MAs
                df['short_ma'] = df['close'].rolling(window=usable_short_period).mean()
                df['long_ma'] = df['close'].rolling(window=usable_long_period).mean()
                
                # Log the number of non-NaN values
                short_ma_non_nan = df['short_ma'].count()
                long_ma_non_nan = df['long_ma'].count()
                logger.debug(f"MA Cross - Short MA: {short_ma_non_nan}, Long MA: {long_ma_non_nan} non-NaN values out of {len(df)} rows")
                
            # Plot Bollinger Bands
            if bb_settings:
                bb_period = bb_settings.get('period', 20)
                bb_std = bb_settings.get('std_dev_multiplier', 2)
                
                # Adjust period if necessary
                usable_period = min(bb_period, max(2, len(df) // 2)) if len(df) < bb_period*2 else bb_period
                if usable_period != bb_period:
                    logger.info(f"Adjusted BB period from {bb_period} to {usable_period} due to limited data")
                
                # Calculate Bollinger Bands
                ma = df['close'].rolling(window=usable_period).mean()
                std = df['close'].rolling(window=usable_period).std()
                df['bb_upper'] = ma + (std * bb_std)
                df['bb_middle'] = ma
                df['bb_lower'] = ma - (std * bb_std)
                
                # Log the number of non-NaN values
                non_nan_count = df['bb_middle'].count()
                logger.debug(f"BB columns have {non_nan_count} non-NaN values out of {len(df)} rows")
                
            # Calculate and plot RSI
            if rsi_settings:
                rsi_period = rsi_settings.get('period', 14)
                buy_threshold = rsi_settings.get('buy_threshold', 30)
                sell_threshold = rsi_settings.get('sell_threshold', 70)
                
                # Adjust period if necessary
                usable_period = min(rsi_period, max(2, len(df) // 2)) if len(df) < rsi_period*2 else rsi_period
                if usable_period != rsi_period:
                    logger.info(f"Adjusted RSI period from {rsi_period} to {usable_period} due to limited data")
                
                # Calculate RSI - using simple implementation
                try:
                    # Calculate price changes
                    delta = df['close'].diff()
                    
                    # Create gain (up) and loss (down) series
                    gain = delta.copy()
                    loss = delta.copy()
                    gain[gain < 0] = 0
                    loss[loss > 0] = 0
                    loss = abs(loss)
                    
                    # Calculate average gain and loss over period
                    avg_gain = gain.rolling(window=usable_period).mean()
                    avg_loss = loss.rolling(window=usable_period).mean()
                    
                    # Calculate RS and RSI
                    rs = avg_gain / avg_loss
                    df['rsi'] = 100 - (100 / (1 + rs))
                    
                    # Log the number of non-NaN values
                    non_nan_count = df['rsi'].count()
                    logger.debug(f"RSI column has {non_nan_count} non-NaN values out of {len(df)} rows")
                    
                    # Normalize RSI to price range for plotting on the same chart if needed
                    min_price = df['low'].min()
                    max_price = df['high'].max()
                    price_range = max_price - min_price
                    
                    # Normalize RSI to 30% of the price range at the bottom of the chart
                    df['rsi_normalized'] = min_price + (df['rsi'] / 100) * (price_range * 0.3)
                    
                except Exception as e:
                    logger.error(f"Failed to calculate RSI: {e}", exc_info=True)
            
            # Try to create a composite signal line that approximates the AI strategy's weighting
            try:
                # We need at least some of the indicators to create a composite
                if any(key in df.columns for key in ['short_ma', 'long_ma', 'rsi', 'bb_upper', 'bb_lower']):
                    # Create a simple weighted composite signal
                    # This is just an approximation since we don't know the actual algorithm
                    df['composite_signal'] = 0
                    
                    if 'short_ma' in df.columns and 'long_ma' in df.columns:
                        # Add crossover component (range -1 to 1)
                        df['ma_cross_signal'] = (df['short_ma'] - df['long_ma']) / df['close'] * 10  # Scale for visibility
                        df['composite_signal'] += df['ma_cross_signal'] * 0.4  # 40% weight
                    
                    if 'rsi' in df.columns:
                        # Add RSI component (normalized to -1 to 1 where 50 is neutral)
                        df['rsi_signal'] = (df['rsi'] - 50) / 50
                        df['composite_signal'] += df['rsi_signal'] * 0.3  # 30% weight
                    
                    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and 'bb_middle' in df.columns:
                        # Add BB component (how far price is from middle band, normalized)
                        df['bb_signal'] = (df['close'] - df['bb_middle']) / (df['bb_upper'] - df['bb_middle'])
                        df['bb_signal'] = df['bb_signal'].clip(-1, 1)  # Limit to -1 to 1 range
                        df['composite_signal'] += df['bb_signal'] * 0.3  # 30% weight
                    
                    # Scale the composite signal to price values for plotting
                    signal_min, signal_max = -1, 1
                    min_price = df['low'].min()
                    max_price = df['high'].max()
                    mid_price = (min_price + max_price) / 2
                    price_range = max_price - min_price
                    signal_range = price_range * 0.6  # Use 60% of price range
                    
                    df['composite_signal_scaled'] = mid_price + df['composite_signal'] * (signal_range / 2)
                    
                    # --- Generate Buy/Sell Signals for Markers based on AI Strategy Blueprint ---
                    buy_threshold = indicator_settings.get('buy_threshold', 0.6)
                    sell_threshold = indicator_settings.get('sell_threshold', -0.6)

                    # A buy signal is when the composite signal crosses ABOVE the buy threshold
                    buy_condition = (df['composite_signal'] > buy_threshold) & (df['composite_signal'].shift(1) <= buy_threshold)
                    # A sell signal is when the composite signal crosses BELOW the sell threshold
                    sell_condition = (df['composite_signal'] < sell_threshold) & (df['composite_signal'].shift(1) >= sell_threshold)

                    # Place marker below the low for buys, and above the high for sells for visibility
                    df['buy_signal'] = np.where(buy_condition, df['low'] * 0.995, np.nan)
                    df['sell_signal'] = np.where(sell_condition, df['high'] * 1.005, np.nan)

                    logger.info(f"Generated {df['buy_signal'].count()} buy signals and {df['sell_signal'].count()} sell signals using thresholds ({buy_threshold}/{sell_threshold}).")

            except Exception as e:
                logger.error(f"Failed to create composite signal: {e}", exc_info=True)
        
        return df, strategy_name

    def update_dynamic_content(self):
        """Updates dynamic content elements like time since creation"""
        if not self.current_trade_id or not self.creation_timestamp:
            return
            
        try:
            # Calculate time since trade creation
            now = datetime.now()
            created_time = datetime.fromtimestamp(self.creation_timestamp)
            time_diff = now - created_time
            
            # Format time difference as days, hours, minutes, seconds
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = "Running for: "
            if days > 0:
                time_str += f"{days}d "
            time_str += f"{hours:02}h:{minutes:02}m:{seconds:02}s"
            
            # Display in creation date field
            creation_date_field = self.ui.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea
            current_text = creation_date_field.text().split('\n')[0]
            creation_date_field.setText(f"{current_text}\n{time_str}")
            
        except Exception as e:
            logger.error(f"Error updating dynamic content: {e}", exc_info=True)
    
    def _format_number(self, value):
        """Format numbers with thousands separators"""
        if isinstance(value, (int, float)):
            try:
                return f"{value:,}"
            except:
                return str(value)
        return str(value)

    def _load_pixmap_for_token(self, token_address: str, size: int = 48) -> QPixmap:
        """Loads a QPixmap for a token, using a default if not found."""
        default_icon_path = PACKAGE_ROOT / "images" / "default_token_icon.png"
        pixmap = QPixmap(str(default_icon_path))

        if not token_address:
            return pixmap

        try:
            token_info = self.token_manager.get_token_by_address(token_address)
            if token_info and token_info.get('icon_local_path'):
                icon_path = PACKAGE_ROOT / token_info['icon_local_path']
                if icon_path.is_file():
                    loaded_pixmap = QPixmap(str(icon_path))
                    if not loaded_pixmap.isNull():
                        pixmap = loaded_pixmap
                else:
                    logger.warning(f"Icon path in DB for {token_address} does not exist: {icon_path}")
        except Exception as e:
            logger.error(f"Error loading icon for {token_address}: {e}", exc_info=True)
        
        return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def _normalize_rsi_for_chart(self, df):
        """Normalize RSI values to fit within the chart's price range."""
        min_price = df['low'].min()
        max_price = df['high'].max()
        price_range = max_price - min_price
        
        # Normalize RSI to fit within the price range
        df['rsi_norm'] = (df['rsi'] / 100) * price_range + min_price
        
        return df
