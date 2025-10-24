"""
Spike Timer Window
A non-interactive window with transparent black background and sharp corners made with PyQt5
"""

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen


class SpikeTimerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.time_left = 0  # milliseconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.on_timer_finished = None  # Callback function
        self.on_timer_finished = None  # Callback function
        
        # Window settings
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        
        # Pencere boyutu ve konumu
        self.setFixedSize(120, 50)
        self.center_on_top()
        
        # Label settings
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, 120, 50)
        font = QFont("Arial", 18, QFont.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet("color: white; background: transparent; border: none;")
        self.label.setText("00:00")
        
    def center_on_top(self):
        """Position window at the top center of screen"""
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 0  # Top
        self.move(x, y)
        
    def start_timer(self, duration_ms):
        """Start timer"""
        # Start with 44 seconds
        self.time_left = 44000  # 44 seconds = 44000 ms
        self.update_display()
        self.show()
        self.raise_()  # Bring window to front
        # print(f"Spike Timer: Started timer for 44 seconds")
        self.timer.start(10)  # 10ms = 0.01s
        
    def show(self):
        """Show window"""
        super().show()
        # print("Spike Timer Window: Shown")
        # Bring window to front
        self.raise_()
        
    def update_timer(self):
        """Update timer"""
        self.time_left -= 10
        if self.time_left <= 0:
            self.time_left = 0
            self.timer.stop()
            self.hide()
            # print("Spike Timer: Timer finished")
            # Call callback function
            if self.on_timer_finished:
                self.on_timer_finished()
        self.update_display()
        
    def update_display(self):
        """Update display"""
        seconds = self.time_left // 1000
        milliseconds = (self.time_left % 1000) // 10  # Salise (0-99)
        self.label.setText(f"{seconds:02d}:{milliseconds:02d}")
        
    def paintEvent(self, event):
        """Draw background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Black background (transparent)
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))  # 70% transparency
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRect(self.rect())
        
    def stop_timer(self):
        """Stop timer"""
        self.timer.stop()
        self.hide()
        # print("Spike Timer Window: Hidden")
