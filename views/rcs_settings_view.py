"""
RCS (Recoil Control System) Settings View
Provides UI controls for recoil control configuration
"""

import time
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QSpinBox, QCheckBox, QGroupBox, QGridLayout,
    QFrame, QComboBox, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import qtawesome as qta

try:
    from tcp_client import get_global_tcp_client
except ImportError:
    print("Warning: TCP client not available for RCS")
    get_global_tcp_client = lambda: None

try:
    from utils.mouse_detector import MouseEventDetector
except ImportError:
    print("Warning: Mouse detector not available for RCS")
    MouseEventDetector = None

class RCSWorker(QThread):
    """Worker thread for RCS functionality"""
    status_updated = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.rcs_enabled = False
        self.pull_speed = 5
        self.mouse_pressed = False
        self.click_start_time = 0
        self.activation_delay = 100  # ms before RCS activates
        self.rapid_click_threshold = 200  # ms for rapid clicks
        self.last_click_time = 0
        self.tcp_client = get_global_tcp_client()
        self.sending_rcs_down = False  # Flag to track if RCS is sending down commands
        
        # Mouse detector for left-click events
        self.mouse_detector = None
        if MouseEventDetector:
            self.mouse_detector = MouseEventDetector()
            self.mouse_detector.mouse_event.connect(self.on_mouse_event)
        
    def run(self):
        self.running = True
        self.status_updated.emit("RCS system started", "running")
        
        # Start mouse detector
        if self.mouse_detector:
            self.mouse_detector.start()
        
        while self.running:
            try:
                if self.rcs_enabled and self.mouse_pressed:
                    current_time = time.time() * 1000  # Convert to milliseconds
                    hold_duration = current_time - self.click_start_time
                    
                    # Check if we should activate RCS
                    if hold_duration >= self.activation_delay:
                        # Check for rapid clicks
                        time_since_last_click = current_time - self.last_click_time
                        is_rapid_click = time_since_last_click <= self.rapid_click_threshold
                        
                        if hold_duration >= self.activation_delay or is_rapid_click:
                            # Send downward movement
                            self.send_rcs_movement()
                            self.sending_rcs_down = True
                        else:
                            self.sending_rcs_down = False
                    else:
                        self.sending_rcs_down = False
                else:
                    self.sending_rcs_down = False
                
                time.sleep(0.01)  # 10ms update rate
                
            except Exception as e:
                print(f"RCS Worker error: {e}")
                time.sleep(0.1)
    
    def on_mouse_event(self, pressed):
        """Handle mouse press/release events from detector"""
        current_time = time.time() * 1000
        
        if pressed and not self.mouse_pressed:
            # Mouse just pressed
            self.mouse_pressed = True
            self.click_start_time = current_time
            self.last_click_time = current_time
        elif not pressed and self.mouse_pressed:
            # Mouse just released
            self.mouse_pressed = False
            self.sending_rcs_down = False
    
    def send_rcs_movement(self):
        """Send downward mouse movement via TCP"""
        if self.tcp_client:
            try:
                # Send downward movement (positive Y value)
                movement_y = self.pull_speed
                self.tcp_client.send_movement(0, movement_y)
            except Exception as e:
                print(f"RCS TCP send error: {e}")
    
    def is_sending_rcs_down(self):
        """Check if RCS is currently sending down commands"""
        return self.sending_rcs_down
    
    def stop(self):
        self.running = False
        if self.mouse_detector:
            self.mouse_detector.stop()
        self.wait()

