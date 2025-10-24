import sys
import asyncio
import threading
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QRectF
from PyQt5.QtGui import (QFont, QPalette, QColor, QPainter, QBrush, QPen, 
                         QLinearGradient, QRadialGradient, QPainterPath, QRegion)
from makcu import create_async_controller, MouseButton
import socket
import concurrent.futures
from colorama import init, Fore

init(autoreset=True)

class Bubble:
    """Hareketli mor bubble sınıfı"""
    def __init__(self, x, y, size, speed_x, speed_y):
        self.x = x
        self.y = y
        self.size = size
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.opacity = random.uniform(0.3, 0.7)
    
    def update(self, width, height):
        """Bubble pozisyonunu güncelle"""
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Sınırları kontrol et ve yön değiştir
        if self.x <= 0 or self.x >= width - self.size:
            self.speed_x *= -1
        if self.y <= 0 or self.y >= height - self.size:
            self.speed_y *= -1
            
        # Sınırlar içinde tut
        self.x = max(0, min(width - self.size, self.x))
        self.y = max(0, min(height - self.size, self.y))

class ServerWorker(QObject):
    """Server işlemlerini ayrı thread'de çalıştır"""
    status_updated = pyqtSignal(str, str, str, int)  # makcu_status, server_ip, system_status, clients
    
    def __init__(self):
        super().__init__()
        self.host = '0.0.0.0'
        self.port = 1515
        self.makcu = None
        self.running = False
        self.makcu_connected = False
        self.client_connections = set()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.command_tasks = set()
        
    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "192.168.1.100"
    
    async def initialize_makcu(self):
        """Makcu bağlantısını başlat"""
        try:
            self.makcu = await create_async_controller(debug=False, auto_reconnect=True)
            if self.makcu:
                self.makcu_connected = True
                return True
            else:
                self.makcu_connected = False
                return False
        except Exception as e:
            self.makcu_connected = False
            return False
    
    async def check_makcu_connection(self):
        """Her 2 saniyede bir Makcu bağlantısını kontrol et"""
        while self.running:
            try:
                if not self.makcu_connected:
                    success = await self.initialize_makcu()
                    if success:
                        self.emit_status_update()
                else:
                    try:
                        if not self.makcu:
                            self.makcu_connected = False
                            self.emit_status_update()
                    except:
                        self.makcu_connected = False
                        self.makcu = None
                        self.emit_status_update()
                
                await asyncio.sleep(2)
                
            except Exception as e:
                await asyncio.sleep(2)
    
    def emit_status_update(self):
        """Status güncellemesini GUI'ye gönder"""
        makcu_status = "BAĞLI" if self.makcu_connected else "BAĞLANTI BEKLENİYOR"
        server_ip = self.get_local_ip()
        system_status = "KULLANIMA HAZIR" if self.makcu_connected else "HAZIRLANIYOR..."
        active_clients = len(self.client_connections)
        
        self.status_updated.emit(makcu_status, server_ip, system_status, active_clients)
    
    async def click(self, writer):
        """Anlık asenkron tıklama işlemi"""
        try:
            if not self.makcu:
                writer.write(b"ERROR: Makcu bagli degil\n")
                await writer.drain()
                return
            
            await self.makcu.click(MouseButton.LEFT)
            await self.makcu.release(MouseButton.LEFT)
            
            writer.write(b"OK: Tiklama basarili\n")
            await writer.drain()
            
        except Exception as e:
            response = f"ERROR: {e}\n"
            writer.write(response.encode())
            await writer.drain()
    
    async def move(self, writer, x, y):
        """Anlık asenkron hareket işlemi"""
        try:
            if not self.makcu:
                writer.write(b"ERROR: Makcu bagli degil\n")
                await writer.drain()
                return
            
            await self.makcu.move(x, y)
            writer.write(b"OK: Hareket basarili\n")
            await writer.drain()
            
        except Exception as e:
            response = f"ERROR: {e}\n"
            writer.write(response.encode())
            await writer.drain()
    
    async def process_command_async(self, command, writer):
        """Komutları asenkron olarak işle"""
        command = command.strip().lower()
        
        try:
            if command == "firecmds":
                await self.click(writer)
                
            elif command.startswith("hareket+"):
                try:
                    coords = command[8:]
                    x, y = map(int, coords.split(","))
                    await self.move(writer, x, y)
                except:
                    writer.write(b"ERROR: Gecersiz format\n")
                    await writer.drain()
            else:
                writer.write(b"ERROR: Bilinmeyen komut\n")
                await writer.drain()
                
        except Exception as e:
            try:
                response = f"ERROR: {e}\n"
                writer.write(response.encode())
                await writer.drain()
            except:
                pass
    
    def create_command_task(self, command, writer):
        """Her komut için ayrı task oluştur"""
        task = asyncio.create_task(self.process_command_async(command, writer))
        self.command_tasks.add(task)
        
        def remove_task(task):
            self.command_tasks.discard(task)
        
        task.add_done_callback(remove_task)
        return task
    
    async def handle_client(self, reader, writer):
        """Her client için ayrı handler"""
        self.client_connections.add(writer)
        client_addr = writer.get_extra_info('peername')
        
        self.emit_status_update()
        
        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if not data:
                        break
                    
                    command = data.decode('utf-8').strip()
                    if command:
                        self.create_command_task(command, writer)
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    break
                    
        except Exception as e:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            self.client_connections.discard(writer)
            self.emit_status_update()
    
    async def cleanup_tasks(self):
        """Tüm aktif task'ları temizle"""
        if self.command_tasks:
            for task in list(self.command_tasks):
                task.cancel()
            
            if self.command_tasks:
                await asyncio.gather(*self.command_tasks, return_exceptions=True)
            
            self.command_tasks.clear()
    
    async def start_server(self):
        """Server'ı başlat"""
        try:
            server = await asyncio.start_server(self.handle_client, self.host, self.port)
            
            self.running = True
            
            # Makcu bağlantı kontrolünü başlat
            connection_task = asyncio.create_task(self.check_makcu_connection())
            
            # İlk durum güncellemesi
            self.emit_status_update()
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            pass
        finally:
            self.running = False
            await self.cleanup_tasks()
            
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
            
            if self.makcu:
                try:
                    await self.makcu.disconnect()
                except:
                    pass
    
    async def start(self):
        """Ana başlatma fonksiyonu"""
        # İlk bağlantı denemesi
        await self.initialize_makcu()
        
        # Server'ı başlat
        await self.start_server()

class DefendingStoreGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_worker = ServerWorker()
        self.server_thread = None
        
        # Bubble'lar için liste
        self.bubbles = []
        self.init_bubbles()
        
        self.setup_ui()
        self.setup_connections()
        self.start_server()
        
        # Bubble animasyon timer'ı
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.update_bubbles)
        self.bubble_timer.start(50)  # 50ms'de bir güncelle (20 FPS)
    
    def init_bubbles(self):
        """Bubble'ları başlat - daha çok ve çeşitli boyutlarda"""
        for _ in range(25):  # Daha fazla bubble
            x = random.randint(0, 800)
            y = random.randint(0, 400) 
            size = random.randint(15, 80)
            speed_x = random.uniform(-1.5, 1.5)
            speed_y = random.uniform(-1.5, 1.5)
            self.bubbles.append(Bubble(x, y, size, speed_x, speed_y))
    
    def update_bubbles(self):
        """Bubble'ları güncelle ve yeniden çiz"""
        for bubble in self.bubbles:
            bubble.update(self.width(), self.height())
        self.update()  # Pencereyi yeniden çiz
    
    def paintEvent(self, event):
        """Tamamen özel oval pencere ve bubble çizimi"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Oval pencere şekli oluştur
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, 40, 40)  # Gerçek oval köşeler
        
        # Pencere arka plan gradyanı
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(20, 10, 35, 240))
        gradient.setColorAt(0.5, QColor(35, 20, 50, 240))
        gradient.setColorAt(1, QColor(25, 15, 40, 240))
        
        painter.fillPath(path, QBrush(gradient))
        
        # Oval kenarlık
        pen = QPen(QColor(138, 43, 226, 120))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Çok şeffaf bubble'lar
        painter.setPen(Qt.NoPen)
        for bubble in self.bubbles:
            color = QColor(138, 43, 226, int(bubble.opacity * 25))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(bubble.x), int(bubble.y), int(bubble.size), int(bubble.size))
    
    def setup_ui(self):
        """Tamamen yeni oval pencere tasarımı"""
        self.setWindowTitle("DefendingStore")
        self.setGeometry(100, 100, 800, 500)
        
        # Şeffaf pencere - tamamen özel çizim
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ana widget - şeffaf
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(40)
        main_layout.setContentsMargins(80, 120, 80, 120)
        
        # DefendingStore başlık
        self.create_DefendingStore_title(main_layout)
        
        # Kapatma butonu
        self.create_close_button()
        
        # Bilgi kartları
        self.create_info_cards(main_layout)
    
    def create_DefendingStore_title(self, parent_layout):
        """Neon efektli DefendingStore başlığı"""
        DefendingStore_label = QLabel("DefendingStore")
        DefendingStore_label.setAlignment(Qt.AlignCenter)
        
        # Neon glow efekti
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setBlurRadius(30)
        glow_effect.setColor(QColor(157, 78, 221, 180))
        glow_effect.setOffset(0, 0)
        DefendingStore_label.setGraphicsEffect(glow_effect)
        
        DefendingStore_label.setStyleSheet("""
            QLabel {
                color: #c77dff;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 64px;
                font-weight: 700;
                letter-spacing: 12px;
                background: transparent;
                border: none;
            }
        """)
        
        parent_layout.addWidget(DefendingStore_label)
    
    def create_close_button(self):
        """Kapatma butonu oluştur - sağ üst köşede"""
        close_button = QLabel("✕")
        close_button.setParent(self)
        close_button.setGeometry(self.width() - 40, 15, 30, 30)
        close_button.setAlignment(Qt.AlignCenter)
        
        # Kapatma butonu stili
        close_button.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-family: 'Arial', sans-serif;
                font-size: 18px;
                font-weight: bold;
                background: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 15px;
                padding: 5px;
            }
            QLabel:hover {
                background: rgba(255, 107, 107, 0.2);
                color: #ff4757;
            }
        """)
        
        # Glow efekti
        close_glow = QGraphicsDropShadowEffect()
        close_glow.setBlurRadius(10)
        close_glow.setColor(QColor(255, 107, 107, 100))
        close_glow.setOffset(0, 0)
        close_button.setGraphicsEffect(close_glow)
        
        # Mouse events
        close_button.mousePressEvent = self.close_button_clicked
        close_button.show()
        
        # Referansı sakla
        self.close_button = close_button
    
    def close_button_clicked(self, event):
        """Kapatma butonu tıklandığında"""
        self.close()
    
    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde kapatma butonunu yeniden konumlandır"""
        super().resizeEvent(event)
        if hasattr(self, 'close_button'):
            self.close_button.setGeometry(self.width() - 40, 15, 30, 30)
    
    def create_info_cards(self, parent_layout):
        """Bilgi bölümünü oluştur - şeffaf kartlar"""
        info_frame = QFrame()
        info_frame.setStyleSheet("background: transparent; border: none;")
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(20)
        info_layout.setContentsMargins(40, 30, 40, 30)
        
        # Version bilgisi
        self.version_label = QLabel("Version 1.3 [BETA] • OemUsr")
        self.version_label.setAlignment(Qt.AlignCenter)
        
        version_glow = QGraphicsDropShadowEffect()
        version_glow.setBlurRadius(15)
        version_glow.setColor(QColor(255, 215, 0, 120))
        version_glow.setOffset(0, 0)
        self.version_label.setGraphicsEffect(version_glow)
        
        self.version_label.setStyleSheet("""
            QLabel {
                color: #ffd700;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 18px;
                font-weight: 400;
                letter-spacing: 2px;
                background: transparent;
                padding: 10px 20px;
            }
        """)
        
        # Makcu durumu
        self.makcu_status_label = QLabel("Makcu • BAĞLANTI BEKLENİYOR")
        self.makcu_status_label.setAlignment(Qt.AlignCenter)
        
        makcu_glow = QGraphicsDropShadowEffect()
        makcu_glow.setBlurRadius(20)
        makcu_glow.setColor(QColor(255, 255, 100, 100))
        makcu_glow.setOffset(0, 0)
        self.makcu_status_label.setGraphicsEffect(makcu_glow)
        
        self.makcu_status_label.setStyleSheet("""
            QLabel {
                color: #ffff64;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 20px;
                font-weight: 500;
                letter-spacing: 2px;
                background: transparent;
                padding: 15px 25px;
            }
        """)
        
        # Server durumu
        self.server_status_label = QLabel("Server • ÇALIŞIYOR")
        self.server_status_label.setAlignment(Qt.AlignCenter)
        
        server_glow = QGraphicsDropShadowEffect()
        server_glow.setBlurRadius(20)
        server_glow.setColor(QColor(157, 78, 221, 120))
        server_glow.setOffset(0, 0)
        self.server_status_label.setGraphicsEffect(server_glow)
        
        self.server_status_label.setStyleSheet("""
            QLabel {
                color: #9d4edd;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 20px;
                font-weight: 500;
                letter-spacing: 2px;
                background: transparent;
                padding: 15px 25px;
            }
        """)
        
        info_layout.addWidget(self.version_label)
        info_layout.addWidget(self.makcu_status_label)
        info_layout.addWidget(self.server_status_label)
        
        parent_layout.addWidget(info_frame)
    
    def setup_connections(self):
        """Sinyal bağlantılarını kurar"""
        self.server_worker.status_updated.connect(self.update_status)
        
        # Status güncelleme timer'ı
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.request_status_update)
        self.status_timer.start(2000)  # Her 2 saniyede bir güncelle
    
    def update_status(self, makcu_status, server_ip, system_status, active_clients):
        """Status bilgilerini neon efekti ile güncelle"""
        # Makcu durumu güncelleme - Türkçe durumlar
        if makcu_status == "BAĞLI":
            makcu_text = "Makcu • BAĞLI"
            
            # Yeşil neon glow
            makcu_glow = QGraphicsDropShadowEffect()
            makcu_glow.setBlurRadius(25)
            makcu_glow.setColor(QColor(100, 255, 100, 150))
            makcu_glow.setOffset(0, 0)
            self.makcu_status_label.setGraphicsEffect(makcu_glow)
            
            self.makcu_status_label.setStyleSheet("""
                QLabel {
                    color: #64ff64;
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 20px;
                    font-weight: 500;
                    letter-spacing: 2px;
                    background: transparent;
                    padding: 15px 25px;
                }
            """)
        else:
            makcu_text = "Makcu • BAĞLANTI BEKLENİYOR"
            
            # Sarı neon glow
            makcu_glow = QGraphicsDropShadowEffect()
            makcu_glow.setBlurRadius(20)
            makcu_glow.setColor(QColor(255, 255, 100, 100))
            makcu_glow.setOffset(0, 0)
            self.makcu_status_label.setGraphicsEffect(makcu_glow)
            
            self.makcu_status_label.setStyleSheet("""
                QLabel {
                    color: #ffff64;
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 20px;
                    font-weight: 500;
                    letter-spacing: 2px;
                    background: transparent;
                    padding: 15px 25px;
                }
            """)
        
        self.makcu_status_label.setText(makcu_text)
    
    def start_server(self):
        """Server'ı başlat"""
        if not self.server_thread or not self.server_thread.is_alive():
            
            def run_server():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.server_worker.start())
            
            self.server_thread = threading.Thread(target=run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
    
    def request_status_update(self):
        """Status güncellemesi iste"""
        if hasattr(self.server_worker, 'emit_status_update'):
            self.server_worker.emit_status_update()
    
    def closeEvent(self, event):
        """Uygulama kapatılırken server'ı durdur"""
        self.server_worker.running = False
        event.accept()
    
    def mousePressEvent(self, event):
        """Fare ile pencereyi taşıma için"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Pencereyi sürükle"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_start_position'):
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Uygulama ikonu ve başlık
    app.setApplicationName("DefendingStore")
    app.setApplicationVersion("1.3 [BETA]")
    
    # Ana pencere
    window = DefendingStoreGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
