"""
Indicator window module
Handles the visual indicator overlay (crosshair/FOV)
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QBitmap, QResizeEvent
from utils.security import set_window_affinity


class IndicatorWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.indicator_width = 0
        self.indicator_height = 0
        self.indicator_color = QColor(255, 0, 0)
        self.indicator_thickness = 2
        self.is_filled = False
        self.is_circle = False
        
        # Aimbot status
        self.aimbot_enabled = True
        
        # Color settings
        self.enabled_color = QColor(0, 255, 0)
        self.disabled_color = QColor(255, 0, 0)

        # Window Setup
        # We make it a fixed large size centered on screen to avoid constant resizing
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput  # Better than attribute for click-through
        )
        # Note: Qt.WA_TranslucentBackground is incompatible with SetWindowDisplayAffinity
        # Removed to ensure screen capture protection works. Using setMask instead.
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Initialize with a reasonable fixed size (e.g., 500x500) which should cover most FOV needs
        # This prevents the window from "jumping" around or resizing constantly
        self.setFixedSize(600, 600)
        self.center_on_screen()

    def center_on_screen(self):
        screen_geo = QApplication.primaryScreen().geometry()
        x = (screen_geo.width() - self.width()) // 2
        y = (screen_geo.height() - self.height()) // 2
        self.move(int(x), int(y))

    def paintEvent(self, event):
        """Draws the indicator at the exact center of the widget"""
        if self.indicator_width <= 0 or self.indicator_height <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        
        # Center of the widget (which is centered on screen)
        # We use floating point for precision drawing
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        
        # Offset logic from original (1px up/left adjustment seems intentional for pixel-perfect centering in games)
        center_x -= 1.0
        center_y -= 1.0
        
        # Select color
        current_color = self.enabled_color if self.aimbot_enabled else self.disabled_color
        
        # Pen Setup
        pen = QPen(current_color)
        pen.setWidthF(float(self.indicator_thickness))
        pen.setJoinStyle(Qt.MiterJoin)
        pen.setCapStyle(Qt.SquareCap)
        
        painter.setPen(pen)
        
        if self.is_filled:
            painter.setBrush(QBrush(current_color))
        else:
            painter.setBrush(Qt.NoBrush)
            
        # dimensions
        w = float(self.indicator_width)
        h = float(self.indicator_height)
        
        # Top-left corner for drawing
        # Adjust for thickness to ensure outline uses "center" of the line or outer? 
        # Usually QPen draws centered on the line path.
        # If we want exact outer dimensions matched, we don't adjust much for simple shapes
        # but for pixel perfect:
        top_left_x = center_x - (w / 2.0)
        top_left_y = center_y - (h / 2.0)
        
        if self.is_circle:
             painter.drawEllipse(QRect(int(top_left_x), int(top_left_y), int(w), int(h)))
        else:
             painter.drawRect(int(top_left_x), int(top_left_y), int(w), int(h))

    def update_mask(self):
        """Updates the window mask to match the indicator shape for transparency"""
        if self.indicator_width <= 0 or self.indicator_height <= 0:
            self.clearMask()
            return

        bmp = QBitmap(self.size())
        bmp.fill(Qt.color0) # Transparent

        painter = QPainter(bmp)
        # Mask is 1-bit, no antialiasing
        
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        center_x -= 1.0
        center_y -= 1.0

        w = float(self.indicator_width)
        h = float(self.indicator_height)
        top_left_x = center_x - (w / 2.0)
        top_left_y = center_y - (h / 2.0)

        # Pen Setup for mask (must be opaque)
        pen = QPen(Qt.color1)
        pen.setWidthF(float(self.indicator_thickness))
        pen.setJoinStyle(Qt.MiterJoin)
        pen.setCapStyle(Qt.SquareCap)

        painter.setPen(pen)

        if self.is_filled:
            painter.setBrush(Qt.color1)
        else:
            painter.setBrush(Qt.NoBrush)

        if self.is_circle:
            painter.drawEllipse(QRect(int(top_left_x), int(top_left_y), int(w), int(h)))
        else:
            painter.drawRect(int(top_left_x), int(top_left_y), int(w), int(h))
        
        painter.end()
        self.setMask(bmp)

    def update_indicator(self, width, height, color, thickness, is_filled, is_circle=False):
        """Updates the indicator's properties and requests a repaint."""
        self.indicator_width = width
        self.indicator_height = height
        self.disabled_color = color
        self.indicator_thickness = thickness
        self.is_filled = is_filled
        self.is_circle = is_circle

        self.update_mask()

        if self.indicator_width <= 0 or self.indicator_height <= 0:
             # Just paint nothing or hide?
             # Better to keep shown but paint nothing logic handles it
             self.update()
             return
        
        self.update()
    
    def showEvent(self, event):
        super().showEvent(event)
        # Apply screen capture protection
        set_window_affinity(int(self.winId()))
        self.update_mask()

    def set_aimbot_status(self, enabled):
        """Set aimbot status and update visual"""
        self.aimbot_enabled = enabled
        self.update()
