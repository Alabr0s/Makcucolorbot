import sys
import threading
import time
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QButtonGroup, QStatusBar, QMessageBox,
    QFileDialog, QInputDialog, QSplashScreen
)
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPainter, QLinearGradient, QBrush, QRadialGradient, QFontDatabase
import random
import math
import urllib.request
import os

# MVC Pattern Imports
# Models
from models import ColorPalette, ColorTheme

# Controllers  
from controllers import ServiceControlTab, WindowColorManager

# Views
from views import ColorSettingsTab, FireSettingsTab

# Utils
from utils import (
    GlobalKeyListener, WatermarkWindow,
    notification_manager, show_success, show_warning, show_error, show_info,
    ModernStatusBar, StatusBarManager
)

# Aimbot modülü (ayrı bir paket olarak kalacak)
from aimbot import AimbotTab

# Global font loading function
def load_roboto_font():
    """Load Roboto font from local file or web if not available"""
    try:
        # Create fonts directory if it doesn't exist
        fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)
        
        # Font file paths
        roboto_regular = os.path.join(fonts_dir, 'Roboto-Regular.ttf')
        roboto_bold = os.path.join(fonts_dir, 'Roboto-Bold.ttf')
        
        font_db = QFontDatabase()
        
        # Download and load Roboto Regular if not exists
        if not os.path.exists(roboto_regular):
            print("Downloading Roboto Regular font...")
            try:
                urllib.request.urlretrieve(
                    'https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.woff2',
                    roboto_regular.replace('.ttf', '.woff2')
                )
                # Alternative: Download TTF version
                urllib.request.urlretrieve(
                    'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf',
                    roboto_regular
                )
            except:
                print("Failed to download Roboto Regular, using system fonts")
        
        # Download and load Roboto Bold if not exists
        if not os.path.exists(roboto_bold):
            print("Downloading Roboto Bold font...")
            try:
                urllib.request.urlretrieve(
                    'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf',
                    roboto_bold
                )
            except:
                print("Failed to download Roboto Bold, using system fonts")
        
        # Load fonts into QFontDatabase
        if os.path.exists(roboto_regular):
            font_id = font_db.addApplicationFont(roboto_regular)
            if font_id != -1:
                print("Roboto Regular font loaded successfully")
        
        if os.path.exists(roboto_bold):
            font_id = font_db.addApplicationFont(roboto_bold)
            if font_id != -1:
                print("Roboto Bold font loaded successfully")
        
        # Set as application default font
        roboto_font = QFont("Roboto", 10)
        QApplication.instance().setFont(roboto_font)
        
        return True
        
    except Exception as e:
        print(f"Font loading error: {e}")
        return False

try:
    import qtawesome as qta
except ImportError:
    print("Hata: qtawesome kütüphanesi bulunamadı. Lütfen 'pip install qtawesome' komutu ile yükleyin.")
    sys.exit()

# Server thread for running server.py
class ServerThread(QThread):
    server_started = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.server_process = None
    
    def run(self):
        try:
            # Import and run server functions
            from server import MakcuTCPServer
            
            self.server = MakcuTCPServer()
            
            # Initialize server
            if self.server.initialize_makcu():
                self.server_started.emit(True)
                self.server.start_mouse_listener()
                self.server.start_server()
            else:
                self.server_started.emit(False)
                
        except Exception as e:
            print(f"Server başlatma hatası: {e}")
            self.server_started.emit(False)
    
    def stop_server(self):
        if hasattr(self, 'server') and self.server:
            self.server.stop_server()
        self.quit()
        self.wait()

