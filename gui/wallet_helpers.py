from PySide6.QtWidgets import QMessageBox, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)

class WalletErrorHelper:
    """Helper class for handling wallet-related errors."""
    
    @staticmethod
    def show_message(parent, message: str):
        """Show a message in a popup dialog."""
        QMessageBox.information(parent, "Message", message)

    @staticmethod
    def handle_error(parent, layout, message: str, error_type: str = "Error"):
        """Handle an error by showing a message in the layout."""
        logger.error(message)
        error_message = QLabel(f"{error_type}: {message}")
        error_message.setFont(QFont("Arial", 10))
        error_message.setAlignment(Qt.AlignCenter)
        error_message.setStyleSheet("color: #ff0000;")
        layout.addWidget(error_message)
        return error_message

    @staticmethod
    def clear_error_messages(layout):
        """Clear any existing error messages from the layout."""
        # Remove all widgets that aren't the title
        while layout.count() > 1:  # Keep the title
            item = layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    @staticmethod
    def validate_seed_phrase(seed_phrase: str) -> bool:
        """Validate that a seed phrase is exactly 24 words."""
        words = seed_phrase.strip().split()
        return len(words) == 24

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate that a password is provided."""
        return bool(password.strip())
