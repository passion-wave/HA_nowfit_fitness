"""Load pure integration modules without importing Home Assistant."""

import sys
import types
from pathlib import Path

ROOT = Path(__file__).parents[1]
CUSTOM_COMPONENTS = ROOT / "custom_components"
NOWFIT = CUSTOM_COMPONENTS / "nowfit"

custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(CUSTOM_COMPONENTS)]
sys.modules.setdefault("custom_components", custom_components)

nowfit = types.ModuleType("custom_components.nowfit")
nowfit.__path__ = [str(NOWFIT)]
sys.modules.setdefault("custom_components.nowfit", nowfit)
