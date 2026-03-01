"""
Centralised path resolution for RadBot.

Two categories of paths:
  1. PACKAGE_ROOT  – read-only assets shipped with the package (images, QSS, docs, configs)
  2. USER_DATA_DIR – writable per-user directory for runtime data (database, logs, wallet files)

When running from source (development), USER_DATA_DIR falls back to
the project root so behaviour is unchanged for developers.
"""

import os
import sys
from pathlib import Path

from platformdirs import user_data_dir

# ── Package root (where the source code lives) ──
PACKAGE_ROOT = Path(__file__).resolve().parent.parent

# ── User-writable data directory ──
# In development (running from source), keep data next to the code.
# In an installed package, use the platform-standard user data dir.
_APP_NAME = "radbot"

def _is_dev_mode() -> bool:
    """Return True when running directly from the source tree (not pip-installed)."""
    # If main.py is in PACKAGE_ROOT and there's no dist-info, we're in dev mode
    return (PACKAGE_ROOT / "main.py").exists() and not any(
        p.name.startswith("radbot-") and p.name.endswith(".dist-info")
        for p in PACKAGE_ROOT.iterdir()
        if p.is_dir()
    )

if _is_dev_mode():
    USER_DATA_DIR = PACKAGE_ROOT
else:
    USER_DATA_DIR = Path(user_data_dir(_APP_NAME))

# ── Derived paths ──
DATA_DIR = USER_DATA_DIR / "data"
LOGS_DIR = USER_DATA_DIR / "logs"
CONFIG_DIR = USER_DATA_DIR / "config"
DATABASE_NAME = "radbot.db"
DATABASE_PATH = DATA_DIR / DATABASE_NAME

# ── Asset paths (always relative to the installed package) ──
IMAGES_DIR = PACKAGE_ROOT / "images"
DOCS_DIR = PACKAGE_ROOT / "docs"
LIBS_DIR = PACKAGE_ROOT / "libs"
STYLES_DIR = PACKAGE_ROOT / "gui" / "styling"

# ── Bundled config (shipped inside the package) ──
_BUNDLED_CONFIG = PACKAGE_ROOT / "config" / "advanced_config.json"
USER_CONFIG = CONFIG_DIR / "advanced_config.json"


def ensure_dirs():
    """Create writable directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _seed_config()


def _seed_config():
    """Copy bundled advanced_config.json to USER_DATA_DIR on first run."""
    if not USER_CONFIG.exists() and _BUNDLED_CONFIG.exists():
        import shutil
        shutil.copy2(_BUNDLED_CONFIG, USER_CONFIG)
