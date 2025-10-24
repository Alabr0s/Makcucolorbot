"""
Utils Package - MVC Pattern
Yardımcı fonksiyonlar ve araçlar
"""

# Güvenli import'lar
from .utils import GlobalKeyListener
try:
    from .mouse_detector import MouseEventDetector
except ImportError:
    print("Mouse detector not available")
    MouseEventDetector = None
# AimTCPClient now comes from tcp_client module for global configuration
try:
    from tcp_client import AimTCPClient
except ImportError:
    # Fallback to utils version if tcp_client is not available
    from .utils import AimTCPClient

# Notification sistemi - direct import
try:
    from .notification_system import notification_manager, show_success, show_warning, show_error, show_info
except ImportError as e:
    print(f"Notification system import error: {e}")
    # Fallback functions
    def notification_manager():
        pass
    def show_success(*args, **kwargs):
        print(f"SUCCESS: {args}")
    def show_warning(*args, **kwargs):
        print(f"WARNING: {args}")
    def show_error(*args, **kwargs):
        print(f"ERROR: {args}")
    def show_info(*args, **kwargs):
        print(f"INFO: {args}")

# Status bar - direct import
try:
    from .modern_status_bar import ModernStatusBar, StatusBarManager
except ImportError as e:
    print(f"Status bar import error: {e}")
    ModernStatusBar = None
    StatusBarManager = None

__all__ = [
    'GlobalKeyListener', 'MouseEventDetector', 'AimTCPClient',
    'notification_manager', 'show_success', 'show_warning', 'show_error', 'show_info',
    'ModernStatusBar', 'StatusBarManager'
]