# Animated Splash Screen
class ModernSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setFixedSize(450, 350)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._opacity = 0.0
        self.bubbles = []
        self._bounce_offset = 0
        self.bounce_direction = 1
        self.initBubbles()
        self.setupUI()
        self.setupAnimations()
        self.center()
    
    def initBubbles(self):
        for _ in range(15):
            bubble = {
                'x': random.randint(0, 450),
                'y': random.randint(0, 350),
                'size': random.randint(10, 30),
                'speed_x': random.uniform(-1, 1),
                'speed_y': random.uniform(-2, -0.5),
                'opacity': random.uniform(0.1, 0.3)
            }
            self.bubbles.append(bubble)
    
    def setupUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        self.title_label = QLabel("DEFENDING STORE")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #a0a0a0;
                font-size: 48px;
                font-weight: bold;
                font-family: 'Roboto', 'Arial Black';
                text-shadow: 0 0 20px #808080;
                background: transparent;
                border: none;
            }
        """)
        
        self.version_label = QLabel("Version 2.1.0")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: normal;
                font-family: 'Roboto', 'Arial';
                margin-top: 10px;
                background: transparent;
                border: none;
            }
        """)
        
        self.status_label = QLabel("Server başlatılıyor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 14px;
                font-family: 'Roboto', 'Arial';
                background: transparent;
                border: none;
                margin-top: 10px;
            }
        """)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.status_label)
        
        widget = QWidget()
        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rounded background gradient (same as server.py)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(26, 26, 46))
        gradient.setColorAt(1, QColor(22, 33, 62))
        
        rect = self.rect()
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 25, 25)
        
        # Draw bubbles (same as server.py)
        for bubble in self.bubbles:
            bubble_gradient = QRadialGradient(bubble['x'], bubble['y'], bubble['size']//2)
            bubble_gradient.setColorAt(0, QColor(157, 78, 221, int(bubble['opacity'] * 255)))
            bubble_gradient.setColorAt(1, QColor(157, 78, 221, 0))
            
            painter.setBrush(QBrush(bubble_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(bubble['x'] - bubble['size']//2), 
                              int(bubble['y'] - bubble['size']//2), 
                              bubble['size'], bubble['size'])
        
        super().paintEvent(event)
    
    def updateBubbles(self):
        # Update bubbles (same logic as server.py)
        for bubble in self.bubbles:
            bubble['x'] += bubble['speed_x']
            bubble['y'] += bubble['speed_y']
            
            # Reset bubble if it goes off screen
            if bubble['y'] < -bubble['size']:
                bubble['y'] = self.height() + bubble['size']
                bubble['x'] = random.randint(0, self.width())
            
            if bubble['x'] < -bubble['size'] or bubble['x'] > self.width() + bubble['size']:
                bubble['speed_x'] *= -1
        
        # Update bounce effect
        self._bounce_offset += self.bounce_direction * 2
        if self._bounce_offset > 50 or self._bounce_offset < -50:
            self.bounce_direction *= -1
        
        # Add title bounce effect
        bounce_y = int(3 * math.sin(self._bounce_offset * 0.1))
        current_style = self.title_label.styleSheet()
        if "transform:" in current_style:
            # Remove existing transform
            parts = current_style.split(";")
            new_parts = [part for part in parts if "transform:" not in part]
            current_style = ";".join(new_parts)
        
        # Add new transform
        new_style = current_style.replace(
            "}", 
            f"transform: translateY({bounce_y}px);}}"
        )
        self.title_label.setStyleSheet(new_style)
        
        self.update()
    
    def setupAnimations(self):
        # Fade animation (same as server.py)
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Bubble animation (same timing as server.py)
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.updateBubbles)
        self.bubble_timer.start(50)
    

    
    def center(self):
        # Same centering logic as server.py
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    def showSplash(self):
        self.show()
        self.fade_animation.start()
    
    def updateStatus(self, message):
        self.status_label.setText(message)
    



class ModernApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load Roboto font first
        load_roboto_font()
        self.old_pos = QPoint()
        
        # Tab widget'larını saklamak için
        self.tab_widgets = {}
        
        # Renk yönetimi
        self.color_manager = WindowColorManager()
        
        # Notification sistemi (QApplication hazır olduktan sonra)
        self.notification_manager = notification_manager
        
        # Bubble effect properties
        self.main_bubbles = []
        self.bubble_timer = None
        self.initMainBubbles()
        
        # Default theme 
        self.current_theme = ColorTheme.LIGHT

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Drag & Drop desteği
        self.setAcceptDrops(True)
        
        self.setup_ui()
        
        # Server.py tarzı tema'yı uygula
        self.apply_server_style()
        
        self.center()
        
        # Start bubble animation
        self.start_bubble_animation()
        
        # Make sure bubbles are non-interactive
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Keep window interactive
        
        # Set window flags to ensure bubbles stay in background
        self.setMouseTracking(False)

        # Global key listener
        self.key_listener_thread = GlobalKeyListener()
        self.key_listener_thread.toggle_visibility_signal.connect(self.toggle_window)
        self.key_listener_thread.start()

        # Watermark
        self.watermark = WatermarkWindow()
        self.watermark.show()
        
        # Program gizli başladığını bildiren notification
        try:
            from utils.notification_system import show_info
            show_info("Program Başlatıldı", "Program arka planda çalışıyor. Insert tuşu ile açabilirsiniz.", 3000)
        except Exception as e:
            print(f"Başlangıç notification hatası: {e}")
    
    def initMainBubbles(self):
        """Initialize bubbles for main window (same as server.py)"""
        for _ in range(20):  # More bubbles for better effect
            bubble = {
                'x': random.randint(0, 800),
                'y': random.randint(0, 150),  # Keep bubbles in top area
                'size': random.randint(8, 25),
                'speed_x': random.uniform(-0.8, 0.8),
                'speed_y': random.uniform(-1.2, -0.3),
                'opacity': random.uniform(0.05, 0.2),  # More subtle for background
                'behind_menu': True  # All bubbles behind interface
            }
            self.main_bubbles.append(bubble)
    
    def start_bubble_animation(self):
        """Start bubble animation timer"""
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.updateMainBubbles)
        self.bubble_timer.start(60)  # Slightly slower for main window
    
    def updateMainBubbles(self):
        """Update main window bubbles (same logic as server.py)"""
        for bubble in self.main_bubbles:
            bubble['x'] += bubble['speed_x']
            bubble['y'] += bubble['speed_y']
            
            # Reset bubble if it goes off screen - keep in top area
            if bubble['y'] < -bubble['size']:
                bubble['y'] = 150 + bubble['size']  # Reset to top area
                bubble['x'] = random.randint(0, self.width())
            
            # Bounce horizontally
            if bubble['x'] < -bubble['size'] or bubble['x'] > self.width() + bubble['size']:
                bubble['speed_x'] *= -1
        
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Custom paint event to draw bubbles (same as server.py)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw bubbles in top area only - non-interactive
        for bubble in self.main_bubbles:
            # Only draw bubbles in the top 150px area
            if bubble['y'] <= 150:
                bubble_gradient = QRadialGradient(bubble['x'], bubble['y'], bubble['size']//2)
                bubble_gradient.setColorAt(0, QColor(157, 78, 221, int(bubble['opacity'] * 255)))
                bubble_gradient.setColorAt(1, QColor(157, 78, 221, 0))
                
                painter.setBrush(QBrush(bubble_gradient))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(bubble['x'] - bubble['size']//2), 
                                  int(bubble['y'] - bubble['size']//2), 
                                  bubble['size'], bubble['size'])
        
        super().paintEvent(event)
    
    def apply_server_style(self):
        """Apply server.py style colors and design"""
        server_style = """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgb(20, 20, 20), stop:1 rgb(30, 30, 30));
                border-radius: 25px;
            }
            
            #mainFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgb(20, 20, 20), stop:1 rgb(30, 30, 30));
                border-radius: 25px;
                border: 2px solid rgba(100, 100, 100, 0.3);
            }
            
            #navBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(20, 20, 20, 180), stop:1 rgba(30, 30, 30, 160));
                border-radius: 25px;
                border: 1px solid rgba(100, 100, 100, 0.3);
                margin: 5px;
            }
            
            #navButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 50, 50, 120), stop:1 rgba(40, 40, 40, 120));
                border: 2px solid rgba(100, 100, 100, 0.3);
                border-radius: 50%;
                padding: 18px;
                margin: 8px 6px;
                color: #d0d0d0;
                font-size: 16px;
            }
            
            #navButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 100, 100, 160), stop:1 rgba(80, 80, 80, 140));
                border: 2px solid rgba(120, 120, 120, 0.8);
                color: white;
            }
            
            #navButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 120, 120, 220), stop:1 rgba(100, 100, 100, 200));
                border: 3px solid rgba(130, 130, 130, 0.9);
                color: white;
            }
            
            #titleLabel {
                color: #a0a0a0;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Roboto', 'Arial Black';
                padding: 10px;
            }
            
            #closeButton {
                background: rgba(220, 53, 69, 100);
                border: 1px solid rgba(220, 53, 69, 0.5);
                border-radius: 15px;
                color: white;
            }
            
            #closeButton:hover {
                background: rgba(220, 53, 69, 180);
                border: 1px solid rgba(220, 53, 69, 0.8);
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(90, 90, 90, 120), stop:1 rgba(70, 70, 70, 120));
                border: 1px solid rgba(110, 110, 110, 0.6);
                border-radius: 12px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                margin: 4px;
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
            
            QLabel {
                color: white;
                font-family: 'Roboto', 'Arial';
                background: transparent;
            }
            
            QFrame {
                background: transparent;
            }
            
            QStackedWidget {
                background: rgba(35, 35, 35, 50);
                border-radius: 15px;
                border: 1px solid rgba(100, 100, 100, 0.2);
            }
            
            QSlider::groove:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 50, 50, 180), stop:1 rgba(40, 40, 40, 180));
                height: 10px;
                border-radius: 5px;
                border: 1px solid rgba(100, 100, 100, 0.3);
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(110, 110, 110, 255), stop:1 rgba(90, 90, 90, 255));
                border: 2px solid rgba(120, 120, 120, 0.8);
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(130, 130, 130, 255), stop:1 rgba(110, 110, 110, 255));
            }
            
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(110, 110, 110, 200), stop:1 rgba(90, 90, 90, 200));
                border-radius: 5px;
            }
            
            QSpinBox, QDoubleSpinBox {
                background: rgba(50, 50, 50, 150);
                border: 1px solid rgba(100, 100, 100, 0.4);
                border-radius: 8px;
                color: white;
                padding: 4px;
                font-weight: bold;
            }
            
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid rgba(120, 120, 120, 0.8);
                box-shadow: 0 0 8px rgba(100, 100, 100, 0.3);
            }
            
            QCheckBox {
                color: white;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid rgba(100, 100, 100, 0.6);
                background: rgba(50, 50, 50, 100);
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(110, 110, 110, 255), stop:1 rgba(90, 90, 90, 255));
                border: 2px solid rgba(120, 120, 120, 0.8);
            }
            
            QGroupBox {
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid rgba(100, 100, 100, 0.4);
                border-radius: 10px;
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
                text-shadow: 0 0 8px #808080;
            }
            
            /* Tab-specific styling for consistent look */
            QScrollArea {
                background: transparent;
                border: none;
            }
            
            QScrollArea > QWidget > QWidget {
                background: rgba(35, 35, 35, 80);
                border-radius: 15px;
            }
            
            QFormLayout QLabel {
                color: #d0d0d0;
                font-weight: bold;
                font-size: 13px;
                padding: 2px;
            }
            
            /* Fix aimbot and fire tab button styles */
            QWidget[objectName="aimbot_tab"] QPushButton,
            QWidget[objectName="fire_tab"] QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(157, 78, 221, 120), stop:1 rgba(120, 60, 180, 120));
                border: 1px solid rgba(157, 78, 221, 0.6);
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                margin: 2px;
            }
            
            QWidget[objectName="aimbot_tab"] QPushButton:hover,
            QWidget[objectName="fire_tab"] QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(157, 78, 221, 180), stop:1 rgba(120, 60, 180, 180));
                border: 1px solid rgba(157, 78, 221, 0.8);
                box-shadow: 0 0 10px rgba(157, 78, 221, 0.4);
            }
            
            QWidget[objectName="aimbot_tab"] QPushButton:checked,
            QWidget[objectName="fire_tab"] QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(157, 78, 221, 220), stop:1 rgba(120, 60, 180, 220));
                border: 2px solid rgba(157, 78, 221, 0.9);
                box-shadow: 0 0 15px rgba(157, 78, 221, 0.6);
            }
            
            /* Combo box styling */
            QComboBox {
                background: rgba(40, 40, 60, 150);
                border: 1px solid rgba(157, 78, 221, 0.4);
                border-radius: 8px;
                color: white;
                padding: 6px 12px;
                font-weight: bold;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border: 2px solid rgba(157, 78, 221, 0.6);
                background: rgba(50, 50, 70, 180);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background: rgba(157, 78, 221, 0.3);
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #9d4edd;
                width: 0;
                height: 0;
            }
            
            QComboBox QAbstractItemView {
                background: rgba(30, 30, 50, 240);
                border: 1px solid rgba(157, 78, 221, 0.6);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(157, 78, 221, 150);
            }
            
            /* Scrollbar styling for long tables */
            QScrollBar:vertical {
                background: rgba(30, 30, 50, 150);
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(157, 78, 221, 180), stop:1 rgba(120, 60, 180, 180));
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(180, 120, 255, 200), stop:1 rgba(157, 78, 221, 200));
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            
            QScrollBar:horizontal {
                background: rgba(30, 30, 50, 150);
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(157, 78, 221, 180), stop:1 rgba(120, 60, 180, 180));
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(180, 120, 255, 200), stop:1 rgba(157, 78, 221, 200));
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """
        
        self.setStyleSheet(server_style)

    def setup_ui(self):
        self.setWindowTitle("Kontrol Paneli")
        self.setMinimumSize(700, 550)
        self.central_widget = QFrame(self)
        self.central_widget.setObjectName("mainFrame")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.create_navbar()
        self.create_content_area()
        self.apply_stylesheet()
    
    def create_navbar(self):
        nav_bar = QFrame()
        nav_bar.setObjectName("navBar")
        nav_bar_layout = QVBoxLayout(nav_bar)
        nav_bar_layout.setContentsMargins(10, 12, 10, 12)
        nav_bar_layout.setSpacing(15)
        nav_bar_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.nav_button_group = QButtonGroup()
        self.nav_button_group.setExclusive(True)

        self.nav_info = [
            ("fa5s.server", "Servis Kontrol"),
            ("fa5s.paint-brush", "Renk Ayarları"),
            ("fa5s.bullseye", "Ateşleme Ayarları"),
            ("fa5s.crosshairs", "Aimbot")
        ]
        
        # Navigation butonlarını saklamak için liste
        self.nav_buttons = []
        
        for i, (icon, tooltip) in enumerate(self.nav_info):
            # Başlangıçta varsayılan renk kullan, sonra tema ile güncellenecek
            button = QPushButton(qta.icon(icon, color="#e3d5f5"), "")
            button.setObjectName("navButton")
            button.setToolTip(tooltip)
            button.setCheckable(True)
            button.setFixedSize(60, 60)  # Slightly larger for the new design
            nav_bar_layout.addWidget(button)
            self.nav_button_group.addButton(button, i)
            self.nav_buttons.append(button)
        
        self.nav_button_group.button(0).setChecked(True)
        nav_bar_layout.addStretch()
        self.main_layout.addWidget(nav_bar)

    def create_content_area(self):
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0,0,0,10)
        content_layout.setSpacing(0)
        self.create_title_bar(content_layout)
        self.create_pages(content_layout)
        self.create_action_buttons(content_layout)
        self.nav_button_group.idClicked.connect(self.pages_widget.setCurrentIndex)
        self.main_layout.addWidget(content_frame)

    def create_pages(self, parent_layout):
        self.pages_widget = QStackedWidget()
        
        # Tab'ları oluştur ve sakla
        self.service_tab = ServiceControlTab(self)
        self.color_tab = ColorSettingsTab(self)
        self.fire_tab = FireSettingsTab(self)
        self.aimbot_tab = AimbotTab(self)
        
        # Set object names for styling
        self.service_tab.setObjectName("service_tab")
        self.color_tab.setObjectName("color_tab")
        self.fire_tab.setObjectName("fire_tab")
        self.aimbot_tab.setObjectName("aimbot_tab")
        
        # Otomatik kaydetme için timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_settings)
        self.auto_save_timer.setSingleShot(True)  # Tek seferlik timer
        
        # Ayar değişikliği flag'i
        self.settings_changed = False
        
        # Color settings'i aimbot'a bağla
        if hasattr(self.aimbot_tab, 'screen_scanner'):
            self.aimbot_tab.screen_scanner.set_color_settings(self.color_tab)
        
        # Color settings'i fire_tab'a bağla
        self.fire_tab.set_color_settings_reference(self.color_tab)
        
        # Widget'ları stacke ekle
        self.pages_widget.addWidget(self.service_tab)
        self.pages_widget.addWidget(self.color_tab)
        self.pages_widget.addWidget(self.fire_tab)
        self.pages_widget.addWidget(self.aimbot_tab)
        
        parent_layout.addWidget(self.pages_widget)

    def create_title_bar(self, parent_layout):
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 5, 5, 5)
        title_label = QLabel("Kontrol Paneli")
        title_label.setObjectName("titleLabel")
        self.close_button = QPushButton(qta.icon('fa5s.times', color='#cccccc'), "")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_button)
        parent_layout.addWidget(title_bar)

    def create_action_buttons(self, parent_layout):
        # Remove action buttons section - no longer needed
        pass

    def apply_stylesheet(self):
        """Apply server.py style with current theme integration"""
        # Use server style as base and integrate with color manager if needed
        self.apply_server_style()
        
        # Update icon colors to match server theme
        self.update_icon_colors_server_style()
        
        # Modern status bar'ı ayarla
        from utils.modern_status_bar import ModernStatusBar, StatusBarManager
        self.statusBar = ModernStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_manager = StatusBarManager(self.statusBar)
    
    def update_icon_colors_server_style(self):
        """Update icon colors to match server.py purple theme"""
        try:
            # Server.py style uses purple theme colors
            icon_color = "#e3d5f5"  # Light purple for icons
            button_icon_color = "#9d4edd"  # Main purple color
            
            # Navigation buttons icons
            if hasattr(self, 'nav_buttons') and hasattr(self, 'nav_info'):
                for i, button in enumerate(self.nav_buttons):
                    if i < len(self.nav_info):
                        icon_name = self.nav_info[i][0]
                        button.setIcon(qta.icon(icon_name, color=icon_color))
            
            # Close button icon
            if hasattr(self, 'close_button'):
                self.close_button.setIcon(qta.icon('fa5s.times', color='#ffffff'))
            
            # Action buttons icons
            if hasattr(self, 'reset_button'):
                self.reset_button.setIcon(qta.icon('fa5s.undo', color=button_icon_color))
            if hasattr(self, 'save_button'):
                self.save_button.setIcon(qta.icon('fa5s.save', color=button_icon_color))
                
        except Exception as e:
            print(f"Icon colors update error: {e}")
    
    def update_icon_colors(self):
        """Icon renklerini temaya göre güncelle"""
        try:
            # Mevcut temaya göre icon rengi belirle
            if self.current_theme == ColorTheme.DARK:
                icon_color = "#ffffff"  # Dark tema için beyaz iconlar
                button_icon_color = "#f0f0f0"
            elif self.current_theme == ColorTheme.BLUE:
                icon_color = "#e3f2fd"  # Blue tema için açık mavi
                button_icon_color = "#bbdefb"
            elif self.current_theme == ColorTheme.GREEN:
                icon_color = "#e8f5e8"  # Green tema için açık yeşil
                button_icon_color = "#c8e6c9"
            elif self.current_theme == ColorTheme.PURPLE:
                icon_color = "#f3e5f5"  # Purple tema için açık mor
                button_icon_color = "#e1bee7"
            else:  # LIGHT tema
                icon_color = "#666666"  # Light tema için koyu gri
                button_icon_color = "#555555"
            
            # Navigation butonlarının iconlarını güncelle
            if hasattr(self, 'nav_buttons') and hasattr(self, 'nav_info'):
                for i, button in enumerate(self.nav_buttons):
                    if i < len(self.nav_info):
                        icon_name = self.nav_info[i][0]
                        button.setIcon(qta.icon(icon_name, color=icon_color))
            
            # Close button iconunu güncelle
            if hasattr(self, 'close_button'):
                self.close_button.setIcon(qta.icon('fa5s.times', color=icon_color))
            
            # Action butonlarının iconlarını güncelle
            if hasattr(self, 'reset_button'):
                self.reset_button.setIcon(qta.icon('fa5s.undo', color=button_icon_color))
            if hasattr(self, 'save_button'):
                self.save_button.setIcon(qta.icon('fa5s.save', color=button_icon_color))
                
        except Exception as e:
            print(f"Icon renkleri güncellenirken hata: {e}")

    def change_theme(self, theme: ColorTheme):
        """Tema değiştir"""
        try:
            self.current_theme = theme
            self.color_manager.set_theme(theme)
            self.apply_stylesheet()
            
            # Tüm tab'lardaki tuş widget'larını güncelle
            self.update_key_widgets()
            
            # Tab'ların temalarını güncelle
            self.update_tab_themes()
            
            # Status bar temasını güncelle
            if hasattr(self.statusBar, 'update_theme'):
                self.statusBar.update_theme()
            
            # Tema değişikliğini config'e kaydet
            try:
                config = self.config_manager.load_config()
                config["theme"]["current_theme"] = theme.value
                success, message = self.config_manager.save_config(config)
            except Exception as e:
                pass
            
            self.statusBar.show_success(f"Tema değiştirildi: {theme.value.title()}", 2000)
            
            # Notification'ı güvenli şekilde göster
            try:
                show_info("Tema Değiştirildi", f"Yeni tema: {theme.value.title()}", 2000)
            except Exception as notification_error:
                pass
            
            # Otomatik kaydetmeyi tetikle
            self.mark_settings_changed()
            
        except Exception as e:
            pass
            self.statusBar.show_error(f"Tema değiştirme hatası: {e}", 3000)
            
            # Notification'ı güvenli şekilde göster
            try:
                show_error("Tema Hatası", str(e), 3000)
            except Exception as notification_error:
                print(f"Error notification hatası: {notification_error}")
    
    def update_tab_themes(self):
        """Tüm tab'ların temalarını güncelle"""
        try:
            # Her tab'ın update_theme metodunu çağır (varsa)
            tabs = [
                ('service_tab', 'Servis Kontrol'),
                ('color_tab', 'Renk Ayarları'),
                ('fire_tab', 'Ateşleme Ayarları'),
                ('aimbot_tab', 'Aimbot')
            ]
            
            for tab_attr, tab_name in tabs:
                if hasattr(self, tab_attr):
                    tab = getattr(self, tab_attr)
                    if hasattr(tab, 'update_theme'):
                        try:
                            tab.update_theme(self.current_theme)
                        except Exception as e:
                            print(f"{tab_name} tab tema güncelleme hatası: {e}")
                    elif hasattr(tab, 'apply_theme'):
                        try:
                            tab.apply_theme(self.current_theme)
                        except Exception as e:
                            print(f"{tab_name} tab tema uygulama hatası: {e}")
                            
        except Exception as e:
            print(f"Tab temaları güncellenirken hata: {e}")

    def update_key_widgets(self):
        """Tüm tuş widget'larını güncelle"""
        try:
            # Fire settings tab'ındaki tuşları güncelle
            if hasattr(self, 'fire_tab'):
                if hasattr(self.fire_tab, 'holdkey_button'):
                    self._update_single_key_widget(self.fire_tab.holdkey_button, "fire_tab.holdkey_button")
                if hasattr(self.fire_tab, 'toggle_button'):
                    self._update_single_key_widget(self.fire_tab.toggle_button, "fire_tab.toggle_button")
            
            # Aimbot tab'ındaki tuşları güncelle
            if hasattr(self, 'aimbot_tab'):
                if hasattr(self.aimbot_tab, 'holdkey_button'):
                    self._update_single_key_widget(self.aimbot_tab.holdkey_button, "aimbot_tab.holdkey_button")
                if hasattr(self.aimbot_tab, 'toggle_button'):
                    self._update_single_key_widget(self.aimbot_tab.toggle_button, "aimbot_tab.toggle_button")
                    
        except Exception as e:
            print(f"Tuş widget'ları güncellenirken hata: {e}")
            if hasattr(self, 'statusBar'):
                self.statusBar.show_warning(f"Tuş widget güncelleme hatası: {e}", 3000)
    
    def _update_single_key_widget(self, widget, widget_name: str):
        """Tek bir tuş widget'ını güncelle"""
        try:
            if hasattr(widget, 'update_text'):
                widget.update_text()
            elif hasattr(widget, '_apply_theme_style'):
                widget._apply_theme_style()
            else:
                print(f"Uyarı: {widget_name} widget'ı tema güncellemesi desteklemiyor")
        except Exception as e:
            print(f"Hata: {widget_name} güncellenirken: {e}")
    
    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()
    
    def dragEnterEvent(self, event):
        """Config'i içe aktar - Donma önleyici versiyon"""
        try:
            print("📥 Import config button clicked")
            
            # QFileDialog'u güvenli şekilde aç
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Ayarları İçe Aktar",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            print(f"📁 Selected import path: {file_path}")
            
            if file_path:
                print("❓ Showing confirmation dialog...")
                reply = QMessageBox.question(
                    self,
                    "Onay",
                    "Mevcut ayarlar değiştirilecek. Devam etmek istediğinizden emin misiniz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    print("🔄 Starting import process...")
                    
                    # Import işlemini güvenli şekilde yap
                    try:
                        success, message = self.config_manager.import_config(file_path)
                        
                        if success:
                            print(f"✅ Import successful: {message}")
                            
                            # Basit bildirim göster
                            QMessageBox.information(self, "Başarılı", 
                                "Config başarıyla içe aktarıldı.\n\nDeğişikliklerin etkili olması için programı yeniden başlatın.")
                            
                            try:
                                show_success("Import Başarılı", "Config içe aktarıldı. Programı yeniden başlatın.", 3000)
                            except Exception as e:
                                print(f"Import notification hatası: {e}")
                        else:
                            print(f"❌ Import failed: {message}")
                            QMessageBox.warning(self, "Hata", message)
                            try:
                                show_error("Import Hatası", message, 3000)
                            except Exception as e:
                                print(f"Import error notification hatası: {e}")
                                
                    except Exception as import_error:
                        print(f"❌ Import process error: {import_error}")
                        QMessageBox.critical(self, "Kritik Hata", f"Import işlemi başarısız: {import_error}")
                        
                else:
                    print("❌ Import cancelled by user")
            else:
                print("❌ No file path selected for import")
                
        except Exception as e:
            print(f"❌ Import config error: {e}")
            import traceback
            traceback.print_exc()
            try:
                show_error("Import Hatası", f"Beklenmeyen hata: {e}", 3000)
            except:
                pass
    
    def import_config_with_reload(self):
        """Config'i içe aktar ve ayarları yeniden yükle - TEST METODU"""
        try:
            print("📥 Import config with reload - TEST VERSION")
            
            # QFileDialog'u güvenli şekilde aç
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Ayarları İçe Aktar (Test)",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self,
                    "Test Import",
                    "Bu test versiyonudur. Ayarları yükleyip UI'ı güncelleyecek. Devam?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    print("🔄 Starting TEST import process...")
                    
                    success, message = self.config_manager.import_config(file_path)
                    
                    if success:
                        print(f"✅ Import successful: {message}")
                        print("🔄 Starting safe reload...")
                        
                        # Güvenli yeniden yükleme
                        self.simple_reload_settings()
                        
                        QMessageBox.information(self, "Test Başarılı", 
                            "Config içe aktarıldı ve ayarlar güncellendi!")
                        
                    else:
                        QMessageBox.warning(self, "Test Hatası", message)
                        
        except Exception as e:
            print(f"❌ Test import error: {e}")
            QMessageBox.critical(self, "Test Hatası", str(e))
    
    def import_config_minimal(self):
        """Minimal config import - UI donmasını önleyici"""
        try:
            print("📥 Minimal import started")
            
            # QTimer ile asenkron çalıştır
            QTimer.singleShot(100, self._show_file_dialog)
            
        except Exception as e:
            print(f"❌ Minimal import error: {e}")
            QMessageBox.critical(self, "Hata", f"Import hatası: {e}")
    
    def _show_file_dialog(self):
        """File dialog'u ayrı thread'de göster"""
        try:
            print("📁 Opening file dialog...")
            
            # File dialog'u non-blocking şekilde aç
            dialog = QFileDialog(self)
            dialog.setWindowTitle("Ayarları İçe Aktar")
            dialog.setNameFilter("JSON Files (*.json);;All Files (*)")
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
            
            # Dialog sonucunu handle et
            if dialog.exec_() == QFileDialog.Accepted:
                files = dialog.selectedFiles()
                if files:
                    file_path = files[0]
                    print(f"📁 Selected file: {file_path}")
                    
                    # Confirmation dialog
                    QTimer.singleShot(50, lambda: self._confirm_import(file_path))
            else:
                print("❌ File dialog cancelled")
                
        except Exception as e:
            print(f"❌ File dialog error: {e}")
            QMessageBox.critical(self, "Hata", f"File dialog hatası: {e}")
    
    def _confirm_import(self, file_path):
        """Import confirmation"""
        try:
            reply = QMessageBox.question(
                self,
                "Config Import",
                f"Seçilen dosya: {file_path}\n\nConfig dosyası yüklenecek. Devam etmek istediğinizden emin misiniz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Import işlemini ayrı thread'de yap
                QTimer.singleShot(50, lambda: self._do_import(file_path))
            else:
                print("❌ Import cancelled by user")
                
        except Exception as e:
            print(f"❌ Confirmation error: {e}")
    
    def _do_import(self, file_path):
        """Actual import operation"""
        try:
            print("🔄 Starting import operation...")
            
            # Config'i yükle
            success, message = self.config_manager.import_config(file_path)
            
            if success:
                print(f"✅ Config imported: {message}")
                
                # Basit mesaj göster
                QMessageBox.information(
                    self, 
                    "Import Başarılı", 
                    "Config başarıyla yüklendi!\n\n" +
                    "Değişikliklerin tam olarak uygulanması için:\n" +
                    "1. Programı kapatın\n" +
                    "2. Programı yeniden başlatın\n\n" +
                    "Veya 'Tüm Ayarları Kaydet' butonuna basıp programı yeniden başlatın."
                )
                
                try:
                    show_success("Config Yüklendi", "Programı yeniden başlatın", 3000)
                except:
                    pass
                    
            else:
                print(f"❌ Import failed: {message}")
                QMessageBox.warning(self, "Import Hatası", message)
                
        except Exception as e:
            print(f"❌ Import operation error: {e}")
            QMessageBox.critical(self, "Hata", f"Import işlemi hatası: {e}")
    
    def import_config_simple_test(self):
        """Çok basit test - sadece mesaj göster"""
        try:
            print("🧪 Simple test button clicked!")
            
            # Sadece bir mesaj göster
            QMessageBox.information(
                self,
                "Test",
                "Import butonu çalışıyor!\n\nŞimdi gerçek import için:\n1. Bu pencereyi kapatın\n2. test_config.json dosyasını manuel olarak seçin"
            )
            
            # Test için sabit dosya yolu kullan
            test_file = "test_config.json"
            
            # Dosya var mı kontrol et
            import os
            if os.path.exists(test_file):
                print(f"📁 Test file found: {test_file}")
                
                reply = QMessageBox.question(
                    self,
                    "Test Import",
                    f"test_config.json dosyası bulundu.\n\nBu dosyayı import etmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    print("🔄 Importing test config...")
                    
                    success, message = self.config_manager.import_config(test_file)
                    
                    if success:
                        QMessageBox.information(self, "Başarılı", "Test config yüklendi! Programı yeniden başlatın.")
                        print("✅ Test import successful")
                    else:
                        QMessageBox.warning(self, "Hata", f"Import hatası: {message}")
                        print(f"❌ Test import failed: {message}")
            else:
                QMessageBox.warning(self, "Dosya Bulunamadı", f"test_config.json dosyası bulunamadı.\n\nDosya yolu: {os.path.abspath(test_file)}")
                print(f"❌ Test file not found: {test_file}")
                
        except Exception as e:
            print(f"❌ Simple test error: {e}")
            QMessageBox.critical(self, "Test Hatası", str(e))
    
    def import_config_input_dialog(self):
        """Input dialog ile config import - QFileDialog kullanmadan"""
        try:
            print("📝 Input dialog import started")
            
            from PyQt5.QtWidgets import QInputDialog
            
            # Kullanıcıdan dosya yolunu al
            text, ok = QInputDialog.getText(
                self, 
                'Config Import', 
                'Config dosyasının tam yolunu girin:\n\n(Örnek: C:\\Users\\YourName\\Desktop\\config.json)\n\nVeya sadece "test" yazın test_config.json için:'
            )
            
            if ok and text:
                file_path = text.strip()
                print(f"📝 User input: {file_path}")
                
                # "test" yazıldıysa test dosyasını kullan
                if file_path.lower() == "test":
                    file_path = "test_config.json"
                    print("🧪 Using test config file")
                
                # Dosya var mı kontrol et
                import os
                if os.path.exists(file_path):
                    print(f"✅ File exists: {file_path}")
                    
                    # Confirmation
                    reply = QMessageBox.question(
                        self,
                        "Config Import Onayı",
                        f"Dosya: {file_path}\n\nBu config dosyasını yüklemek istediğinizden emin misiniz?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        print("🔄 Starting import...")
                        
                        # Import işlemi
                        success, message = self.config_manager.import_config(file_path)
                        
                        if success:
                            print(f"✅ Import successful: {message}")
                            QMessageBox.information(
                                self, 
                                "Import Başarılı", 
                                f"Config başarıyla yüklendi!\n\nDosya: {file_path}\n\nDeğişikliklerin uygulanması için programı yeniden başlatın."
                            )
                            
                            try:
                                show_success("Config Yüklendi", "Programı yeniden başlatın", 3000)
                            except:
                                pass
                        else:
                            print(f"❌ Import failed: {message}")
                            QMessageBox.warning(self, "Import Hatası", f"Import başarısız:\n\n{message}")
                    else:
                        print("❌ Import cancelled")
                else:
                    print(f"❌ File not found: {file_path}")
                    QMessageBox.warning(
                        self, 
                        "Dosya Bulunamadı", 
                        f"Belirtilen dosya bulunamadı:\n\n{file_path}\n\nLütfen dosya yolunu kontrol edin."
                    )
            else:
                print("❌ Input dialog cancelled")
                
        except Exception as e:
            print(f"❌ Input dialog import error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Import Hatası", f"Beklenmeyen hata:\n\n{e}")

    def center(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) / 2
        y = (screen_geometry.height() - self.height()) / 2
        self.move(int(x), int(y))

    def toggle_window(self):
        """Pencere görünürlüğünü değiştir"""
        if self.isVisible():
            self.hide()
            try:
                show_info("Panel Gizlendi", "Insert tuşu ile tekrar açabilirsiniz.", 2000)
            except Exception as e:
                print(f"Hide notification hatası: {e}")
        else:
            self.show()
            self.activateWindow()
            try:
                show_success("Panel Açıldı", "Kontrol paneli aktif.", 1500)
            except Exception as e:
                print(f"Show notification hatası: {e}")

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()
    
    def dragEnterEvent(self, event):
        """Dosya sürükleme girişi"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Dosya bırakma"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            if file.endswith('.json'):
                print(f"Config dosyası sürüklendi: {file}")
                break

    def toggle_always_on_top(self):
        """Always on top özelliğini aç/kapat"""
        current_flags = self.windowFlags()
        if current_flags & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(current_flags & ~Qt.WindowStaysOnTopHint)
            print("Always on top disabled")
        else:
            self.setWindowFlags(current_flags | Qt.WindowStaysOnTopHint)
            print("Always on top enabled")
        self.show()
    
    def reset_to_defaults(self):
        """Tüm ayarları varsayılana sıfırla"""
        reply = QMessageBox.question(
            self,
            "Ayarları Sıfırla",
            "Tüm ayarlar varsayılan değerlere sıfırlanacak. Emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                print("🔄 Resetting all settings to defaults...")
                # Manual reset without config system
                
                # Reset theme
                self.current_theme = ColorTheme.LIGHT
                self.color_manager.set_theme(self.current_theme)
                self.update_theme_styles()
                
                # Manual reset for each tab if they have reset methods
                if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'reset_to_defaults'):
                    self.color_tab.reset_to_defaults()
                
                if hasattr(self, 'fire_tab') and hasattr(self.fire_tab, 'reset_to_defaults'):
                    self.fire_tab.reset_to_defaults()
                
                if hasattr(self, 'aimbot_tab') and hasattr(self.aimbot_tab, 'reset_to_defaults'):
                    self.aimbot_tab.reset_to_defaults()
                
                if hasattr(self, 'anti_smoke_tab') and hasattr(self.anti_smoke_tab, 'reset_to_defaults'):
                    self.anti_smoke_tab.reset_to_defaults()
                
                QMessageBox.information(self, "Başarılı", "Ayarlar varsayılana sıfırlandı.")
                
                try:
                    show_success("Sıfırlama Başarılı", "Tüm ayarlar varsayılan değerlere sıfırlandı.", 2000)
                except:
                    pass
                    
            except Exception as e:
                print(f"❌ Reset error: {e}")
                QMessageBox.critical(self, "Hata", f"Sıfırlama hatası: {e}")
                
                try:
                    show_error("Sıfırlama Hatası", f"Ayarlar sıfırlanırken hata: {e}", 3000)
                except:
                    pass

    def load_settings_to_ui(self):
        """Tüm ayarları UI'a yükle - TAM OTOMATIK SISTEM"""
        try:
            config = self.config_manager.load_config()
            print(f"📖 Config loaded with sections: {list(config.keys())}")
            
            # TEMA AYARLARINI YÜKLE VE UYGULA
            self.load_and_apply_theme_settings(config)
            
            # TÜM TAB AYARLARINI YÜKLE
            self.load_all_tab_settings(config)
            
            print("✅ === ALL SETTINGS LOADED AND APPLIED ===")
            
        except Exception as e:
            print(f"❌ Critical error loading settings: {e}")
            import traceback
            traceback.print_exc()
    
    def load_and_apply_theme_settings(self, config):
        """Tema ayarlarını yükle ve hemen uygula"""
        try:
            theme_config = config.get("theme", {})
            theme_name = theme_config.get("current_theme", "light")
            print(f"🎨 Loading theme: {theme_name}")
            
            # Tema'yı ayarla
            for theme in ColorTheme:
                if theme.value == theme_name:
                    self.current_theme = theme
                    break
            
            # Tema tab'ını güncelle
            if hasattr(self, 'theme_tab') and hasattr(self.theme_tab, 'set_theme'):
                self.theme_tab.set_theme(self.current_theme)
            
            # Tema'yı hemen uygula
            self.color_manager.set_theme(self.current_theme)
            self.apply_stylesheet()
            
            print(f"✅ Theme applied: {self.current_theme.value}")
            
        except Exception as e:
            print(f"❌ Error loading theme: {e}")
    
    def load_all_tab_settings(self, config):
        """Tüm tab ayarlarını kapsamlı şekilde yükle"""
        print("📋 Loading all tab settings...")
        
        # 1. RENK AYARLARI
        self.load_comprehensive_color_settings(config)
        
        # 2. AIMBOT AYARLARI
        self.load_comprehensive_aimbot_settings(config)
        
        # 3. TRIGGERBOT AYARLARI  
        self.load_comprehensive_triggerbot_settings(config)
    
    def load_comprehensive_triggerbot_settings(self, config):
        """Triggerbot ayarlarını kapsamlı şekilde yükle"""
        try:
            triggerbot_config = config.get("triggerbot", {})
            print(f"🔥 Loading triggerbot config: {triggerbot_config}")
            
            if hasattr(self, 'fire_tab') and hasattr(self.fire_tab, 'load_settings'):
                # Triggerbot'un tüm ayarlarını hazırla
                settings = {
                    # Ana kontrol
                    "triggerbot_enabled": str(triggerbot_config.get("enabled", False)).lower(),
                    
                    # Ateşleme ayarları
                    "fire_delay_min": str(triggerbot_config.get("fire_delay_min", 170)),
                    "fire_delay_max": str(triggerbot_config.get("fire_delay_max", 480)),
                    
                    # Tarama ayarları
                    "area_size": str(triggerbot_config.get("area_size", 6)),
                    "scan_fps": str(triggerbot_config.get("scan_fps", 200)),
                    
                    # Tuş ayarları
                    "use_holdkey": str(triggerbot_config.get("use_holdkey", False)).lower(),
                    "hold_key": triggerbot_config.get("holdkey", "g"),
                    "toggle_key": triggerbot_config.get("toggle_key", "home")
                }
                
                print(f"🔥 Applying triggerbot settings: {settings}")
                self.fire_tab.load_settings(settings)
                print("✅ Triggerbot settings loaded successfully")
            else:
                print("⚠️ Fire tab not available or no load_settings method")
                
        except Exception as e:
            print(f"❌ Error loading triggerbot settings: {e}")
    
    def force_refresh_all_tabs(self):
        """Tüm tab'ları zorla yenile - Config import sonrası"""
        print("🔄 === FORCE REFRESHING ALL TABS ===")
        
        try:
            config = self.config_manager.load_config()
            
            # Her tab'ı ayrı ayrı yenile
            tabs_to_refresh = [
                ('color_tab', 'color_detection'),
                ('aimbot_tab', 'aimbot'),
                ('fire_tab', 'triggerbot'),
                ('anti_smoke_tab', 'anti_smoke')
            ]
            
            for tab_attr, config_section in tabs_to_refresh:
                if hasattr(self, tab_attr):
                    tab = getattr(self, tab_attr)
                    section_config = config.get(config_section, {})
                    
                    print(f"🔄 Refreshing {tab_attr} with config: {section_config}")
                    
                    # Tab'ın load_settings metodunu çağır
                    if hasattr(tab, 'load_settings') and section_config:
                        try:
                            tab.load_settings(section_config)
                            print(f"✅ {tab_attr} refreshed successfully")
                        except Exception as e:
                            print(f"❌ Error refreshing {tab_attr}: {e}")
                    
                    # Özel güncelleme metodları varsa çağır
                    if hasattr(tab, 'update_ui_from_config'):
                        try:
                            tab.update_ui_from_config(section_config)
                        except Exception as e:
                            print(f"❌ Error in update_ui_from_config for {tab_attr}: {e}")
            
            print("✅ === ALL TABS FORCE REFRESHED ===")
            
        except Exception as e:
            print(f"❌ Error in force_refresh_all_tabs: {e}")
            import traceback
            traceback.print_exc()
    
    def simple_reload_settings(self):
        """Basit ve güvenli ayar yeniden yükleme - Donma önleyici"""
        print("🔄 === SIMPLE SETTINGS RELOAD ===")
        
        try:
            config = self.config_manager.load_config()
            print(f"📖 Config loaded: {list(config.keys())}")
            
            # 1. TEMA AYARLARINI YÜKLE (change_theme çağırmadan)
            theme_config = config.get("theme", {})
            theme_name = theme_config.get("current_theme", "light")
            print(f"🎨 Theme from config: {theme_name}")
            
            # Tema'yı ayarla ama change_theme çağırma
            for theme in ColorTheme:
                if theme.value == theme_name:
                    self.current_theme = theme
                    break
            
            # Tema tab'ını güncelle
            if hasattr(self, 'theme_tab') and hasattr(self.theme_tab, 'set_theme'):
                self.theme_tab.set_theme(self.current_theme)
            
            # 2. TAB AYARLARINI YÜKLE (tek tek, güvenli şekilde)
            self.safe_load_tab_settings(config)
            
            # 3. TEMA'YI UYGULA (son adım)
            self.color_manager.set_theme(self.current_theme)
            self.apply_stylesheet()
            
            print("✅ === SIMPLE RELOAD COMPLETED ===")
            
        except Exception as e:
            print(f"❌ Error in simple_reload_settings: {e}")
            import traceback
            traceback.print_exc()
    
    def safe_load_tab_settings(self, config):
        """Tab ayarlarını güvenli şekilde yükle"""
        print("📋 Safe loading tab settings...")
        
        # Color settings
        try:
            color_config = config.get("color_detection", {})
            if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'load_settings') and color_config:
                settings = {
                    "hue_min": str(color_config.get("hue_min", 270)),
                    "hue_max": str(color_config.get("hue_max", 330)),
                    "sat_min": str(color_config.get("sat_min", 0.25)),
                    "sat_max": str(color_config.get("sat_max", 1.0)),
                    "val_min": str(color_config.get("val_min", 100)),
                    "val_max": str(color_config.get("val_max", 255))
                }
                self.color_tab.load_settings(settings)
                print("✅ Color settings loaded")
        except Exception as e:
            print(f"❌ Error loading color settings: {e}")
        
        # Aimbot settings
        try:
            aimbot_config = config.get("aimbot", {})
            if hasattr(self, 'aimbot_tab') and hasattr(self.aimbot_tab, 'load_settings') and aimbot_config:
                self.aimbot_tab.load_settings(aimbot_config)
                print("✅ Aimbot settings loaded")
        except Exception as e:
            print(f"❌ Error loading aimbot settings: {e}")
        
        # Triggerbot settings
        try:
            triggerbot_config = config.get("triggerbot", {})
            if hasattr(self, 'fire_tab') and hasattr(self.fire_tab, 'load_settings') and triggerbot_config:
                settings = {
                    "triggerbot_enabled": str(triggerbot_config.get("enabled", False)).lower(),
                    "fire_delay_min": str(triggerbot_config.get("fire_delay_min", 170)),
                    "fire_delay_max": str(triggerbot_config.get("fire_delay_max", 480)),
                    "area_size": str(triggerbot_config.get("area_size", 6)),
                    "scan_fps": str(triggerbot_config.get("scan_fps", 200)),
                    "use_holdkey": str(triggerbot_config.get("use_holdkey", False)).lower(),
                    "hold_key": triggerbot_config.get("holdkey", "g"),
                    "toggle_key": triggerbot_config.get("toggle_key", "home")
                }
                self.fire_tab.load_settings(settings)
                print("✅ Triggerbot settings loaded")
        except Exception as e:
            print(f"❌ Error loading triggerbot settings: {e}")
        
        # Anti-smoke settings
        try:
            antismoke_config = config.get("anti_smoke", {})
            if hasattr(self, 'anti_smoke_tab') and hasattr(self.anti_smoke_tab, 'load_settings') and antismoke_config:
                self.anti_smoke_tab.load_settings(antismoke_config)
                print("✅ Anti-smoke settings loaded")
        except Exception as e:
            print(f"❌ Error loading anti-smoke settings: {e}")
        
        print("✅ Safe tab loading completed")
    
    def load_comprehensive_color_settings(self, config):
        """Renk ayarlarını kapsamlı şekilde yükle"""
        try:
            color_config = config.get("color_detection", {})
            print(f"🌈 Loading color settings: {color_config}")
            
            if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'load_settings'):
                # Tüm renk ayarlarını hazırla
                settings = {
                    "hue_min": str(color_config.get("hue_min", 270)),
                    "hue_max": str(color_config.get("hue_max", 330)),
                    "sat_min": str(color_config.get("sat_min", 0.25)),
                    "sat_max": str(color_config.get("sat_max", 1.0)),
                    "val_min": str(color_config.get("val_min", 100)),
                    "val_max": str(color_config.get("val_max", 255))
                }
                
                print(f"🌈 Applying color settings: {settings}")
                self.color_tab.load_settings(settings)
                print("✅ Color settings loaded successfully")
            else:
                print("⚠️ Color tab not available or no load_settings method")
                
        except Exception as e:
            print(f"❌ Error loading color settings: {e}")
    
    def load_comprehensive_aimbot_settings(self, config):
        """Aimbot ayarlarını kapsamlı şekilde yükle"""
        try:
            aimbot_config = config.get("aimbot", {})
            print(f"🎯 Loading aimbot config: {aimbot_config}")
            
            if hasattr(self, 'aimbot_tab'):
                # Aimbot'un tüm ayarlarını hazırla
                settings = {
                    # Temel ayarlar
                    "enabled": str(aimbot_config.get("enabled", True)).lower(),
                    "holdkey": aimbot_config.get("holdkey", "f"),
                    "toggle_key": aimbot_config.get("toggle_key", "insert"),
                    "use_holdkey": str(aimbot_config.get("use_holdkey", False)).lower(),
                    
                    # Indicator ayarları
                    "indicator_enabled": str(aimbot_config.get("indicator_enabled", True)).lower(),
                    "indicator_filled": str(aimbot_config.get("indicator_filled", False)).lower(),
                    "indicator_size_x": str(aimbot_config.get("indicator_size_x", 60)),
                    "indicator_size_y": str(aimbot_config.get("indicator_size_y", 13)),
                    "indicator_thickness": str(aimbot_config.get("indicator_thickness", 1)),
                    "indicator_opacity": str(aimbot_config.get("indicator_opacity", 255)),
                    
                    # Performans ayarları
                    "aim_speed": str(aimbot_config.get("aim_speed", 50)),
                    "scan_area": str(aimbot_config.get("scan_area", 100)),
                    "sensitivity": str(aimbot_config.get("sensitivity", 1.0)),
                    "smoothing": str(aimbot_config.get("smoothing", 0.5)),
                    "fov_size": str(aimbot_config.get("fov_size", 100)),
                    "target_area_size": str(aimbot_config.get("target_area_size", 6)),
                    "scan_fps": str(aimbot_config.get("scan_fps", 200)),
                    
                    # Gelişmiş ayarlar
                    "auto_shoot": str(aimbot_config.get("auto_shoot", False)).lower(),
                    "prediction": str(aimbot_config.get("prediction", False)).lower(),
                    "prediction_strength": str(aimbot_config.get("prediction_strength", 1.0)),
                    "color_tolerance": str(aimbot_config.get("color_tolerance", 5)),
                    
                    # Görsel ayarlar
                    "debug_mode": str(aimbot_config.get("debug_mode", False)).lower(),
                    "show_fov": str(aimbot_config.get("show_fov", False)).lower(),
                    "show_crosshair": str(aimbot_config.get("show_crosshair", True)).lower(),
                    "crosshair_size": str(aimbot_config.get("crosshair_size", 20)),
                    "crosshair_color": aimbot_config.get("crosshair_color", "#00ff00"),
                    "target_priority": aimbot_config.get("target_priority", "closest"),
                    "target_type": aimbot_config.get("target_type", "body")
                }
                
                print(f"🎯 Applying aimbot settings: {settings}")
                
                # Aimbot tab'ının load_settings metodunu çağır
                if hasattr(self.aimbot_tab, 'load_settings'):
                    self.aimbot_tab.load_settings(settings)
                    print("✅ Aimbot settings loaded via load_settings")
                else:
                    # Manuel olarak ayarları uygula
                    self.apply_aimbot_settings_manually(settings)
                    print("✅ Aimbot settings applied manually")
                    
            else:
                print("⚠️ Aimbot tab not available")
                
        except Exception as e:
            print(f"❌ Error loading aimbot settings: {e}")
            import traceback
            traceback.print_exc()
    
    def load_comprehensive_triggerbot_settings(self, config):
        """Triggerbot ayarlarını kapsamlı şekilde yükle"""
        try:
            triggerbot_config = config.get("triggerbot", {})
            print(f"🔫 Loading triggerbot config: {triggerbot_config}")
            
            if hasattr(self, 'fire_tab'):
                # Triggerbot'un tüm ayarlarını hazırla
                settings = {
                    # Temel ayarlar
                    "triggerbot_enabled": str(triggerbot_config.get("enabled", False)).lower(),
                    "fire_delay_min": str(triggerbot_config.get("fire_delay_min", 170)),
                    "fire_delay_max": str(triggerbot_config.get("fire_delay_max", 480)),
                    "area_size": str(triggerbot_config.get("target_area_size", 8)),
                    "scan_fps": str(triggerbot_config.get("scan_fps", 150)),
                    
                    # Tuş ayarları
                    "fire_key": triggerbot_config.get("fire_key", "p"),
                    "toggle_key": triggerbot_config.get("toggle_key", "home"),
                    "hold_key": triggerbot_config.get("holdkey", "alt"),
                    "use_holdkey": str(triggerbot_config.get("use_holdkey", True)).lower(),
                    
                    # Gelişmiş ayarlar
                    "burst_mode": str(triggerbot_config.get("burst_mode", False)).lower(),
                    "burst_count": str(triggerbot_config.get("burst_count", 3)),
                    "burst_delay": str(triggerbot_config.get("burst_delay", 50)),
                    "recoil_control": str(triggerbot_config.get("recoil_control", False)).lower(),
                    "recoil_strength": str(triggerbot_config.get("recoil_strength", 1.0)),
                    "color_tolerance": str(triggerbot_config.get("color_tolerance", 10)),
                    "auto_reload": str(triggerbot_config.get("auto_reload", False)).lower(),
                    "reload_key": triggerbot_config.get("reload_key", "r"),
                    "safety_delay": str(triggerbot_config.get("safety_delay", 100))
                }
                
                print(f"🔫 Applying triggerbot settings: {settings}")
                
                # Fire tab'ının load_settings metodunu çağır
                if hasattr(self.fire_tab, 'load_settings'):
                    self.fire_tab.load_settings(settings)
                    print("✅ Triggerbot settings loaded via load_settings")
                else:
                    print("⚠️ Fire tab has no load_settings method")
                    
            else:
                print("⚠️ Fire tab not available")
                
        except Exception as e:
            print(f"❌ Error loading triggerbot settings: {e}")
            import traceback
            traceback.print_exc()
    
    def load_comprehensive_antismoke_settings(self, config):
        """Anti-smoke ayarlarını kapsamlı şekilde yükle"""
        try:
            antismoke_config = config.get("anti_smoke", {})
            print(f"💨 Loading anti-smoke config: {antismoke_config}")
            
            if hasattr(self, 'anti_smoke_tab'):
                settings = {
                    "enabled": str(antismoke_config.get("enabled", False)).lower(),
                    "detection_sensitivity": str(antismoke_config.get("detection_sensitivity", 0.7)),
                    "scan_area_size": str(antismoke_config.get("scan_area_size", 50)),
                    "update_frequency": str(antismoke_config.get("update_frequency", 30)),
                    "show_detection_area": str(antismoke_config.get("show_detection_area", False)).lower()
                }
                
                print(f"💨 Applying anti-smoke settings: {settings}")
                
                if hasattr(self.anti_smoke_tab, 'load_settings'):
                    self.anti_smoke_tab.load_settings(settings)
                    print("✅ Anti-smoke settings loaded")
                else:
                    print("⚠️ Anti-smoke tab has no load_settings method")
                    
            else:
                print("⚠️ Anti-smoke tab not available")
                
        except Exception as e:
            print(f"❌ Error loading anti-smoke settings: {e}")
    
    def apply_aimbot_settings_manually(self, settings):
        """Aimbot ayarlarını manuel olarak uygula"""
        try:
            # Aimbot tab'ındaki widget'lara doğrudan erişim
            if hasattr(self.aimbot_tab, 'enabled_checkbox'):
                enabled = settings.get("enabled", "true").lower() == "true"
                self.aimbot_tab.enabled_checkbox.setChecked(enabled)
            
            # Diğer ayarları da benzer şekilde uygula...
            print("✅ Aimbot settings applied manually")
            
        except Exception as e:
            print(f"❌ Error applying aimbot settings manually: {e}")
    

    

        
        # Renk ayarlarını yükle (eski format uyumluluğu için)
        color_config = {}
        color_detection = config.get("color_detection", {})
        if color_detection:
            color_config = {
                "hue_min": str(color_detection.get("hue_min", 270)),
                "hue_max": str(color_detection.get("hue_max", 330)),
                "sat_min": str(color_detection.get("sat_min", 0.25)),
                "sat_max": str(color_detection.get("sat_max", 1.0)),
                "val_min": str(color_detection.get("val_min", 100)),
                "val_max": str(color_detection.get("val_max", 255))
            }
        
        # Her tab'ın ayarlarını yükle
        self.color_tab.load_settings(color_config)
        
        # Fire tab ayarlarını yükle
        fire_config = {}
        triggerbot = config.get("triggerbot", {})
        if triggerbot:
            fire_config = {
                "fire_delay_min": str(triggerbot.get("fire_delay_min", 170)),
                "fire_delay_max": str(triggerbot.get("fire_delay_max", 480)),
                "area_size": str(triggerbot.get("target_area_size", 8)),
                "scan_fps": str(triggerbot.get("scan_fps", 150)),
                "fire_key": triggerbot.get("fire_key", "p"),
                "toggle_key": triggerbot.get("toggle_key", "home"),
                "hold_key": triggerbot.get("holdkey", "alt"),
                "use_holdkey": str(triggerbot.get("use_holdkey", True)).lower()
            }
        
        self.fire_tab.load_settings(fire_config)
        
        # Aimbot ayarlarını yükle
        if hasattr(self, 'aimbot_tab'):
            aimbot = config.get("aimbot", {})
            # Aimbot tab'ının load_settings metodunu çağır (varsa)
            if hasattr(self.aimbot_tab, 'load_settings'):
                aimbot_config = {
                    "holdkey": aimbot.get("holdkey", "f"),
                    "toggle_key": aimbot.get("toggle_key", "insert"),
                    "use_holdkey": str(aimbot.get("use_holdkey", False)).lower(),
                    "sensitivity": str(aimbot.get("sensitivity", 1.0)),
                    "fov_size": str(aimbot.get("fov_size", 100)),
                    "target_area_size": str(aimbot.get("target_area_size", 6)),
                    "scan_fps": str(aimbot.get("scan_fps", 200))
                }
                self.aimbot_tab.load_settings(aimbot_config)

    def save_settings_from_ui(self):
        """Tüm ayarları kapsamlı şekilde kaydet"""
        print("💾 === COMPREHENSIVE SETTINGS SAVE ===")
        
        try:
            # Mevcut config'i yükle
            config = self.config_manager.load_config()
            print(f"📖 Base config loaded: {list(config.keys())}")
            
            # TÜM AYARLARI TOPLA VE KAYDET
            self.collect_and_save_all_settings(config)
            
            # Config'i kaydet
            success, message = self.config_manager.save_config(config)
            
            if success:
                print(f"✅ === ALL SETTINGS SAVED SUCCESSFULLY ===")
                self.statusBar.show_success("Tüm ayarlar kaydedildi", 3000)
                try:
                    show_success("Ayarlar Kaydedildi", "Tüm ayarlar başarıyla kaydedildi", 2000)
                except Exception as e:
                    print(f"Notification error: {e}")
            else:
                print(f"❌ Config save failed: {message}")
                self.statusBar.show_error(message, 3000)
                try:
                    show_error("Kaydetme Hatası", message, 3000)
                except Exception as e:
                    print(f"Error notification: {e}")
            
        except Exception as e:
            print(f"❌ Critical save error: {e}")
            import traceback
            traceback.print_exc()
    
    def collect_and_save_all_settings(self, config):
        """Tüm tab'lardan ayarları topla ve config'e kaydet"""
        print("📋 Collecting settings from all tabs...")
        
        # 1. TEMA AYARLARI
        self.collect_theme_settings(config)
        
        # 2. RENK AYARLARI
        self.collect_color_settings(config)
        
        # 3. AIMBOT AYARLARI
        self.collect_aimbot_settings(config)
        
        # 4. TRIGGERBOT AYARLARI
        self.collect_triggerbot_settings(config)
        
        # 5. ANTI-SMOKE AYARLARI
        self.collect_antismoke_settings(config)
        
        print("✅ All settings collected")
    
    def collect_theme_settings(self, config):
        """Tema ayarlarını topla"""
        try:
            if "theme" not in config:
                config["theme"] = {}
            
            config["theme"]["current_theme"] = self.current_theme.value
            print(f"💾 Theme settings collected: {self.current_theme.value}")
            
        except Exception as e:
            print(f"❌ Error collecting theme settings: {e}")
    
    def collect_color_settings(self, config):
        """Renk ayarlarını topla"""
        try:
            if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'get_widgets'):
                widgets = self.color_tab.get_widgets()
                
                if "color_detection" not in config:
                    config["color_detection"] = {}
                
                config["color_detection"]["hue_min"] = widgets['hue_min'].value()
                config["color_detection"]["hue_max"] = widgets['hue_max'].value()
                config["color_detection"]["sat_min"] = widgets['sat_min'].value() / 100.0
                config["color_detection"]["sat_max"] = widgets['sat_max'].value() / 100.0
                config["color_detection"]["val_min"] = widgets['val_min'].value()
                config["color_detection"]["val_max"] = widgets['val_max'].value()
                
                print(f"💾 Color settings collected: {len(config['color_detection'])} items")
            
        except Exception as e:
            print(f"❌ Error collecting color settings: {e}")
    
    def collect_aimbot_settings(self, config):
        """Aimbot ayarlarını topla"""
        try:
            if hasattr(self, 'aimbot_tab') and hasattr(self.aimbot_tab, 'save_settings'):
                aimbot_settings = self.aimbot_tab.save_settings()
                
                if "aimbot" not in config:
                    config["aimbot"] = {}
                
                # Aimbot ayarlarını config'e aktar
                for key, value in aimbot_settings.items():
                    config["aimbot"][key] = value
                
                print(f"💾 Aimbot settings collected: {len(aimbot_settings)} items")
            
        except Exception as e:
            print(f"❌ Error collecting aimbot settings: {e}")
    
    def collect_triggerbot_settings(self, config):
        """Triggerbot ayarlarını topla"""
        try:
            if hasattr(self, 'fire_tab'):
                if "triggerbot" not in config:
                    config["triggerbot"] = {}
                
                # Triggerbot ayarlarını topla
                config["triggerbot"]["enabled"] = self.fire_tab.enabled_checkbox.isChecked()
                config["triggerbot"]["fire_delay_min"] = self.fire_tab.widgets["fire_delay_min"].value()
                config["triggerbot"]["fire_delay_max"] = self.fire_tab.widgets["fire_delay_max"].value()
                config["triggerbot"]["area_size"] = self.fire_tab.widgets["area_size"].value()
                config["triggerbot"]["scan_fps"] = self.fire_tab.widgets["scan_fps"].value()
                config["triggerbot"]["use_holdkey"] = self.fire_tab.holdkey_checkbox.isChecked()
                config["triggerbot"]["holdkey"] = self.fire_tab.holdkey_button.current_key
                config["triggerbot"]["toggle_key"] = self.fire_tab.toggle_button.current_key
                
                print(f"💾 Triggerbot settings collected: {len(config['triggerbot'])} items")
            
        except Exception as e:
            print(f"❌ Error collecting triggerbot settings: {e}")
    
    def collect_antismoke_settings(self, config):
        """Anti-smoke ayarlarını topla"""
        try:
            if hasattr(self, 'anti_smoke_tab') and hasattr(self.anti_smoke_tab, 'save_settings'):
                antismoke_settings = self.anti_smoke_tab.save_settings()
                
                if "anti_smoke" not in config:
                    config["anti_smoke"] = {}
                
                # Anti-smoke ayarlarını config'e aktar
                for key, value in antismoke_settings.items():
                    config["anti_smoke"][key] = value
                
                print(f"💾 Anti-smoke settings collected: {len(antismoke_settings)} items")
            
        except Exception as e:
            print(f"❌ Error collecting anti-smoke settings: {e}")
    
    def collect_theme_settings(self, config):
        """Tema ayarlarını topla"""
        try:
            config["theme"]["current_theme"] = self.current_theme.value
            print(f"🎨 Theme collected: {self.current_theme.value}")
        except Exception as e:
            print(f"❌ Error collecting theme: {e}")
    
    def collect_color_settings(self, config):
        """Renk ayarlarını topla"""
        try:
            if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'save_settings'):
                color_data = self.color_tab.save_settings()
                if color_data:
                    config["color_detection"] = {
                        "hue_min": int(float(color_data.get("hue_min", 270))),
                        "hue_max": int(float(color_data.get("hue_max", 330))),
                        "sat_min": float(color_data.get("sat_min", 0.25)),
                        "sat_max": float(color_data.get("sat_max", 1.0)),
                        "val_min": int(float(color_data.get("val_min", 100))),
                        "val_max": int(float(color_data.get("val_max", 255)))
                    }
                    print(f"🌈 Color settings collected: {config['color_detection']}")
                else:
                    print("⚠️ No color data returned from color_tab")
            else:
                print("⚠️ Color tab not available or no save_settings method")
        except Exception as e:
            print(f"❌ Error collecting color settings: {e}")
    
    def collect_aimbot_settings(self, config):
        """Aimbot ayarlarını topla"""
        try:
            if hasattr(self, 'aimbot_tab'):
                # Aimbot tab'ından ayarları al
                if hasattr(self.aimbot_tab, 'save_settings'):
                    aimbot_data = self.aimbot_tab.save_settings()
                    if aimbot_data:
                        # Tüm aimbot ayarlarını güncelle
                        config["aimbot"].update({
                            "enabled": aimbot_data.get("enabled", "true").lower() == "true",
                            "holdkey": aimbot_data.get("holdkey", "f"),
                            "toggle_key": aimbot_data.get("toggle_key", "insert"),
                            "use_holdkey": aimbot_data.get("use_holdkey", "false").lower() == "true",
                            "sensitivity": float(aimbot_data.get("sensitivity", 1.0)),
                            "smoothing": float(aimbot_data.get("smoothing", 0.5)),
                            "fov_size": int(float(aimbot_data.get("fov_size", 100))),
                            "target_area_size": int(float(aimbot_data.get("target_area_size", 6))),
                            "scan_fps": int(float(aimbot_data.get("scan_fps", 200))),
                            "auto_shoot": aimbot_data.get("auto_shoot", "false").lower() == "true",
                            "prediction": aimbot_data.get("prediction", "false").lower() == "true",
                            "prediction_strength": float(aimbot_data.get("prediction_strength", 1.0)),
                            "color_tolerance": int(float(aimbot_data.get("color_tolerance", 5))),
                            "debug_mode": aimbot_data.get("debug_mode", "false").lower() == "true",
                            "show_fov": aimbot_data.get("show_fov", "false").lower() == "true",
                            "show_crosshair": aimbot_data.get("show_crosshair", "true").lower() == "true",
                            "crosshair_size": int(float(aimbot_data.get("crosshair_size", 20))),
                            "crosshair_color": aimbot_data.get("crosshair_color", "#00ff00"),
                            "target_priority": aimbot_data.get("target_priority", "closest")
                        })
                        print(f"🎯 Aimbot settings collected: {len(config['aimbot'])} items")
                    else:
                        print("⚠️ No aimbot data returned")
                else:
                    # Manuel olarak widget'lardan ayarları topla
                    self.collect_aimbot_settings_manually(config)
            else:
                print("⚠️ Aimbot tab not available")
        except Exception as e:
            print(f"❌ Error collecting aimbot settings: {e}")
            import traceback
            traceback.print_exc()
    
    def collect_triggerbot_settings(self, config):
        """Triggerbot ayarlarını topla"""
        try:
            if hasattr(self, 'fire_tab') and hasattr(self.fire_tab, 'save_settings'):
                triggerbot_data = self.fire_tab.save_settings()
                if triggerbot_data:
                    # Tüm triggerbot ayarlarını güncelle
                    config["triggerbot"].update({
                        "enabled": triggerbot_data.get("triggerbot_enabled", "false").lower() == "true",
                        "fire_delay_min": int(float(triggerbot_data.get("fire_delay_min", 170))),
                        "fire_delay_max": int(float(triggerbot_data.get("fire_delay_max", 480))),
                        "target_area_size": int(float(triggerbot_data.get("area_size", 8))),
                        "scan_fps": int(float(triggerbot_data.get("scan_fps", 150))),
                        "fire_key": triggerbot_data.get("fire_key", "p"),
                        "toggle_key": triggerbot_data.get("toggle_key", "home"),
                        "holdkey": triggerbot_data.get("hold_key", "alt"),
                        "use_holdkey": triggerbot_data.get("use_holdkey", "true").lower() == "true",
                        "burst_mode": triggerbot_data.get("burst_mode", "false").lower() == "true",
                        "burst_count": int(float(triggerbot_data.get("burst_count", 3))),
                        "burst_delay": int(float(triggerbot_data.get("burst_delay", 50))),
                        "recoil_control": triggerbot_data.get("recoil_control", "false").lower() == "true",
                        "recoil_strength": float(triggerbot_data.get("recoil_strength", 1.0)),
                        "color_tolerance": int(float(triggerbot_data.get("color_tolerance", 10))),
                        "auto_reload": triggerbot_data.get("auto_reload", "false").lower() == "true",
                        "reload_key": triggerbot_data.get("reload_key", "r"),
                        "safety_delay": int(float(triggerbot_data.get("safety_delay", 100)))
                    })
                    print(f"🔫 Triggerbot settings collected: {len(config['triggerbot'])} items")
                else:
                    print("⚠️ No triggerbot data returned")
            else:
                print("⚠️ Fire tab not available or no save_settings method")
        except Exception as e:
            print(f"❌ Error collecting triggerbot settings: {e}")
    
    def collect_antismoke_settings(self, config):
        """Anti-smoke ayarlarını topla"""
        try:
            if hasattr(self, 'anti_smoke_tab') and hasattr(self.anti_smoke_tab, 'save_settings'):
                antismoke_data = self.anti_smoke_tab.save_settings()
                if antismoke_data:
                    config["anti_smoke"].update({
                        "enabled": antismoke_data.get("enabled", "false").lower() == "true",
                        "detection_sensitivity": float(antismoke_data.get("detection_sensitivity", 0.7)),
                        "scan_area_size": int(float(antismoke_data.get("scan_area_size", 50))),
                        "update_frequency": int(float(antismoke_data.get("update_frequency", 30))),
                        "show_detection_area": antismoke_data.get("show_detection_area", "false").lower() == "true"
                    })
                    print(f"💨 Anti-smoke settings collected: {len(config['anti_smoke'])} items")
                else:
                    print("⚠️ No anti-smoke data returned")
            else:
                print("⚠️ Anti-smoke tab not available or no save_settings method")
        except Exception as e:
            print(f"❌ Error collecting anti-smoke settings: {e}")
    
    def collect_aimbot_settings_manually(self, config):
        """Aimbot ayarlarını manuel olarak widget'lardan topla"""
        try:
            # Aimbot tab'ındaki widget'lardan doğrudan ayarları al
            if hasattr(self.aimbot_tab, 'enabled_checkbox'):
                config["aimbot"]["enabled"] = self.aimbot_tab.enabled_checkbox.isChecked()
            
            # Diğer widget'ları da kontrol et...
            print("✅ Aimbot settings collected manually")
            
        except Exception as e:
            print(f"❌ Error collecting aimbot settings manually: {e}")
    
    def save_theme_settings(self, config):
        """Tema ayarlarını kaydet"""
        try:
            config["theme"]["current_theme"] = self.current_theme.value
            print(f"🎨 Theme saved: {self.current_theme.value}")
        except Exception as e:
            print(f"❌ Error saving theme settings: {e}")
    
    def save_color_settings(self, config):
        """Renk ayarlarını kaydet"""
        try:
            if hasattr(self, 'color_tab'):
                color_settings = self.color_tab.save_settings()
                if color_settings:
                    config["color_detection"] = {
                        "hue_min": int(float(color_settings.get("hue_min", 270))),
                        "hue_max": int(float(color_settings.get("hue_max", 330))),
                        "sat_min": float(color_settings.get("sat_min", 0.25)),
                        "sat_max": float(color_settings.get("sat_max", 1.0)),
                        "val_min": int(float(color_settings.get("val_min", 100))),
                        "val_max": int(float(color_settings.get("val_max", 255)))
                    }
                    print(f"🌈 Color settings saved: {config['color_detection']}")
        except Exception as e:
            print(f"❌ Error saving color settings: {e}")
    
    def save_aimbot_settings(self, config):
        """Aimbot ayarlarını kaydet"""
        try:
            if hasattr(self, 'aimbot_tab') and hasattr(self.aimbot_tab, 'save_settings'):
                aimbot_settings = self.aimbot_tab.save_settings()
                if aimbot_settings:
                    config["aimbot"].update({
                        "enabled": aimbot_settings.get("enabled", "true").lower() == "true",
                        "holdkey": aimbot_settings.get("holdkey", "f"),
                        "toggle_key": aimbot_settings.get("toggle_key", "insert"),
                        "use_holdkey": aimbot_settings.get("use_holdkey", "false").lower() == "true",
                        "sensitivity": float(aimbot_settings.get("sensitivity", 1.0)),
                        "smoothing": float(aimbot_settings.get("smoothing", 0.5)),
                        "fov_size": int(float(aimbot_settings.get("fov_size", 100))),
                        "target_area_size": int(float(aimbot_settings.get("target_area_size", 6))),
                        "scan_fps": int(float(aimbot_settings.get("scan_fps", 200))),
                        "auto_shoot": aimbot_settings.get("auto_shoot", "false").lower() == "true",
                        "prediction": aimbot_settings.get("prediction", "false").lower() == "true",
                        "prediction_strength": float(aimbot_settings.get("prediction_strength", 1.0)),
                        "color_tolerance": int(float(aimbot_settings.get("color_tolerance", 5))),
                        "debug_mode": aimbot_settings.get("debug_mode", "false").lower() == "true",
                        "show_fov": aimbot_settings.get("show_fov", "false").lower() == "true",
                        "show_crosshair": aimbot_settings.get("show_crosshair", "true").lower() == "true",
                        "crosshair_size": int(float(aimbot_settings.get("crosshair_size", 20))),
                        "crosshair_color": aimbot_settings.get("crosshair_color", "#00ff00"),
                        "target_priority": aimbot_settings.get("target_priority", "closest")
                    })
                    print(f"🎯 Aimbot settings saved: {list(config['aimbot'].keys())}")
        except Exception as e:
            print(f"❌ Error saving aimbot settings: {e}")
    
    def save_triggerbot_settings(self, config):
        """Triggerbot ayarlarını kaydet"""
        try:
            if hasattr(self, 'fire_tab'):
                fire_settings = self.fire_tab.save_settings()
                if fire_settings:
                    config["triggerbot"].update({
                        "enabled": fire_settings.get("triggerbot_enabled", "false").lower() == "true",
                        "fire_delay_min": int(float(fire_settings.get("fire_delay_min", 170))),
                        "fire_delay_max": int(float(fire_settings.get("fire_delay_max", 480))),
                        "target_area_size": int(float(fire_settings.get("area_size", 8))),
                        "scan_fps": int(float(fire_settings.get("scan_fps", 150))),
                        "fire_key": fire_settings.get("fire_key", "p"),
                        "toggle_key": fire_settings.get("toggle_key", "home"),
                        "holdkey": fire_settings.get("hold_key", "alt"),
                        "use_holdkey": fire_settings.get("use_holdkey", "true").lower() == "true",
                        "burst_mode": fire_settings.get("burst_mode", "false").lower() == "true",
                        "burst_count": int(float(fire_settings.get("burst_count", 3))),
                        "burst_delay": int(float(fire_settings.get("burst_delay", 50))),
                        "recoil_control": fire_settings.get("recoil_control", "false").lower() == "true",
                        "recoil_strength": float(fire_settings.get("recoil_strength", 1.0)),
                        "color_tolerance": int(float(fire_settings.get("color_tolerance", 10))),
                        "auto_reload": fire_settings.get("auto_reload", "false").lower() == "true",
                        "reload_key": fire_settings.get("reload_key", "r"),
                        "safety_delay": int(float(fire_settings.get("safety_delay", 100)))
                    })
                    print(f"🔫 Triggerbot settings saved: {list(config['triggerbot'].keys())}")
        except Exception as e:
            print(f"❌ Error saving triggerbot settings: {e}")
    
    def save_antismoke_settings(self, config):
        """Anti-smoke ayarlarını kaydet"""
        try:
            if hasattr(self, 'anti_smoke_tab') and hasattr(self.anti_smoke_tab, 'save_settings'):
                antismoke_settings = self.anti_smoke_tab.save_settings()
                if antismoke_settings:
                    config["anti_smoke"].update({
                        "enabled": antismoke_settings.get("enabled", "false").lower() == "true",
                        "detection_sensitivity": float(antismoke_settings.get("detection_sensitivity", 0.7)),
                        "scan_area_size": int(float(antismoke_settings.get("scan_area_size", 50))),
                        "update_frequency": int(float(antismoke_settings.get("update_frequency", 30))),
                        "show_detection_area": antismoke_settings.get("show_detection_area", "false").lower() == "true"
                    })
                    print(f"💨 Anti-smoke settings saved: {list(config['anti_smoke'].keys())}")
        except Exception as e:
            print(f"❌ Error saving anti-smoke settings: {e}")
    
    def mark_settings_changed(self):
        """Ayarların değiştiğini işaretle ve otomatik kaydetmeyi başlat"""
        self.settings_changed = True
        # 2 saniye sonra otomatik kaydet
        self.auto_save_timer.start(2000)
        print("⏰ Settings marked as changed, auto-save scheduled in 2 seconds")
    
    def auto_save_settings(self):
        """Otomatik ayar kaydetme"""
        if self.settings_changed:
            print("💾 Auto-saving settings...")
            self.save_settings_from_ui()
            self.settings_changed = False

    def reset_to_defaults(self):
        """Ayarları varsayılana sıfırla"""
        reply = QMessageBox.question(
            self, 
            'Onay', 
            'Tüm ayarları varsayılan değerlere sıfırlamak istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!', 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Varsayılan config'i yükle ve kaydet
            default_config = self.config_manager.reset_to_defaults()
            
            # Tema'yı varsayılana çevir
            self.current_theme = ColorTheme.LIGHT
            self.color_manager.set_theme(self.current_theme)
            
            # UI'ı güncelle
            self.load_settings_to_ui()
            self.apply_stylesheet()
            self.update_key_widgets()
            
            self.statusBar.show_success("Tüm ayarlar varsayılan değerlere sıfırlandı.", 3000)
            try:
                show_info("Ayarlar Sıfırlandı", "Tüm ayarlar varsayılan değerlere döndürüldü", 2000)
            except Exception as e:
                print(f"Info notification hatası: {e}")

    def closeEvent(self, event):
        # Stop bubble animation
        if self.bubble_timer:
            self.bubble_timer.stop()
        
        # Temizlik işlemleri
        self.watermark.close()
        
        # Tab'ların temizlik işlemlerini çağır
        if hasattr(self, 'service_tab'):
            self.service_tab.cleanup()
        if hasattr(self, 'aimbot_tab'):
            self.aimbot_tab.cleanup()
        if hasattr(self, 'fire_tab'):
            self.fire_tab.cleanup()
        
        # Server thread'i durdur
        if hasattr(self, 'server_thread'):
            self.server_thread.stop_server()
        
        self.key_listener_thread.stop()
        self.key_listener_thread.wait()
        
        event.accept()
    
    def apply_config_from_data(self, config_data):
        """Config data'sından ayarları uygula - Config Info Tab'ından çağrılır - HIZLI VERSİYON"""
        try:
            print("🔄 === APPLYING CONFIG FROM DATA (FAST) ===")
            print(f"📖 Config sections: {list(config_data.keys())}")
            
            # 1. TEMA AYARLARINI UYGULA (change_theme çağırmadan)
            if "theme" in config_data:
                theme_config = config_data["theme"]
                theme_name = theme_config.get("current_theme", "light")
                print(f"🎨 Setting theme (fast): {theme_name}")
                
                # Tema'yı ayarla ama change_theme çağırma (çok yavaş)
                for theme in ColorTheme:
                    if theme.value == theme_name:
                        self.current_theme = theme
                        break
                
                # Tema tab'ını güncelle
                if hasattr(self, 'theme_tab') and hasattr(self.theme_tab, 'set_theme'):
                    self.theme_tab.set_theme(self.current_theme)
            
            # 2. TAB AYARLARINI UYGULA (hızlı versiyon)
            self.apply_tab_settings_from_data_fast(config_data)
            
            # 3. TEMA'YI UYGULA (son adım)
            if "theme" in config_data:
                self.color_manager.set_theme(self.current_theme)
                self.apply_stylesheet()
            
            print("✅ === CONFIG APPLIED FROM DATA (FAST) ===")
            
        except Exception as e:
            print(f"❌ Error applying config from data: {e}")
            import traceback
            traceback.print_exc()
    
    def apply_tab_settings_from_data(self, config_data):
        """Tab ayarlarını config data'sından uygula"""
        print("📋 Applying tab settings from data...")
        
        # Color settings
        try:
            if "color_detection" in config_data:
                color_config = config_data["color_detection"]
                if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'load_settings'):
                    settings = {
                        "hue_min": str(color_config.get("hue_min", 270)),
                        "hue_max": str(color_config.get("hue_max", 330)),
                        "sat_min": str(color_config.get("sat_min", 0.25)),
                        "sat_max": str(color_config.get("sat_max", 1.0)),
                        "val_min": str(color_config.get("val_min", 100)),
                        "val_max": str(color_config.get("val_max", 255))
                    }
                    self.color_tab.load_settings(settings)
                    print("✅ Color settings applied from data")
        except Exception as e:
            print(f"❌ Error applying color settings: {e}")
        
        # Aimbot settings
        try:
            if "aimbot" in config_data:
                aimbot_config = config_data["aimbot"]
                if hasattr(self, 'aimbot_tab') and hasattr(self.aimbot_tab, 'load_settings'):
                    # Aimbot config'i string formatına çevir (load_settings string bekliyor)
                    settings = {}
                    for key, value in aimbot_config.items():
                        if isinstance(value, bool):
                            settings[key] = str(value).lower()
                        else:
                            settings[key] = str(value)
                    
                    print(f"🎯 Applying aimbot settings from data: {settings}")
                    self.aimbot_tab.load_settings(settings)
                    print("✅ Aimbot settings applied from data")
        except Exception as e:
            print(f"❌ Error applying aimbot settings: {e}")
        
        # Triggerbot settings
        try:
            if "triggerbot" in config_data:
                triggerbot_config = config_data["triggerbot"]
                if hasattr(self, 'fire_tab') and hasattr(self.fire_tab, 'load_settings'):
                    settings = {
                        "triggerbot_enabled": str(triggerbot_config.get("enabled", False)).lower(),
                        "fire_delay_min": str(triggerbot_config.get("fire_delay_min", 170)),
                        "fire_delay_max": str(triggerbot_config.get("fire_delay_max", 480)),
                        "area_size": str(triggerbot_config.get("area_size", 6)),
                        "scan_fps": str(triggerbot_config.get("scan_fps", 200)),
                        "use_holdkey": str(triggerbot_config.get("use_holdkey", False)).lower(),
                        "hold_key": triggerbot_config.get("holdkey", "g"),
                        "toggle_key": triggerbot_config.get("toggle_key", "home")
                    }
                    self.fire_tab.load_settings(settings)
                    print("✅ Triggerbot settings applied from data")
        except Exception as e:
            print(f"❌ Error applying triggerbot settings: {e}")
        
        print("✅ All tab settings applied from data")
    
    def apply_tab_settings_from_data_fast(self, config_data):
        """Tab ayarlarını config data'sından hızlı uygula - UI donmasını önler"""
        print("📋 Applying tab settings from data (FAST)...")
        
        # Color settings (hızlı)
        try:
            if "color_detection" in config_data:
                color_config = config_data["color_detection"]
                if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'load_settings'):
                    settings = {
                        "hue_min": str(color_config.get("hue_min", 270)),
                        "hue_max": str(color_config.get("hue_max", 330)),
                        "sat_min": str(color_config.get("sat_min", 0.25)),
                        "sat_max": str(color_config.get("sat_max", 1.0)),
                        "val_min": str(color_config.get("val_min", 100)),
                        "val_max": str(color_config.get("val_max", 255))
                    }
                    self.color_tab.load_settings(settings)
                    print("✅ Color settings applied (fast)")
        except Exception as e:
            print(f"❌ Error applying color settings (fast): {e}")
        
        # Aimbot settings (hızlı)
        try:
            if "aimbot" in config_data:
                aimbot_config = config_data["aimbot"]
                if hasattr(self, 'aimbot_tab') and hasattr(self.aimbot_tab, 'load_settings'):
                    # Aimbot config'i string formatına çevir (load_settings string bekliyor)
                    settings = {}
                    for key, value in aimbot_config.items():
                        if isinstance(value, bool):
                            settings[key] = str(value).lower()
                        else:
                            settings[key] = str(value)
                    
                    print(f"🎯 Applying aimbot settings (fast): {len(settings)} items")
                    self.aimbot_tab.load_settings(settings)
                    print("✅ Aimbot settings applied (fast)")
        except Exception as e:
            print(f"❌ Error applying aimbot settings (fast): {e}")
        
        # Triggerbot settings (hızlı)
        try:
            if "triggerbot" in config_data:
                triggerbot_config = config_data["triggerbot"]
                if hasattr(self, 'fire_tab') and hasattr(self.fire_tab, 'load_settings'):
                    settings = {
                        "triggerbot_enabled": str(triggerbot_config.get("enabled", False)).lower(),
                        "fire_delay_min": str(triggerbot_config.get("fire_delay_min", 170)),
                        "fire_delay_max": str(triggerbot_config.get("fire_delay_max", 480)),
                        "area_size": str(triggerbot_config.get("area_size", 6)),
                        "scan_fps": str(triggerbot_config.get("scan_fps", 200)),
                        "use_holdkey": str(triggerbot_config.get("use_holdkey", False)).lower(),
                        "hold_key": triggerbot_config.get("holdkey", "g"),
                        "toggle_key": triggerbot_config.get("toggle_key", "home")
                    }
                    self.fire_tab.load_settings(settings)
                    print("✅ Triggerbot settings applied (fast)")
        except Exception as e:
            print(f"❌ Error applying triggerbot settings (fast): {e}")
        
        print("✅ All tab settings applied (fast)")


