"""
UI components module
Contains reusable UI components and styling
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, 
                             QCheckBox, QPushButton, QHBoxLayout, QFrame, QColorDialog, 
                             QSlider, QLineEdit, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class ModernSlider:
    """Modern designed slider creator"""
    
    @staticmethod
    def create(min_val, max_val, on_change, default_val=0, unit=""):
        """Create modern designed slider"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setFixedHeight(20)
        
        # Value label
        value_label = QLabel(f"{default_val}{unit}")
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
        
        def update_label(value):
            value_label.setText(f"{value}{unit}")
        
        slider.valueChanged.connect(update_label)
        slider.valueChanged.connect(on_change)
        
        layout.addWidget(slider, 1)
        layout.addWidget(value_label)
        
        return container, slider


class StyleManager:
    """Style manager"""
    
    @staticmethod
    def get_main_stylesheet():
        """Return main stylesheet"""
        return """
            /* Main widget background */
            QWidget {
                background-color: #0f1419;
                color: #e6f1ff;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            
            /* Group boxes */
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                border: 2px solid #1e3a5f;
                border-radius: 12px;
                margin: 5px;
                padding: 20px 15px 15px 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1419);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                top: -10px;
                padding: 5px 10px;
                color: #64b5f6;
                background-color: #0f1419;
                border: 1px solid #1e3a5f;
                border-radius: 6px;
            }
            
            /* Labels */
            QLabel {
                color: #b3d9ff;
                font-size: 12px;
                font-weight: 500;
            }
            
            /* Checkboxes */
            QCheckBox {
                color: #e6f1ff;
                spacing: 15px;
                margin: 6px 0px;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #2196f3;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1419);
            }
            QCheckBox::indicator:hover {
                border-color: #42a5f5;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3a5f, stop:1 #1a2332);
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
            
            /* Buttons */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
                border: 2px solid #1976d2;
                border-radius: 8px;
                padding: 10px 20px;
                margin: 3px 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                min-height: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42a5f5, stop:1 #2196f3);
                border-color: #2196f3;

            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
                border-color: #1565c0;

            }
            QPushButton:disabled {
                background: #2a2a2a;
                border-color: #444;
                color: #666;
            }
            
            /* Text input */
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1419);
                border: 2px solid #1e3a5f;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e6f1ff;
                font-size: 12px;
                font-weight: 500;
                selection-background-color: #2196f3;
            }
            QLineEdit:focus {
                border-color: #2196f3;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3a5f, stop:1 #1a2332);
            }
            QLineEdit:hover {
                border-color: #42a5f5;
            }
            
            /* Slider */
            QSlider::groove:horizontal {
                border: 2px solid #1e3a5f;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1419);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42a5f5, stop:1 #2196f3);
                border: 2px solid #1976d2;
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #64b5f6, stop:1 #42a5f5);
                border-color: #2196f3;
            }
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background: #1a2332;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #2196f3;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #42a5f5;
            }
        """


class ColorPicker:
    """Color picker helper class"""
    
    @staticmethod
    def create_color_button_with_preview(initial_color, button_text="🎨 Select Color"):
        """Create color button and preview"""
        color_layout = QHBoxLayout()
        
        color_button = QPushButton(button_text)
        color_button.setFixedHeight(35)
        color_button.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2196f3, stop:1 #1976d2);
            border: 2px solid #1976d2;
            border-radius: 8px;
            color: #ffffff;
            font-size: 12px;
            font-weight: 600;
            padding: 10px 20px;
            min-width: 120px;
        """)
        
        color_preview = QFrame()
        color_preview.setFixedSize(35, 35)
        color_preview.setStyleSheet(f"""
            background-color: {initial_color.name()};
            border: 2px solid #2196f3;
            border-radius: 8px;
        """)
        
        color_layout.addWidget(color_button)
        color_layout.addWidget(color_preview)
        color_layout.addStretch()
        
        return color_layout, color_button, color_preview
