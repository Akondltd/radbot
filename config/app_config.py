from pathlib import Path
from typing import Optional

from config.paths import PACKAGE_ROOT, USER_DATA_DIR

def get_absolute_path(relative_path: Optional[str]) -> Optional[Path]:
    """Converts a relative path to an absolute path.

    Checks USER_DATA_DIR first (writable, e.g. cached icons), then falls
    back to PACKAGE_ROOT (read-only package assets / seed icons).
    In dev mode the two are the same directory so behaviour is unchanged.
    """
    if not relative_path:
        return None
    # Prefer user-writable data dir (cached icons, etc.)
    user_path = USER_DATA_DIR / relative_path
    if user_path.is_file():
        return user_path
    # Fall back to package assets (seed icons, default images)
    return PACKAGE_ROOT / relative_path
