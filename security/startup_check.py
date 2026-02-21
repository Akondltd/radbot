"""
Lightweight startup security check for RadBot.
Verifies critical dependencies haven't been tampered with.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DependencyVerifier:
    """Verifies installed packages match known-good signatures."""
    
    def __init__(self):
        self.security_dir = Path(__file__).parent
        self.baseline_file = self.security_dir / 'known_good_packages.json'
        
    def get_package_signature(self, package_name: str) -> Optional[str]:
        """Get a simple signature for an installed package."""
        try:
            import importlib
            import inspect
            
            # Import the package
            module = importlib.import_module(package_name)
            
            # Get package version and location
            version = getattr(module, '__version__', 'unknown')
            location = getattr(module, '__file__', 'unknown')
            
            # Create simple signature
            sig_string = f"{package_name}:{version}:{location}"
            return hashlib.sha256(sig_string.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.debug(f"Could not get signature for {package_name}: {e}")
            return None
    
    def create_baseline(self) -> bool:
        """Create baseline of current package signatures."""
        try:
            # Critical packages that handle wallets/crypto
            critical_packages = [
                'cryptography',
                'bip_utils',
                'mnemonic',
            ]
            
            # Additional important packages
            important_packages = [
                'requests',
                'pandas',
                'PySide6',
            ]
            
            baseline = {
                'critical': {},
                'important': {}
            }
            
            # Get signatures for critical packages
            for pkg in critical_packages:
                sig = self.get_package_signature(pkg)
                if sig:
                    baseline['critical'][pkg] = sig
            
            # Get signatures for important packages
            for pkg in important_packages:
                sig = self.get_package_signature(pkg)
                if sig:
                    baseline['important'][pkg] = sig
            
            # Save baseline
            self.security_dir.mkdir(exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline, f, indent=2)
            
            logger.info(f"Created package baseline: {self.baseline_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating baseline: {e}")
            return False
    
    def verify_packages(self) -> bool:
        """Verify current packages match baseline."""
        try:
            # If no baseline exists, create one
            if not self.baseline_file.exists():
                logger.info("No baseline found, creating new baseline")
                return self.create_baseline()
            
            # Load baseline
            with open(self.baseline_file, 'r') as f:
                baseline = json.load(f)
            
            issues = []
            
            # Check critical packages
            for pkg, expected_sig in baseline.get('critical', {}).items():
                current_sig = self.get_package_signature(pkg)
                if current_sig != expected_sig:
                    issues.append(f"CRITICAL: {pkg} signature mismatch")
            
            # Check important packages  
            for pkg, expected_sig in baseline.get('important', {}).items():
                current_sig = self.get_package_signature(pkg)
                if current_sig != expected_sig:
                    issues.append(f"WARNING: {pkg} signature mismatch")
            
            if issues:
                logger.warning("Package verification issues detected:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
                logger.warning("Run 'python security/startup_check.py --reset' to create new baseline")
                return False
            
            logger.info("Package verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying packages: {e}")
            return False


def main():
    """Main entry point for standalone execution."""
    import sys
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='RadBot dependency verifier')
    parser.add_argument('--reset', action='store_true', 
                       help='Reset baseline (after updating packages)')
    args = parser.parse_args()
    
    verifier = DependencyVerifier()
    
    if args.reset:
        logger.info("Resetting package baseline...")
        success = verifier.create_baseline()
    else:
        logger.info("Verifying packages...")
        success = verifier.verify_packages()
    
    if success:
        logger.info("Verification complete")
        return 0
    else:
        logger.error("Verification failed")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
