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
    """TCP UDP Client that uses global configuration"""
    
    def __init__(self, host=None, port=None):
        # Use global configuration
        self.socket = None
        self.udp_socket = None
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
        """Connect to the TCP server and initialize UDP"""
        with self.connection_lock:
            current_time = time.time()
            if current_time - self.last_connect_attempt < self.connect_cooldown:
                return self.connected
            
            self.last_connect_attempt = current_time
            
            try:
                if self.socket:
                    try: self.socket.close()
                    except: pass
                if self.udp_socket:
                    try: self.udp_socket.close()
                    except: pass
                
                # TCP Connection
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.socket.settimeout(0.5)
                self.socket.connect((self.host, self.port))
                self.socket.settimeout(None)
                
                # UDP Connection
                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                self.connected = True
                return True
            except Exception:
                self.connected = False
                if self.socket:
                    try: self.socket.close()
                    except: pass
                    self.socket = None
                if self.udp_socket:
                    try: self.udp_socket.close()
                    except: pass
                    self.udp_socket = None
                return False
    
    def send_movement(self, x, y):
        """Send movement command via UDP if available"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            message = f"hareket+{x},{y}\n"
            
            # UDP Priority for movement
            if self.udp_socket:
                try:
                    self.udp_socket.sendto(message.encode('utf-8'), (self.host, self.port))
                    return True
                except:
                    pass
            
            # Fallback to TCP
            with self.connection_lock:
                if self.socket:
                    self.socket.send(message.encode('utf-8'))
                    return True
                return False
        except Exception:
            self.connected = False
            if self.socket:
                try: self.socket.close()
                except: pass
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
                try: self.socket.close()
                except: pass
                self.socket = None
            if self.udp_socket:
                try: self.udp_socket.close()
                except: pass
                self.udp_socket = None
            self.connected = False

# Global singleton instance
_global_tcp_client = None
_client_lock = threading.Lock()

def get_global_tcp_client():
    """
    Get or create the global TCP client instance.
    This ensures all parts of the app use the same connection.
    """
    global _global_tcp_client
    with _client_lock:
        if _global_tcp_client is None:
            _global_tcp_client = AimTCPClient()
        return _global_tcp_client