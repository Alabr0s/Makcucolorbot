import sys
import asyncio
import socket
import logging
import json
import os
import math
import random
from collections import deque
from datetime import datetime

# TUI ve Görsel Kütüphaneler
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box
from colorama import init

# Makcu HW Import
try:
    from makcu import create_async_controller, MouseButton
except ImportError:
    class MouseButton: LEFT = 0; RIGHT = 1; MIDDLE = 2

init(autoreset=True)
console = Console()

# ==========================================
#   YAPILANDIRMA YÖNETİCİSİ (CONFIG)
# ==========================================
DEFAULT_CONFIG = {
    "server": {
        "port": 1515,
        "log_buffer_size": 20,
        "ui_refresh_fps": 20
    },
    "humanizer": {
        "bezier_threshold": 13,     # Bu değerden küçük hareketlerde bezier devre dışı
        "min_speed": 0.005,         # Döngü arası minimum bekleme
        "max_speed": 0.015,         # Döngü arası maksimum bekleme
        "curve_variance": 40        # Eğrinin ne kadar sapacağı (rastgelelik gücü)
    }
}

class ConfigManager:
    @staticmethod
    def load():
        if not os.path.exists("config.json"):
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG

# --- GLOBAL DURUM YÖNETİMİ ---
class AppState:
    config = ConfigManager.load()
    logs = deque(maxlen=config["server"]["log_buffer_size"])
    connected_clients = 0
    makcu_connected = False
    server_ip = "..."
    system_status = "INITIALIZING"
    last_move = "N/A"
    total_commands = 0
    running = True 
       
    @staticmethod
    def add_log(message, category="SYS", level="INFO", save_to_file=True):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if save_to_file:
            logger = logging.getLogger("SystemCore")
            if level == "ERROR": logger.error(f"[{category}] {message}")
            else: logger.info(f"[{category}] {message}")

        colors = {"ERROR": "bold red", "NET": "cyan", "ALGO": "magenta", "HW": "yellow", "SUCCESS": "bold green"}
        style = colors.get(category, "white")
        AppState.logs.append(f"[dim]{timestamp}[/] [bold {style}][{category}][/] {message}")

# --- LOGLAMA SİSTEMİ ---
class TUILogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            cat = "ERROR" if record.levelno >= logging.ERROR else "SYS"
            AppState.add_log(msg, category=cat, level=record.levelname, save_to_file=False)
        except Exception: self.handleError(record)

def setup_logging():
    tui_handler = TUILogHandler()
    tui_handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO, handlers=[tui_handler])

