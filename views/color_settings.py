from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSlider, 
                             QHBoxLayout, QLabel, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from controllers.theme_controller import WindowColorManager
from models.color_palette import ColorTheme
import colorsys


class ColorSpectrumWidget(QWidget):
    """Widget displaying HSV color spectrum
    
    Note: OpenCV Hue values range from 0-180.
    This widget converts OpenCV values to standard HSV (0-360) for display.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 60)
        self.setMaximumHeight(80)
        # OpenCV Hue values (0-180)
        self.hue_min = 140  # 280° (purple/violet)
        self.hue_max = 150  # 300° (purple/violet)
        
    def update_hue_range(self, hue_min, hue_max):
        """Update hue range (OpenCV format 0-180)"""
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.update()
        
    def paintEvent(self, event):
        """Draw the spectrum"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(40, 40, 40, 200))
        
        # Draw full spectrum (0-360 degrees)
        spectrum_height = 40
        spectrum_y = 10
        
        # Draw a color for each degree
        for i in range(360):
            h = i / 360.0
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            color = QColor(int(r * 255), int(g * 255), int(b * 255))
            
            x = int((i / 360.0) * (self.width() - 20)) + 10
            painter.setPen(QPen(color, 2))
            painter.drawLine(x, spectrum_y, x, spectrum_y + spectrum_height)
        
        # Convert OpenCV Hue values to standard HSV (0-180 -> 0-360)
        # Example: 140 -> 280°, 150 -> 300° (purple/violet region)
        hue_min_degrees = self.hue_min * 2
        hue_max_degrees = self.hue_max * 2
        
        # Highlight selected range
        min_x = int((hue_min_degrees / 360.0) * (self.width() - 20)) + 10
        max_x = int((hue_max_degrees / 360.0) * (self.width() - 20)) + 10
        
        # Selected range border
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(min_x, spectrum_y - 2, max_x - min_x, spectrum_height + 4)
        
        # Show selected color at bottom
        h = ((hue_min_degrees + hue_max_degrees) / 2.0) / 360.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.7, 0.9)
        selected_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        
        painter.setBrush(QBrush(selected_color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(10, spectrum_y + spectrum_height + 10, self.width() - 20, 15)


class ColorPreviewWidget(QWidget):
    """Widget displaying HSV color values as a human figure
    
    Note: OpenCV Hue values range from 0-180.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 400)
        # OpenCV Hue values (0-180)
        self.hue_min = 140  # 280° (purple/violet)
        self.hue_max = 150  # 300° (purple/violet)
        self.sat_min = 0.43  # Medium-high saturation
        self.sat_max = 0.76
        self.val_min = 150  # Bright
        self.val_max = 255
        
    def update_color_values(self, hue_min, hue_max, sat_min, sat_max, val_min, val_max):
        """Update color values"""
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.sat_min = sat_min
        self.sat_max = sat_max
        self.val_min = val_min
        self.val_max = val_max
        self.update()  # Redraw widget
        
    def get_preview_color(self):
        """Calculate average color for preview"""
        # Get average HSV values
        # OpenCV Hue (0-180) -> Standard HSV (0-360) -> Normalize (0-1)
        hue_opencv = (self.hue_min + self.hue_max) / 2.0
        hue_degrees = hue_opencv * 2  # 145 -> 290° (purple)
        h = hue_degrees / 360.0  # Normalize to 0-1 range
        
        s = (self.sat_min + self.sat_max) / 2.0
        v = (self.val_min + self.val_max) / 2.0 / 255.0  # Normalize to 0-1 range
        
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        return QColor(int(r * 255), int(g * 255), int(b * 255))
        
    def paintEvent(self, event):
        """Draw the widget"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(40, 40, 40, 200))
        
        # Get preview color
        color = self.get_preview_color()
        
        # Draw human figure
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Head
        head_radius = 40
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 3))
        painter.drawEllipse(center_x - head_radius, center_y - 120, head_radius * 2, head_radius * 2)
        
        # Body
        body_width = 80
        body_height = 120
        painter.drawRoundedRect(
            center_x - body_width // 2, 
            center_y - 60, 
            body_width, 
            body_height,
            10, 10
        )
        
        # Left arm
        arm_width = 25
        arm_length = 100
        painter.drawRoundedRect(
            center_x - body_width // 2 - arm_width - 5,
            center_y - 50,
            arm_width,
            arm_length,
            8, 8
        )
        
        # Right arm
        painter.drawRoundedRect(
            center_x + body_width // 2 + 5,
            center_y - 50,
            arm_width,
            arm_length,
            8, 8
        )
        
        # Left leg
        leg_width = 30
        leg_length = 110
        painter.drawRoundedRect(
            center_x - leg_width - 5,
            center_y + 60,
            leg_width,
            leg_length,
            8, 8
        )
        
        # Right leg
        painter.drawRoundedRect(
            center_x + 5,
            center_y + 60,
            leg_width,
            leg_length,
            8, 8
        )
        
        # Color info text (OpenCV values and degree equivalents)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawText(10, 30, f"Hue: {self.hue_min:.0f}-{self.hue_max:.0f} ({self.hue_min*2:.0f}°-{self.hue_max*2:.0f}°)")
        painter.drawText(10, 50, f"Sat: {self.sat_min:.2f} - {self.sat_max:.2f}")
        painter.drawText(10, 70, f"Val: {self.val_min:.0f} - {self.val_max:.0f}")


class ColorSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.widgets = {}
        self.color_manager = WindowColorManager()
        self.current_theme = ColorTheme.LIGHT
        self.setup_ui()
    
    def get_slider_style(self, slider_type):
        """Return CSS style based on slider type"""
        base_style = """
            QSlider::groove:horizontal {
                height: 10px;
                border-radius: 5px;
                border: 1px solid rgba(100, 100, 100, 0.5);
                %s
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 255), 
                    stop:0.5 rgba(220, 220, 220, 255),
                    stop:1 rgba(255, 255, 255, 255));
                border: 2px solid rgba(100, 100, 100, 200);
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 255), 
                    stop:0.5 rgba(240, 240, 255, 255),
                    stop:1 rgba(255, 255, 255, 255));
                border: 2px solid rgba(150, 150, 200, 255);
            }
        """
        
        if slider_type == 'hue':
            gradient = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0.00 #FF0000,
                    stop:0.17 #FFFF00,
                    stop:0.33 #00FF00,
                    stop:0.50 #00FFFF,
                    stop:0.67 #0000FF,
                    stop:0.83 #FF00FF,
                    stop:1.00 #FF0000);
            """
        elif slider_type == 'saturation':
            gradient = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #808080,
                    stop:1 #9966CC);
            """
        elif slider_type == 'value':
            gradient = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #000000,
                    stop:1 #FFFFFF);
            """
        else:
            gradient = "background: rgba(30, 30, 30, 200);"
        
        return base_style % gradient

    def setup_ui(self):
        # Main layout horizontal: settings on left, preview on right
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left side: Settings
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_box = QGroupBox("Color Settings (OpenCV HSV)")
        form_layout = QFormLayout(group_box)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Apply styling
        self.apply_styles()
        
        # Color preset buttons
        preset_group = QGroupBox("Color Presets")
        preset_layout = QHBoxLayout(preset_group)
        preset_layout.setSpacing(10)
        
        self.purple_btn = QPushButton("Purple")
        self.red_btn = QPushButton("Red")
        self.yellow_btn = QPushButton("Yellow")
        
        # Style the preset buttons (gray)
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(90, 90, 90, 120), stop:1 rgba(70, 70, 70, 120));
                border: 1px solid rgba(110, 110, 110, 0.6);
                border-radius: 12px;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                margin: 2px;
                min-height: 25px;
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
        
        for btn in [self.purple_btn, self.red_btn, self.yellow_btn]:
            btn.setStyleSheet(button_style)
            preset_layout.addWidget(btn)
        
        # Connect button signals
        self.purple_btn.clicked.connect(self.set_purple_preset)
        self.red_btn.clicked.connect(self.set_red_preset)
        self.yellow_btn.clicked.connect(self.set_yellow_preset)
        
        layout.addWidget(preset_group)
        
        # Sliders for color settings
        color_settings = [
            ("hue_min", "Hue Min (0-180):", 0, 180, 1, 'hue'),
            ("hue_max", "Hue Max (0-180):", 0, 180, 1, 'hue'),
            ("sat_min", "Sat Min (0-1):", 0, 100, 100, 'saturation'),
            ("sat_max", "Sat Max (0-1):", 0, 100, 100, 'saturation'),
            ("val_min", "Val Min (0-255):", 0, 255, 1, 'value'),
            ("val_max", "Val Max (0-255):", 0, 255, 1, 'value')
        ]
        
        for setting in color_settings:
            key = setting[0]
            label_text = setting[1]
            min_val = setting[2]
            max_val = setting[3]
            factor = setting[4]
            slider_type = setting[5]
            
            label = QLabel(label_text)
            slider_layout = QHBoxLayout()
            
            # Use normal slider but apply colorful style
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setStyleSheet(self.get_slider_style(slider_type))
            
            # Default values (Bright Purple/Violet - OpenCV format)
            default_values = {
                "hue_min": 140,  # 280° (purple/violet)
                "hue_max": 150,  # 300° (purple/violet)
                "sat_min": 43,   # 0.43 (medium-high saturation)
                "sat_max": 76,   # 0.76
                "val_min": 150,  # Bright
                "val_max": 255   # Maximum brightness
            }
            
            if key in default_values:
                slider.setValue(default_values[key])
            
            value_label = QLabel("0")
            value_label.setMinimumWidth(50)
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
                    border: 1px solid rgba(120, 120, 120, 0.8);
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-weight: bold;
                    color: #ffffff;
                    font-size: 11px;
                    min-width: 45px;
                }
            """)

            # Capture factor for lambda function
            slider.valueChanged.connect(
                lambda val, lbl=value_label, f=factor: lbl.setText(
                    f"{val/f:.2f}" if f > 1 else str(val)
                )
            )
            
            # Update preview when slider changes
            slider.valueChanged.connect(self.update_preview)
            
            # Show initial value
            initial_val = slider.value()
            value_label.setText(f"{initial_val/factor:.2f}" if factor > 1 else str(initial_val))
            
            slider_layout.addWidget(slider)
            slider_layout.addWidget(value_label)
            
            form_layout.addRow(label, slider_layout)
            self.widgets[key] = slider
        
        layout.addWidget(group_box)
        layout.addStretch()
        
        # Right side: Preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(10)
        
        # Spectrum widget
        spectrum_group = QGroupBox("Color Spectrum (0-360°)")
        spectrum_layout = QVBoxLayout(spectrum_group)
        self.spectrum_widget = ColorSpectrumWidget()
        spectrum_layout.addWidget(self.spectrum_widget)
        preview_layout.addWidget(spectrum_group)
        
        # Human figure preview
        figure_group = QGroupBox("Color Preview")
        figure_layout = QVBoxLayout(figure_group)
        self.preview_widget = ColorPreviewWidget()
        figure_layout.addWidget(self.preview_widget)
        preview_layout.addWidget(figure_group)
        
        # Update initial preview
        self.update_preview()
        
        # Add to layout
        main_layout.addWidget(left_widget, stretch=2)
        main_layout.addWidget(preview_widget, stretch=1)

    def update_preview(self):
        """Update preview widget and spectrum"""
        hue_min = self.widgets["hue_min"].value()
        hue_max = self.widgets["hue_max"].value()
        sat_min = self.widgets["sat_min"].value() / 100.0
        sat_max = self.widgets["sat_max"].value() / 100.0
        val_min = self.widgets["val_min"].value()
        val_max = self.widgets["val_max"].value()
        
        self.preview_widget.update_color_values(
            hue_min, hue_max, sat_min, sat_max, val_min, val_max
        )
        
        self.spectrum_widget.update_hue_range(hue_min, hue_max)

    def get_widgets(self):
        """Return widgets to main application"""
        return self.widgets

    def load_settings(self, config):
        """Load settings"""
        for key, widget in self.widgets.items():
            if key in config:
                value_str = config[key]
                # Calculate factor for decimal values
                if key in ["sat_min", "sat_max"]:
                    factor = 100
                    try:
                        value = int(float(value_str) * factor)
                        widget.setValue(value)
                    except ValueError:
                        widget.setValue(0)
                else:
                    try:
                        value = int(float(value_str))
                        widget.setValue(value)
                    except ValueError:
                        widget.setValue(0)
        
        # Update preview after loading settings
        self.update_preview()

    def save_settings(self):
        """Save settings"""
        settings = {}
        for key, widget in self.widgets.items():
            if key in ["sat_min", "sat_max"]:
                factor = 100
                value = widget.value() / factor
                settings[key] = f"{value:.2f}"
            else:
                settings[key] = str(widget.value())
        return settings
    
    def update_theme(self, theme: ColorTheme):
        """Called when theme is updated"""
        self.current_theme = theme
    
    def set_purple_preset(self):
        """Set purple color preset (Valorant enemy outline)"""
        preset_values = {
            "hue_min": 140,  # 280° (purple/violet)
            "hue_max": 150,  # 300° (purple/violet)
            "sat_min": 43,   # 0.43
            "sat_max": 76,   # 0.76
            "val_min": 150,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def set_red_preset(self):
        """Set red color preset (Valorant enemy outline)"""
        preset_values = {
            "hue_min": 0,    # 0° (red)
            "hue_max": 10,   # 20° (red)
            "sat_min": 70,   # 0.70 (high saturation)
            "sat_max": 100,  # 1.00 (full saturation)
            "val_min": 180,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def set_yellow_preset(self):
        """Set yellow color preset (Valorant teammate outline)"""
        preset_values = {
            "hue_min": 20,   # 40° (yellow)
            "hue_max": 30,   # 60° (yellow)
            "sat_min": 60,   # 0.60
            "sat_max": 100,  # 1.00 (full saturation)
            "val_min": 180,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def apply_preset(self, values):
        """Apply preset values to sliders"""
        for key, value in values.items():
            if key in self.widgets:
                self.widgets[key].setValue(value)
        # Update preview after applying preset
        self.update_preview()
    
    def apply_styles(self):
        """Apply gray theme styling"""
        self.setStyleSheet("""
        QGroupBox {
            color: white;
            font-weight: bold;
            font-size: 14px;
            border: 2px solid rgba(100, 100, 100, 0.4);
            border-radius: 15px;
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
        
        QLabel {
            color: #d0d0d0;
            font-weight: bold;
            font-size: 13px;
            padding: 2px;
            font-family: 'Roboto', 'Arial';
        }
        
        /* Scrollbar styling */
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
        """)