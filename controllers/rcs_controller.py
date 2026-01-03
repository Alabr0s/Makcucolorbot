"""
RCS Controller
Manages the Recoil Control System logic and TCP communication
"""

import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from models.weapon_patterns import WeaponDatabase
from tcp_client import get_global_tcp_client

try:
    from utils.mouse_detector import MouseEventDetector
    MOUSE_DETECTOR_AVAILABLE = True
except ImportError:
    print("Warning: Mouse detector not available")
    MOUSE_DETECTOR_AVAILABLE = False

class RCSWorker(QThread):
    """Worker thread for executing RCS patterns and reset"""
    # Signals to update UI
    status_signal = pyqtSignal(str, str) # message, type
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = False
        self.resetting = False
        
    def run(self):
        self.running = True
        self.status_signal.emit("RCS Engine Started", "success")
        
        while self.running:
            try:
                current_time = time.time() * 1000
                
                # 1. Active Firing and Recoil Control
                if (self.controller.enabled and 
                    self.controller.mouse_pressed and 
                    self.controller.current_weapon):
                    
                    # Stop any pending reset if user starts firing again
                    self.resetting = False
                    
                    
                    # DELAY LOGIC: Wait 160ms (Tap Protection) before starting RCS
                    # This allows "One Taps" without pulldown, but catches the spray (Bullet 3+)
                    if (current_time - self.controller.click_start_time) >= 160:
                        self.process_recoil()
                
                # 2. Reset Phase (Mouse released)
                elif self.controller.enabled and not self.controller.mouse_pressed:
                    
                    # Start reset phase if enabled and recoil exists
                    if (self.controller.recoil_reset_enabled and 
                        not self.resetting and 
                        self.controller.accumulated_recoil_y > 0):
                        
                        self.resetting = True
                        self.controller.reset_pattern()
                    
                    if self.resetting:
                        self.process_reset()
                    else:
                        # Safety: if reset disabled or done, clear accumulation
                        if not self.controller.recoil_reset_enabled:
                            self.controller.accumulated_recoil_y = 0
                
                time.sleep(0.005) # 200 Hz update rate
                
            except Exception as e:
                print(f"RCS Loop Error: {e}")
                time.sleep(1)
                
    def process_recoil(self):
        """Execute one step of the recoil pattern if timing is right"""
        weapon = self.controller.current_weapon
        pattern = weapon.pattern
        idx = self.controller.pattern_index
        
        if idx >= len(pattern):
            return
            
        offset_x, offset_y, duration = pattern[idx]
        current_time = time.time() * 1000
        
        # Check if enough time passed since last shot/step
        if current_time - self.controller.last_step_time >= duration:
            # Send movement
            self.controller.send_movement(offset_x, offset_y, is_recoil=True)
            
            # Advance pattern
            self.controller.last_step_time = current_time
            self.controller.pattern_index += 1

    def process_reset(self):
        """Instantly return mouse to original vertical position"""
        if self.controller.accumulated_recoil_y <= 0:
            self.resetting = False
            return
            
        # INSTANT RESET (User Request)
        # Send the entire accumulated distance in one go
        pixels_to_return = self.controller.accumulated_recoil_y
        
        self.controller.send_movement(0, -pixels_to_return, is_recoil=False)
        self.controller.accumulated_recoil_y = 0
        self.resetting = False
        print("RCS: Instant Reset Complete")

class RCSController(QObject):
    """
    Controller for RCS
    Separates logic from UI
    """
    # Signals
    connection_status_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.db = WeaponDatabase()
        
        # State
        self.enabled = False
        self.mouse_pressed = False
        self.current_weapon = self.db.get_weapon("Vandal")
        self.recoil_strength = 100
        
        # New Feature Flags
        self.recoil_reset_enabled = True
        
        # Pattern State
        self.pattern_index = 0
        self.last_step_time = 0
        self.accumulated_recoil_y = 0 # Track total downward movement
        self.click_start_time = 0 # Track when click started
        
        # Components
        self.tcp_client = get_global_tcp_client()
        self.worker = RCSWorker(self)
        
        # Mouse Detector
        self.mouse_detector = None
        if MOUSE_DETECTOR_AVAILABLE:
            self.mouse_detector = MouseEventDetector()
            self.mouse_detector.mouse_event.connect(self.on_mouse_event)
            
    def start(self):
        """Start the system"""
        if self.mouse_detector:
            self.mouse_detector.start()
        self.worker.start()
        
    def stop(self):
        """Stop the system"""
        self.worker.running = False
        if self.mouse_detector:
            self.mouse_detector.stop()
        self.worker.wait()
        
    def on_mouse_event(self, pressed):
        """Handle global mouse events"""
        if pressed:
            self.mouse_pressed = True
            current_time = time.time() * 1000
            self.click_start_time = current_time
            self.last_step_time = current_time
            self.pattern_index = 0
            # Reset accumulated recoil only on NEW press
            self.accumulated_recoil_y = 0 
            print("RCS: Mouse Pressed")
        else:
            self.mouse_pressed = False
            self.reset_pattern()
            print("RCS: Mouse Released")

    def reset_pattern(self):
        self.pattern_index = 0
        
    def set_enabled(self, enabled):
        self.enabled = enabled
        print(f"RCS Enabled: {enabled}")
        
    def set_reset_enabled(self, enabled):
        self.recoil_reset_enabled = enabled
        print(f"RCS Reset Enabled: {enabled}")
        
    def set_weapon(self, weapon_name):
        self.current_weapon = self.db.get_weapon(weapon_name)
        self.reset_pattern()
        print(f"RCS Weapon: {weapon_name}")
        
    def set_strength(self, percent):
        self.recoil_strength = max(0, min(100, percent))
        
    def send_movement(self, x, y, is_recoil=True):
        """Send TCP movement command"""
        if not self.tcp_client:
            return
            
        if is_recoil:
            strength_factor = self.recoil_strength / 100.0
            final_x = int(x * strength_factor)
            final_y = int(y * strength_factor)
        else:
            # For reset, raw values
            final_x = x
            final_y = y
            
        if final_x == 0 and final_y == 0:
            return
            
        if is_recoil:
             self.accumulated_recoil_y += final_y
            
        # Debug Log
        # print(f"RCS Sending: {final_x}, {final_y}")
        
        try:
            success = self.tcp_client.send_movement(final_x, final_y)
            self.connection_status_changed.emit(success)
        except Exception as e:
            print(f"RCS Send Error: {e}")
            self.connection_status_changed.emit(False)
