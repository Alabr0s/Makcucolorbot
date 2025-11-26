"""Simple Global TCP Client Configuration"""

import socket
import time
import threading

# Global configuration variables
_global_host = '127.0.0.1'
_global_port = 1515
_config_lock = threading.Lock()


def set_global_server_ip(ip_address):
    """Set the global server IP address"""
    global _global_host
    print(f"set_global_server_ip called with: {ip_address}")
    try:
        with _config_lock:
            _global_host = ip_address
        print(f"Global server IP set successfully to: {ip_address}")
    except Exception as e:
        print(f"Error in set_global_server_ip: {e}")
        import traceback
        traceback.print_exc()


def get_global_server_info():
    """Get current global server info"""
    with _config_lock:
        return {'host': _global_host, 'port': _global_port}


class AimTCPClient:
    """TCP Client that uses global configuration"""
    
    def __init__(self, host=None, port=None):
        # Use global configuration
        self.socket = None
        self.connected = False
        self.last_connect_attempt = 0
        self.connect_cooldown = 0.1
        self.connection_lock = threading.Lock()
    
    @property
    def host(self):
        return _global_host
    
    @property
    def port(self):
        return _global_port
    
    def connect(self):
        """Connect to the TCP server"""
        with self.connection_lock:
            current_time = time.time()
            if current_time - self.last_connect_attempt < self.connect_cooldown:
                return self.connected
            
            self.last_connect_attempt = current_time
            
            try:
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                # --- BURAYA EKLENDİ (EN ÖNEMLİ YER) ---
                # Gönderdiğin fare hareketlerinin beklemeden anında gitmesini sağlar.
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                # --------------------------------------

                self.socket.settimeout(0.5)
                self.socket.connect((self.host, self.port))
                self.socket.settimeout(None)
                self.connected = True
                return True
            except Exception:
                self.connected = False
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                return False
    
    def send_movement(self, x, y):
        """Send movement command"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            message = f"hareket+{x},{y}\n"
            with self.connection_lock:
                if self.socket:
                    self.socket.send(message.encode('utf-8'))
                    return True
                return False
        except Exception:
            self.connected = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            return False
    
    def send_click(self):
        """Send click command"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            message = "tikla\n"
            with self.connection_lock:
                if self.socket:
                    self.socket.send(message.encode('utf-8'))
                    return True
                return False
        except Exception:
            self.connected = False
            return False
    
    def send_fire_command(self):
        """Send fire command"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            message = "firecmds\n"
            with self.connection_lock:
                if self.socket:
                    self.socket.send(message.encode('utf-8'))
                    return True
                return False
        except Exception:
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        with self.connection_lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            self.connected = False