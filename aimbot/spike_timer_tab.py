"""
Spike Timer Tab
Tab that provides spike timer settings and control
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, 
                             QCheckBox, QHBoxLayout, QScrollArea, QFrame, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import mss
import numpy as np
import time
from .spike_timer_window import SpikeTimerWindow
from .ui_components import ModernSlider


class SpikeTimerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.spike_timer_window = SpikeTimerWindow()
        # Callback to be called when timer finishes
        self.spike_timer_window.on_timer_finished = self.on_timer_finished
        self.screen_scanner_timer = QTimer()
        self.screen_scanner_timer.timeout.connect(self.scan_screen)
        self.is_scanning = False
        self.was_scanning = False  # Store previous state when scanning stops
        self.last_red_time = 0 # Track when we last saw the red indicator
        self.spike_active = False # Track if we believe spike is currently active
        
        # Default settings
        self.time_tolerance = 5  # Range 0-5 (44 seconds for 5)
        self.is_enabled = True   # On/off control
        
        self.setup_ui()
        
        # Start
        self.start_scanning()
        


    def toggle_scanning(self):
        """Enable/disable scanning"""
        self.is_enabled = self.enable_checkbox.isChecked()
        if self.is_enabled:
            self.start_scanning()
            self.status_label.setText("ACTIVE - SCANNING")
            self.status_label.setStyleSheet("background-color: #00cc66; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;")
        else:
            self.stop_scanning()
            self.spike_active = False
            self.spike_timer_window.stop_timer()
            self.status_label.setText("INACTIVE")
            self.status_label.setStyleSheet("background-color: #2d2d2d; color: #666; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;")
    
    def start_scanning(self):
        """Start screen scanning"""
        if not self.is_scanning:
            self.screen_scanner_timer.start(1000 // 124)  # 124 FPS
            self.is_scanning = True
            
    def stop_scanning(self):
        """Stop screen scanning"""
        self.screen_scanner_timer.stop()
        self.is_scanning = False
    
    def scan_screen(self):
        """Scan screen and look for spike"""
        if not self.is_enabled:
            return
            
        try:
            with mss.mss() as sct:
                # Scan 80x80 pixels at the top center of screen
                screen = sct.monitors[1]  # Main monitor
                center_x = screen['width'] // 2
                center_y = 0  # Top
                
                # 80x80 area
                monitor = {
                    'top': center_y,
                    'left': center_x - 40,
                    'width': 80,
                    'height': 80
                }
                
                # Take screenshot
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                
                # Look for RGB(230, 0, 0) color (in BGR format)
                # Note: mss returns BGRA
                # R is index 2, G is 1, B is 0
                # Using a slightly wider threshold for robustness
                red_pixels = np.sum((img[:, :, 2] > 180) & (img[:, :, 1] < 70) & (img[:, :, 0] < 70))
                
                is_red_present = red_pixels > 20
                
                current_time = time.time()
                
                if is_red_present:
                    self.last_red_time = current_time
                
                # State Logic
                if not self.spike_active:
                    # If we see red, start the timer
                    if is_red_present:
                        self.start_spike_timer()
                else:
                    # Timer is active, check if we lost the signal
                    # If red is NOT present
                    if not is_red_present:
                        # Check how long it has been missing
                        if (current_time - self.last_red_time) > 2.0:
                            # Missing for > 1 second, abort
                            self.spike_timer_window.stop_timer()
                            self.spike_active = False
                            # print("Spike timer aborted: Signal lost")

        except Exception as e:
            print(f"Spike timer scan error: {e}")
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #333;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        header_layout.setSpacing(15)
        
        title_label = QLabel("SPIKE TIMER")
        title_label.setStyleSheet("color: #fff; font-size: 20px; font-weight: 900; letter-spacing: 2px;")
        
        # Status Badge
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setStyleSheet("""
            background-color: #2d2d2d; 
            color: #666; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-weight: bold; 
            font-size: 10px;
            letter-spacing: 1px;
        """)
        
        # Toggle Switch
        self.enable_checkbox = QCheckBox("ACTIVATE")
        self.enable_checkbox.setCursor(Qt.PointingHandCursor)
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.setStyleSheet("""
            QCheckBox { color: #fff; font-weight: bold; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 36px; height: 18px; border-radius: 9px; background: #333; }
            QCheckBox::indicator:checked { background: #00cc66; }
        """)
        self.enable_checkbox.stateChanged.connect(self.toggle_scanning)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.enable_checkbox)
        
        main_layout.addWidget(header_frame)
        
        # --- Content Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background: #121212;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # Instructions / Info Card
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #181818; border-radius: 10px; border: 1px solid #333;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        info_icon = QLabel("💡")
        info_icon.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        
        info_text = QLabel("The Spike Timer automatically detects the red spike indicator on your screen and starts a countdown. Use the tolerance slider below to adjust the exact countdown duration.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #aaa; font-size: 13px; background: transparent; border: none;")
        
        info_layout.addWidget(info_icon)
        info_layout.addSpacing(15)
        info_layout.addWidget(info_text)
        
        content_layout.addWidget(info_frame)
        
        # Settings Section
        settings_label = QLabel("CONFIGURATION")
        settings_label.setStyleSheet("color: #666; font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        content_layout.addWidget(settings_label)
        
        settings_frame = QFrame()
        settings_frame.setStyleSheet("background-color: #181818; border-radius: 15px;")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(25, 25, 25, 25)
        settings_layout.setSpacing(20)
        
        # Tolerance Slider
        slider_container, self.tolerance_slider = self.create_slider("Time Tolerance (35s - 45s)", 0, 5, 0, "")
        
        note_label = QLabel("Adjustment: 0 = 45s, 5 = 35s")
        note_label.setStyleSheet("color: #555; font-size: 11px; margin-top: -10px;")
        
        settings_layout.addWidget(slider_container)
        settings_layout.addWidget(note_label)
        
        content_layout.addWidget(settings_frame)
        
        # Test Button
        test_btn = QPushButton("TEST TIMER HUD")
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.setFixedHeight(45)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #fff;
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #252525;
                border: 1px solid #555;
            }
            QPushButton:pressed {
                background-color: #00cc66;
                color: #000;
            }
        """)
        test_btn.clicked.connect(lambda: self.spike_timer_window.start_timer(10000)) # 10s test
        content_layout.addWidget(test_btn)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Update status initial
        self.toggle_scanning()

    def create_slider(self, label_text, min_val, max_val, default_val, unit):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        header = QHBoxLayout()
        header_lbl = QLabel(label_text)
        header_lbl.setStyleSheet("color: #ccc; font-weight: 600; font-size: 12px;")
        
        val_lbl = QLabel(f"{default_val}{unit}")
        val_lbl.setStyleSheet("color: #fff; font-weight: bold; font-family: monospace;")
        
        header.addWidget(header_lbl)
        header.addStretch()
        header.addWidget(val_lbl)
        
        slider = ModernSlider.create(min_val, max_val, self.update_tolerance, default_val, unit)
        # Assuming ModernSlider.create returns a tuple (container, slider) or just slider. 
        # Checking existing code: create_modern_slider returned (widget, slider). 
        # ModernSlider.create returns (widget, slider) based on previous context.
        # But wait, create_modern_slider in original file called ModernSlider.create...
        
        # To be safe and consistent with the new unified look, let's make a manual slider here 
        # or adapt the returned widget.
        # Let's use the new slider style used in other tabs for consistency.
        
        from PyQt5.QtWidgets import QSlider
        new_slider = QSlider(Qt.Horizontal)
        new_slider.setRange(min_val, max_val)
        new_slider.setValue(default_val)
        new_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #333; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00cc66; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
        """)
        new_slider.valueChanged.connect(self.update_tolerance)
        new_slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}{unit}"))
        
        layout.addLayout(header)
        layout.addWidget(new_slider)
        
        # Note: Previous implementation might have logic mapping 0-5 to seconds display?
        # The logic is in update_tolerance/start_spike_timer.
        
        return container, new_slider

    
    def start_spike_timer(self):
        """Start spike timer window"""
        # Do NOT stop scanning, we want to monitor presence
        self.spike_active = True
        self.was_scanning = self.is_scanning
        
        # Fixed to 45 seconds as per user request
        # Previous logic: seconds = 45 - (self.time_tolerance * 2)
        seconds = 44.30
        duration_ms = int(seconds * 1000)
        
        if duration_ms > 0:
            self.spike_timer_window.start_timer(duration_ms)
    
    def update_tolerance(self):
        """Update time tolerance value"""
        self.time_tolerance = self.tolerance_slider.value()
    
    def on_timer_finished(self):
        """Called when timer finishes"""
        # Continue scanning
        if self.was_scanning and self.is_enabled:
            self.start_scanning()
    
    def get_settings(self):
        """Get settings for config"""
        return {
            "active": "true" if self.enable_checkbox.isChecked() else "false",
            "time_tolerance": str(self.tolerance_slider.value())
        }
        
    def load_settings(self, settings):
        """Load settings from config"""
        if "active" in settings:
            self.enable_checkbox.setChecked(settings["active"] == "true")
            
        if "time_tolerance" in settings:
            val = int(settings["time_tolerance"])
            self.tolerance_slider.setValue(val)
            
    def cleanup(self):
        """Cleanup operations"""
        self.stop_scanning()
        if self.spike_timer_window:
            self.spike_timer_window.close()