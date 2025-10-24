"""
Modern Renk Paleti Sistemi
Bu modül, uygulama genelinde kullanılacak renk paletlerini yönetir.
"""

from enum import Enum
from typing import Dict, Tuple, Optional
from PyQt5.QtGui import QColor


class ColorTheme(Enum):
    """Mevcut renk temaları"""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    ORANGE = "orange"
    RED = "red"
    CUSTOM = "custom"


class ColorPalette:
    """
    Renk paleti yönetim sınıfı
    Farklı temalar için renk setleri sağlar
    """
    
    def __init__(self, theme: ColorTheme = ColorTheme.LIGHT):
        self.current_theme = theme
        self._palettes = self._initialize_palettes()
        self._custom_colors = {}
    
    def _initialize_palettes(self) -> Dict[ColorTheme, Dict[str, str]]:
        """Tüm renk paletlerini başlat"""
        return {
            ColorTheme.LIGHT: {
                # Ana renkler
                'primary': '#3498db',
                'secondary': '#95a5a6',
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'info': '#17a2b8',
                
                # Arka plan renkleri
                'background_primary': '#ffffff',
                'background_secondary': '#f8f9fa',
                'background_tertiary': '#e9ecef',
                'background_hover': '#f1f3f4',
                'background_active': '#ecf0f1',
                
                # Metin renkleri
                'text_primary': '#212529',
                'text_secondary': '#495057',
                'text_muted': '#6c757d',
                'text_light': '#adb5bd',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#dee2e6',
                'border_secondary': '#e9ecef',
                'border_light': '#f8f9fa',
                'border_dark': '#adb5bd',
                
                # Navigasyon renkleri
                'nav_background': '#f8f9fa',
                'nav_border': '#dee2e6',
                'nav_button_hover': '#f8f9fa',
                'nav_button_active': '#ecf0f1',
                'nav_accent': '#3498db',
                
                # Gölge renkleri
                'shadow_light': 'rgba(0, 0, 0, 0.1)',
                'shadow_medium': 'rgba(0, 0, 0, 0.15)',
                'shadow_dark': 'rgba(0, 0, 0, 0.2)',
            },
            
            ColorTheme.DARK: {
                # Ana renkler
                'primary': '#4a9eff',
                'secondary': '#6c757d',
                'success': '#28a745',
                'warning': '#ffc107',
                'danger': '#dc3545',
                'info': '#17a2b8',
                
                # Arka plan renkleri
                'background_primary': '#1a1a1a',
                'background_secondary': '#2d2d2d',
                'background_tertiary': '#3a3a3a',
                'background_hover': '#404040',
                'background_active': '#4a4a4a',
                
                # Metin renkleri
                'text_primary': '#ffffff',
                'text_secondary': '#e9ecef',
                'text_muted': '#adb5bd',
                'text_light': '#6c757d',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#404040',
                'border_secondary': '#3a3a3a',
                'border_light': '#2d2d2d',
                'border_dark': '#1a1a1a',
                
                # Navigasyon renkleri
                'nav_background': '#2d2d2d',
                'nav_border': '#404040',
                'nav_button_hover': '#404040',
                'nav_button_active': '#4a4a4a',
                'nav_accent': '#4a9eff',
                
                # Gölge renkleri
                'shadow_light': 'rgba(0, 0, 0, 0.3)',
                'shadow_medium': 'rgba(0, 0, 0, 0.4)',
                'shadow_dark': 'rgba(0, 0, 0, 0.5)',
            },
            
            ColorTheme.BLUE: {
                # Ana renkler
                'primary': '#0066cc',
                'secondary': '#4d79a4',
                'success': '#28a745',
                'warning': '#ffc107',
                'danger': '#dc3545',
                'info': '#17a2b8',
                
                # Arka plan renkleri
                'background_primary': '#f0f4f8',
                'background_secondary': '#e1ecf4',
                'background_tertiary': '#d3e2f0',
                'background_hover': '#c5d9ec',
                'background_active': '#b7d0e8',
                
                # Metin renkleri
                'text_primary': '#1a365d',
                'text_secondary': '#2d3748',
                'text_muted': '#4a5568',
                'text_light': '#718096',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#bee3f8',
                'border_secondary': '#90cdf4',
                'border_light': '#63b3ed',
                'border_dark': '#3182ce',
                
                # Navigasyon renkleri
                'nav_background': '#e1ecf4',
                'nav_border': '#bee3f8',
                'nav_button_hover': '#c5d9ec',
                'nav_button_active': '#b7d0e8',
                'nav_accent': '#0066cc',
                
                # Gölge renkleri
                'shadow_light': 'rgba(0, 102, 204, 0.1)',
                'shadow_medium': 'rgba(0, 102, 204, 0.15)',
                'shadow_dark': 'rgba(0, 102, 204, 0.2)',
            },
            
            ColorTheme.GREEN: {
                # Ana renkler
                'primary': '#38a169',
                'secondary': '#68d391',
                'success': '#48bb78',
                'warning': '#ed8936',
                'danger': '#e53e3e',
                'info': '#4299e1',
                
                # Arka plan renkleri
                'background_primary': '#f0fff4',
                'background_secondary': '#c6f6d5',
                'background_tertiary': '#9ae6b4',
                'background_hover': '#68d391',
                'background_active': '#48bb78',
                
                # Metin renkleri
                'text_primary': '#1a202c',
                'text_secondary': '#2d3748',
                'text_muted': '#4a5568',
                'text_light': '#718096',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#9ae6b4',
                'border_secondary': '#68d391',
                'border_light': '#48bb78',
                'border_dark': '#38a169',
                
                # Navigasyon renkleri
                'nav_background': '#c6f6d5',
                'nav_border': '#9ae6b4',
                'nav_button_hover': '#68d391',
                'nav_button_active': '#48bb78',
                'nav_accent': '#38a169',
                
                # Gölge renkleri
                'shadow_light': 'rgba(56, 161, 105, 0.1)',
                'shadow_medium': 'rgba(56, 161, 105, 0.15)',
                'shadow_dark': 'rgba(56, 161, 105, 0.2)',
            },
            
            ColorTheme.PURPLE: {
                # Ana renkler
                'primary': '#805ad5',
                'secondary': '#b794f6',
                'success': '#38a169',
                'warning': '#ed8936',
                'danger': '#e53e3e',
                'info': '#4299e1',
                
                # Arka plan renkleri
                'background_primary': '#faf5ff',
                'background_secondary': '#e9d8fd',
                'background_tertiary': '#d6bcfa',
                'background_hover': '#c4b5fd',
                'background_active': '#b794f6',
                
                # Metin renkleri
                'text_primary': '#1a202c',
                'text_secondary': '#2d3748',
                'text_muted': '#4a5568',
                'text_light': '#718096',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#d6bcfa',
                'border_secondary': '#c4b5fd',
                'border_light': '#b794f6',
                'border_dark': '#9f7aea',
                
                # Navigasyon renkleri
                'nav_background': '#e9d8fd',
                'nav_border': '#d6bcfa',
                'nav_button_hover': '#c4b5fd',
                'nav_button_active': '#b794f6',
                'nav_accent': '#805ad5',
                
                # Gölge renkleri
                'shadow_light': 'rgba(128, 90, 213, 0.1)',
                'shadow_medium': 'rgba(128, 90, 213, 0.15)',
                'shadow_dark': 'rgba(128, 90, 213, 0.2)',
            },
            
            ColorTheme.ORANGE: {
                # Ana renkler
                'primary': '#dd6b20',
                'secondary': '#fd9853',
                'success': '#38a169',
                'warning': '#ed8936',
                'danger': '#e53e3e',
                'info': '#4299e1',
                
                # Arka plan renkleri
                'background_primary': '#fffaf0',
                'background_secondary': '#feebc8',
                'background_tertiary': '#fbd38d',
                'background_hover': '#f6ad55',
                'background_active': '#ed8936',
                
                # Metin renkleri
                'text_primary': '#1a202c',
                'text_secondary': '#2d3748',
                'text_muted': '#4a5568',
                'text_light': '#718096',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#fbd38d',
                'border_secondary': '#f6ad55',
                'border_light': '#ed8936',
                'border_dark': '#dd6b20',
                
                # Navigasyon renkleri
                'nav_background': '#feebc8',
                'nav_border': '#fbd38d',
                'nav_button_hover': '#f6ad55',
                'nav_button_active': '#ed8936',
                'nav_accent': '#dd6b20',
                
                # Gölge renkleri
                'shadow_light': 'rgba(221, 107, 32, 0.1)',
                'shadow_medium': 'rgba(221, 107, 32, 0.15)',
                'shadow_dark': 'rgba(221, 107, 32, 0.2)',
            },
            
            ColorTheme.RED: {
                # Ana renkler
                'primary': '#e53e3e',
                'secondary': '#fc8181',
                'success': '#38a169',
                'warning': '#ed8936',
                'danger': '#c53030',
                'info': '#4299e1',
                
                # Arka plan renkleri
                'background_primary': '#fff5f5',
                'background_secondary': '#fed7d7',
                'background_tertiary': '#feb2b2',
                'background_hover': '#fc8181',
                'background_active': '#f56565',
                
                # Metin renkleri
                'text_primary': '#1a202c',
                'text_secondary': '#2d3748',
                'text_muted': '#4a5568',
                'text_light': '#718096',
                'text_white': '#ffffff',
                
                # Kenarlık renkleri
                'border_primary': '#feb2b2',
                'border_secondary': '#fc8181',
                'border_light': '#f56565',
                'border_dark': '#e53e3e',
                
                # Navigasyon renkleri
                'nav_background': '#fed7d7',
                'nav_border': '#feb2b2',
                'nav_button_hover': '#fc8181',
                'nav_button_active': '#f56565',
                'nav_accent': '#e53e3e',
                
                # Gölge renkleri
                'shadow_light': 'rgba(229, 62, 62, 0.1)',
                'shadow_medium': 'rgba(229, 62, 62, 0.15)',
                'shadow_dark': 'rgba(229, 62, 62, 0.2)',
            }
        }
    
    def set_theme(self, theme: ColorTheme):
        """Aktif temayı değiştir"""
        self.current_theme = theme
    
    def get_color(self, color_key: str) -> str:
        """Belirtilen renk anahtarı için renk değerini döndür"""
        if self.current_theme == ColorTheme.CUSTOM:
            return self._custom_colors.get(color_key, '#000000')
        
        palette = self._palettes.get(self.current_theme, self._palettes[ColorTheme.LIGHT])
        return palette.get(color_key, '#000000')
    
    def get_qcolor(self, color_key: str) -> QColor:
        """QColor objesi olarak renk döndür"""
        hex_color = self.get_color(color_key)
        return QColor(hex_color)
    
    def get_rgba(self, color_key: str, alpha: float = 1.0) -> str:
        """RGBA formatında renk döndür"""
        hex_color = self.get_color(color_key)
        # Hex'i RGB'ye çevir
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    def get_palette(self) -> Dict[str, str]:
        """Mevcut tema için tüm renk paletini döndür"""
        if self.current_theme == ColorTheme.CUSTOM:
            return self._custom_colors.copy()
        return self._palettes.get(self.current_theme, {}).copy()
    
    def set_custom_color(self, color_key: str, hex_color: str):
        """Özel renk ayarla"""
        self._custom_colors[color_key] = hex_color
    
    def get_gradient(self, start_color: str, end_color: str, direction: str = "vertical") -> str:
        """Gradient CSS döndür"""
        start = self.get_color(start_color)
        end = self.get_color(end_color)
        
        if direction == "vertical":
            return f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {start}, stop:1 {end})"
        elif direction == "horizontal":
            return f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {start}, stop:1 {end})"
        elif direction == "diagonal":
            return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {start}, stop:1 {end})"
        else:
            return start
    
    def get_available_themes(self) -> list:
        """Mevcut temaları listele"""
        return [theme.value for theme in ColorTheme]
    
    def create_color_variations(self, base_color: str, steps: int = 5) -> list:
        """Bir ana renkten farklı tonlar oluştur"""
        base = QColor(base_color)
        variations = []
        
        for i in range(steps):
            # Parlaklık değişimi
            factor = 0.3 + (0.7 * i / (steps - 1))  # 0.3'ten 1.0'a
            lighter = base.lighter(int(100 + (100 * factor)))
            variations.append(lighter.name())
        
        return variations


# Global renk paleti instance'ı
color_palette = ColorPalette()


def get_color(color_key: str) -> str:
    """Hızlı erişim için global fonksiyon"""
    return color_palette.get_color(color_key)


def set_theme(theme: ColorTheme):
    """Hızlı tema değişimi için global fonksiyon"""
    color_palette.set_theme(theme)


def get_qcolor(color_key: str) -> QColor:
    """QColor için hızlı erişim"""
    return color_palette.get_qcolor(color_key)