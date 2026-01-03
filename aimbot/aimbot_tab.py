"""
Main aimbot tab module
Contains the main AimbotTab class that orchestrates all components
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, 
                             QCheckBox, QPushButton, QHBoxLayout, QFrame, QColorDialog, 
                             QApplication, QGridLayout, QScrollArea, QSlider, QComboBox)
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #333;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        header_layout.setSpacing(15)
        
        title_label = QLabel("AIMBOT CONFIG")
        title_label.setStyleSheet("color: #fff; font-size: 20px; font-weight: 900; letter-spacing: 2px;")
        
        # Indicator Control
        self.indicator_checkbox = QCheckBox("SHOW FOV")
        self.indicator_checkbox.setCursor(Qt.PointingHandCursor)
        self.indicator_checkbox.setStyleSheet("""
            QCheckBox { color: #888; font-weight: bold; font-size: 11px; spacing: 5px; }
            QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; background: #333; border: 1px solid #555; }
            QCheckBox::indicator:checked { background: #00cc66; border: 1px solid #00aa55; }
        """)
        self.indicator_checkbox.stateChanged.connect(self.update_indicator_from_controls)
        
        # Toggle Key
        self.toggle_button = KeyCaptureButton("insert")
        self.toggle_button.setStyleSheet(self.get_key_btn_style())
        self.toggle_button.setFixedSize(70, 30)
        self.toggle_button.key_captured.connect(self.on_toggle_captured)
        
        tog_label = QLabel("Toggle:")
        tog_label.setStyleSheet("color: #888; font-weight: bold; font-size: 11px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        header_layout.addWidget(self.indicator_checkbox)
        header_layout.addSpacing(20)
        
        header_layout.addWidget(tog_label)
        header_layout.addWidget(self.toggle_button)
        
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
        
        # 1. Target Priority (Cards)
        target_label = QLabel("TARGET PRIORITY")
        target_label.setStyleSheet("color: #666; font-weight: 900; letter-spacing: 2px; font-size: 11px;")
        content_layout.addWidget(target_label)
        
        target_layout = QHBoxLayout()
        target_layout.setSpacing(15)
        
        self.head_button = self.create_target_card("HEAD", "Prioritizes headshots for maximum damage.", "#e53e3e")
        self.head_button.clicked.connect(lambda: self.set_target_type("head"))
        
        self.body_button = self.create_target_card("BODY", "Aims for center of mass. More reliable.", "#ecc94b")
        self.body_button.clicked.connect(lambda: self.set_target_type("body"))
        self.body_button.setChecked(True) # Default visual state handled in update
        
        target_layout.addWidget(self.head_button)
        target_layout.addWidget(self.body_button)
        
        content_layout.addLayout(target_layout)
        
        # --- Silent Aim Section ---
        silent_aim_container = QWidget()
        silent_aim_layout = QVBoxLayout(silent_aim_container)
        silent_aim_layout.setContentsMargins(0, 0, 0, 0)
        silent_aim_layout.setSpacing(10)
        
        self.silent_aim_checkbox = QCheckBox("SILENT AIM (EXPERIMENTAL)")
        self.silent_aim_checkbox.setCursor(Qt.PointingHandCursor)
        self.silent_aim_checkbox.setStyleSheet("""
            QCheckBox { color: #ff5555; font-weight: 900; font-size: 12px; spacing: 8px; letter-spacing: 1px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; background: #221111; border: 1px solid #552222; }
            QCheckBox::indicator:checked { background: #ff4444; border: 1px solid #ff2222; }
            QCheckBox::indicator:hover { border: 1px solid #ff6666; }
        """)
        self.silent_aim_checkbox.stateChanged.connect(self.toggle_silent_aim)
        
        self.silent_aim_warning = QFrame()
        self.silent_aim_warning.setStyleSheet("""
            background-color: #2b1111; 
            border: 1px dashed #ff4444; 
            border-radius: 8px;
        """)
        self.silent_aim_warning.setFixedHeight(80)
        warning_layout = QVBoxLayout(self.silent_aim_warning)
        warning_lbl = QLabel("SILENT AIM ACTIVE - ADVANCED SETTINGS UNAVAILABLE")
        warning_lbl.setStyleSheet("color: #ff6666; font-weight: bold; font-size: 13px; letter-spacing: 1px;")
        warning_lbl.setAlignment(Qt.AlignCenter)
        warning_layout.addWidget(warning_lbl)
        self.silent_aim_warning.hide()
        
        silent_aim_layout.addWidget(self.silent_aim_checkbox)
        silent_aim_layout.addWidget(self.silent_aim_warning)
        
        content_layout.addWidget(silent_aim_container)
        
        # 2. Performance & Aim Settings
        self.settings_grid_widget = QWidget()
        settings_grid = QHBoxLayout(self.settings_grid_widget)
        settings_grid.setContentsMargins(0, 0, 0, 0)
        settings_grid.setSpacing(20)
        
        # Left: Aim Mechanics
        aim_frame = QFrame()
        aim_frame.setStyleSheet("background-color: #181818; border-radius: 15px;")
        aim_layout = QVBoxLayout(aim_frame)
        aim_layout.setContentsMargins(25, 25, 25, 25)
        aim_layout.setSpacing(20)
        
        aim_lbl = QLabel("AIM MECHANICS")
        aim_lbl.setStyleSheet("color: #666; font-weight: 900; letter-spacing: 2px; font-size: 11px;")
        aim_layout.addWidget(aim_lbl)
        
        self.aim_speed_slider = self.create_slider("Aim Speed", 1, 50, 40, "")
        aim_layout.addWidget(self.aim_speed_slider[0])
        self.aim_speed_slider[1].valueChanged.connect(self.update_aim_speed)
        
        self.smooth_aim_slider = self.create_slider("Smoothness", 0, 100, 0, "%")
        aim_layout.addWidget(self.smooth_aim_slider[0])
        self.smooth_aim_slider[1].valueChanged.connect(self.update_smooth_aim)

        self.y_offset_slider = self.create_slider("Y-Axis Offset", 0, 10, 0, "px")
        aim_layout.addWidget(self.y_offset_slider[0])
        self.y_offset_slider[1].valueChanged.connect(self.update_y_offset)
        
        aim_layout.addStretch()
        
        # Right: Scanner & FOV
        scan_frame = QFrame()
        scan_frame.setStyleSheet("background-color: #181818; border-radius: 15px;")
        scan_layout = QVBoxLayout(scan_frame)
        scan_layout.setContentsMargins(25, 25, 25, 25)
        scan_layout.setSpacing(20)
        
        scan_lbl = QLabel("SCANNER & FOV")
        scan_lbl.setStyleSheet("color: #666; font-weight: 900; letter-spacing: 2px; font-size: 11px;")
        scan_layout.addWidget(scan_lbl)
        
        self.size_x_slider = self.create_slider("FOV Width (X)", 0, 200, 80, "px")
        scan_layout.addWidget(self.size_x_slider[0])
        self.size_x_slider[1].valueChanged.connect(self.update_indicator_from_controls)

        self.size_y_slider = self.create_slider("FOV Height (Y)", 0, 200, 15, "px")
        scan_layout.addWidget(self.size_y_slider[0])
        self.size_y_slider[1].valueChanged.connect(self.update_indicator_from_controls)
        
        # FPS Selection
        fps_layout = QHBoxLayout()
        fps_lbl = QLabel("Scan Rate")
        fps_lbl.setStyleSheet("color: #ccc; font-weight: 600; font-size: 12px;")
        
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS", "75 FPS", "125 FPS", "160 FPS", "175 FPS", "200 FPS"])
        self.fps_combo.setCurrentText("60 FPS")
        self.fps_combo.currentTextChanged.connect(self.update_fps_setting)
        self.fps_combo.setFixedSize(100, 30)
        self.fps_combo.setStyleSheet("""
            QComboBox {
                background: #252525; border: 1px solid #333; border-radius: 5px; color: white; padding-left: 10px; font-weight: bold;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #252525; selection-background-color: #333; color: white; }
        """)
        
        fps_layout.addWidget(fps_lbl)
        fps_layout.addStretch()
        fps_layout.addWidget(self.fps_combo)
        scan_layout.addLayout(fps_layout)

        # Hold Key
        hold_layout = QHBoxLayout()
        self.holdkey_checkbox = QCheckBox("Hold Key:")
        self.holdkey_checkbox.setStyleSheet("""
            QCheckBox { color: #ccc; font-weight: 600; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; background: #333; border: 1px solid #555; }
            QCheckBox::indicator:checked { background: #00cc66; border: 1px solid #00aa55; }
        """)
        self.holdkey_checkbox.stateChanged.connect(self.update_holdkey_settings)
        
        self.holdkey_button = KeyCaptureButton("f")
        self.holdkey_button.setFixedSize(70, 30)
        self.holdkey_button.setStyleSheet(self.get_key_btn_style())
        self.holdkey_button.key_captured.connect(self.on_holdkey_captured)
        
        hold_layout.addWidget(self.holdkey_checkbox)
        hold_layout.addStretch()
        hold_layout.addWidget(self.holdkey_button)
        scan_layout.addLayout(hold_layout)

        scan_layout.addStretch()
        
        settings_grid.addWidget(aim_frame)
        settings_grid.addWidget(scan_frame)
        
        content_layout.addWidget(self.settings_grid_widget)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.y_offset_slider[1].setEnabled(False) # Initial state
        
    def create_target_card(self, name, desc, color):
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(80)
        
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: white; font-weight: 900; font-size: 18px; letter-spacing: 1px; background: transparent;")
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"color: #888; font-size: 11px; background: transparent;")
        desc_lbl.setWordWrap(True)
        
        layout.addWidget(name_lbl)
        layout.addWidget(desc_lbl)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-left: 4px solid #333;
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1a, stop:1 #222);
                border: 1px solid {color};
                border-left: 6px solid {color};
            }}
            QPushButton:hover:!checked {{
                background-color: #222;
                border: 1px solid #444;
            }}
        """)
        return btn

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
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #333; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00cc66; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
        """)
        
        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}{unit}"))
        
        layout.addLayout(header)
        layout.addWidget(slider)
        
        return container, slider

    def get_key_btn_style(self):
        return """
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { border-color: #00cc66; }
        """
        
    # Reimplement set_target_type to update UI states manually since we use custom buttons
    def set_target_type(self, target_type):
        if target_type == "head":
            self.head_button.setChecked(True)
            self.body_button.setChecked(False)
            self.y_offset_slider[1].setEnabled(True)
            # self.y_offset_slider[0].setOpacity(1.0) if hasattr(self.y_offset_slider[0], 'setOpacity') else None # Opacity not directly supported on QWidget
        else:
            self.head_button.setChecked(False)
            self.body_button.setChecked(True)
            self.y_offset_slider[1].setEnabled(False)
        
        self.screen_scanner.set_target_type(target_type)

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
        # self.aim_speed_slider is (container, slider)
        speed_value = self.aim_speed_slider[1].value()
        self.screen_scanner.set_aim_speed(speed_value)
    
    def update_y_offset(self):
        """Update Y offset value"""
        # self.y_offset_slider is (container, slider)
        offset_value = self.y_offset_slider[1].value()
        self.screen_scanner.set_y_offset(offset_value)
    
    def update_smooth_aim(self):
        """Update smooth aim value"""
        # self.smooth_aim_slider is (container, slider)
        val = self.smooth_aim_slider[1].value()
        if hasattr(self.screen_scanner, 'set_smooth_aim'):
             self.screen_scanner.set_smooth_aim(val)

    def update_scan_speed(self): # scan_speed_slider not used in new UI, handle gracefully or ignore
        pass # Not implemented in new UI yet or removed

    def update_prediction_settings(self): # prediction not used in new UI
        pass

    def update_fps_setting(self, text=None):
        if text is None: text = self.fps_combo.currentText()
        try:
             fps = int(text.split()[0])
             if hasattr(self.screen_scanner, 'set_fps'):
                 self.screen_scanner.set_fps(fps)
        except:
             pass

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
            # Enable Y offset slider - tuple access
            self.y_offset_slider[1].setEnabled(True)
        else:  # body
            self.head_button.setChecked(False)
            self.body_button.setChecked(True)
            # Disable Y offset slider - tuple access
            self.y_offset_slider[1].setEnabled(False)
        
        # Inform screen scanner of target type
        self.screen_scanner.set_target_type(target_type)

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

    def toggle_silent_aim(self, state):
        """Toggle silent aim mode"""
        enabled = (state == Qt.Checked)
        
        if enabled:
            self.settings_grid_widget.hide()
            self.silent_aim_warning.show()
        else:
            self.settings_grid_widget.show()
            self.silent_aim_warning.hide()
            
        if hasattr(self, 'screen_scanner'):
            self.screen_scanner.set_silent_aim(enabled)
    
    def update_indicator_from_controls(self):
        # Tuple access
        width = self.size_x_slider[1].value()
        height = self.size_y_slider[1].value()
        thickness = 1 
        opacity = 255
        is_filled = False

        color = QColor(255, 0, 0)
        color.setAlpha(opacity)
        
        # Update parameters first
        self.indicator.update_indicator(width, height, color, thickness, is_filled)

        # Check visibility condition
        should_be_visible = self.indicator_checkbox.isChecked() and width > 0 and height > 0
        
        if should_be_visible:
            if not self.indicator.isVisible():
                self.indicator.show()
                self.indicator.raise_()  # Bring to front
            self.indicator.update()  # Force repaint
        else:
            self.indicator.hide()
            
    def load_settings(self, settings):
        """Load settings from config - COMPREHENSIVE VERSION"""
        try:
            print(f"🎯 Loading aimbot settings: {settings}")
            
            # 1. First block signals to prevent intermediate updates
            self.indicator_checkbox.blockSignals(True)
            self.size_x_slider[1].blockSignals(True)
            self.size_y_slider[1].blockSignals(True)
            
            if 'enabled' in settings:
                enabled = settings['enabled'].lower() == 'true'
                if hasattr(self, 'screen_scanner') and self.screen_scanner:
                    self.screen_scanner.set_aimbot_enabled(enabled)
            
            if 'indicator_enabled' in settings:
                enabled = settings['indicator_enabled'].lower() == 'true'
                self.indicator_checkbox.setChecked(enabled)
            else:
                self.indicator_checkbox.setChecked(True)
            
            if 'indicator_size' in settings:
                size = int(float(settings['indicator_size']))
                self.size_x_slider[1].setValue(size)
                self.size_y_slider[1].setValue(size)
            elif 'indicator_size_x' in settings and 'indicator_size_y' in settings:
                size_x = int(float(settings['indicator_size_x']))
                size_y = int(float(settings['indicator_size_y']))
                self.size_x_slider[1].setValue(size_x)
                self.size_y_slider[1].setValue(size_y)
            else:
                self.size_x_slider[1].setValue(80)
                self.size_y_slider[1].setValue(15)
            
            # Unblock signals
            self.indicator_checkbox.blockSignals(False)
            self.size_x_slider[1].blockSignals(False)
            self.size_y_slider[1].blockSignals(False)
            
            # Silent Aim
            if 'silent_aim' in settings:
                silent_aim = settings['silent_aim'].lower() == 'true'
                self.silent_aim_checkbox.setChecked(silent_aim)
                self.toggle_silent_aim(Qt.Checked if silent_aim else Qt.Unchecked)
            
            # ... (rest of loading logic)
            
            if 'aim_speed' in settings:
                speed = int(float(settings['aim_speed']))
                self.aim_speed_slider[1].setValue(speed)
            elif 'sensitivity' in settings:
                speed = int(float(settings['sensitivity']) * 50)
                self.aim_speed_slider[1].setValue(speed)
            else:
                self.aim_speed_slider[1].setValue(50)
            
            if 'use_holdkey' in settings:
                use_holdkey = settings['use_holdkey'].lower() == 'true'
                self.holdkey_checkbox.setChecked(use_holdkey)
            
            if 'holdkey' in settings:
                holdkey = settings['holdkey']
                self.holdkey_button.current_key = holdkey
                self.holdkey_button.update_text()
            
            if 'toggle_key' in settings:
                toggle_key = settings['toggle_key']
                self.toggle_button.current_key = toggle_key
                self.toggle_button.update_text()
            
            if 'target_type' in settings:
                target_type = settings['target_type']
                self.set_target_type(target_type)
            
            if 'y_offset' in settings:
                y_offset = int(float(settings['y_offset']))
                self.y_offset_slider[1].setValue(y_offset)
            else:
                self.y_offset_slider[1].setValue(0)
                
            if 'fps' in settings:
                fps_value = int(float(settings['fps']))
                fps_text = f"{fps_value} FPS"
                index = self.fps_combo.findText(fps_text)
                if index >= 0:
                    self.fps_combo.setCurrentIndex(index)
                else:
                    self.fps_combo.setCurrentText("60 FPS")
            else:
                self.fps_combo.setCurrentText("60 FPS")
                
            if 'smooth_aim' in settings:
                smooth_aim = int(float(settings['smooth_aim']))
                self.smooth_aim_slider[1].setValue(smooth_aim)
            else:
                self.smooth_aim_slider[1].setValue(0)
            
            # APPLY ALL SETTINGS
            self.update_indicator_from_controls()
            self.update_aim_speed()
            self.update_holdkey_settings()
            self.update_y_offset()
            self.update_fps_setting()
            self.update_smooth_aim()
            
            if hasattr(self, 'screen_scanner') and 'toggle_key' in settings:
                self.screen_scanner.set_toggle_key(settings['toggle_key'])
            
            # FORCE UPDATE SLIDER UI (not really needed with new UI but keeping loop if needed)
            
            print("✅ Aimbot settings loaded and applied successfully")
            
        except Exception as e:
            print(f"❌ Error loading aimbot settings: {e}")
            import traceback
            traceback.print_exc()
    
    def get_settings(self):
        """Get settings for config"""
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
                'indicator_size_x': str(self.size_x_slider[1].value()),
                'indicator_size_y': str(self.size_y_slider[1].value()),
                
                # Aimbot settings
                'aim_speed': str(self.aim_speed_slider[1].value()),
                
                # New features
                'fps': str(int(self.fps_combo.currentText().split()[0])),  # "60 FPS" -> "60"
                'smooth_aim': str(self.smooth_aim_slider[1].value()),

                # Holdkey settings
                'use_holdkey': str(self.holdkey_checkbox.isChecked()).lower(),
                'holdkey': self.holdkey_button.current_key,
                'toggle_key': self.toggle_button.current_key,
                
                # Target type
                'target_type': 'head' if self.head_button.isChecked() else 'body',
                
                # Y Offset
                'y_offset': str(self.y_offset_slider[1].value()),
                
                # Silent Aim
                'silent_aim': str(self.silent_aim_checkbox.isChecked()).lower()
            }
            
            print(f"💾 Aimbot settings saved: {len(settings)} items")
            return settings
            
        except Exception as e:
            print(f"❌ Error getting aimbot settings: {e}")
            import traceback
            traceback.print_exc()
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
