import sys
import asyncio
import threading
import socket
import concurrent.futures
from makcu import create_async_controller, MouseButton
from colorama import init, Fore, Style
import time

init(autoreset=True)

class ServerWorker:
    """Server işlemleri için worker sınıfı"""
    
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 1515
        self.makcu = None
        self.running = False
        self.makcu_connected = False
        self.client_connections = set()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.command_tasks = set()
        self.status_callback = None
        
    def set_status_callback(self, callback):
        """Set callback function for status updates"""
        self.status_callback = callback
        
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
        """Status güncellemesini terminale gönder"""
        makcu_status = "BAĞLI" if self.makcu_connected else "BAĞLANTI BEKLENİYOR"
        server_ip = self.get_local_ip()
        system_status = "KULLANIMA HAZIR" if self.makcu_connected else "HAZIRLANIYOR..."
        active_clients = len(self.client_connections)
        
        if self.status_callback:
            self.status_callback(makcu_status, server_ip, system_status, active_clients)
    
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
        
        print(f"{Fore.GREEN}[+] New Connecting: {client_addr}")
        self.emit_status_update()
        
        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if not data:
                        break
                    
                    command = data.decode('utf-8').strip()
                    if command:
                        #print(f"{Fore.CYAN}[*] Komut alındı: {command}")
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
            print(f"{Fore.YELLOW}[-] Connecting Closed: {client_addr}")
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
            
            print(f"{Fore.MAGENTA}=== Defending Store SERVER ===")
            print(f"{Fore.BLUE}Server Started: {self.host}:{self.port}")
            print(f"{Fore.BLUE}Makcu Status: { 'Connected' if self.makcu_connected else 'connect waiting...' }")
            print(f"{Fore.BLUE}IP: {self.get_local_ip()}")
            print(f"{Fore.MAGENTA}======================")
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            print(f"{Fore.RED}[!] Server Error: {e}")
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

class TerminalInterface:
    def __init__(self):
        self.server_worker = ServerWorker()
        self.server_worker.set_status_callback(self.update_status)
        self.server_thread = None
    
    def update_status(self, makcu_status, server_ip, system_status, active_clients):
        """Terminalde durum güncellemesi göster"""
        status_color = Fore.GREEN if makcu_status == "BAĞLI" else Fore.YELLOW
        print(f"\n{Fore.CYAN}[DURUM GÜNCELLEMESİ]")
        print(f"{Fore.WHITE}Makcu: {status_color}{makcu_status}")
        print(f"{Fore.WHITE}Server IP: {Fore.WHITE}{server_ip}")
        print(f"{Fore.WHITE}Sistem: {Fore.WHITE}{system_status}")
        print(f"{Fore.WHITE}Aktif Bağlantılar: {Fore.WHITE}{active_clients}")
        print(f"{Fore.CYAN}{'='*30}")
    
    def start_server(self):
        """Server'ı başlat"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.server_worker.start())
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def run(self):
        """Ana uygulama döngüsü"""
        print(f"{Fore.MAGENTA}Defending Store Terminal Server")
        print(f"{Fore.MAGENTA}======================")
        print(f"{Fore.WHITE}Server başlatılıyor...")
        
        self.start_server()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Server kapatılıyor...")
            self.server_worker.running = False
            sys.exit(0)

def main():
    # Uygulama ikonu ve başlık
    app = TerminalInterface()
    app.run()

if __name__ == "__main__":
    main()
