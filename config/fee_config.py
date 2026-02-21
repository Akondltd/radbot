"""
Fee Configuration - Protected

DO NOT MODIFY - Values are integrity-checked at runtime.
Modifications will cause application failure.

This module attempts to use the native compiled module (fee_native.pyd/.so)
for enhanced protection. Falls back to pure Python if native not available.
"""

import base64
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Try to import native module first
_NATIVE_AVAILABLE = False
_native = None

def _try_load_native_module():
    """Attempt to load the native fee module."""
    global _NATIVE_AVAILABLE, _native
    
    if _native is not None:
        return  # Already loaded
    
    # Try multiple import approaches
    import importlib.util
    import os
    import sys
    
    # Get config directory path
    config_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Approach 1: Add config dir to sys.path and import directly
    try:
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
        import fee_native as native_mod
        _native = native_mod
        _NATIVE_AVAILABLE = True
        logger.info("Native fee module loaded successfully (direct import)")
        return
    except ImportError as e:
        logger.debug(f"Direct import failed: {e}")
    
    # Approach 2: Load from same directory as this file using importlib
    try:
        # On Windows, add config dir to DLL search path
        if sys.platform == 'win32':
            try:
                os.add_dll_directory(config_dir)
            except (AttributeError, OSError):
                pass  # Not available on older Python or if dir doesn't exist
        
        # Find the .pyd or .so file
        for filename in os.listdir(config_dir):
            if filename.startswith('fee_native') and (filename.endswith('.pyd') or filename.endswith('.so')):
                native_path = os.path.join(config_dir, filename)
                spec = importlib.util.spec_from_file_location("fee_native", native_path)
                if spec and spec.loader:
                    native_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(native_mod)
                    _native = native_mod
                    _NATIVE_AVAILABLE = True
                    logger.info(f"Native fee module loaded successfully ({filename})")
                    return
    except Exception as e:
        logger.debug(f"Native module load attempt failed: {e}")
    
    # Fallback: No native module available
    logger.warning(
        "Native fee module not available. Using pure Python fallback. "
        "For enhanced security, build with: python config/build_fee_native.py"
    )

# Try to load on module import
_try_load_native_module()


class FeeConfig:
    """
    Obfuscated fee configuration.
    
    Values are encoded and validated at runtime to prevent tampering.
    """
    
    # Runtime-derived decoding key (dispersed as byte values)
    _key = bytes([0x72, 0x61, 0x64, 0x62, 0x6f, 0x74, 0x5f, 0x66,
                  0x65, 0x65, 0x5f, 0x6b, 0x65, 0x79, 0x5f, 0x32,
                  0x30, 0x32, 0x35])
    
    _fee_parts = [
        b'Qg==',
        b'XA==',
        b'QlFV',
    ]
    
    _component_parts = [
        b'EQ4JEgAaOggROi0PHQ==',
        b'QwIeEBgYPAoCXC9eDQ==',
        b'RhFRUhYcNAAUDTgFVg==',
        b'BxAXGwkZKhZXXCcfVw==',
        b'FFNUAVoeLAdQUDoNVQEpBg==',
    ]
    
    # Integrity hash (SHA256 of correct values)
    _integrity = '0abf50e714742d8348a1fdc6d33dc6c88c6ed01fb3e6bf5ffc5fa021cd820d05'

    
    @staticmethod
    def _xor_decode(encoded: bytes, key: bytes) -> str:
        """XOR decode with key."""
        decoded = bytearray()
        key_len = len(key)
        for i, byte in enumerate(base64.b64decode(encoded)):
            decoded.append(byte ^ key[i % key_len])
        return decoded.decode('utf-8')
    
    @classmethod
    def _verify_integrity(cls, fee_str: str, component_str: str) -> bool:
        """Verify decoded values against pre-computed integrity hash."""
        import hashlib
        combined = f"{fee_str}|{component_str}"
        actual_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        if actual_hash != cls._integrity:
            raise RuntimeError(
                "CRITICAL: Fee configuration integrity check failed. "
                "Application has been tampered with. Refusing to start."
            )
        return True
    
    @classmethod
    def get_fee_percentage(cls) -> Decimal:
        """Get the fee percentage (0.1%)."""
        # Decode fee from parts
        fee_str = ''.join(cls._xor_decode(part, cls._key) for part in cls._fee_parts)
        
        # Get component for integrity check
        component_str = ''.join(
            cls._xor_decode(part, cls._key) for part in cls._component_parts
        )
        
        # Verify integrity
        cls._verify_integrity(fee_str, component_str)
        
        return Decimal(fee_str)
    
    @classmethod
    def get_fee_component_address(cls) -> str:
        """Get the fee component address."""
        # Decode component from parts
        component_str = ''.join(
            cls._xor_decode(part, cls._key) for part in cls._component_parts
        )
        
        # Get fee for integrity check
        fee_str = ''.join(cls._xor_decode(part, cls._key) for part in cls._fee_parts)
        
        # Verify integrity
        cls._verify_integrity(fee_str, component_str)
        
        return component_str


