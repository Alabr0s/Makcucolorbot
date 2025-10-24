"""
Anti-Smoke Settings Tab
Custom tab for adjusting anti-smoke parameters
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, 
                             QCheckBox, QPushButton, QHBoxLayout, QFrame, QScrollArea,
                             QSpinBox, QDoubleSpinBox, QTextEdit, QSplitter, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from models.color_palette import ColorTheme

try:
    from .ui_components import ModernSlider, StyleManager
except ImportError:
    # Use simple alternatives if ui_components is not available
    ModernSlider = None
    StyleManager = None


class AntiSmokeTab(QWidget):
    def __init__(self, screen_scanner, parent=None):
        super().__init__(parent)
        self.screen_scanner = screen_scanner
        self.anti_smoke_detector = screen_scanner.anti_smoke_detector
        self.parent_app = parent
        self.current_theme = ColorTheme.LIGHT  # Default theme
        
        # For test cluster
        self.test_cluster = None
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_live_debug)
        
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Single group - All settings (like aimbot tab)
        main_group = self.create_main_group()
        
        # Add group to scroll area
        scroll_area.setWidget(main_group)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Apply style
        self.apply_styles()
    
    def create_main_group(self):
        """Single group containing all settings (aimbot tab style)"""
        group = QGroupBox("")
        layout = QFormLayout(group)
        layout.setSpacing(18)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === MAIN CONTROL ===
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        layout.addRow("Anti-Smoke Active:", self.enabled_checkbox)
        
        # Status indicator
        self.status_label = QLabel("Off")
        self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        layout.addRow("Status:", self.status_label)
        
        # === QUICK SETTINGS ===
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(12)
        
        self.conservative_btn = QPushButton("Conservative")
        self.conservative_btn.clicked.connect(self.apply_conservative_preset)
        self.conservative_btn.setToolTip("Less filtering - More targets pass")
        self.conservative_btn.setFixedHeight(35)
        
        self.balanced_btn = QPushButton("Balanced")
        self.balanced_btn.clicked.connect(self.apply_balanced_preset)
        self.balanced_btn.setToolTip("Default settings - Recommended")
        self.balanced_btn.setFixedHeight(35)
        
        self.aggressive_btn = QPushButton("Aggressive")
        self.aggressive_btn.clicked.connect(self.apply_aggressive_preset)
        self.aggressive_btn.setToolTip("Heavy filtering - Only clear targets")
        self.aggressive_btn.setFixedHeight(35)
        
        preset_layout.addWidget(self.conservative_btn)
        preset_layout.addWidget(self.balanced_btn)
        preset_layout.addWidget(self.aggressive_btn)
        
        layout.addRow("Quick Settings:", preset_layout)
        
        # === PIXEL CONTROLS ===
        self.min_pixel_spin = QSpinBox()
        self.min_pixel_spin.setRange(1, 100)
        self.min_pixel_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Min Pixel Count:", self.min_pixel_spin)
        
        self.max_pixel_spin = QSpinBox()
        self.max_pixel_spin.setRange(100, 2000)
        self.max_pixel_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Max Pixel Count:", self.max_pixel_spin)
        
        # === SIZE CONTROLS ===
        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(10, 500)
        self.min_area_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Min Area:", self.min_area_spin)
        
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(20, 200)
        self.max_width_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Max Width:", self.max_width_spin)
        
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(20, 200)
        self.max_height_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Max Height:", self.max_height_spin)
        
        # === ADVANCED SETTINGS ===
        self.aspect_ratio_spin = QDoubleSpinBox()
        self.aspect_ratio_spin.setRange(1.0, 5.0)
        self.aspect_ratio_spin.setSingleStep(0.1)
        self.aspect_ratio_spin.setDecimals(1)
        self.aspect_ratio_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Max Aspect Ratio:", self.aspect_ratio_spin)
        
        self.pixel_density_spin = QDoubleSpinBox()
        self.pixel_density_spin.setRange(0.01, 1.0)
        self.pixel_density_spin.setSingleStep(0.01)
        self.pixel_density_spin.setDecimals(3)
        self.pixel_density_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Max Pixel Density:", self.pixel_density_spin)
        
        self.strip_threshold_spin = QDoubleSpinBox()
        self.strip_threshold_spin.setRange(0.1, 1.0)
        self.strip_threshold_spin.setSingleStep(0.05)
        self.strip_threshold_spin.setDecimals(2)
        self.strip_threshold_spin.valueChanged.connect(self.on_parameter_changed)
        layout.addRow("Continuous Strip Threshold:", self.strip_threshold_spin)
        
        # === TEST TOOLS ===
        test_layout = QHBoxLayout()
        test_layout.setSpacing(8)
        
        self.test_valid_btn = QPushButton("Valid Target")
        self.test_valid_btn.clicked.connect(self.test_valid_target)
        self.test_valid_btn.setFixedHeight(30)
        
        self.test_smoke_btn = QPushButton("Smoke Test")
        self.test_smoke_btn.clicked.connect(self.test_smoke_target)
        self.test_smoke_btn.setFixedHeight(30)
        
        self.test_noise_btn = QPushButton("Noise Test")
        self.test_noise_btn.clicked.connect(self.test_noise_target)
        self.test_noise_btn.setFixedHeight(30)
        
        test_layout.addWidget(self.test_valid_btn)
        test_layout.addWidget(self.test_smoke_btn)
        test_layout.addWidget(self.test_noise_btn)
        
        layout.addRow("Test Tools:", test_layout)
        
        # Live debug
        self.live_debug_checkbox = QCheckBox()
        self.live_debug_checkbox.stateChanged.connect(self.toggle_live_debug)
        layout.addRow("Live Debug:", self.live_debug_checkbox)
        
        # Results area
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(120)
        self.result_text.setReadOnly(True)
        layout.addRow("Test Results:", self.result_text)
        
        # Debug area
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(100)
        self.debug_text.setReadOnly(True)
        layout.addRow("Live Debug:", self.debug_text)
        
        return group

    
    def load_current_settings(self):
        """Load current settings"""
        params = self.anti_smoke_detector.get_parameters()
        
        self.enabled_checkbox.setChecked(params['enabled'])
        self.min_pixel_spin.setValue(params['min_pixel_count'])
        self.max_pixel_spin.setValue(params['max_pixel_count'])
        self.min_area_spin.setValue(params['min_area'])
        self.max_width_spin.setValue(params['max_width'])
        self.max_height_spin.setValue(params['max_height'])
        self.aspect_ratio_spin.setValue(params['max_aspect_ratio'])
        self.pixel_density_spin.setValue(params['max_pixel_density'])
        self.strip_threshold_spin.setValue(params['continuous_strip_threshold'])
        
        # Update status indicator
        self.on_enabled_changed()
    
    def on_enabled_changed(self):
        """When anti-smoke active/inactive status changes"""
        enabled = self.enabled_checkbox.isChecked()
        self.anti_smoke_detector.set_enabled(enabled)
        
        # Anti-smoke status notification
        try:
            from utils.notification_system import show_success, show_warning
            
            if enabled:
                show_success("Anti-Smoke Active", "Anti-smoke system enabled", 2000)
            else:
                show_warning("Anti-Smoke Inactive", "Anti-smoke system disabled", 2000)
                
        except Exception as e:
            print(f"Anti-smoke notification error: {e}")
        
        # Update status indicator
        if enabled:
            self.status_label.setText("Active")
            self.status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
        else:
            self.status_label.setText("Off")
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        
        self.log_result(f"Anti-Smoke: {'Active' if enabled else 'Inactive'}")
    
    def on_parameter_changed(self):
        """When parameter changes"""
        params = {
            'min_pixel_count': self.min_pixel_spin.value(),
            'max_pixel_count': self.max_pixel_spin.value(),
            'min_area': self.min_area_spin.value(),
            'max_width': self.max_width_spin.value(),
            'max_height': self.max_height_spin.value(),
            'max_aspect_ratio': self.aspect_ratio_spin.value(),
            'max_pixel_density': self.pixel_density_spin.value(),
            'continuous_strip_threshold': self.strip_threshold_spin.value()
        }
        
        self.anti_smoke_detector.set_parameters(**params)
        
        # Re-run if test exists
        if self.test_cluster:
            self.update_test_results()
    
    def apply_conservative_preset(self):
        """Conservative settings - Less filtering"""
        self.min_pixel_spin.setValue(8)
        self.max_pixel_spin.setValue(800)
        self.min_area_spin.setValue(30)
        self.max_width_spin.setValue(120)
        self.max_height_spin.setValue(120)
        self.aspect_ratio_spin.setValue(2.0)
        self.pixel_density_spin.setValue(0.85)
        self.strip_threshold_spin.setValue(0.8)
        self.log_result("Conservative settings applied")
    
    def apply_balanced_preset(self):
        """Balanced settings - Default"""
        self.min_pixel_spin.setValue(15)
        self.max_pixel_spin.setValue(500)
        self.min_area_spin.setValue(50)
        self.max_width_spin.setValue(80)
        self.max_height_spin.setValue(80)
        self.aspect_ratio_spin.setValue(1.3)
        self.pixel_density_spin.setValue(0.7)
        self.strip_threshold_spin.setValue(0.6)
        self.log_result("Balanced settings applied")
    
    def apply_aggressive_preset(self):
        """Aggressive settings - Heavy filtering"""
        self.min_pixel_spin.setValue(25)
        self.max_pixel_spin.setValue(300)
        self.min_area_spin.setValue(80)
        self.max_width_spin.setValue(60)
        self.max_height_spin.setValue(60)
        self.aspect_ratio_spin.setValue(1.1)
        self.pixel_density_spin.setValue(0.5)
        self.strip_threshold_spin.setValue(0.4)
        self.log_result("Aggressive settings applied")
    
    def test_valid_target(self):
        """Valid target test"""
        # Vertical enemy character-like cluster
        cluster = []
        for y in range(20, 45):  # 25 pixel height
            for x in range(50, 58):  # 8 pixel width
                if (x + y) % 3 != 0:  # 67% filled
                    cluster.append((x, y))
        
        self.test_cluster = cluster
        self.update_test_results()
        self.log_result(f"Valid target test: {len(cluster)} pixels")
    
    def test_smoke_target(self):
        """Smoke test"""
        # Horizontal smoke-like cluster
        cluster = []
        for y in range(30, 35):  # 5 pixel height
            for x in range(40, 85):  # 45 pixel width
                if (x + y) % 2 == 0:  # 50% filled
                    cluster.append((x, y))
        
        self.test_cluster = cluster
        self.update_test_results()
        self.log_result(f"Smoke test: {len(cluster)} pixels")
    
    def test_noise_target(self):
        """Noise test"""
        # Few random pixels
        cluster = [(100, 100), (102, 103), (105, 107), (108, 101)]
        
        self.test_cluster = cluster
        self.update_test_results()
        self.log_result(f"Noise test: {len(cluster)} pixels")
    
    def update_test_results(self):
        """Update test results"""
        if not self.test_cluster:
            return
        
        is_valid = self.anti_smoke_detector.is_valid_target(self.test_cluster)
        debug_info = self.anti_smoke_detector.get_debug_info(self.test_cluster)
        
        result = f"Result: {'✅ VALID TARGET' if is_valid else '❌ FILTERED'}\n\n{debug_info}"
        self.result_text.setPlainText(result)
    
    def toggle_live_debug(self):
        """Live debug on/off"""
        if self.live_debug_checkbox.isChecked():
            self.test_timer.start(500)  # Update every 0.5 seconds
            self.log_result("Live debug started")
        else:
            self.test_timer.stop()
            self.debug_text.clear()
            self.log_result("Live debug stopped")
    
    def update_live_debug(self):
        """Update live debug information"""
        try:
            # Get last target information from screen scanner
            if hasattr(self.screen_scanner, 'primary_target') and self.screen_scanner.primary_target:
                cluster = self.screen_scanner.primary_target.get('cluster', [])
                if cluster:
                    debug_info = self.anti_smoke_detector.get_debug_info(cluster)
                    self.debug_text.setPlainText(f"[LIVE] Last Target:\n{debug_info}")
                else:
                    self.debug_text.setPlainText("[LIVE] Target not found")
            else:
                self.debug_text.setPlainText("[LIVE] No active target")
        except Exception as e:
            self.debug_text.setPlainText(f"[LIVE] Error: {str(e)}")
    
    def log_result(self, message):
        """Log result"""
        current_text = self.result_text.toPlainText()
        new_text = f"[{self.get_timestamp()}] {message}\n{current_text}"
        self.result_text.setPlainText(new_text)
    
    def get_timestamp(self):
        """Get timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def apply_styles(self):
        """Apply styles compatible with white theme"""
        base_style = """
        QWidget {
            background: transparent;
            color: #495057;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QGroupBox {
            background: transparent;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            font-weight: 600;
            font-size: 14px;
            color: #495057;
            margin-top: 20px;
            padding-top: 20px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 20px;
            padding: 8px 15px;
            background-color: #ffffff;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            color: #495057;
            font-weight: 700;
        }
        """
        
        custom_style = """
        QFormLayout QLabel {
            border: none;
            background: transparent;
            font-weight: 600;
            color: #495057;
            font-size: 13px;
        }
        
        QCheckBox {
            background: transparent;
            color: #495057;
            font-weight: 500;
            spacing: 8px;
            font-size: 13px;
        }
        
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            background: #ffffff;
        }
        
        QCheckBox::indicator:hover {
            border-color: #2196f3;
            background: #e3f2fd;
        }
        
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2196f3, stop:1 #1976d2);
            border-color: #1976d2;
        }
        
        QCheckBox::indicator:checked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #42a5f5, stop:1 #2196f3);
        }
        
        QLabel {
            background: transparent;
            color: #495057;
            font-weight: 500;
            font-size: 13px;
        }
        
        QSpinBox, QDoubleSpinBox {
            background: #ffffff;
            border: 2px solid #ced4da;
            border-radius: 10px;
            padding: 10px 15px;
            color: #495057;
            font-weight: 500;
            font-size: 13px;
            min-width: 100px;
            min-height: 20px;
        }
        
        QSpinBox:hover, QDoubleSpinBox:hover {
            border-color: #2196f3;
            background: #f8f9fa;
        }
        
        QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #2196f3;
            background: #e3f2fd;

        }
        
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            background: #f8f9fa;
            border: 1px solid #ced4da;
            border-radius: 4px;
            width: 20px;
        }
        
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            background: #f8f9fa;
            border: 1px solid #ced4da;
            border-radius: 4px;
            width: 20px;
        }
        
        QPushButton {
            background: #ffffff;
            border: 1px solid #e1e8ed;
            border-radius: 6px;
            color: #2c3e50;
            font-weight: 500;
            padding: 10px 20px;
            font-size: 13px;
            min-height: 18px;
        }
        
        QPushButton:hover {
            background: #f8f9fa;
            border-color: #3498db;
            color: #2980b9;


        }
        
        QPushButton:pressed {
            background: #ecf0f1;
            color: #2c3e50;
            border-color: #2980b9;


        }
        
        QTextEdit {
            background: #ffffff;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 12px;
            color: #495057;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        }
        
        QTextEdit:focus {
            border-color: #2196f3;
            background: #e3f2fd;
        }
        
        QScrollBar:vertical {
            background: #f8f9fa;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: #dee2e6;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #adb5bd;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
        """
        
        self.setStyleSheet(base_style + custom_style)
    
    def load_settings(self, settings):
        """Load settings from config"""
        try:
            print(f"💨 Loading anti-smoke settings: {settings}")
            
            # Main control
            if 'enabled' in settings:
                enabled = settings['enabled'].lower() == 'true'
                self.enabled_checkbox.setChecked(enabled)
                self.anti_smoke_detector.set_enabled(enabled)
            
            # Pixel controls
            if 'min_pixel_count' in settings:
                self.min_pixel_spin.setValue(int(float(settings['min_pixel_count'])))
            
            if 'max_pixel_count' in settings:
                self.max_pixel_spin.setValue(int(float(settings['max_pixel_count'])))
            
            # Size controls
            if 'min_area' in settings:
                self.min_area_spin.setValue(int(float(settings['min_area'])))
            
            if 'max_width' in settings:
                self.max_width_spin.setValue(int(float(settings['max_width'])))
            
            if 'max_height' in settings:
                self.max_height_spin.setValue(int(float(settings['max_height'])))
            
            # Advanced settings
            if 'max_aspect_ratio' in settings:
                self.aspect_ratio_spin.setValue(float(settings['max_aspect_ratio']))
            
            if 'max_pixel_density' in settings:
                self.pixel_density_spin.setValue(float(settings['max_pixel_density']))
            
            if 'continuous_strip_threshold' in settings:
                self.strip_threshold_spin.setValue(float(settings['continuous_strip_threshold']))
            
            # Live debug
            if 'live_debug' in settings:
                self.live_debug_checkbox.setChecked(settings['live_debug'].lower() == 'true')
            
            # Apply parameters
            self.on_parameter_changed()
            
            print("✅ Anti-smoke settings loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading anti-smoke settings: {e}")
            import traceback
            traceback.print_exc()
    
    def save_settings(self):
        """Save settings for config"""
        try:
            settings = {
                # Main control
                'enabled': str(self.enabled_checkbox.isChecked()).lower(),
                
                # Pixel controls
                'min_pixel_count': str(self.min_pixel_spin.value()),
                'max_pixel_count': str(self.max_pixel_spin.value()),
                
                # Size controls
                'min_area': str(self.min_area_spin.value()),
                'max_width': str(self.max_width_spin.value()),
                'max_height': str(self.max_height_spin.value()),
                
                # Advanced settings
                'max_aspect_ratio': str(self.aspect_ratio_spin.value()),
                'max_pixel_density': str(self.pixel_density_spin.value()),
                'continuous_strip_threshold': str(self.strip_threshold_spin.value()),
                
                # Live debug
                'live_debug': str(self.live_debug_checkbox.isChecked()).lower()
            }
            
            print(f"💾 Anti-smoke settings saved: {len(settings)} items")
            return settings
            
        except Exception as e:
            print(f"❌ Error saving anti-smoke settings: {e}")
            return {}

    def update_theme(self, theme: ColorTheme):
        """Called when theme is updated"""
        self.current_theme = theme
        # Custom theme update for anti-smoke tab can be done here if needed