# --- OYUN SUNUCUSU VE HAREKET MANTIĞI ---
class GameServer:
    def __init__(self):
        self.makcu = None
        self.client_connections = set()
        self.human_cfg = AppState.config.get("humanizer", DEFAULT_CONFIG["humanizer"])

    async def initialize_makcu(self):
        try:
            AppState.system_status = "SCANNING BUS"
            self.makcu = await create_async_controller(debug=False, auto_reconnect=True) 
            if self.makcu:
                AppState.makcu_connected, AppState.system_status = True, "OPERATIONAL"
                AppState.add_log("Controller Ready.", "HW", "SUCCESS")
            else:
                AppState.makcu_connected = False
                AppState.add_log("Controller Not Found.", "HW", "ERROR")
        except Exception as e:
            AppState.add_log(f"Driver Error: {e}", "HW", "ERROR")

    # --- BEZIER MATEMATİK FONKSİYONLARI ---
    def cubic_bezier(self, t, p0, p1, p2, p3):
        """
        3. Derece Bezier Formülü: B(t) = (1-t)^3*P0 + 3*(1-t)^2*t*P1 + 3*(1-t)*t^2*P2 + t^3*P3
        """
        return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3

    def ease_out_quart(self, x):
        """
        Hızlı başlangıç, yavaş bitiş için easing fonksiyonu.
        İnsansı nişan alma hissi verir.
        """
        return 1 - pow(1 - x, 4)

    async def execute_move(self, target_x, target_y):
        if not self.makcu: return
        
        AppState.last_move = f"{target_x}, {target_y}"
        AppState.total_commands += 1
        
        # 1. Mesafe Hesapla
        distance = math.hypot(target_x, target_y)
        threshold = self.human_cfg["bezier_threshold"]

        # --- DURUM 1: KISA MESAFE (MİKRO HAREKET) ---
        # Eğer hareket çok küçükse bezier hesaplamaya gerek yok, direkt git.
        if distance < threshold:
            await self.makcu.move(int(target_x), int(target_y))
            return

        # --- DURUM 2: UZUN MESAFE (İNSANSI BEZIER) ---
        
        # Başlangıç (0,0) çünkü komutlar relatif geliyor
        start_point = (0, 0)
        end_point = (target_x, target_y)

        # Kontrol Noktaları (Control Points) Oluşturma
        # Dümdüz bir çizgi yerine, yolun 1/3'ünde ve 2/3'ünde rastgele sapmalar oluşturuyoruz.
        variance = min(distance * 0.2, self.human_cfg["curve_variance"]) # Mesafe arttıkça sapma artar ama limitli
        
        # Rastgelelik (Noise) ekle
        rx1 = random.randint(int(-variance), int(variance))
        ry1 = random.randint(int(-variance), int(variance))
        rx2 = random.randint(int(-variance), int(variance))
        ry2 = random.randint(int(-variance), int(variance))

        # P1 ve P2 noktalarını hesapla
        p1 = (target_x * 0.3 + rx1, target_y * 0.3 + ry1)
        p2 = (target_x * 0.6 + rx2, target_y * 0.6 + ry2)

        # Adım Sayısı (Step Count)
        # Daha uzun mesafe = daha fazla adım (daha yumuşak hareket)
        steps = int(distance / 5) # Her 5 piksel için 1 adım
        if steps < 5: steps = 5
        
        current_x, current_y = 0, 0 # Şu an nerede olduğumuzu takip ediyoruz (Relatif kümülatif)

        for i in range(1, steps + 1):
            t = i / steps
            
            # Easing uygula (Doğrusal zaman yerine bükülmüş zaman)
            # t değerini manipüle ederek başlangıçta hızlı, sonda yavaş olmasını sağlıyoruz
            eased_t = self.ease_out_quart(t)

            # Bezier üzerindeki yeni konumu bul
            next_x = self.cubic_bezier(eased_t, start_point[0], p1[0], p2[0], end_point[0])
            next_y = self.cubic_bezier(eased_t, start_point[1], p1[1], p2[1], end_point[1])

            # Hardware'e sadece "farkı" (delta) gönderiyoruz
            delta_x = int(next_x - current_x)
            delta_y = int(next_y - current_y)

            if delta_x != 0 or delta_y != 0:
                await self.makcu.move(delta_x, delta_y)
                current_x += delta_x
                current_y += delta_y
            
            # Hız kontrolü (Rastgele gecikme ekleyerek robotik hissi kır)
            # Hızlı hareketlerde bekleme süresi azalır
            sleep_time = random.uniform(self.human_cfg["min_speed"], self.human_cfg["max_speed"])
            await asyncio.sleep(sleep_time)

        # Yuvarlama hatalarını temizle (Kalan son pikselleri tamamla)
        remain_x = int(target_x - current_x)
        remain_y = int(target_y - current_y)
        
        if remain_x != 0 or remain_y != 0:
            await self.makcu.move(remain_x, remain_y)

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        self.client_connections.add(writer)
        AppState.connected_clients = len(self.client_connections)
        AppState.add_log(f"New client: {addr}", "NET", "INFO")

        try:
            while AppState.running:
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=15.0)
                    if not data: 
                        break
                    
                    raw_data = data.decode('utf-8').strip()
                    commands = raw_data.split('\n')
                    
                    for cmd in commands:
                        cmd = cmd.lower().strip()
                        if not cmd: continue
                        
                        if cmd == "firecmds":
                            await self.makcu.click(MouseButton.LEFT)
                            await self.makcu.release(MouseButton.LEFT)
                        elif cmd.startswith("hareket+"):
                            try:
                                coords = cmd.split('+')[1]
                                x, y = map(int, coords.split(','))
                                await self.execute_move(x, y)
                            except Exception: continue
                        
                        writer.write(b"OK\n")
                        await writer.drain()

                except asyncio.TimeoutError:
                    continue 
                except (ConnectionResetError, BrokenPipeError):
                    break
        except Exception as e:
            AppState.add_log(f"Client Exception: {e}", "SYS", "ERROR")
        finally:
            self.client_connections.discard(writer)
            AppState.connected_clients = len(self.client_connections)
            writer.close()
            try:
                await writer.wait_closed()
            except: pass
            AppState.add_log(f"Disconnected: {addr}", "NET", "INFO")

    class UDPProtocol(asyncio.DatagramProtocol):
        def __init__(self, game_server):
            self.game_server = game_server

        def connection_made(self, transport):
            self.transport = transport
            AppState.add_log("UDP Transport Established", "NET", "SUCCESS")

        def datagram_received(self, data, addr):
            try:
                message = data.decode('utf-8').strip()
                lines = message.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        asyncio.create_task(self.game_server.process_udp_command(line))
            except Exception:
                pass

    async def process_udp_command(self, cmd):
        cmd = cmd.lower().strip()
        if not cmd: return
        
        try:
            if cmd == "firecmds":
                if self.makcu:
                    await self.makcu.click(MouseButton.LEFT)
                    await self.makcu.release(MouseButton.LEFT)
            elif cmd.startswith("hareket+"):
                try:
                    coords = cmd.split('+')[1]
                    x, y = map(int, coords.split(','))
                    await self.execute_move(x, y)
                except Exception: pass
        except Exception:
            pass

    async def start(self):
        await self.initialize_makcu()
        AppState.server_ip = socket.gethostbyname(socket.gethostname())
        try:
            # TCP Server
            server = await asyncio.start_server(self.handle_client, '0.0.0.0', AppState.config["server"]["port"])
            AppState.add_log(f"TCP Listening on Port: {AppState.config['server']['port']}", "NET", "SUCCESS")
            
            # UDP Server
            loop = asyncio.get_running_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: self.UDPProtocol(self),
                local_addr=('0.0.0.0', AppState.config["server"]["port"])
            )
            AppState.add_log(f"UDP Listening on Port: {AppState.config['server']['port']}", "NET", "SUCCESS")

            async with server: 
                await server.serve_forever()
                
        except Exception as e: 
            AppState.add_log(f"Server Fatal Error: {e}", "SYS", "ERROR")

