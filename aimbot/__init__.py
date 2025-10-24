"""
Aimbot package initialization
Exports main components for easy importing
"""

from .screen_scanner import ScreenScanner
from .mouse_controller import MouseController
from .indicator_window import IndicatorWindow
from .key_capture import KeyCaptureButton
from .ui_components import ModernSlider, StyleManager, ColorPicker
from .aimbot_tab import AimbotTab
from .spike_timer_tab import SpikeTimerTab

__all__ = [
    'AimbotTab',
    'SpikeTimerTab',
    'ScreenScanner',
    'MouseController', 
    'IndicatorWindow',
    'KeyCaptureButton',
    'ModernSlider',
    'StyleManager',
    'ColorPicker'
]