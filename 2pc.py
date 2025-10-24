import sys
import asyncio
import threading
import random
import math
import socket
import concurrent.futures
from colorama import init, Fore, Style, Back
import time
import os

# Windows için ctypes modülünü içe aktar
try:
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
except ImportError:
    ctypes = None

init(autoreset=True)

class ServerWorker:
    """Server işlemlerini yönetir"""
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 1515
        self.running = False
        self.client_connections = set()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.command_tasks = set()
        self.makcu_connected = False
        self.makcu = None
        self.set_console_title()
        
    def set_console_title(self):
        """Konsol başlığını ayarla"""
        title = "Defending Store | https://defendingstore.com"
        if os.name == 'nt' and ctypes:
            # Windows için başlık ayarlama
            try:
                ctypes.windll.kernel32.SetConsoleTitleW(title)
            except Exception:
                pass  # Başlık ayarlanamazsa devam et
        else:
            # Diğer sistemler için başlık ayarlama
            try:
                sys.stdout.write(f'\033]0;{title}\a')
                sys.stdout.flush()
            except Exception:
                pass  # Başlık ayarlanamazsa devam et
        
    def clear_screen(self):
        """Konsolu temizle"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "192.168.1.100"
    
    async def initialize_makcu(self):
        """Makcu bağlantısını başlat - örnek/mock bağlantı"""
        try:
            # Burada gerçek bir makcu bağlantısı başlatılabilir
            # Şimdilik mock bir bağlantı simulasyonu yapıyoruz
            print(f"{Fore.YELLOW}Makcu bağlantısı deneniyor...")
            await asyncio.sleep(1)  # Bağlantı süresi simulasyonu
            
            # Mock başarılı bağlantı
            self.makcu_connected = True
            print(f"{Fore.GREEN}Makcu bağlantısı başarılı!")
            return True
        except Exception as e:
            self.makcu_connected = False
            print(f"{Fore.RED}Makcu bağlantı hatası: {e}")
            return False
    
    async def check_makcu_connection(self):
        """Her 5 saniyede bir Makcu bağlantısını kontrol et"""
        while self.running:
            try:
                if not self.makcu_connected:
                    success = await self.initialize_makcu()
                    if success:
                        self.display_status()
                else:
                    # Bağlantı varsa, bağlantı durumunu kontrol et
                    # Burada gerçek bağlantı kontrolü yapılabilir
                    pass
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"{Fore.RED}Bağlantı kontrol hatası: {e}")
                await asyncio.sleep(5)
    
    def display_status(self):
        """Durum bilgisini göster"""
        self.clear_screen()
        self.set_console_title()  # Başlığı güncelle
        ip_address = self.get_local_ip()
        client_count = len(self.client_connections)
        connection_status = f"{Fore.GREEN}BAĞLI" if self.makcu_connected else f"{Fore.YELLOW}BAĞLANTI BEKLENİYOR"
        system_status = f"{Fore.GREEN}KULLANIMA HAZIR" if self.makcu_connected else f"{Fore.YELLOW}HAZIRLANIYOR..."
        
        print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT}=== DEFENDING STORE SERVER ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}Website: {Fore.MAGENTA}https://defendingstore.com")
        print(f"{Fore.CYAN}IP Address: {Fore.WHITE}{ip_address}")
        print(f"{Fore.CYAN}Port: {Fore.WHITE}{self.port}")
        print(f"{Fore.CYAN}Makcu Status: {connection_status}")
        print(f"{Fore.CYAN}System Status: {system_status}")
        print(f"{Fore.CYAN}Active Clients: {Fore.WHITE}{client_count}")
        print(f"{Fore.CYAN}Server Status: {Fore.GREEN}RUNNING")
        print("=" * 40)
    
    async def click(self, writer):
        """Anlık asenkron tıklama işlemi"""
        try:
            if not self.makcu_connected:
                writer.write(b"ERROR: Makcu bagli degil\n")
                await writer.drain()
                return
            
            # Mock tıklama işlemi
            print(f"{Fore.YELLOW}Tıklama işlemi gerçekleştirildi")
            writer.write(b"OK: Tiklama basarili\n")
            await writer.drain()
            
        except Exception as e:
            response = f"ERROR: {e}\n"
            writer.write(response.encode())
            await writer.drain()
    
    async def move(self, writer, x, y):
        """Anlık asenkron hareket işlemi"""
        try:
            if not self.makcu_connected:
                writer.write(b"ERROR: Makcu bagli degil\n")
                await writer.drain()
                return
            
            # Mock hareket işlemi
            print(f"{Fore.YELLOW}Hareket işlemi: X={x}, Y={y}")
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
        print(f"{Fore.GREEN}Yeni client bağlandı: {client_addr}")
        
        self.display_status()
        
        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if not data:
                        break
                    
                    command = data.decode('utf-8').strip()
                    if command:
                        print(f"{Fore.CYAN}Gelen komut: {Fore.WHITE}{command}")
                        self.display_status()  # Ekranı temizle ve yeniden göster
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
            print(f"{Fore.RED}Client bağlantısı kesildi: {client_addr}")
            self.display_status()
    
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
            print(f"{Fore.GREEN}DEFENDING STORE Server başlatıldı!")
            print(f"{Fore.CYAN}Dinlenen adres: {Fore.WHITE}{self.host}:{self.port}")
            
            self.running = True
            
            # Makcu bağlantı kontrolünü başlat
            connection_task = asyncio.create_task(self.check_makcu_connection())
            
            # İlk durum güncellemesi
            self.display_status()
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            print(f"{Fore.RED}Server başlatma hatası: {e}")
        finally:
            self.running = False
            await self.cleanup_tasks()
            
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
    
    async def start(self):
        """Ana başlatma fonksiyonu"""
        # İlk bağlantı denemesi
        await self.initialize_makcu()
        
        # Server'ı başlat
        await self.start_server()

def main():
    # Konsolu temizle
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{Back.BLUE}{Fore.WHITE}{Style.BRIGHT}=== DEFENDING STORE ==={Style.RESET_ALL}")
    print(f"{Fore.CYAN}Website: {Fore.MAGENTA}https://defendingstore.com")
    print(f"{Fore.YELLOW}Server başlatılıyor...")
    
    # Server worker oluştur
    server_worker = ServerWorker()
    
    # Async event loop başlat
    try:
        asyncio.run(server_worker.start())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Server kapatılıyor...")
        server_worker.running = False
    except Exception as e:
        print(f"{Fore.RED}Hata oluştu: {e}")

if __name__ == "__main__":
    main()