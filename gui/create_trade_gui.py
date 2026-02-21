from PySide6.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QRadioButton, QButtonGroup 
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QSize
from PySide6.QtGui import QColor, QPalette, QIcon
from typing import Optional, Dict
from decimal import Decimal, InvalidOperation 
import logging 
import json
from pathlib import Path
from functools import partial 
import time

from core.wallet import RadixWallet
from config.paths import PACKAGE_ROOT 
from .create_trade_ui import Ui_CreateTradeTabMain
from .trade_pairs_gui import TradePairsManager 
from .selectable_trade_pair_widget import SelectableTradePairWidget
from .available_pair_widget import AvailablePairWidget 
from database.database import Database 
from database.trade_manager import TradeManager 
from database.trade_pairs import TradePairManager
from database.balance_manager import BalanceManager
from database.statistics_manager import StatisticsManager
from gui.selectable_trade_pair_widget import SelectableTradePairWidget
from gui.components.toggle_switch import TokenSelector
from gui.components.token_selection_dialog import TokenSelectionDialog
from gui.components.simple_pair_result_widget import SimplePairResultWidget
from services.route_checker import RouteChecker

logger = logging.getLogger(__name__) 

class CreateTradeTabMain(QWidget):
    trade_created = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CreateTradeTabMain()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)

        # Replace radio buttons with toggle switches
        self._replace_radio_buttons_with_toggles()

        # Connect Create Trade button
        self.ui.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.clicked.connect(self.create_trade_from_ui)

        # Connect navigation buttons for stacked widget
        self.ui.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.clicked.connect(self._show_configure_pairs_page)
        self.ui.CreateTradeTabConfigureTradePairsBackButton.clicked.connect(self._show_create_trade_page)

        # Connect amount field to validate input and stop pulse on focus
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.textChanged.connect(self._validate_create_trade_button)
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.installEventFilter(self)

        # Connect ping pong price fields to validate input
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.textChanged.connect(self._validate_create_trade_button)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.textChanged.connect(self._validate_create_trade_button)

        # Connect strategy checkboxes with exclusivity logic
        self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.toggled.connect(self._on_strategy_selected)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.toggled.connect(self._on_strategy_selected)
        
        # Connect indicator checkboxes with exclusivity logic
        self.ui.CreateTradeTabMainCreateTradeSubTabRSICheckbox.toggled.connect(self._on_indicator_selected)
        self.ui.CreateTradeTabMainCreateTradeSubTabMACCheckbox.toggled.connect(self._on_indicator_selected)
        self.ui.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.toggled.connect(self._on_indicator_selected)
        self.ui.CreateTradeTabMainCreateTradeSubTabBBCheckbox.toggled.connect(self._on_indicator_selected)

        self.db_instance = Database()
        self.token_manager = self.db_instance.get_token_manager()
        self.trade_manager = self.db_instance.get_trade_manager() 
        self.trade_pair_manager = self.db_instance.get_trade_pair_manager()
        self.balance_manager = self.db_instance.get_balance_manager()
        self.statistics_manager = self.db_instance.get_statistics_manager()
        self.pool_manager = self.db_instance.get_pool_manager()
        self.route_checker: Optional[RouteChecker] = None  # Initialized when wallet is set
        self.xrd_rri: Optional[str] = None 
        self.xrd_icon_url: Optional[str] = None
        self.xrd_icon_local_path: Optional[str] = None 
        self.indicator_defaults = {}
        
        # Pool search state
        self.selected_token_a = None
        self.selected_token_b = None

        content_widget = self.ui.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.widget()
        if not content_widget.layout(): 
            self.main_tab_configured_pairs_layout = QVBoxLayout(content_widget)
            self.main_tab_configured_pairs_layout.setContentsMargins(0, 0, 0, 0)
            self.main_tab_configured_pairs_layout.setSpacing(5)
            self.main_tab_configured_pairs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        else:
            self.main_tab_configured_pairs_layout = content_widget.layout()

        if not self.ui.scrollAreaWidgetContents_8.layout():
            self.configure_tab_individual_tokens_layout = QVBoxLayout(self.ui.scrollAreaWidgetContents_8)
            self.configure_tab_individual_tokens_layout.setContentsMargins(0, 0, 0, 0)
            self.configure_tab_individual_tokens_layout.setSpacing(5)
            self.configure_tab_individual_tokens_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.ui.scrollAreaWidgetContents_8.setLayout(self.configure_tab_individual_tokens_layout) 
        else:
            self.configure_tab_individual_tokens_layout = self.ui.scrollAreaWidgetContents_8.layout()

        self.wallet: Optional[RadixWallet] = None
        self.selected_trade_pair_widget: Optional[SelectableTradePairWidget] = None
        self.selectable_pair_widgets: Dict[str, SelectableTradePairWidget] = {} 

        self.trade_pairs_manager = TradePairsManager(self.db_instance)
        selected_pairs_container_widget = self.ui.scrollAreaWidgetContents_9
        if not selected_pairs_container_widget.layout(): 
            selected_pairs_layout = QVBoxLayout(selected_pairs_container_widget)
            selected_pairs_layout.setContentsMargins(0, 0, 0, 0)
            selected_pairs_container_widget.setLayout(selected_pairs_layout) 
        else:
            selected_pairs_layout = selected_pairs_container_widget.layout()
        selected_pairs_layout.addWidget(self.trade_pairs_manager)

        self.trade_pairs_manager.pairs_changed.connect(self._populate_available_trade_pairs)
        self.trade_pairs_manager.pairs_changed.connect(self._populate_individual_tokens_for_configuration)
        self.trade_pairs_manager.pairs_changed.connect(self._on_configured_pairs_changed)

        # Setup pool search scroll area layout
        pool_search_container = self.ui.scrollAreaWidgetContents_11
        if not pool_search_container.layout():
            self.pool_search_layout = QVBoxLayout(pool_search_container)
            self.pool_search_layout.setContentsMargins(0, 0, 0, 0)
            self.pool_search_layout.setSpacing(5)
            self.pool_search_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            pool_search_container.setLayout(self.pool_search_layout)
        else:
            self.pool_search_layout = pool_search_container.layout()
        
        # Connect pool search buttons
        self.ui.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton.clicked.connect(self._on_token_a_button_clicked)
        self.ui.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton.clicked.connect(self._on_token_b_button_clicked)
        self.ui.CreateTradeTabConfigureTradePairsFindPoolsSearchButton.clicked.connect(self._on_search_pools_clicked)
        
        # Set default tokens for the buttons (hUSDC for Token A, XRD for Token B)
        self._initialize_default_pool_search_tokens()
                
        # Setup shimmer animation for Configure Trade Pairs button
        self._setup_shimmer_animation()
        
        self._load_indicator_defaults()     

    def _replace_radio_buttons_with_toggles(self):
        """Setup toggle switches - uses existing toggles in responsive mode or creates new ones in legacy mode."""
        from gui.create_trade_ui import USE_RESPONSIVE_LAYOUTS
        
        if USE_RESPONSIVE_LAYOUTS:
            # Responsive mode: Use toggle switches already created in UI file
            self.start_token_toggle = self.ui.CreateTradeTabMainCreateTradeSubTabStartTokenToggle
            self.accumulate_token_toggle = self.ui.CreateTradeTabMainCreateTradeSubTabAccumulateTokenToggle
            
            # Connect signals (ToggleSwitch uses 'toggled' signal)
            self.start_token_toggle.toggled.connect(self._update_amount_label)
            self.accumulate_token_toggle.toggled.connect(self._update_ping_pong_labels)
            
            logger.debug("Using responsive layout toggle switches")
        else:
            # Legacy mode: Hide radio buttons and create TokenSelector widgets with absolute positioning
            from PySide6.QtWidgets import QVBoxLayout
            
            # Hide original radio buttons
            self.ui.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonOne.setVisible(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonTwo.setVisible(False)
            
            # Create start token toggle
            self.start_token_toggle = TokenSelector("")
            self.start_token_toggle.setGeometry(255, 100, 112, 20)
            self.start_token_toggle.setParent(self.ui.CreateTradeSubTab)
            self.start_token_toggle.selectionChanged.connect(self._update_amount_label)
            
            # Create accumulate token toggle
            self.accumulate_token_toggle = TokenSelector("")
            self.accumulate_token_toggle.setGeometry(400, 100, 112, 20)
            self.accumulate_token_toggle.setParent(self.ui.CreateTradeSubTab)
            self.accumulate_token_toggle.selectionChanged.connect(self._update_ping_pong_labels)
            
            # Hide accumulation radio buttons if they exist
            if hasattr(self.ui, 'CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne'):
                self.ui.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne.setVisible(False)
                self.ui.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonTwo.setVisible(False)
            
            logger.debug("Using legacy layout with TokenSelector widgets")
    
    def _get_compound_profit_widget(self):
        """Get the appropriate compound profit widget based on layout mode."""
        from gui.create_trade_ui import USE_RESPONSIVE_LAYOUTS
        
        if USE_RESPONSIVE_LAYOUTS:
            return self.ui.CreateTradeTabMainCreateTradeSubTabCompoundProfitToggle
        else:
            return self.ui.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox
    
    def _show_configure_pairs_page(self):
        """Switch to the Configure Trade Pairs page."""
        self.ui.CreateTradeTabMenu.setCurrentIndex(0)  # ConfigTradePairsSubTab is index 0
        logger.debug("Switched to Configure Trade Pairs page")
    
    def _show_create_trade_page(self):
        """Switch back to the Create Trade page."""
        self.ui.CreateTradeTabMenu.setCurrentIndex(1)  # CreateTradeSubTab is index 1
        self._setup_shimmer_animation()  # Re-check shimmer when returning from config page
        logger.debug("Switched to Create Trade page")
    
    def eventFilter(self, obj, event):
        """Stop the amount field pulse when the user clicks into it."""
        if obj == self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField:
            from PySide6.QtCore import QEvent
            if event.type() == QEvent.FocusIn:
                self._stop_amount_pulse()
        return super().eventFilter(obj, event)

    def _start_amount_pulse(self):
        """Start a gentle blue border pulse on the amount field to draw attention."""
        if hasattr(self, '_amount_pulse_timer') and self._amount_pulse_timer.isActive():
            return  # Already pulsing

        self._amount_pulse_state = 0
        self._amount_pulse_timer = QTimer(self)
        self._amount_pulse_timer.timeout.connect(self._update_amount_pulse)
        self._amount_pulse_timer.start(800)
        logger.debug("Amount field pulse started")

    def _update_amount_pulse(self):
        """Toggle between two border styles to create a gentle pulse."""
        field = self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField
        if self._amount_pulse_state % 2 == 0:
            field.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #0078D4;
                    border-radius: 4px;
                    padding: 2px;
                }
            """)
        else:
            field.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #4DA6FF;
                    border-radius: 4px;
                    padding: 2px;
                }
            """)
        self._amount_pulse_state += 1

    def _stop_amount_pulse(self):
        """Stop the amount field pulse and restore default styling."""
        if hasattr(self, '_amount_pulse_timer') and self._amount_pulse_timer.isActive():
            self._amount_pulse_timer.stop()
            logger.debug("Amount field pulse stopped")
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setStyleSheet("")

    def _setup_shimmer_animation(self):
        """Setup shimmer animation for Configure Trade Pairs button when no pairs exist."""
        # Stop any existing shimmer timer first
        if hasattr(self, 'shimmer_timer') and self.shimmer_timer.isActive():
            self.shimmer_timer.stop()
            logger.debug("Stopped existing shimmer timer")

        # Check if trade pairs exist
        has_trade_pairs = self._check_trade_pairs_exist()
        
        if not has_trade_pairs:
            # Create shimmer effect using QTimer
            self.shimmer_state = 0
            self.shimmer_timer = QTimer(self)
            self.shimmer_timer.timeout.connect(self._update_shimmer)
            self.shimmer_timer.start(800)  # Update every 800ms
            
            logger.info("Shimmer animation started - no trade pairs configured")
        else:
            # Normal button style
            self.ui.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setStyleSheet("""
                QPushButton {
                    background-color: #106EBE;
                    color: #f0f0f0;
                    border: 1px solid #0078d7;
                    border-radius: 4px;
                    padding: 3px;
                }
                QPushButton:hover {
                    background-color: #0078d7;
                }
            """)
            logger.info("Normal button style - trade pairs exist")
    
    def _update_shimmer(self):
        """Update shimmer effect by toggling between two styles."""
        shimmer_styles = [
            """
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: 2px solid #0078D4;
                    border-radius: 4px;
                    padding: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106EBE;
                }
            """,
            """
                QPushButton {
                    background-color: #1E90FF;
                    color: white;
                    border: 2px solid #4DA6FF;
                    border-radius: 4px;
                    padding: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4169E1;
                }
            """
        ]
        
        self.ui.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setStyleSheet(
            shimmer_styles[self.shimmer_state % 2]
        )
        self.shimmer_state += 1
    
    def _check_trade_pairs_exist(self):
        """Check if current wallet has any selected trade pairs."""
        try:
            # Need to have a wallet selected first
            if not self.wallet:
                logger.info("No wallet selected yet, cannot check trade pairs")
                return False
            
            # Query database for selected pairs for this wallet
            cursor = self.db_instance._conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM selected_pairs WHERE wallet_id = ?",
                (self.wallet.wallet_id,)
            )
            count = cursor.fetchone()[0]
            logger.info(f"Selected trade pairs count for wallet {self.wallet.wallet_id}: {count}")
            logger.info(f"Has trade pairs: {count > 0}")
            return count > 0
        except Exception as e:
            logger.error(f"Error checking trade pairs: {e}", exc_info=True)
            return False     

    def set_wallet(self, wallet: Optional[RadixWallet]):
        logger.info(f"CreateTradeTabMain: Setting wallet to: {'None' if wallet is None else wallet.public_address}")
        self.wallet = wallet
        self.trade_pairs_manager.set_wallet_context(wallet) 
        
        # Initialize route checker with wallet address
        if wallet:
            self.route_checker = RouteChecker(self.token_manager, wallet.public_address)
        else:
            self.route_checker = None
        
        if self.selected_trade_pair_widget:
            self.selected_trade_pair_widget.deselect()
            self.selected_trade_pair_widget = None
        self._update_trade_direction_ui() 
        self._reset_create_trade_form() 

        if wallet:
            logger.debug(f"Wallet set in CreateTradeTabMain. Wallet ID: {wallet.wallet_id if wallet else 'N/A'}")
            if not self.xrd_icon_url: 
                xrd_details = self.token_manager.get_token_by_symbol("XRD")
                if xrd_details:
                    self.xrd_rri = xrd_details.get('address') 
                    self.xrd_icon_url = xrd_details.get('icon_url')
                    if self.xrd_rri: 
                        self.xrd_icon_local_path = xrd_details.get('icon_local_path')
                    else:
                        self.xrd_icon_local_path = None
                    logger.debug(f"XRD details fetched: RRI='{self.xrd_rri}', URL='{self.xrd_icon_url}', LocalPath='{self.xrd_icon_local_path}'")
                else:
                    logger.error("Could not fetch XRD details (RRI, icon URL, local path).")
            
            self._populate_available_trade_pairs() 
            self._populate_individual_tokens_for_configuration()
        else:
            logger.debug("Wallet cleared in CreateTradeTabMain.")
            self._clear_layout(self.main_tab_configured_pairs_layout)
            placeholder_label_main = QLabel("No wallet active. Please load one.")
            placeholder_label_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_tab_configured_pairs_layout.addWidget(placeholder_label_main)
            placeholder_label_config = QLabel("No wallet active. Please load one.")
            placeholder_label_config.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.configure_tab_individual_tokens_layout.addWidget(placeholder_label_config)

        self._setup_shimmer_animation()  # Re-check shimmer when wallet changes

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def _populate_available_trade_pairs(self):
        self._clear_layout(self.main_tab_configured_pairs_layout)
        self.selected_trade_pair_widget = None

        if not self.wallet:
            no_wallet_label = QLabel("Please select a wallet to see available trade pairs.")
            no_wallet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_tab_configured_pairs_layout.addWidget(no_wallet_label)
            return

        trade_pairs = self.trade_pair_manager.get_all_trade_pairs(self.wallet.wallet_id)

        if not trade_pairs:
            no_pairs_label = QLabel("No trade pairs configured.")
            no_pairs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_tab_configured_pairs_layout.addWidget(no_pairs_label)
            self._clear_trade_form_controls()
            return

        for pair_data in trade_pairs:
            widget = SelectableTradePairWidget(
                trade_pair_id=pair_data['trade_pair_id'],
                base_token_symbol=pair_data['base_token_symbol'],
                quote_token_symbol=pair_data['quote_token_symbol'],
                base_token_rri=pair_data['base_token_rri'],
                quote_token_rri=pair_data['quote_token_rri'],
                base_token_icon_url=pair_data.get('base_token_icon_url'),
                quote_token_icon_url=pair_data.get('quote_token_icon_url'),
                base_token_icon_local_path=pair_data.get('base_token_icon_local_path'),
                quote_token_icon_local_path=pair_data.get('quote_token_icon_local_path')
            )
            widget.clicked.connect(self.on_trade_pair_selected)
            self.main_tab_configured_pairs_layout.addWidget(widget)

        # Auto-select the first pair in the list
        if self.main_tab_configured_pairs_layout.count() > 0:
            first_widget = self.main_tab_configured_pairs_layout.itemAt(0).widget()
            if isinstance(first_widget, SelectableTradePairWidget):
                first_widget.select()

    def _populate_individual_tokens_for_configuration(self):
        """Populate middle scroll area with trade pairs that exist but aren't selected yet."""
        self._clear_layout(self.configure_tab_individual_tokens_layout)
        
        if not self.wallet:
            logger.warning("_populate_individual_tokens_for_configuration: No wallet active.")
            placeholder_label = QLabel("No wallet active. Cannot load pairs of interest.")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.configure_tab_individual_tokens_layout.addWidget(placeholder_label)
            return
        
        wallet_id = self.wallet.wallet_id
        if not wallet_id:
            logger.error("Wallet has no wallet_id. Cannot populate pairs of interest.")
            placeholder_label = QLabel("Error: Wallet ID not found.")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.configure_tab_individual_tokens_layout.addWidget(placeholder_label)
            return

        # Get all pairs from trade_pairs that aren't in selected_pairs for this wallet
        unselected_pairs = self.trade_pair_manager.get_unselected_trade_pairs(wallet_id)
        logger.debug(f"Found {len(unselected_pairs)} unselected trade pairs for wallet {wallet_id}.")

        if not unselected_pairs:
            placeholder_label = QLabel("<html><head/><body><p>No pairs of interest.<br>Search for pools to add pairs.</p></body></html>")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.configure_tab_individual_tokens_layout.addWidget(placeholder_label)
            return

        pairs_added = 0
        for pair_data in unselected_pairs:
            base_token_rri = pair_data.get('base_token_rri')
            quote_token_rri = pair_data.get('quote_token_rri')
            base_token_symbol = pair_data.get('base_token_symbol', 'Unknown')
            quote_token_symbol = pair_data.get('quote_token_symbol', 'Unknown')
            base_token_icon_url = pair_data.get('base_token_icon_url')
            base_token_icon_local_path = pair_data.get('base_token_icon_local_path')
            quote_token_icon_url = pair_data.get('quote_token_icon_url')
            quote_token_icon_local_path = pair_data.get('quote_token_icon_local_path')

            if not base_token_rri or not quote_token_rri:
                logger.warning(f"Skipping pair due to missing RRI: {pair_data}")
                continue

            widget = AvailablePairWidget(
                base_token_symbol=base_token_symbol,
                base_token_rri=base_token_rri,
                base_token_icon_url=base_token_icon_url,
                base_token_icon_local_path=base_token_icon_local_path,
                quote_token_symbol=quote_token_symbol, 
                quote_token_rri=quote_token_rri,
                quote_token_icon_url=quote_token_icon_url,
                quote_token_icon_local_path=quote_token_icon_local_path,
                is_suggestion=False  # These are actual pairs, not suggestions
            )
            widget.add_pair_requested.connect(
                lambda base_rri=base_token_rri, quote_rri=quote_token_rri, sym=base_token_symbol, w=widget: 
                    self._on_individual_token_for_configuration_selected(base_rri, quote_rri, sym, w)
            )
            widget.delete_pair_requested.connect(
                lambda base_rri=base_token_rri, quote_rri=quote_token_rri, w=widget:
                    self._on_trade_pair_delete_requested(base_rri, quote_rri, w)
            )
            self.configure_tab_individual_tokens_layout.addWidget(widget)
            pairs_added += 1
        
        logger.debug(f"Finished populating {pairs_added} pairs of interest for configuration.")

    def _on_individual_token_for_configuration_selected(self, base_token_rri: str, quote_token_rri: str, base_token_symbol: str, widget_instance: QWidget):
        logger.info(f"Pair {base_token_symbol} ({base_token_rri}/{quote_token_rri}) selected for activation.")
        if self.trade_pairs_manager:
            success = self.trade_pairs_manager.db_trade_pair_manager.select_trade_pair(base_token_rri, quote_token_rri, self.trade_pairs_manager.active_wallet_id)
            if success:
                logger.debug(f"Successfully selected pair {base_token_symbol} ({base_token_rri}/{quote_token_rri}) in database. Refreshing UI.")
                widget_instance.deleteLater() 
                self.trade_pairs_manager.load_trade_pairs() 
            else:
                logger.error(f"Database error: Failed to select trade pair {base_token_symbol} ({base_token_rri}/{quote_token_rri}). The pair will remain in the available list.")
        else:
            logger.error("TradePairsManager not available to select pair.")

    def _on_trade_pair_delete_requested(self, base_token_rri: str, quote_token_rri: str, widget_instance: QWidget):
        """Handle deletion of a trade pair from the database."""
        logger.info(f"Delete requested for pair {base_token_rri}/{quote_token_rri}")
        
        if not self.trade_pair_manager:
            logger.error("TradePairManager not available for deletion.")
            return
        
        # Call the delete method on the database manager
        success = self.trade_pair_manager.delete_trade_pair(base_token_rri, quote_token_rri)
        
        if success:
            logger.info(f"Successfully deleted trade pair {base_token_rri}/{quote_token_rri} from database.")
            # Remove widget from UI
            widget_instance.deleteLater()
            # Refresh the selected pairs list (in case it was selected)
            if self.trade_pairs_manager:
                self.trade_pairs_manager.load_trade_pairs()
        else:
            logger.error(f"Failed to delete trade pair {base_token_rri}/{quote_token_rri}")

    def on_trade_pair_selected(self, clicked_widget: 'SelectableTradePairWidget'):
        logger.debug(f"on_trade_pair_selected called with widget: {clicked_widget.base_token_symbol}/{clicked_widget.quote_token_symbol}")

        if self.selected_trade_pair_widget == clicked_widget:
            logger.debug("Deselecting currently selected widget")
            clicked_widget.deselect()
            self.selected_trade_pair_widget = None
        else:
            if self.selected_trade_pair_widget:
                logger.debug(f"Deselecting previous widget: {self.selected_trade_pair_widget.base_token_symbol}/{self.selected_trade_pair_widget.quote_token_symbol}")
                self.selected_trade_pair_widget.deselect()
            
            logger.debug(f"Selecting new widget: {clicked_widget.base_token_symbol}/{clicked_widget.quote_token_symbol}")
            # Ensure autoFillBackground is enabled for proper highlighting
            clicked_widget.setAutoFillBackground(True)
            clicked_widget.select()
            self.selected_trade_pair_widget = clicked_widget
        
        self._update_trade_direction_ui()

    def _update_trade_direction_ui(self):
        """Update the trade direction UI with token information."""
        logger.debug(f"_update_trade_direction_ui: selected_trade_pair_widget: {self.selected_trade_pair_widget}, wallet: {self.wallet}")

        if self.selected_trade_pair_widget and self.wallet:
            base_sym = self.selected_trade_pair_widget.base_token_symbol
            quote_sym = self.selected_trade_pair_widget.quote_token_symbol
            base_rri = self.selected_trade_pair_widget.base_token_rri
            quote_rri = self.selected_trade_pair_widget.quote_token_rri

            # Update toggle switches with token symbols
            self.start_token_toggle.setTokens(base_sym, quote_sym)
            self.accumulate_token_toggle.setTokens(base_sym, quote_sym)
            
            # Default to accumulating base token
            self.accumulate_token_toggle.setSelection(False)

            # Get all balances and extract available amounts
            logger.debug("Updating balance manager internal state...")
            
            # Check if balance manager has a valid wallet reference
            if self.balance_manager.wallet is None:
                logger.debug("Balance manager wallet is None, setting it to current wallet")
                self.balance_manager.wallet = self.wallet
            
            # Load active trades to calculate locked amounts
            self.balance_manager._load_active_trades()
            self.balance_manager._update_internal_state()
            
            all_balances = self.balance_manager.get_all_balances()
            logger.debug(f"All balances from balance manager: {all_balances}")
            
            # Calculate available balance
            base_balance_info = all_balances.get(base_rri, {})
            quote_balance_info = all_balances.get(quote_rri, {})
            
            base_balance = Decimal(str(base_balance_info.get('available', 0)))
            quote_balance = Decimal(str(quote_balance_info.get('available', 0)))
            
            has_base = base_balance > 0
            has_quote = quote_balance > 0

            logger.debug(f"has_base: {has_base}, has_quote: {has_quote}")

            # Set default selection based on available balance
            if has_quote and not has_base:
                self.start_token_toggle.setSelection(True)  # Select quote token
            elif has_base and not has_quote:
                self.start_token_toggle.setSelection(False)  # Select base token
            elif has_base and has_quote:
                self.start_token_toggle.setSelection(True)  # Default to quote if both available
            
            # Enable/disable amount field based on balance
            self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setEnabled(has_base or has_quote)
            
            # Pulse the amount field if it is enabled and empty
            if (has_base or has_quote) and not self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.text().strip():
                self._start_amount_pulse()
            else:
                self._stop_amount_pulse()
            
            # Update displays
            self._update_price_display()
            self._update_ping_pong_labels()
            self._update_amount_label()
            self._validate_create_trade_button()

        else:
            logger.debug("No trade pair selected or no wallet - resetting UI")
            # Reset toggle switches
            self.start_token_toggle.setTokens("Token 1", "Token 2")
            self.accumulate_token_toggle.setTokens("Token 1", "Token 2")
            
            self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setEnabled(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText("<html><head/><body><p><span style=\" font-weight:700;\">Amount of Token to trade:</span></p></body></html>")
            self._stop_amount_pulse()
            self._validate_create_trade_button()

    def _update_price_display(self):
        """Update the current price display for the selected trade pair."""
        if not self.selected_trade_pair_widget:
            self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setText("No trade pair selected")
            self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setText("")
            return
            
        base_sym = self.selected_trade_pair_widget.base_token_symbol
        quote_sym = self.selected_trade_pair_widget.quote_token_symbol
        base_rri = self.selected_trade_pair_widget.base_token_rri
        quote_rri = self.selected_trade_pair_widget.quote_token_rri
        
        # Get current prices from tokens table
        try:
            token_manager = self.db_instance.get_token_manager()
            
            # Get base token price
            base_token = token_manager.get_token_by_address(base_rri)
            if base_token:
                base_price_xrd = Decimal(str(base_token.get('token_price_xrd', 0)))
                base_price_usd = Decimal(str(base_token.get('token_price_usd', 0)))
            else:
                base_price_xrd = Decimal('0')
                base_price_usd = Decimal('0')
                
            # Get quote token price
            quote_token = token_manager.get_token_by_address(quote_rri)
            if quote_token:
                quote_price_xrd = Decimal(str(quote_token.get('token_price_xrd', 0)))
                quote_price_usd = Decimal(str(quote_token.get('token_price_usd', 0)))
            else:
                quote_price_xrd = Decimal('0')
                quote_price_usd = Decimal('0')
            
            # Calculate relative prices (quote per base)
            if base_price_usd > 0:
                # Price in terms of quote/base
                relative_price = quote_price_usd / base_price_usd
            else:
                relative_price = Decimal('0')
                
            if relative_price > 0:
                reverse_price = Decimal('1') / relative_price
                
                # Update price labels with clear descriptions
                self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setText(
                    f"{relative_price:.6f} {base_sym} per {quote_sym}"
                )
                self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setText(
                    f"{reverse_price:.6f} {quote_sym} per {base_sym}"
                )
            else:
                self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setText(
                    f"Price data unavailable for {base_sym}/{quote_sym}"
                )
                self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setText("")
                
        except Exception as e:
            logger.error(f"Error updating price display: {e}", exc_info=True)
            self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setText("Error loading prices")
            self.ui.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setText("")

    def _update_ping_pong_labels(self):
        """Determine pricing token for all strategies and update ping pong labels.
        
        This method:
        1. Determines which token should be used for pricing (more expensive = denominator = decimal)
        2. Stores it in self.ping_pong_pricing_token and self.ping_pong_pricing_token_symbol
        3. These values are then used by ALL strategies (Ping Pong, Manual, AI) when creating trades
        4. Updates the Ping Pong UI labels to match
        """
        if not self.selected_trade_pair_widget:
            return
            
        base_sym = self.selected_trade_pair_widget.base_token_symbol
        quote_sym = self.selected_trade_pair_widget.quote_token_symbol
        base_rri = self.selected_trade_pair_widget.base_token_rri
        quote_rri = self.selected_trade_pair_widget.quote_token_rri
        
        # Determine which token provides intuitive "buy low, sell high" pricing
        # This is the token with HIGHER USD value (gives decimal prices)
        try:
            token_manager = self.db_instance.get_token_manager()
            
            base_token = token_manager.get_token_by_address(base_rri)
            quote_token = token_manager.get_token_by_address(quote_rri)
            
            base_price_usd = Decimal(str(base_token.get('token_price_usd', 0))) if base_token else Decimal('0')
            quote_price_usd = Decimal(str(quote_token.get('token_price_usd', 0))) if quote_token else Decimal('0')
            
            # Use the token with HIGHER USD value for intuitive pricing
            # When price is shown in the higher-value token, numbers are decimals (buy low, sell high works)
            if base_price_usd > 0 and quote_price_usd > 0:
                if base_price_usd > quote_price_usd:
                    # Base token is more expensive - use it for pricing
                    pricing_token_symbol = base_sym
                    self.ping_pong_pricing_token = 'base'
                    logger.debug(f"Pricing token set to 'base' ({base_sym}) - base_USD={base_price_usd} > quote_USD={quote_price_usd}")
                else:
                    # Quote token is more expensive - use it for pricing
                    pricing_token_symbol = quote_sym
                    self.ping_pong_pricing_token = 'quote'
                    logger.debug(f"Pricing token set to 'quote' ({quote_sym}) - quote_USD={quote_price_usd} >= base_USD={base_price_usd}")
            else:
                # Default to quote token if prices unavailable (often stable coins)
                pricing_token_symbol = quote_sym
                self.ping_pong_pricing_token = 'quote'
                logger.warning(f"Defaulting pricing token to 'quote' ({quote_sym}) - prices unavailable")
                
            # Store for later reference when creating the trade (used by ALL strategies)
            self.ping_pong_pricing_token_symbol = pricing_token_symbol
            logger.debug(f"Stored pricing_token='{self.ping_pong_pricing_token}', pricing_token_symbol='{pricing_token_symbol}'")
                
        except Exception as e:
            logger.error(f"Error determining pricing token: {e}")
            pricing_token_symbol = base_sym
            self.ping_pong_pricing_token = 'base'
            self.ping_pong_pricing_token_symbol = base_sym
        
        # Update Ping Pong UI labels to show the intuitive pricing token
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol.setText(pricing_token_symbol)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol.setText(pricing_token_symbol)
        
        # Update placeholders with example prices
        self._update_ping_pong_placeholders()
    
    def _update_ping_pong_placeholders(self):
        """Update ping pong price field placeholders with intuitive examples."""
        if not self.selected_trade_pair_widget:
            return
            
        try:
            # Get current relative price
            base_rri = self.selected_trade_pair_widget.base_token_rri
            quote_rri = self.selected_trade_pair_widget.quote_token_rri
            
            token_manager = self.db_instance.get_token_manager()
            base_token = token_manager.get_token_by_address(base_rri)
            quote_token = token_manager.get_token_by_address(quote_rri)
            
            base_price_usd = Decimal(str(base_token.get('token_price_usd', 0))) if base_token else Decimal('0')
            quote_price_usd = Decimal(str(quote_token.get('token_price_usd', 0))) if quote_token else Decimal('0')
            
            if base_price_usd > 0 and quote_price_usd > 0:
                if self.ping_pong_pricing_token == 'base':
                    # Price in base tokens per quote token
                    current_price = quote_price_usd / base_price_usd
                else:
                    # Price in quote tokens per base token
                    current_price = base_price_usd / quote_price_usd
                    
                # Suggest buy 5% below current, sell 5% above current
                buy_suggestion = current_price * Decimal('0.95')
                sell_suggestion = current_price * Decimal('1.05')
                
                # Format based on magnitude
                if current_price < Decimal('0.01'):
                    self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setPlaceholderText(f"{buy_suggestion:.6f}")
                    self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setPlaceholderText(f"{sell_suggestion:.6f}")
                elif current_price < Decimal('1'):
                    self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setPlaceholderText(f"{buy_suggestion:.4f}")
                    self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setPlaceholderText(f"{sell_suggestion:.4f}")
                else:
                    self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setPlaceholderText(f"{buy_suggestion:.2f}")
                    self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setPlaceholderText(f"{sell_suggestion:.2f}")
            else:
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setPlaceholderText("0.95")
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setPlaceholderText("1.05")
                
        except Exception as e:
            logger.error(f"Error updating ping pong placeholders: {e}")

    def _update_amount_label(self):
        """Update the amount label based on selected start token."""
        if self.selected_trade_pair_widget and self.wallet:
            base_sym = self.selected_trade_pair_widget.base_token_symbol
            quote_sym = self.selected_trade_pair_widget.quote_token_symbol
            base_rri = self.selected_trade_pair_widget.base_token_rri
            quote_rri = self.selected_trade_pair_widget.quote_token_rri

            available_balances = self.balance_manager.get_all_balances()
            base_balance = available_balances.get(base_rri, {}).get('available', 0)
            quote_balance = available_balances.get(quote_rri, {}).get('available', 0)

            # Check which token is selected in the toggle
            if self.start_token_toggle.isSecondTokenSelected():
                # Quote token selected
                formatted_text = f"<html><head/><body><p><span style=\" font-weight:700;\">Amount of {quote_sym} to trade:</span></p></body></html>"

                self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText(formatted_text)
                self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setPlaceholderText(f"{quote_balance} (max)")
            else:
                # Base token selected
                formatted_text = f"<html><head/><body><p><span style=\" font-weight:700;\">Amount of {base_sym} to trade:</span></p></body></html>"

                self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText(formatted_text)
                self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setPlaceholderText(f"{base_balance} (max)")
        else:
            self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText("<html><head/><body><p><span style=\" font-weight:700;\">Amount of Token to trade:</span></p></body></html>")
            self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setPlaceholderText("Enter amount")

    def _load_indicator_defaults(self):
        config_dir = PACKAGE_ROOT / 'config'
        user_defaults_path = config_dir / 'indicator_defaults.json'
        app_defaults_path = config_dir / 'start_default_indicators.json'

        try:
            if user_defaults_path.exists():
                with open(user_defaults_path, 'r') as f:
                    self.indicator_defaults = json.load(f)
            else:
                with open(app_defaults_path, 'r') as f:
                    self.indicator_defaults = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load indicator defaults: {e}")
            self.indicator_defaults = {}

    def _get_indicator_settings_json(self, strategy_name: str) -> str:
        """
        Constructs a clean JSON string for indicator settings by intelligently
        selecting the correct parameters from the defaults file based on the chosen strategy.
        """
        settings = {}

        if strategy_name == "AI_Strategy":
            # AI Strategy uses ML-optimized parameters stored in ai_strategy_parameters table
            # Only save essential fields here (pricing token info for accumulation logic)
            # Stop loss/trailing stop will be added later in create_trade_from_ui
            settings['pricing_token'] = getattr(self, 'ping_pong_pricing_token', 'base')
            settings['pricing_token_symbol'] = getattr(self, 'ping_pong_pricing_token_symbol', 
                                                       self.selected_trade_pair_widget.base_token_symbol if self.selected_trade_pair_widget else '')
        
        elif strategy_name == "Manual":
            # For a manual strategy, build the settings dict from individually checked indicators.
            if self.ui.CreateTradeTabMainCreateTradeSubTabRSICheckbox.isChecked():
                settings['RSI'] = self.indicator_defaults.get('RSI', {})
            if self.ui.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.isChecked():
                settings['MACD'] = self.indicator_defaults.get('MACD', {})
            if self.ui.CreateTradeTabMainCreateTradeSubTabBBCheckbox.isChecked():
                settings['BB'] = self.indicator_defaults.get('BB', {})
            if self.ui.CreateTradeTabMainCreateTradeSubTabMACCheckbox.isChecked():
                settings['MA_CROSS'] = self.indicator_defaults.get('MA_CROSS', {})
            # Add pricing token information for accumulation logic
            settings['pricing_token'] = getattr(self, 'ping_pong_pricing_token', 'base')
            settings['pricing_token_symbol'] = getattr(self, 'ping_pong_pricing_token_symbol', 
                                                       self.selected_trade_pair_widget.base_token_symbol if self.selected_trade_pair_widget else '')
        
        # For PingPong, this method returns an empty dict, which is handled/overwritten
        # in the calling function.
        
        return json.dumps(settings, indent=4)

    def create_trade_from_ui(self):
        if not self.wallet:
            QMessageBox.warning(self, "Error", "Select a wallet first")
            return

        if not self.selected_trade_pair_widget:
            QMessageBox.warning(self, "Error", "Select a trade pair first")
            return

        trade_pair_id = self.selected_trade_pair_widget.trade_pair_id
        pool_address = self.trade_pair_manager.get_pool_address_for_pair(trade_pair_id)

        # Pool address is optional - Astrolescent pairs use token USD prices for calculations
        if not pool_address:
            logger.info(f"No Ociswap pool for trade_pair_id {trade_pair_id} - will use token USD prices")

        start_token_address = None
        start_token_symbol = None
        if self.start_token_toggle.isSecondTokenSelected():
            start_token_address = self.selected_trade_pair_widget.quote_token_rri
            start_token_symbol = self.selected_trade_pair_widget.quote_token_symbol
        else:
            start_token_address = self.selected_trade_pair_widget.base_token_rri
            start_token_symbol = self.selected_trade_pair_widget.base_token_symbol

        amount_str = self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.text()
        try:
            start_amount = Decimal(amount_str)
            if start_amount <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Error", "Enter a valid positive amount")
            return

        # Balance Validation
        available_balances = self.balance_manager.get_all_balances()
        available_balance = available_balances.get(start_token_address, {}).get('available', 0)

        if start_amount > available_balance:
            QMessageBox.warning(self, "Error", 
                                f"Insufficient {start_token_symbol}: need {start_amount}, have {available_balance:.8f}")
            return

        is_compounding = self._get_compound_profit_widget().isChecked()
        
        # Get stop loss and trailing stop values (default 0 = disabled)
        stop_loss_pct = 0.0
        trailing_stop_pct = 0.0
        
        try:
            stop_loss_text = self.ui.CreateTradeTabMainCreateTradeSubTabStopLossInput.text().strip()
            if stop_loss_text:
                stop_loss_pct = float(stop_loss_text)
                if stop_loss_pct < 0:
                    QMessageBox.warning(self, "Error", "Stop Loss must be 0 or positive")
                    return
        except ValueError:
            QMessageBox.warning(self, "Error", "Stop Loss must be a valid number")
            return
        
        try:
            trailing_stop_text = self.ui.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.text().strip()
            if trailing_stop_text:
                trailing_stop_pct = float(trailing_stop_text)
                if trailing_stop_pct < 0:
                    QMessageBox.warning(self, "Error", "Trailing Stop must be 0 or positive")
                    return
        except ValueError:
            QMessageBox.warning(self, "Error", "Trailing Stop must be a valid number")
            return
        
        strategy_name = "Manual" 
        if self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.isChecked():
            strategy_name = "AI_Strategy"
        elif self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.isChecked():
            strategy_name = "Ping Pong"

        indicator_settings_json = self._get_indicator_settings_json(strategy_name)

        if strategy_name == "Ping Pong":
            ping_pong_settings = {
                'buy_price': str(self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.text()),
                'sell_price': str(self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.text()),
                'pricing_token': getattr(self, 'ping_pong_pricing_token', 'base'),
                'pricing_token_symbol': getattr(self, 'ping_pong_pricing_token_symbol', self.selected_trade_pair_widget.base_token_symbol)
            }
            
            # Validate Ping Pong prices
            try:
                buy_price_float = float(ping_pong_settings['buy_price'])
                sell_price_float = float(ping_pong_settings['sell_price'])
                
                if buy_price_float <= 0 or sell_price_float <= 0:
                    self.ui.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setText(
                        "Error: Prices must be greater than zero")
                    return
                
                # Always use intuitive "buy low, sell high" validation
                # The pricing token selection already handles making this intuitive
                if buy_price_float >= sell_price_float:
                    self.ui.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setText(
                        f"Error: Buy price must be lower than sell price (buy low, sell high)")
                    return
                    
            except ValueError:
                self.ui.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setText(
                    "Error: Prices must be valid numbers")
                return
            
            indicator_settings_json = json.dumps(ping_pong_settings, indent=4)
        
        # Add stop loss and trailing stop to all strategies
        settings_dict = json.loads(indicator_settings_json) if indicator_settings_json else {}
        settings_dict['stop_loss_percentage'] = stop_loss_pct
        settings_dict['trailing_stop_percentage'] = trailing_stop_pct
        indicator_settings_json = json.dumps(settings_dict, indent=4)
        
        # Get accumulation token address
        if not self.accumulate_token_toggle.isSecondTokenSelected():
            accumulation_token_address = self.selected_trade_pair_widget.base_token_rri
            accumulation_token_symbol = self.selected_trade_pair_widget.base_token_symbol
        else:
            accumulation_token_address = self.selected_trade_pair_widget.quote_token_rri
            accumulation_token_symbol = self.selected_trade_pair_widget.quote_token_symbol
        
        trade_params = {
            'trade_pair_id': trade_pair_id,
            'wallet_address': self.wallet.public_address,
            'start_token_address': start_token_address,
            'start_token_symbol': start_token_symbol,
            'start_amount': str(start_amount),
            'is_active': 1,
            'is_compounding': 1 if is_compounding else 0,
            'strategy_name': strategy_name,
            'indicator_settings_json': indicator_settings_json,
            'ociswap_pool_address': pool_address,
            'created_at': int(time.time()),
            'updated_at': int(time.time()),
            'current_signal': 'hold',
            'last_signal_updated_at': int(time.time()),
            'trade_amount': str(start_amount),
            'trade_token_address': start_token_address,
            'trade_token_symbol': start_token_symbol,
            'accumulation_token_address': accumulation_token_address,
            'accumulation_token_symbol': accumulation_token_symbol
        }

        logger.debug(f"Attempting to create trade with params: {trade_params}")

        new_trade_id = self.trade_manager.add_trade(trade_params)

        if new_trade_id:
            # Statistics are automatically updated by trade_manager.add_trade()
            QMessageBox.information(self, "Success", 
                                    f"Trade {new_trade_id} created: {start_amount} {start_token_symbol}")
            self.trade_created.emit()
            self._reset_create_trade_form()
        else:
            QMessageBox.critical(self, "Error", "Failed to create trade")

    def _reset_create_trade_form(self):
        """Resets the trade creation form to its default state."""
        logger.debug("Resetting Create Trade form.")
        if self.selected_trade_pair_widget:
            self.selected_trade_pair_widget.deselect()
            self.selected_trade_pair_widget = None

        self.start_token_toggle.setTokens("Token 1", "Token 2")
        self.start_token_toggle.setSelection(False)
        self.accumulate_token_toggle.setTokens("Token 1", "Token 2")
        self.accumulate_token_toggle.setSelection(False)

        # Reset amount field
        self._stop_amount_pulse()
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.clear()
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setEnabled(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setPlaceholderText("Enter amount")
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText("<html><head/><body><p><span style=\" font-weight:700;\">Amount of Token to trade:</span></p></body></html>")
        
        # Reset strategy checkboxes
        self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setChecked(False)
        
        # Reset indicator checkboxes
        self.ui.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setChecked(False)
        
        # Reset ping pong fields
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.clear()
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setEnabled(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.clear()
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setEnabled(False)
        
        # Reset compound profit widget
        self._get_compound_profit_widget().setChecked(False)
        
        # Reset create trade button
        self.ui.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setEnabled(False)

        # Re-populate pairs, which will auto-select the first one if available
        self._populate_available_trade_pairs()

    def _clear_trade_form_controls(self):
        """Clear and disable form inputs without re-triggering trade pair population."""
        if self.selected_trade_pair_widget:
            self.selected_trade_pair_widget.deselect()
            self.selected_trade_pair_widget = None

        self.start_token_toggle.setTokens("Token 1", "Token 2")
        self.start_token_toggle.setSelection(False)
        self.accumulate_token_toggle.setTokens("Token 1", "Token 2")
        self.accumulate_token_toggle.setSelection(False)

        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.clear()
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setEnabled(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setPlaceholderText("Enter amount")
        self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText("<html><head/><body><p><span style=\" font-weight:700;\">Amount of Token to trade:</span></p></body></html>")

        self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setChecked(False)

        self.ui.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setChecked(False)

        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.clear()
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setEnabled(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.clear()
        self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setEnabled(False)

        self._get_compound_profit_widget().setChecked(False)
        self.ui.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setEnabled(False)

    def _on_strategy_selected(self):
        """Handle strategy selection with mutual exclusivity"""
        sender = self.sender()
        
        if sender.isChecked():
            # Uncheck all other strategies
            if sender == self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox:
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setChecked(False)
            elif sender == self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox:
                self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setChecked(False)
            
            # Uncheck all indicators when a strategy is selected
            self.ui.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setChecked(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setChecked(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setChecked(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setChecked(False)
            
            # Show/hide ping pong specific fields
            if sender == self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox:
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setEnabled(True)
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setEnabled(True)
            else:
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setEnabled(False)
                self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setEnabled(False)
        else:
            # If unchecking a strategy, hide ping pong fields
            self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setEnabled(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setEnabled(False)
        
        self._validate_create_trade_button()

    def _on_indicator_selected(self):
        """Handle indicator selection with strategy exclusivity"""
        sender = self.sender()
        
        if sender.isChecked():
            # Uncheck all strategies when an indicator is selected
            self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setChecked(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setChecked(False)
            
            # Disable ping pong fields when indicators are selected
            self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setEnabled(False)
            self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setEnabled(False)
        
        self._validate_create_trade_button()

    def _validate_create_trade_button(self):
        """Enable the create trade button if all conditions are met"""
        # Check if a trade pair is selected
        has_trade_pair = self.selected_trade_pair_widget is not None
        
        # Check if a token direction is selected
        has_token_selection = self.start_token_toggle.isFirstTokenSelected() or self.start_token_toggle.isSecondTokenSelected()
        
        # Check if amount is entered
        has_amount = bool(self.ui.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.text().strip())
        
        # Check if a strategy or at least one indicator is selected
        has_strategy = (self.ui.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.isChecked() or 
                       self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.isChecked())
        
        has_indicator = (self.ui.CreateTradeTabMainCreateTradeSubTabRSICheckbox.isChecked() or
                        self.ui.CreateTradeTabMainCreateTradeSubTabMACCheckbox.isChecked() or
                        self.ui.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.isChecked() or
                        self.ui.CreateTradeTabMainCreateTradeSubTabBBCheckbox.isChecked())
        
        has_strategy_or_indicator = has_strategy or has_indicator
        
        # For ping pong strategy, also check if buy/sell prices are entered
        ping_pong_valid = True
        if self.ui.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.isChecked():
            buy_price = self.ui.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.text().strip()
            sell_price = self.ui.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.text().strip()
            ping_pong_valid = bool(buy_price) and bool(sell_price)
        
        # Enable button only if all conditions are met
        should_enable = (has_trade_pair and has_token_selection and has_amount and 
                        has_strategy_or_indicator and ping_pong_valid)
        
        self.ui.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setEnabled(should_enable)

    def _on_configured_pairs_changed(self):
        logger.debug("CreateTradeTabMain: _on_configured_pairs_changed triggered.")

        previously_selected_base_rri = None
        if self.selected_trade_pair_widget:
            previously_selected_base_rri = self.selected_trade_pair_widget.base_token_rri
            logger.debug(f"Previously selected pair RRI: {previously_selected_base_rri}")
            
        self.selected_trade_pair_widget = None

        self._populate_available_trade_pairs()

        if previously_selected_base_rri and previously_selected_base_rri in self.selectable_pair_widgets:
            new_widget_instance = self.selectable_pair_widgets[previously_selected_base_rri]
            logger.info(f"Re-selecting previously selected pair: {previously_selected_base_rri} with new widget instance.")
            self.on_trade_pair_selected(new_widget_instance)
        else:
            if previously_selected_base_rri:
                logger.info(f"Previously selected pair ({previously_selected_base_rri}) is no longer available after refresh.")
            else:
                logger.info("No pair was previously selected, or list was empty.")
            self._update_trade_direction_ui()

    def _initialize_default_pool_search_tokens(self):
        """Initialize the pool search buttons with default tokens (hUSDC and XRD)."""
        try:
            # Get hUSDC for Token A (base token)
            husdc_token = self.token_manager.get_token_by_symbol('hUSDC')
            if husdc_token:
                self.selected_token_a = husdc_token
                self._set_token_button(
                    self.ui.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton,
                    husdc_token
                )
                logger.debug(f"Default Token A set to hUSDC")
            else:
                logger.warning("hUSDC not found for default Token A")
            
            # Get XRD for Token B (quote token)
            xrd_token = self.token_manager.get_token_by_symbol('XRD')
            if xrd_token:
                self.selected_token_b = xrd_token
                self._set_token_button(
                    self.ui.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton,
                    xrd_token
                )
                logger.debug(f"Default Token B set to XRD")
            else:
                logger.warning("XRD not found for default Token B")
                
        except Exception as e:
            logger.error(f"Error setting default pool search tokens: {e}", exc_info=True)
    
    def _set_token_button(self, button, token: Dict):
        """Set a token button's text and icon."""
        symbol = token.get('symbol', 'Unknown')
        button.setText(f"  {symbol}")  # Add spacing for icon
        
        # Set icon
        icon_path = token.get('icon_local_path')
        if icon_path:
            full_path = Path(icon_path)
            if not full_path.is_absolute():
                full_path = PACKAGE_ROOT / icon_path
            if full_path.exists():
                button.setIcon(QIcon(str(full_path)))
                button.setIconSize(QSize(20, 20))
            else:
                # Use default icon
                default_icon = PACKAGE_ROOT / 'images' / 'default_token_icon.png'
                if default_icon.exists():
                    button.setIcon(QIcon(str(default_icon)))
                    button.setIconSize(QSize(20, 20))
        else:
            # Use default icon
            default_icon = PACKAGE_ROOT / 'images' / 'default_token_icon.png'
            if default_icon.exists():
                button.setIcon(QIcon(str(default_icon)))
                button.setIconSize(QSize(20, 20))

    def _on_token_a_button_clicked(self):
        """Handle Token A button click - show token selection dialog (excludes XRD)."""
        logger.debug("Token A button clicked")
        
        # Get all tokens
        tokens = self.token_manager.get_all_tokens_for_selection()
        
        if not tokens:
            QMessageBox.warning(self, "No Tokens", "No tokens found in database.")
            return
        
        # Show token selection dialog - exclude XRD since it's always Token B (quote)
        dialog = TokenSelectionDialog(tokens, self, exclude_symbols={'XRD'})
        if dialog.exec():
            selected_token = dialog.get_selected_token()
            if selected_token:
                self.selected_token_a = selected_token
                self._set_token_button(
                    self.ui.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton,
                    selected_token
                )
                logger.info(f"Token A selected: {selected_token.get('symbol', 'Unknown')}")
                
                # Clear pool search results when token changes
                self._clear_pool_search_results()

    def _on_token_b_button_clicked(self):
        """Handle Token B button click - show token selection dialog."""
        logger.debug("Token B button clicked")
        
        # Get all tokens
        tokens = self.token_manager.get_all_tokens_for_selection()
        
        if not tokens:
            QMessageBox.warning(self, "No Tokens", "No tokens found in database.")
            return
        
        # Show token selection dialog - XRD first since it's typically the quote token
        dialog = TokenSelectionDialog(tokens, self, xrd_first=True)
        if dialog.exec():
            selected_token = dialog.get_selected_token()
            if selected_token:
                self.selected_token_b = selected_token
                self._set_token_button(
                    self.ui.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton,
                    selected_token
                )
                logger.info(f"Token B selected: {selected_token.get('symbol', 'Unknown')}")
                
                # Clear pool search results when token changes
                self._clear_pool_search_results()

    def _on_search_pools_clicked(self):
        """Handle Search Pools button click - search for pools with selected tokens."""
        logger.debug("Search Pools button clicked")
        
        # Validate both tokens selected
        if not self.selected_token_a or not self.selected_token_b:
            QMessageBox.warning(self, "Incomplete Selection", 
                              "Please select both Token A and Token B before searching.")
            return
        
        # Check if same token selected twice
        if self.selected_token_a['address'] == self.selected_token_b['address']:
            QMessageBox.warning(self, "Invalid Pair", 
                              "Cannot create a pair with the same token. Please select different tokens.")
            return
        
        # Search for pools
        token_a_address = self.selected_token_a['address']
        token_b_address = self.selected_token_b['address']
        
        logger.info(f"Searching routes for {self.selected_token_a['symbol']}/{self.selected_token_b['symbol']}")
        
        # Clear previous results
        self._clear_pool_search_results()
        
        # Show searching message
        self._show_searching_message()
        
        # Allow UI to update before blocking search operations
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Step 1: Check if Ociswap pool exists
        pools = self.pool_manager.search_pools_for_pair(token_a_address, token_b_address)
        
        if pools:
            # Clear animation and show result
            self._clear_pool_search_results()
            
            # Ociswap pool exists - show simple pair widget
            logger.info(f"Found {len(pools)} direct pools, showing pair")
            pair_data = {
                'token_a_address': token_a_address,
                'token_b_address': token_b_address,
                'token_a_symbol': self.selected_token_a['symbol'],
                'token_b_symbol': self.selected_token_b['symbol'],
                'source': 'ociswap'
            }
            pair_widget = SimplePairResultWidget(pair_data, self.ui.scrollAreaWidgetContents_11)
            pair_widget.pair_clicked.connect(self._on_pair_selected)
            self.pool_search_layout.addWidget(pair_widget)
        else:
            # Step 2: No Ociswap pool - check Astrolescent route
            logger.info("No direct pools found, checking aggregated routes...")
            
            if not self.route_checker:
                self._clear_pool_search_results()
                no_route_label = QLabel("Please set a wallet to check trade pair routes.")
                no_route_label.setStyleSheet("color: #999; padding: 10px;")
                no_route_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.pool_search_layout.addWidget(no_route_label)
                return
            
            route_info = self.route_checker.check_route_exists(token_a_address, token_b_address)
            
            # Clear animation before showing result
            self._clear_pool_search_results()
            
            if route_info['route_exists']:
                # Astrolescent route found - show pair widget
                logger.info(f"Aggregated route found with {route_info['price_impact']:.2f}% impact")
                pair_data = {
                    'token_a_address': token_a_address,
                    'token_b_address': token_b_address,
                    'token_a_symbol': self.selected_token_a['symbol'],
                    'token_b_symbol': self.selected_token_b['symbol'],
                    'source': 'astrolescent',
                    'price_impact': route_info['price_impact'],
                    'feasible': route_info['feasible']
                }
                pair_widget = SimplePairResultWidget(pair_data, self.ui.scrollAreaWidgetContents_11)
                pair_widget.pair_clicked.connect(self._on_pair_selected)
                self.pool_search_layout.addWidget(pair_widget)
            else:
                # No route found anywhere
                error_msg = route_info.get('error', 'Unknown error')
                no_route_label = QLabel(f"No trading route found.\n{error_msg}")
                no_route_label.setStyleSheet("color: #999; padding: 10px;")
                no_route_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_route_label.setWordWrap(True)
                self.pool_search_layout.addWidget(no_route_label)
                logger.info(f"No route found: {error_msg}")

    def _show_searching_message(self):
        """Display 'Searching...' message in the pool search results area."""
        # Ensure the scroll area widget is visible
        self.ui.scrollAreaWidgetContents_11.show()
        self.ui.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.show()
        
        # Create label for searching message
        searching_label = QLabel("Searching...")
        searching_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        searching_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        
        # Add stretch before to center vertically
        self.pool_search_layout.addStretch(1)
        # Add the message centered
        self.pool_search_layout.addWidget(searching_label, 0, Qt.AlignmentFlag.AlignCenter)
        # Add stretch after to center vertically
        self.pool_search_layout.addStretch(1)
        
        # Make sure the label is visible
        searching_label.show()
        
        logger.debug("Searching message displayed")
    
    def _clear_pool_search_results(self):
        """Clear all widgets from pool search results area."""
        self._clear_layout(self.pool_search_layout)

    def _on_pair_selected(self, pair_data: Dict):
        """
        Handle pair selection - add the token pair to trade_pairs table.
        Works for both Ociswap and Astrolescent routes.
        
        Args:
            pair_data: Dictionary containing pair information
        """
        token_a_symbol = pair_data.get('token_a_symbol', 'Unknown')
        token_b_symbol = pair_data.get('token_b_symbol', 'Unknown')
        source = pair_data.get('source', 'unknown')
        
        logger.info(f"Pair selected: {token_a_symbol}/{token_b_symbol} (source: {source})")
        
        # Get token addresses
        base_token_address = pair_data['token_a_address']
        quote_token_address = pair_data['token_b_address']
        
        # Add to trade_pairs table (no pool_address needed - Astrolescent handles routing)
        success = self.trade_pair_manager.add_trade_pair(
            base_token=base_token_address,
            quote_token=quote_token_address,
            price=None
        )
        
        if success:
            logger.info(f"Trade pair added successfully: {token_a_symbol}/{token_b_symbol}")
            
            # Refresh the middle scroll area to show the new pair
            self._populate_individual_tokens_for_configuration()
            
            # Show success message with source info
            source_msg = "via direct pools" if source == 'ociswap' else "via aggregated routes"
            impact_msg = ""
            if source == 'astrolescent':
                price_impact = pair_data.get('price_impact', 0)
                impact_msg = f"Price impact: {price_impact:.1f}%"
            
            QMessageBox.information(
                self, 
                "Pair Added", 
                f"{token_a_symbol}/{token_b_symbol} has been added to your Pairs of Interest \n{source_msg}. {impact_msg}\n\n"
                f"Move them to Radbot Pairs to build historical data."
            )
        else:
            # Most likely already exists due to UNIQUE constraint
            logger.info(f"Trade pair may already exist: {token_a_symbol}/{token_b_symbol}")
            QMessageBox.information(
                self,
                "Pair Exists",
                f"{token_a_symbol}/{token_b_symbol} already exists in your pairs."
            )
