import logging
import json
import shutil
import os
import sys
from pathlib import Path
from typing import Optional, Union, Dict

from config.paths import PACKAGE_ROOT, USER_DATA_DIR

# Add libs directory to DLL search path for Cairo (Windows)
if sys.platform == 'win32':
    libs_dir = PACKAGE_ROOT / "libs"
    if libs_dir.exists():
        # Add to PATH for Cairo DLL loading
        os.environ['PATH'] = str(libs_dir) + os.pathsep + os.environ.get('PATH', '')
        # Also try adding to DLL search (Python 3.8+)
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(str(libs_dir))
from PySide6.QtWidgets import (
    QWidget, QLabel, QFileDialog, QMessageBox, QDialog, QInputDialog, QVBoxLayout, QLineEdit, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QEvent, QPoint, Signal, QTimer
from PySide6.QtGui import QPixmap, QMovie, QFont
import segno
from PIL.ImageQt import ImageQt
from PIL import Image
from gui.wallet_ui import Ui_WalletTabMain
from core.wallet import RadixWallet
from gui.components.token_display import TokenDisplayWidget
from gui.components.wallet_qr_popup import WalletQRCodeWindow
from gui.components.transaction_manifest_dialog import TransactionManifestDialog
from services.trade_monitor import TradeMonitor
from database.database import Database
from services.wallet_balance_service import WalletBalanceService
from core.radix_network import RadixNetwork, RadixNetworkError 
from core.transaction_builder import RadixTransactionBuilder
from decimal import Decimal, InvalidOperation 
from radix_engine_toolkit import Decimal as RETDecimal, TransactionHeaderV1

# Configure a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust as needed
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class WalletQRCodeWindow(QDialog):
    """
    Popup window displaying the wallet address as an artistic QR code
    with a background GIF animation.
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Wallet Address QR Code")
        self.setFixedSize(300, 300)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Container widget for layering background and QR code labels
        self.container = QWidget(self)
        self.container.setObjectName("qrCodeContainer") # Add unique name for styling
        self.container.setGeometry(0, 0, 300, 300)
        self.container.setStyleSheet("background-color: transparent;")

        # Background GIF label
        self.bg_label = QLabel(self.container)
        self.bg_label.setObjectName("qrCodeBackgroundLabel") # Add unique name for styling
        self.bg_label.setGeometry(0, 0, 300, 300)
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.bg_label.setAttribute(Qt.WA_TranslucentBackground)

        # QR code display label
        self.qr_label = QLabel(self.container)
        self.qr_label.setGeometry(0, 0, 300, 300)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.qr_label.raise_()

        # Resolve image paths relative to project root
        self.gif_path = PACKAGE_ROOT / "images" / "GreenNod.gif"
        self.gif_path2 = PACKAGE_ROOT / "images" / "trans_background25.png"

        logger.debug(f"Loading GIF from: {self.gif_path.resolve()}")
        logger.debug(f"Loading background image from: {self.gif_path2.resolve()}")

        if not self.gif_path.exists():
            logger.warning("GIF file not found at expected path.")
        if not self.gif_path2.exists():
            logger.warning("Background image file not found at expected path.")

        # Setup and start the background GIF animation
        self.movie = QMovie(str(self.gif_path))
        self.movie.setScaledSize(QSize(300, 300))
        self.bg_label.setMovie(self.movie)
        self.movie.start()

    def set_wallet_address(self, address: str, wallet_file_path: Optional[Path] = None):
        """
        Generate an artistic QR code for the wallet address and display it.
        Also updates the wallet JSON file with the QR code image path if provided.
        Saves QR codes in project's images/qr directory.
        """
        qr = segno.make(address)
        
        # Create QR code directory in project root
        qr_dir = PACKAGE_ROOT / "images" / "qr"
        qr_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from last 12 chars of address (unique identifier)
        address_suffix = address.replace('_', '')[-12:]
        qr_filename = f"qr_{address_suffix}.png"
        qr_img_path = qr_dir / qr_filename
        
        try:
            # Generate artistic QR code directly to project directory
            qr.to_artistic(
                str(self.gif_path2),
                str(qr_img_path),
                scale=5,
                dark='white',
                light=None,
                border=1
            )
            pil_img = Image.open(qr_img_path)
            qimage = ImageQt(pil_img)
            pixmap = QPixmap.fromImage(qimage)
            pixmap = pixmap.scaled(296, 296, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qr_label.setPixmap(pixmap)
            logger.debug(f"Artistic QR code generated and saved to {qr_img_path}")
        except Exception as e:
            logger.error(f"Failed to generate artistic QR code: {e}")
            # Fallback: generate plain QR code
            try:
                img = qr.to_pil(scale=10)
                img.save(qr_img_path)
                qimage = ImageQt(img)
                pixmap = QPixmap.fromImage(qimage)
                self.qr_label.setPixmap(pixmap)
                logger.info(f"Plain QR code saved as fallback to {qr_img_path}")
            except Exception as fallback_error:
                logger.error(f"Failed to generate fallback QR code: {fallback_error}")
                return

        if wallet_file_path:
            try:
                # Store relative path in wallet file for portability
                relative_path = f"images/qr/{qr_filename}"
                with open(wallet_file_path, 'r', encoding='utf-8') as f:
                    wallet_data = json.load(f)
                wallet_data['qr_code_image'] = relative_path
                with open(wallet_file_path, 'w', encoding='utf-8') as f:
                    json.dump(wallet_data, f, indent=4)
                logger.debug(f"Updated wallet config with QR code path: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to update wallet config with QR code path: {e}")

def show_message(widget, message: str):
    """
    Helper function to show informational message boxes.
    """
    QMessageBox.information(widget, "Rad Bot", message)



class WalletTabMain(QWidget):
    """
    Main wallet tab widget managing wallet loading, creation,
    import/export, and QR code display.
    """
    wallet_loaded = Signal(object)  # Signal emitted when wallet is loaded
    wallet_unloaded = Signal() # Signal for when wallet is locked/closed

    def __init__(self, parent=None, db_path: str = None, service_manager=None, main_window=None, service_coordinator=None):
        super().__init__(parent)
        logger.debug("Initializing WalletTabMain")
        self.main_window = main_window # Store the main window reference
        self.service_coordinator = service_coordinator  # NEW: For task coordination
        self.ui = Ui_WalletTabMain()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        self.wallet: Optional[RadixWallet] = None
        self.wallet_qr_popup = WalletQRCodeWindow(self)
        self.balance_service: Optional[WalletBalanceService] = None
        self.db_path = db_path
        self.service_manager = service_manager
        if self.db_path:
            self.db_instance = Database(self.db_path)
            self.balance_manager = self.db_instance.get_balance_manager()
            self.token_manager = self.db_instance.get_token_manager()
        else:
            self.db_instance = None
            self.balance_manager = None
            self.token_manager = None
            logger.error("Database path not provided to WalletTabMain, managers not initialized.")

        # Initialize balance display
        self.balance_layout: Optional[QVBoxLayout] = None
        
        # Password change detection (debounced)
        self._loaded_password: Optional[str] = None  # Store password used to load wallet
        self._password_change_timer = QTimer(self)
        self._password_change_timer.setSingleShot(True)
        self._password_change_timer.setInterval(500)  # 500ms debounce
        self._password_change_timer.timeout.connect(self._on_password_change_debounced)

        self._init_ui_elements()
        self._setup_signals()
        
        # Additional signals for wallet operations
        self.ui.WalletTabMainSelectWalletBrowseButton.clicked.connect(self.select_wallet_file)
        self.ui.WalletTabMainEnterWalletPasswordLoadButton.clicked.connect(self.load_wallet)
        
        # Connect password field change detection
        self.ui.WalletTabMainWalletPasswordUnlockInput.textChanged.connect(self._on_password_text_changed)
    
    @staticmethod
    def _get_relative_wallet_path(wallet_file_path: Path) -> str:
        """
        Convert absolute wallet file path to relative path for portability.
        Returns path relative to project root.
        """
        try:
            # Get project root (parent of gui directory)
            # Convert wallet path to relative
            relative_path = wallet_file_path.resolve().relative_to(PACKAGE_ROOT)
            return str(relative_path).replace('\\', '/')  # Use forward slashes for cross-platform
        except ValueError:
            # If wallet is outside project directory, return absolute path as fallback
            logger.warning(f"Wallet file {wallet_file_path} is outside project directory, storing absolute path")
            return str(wallet_file_path)
    
    @staticmethod
    def _resolve_wallet_path(stored_path: str) -> Path:
        """
        Convert stored wallet path (relative or absolute) to absolute Path object.
        Handles both relative paths (from project root) and absolute paths.
        """
        wallet_path = Path(stored_path)
        if not wallet_path.is_absolute():
            # Resolve relative to project root
            wallet_path = (PACKAGE_ROOT / wallet_path).resolve()
        return wallet_path
    
    def _setup_signals(self):
        """Set up all UI signal connections"""
        self.ui.WalletTabMainEnterWalletPasswordCreateButton.clicked.connect(self.create_wallet)
        self.ui.WalletTabMainSelectWalletExportButton.clicked.connect(self.export_wallet)
        self.ui.WalletTabMainWithdrawButton.clicked.connect(self.handle_withdraw)
        self.ui.WalletTabMainWalletPasswordWithdrawInput.returnPressed.connect(self.handle_withdraw)
        self.ui.WalletTabMainSelectWalletImportButton.clicked.connect(self.import_wallet)
        
        # Set up QR code icon behavior
        qr_icon = self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon
        qr_icon.setCursor(Qt.PointingHandCursor)
        qr_icon.installEventFilter(self)
        
    def init_balance_display(self):
        """Initialize wallet balance display UI components using QScrollArea."""
        logger.debug("Initializing balance display (ScrollArea)")
        contents_widget = self.ui.WalletTabMainWalletBalancesScrollArea.widget()
        if not contents_widget:
            logger.warning("WalletTabMainWalletBalancesScrollArea has no widget set. Creating one.")
            contents_widget = QWidget() # Create a new QWidget to be the scrollable content
            self.ui.WalletTabMainWalletBalancesScrollArea.setWidget(contents_widget)
            self.ui.WalletTabMainWalletBalancesScrollArea.setWidgetResizable(True) # Crucial for layout to work
        
        # Background from theme QSS

        # Use the existing layout created by the responsive UI
        if hasattr(self.ui, 'WalletTabMainWalletBalancesScrollAreaLayout'):
            self.balance_layout = self.ui.WalletTabMainWalletBalancesScrollAreaLayout
            logger.debug("Using existing WalletTabMainWalletBalancesScrollAreaLayout from responsive UI")
        elif self.balance_layout is None:
            # Fallback: create new layout if responsive UI doesn't exist (legacy mode)
            self.balance_layout = QVBoxLayout(contents_widget) # Set the layout on the contents_widget
            self.balance_layout.setSpacing(5) 
            self.balance_layout.setContentsMargins(10, 10, 10, 10)
            self.balance_layout.setAlignment(Qt.AlignTop) # Align items to the top
            logger.debug("Created new balance layout (legacy mode)")
        else:
            # If layout exists, ensure it's set on the correct widget
            if contents_widget.layout() != self.balance_layout:
                # This case might happen if the contents_widget was somehow replaced or layout was removed
                # It's safer to just re-apply
                # First, clear old widgets if any are still managed by this layout instance from a previous parent
                self._clear_balance_layout(save_withdrawal_amounts=False) # Clear items from the old layout's control
                contents_widget.setLayout(self.balance_layout) # Re-apply to new/current contents_widget
        
        self._clear_balance_layout(save_withdrawal_amounts=False) # Clear any widgets currently in the layout
        placeholder = QLabel("No wallet loaded")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setObjectName("placeholder_text")  # Use theme styling
        self.balance_layout.addWidget(placeholder)
        logger.debug("Balance display initialized with placeholder.")

    # Helper method to clear balance layout while preserving withdrawal amounts
    def _clear_balance_layout(self, save_withdrawal_amounts=True):
        """Clear balance layout, optionally saving withdrawal amounts first"""
        if save_withdrawal_amounts:
            # Save current withdrawal amounts before clearing
            self._saved_withdrawal_amounts = {}
            for i in range(self.balance_layout.count()):
                widget = self.balance_layout.itemAt(i).widget()
                if isinstance(widget, TokenDisplayWidget):
                    try:
                        # Get raw text to preserve user's format ("100" not "100.00000000")
                        amount_text = widget.get_withdraw_amount_text()
                        if amount_text:  # Only save if user entered something
                            # Verify it's a valid number > 0
                            try:
                                amount_value = float(amount_text)
                                if amount_value > 0:
                                    self._saved_withdrawal_amounts[widget.token_rri] = amount_text
                                    logger.debug(f"Saved withdrawal amount for {widget.token_symbol}: {amount_text}")
                            except ValueError:
                                pass  # Invalid number, don't save
                    except:
                        pass
        
        while self.balance_layout.count():
            item = self.balance_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _display_balance_error(self, error_message: str):
        # Log the error but don't immediately show red error in UI
        # Balance service will retry and might succeed shortly
        logger.warning(f"Balance update error (logged, not displayed): {error_message}")
        
        # Only show a neutral message if balance layout is empty
        if self.balance_layout.count() == 0:
            self._clear_balance_layout(save_withdrawal_amounts=False)
            placeholder = QLabel("Loading wallet balance...")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("placeholder_text")  # Use theme styling
            placeholder.setStyleSheet("padding: 10px;")
            self.balance_layout.addWidget(placeholder)
            self.balance_layout.addStretch(1)

    def update_balance_display(self, balances_or_message: Union[dict, str]):
        logger.debug(f"update_balance_display (ScrollArea) called with type: {type(balances_or_message)}, content: {str(balances_or_message)[:200]}...") # Log type and snippet
        
        # Don't clear layout yet - only clear when we have new data to replace it with
        # This prevents the flickering/disappearing balance list during updates

        if not self.wallet:
            logger.info("Update balance display: No wallet loaded.")
            self._clear_balance_layout()  # Only clear if no wallet
            placeholder = QLabel("No wallet loaded")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("placeholder_text")  # Use theme styling
            placeholder.setStyleSheet("padding: 10px;")
            self.balance_layout.addWidget(placeholder)
            self.balance_layout.addStretch(1)
            return

        logger.info(f"--- Detailed Type Check for balances_or_message ---")
        logger.info(f"Value snippet: {str(balances_or_message)[:500]}")
        logger.info(f"Actual Type: {type(balances_or_message)}")
        logger.info(f"Is instance of dict? {isinstance(balances_or_message, dict)}")
        logger.info(f"Is instance of str? {isinstance(balances_or_message, str)}")
        try:
            if hasattr(balances_or_message, 'keys') and callable(getattr(balances_or_message, 'keys')):
                logger.info(f"Has 'keys' method. Keys: {list(balances_or_message.keys())[:5] if balances_or_message else 'None'}")
            elif hasattr(balances_or_message, '__getitem__'):
                 logger.info(f"Has '__getitem__', might be dict-like.")
        except Exception as e:
            logger.info(f"Error during dict-like attribute check: {e}")
        logger.info(f"--- End Detailed Type Check ---")

        if isinstance(balances_or_message, dict):
            # Only clear layout when we have actual balance data (dict with items)
            # Empty dict means "wallet loaded but no tokens" - should replace display
            if not balances_or_message:
                logger.info("No token balances found for the current wallet.")
                self._clear_balance_layout()  # Clear for empty wallet
                placeholder = QLabel("No funds detected in this wallet yet.")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setObjectName("placeholder_text")  # Use theme styling
                placeholder.setStyleSheet("padding: 10px;")
                self.balance_layout.addWidget(placeholder)
            else:
                # We have actual balance data - safe to clear and rebuild
                logger.info(f"Rendering {len(balances_or_message)} token(s).")
                self._clear_balance_layout()  # Clear before adding new balance widgets
                for token_rri, details in balances_or_message.items():
                    token_rri_val = token_rri # Already have this from the loop key
                    details_dict = details if isinstance(details, dict) else {}
                    symbol = details_dict.get('symbol', 'N/A')
                    name = details_dict.get('name', symbol) # Use name, fallback to symbol
                    amount = details_dict.get('available', 0.0) 
                    divisibility = details_dict.get('divisibility', 18) 
                    
                    # Fetch full token details to get the icon path
                    full_token_details = self.token_manager.get_token_by_address(token_rri_val)
                    icon_local_path = None
                    if full_token_details:
                        icon_local_path = full_token_details.get('icon_local_path')
                    else:
                        logger.warning(f"Could not retrieve full token details for {token_rri_val}. Icon will be missing.")

                    logger.debug(f"Creating TokenDisplayWidget for {name} ({symbol}, {token_rri_val}) with amount {amount}, divisibility {divisibility}, icon_path {icon_local_path}")
                    try:
                        # Ensure TokenDisplayWidget is imported: from ..components.token_display import TokenDisplayWidget
                        token_widget = TokenDisplayWidget(
                            token_name=name,
                            token_symbol=symbol,
                            token_amount=amount, 
                            token_rri=token_rri_val,
                            divisibility=divisibility,
                            icon_local_path=icon_local_path # Pass icon path
                        )
                        # Connect Max button signal
                        token_widget.max_clicked.connect(self._handle_max_withdraw)
                        
                        # Restore previously entered withdrawal amount if it exists
                        if hasattr(self, '_saved_withdrawal_amounts') and token_rri_val in self._saved_withdrawal_amounts:
                            saved_text = self._saved_withdrawal_amounts[token_rri_val]
                            # Restore exact text user entered (preserves format like "100" not "100.00000000")
                            token_widget.set_withdraw_amount_text(saved_text)
                            logger.debug(f"Restored withdrawal amount for {symbol}: {saved_text}")
                        
                        self.balance_layout.addWidget(token_widget)
                    except Exception as e:
                        logger.error(f"Error creating TokenDisplayWidget for {symbol}: {e}", exc_info=True)
                        error_label = QLabel(f"Error displaying {symbol}")
                        error_label.setProperty("class", "status_error")  # Use theme error styling
                        self.balance_layout.addWidget(error_label)
            self.balance_layout.addStretch(1)

        elif isinstance(balances_or_message, str):
            logger.info(f"Displaying message in balance panel: {balances_or_message}")
            lower_msg = balances_or_message.lower()
            
            # For "loading" or "refreshing" messages, keep existing balances visible
            # Don't clear the layout - user can still see their last known balances
            if "loading" in lower_msg or "refreshing" in lower_msg or "updating" in lower_msg:
                logger.info("Temporary status message - keeping existing balances visible")
                # Don't clear, don't add placeholder - existing balances remain visible
                return
            
            # For errors or other messages, clear and show the message
            self._clear_balance_layout()
            placeholder = QLabel(balances_or_message)
            placeholder.setAlignment(Qt.AlignCenter)
            # Use theme classes for styling
            if "error" in lower_msg or "failed" in lower_msg:
                placeholder.setProperty("class", "status_error")
                placeholder.setStyleSheet("font-weight: bold; padding: 10px;")
            else:
                placeholder.setObjectName("placeholder_text")
                placeholder.setStyleSheet("padding: 10px;")
            placeholder.setWordWrap(True)
            self.balance_layout.addWidget(placeholder)
            self.balance_layout.addStretch(1)
        else:
            logger.warning(f"update_balance_display called with unexpected type: {type(balances_or_message)}")
            self._clear_balance_layout()  # Clear for error display
            error_label = QLabel(f"An unexpected error occurred displaying balances. Data type: {type(balances_or_message)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setProperty("class", "status_error")
            error_label.setStyleSheet("font-weight: bold; padding: 10px;")
            error_label.setWordWrap(True)
            self.balance_layout.addWidget(error_label)
            self.balance_layout.addStretch(1)

    def handle_balance_service_update(self, payload, is_error: bool = False):
        if is_error:
            message = payload if isinstance(payload, str) else str(payload)
            self._display_balance_error(message)
            return

        if isinstance(payload, dict) or isinstance(payload, str):
            self.update_balance_display(payload)
        else:
            logger.warning(f"WalletBalanceService emitted unsupported payload type: {type(payload)}")
            self.update_balance_display({})

    def load_wallet(self):
        """Load a wallet from file, initialize services, and update UI."""
        logger.debug("Attempting to load wallet...")
        try:  # Outer try for overall function structure
            existing_wallet_file = None
            if self.wallet and hasattr(self.wallet, 'wallet_file') and self.wallet.wallet_file:
                existing_wallet_file = Path(self.wallet.wallet_file).resolve()
            wallet_file_path_str = self.ui.WalletTabMainSelectWalletInputText.text()
            if not wallet_file_path_str:
                QMessageBox.warning(self, "Input Error", "Please select a wallet file first.")
                logger.warning("Load wallet attempt failed: No wallet file selected.")
                return

            wallet_file = Path(wallet_file_path_str)
            if not wallet_file.exists() or not wallet_file.is_file():
                QMessageBox.critical(self, "File Error", f"Wallet file not found or is not a file: {wallet_file}")
                logger.error(f"Load wallet attempt failed: Wallet file not found at {wallet_file}")
                return

            password = self._require_unlock_password()
            if password is None:
                logger.warning("Load wallet attempt failed: Password not provided.")
                return

            logger.debug(f"Attempting to load wallet from: {wallet_file}")
            try:
                self.wallet = RadixWallet(wallet_file, password)
                self.wallet.load_wallet() 

                is_same_wallet = False
                if existing_wallet_file is not None:
                    try:
                        is_same_wallet = existing_wallet_file == wallet_file.resolve()
                    except Exception:
                        is_same_wallet = False

                if not (self.wallet and self.wallet.public_address):
                    logger.error("Wallet object loaded, but public_address is missing. Password might be incorrect or wallet file corrupted.")
                    self.wallet = None
                    QMessageBox.critical(self, "Wallet Load Failed", "Failed to load wallet. Please check the wallet file and password.")
                    self.update_balance_display("No wallet loaded") 
                    self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.setVisible(False)
                    return

                logger.info(f"Wallet loaded successfully: {self.wallet.public_address}")
                
                # Store the password used to load (for change detection)
                self._loaded_password = password
                
                self.ui.WalletTabMainCurrentAddressStatusLabel.setText(
                    f"{self.wallet.public_address}")
            
                wallet_name = wallet_file.stem 
                # Database interaction for saving wallet entry and setting active wallet
                if self.db_instance:
                    try:
                        wallet_manager = self.db_instance.get_wallet_manager()
                        # Store relative path for portability
                        relative_path = self._get_relative_wallet_path(wallet_file)
                        wallet_id = wallet_manager.get_or_create_wallet_entry(
                            wallet_name, 
                            self.wallet.public_address, 
                            relative_path
                        )

                        if wallet_id:
                            self.wallet.wallet_id = wallet_id # Assign the wallet_id to the RadixWallet instance
                            logger.info(f"Wallet entry obtained/created with ID: {wallet_id} for {wallet_name}")
                            settings_manager = self.db_instance.get_settings_manager()
                            updated = settings_manager.update_settings({'active_wallet_id': wallet_id})
                            if updated:
                                logger.info(f"Active wallet set to wallet_id: {wallet_id} in database.")
                            else:
                                logger.error(f"Failed to set active wallet in database for wallet_id: {wallet_id}.")
                        else:
                            logger.error(f"Failed to get or create wallet entry in database for {wallet_name}.")
                    except Exception as db_exc:
                        logger.error(f"Database operation failed during wallet load for {wallet_name}: {db_exc}", exc_info=True)
                else:
                    logger.warning("Database instance not available. Skipping wallet DB operations for load_wallet.") 

                # Emit wallet_loaded signal AFTER setting the wallet_id
                self.wallet_loaded.emit(self.wallet)

                # --- Refactored WalletBalanceService Initialization ---
                # Ensure WalletBalanceService is initialized on first load
                if not self.balance_service:
                    logger.debug("Attempting to initialize new WalletBalanceService.")
                    if self.db_instance:
                        balance_manager_instance = self.db_instance.get_balance_manager()
                        if balance_manager_instance:
                            # Get icon cache and token updater services from main window
                            icon_cache_service = getattr(self.main_window, 'icon_cache_service', None) if self.main_window else None
                            token_updater_service = getattr(self.main_window, 'token_updater_service', None) if self.main_window else None
                            
                            # Create the service instance
                            self.balance_service = WalletBalanceService(
                                wallet=self.wallet, 
                                balance_manager=balance_manager_instance,
                                icon_cache_service=icon_cache_service,
                                token_updater_service=token_updater_service,  # For fetching full token metadata
                                service_coordinator=self.service_coordinator  # NEW: For coordination
                            )
                            logger.info("WalletBalanceService initialized with task coordination.")
                            
                            # Connect signals with QueuedConnection for thread safety
                            self.balance_service.balance_updated.connect(self.update_balance_display, Qt.QueuedConnection)
                            self.balance_service.error_occurred.connect(self._display_balance_error, Qt.QueuedConnection)
                            
                            # Register or start the service
                            if self.service_manager:
                                logger.debug("Registering balance service with ServiceManager.")
                                self.service_manager.register_service(self.balance_service)
                            else:
                                logger.warning("No ServiceManager, starting balance service directly.")
                                self.balance_service.start()
                        else:
                            logger.error("Failed to get BalanceManager. WalletBalanceService not created.")
                    else:
                        logger.error("db_instance is None. WalletBalanceService not created.")

                # If the service exists (either just created or from before), update its wallet
                if self.balance_service:
                    logger.debug("Updating WalletBalanceService with new wallet context.")
                    self.balance_service.set_wallet(self.wallet)
                    
                    # Show cached balances immediately for responsive UX
                    if not is_same_wallet:
                        try:
                            logger.info("Rendering cached balances from database")
                            self._render_balances_from_manager()
                        except Exception as render_exc:
                            logger.warning(f"Failed to render cached balances: {render_exc}", exc_info=True)
                            self.update_balance_display("Loading wallet balance...")
                    
                    # Trigger background refresh to get latest balances
                    try:
                        logger.info("Triggering background balance refresh after wallet load")
                        self.schedule_balance_refresh(delay_ms=0)
                    except Exception as e:
                        logger.warning(f"Failed to trigger balance refresh: {e}")
                else:
                    logger.error("Cannot proceed with balance updates as WalletBalanceService is unavailable.")
                    self.update_balance_display("Error: Balance service failed")

                self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.setVisible(True)
                logger.info(f"wallet_loaded signal emitted for {self.wallet.public_address} (ID: {self.wallet.wallet_id})")

                # Ensure a statistics entry exists for the loaded wallet
                statistics_manager = self.db_instance.get_statistics_manager()
                statistics_manager.ensure_statistics_entry(self.wallet.wallet_id)

            except ValueError as ve: 
                logger.error(f"Wallet integrity error: {ve}", exc_info=True)
                QMessageBox.critical(self, "Wallet Load Failed", f"Could not load the wallet: {str(ve)}. Please check your password and wallet file.")
                self.cleanup_wallet_resources_on_failure() 
                return
            except Exception as e: 
                logger.error(f"Error during wallet loading and initialization: {e}", exc_info=True)
                QMessageBox.critical(self, "Wallet Load Failed", f"An unexpected error occurred while loading the wallet: {str(e)}")
                self.cleanup_wallet_resources_on_failure() 
                return 

        except Exception as e: 
            logger.error(f"Unexpected error in the load_wallet function structure: {e}", exc_info=True)
            QMessageBox.critical(self, "Application Error", f"An unexpected error occurred in the wallet loading process: {str(e)}")
            self.cleanup_wallet_resources_on_failure() 
            return

    def cleanup_wallet_resources_on_failure(self):
        """Clean up wallet-related resources and UI elements on failure."""
        logger.debug("Cleaning up wallet resources on failure.")
        if self.balance_service:
            logger.debug(f"Stopping and unregistering balance service: {self.balance_service}")
            if self.service_manager and hasattr(self.service_manager, 'unregister_service'):
                self.service_manager.unregister_service(self.balance_service)
            if hasattr(self.balance_service, 'stop'):  # Ensure stop method exists
                self.balance_service.stop()
            self.balance_service = None

        if self.wallet:
            logger.debug(f"Resetting wallet instance: {self.wallet}")
            # If RadixWallet has specific cleanup like disconnecting signals or stopping threads, call them here.
            # e.g., self.wallet.disconnect_signals() or self.wallet.stop_threads()
            self.wallet = None
        
        self.ui.WalletTabMainCurrentAddressStatusLabel.setText("No wallet loaded")
        self.ui.WalletTabMainSelectWalletInputText.clear()
        # Do not clear self.ui.WalletTabMainWalletPasswordInput.text() - user preference
        self.update_balance_display("No wallet loaded / Error")
        
        # Hide QR code icon and button
        self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.setVisible(False)

    def init_withdraw_ui(self):
        """Initialize withdraw UI components."""
        self.ui.WalletTabMainWithdrawButton.clicked.connect(self.handle_withdraw)
        self.ui.WalletTabMainWalletPasswordWithdrawInput.returnPressed.connect(self.handle_withdraw)
        self.ui.WalletTabMainSelectWalletImportButton.clicked.connect(self.import_wallet)
        
        # Connect balance update signal
        if hasattr(self.wallet, 'balance_updated'):
            self.wallet.balance_updated.connect(self.update_balance_display)
            self.wallet.error_occurred.connect(self.handle_balance_error)
        
    def handle_balance_error(self, error: str):
        """Handle balance update error."""
        QMessageBox.warning(self, "Error", f"Failed to update balance: {error}")
        logger.error(f"Balance update error: {error}")

        # Set pointer cursor on QR code icon for better UX
        qr_icon = self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon
        qr_icon.setCursor(Qt.PointingHandCursor)
        
        # Install event filter for QR code icon
        qr_icon.installEventFilter(self)

    def eventFilter(self, watched, event):
        """Handle event filtering to show QR popup on mouse hover."""
        if watched == self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon:
            if event.type() == QEvent.Enter:
                logger.debug("Mouse entered QR code icon area, showing popup.")
                self.show_wallet_qr_popup()
                return True  # Event handled
            elif event.type() == QEvent.Leave:
                if hasattr(self, 'wallet_qr_popup') and self.wallet_qr_popup.isVisible():
                    self.wallet_qr_popup.close()
                    return True
        return super().eventFilter(watched, event)

    def show_wallet_qr_popup(self):
        """Display the QR code popup window near the QR code icon."""
        logger.debug("show_wallet_qr_popup called")
        if not self.wallet:
            logger.warning("No wallet loaded; cannot show QR code.")
            return
        address = self.wallet.public_address
        if not address:
            logger.warning("Wallet address not available; cannot show QR code.")
            return
        wallet_file_path = Path(self.wallet.wallet_file) if hasattr(self.wallet, 'wallet_file') else None
        self.wallet_qr_popup.set_wallet_address(address, wallet_file_path)
        icon_pos = self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.mapToGlobal(QPoint(0, 0))
        popup_x = icon_pos.x() + self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.width() + 10
        popup_y = icon_pos.y()
        self.wallet_qr_popup.move(popup_x, popup_y)
        logger.debug("Showing QR popup window")
        self.wallet_qr_popup.show()
        self.wallet_qr_popup.raise_()
        self.wallet_qr_popup.activateWindow()

    def select_wallet_file(self):
        """Open file dialog to select a wallet file and update the input field."""
        logger.debug("select_wallet_file method entered.") 
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self, 
            "Select Wallet File", 
            "", 
            "JSON Files (*.json)"
        )
        logger.debug(f"QFileDialog.getOpenFileName returned: file_path='{file_path}', selected_filter='{selected_filter}'")
        if file_path:  # This condition is key
            logger.debug(f"file_path ('{file_path}') is considered True. Attempting to setText on WalletTabMainSelectWalletInputText.")
            self.ui.WalletTabMainSelectWalletInputText.setText(file_path)
            # Verify immediately if setText worked
            current_text = self.ui.WalletTabMainSelectWalletInputText.text()
            logger.debug(f"After setText, WalletTabMainSelectWalletInputText contains: '{current_text}'")
            if current_text == file_path:
                logger.debug("setText on WalletTabMainSelectWalletInputText appears to have worked successfully.")
            else:
                logger.warning(f"setText on WalletTabMainSelectWalletInputText FAILED or had no effect. Expected '{file_path}', got '{current_text}'")
            return file_path
        else:
            logger.debug(f"file_path ('{file_path}') is considered False. Not calling setText.")
        return None

    def get_wallet_password(self) -> str:
        """Retrieve the password entered by the user."""
        return self.ui.WalletTabMainWalletPasswordUnlockInput.text().strip()

    def _flash_line_edit(self, line_edit: Optional[QLineEdit], flashes: int = 2, color: str = "#ff5555"):
        """Briefly highlight a QLineEdit to draw the user's attention."""
        if line_edit is None:
            return

        original_style = line_edit.styleSheet()
        border_fragment = f" border: 1px solid {color};"
        highlight_style = original_style + border_fragment if original_style else f"border: 1px solid {color};"

        def apply_flash(remaining: int):
            if remaining <= 0:
                line_edit.setStyleSheet(original_style)
                return
            line_edit.setStyleSheet(highlight_style)
            line_edit.repaint()
            QTimer.singleShot(150, lambda: restore_flash(remaining))

        def restore_flash(remaining: int):
            line_edit.setStyleSheet(original_style)
            line_edit.repaint()
            QTimer.singleShot(150, lambda: apply_flash(remaining - 1))

        apply_flash(flashes * 2)

    def _require_password_field(self, line_edit: Optional[QLineEdit], message: str) -> Optional[str]:
        if line_edit is None:
            return None

        password = line_edit.text().strip()
        if not password:
            self._flash_line_edit(line_edit)
            if message:
                QMessageBox.warning(self, "Password Required", message)
            return None
        return password

    def _require_unlock_password(self) -> Optional[str]:
        return self._require_password_field(
            self.ui.WalletTabMainWalletPasswordUnlockInput,
            "Please enter the wallet password in the unlock field."
        )

    def _require_withdraw_password(self) -> Optional[str]:
        return self._require_password_field(
            self.ui.WalletTabMainWalletPasswordWithdrawInput,
            "Please enter the wallet password to authorize the withdrawal."
        )

    def _on_password_text_changed(self, new_text: str):
        """
        Handle password field text changes.
        Uses debounce to avoid unloading while user is typing.
        """
        # Only trigger if a wallet is currently loaded
        if self.wallet is not None:
            # Restart the debounce timer
            self._password_change_timer.start()
    
    def _on_password_change_debounced(self):
        """
        Called after password change debounce timer expires.
        Unloads wallet if password has changed from what was used to load it.
        """
        if self.wallet is None:
            return
        
        current_password = self.ui.WalletTabMainWalletPasswordUnlockInput.text()
        
        # Check if password actually changed from what was used to load
        if self._loaded_password is not None and current_password != self._loaded_password:
            logger.info("Password changed after wallet load - unloading wallet for security")
            self.unload_wallet()
    
    def unload_wallet(self):
        """
        Unload the current wallet and reset UI to logged-out state.
        Called when password is changed after wallet load.
        """
        logger.info("Unloading wallet...")
        
        # Stop and cleanup balance service
        if self.balance_service:
            logger.debug("Stopping balance service")
            if self.service_manager and hasattr(self.service_manager, 'unregister_service'):
                self.service_manager.unregister_service(self.balance_service)
            if hasattr(self.balance_service, 'stop'):
                self.balance_service.stop()
            self.balance_service = None
        
        # Clear wallet reference
        if self.wallet:
            logger.debug(f"Clearing wallet: {self.wallet.public_address}")
            self.wallet = None
        
        # Clear stored password
        self._loaded_password = None
        
        # Reset UI elements
        self.ui.WalletTabMainCurrentAddressStatusLabel.setText("No wallet loaded")
        self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.setVisible(False)
        
        # Clear balance display
        self._clear_balance_layout(save_withdrawal_amounts=False)
        placeholder = QLabel("No wallet loaded")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setObjectName("placeholder_text")
        self.balance_layout.addWidget(placeholder)
        
        # Clear withdrawal fields
        self.ui.WalletTabMainWithdrawAddressTextInput.clear()
        self.ui.WalletTabMainWalletPasswordWithdrawInput.clear()
        
        # Emit signal so main window can hide tabs
        self.wallet_unloaded.emit()
        logger.info("Wallet unloaded successfully")

    def _get_project_root(self) -> Path:
        """Return the project root directory (contains main.py)."""
        return PACKAGE_ROOT

    def _scan_for_mobile_wallet(self, seed_phrase: str, password: str) -> Optional[int]:
        """
        Scan account indices 0-20 for a funded wallet from the given seed phrase.
        Returns the account index if found, None otherwise.
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
        from PySide6.QtCore import QTimer
        import time
        
        SCAN_START_INDEX = 0
        SCAN_END_INDEX = 20
        SCAN_DELAY_MS = 2000  # 2 seconds
        
        # Create progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Scanning for Mobile Wallets")
        progress_dialog.setMinimumWidth(400)
        progress_dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        status_label = QLabel("Preparing to scan...")
        layout.addWidget(status_label)
        
        address_label = QLabel("")
        address_label.setWordWrap(True)
        address_label.setObjectName("secondary_text")
        address_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(address_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(SCAN_START_INDEX, SCAN_END_INDEX)
        progress_bar.setValue(SCAN_START_INDEX)
        layout.addWidget(progress_bar)
        
        cancel_btn = QPushButton("Cancel")
        layout.addWidget(cancel_btn)
        
        progress_dialog.setLayout(layout)
        
        # Scan state
        scan_state = {
            "current_index": SCAN_START_INDEX,
            "found_accounts": [],  # List of (index, address, balance_info) tuples
            "cancelled": False
        }
        
        def cancel_scan():
            scan_state["cancelled"] = True
            progress_dialog.reject()
        
        cancel_btn.clicked.connect(cancel_scan)
        
        def check_next_account():
            if scan_state["cancelled"]:
                return
            
            current_idx = scan_state["current_index"]
            
            if current_idx > SCAN_END_INDEX:
                # Scan complete - show results
                progress_dialog.accept()
                
                if not scan_state["found_accounts"]:
                    QMessageBox.warning(
                        self,
                        "No Wallets Found",
                        f"No funded wallets found in account indices {SCAN_START_INDEX}-{SCAN_END_INDEX}.\n"
                        "The wallet may be using a higher index or may not have any funds."
                    )
                    return
                
                # Show selection dialog for multiple accounts
                return
            
            status_label.setText(f"Checking account {current_idx} of {SCAN_END_INDEX}...")
            progress_bar.setValue(current_idx)
            
            try:
                # Create temporary wallet instance for this account index
                temp_file = Path(f"temp_scan_{current_idx}.json")
                temp_wallet = RadixWallet(temp_file, password, account_index=current_idx)
                priv_key_bytes = temp_wallet.derive_private_key_from_seed(seed_phrase)
                
                # Derive address without saving
                from radix_engine_toolkit import PrivateKey, Address
                private_key = PrivateKey.new_ed25519(priv_key_bytes)
                public_key = private_key.public_key()
                address = Address.preallocated_account_address_from_public_key(public_key, 1)
                address_str = address.as_str()
                
                address_label.setText(f"Address: {address_str}")
                logger.debug(f"Scanning account {current_idx}: {address_str}")
                
                # Check if wallet has balance
                from core.radix_network import RadixNetwork
                from decimal import Decimal
                network = RadixNetwork()
                balances = network.get_token_balances(address_str)
                
                # Calculate total balance info
                total_xrd = Decimal('0')
                token_count = 0
                if balances:
                    for token_address, token_data in balances.items():
                        amount_str = token_data.get('amount', '0')
                        try:
                            # Gateway returns human-readable amounts
                            amount = Decimal(amount_str)
                            if amount > 0:
                                token_count += 1
                                # Track XRD specifically
                                if token_address == "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd":
                                    total_xrd = amount
                                logger.debug(f"Account {current_idx}: {token_data.get('symbol', 'UNKNOWN')} = {amount_str}")
                        except (ValueError, TypeError, InvalidOperation):
                            logger.warning(f"Invalid amount format for {token_address}: {amount_str}")
                
                # Clean up temp file if it was created
                if temp_file.exists():
                    temp_file.unlink()
                
                if token_count > 0:
                    # Found account with balance - add to list
                    balance_info = f"{token_count} token(s), {total_xrd:.2f} XRD"
                    scan_state["found_accounts"].append((current_idx, address_str, balance_info))
                    logger.info(f"Found funded account at index {current_idx}: {balance_info}")
                
                # Always continue to next account (don't stop at first match)
                scan_state["current_index"] += 1
                QTimer.singleShot(SCAN_DELAY_MS, check_next_account)
                    
            except Exception as e:
                logger.error(f"Error scanning account {current_idx}: {e}", exc_info=True)
                # Continue to next account on error
                scan_state["current_index"] += 1
                QTimer.singleShot(SCAN_DELAY_MS, check_next_account)
        
        # Start the scan
        QTimer.singleShot(100, check_next_account)
        progress_dialog.exec()
        
        # If scan completed and found accounts, show selection dialog
        if scan_state["found_accounts"]:
            if len(scan_state["found_accounts"]) == 1:
                # Only one account found - auto-select it
                selected_index = scan_state["found_accounts"][0][0]
                selected_address = scan_state["found_accounts"][0][1]
                QMessageBox.information(
                    self,
                    "Wallet Found",
                    f"Found funded wallet at account index {selected_index}:\n{selected_address}"
                )
                return selected_index
            else:
                # Multiple accounts - let user choose
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel
                
                select_dialog = QDialog(self)
                select_dialog.setWindowTitle("Select Wallet Account")
                select_dialog.setMinimumWidth(600)
                
                layout = QVBoxLayout(select_dialog)
                layout.addWidget(QLabel(f"Found {len(scan_state['found_accounts'])} funded account(s). Select one to import:"))
                
                list_widget = QListWidget()
                for idx, addr, balance in scan_state["found_accounts"]:
                    list_widget.addItem(f"Account {idx}: {addr[:20]}...{addr[-10:]} ({balance})")
                list_widget.setCurrentRow(0)
                layout.addWidget(list_widget)
                
                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                button_box.accepted.connect(select_dialog.accept)
                button_box.rejected.connect(select_dialog.reject)
                layout.addWidget(button_box)
                
                if select_dialog.exec() == QDialog.Accepted:
                    selected_row = list_widget.currentRow()
                    if selected_row >= 0:
                        return scan_state["found_accounts"][selected_row][0]
        
        return None

    def create_wallet(self):
        """Create a new wallet, save it to a file, display seed phrase, and load it."""
        password = self._require_unlock_password()
        if not password:
            logger.info("Wallet creation cancelled: Password not provided.")
            return

        default_path = USER_DATA_DIR / "radbot_wallet.json"
        file_path_str, _ = QFileDialog.getSaveFileName(
            self, 
            "Create New Wallet File", 
            str(default_path),
            "JSON Files (*.json)"
        )

        if not file_path_str:
            logger.info("Wallet creation cancelled by user (no file selected for saving).")
            return
        
        wallet_file_path = Path(file_path_str)

        try:
            # Create and save the new wallet
            self.wallet = RadixWallet(wallet_file_path, password)
            self.wallet.wallet_id = None
            seed_phrase = self.wallet.create_new_wallet()  # This method saves the wallet

            logger.info(f"New wallet created with address: {self.wallet.public_address} and saved to {wallet_file_path}")

            # Update UI to reflect the new wallet
            self.ui.WalletTabMainSelectWalletInputText.setText(str(wallet_file_path))
            # self.ui.WalletTabMainWalletPasswordInput.setText(password)  # Don't clear password to keep it stored in RAM
            self.ui.WalletTabMainCurrentAddressStatusLabel.setText(f"{self.wallet.public_address}")
            
            # Display seed phrase securely
            words = seed_phrase.strip().split()
            if len(words) != 24:
                logger.error("Expected 24 words in generated seed phrase, got %d", len(words))
            else:
                table_rows = []
                for row in range(6):
                    cells = []
                    for col in range(4):
                        idx = row + col * 6
                        word = words[idx]
                        cell_html = (
                            "<td style=\"padding:4px 16px 4px 0; white-space:nowrap;\">"
                            f"<span style=\"font-weight:bold;\">{idx + 1:02d}.</span>&nbsp;{word}"
                            "</td>"
                        )
                        cells.append(cell_html)
                    table_rows.append(f"<tr>{''.join(cells)}</tr>")
                table_html = (
                    "<table style=\"margin:8px 0; border-collapse:collapse;"
                    " font-family:'Courier New', monospace; font-size:13px;\">"
                    f"{''.join(table_rows)}</table>"
                )

                seed_phrase_message = (
                    "<div style=\"max-width:520px;\">"
                    "<p><b>New Wallet Created Successfully!</b></p>"
                    "<p><b>IMPORTANT:</b> Write down your 24-word seed phrase exactly as shown below. "
                    "This is the <b>ONLY</b> way to recover your wallet if you lose access. "
                    "Store it in a very safe and private place.</p>"
                    "<p>Your wallet password (used for encrypting the wallet file) is <b>NOT</b> part of the seed phrase. "
                    "You will need both the wallet file and the password to access your funds.</p>"
                    "<p><b>Seed Phrase:</b></p>"
                    f"{table_html}"
                    "<p><b>Please TRIPLE check you wrote it down correctly!</b></p>"
                    "</div>"
                )

                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Seed Phrase - WRITE IT DOWN!")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setTextFormat(Qt.RichText)
                msg_box.setText(seed_phrase_message)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.setMinimumWidth(520)
                msg_box.exec()
                
                # Security: Clear mnemonic from memory after user has seen it
                seed_phrase = None
                self.wallet.mnemonic = None
                logger.debug("Mnemonic cleared from memory after display")

            # Database interaction for saving wallet entry and setting active wallet
            wallet_id = None
            if self.db_instance:
                try:
                    created_wallet_name = wallet_file_path.stem 
                    wallet_manager = self.db_instance.get_wallet_manager()
                    settings_manager = self.db_instance.get_settings_manager()
                    if wallet_manager and settings_manager:
                        # Store relative path for portability
                        relative_path = self._get_relative_wallet_path(wallet_file_path)
                        wallet_id = wallet_manager.get_or_create_wallet_entry(
                            created_wallet_name, 
                            self.wallet.public_address, 
                            relative_path
                        )

                        if wallet_id:
                            self.wallet.wallet_id = wallet_id
                            logger.info(f"Wallet entry obtained/created with ID: {wallet_id} for {created_wallet_name}")
                            updated = settings_manager.update_settings({'active_wallet_id': wallet_id})
                            if updated:
                                logger.info(f"Active wallet set to wallet_id: {wallet_id} in database.")
                            else:
                                logger.error(f"Failed to set active wallet in database for wallet_id: {wallet_id}.")
                        else:
                            logger.error(f"Failed to get or create wallet entry in database for {created_wallet_name}.")
                    else:
                        logger.error("Failed to get WalletManager or SettingsManager from db_instance for create_wallet.")
                except Exception as db_exc:
                    logger.error(f"Database operation failed after wallet creation for {wallet_file_path.stem}: {db_exc}", exc_info=True)
            else:
                logger.warning("Database instance not available. Skipping wallet DB operations for create_wallet.")

            # Ensure a statistics entry exists for the new wallet (if possible)
            if self.db_instance and getattr(self.wallet, 'wallet_id', None) is not None:
                try:
                    statistics_manager = self.db_instance.get_statistics_manager()
                    if statistics_manager:
                        statistics_manager.ensure_statistics_entry(self.wallet.wallet_id)
                    else:
                        logger.error("StatisticsManager unavailable; statistics entry not ensured for new wallet.")
                except Exception as stats_exc:
                    logger.error(f"Failed to ensure statistics entry for wallet_id {self.wallet.wallet_id}: {stats_exc}", exc_info=True)

            # Manage balance service
            if not self.balance_service:
                logger.debug("Attempting to initialize new WalletBalanceService for created wallet.")
                if self.db_instance:
                    balance_manager_instance = self.db_instance.get_balance_manager()
                    if balance_manager_instance:
                        # Get icon cache service from main window
                        icon_cache_service = getattr(self.main_window, 'icon_cache_service', None) if self.main_window else None
                        
                        self.balance_service = WalletBalanceService(
                            wallet=self.wallet, 
                            balance_manager=balance_manager_instance,
                            icon_cache_service=icon_cache_service,
                            service_coordinator=self.service_coordinator  # NEW: For coordination
                        )
                        logger.info("WalletBalanceService initialized with task coordination.")
                        self.balance_service.balance_updated.connect(lambda msg: self.handle_balance_service_update(msg, is_error=False))
                        self.balance_service.error_occurred.connect(lambda msg: self.handle_balance_service_update(msg, is_error=True))
                        if self.service_manager:
                            self.service_manager.register_service(self.balance_service)
                        else:
                            logger.debug("No ServiceManager, starting balance service directly.")
                            self.balance_service.start()
                    else:
                        logger.error("Failed to get BalanceManager from db_instance. WalletBalanceService not created for created wallet.")
                else:
                    logger.error("db_instance is None. WalletBalanceService not created for created wallet.")
            elif self.balance_service: # If service exists, just update its wallet
                logger.debug("Existing WalletBalanceService found, setting new wallet for created wallet.")
                self.balance_service.set_wallet(self.wallet)
            else:
                logger.error("BalanceService could not be initialized or found for created wallet.")

            if self.balance_service and getattr(self.balance_service, "balance_manager", None):
                try:
                    self._render_balances_from_manager()
                except Exception as render_exc:
                    logger.warning(f"Initial balance render failed after wallet creation: {render_exc}", exc_info=True)
                    self.update_balance_display("No funds detected in this wallet yet.")
            else:
                self.update_balance_display("No funds detected in this wallet yet.")
            self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.setVisible(True)

            # Store the password used to create (for change detection)
            self._loaded_password = password

            self.wallet_loaded.emit(self.wallet)  # Notify that wallet is created
            wallet_id_for_log = getattr(self.wallet, 'wallet_id', 'unknown')
            logger.info(f"create_wallet signal emitted for {self.wallet.public_address} (ID: {wallet_id_for_log})")

        except Exception as e:
            logger.error(f"Failed to create or initialize wallet: {e}", exc_info=True)
            QMessageBox.critical(self, "Wallet Creation Failed", f"Could not create or initialize the wallet: {str(e)}")
            self.wallet = None 
            if self.balance_service:
                if self.service_manager and hasattr(self.service_manager, 'unregister_service'):
                    self.service_manager.unregister_service(self.balance_service)
                elif hasattr(self.balance_service, 'stop'):
                    self.balance_service.stop()
                self.balance_service = None
            self.update_balance_display("No wallet loaded")
        except Exception as e:
            logger.error(f"Failed to import wallet: {e}")
            self.show_message(f"Failed to import wallet: {e}")


    def import_wallet(self):
        """Import a wallet from a 24-word seed phrase."""
        logger.debug("Import wallet button clicked")
        
        # Create custom dialog with scan option
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Wallet from Seed Phrase")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Enter your 24-word seed phrase below. (space separated)...\n"
            "\n• Import wallet: You may import a wallet you previously created with Radbot,\n" 
            "or even import one you created with the official Radix Mobile wallet.\n"
            "\n• Scan for Mobile Wallets: Searches indices 0-20 for funded wallets."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Seed phrase input
        seed_input = QTextEdit()
        seed_input.setPlaceholderText("Enter 24-word seed phrase (space separated)...")
        seed_input.setMaximumHeight(100)
        layout.addWidget(seed_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        import_btn = QPushButton("Import Directly")
        scan_btn = QPushButton("Scan for Mobile Wallets")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addWidget(import_btn)
        button_layout.addWidget(scan_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        result = {"action": None, "seed_phrase": None}
        
        def on_import():
            result["action"] = "import"
            result["seed_phrase"] = seed_input.toPlainText()
            dialog.accept()
        
        def on_scan():
            result["action"] = "scan"
            result["seed_phrase"] = seed_input.toPlainText()
            dialog.accept()
        
        import_btn.clicked.connect(on_import)
        scan_btn.clicked.connect(on_scan)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() != QDialog.Accepted:
            logger.info("Wallet import cancelled by user.")
            return
        
        seed_phrase = result["seed_phrase"].strip()
        if not seed_phrase:
            logger.info("Wallet import cancelled: No seed phrase entered.")
            return
        
        words = seed_phrase.split()
        if len(words) != 24:
            self.show_message("Seed phrase must be exactly 24 words.")
            return

        password = self._require_unlock_password()
        if not password:
            logger.info("Wallet import cancelled: Password not provided.")
            return
        
        # Handle scan vs direct import
        if result["action"] == "scan":
            account_index = self._scan_for_mobile_wallet(seed_phrase, password)
            if account_index is None:
                return  # Scan cancelled or failed
        else:
            account_index = 1  # Default account index

        default_path = USER_DATA_DIR / "radbot_imported_wallet.json"
        file_path_str, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Imported Wallet As", 
            str(default_path),
            "JSON Files (*.json)"
        )
        if not file_path_str:
            logger.info("Wallet import cancelled by user (no file selected for saving).")
            return
        
        imported_wallet_file_path = Path(file_path_str)

        try:
            # Create the wallet instance with the found/selected account index
            self.wallet = RadixWallet(imported_wallet_file_path, password, account_index=account_index)
            self.wallet.wallet_id = None  # Initialize wallet_id before any operations
            priv_key_bytes = self.wallet.derive_private_key_from_seed(seed_phrase)
            self.wallet.import_wallet(priv_key_bytes)  # This saves the wallet file with the imported key
            
            # Security: Clear seed phrase from memory immediately after use
            seed_phrase = None
            priv_key_bytes = None
            logger.debug("Seed phrase and private key bytes cleared from memory after import")

            # Database interaction - BEFORE emitting signals or initializing services
            if self.db_instance:
                try:
                    imported_wallet_name = imported_wallet_file_path.stem
                    wallet_manager = self.db_instance.get_wallet_manager()
                    settings_manager = self.db_instance.get_settings_manager()
                    if wallet_manager and settings_manager:
                        # Store relative path for portability
                        relative_path = self._get_relative_wallet_path(imported_wallet_file_path)
                        wallet_id = wallet_manager.get_or_create_wallet_entry(
                            imported_wallet_name,
                            self.wallet.public_address,
                            relative_path
                        )
                        if wallet_id:
                            self.wallet.wallet_id = wallet_id  # Set wallet_id immediately
                            logger.info(f"Wallet entry obtained/created with ID: {wallet_id} for {imported_wallet_name}")
                            updated = settings_manager.update_settings({'active_wallet_id': wallet_id})
                            if updated:
                                logger.info(f"Active wallet set to wallet_id: {wallet_id} in database.")
                            else:
                                logger.error(f"Failed to set active wallet ID: {wallet_id} in database.")
                        else:
                            logger.error(f"Failed to get or create wallet entry for {imported_wallet_name}.")
                    else:
                        logger.error("Failed to get WalletManager or SettingsManager from db_instance for import_wallet.")
                except Exception as db_exc:
                    logger.error(f"Database error during import_wallet for {imported_wallet_name}: {db_exc}", exc_info=True)
            else:
                logger.warning("db_instance not available. Skipping DB operations for import_wallet.")

            # Ensure a statistics entry exists for the imported wallet (after wallet_id is set)
            if self.db_instance and self.wallet.wallet_id is not None:
                try:
                    statistics_manager = self.db_instance.get_statistics_manager()
                    if statistics_manager:
                        statistics_manager.ensure_statistics_entry(self.wallet.wallet_id)
                    else:
                        logger.error("StatisticsManager unavailable; statistics entry not ensured for imported wallet.")
                except Exception as stats_exc:
                    logger.error(f"Failed to ensure statistics entry for wallet_id {self.wallet.wallet_id}: {stats_exc}", exc_info=True)

            self.ui.WalletTabMainSelectWalletInputText.setText(str(imported_wallet_file_path))
            self.ui.WalletTabMainCurrentAddressStatusLabel.setText(f"{self.wallet.public_address}")
            self.show_message("Wallet imported and saved successfully!")
            logger.info(f"Wallet imported: {self.wallet.public_address} and saved to {imported_wallet_file_path}")

            # Manage balance service
            if not self.balance_service:
                logger.debug("Attempting to initialize new WalletBalanceService for imported wallet.")
                if self.db_instance:
                    balance_manager_instance = self.db_instance.get_balance_manager()
                    if balance_manager_instance:
                        balance_manager_instance.wallet = self.wallet
                        
                        # Get icon cache service from main window
                        icon_cache_service = getattr(self.main_window, 'icon_cache_service', None) if self.main_window else None
                        
                        self.balance_service = WalletBalanceService(
                            wallet=self.wallet, 
                            balance_manager=balance_manager_instance,
                            icon_cache_service=icon_cache_service,
                            service_coordinator=self.service_coordinator  # NEW: For coordination
                        )
                        logger.info("WalletBalanceService initialized with task coordination for imported wallet.")
                        self.balance_service.balance_updated.connect(lambda msg: self.handle_balance_service_update(msg, is_error=False))
                        self.balance_service.error_occurred.connect(lambda msg: self.handle_balance_service_update(msg, is_error=True))
                        if self.service_manager:
                            self.service_manager.register_service(self.balance_service)
                        else:
                            logger.debug("No ServiceManager, starting balance service directly for imported wallet.")
                            self.balance_service.start()
                    else:
                        logger.error("Failed to get BalanceManager from db_instance. WalletBalanceService not created for imported wallet.")
                else:
                    logger.error("db_instance is None. WalletBalanceService not created for imported wallet.")
            elif self.balance_service:
                logger.debug("Existing WalletBalanceService found, setting new wallet for imported wallet.")
                self.balance_service.set_wallet(self.wallet)
            else:
                logger.error("BalanceService could not be initialized or found for imported wallet.")

            if self.balance_service and getattr(self.balance_service, "balance_manager", None):
                try:
                    # Show cached balances immediately
                    logger.info("Rendering cached balances from database after import")
                    self._render_balances_from_manager()
                except Exception as render_exc:
                    logger.warning(f"Failed to render cached balances after import: {render_exc}", exc_info=True)
                    self.update_balance_display("No funds detected in this wallet yet.")
                
                # Trigger background refresh to get latest balances
                try:
                    logger.info("Triggering background balance refresh after wallet import")
                    self.schedule_balance_refresh(delay_ms=0)
                except Exception as e:
                    logger.warning(f"Failed to trigger balance refresh: {e}")
            else:
                self.update_balance_display("No funds detected in this wallet yet.")
            self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon.setVisible(True)

            # Store the password used to import (for change detection)
            self._loaded_password = password

            self.wallet_loaded.emit(self.wallet)
            wallet_id_for_log = getattr(self.wallet, 'wallet_id', 'unknown')
            logger.info(f"import_wallet signal emitted for {self.wallet.public_address} (ID: {wallet_id_for_log})")

        except Exception as e:
            logger.error(f"Failed to import or initialize wallet: {e}", exc_info=True)
            QMessageBox.critical(self, "Wallet Import Failed", f"Could not import or initialize the wallet: {str(e)}")
            # Use the centralized cleanup method on failure
            self.cleanup_wallet_resources_on_failure()

    def _init_ui_elements(self):
        """Initialize specific UI elements, styles, and states."""
        # Initialize the new balance display (ScrollArea based)
        self.init_balance_display()  # Setup the balance scroll area
        self.ui.WalletTabMainWalletBalancesScrollArea.setVisible(True)  # Ensure scroll area is visible

        # Set pointer cursor on QR code icon for better UX
        qr_icon = self.ui.WalletTabMainCurrentWalletAddressQRCodeIcon
        qr_icon.setCursor(Qt.PointingHandCursor)
        qr_icon.installEventFilter(self)  # For hover effect to show QR code
        qr_icon.setVisible(False)  # Initially hidden

        # Setup for password fields
        if hasattr(self.ui, 'WalletTabMainWalletPasswordUnlockInput'):
            self.ui.WalletTabMainWalletPasswordUnlockInput.setEchoMode(QLineEdit.Password)
        else:
            logger.warning("'WalletTabMainWalletPasswordUnlockInput' not found in UI.")

        if hasattr(self.ui, 'WalletTabMainWalletPasswordWithdrawInput'):
            self.ui.WalletTabMainWalletPasswordWithdrawInput.setEchoMode(QLineEdit.Password)
        else:
            logger.warning("'WalletTabMainWalletPasswordWithdrawInput' not found in UI.")

        # Initial state for some labels
        self.ui.WalletTabMainCurrentAddressStatusLabel.setText("Not found. Create, load or import a wallet below.")
        self.ui.WalletTabMainCurrentAddressStatusLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def show_message(self, message: str):
        """Show an informational message box."""
        QMessageBox.information(self, "Information", message)


    def _render_balances_from_manager(self):
        """Renders balances from BalanceManager into the scroll area."""
        logger.debug("Rendering balances from manager into ScrollArea.")
        self._clear_balance_layout(save_withdrawal_amounts=True)  # Preserve withdrawal amounts during refresh

        if not self.wallet:
            logger.warning("Attempted to render balances but no wallet is loaded.")
            placeholder = QLabel("No wallet loaded. Balances cannot be displayed.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("placeholder_text")
            self.balance_layout.addWidget(placeholder)
            return

        try:
            all_balances = []
            if self.balance_service and self.balance_service.balance_manager:
                # Check if balances have been loaded (not just initialized)
                last_update = self.balance_service.balance_manager.get_last_update_time()
                if last_update is None:
                    logger.info("Balances not yet loaded from network, showing loading state")
                    placeholder = QLabel("Loading balances from network...")
                    placeholder.setAlignment(Qt.AlignCenter)
                    placeholder.setObjectName("placeholder_text")
                    self.balance_layout.addWidget(placeholder)
                    return
                
                # Get all balances from the balance manager
                balances_dict = self.balance_service.balance_manager.get_all_balances()
                all_balances = list(balances_dict.values())
                logger.debug(f"Retrieved {len(all_balances)} balances from manager")
                logger.debug(f"Balances from manager for rendering: {all_balances}")
            else:
                logger.warning("Balance service or manager not available to fetch balances.")

            if not all_balances:
                logger.info("No balances to display in ScrollArea (all_balances is empty or None).")
                placeholder = QLabel("No tokens found or balances unavailable.")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setObjectName("placeholder_text")
                self.balance_layout.addWidget(placeholder)
                return # Early exit if no balances

            # Sort balances: XRD first, then by symbol alphabetically
            all_balances.sort(key=lambda b: (b['symbol'] != 'XRD', b['symbol']))

            for balance_data in all_balances:
                try:
                    token_name = balance_data.get('name', 'Unknown')
                    symbol = balance_data.get('symbol', 'N/A')
                    amount_float = float(balance_data.get('available', 0))
                    token_rri = balance_data.get('rri', '')
                    divisibility = balance_data.get('divisibility', 18)
                    icon_path = balance_data.get('icon_local_path')
                    
                    token_widget = TokenDisplayWidget(
                        token_name=token_name,
                        token_symbol=symbol,
                        token_amount=amount_float,
                        token_rri=token_rri,
                        divisibility=divisibility,
                        icon_local_path=icon_path,
                        parent=self
                    )
                    # Connect Max button signal
                    token_widget.max_clicked.connect(self._handle_max_withdraw)
                    
                    # Restore previously entered withdrawal amount if it exists
                    if hasattr(self, '_saved_withdrawal_amounts') and token_rri in self._saved_withdrawal_amounts:
                        saved_text = self._saved_withdrawal_amounts[token_rri]
                        # Restore exact text user entered (preserves format like "100" not "100.00000000")
                        token_widget.set_withdraw_amount_text(saved_text)
                        logger.debug(f"Restored withdrawal amount for {symbol}: {saved_text}")
                    
                    self.balance_layout.addWidget(token_widget)
                    logger.debug(f"Created TokenDisplayWidget for {symbol} with amount {amount_float}")
                except ValueError as ve:
                    logger.error(f"ValueError converting balance for {symbol}: {ve}")
                except Exception as e:
                    logger.error(f"Error creating TokenDisplayWidget for {symbol}: {e}", exc_info=True)
            
            spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self.balance_layout.addItem(spacer)

        except Exception as e:
            logger.error(f"Error rendering balances from manager: {e}", exc_info=True)
            self._clear_balance_layout(save_withdrawal_amounts=False) # Clear again in case of partial render
            error_label = QLabel(f"Error displaying balances: {e}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setProperty("class", "status_error")
            self.balance_layout.addWidget(error_label)

        # Initial state for some labels
        # self.ui.WalletTabMainCurrentAddressStatusLabel.setText("N/A")
        # self.ui.WalletTabMainCurrentAddressStatusLabel.setText("No wallet loaded.")
        # self.ui.WalletTabMainCurrentAddressStatusLabel.setStyleSheet("color: #888;")

        # Hide QR code popup initially
        if self.wallet_qr_popup is None:
            self.wallet_qr_popup = WalletQRCodeWindow(self)
        self.wallet_qr_popup.hide()
        self.update_balance_display("Loading balances...") # Call after init_balance_display - message triggers keep-existing-balances logic

    def _handle_max_withdraw(self, token_rri: str):
        """Handle Max button click for a specific token"""
        if not self.balance_layout:
            return
        
        # Find the widget for this token
        target_widget = None
        for i in range(self.balance_layout.count()):
            widget = self.balance_layout.itemAt(i).widget()
            if isinstance(widget, TokenDisplayWidget) and widget.token_rri == token_rri:
                target_widget = widget
                break
        
        if not target_widget:
            return
        
        # For non-XRD tokens, just set to balance
        if token_rri != "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd":
            target_widget.set_withdraw_amount(float(target_widget.balance))
            logger.info(f"Set max withdraw amount for {target_widget.token_symbol}: {target_widget.balance}")
            return
        
        # For XRD, we need to account for transaction fees
        # Calculate the fee based on current withdrawal amounts
        try:
            # Build transfers dictionary with current non-XRD withdrawal amounts
            transfers_for_preview = {}
            for i in range(self.balance_layout.count()):
                widget = self.balance_layout.itemAt(i).widget()
                if isinstance(widget, TokenDisplayWidget):
                    try:
                        amount = Decimal(widget.get_withdraw_amount().as_str())
                        if amount > 0 and widget.token_rri != token_rri:  # Don't include XRD itself yet
                            transfers_for_preview[widget.token_rri] = widget.get_withdraw_amount()
                    except:
                        pass
            
            current_wallet = self.wallet
            if not current_wallet:
                return
            
            # Get withdraw address for fee calculation
            withdraw_address = self.ui.WalletTabMainWithdrawAddressTextInput.toPlainText().strip()
            if not withdraw_address:
                # No destination - use conservative estimate
                xrd_balance = Decimal(str(target_widget.balance))
                max_xrd = max(Decimal("0"), xrd_balance - Decimal("0.5"))
                formatted_amount = f"{max_xrd:.8f}".rstrip('0').rstrip('.')
                target_widget.set_withdraw_amount(float(formatted_amount))
                logger.info(f"Set max XRD withdraw (no address): {formatted_amount} (balance - 0.5 XRD buffer)")
                return
            
            # Two-pass fee refinement for near-zero dust:
            # Pass 1: raw fee (no multiplier) to learn the actual network cost
            # Pass 2: exact amounts with tight 2% safety margin for validation
            rtb = RadixTransactionBuilder(current_wallet)
            xrd_balance = Decimal(str(target_widget.balance))
            
            # PASS 1: Get raw network fee with no safety multiplier
            rough_estimate = max(Decimal("0"), xrd_balance - Decimal("0.5"))
            transfers_pass1 = dict(transfers_for_preview)
            transfers_pass1[token_rri] = RETDecimal(str(rough_estimate))
            
            raw_fee = rtb.get_withdrawal_fee_preview(
                destination_address=withdraw_address,
                transfers=transfers_pass1,
                safety_multiplier=Decimal('1')
            )
            
            if raw_fee is None or raw_fee < 0:
                logger.warning("Pass 1 fee preview failed, using 0.5 XRD buffer")
                buffer = Decimal("0.5")
                max_xrd = max(Decimal("0"), xrd_balance - buffer)
                formatted_amount = f"{max_xrd:.8f}".rstrip('0').rstrip('.')
                target_widget.set_withdraw_amount(float(formatted_amount))
                self._cached_withdrawal_fee = buffer
                logger.info(f"Set max XRD withdraw (fallback): {formatted_amount} (balance: {xrd_balance}, buffer: {buffer})")
                return
            
            raw_fee_decimal = Decimal(str(raw_fee))
            logger.info(f"Max withdraw pass 1 — raw network fee: {raw_fee_decimal} XRD")
            
            # PASS 2: Refine with exact max amount and tight safety multiplier
            candidate_max = max(Decimal("0"), xrd_balance - raw_fee_decimal - Decimal("0.005"))
            transfers_pass2 = dict(transfers_for_preview)
            transfers_pass2[token_rri] = RETDecimal(str(candidate_max))
            
            tight_fee = rtb.get_withdrawal_fee_preview(
                destination_address=withdraw_address,
                transfers=transfers_pass2,
                safety_multiplier=Decimal('1.10')
            )
            
            if tight_fee is not None and tight_fee > 0:
                buffer = Decimal(str(tight_fee))
                logger.info(f"Max withdraw pass 2 — tight fee: {buffer} XRD (10% safety)")
            else:
                # Pass 2 failed, use pass 1 result with small fixed buffer
                buffer = raw_fee_decimal + Decimal("0.01")
                logger.warning(f"Pass 2 failed, using raw fee + 0.01: {buffer} XRD")
            
            max_xrd = max(Decimal("0"), xrd_balance - buffer)
            safe_max_xrd = max_xrd - Decimal("0.00000001")
            formatted_amount = f"{safe_max_xrd:.8f}".rstrip('0').rstrip('.')
            target_widget.set_withdraw_amount(float(formatted_amount))
            
            # Store the calculated fee and token set so we can detect stale cache on withdraw
            self._cached_withdrawal_fee = buffer
            self._cached_withdrawal_tokens = set(transfers_for_preview.keys())  # Non-XRD tokens at time of Max
            
            estimated_dust = buffer - raw_fee_decimal
            logger.info(f"Set max XRD withdraw: {formatted_amount} (balance: {xrd_balance}, fee buffer: {buffer}, est. dust: ~{estimated_dust:.6f} XRD)")
            
        except Exception as e:
            logger.error(f"Error calculating max XRD withdrawal: {e}", exc_info=True)
            # Fallback to conservative estimate
            xrd_balance = Decimal(str(target_widget.balance))
            max_xrd = max(Decimal("0"), xrd_balance - Decimal("0.5"))
            formatted_amount = f"{max_xrd:.8f}".rstrip('0').rstrip('.')
            target_widget.set_withdraw_amount(float(formatted_amount))
            logger.warning(f"Error in max XRD calculation, using conservative: {formatted_amount}")

    def handle_withdraw(self):
        """Handle withdraw functionality."""
        if not self.wallet:
            self.show_message("Please load a wallet first")
            return

        current_wallet = self.wallet
        withdraw_password = self._require_withdraw_password()
        if not withdraw_password:
            logger.warning("Withdrawal attempt blocked: password not provided.")
            return
        if not self.wallet.verify_password(withdraw_password):
            logger.error("Withdrawal attempt blocked: incorrect password provided.")
            self._flash_line_edit(self.ui.WalletTabMainWalletPasswordWithdrawInput)
            QMessageBox.critical(self, "Incorrect Password", "The password entered for withdrawal is incorrect.")
            self.ui.WalletTabMainWalletPasswordWithdrawInput.clear()
            return

        withdraw_address = self.ui.WalletTabMainWithdrawAddressTextInput.toPlainText().strip()
        if not withdraw_address:
            self.show_message("Please enter a valid withdraw address")
            return
        withdrawals_to_review = []
        transfers_for_preview = {}
        if self.balance_layout:
            for i in range(self.balance_layout.count()):
                widget = self.balance_layout.itemAt(i).widget()
                if isinstance(widget, TokenDisplayWidget):
                    amount_to_withdraw_dec = Decimal(widget.get_withdraw_amount().as_str())
                    logger.debug(f"Checking widget {widget.token_symbol}: amount={amount_to_withdraw_dec}, balance={widget.balance}")
                    # Validate against the widget's stored balance with small tolerance for float precision
                    balance_dec = Decimal(str(widget.balance))
                    # Allow up to 0.00000001 difference for float rounding issues
                    if amount_to_withdraw_dec > 0 and amount_to_withdraw_dec <= balance_dec + Decimal("0.00000001"):
                        rri = widget.token_rri
                        amount_val = widget.get_withdraw_amount() # Get RETDecimal for manifest
                        logger.info(f"Adding {widget.token_symbol} to withdrawal: {amount_to_withdraw_dec}")
                        withdrawals_to_review.append({
                            'symbol': widget.token_symbol,
                            'rri': rri,
                            'amount': amount_val,
                            'name': widget.token_name,
                            'icon_local_path': widget.icon_local_path
                        })
                        # Also prepare the dictionary for the fee preview
                        transfers_for_preview[rri] = amount_val
        
        logger.info(f"Total assets for withdrawal: {len(withdrawals_to_review)}")
        assets_summary = [f"{w['symbol']}={w['amount'].as_str()}" for w in withdrawals_to_review]
        logger.info(f"Assets list: {assets_summary}")

        if not withdrawals_to_review:
            self.show_message("Please enter an amount for at least one token to withdraw.")
            return

        try:
            # Create transaction builder (needed for dialog and optional preview)
            rtb = RadixTransactionBuilder(current_wallet)
            
            # Validate that user has enough XRD for the transaction
            xrd_rri = "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd"
            xrd_withdraw_amount = Decimal("0")
            xrd_balance = Decimal("0")
            
            # Get XRD withdrawal amount and balance
            for withdrawal in withdrawals_to_review:
                if withdrawal['rri'] == xrd_rri:
                    xrd_withdraw_amount = Decimal(withdrawal['amount'].as_str())
                    # Find the balance from widgets
                    for i in range(self.balance_layout.count()):
                        widget = self.balance_layout.itemAt(i).widget()
                        if isinstance(widget, TokenDisplayWidget) and widget.token_rri == xrd_rri:
                            xrd_balance = Decimal(str(widget.balance))
                            break
                    break
            
            # Smart fee calculation: only preview if necessary
            # 1. Use cached fee from Max button if token set hasn't changed
            # 2. Re-preview if tokens were added/removed since Max (cache stale)
            # 3. Skip preview if XRD withdrawal leaves enough margin (>= 1 XRD)
            # 4. Two-pass tight preview if user is withdrawing close to full balance
            need_preview = True
            display_fee = None  # Fee shown to user
            actual_fee = None   # Fee actually locked
            adjust_xrd_for_new_fee = False  # Auto-adjust XRD when Max was used but tokens changed
            
            # Check if we have a cached fee from Max button
            cached_fee = getattr(self, '_cached_withdrawal_fee', None)
            if cached_fee:
                # Compare current non-XRD token set to what was cached
                cached_tokens = getattr(self, '_cached_withdrawal_tokens', set())
                current_non_xrd_tokens = {rri for rri in transfers_for_preview.keys() if rri != xrd_rri}
                
                if cached_tokens == current_non_xrd_tokens:
                    # Cache is valid — same token set
                    display_fee = cached_fee
                    actual_fee = cached_fee
                    need_preview = False
                    logger.info(f"Using cached fee from Max button: {display_fee} XRD (tight 2% safety margin)")
                else:
                    # Token set changed since Max — cache is stale
                    added = current_non_xrd_tokens - cached_tokens
                    removed = cached_tokens - current_non_xrd_tokens
                    logger.info(f"Cached fee invalidated: tokens changed (added={len(added)}, removed={len(removed)})")
                    self._cached_withdrawal_fee = None
                    adjust_xrd_for_new_fee = True  # Will auto-adjust XRD after re-preview
            
            if need_preview and not adjust_xrd_for_new_fee:
                if xrd_withdraw_amount > 0:
                    # Check if withdrawal leaves enough XRD for fees
                    margin = xrd_balance - xrd_withdraw_amount
                    num_tokens = len(withdrawals_to_review)
                    estimated_max_fee = Decimal("0.35") + (Decimal("0.16") * Decimal(str(num_tokens - 1)))
                    safe_margin = max(estimated_max_fee * Decimal("1.2"), Decimal("1.0"))
                    
                    if margin >= safe_margin:
                        display_fee = estimated_max_fee
                        actual_fee = safe_margin
                        need_preview = False
                        logger.info(f"XRD withdrawal has safe margin ({margin} XRD >= {safe_margin} XRD for {num_tokens} tokens), showing {display_fee} XRD fee, locking {actual_fee} XRD")
                    else:
                        logger.info(f"XRD withdrawal close to balance (margin: {margin} XRD), preview needed")
                else:
                    # Not withdrawing XRD - calculate fee based on number of tokens
                    num_tokens = len(withdrawals_to_review)
                    estimated_max_fee = Decimal("0.35") + (Decimal("0.16") * Decimal(str(num_tokens - 1)))
                    safe_margin = max(estimated_max_fee * Decimal("1.2"), Decimal("1.0"))
                    display_fee = estimated_max_fee
                    actual_fee = safe_margin
                    need_preview = False
                    logger.info(f"Not withdrawing XRD, showing {display_fee} XRD fee ({num_tokens} tokens), locking {actual_fee} XRD")
            
            # Preview needed: either close-to-balance or stale cache after Max
            if need_preview:
                if adjust_xrd_for_new_fee and xrd_withdraw_amount > 0:
                    # Two-pass tight refinement (Max was used, tokens changed)
                    logger.info("Running two-pass fee refinement for stale Max cache...")
                    rough_xrd = max(Decimal("0"), xrd_balance - Decimal("0.5"))
                    pass1_transfers = dict(transfers_for_preview)
                    pass1_transfers[xrd_rri] = RETDecimal(str(rough_xrd))
                    
                    raw_fee = rtb.get_withdrawal_fee_preview(
                        destination_address=withdraw_address,
                        transfers=pass1_transfers,
                        safety_multiplier=Decimal('1')
                    )
                    
                    if raw_fee is not None and raw_fee > 0:
                        raw_fee_decimal = Decimal(str(raw_fee))
                        candidate_max = max(Decimal("0"), xrd_balance - raw_fee_decimal - Decimal("0.005"))
                        pass2_transfers = dict(transfers_for_preview)
                        pass2_transfers[xrd_rri] = RETDecimal(str(candidate_max))
                        
                        tight_fee = rtb.get_withdrawal_fee_preview(
                            destination_address=withdraw_address,
                            transfers=pass2_transfers,
                            safety_multiplier=Decimal('1.02')
                        )
                        
                        if tight_fee is not None and tight_fee > 0:
                            display_fee = Decimal(str(tight_fee))
                        else:
                            display_fee = raw_fee_decimal + Decimal("0.01")
                        actual_fee = display_fee
                        
                        # Auto-adjust XRD amount if new fee is higher
                        new_max_xrd = max(Decimal("0"), xrd_balance - actual_fee) - Decimal("0.00000001")
                        if new_max_xrd < xrd_withdraw_amount:
                            old_amount = xrd_withdraw_amount
                            xrd_withdraw_amount = new_max_xrd
                            formatted = f"{new_max_xrd:.8f}".rstrip('0').rstrip('.')
                            
                            # Update widget
                            for i in range(self.balance_layout.count()):
                                widget = self.balance_layout.itemAt(i).widget()
                                if isinstance(widget, TokenDisplayWidget) and widget.token_rri == xrd_rri:
                                    widget.set_withdraw_amount(float(formatted))
                                    break
                            
                            # Update transfers and withdrawal list
                            transfers_for_preview[xrd_rri] = RETDecimal(formatted)
                            for w in withdrawals_to_review:
                                if w['rri'] == xrd_rri:
                                    w['amount'] = RETDecimal(formatted)
                                    break
                            
                            logger.info(f"Auto-adjusted XRD: {old_amount} → {new_max_xrd} (fee increased for additional tokens)")
                        
                        self._cached_withdrawal_fee = actual_fee
                        self._cached_withdrawal_tokens = {rri for rri in transfers_for_preview.keys() if rri != xrd_rri}
                        logger.info(f"Re-calculated fee after token change: {display_fee} XRD")
                    else:
                        num_tokens = len(withdrawals_to_review)
                        estimated_max_fee = Decimal("0.35") + (Decimal("0.16") * Decimal(str(num_tokens - 1)))
                        safe_margin = max(estimated_max_fee * Decimal("1.2"), Decimal("1.5"))
                        display_fee = safe_margin
                        actual_fee = safe_margin
                        logger.warning(f"Two-pass preview failed, using {safe_margin} XRD fallback for {num_tokens} tokens")
                else:
                    # Standard preview (user manually entered amount close to max, or no XRD)
                    safe_lock_fee = rtb.get_withdrawal_fee_preview(
                        destination_address=withdraw_address,
                        transfers=transfers_for_preview
                    )
                    
                    if safe_lock_fee is not None and safe_lock_fee > 0:
                        display_fee = Decimal(safe_lock_fee)
                        actual_fee = Decimal(safe_lock_fee)
                        logger.info(f"Preview fee for close-to-balance withdrawal: {display_fee} XRD")
                    else:
                        num_tokens = len(withdrawals_to_review)
                        estimated_max_fee = Decimal("0.35") + (Decimal("0.16") * Decimal(str(num_tokens - 1)))
                        safe_margin = max(estimated_max_fee * Decimal("1.2"), Decimal("1.5"))
                        display_fee = safe_margin
                        actual_fee = safe_margin
                        logger.warning(f"Preview failed, using {safe_margin} XRD fallback for {num_tokens} tokens")
            
            # Final check: ensure we have fee values
            if display_fee is None:
                num_tokens = len(withdrawals_to_review)
                estimated_max_fee = Decimal("0.35") + (Decimal("0.16") * Decimal(str(num_tokens - 1)))
                safe_margin = max(estimated_max_fee * Decimal("1.2"), Decimal("1.0"))
                display_fee = estimated_max_fee
                actual_fee = safe_margin
                logger.warning(f"No fee calculated, using estimated {display_fee} XRD display, {actual_fee} XRD lock for {num_tokens} tokens")
            
            # Check if withdrawing XRD and if it leaves enough for fees
            # Use actual_fee for validation (the higher amount we'll actually lock)
            if xrd_withdraw_amount > 0:
                required_total = xrd_withdraw_amount + actual_fee
                # Allow tiny tolerance for decimal precision (0.00000001 XRD)
                if required_total > xrd_balance + Decimal("0.00000001"):
                    shortage = required_total - xrd_balance
                    QMessageBox.warning(
                        self,
                        "Insufficient XRD",
                        f"Cannot withdraw {xrd_withdraw_amount} XRD.\n\n"
                        f"Required: {xrd_withdraw_amount} XRD (withdrawal) + {display_fee} XRD (fee) = {required_total} XRD\n"
                        f"Available: {xrd_balance} XRD\n"
                        f"Shortage: {shortage} XRD\n\n"
                        f"Please reduce the XRD withdrawal amount or click 'Max' to withdraw the maximum safe amount."
                    )
                    return

            # 3. Show the confirmation dialog which now handles submission
            # Pass display_fee (shown to user) and actual_fee (actually locked)
            dialog = TransactionManifestDialog(
                rtb=rtb,
                transfers_for_preview=transfers_for_preview,
                sender_address=current_wallet.public_address, 
                recipient_address=withdraw_address, 
                assets=withdrawals_to_review, 
                calculated_fee=display_fee,  # Fee displayed to user (conservative)
                actual_lock_fee=actual_fee,   # Fee actually locked (safer)
                parent=self
            )
            dialog.transaction_successful.connect(self.schedule_balance_refresh)
            dialog.exec()

        except Exception as e:
            logger.error(f"Error during withdrawal preparation: {e}", exc_info=True)
            self.show_message(f"An error occurred: {e}")
        finally:
            self.ui.WalletTabMainWalletPasswordWithdrawInput.clear()

    def schedule_balance_refresh(self, delay_ms: int = 5000):
        """
        Refresh wallet balances after an optional delay.
        
        Args:
            delay_ms: Delay in milliseconds before refresh (default 5000ms = 5 seconds).
                      Set to 0 for immediate refresh.
        """
        if not self.balance_service:
            logger.warning("Cannot refresh balances: balance service not available")
            return
        
        if delay_ms > 0:
            logger.info(f"Scheduling wallet balance refresh in {delay_ms/1000:.1f} seconds")
            QTimer.singleShot(delay_ms, self.balance_service.trigger_refresh)
        else:
            logger.info("Refreshing wallet balances immediately")
            self.balance_service.trigger_refresh()

    def export_wallet(self):
        """Allow the user to export the currently loaded wallet file to a chosen location."""
        if not self.wallet:
            QMessageBox.information(self, "Export Wallet", "Please load a wallet before attempting to export.")
            return

        password = self._require_unlock_password()
        if not password:
            logger.warning("Wallet export cancelled: no password provided.")
            return

        if not self.wallet.verify_password(password):
            logger.error("Wallet export failed: incorrect password provided.")
            self._flash_line_edit(self.ui.WalletTabMainWalletPasswordUnlockInput)
            QMessageBox.critical(self, "Export Wallet", "Incorrect wallet password. Export aborted.")
            return

        source_path = Path(self.wallet.wallet_file) if hasattr(self.wallet, 'wallet_file') else None
        if not source_path or not source_path.exists():
            QMessageBox.critical(self, "Export Wallet", "Wallet file could not be located on disk.")
            logger.error("Wallet export failed: wallet file path missing or does not exist.")
            return

        default_path = USER_DATA_DIR / source_path.name
        destination_path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export Wallet File",
            str(default_path),
            "JSON Files (*.json)"
        )

        if not destination_path_str:
            logger.info("Wallet export cancelled by user.")
            return

        destination_path = Path(destination_path_str)

        try:
            shutil.copy2(source_path, destination_path)
            QMessageBox.information(self, "Export Wallet", f"Wallet exported successfully to:\n{destination_path}")
            logger.info(f"Wallet exported to {destination_path}")
        except Exception as e:
            logger.error(f"Failed to export wallet to {destination_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Wallet", f"Failed to export wallet: {e}")

    def lock_wallet(self):
        """Locks the current wallet and resets the UI to its initial state."""
        if self.wallet:
            self.wallet = None
            self.cleanup_wallet_resources_on_failure()
            logger.info("Wallet has been locked.")
            self.wallet_unloaded.emit()
