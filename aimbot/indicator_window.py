"""
Indicator window module
Handles the visual indicator overlay
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush


class IndicatorWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.indicator_width = 0  # X size
        self.indicator_height = 0  # Y size
        self.indicator_color = QColor(255, 0, 0)  # User's selected color (when disabled)
        self.indicator_thickness = 2
        self.is_filled = False
        
        # Aimbot status
        self.aimbot_enabled = True
        
        # Color settings
        self.enabled_color = QColor(0, 255, 0)  # Green (when enabled)
        self.disabled_color = QColor(255, 0, 0)  # User's selected color (when disabled)

        # Make window always on top, frameless and transparent to mouse events
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        """Method that draws the rectangle and 1x1 point at the center to the window."""
        if self.indicator_width <= 0 or self.indicator_height <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # Edge smoothing
        
        # Rectangle center - EXACT SCREEN CENTER (unchanging)
        screen_geo = QApplication.primaryScreen().geometry()
        screen_center_x = screen_geo.width() // 2
        screen_center_y = screen_geo.height() // 2
        
        # Convert to window coordinates
        window_pos = self.pos()
        rect_center_x = screen_center_x - window_pos.x()
        rect_center_y = screen_center_y - window_pos.y()
        
        # Move square 1px up and 1px left
        rect_center_x -= 1  # 1px left
        rect_center_y -= 1  # 1px up
        
        # Select color based on aimbot status
        current_color = self.enabled_color if self.aimbot_enabled else self.disabled_color
        
        # Rectangle's main pen
        rect_pen = QPen(current_color, self.indicator_thickness)
        
        if self.is_filled:
            # If filled, paint the rectangle
            painter.setPen(rect_pen)
            painter.setBrush(QBrush(current_color))
        else:
            # If empty, set to draw only the outline
            painter.setBrush(Qt.NoBrush)
            
            # --- NEW: Draw a 1x1 pixel point at the center ---
            # Create a separate pen for the point and set its color and 1px thickness
            dot_pen = QPen(current_color, 1)
            painter.setPen(dot_pen)
            painter.drawPoint(QPoint(rect_center_x, rect_center_y)) # Draws a 1x1 pixel point at the center

        # Reset pen to draw the rectangle's main outline
        painter.setPen(rect_pen)

        # Draw rectangle - based on center
        half_width = (self.indicator_width - self.indicator_thickness) / 2
        half_height = (self.indicator_height - self.indicator_thickness) / 2
        
        rect_x = rect_center_x - half_width
        rect_y = rect_center_y - half_height
        
        painter.drawRect(int(rect_x), int(rect_y), int(self.indicator_width - self.indicator_thickness), int(self.indicator_height - self.indicator_thickness))

    def update_indicator(self, width, height, color, thickness, is_filled):
        """Updates the indicator's properties and applies offset by centering the screen."""
        self.indicator_width = width
        self.indicator_height = height
        self.disabled_color = color  # Use user's selected color when disabled
        self.indicator_thickness = thickness
        self.is_filled = is_filled

        if self.indicator_width <= 0 or self.indicator_height <= 0:
            self.hide()
            return
        
        # Calculate area for rectangle
        window_width = max(width, height) + 20  # Largest dimension + extra space
        window_height = max(width, height) + 20
        self.setFixedSize(window_width, window_height)
        
        screen_geo = QApplication.primaryScreen().geometry()
        
        # Position window at the center of the screen
        x = screen_geo.center().x() - window_width / 2
        y = screen_geo.center().y() - window_height / 2
        
        offset_x = 0
        offset_y = 0
        self.move(int(x + offset_x), int(y + offset_y))
        
        self.update()
    
    def set_aimbot_status(self, enabled):
        """Set aimbot status and update screen"""
        self.aimbot_enabled = enabled
        self.update()  # Redraw screen
