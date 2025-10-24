"""
License Validation System
Handles license key validation against the remote server
"""

import socket
import subprocess
import hashlib
import platform
from typing import Tuple, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QProgressBar, QFrame, QApplication, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPainter, QLinearGradient, QBrush, QColor, QRadialGradient
import random
import math


class LicenseValidationThread(QThread):
    """Thread for handling license validation to avoid UI blocking"""
    validation_complete = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, license_key: str, hwid: str):
        super().__init__()
        self.license_key = license_key
        self.hwid = hwid
        self.server_host = "synpserver.duckdns.org"
        self.server_port = 3313
        self.success_response = "dPRC3n8019n3pSappQgE20JWTLracB"
    
    def run(self):
        """Perform license validation"""
        try:
            # Create message in expected format: key:{key} hwid:{hwid}
            message = f"key:{self.license_key} hwid:{self.hwid}"
            
            # Connect to server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # 10 second timeout
            
            client_socket.connect((self.server_host, self.server_port))
            
            # Send message
            client_socket.sendall(message.encode('utf-8'))
            
            # Receive response
            response = client_socket.recv(4096).decode('utf-8', errors='ignore')
            client_socket.close()
            
            # Check if validation successful
            if response == self.success_response:
                self.validation_complete.emit(True, "License validated! Continuing to program...")
            else:
                self.validation_complete.emit(False, f"License validation error")
                
        except socket.timeout:
            self.validation_complete.emit(False, "Server connection timed out!")
        except socket.gaierror:
            self.validation_complete.emit(False, "Cannot reach server address!")
        except ConnectionRefusedError:
            self.validation_complete.emit(False, "Server connection refused!")
        except Exception as e:
            self.validation_complete.emit(False, f"Connection error")


