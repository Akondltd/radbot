import os
import json
import base64
from pathlib import Path
from typing import Optional
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple

from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip39WordsNum,
    Bip32Slip10Ed25519,
)
from radix_engine_toolkit import PrivateKey, PublicKey, Address, Hash
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from core.radix_network import RadixNetwork, get_nonce

# Configure a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust as needed
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class RadixWallet:
    RADIX_SLIP10_PATH_TEMPLATE = "m/44'/1022'/{account}'/525'/1460'/0'"

    def __init__(
        self,
        wallet_file: Path,
        password: str,
        gateway_url: Optional[str] = None,
        account_index: int = 1,  # Default to account 1 (Radix Mobile Wallet default)
):
        self.wallet_file = Path(wallet_file)
        self.password = password.encode("utf-8")
        self.network_id = 1 # Hardcode to mainnet
        self.gateway_url = gateway_url # Store gateway_url
        self.radix_network = RadixNetwork(gateway_url=self.gateway_url)
        self.account_index = account_index

        self._private_key: Optional[PrivateKey] = None
        self._public_key: Optional[PublicKey] = None
        self._radix_address: Optional[Address] = None
        self.mnemonic: Optional[str] = None

    def verify_password(self, password_to_check: str) -> bool:
        """Verifies the provided password against the wallet's password."""
        if not self.password: # Should not happen if wallet is loaded/created
            return False
        return self.password == password_to_check.encode('utf-8')

    def is_fully_loaded(self) -> bool:
        """Checks if the wallet's core attributes are loaded and ready."""
        return all([self._private_key, self._public_key, self._radix_address])

    def get_active_address(self) -> str:
        """Returns the primary public address for the wallet."""
        return self.public_address

    def get_public_key(self) -> PublicKey:
        """Returns the wallet's public key object. Raises ValueError if not loaded."""
        if not self._public_key:
            raise ValueError("Wallet not loaded or public key not available.")
        return self._public_key

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = Scrypt(salt=salt, length=32, n=2 ** 14, r=8, p=1)
        return kdf.derive(self.password)

    def generate_mnemonic(self) -> str:
        return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24).ToStr()

    def _derive_private_key(self, mnemonic: str, bip39_passphrase: str = "") -> bytes:
        """Derive private key from mnemonic with optional BIP39 passphrase.
        
        Args:
            mnemonic: 24-word seed phrase
            bip39_passphrase: Optional BIP39 passphrase (25th word). Most wallets use empty string.
        """
        seed = Bip39SeedGenerator(mnemonic).Generate(passphrase=bip39_passphrase)
        derivation_path = self.RADIX_SLIP10_PATH_TEMPLATE.format(account=self.account_index)
        logger.debug(f"Deriving wallet with path: {derivation_path}, BIP39 passphrase: {'(set)' if bip39_passphrase else '(empty)'}")
        bip32_ctx = Bip32Slip10Ed25519.FromSeedAndPath(seed, derivation_path)
        priv_key_bytes = bip32_ctx.PrivateKey().Raw().ToBytes()
        return priv_key_bytes

    def derive_private_key_from_seed(self, mnemonic: str, bip39_passphrase: str = "") -> bytes:
        """Derive private key from seed phrase. For mobile wallet imports, use empty passphrase."""
        return self._derive_private_key(mnemonic, bip39_passphrase)

    def create_new_wallet(self) -> str:
        mnemonic = self.generate_mnemonic()
        priv_key_bytes = self._derive_private_key(mnemonic)

        self._private_key = PrivateKey.new_ed25519(priv_key_bytes)
        self._public_key = self._private_key.public_key()
        self._radix_address = Address.preallocated_account_address_from_public_key(
            self._public_key, self.network_id
        )
        self.mnemonic = mnemonic

        self._save_encrypted_key(priv_key_bytes)
        return self.mnemonic

    def load_wallet(self) -> None:
        if not self.wallet_file.exists():
            raise FileNotFoundError("Wallet file does not exist")

        with open(self.wallet_file, "r") as f:
            container = json.load(f)

        salt = base64.b64decode(container["salt"])
        nonce = base64.b64decode(container["nonce"])
        encrypted_key = base64.b64decode(container["encrypted_key"])

        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        priv_key_bytes = aesgcm.decrypt(nonce, encrypted_key, None)

        self._private_key = PrivateKey.new_ed25519(priv_key_bytes)
        self._public_key = self._private_key.public_key()
        self._radix_address = Address.preallocated_account_address_from_public_key(
            self._public_key, self.network_id
        )

    def get_balance(self) -> str:
        """Get the wallet balance using our RadixNetwork class."""
        try:
            from core.radix_network import RadixNetwork
            
            # Initialize our network client
            network = RadixNetwork()
            
            # Get token balances
            balances = network.get_token_balances(self)
            
            # Format the balance information
            balance_info = []
            for token, data in balances.items():
                amount = data.get('amount', 0)
                symbol = data.get('symbol', token)
                balance_info.append(f"{amount} {symbol}")
            
            return "\n".join(balance_info) if balance_info else "No tokens found"
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return "Error fetching balance"

    def fetch_raw_token_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch raw token data including RRI, amount, symbol, name, and decimals from RadixNetwork."""
        try:
            from core.radix_network import RadixNetwork # Local import to avoid circular dependencies if any
            
            # Check if public address is available
            if not hasattr(self, '_radix_address') or not self._radix_address:
                logger.error("Cannot fetch token data: wallet not loaded or address not available")
                return {}
                
            network = RadixNetwork()
            # Add timeout to prevent hanging forever
            raw_balances_data = {}
            
            try:
                # Use a timeout to prevent hanging operations
                raw_balances_data = network.get_token_balances(self.public_address) # Pass address string
            except Exception as network_error:
                logger.error(f"Network error fetching token data: {network_error}", exc_info=True)
                return {}
                
            return raw_balances_data
        except Exception as e:
            logger.error(f"Error fetching raw token data: {e}", exc_info=True)
            return {} # Return empty dict on error

    def _save_encrypted_key(self, priv_key_bytes: bytes) -> None:
        salt = os.urandom(16)
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        encrypted = aesgcm.encrypt(nonce, priv_key_bytes, None)

        container = {
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "encrypted_key": base64.b64encode(encrypted).decode(),
        }

        self.wallet_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.wallet_file, "w") as f:
            json.dump(container, f, indent=4)

    def sign_and_submit_transaction(self, manifest_string: str) -> Optional[Dict[str, Any]]:
        """Signs and submits a transaction manifest, returning the receipt."""
        if not self.is_fully_loaded():
            logger.error("Wallet is not fully loaded. Cannot sign transaction.")
            return None

        try:
            logger.info("Preparing to sign and submit transaction.")
            current_epoch = self.radix_network.get_current_epoch()
            header = TransactionHeaderV1(
                network_id=self.network_id,
                start_epoch_inclusive=current_epoch,
                end_epoch_exclusive=current_epoch + self.radix_network.EPOCH_VALIDITY_BUFFER,
                nonce=get_nonce(),
                notary_public_key=self._public_key,
                notary_is_signatory=True,
                tip_percentage=0
            )

            manifest = TransactionManifestV1.from_string(manifest_string, self.network_id)

            transaction = TransactionV1Builder() \
                .header(header) \
                .manifest(manifest) \
                .build()

            notarized_transaction = transaction.sign_with_private_key(self._private_key) \
                .notarize_with_private_key(self._private_key)

            tx_hex = notarized_transaction.to_payload_bytes().hex()
            logger.debug(f"Submitting transaction with intent hash: {notarized_transaction.intent_hash().as_str()}")

            return self.radix_network.submit_transaction(tx_hex)

        except Exception as e:
            logger.error(f"Failed to sign and submit transaction: {e}", exc_info=True)
            return None

    @property
    def public_address(self) -> str:
        if not self._radix_address:
            raise ValueError("Wallet not loaded")
        return self._radix_address.as_str()

    def sign(self, message: bytes) -> bytes:
        if not self._private_key:
            raise ValueError("Wallet not loaded")
        # Wrap message bytes as a Hash object using from_unhashed_bytes
        message_hash = Hash.from_unhashed_bytes(message)
        signature = self._private_key.sign(message_hash)
        return bytes(signature)

    def export_private_key(self, password: str) -> str:
        if not self._private_key:
            raise ValueError("No wallet loaded to export private key from")
        if password.encode("utf-8") != self.password:
            raise ValueError("Incorrect password")
        if callable(getattr(self._private_key, "raw", None)):
            priv_key_bytes = self._private_key.raw()
        else:
            priv_key_bytes = self._private_key.raw
        return base64.b64encode(priv_key_bytes).decode()

    def import_wallet(self, priv_key_bytes: bytes) -> None:
        self._private_key = PrivateKey.new_ed25519(priv_key_bytes)
        self._public_key = self._private_key.public_key()
        self._radix_address = Address.preallocated_account_address_from_public_key(
            self._public_key, self.network_id
        )
        self.mnemonic = None
        self._save_encrypted_key(priv_key_bytes)