"""
Automated dependency security checker for RadBot.
Runs pip-audit and safety checks to detect vulnerable packages.
"""
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pip_audit():
    """Run pip-audit to check for known vulnerabilities."""
    logger.info("Running pip-audit security scan...")
    try:
        result = subprocess.run(
            ['pip-audit', '--desc'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ pip-audit: No known vulnerabilities found")
            return True
        else:
            logger.error("✗ pip-audit found vulnerabilities:")
            logger.error(result.stdout)
            return False
            
    except FileNotFoundError:
        logger.error("pip-audit not installed. Run: pip install pip-audit")
        return False
    except subprocess.TimeoutExpired:
        logger.error("pip-audit timed out after 60 seconds")
        return False
    except Exception as e:
        logger.error(f"Error running pip-audit: {e}")
        return False


def run_safety_check():
    """Run safety check against known vulnerability database."""
    logger.info("Running safety security scan...")
    try:
        # Get path to requirements file
        from config.paths import PACKAGE_ROOT
        req_file = PACKAGE_ROOT / 'requirements.txt'
        
        result = subprocess.run(
            ['safety', 'check', '--file', str(req_file), '--output', 'text'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ safety: No known vulnerabilities found")
            return True
        else:
            logger.warning("✗ safety found potential issues:")
            logger.warning(result.stdout)
            return False
            
    except FileNotFoundError:
        logger.error("safety not installed. Run: pip install safety")
        return False
    except subprocess.TimeoutExpired:
        logger.error("safety check timed out after 60 seconds")
        return False
    except Exception as e:
        logger.error(f"Error running safety: {e}")
        return False


def main():
    """Run all security checks."""
    logger.info("=" * 60)
    logger.info("RADBOT DEPENDENCY SECURITY CHECK")
    logger.info("=" * 60)
    
    pip_audit_ok = run_pip_audit()
    safety_ok = run_safety_check()
    
    logger.info("=" * 60)
    
    if pip_audit_ok and safety_ok:
        logger.info("✓ ALL SECURITY CHECKS PASSED")
        return 0
    else:
        logger.warning("✗ SECURITY ISSUES DETECTED - Review output above")
        logger.warning("Consider updating vulnerable packages or reviewing risks")
        return 1


if __name__ == '__main__':
    sys.exit(main())
