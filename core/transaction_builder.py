import logging
import random
from typing import Optional, Dict, Tuple, Any
from decimal import Decimal, ROUND_DOWN
import time

from radix_engine_toolkit import (
    TransactionManifestV1,
    NotarizedTransactionV1,
    TransactionHeaderV1,
    TransactionV1Builder,
    InstructionsV1,
    Decimal as RETDecimal,
)
from core.wallet import RadixWallet
from core.manifest_builder import ManifestBuilder
from core.radix_network import RadixNetwork
from config.config_loader import config

# Configure logging
logger = logging.getLogger(__name__)


class RadixTransactionBuilder:
    """
    A builder class for creating and notarizing Radix transactions.
    This class encapsulates the logic for constructing transaction headers
    and notarizing transactions.
    """

    def __init__(self, wallet: RadixWallet):
        """
        Initializes the RadixTransactionBuilder.
        Args:
            wallet (RadixWallet): The wallet instance to use for building transactions.
        """
        if not isinstance(wallet, RadixWallet):
            raise TypeError("wallet must be an instance of RadixWallet")
        self.wallet = wallet
        self.network_id = 0x01
        logger.debug(
            f"RadixTransactionBuilder initialized for wallet: {wallet.public_address} on network {self.network_id}"
        )

    @staticmethod
    def _generate_nonce_static() -> int:
        """Generates a secure 32-bit nonce for static methods."""
        return random.getrandbits(32)

    @staticmethod
    def build_transaction_header(wallet: RadixWallet, network_id: int, start_epoch: int) -> TransactionHeaderV1:
        """
        Builds a standard transaction header.

        Args:
            wallet (RadixWallet): The wallet instance providing the public key.
            network_id (int): The network ID for the transaction.
            start_epoch (int): The starting epoch for the transaction's validity.

        Returns:
            TransactionHeaderV1: The constructed transaction header.
        """
        return TransactionHeaderV1(
            network_id=network_id,
            start_epoch_inclusive=start_epoch,
            end_epoch_exclusive=start_epoch + 2,  # Standard 2-epoch validity
            nonce=RadixTransactionBuilder._generate_nonce_static(),
            notary_public_key=wallet.get_public_key(),
            notary_is_signatory=True,
            tip_percentage=0
        )

    def get_withdrawal_fee_preview(
        self,
        destination_address: str,
        transfers: Dict[str, Decimal],
        safety_multiplier: Optional[Decimal] = None
    ) -> Optional[Decimal]:
        """
        Orchestrates the transaction preview to calculate the withdrawal fee.
        Does TWO previews: first with 1 XRD to estimate, second with safety buffer for accurate hash.

        Args:
            destination_address (str): The recipient's address.
            transfers (Dict[str, Decimal]): A dictionary of token RRIs and amounts to withdraw.
            safety_multiplier (Decimal): Multiplier for fee safety buffer. If None, uses config value.

        Returns:
            Optional[Decimal]: The safe lock fee (preview_fee * multiplier), or None if it fails.
        """
        # Use configurable fee multiplier from advanced_config.json
        if safety_multiplier is None:
            safety_multiplier = Decimal(str(config.withdrawal_fee_multiplier))
        try:
            logger.info("Fetching withdrawal fee preview (two-pass for accurate hash)...")
            radix_network = RadixNetwork(network_id=self.network_id)
            mb = ManifestBuilder()

            # 1. Get network epoch
            current_epoch = radix_network.get_current_epoch()
            if current_epoch is None:
                logger.error("Could not retrieve current epoch. Fee calculation aborted.")
                return None

            # Get owner badge details
            owner_badge_details = radix_network.get_owner_badge_details(self.wallet.public_address)
            if owner_badge_details is None:
                logger.error("Failed to retrieve owner badge for fee preview.")
                raise ValueError("Could not retrieve owner badge details.")

            # 2. FIRST PASS: Preview with 1 XRD to get fee estimate
            manifest_initial = mb.build_transfer_manifest(
                from_account_address=self.wallet.public_address,
                to_account_address=destination_address,
                transfers=transfers,
                fee_to_lock=RETDecimal("1"),
                network_id=self.network_id,
                owner_badge_details=owner_badge_details,
            )

            header = self.build_transaction_header(
                wallet=self.wallet,
                network_id=self.network_id,
                start_epoch=current_epoch,
            )

            fee_ret_decimal = radix_network.get_transaction_fee(manifest_initial, header)
            if fee_ret_decimal is None:
                logger.warning("Failed to get initial fee estimate.")
                return None

            initial_fee = Decimal(fee_ret_decimal.as_str())
            logger.info(f"FIRST PASS - Initial fee estimate: {initial_fee} XRD")

            # 3. Calculate safe lock fee
            safe_lock_fee = initial_fee * safety_multiplier
            logger.info(f"CALCULATED - Safe lock fee: {initial_fee} * {safety_multiplier} = {safe_lock_fee} XRD")

            # 4. SECOND PASS: Preview with safe lock fee to get correct hash
            # (This preview ensures the transaction hash matches what we'll submit)
            mb2 = ManifestBuilder()
            manifest_final = mb2.build_transfer_manifest(
                from_account_address=self.wallet.public_address,
                to_account_address=destination_address,
                transfers=transfers,
                fee_to_lock=RETDecimal(str(safe_lock_fee)),
                network_id=self.network_id,
                owner_badge_details=owner_badge_details,
            )

            # Re-preview with final lock fee (validates the transaction will work)
            final_fee = radix_network.get_transaction_fee(manifest_final, header)
            if final_fee is None:
                logger.warning("SECOND PASS FAILED - Transaction validation failed with lock fee.")
                return None

            final_fee_decimal = Decimal(final_fee.as_str())
            logger.info(f"SECOND PASS - Validation successful (actual network fee: {final_fee_decimal} XRD)")
            logger.info(f"VERIFY - safe_lock_fee variable = {safe_lock_fee}, type = {type(safe_lock_fee)}")
            logger.info(f"VERIFY - Returning exactly: {safe_lock_fee} XRD")
            
            # Return the calculated safe lock fee (NOT the network's actual fee)
            return safe_lock_fee

        except Exception as e:
            logger.error(f"Error during fee preview orchestration: {e}", exc_info=True)
            return None

    def create_notarized_transaction_for_submission(
        self,
        sender_address: str,
        recipient_address: str,
        transfers: Dict[str, RETDecimal],
        message: Optional[str] = None,
        fee_to_lock: Optional[RETDecimal] = None,
    ) -> Tuple[NotarizedTransactionV1, str, TransactionHeaderV1]:
        """
        Creates the final notarized transaction for submission after user confirmation.
        This uses a hardcoded fee_to_lock to ensure the manifest is identical to the preview.
        """
        try:
            mb = ManifestBuilder()
            rn = RadixNetwork()

            # Build the manifest with the specified fee_to_lock to match the preview
            if fee_to_lock is None:
                fee_to_lock = RETDecimal("1")
            
            manifest = mb.build_transfer_manifest(
                from_account_address=sender_address,
                to_account_address=recipient_address,
                transfers=transfers,
                fee_to_lock=fee_to_lock,
                network_id=self.network_id,
            )
            manifest_string = manifest.instructions().as_str()

            # 2. Build the transaction header
            header = self.build_transaction_header(
                wallet=self.wallet,
                network_id=self.network_id,
                start_epoch=rn.get_current_epoch(),
            )

            # 3. Build and notarize the transaction
            notarized_transaction = self.build_and_notarize_transaction(
                manifest_string=manifest_string,
                transaction_header=header,
                message_content=message,
            )

            logger.info("Successfully created notarized transaction for submission.")
            return notarized_transaction, manifest_string, header

        except Exception as e:
            logger.error(f"Error creating notarized transaction for submission: {e}", exc_info=True)
            raise

    def build_and_notarize_transaction(
        self,
        manifest_string: str,
        transaction_header: TransactionHeaderV1,
        message_content: Optional[str] = None,
    ) -> NotarizedTransactionV1:
        """
        Builds, signs, and notarizes a transaction from a manifest and header.

        Args:
            manifest_string (str): The string representation of the manifest.
            transaction_header (TransactionHeaderV1): The pre-built transaction header.
            message_content (Optional[str]): An optional plaintext message.

        Returns:
            NotarizedTransactionV1: The finalized, notarized transaction.
        """
        if not self.wallet.is_fully_loaded():
            raise ValueError("Wallet is not fully loaded and cannot sign transactions.")

        # Parse the manifest string into instructions and create manifest
        instructions = InstructionsV1.from_string(manifest_string, self.network_id)
        manifest = TransactionManifestV1(instructions, [])

        # Build the transaction using the correct step-by-step pattern
        try:
            # Chain the calls to build the transaction intent
            builder = TransactionV1Builder().header(transaction_header).manifest(manifest)

            # Add a message if provided, then sign
            if message_content:
                from radix_engine_toolkit import MessageV1

                msg = MessageV1.new_plain_text(message_content)
                signed_intent = builder.message(msg).sign_with_private_key(
                    self.wallet._private_key
                )
                logger.debug(f"Plain text message added: {message_content}")
            else:
                # Sign directly if no message
                signed_intent = builder.sign_with_private_key(self.wallet._private_key)

            # Notarize the transaction
            notarized_tx = signed_intent.notarize_with_private_key(
                self.wallet._private_key
            )
            logger.info("Transaction signed and notarized successfully.")
            return notarized_tx
        except Exception as e:
            logger.error(
                f"Error during transaction signing/notarizing: {e}",
                exc_info=True,
            )
            raise

    def submit_manifest(self, manifest_string: str) -> Optional[Dict[str, Any]]:
        """
        Builds, signs, and submits a transaction from a pre-made manifest string.

        Args:
            manifest_string (str): The transaction manifest to submit.

        Returns:
            Optional[Dict[str, Any]]: Dict containing 'submission_response' and 'intent_hash', or None on failure.
        """
        if not self.wallet.is_fully_loaded():
            logger.error("Cannot submit manifest: Wallet is not fully loaded.")
            return None

        try:
            radix_network = RadixNetwork(network_id=self.network_id)
            current_epoch = radix_network.get_current_epoch()

            header = self.build_transaction_header(
                wallet=self.wallet,
                network_id=self.network_id,
                start_epoch=current_epoch,
            )

            # Parse the manifest string into instructions and create manifest
            instructions = InstructionsV1.from_string(manifest_string, self.network_id)
            manifest = TransactionManifestV1(instructions, [])

            # Correctly build, sign, and notarize the transaction in one chain
            notarized_transaction = TransactionV1Builder() \
                .header(header) \
                .manifest(manifest) \
                .sign_with_private_key(self.wallet._private_key) \
                .notarize_with_private_key(self.wallet._private_key)

            tx_hex = notarized_transaction.to_payload_bytes().hex()
            intent_hash = notarized_transaction.intent_hash().as_str()
            logger.debug(f"Submitting transaction with intent hash: {intent_hash}")

            submission_response = radix_network.submit_transaction(tx_hex)
            
            # Return both the submission response and intent hash
            return {
                'submission_response': submission_response,
                'intent_hash': intent_hash,
                'success': submission_response and not submission_response.get('duplicate')
            }

        except Exception as e:
            logger.error(f"Failed to sign and submit manifest with epoch: {e}", exc_info=True)
            return None

    def create_notarized_transaction_for_manifest(self, manifest_string: str, sender_address: str) -> tuple:
        """
        Create a notarized transaction from a manifest string (like DEX trade manifests).
        This mirrors create_notarized_transaction_for_submission but for external manifests.
        
        Args:
            manifest_string (str): The manifest string from Astrolescent DEX aggregator
            sender_address (str): The sender's address
            
        Returns:
            tuple: (notarized_transaction, manifest_string, header)
        """
        if not self.wallet.is_fully_loaded():
            logger.error("Cannot create notarized transaction: Wallet is not fully loaded.")
            return None, None, None

        try:
            # Get current epoch for transaction header
            radix_network = RadixNetwork(network_id=self.network_id)
            current_epoch = radix_network.get_current_epoch()
            
            # Build transaction header
            header = self.build_transaction_header(
                wallet=self.wallet,
                network_id=self.network_id,
                start_epoch=current_epoch
            )

            # Parse the manifest string into instructions and create manifest
            instructions = InstructionsV1.from_string(manifest_string, self.network_id)
            manifest = TransactionManifestV1(instructions, [])

            # Build, sign, and notarize the transaction
            notarized_transaction = TransactionV1Builder() \
                .header(header) \
                .manifest(manifest) \
                .sign_with_private_key(self.wallet._private_key) \
                .notarize_with_private_key(self.wallet._private_key)

            logger.debug(f"Created notarized transaction for manifest with intent hash: {notarized_transaction.intent_hash().as_str()}")
            
            return notarized_transaction, manifest_string, header

        except Exception as e:
            logger.error(f"Failed to create notarized transaction for manifest: {e}", exc_info=True)
            return None, None, None

    def verify_transaction_status(self, intent_hash: str, timeout_seconds: int = 60) -> Dict[str, Any]:
        """
        Verify transaction status by polling the network until committed or failed.
        
        Args:
            intent_hash (str): The transaction intent hash to check
            timeout_seconds (int): Maximum time to wait for transaction completion
            
        Returns:
            Dict containing 'status', 'committed', and 'error_message' if any
        """
        try:
            radix_network = RadixNetwork(network_id=self.network_id)
            poll_interval = 2  # seconds
            max_polls = timeout_seconds // poll_interval
            
            logger.info(f"Verifying transaction status for {intent_hash} (timeout: {timeout_seconds}s)")
            
            for attempt in range(max_polls):
                try:
                    status_response = radix_network.get_transaction_status(intent_hash)
                    status = status_response.get('status', 'Unknown')
                    
                    logger.debug(f"Transaction {intent_hash} status check {attempt + 1}/{max_polls}: {status}")
                    
                    if status == 'CommittedSuccess':
                        logger.info(f"Transaction {intent_hash} committed successfully!")
                        return {
                            'status': status,
                            'committed': True,
                            'success': True,
                            'error_message': None
                        }
                    elif status in ['CommittedFailure', 'Rejected']:
                        error_msg = status_response.get('error_message', f"Transaction {status.lower()}")
                        logger.warning(f"Transaction {intent_hash} failed with status: {status}")
                        return {
                            'status': status,
                            'committed': False,
                            'success': False,
                            'error_message': error_msg
                        }
                    elif status in ['Pending', 'Unknown']:
                        # Continue polling
                        if attempt < max_polls - 1:  # Don't sleep on last attempt
                            time.sleep(poll_interval)
                        continue
                    else:
                        logger.warning(f"Unknown transaction status: {status}")
                        if attempt < max_polls - 1:
                            time.sleep(poll_interval)
                        continue
                        
                except Exception as e:
                    logger.warning(f"Error checking transaction status (attempt {attempt + 1}): {e}")
                    if attempt < max_polls - 1:
                        time.sleep(poll_interval)
                    continue
            
            # Timeout reached
            logger.error(f"Transaction {intent_hash} verification timed out after {timeout_seconds}s")
            return {
                'status': 'Timeout',
                'committed': False,
                'success': False,
                'error_message': f"Transaction verification timed out after {timeout_seconds} seconds"
            }
            
        except Exception as e:
            logger.error(f"Failed to verify transaction status for {intent_hash}: {e}", exc_info=True)
            return {
                'status': 'Error',
                'committed': False,
                'success': False,
                'error_message': str(e)
            }