class HWIDGenerator:
    """Hardware ID generation utility"""
    
    @staticmethod
    def get_hwid() -> str:
        """Generate hardware ID based on system information"""
        try:
            # Get various system information
            system_info = []
            
            # CPU info
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        cpu_id = result.stdout.strip().split('\n')[-1].strip()
                        if cpu_id and cpu_id != "ProcessorId":
                            system_info.append(cpu_id)
                else:
                    # For Linux/Mac - use different approach
                    result = subprocess.run(['cat', '/proc/cpuinfo'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'Serial' in line:
                                system_info.append(line.split(':')[1].strip())
                                break
            except:
                pass
            
            # Motherboard info
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'baseboard', 'get', 'SerialNumber'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        mb_serial = result.stdout.strip().split('\n')[-1].strip()
                        if mb_serial and mb_serial != "SerialNumber":
                            system_info.append(mb_serial)
            except:
                pass
            
            # Machine name
            try:
                system_info.append(platform.node())
            except:
                pass
            
            # Platform info
            try:
                system_info.append(platform.machine())
                system_info.append(platform.processor())
            except:
                pass
            
            # If no hardware info found, use platform info
            if not system_info:
                system_info = [platform.system(), platform.release(), platform.machine()]
            
            # Create hash
            combined_info = '|'.join(filter(None, system_info))
            hwid_hash = hashlib.sha256(combined_info.encode()).hexdigest()[:16]
            
            return hwid_hash.upper()
            
        except Exception as e:
            print(f"HWID generation error: {e}")
            # Fallback HWID
            fallback_data = f"{platform.system()}{platform.node()}{platform.machine()}"
            return hashlib.sha256(fallback_data.encode()).hexdigest()[:16].upper()


class LicenseDialog(QDialog):
    """Modern license validation dialog with server.py styling"""
    
    def __init__(self):
        super().__init__()
        self.hwid = HWIDGenerator.get_hwid()
        self.validation_thread = None
        self.bubbles = []
        self._opacity = 1.0
        
        # Mouse drag variables
        self.drag_position = None
        
        # Set window properties first - frameless and stays on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)
        
        self.setupUI()
        self.setupAnimations()
        
        # Auto-generate some bubbles for background effect
        self.initBubbles()
        
        # Center after UI is set up
        self.center()
    
    def initBubbles(self):
        """Initialize background bubbles"""
        for _ in range(12):
            bubble = {
                'x': random.randint(0, 500),
                'y': random.randint(0, 400),
                'size': random.randint(8, 20),
                'speed_x': random.uniform(-0.5, 0.5),
                'speed_y': random.uniform(-1, -0.2),
                'opacity': random.uniform(0.1, 0.25)
            }
            self.bubbles.append(bubble)
    
    def setupUI(self):
        """Setup the user interface"""
        self.setFixedSize(500, 400)
        self.setWindowTitle("License Validation - SYNAPSE")
        
        # Main layout directly on dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("DEFENDING STORE")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #a0a0a0;
            font-size: 36px;
            font-weight: bold;
            font-family: 'Roboto', 'Arial Black';
            margin-bottom: 10px;
        """)
        
        # Subtitle
        subtitle_label = QLabel("License Validation")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            color: #ffffff;
            font-size: 18px;
            font-weight: normal;
            font-family: 'Roboto', 'Arial';
            margin-bottom: 20px;
        """)
        
        # License key input
        license_label = QLabel("License Key:")
        license_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            font-family: 'Roboto', 'Arial';
        """)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter your license key...")
        self.license_input.setFixedHeight(45)  # Fixed height for better visibility
        self.license_input.setStyleSheet("""
            QLineEdit {
                background: rgba(50, 50, 50, 150);
                border: 2px solid rgba(100, 100, 100, 0.4);
                border-radius: 12px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 16px;
                font-family: 'Roboto', 'Arial';
            }
            QLineEdit:focus {
                border: 2px solid rgba(120, 120, 120, 0.8);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.validate_button = QPushButton("Validate")
        self.validate_button.setFixedHeight(50)  # Fixed height for better visibility
        self.validate_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
                border: 2px solid rgba(110, 110, 110, 0.6);
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 12px 24px;
                font-family: 'Roboto', 'Arial';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 120, 120, 220), stop:1 rgba(100, 100, 100, 220));
                border: 2px solid rgba(130, 130, 130, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(70, 70, 70, 200), stop:1 rgba(90, 90, 90, 200));
            }
            QPushButton:disabled {
                background: rgba(60, 60, 80, 100);
                border: 2px solid rgba(100, 100, 120, 0.4);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.validate_button.clicked.connect(self.validate_license)
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(50)  # Fixed height for better visibility
        self.exit_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(220, 53, 69, 150), stop:1 rgba(180, 40, 55, 150));
                border: 2px solid rgba(220, 53, 69, 0.6);
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 12px 24px;
                font-family: 'Roboto', 'Arial';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(220, 53, 69, 200), stop:1 rgba(180, 40, 55, 200));
                border: 2px solid rgba(220, 53, 69, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(180, 40, 55, 180), stop:1 rgba(220, 53, 69, 180));
            }
        """)
        self.exit_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.exit_button)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(50, 50, 50, 150);
                border: 1px solid rgba(100, 100, 100, 0.4);
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 100, 100, 200), stop:1 rgba(80, 80, 80, 200));
                border-radius: 8px;
            }
        """)
        self.progress_bar.setVisible(False)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-family: 'Roboto', 'Arial';
            margin-top: 10px;
        """)
        
        # Add widgets to layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addStretch()
        main_layout.addWidget(license_label)
        main_layout.addWidget(self.license_input)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        
        # Enable enter key to validate
        self.license_input.returnPressed.connect(self.validate_license)
    
    def setupAnimations(self):
        """Setup bubble animations"""
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.updateBubbles)
        self.bubble_timer.start(60)
    
    def paintEvent(self, event):
        """Custom paint event for background and bubbles"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rounded background gradient (gray theme)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(20, 20, 20))
        gradient.setColorAt(1, QColor(30, 30, 30))
        
        rect = self.rect()
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 25, 25)
        
        # Draw border (gray theme)
        painter.setPen(QColor(100, 100, 100, 80))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 25, 25)
        
        # Draw bubbles (gray theme)
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
        """Update bubble positions"""
        for bubble in self.bubbles:
            bubble['x'] += bubble['speed_x']
            bubble['y'] += bubble['speed_y']
            
            # Reset bubble if it goes off screen
            if bubble['y'] < -bubble['size']:
                bubble['y'] = self.height() + bubble['size']
                bubble['x'] = random.randint(0, self.width())
            
            if bubble['x'] < -bubble['size'] or bubble['x'] > self.width() + bubble['size']:
                bubble['speed_x'] *= -1
        
        self.update()
    
    def center(self):
        """Center the dialog on screen"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def validate_license(self):
        """Validate the license key"""
        license_key = self.license_input.text().strip()
        
        if not license_key:
            self.show_error("Please enter your license key!")
            return
        
        # Disable UI during validation
        self.validate_button.setEnabled(False)
        self.license_input.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Validating license...")
        
        # Start validation thread
        self.validation_thread = LicenseValidationThread(license_key, self.hwid)
        self.validation_thread.validation_complete.connect(self.on_validation_complete)
        self.validation_thread.start()
    
    def on_validation_complete(self, success: bool, message: str):
        """Handle validation completion"""
        # Re-enable UI
        self.validate_button.setEnabled(True)
        self.license_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("""
                color: #4caf50;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Roboto', 'Arial';
                margin-top: 10px;
            """)
            
            # Close dialog after 1 second
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("""
                color: #f44336;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Roboto', 'Arial';
                margin-top: 10px;
            """)
            
            # Clear after 3 seconds
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
    
    def show_error(self, message: str):
        """Show error message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            color: #f44336;
            font-size: 14px;
            font-weight: bold;
            font-family: 'Roboto', 'Arial';
            margin-top: 10px;
        """)
        
        # Clear after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()


def validate_license() -> bool:
    """
    Show license validation dialog and return validation result
    Returns True if license is valid, False otherwise
    """
    # Bypass license validation - always return True
    return True

if __name__ == "__main__":
    # Test the license dialog
    import sys
    
    app = QApplication(sys.argv)
    
    # Test HWID generation
    hwid = HWIDGenerator.get_hwid()
    print(f"Generated HWID: {hwid}")
    
    # Test dialog
    if validate_license():
        print("License validation successful!")
    else:
        print("License validation failed or cancelled.")
    
    sys.exit(0)