"""
Modern Notification System
Notifications that appear from the bottom right corner for Aimbot/Triggerbot status
"""

import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect,
    QApplication, QFrame, QPushButton
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, 
    pyqtSignal, QPoint, QSize
)
from PyQt5.QtGui import QColor, QFont

from controllers.theme_controller import WindowColorManager
from models.color_palette import get_color


class ModernNotification(QWidget):
    """Modern notification widget"""
    
    # Notification types
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"
    INFO = "info"
    AIMBOT = "aimbot"
    TRIGGERBOT = "triggerbot"
    
    closed = pyqtSignal()
    
    def __init__(self, title: str, message: str, notification_type: str = INFO, duration: int = 3000):
        super().__init__()
        
        try:
            self.title = title
            self.message = message
            self.notification_type = notification_type
            self.duration = duration
            self.color_manager = WindowColorManager()
            
            # Animation properties
            self.opacity_effect = QGraphicsOpacityEffect()
            self.setGraphicsEffect(self.opacity_effect)
            
            # Progress bar for auto-close
            self.progress_value = 0
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(self._update_progress)
            
            self.setup_ui()
            self.setup_animations()
            
            # Auto close timer
            if duration > 0:
                # Start progress animation
                self.progress_timer.start(50)  # Update every 50ms
                self.auto_close_timer = QTimer()
                self.auto_close_timer.setSingleShot(True)
                self.auto_close_timer.timeout.connect(self.close_notification)
                self.auto_close_timer.start(duration)
                
        except Exception as e:
            print(f"ModernNotification init error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def setup_ui(self):
        """Setup UI - Completely redesigned"""
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 120)
        
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # İçerik frame'i with shadow effect
        self.content_frame = QFrame()
        self.content_frame.setObjectName("notificationFrame")
        main_layout.addWidget(self.content_frame)
        
        # Frame layout
        frame_layout = QVBoxLayout(self.content_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        # Top content area
        top_widget = QWidget()
        top_widget.setObjectName("topContent")
        content_layout = QHBoxLayout(top_widget)
        content_layout.setContentsMargins(20, 15, 20, 10)
        content_layout.setSpacing(15)
        
        # Icon container with circular background
        icon_container = QWidget()
        icon_container.setObjectName("iconContainer")
        icon_container.setFixedSize(50, 50)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel()
        self.icon_label.setObjectName("iconLabel")
        self.icon_label.setFixedSize(50, 50)
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.icon_label)
        
        content_layout.addWidget(icon_container)
        
        # Text area with better spacing
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 2, 0, 2)
        text_layout.setSpacing(4)
        
        # Title with premium typography
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("notificationTitle")
        text_layout.addWidget(self.title_label)
        
        # Message with subtle styling
        self.message_label = QLabel(self.message)
        self.message_label.setObjectName("notificationMessage")
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.message_label)
        
        text_layout.addStretch()
        content_layout.addWidget(text_widget, 1)
        
        # Modern close button
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("notificationClose")
        self.close_button.setFixedSize(28, 28)
        self.close_button.clicked.connect(self.close_notification)
        self.close_button.setCursor(Qt.PointingHandCursor)
        content_layout.addWidget(self.close_button, 0, Qt.AlignTop)
        
        frame_layout.addWidget(top_widget)
        
        # Progress bar at bottom
        self.progress_bar = QWidget()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setFixedHeight(4)
        frame_layout.addWidget(self.progress_bar)
        
        # Apply style
        self.apply_style()
    
    def setup_animations(self):
        """Setup animations - Enhanced with multiple effects"""
        # Slide in animation with smooth bounce
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(700)
        self.slide_animation.setEasingCurve(QEasingCurve.OutBack)
        
        # Fade animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _update_progress(self):
        """Update progress bar animation"""
        if self.duration > 0:
            self.progress_value += 50  # 50ms increment
            progress_percent = min(100, (self.progress_value / self.duration) * 100)
            
            # Update progress bar width
            self.progress_bar.setStyleSheet(f"""
                QWidget#progressBar {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(255, 255, 255, 0.4),
                        stop:{progress_percent/100} rgba(255, 255, 255, 0.4),
                        stop:{progress_percent/100} rgba(255, 255, 255, 0.1),
                        stop:1 rgba(255, 255, 255, 0.1));
                    border-radius: 0px 0px 18px 18px;
                }}
            """)
            
            if progress_percent >= 100:
                self.progress_timer.stop()
    
    def apply_style(self):
        """Apply style based on notification type - Premium redesign (Qt-compatible)"""
        # Premium color scheme with gradients (Qt-compatible)
        colors = {
            self.SUCCESS: {
                'bg_start': 'rgba(75, 75, 75, 250)',
                'bg_end': 'rgba(95, 95, 95, 250)',
                'accent': 'rgba(130, 130, 130, 255)',
                'icon': '✓',
                'icon_bg': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(110, 110, 110, 255), stop:1 rgba(90, 90, 90, 255))',
            },
            self.WARNING: {
                'bg_start': 'rgba(75, 75, 60, 250)',
                'bg_end': 'rgba(95, 95, 80, 250)',
                'accent': 'rgba(120, 120, 100, 255)',
                'icon': '⚠',
                'icon_bg': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(110, 110, 90, 255), stop:1 rgba(90, 90, 70, 255))',
            },
            self.ERROR: {
                'bg_start': 'rgba(75, 60, 60, 250)',
                'bg_end': 'rgba(95, 80, 80, 250)',
                'accent': 'rgba(120, 100, 100, 255)',
                'icon': '✗',
                'icon_bg': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(110, 90, 90, 255), stop:1 rgba(90, 70, 70, 255))',
            },
            self.INFO: {
                'bg_start': 'rgba(65, 65, 85, 250)',
                'bg_end': 'rgba(85, 85, 105, 250)',
                'accent': 'rgba(110, 110, 130, 255)',
                'icon': 'ℹ',
                'icon_bg': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(100, 100, 120, 255), stop:1 rgba(80, 80, 100, 255))',
            },
            self.AIMBOT: {
                'bg_start': 'rgba(65, 85, 95, 250)',
                'bg_end': 'rgba(85, 105, 115, 250)',
                'accent': 'rgba(110, 130, 140, 255)',
                'icon': '🎯',
                'icon_bg': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(100, 120, 130, 255), stop:1 rgba(80, 100, 110, 255))',
            },
            self.TRIGGERBOT: {
                'bg_start': 'rgba(95, 65, 65, 250)',
                'bg_end': 'rgba(115, 85, 85, 250)',
                'accent': 'rgba(140, 110, 110, 255)',
                'icon': '🔫',
                'icon_bg': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(130, 100, 100, 255), stop:1 rgba(110, 80, 80, 255))',
            }
        }
        
        color_config = colors.get(self.notification_type, colors[self.INFO])
        
        # Set icon
        self.icon_label.setText(color_config['icon'])
        
        # Qt-compatible styling (removed unsupported CSS properties)
        style = f"""
            QWidget {{
                background: transparent;
            }}
            
            QFrame#notificationFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color_config['bg_start']}, 
                    stop:1 {color_config['bg_end']});
                border: 2px solid {color_config['accent']};
                border-radius: 20px;
            }}
            
            QWidget#topContent {{
                background: transparent;
            }}
            
            QWidget#iconContainer {{
                background: transparent;
            }}
            
            QLabel#iconLabel {{
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                background: {color_config['icon_bg']};
                border: 3px solid rgba(255, 255, 255, 0.2);
                border-radius: 25px;
            }}
            
            QLabel#notificationTitle {{
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Roboto', 'Arial';
                margin: 0px;
                padding: 0px;
                background: transparent;
            }}
            
            QLabel#notificationMessage {{
                color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
                font-family: 'Segoe UI', 'Roboto', 'Arial';
                margin: 0px;
                padding: 0px;
                background: transparent;
            }}
            
            QPushButton#notificationClose {{
                background: rgba(220, 53, 69, 100);
                border: 1px solid rgba(220, 53, 69, 0.5);
                border-radius: 14px;
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }}
            
            QPushButton#notificationClose:hover {{
                background: rgba(220, 53, 69, 180);
                border: 1px solid rgba(220, 53, 69, 0.8);
            }}
            
            QPushButton#notificationClose:pressed {{
                background: rgba(220, 53, 69, 80);
                border: 1px solid rgba(220, 53, 69, 0.3);
            }}
            
            QWidget#progressBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.4),
                    stop:0 rgba(255, 255, 255, 0.4),
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:1 rgba(255, 255, 255, 0.1));
                border-radius: 0px 0px 18px 18px;
            }}
        """
        
        self.setStyleSheet(style)
    
    def _lighten_color(self, hex_color: str, amount: int) -> str:
        """Lighten the color"""
        try:
            color = QColor(hex_color)
            h, s, v, a = color.getHsv()
            v = min(255, v + amount)
            color.setHsv(h, s, v, a)
            return color.name()
        except:
            return hex_color
    
    def show_notification(self):
        """Show notification"""
        try:
            # QApplication kontrolü
            app = QApplication.instance()
            if not app:
                return
            
            # Ekran boyutlarını al
            desktop = QApplication.desktop()
            if not desktop:
                return
                
            screen_rect = desktop.availableGeometry()
            
            # Başlangıç pozisyonu (ekran dışında)
            start_pos = QPoint(
                screen_rect.width(),
                screen_rect.height() - self.height() - 20
            )
            
            # Bitiş pozisyonu (ekran içinde)
            end_pos = QPoint(
                screen_rect.width() - self.width() - 20,
                screen_rect.height() - self.height() - 20
            )
            
            # Widget'ı konumlandır ve göster
            self.move(start_pos)
            self.show()
            
            # Slide animasyonu
            self.slide_animation.setStartValue(QRect(start_pos, self.size()))
            self.slide_animation.setEndValue(QRect(end_pos, self.size()))
            self.slide_animation.start()
            
            # Fade in
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
            
        except Exception as e:
            print(f"❌ ModernNotification.show_notification error: {e}")
            import traceback
            traceback.print_exc()
    
    def close_notification(self):
        """Close notification - Enhanced animation"""
        # Stop all timers
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
        
        # Slide out with fade
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry()
        
        end_pos = QPoint(
            screen_rect.width() + 50,
            self.pos().y()
        )
        
        # Smooth slide out
        self.slide_animation.setStartValue(self.geometry())
        self.slide_animation.setEndValue(QRect(end_pos, self.size()))
        self.slide_animation.setDuration(400)
        self.slide_animation.setEasingCurve(QEasingCurve.InBack)
        
        # Fade out
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setDuration(400)
        self.fade_animation.finished.connect(self._finish_close)
        
        self.slide_animation.start()
        self.fade_animation.start()
    
    def _finish_close(self):
        """Complete the closing process"""
        self.closed.emit()
        self.close()
        self.deleteLater()
    
    def mousePressEvent(self, event):
        """Tıklama ile kapat"""
        if event.button() == Qt.LeftButton:
            self.close_notification()
    
    def closeEvent(self, event):
        """Widget kapatıldığında tüm timer'ları durdur"""
        # Stop all timers when widget is closed
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
        
        # Stop animations
        if hasattr(self, 'slide_animation'):
            self.slide_animation.stop()
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
        
        event.accept()