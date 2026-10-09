"""
Conftest configuration for archived modules.
Adds _archive and repository root to sys.path for standalone testing of archived packages.
"""

import sys
from pathlib import Path

ARCHIVE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ARCHIVE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(ARCHIVE_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_DIR))
