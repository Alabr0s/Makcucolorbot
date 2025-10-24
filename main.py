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

# License validation import
from license_validator import validate_license

# MVC Pattern Imports
# Models
from models import ColorPalette, ColorTheme

# Controllers  
from controllers import WindowColorManager

# Views
from views import ColorSettingsTab, FireSettingsTab, RCSSettingsTab

# Utils
from utils import (
    GlobalKeyListener,
    notification_manager, show_success, show_warning, show_error, show_info,
    ModernStatusBar, StatusBarManager
)

# Aimbot module (will remain as a separate package)
from aimbot import AimbotTab, SpikeTimerTab

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
    print("Error: qtawesome library not found. Please install it with 'pip install qtawesome' command.")
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
            print(f"Server start error: {e}")
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
                font-size: 36px;
                font-weight: bold;
                font-family: 'Roboto', 'Arial Black';
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
        
        self.status_label = QLabel("Starting server...")
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
        
        # Draw rounded background gradient (same as server.py but gray)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(20, 20, 20))
        gradient.setColorAt(1, QColor(30, 30, 30))
        
        rect = self.rect()
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 25, 25)
        
        # Draw bubbles (same as server.py but gray)
        for bubble in self.bubbles:
            bubble_gradient = QRadialGradient(bubble['x'], bubble['y'], bubble['size']//2)
            bubble_gradient.setColorAt(0, QColor(100, 100, 100, int(bubble['opacity'] * 255)))
            bubble_gradient.setColorAt(1, QColor(100, 100, 100, 0))
            
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
        # Config manager removed - no longer using config
        self.old_pos = QPoint()
        
        # To store tab widgets
        self.tab_widgets = {}
        
        # Color management
        self.color_manager = WindowColorManager()
        
        # Notification system (after QApplication is ready)
        self.notification_manager = notification_manager
        
        # Bubble effect properties
        self.main_bubbles = []
        self.bubble_timer = None
        self.initMainBubbles()
        
        # Default theme (without config)
        self.current_theme = ColorTheme.LIGHT

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Drag & Drop support
        self.setAcceptDrops(True)
        
        self.setup_ui()
        
        # Load settings after UI is set up (works without config)
        # load_settings_to_ui function removed
        
        # Apply server.py style theme
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

        # Notification informing that the program started hidden
        try:
            from utils.notification_system import show_info
            show_info("Program Started", "Program is running in the background. You can open it with the Insert key.", 3000)
        except Exception as e:
            print(f"Startup notification error: {e}")

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
                bubble_gradient.setColorAt(0, QColor(100, 100, 100, int(bubble['opacity'] * 255)))
                bubble_gradient.setColorAt(1, QColor(100, 100, 100, 0))
                
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
                background: rgba(30, 30, 30, 200);
                height: 8px;
                border-radius: 4px;
                border: none;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(160, 160, 160, 255), 
                    stop:0.5 rgba(180, 180, 180, 255),
                    stop:1 rgba(160, 160, 160, 255));
                border: none;
                width: 26px;
                height: 26px;
                margin: -9px 0;
                border-radius: 13px;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(180, 180, 180, 255), 
                    stop:0.5 rgba(200, 200, 200, 255),
                    stop:1 rgba(180, 180, 180, 255));
            }
            
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(140, 140, 140, 255), 
                    stop:0.5 rgba(160, 160, 160, 255),
                    stop:1 rgba(140, 140, 140, 255));
            }
            
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 100, 100, 255), 
                    stop:0.5 rgba(140, 140, 140, 255),
                    stop:1 rgba(120, 120, 120, 255));
                border-radius: 4px;
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
            }
            
            QCheckBox {
                color: white;
                font-weight: bold;
                spacing: 12px;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border-radius: 12px;
                border: 3px solid rgba(70, 70, 70, 0.9);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 50, 50, 200), stop:1 rgba(30, 30, 30, 200));
            }
            
            QCheckBox::indicator:hover {
                border: 3px solid rgba(100, 100, 100, 1.0);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 60, 60, 220), stop:1 rgba(40, 40, 40, 220));
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(160, 160, 160, 255), stop:1 rgba(120, 120, 120, 255));
                border: 3px solid rgba(180, 180, 180, 1.0);
            }
            
            QCheckBox::indicator:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(180, 180, 180, 255), stop:1 rgba(140, 140, 140, 255));
                border: 3px solid rgba(200, 200, 200, 1.0);
            }
            
            QCheckBox::indicator:checked:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(140, 140, 140, 255), stop:1 rgba(100, 100, 100, 255));
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
                    stop:0 rgba(90, 90, 90, 120), stop:1 rgba(70, 70, 70, 120));
                border: 1px solid rgba(110, 110, 110, 0.6);
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                margin: 2px;
            }
            
            QWidget[objectName="aimbot_tab"] QPushButton:hover,
            QWidget[objectName="fire_tab"] QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(110, 110, 110, 180), stop:1 rgba(90, 90, 90, 180));
                border: 1px solid rgba(120, 120, 120, 0.8);
            }
            
            QWidget[objectName="aimbot_tab"] QPushButton:checked,
            QWidget[objectName="fire_tab"] QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 120, 120, 220), stop:1 rgba(100, 100, 100, 220));
                border: 2px solid rgba(130, 130, 130, 0.9);
            }
            
            /* Combo box styling */
            QComboBox {
                background: rgba(50, 50, 50, 150);
                border: 1px solid rgba(100, 100, 100, 0.4);
                border-radius: 8px;
                color: white;
                padding: 6px 12px;
                font-weight: bold;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border: 2px solid rgba(110, 110, 110, 0.6);
                background: rgba(60, 60, 60, 180);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background: rgba(100, 100, 100, 0.3);
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #a0a0a0;
                width: 0;
                height: 0;
            }
            
            QComboBox QAbstractItemView {
                background: rgba(35, 35, 35, 240);
                border: 1px solid rgba(100, 100, 100, 0.6);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(100, 100, 100, 150);
            }
            
            /* Scrollbar styling for long tables */
            QScrollBar:vertical {
                background: rgba(35, 35, 35, 150);
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(120, 120, 120, 200), stop:1 rgba(100, 100, 100, 200));
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            
            QScrollBar:horizontal {
                background: rgba(35, 35, 35, 150);
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 120, 120, 200), stop:1 rgba(100, 100, 100, 200));
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
        self.setWindowTitle("Defending Store")
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
            ("fa5s.paint-brush", "Color Settings"),
            ("fa5s.bullseye", "Firing Settings"),
            ("fa5s.crosshairs", "Aimbot"),
            ("fa5s.arrows-alt-v", "RCS Sistemi"),
            ("fa5s.clock", "Spike Timer")
        ]
        
        # List to store navigation buttons
        self.nav_buttons = []
        
        for i, (icon, tooltip) in enumerate(self.nav_info):
            # Use default color at start, then update with theme
            button = QPushButton(qta.icon(icon, color="#d0d0d0"), "")
            button.setObjectName("navButton")
            button.setToolTip(tooltip)
            button.setCheckable(True)
            button.setFixedSize(60, 60)  # Slightly larger for the new design
            nav_bar_layout.addWidget(button)
            self.nav_button_group.addButton(button, i)
            self.nav_buttons.append(button)
        
        self.nav_button_group.button(0).setChecked(True)  # Now points to Color Settings
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
        
        # Create and store tabs
        self.color_tab = ColorSettingsTab(self)
        self.fire_tab = FireSettingsTab(self)
        self.aimbot_tab = AimbotTab(self)
        self.rcs_tab = RCSSettingsTab(self)
        self.spike_timer_tab = SpikeTimerTab(self)
        
        # Set object names for styling
        self.color_tab.setObjectName("color_tab")
        self.fire_tab.setObjectName("fire_tab")
        self.aimbot_tab.setObjectName("aimbot_tab")
        self.rcs_tab.setObjectName("rcs_tab")
        self.spike_timer_tab.setObjectName("spike_timer_tab")
        
        # Timer for auto-save
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_settings)
        self.auto_save_timer.setSingleShot(True)  # Tek seferlik timer
        
        # Setting change flag
        self.settings_changed = False
        
        # Connect color settings to aimbot
        if hasattr(self.aimbot_tab, 'screen_scanner'):
            self.aimbot_tab.screen_scanner.set_color_settings(self.color_tab)
        
        # Connect color settings to fire_tab
        self.fire_tab.set_color_settings_reference(self.color_tab)
        
        # RCS ve Aimbot entegrasyonu
        if hasattr(self.rcs_tab, 'get_rcs_worker') and hasattr(self.aimbot_tab, 'mouse_controller'):
            rcs_worker = self.rcs_tab.get_rcs_worker()
            self.aimbot_tab.mouse_controller.set_rcs_worker(rcs_worker)
        
        # Add widgets to stack
        self.pages_widget.addWidget(self.color_tab)
        self.pages_widget.addWidget(self.fire_tab)
        self.pages_widget.addWidget(self.aimbot_tab)
        self.pages_widget.addWidget(self.rcs_tab)
        self.pages_widget.addWidget(self.spike_timer_tab)
        
        parent_layout.addWidget(self.pages_widget)

    def create_title_bar(self, parent_layout):
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 5, 5, 5)
        title_label = QLabel("Defending Store")
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
        
        # Set up modern status bar
        from utils.modern_status_bar import ModernStatusBar, StatusBarManager
        self.statusBar = ModernStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_manager = StatusBarManager(self.statusBar)
    
    def update_icon_colors_server_style(self):
        """Update icon colors to match gray theme"""
        try:
            # Gray theme colors
            icon_color = "#d0d0d0"  # Light gray for icons
            button_icon_color = "#a0a0a0"  # Main gray color
            
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
        """Update icon colors based on theme"""
        try:
            # Determine icon color based on current theme
            if self.current_theme == ColorTheme.DARK:
                icon_color = "#ffffff"  # White icons for dark theme
                button_icon_color = "#f0f0f0"
            elif self.current_theme == ColorTheme.BLUE:
                icon_color = "#e3f2fd"  # Light blue for blue theme
                button_icon_color = "#bbdefb"
            elif self.current_theme == ColorTheme.GREEN:
                icon_color = "#e8f5e8"  # Light green for green theme
                button_icon_color = "#c8e6c9"
            elif self.current_theme == ColorTheme.PURPLE:
                icon_color = "#f3e5f5"  # Light purple for purple theme
                button_icon_color = "#e1bee7"
            else:  # LIGHT tema
                icon_color = "#666666"  # Dark gray for light theme
                button_icon_color = "#555555"
            
            # Update navigation button icons
            if hasattr(self, 'nav_buttons') and hasattr(self, 'nav_info'):
                for i, button in enumerate(self.nav_buttons):
                    if i < len(self.nav_info):
                        icon_name = self.nav_info[i][0]
                        button.setIcon(qta.icon(icon_name, color=icon_color))
            
            # Update close button icon
            if hasattr(self, 'close_button'):
                self.close_button.setIcon(qta.icon('fa5s.times', color=icon_color))
            
            # Update action button icons
            if hasattr(self, 'reset_button'):
                self.reset_button.setIcon(qta.icon('fa5s.undo', color=button_icon_color))
            if hasattr(self, 'save_button'):
                self.save_button.setIcon(qta.icon('fa5s.save', color=button_icon_color))
                
        except Exception as e:
            print(f"Error updating icon colors: {e}")

    def change_theme(self, theme: ColorTheme):
        """Change theme"""
        try:
            self.current_theme = theme
            self.color_manager.set_theme(theme)
            self.apply_stylesheet()
            
            # Update key widgets in all tabs
            self.update_key_widgets()
            
            # Update tab themes
            self.update_tab_themes()
            
            # Update status bar theme
            if hasattr(self.statusBar, 'update_theme'):
                self.statusBar.update_theme()
            
            # Save theme change to config
            try:
                config = self.config_manager.load_config()
                config["theme"]["current_theme"] = theme.value
                success, message = self.config_manager.save_config(config)
            except Exception as e:
                pass
            
            self.statusBar.show_success(f"Theme changed: {theme.value.title()}", 2000)
            
            # Show notification safely
            try:
                show_info("Theme Changed", f"New theme: {theme.value.title()}", 2000)
            except Exception as notification_error:
                pass
            
            # Trigger auto-save
            self.mark_settings_changed()
            
        except Exception as e:
            pass
            self.statusBar.show_error(f"Theme change error: {e}", 3000)
            
            # Show notification safely
            try:
                show_error("Theme Error", str(e), 3000)
            except Exception as notification_error:
                print(f"Error notification error: {notification_error}")
    
    def update_tab_themes(self):
        """Update themes of all tabs"""
        try:
            # Call update_theme method of each tab (if exists)
            tabs = [
                ('color_tab', 'Color Settings'),
                ('fire_tab', 'Firing Settings'),
                ('aimbot_tab', 'Aimbot'),
                ('rcs_tab', 'RCS Sistemi')
            ]
            
            for tab_attr, tab_name in tabs:
                if hasattr(self, tab_attr):
                    tab = getattr(self, tab_attr)
                    if hasattr(tab, 'update_theme'):
                        try:
                            tab.update_theme(self.current_theme)
                        except Exception as e:
                            print(f"{tab_name} tab theme update error: {e}")
                    elif hasattr(tab, 'apply_theme'):
                        try:
                            tab.apply_theme(self.current_theme)
                        except Exception as e:
                            print(f"{tab_name} tab theme apply error: {e}")
                            
        except Exception as e:
            print(f"Error updating tab themes: {e}")

    def update_key_widgets(self):
        """Update all key widgets"""
        try:
            # Update keys in fire settings tab
            if hasattr(self, 'fire_tab'):
                if hasattr(self.fire_tab, 'holdkey_button'):
                    self._update_single_key_widget(self.fire_tab.holdkey_button, "fire_tab.holdkey_button")
                if hasattr(self.fire_tab, 'toggle_button'):
                    self._update_single_key_widget(self.fire_tab.toggle_button, "fire_tab.toggle_button")
            
            # Update keys in aimbot tab
            if hasattr(self, 'aimbot_tab'):
                if hasattr(self.aimbot_tab, 'holdkey_button'):
                    self._update_single_key_widget(self.aimbot_tab.holdkey_button, "aimbot_tab.holdkey_button")
                if hasattr(self.aimbot_tab, 'toggle_button'):
                    self._update_single_key_widget(self.aimbot_tab.toggle_button, "aimbot_tab.toggle_button")
                    
        except Exception as e:
            print(f"Error updating key widgets: {e}")
            if hasattr(self, 'statusBar'):
                self.statusBar.show_warning(f"Key widget update error: {e}", 3000)
    
    def _update_single_key_widget(self, widget, widget_name: str):
        """Update a single key widget"""
        try:
            if hasattr(widget, 'update_text'):
                widget.update_text()
            elif hasattr(widget, '_apply_theme_style'):
                widget._apply_theme_style()
            else:
                print(f"Warning: {widget_name} widget does not support theme updates")
        except Exception as e:
            print(f"Error while updating {widget_name}: {e}")
    

    
    def export_config(self):
        """Export config"""
        try:
            print("📤 Export config button clicked")
            
            # Open QFileDialog safely
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Settings",
                "defending_store_settings.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            print(f"📁 Selected export path: {file_path}")
            
            if file_path:
                print("🔄 Starting export process...")
                success, message = self.config_manager.export_config(file_path)
                
                if success:
                    print(f"✅ Export successful: {message}")
                    QMessageBox.information(self, "Success", message)
                    try:
                        show_success("Export Successful", f"Settings successfully exported", 2000)
                    except Exception as e:
                        print(f"Export notification error: {e}")
                else:
                    print(f"❌ Export failed: {message}")
                    QMessageBox.warning(self, "Error", message)
                    try:
                        show_error("Export Error", message, 3000)
                    except Exception as e:
                        print(f"Export error notification error: {e}")
            else:
                print("❌ No file path selected for export")
                
        except Exception as e:
            print(f"❌ Export config error: {e}")
            import traceback
            traceback.print_exc()
            try:
                show_error("Export Error", f"Unexpected error: {e}", 3000)
            except:
                pass
    
    def import_config(self):
        """Import config - Freeze prevention version"""
        try:
            print("📥 Import config button clicked")
            
            # Open QFileDialog safely
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Settings",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            print(f"📁 Selected import path: {file_path}")
            
            if file_path:
                print("❓ Showing confirmation dialog...")
                # Confirmation
                reply = QMessageBox.question(
                    self,
                    "Drag & Drop Import",
                    f"Dragged file:\n{file_path}\n\nDo you want to load this config file?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    print("🔄 Starting import process...")
                    
                    # Perform import operation safely
                    try:
                        success, message = self.config_manager.import_config(file_path)
                        
                        if success:
                            print(f"✅ Import successful: {message}")
                            
                            # Show simple notification
                            QMessageBox.information(self, "Success", 
                                "Config successfully imported.\n\nRestart the program for changes to take effect.")
                            
                            try:
                                show_success("Import Successful", "Config imported. Please restart the program.", 3000)
                            except Exception as e:
                                print(f"Import notification error: {e}")
                        else:
                            print(f"❌ Import failed: {message}")
                            QMessageBox.warning(self, "Error", message)
                            try:
                                show_error("Import Error", message, 3000)
                            except Exception as e:
                                print(f"Import error notification error: {e}")
                                
                    except Exception as import_error:
                        print(f"❌ Import process error: {import_error}")
                        QMessageBox.critical(self, "Critical Error", f"Import process failed: {import_error}")
                        
                else:
                    print("❌ Import cancelled by user")
            else:
                print("❌ No file path selected for import")
                
        except Exception as e:
            print(f"❌ Import config error: {e}")
            import traceback
            traceback.print_exc()
            try:
                show_error("Import Error", f"Unexpected error: {e}", 3000)
            except:
                pass
    
    def import_config_with_reload(self):
        """Import config and reload settings - TEST METHOD"""
        try:
            print("📥 Import config with reload - TEST VERSION")
            
            # Open QFileDialog safely
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Settings (Test)",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self,
                    "Test Import",
                    "This is a test version. It will load settings and update the UI. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    print("🔄 Starting TEST import process...")
                    
                    success, message = self.config_manager.import_config(file_path)
                    
                    if success:
                        print(f"✅ Import successful: {message}")
                        print("🔄 Starting safe reload...")
                        
                        # Safe reload
                        self.simple_reload_settings()
                        
                        QMessageBox.information(self, "Test Successful", 
                            "Config imported and settings updated!")
                        
                    else:
                        QMessageBox.warning(self, "Test Error", message)
                        
        except Exception as e:
            print(f"❌ Test import error: {e}")
            QMessageBox.critical(self, "Test Hatası", str(e))
    
    def import_config_minimal(self):
        """Minimal config import - UI freeze prevention"""
        try:
            print("📥 Minimal import started")
            
            # Run asynchronously with QTimer
            QTimer.singleShot(100, self._show_file_dialog)
            
        except Exception as e:
            print(f"❌ Minimal import error: {e}")
            QMessageBox.critical(self, "Error", f"Import error: {e}")
    
    def _show_file_dialog(self):
        """Show file dialog in separate thread"""
        try:
            print("📁 Opening file dialog...")
            
            # Open file dialog in non-blocking way
            dialog = QFileDialog(self)
            dialog.setWindowTitle("Import Settings")
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
            QMessageBox.critical(self, "Error", f"File dialog error: {e}")
    
    def _confirm_import(self, file_path):
        """Import confirmation"""
        try:
            reply = QMessageBox.question(
                self,
                "Config Import",
                f"Selected file: {file_path}\n\nConfig file will be loaded. Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Perform import operation in separate thread
                QTimer.singleShot(50, lambda: self._do_import(file_path))
            else:
                print("❌ Import cancelled by user")
                
        except Exception as e:
            print(f"❌ Confirmation error: {e}")
    
    def _do_import(self, file_path):
        """Actual import operation"""
        try:
            print("🔄 Starting import operation...")
            
            # Load config
            success, message = self.config_manager.import_config(file_path)
            
            if success:
                print(f"✅ Config imported: {message}")
                
                # Show simple message
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    "Config successfully loaded!\n\n" +
                    "To apply changes completely:\n" +
                    "1. Close the program\n" +
                    "2. Restart the program\n\n" +
                    "Or press the 'Save All Settings' button and restart the program."
                )
                
                try:
                    show_success("Config Loaded", "Restart the program", 3000)
                except:
                    pass
                    
            else:
                print(f"❌ Import failed: {message}")
                QMessageBox.warning(self, "Import Error", message)
                
        except Exception as e:
            print(f"❌ Import operation error: {e}")
            QMessageBox.critical(self, "Error", f"Import process error: {e}")
    
    def import_config_simple_test(self):
        """Very simple test - just show message"""
        try:
            print("🧪 Simple test button clicked!")
            
            # Show only a message
            QMessageBox.information(
                self,
                "Test",
                "Import button is working!\n\nFor real import:\n1. Close this window\n2. Manually select the test_config.json file"
            )
            
            # Use fixed file path for testing
            test_file = "test_config.json"
            
            # Check if file exists
            import os
            if os.path.exists(test_file):
                print(f"📁 Test file found: {test_file}")
                
                reply = QMessageBox.question(
                    self,
                    "Test Import",
                    f"test_config.json file found.\n\nDo you want to import this file?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    print("🔄 Importing test config...")
                    
                    success, message = self.config_manager.import_config(test_file)
                    
                    if success:
                        QMessageBox.information(self, "Success", "Test config loaded! Please restart the program.")
                        print("✅ Test import successful")
                    else:
                        QMessageBox.warning(self, "Error", f"Import error: {message}")
                        print(f"❌ Test import failed: {message}")
            else:
                QMessageBox.warning(self, "File Not Found", f"test_config.json file not found.\n\nFile path: {os.path.abspath(test_file)}")
                print(f"❌ Test file not found: {test_file}")
                
        except Exception as e:
            print(f"❌ Simple test error: {e}")
            QMessageBox.critical(self, "Test Hatası", str(e))
    
    def import_config_input_dialog(self):
        """Input dialog ile config import - QFileDialog kullanmadan"""
        try:
            print("📝 Input dialog import started")
            
            from PyQt5.QtWidgets import QInputDialog
            
            # Get file path from user
            text, ok = QInputDialog.getText(
                self, 
                'Config Import', 
                'Enter the full path of the config file:\n\n(Example: C:\\Users\\YourName\\Desktop\\config.json)\n\nOr just type "test" for test_config.json:'
            )
            
            if ok and text:
                file_path = text.strip()
                print(f"📝 User input: {file_path}")
                
                # Use test file if "test" was entered
                if file_path.lower() == "test":
                    file_path = "test_config.json"
                    print("🧪 Using test config file")
                
                # Check if file exists
                import os
                if os.path.exists(file_path):
                    print(f"✅ File exists: {file_path}")
                    
                    # Confirmation
                    reply = QMessageBox.question(
                        self,
                        "Config Import Confirmation",
                        f"File: {file_path}\n\nAre you sure you want to load this config file?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        print("🔄 Starting import...")
                        
                        # Import operation
                        success, message = self.config_manager.import_config(file_path)
                        
                        if success:
                            print(f"✅ Import successful: {message}")
                            QMessageBox.information(
                                self, 
                                "Import Successful", 
                                f"Config successfully loaded!\n\nFile: {file_path}\n\nRestart the program to apply changes."
                            )
                            
                            try:
                                show_success("Config Loaded", "Restart the program", 3000)
                            except:
                                pass
                        else:
                            print(f"❌ Import failed: {message}")
                            QMessageBox.warning(self, "Import Error", f"Import failed:\n\n{message}")
                    else:
                        print("❌ Import cancelled")
                else:
                    print(f"❌ File not found: {file_path}")
                    QMessageBox.warning(
                        self, 
                        "File Not Found", 
                        f"The specified file was not found:\n\n{file_path}\n\nPlease check the file path."
                    )
            else:
                print("❌ Input dialog cancelled")
                
        except Exception as e:
            print(f"❌ Input dialog import error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Import Error", f"Unexpected error:\n\n{e}")

    def center(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) / 2
        y = (screen_geometry.height() - self.height()) / 2
        self.move(int(x), int(y))

    def toggle_window(self):
        """Change window visibility"""
        if self.isVisible():
            self.hide()
            try:
                show_info("Panel Hidden", "You can reopen it with the Insert key.", 2000)
            except Exception as e:
                print(f"Hide notification error: {e}")
        else:
            self.show()
            self.activateWindow()
            try:
                show_success("Panel Opened", "Control panel is active.", 1500)
            except Exception as e:
                print(f"Show notification error: {e}")

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()
    
    def dragEnterEvent(self, event):
        """Drag & Drop - When file is dragged"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().endswith('.json'):
                event.accept()
                print("📁 JSON file dragged in")
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Drag & Drop - When file is dropped"""
        try:
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                print(f"📁 File dropped: {file_path}")
                
                if file_path.endswith('.json'):
                    # Confirmation
                    reply = QMessageBox.question(
                        self,
                        "Drag & Drop Import",
                        f"Dragged file:\n{file_path}\n\nDo you want to load this config file?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        print("🔄 Starting drag & drop import...")
                        
                        success, message = self.config_manager.import_config(file_path)
                        
                        if success:
                            print(f"✅ Drag & drop import successful")
                            QMessageBox.information(
                                self,
                                "Import Successful",
                                f"Config successfully loaded!\n\nRestart the program."
                            )
                            
                            try:
                                show_success("Config Loaded", "Loaded via Drag & Drop", 3000)
                            except:
                                pass
                        else:
                            QMessageBox.warning(self, "Import Error", message)
                else:
                    QMessageBox.warning(self, "Invalid File", "Only .json files are supported.")
                    
        except Exception as e:
            print(f"❌ Drag & drop error: {e}")
            QMessageBox.critical(self, "Drag & Drop Error", str(e))

    def load_settings_to_ui(self):
        """Config system disabled - No settings are loaded"""
        print("⚠️ Config system disabled - using default settings")
        pass
    
    def load_and_apply_theme_settings(self, config):
        """Load theme settings and apply immediately"""
        try:
            theme_config = config.get("theme", {})
            theme_name = theme_config.get("current_theme", "light")
            print(f"🎨 Loading theme: {theme_name}")
            
            # Set theme
            for theme in ColorTheme:
                if theme.value == theme_name:
                    self.current_theme = theme
                    break
            
            # Tema tab'ını güncelle
            if hasattr(self, 'theme_tab') and hasattr(self.theme_tab, 'set_theme'):
                self.theme_tab.set_theme(self.current_theme)
            
            # Apply theme immediately
            self.color_manager.set_theme(self.current_theme)
            self.apply_stylesheet()
            
            print(f"✅ Theme applied: {self.current_theme.value}")
            
        except Exception as e:
            print(f"❌ Error loading theme: {e}")
    
    def load_all_tab_settings(self, config):
        """Load all tab settings comprehensively"""
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
                    
                    # Firing settings
                    "fire_delay_min": str(triggerbot_config.get("fire_delay_min", 170)),
                    "fire_delay_max": str(triggerbot_config.get("fire_delay_max", 480)),
                    
                    # Scan settings
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
        """Force refresh all tabs - After config import"""
        print("🔄 === FORCE REFRESHING ALL TABS ===")
        
        try:
            config = self.config_manager.load_config()
            
            # Refresh each tab individually
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
                    
                    # Call tab's load_settings method
                    if hasattr(tab, 'load_settings') and section_config:
                        try:
                            tab.load_settings(section_config)
                            print(f"✅ {tab_attr} refreshed successfully")
                        except Exception as e:
                            print(f"❌ Error refreshing {tab_attr}: {e}")
                    
                    # Call special update methods if they exist
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
        """Simple and safe settings reload - Freeze prevention"""
        print("🔄 === SIMPLE SETTINGS RELOAD ===")
        
        try:
            config = self.config_manager.load_config()
            print(f"📖 Config loaded: {list(config.keys())}")
            
            # 1. LOAD THEME SETTINGS (without calling change_theme)
            theme_config = config.get("theme", {})
            theme_name = theme_config.get("current_theme", "light")
            print(f"🎨 Theme from config: {theme_name}")
            
            # Set theme but don't call change_theme
            for theme in ColorTheme:
                if theme.value == theme_name:
                    self.current_theme = theme
                    break
            
            # Tema tab'ını güncelle
            if hasattr(self, 'theme_tab') and hasattr(self.theme_tab, 'set_theme'):
                self.theme_tab.set_theme(self.current_theme)
            
            # 2. LOAD TAB SETTINGS (one by one, safely)
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
        """Load tab settings safely"""
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
        """Load color settings comprehensively"""
        try:
            color_config = config.get("color_detection", {})
            print(f"🌈 Loading color settings: {color_config}")
            
            if hasattr(self, 'color_tab') and hasattr(self.color_tab, 'load_settings'):
                # Prepare all color settings
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
        """Load aimbot settings comprehensively"""
        try:
            aimbot_config = config.get("aimbot", {})
            print(f"🎯 Loading aimbot config: {aimbot_config}")
            
            if hasattr(self, 'aimbot_tab'):
                # Prepare all aimbot settings
                settings = {
                    # Temel ayarlar
                    "enabled": str(aimbot_config.get("enabled", True)).lower(),
                    "holdkey": aimbot_config.get("holdkey", "f"),
                    "toggle_key": aimbot_config.get("toggle_key", "insert"),
                    "use_holdkey": str(aimbot_config.get("use_holdkey", False)).lower(),
                    
                    # Indicator settings
                    "indicator_enabled": str(aimbot_config.get("indicator_enabled", True)).lower(),
                    "indicator_filled": str(aimbot_config.get("indicator_filled", False)).lower(),
                    "indicator_size_x": str(aimbot_config.get("indicator_size_x", 60)),
                    "indicator_size_y": str(aimbot_config.get("indicator_size_y", 13)),
                    "indicator_thickness": str(aimbot_config.get("indicator_thickness", 1)),
                    "indicator_opacity": str(aimbot_config.get("indicator_opacity", 255)),
                    
                    # Performance settings
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
                    
                    # Visual settings
                    "debug_mode": str(aimbot_config.get("debug_mode", False)).lower(),
                    "show_fov": str(aimbot_config.get("show_fov", False)).lower(),
                    "show_crosshair": str(aimbot_config.get("show_crosshair", True)).lower(),
                    "crosshair_size": str(aimbot_config.get("crosshair_size", 20)),
                    "crosshair_color": aimbot_config.get("crosshair_color", "#00ff00"),
                    "target_priority": aimbot_config.get("target_priority", "closest"),
                    "target_type": aimbot_config.get("target_type", "body")
                }
                
                print(f"🎯 Applying aimbot settings: {settings}")
                
                # Call aimbot tab's load_settings method
                if hasattr(self.aimbot_tab, 'load_settings'):
                    self.aimbot_tab.load_settings(settings)
                    print("✅ Aimbot settings loaded via load_settings")
                else:
                    # Apply settings manually
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
                
                # Call fire tab's load_settings method
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
        """Load anti-smoke settings comprehensively"""
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
        """Apply aimbot settings manually"""
        try:
            # Direct access to widgets in aimbot tab
            if hasattr(self.aimbot_tab, 'enabled_checkbox'):
                enabled = settings.get("enabled", "true").lower() == "true"
                self.aimbot_tab.enabled_checkbox.setChecked(enabled)
            
            # Apply other settings similarly...
            print("✅ Aimbot settings applied manually")
            
        except Exception as e:
            print(f"❌ Error applying aimbot settings manually: {e}")
    

    

        
        # Load color settings (for old format compatibility)
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
        
        # Load settings for each tab
        self.color_tab.load_settings(color_config)
        
        # Load fire tab settings
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
        
        # Load aimbot settings
        if hasattr(self, 'aimbot_tab'):
            aimbot = config.get("aimbot", {})
            # Call aimbot tab's load_settings method (if exists)
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
        """Save all settings comprehensively"""
        print("💾 === COMPREHENSIVE SETTINGS SAVE ===")
        
        try:
            # Load current config
            config = self.config_manager.load_config()
            print(f"📖 Base config loaded: {list(config.keys())}")
            
            # COLLECT AND SAVE ALL SETTINGS
            self.collect_and_save_all_settings(config)
            
            # Config'i kaydet
            success, message = self.config_manager.save_config(config)
            
            if success:
                print(f"✅ === ALL SETTINGS SAVED SUCCESSFULLY ===")
                self.statusBar.show_success("All settings saved", 3000)
                try:
                    show_success("Settings Saved", "All settings saved successfully", 2000)
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
        
        # Tab'ların temizlik işlemlerini çağır
        if hasattr(self, 'aimbot_tab'):
            self.aimbot_tab.cleanup()
        if hasattr(self, 'fire_tab'):
            self.fire_tab.cleanup()
        if hasattr(self, 'rcs_tab'):
            self.rcs_tab.cleanup()
        if hasattr(self, 'spike_timer_tab'):
            self.spike_timer_tab.cleanup()
        
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
        
        # RCS settings (hızlı)
        try:
            if "rcs" in config_data:
                rcs_config = config_data["rcs"]
                if hasattr(self, 'rcs_tab') and hasattr(self.rcs_tab, 'load_settings'):
                    settings = {
                        "rcs_enabled": str(rcs_config.get("enabled", False)).lower(),
                        "pull_speed": str(rcs_config.get("pull_speed", 5)),
                        "activation_delay": str(rcs_config.get("activation_delay", 100)),
                        "rapid_click_threshold": str(rcs_config.get("rapid_click_threshold", 200)),
                        "aimbot_integration": str(rcs_config.get("aimbot_integration", True)).lower()
                    }
                    self.rcs_tab.load_settings(settings)
                    print("✅ RCS settings applied (fast)")
        except Exception as e:
            print(f"❌ Error applying RCS settings (fast): {e}")
        
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
    
    # LICENSE VALIDATION - Must be first before QApplication!
    print("Starting license validation...", flush=True)
    if not validate_license():
        print("License validation failed or cancelled. Exiting...", flush=True)
        sys.exit(1)
    print("License validation successful!", flush=True)
    
    try:
        app = QApplication(sys.argv)
        print("QApplication created successfully", flush=True)
        
        # Show connection dialog after license validation
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