"""
Spike Timer Window
A modern HUD-style overlay for the Spike Timer
"""

import time
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QBitmap
from utils.security import set_window_affinity

class SpikeTimerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_time = 45000 # 45 seconds default
        self.time_left = 0  
        self.start_timestamp = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.on_timer_finished = None 
        
        # Window flags for overlay
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        # Qt.WA_TranslucentBackground is incompatible with SetWindowDisplayAffinity
        # We use setMask instead for rounded corners
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Dimensions
        self.setFixedSize(160, 60)
        self.center_on_top()
        
        # Create mask for rounded corners since we disabled TranslucentBackground
        self.update_mask()

    def update_mask(self):
        bmp = QBitmap(self.size())
        bmp.fill(Qt.color0) # Transparent
        painter = QPainter(bmp)
        painter.setBrush(Qt.color1) # Opaque area
        painter.setPen(Qt.NoPen)
        # Match the rounded rect drawing in paintEvent
        rect = self.rect()
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        painter.end()
        self.setMask(bmp)
        
    def center_on_top(self):
        """Position window at the top center of screen with margin"""
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 80  # Slightly down from top
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        # Apply screen capture protection
        set_window_affinity(int(self.winId()))
        
    def start_timer(self, duration_ms=45000):
        """Start timer with duration"""
        self.total_time = duration_ms
        self.time_left = duration_ms
        self.start_timestamp = time.time()
        self.update_display()
        self.show()
        self.raise_() 
        self.timer.start(10) # 10ms update
        
    def stop_timer(self):
        """Stop and hide"""
        self.timer.stop()
        self.hide()
        
    def update_timer(self):
        elapsed_seconds = time.time() - self.start_timestamp
        elapsed_ms = int(elapsed_seconds * 1000)
        self.time_left = self.total_time - elapsed_ms
        
        if self.time_left <= 0:
            self.time_left = 0
            self.timer.stop()
            self.hide()
            if self.on_timer_finished:
                self.on_timer_finished()
                
        self.update_display()
        
    def update_display(self):
        self.update() # Trigger paintEvent
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # 1. Background (Dark Gradient)
        # Alpha bumped to 255 as we disabled TranslucentBackground
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(20, 20, 20, 255))
        gradient.setColorAt(1, QColor(40, 40, 40, 255))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        
        # 2. Progress Bar Background
        bar_height = 4
        bar_y = self.height() - 8
        painter.setBrush(QColor(60, 60, 60))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(10, bar_y, self.width() - 20, bar_height, 2, 2)
        
        # 3. Progress Bar Fill & Color Logic
        progress_pct = self.time_left / self.total_time
        fill_width = (self.width() - 20) * progress_pct
        
        # Dynamic Color
        if self.time_left > 7000:
            main_color = QColor("#00cc66") # Green
        elif self.time_left > 3500:
            main_color = QColor("#ecc94b") # Yellow
        else:
            main_color = QColor("#f56565") # Red
            
        painter.setBrush(main_color)
        painter.drawRoundedRect(10, bar_y, int(fill_width), bar_height, 2, 2)
        
        # 4. Text - "SPIKE" Label
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(QRectF(10, 5, self.width()-20, 20), Qt.AlignLeft | Qt.AlignVCenter, "SPIKE TIMEOUT")
        
        # 5. Text - Time
        seconds = self.time_left // 1000
        ms_remainder = self.time_left % 1000
        # Convert ms to 0-60 scale (frames-like)
        frames = int((ms_remainder / 1000) * 60)
        time_str = f"{seconds:02d}.{frames:02d}"
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 20, QFont.Bold))
        # Add glow effect hint by drawing delicately? (Optional/Expensive, stuck to simple clean text)
        painter.drawText(QRectF(0, 5, self.width(), 40), Qt.AlignCenter, time_str)
        
