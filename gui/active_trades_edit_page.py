from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from database.trade_manager import TradeManager
from database.tokens import TokenManager  # Add this for token icon management
from gui.active_trades_ui import Ui_ActiveTradesTabMain
from services.trade_monitor import TradeMonitor
from gui.overlapping_icon_widget import OverlappingIconWidget
from gui.components.toggle_switch import TokenSelector, ToggleSwitch
from decimal import Decimal, InvalidOperation
from pathlib import Path
from config.paths import PACKAGE_ROOT
import logging
import json

logger = logging.getLogger(__name__)

class ActiveTradeEditPage(QWidget):
    """Manages the 'Edit' page of the Active Trades tab."""
    trade_updated = Signal(int)

    def __init__(self, ui: Ui_ActiveTradesTabMain, trade_manager: TradeManager, parent=None):
        super().__init__(parent)
        self.ui = ui
        self.trade_manager = trade_manager
        self.current_trade_id = None
        
        # Get token manager for icon loading
        self.token_manager = None  # Will be set from ActiveTradesTabMain
        
        # Store token addresses for current trade (used when switching strategies)
        self.current_base_token_address = None
        self.current_quote_token_address = None
        self.current_base_token_symbol = None
        self.current_quote_token_symbol = None
        self.current_pricing_token = None
        
        # Flag to prevent recursive updates when programmatically setting checkbox states
        self.updating_checkboxes = False
        
        # Create TokenPairDisplay widget to replace the QDial placeholder
        self.token_pair_display = None
        self._setup_token_pair_display()
        
        # Create accumulate token toggle to replace radio buttons
        self.accumulate_token_toggle = None
        self._setup_accumulate_token_toggle()
        
        # Setup connections for the edit page buttons
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBackButton.clicked.connect(self.go_back_to_list)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton.clicked.connect(self.save_trade_changes)
        
        # Resize the trade pair text area to make room for ticker and icons
        trade_pair_area = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea
        geom = trade_pair_area.geometry()
        trade_pair_area.setGeometry(geom.x(), geom.y(), 128, geom.height())
        
        # Connect indicator/strategy group toggles to enforce compatibility
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.toggled.connect(self.enforce_indicator_compatibility)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.toggled.connect(self.enforce_indicator_compatibility)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.toggled.connect(self.enforce_indicator_compatibility)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.toggled.connect(self.enforce_indicator_compatibility)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.toggled.connect(self.enforce_indicator_compatibility)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.toggled.connect(self.enforce_indicator_compatibility)
        
        # Connect individual "Indicator Selected" checkboxes
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.clicked.connect(self.handle_indicator_checkbox)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.clicked.connect(self.handle_indicator_checkbox)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.clicked.connect(self.handle_indicator_checkbox)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.clicked.connect(self.handle_indicator_checkbox)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.clicked.connect(self.handle_indicator_checkbox)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.clicked.connect(self.handle_indicator_checkbox)
        
        # Connect individual indicator groups to enforce mutual exclusivity
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.toggled.connect(self.handle_indicator_group)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.toggled.connect(self.handle_indicator_group)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.toggled.connect(self.handle_indicator_group)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.toggled.connect(self.handle_indicator_group)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.toggled.connect(self.handle_indicator_group)
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.toggled.connect(self.handle_indicator_group)

    def set_token_manager(self, token_manager: TokenManager):
        """Set the token manager from the main class."""
        self.token_manager = token_manager

    def _setup_token_pair_display(self):
        """Setup the token pair display widget."""
        try:
            # Check if we're in responsive mode by looking for the placeholder's parent layout
            placeholder = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder
            
            if placeholder and placeholder.parent():
                # Responsive mode: Replace the placeholder label with OverlappingIconWidget
                parent_widget = placeholder.parent()
                
                # Get the placeholder's layout
                parent_layout = placeholder.parent().layout()
                
                if parent_layout:
                    # Find and replace placeholder in layout
                    for i in range(parent_layout.count()):
                        item = parent_layout.itemAt(i)
                        if item and item.layout():  # It's the icon_container HBoxLayout
                            container_layout = item.layout()
                            # Remove placeholder from center of container
                            for j in range(container_layout.count()):
                                container_item = container_layout.itemAt(j)
                                if container_item and container_item.widget() == placeholder:
                                    container_layout.removeWidget(placeholder)
                                    placeholder.deleteLater()
                                    
                                    # Insert OverlappingIconWidget in its place
                                    self.token_pair_display = OverlappingIconWidget(parent=parent_widget)
                                    self.token_pair_display.setMinimumSize(45, 25)
                                    container_layout.insertWidget(j, self.token_pair_display)
                                    logger.info("Replaced placeholder with OverlappingIconWidget in responsive layout")
                                    return
                
                # Fallback: Legacy mode with fixed geometry
                placeholder.hide()
                self.token_pair_display = OverlappingIconWidget(parent=parent_widget)
                self.token_pair_display.setGeometry(230, 45, 45, 25)
                self.token_pair_display.show()
                logger.info(f"Created OverlappingIconWidget with fixed geometry at {self.token_pair_display.geometry()}")
            else:
                logger.warning("IconsPlaceholder not found")
                
        except Exception as e:
            logger.error(f"Error setting up token pair display: {e}", exc_info=True)
    
    def _setup_accumulate_token_toggle(self):
        """Setup the accumulate token toggle switch wrapper for API compatibility."""
        try:
            # In responsive mode, the toggle is already created in the UI file
            # In legacy mode, radio buttons exist but are hidden
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenToggle'):
                # Responsive mode: Use the toggle created in UI file
                toggle_widget = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenToggle
                # Initially hide to prevent flash animation
                toggle_widget.hide()
            else:
                # Legacy mode: Create toggle dynamically and hide radio buttons
                if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne'):
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne.hide()
                if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo'):
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo.hide()
                
                toggle_widget = ToggleSwitch("Token 1", "Token 2", self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
                toggle_widget.setGeometry(QRect(50, 155, 71, 20))
                toggle_widget.hide()
            
            # Create a wrapper object with the methods we need
            class ToggleWrapper:
                def __init__(self, toggle):
                    self.toggle = toggle
                    
                def setTokens(self, token1, token2):
                    self.toggle.setLeftText(token1)
                    self.toggle.setRightText(token2)
                    
                def setSelection(self, is_right):
                    self.toggle.setChecked(is_right)
                    
                def show(self):
                    self.toggle.show()
                    
                def hide(self):
                    self.toggle.hide()
                    
                def isChecked(self):
                    return self.toggle.isChecked()
            
            self.accumulate_token_toggle_raw = toggle_widget
            self.accumulate_token_toggle = ToggleWrapper(toggle_widget)
                
        except Exception as e:
            logger.error(f"Error setting up accumulate token toggle: {e}")

    def load_trade_for_edit(self, trade_id: int):
        """Fetches and displays the details for a given trade ID in the edit form."""
        self.current_trade_id = trade_id
        
        # Clear feedback message from previous edits
        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText("")
        
        # Clear all fields first to prevent stale data from previous edits
        self._clear_all_indicator_fields()
        
        try:
            trade_data = self.trade_manager.get_trade_by_id(trade_id)
            if not trade_data:
                logger.warning(f"No trade data found for editing trade_id: {trade_id}")
                return

            logger.info(f"Loading trade {trade_id} with strategy: {trade_data.get('strategy_name', 'None')}")
            
            # Get the trade's strategy and indicator settings FIRST
            strategy_name = trade_data.get('strategy_name', '')
            indicator_settings_json = trade_data.get('indicator_settings_json', '{}')
            
            try:
                import json
                indicator_settings = json.loads(indicator_settings_json) if indicator_settings_json else {}
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in indicator_settings_json for trade {trade_id}")
                indicator_settings = {}
            
            logger.info(f"Strategy: {strategy_name}, Settings: {indicator_settings}")
            
            # Clear previous selections - uncheck all groups and checkboxes
            self.updating_checkboxes = True  # Prevent recursive updates
            
            indicator_groups = [
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup,
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup,
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup,
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup,
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup,
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup
            ]
            
            # Uncheck all indicator groups and their checkboxes first
            for group in indicator_groups:
                group.setChecked(False)
            
            # Also uncheck all individual checkboxes
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setChecked(False)
            
            self.updating_checkboxes = False  # Re-enable updates
            
            # Display trade ID
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea.setText(str(trade_id))
            
            # Display trade pair information
            base_token_symbol = trade_data.get('base_token_symbol', 'Unknown')
            quote_token_symbol = trade_data.get('quote_token_symbol', 'Unknown')
            trade_pair_text = f"{base_token_symbol}/{quote_token_symbol}"
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea.setText(trade_pair_text)
            
            # Display token amount (now a QLabel, not editable) - use CURRENT amount, not start amount
            token_amount = trade_data.get('trade_amount', trade_data.get('start_amount', 0))
            # Convert to Decimal for safe formatting (might be string from database)
            try:
                token_amount_decimal = Decimal(str(token_amount))
                formatted_amount = f"{token_amount_decimal:,.6f}".rstrip('0').rstrip('.')
            except (ValueError, InvalidOperation):
                formatted_amount = str(token_amount)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField.setText(formatted_amount)
            
            # Set the token ticker based on current holding
            current_token = trade_data.get('trade_token_address', trade_data.get('start_token_address'))
            base_token = trade_data.get('base_token')
            if current_token == base_token:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setText(base_token_symbol)
            else:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setText(quote_token_symbol)
            
            # Set accumulation token toggle
            accumulation_token_address = trade_data.get('accumulation_token_address')
            base_token_address = trade_data.get('base_token')
            quote_token_address = trade_data.get('quote_token')
            
            # Store token info for later use (e.g., when switching strategies)
            self.current_base_token_address = base_token_address
            self.current_quote_token_address = quote_token_address
            self.current_base_token_symbol = base_token_symbol
            self.current_quote_token_symbol = quote_token_symbol
            
            # Set token symbols on toggle switch
            if self.accumulate_token_toggle:
                # Set tokens first before setting selection
                self.accumulate_token_toggle.setTokens(base_token_symbol, quote_token_symbol)
                # Set selection: False = first token (base), True = second token (quote)
                if accumulation_token_address == base_token_address:
                    self.accumulate_token_toggle.setSelection(False)
                else:
                    self.accumulate_token_toggle.setSelection(True)
                # Now show the toggle after everything is set
                self.accumulate_token_toggle.show()
            
            # Update token pair display widget (same as Info page approach)
            if self.token_pair_display:
                base_token = trade_data.get('base_token', '')
                quote_token = trade_data.get('quote_token', '')
                
                base_pixmap = self._load_pixmap_for_token(base_token, size=25)
                quote_pixmap = self._load_pixmap_for_token(quote_token, size=25)
                self.token_pair_display.set_icons(base_pixmap, quote_pixmap)
                            
            # Update current prices
            self._update_current_prices(trade_data)
            
            # Set compound profit checkbox - database column is 'is_compounding'
            is_compounding = trade_data.get('is_compounding', 0)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setChecked(bool(is_compounding))
            
            # Load stop loss and trailing stop values from indicator_settings_json
            stop_loss_pct = indicator_settings.get('stop_loss_percentage', 0.0)
            trailing_stop_pct = indicator_settings.get('trailing_stop_percentage', 0.0)
            
            # Display stop values (0 = disabled, empty field)
            if stop_loss_pct > 0:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setText(str(stop_loss_pct))
            else:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setText("")
                
            if trailing_stop_pct > 0:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setText(str(trailing_stop_pct))
            else:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setText("")
            
            # NOW SET THE STRATEGY AND INDICATORS BASED ON THE LOADED DATA
            logger.info(f"Setting strategy: {strategy_name}")
            
            # Handle each strategy type
            if strategy_name == 'Ping Pong':
                logger.info("Loading Ping Pong strategy")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.setChecked(True)
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setChecked(True)
                
                # Set Ping Pong parameters
                buy_price = indicator_settings.get('buy_price', '')
                sell_price = indicator_settings.get('sell_price', '')
                pricing_token = indicator_settings.get('pricing_token', 'base')
                pricing_token_symbol = indicator_settings.get('pricing_token_symbol', '')
                
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setText(str(buy_price))
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setText(str(sell_price))
                
                # Update the price symbol labels
                if pricing_token_symbol:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setText(pricing_token_symbol)
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setText(pricing_token_symbol)
                else:
                    # Fallback to determining from token addresses
                    if pricing_token == 'base':
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setText(base_token_symbol)
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setText(base_token_symbol)
                    else:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setText(quote_token_symbol)
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setText(quote_token_symbol)
                
                # Store pricing token info for save operation
                self.ping_pong_pricing_token = pricing_token
                self.ping_pong_pricing_token_symbol = pricing_token_symbol if pricing_token_symbol else (base_token_symbol if pricing_token == 'base' else quote_token_symbol)
                self.current_pricing_token = pricing_token
                
                # Update placeholder suggestions with current price +/- 5%
                self._update_ping_pong_placeholders(base_token_address, quote_token_address, pricing_token)
                
            elif strategy_name == 'AI_Strategy':
                logger.info("Loading AI Strategy")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.setChecked(True)
                if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox'):
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setChecked(True)
                
                # AI Strategy uses ML - no manual field configuration needed
                    
            elif strategy_name == 'Manual':
                logger.info(f"Loading Manual strategy with individual indicators. Settings keys: {list(indicator_settings.keys())}")
                # For Manual strategy, check each indicator that was saved
                
                if 'RSI' in indicator_settings:
                    logger.info("Setting RSI indicator fields")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.setChecked(True)
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setChecked(True)
                    
                    rsi_settings = indicator_settings.get('RSI', {})
                    logger.debug(f"RSI settings: {rsi_settings}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.setText(str(rsi_settings.get('period', 14)))
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.setText(str(rsi_settings.get('buy_threshold', 30)))
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.setText(str(rsi_settings.get('sell_threshold', 70)))
                    logger.info("RSI fields populated")
                
                if 'MACD' in indicator_settings:
                    logger.info("Setting MACD indicator fields")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.setChecked(True)
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setChecked(True)
                    
                    macd_settings = indicator_settings.get('MACD', {})
                    logger.debug(f"MACD settings: {macd_settings}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.setText(str(macd_settings.get('fast_period', 12)))
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.setText(str(macd_settings.get('slow_period', 26)))
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.setText(str(macd_settings.get('signal_period', 9)))
                    logger.info("MACD fields populated")
                
                if 'BB' in indicator_settings:
                    logger.info("Setting BB indicator fields")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.setChecked(True)
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setChecked(True)
                    
                    bb_settings = indicator_settings.get('BB', {})
                    logger.debug(f"BB settings: {bb_settings}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.setText(str(bb_settings.get('period', 20)))
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.setText(str(bb_settings.get('std_dev_multiplier', 2.0)))
                    logger.info("BB fields populated")
                
                if 'MA_CROSS' in indicator_settings:
                    logger.info("Setting MA Crossover indicator fields")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.setChecked(True)
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setChecked(True)
                    
                    ma_settings = indicator_settings.get('MA_CROSS', {})
                    logger.debug(f"MA_CROSS settings: {ma_settings}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.setText(str(ma_settings.get('short_period', 20)))
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.setText(str(ma_settings.get('long_period', 50)))
                    logger.info("MA Crossover fields populated")
            else:
                logger.warning(f"Unknown strategy: {strategy_name}")
            
            logger.info(f"Successfully loaded edit form for trade {trade_id} with strategy {strategy_name}")

        except Exception as e:
            logger.error(f"Failed to load trade for editing (trade_id {trade_id}): {e}", exc_info=True)

    def save_trade_changes(self):
        """Gathers data from the form and saves it to the database."""
        if self.current_trade_id is None:
            logger.error("save_trade_changes called with no active trade_id.")
            return

        try:
            update_data = {}
            indicator_settings = {}
            selected_strategy = None
            
            # Token amount is display-only (QLabel) and cannot be edited
            # No validation needed for this field
            
            # Check if accumulation token selection has changed
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne'):
                # Find token addresses first
                trade_data = self.trade_manager.get_trade_by_id(self.current_trade_id)
                if trade_data:
                    base_token_address = trade_data.get('base_token')
                    quote_token_address = trade_data.get('quote_token')
                    base_token_symbol = trade_data.get('base_token_symbol')
                    quote_token_symbol = trade_data.get('quote_token_symbol')
                    
                    # Get accumulation token selection
                    # The toggle state corresponds to which token to accumulate
                    # False = left token (base), True = right token (quote)
                    is_quote_selected = self.accumulate_token_toggle_raw.isChecked()
                    
                    if is_quote_selected:
                        update_data['accumulation_token_address'] = quote_token_address
                        update_data['accumulation_token_symbol'] = quote_token_symbol
                    else:
                        update_data['accumulation_token_address'] = base_token_address
                        update_data['accumulation_token_symbol'] = base_token_symbol
            
            # Check which strategy/indicator is selected and gather their settings
            
            # RSI Indicator
            rsi_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup
            rsi_checkbox = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox
            if rsi_group.isChecked() or (rsi_checkbox and rsi_checkbox.isChecked()):
                selected_strategy = 'RSI'
                rsi_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.text()
                buy_threshold = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.text()
                sell_threshold = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.text()
                
                try:
                    rsi_period_int = int(rsi_period) if rsi_period else 14
                    buy_threshold_float = float(buy_threshold) if buy_threshold else 30
                    sell_threshold_float = float(sell_threshold) if sell_threshold else 70
                    
                    # Validation
                    if rsi_period_int <= 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: RSI period must be greater than zero.")
                        return
                    
                    if not (0 <= buy_threshold_float <= 100 and 0 <= sell_threshold_float <= 100):
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: RSI thresholds must be between 0 and 100.")
                        return
                        
                    if buy_threshold_float >= sell_threshold_float:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: RSI buy threshold must be less than sell threshold.")
                        return
                    
                    indicator_settings['period'] = rsi_period_int
                    indicator_settings['buy_threshold'] = buy_threshold_float
                    indicator_settings['sell_threshold'] = sell_threshold_float
                except ValueError:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                        "Error: RSI settings must be numbers. Period should be an integer.")
                    return
            
            # MACD Indicator
            macd_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup
            macd_checkbox = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox
            if macd_group.isChecked() or (macd_checkbox and macd_checkbox.isChecked()):
                selected_strategy = 'MACD'
                fast_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.text()
                slow_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.text()
                signal_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.text()
                
                try:
                    fast_period_int = int(fast_period) if fast_period else 12
                    slow_period_int = int(slow_period) if slow_period else 26
                    signal_period_int = int(signal_period) if signal_period else 9
                    
                    # Validation
                    if fast_period_int <= 0 or slow_period_int <= 0 or signal_period_int <= 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: MACD periods must be greater than zero.")
                        return
                        
                    if fast_period_int >= slow_period_int:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: MACD fast period must be less than slow period.")
                        return
                    
                    indicator_settings['fast_period'] = fast_period_int
                    indicator_settings['slow_period'] = slow_period_int
                    indicator_settings['signal_period'] = signal_period_int
                except ValueError:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                        "Error: MACD settings must be integers.")
                    return
            
            # Bollinger Bands Indicator
            bb_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup
            bb_checkbox = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox
            if bb_group.isChecked() or (bb_checkbox and bb_checkbox.isChecked()):
                selected_strategy = 'Bollinger Bands'
                bb_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.text()
                std_dev = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.text()
                
                try:
                    bb_period_int = int(bb_period) if bb_period else 20
                    std_dev_float = float(std_dev) if std_dev else 2.0
                    
                    # Validation
                    if bb_period_int <= 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Bollinger Bands period must be greater than zero.")
                        return
                        
                    if std_dev_float <= 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Standard deviation multiplier must be greater than zero.")
                        return
                    
                    indicator_settings['period'] = bb_period_int
                    indicator_settings['std_dev_multiplier'] = std_dev_float
                except ValueError:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                        "Error: BB period must be an integer and std dev multiplier must be a number.")
                    return
            
            # Moving Average Crossover Indicator
            ma_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup
            ma_checkbox = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox
            if ma_group.isChecked() or (ma_checkbox and ma_checkbox.isChecked()):
                selected_strategy = 'Moving Average Crossover'
                short_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.text()
                long_period = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.text()
                
                try:
                    short_period_int = int(short_period) if short_period else 20
                    long_period_int = int(long_period) if long_period else 50
                    
                    # Validation
                    if short_period_int <= 0 or long_period_int <= 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: MA periods must be greater than zero.")
                        return
                        
                    if short_period_int >= long_period_int:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Short MA period must be less than long MA period.")
                        return
                    
                    indicator_settings['short_period'] = short_period_int
                    indicator_settings['long_period'] = long_period_int
                except ValueError:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                        "Error: MA Crossover periods must be integers.")
                    return
            
            # Ping Pong Strategy
            ping_pong_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup
            ping_pong_checkbox = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox
            if ping_pong_group.isChecked() or (ping_pong_checkbox and ping_pong_checkbox.isChecked()):
                selected_strategy = 'Ping Pong'
                buy_price = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.text()
                sell_price = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.text()
                
                # Ensure both prices are provided and valid
                if not buy_price or not sell_price:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                        "Error: Both buy and sell prices must be specified for Ping Pong strategy.")
                    return
                    
                try:
                    buy_price_float = float(buy_price)
                    sell_price_float = float(sell_price)
                    
                    # Validation: prices must be positive
                    if buy_price_float <= 0 or sell_price_float <= 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Buy and sell prices must be greater than zero.")
                        return
                    
                    # Intuitive pricing: Buy low, sell high
                    # buy_price = price to BUY accumulation token (should be lower)
                    # sell_price = price to SELL accumulation token (should be higher)
                    if buy_price_float >= sell_price_float:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Buy Price must be lower than Sell Price.\n"
                            "Buy accumulation token when price is LOW, sell when price is HIGH.")
                        return
                    
                    indicator_settings['buy_price'] = buy_price_float
                    indicator_settings['sell_price'] = sell_price_float
                    indicator_settings['pricing_token'] = getattr(self, 'ping_pong_pricing_token', 'base')
                    indicator_settings['pricing_token_symbol'] = getattr(self, 'ping_pong_pricing_token_symbol', '')
                    
                except ValueError:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                        "Error: Ping Pong prices must be valid numbers.")
                    return
            
            # AI Strategy
            ai_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup
            ai_checkbox = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox
            if ai_group.isChecked() or (ai_checkbox and ai_checkbox.isChecked()):
                selected_strategy = 'AI_Strategy'
                # AI Strategy uses ML - preserve existing settings from database
                # Load existing indicator settings to preserve them
                trade_data = self.trade_manager.get_trade_by_id(self.current_trade_id)
                if trade_data:
                    existing_settings_json = trade_data.get('indicator_settings_json', '{}')
                    try:
                        import json
                        indicator_settings = json.loads(existing_settings_json) if existing_settings_json else {}
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse existing indicator_settings_json for trade {self.current_trade_id}")
                        indicator_settings = {}
                else:
                    indicator_settings = {}
            
            # Check for Multi-Indicator Strategy
            # Count how many individual indicator groups are checked
            checked_indicators = []
            if rsi_group.isChecked() or (rsi_checkbox and rsi_checkbox.isChecked()):
                checked_indicators.append('RSI')
            if macd_group.isChecked() or (macd_checkbox and macd_checkbox.isChecked()):
                checked_indicators.append('MACD')
            if bb_group.isChecked() or (bb_checkbox and bb_checkbox.isChecked()):
                checked_indicators.append('Bollinger Bands')
            if ma_group.isChecked() or (ma_checkbox and ma_checkbox.isChecked()):
                checked_indicators.append('Moving Average Crossover')
                
            # If multiple indicators are selected, consider it a Manual Strategy (user-managed indicators)
            if len(checked_indicators) > 1:
                selected_strategy = 'Manual'
                multi_settings = {}
                
                # Store settings for each selected indicator with description fields
                if 'RSI' in checked_indicators:
                    multi_settings['RSI'] = {
                        'period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.text() or 14),
                        'buy_threshold': float(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.text() or 30),
                        'sell_threshold': float(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.text() or 70),
                        'description': 'RSI settings for individual indicator'
                    }
                
                if 'MACD' in checked_indicators:
                    multi_settings['MACD'] = {
                        'fast_period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.text() or 12),
                        'slow_period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.text() or 26),
                        'signal_period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.text() or 9),
                        'description': 'MACD settings for individual indicator'
                    }
                
                if 'Bollinger Bands' in checked_indicators:
                    multi_settings['BB'] = {
                        'period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.text() or 20),
                        'std_dev_multiplier': float(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.text() or 2.0),
                        'description': 'Bollinger Bands settings for individual indicator'
                    }
                
                if 'Moving Average Crossover' in checked_indicators:
                    multi_settings['MA_CROSS'] = {
                        'short_period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.text() or 20),
                        'long_period': int(self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.text() or 50),
                        'description': 'Moving Average Crossover settings for individual indicator'
                    }
                
                # Add pricing token info from trade data
                trade_data = self.trade_manager.get_trade_by_id(self.current_trade_id)
                if trade_data:
                    # Get accumulation token to use as pricing token
                    accumulation_symbol = trade_data.get('accumulation_token_symbol', '')
                    multi_settings['pricing_token'] = 'base'
                    multi_settings['pricing_token_symbol'] = accumulation_symbol
                
                indicator_settings = multi_settings
            
            # Check if any strategy was selected
            if not selected_strategy:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                    "Error: Please select at least one indicator or strategy.")
                return
            
            # Get stop loss and trailing stop values (default 0 = disabled)
            stop_loss_pct = 0.0
            trailing_stop_pct = 0.0
            
            try:
                stop_loss_text = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.text().strip()
                if stop_loss_text:
                    stop_loss_pct = float(stop_loss_text)
                    if stop_loss_pct < 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Stop Loss must be 0 or positive")
                        return
            except ValueError:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                    "Error: Stop Loss must be a valid number")
                return
            
            try:
                trailing_stop_text = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.text().strip()
                if trailing_stop_text:
                    trailing_stop_pct = float(trailing_stop_text)
                    if trailing_stop_pct < 0:
                        self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                            "Error: Trailing Stop must be 0 or positive")
                        return
            except ValueError:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                    "Error: Trailing Stop must be a valid number")
                return
            
            # Add stop loss and trailing stop to indicator_settings
            indicator_settings['stop_loss_percentage'] = stop_loss_pct
            indicator_settings['trailing_stop_percentage'] = trailing_stop_pct
            
            # Convert indicator_settings to JSON
            import json
            indicator_settings_json = json.dumps(indicator_settings)
            
            # Update the trade with the new strategy and settings
            update_data['strategy_name'] = selected_strategy
            update_data['indicator_settings_json'] = indicator_settings_json
            
            # Get compound profit setting - database column is 'is_compounding'
            is_compounding = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.isChecked()
            update_data['is_compounding'] = 1 if is_compounding else 0
            
            # Save changes to the database
            success = self.trade_manager.update_trade(self.current_trade_id, update_data)
            
            if success:
                logger.info(f"Successfully updated trade {self.current_trade_id}")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                    f"Trade successfully updated with {selected_strategy} strategy!")
                self.trade_updated.emit(self.current_trade_id)
                self.go_back_to_list()  # Return to info screen after saving
            else:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                    "Error: Failed to update trade. Please check logs for details.")
                logger.warning(f"Failed to update trade {self.current_trade_id} in database")

        except Exception as e:
            error_msg = f"Failed to save changes for trade {self.current_trade_id}: {e}"
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText(
                f"Error: {str(e)}")
            logger.error(error_msg, exc_info=True)

    def go_back_to_list(self):
        """Switches the stacked widget back to the list of trades (index 0)."""
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0)

    def enforce_indicator_compatibility(self, checked):
        """
        Enforces compatibility rules between indicators and strategies:
        - Base indicators (RSI, MACD, BB, MA Crossover) can be combined with each other
        - Strategies (AI_Strategy, Ping Pong) cannot be combined with any other indicator or strategy
        """
        if self.updating_checkboxes:
            return
            
        self.updating_checkboxes = True
        
        # Get all indicator and strategy groups
        rsi_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup
        macd_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup
        bb_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup
        ma_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup
        ping_pong_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup
        ai_strategy_group = self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup
        
        # Identify which group was toggled
        sender = self.sender()
        
        # Group the widgets by type for easier handling
        base_indicators = [rsi_group, macd_group, bb_group, ma_group]
        strategies = [ping_pong_group, ai_strategy_group]
        
        # If a strategy was toggled ON
        if checked and (sender in strategies):
            logger.info(f"Strategy selected: {sender.objectName()}")
            
            # Uncheck all other indicators and strategies
            for group in base_indicators + strategies:
                if group != sender:
                    group.setChecked(False)
                    
            # Make sure the selected indicator checkbox is checked
            selected_checkbox_name = f"{sender.objectName()}SelectedCheckbox"
            selected_checkbox = getattr(self.ui, selected_checkbox_name, None)
            if selected_checkbox:
                selected_checkbox.setChecked(True)
        
        # If a base indicator was toggled ON
        elif checked and (sender in base_indicators):
            logger.info(f"Base indicator selected: {sender.objectName()}")
            
            # Uncheck any strategies
            for strategy in strategies:
                strategy.setChecked(False)
                
            # Make sure the selected indicator checkbox is checked
            selected_checkbox_name = f"{sender.objectName()}IndicatorSelectedCheckbox"
            selected_checkbox = getattr(self.ui, selected_checkbox_name, None)
            if selected_checkbox:
                selected_checkbox.setChecked(True)
        
        self.updating_checkboxes = False

    def handle_indicator_checkbox(self):
        """
        Handles the "Indicator Selected" checkbox clicks to ensure only one strategy can be active at a time.
        """
        if self.updating_checkboxes:
            return
            
        self.updating_checkboxes = True
        
        # Get all indicator checkboxes
        checkboxes = [
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox
        ]
        
        # Identify which checkbox was clicked
        sender = self.sender()
        is_checked = sender.isChecked()
        
        # Define whether this is a strategy checkbox (mutually exclusive with all others)
        # or a base indicator (can be combined with other base indicators)
        is_strategy = sender in [
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox
        ]
        
        # If a strategy checkbox was checked, uncheck all other checkboxes
        if is_checked and is_strategy:
            for checkbox in checkboxes:
                if checkbox != sender:
                    checkbox.setChecked(False)
        
        # If a base indicator checkbox was checked, only uncheck strategy checkboxes
        elif is_checked and not is_strategy:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setChecked(False)
        
        # Make sure associated group box is toggled appropriately
        if sender == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.setChecked(is_checked)
        elif sender == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.setChecked(is_checked)
        elif sender == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.setChecked(is_checked)
        elif sender == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.setChecked(is_checked)
        elif sender == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.setChecked(is_checked)
            # When Ping Pong is selected, update placeholders and token symbols
            if is_checked and self.current_base_token_address and self.current_quote_token_address:
                self._setup_ping_pong_ui()
        elif sender == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.setChecked(is_checked)
        
        self.updating_checkboxes = False

    def handle_indicator_group(self, checked):
        """
        Handles the indicator group toggles to enforce mutual exclusivity and clear sub-checkboxes.
        """
        if self.updating_checkboxes:
            return
            
        self.updating_checkboxes = True
        
        # Get all indicator groups
        groups = [
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup,
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup
        ]
        
        # Identify which group was toggled
        sender = self.sender()
        
        # If a group was checked, uncheck all other groups
        if checked:
            for group in groups:
                if group != sender:
                    group.setChecked(False)
                    # Also uncheck the sub-checkboxes when unchecking a group
                    self._uncheck_group_checkboxes(group)
        else:
            # When unchecking a group, also uncheck its sub-checkboxes
            self._uncheck_group_checkboxes(sender)
        
        self.updating_checkboxes = False
    
    def _uncheck_group_checkboxes(self, group):
        """Helper method to uncheck all checkboxes within a group when the group is deselected."""
        # RSI group checkboxes
        if group == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
        
        # MACD group checkboxes  
        elif group == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
        
        # BB group checkboxes
        elif group == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
        
        # MA Crossover group checkboxes
        elif group == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
        
        # Ping Pong group checkboxes
        elif group == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setChecked(False)
        
        # AI Strategy group checkboxes
        elif group == self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup:
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setChecked(False)

    def _load_pixmap_for_token(self, token_address: str, size: int = 48) -> QPixmap:
        """Loads a QPixmap for a token, using a default if not found."""
        default_icon_path = PACKAGE_ROOT / "images" / "default_token_icon.png"
        pixmap = QPixmap(str(default_icon_path))

        if not token_address or not self.token_manager:
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

    def _update_current_prices(self, trade_data):
        """Update the current prices display."""
        try:
            # Get token manager to fetch prices
            if not self.token_manager:
                from database.database import Database
                db = Database()
                self.token_manager = db.get_token_manager()
            
            base_token = trade_data.get('base_token')
            quote_token = trade_data.get('quote_token')
            base_symbol = trade_data.get('base_token_symbol', 'Unknown')
            quote_symbol = trade_data.get('quote_token_symbol', 'Unknown')
            
            # Get token prices
            base_token_info = self.token_manager.get_token_by_address(base_token)
            quote_token_info = self.token_manager.get_token_by_address(quote_token)
            
            if base_token_info and quote_token_info:
                base_price_xrd = Decimal(str(base_token_info.get('token_price_xrd', 0)))
                quote_price_xrd = Decimal(str(quote_token_info.get('token_price_xrd', 0)))
                
                if base_price_xrd > 0 and quote_price_xrd > 0:
                    # Calculate relative prices
                    quote_per_base = base_price_xrd / quote_price_xrd
                    base_per_quote = quote_price_xrd / base_price_xrd
                    
                    # Update price labels
                    price_one_text = f"1 {base_symbol} = {quote_per_base:.6f} {quote_symbol}"
                    price_two_text = f"1 {quote_symbol} = {base_per_quote:.6f} {base_symbol}"
                    
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setText(price_one_text)
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setText(price_two_text)
                else:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setText("Price data unavailable")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setText("")
            else:
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setText("Price data unavailable")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setText("")
                
        except Exception as e:
            logger.error(f"Failed to update current prices: {e}")
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setText("Price data unavailable")
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setText("")

    def _clear_all_indicator_fields(self):
        """Clear all indicator and strategy fields to prevent stale data."""
        try:
            # Clear Ping Pong fields (always exist)
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.clear()
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.clear()
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setPlaceholderText("")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setPlaceholderText("")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setText("")
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setText("")
            
            # Clear RSI fields - CORRECT widget names with safety checks
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.clear()
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.clear()
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.clear()
            
            # Clear MACD fields - CORRECT widget names with safety checks
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.clear()
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.clear()
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.clear()
            
            # Clear BB fields - CORRECT widget names with safety checks
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.clear()
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.clear()
            
            # Clear MA fields - CORRECT widget names with safety checks
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.clear()
            if hasattr(self.ui, 'ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField'):
                self.ui.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.clear()
            
            logger.debug("Cleared all indicator fields")
            
        except Exception as e:
            logger.error(f"Error clearing indicator fields: {e}", exc_info=True)
            # Don't re-raise - we want to continue loading even if clear fails

    def _setup_ping_pong_ui(self):
        """
        Set up Ping Pong UI when user switches to this strategy.
        Determines pricing token, updates symbol labels, and sets placeholder suggestions.
        """
        try:
            if not self.token_manager:
                logger.warning("Token manager not available for Ping Pong setup")
                return
            
            # Get token data
            base_token = self.token_manager.get_token_by_address(self.current_base_token_address)
            quote_token = self.token_manager.get_token_by_address(self.current_quote_token_address)
            
            if not base_token or not quote_token:
                logger.warning("Token data not available for Ping Pong setup")
                return
            
            base_price_usd = Decimal(str(base_token.get('token_price_usd', 0)))
            quote_price_usd = Decimal(str(quote_token.get('token_price_usd', 0)))
            
            # Determine pricing token (more expensive token for decimal display)
            if base_price_usd > 0 and quote_price_usd > 0:
                if base_price_usd > quote_price_usd:
                    # Base is more expensive - use it for pricing
                    pricing_token = 'base'
                    pricing_token_symbol = self.current_base_token_symbol
                    logger.debug(f"Pricing token set to 'base' ({self.current_base_token_symbol}) - base_USD={base_price_usd} > quote_USD={quote_price_usd}")
                else:
                    # Quote is more expensive - use it for pricing
                    pricing_token = 'quote'
                    pricing_token_symbol = self.current_quote_token_symbol
                    logger.debug(f"Pricing token set to 'quote' ({self.current_quote_token_symbol}) - quote_USD={quote_price_usd} >= base_USD={base_price_usd}")
            else:
                # Default to quote token if prices unavailable
                pricing_token = 'quote'
                pricing_token_symbol = self.current_quote_token_symbol
                logger.warning(f"Defaulting pricing token to 'quote' ({self.current_quote_token_symbol}) - prices unavailable")
            
            # Store for save operation
            self.ping_pong_pricing_token = pricing_token
            self.ping_pong_pricing_token_symbol = pricing_token_symbol
            self.current_pricing_token = pricing_token
            
            # Update symbol labels
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setText(pricing_token_symbol)
            self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setText(pricing_token_symbol)
            
            # Update placeholder suggestions
            self._update_ping_pong_placeholders(self.current_base_token_address, self.current_quote_token_address, pricing_token)
            
            logger.debug(f"Ping Pong UI setup complete - pricing_token='{pricing_token}', symbol='{pricing_token_symbol}'")
            
        except Exception as e:
            logger.error(f"Error setting up Ping Pong UI: {e}")

    def _update_ping_pong_placeholders(self, base_token_address, quote_token_address, pricing_token):
        """Update ping pong price field placeholders with current price +/- 5% suggestions."""
        try:
            # Get token manager
            if not self.token_manager:
                logger.warning("Token manager not available for placeholder suggestions")
                return
            
            # Get current token prices
            base_token = self.token_manager.get_token_by_address(base_token_address)
            quote_token = self.token_manager.get_token_by_address(quote_token_address)
            
            if not base_token or not quote_token:
                logger.warning("Token data not available for placeholder suggestions")
                return
            
            base_price_usd = Decimal(str(base_token.get('token_price_usd', 0)))
            quote_price_usd = Decimal(str(quote_token.get('token_price_usd', 0)))
            
            if base_price_usd > 0 and quote_price_usd > 0:
                # Calculate current price based on pricing_token
                # This matches the user-friendly decimal display
                if base_price_usd > quote_price_usd:
                    # Base is more expensive - display shows quote/base (decimal)
                    current_price = quote_price_usd / base_price_usd
                else:
                    # Quote is more expensive - display shows base/quote (decimal)
                    current_price = base_price_usd / quote_price_usd
                
                # Suggest buy 5% below current, sell 5% above current
                buy_suggestion = current_price * Decimal('0.95')
                sell_suggestion = current_price * Decimal('1.05')
                
                # Format based on magnitude
                if current_price < Decimal('0.01'):
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setPlaceholderText(f"{buy_suggestion:.6f}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setPlaceholderText(f"{sell_suggestion:.6f}")
                elif current_price < Decimal('1'):
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setPlaceholderText(f"{buy_suggestion:.4f}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setPlaceholderText(f"{sell_suggestion:.4f}")
                else:
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setPlaceholderText(f"{buy_suggestion:.2f}")
                    self.ui.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setPlaceholderText(f"{sell_suggestion:.2f}")
                
                logger.debug(f"Set ping pong placeholders - Buy: {buy_suggestion:.6f}, Sell: {sell_suggestion:.6f}")
            
        except Exception as e:
            logger.error(f"Error updating ping pong placeholders: {e}")

    def go_back_to_info(self):
        """Navigate back to the info page."""
        self.ui.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(1)  # Back to Info page
