import logging
import os
import time
from PySide6.QtCore import Qt, Signal, QObject, QRunnable, QThreadPool, QTimer
from PySide6.QtGui import QPixmap, QMovie, QCursor, QClipboard
from PySide6.QtWidgets import QApplication
from typing import List, Dict, Any, Optional
from radix_engine_toolkit import Decimal as RETDecimal, RadixEngineToolkitError
from decimal import Decimal as StdDecimal # Standard Python Decimal for formatting
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                               QPushButton, QDialogButtonBox, QWidget, QSizePolicy, QScrollArea, QStackedWidget)
from config.app_config import get_absolute_path
from core.radix_network import RadixNetwork, RadixNetworkError
from core.transaction_builder import RadixTransactionBuilder

# Configure a logger for this module to ensure its messages are captured
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class WorkerSignals(QObject):
    '''Defines the signals available from a running worker thread.'''
    finished = Signal()
    error = Signal(str, str) # Error message, optional tx_id
    result = Signal(str) # For the transaction ID

class TransactionSubmitWorker(QRunnable):
    '''Worker thread for submitting a transaction.'''
    def __init__(self, rtb: RadixTransactionBuilder, transfers: dict, destination_address: str, message: Optional[str], fee_to_lock: Optional[RETDecimal] = None):
        super().__init__()
        self.rtb = rtb
        self.transfers = transfers
        self.destination_address = destination_address
        self.message = message
        self.fee_to_lock = fee_to_lock
        self.signals = WorkerSignals()

    def run(self):
        try:
            notarized_transaction, _, _ = self.rtb.create_notarized_transaction_for_submission(
                sender_address=self.rtb.wallet.public_address,
                recipient_address=self.destination_address,
                transfers=self.transfers,
                message=self.message,
                fee_to_lock=self.fee_to_lock
            )
            
            # Compile and submit the transaction
            compiled_tx = notarized_transaction.to_payload_bytes().hex()
            logger.debug(f"Submitting compiled_tx: {compiled_tx}")

            rn = RadixNetwork()
            submission_response = rn.submit_transaction(compiled_tx)
            logger.info(f"Submission response: {submission_response}")

            if not submission_response or submission_response.get('duplicate'):
                tx_id = notarized_transaction.intent_hash().as_str()
                error_msg = f"Transaction already submitted. TxID: {tx_id}" if submission_response.get('duplicate') else "Submission failed: Unknown error."
                self.signals.error.emit(error_msg)
                return

            tx_id = notarized_transaction.intent_hash().as_str()
            start_time = time.time()
            timeout = 60  # 60 seconds

            while time.time() - start_time < timeout:
                try:
                    status_response = rn.get_transaction_status(tx_id)
                    logger.debug(f"Full status response: {status_response}")
                    
                    # Check multiple possible status locations in response
                    status = None
                    if isinstance(status_response, dict):
                        # Try different possible response formats
                        status = status_response.get('status')
                        if not status and 'intent_status' in status_response:
                            status = status_response.get('intent_status')
                        if not status and 'transaction_status' in status_response:
                            status = status_response.get('transaction_status')
                    
                    logger.info(f"Transaction {tx_id} status: {status}")
                    
                    if not status:
                        logger.warning(f"No status field found in response: {status_response}")
                        time.sleep(2)
                        continue
                    
                    # Check for success (case-insensitive)
                    status_lower = str(status).lower()
                    if 'success' in status_lower or status_lower == 'committedsuccess':
                        logger.info(f"Transaction {tx_id} committed successfully!")
                        try:
                            self.signals.result.emit(tx_id)
                            logger.debug(f"SUCCESS signal emitted for tx {tx_id}")
                            # Small delay to ensure Qt processes the signal before thread exits
                            time.sleep(0.1)
                        except Exception as emit_error:
                            logger.error(f"CRITICAL: Failed to emit success signal: {emit_error}", exc_info=True)
                            # Try again with error signal as fallback to unblock UI
                            try:
                                self.signals.error.emit(f"Transaction succeeded but UI notification failed: {tx_id}", tx_id)
                                time.sleep(0.1)
                            except:
                                pass
                        return
                    elif 'failure' in status_lower or 'reject' in status_lower:
                        logger.error(f"Transaction {tx_id} failed with status: {status}")
                        try:
                            self.signals.error.emit(f"Transaction failed with status: {status}", tx_id)
                            logger.debug(f"ERROR signal emitted for tx {tx_id}")
                        except Exception as emit_error:
                            logger.error(f"CRITICAL: Failed to emit error signal: {emit_error}", exc_info=True)
                        return
                    # If 'Pending' or other, continue polling
                    elapsed = time.time() - start_time
                    logger.debug(f"Transaction pending, elapsed: {elapsed:.1f}s / {timeout}s")
                    time.sleep(2)  # Wait 2 seconds before next poll
                except RadixNetworkError as e:
                    logger.warning(f"Polling for tx status failed: {e}")
                    time.sleep(2) # Wait before retrying poll
                except Exception as e:
                    logger.error(f"Unexpected error polling status: {e}", exc_info=True)
                    time.sleep(2)

            elapsed_time = time.time() - start_time
            logger.error(f"Transaction {tx_id} timed out after {elapsed_time:.1f}s. Last known status: {status if 'status' in locals() else 'Unknown'}")
            self.signals.error.emit(f"Transaction timed out after {elapsed_time:.0f} seconds.", tx_id if 'tx_id' in locals() else '')

        except Exception as e:
            logger.error(f"Error submitting transaction: {e}", exc_info=True)
            self.signals.error.emit(str(e), '')

