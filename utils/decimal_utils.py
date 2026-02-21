"""
Decimal Precision Utilities

Centralized decimal handling to maintain consistency across the application
and minimize dust accumulation.
"""

from decimal import Decimal, ROUND_DOWN
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DecimalUtils:
    """Utilities for precise decimal handling with token divisibility support."""
    
    @staticmethod
    def to_manifest_decimal(value: Decimal, divisibility: int) -> str:
        """
        Convert Decimal to RETDecimal-safe manifest string.
        Respects token divisibility and truncates excess precision.
        
        Args:
            value: The calculated amount
            divisibility: Token's divisibility (e.g., 6 for USDC, 18 for XRD)
            
        Returns:
            Manifest-ready decimal string
            
        Example:
            >>> amount = Decimal("123.123456789")
            >>> DecimalUtils.to_manifest_decimal(amount, 6)
            '123.123456'
        """
        try:
            from radix_engine_toolkit import Decimal as RETDecimal
            
            # Create quantizer based on divisibility
            quantizer = Decimal(10) ** -divisibility
            
            # Truncate to divisibility (ROUND_DOWN to avoid spending more than we have)
            truncated = value.quantize(quantizer, rounding=ROUND_DOWN)
            
            # Convert to RETDecimal for manifest format
            ret_decimal = RETDecimal(str(truncated))
            return ret_decimal.as_str()
            
        except Exception as e:
            logger.error(f"Error converting {value} to manifest decimal: {e}", exc_info=True)
            raise
    
    @staticmethod
    def from_ledger_string(value: str, divisibility: int) -> Decimal:
        """
        Convert ledger string to Python Decimal, respecting divisibility.
        This eliminates any phantom precision from the ledger response.
        
        Args:
            value: String value from ledger (e.g., "123.123456789")
            divisibility: Token's divisibility
            
        Returns:
            Decimal truncated to proper divisibility
            
        Example:
            >>> DecimalUtils.from_ledger_string("123.123456789", 6)
            Decimal('123.123456')
        """
        try:
            # Convert to Decimal
            decimal_value = Decimal(value)
            
            # Truncate to divisibility
            quantizer = Decimal(10) ** -divisibility
            truncated = decimal_value.quantize(quantizer, rounding=ROUND_DOWN)
            
            return truncated
            
        except Exception as e:
            logger.error(f"Error converting ledger string {value}: {e}", exc_info=True)
            return Decimal("0")
    
    @staticmethod
    def is_dust(value: Decimal, divisibility: int) -> bool:
        """
        Check if a value is dust (rounds to zero given divisibility).
        
        Args:
            value: The amount to check
            divisibility: Token's divisibility
            
        Returns:
            True if the value rounds to zero
            
        Example:
            >>> DecimalUtils.is_dust(Decimal("0.0000001"), 6)
            True
            >>> DecimalUtils.is_dust(Decimal("0.000001"), 6)
            False
        """
        try:
            quantizer = Decimal(10) ** -divisibility
            truncated = value.quantize(quantizer, rounding=ROUND_DOWN)
            return truncated == Decimal("0")
        except:
            return True
    
    @staticmethod
    def normalize_balance(value: Decimal, divisibility: int) -> Decimal:
        """
        Normalize a balance to match on-chain precision.
        Use this when syncing database with ledger to eliminate dust.
        
        Args:
            value: The balance value
            divisibility: Token's divisibility
            
        Returns:
            Normalized decimal
        """
        quantizer = Decimal(10) ** -divisibility
        return value.quantize(quantizer, rounding=ROUND_DOWN)
    
    @staticmethod
    def format_for_display(value: Decimal, decimals: int = 8) -> str:
        """
        Format Decimal for user display (not for manifests).
        
        Args:
            value: The value to format
            decimals: Number of decimals to show (default 8)
            
        Returns:
            Formatted string for UI display
            
        Example:
            >>> DecimalUtils.format_for_display(Decimal("123.456789012"), 8)
            '123.45678901'
        """
        try:
            # Convert to float for display (precision loss acceptable for UI)
            return f"{float(value):.{decimals}f}"
        except:
            return "0.00000000"
    
    @staticmethod
    def calculate_trade_amount(
        balance: Decimal,
        percentage: Decimal,
        divisibility: int,
        reserve_for_fees: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate trade amount from balance, accounting for divisibility.
        
        Args:
            balance: Available balance
            percentage: Percentage to trade (e.g., Decimal("0.95") for 95%)
            divisibility: Token divisibility
            reserve_for_fees: Optional amount to reserve for fees
            
        Returns:
            Trade amount truncated to divisibility
        """
        # Calculate amount
        amount = balance * percentage
        
        # Subtract fee reserve if specified
        if reserve_for_fees:
            amount -= reserve_for_fees
        
        # Truncate to divisibility
        quantizer = Decimal(10) ** -divisibility
        return amount.quantize(quantizer, rounding=ROUND_DOWN)
    
    @staticmethod
    def calculate_fee(amount: Decimal, fee_percentage: Decimal, divisibility: int) -> Decimal:
        """
        Calculate fee amount with proper divisibility.
        
        Args:
            amount: Trade amount
            fee_percentage: Fee percentage (e.g., Decimal("0.001") for 0.1%)
            divisibility: Fee token divisibility (usually XRD = 18)
            
        Returns:
            Fee amount truncated to divisibility
        """
        fee = amount * fee_percentage
        quantizer = Decimal(10) ** -divisibility
        return fee.quantize(quantizer, rounding=ROUND_DOWN)


class BalanceSyncHelper:
    """Helper for syncing database balances with ledger to eliminate dust."""
    
    @staticmethod
    def sync_balance_from_ledger(
        db_balance: Decimal,
        ledger_balance_str: str,
        divisibility: int
    ) -> tuple[Decimal, bool]:
        """
        Sync database balance with ledger balance.
        
        Args:
            db_balance: Current balance in database
            ledger_balance_str: Balance string from ledger
            divisibility: Token divisibility
            
        Returns:
            (corrected_balance, was_adjusted)
        """
        # Convert ledger balance respecting divisibility
        ledger_balance = DecimalUtils.from_ledger_string(ledger_balance_str, divisibility)
        
        # Check if adjustment needed
        if ledger_balance != db_balance:
            logger.debug(f"Balance adjustment: {db_balance} -> {ledger_balance}")
            return ledger_balance, True
        
        return db_balance, False
    
    @staticmethod
    def should_display_balance(balance: Decimal, divisibility: int) -> bool:
        """
        Determine if a balance should be displayed in wallet UI.
        Returns False for dust amounts that round to zero.
        
        Args:
            balance: Token balance
            divisibility: Token divisibility
            
        Returns:
            True if balance should be displayed
        """
        return not DecimalUtils.is_dust(balance, divisibility)


# Convenience functions for common operations
def to_manifest(value: Decimal, divisibility: int) -> str:
    """Shorthand for to_manifest_decimal."""
    return DecimalUtils.to_manifest_decimal(value, divisibility)


def from_ledger(value: str, divisibility: int) -> Decimal:
    """Shorthand for from_ledger_string."""
    return DecimalUtils.from_ledger_string(value, divisibility)


def is_displayable(balance: Decimal, divisibility: int) -> bool:
    """Shorthand for should_display_balance."""
    return BalanceSyncHelper.should_display_balance(balance, divisibility)


# Example usage
if __name__ == "__main__":
    print("Decimal Utils Examples:")
    print("=" * 60)
    
    # Example 1: Trade amount calculation
    print("\n1. Trade Amount (6-decimal token like USDC):")
    balance = Decimal("100.123456789")  # Has extra precision
    trade_amt = DecimalUtils.calculate_trade_amount(balance, Decimal("0.95"), 6)
    print(f"   Balance: {balance}")
    print(f"   95% trade: {trade_amt}")
    print(f"   Manifest: {to_manifest(trade_amt, 6)}")
    
    # Example 2: Fee calculation
    print("\n2. Fee Calculation (XRD = 18 decimals):")
    xrd_amount = Decimal("1000.123456789012345678")
    fee = DecimalUtils.calculate_fee(xrd_amount, Decimal("0.001"), 18)
    print(f"   Amount: {xrd_amount}")
    print(f"   Fee (0.1%): {fee}")
    print(f"   Manifest: {to_manifest(fee, 18)}")
    
    # Example 3: Dust detection
    print("\n3. Dust Detection:")
    tiny = Decimal("0.0000001")
    print(f"   Amount: {tiny}")
    print(f"   Is dust (6 decimals): {DecimalUtils.is_dust(tiny, 6)}")
    print(f"   Is dust (18 decimals): {DecimalUtils.is_dust(tiny, 18)}")
    
    # Example 4: Ledger sync
    print("\n4. Ledger Balance Sync:")
    db_bal = Decimal("100.123456789")
    ledger_bal = "100.123456"  # Ledger only has 6 decimals
    corrected, adjusted = BalanceSyncHelper.sync_balance_from_ledger(db_bal, ledger_bal, 6)
    print(f"   DB balance: {db_bal}")
    print(f"   Ledger balance: {ledger_bal}")
    print(f"   Corrected: {corrected}")
    print(f"   Was adjusted: {adjusted}")
    
    # Example 5: Display filtering
    print("\n5. Display Filtering:")
    balances = [
        (Decimal("100.123456"), 6, "Should display"),
        (Decimal("0.0000001"), 6, "Should hide (dust)"),
        (Decimal("0.000001"), 6, "Should display (minimum)"),
        (Decimal("0"), 6, "Should hide (zero)"),
    ]
    for bal, div, label in balances:
        display = is_displayable(bal, div)
        print(f"   {bal} ({label}): {'✓ Show' if display else '✗ Hide'}")
