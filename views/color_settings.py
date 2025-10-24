from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSlider, 
                             QHBoxLayout, QLabel, QPushButton)
from PyQt5.QtCore import Qt
from controllers.theme_controller import WindowColorManager
from models.color_palette import ColorTheme


class ColorSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.widgets = {}
        self.color_manager = WindowColorManager()
        self.current_theme = ColorTheme.LIGHT  # Varsayılan tema
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        group_box = QGroupBox("Renk Ayarları")
        form_layout = QFormLayout(group_box)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Apply styling
        self.apply_styles()
        
        # Color preset buttons
        preset_group = QGroupBox("Renk Şablonları")
        preset_layout = QHBoxLayout(preset_group)
        preset_layout.setSpacing(10)
        
        self.purple_btn = QPushButton("Purple")
        self.red_btn = QPushButton("Red")
        self.yellow_btn = QPushButton("Yellow")
        
        # Style the preset buttons
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
        
        # Renk ayarları için slider'lar
        color_settings = [
            ("hue_min", "Hue Min:", 0, 360),
            ("hue_max", "Hue Max:", 0, 360),
            ("sat_min", "Sat Min:", 0, 100, 100),  # factor 100 for decimal
            ("sat_max", "Sat Max:", 0, 100, 100),  # factor 100 for decimal
            ("val_min", "Val Min:", 0, 255),
            ("val_max", "Val Max:", 0, 255)
        ]
        
        for setting in color_settings:
            key = setting[0]
            label_text = setting[1]
            min_val = setting[2]
            max_val = setting[3]
            factor = setting[4] if len(setting) > 4 else 1
            
            label = QLabel(label_text)
            slider_layout = QHBoxLayout()
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            
            # Varsayılan değerleri ayarla (Purple preset as default)
            default_values = {
                "hue_min": 140,
                "hue_max": 150,
                "sat_min": 43,  # 0.43 * 100
                "sat_max": 76,  # 0.76 * 100
                "val_min": 150,
                "val_max": 255
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

            # Lambda fonksiyonu için factor'ü yakalayalım
            slider.valueChanged.connect(
                lambda val, lbl=value_label, f=factor: lbl.setText(
                    f"{val/f:.2f}" if f > 1 else str(val)
                )
            )
            
            # Başlangıç değerini göster
            initial_val = slider.value()
            value_label.setText(f"{initial_val/factor:.2f}" if factor > 1 else str(initial_val))
            
            slider_layout.addWidget(slider)
            slider_layout.addWidget(value_label)
            
            form_layout.addRow(label, slider_layout)
            self.widgets[key] = slider
        
        layout.addWidget(group_box)
        layout.addStretch()

    def get_widgets(self):
        """Ana uygulamaya widget'ları döndür"""
        return self.widgets

    def load_settings(self, config):
        """Ayarları yükle"""
        for key, widget in self.widgets.items():
            if key in config:
                value_str = config[key]
                # Ondalıklı değerler için factor hesapla
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

    def save_settings(self):
        """Ayarları kaydet"""
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
        """Tema güncellendiğinde çağrılır"""
        self.current_theme = theme
        # Color settings tab'ı için özel tema güncellemesi gerekirse burada yapılabilir
    
    def set_purple_preset(self):
        """Purple renk şablonunu ayarla"""
        preset_values = {
            "hue_min": 140,
            "hue_max": 150,
            "sat_min": 43,  # 0.43 * 100
            "sat_max": 76,  # 0.76 * 100
            "val_min": 150,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def set_red_preset(self):
        """Red renk şablonunu ayarla"""
        preset_values = {
            "hue_min": 0,
            "hue_max": 10,
            "sat_min": 50,  # 0.50 * 100
            "sat_max": 90,  # 0.90 * 100
            "val_min": 100,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def set_yellow_preset(self):
        """Yellow renk şablonunu ayarla"""
        preset_values = {
            "hue_min": 50,
            "hue_max": 70,
            "sat_min": 40,  # 0.40 * 100
            "sat_max": 85,  # 0.85 * 100
            "val_min": 120,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def apply_preset(self, values):
        """Preset değerlerini slider'lara uygula"""
        for key, value in values.items():
            if key in self.widgets:
                self.widgets[key].setValue(value)
    
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
        """)