def main():
    import sys
    
    # Force console output
    print("=== SYNAPSE APPLICATION STARTING ===", flush=True)
    
    try:
        app = QApplication(sys.argv)
        print("QApplication created successfully", flush=True)
        
        # Show connection dialog before splash screen
        try:
            print("Importing connection dialog...", flush=True)
            from server_connection_dialog import show_connection_dialog
            from tcp_client import set_global_server_ip
            print("Imports successful", flush=True)
            
            print("Showing connection dialog...", flush=True)
            selected_ip = show_connection_dialog()
            print(f"Connection dialog completed. Selected IP: {selected_ip}", flush=True)
            
            print("Setting global server IP...", flush=True)
            set_global_server_ip(selected_ip)
            print(f"Global TCP client configured for IP: {selected_ip}", flush=True)
            
        except Exception as e:
            print(f"Error in connection dialog: {e}", flush=True)
            import traceback
            traceback.print_exc()
            print("Using default IP: 127.0.0.1", flush=True)
            selected_ip = '127.0.0.1'
        
        # Show splash screen
        print("Starting splash screen...", flush=True)
        splash = ModernSplashScreen()
        print("Splash screen created, showing...", flush=True)
        splash.showSplash()
        print("Splash screen shown, continuing with main flow...", flush=True)
        
    except Exception as e:
        print(f"Critical error in main: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Start server thread
    server_thread = ServerThread()
    server_ready = False
    
    def on_server_started(success):
        nonlocal server_ready
        server_ready = True
        if success:
            splash.updateStatus("Makcu Test ediliyor.")
        else:
            splash.updateStatus("Makcu Bağlantı hatası")
    
    server_thread.server_started.connect(on_server_started)
    server_thread.start()
    
    # Update splash screen status
    splash.updateStatus("Color Bot Başlatılıyor...")
    
    # Wait for server and splash screen timing
    start_time = time.time()
    min_splash_time = 7.0  # Minimum 7 seconds for splash
    
    while time.time() - start_time < min_splash_time:
        app.processEvents()
        time.sleep(0.05)
        
        # Update status gradually
        elapsed = time.time() - start_time
        
        if elapsed > 1.5:
            splash.updateStatus("Sistem modülleri yükleniyor...")
        if elapsed > 3.0 and server_ready:
            splash.updateStatus("Dosya bütünlüğü test ediliyor...")
        if elapsed > 4.5:
            splash.updateStatus("Arayüz bileşenleri hazırlanıyor...")
        if elapsed > 6.0:
            splash.updateStatus("Son kontroller yapılıyor...")
    
    # Update final status
    splash.updateStatus("Tamamlandı!")
    
    # Longer delay before showing main app to appreciate completion
    time.sleep(1.2)
    
    # Close splash screen
    splash.close()
    
    # Notification sistemi debug
    try:
        from notification_system import debug_notification_system
        debug_notification_system()
    except Exception as e:
        print(f"Notification debug error: {e}")
    
    # Create and show main application
    editor = ModernApp()
    
    # Add server thread reference to main app for cleanup
    editor.server_thread = server_thread
    
    # Program başlangıçta gizli olarak başlar, Insert tuşu ile açılır
    # Arka planda çalışır ve Insert tuşu ile kontrol paneli açılır/kapanır
    editor.hide()
    
    # Show initial notification
    try:
        from utils.notification_system import show_success
        show_success("SYNAPSE Hazır", "Server başlatıldı. Insert tuşu ile kontrol panelini açın.", 3000)
    except Exception as e:
        print(f"Initial notification error: {e}")
    
    # Handle app cleanup
    def cleanup():
        if hasattr(editor, 'server_thread'):
            editor.server_thread.stop_server()
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()