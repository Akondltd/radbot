import logging
from typing import Dict, Optional

from radix_engine_toolkit import (
    Address,
    TransactionManifestV1,
    Decimal,
    ManifestV1Builder,
    ManifestBuilderBucket,
    non_fungible_local_id_from_str,
    NonFungibleGlobalId,
)


logger = logging.getLogger(__name__)


class ManifestBuilder:
    """
    A dedicated, stateless builder for creating Radix Transaction Manifests.

    This class is responsible for constructing the manifest instructions
    based on the desired on-ledger actions, including correct vault and
    bucket interactions.
    """

    @staticmethod
    def build_transfer_manifest(
        from_account_address: str,
        to_account_address: str,
        transfers: Dict[str, Decimal],
        fee_to_lock: Decimal,
        network_id: int,
        owner_badge_details: Optional[Dict[str, str]] = None,
    ) -> TransactionManifestV1:
        """
        Builds a manifest for transferring one or more assets from one account to another.

        This manifest performs the following actions for each asset:
        1. Locks a fee from the source account (once).
        2. Withdraws the specified token amount.
        3. Takes the withdrawn amount into a named bucket.
        4. Deposits that bucket into the destination account.

        Args:
            from_account_address: The bech32m-encoded address of the source account.
            to_account_address: The bech32m-encoded address of the destination account.
            transfers: A dictionary where keys are token RRIs and values are the
                       amounts to transfer. Can contain one or more assets.
            fee_to_lock: The amount of XRD to lock for the transaction fee.
            network_id: The network ID (e.g., 1 for Mainnet).
            owner_badge_details: An optional dictionary containing the resource address and local ID hex of the owner badge.

        Returns:
            The constructed transaction manifest.
        """
        logger.debug(
            f"Building transfer manifest: {len(transfers)} assets from "
            f"{from_account_address} to {to_account_address}."
        )

        # Create Address objects with the network_id to prevent ambiguity
        source_account = Address(from_account_address)
        destination_account = Address(to_account_address)

        manifest_builder = ManifestV1Builder()

        # 1. Lock the transaction fee using the correct high-level method.
        manifest_builder = manifest_builder.account_lock_fee(
            address=source_account, amount=fee_to_lock
        )
        logger.debug(f"  - Instruction: Lock fee of {fee_to_lock} XRD.")

        # For each asset, withdraw, take into a bucket, and deposit the bucket.
        for i, (token_rri, amount) in enumerate(transfers.items()):
            bucket_name = f"bucket_{i}"
            token_address = Address(token_rri)
            logger.debug(f"  - Processing transfer for {amount} {token_rri}.")

            # Withdraw the asset from the source account
            manifest_builder = manifest_builder.account_withdraw(
                address=source_account, resource_address=token_address, amount=amount
            )

            # Take the withdrawn asset from the worktop into a named bucket
            manifest_builder = manifest_builder.take_from_worktop(
                resource_address=token_address,
                amount=amount,
                into_bucket=ManifestBuilderBucket(bucket_name),
            )

            # Deposit the bucket into the destination account using a method that handles restrictive deposit rules.
            manifest_builder = manifest_builder.account_try_deposit_or_abort(
                destination_account, ManifestBuilderBucket(bucket_name), None
            )

        # Build the final manifest
        final_manifest = manifest_builder.build(network_id)
        logger.debug("Transfer manifest built successfully.")

        return final_manifest