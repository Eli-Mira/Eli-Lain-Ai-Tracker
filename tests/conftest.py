"""Pytest configuration for news tracker."""

import sys
from pathlib import Path

# Add repo src trees to path (intel_sources, tracker_core)
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tracker-core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
