from PySide6.QtWidgets import (QDialog, QLabel, QVBoxLayout, QHBoxLayout, 
                                QPushButton, QFileDialog, QMessageBox, QWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ImageQt import ImageQt
from typing import Optional
from pathlib import Path
import segno
import os
import tempfile
import logging
import json

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
        self.container.setGeometry(0, 0, 300, 300)

        # Background GIF label
        self.bg_label = QLabel(self.container)
        self.bg_label.setGeometry(0, 0, 300, 300)
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.bg_label.setAttribute(Qt.WA_TranslucentBackground)

        # QR code display label
        self.qr_label = QLabel(self.container)
        self.qr_label.setGeometry(0, 0, 300, 300)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setAttribute(Qt.WA_TranslucentBackground)

        # Add container to the dialog
        layout = QVBoxLayout(self)
        layout.addWidget(self.container)

    def set_wallet_address(self, address: str, wallet_file_path: Optional[Path] = None):
        """Set the wallet address and generate QR code."""
        qr = segno.make(address)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            try:
                qr.to_artistic(
                    self.parent().gif_path2,
                    tmpfile.name,
                    scale=5,
                    dark='white',
                    light=None,
                    border=1
                )
                tmpfile.flush()
                pil_img = Image.open(tmpfile.name)
                qimage = ImageQt(pil_img)
                pixmap = QPixmap.fromImage(qimage)
                pixmap = pixmap.scaled(296, 296, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.qr_label.setPixmap(pixmap)
                logger.debug(f"Artistic QR code generated and displayed from {tmpfile.name}")
            except Exception as e:
                logger.error(f"Failed to generate artistic QR code: {e}")
                # Fallback: generate plain QR code if artistic fails
                img = qr.to_pil(scale=10)
                qimage = ImageQt(img)
                pixmap = QPixmap.fromImage(qimage)
                self.qr_label.setPixmap(pixmap)
                logger.info("Displayed plain QR code as fallback.")

        if wallet_file_path:
            try:
                qr_img_path = tmpfile.name
                with open(wallet_file_path, 'r', encoding='utf-8') as f:
                    wallet_data = json.load(f)
                wallet_data['qr_code_image'] = qr_img_path
                with open(wallet_file_path, 'w', encoding='utf-8') as f:
                    json.dump(wallet_data, f, indent=4)
                logger.debug(f"Updated wallet config with QR code path: {qr_img_path}")
            except Exception as e:
                logger.error(f"Failed to update wallet config with QR code path: {e}")

    def save_qr(self):
        """Save the QR code to a file."""
        if not hasattr(self, 'wallet_file_path') or not self.wallet_file_path:
            QMessageBox.warning(self, "Error", "No wallet file path available.")
            return
            
        # Get save file name
        default_name = os.path.splitext(os.path.basename(self.wallet_file_path))[0] + "_qr.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code",
            default_name,
            "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            # Save the QR code
            self.qr_label.pixmap().save(file_path)
            QMessageBox.information(
                self,
                "Success",
                f"QR code saved to: {file_path}"
            )
        
    def save_qr(self):
        """Save the QR code to a file."""
        if not hasattr(self, 'wallet_file_path') or not self.wallet_file_path:
            QMessageBox.warning(self, "Error", "No wallet file path available.")
            return
            
        # Get save file name
        default_name = os.path.splitext(os.path.basename(self.wallet_file_path))[0] + "_qr.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code",
            default_name,
            "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            # Save the QR code
            self.qr_label.pixmap().save(file_path)
            QMessageBox.information(
                self,
                "Success",
                f"QR code saved to: {file_path}"
            )
