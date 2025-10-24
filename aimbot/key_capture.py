"""
Key capture module
Handles key binding and capture functionality
"""

import time
import threading
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSignal, QTimer, QMetaObject, Qt, pyqtSlot
from controllers.theme_controller import WindowColorManager

try:
    import pynput.mouse
    import pynput.keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("pynput library not found. Advanced key capture feature may not work.")


class KeyCaptureButton(QPushButton):
    """Key capture button"""
    key_captured = pyqtSignal(str)
    
    def __init__(self, current_key="f"):
        super().__init__()
        self.current_key = current_key
        self.is_capturing = False
        self.color_manager = WindowColorManager()
        
        # To store listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        self.capture_thread = None
        
        # Key mapping dictionary - Including mouse buttons
        self.key_mapping = {
            # Mouse buttons
            'left': 'Left Mouse (L)',
            'right': 'Right Mouse (R)', 
            'middle': 'Middle Mouse (M)',
            'x1': 'Mouse X1 (Side)',
            'x2': 'Mouse X2 (Side)',
            'scroll_up': 'Mouse Wheel ↑',
            'scroll_down': 'Mouse Wheel ↓',
            # Keyboard keys
            'ctrl': 'Ctrl',
            'alt': 'Alt',
            'shift': 'Shift',
            'space': 'Space',
            'tab': 'Tab',
            'enter': 'Enter',
            'esc': 'Esc',
            'caps lock': 'Caps Lock',
            'cmd': 'Cmd',
            'page up': 'Page Up',
            'page down': 'Page Down',
            'home': 'Home',
            'end': 'End',
            'insert': 'Insert',
            'delete': 'Delete',
            'backspace': 'Backspace',
            'num lock': 'Num Lock',
            'scroll lock': 'Scroll Lock',
            'pause': 'Pause',
            'print screen': 'Print Screen',
            # Function keys
            'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4',
            'f5': 'F5', 'f6': 'F6', 'f7': 'F7', 'f8': 'F8',
            'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12'
        }
        
        self.setProperty('capturing', 'false')
        self.update_text()
        self.clicked.connect(self.start_capture)
    
    def __del__(self):
        """Clean up when widget is deleted"""
        try:
            self.is_capturing = False
            self._cleanup_listeners()
        except:
            pass
    
    def closeEvent(self, event):
        """Clean up when widget is closed"""
        try:
            self.is_capturing = False
            self._cleanup_listeners()
        except:
            pass
        super().closeEvent(event)
    
    def update_text(self):
        """Update button text"""
        display_name = self.key_mapping.get(self.current_key.lower(), self.current_key.upper())
        
        if self.is_capturing:
            self.setText("Press Key...")
            self.setProperty('capturing', 'true')
        else:
            self.setText(display_name)
            self.setProperty('capturing', 'false')
        
        # Apply purple theme style compatible with server.py
        if self.is_capturing:
            style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 215, 0, 150), stop:1 rgba(255, 193, 7, 150));
                    border: 2px solid rgba(255, 215, 0, 0.8);
                    border-radius: 12px;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    margin: 2px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 215, 0, 200), stop:1 rgba(255, 193, 7, 200));
                }
            """
        else:
            style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(90, 90, 90, 120), stop:1 rgba(70, 70, 70, 120));
                    border: 1px solid rgba(110, 110, 110, 0.6);
                    border-radius: 12px;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    margin: 2px;
                    min-height: 20px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(110, 110, 110, 180), stop:1 rgba(90, 90, 90, 180));
                    border: 1px solid rgba(120, 120, 120, 0.8);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(70, 70, 70, 200), stop:1 rgba(90, 90, 90, 200));
                }
            """
        
        self.setStyleSheet(style)
        
        # Re-apply style
        self.style().unpolish(self)
        self.style().polish(self)
    
    def start_capture(self):
        """Start key capture"""
        if self.is_capturing:
            return
        
        try:
            # Clean up previous listeners
            self._cleanup_listeners()
            
            self.is_capturing = True
            self.update_text()
            
            # Listen for keys in separate thread
            self.capture_thread = threading.Thread(target=self.capture_key, daemon=True)
            self.capture_thread.start()
            
        except Exception as e:
            print(f"Key capture start error: {e}")
            self.is_capturing = False
            self.update_text()
    
    def capture_key(self):
        """Capture key"""
        if not PYNPUT_AVAILABLE:
            print("pynput library is required. Install with pip install pynput.")
            try:
                QMetaObject.invokeMethod(self, "_capture_failed", Qt.QueuedConnection)
            except Exception as e:
                print(f"Failed invoke error (pynput): {e}")
                QTimer.singleShot(0, self._capture_failed)
            return
            
        try:
            # Hook for mouse buttons - Enhanced mouse support
            def on_mouse_click(x, y, button, pressed):
                if pressed and self.is_capturing:
                    try:
                        # Normalize mouse button name
                        button_str = str(button).lower()
                        
                        # Check pynput Button enum
                        if 'button.left' in button_str:
                            button_name = 'left'
                        elif 'button.right' in button_str:
                            button_name = 'right'
                        elif 'button.middle' in button_str:
                            button_name = 'middle'
                        elif 'button.x1' in button_str:
                            button_name = 'x1'
                        elif 'button.x2' in button_str:
                            button_name = 'x2'
                        else:
                            # Fallback: take after last dot
                            button_name = button_str.split('.')[-1] if '.' in button_str else button_str
                        
                        print(f"🔎 Mouse button detected: {button_str} -> {button_name}")
                        self.finish_capture(button_name)
                        return False  # Stop hook
                    except Exception as e:
                        print(f"Mouse click handler error: {e}")
                        return False
            
            # Separate handler for mouse scroll
            def on_mouse_scroll(x, y, dx, dy):
                if self.is_capturing:
                    try:
                        if dy > 0:
                            scroll_name = 'scroll_up'
                        else:
                            scroll_name = 'scroll_down'
                        
                        print(f"🔎 Mouse scroll detected: {scroll_name}")
                        self.finish_capture(scroll_name)
                        return False
                    except Exception as e:
                        print(f"Mouse scroll handler error: {e}")
                        return False
            
            # Hook for keyboard keys
            def on_key_press(key):
                if self.is_capturing:
                    try:
                        # Special keys
                        if hasattr(key, 'name'):
                            key_name = key.name
                        elif hasattr(key, 'char') and key.char:
                            key_name = key.char
                        else:
                            key_name = str(key).replace('Key.', '')
                        
                        self.finish_capture(key_name)
                        return False  # Stop hook
                    except Exception as e:
                        print(f"Key press handler error: {e}")
                        return False
            
            # Start mouse listener - With click and scroll support
            import pynput.mouse as mouse
            import pynput.keyboard as kb
            
            print("🔎 Starting mouse and keyboard listeners...")
            
            self.mouse_listener = mouse.Listener(
                on_click=on_mouse_click,
                on_scroll=on_mouse_scroll
            )
            self.keyboard_listener = kb.Listener(on_press=on_key_press)
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            # 10 second timeout
            timeout = 100  # 10 seconds (0.1 * 100)
            while self.is_capturing and timeout > 0:
                time.sleep(0.1)
                timeout -= 1
            
            # Cleanup
            self._cleanup_listeners()
            
            if self.is_capturing:  # Timeout occurred
                try:
                    QMetaObject.invokeMethod(self, "_capture_timeout", Qt.QueuedConnection)
                except Exception as e:
                    print(f"Timeout invoke error: {e}")
                    QTimer.singleShot(0, self._capture_timeout)
                
        except Exception as e:
            print(f"Key capture error: {e}")
            self._cleanup_listeners()
            try:
                QMetaObject.invokeMethod(self, "_capture_failed", Qt.QueuedConnection)
            except Exception as invoke_error:
                print(f"Failed invoke error (exception): {invoke_error}")
                QTimer.singleShot(0, self._capture_failed)
    
    def _cleanup_listeners(self):
        """Clean up listeners"""
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
        except:
            pass
        
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
        except:
            pass
    
    @pyqtSlot()
    def _capture_timeout(self):
        """Called when timeout occurs"""
        if self.is_capturing:
            self.is_capturing = False
            self.update_text()
    
    @pyqtSlot()
    def _capture_failed(self):
        """Called when capture fails"""
        if self.is_capturing:
            self.is_capturing = False
            self.update_text()
    
    def finish_capture(self, key_name):
        """Finish key capture"""
        if not self.is_capturing:
            return
            
        self.is_capturing = False
        
        # Clean and normalize key name
        clean_key = str(key_name).lower().strip()
        
        # Common key name corrections - Mouse and keyboard
        key_normalizations = {
            # Keyboard keys
            'alt_l': 'alt',
            'alt_r': 'alt',
            'ctrl_l': 'ctrl', 
            'ctrl_r': 'ctrl',
            'shift_l': 'shift',
            'shift_r': 'shift',
            'cmd_l': 'cmd',
            'cmd_r': 'cmd',
            'caps_lock': 'caps lock',
            'page_up': 'page up',
            'page_down': 'page down',
            'num_lock': 'num lock',
            'scroll_lock': 'scroll lock',
            # Mouse buttons - normalize from pynput format
            'button.left': 'left',
            'button.right': 'right',
            'button.middle': 'middle',
            'button.x1': 'x1',
            'button.x2': 'x2',
            # Mouse wheel
            'scroll.up': 'scroll_up',
            'scroll.down': 'scroll_down'
        }
        
        self.current_key = key_normalizations.get(clean_key, clean_key)
        
        # Simple and safe UI update
        QTimer.singleShot(0, self._update_ui_after_capture)
    
    def _safe_invoke_ui_update(self):
        """Safely invoke UI update"""
        try:
            # First try QMetaObject.invokeMethod
            QMetaObject.invokeMethod(self, "_update_ui_after_capture", Qt.QueuedConnection)
        except Exception as e:
            print(f"QMetaObject.invokeMethod error: {e}")
            try:
                # Alternative: Use QTimer
                QTimer.singleShot(0, self._update_ui_after_capture)
            except Exception as timer_error:
                print(f"QTimer.singleShot error: {timer_error}")
                # Last resort: call directly (may not be thread-safe)
                try:
                    self._update_ui_after_capture()
                except Exception as direct_error:
                    print(f"Direct call error: {direct_error}")
    
    @pyqtSlot()
    def _update_ui_after_capture(self):
        """Update UI in main thread"""
        try:
            # Check if widget is still valid
            if not self or not hasattr(self, 'current_key'):
                return
                
            self.update_text()
            
            # Check widget status before emitting signal
            if hasattr(self, 'key_captured') and self.key_captured:
                self.key_captured.emit(self.current_key)
                
        except RuntimeError as e:
            # Widget may have been deleted
            print(f"Widget runtime error: {e}")
        except Exception as e:
            print(f"UI update error: {e}")