import requests
import json
import secrets
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from radix_engine_toolkit import (
    Address,
    PublicKey,
    TransactionManifestV1,
    Decimal as RETDecimal,
    TransactionV1Builder,
    TransactionHeaderV1,
    MessageV1,
    PrivateKey,
    NotarizedTransactionV1
)
# Using V1 classes.
import logging
from radix_engine_toolkit import (Decimal as RETDecimal, NotarizedTransactionV1, TransactionHeaderV1, MessageV1, TransactionV1Builder)
import decimal
from utils.api_tracker import api_tracker

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class RadixNetworkError(Exception):
    """Custom exception for Radix network-related errors."""
    pass

def get_nonce():
    """Generates a random 32-bit nonce."""
    return secrets.randbits(32)

class RadixNetwork:
    EPOCH_VALIDITY_BUFFER = 2  # Number of epochs the transaction is valid for
    def __init__(self, gateway_url: str = "https://mainnet.radixdlt.com", network_id: int = 1):
        self.gateway_url = gateway_url
        self.network_id = network_id
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Set reasonable timeouts to prevent hanging
        self.session.timeout = (5, 30)  # (connect timeout, read timeout)
        # Add request retry logic
        retry_adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount('http://', retry_adapter)
        self.session.mount('https://', retry_adapter)
        logger.info(f"RadixNetwork initialized with gateway: {self.gateway_url}, network_id: {self.network_id}")

    def get_current_epoch(self) -> int:
        status_url = f"{self.gateway_url}/status/gateway-status"
        logger.debug(f"Fetching current epoch from {status_url}")
        try:
            api_tracker.record('radix_gateway')
            response = self.session.post(status_url, json={})
            response.raise_for_status()
            data = response.json()
            ledger_state = data.get('ledger_state')
            if not ledger_state:
                logger.error(f"'ledger_state' not found in gateway status response: {data}")
                raise ValueError("'ledger_state' not found in gateway status response.")
            
            epoch = ledger_state.get('epoch')
            if epoch is None:
                logger.error(f"Could not find epoch in gateway status response's ledger_state: {data}")
                raise ValueError("Epoch not found in gateway status response's ledger_state.")
            
            logger.info(f"Current epoch from gateway {self.gateway_url}: {epoch}")
            return int(epoch)
        except requests.RequestException as e:
            logger.error(f"Error fetching current epoch: {e}")
            if e.response:
                logger.error(f"Response body: {e.response.text}")
            raise

    def get_entity_details(self, addresses: List[str]) -> Dict:
        url = f"{self.gateway_url}/state/entity/details"
        payload = {
            "addresses": addresses,
            "aggregation_level": "Vault",
            "opt_ins": {
                "explicit_metadata": ["symbol", "name"]
            }
        }
        try:
            api_tracker.record('radix_gateway')
            response = self.session.post(url, json=payload, timeout=(5, 30))
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, requests.exceptions.Timeout, 
                requests.exceptions.ConnectionError, ConnectionResetError,
                ConnectionAbortedError, ConnectionRefusedError, 
                requests.exceptions.ReadTimeout) as e:
            logger.error(f"Error getting entity details: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response body: {e.response.text}")
            # Return empty dict instead of raising to prevent application crashes
            return {}

    def get_token_metadata(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch token metadata from Radix Gateway for a specific resource address.
        
        Args:
            token_address: The resource address (RRI) of the token
            
        Returns:
            Dictionary with 'symbol', 'name', 'divisibility', 'icon_url', 'description', 'info_url'
            or None if fetch fails
        """
        try:
            logger.debug(f"Fetching metadata for token: {token_address}")
            details = self.get_entity_details([token_address])
            
            if not details or 'items' not in details:
                logger.warning(f"No entity details returned for token {token_address}")
                return None
            
            items = details.get('items', [])
            if not items:
                logger.warning(f"Empty items list for token {token_address}")
                return None
            
            token_data = items[0]
            metadata = token_data.get('metadata', {})
            
            # Extract standard metadata fields
            symbol = None
            name = None
            divisibility = 18  # Default
            icon_url = None
            description = None
            info_url = None
            
            # Metadata is returned as list of items with 'key' and 'value'
            if 'items' in metadata:
                for item in metadata['items']:
                    key = item.get('key')
                    value = item.get('value', {})
                    typed_value = value.get('typed', {})
                    
                    if key == 'symbol':
                        symbol = typed_value.get('value')
                    elif key == 'name':
                        name = typed_value.get('value')
                    elif key == 'divisibility':
                        div_value = typed_value.get('value')
                        if div_value is not None:
                            divisibility = int(div_value)
                    elif key == 'icon_url':
                        icon_url = typed_value.get('value')
                    elif key == 'description':
                        description = typed_value.get('value')
                    elif key == 'info_url':
                        info_url = typed_value.get('value')
            
            # Fallback: use address prefix as symbol if nothing found
            if not symbol:
                symbol = f"TOKEN_{token_address[:8]}"
            if not name:
                name = symbol
            
            logger.info(f"Fetched metadata for {token_address}: {symbol} ({name}), divisibility={divisibility}, icon_url={icon_url is not None}")
            return {
                'symbol': symbol,
                'name': name,
                'divisibility': divisibility,
                'icon_url': icon_url,
                'description': description,
                'info_url': info_url
            }
            
        except Exception as e:
            logger.error(f"Error fetching token metadata for {token_address}: {e}", exc_info=True)
            return None

    def get_owner_badge_details(self, account_address: str) -> Optional[Dict[str, str]]:
        """
        Retrieves the owner badge details for a given account, required for transaction authorization.

        This now uses the definitive `role_assignments` structure for modern accounts.

        Args:
            account_address (str): The public address of the account.

        Returns:
            Optional[Dict[str, str]]: A dictionary with badge details if found, otherwise None.
        """
        logger.debug(f"Fetching owner badge details for account: {account_address}")
        try:
            # 1. Get entity details for the account
            account_details_response = self.get_entity_details([account_address])
            if not account_details_response or not account_details_response.get('items'):
                logger.error(f"Failed to retrieve entity details for account {account_address}")
                return None
            account_details = account_details_response['items'][0]

            # 2. Navigate the correct path for modern accounts via role_assignments
            requirement = account_details['details']['role_assignments']['owner']['rule']['access_rule']['proof_rule']['requirement']

            if requirement['type'] == 'NonFungible':
                non_fungible = requirement['non_fungible']
                resource_address = non_fungible['resource_address']
                # The local_id from simple_rep is a string like "[<hex_id>]".
                # The toolkit's from_str function requires these brackets to parse the type correctly.
                local_id = non_fungible['local_id']['simple_rep']

                logger.info(f"Successfully found owner badge for {account_address} via role_assignments.")
                return {
                    "resource_address": resource_address,
                    "local_id": local_id,
                    "type": "NonFungible",
                }
            else:
                logger.warning(f"Owner requirement for {account_address} is not of type NonFungible.")
                return None

        except (KeyError, TypeError, IndexError) as e:
            logger.error(
                f"Could not parse owner badge details for {account_address} from role_assignments. Error: {e}",
                exc_info=True
            )
            return None

    def get_token_balances(self, account_address: str) -> Dict[str, Dict[str, Any]]:
        """
        Fetches token balances for a given account address, including metadata like symbol, name, and decimals.
        Returns a dictionary where keys are resource_addresses and values are dicts
        containing 'amount' (atomic string), 'symbol', 'name', and 'decimals'.
        """
        logger.debug(f"Getting token balances for account: {account_address}")
        if not account_address:
            logger.warning("No account address provided to get_token_balances")
            return {}

        # Make the network operation safe - catch all possible errors
        try:
            # 1. Get entity details for the account
            account_details = self.get_entity_details([account_address])
            
            # 2. Handle missing entity details more gracefully
            if not account_details or not account_details.get('items'):
                logger.warning(f"No entity details found for account: {account_address}")
                return {}
                
            # 3. Process account details if present
            account_data = account_details['items'][0]
            result = {}
            
            # 4. Process fungible resources
            if 'fungible_resources' in account_data and 'items' in account_data['fungible_resources']:
                fungible_resources = account_data['fungible_resources']['items']
                
                for resource in fungible_resources:
                    resource_address = resource.get('resource_address')
                    
                    if not resource_address:
                        continue
                    
                    # Default values for resource information
                    resource_info = {
                        'amount': '0',
                        'symbol': 'UNKNOWN',
                        'name': 'Unknown Token',
                        'decimals': 18  # Default decimals
                    }
                    
                    # Safely extract amount from vaults
                    try:
                        if ('vaults' in resource and 'items' in resource['vaults'] and 
                            resource['vaults']['items'] and 'amount' in resource['vaults']['items'][0]):
                            resource_info['amount'] = resource['vaults']['items'][0]['amount']
                    except (KeyError, IndexError, TypeError) as e:
                        logger.warning(f"Error extracting amount from resource {resource_address}: {e}")
                    
                    # Safely extract metadata
                    try:
                        if 'metadata' in resource:
                            metadata = resource['metadata'].get('items', [])
                            for meta_item in metadata:
                                key = meta_item.get('key')
                                value = meta_item.get('value', {}).get('typed', {}).get('value')
                                
                                if key == 'symbol' and value:
                                    resource_info['symbol'] = value
                                elif key == 'name' and value:
                                    resource_info['name'] = value
                                elif key == 'decimals' and value:
                                    try:
                                        resource_info['decimals'] = int(value)
                                    except (ValueError, TypeError):
                                        pass  # Keep default decimals
                            
                            # Log when metadata was successfully extracted from first API call
                            if resource_info['symbol'] != 'UNKNOWN' and resource_info['name'] != 'Unknown Token':
                                logger.debug(f"Extracted metadata from first API call for {resource_address}: "
                                           f"{resource_info['symbol']} ({resource_info['name']})")
                    except Exception as meta_error:
                        logger.warning(f"Error processing metadata for resource {resource_address}: {meta_error}")
                    
                    result[resource_address] = resource_info
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in get_token_balances: {e}", exc_info=True)
            return {}

    def get_transaction_fee(self, manifest: TransactionManifestV1, header: TransactionHeaderV1) -> RETDecimal:
        """
        Previews a transaction to get the fee.
        """
        current_epoch = self.get_current_epoch()
        if current_epoch is None:
            logger.error("Could not determine current epoch, aborting fee calculation.")
            return RETDecimal("0")

        instructions_obj = manifest.instructions()

        # Use the .as_str() method to get the human-readable manifest string.
        manifest_instructions_for_payload = instructions_obj.as_str()

        payload = {
            "manifest": manifest_instructions_for_payload,
            "network": self.network_id,
            "start_epoch_inclusive": current_epoch,
            "end_epoch_exclusive": current_epoch + self.EPOCH_VALIDITY_BUFFER,
            "nonce": str(header.nonce),  # API expects nonce as a string
            "signer_public_keys": [self.public_key_to_gateway_format(header.notary_public_key)],
            "tip_percentage": header.tip_percentage,
            "flags": {
                "use_free_credit": True,
                "assume_all_signature_proofs": True,
                "skip_epoch_check": False
            }
        }

        if header.notary_public_key:
            payload["notary_public_key"] = self.public_key_to_gateway_format(header.notary_public_key)
            payload["notary_is_signatory"] = header.notary_is_signatory
        
        logger.debug(f"Requesting transaction preview from {self.gateway_url}/transaction/preview with payload: {json.dumps(payload, indent=2)}")

        try:
            api_tracker.record('radix_gateway')
            response = self.session.post(f"{self.gateway_url}/transaction/preview", json=payload, timeout=(5, 30))
            response.raise_for_status()
            response_json = response.json()

            # Log the full response from the preview endpoint as requested.
            logger.debug(f"Transaction preview response: {json.dumps(response_json, indent=2)}")

            receipt = response_json.get('receipt', {})

            # Initialize total_fee as RETDecimal
            total_fee = RETDecimal("0")

            # Extract fee from fee_source -> from_vaults -> xrd_amount
            fee_source = receipt.get('fee_source', {})
            if fee_source:
                from_vaults = fee_source.get('from_vaults', [])
                total_fee_decimal = decimal.Decimal("0")
                for vault in from_vaults:
                    if isinstance(vault, dict):
                        xrd_amount = vault.get('xrd_amount', '0')
                        try:
                            total_fee_decimal += decimal.Decimal(xrd_amount)
                        except Exception as e:
                            logger.error(f"Error parsing xrd_amount '{xrd_amount}': {e}")
                total_fee = RETDecimal(str(total_fee_decimal))
                logger.info(f"Calculated total fee from fee_source: {total_fee.as_str()} XRD")
            else:
                logger.warning("No fee_source found in preview response")
        
            return total_fee
        except requests.exceptions.HTTPError as e_http:
            logger.error(f"HTTP error during transaction fee preview: {e_http}", exc_info=True)
            if e_http.response:
                logger.error(f"Response content: {e_http.response.text}")
            return RETDecimal("-1") 
        except json.JSONDecodeError as e_json_decode: # Specific handling for JSON decoding errors
            logger.error(f"Failed to decode JSON response from transaction fee preview: {e_json_decode}", exc_info=True)
            if response is not None:
                logger.error(f"Response content that failed to parse: {response.text}")
            return RETDecimal("-1") # Indicate error
        except Exception as e: # General catch-all for other unexpected errors
            logger.error(f"An unexpected error occurred in get_transaction_fee: {e}", exc_info=True)
            return RETDecimal("-1")

    def public_key_to_gateway_format(self, ret_public_key: PublicKey) -> Dict[str, str]:
        """Helper to convert RET PublicKey to API JSON format."""
        if ret_public_key.is_ed25519():
            key_type = "EddsaEd25519"
            # .value is already the bytes object, so we can call .hex() directly.
            key_hex = ret_public_key.value.hex()
        elif ret_public_key.is_secp256k1():
            key_type = "EcdsaSecp256k1"
            # .value is already the bytes object, so we can call .hex() directly.
            key_hex = ret_public_key.value.hex()
        else:
            logger.error(f"Unsupported public key type: {type(ret_public_key)}")
            raise TypeError(f"Unsupported public key type: {type(ret_public_key)}")

        return {
            "key_type": key_type,
            "key_hex": key_hex,
        }

    def submit_transaction(self, notarized_transaction_hex: str) -> Dict:
        """
        Submit a notarized transaction to the Radix network.
        """
        url = f"{self.gateway_url}/transaction/submit"
        logger.debug(f"Submitting transaction to {url}")

        payload = {
            "notarized_transaction_hex": notarized_transaction_hex
        }

        try:
            api_tracker.record('radix_gateway')
            response = self.session.post(url, json=payload, timeout=(5, 30))
            response.raise_for_status()
            logger.debug(f"Transaction submission response: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting transaction: {e}")
            if e.response is not None:
                logger.error(f"Submit API Response Text: {e.response.text}")
            raise

    def preview_transaction(self, manifest_string: str, transaction_header: TransactionHeaderV1) -> Dict:
        """
        Previews a transaction to validate it and get execution details.
        """
        url = f"{self.gateway_url}/transaction/preview"
        logger.debug(f"Previewing transaction at {url}")

        payload = {
            "manifest": manifest_string,
            "network": self.network_id,
            "start_epoch_inclusive": transaction_header.start_epoch_inclusive,
            "end_epoch_exclusive": transaction_header.end_epoch_exclusive,
            "tip_percentage": transaction_header.tip_percentage,
            "nonce": str(transaction_header.nonce), # API expects nonce as a string
            "signer_public_keys": [
                self.public_key_to_gateway_format(transaction_header.notary_public_key)
            ],
            "flags": {
                "use_free_credit": True,
                "assume_all_signature_proofs": True,
                "skip_epoch_check": False,
            },
        }

        try:
            api_tracker.record('radix_gateway')
            response = self.session.post(url, json=payload, timeout=(5, 30))
            response.raise_for_status()
            logger.debug(f"Transaction preview response: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error previewing transaction: {e}")
            if e.response is not None:
                logger.error(f"Preview API Response Text: {e.response.text}")
            raise RadixNetworkError(f"Failed to preview transaction") from e

    def get_transaction_status(self, intent_hash: str) -> Dict:
        """
        Get the status of a submitted transaction by its intent hash.
        """
        url = f"{self.gateway_url}/transaction/status"
        logger.debug(f"Getting status for transaction {intent_hash} from {url}")

        payload = {
            "intent_hash": intent_hash
        }

        try:
            api_tracker.record('radix_gateway')
            response = self.session.post(url, json=payload, timeout=(5, 30))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting transaction status for {intent_hash}: {e}")
            if e.response is not None:
                logger.error(f"Status API Response Text: {e.response.text}")
            raise RadixNetworkError(f"Failed to get status for {intent_hash}") from e

    def get_xrd_balance(self, address: str) -> RETDecimal:
        details = self.get_entity_details([address])
        xrd_balance = RETDecimal("0")
        if details and 'items' in details and len(details['items']) > 0:
            account_details = details['items'][0]
            fungible_resources = account_details.get('fungible_resources', {}).get('items', [])
            for resource in fungible_resources:
                if resource.get('resource_address') == "resource_rdx1tknxxxxxxxxxradxrdxxxxxxxxx009923554798xxxxxxxxxradxrd":
                    try:
                        if 'vaults' in resource and isinstance(resource['vaults'], dict) and \
                           'items' in resource['vaults'] and isinstance(resource['vaults']['items'], list) and \
                           len(resource['vaults']['items']) > 0 and isinstance(resource['vaults']['items'][0], dict) and \
                           'amount' in resource['vaults']['items'][0]:
                            xrd_balance = RETDecimal(resource['vaults']['items'][0]['amount'])
                            break
                        elif 'amount' in resource: # Fallback for potentially different structures
                            xrd_balance = RETDecimal(resource['amount'])
                            break
                        else:
                            logger.warning(f"XRD Resource {resource.get('resource_address')} in get_xrd_balance missing 'amount' or expected nested structure. Data: {resource}")
                    except (TypeError, KeyError, IndexError) as e:
                        logger.error(f"Error parsing XRD resource {resource.get('resource_address')} in get_xrd_balance: {e}. Data: {resource}")
                        # xrd_balance remains "0"
                    break # Found XRD resource, processed or failed, exit loop
        return xrd_balance

    @staticmethod
    def _get_fee_from_fee_destination(fee_destination: dict) -> decimal.Decimal:
        """
        Calculates the total transaction fee from the 'fee_destination' dictionary.
        """
        total_fee = decimal.Decimal("0")  # Use Python's standard Decimal for calculation
        if not fee_destination:
            return total_fee

        for key, value_str in fee_destination.items():
            try:
                # The API can return lists (e.g., for royalties), so only process strings.
                if isinstance(value_str, str):
                    # Convert string value to Python's Decimal for safe arithmetic
                    fee_component = decimal.Decimal(value_str)
                    total_fee += fee_component
            except Exception as e:
                logger.error(
                    f"Error converting fee value '{value_str}' for key '{key}' to Decimal: {e}",
                    exc_info=True,
                )
        logger.info(f"Calculated total fee from fee_destination: {total_fee} XRD")
        return total_fee
