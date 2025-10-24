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
                             QPushButton, QLineEdit, QApplication, QMessageBox, QProgressBar)
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
        self.setup_style()
        self.center_on_screen()
        self.start_scanning()
    
    def setup_ui(self):
        """UI setup - Loading screen"""
        self.setWindowTitle("Searching for Server...")
        self.setFixedSize(380, 280)  # Smaller size
        # Borderless window
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Smaller spacing
        layout.setContentsMargins(30, 25, 30, 25)  # Smaller margins
        
        # Title label
        self.title_label = QLabel("SEARCHING FOR SERVER")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        
        # Status message
        self.status_label = QLabel("Scanning network...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("progressBar")
        
        # Timer for animation effect
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_title)
        self.animation_timer.start(500)
        self.dot_count = 0
        
        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def animate_title(self):
        """Title animation"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.title_label.setText(f"SEARCHING FOR SERVER{dots}")
    
    def setup_style(self):
        """Modern splash screen tema stilleri (Qt-compatible)"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 30, 30, 255), stop:0.5 rgba(40, 40, 40, 255), stop:1 rgba(35, 35, 35, 255));
                border-radius: 20px;
                border: 3px solid rgba(120, 120, 120, 0.6);
            }
            
            #titleLabel {
                color: #a0a0a0;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Arial Black', 'Arial';
                padding: 8px;
                background: transparent;
                border: none;
            }
            
            #statusLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-family: 'Roboto', 'Arial';
                padding: 5px;
                background: transparent;
                border: none;
                min-height: 25px;
            }
            
            #progressBar {
                border: 2px solid rgba(100, 100, 100, 0.4);
                border-radius: 8px;
                background: rgba(50, 50, 50, 150);
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 10px;
                height: 18px;
            }
            
            #progressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(110, 110, 110, 255), 
                    stop:0.5 rgba(120, 120, 120, 255),
                    stop:1 rgba(130, 130, 130, 255));
                border-radius: 6px;
                margin: 1px;
            }
        """)
    
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
        self.title_label.setText("SERVER FOUND!")
        self.selected_ip = ip
        self.connection_accepted.emit(ip)
        
        print(f"Server found: {ip}")
        
        # Close dialog after a short delay
        QTimer.singleShot(1500, self.accept)
    
    @pyqtSlot(bool)
    def on_scan_completed(self, success):
        """When scanning is completed"""
        if not success:
            self.animation_timer.stop()
            self.title_label.setText("SERVER NOT FOUND")
            self.status_label.setText("Wait for manual IP entry...")
            # Show dialog for manual IP entry
            QTimer.singleShot(2000, lambda: self.show_manual_input())
    
    def show_manual_input(self):
        """Show manual IP entry dialog"""
        self.setup_manual_input_ui()
    
    def setup_manual_input_ui(self):
        """Change UI for manual IP entry"""
        # Clear existing widgets
        layout = self.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Adjust layout spacing
        layout.setSpacing(12)  # Smaller spacing
        layout.setContentsMargins(25, 20, 25, 20)  # Smaller margins
        
        # New UI elements
        self.title_label = QLabel("MANUAL IP ENTRY")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        
        self.instruction_label = QLabel("Enter server IP address:")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setObjectName("instructionLabel")
        
        # IP input field
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Example: 192.168.1.100")
        self.ip_input.setText("127.0.0.1")  # Default value
        self.ip_input.setObjectName("ipInput")
        self.ip_input.setMaxLength(15)  # Sufficient for IP address
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Smaller button spacing
        
        self.connect_button = QPushButton("CONNECT")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.clicked.connect(self.validate_and_connect)
        
        self.cancel_button = QPushButton("CANCEL")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.handle_cancel)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.connect_button)
        
        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.ip_input)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Connect with Enter key
        self.ip_input.returnPressed.connect(self.validate_and_connect)
        self.ip_input.setFocus()
        
        # Style update
        self.update_manual_input_style()
    
    def validate_and_connect(self):
        """Validate IP address and test connection"""
        ip_text = self.ip_input.text().strip()
        
        # Simple IP validation
        if not self.is_valid_ip(ip_text):
            self.show_error_message("Invalid IP address! Try again:")
            return
        
        # Testing connection message
        self.instruction_label.setText(f"Testing {ip_text}...")
        self.instruction_label.setStyleSheet("""
            color: #ffd93d; 
            font-weight: bold;
            font-size: 13px;
            font-family: 'Roboto', 'Arial';
            padding: 8px 5px;
            background: transparent;
            border: none;
            margin-bottom: 5px;
        """)
        self.connect_button.setEnabled(False)  # Disable button
        
        # Test connection with a short delay (for UI update)
        QTimer.singleShot(100, lambda: self.perform_connection_test(ip_text))
    
    def perform_connection_test(self, ip_text):
        """Perform actual connection test"""
        # Test connection
        if self.test_connection_to_ip(ip_text):
            # Connection successful
            self.instruction_label.setText(f"Connection to {ip_text} successful!")
            self.instruction_label.setStyleSheet("""
                color: #51cf66; 
                font-weight: bold;
                font-size: 13px;
                font-family: 'Roboto', 'Arial';
                padding: 8px 5px;
                background: transparent;
                border: none;
                margin-bottom: 5px;
            """)
            self.selected_ip = ip_text
            self.connection_accepted.emit(self.selected_ip)
            # Close after a short delay
            QTimer.singleShot(1000, self.accept)
        else:
            # Connection failed
            self.show_error_message(f"Cannot connect to {ip_text}! Enter new IP:")
            self.connect_button.setEnabled(True)  # Re-enable button
    
    def test_connection_to_ip(self, ip, port=1515, timeout=3):
        """Test connection to specified IP address"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def show_error_message(self, message):
        """Show error message and re-enable IP entry"""
        self.instruction_label.setText(message)
        self.instruction_label.setStyleSheet("""
            color: #ff6b6b; 
            font-weight: bold;
            font-size: 13px;
            font-family: 'Roboto', 'Arial';
            padding: 8px 5px;
            background: transparent;
            border: none;
            margin-bottom: 5px;
        """)
        self.ip_input.setFocus()
        self.ip_input.selectAll()
        self.connect_button.setEnabled(True)  # Re-enable button
        # Return to normal color after 4 seconds
        QTimer.singleShot(4000, self.reset_instruction_style)
    
    def reset_instruction_style(self):
        """Return instruction label to normal style"""
        self.instruction_label.setText("Enter server IP address:")
        self.instruction_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 13px;
            font-family: 'Roboto', 'Arial';
            padding: 8px 5px;
            background: transparent;
            border: none;
            margin-bottom: 5px;
        """)
    
    def handle_cancel(self):
        """When cancel button is pressed"""
        self.show_error_message("Cancelled! Enter new IP or close:")
        # Change cancel button to close button
        self.cancel_button.setText("CLOSE")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.reject)
    
    def is_valid_ip(self, ip):
        """Check if IP address is valid"""
        import re
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(pattern, ip) is not None
    
    def update_manual_input_style(self):
        """Style update for manual entry"""
        self.setStyleSheet(self.styleSheet() + """
            #instructionLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;  /* Smaller font */
                font-family: 'Roboto', 'Arial';
                padding: 8px 5px;  /* Smaller padding */
                background: transparent;
                border: none;
                margin-bottom: 5px;  /* Smaller margin */
            }
            
            #ipInput {
                border: 2px solid rgba(120, 120, 120, 0.6);
                border-radius: 6px;  /* Smaller radius */
                background: rgba(50, 50, 50, 150);
                color: white;
                font-size: 14px;  /* Smaller font */
                font-family: 'Roboto', 'Arial';
                padding: 10px;  /* Smaller padding */
                text-align: center;
                margin: 5px 15px;  /* Smaller margin */
                min-height: 16px;  /* Smaller height */
            }
            
            #ipInput:focus {
                border: 2px solid rgba(120, 120, 120, 0.8);
                background: rgba(60, 60, 60, 180);
            }
            
            #connectButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(110, 110, 110, 200), stop:1 rgba(90, 90, 90, 200));
                border: 2px solid rgba(120, 120, 120, 0.8);
                border-radius: 6px;  /* Smaller radius */
                color: white;
                font-size: 12px;  /* Smaller font */
                font-weight: bold;
                font-family: 'Arial';
                padding: 8px 20px;  /* Smaller padding */
                margin: 5px 3px;  /* Smaller margin */
                min-width: 70px;  /* Smaller width */
                min-height: 28px;  /* Smaller height */
            }
            
            #connectButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(130, 130, 130, 220), stop:1 rgba(110, 110, 110, 220));
            }
            
            #connectButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(90, 90, 90, 200), stop:1 rgba(70, 70, 70, 200));
            }
            
            #cancelButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(70, 70, 70, 200), stop:1 rgba(50, 50, 50, 200));
                border: 2px solid rgba(100, 100, 100, 0.8);
                border-radius: 6px;  /* Smaller radius */
                color: white;
                font-size: 12px;  /* Smaller font */
                font-weight: bold;
                font-family: 'Arial';
                padding: 8px 20px;  /* Smaller padding */
                margin: 5px 3px;  /* Smaller margin */
                min-width: 70px;  /* Smaller width */
                min-height: 28px;  /* Smaller height */
            }
            
            #cancelButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(90, 90, 90, 220), stop:1 rgba(70, 70, 70, 220));
            }
            
            #cancelButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 50, 50, 200), stop:1 rgba(30, 30, 30, 200));
            }
        """)
    
    def closeEvent(self, event):
        """Dialog closing event"""
        if self.scanner and self.scanner.isRunning():
            self.scanner.terminate()
            self.scanner.wait()
        event.accept()
    
    def get_selected_ip(self):
        """Get selected IP address"""
        return self.selected_ip
    
    def keyPressEvent(self, event):
        """Key press events"""
        if event.key() == Qt.Key_Escape:
            # Don't allow closing with Escape
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