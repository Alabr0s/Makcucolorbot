"""
Modern Status Bar System
Modern design for popup messages in the bottom left
"""

from PyQt5.QtWidgets import (
    QStatusBar, QLabel, QWidget, QHBoxLayout, QProgressBar,
    QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

from controllers.theme_controller import WindowColorManager
from models.color_palette import get_color


class ModernStatusBar(QStatusBar):
    """Modern status bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_manager = WindowColorManager()
        self.setup_ui()
        self.apply_modern_style()
        
        # Animation için
        self.fade_timer = QTimer()
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self._start_fade_out)
        
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def setup_ui(self):
        """Setup UI"""
        # Ana widget
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(15, 5, 15, 5)
        self.main_layout.setSpacing(10)
        
        # Status ikonu
        self.status_icon = QLabel("●")
        self.status_icon.setFixedSize(16, 16)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_icon)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.main_layout.addWidget(self.status_label)
        
        # Spacer
        self.main_layout.addStretch()
        
        # Progress bar (isteğe bağlı)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedSize(100, 16)
        self.main_layout.addWidget(self.progress_bar)
        
        # Sağ taraf bilgileri
        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Segoe UI", 8))
        self.main_layout.addWidget(self.info_label)
        
        # Add widget to status bar
        self.addPermanentWidget(self.main_widget, 1)
    
    def apply_modern_style(self):
        """Apply modern style"""
        bg_color = get_color('background_primary')
        border_color = get_color('border_primary')
        text_color = get_color('text_secondary')
        
        style = f"""
            QStatusBar {{
                background: {bg_color};
                border-top: 1px solid {border_color};
                color: {text_color};
                font-family: 'Segoe UI', sans-serif;
                font-size: 9px;
                padding: 0px;
                margin: 0px;
            }}
            
            QWidget {{
                background: transparent;
                color: {text_color};
            }}
            
            QLabel {{
                background: transparent;
                color: {text_color};
                border: none;
                padding: 2px;
            }}
            
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 8px;
                background: {get_color('background_secondary')};
                text-align: center;
                font-size: 8px;
                color: {text_color};
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {get_color('primary')}, 
                    stop:1 {get_color('primary')});
                border-radius: 7px;
                margin: 1px;
            }}
        """
        
        self.setStyleSheet(style)
    
    def showMessage(self, message: str, timeout: int = 0, message_type: str = "info"):
        """Show modern message"""
        # Mesaj türüne göre ikon ve renk
        icons_colors = {
            "success": ("✓", get_color('success')),
            "warning": ("⚠", get_color('warning')),
            "error": ("✗", get_color('danger')),
            "info": ("ℹ", get_color('info')),
            "loading": ("⟳", get_color('primary'))
        }
        
        icon, color = icons_colors.get(message_type, icons_colors["info"])
        
        # İkon ve mesajı ayarla
        self.status_icon.setText(icon)
        self.status_icon.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.status_label.setText(message)
        
        # Fade in effect
        self.opacity_effect.setOpacity(1.0)
        
        # Auto fade timer
        if timeout > 0:
            self.fade_timer.start(timeout)
        else:
            self.fade_timer.stop()
    
    def show_success(self, message: str, timeout: int = 3000):
        """Success message"""
        self.showMessage(message, timeout, "success")
    
    def show_warning(self, message: str, timeout: int = 3000):
        """Warning message"""
        self.showMessage(message, timeout, "warning")
    
    def show_error(self, message: str, timeout: int = 5000):
        """Error message"""
        self.showMessage(message, timeout, "error")
    
    def show_info(self, message: str, timeout: int = 3000):
        """Info message"""
        self.showMessage(message, timeout, "info")
    
    def show_loading(self, message: str):
        """Loading message"""
        self.showMessage(message, 0, "loading")
        # Loading animasyonu için ikon döndürme
        self._start_loading_animation()
    
    def _start_loading_animation(self):
        """Start loading animation"""
        # Basit loading animasyonu
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading_icon)
        self.loading_timer.start(200)
        self.loading_state = 0
    
    def _update_loading_icon(self):
        """Update loading icon"""
        loading_icons = ["⟳", "⟲", "⟳", "⟲"]
        self.status_icon.setText(loading_icons[self.loading_state % len(loading_icons)])
        self.loading_state += 1
    
    def stop_loading(self):
        """Stop loading animation"""
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
        self.status_icon.setText("●")
    
    def _start_fade_out(self):
        """Start fade out animation"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.3)
        self.fade_animation.start()
    
    def show_progress(self, value: int, maximum: int = 100, text: str = ""):
        """Progress bar göster"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        
        if text:
            self.progress_bar.setFormat(f"{text} %p%")
        else:
            self.progress_bar.setFormat("%p%")
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
    
    def set_info(self, info_text: str):
        """Set right side info text"""
        self.info_label.setText(info_text)
    
    def update_theme(self):
        """Refresh style when theme is updated"""
        self.apply_modern_style()


class StatusBarManager:
    """Status bar manager"""
    
    def __init__(self, status_bar: ModernStatusBar):
        self.status_bar = status_bar
        self.message_queue = []
        self.current_message = None
        
        # Queue timer
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self._process_queue)
        self.queue_timer.start(100)  # 100ms'de bir kontrol et
    
    def add_message(self, message: str, message_type: str = "info", timeout: int = 3000, priority: int = 0):
        """Add message to queue"""
        message_data = {
            'message': message,
            'type': message_type,
            'timeout': timeout,
            'priority': priority
        }
        
        # Önceliğe göre sırala
        self.message_queue.append(message_data)
        self.message_queue.sort(key=lambda x: x['priority'], reverse=True)
    
    def _process_queue(self):
        """Process message queue"""
        if not self.message_queue:
            return
        
        # Mevcut mesaj yoksa veya süresi dolmuşsa yeni mesaj göster
        if not self.current_message or self._is_message_expired():
            message_data = self.message_queue.pop(0)
            self._show_message(message_data)
    
    def _show_message(self, message_data):
        """Show message"""
        self.current_message = message_data
        self.current_message['start_time'] = QTimer()
        
        message_type = message_data['type']
        if message_type == "success":
            self.status_bar.show_success(message_data['message'], message_data['timeout'])
        elif message_type == "warning":
            self.status_bar.show_warning(message_data['message'], message_data['timeout'])
        elif message_type == "error":
            self.status_bar.show_error(message_data['message'], message_data['timeout'])
        else:
            self.status_bar.show_info(message_data['message'], message_data['timeout'])
    
    def _is_message_expired(self):
        """Check if message has expired"""
        if not self.current_message:
            return True
        
        # Basit timeout kontrolü (gerçek implementasyon için daha karmaşık olabilir)
        return False
    
    def clear_queue(self):
        """Clear message queue"""
        self.message_queue.clear()
        self.current_message = None