from makcu import create_controller, MouseButton
import socket
import threading
import time
import sys
import re
from pynput import mouse
from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QLinearGradient, QBrush, QRadialGradient
from PyQt5.QtCore import QThread, pyqtSignal
import math
import random

# Process hollowing import - Added for stealth mode
try:
    from utils.process_hollower import run_as_stealth_process
    PROCESS_HOLLOWING_AVAILABLE = True
except ImportError:
    PROCESS_HOLLOWING_AVAILABLE = False

class AnimatedSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._opacity = 0.0
        self.bubbles = []
        self.initBubbles()
        self.setupUI()
        self.setupAnimations()
        self.center()
    
    def initBubbles(self):
        for _ in range(15):
            bubble = {
                'x': random.randint(0, 400),
                'y': random.randint(0, 300),
                'size': random.randint(10, 30),
                'speed_x': random.uniform(-1, 1),
                'speed_y': random.uniform(-2, -0.5),
                'opacity': random.uniform(0.1, 0.3)
            }
            self.bubbles.append(bubble)
    
    def setupUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Use a legitimate title for the splash screen
        legitimate_titles = [
            "Windows Update", 
            "System Configuration", 
            "Device Manager", 
            "Task Manager",
            "Control Panel",
            "Windows Security"
        ]
        self.title_label = QLabel(random.choice(legitimate_titles))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #9d4edd;
                font-size: 48px;
                font-weight: bold;
                font-family: 'Roboto', 'Arial Black';
                background: transparent;
                border: none;
            }
        """)
        
        # Use a legitimate version number
        self.version_label = QLabel("Version 10.0.19041")
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
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        
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
        
        # Draw rounded background gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(26, 26, 46))
        gradient.setColorAt(1, QColor(22, 33, 62))
        
        # Create rounded rectangle path
        rect = self.rect()
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 25, 25)
        
        # Draw bubbles
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
    
    def setupAnimations(self):
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.updateBubbles)
        self.bubble_timer.start(50)
    
    def center(self):
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
        
        QTimer.singleShot(3000, self.close)

class MakcuTCPServer:
    def __init__(self, host='127.0.0.1', port=1515):
        self.host = host
        self.port = port
        self.makcu = None
        self.server_socket = None
        self.running = False
        self.makcu_enabled = True
        self.mouse_listener = None
        
    def initialize_makcu(self):
        try:
            self.makcu = create_controller(debug=True, auto_reconnect=True)
            if self.makcu:
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def on_middle_click(self, x, y, button, pressed):
        if button == mouse.Button.middle and pressed:
            self.makcu_enabled = not self.makcu_enabled
    
    def start_mouse_listener(self):
        try:
            self.mouse_listener = mouse.Listener(on_click=self.on_middle_click)
            self.mouse_listener.start()
        except Exception as e:
            pass
    
    def force_release_all_buttons(self):
        try:
            buttons = [MouseButton.LEFT, MouseButton.RIGHT, MouseButton.MIDDLE]
            for button in buttons:
                try:
                    self.makcu.release(button)
                except:
                    pass
            return True
        except Exception as e:
            return False
    
    def process_command(self, command):
        command = command.strip()
        
        if not self.makcu_enabled:
            return "INFO: Makcu commands disabled\n"
        
        try:
            if command.lower() == "firecmds":
                try:
                    self.makcu.press(MouseButton.LEFT)
                    time.sleep(0.01)
                    self.makcu.release(MouseButton.LEFT)
                    return "OK: Left click executed\n"
                except Exception as click_error:
                    try:
                        self.makcu.release(MouseButton.LEFT)
                    except:
                        pass
                    return f"ERROR: Click failed - {click_error}\n"
                
            elif command.lower() == "release" or command.lower() == "unstuck":
                if self.force_release_all_buttons():
                    return "OK: All buttons released\n"
                else:
                    return "ERROR: Failed to release buttons\n"
                
            elif command.startswith("hareket+"):
                match = re.search(r'hareket\+(-?\d+),(-?\d+)', command)
                
                if match:
                    x = int(match.group(1))
                    y = int(match.group(2))
                    self.makcu.move(x, y)
                    return f"OK: Mouse moved to ({x}, {y})\n"
                else:
                    return "ERROR: Invalid movement format. Use: hareket+x,y\n"
            else:
                return "ERROR: Unknown command\n"
                
        except Exception as e:
            error_msg = f"ERROR: Command execution failed - {e}\n"
            return error_msg
    
    def handle_client(self, client_socket, client_address):
        try:
            # --- BURAYA EKLENDİ (İstemci için kritik hız ayarı) ---
            # TCP_NODELAY: Küçük veri paketlerinin birikmesini engeller, anında iletir.
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # ------------------------------------------------------

            status = "ENABLED" if self.makcu_enabled else "DISABLED"
            welcome_msg = f"Connected to Makcu TCP Server\nMakcu Status: {status}\nCommands: 'firecmds', 'hareket+x,y', 'release'\n"
            client_socket.send(welcome_msg.encode('utf-8'))
            
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    commands = data.decode('utf-8').strip().split('\n')
                    for command in commands:
                        if command.strip():
                            response = self.process_command(command)
                            client_socket.send(response.encode('utf-8'))
                            
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except Exception as e:
                    break
                    
        except Exception as e:
            pass
        finally:
            client_socket.close()
    
    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # --- BURAYA EKLENDİ (Sunucu soketi için ayar) ---
            # Soket oluşturulduğu an gecikme önleyiciyi aktif ediyoruz.
            self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) 
            # ------------------------------------------------
            
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        pass
                    break
                    
        except Exception as e:
            pass
        finally:
            self.stop_server()
    
    def stop_server(self):
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
            
        if self.mouse_listener:
            self.mouse_listener.stop()
            
        if self.makcu:
            try:
                self.makcu.disconnect()
            except:
                pass

class ServerThread(QThread):
    def __init__(self):
        super().__init__()
        self.server = None
    
    def run(self):
        self.server = MakcuTCPServer()
        
        if not self.server.initialize_makcu():
            time.sleep(10)
            return
        
        try:
            self.server.start_mouse_listener()
            self.server.start_server()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
        finally:
            if self.server:
                self.server.stop_server()
    
    def stop_server(self):
        if self.server:
            self.server.stop_server()
        self.quit()
        self.wait()

def show_splash_screen():
    app = QApplication(sys.argv)
    splash = AnimatedSplashScreen()
    splash.showSplash()
    app.processEvents()
    
    start_time = time.time()
    while time.time() - start_time < 3:
        app.processEvents()
        time.sleep(0.01)
    
    # Start server in separate thread
    server_thread = ServerThread()
    server_thread.start()
    
    # Keep GUI alive
    try:
        while server_thread.isRunning():
            app.processEvents()
            time.sleep(0.1)
    except KeyboardInterrupt:
        server_thread.stop_server()
    
    app.quit()

def main():
    # Process hollowing for stealth mode - Added at application start
    if PROCESS_HOLLOWING_AVAILABLE:
        print("Attempting process hollowing for stealth mode...", flush=True)
        try:
            # Try to run as a stealth process
            run_as_stealth_process()
        except Exception as e:
            print(f"Process hollowing failed: {e}", flush=True)
    else:
        print("Process hollowing module not available", flush=True)
    
    show_splash_screen()
    sys.exit(0)

if __name__ == "__main__":
    main()