class RCSSettingsTab(QWidget):
    """RCS Settings Tab for recoil control configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_theme = None
        self.rcs_worker = RCSWorker()
        self.rcs_worker.status_updated.connect(self.update_status)
        
        # Start RCS worker thread
        self.rcs_worker.start()
        
        self.setup_ui()
        self.apply_default_values()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main scroll area to prevent content overflow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        # Create content widget for scroll area
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("RCS (Recoil Control System)")
        title_label.setObjectName("sectionTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #a0a0a0; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Enable/Disable RCS
        enable_group = QGroupBox("RCS Control")
        enable_layout = QVBoxLayout(enable_group)
        enable_layout.setSpacing(10)
        enable_layout.setContentsMargins(15, 20, 15, 15)
        
        self.rcs_enabled_cb = QCheckBox("Enable RCS System")
        self.rcs_enabled_cb.stateChanged.connect(self.on_rcs_enabled_changed)
        enable_layout.addWidget(self.rcs_enabled_cb)
        
        # Status label
        self.status_label = QLabel("RCS system disabled")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold; padding: 5px;")
        enable_layout.addWidget(self.status_label)
        
        main_layout.addWidget(enable_group)
        
        # RCS Settings
        settings_group = QGroupBox("RCS Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(15)
        settings_layout.setContentsMargins(15, 20, 15, 15)
        settings_layout.setColumnStretch(1, 2)  # Make slider column wider
        settings_layout.setColumnMinimumWidth(0, 150)  # Minimum width for labels
        settings_layout.setColumnMinimumWidth(2, 80)   # Minimum width for spinboxes
        
        # Pull Speed
        speed_label = QLabel("Pull Speed:")
        speed_label.setStyleSheet("font-weight: bold;")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 20)
        self.speed_slider.setValue(5)
        self.speed_slider.setMinimumWidth(200)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(1, 20)
        self.speed_spinbox.setValue(5)
        self.speed_spinbox.setFixedWidth(70)
        self.speed_spinbox.valueChanged.connect(self.on_speed_spinbox_changed)
        
        settings_layout.addWidget(speed_label, 0, 0, Qt.AlignLeft)
        settings_layout.addWidget(self.speed_slider, 0, 1)
        settings_layout.addWidget(self.speed_spinbox, 0, 2, Qt.AlignLeft)
        
        # Activation Delay
        delay_label = QLabel("Activation Delay (ms):")
        delay_label.setStyleSheet("font-weight: bold;")
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(50, 500)
        self.delay_spinbox.setValue(100)
        self.delay_spinbox.setFixedWidth(100)
        self.delay_spinbox.valueChanged.connect(self.on_delay_changed)
        
        settings_layout.addWidget(delay_label, 1, 0, Qt.AlignLeft)
        settings_layout.addWidget(self.delay_spinbox, 1, 1, 1, 2, Qt.AlignLeft)
        
        # Rapid Click Threshold
        rapid_label = QLabel("Rapid Click Threshold (ms):")
        rapid_label.setStyleSheet("font-weight: bold;")
        self.rapid_spinbox = QSpinBox()
        self.rapid_spinbox.setRange(100, 1000)
        self.rapid_spinbox.setValue(200)
        self.rapid_spinbox.setFixedWidth(100)
        self.rapid_spinbox.valueChanged.connect(self.on_rapid_changed)
        
        settings_layout.addWidget(rapid_label, 2, 0, Qt.AlignLeft)
        settings_layout.addWidget(self.rapid_spinbox, 2, 1, 1, 2, Qt.AlignLeft)
        
        main_layout.addWidget(settings_group)
        
        # Integration Settings
        integration_group = QGroupBox("Integration Settings")
        integration_layout = QVBoxLayout(integration_group)
        integration_layout.setSpacing(10)
        integration_layout.setContentsMargins(15, 20, 15, 15)
        
        self.aimbot_integration_cb = QCheckBox("Enable Aimbot Integration")
        self.aimbot_integration_cb.setChecked(True)
        self.aimbot_integration_cb.setToolTip("Cancels aimbot's up/down movements when RCS is active")
        integration_layout.addWidget(self.aimbot_integration_cb)
        
        integration_info = QLabel("When RCS is active, aimbot will only make left/right movements")
        integration_info.setStyleSheet("color: #cccccc; font-style: italic; font-size: 11px; padding: 5px;")
        integration_info.setWordWrap(True)
        integration_layout.addWidget(integration_info)
        
        main_layout.addWidget(integration_group)
        
        # Info section
        info_group = QGroupBox("Usage Information")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(15, 20, 15, 15)
        
        info_text = QLabel(
            "• RCS activates when left-click is held down\n"
            "• RCS is also active during rapid clicks\n"
            "• RCS does not work with single clicks\n"
            "• Designed according to Valorant spray pattern"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #cccccc; font-size: 11px; line-height: 1.4; padding: 5px;")
        info_layout.addWidget(info_text)
        
        main_layout.addWidget(info_group)
        
        main_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Set scroll area as main layout
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)
        
        # Apply consistent styling
        self.apply_server_style()
    
    def apply_server_style(self):
        """Apply server.py consistent styling for RCS tab"""
        server_style = """
            /* RCS Tab specific styling */
            QScrollArea {
                background: transparent;
                border: none;
            }
            
            QGroupBox {
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid rgba(100, 100, 100, 0.4);
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 12px;
                background: rgba(35, 35, 35, 80);
            }
            
            QGroupBox::title {
                color: #a0a0a0;
                subcontrol-origin: margin;
                left: 12px;
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
            
            QSpinBox {
                background: rgba(50, 50, 50, 150);
                border: 1px solid rgba(100, 100, 100, 0.4);
                border-radius: 8px;
                color: white;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 12px;
            }
            
            QSpinBox:focus {
                border: 2px solid rgba(120, 120, 120, 0.8);
                background: rgba(60, 60, 60, 180);
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background: rgba(100, 100, 100, 0.3);
                border: none;
                width: 16px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: rgba(120, 120, 120, 0.6);
            }
            
            QLabel {
                color: white;
                font-family: 'Roboto', 'Arial';
                background: transparent;
            }
            
            QLabel[objectName="sectionTitle"] {
                color: #a0a0a0;
                font-size: 18px;
                font-weight: bold;
            }
            
            QLabel[objectName="statusLabel"] {
                font-weight: bold;
                padding: 5px;
                border-radius: 4px;
                background: rgba(35, 35, 35, 80);
            }
        """
        
        self.setStyleSheet(server_style)
    
    def apply_default_values(self):
        """Apply default values to the UI"""
        self.on_speed_changed(5)
        self.on_delay_changed(100)
        self.on_rapid_changed(200)
    
    def on_rcs_enabled_changed(self, state):
        """Handle RCS enable/disable"""
        enabled = state == Qt.Checked
        self.rcs_worker.rcs_enabled = enabled
        
        if enabled:
            self.status_label.setText("RCS system active")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.status_label.setText("RCS system disabled")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
    
    def on_speed_changed(self, value):
        """Handle speed slider change"""
        self.speed_spinbox.blockSignals(True)
        self.speed_spinbox.setValue(value)
        self.speed_spinbox.blockSignals(False)
        self.rcs_worker.pull_speed = value
    
    def on_speed_spinbox_changed(self, value):
        """Handle speed spinbox change"""
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(value)
        self.speed_slider.blockSignals(False)
        self.rcs_worker.pull_speed = value
    
    def on_delay_changed(self, value):
        """Handle activation delay change"""
        self.rcs_worker.activation_delay = value
    
    def on_rapid_changed(self, value):
        """Handle rapid click threshold change"""
        self.rcs_worker.rapid_click_threshold = value
    
    def update_status(self, message, status):
        """Update status display"""
        color_map = {
            "running": "#4CAF50",
            "stopped": "#f44336",
            "error": "#FF9800"
        }
        color = color_map.get(status, "#ccc")
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def get_rcs_worker(self):
        """Get RCS worker instance for integration"""
        return self.rcs_worker
    
    def is_aimbot_integration_enabled(self):
        """Check if aimbot integration is enabled"""
        return self.aimbot_integration_cb.isChecked()
    
    def load_settings(self, settings):
        """Load settings from config"""
        try:
            self.rcs_enabled_cb.setChecked(settings.get("rcs_enabled", "false").lower() == "true")
            self.speed_slider.setValue(int(settings.get("pull_speed", "5")))
            self.delay_spinbox.setValue(int(settings.get("activation_delay", "100")))
            self.rapid_spinbox.setValue(int(settings.get("rapid_click_threshold", "200")))
            self.aimbot_integration_cb.setChecked(settings.get("aimbot_integration", "true").lower() == "true")
        except Exception as e:
            print(f"RCS load settings error: {e}")
    
    def get_settings(self):
        """Get current settings for saving"""
        return {
            "rcs_enabled": str(self.rcs_enabled_cb.isChecked()).lower(),
            "pull_speed": str(self.speed_slider.value()),
            "activation_delay": str(self.delay_spinbox.value()),
            "rapid_click_threshold": str(self.rapid_spinbox.value()),
            "aimbot_integration": str(self.aimbot_integration_cb.isChecked()).lower()
        }
    
    def update_theme(self, theme):
        """Update theme colors"""
        self.current_theme = theme
        # Theme updates can be added here if needed
    
    def cleanup(self):
        """Cleanup when closing"""
        if self.rcs_worker:
            self.rcs_worker.stop()