# Module-level lazy-loaded values
_fee_percentage = None
_fee_component_address = None


def get_fee_percentage() -> Decimal:
    """Get fee percentage with runtime validation."""
    global _fee_percentage
    if _fee_percentage is None:
        if _NATIVE_AVAILABLE:
            _fee_percentage = _native.get_fee_percentage()
        else:
            _fee_percentage = FeeConfig.get_fee_percentage()
    return _fee_percentage


def get_fee_component_address() -> str:
    """Get fee component address with runtime validation."""
    global _fee_component_address
    if _fee_component_address is None:
        if _NATIVE_AVAILABLE:
            _fee_component_address = _native.get_fee_component_address()
        else:
            _fee_component_address = FeeConfig.get_fee_component_address()
    return _fee_component_address


def verify_fee_integrity() -> bool:
    """
    Re-verify fee configuration integrity (bypass cache).
    
    Call this before each trade to ensure cached values haven't been
    tampered with at runtime via monkey-patching.
    
    Returns:
        bool: True if integrity check passes
    
    Raises:
        RuntimeError: If integrity check fails
    """
    if _NATIVE_AVAILABLE:
        status = _native.get_security_status()
        if not status.get('integrity_valid', False):
            raise RuntimeError("Native fee module integrity check failed")
        return True
    
    # Force fresh decode and verify (ignores cached values)
    return FeeConfig._verify_integrity(
        ''.join(FeeConfig._xor_decode(p, FeeConfig._key) for p in FeeConfig._fee_parts),
        ''.join(FeeConfig._xor_decode(p, FeeConfig._key) for p in FeeConfig._component_parts),
    )


def verify_manifest_contains_fee(manifest: str) -> bool:
    """
    Verify that a manifest contains the expected fee transfer.
    
    CRITICAL: Call this BEFORE signing any manifest from Astrolescent API.
    
    Args:
        manifest: The manifest string from Astrolescent API
    
    Returns:
        bool: True if manifest contains valid fee, False otherwise
    """
    if _NATIVE_AVAILABLE:
        return _native.verify_manifest_contains_fee(manifest)
    
    # Pure Python fallback
    component = get_fee_component_address()
    
    # Basic check: component address must be present
    if component not in manifest:
        logger.warning("Manifest verification FAILED: Fee component not found")
        return False
    
    # Check for deposit/transfer operation
    addr_pos = manifest.find(component)
    start = max(0, addr_pos - 200)
    end = min(len(manifest), addr_pos + 200)
    context = manifest[start:end].lower()
    
    valid_ops = ['deposit', 'try_deposit', 'call_method']
    if not any(op in context for op in valid_ops):
        logger.warning("Manifest verification FAILED: No valid deposit operation found")
        return False
    
    logger.debug("Manifest verification passed")
    return True


def is_native_module_available() -> bool:
    """Check if the native protection module is loaded."""
    return _NATIVE_AVAILABLE


def get_security_status() -> dict:
    """
    Get current security status for diagnostics.
    
    Returns:
        dict: Security status information
    """
    if _NATIVE_AVAILABLE:
        return _native.get_security_status()
    
    return {
        'native_module': False,
        'fallback_mode': True,
        'integrity_valid': True,  # Assume valid in fallback
    }
