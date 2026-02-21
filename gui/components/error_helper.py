from PySide6.QtWidgets import QMessageBox
from typing import Dict, Tuple

class WalletErrorHelper:
    @staticmethod
    def show_message(parent, message):
        """Show an error message dialog."""
        QMessageBox.warning(
            parent,
            "Wallet Error",
            message,
            QMessageBox.Ok
        )
        
    @staticmethod
    def show_success(parent, message):
        """Show a success message dialog."""
        QMessageBox.information(
            parent,
            "Success",
            message,
            QMessageBox.Ok
        )
        
    @staticmethod
    def show_withdrawal_summary(parent, results: Dict[str, Tuple[bool, str]]):
        """Show summary of withdrawal results."""
        success_count = sum(1 for success, _ in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            QMessageBox.information(
                parent,
                "Success",
                "All withdrawal transactions processed successfully!\n\n"
                "Please wait for the transactions to be confirmed on the ledger.",
                QMessageBox.Ok
            )
        elif success_count > 0:
            QMessageBox.information(
                parent,
                "Partial Success",
                f"{success_count} out of {total_count} withdrawal transactions succeeded.\n\n"
                "Please wait for the transactions to be confirmed on the ledger.\n"
                "Check the logs for details on failed transactions.",
                QMessageBox.Ok
            )
        else:
            QMessageBox.warning(
                parent,
                "Failed",
                "No withdrawal transactions succeeded.\n\n"
                "Please check the error messages above for details.",
                QMessageBox.Ok
            )