class AssetRowWidget(QFrame):
    def __init__(self, asset_info, parent=None):
        super().__init__(parent)
        self.asset_info = asset_info
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # AssetRowWidget styling now in dark_theme.qss

        # Log asset_info at the beginning of setup_ui
        logger.debug(f"AssetRowWidget setup_ui - asset_info: {self.asset_info}")

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(30, 30)
        
        icon_local_path = self.asset_info.get('icon_local_path')
        
        if icon_local_path:
            icon_file_path = get_absolute_path(icon_local_path)
        else:
            icon_file_path = get_absolute_path('images/default_token_icon.png')

        if os.path.exists(icon_file_path):
            pixmap = QPixmap(icon_file_path)
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                # Icon styling handled by theme
            else:
                logger.warning(f"Failed to load icon: {icon_file_path}, pixmap is null.")
                self._set_default_icon_style()
        else:
            logger.warning(f"Icon file not found: {icon_file_path}")
            self._set_default_icon_style()
            
        layout.addWidget(self.icon_label)

        # Asset Name/Symbol
        name_symbol = self.asset_info.get('name', self.asset_info.get('symbol', 'Unknown'))
        name_label = QLabel(name_symbol)
        name_font = name_label.font()
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        # Color handled by dialog QSS
        name_label.setMinimumWidth(80)  # Set a minimum width
        layout.addWidget(name_label)

        layout.addStretch(1)

        # Asset Amount
        asset_symbol = self.asset_info.get('symbol', '')

        amount_value = self.asset_info.get('amount')
        amount_str = "Invalid Amount"
        if isinstance(amount_value, RETDecimal):
            # Convert RETDecimal to standard Decimal for formatting, ensuring it's not overly long
            std_decimal_amount = StdDecimal(amount_value.as_str())
            # Format to a reasonable number of decimal places, e.g., 6
            amount_str = f"{std_decimal_amount.quantize(StdDecimal('0.000001'))} {asset_symbol}"
        else:
            amount_str = f"{str(amount_value)} {asset_symbol}"

        logger.debug(f"AssetRowWidget: name_symbol='{name_symbol}', formatted amount_str='{amount_str}'")
            
        amount_label = QLabel(amount_str)
        amount_font = amount_label.font()
        amount_font.setPointSize(12)
        amount_font.setBold(True)
        amount_label.setFont(amount_font)
        amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Color handled by dialog QSS
        amount_label.setMinimumWidth(100) # Set a minimum width
        layout.addWidget(amount_label)

        self.setLayout(layout)

    def _set_default_icon_style(self):
        logger.warning("AssetRowWidget: Setting default icon style.")
        self.icon_label.setStyleSheet("background-color: #1e293b; border-radius: 15px;")

