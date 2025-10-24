"""
Mouse Event Detection for RCS System
Detects left mouse button press/release events
"""

import time
import threading
from PyQt5.QtCore import QThread, pyqtSignal

try:
    import win32api
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    print("Warning: win32api not available, RCS mouse detection disabled")
    WINDOWS_AVAILABLE = False

class MouseEventDetector(QThread):
    """Detects mouse events for RCS system"""
    mouse_event = pyqtSignal(bool)  # True for press, False for release
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.left_button_pressed = False
        
    def run(self):
        """Main thread loop for mouse detection"""
        if not WINDOWS_AVAILABLE:
            return
            
        self.running = True
        
        while self.running:
            try:
                # Check left mouse button state
                left_state = win32api.GetAsyncKeyState(win32con.VK_LBUTTON)
                is_pressed = (left_state & 0x8000) != 0
                
                # Detect state changes
                if is_pressed and not self.left_button_pressed:
                    # Mouse just pressed
                    self.left_button_pressed = True
                    self.mouse_event.emit(True)
                elif not is_pressed and self.left_button_pressed:
                    # Mouse just released
                    self.left_button_pressed = False
                    self.mouse_event.emit(False)
                
                time.sleep(0.001)  # 1ms polling rate for responsiveness
                
            except Exception as e:
                print(f"Mouse detection error: {e}")
                time.sleep(0.01)
    
    def stop(self):
        """Stop the mouse detection thread"""
        self.running = False
        self.wait()