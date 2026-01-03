"""
Server Connection Dialog
Automatically scans network using ARP and connects to available TCP servers on port 1515
"""

import sys
import subprocess
import socket
import threading
import time
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QApplication, QMessageBox, QProgressBar, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QMovie
import re


class NetworkScanner(QThread):
    progress_update = pyqtSignal(str, int)  # message, progress
    connection_found = pyqtSignal(str)  # IP address
    scan_completed = pyqtSignal(bool)  # success/failure
    
    def __init__(self):
        super().__init__()
        self.local_ip = self.get_local_ip()
        
    def get_local_ip(self):
        """Get our own IP address"""
        try:
            # Learn our own IP by connecting to Google DNS
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def get_arp_ips(self):
        """Get IPv4 addresses from ARP table"""
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                # Extract IPv4 addresses with regex
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                ips = re.findall(ip_pattern, result.stdout)
                # Filter out our own IP and broadcast/multicast addresses
                filtered_ips = []
                for ip in ips:
                    if (ip != self.local_ip and 
                        not ip.startswith('224.') and 
                        not ip.startswith('239.') and
                        not ip.endswith('.255') and
                        ip != '127.0.0.1'):
                        filtered_ips.append(ip)
                return list(set(filtered_ips))  # Remove duplicates
            return []
        except Exception as e:
            print(f"ARP error: {e}")
            return []
    
    def test_connection(self, ip, port=1515, timeout=2):
        """Test TCP connection to specified IP and port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # --- TCP_NODELAY EKLENDI ---
            # Nagle algoritmasını kapatır, bağlantı testi sırasında
            # handshake işleminin milisaniye daha hızlı olmasını sağlar.
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # ---------------------------

            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def run(self):
        """Main scanning operation"""
        self.progress_update.emit("Scanning network addresses...", 10)
        
        # Get IPs from ARP table
        ips = self.get_arp_ips()
        
        if not ips:
            self.progress_update.emit("No IP addresses found!", 100)
            self.scan_completed.emit(False)
            return
        
        self.progress_update.emit(f"{len(ips)} IP addresses found, testing...", 30)
        
        # Test each IP
        for i, ip in enumerate(ips):
            progress = 30 + int((i / len(ips)) * 60)
            self.progress_update.emit(f"Testing: {ip}", progress)
            
            if self.test_connection(ip):
                self.progress_update.emit(f"Server found: {ip}", 100)
                self.connection_found.emit(ip)
                return
            
            time.sleep(0.1)  # Short wait
        
        self.progress_update.emit("No servers found!", 100)
        self.scan_completed.emit(False)


class ServerConnectionDialog(QDialog):
    connection_accepted = pyqtSignal(str)  # IP address signal
    
    def __init__(self):
        super().__init__()
        self.selected_ip = '127.0.0.1'  # Default IP
        self.scanner = None
        self.setup_ui()
        self.center_on_screen()
        self.start_scanning()
    
    def setup_ui(self):
        """UI setup - Loading screen"""
        self.setWindowTitle("Connecting...")
        self.setFixedSize(400, 300)
        # Borderless window
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main Layout inside a frame for styling
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QFrame()
        self.frame.setObjectName("mainFrame")
        self.frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #121212;
                border: 1px solid #333;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(self.frame)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Icon/Logo area
        logo_label = QLabel("📡")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 48px; background: transparent;")
        
        # Title label
        self.title_label = QLabel("SEARCHING FOR SERVER")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #fff;
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 2px;
            background: transparent;
        """)
        
        # Status message
        self.status_label = QLabel("Scanning network...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #888;
            font-size: 13px;
            background: transparent;
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a1a;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #00cc66;
                border-radius: 3px;
            }
        """)
        
        # Animation setup
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_title)
        self.animation_timer.start(500)
        self.dot_count = 0
        
        # Add widgets
        layout.addStretch()
        layout.addWidget(logo_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addSpacing(10)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        
        main_layout.addWidget(self.frame)
    
    def animate_title(self):
        """Title animation"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.title_label.setText(f"SEARCHING FOR SERVER{dots}")
    
    def center_on_screen(self):
        """Center dialog on screen"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def start_scanning(self):
        """Ağ tarama işlemini başlat"""
        self.scanner = NetworkScanner()
        self.scanner.progress_update.connect(self.update_progress)
        self.scanner.connection_found.connect(self.on_connection_found)
        self.scanner.scan_completed.connect(self.on_scan_completed)
        self.scanner.start()
    
    @pyqtSlot(str, int)
    def update_progress(self, message, progress):
        """İlerleme güncellemesi"""
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)
    
    @pyqtSlot(str)
    def on_connection_found(self, ip):
        """When connection is found"""
        self.animation_timer.stop()
        self.title_label.setText("SERVER FOUND")
        self.title_label.setStyleSheet("color: #00cc66; font-size: 16px; font-weight: 900; letter-spacing: 2px;")
        self.status_label.setText(f"Connected to {ip}")
        self.selected_ip = ip
        self.connection_accepted.emit(ip)
        
        # Close dialog after a short delay
        QTimer.singleShot(1000, self.accept)
    
    @pyqtSlot(bool)
    def on_scan_completed(self, success):
        """When scanning is completed"""
        if not success:
            self.animation_timer.stop()
            self.title_label.setText("SERVER NOT FOUND")
            self.title_label.setStyleSheet("color: #e53e3e; font-size: 16px; font-weight: 900; letter-spacing: 2px;")
            self.status_label.setText("Switching to manual entry...")
            # Show dialog for manual IP entry
            QTimer.singleShot(1500, lambda: self.show_manual_input())
    
    def show_manual_input(self):
        """Show manual IP entry dialog"""
        self.setup_manual_input_ui()
    
    def setup_manual_input_ui(self):
        """Change UI for manual IP entry"""
        # Clear existing widgets in the frame layout
        layout = self.frame.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Header
        title = QLabel("MANUAL CONNECTION")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #fff;
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 1px;
        """)
        
        desc = QLabel("Enter server IP address manually")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        
        # IP Input
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g. 192.168.1.100")
        self.ip_input.setText("127.0.0.1")
        self.ip_input.setAlignment(Qt.AlignCenter)
        self.ip_input.setMaxLength(15)
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                color: #fff;
                padding: 12px;
                font-family: monospace;
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00cc66;
                background-color: #222;
            }
        """)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("EXIT")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #333;
                border-radius: 6px;
                color: #888;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                color: #fff;
                border: 1px solid #555;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.connect_button = QPushButton("CONNECT")
        self.connect_button.setCursor(Qt.PointingHandCursor)
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #00cc66;
                border: none;
                border-radius: 6px;
                color: #000;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00e673;
            }
            QPushButton:pressed {
                background-color: #00b359;
            }
        """)
        self.connect_button.clicked.connect(self.validate_and_connect)
        
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.connect_button)
        
        # Status/Error Label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #e53e3e; font-size: 11px; font-weight: bold;")
        
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.error_label)
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        # Connect enter key
        self.ip_input.returnPressed.connect(self.validate_and_connect)
        self.ip_input.setFocus()
    
    def validate_and_connect(self):
        """Validate IP and connect"""
        ip_text = self.ip_input.text().strip()
        
        if not self.is_valid_ip(ip_text):
            self.show_error("Invalid IP Format")
            return
            
        self.error_label.setText("Testing connection...")
        self.error_label.setStyleSheet("color: #ecc94b; font-size: 11px; font-weight: bold;")
        self.connect_button.setEnabled(False)
        self.ip_input.setEnabled(False)
        
        QTimer.singleShot(100, lambda: self.perform_connection_test(ip_text))
        
    def perform_connection_test(self, ip_text):
        if self.test_connection_to_ip(ip_text):
            self.error_label.setText("Success!")
            self.error_label.setStyleSheet("color: #00cc66; font-size: 11px; font-weight: bold;")
            self.selected_ip = ip_text
            self.connection_accepted.emit(ip_text)
            QTimer.singleShot(500, self.accept)
        else:
            self.show_error("Connection Failed")
            self.connect_button.setEnabled(True)
            self.ip_input.setEnabled(True)
            self.ip_input.setFocus()
    
    def show_error(self, msg):
        self.error_label.setText(msg)
        self.error_label.setStyleSheet("color: #e53e3e; font-size: 11px; font-weight: bold;")
        
        # Shake animation using property animation usually, but we'll stick to simple flash
        # (Could implement QPropertyAnimation on the frame position for a shake if requested)

    def test_connection_to_ip(self, ip, port=1515, timeout=3):
        """Test connection to specified IP address"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
            
    def is_valid_ip(self, ip):
        """Check if IP address is valid"""
        import re
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(pattern, ip) is not None

    def closeEvent(self, event):
        if self.scanner and self.scanner.isRunning():
            self.scanner.terminate()
            self.scanner.wait()
        event.accept()
    
    def get_selected_ip(self):
        return self.selected_ip
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            return
        super().keyPressEvent(event)


def show_connection_dialog():
    """Show connection dialog and return selected IP"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    print("Opening server scanning dialog...")
    dialog = ServerConnectionDialog()
    
    result = dialog.exec_()
    selected_ip = dialog.get_selected_ip()
    
    print(f"Dialog result: {result}, Selected IP: {selected_ip}")
    
    if result == QDialog.Accepted:
        return selected_ip
    else:
        # Use default IP if user closes dialog
        return '127.0.0.1'


if __name__ == "__main__":
    # Test dialog
    app = QApplication(sys.argv)
    ip = show_connection_dialog()
    print(f"Selected IP: {ip}")    
