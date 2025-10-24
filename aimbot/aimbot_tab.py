"""
Main aimbot tab module
Contains the main AimbotTab class that orchestrates all components
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, 
                             QCheckBox, QPushButton, QHBoxLayout, QFrame, QColorDialog, 
                             QApplication, QGridLayout, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Import aimbot components
from .screen_scanner import ScreenScanner
from .indicator_window import IndicatorWindow
from .key_capture import KeyCaptureButton
from .ui_components import ModernSlider, StyleManager, ColorPicker
from controllers.theme_controller import WindowColorManager
from models.color_palette import ColorTheme


class AimbotTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.current_indicator_color = QColor(255, 0, 0)
        self.indicator = IndicatorWindow()
        self.current_theme = ColorTheme.LIGHT  # Default theme
        self.screen_scanner = ScreenScanner(self.indicator)
        self.debug_window = None  # Debug window reference
        self.setup_ui()
        

        
        # Start screen scanner
        self.screen_scanner.target_found.connect(self.on_target_found)
        self.screen_scanner.start()

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
        
        # Apply style
        self.apply_styles()
        
        # Disable Y offset slider at startup (because body is default)
        self.y_offset_slider.setEnabled(False)
    
    def create_main_group(self):
        """Single group containing all settings"""
        group = QGroupBox("")
        layout = QFormLayout(group)
        layout.setSpacing(18)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === INDICATOR SETTINGS ===
        self.indicator_checkbox = QCheckBox()
        self.indicator_checkbox.stateChanged.connect(self.update_indicator_from_controls)
        layout.addRow("Show:", self.indicator_checkbox)
        
        # Size X slider
        size_x_widget, self.size_x_slider = self.create_modern_slider(0, 200, self.update_indicator_from_controls, 60, "px")
        layout.addRow("Size X:", size_x_widget)
        
        # Size Y slider
        size_y_widget, self.size_y_slider = self.create_modern_slider(0, 200, self.update_indicator_from_controls, 13, "px")
        layout.addRow("Size Y:", size_y_widget)
        

        
        # === AIMBOT SETTINGS ===
        # Aim speed
        aim_speed_widget, self.aim_speed_slider = self.create_modern_slider(1, 50, self.update_aim_speed, 3, "")
        layout.addRow("Aim Speed:", aim_speed_widget)
        

        
        # Target type selection
        target_type_layout = QHBoxLayout()
        target_type_layout.setSpacing(12)
        
        # Head button
        self.head_button = QPushButton("Head")
        self.head_button.setCheckable(True)
        self.head_button.setFixedHeight(35)
        self.head_button.clicked.connect(lambda: self.set_target_type("head"))
        
        # Body button
        self.body_button = QPushButton("Body")
        self.body_button.setCheckable(True)
        self.body_button.setChecked(True)  # Body selected by default
        self.body_button.setFixedHeight(35)
        self.body_button.clicked.connect(lambda: self.set_target_type("body"))
        
        target_type_layout.addWidget(self.head_button)
        target_type_layout.addWidget(self.body_button)
        target_type_layout.addStretch()
        
        layout.addRow("Target Type:", target_type_layout)
        
        # Y Offset slider (for Head)
        y_offset_widget, self.y_offset_slider = self.create_modern_slider(0, 10, self.update_y_offset, 0, "px")
        layout.addRow("Y Offset:", y_offset_widget)
        
        # === NEW FEATURES ===
        # FPS (Frame Rate) - New Feature
        fps_layout = QHBoxLayout()
        fps_layout.setSpacing(12)
        
        # FPS Dropdown
        from PyQt5.QtWidgets import QComboBox
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS", "75 FPS", "125 FPS", "160 FPS", "175 FPS", "200 FPS"])
        self.fps_combo.setCurrentText("60 FPS")  # Default
        self.fps_combo.currentTextChanged.connect(self.update_fps_setting)
        self.fps_combo.setFixedHeight(35)
        
        fps_info_label = QLabel("Higher FPS = Faster scanning")
        fps_info_label.setProperty('info_type', 'fps')
        
        fps_layout.addWidget(self.fps_combo)
        fps_layout.addWidget(fps_info_label)
        fps_layout.addStretch()
        layout.addRow("Scan FPS:", fps_layout)
        
        # Scan Speed
        scan_speed_widget, self.scan_speed_slider = self.create_modern_slider(1, 100, self.update_scan_speed, 100, "")
        layout.addRow("Scan Speed:", scan_speed_widget)
        
        # Smooth Aim (Soft Aim)
        smooth_aim_widget, self.smooth_aim_slider = self.create_modern_slider(0, 100, self.update_smooth_aim, 0, "%")
        layout.addRow("Smooth Aim:", smooth_aim_widget)
        
        # Adaptive Prediction (Custom Feature)
        prediction_layout = QHBoxLayout()
        prediction_layout.setSpacing(12)
        
        self.prediction_checkbox = QCheckBox()
        self.prediction_checkbox.stateChanged.connect(self.update_prediction_settings)
        prediction_layout.addWidget(self.prediction_checkbox)
        
        prediction_strength_widget, self.prediction_strength_slider = self.create_modern_slider(1, 100, self.update_prediction_settings, 50, "%")
        prediction_layout.addWidget(prediction_strength_widget)
        
        layout.addRow("Adaptive Prediction:", prediction_layout)
        
        # === CONTROL SETTINGS ===
        # Holdkey checkbox
        self.holdkey_checkbox = QCheckBox()
        self.holdkey_checkbox.stateChanged.connect(self.update_holdkey_settings)
        layout.addRow("Holdkey Active:", self.holdkey_checkbox)
        
        # Holdkey key selector
        holdkey_layout = QHBoxLayout()
        holdkey_layout.setSpacing(12)
        self.holdkey_button = KeyCaptureButton("f")
        self.holdkey_button.setFixedHeight(35)
        self.holdkey_button.key_captured.connect(self.on_holdkey_captured)
        
        info_label = QLabel("Click and press key")
        info_label.setProperty('info_type', 'key')
        
        holdkey_layout.addWidget(self.holdkey_button)
        holdkey_layout.addWidget(info_label)
        holdkey_layout.addStretch()
        layout.addRow("Holdkey Key:", holdkey_layout)
        
        # Toggle key selector
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(12)
        self.toggle_button = KeyCaptureButton("insert")
        self.toggle_button.setFixedHeight(35)
        self.toggle_button.key_captured.connect(self.on_toggle_captured)
        
        toggle_info_label = QLabel("Toggle key")
        toggle_info_label.setProperty('info_type', 'key')
        
        toggle_layout.addWidget(self.toggle_button)
        toggle_layout.addWidget(toggle_info_label)
        toggle_layout.addStretch()
        layout.addRow("Toggle Key:", toggle_layout)
        

        
        return group
    

    
    def apply_styles(self):
        """Apply purple theme style compatible with Server.py"""
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
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(90, 90, 90, 120), stop:1 rgba(70, 70, 70, 120));
            border: 1px solid rgba(110, 110, 110, 0.6);
            border-radius: 8px;
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            margin: 2px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(110, 110, 110, 180), stop:1 rgba(90, 90, 90, 180));
            border: 1px solid rgba(120, 120, 120, 0.8);
        }
        
        QPushButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(120, 120, 120, 220), stop:1 rgba(100, 100, 100, 220));
            border: 2px solid rgba(130, 130, 130, 0.9);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(70, 70, 70, 200), stop:1 rgba(90, 90, 90, 200));
        }
        
        QComboBox {
            background: rgba(50, 50, 50, 150);
            border: 1px solid rgba(100, 100, 100, 0.4);
            border-radius: 8px;
            color: white;
            padding: 6px 12px;
            font-weight: bold;
            min-width: 100px;
        }
        
        QComboBox:hover {
            border: 2px solid rgba(110, 110, 110, 0.6);
            background: rgba(60, 60, 60, 180);
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
            background: rgba(100, 100, 100, 0.3);
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #a0a0a0;
            width: 0;
            height: 0;
        }
        
        QComboBox QAbstractItemView {
            background: rgba(35, 35, 35, 240);
            border: 1px solid rgba(100, 100, 100, 0.6);
            border-radius: 8px;
            color: white;
            selection-background-color: rgba(100, 100, 100, 150);
        }
        
        /* Scrollbar styling for long tables */
        QScrollBar:vertical {
            background: rgba(35, 35, 35, 150);
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(120, 120, 120, 200), stop:1 rgba(100, 100, 100, 200));
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
        
        QScrollBar:horizontal {
            background: rgba(35, 35, 35, 150);
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(120, 120, 120, 200), stop:1 rgba(100, 100, 100, 200));
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: transparent;
        }
        """
        
        self.setStyleSheet(custom_style)
    
    def create_modern_slider(self, min_val, max_val, on_change, default_val=0, unit=""):
        """Create modern designed slider"""
        return ModernSlider.create(min_val, max_val, on_change, default_val, unit)

    def open_color_dialog(self):
        color = QColorDialog.getColor(self.current_indicator_color, self, "Select Indicator Color")
        if color.isValid():
            self.current_indicator_color = color
            self.color_preview.setStyleSheet(f"""
                background-color: {color.name()};
                border: 2px solid #2196f3;
                border-radius: 8px;
            """)
            self.update_indicator_from_controls()
    


    def update_indicator_from_controls(self):
        if not self.indicator_checkbox.isChecked():
            self.indicator.hide()
            return
        
        width = self.size_x_slider.value()
        height = self.size_y_slider.value()
        thickness = 1  # Fixed thickness
        opacity = 255  # Fixed opacity
        is_filled = False  # Fixed empty fill

        color = QColor(255, 0, 0)  # Fixed red color
        color.setAlpha(opacity)

        self.indicator.update_indicator(width, height, color, thickness, is_filled)

        if width > 0 and height > 0:
            self.indicator.show()
        else:
            self.indicator.hide()
    
    def update_aim_speed(self):
        """Update aim speed value"""
        speed_value = self.aim_speed_slider.value()
        self.screen_scanner.set_aim_speed(speed_value)
    
    def update_y_offset(self):
        """Update Y offset value"""
        offset_value = self.y_offset_slider.value()
        self.screen_scanner.set_y_offset(offset_value)
    

    
    def update_holdkey_settings(self):
        """Update holdkey settings"""
        enabled = self.holdkey_checkbox.isChecked()
        key = self.holdkey_button.current_key
        self.screen_scanner.set_holdkey_settings(enabled, key)
    
    def on_holdkey_captured(self, key):
        """Called when new key is captured"""
        self.update_holdkey_settings()
        
        # Key capture notification
        try:
            from utils.notification_system import show_info
            show_info("Key Assigned", f"Aimbot holdkey: {key.upper()}", 1500)
        except Exception as e:
            print(f"Holdkey capture notification error: {e}")
    

    

    def set_target_type(self, target_type):
        """Set target type"""
        # Update buttons
        if target_type == "head":
            self.head_button.setChecked(True)
            self.body_button.setChecked(False)
            # Enable Y offset slider
            self.y_offset_slider.setEnabled(True)
        else:  # body
            self.head_button.setChecked(False)
            self.body_button.setChecked(True)
            # Disable Y offset slider
            self.y_offset_slider.setEnabled(False)
        
        # Inform screen scanner of target type
        self.screen_scanner.set_target_type(target_type)
    
    # Anti-smoke settings are now managed in a separate tab
    
    def on_toggle_captured(self, key):
        """Called when toggle key is captured"""
        self.screen_scanner.set_toggle_key(key)
        
        # Key capture notification
        try:
            from utils.notification_system import show_info
            show_info("Key Assigned", f"Aimbot toggle: {key.upper()}", 1500)
        except Exception as e:
            print(f"Toggle capture notification error: {e}")
    

    

    def on_target_found(self, move_x, move_y):
        """Called when target is found"""
        # Send message to status bar in main application
        if hasattr(self.parent_app, 'statusBar'):
            self.parent_app.statusBar.showMessage(f"Target found: {move_x}, {move_y}", 500)
    
    def load_settings(self, settings):
        """Load settings from config - COMPREHENSIVE VERSION"""
        try:
            print(f"🎯 Loading aimbot settings: {settings}")
            
            # IMPORTANT: Aimbot enabled status - This was missing!
            if 'enabled' in settings:
                enabled = settings['enabled'].lower() == 'true'
                print(f"🎯 Setting aimbot enabled: {enabled}")
                
                # Inform screen scanner of aimbot status
                if hasattr(self, 'screen_scanner') and self.screen_scanner:
                    self.screen_scanner.set_aimbot_enabled(enabled)
                    print(f"🎯 Screen scanner aimbot enabled set to: {enabled}")
            
            # Indicator settings
            if 'indicator_enabled' in settings:
                enabled = settings['indicator_enabled'].lower() == 'true'
                self.indicator_checkbox.setChecked(enabled)
                print(f"🎯 Indicator enabled: {enabled}")
            else:
                print("⚠️ indicator_enabled not found in settings, using default: True")
                self.indicator_checkbox.setChecked(True)
            
            if 'indicator_filled' in settings:
                filled = settings['indicator_filled'].lower() == 'true'
                self.fill_checkbox.setChecked(filled)
                print(f"🎯 Indicator filled: {filled}")
            else:
                print("⚠️ indicator_filled not found in settings, using default: False")
                self.fill_checkbox.setChecked(False)
            
            if 'indicator_size' in settings:
                size = int(float(settings['indicator_size']))
                # Use old size value for both X and Y
                self.size_x_slider.setValue(size)
                self.size_y_slider.setValue(size)
                print(f"🎯 Indicator size (both X&Y): {size}")
            elif 'indicator_size_x' in settings and 'indicator_size_y' in settings:
                # New separate X and Y values
                size_x = int(float(settings['indicator_size_x']))
                size_y = int(float(settings['indicator_size_y']))
                self.size_x_slider.setValue(size_x)
                self.size_y_slider.setValue(size_y)
                print(f"🎯 Indicator size X: {size_x}, Y: {size_y}")
            else:
                print("⚠️ indicator_size not found in settings, using default: X=60, Y=13")
                self.size_x_slider.setValue(60)
                self.size_y_slider.setValue(13)
            
            # Backward compatibility - ignore old settings
            # thickness, opacity, filled are no longer used
            
            # Aimbot performance settings
            if 'aim_speed' in settings:
                speed = int(float(settings['aim_speed']))
                self.aim_speed_slider.setValue(speed)
                print(f"🎯 Aim speed: {speed}")
            elif 'sensitivity' in settings:
                # Stored as sensitivity in config, used as aim_speed
                speed = int(float(settings['sensitivity']) * 50)  # 1.0 -> 50
                self.aim_speed_slider.setValue(speed)
                print(f"🎯 Aim speed (from sensitivity): {speed}")
            else:
                print("⚠️ Neither aim_speed nor sensitivity found in settings, using default: 50")
                self.aim_speed_slider.setValue(50)
            
            # Scan area is no longer used - backward compatibility
            
            # Holdkey settings
            if 'use_holdkey' in settings:
                use_holdkey = settings['use_holdkey'].lower() == 'true'
                self.holdkey_checkbox.setChecked(use_holdkey)
                print(f"🎯 Use holdkey: {use_holdkey}")
            
            if 'holdkey' in settings:
                holdkey = settings['holdkey']
                self.holdkey_button.current_key = holdkey
                self.holdkey_button.update_text()
                print(f"🎯 Holdkey: {holdkey}")
            
            if 'toggle_key' in settings:
                toggle_key = settings['toggle_key']
                self.toggle_button.current_key = toggle_key
                self.toggle_button.update_text()
                print(f"🎯 Toggle key: {toggle_key}")
            
            # Debug mode is no longer used
            
            # Target type
            if 'target_type' in settings:
                target_type = settings['target_type']
                print(f"🎯 Target type: {target_type}")
                if target_type == 'head':
                    self.set_target_type('head')
                else:
                    self.set_target_type('body')
            
            # Y Offset
            if 'y_offset' in settings:
                y_offset = int(float(settings['y_offset']))
                self.y_offset_slider.setValue(y_offset)
                print(f"🎯 Y Offset: {y_offset}")
            else:
                print("⚠️ y_offset not found in settings, using default: 0")
                self.y_offset_slider.setValue(0)
                
            # New features - FPS
            if 'fps' in settings:
                fps_value = int(float(settings['fps']))
                fps_text = f"{fps_value} FPS"
                # Check if this value exists in combo box
                index = self.fps_combo.findText(fps_text)
                if index >= 0:
                    self.fps_combo.setCurrentIndex(index)
                    print(f"🎯 FPS: {fps_value}")
                else:
                    print(f"⚠️ FPS value {fps_value} not found in combo, using default: 60")
                    self.fps_combo.setCurrentText("60 FPS")
            else:
                print("⚠️ fps not found in settings, using default: 60")
                self.fps_combo.setCurrentText("60 FPS")
                
            # New features - Scan Speed
            if 'scan_speed' in settings:
                scan_speed = int(float(settings['scan_speed']))
                self.scan_speed_slider.setValue(scan_speed)
                print(f"🎯 Scan Speed: {scan_speed}")
            else:
                print("⚠️ scan_speed not found in settings, using default: 100")
                self.scan_speed_slider.setValue(100)
                
            # Smooth Aim
            if 'smooth_aim' in settings:
                smooth_aim = int(float(settings['smooth_aim']))
                self.smooth_aim_slider.setValue(smooth_aim)
                print(f"🎯 Smooth Aim: {smooth_aim}%")
            else:
                print("⚠️ smooth_aim not found in settings, using default: 0")
                self.smooth_aim_slider.setValue(0)
                
            # Prediction settings
            if 'prediction_enabled' in settings:
                prediction_enabled = settings['prediction_enabled'].lower() == 'true'
                self.prediction_checkbox.setChecked(prediction_enabled)
                print(f"🎯 Prediction Enabled: {prediction_enabled}")
            else:
                self.prediction_checkbox.setChecked(False)
                
            if 'prediction_strength' in settings:
                prediction_strength = int(float(settings['prediction_strength']))
                self.prediction_strength_slider.setValue(prediction_strength)
                print(f"🎯 Prediction Strength: {prediction_strength}%")
            else:
                self.prediction_strength_slider.setValue(50)
            
            # APPLY ALL SETTINGS
            print("🎯 Applying all aimbot settings...")
            self.update_indicator_from_controls()
            self.update_aim_speed()
            self.update_holdkey_settings()
            self.update_y_offset()
            
            # Apply new feature settings
            self.update_fps_setting()
            self.update_scan_speed()
            self.update_smooth_aim()
            self.update_prediction_settings()
            
            # Also inform screen scanner of toggle key
            if hasattr(self, 'screen_scanner') and 'toggle_key' in settings:
                self.screen_scanner.set_toggle_key(settings['toggle_key'])
            
            # FORCE UPDATE SLIDER UI
            print("🔄 Force updating slider UI labels...")
            self._force_update_slider_labels()
            
            # CHECK SLIDER VALUES
            print("🔍 === SLIDER VALUES AFTER LOADING ===")
            print(f"🔍 Size X slider value: {self.size_x_slider.value()}")
            print(f"🔍 Size Y slider value: {self.size_y_slider.value()}")
            print(f"🔍 Aim speed slider value: {self.aim_speed_slider.value()}")
            print("🔍 === END SLIDER VALUES ===")
            
            print("✅ Aimbot settings loaded and applied successfully")
            
        except Exception as e:
            print(f"❌ Error loading aimbot settings: {e}")
            import traceback
            traceback.print_exc()
    
    def save_settings(self):
        """Config system disabled - Settings not saved"""
        print("⚠️ Aimbot save_settings disabled")
        return {}
        """Save settings for config"""
        try:
            # Get real aimbot status from screen scanner
            aimbot_enabled = False
            if hasattr(self, 'screen_scanner') and self.screen_scanner:
                aimbot_enabled = self.screen_scanner.get_aimbot_status()
            
            settings = {
                # IMPORTANT: Aimbot enabled status
                'enabled': str(aimbot_enabled).lower(),
                
                # Indicator settings
                'indicator_enabled': str(self.indicator_checkbox.isChecked()).lower(),
                'indicator_size_x': str(self.size_x_slider.value()),
                'indicator_size_y': str(self.size_y_slider.value()),
                
                # Aimbot settings
                'aim_speed': str(self.aim_speed_slider.value()),
                
                # New features
                'fps': str(int(self.fps_combo.currentText().split()[0])),  # "60 FPS" -> "60"
                'scan_speed': str(self.scan_speed_slider.value()),
                'smooth_aim': str(self.smooth_aim_slider.value()),
                'prediction_enabled': str(self.prediction_checkbox.isChecked()).lower(),
                'prediction_strength': str(self.prediction_strength_slider.value()),
                
                # Holdkey settings
                'use_holdkey': str(self.holdkey_checkbox.isChecked()).lower(),
                'holdkey': self.holdkey_button.current_key,
                'toggle_key': self.toggle_button.current_key,
                
                # Target type
                'target_type': 'head' if self.head_button.isChecked() else 'body',
                
                # Y Offset
                'y_offset': str(self.y_offset_slider.value())
            }
            
            print(f"💾 Aimbot settings saved: {len(settings)} items")
            return settings
            
        except Exception as e:
            print(f"❌ Error saving aimbot settings: {e}")
            return {}

    def update_theme(self, theme: ColorTheme):
        """Called when theme is updated"""
        self.current_theme = theme
        # Custom theme update for aimbot tab can be done here if needed
        # Key capture buttons automatically detect theme changes

    def _force_update_slider_labels(self):
        """Force update slider labels"""
        try:
            # Manually trigger valueChanged signal of sliders
            # This ensures labels are updated
            
            print("🔄 Triggering slider valueChanged signals...")
            
            # Re-set current value for each slider (this triggers valueChanged signal)
            current_size_x = self.size_x_slider.value()
            self.size_x_slider.setValue(current_size_x)
            print(f"🔄 Size X slider refreshed: {current_size_x}")
            
            current_size_y = self.size_y_slider.value()
            self.size_y_slider.setValue(current_size_y)
            print(f"🔄 Size Y slider refreshed: {current_size_y}")
            
            current_thickness = self.thickness_slider.value()
            self.thickness_slider.setValue(current_thickness)
            print(f"🔄 Thickness slider refreshed: {current_thickness}")
            
            current_opacity = self.opacity_slider.value()
            self.opacity_slider.setValue(current_opacity)
            print(f"🔄 Opacity slider refreshed: {current_opacity}")
            
            current_aim_speed = self.aim_speed_slider.value()
            self.aim_speed_slider.setValue(current_aim_speed)
            print(f"🔄 Aim speed slider refreshed: {current_aim_speed}")
            
            current_scan_area = self.scan_area_slider.value()
            self.scan_area_slider.setValue(current_scan_area)
            print(f"🔄 Scan area slider refreshed: {current_scan_area}")
            
            current_y_offset = self.y_offset_slider.value()
            self.y_offset_slider.setValue(current_y_offset)
            print(f"🔄 Y offset slider refreshed: {current_y_offset}")
            
            # New feature sliders
            current_scan_speed = self.scan_speed_slider.value()
            self.scan_speed_slider.setValue(current_scan_speed)
            print(f"🔄 Scan speed slider refreshed: {current_scan_speed}")
            
            current_smooth_aim = self.smooth_aim_slider.value()
            self.smooth_aim_slider.setValue(current_smooth_aim)
            print(f"🔄 Smooth aim slider refreshed: {current_smooth_aim}")
            
            current_prediction_strength = self.prediction_strength_slider.value()
            self.prediction_strength_slider.setValue(current_prediction_strength)
            print(f"🔄 Prediction strength slider refreshed: {current_prediction_strength}")
            
            print("✅ All slider labels force updated")
            
        except Exception as e:
            print(f"❌ Error force updating slider labels: {e}")

    def cleanup(self):
        """Cleanup operations"""
        if hasattr(self, 'screen_scanner'):
            self.screen_scanner.stop()
        if hasattr(self, 'indicator'):
            self.indicator.close()
        if hasattr(self, 'debug_window') and self.debug_window:
            self.debug_window.close()
            
    # === NEW FEATURE UPDATE METHODS ===
    
    def update_fps_setting(self):
        """Update FPS setting"""
        fps_text = self.fps_combo.currentText()
        fps_value = int(fps_text.split()[0])  # "60 FPS" -> 60
        if hasattr(self, 'screen_scanner'):
            self.screen_scanner.set_fps(fps_value)
            
    def update_scan_speed(self):
        """Update scan speed"""
        speed_value = self.scan_speed_slider.value()
        if hasattr(self, 'screen_scanner'):
            self.screen_scanner.set_scan_speed(speed_value)
            
    def update_smooth_aim(self):
        """Update smooth aim setting"""
        smooth_value = self.smooth_aim_slider.value()
        if hasattr(self, 'screen_scanner'):
            self.screen_scanner.set_smoothing(smooth_value)
            
    def update_prediction_settings(self):
        """Update adaptive prediction settings"""
        enabled = self.prediction_checkbox.isChecked()
        strength = self.prediction_strength_slider.value()
        
        # Enable/disable prediction strength slider
        self.prediction_strength_slider.setEnabled(enabled)
        
        if hasattr(self, 'screen_scanner'):
            self.screen_scanner.set_prediction(enabled, strength)
