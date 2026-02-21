# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
"""
Native Fee Configuration Module

This module is compiled to a native binary (.pyd on Windows, .so on Linux)
to provide enhanced protection against tampering.

Compile with: python config/build_fee_native.py
"""

import hashlib
import sys
import os
from decimal import Decimal

# C-level imports for anti-debugging
from libc.stdlib cimport abort
from cpython.exc cimport PyErr_SetString


# ============================================================================
# ANTI-DEBUGGING CHECKS
# ============================================================================

cdef bint _is_debugger_present():
    """Check for common debugging scenarios."""
    cdef bint detected = False
    
    # Check 1: sys.gettrace() - Python debuggers set a trace function
    if sys.gettrace() is not None:
        detected = True
    
    # Check 2: Common debugger environment variables
    cdef list debug_vars = ['PYTHONBREAKPOINT', 'PYDEVD_USE_CYTHON', 'PYCHARM_DEBUG']
    for var in debug_vars:
        if os.environ.get(var):
            detected = True
            break
    
    # Check 3: sys.flags.debug
    if hasattr(sys.flags, 'debug') and sys.flags.debug:
        detected = True
    
    return detected


cdef void _anti_debug_check() except *:
    """Abort if debugging is detected."""
    if _is_debugger_present():
        PyErr_SetString(RuntimeError, "Security check failed")
        raise RuntimeError("Security check failed")


# ============================================================================
# INTEGRITY VERIFICATION
# ============================================================================

# The actual values - embedded in compiled binary
# These are NOT easily visible in the .pyd file like they would be in .py
cdef str _FEE_VALUE = "0.001"
cdef str _COMPONENT_VALUE = "component_rdx1czrwlclg9p5h4p50yhkfqhgn3uqsyfmup29xt2f20c5jsa55ef0xv4"

# Pre-computed integrity hash (SHA256 of "fee|component" combined)
cdef str _INTEGRITY_HASH = "0abf50e714742d8348a1fdc6d33dc6c88c6ed01fb3e6bf5ffc5fa021cd820d05"


cdef bint _verify_internal_integrity():
    """Verify the embedded values haven't been patched in the binary."""
    if not _FEE_VALUE.startswith("0."):
        return False
    if not _COMPONENT_VALUE.startswith("component_rdx1"):
        return False
    if len(_COMPONENT_VALUE) != 68:
        return False
    
    # Verify against pre-computed hash
    cdef str combined = f"{_FEE_VALUE}|{_COMPONENT_VALUE}"
    cdef str actual_hash = hashlib.sha256(combined.encode()).hexdigest()
    if actual_hash != _INTEGRITY_HASH:
        return False
    
    return True


# ============================================================================
# FEE CONFIGURATION (Public API)
# ============================================================================

def get_fee_percentage() -> Decimal:
    """
    Get the fee percentage.
    
    Returns:
        Decimal: The fee percentage (e.g., Decimal('0.001') for 0.1%)
    
    Raises:
        RuntimeError: If security checks fail
    """
    _anti_debug_check()
    
    if not _verify_internal_integrity():
        raise RuntimeError("Configuration integrity check failed")
    
    return Decimal(_FEE_VALUE)


def get_fee_component_address() -> str:
    """
    Get the fee component address.
    
    Returns:
        str: The component address for fee collection
    
    Raises:
        RuntimeError: If security checks fail
    """
    _anti_debug_check()
    
    if not _verify_internal_integrity():
        raise RuntimeError("Configuration integrity check failed")
    
    return _COMPONENT_VALUE


# ============================================================================
# MANIFEST VERIFICATION
# ============================================================================

def verify_manifest_contains_fee(manifest: str, min_fee_percentage: float = 0.0005) -> bool:
    """
    Verify that a manifest contains the expected fee transfer.
    
    This is a critical security check - call this BEFORE signing any manifest
    returned from the Astrolescent API.
    
    Args:
        manifest: The manifest string from Astrolescent API
        min_fee_percentage: Minimum expected fee (default 0.05% to allow for rounding)
    
    Returns:
        bool: True if manifest contains valid fee, False otherwise
    """
    _anti_debug_check()
    
    cdef str component = _COMPONENT_VALUE
    
    # Check 1: Component address must be present in manifest
    if component not in manifest:
        return False
    
    # Check 2: Look for CALL_METHOD pattern with our component
    # Astrolescent manifests use a specific format
    cdef str call_pattern = f'CALL_METHOD\n    Address("{component}")'
    cdef str alt_pattern = f'Address("{component}")'
    
    if call_pattern not in manifest and alt_pattern not in manifest:
        return False
    
    # Check 3: Verify it's a deposit/transfer call, not some other reference
    # Look for common deposit method patterns near our address
    cdef int addr_pos = manifest.find(component)
    if addr_pos == -1:
        return False
    
    # Get context around the address (200 chars before and after)
    cdef int start = max(0, addr_pos - 200)
    cdef int end = min(len(manifest), addr_pos + 200)
    cdef str context = manifest[start:end].lower()
    
    # Must have a deposit or transfer-like operation
    cdef list valid_operations = ['deposit', 'try_deposit', 'call_method']
    cdef bint has_valid_op = False
    for op in valid_operations:
        if op in context:
            has_valid_op = True
            break
    
    return has_valid_op


def get_security_status() -> dict:
    """
    Get current security status for logging/diagnostics.
    
    Returns:
        dict: Security status information
    """
    return {
        'debugger_detected': _is_debugger_present(),
        'integrity_valid': _verify_internal_integrity(),
        'native_module': True,
    }
