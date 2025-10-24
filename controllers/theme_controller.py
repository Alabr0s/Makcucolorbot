"""
Window Color Manager
This module provides dynamic color management for PyQt5 widgets.
"""

from typing import Dict, Optional, List
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from models.color_palette import ColorPalette, ColorTheme, color_palette


class WindowColorManager(QObject):
    """
    Window and widget color management class
    Centrally manages colors of all UI components
    """
    
    # Send signal when theme changes
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.palette = color_palette
        self.registered_widgets = []
        self.style_templates = self._initialize_style_templates()
    
    def _initialize_style_templates(self) -> Dict[str, str]:
        """Initialize CSS style templates"""
        return {
            'main_frame': """
                QFrame#mainFrame {{ 
                    background: {gradient_bg}; 
                    border-radius: 20px; 
                    border: 1px solid {border_primary};
                }}
            """,
            
            'nav_bar': """
                QFrame#navBar {{ 
                    background: {gradient_nav}; 
                    border-top-left-radius: 20px; 
                    border-bottom-left-radius: 20px;
                    border-right: 1px solid {nav_border};
                }}
            """,
            
            'nav_button': """
                QPushButton#navButton {{ 
                    background: transparent; 
                    border: none; 
                    border-radius: 8px; 
                    color: {text_muted};
                    font-weight: 500;
                    font-size: 13px;
                    padding: 12px;
                    margin: 2px;
                }}
                QPushButton#navButton:hover {{ 
                    background: {nav_button_hover}; 
                    color: {text_primary};
                    border-left: 3px solid {nav_accent};
                }}
                QPushButton#navButton:checked {{ 
                    background: {nav_button_active}; 
                    color: {text_primary};
                    border-left: 3px solid {nav_accent};
                    font-weight: 600;
                }}
            """,
            
            'title_label': """
                QLabel#titleLabel {{ 
                    color: {text_primary}; 
                    font-size: 18px; 
                    font-weight: 700; 
                    padding-left: 15px; 
                }}
            """,
            
            'close_button': """
                QPushButton#closeButton {{ 
                    background-color: transparent; 
                    border: none; 
                    border-radius: 18px;
                    padding: 8px;
                }}
                QPushButton#closeButton:hover {{ 
                    background-color: {danger_light};
                    color: {danger};
                }}
            """,
            
            'group_box': """
                QGroupBox {{ 
                    color: {text_secondary}; 
                    font-weight: 600;
                    font-size: 14px;
                    border: 2px solid {border_primary}; 
                    border-radius: 15px; 
                    margin-top: 20px; 
                    padding: 25px 20px 20px 20px;
                    background: {gradient_group};
                }}
                QGroupBox::title {{ 
                    subcontrol-origin: margin; 
                    subcontrol-position: top left; 
                    left: 20px;
                    top: -12px;
                    padding: 8px 15px;
                    background-color: {background_primary};
                    border: 2px solid {border_primary};
                    border-radius: 8px;
                    color: {text_secondary};
                    font-weight: 700;
                }}
            """,
            
            'label': """
                QLabel {{ 
                    color: {text_secondary}; 
                    font-size: 13px; 
                    font-weight: 500;
                }}
            """,
            
            'button': """
                QPushButton {{ 
                    background: {background_primary};
                    color: {text_primary}; 
                    border: 1px solid {border_secondary}; 
                    padding: 12px 24px; 
                    border-radius: 8px; 
                    font-size: 13px; 
                    font-weight: 500;
                    min-height: 20px;
                }}
                QPushButton:hover {{ 
                    background: {background_hover};
                    border-color: {primary};
                    color: {primary};

                }}
                QPushButton:pressed {{ 
                    background: {background_active};
                    border-color: {primary};
                }}
            """,
            
            'save_button': """
                QPushButton#saveButton {{ 
                    background: {success};
                    color: {text_white};
                    border: 1px solid {success};
                }}
                QPushButton#saveButton:hover {{ 
                    background: {success_light};
                    border-color: {success};

                }}
            """,
            
            'slider': """
                QSlider {{
                    background: transparent;
                    min-height: 40px;
                }}
                QSlider::groove:horizontal {{ 
                    border: none;
                    height: 4px; 
                    background: {background_tertiary}; 
                    margin: 2px 0; 
                    border-radius: 2px;
                }}
                QSlider::handle:horizontal {{ 
                    background: {primary}; 
                    border: 2px solid {background_primary}; 
                    width: 18px; 
                    height: 18px; 
                    margin: -8px 0; 
                    border-radius: 9px;

                }}
                QSlider::handle:horizontal:hover {{
                    background: {primary_dark};

                }}
                QSlider::sub-page:horizontal {{
                    background: {primary};
                    border-radius: 2px;
                }}
                QSlider::add-page:horizontal {{
                    background: {background_tertiary};
                    border-radius: 2px;
                }}
            """,
            
            'checkbox': """
                QCheckBox {{ 
                    color: {text_primary}; 
                    font-weight: 500;
                    font-size: 13px;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{ 
                    width: 18px; 
                    height: 18px; 
                    border: 1px solid {border_dark}; 
                    border-radius: 3px;
                    background: {background_primary};
                }}
                QCheckBox::indicator:hover {{
                    border-color: {primary};
                    background: {background_hover};
                }}
                QCheckBox::indicator:checked {{ 
                    background: {primary};
                    border-color: {primary};
                }}
                QCheckBox::indicator:checked:hover {{
                    background: {primary_dark};
                    border-color: {primary_dark};
                }}
            """,
            
            'scroll_area': """
                QScrollArea {{
                    border: none;
                    background: transparent;
                }}
                QScrollBar:vertical {{
                    background: {background_secondary};
                    width: 12px;
                    border-radius: 6px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: {border_primary};
                    border-radius: 6px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {border_dark};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: transparent;
                }}
            """,
            
            'spinbox': """
                QSpinBox, QDoubleSpinBox {{
                    background: {background_primary};
                    border: 1px solid {border_dark};
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: {text_primary};
                    font-weight: 500;
                    font-size: 13px;
                    min-width: 80px;
                    min-height: 18px;
                }}
                QSpinBox:hover, QDoubleSpinBox:hover {{
                    border-color: {primary};
                    background: {background_hover};
                }}
                QSpinBox:focus, QDoubleSpinBox:focus {{
                    border-color: {primary};
                    background: {background_primary};

                }}
                QSpinBox::up-button, QDoubleSpinBox::up-button {{
                    background: {background_tertiary};
                    border: 1px solid {border_dark};
                    border-radius: 3px;
                    width: 16px;
                }}
                QSpinBox::down-button, QDoubleSpinBox::down-button {{
                    background: {background_tertiary};
                    border: 1px solid {border_dark};
                    border-radius: 3px;
                    width: 16px;
                }}
                QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
                    background: {background_hover};
                    border-color: {border_secondary};
                }}
                QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                    background: {background_hover};
                    border-color: {border_secondary};
                }}
            """,
            
            'textedit': """
                QTextEdit {{
                    background: {background_primary};
                    border: 1px solid {border_dark};
                    border-radius: 6px;
                    padding: 12px;
                    color: {text_primary};
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                    font-weight: 400;
                }}
                QTextEdit:hover {{
                    border-color: {primary};
                    background: {background_hover};
                }}
                QTextEdit:focus {{
                    border-color: {primary};
                    background: {background_primary};

                }}
            """,
            
            'status_bar': """
                QStatusBar {{
                    color: {text_secondary}; 
                    background-color: transparent; 
                    font-weight: 500; 
                    font-size: 12px;
                }}
            """,
            
            'key_capture_button': """
                QPushButton[capturing="false"] {{
                    background: {gradient_key_normal};
                    border: 2px solid {border_primary};
                    border-radius: 8px;
                    color: {text_primary};
                    font-size: 12px;
                    font-weight: 600;
                    padding: 10px 20px;
                    min-width: 130px;
                }}
                QPushButton[capturing="false"]:hover {{
                    background: {gradient_key_hover};
                    border-color: {primary};
                    color: {primary};

                }}
                QPushButton[capturing="true"] {{
                    background: {gradient_key_capturing};
                    border: 2px solid {primary};
                    border-radius: 8px;
                    color: {text_white};
                    font-weight: 600;
                    font-size: 12px;
                    padding: 10px 20px;
                    min-width: 130px;
                    animation: pulse 1s infinite;
                }}
                QPushButton[capturing="true"]:hover {{
                    background: {primary};
                    border-color: {primary_dark};
                }}
            """,
            
            'info_label': """
                QLabel[info_type="key"] {{
                    color: {primary};
                    font-size: 11px;
                    font-weight: 500;
                }}
                QLabel[info_type="description"] {{
                    color: {text_muted};
                    font-size: 11px;
                    font-style: italic;
                }}
            """
        }
    
    def register_widget(self, widget: QWidget, style_key: str = None):
        """Register widget to color management"""
        if widget not in self.registered_widgets:
            self.registered_widgets.append((widget, style_key))
    
    def unregister_widget(self, widget: QWidget):
        """Remove widget from color management"""
        self.registered_widgets = [(w, s) for w, s in self.registered_widgets if w != widget]
    
    def set_theme(self, theme: ColorTheme):
        """Change theme and update all widgets"""
        self.palette.set_theme(theme)
        self.update_all_widgets()
        self.theme_changed.emit(theme.value)
    
    def get_style_for_component(self, component_name: str) -> str:
        """Return style for specified component"""
        template = self.style_templates.get(component_name, "")
        if not template:
            return ""
        
        # Apply color values to template
        colors = self._get_color_values()
        return template.format(**colors)
    
    def _get_color_values(self) -> Dict[str, str]:
        """Get all color values"""
        palette = self.palette.get_palette()
        
        # Create additional color variations
        colors = palette.copy()
        
        # Gradients
        colors['gradient_bg'] = self.palette.get_gradient('background_primary', 'background_secondary')
        colors['gradient_nav'] = self.palette.get_gradient('background_secondary', 'background_tertiary')
        colors['gradient_group'] = self.palette.get_gradient('background_primary', 'background_secondary')
        
        # Button gradients
        colors['gradient_key_normal'] = self.palette.get_gradient('background_primary', 'background_secondary')
        colors['gradient_key_hover'] = self.palette.get_gradient('background_hover', 'background_active')
        colors['gradient_key_capturing'] = self.palette.get_gradient('primary', 'primary')
        
        # Shadow colors
        colors['primary_shadow'] = self.palette.get_rgba('primary', 0.3)
        colors['success_shadow'] = self.palette.get_rgba('success', 0.2)
        colors['danger_light'] = self.palette.get_rgba('danger', 0.1)
        
        # Daha koyu tonlar
        primary_color = self.palette.get_qcolor('primary')
        colors['primary_dark'] = primary_color.darker(120).name()
        
        success_color = self.palette.get_qcolor('success')
        colors['success_light'] = success_color.lighter(110).name()
        
        return colors
    
    def update_all_widgets(self):
        """Update all registered widgets"""
        for widget, style_key in self.registered_widgets:
            if widget and not widget.isHidden():
                if style_key:
                    style = self.get_style_for_component(style_key)
                    widget.setStyleSheet(style)
    
    def get_complete_stylesheet(self) -> str:
        """Return unified stylesheet for all components"""
        complete_style = ""
        for component_name in self.style_templates.keys():
            complete_style += self.get_style_for_component(component_name) + "\n"
        return complete_style
    
    def apply_theme_to_widget(self, widget: QWidget, custom_styles: Dict[str, str] = None):
        """Belirli bir widget'a tema uygula"""
        base_style = self.get_complete_stylesheet()
        
        if custom_styles:
            colors = self._get_color_values()
            for selector, template in custom_styles.items():
                formatted_style = template.format(**colors)
                base_style += f"\n{selector} {{ {formatted_style} }}"
        
        widget.setStyleSheet(base_style)
    
    def create_custom_style(self, template: str) -> str:
        """Fill custom style template with color values"""
        colors = self._get_color_values()
        return template.format(**colors)


# Global window color manager instance
window_color_manager = WindowColorManager()


def get_style(component_name: str) -> str:
    """Global function for quick access"""
    return window_color_manager.get_style_for_component(component_name)


def set_theme(theme: ColorTheme):
    """Global function for quick theme change"""
    window_color_manager.set_theme(theme)


def apply_theme_to_app():
    """Apply theme to entire application"""
    app = QApplication.instance()
    if app:
        stylesheet = window_color_manager.get_complete_stylesheet()
        app.setStyleSheet(stylesheet)
