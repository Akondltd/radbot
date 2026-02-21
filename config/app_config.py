from pathlib import Path
from typing import Optional

from config.paths import PACKAGE_ROOT as APP_ROOT

def get_absolute_path(relative_path: Optional[str]) -> Optional[Path]:
    """Converts a relative path from the project root to an absolute path."""
    if not relative_path:
        return None
    # Ensure the input is treated as a relative path
    return APP_ROOT.joinpath(relative_path)
