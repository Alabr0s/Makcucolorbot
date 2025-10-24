"""
Spike Timer Tab
Tab that provides spike timer settings and control
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, 
                             QCheckBox, QHBoxLayout, QScrollArea, QSpinBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import mss
import numpy as np
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
        
        # Default settings
        self.time_tolerance = 5  # Range 0-5 (44 seconds for 5)
        self.is_enabled = True   # On/off control
        
        self.setup_ui()
        self.apply_styles()
        
        # Start
        self.start_scanning()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Single group - All settings
        main_group = self.create_main_group()
        
        # Add group to scroll area
        scroll_area.setWidget(main_group)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
    
    def create_main_group(self):
        """Single group containing all settings"""
        group = QGroupBox("")
        layout = QFormLayout(group)
        layout.setSpacing(18)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # On/Off checkbox
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.stateChanged.connect(self.toggle_scanning)
        layout.addRow("Active:", self.enable_checkbox)
        
        # Time tolerance slider
        tolerance_widget, self.tolerance_slider = self.create_modern_slider(0, 5, self.update_tolerance, 0, "")
        layout.addRow("Time Tolerance:", tolerance_widget)
        
        # Bilgi etiketi
        info_label = QLabel("If Time Tolerance is 5, countdown is 35:00")
        info_label.setStyleSheet("color: #a0a0a0; font-style: italic;")
        layout.addRow("", info_label)
        
        return group
    
    def create_modern_slider(self, min_val, max_val, on_change, default_val=0, unit=""):
        """Create modern designed slider"""
        return ModernSlider.create(min_val, max_val, on_change, default_val, unit)
    
    def apply_styles(self):
        """Server.py ile uyumlu mor tema stil uygula"""
        custom_style = """
        QScrollArea {
            border: none;
            background: transparent;
        }
        
        QGroupBox {
            color: white;
            font-weight: bold;
            font-size: 14px;
            border: 2px solid rgba(100, 100, 100, 0.4);
            border-radius: 10px;
            margin-top: 10px;
            padding-top: 10px;
            background: rgba(35, 35, 35, 80);
        }
        
        QGroupBox::title {
            color: #a0a0a0;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            font-weight: bold;
        }
        
        QCheckBox {
            color: white;
            font-weight: bold;
            spacing: 12px;
            font-size: 13px;
        }
        
        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border-radius: 12px;
            border: 3px solid rgba(70, 70, 70, 0.9);
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(50, 50, 50, 200), stop:1 rgba(30, 30, 30, 200));
        }
        
        QCheckBox::indicator:hover {
            border: 3px solid rgba(100, 100, 100, 1.0);
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(60, 60, 60, 220), stop:1 rgba(40, 40, 40, 220));
        }
        
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(160, 160, 160, 255), stop:1 rgba(120, 120, 120, 255));
            border: 3px solid rgba(180, 180, 180, 1.0);
        }
        
        QCheckBox::indicator:checked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(180, 180, 180, 255), stop:1 rgba(140, 140, 140, 255));
            border: 3px solid rgba(200, 200, 200, 1.0);
        }
        
        QLabel {
            color: white;
            font-family: 'Roboto', 'Arial';
            background: transparent;
            font-weight: bold;
            font-size: 13px;
        }
        
        QSlider::groove:horizontal {
            background: rgba(30, 30, 30, 200);
            height: 8px;
            border-radius: 4px;
            border: none;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(160, 160, 160, 255), 
                stop:0.5 rgba(180, 180, 180, 255),
                stop:1 rgba(160, 160, 160, 255));
            border: none;
            width: 26px;
            height: 26px;
            margin: -9px 0;
            border-radius: 13px;
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(180, 180, 180, 255), 
                stop:0.5 rgba(200, 200, 200, 255),
                stop:1 rgba(180, 180, 180, 255));
        }
        
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 100, 100, 255), 
                stop:0.5 rgba(140, 140, 140, 255),
                stop:1 rgba(120, 120, 120, 255));
            border-radius: 4px;
        }
        """
        
        self.setStyleSheet(custom_style)
    
    def toggle_scanning(self):
        """Enable/disable scanning"""
        self.is_enabled = self.enable_checkbox.isChecked()
        if self.is_enabled:
            self.start_scanning()
        else:
            self.stop_scanning()
    
    def start_scanning(self):
        """Start screen scanning"""
        if not self.is_scanning:
            self.screen_scanner_timer.start(1000 // 124)  # 124 FPS
            self.is_scanning = True
            # print("Spike Timer: Scanning started")
            
    def stop_scanning(self):
        """Stop screen scanning"""
        self.screen_scanner_timer.stop()
        self.is_scanning = False
        # print("Spike Timer: Scanning stopped")
    
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
                red_pixels = np.sum((img[:, :, 2] == 230) & (img[:, :, 1] == 0) & (img[:, :, 0] == 0))
                
                # Debug output
                # print(f"Spike Timer: {red_pixels} red pixels detected")
                
                # If more than 20 red pixels
                if red_pixels > 20:
                    # Show spike timer window
                    self.start_spike_timer()
                    
        except Exception as e:
            print(f"Spike timer scan error: {e}")
    
    def start_spike_timer(self):
        """Start spike timer window"""
        # Stop scanning
        self.was_scanning = self.is_scanning
        if self.is_scanning:
            self.stop_scanning()
        
        # Determine duration based on time tolerance
        # 00:00 for 0, 44:00 for 5 (seconds:milliseconds)
        base_seconds = self.time_tolerance * 8.8  # 0-44 seconds range (44 seconds for 5)
        duration_ms = int(base_seconds * 1000)  # Convert to milliseconds
        
        # print(f"Spike Timer: Starting timer with {base_seconds} seconds (tolerance: {self.time_tolerance})")
        
        # Show window even if duration is 0 (at least 1000ms)
        if duration_ms == 0:
            duration_ms = 1000  # At least 1 second
            
        if duration_ms > 0:
            self.spike_timer_window.start_timer(duration_ms)
    
    def update_tolerance(self):
        """Update time tolerance value"""
        self.time_tolerance = self.tolerance_slider.value()
    
    def on_timer_finished(self):
        """Called when timer finishes"""
        # print("Spike Timer: Timer finished, resuming scanning")
        # Continue scanning
        if self.was_scanning and self.is_enabled:
            self.start_scanning()
    
    def cleanup(self):
        """Cleanup operations"""
        self.stop_scanning()
        if self.spike_timer_window:
            self.spike_timer_window.close()