# ==========================================
#   TUI YÖNETİCİSİ
# ==========================================
class UIManager:
    def __init__(self):
        self.layout = Layout()
        self.init_layout()

    def init_layout(self):
        self.layout.split(
            Layout(name="header", size=1),
            Layout(name="main_body", ratio=1)
        )
        self.layout["main_body"].split_row(
            Layout(name="left_side", ratio=2),
            Layout(name="right_side", ratio=1)
        )
        self.layout["left_side"].split(
            Layout(name="status_bar", size=6),
            Layout(name="logs", ratio=1)
        )

    def generate_config_panel(self):
        cfg_table = Table(show_header=False, expand=True, box=None)
        cfg_table.add_column("Key", style="dim cyan")
        cfg_table.add_column("Value", style="bold yellow", justify="right")
        
        s_cfg = AppState.config["server"]
        h_cfg = AppState.config.get("humanizer", {})
        
        cfg_table.add_row("SERVER PORT", str(s_cfg["port"]))
        cfg_table.add_row("BEZIER THRESHOLD", str(h_cfg.get("bezier_threshold", 13)))
        cfg_table.add_row("CURVE VARIANCE", str(h_cfg.get("curve_variance", 20)))
        cfg_table.add_row("MODE", "SMART HUMANIZER") 
        
        return Panel(cfg_table, title="[bold white]LIVE CONFIG[/]", border_style="blue")

    def update(self):
        status_style = "bold white on dark_green" if AppState.makcu_connected else "bold white on red"
        self.layout["header"].update(Text(f" DEFENDING STORE | {AppState.server_ip} | {AppState.system_status} ", style=status_style, justify="center"))
        
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(ratio=1); grid.add_column(ratio=1)
        
        def mp(l, v, c): return Panel(f"[bold {c}]{v}[/]", title=f"[dim]{l}[/]", border_style="magenta", box=box.ROUNDED)
        
        grid.add_row(mp("CLIENTS", str(AppState.connected_clients), "cyan"), mp("OPS", str(AppState.total_commands), "yellow"))
        grid.add_row(mp("VECTOR", AppState.last_move, "white"), mp("HW", "READY" if AppState.makcu_connected else "LOST", "green" if AppState.makcu_connected else "red"))
        
        self.layout["status_bar"].update(grid)
        log_text = Text.from_markup("\n".join(AppState.logs))
        self.layout["logs"].update(Panel(log_text, title="[bold]SYSTEM EVENTS[/]", border_style="purple", box=box.HEAVY_EDGE))
        self.layout["right_side"].update(self.generate_config_panel())
        return self.layout

async def main():
    setup_logging()
    server = GameServer()
    ui = UIManager()
    
    refresh_rate = 1 / AppState.config["server"]["ui_refresh_fps"]
    
    with Live(ui.layout, refresh_per_second=AppState.config["server"]["ui_refresh_fps"], screen=True) as live:
        server_task = asyncio.create_task(server.start())
        
        try:
            while AppState.running:
                if server_task.done() and server_task.exception():
                    AppState.add_log(f"Server Task Crashed: {server_task.exception()}", "SYS", "ERROR")
                    break
                
                live.update(ui.update())
                await asyncio.sleep(refresh_rate)
        except (KeyboardInterrupt, asyncio.CancelledError):
            AppState.running = False
        finally:
            AppState.add_log("Shutting down...", "SYS", "INFO")
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