class TransactionManifestDialog(QDialog):
    transaction_successful = Signal()

    def __init__(self, rtb: RadixTransactionBuilder, transfers_for_preview: dict, 
                 sender_address: str, recipient_address: str, assets: List[Dict[str, Any]], 
                 calculated_fee: Optional[StdDecimal] = None, actual_lock_fee: Optional[StdDecimal] = None,
                 message: str = "", parent=None):
        super().__init__(parent)
        self.rtb = rtb
        self.transfers_for_preview = transfers_for_preview
        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.assets = assets
        self.calculated_fee = calculated_fee
        self.message = message
        self.accepted = False
        self.threadpool = QThreadPool()
        self.is_success_state = False  # Track if showing success or error
        
        # Store the lock fee as RETDecimal for transaction builder
        # Use actual_lock_fee if provided (what we actually lock), otherwise use calculated_fee
        fee_for_locking = actual_lock_fee if actual_lock_fee is not None else calculated_fee
        if fee_for_locking is not None and fee_for_locking > 0:
            self.fee_to_lock = RETDecimal(str(fee_for_locking))
            logger.info(f"Fee to lock: {fee_for_locking} XRD (display: {calculated_fee} XRD)")
        else:
            self.fee_to_lock = None

        self.setWindowTitle("Confirm Transaction")
        self.setModal(True)
        # All styling now in dark_theme.qss
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Stacked widget to switch between review, processing, and result views
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # --- Page 1: Review Details ---
        self.review_widget = QWidget()
        review_layout = QVBoxLayout(self.review_widget)
        review_layout.setContentsMargins(0,0,0,0)
        review_layout.setSpacing(15)

        title_label = QLabel("Review Your Transfer")
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        review_layout.addWidget(title_label)

        # Sender Info
        sender_frame = QFrame()
        sender_frame.setObjectName("header_frame")
        sender_layout = QVBoxLayout(sender_frame)
        sender_title = QLabel("SENDER")
        sender_title.setObjectName("secondary_text")
        sender_title.setStyleSheet("font-size: 10px;")
        sender_address_label = QLabel(self.sender_address)
        sender_address_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sender_layout.addWidget(sender_title)
        sender_layout.addWidget(sender_address_label)
        review_layout.addWidget(sender_frame)

        # Receiver Info
        receiver_frame = QFrame()
        receiver_frame.setObjectName("header_frame")
        receiver_layout = QVBoxLayout(receiver_frame)
        receiver_title = QLabel("RECEIVER")
        receiver_title.setObjectName("secondary_text")
        receiver_title.setStyleSheet("font-size: 10px;")
        receiver_address_label = QLabel(self.recipient_address)
        receiver_address_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        receiver_layout.addWidget(receiver_title)
        receiver_layout.addWidget(receiver_address_label)
        review_layout.addWidget(receiver_frame)

        # Assets Section
        assets_title_label = QLabel("ASSETS TO TRANSFER")
        assets_title_label.setObjectName("secondary_text")
        assets_title_label.setStyleSheet("font-size: 10px; padding-top: 5px;")
        review_layout.addWidget(assets_title_label)

        # Scrollable area for assets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Scroll area styling from dark_theme.qss
        scroll_content = QWidget()
        self.assets_layout = QVBoxLayout(scroll_content)
        self.assets_layout.setSpacing(5)
        scroll_area.setWidget(scroll_content)
        review_layout.addWidget(scroll_area)

        if not self.assets:
            no_assets_label = QLabel("No assets selected for transfer.")
            no_assets_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.assets_layout.addWidget(no_assets_label)
        else:
            for asset in self.assets:
                asset_row = AssetRowWidget(asset)
                self.assets_layout.addWidget(asset_row)

        # Fee Section
        fee_frame = QFrame()
        fee_frame.setObjectName("footer_frame")
        fee_layout = QHBoxLayout(fee_frame)
        fee_title_label = QLabel("TRANSACTION FEE")
        fee_title_label.setStyleSheet("font-weight: bold;")
        self.fee_amount_label = QLabel()

        if self.calculated_fee is not None and self.calculated_fee >= StdDecimal("0"):
            fee_text = f"{self.calculated_fee.quantize(StdDecimal('0.000001'))} XRD"
            self.fee_amount_label.setText(fee_text)
            logger.info(f"Displaying pre-calculated fee: {fee_text}")
        else:
            self.fee_amount_label.setText("N/A")
            logger.warning("Calculated fee is not available. Displaying 'N/A'.")

        fee_layout.addWidget(fee_title_label)
        fee_layout.addStretch()
        fee_layout.addWidget(self.fee_amount_label)
        review_layout.addWidget(fee_frame)

        self.stacked_widget.addWidget(self.review_widget)

        # --- Page 2: Processing View ---
        self.processing_widget = QWidget()
        processing_layout = QVBoxLayout(self.processing_widget)
        processing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        processing_layout.setSpacing(20)

        self.loading_label = QLabel()
        # Use the Qt resource path directly, correcting the typo from 'spinnner'
        loading_gif_path = 'images/loading_spinner.gif'
        self.movie = QMovie(loading_gif_path)

        # By making the QMovie object an instance variable (self.movie), we prevent
        # it from being garbage collected. We also check if it's valid.
        if self.movie.isValid():
            self.loading_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.loading_label.setText("Loading...") # Fallback text
            print(f"Warning: Could not load or find GIF at resource path {loading_gif_path}")
        processing_layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)

        processing_text = QLabel("Submitting Transaction...")
        processing_text.setStyleSheet("font-size: 16px;")
        processing_layout.addWidget(processing_text, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.processing_widget)

        # --- Page 3: Result View ---
        self.result_widget = QWidget()
        result_layout = QVBoxLayout(self.result_widget)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.setSpacing(15)

        self.result_icon_label = QLabel()
        self.result_icon_label.setFixedSize(250, 250)
        result_layout.addWidget(self.result_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.result_message_label = QLabel()
        self.result_message_label.setWordWrap(True)
        self.result_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.addWidget(self.result_message_label)

        # TxID row with copy button
        tx_id_row = QHBoxLayout()
        tx_id_row.setSpacing(5)
        
        self.tx_id_label = QLabel()
        self.tx_id_label.setWordWrap(True)
        self.tx_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tx_id_label.setObjectName("secondary_text")
        self.tx_id_label.setStyleSheet("font-size: 10px;")
        tx_id_row.addWidget(self.tx_id_label)
        
        self.copy_tx_button = QPushButton("Copy")
        self.copy_tx_button.setObjectName("copy_button")  # Use theme styling
        self.copy_tx_button.setFixedSize(50, 24)
        self.copy_tx_button.setToolTip("Copy Transaction ID")
        self.copy_tx_button.clicked.connect(self.copy_txid_to_clipboard)
        self.copy_tx_button.hide()
        tx_id_row.addWidget(self.copy_tx_button)
        
        result_layout.addLayout(tx_id_row)

        self.stacked_widget.addWidget(self.result_widget)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox()
        self.confirm_button = self.button_box.addButton("Confirm Transfer", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        self.close_button = self.button_box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        self.close_button.hide()

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.close_button.clicked.connect(self.reject)


        self.main_layout.addWidget(self.button_box)

    def copy_txid_to_clipboard(self):
        """Copy the transaction ID to clipboard"""
        tx_text = self.tx_id_label.text()
        if tx_text and tx_text.startswith("TxID: "):
            tx_id = tx_text.replace("TxID: ", "")
            clipboard = QApplication.clipboard()
            clipboard.setText(tx_id)
            
            # Visual feedback - green for success, red for error
            if self.is_success_state:
                bg_color = "#4CAF50"
                border_color = "#45A049"
            else:
                bg_color = "#F44336"
                border_color = "#D32F2F"
            
            self.copy_tx_button.setText("Copied!")
            self.copy_tx_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    color: #FFFFFF;
                    font-size: 10px;
                    padding: 2px 6px;
                }}
            """)
            QTimer.singleShot(1500, self._reset_copy_button)
            logger.info(f"Copied TxID to clipboard: {tx_id}")
    
    def _reset_copy_button(self):
        """Reset copy button after visual feedback"""
        self.copy_tx_button.setText("Copy")
        # Return to theme styling via objectName
        self.copy_tx_button.setStyleSheet("")

    def show_result(self, is_success: bool, message: str, tx_id: Optional[str] = None):
        logger.info(f"show_result called: is_success={is_success}, tx_id={tx_id}")
        self.stacked_widget.setCurrentWidget(self.result_widget)
        self.confirm_button.hide()
        self.cancel_button.hide()
        self.close_button.show()

        if is_success:
            self.is_success_state = True
            icon_path = get_absolute_path('images/success_icon.png')
            self.result_message_label.setText(f"<b>{message}</b>")
            if tx_id:
                self.tx_id_label.setText(f"TxID: {tx_id}")
                self.tx_id_label.show()
                self.copy_tx_button.show()
            try:
                self.transaction_successful.emit()
                logger.debug("transaction_successful signal emitted from dialog")
            except Exception as sig_err:
                logger.error(f"Failed to emit transaction_successful signal: {sig_err}", exc_info=True)
        else:
            self.is_success_state = False
            icon_path = get_absolute_path('images/error_icon.png')
            self.result_message_label.setText(f"<b>Transaction Failed</b><br>{message}")
            if tx_id:
                self.tx_id_label.setText(f"TxID: {tx_id}")
                self.tx_id_label.show()
                self.copy_tx_button.show()
            else:
                self.tx_id_label.hide()
                self.copy_tx_button.hide()

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.result_icon_label.setPixmap(pixmap)

    def accept(self):
        if self.calculated_fee is None:
            self.show_result(False, "Cannot proceed: transaction fee could not be calculated.")
            return

        self.stacked_widget.setCurrentWidget(self.processing_widget)
        self.confirm_button.hide()
        self.cancel_button.hide()

        worker = TransactionSubmitWorker(
            rtb=self.rtb,
            transfers=self.transfers_for_preview,
            destination_address=self.recipient_address,
            message=self.message,
            fee_to_lock=self.fee_to_lock
        )
        # Use QueuedConnection to ensure signals are properly queued to main thread
        worker.signals.result.connect(lambda tx_id: self.show_result(True, "Transaction Submitted Successfully!", tx_id), Qt.ConnectionType.QueuedConnection)
        worker.signals.error.connect(lambda err, tx_id: self.show_result(False, err, tx_id if tx_id else None), Qt.ConnectionType.QueuedConnection)
        logger.debug("Worker signals connected with QueuedConnection")

        self.threadpool.start(worker)

    def reject(self):
        self.accepted = False
        super().reject()
