import sys
import os
import threading
import time
import socket
import subprocess
import numpy as np
from PyQt5.QtWidgets import QPushButton, QLabel, QWidget
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QPixmap

# Required Libraries
try:
    import qtawesome as qta
except ImportError:
    print("Error: qtawesome library not found. Please install with 'pip install qtawesome'")
    sys.exit()

try:
    from pynput import keyboard
except ImportError:
    print("Error: pynput library not found. Please install with 'pip install pynput'")
    sys.exit()

try:
    import mss
except ImportError:
    print("Error: mss library not found. Please install with 'pip install mss'")
    sys.exit()

try:
    import cv2
except ImportError:
    print("Error: opencv-python library not found. Please install with 'pip install opencv-python'")
    sys.exit()


def key_event_to_string(event):
    key = event.key()
    text = event.text()
    if Qt.Key_Alt <= key <= Qt.Key_Hyper_R:
        key_map = {Qt.Key_Control: "Ctrl", Qt.Key_Shift: "Shift", Qt.Key_Alt: "Alt", Qt.Key_Meta: "Meta", Qt.Key_AltGr: "AltGr"}
        return key_map.get(key, "Unknown Modifier")
    elif Qt.Key_F1 <= key <= Qt.Key_F35:
        return f"F{key - Qt.Key_F1 + 1}"
    elif text.isalnum():
        return text.lower()
    else:
        key_map = {
            Qt.Key_Escape: "Esc", Qt.Key_Tab: "Tab", Qt.Key_Backspace: "Backspace",
            Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter", Qt.Key_Insert: "Insert",
            Qt.Key_Delete: "Delete", Qt.Key_Home: "Home", Qt.Key_End: "End",
            Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown", Qt.Key_CapsLock: "capslock",
            Qt.Key_Space: "space", Qt.Key_Up: "Up", Qt.Key_Down: "Down",
            Qt.Key_Left: "Left", Qt.Key_Right: "Right"
        }
        return key_map.get(key, "Unknown Key")


class KeyCaptureButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_capturing = False
        self._key_name = ""
        self.clicked.connect(self._start_capture)
        
        # Renk yöneticisi import et
        try:
            from controllers.theme_controller import WindowColorManager
            self.color_manager = WindowColorManager()
        except ImportError:
            self.color_manager = None
        
        self.setProperty('capturing', 'false')
        self.setText("Assign Key")

    def text(self):
        return self._key_name

    def setText(self, text):
        self._key_name = text
        super().setText(text if text else "Assign Key")
        self.setProperty('capturing', 'false')
        self._apply_theme_style()

    def _start_capture(self):
        self.is_capturing = True
        super().setText("Listening...")
        self.setProperty('capturing', 'true')
        self._apply_theme_style()
        self.setFocus()

    def _stop_capture(self, captured_key=None):
        if captured_key:
            self.setText(captured_key)
        else:
            super().setText(self.text() if self.text() else "Assign Key")
        self.is_capturing = False
        self.setProperty('capturing', 'false')
        self._apply_theme_style()
        self.clearFocus()
    
    def _apply_theme_style(self):
        """Apply theme style"""
        if self.color_manager:
            style = self.color_manager.get_style_for_component('key_capture_button')
            self.setStyleSheet(style)
            # Style'ı yeniden uygula
            self.style().unpolish(self)
            self.style().polish(self)
    
    def update_text(self):
        """Update button text (for theme compatibility)"""
        # Mevcut durumu koru ve tema stilini yeniden uygula
        self._apply_theme_style()

    def keyPressEvent(self, event):
        if self.is_capturing:
            key_name = key_event_to_string(event)
            if key_name != "Esc":
                self._stop_capture(captured_key=key_name)
            else:
                self._stop_capture()
            event.accept()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if self.is_capturing:
            self._stop_capture()
        super().focusOutEvent(event)


def get_application_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))





# Import new global TCP client
from tcp_client import AimTCPClient

# Legacy AimTCPClient class is now imported from tcp_client module
# This maintains backward compatibility while using the global configuration


class DriverProcess:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.process = None

    def is_running(self):
        driver_name = "driver.exe"
        try:
            command = f'tasklist /FI "IMAGENAME eq {driver_name}"'
            output = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL)
            return driver_name.encode() in output
        except (subprocess.CalledProcessError, Exception):
            return False

    def start(self):
        if self.is_running():
            return False
        if not os.path.exists(self.driver_path):
            return False
        try:
            self.process = subprocess.Popen([self.driver_path, 'key=NOL247FA31Y0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def stop(self):
        driver_name = "driver.exe"
        try:
            command = ["taskkill", "/F", "/IM", driver_name, "/T"]
            subprocess.run(command, capture_output=True, text=True, check=False)
        except Exception:
            pass
        self.process = None



class GlobalKeyListener(QThread):
    toggle_visibility_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.listener = None

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            self.listener = listener
            listener.join()

    def on_press(self, key):
        if key == keyboard.Key.insert:
            self.toggle_visibility_signal.emit()

    def stop(self):
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass


class WatermarkWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Animasyon değişkenleri
        self.rainbow_offset = 0
        self.opacity = 0.8
        
        # Resim yükleme
        self.image_path = None
        self.pixmap = None
        self.load_image()
        
        # Pencere ayarları
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Boyut ve pozisyon
        if self.pixmap:
            # Resim varsa resim boyutuna göre ayarla
            self.setFixedSize(self.pixmap.width(), self.pixmap.height())
        else:
            # Resim yoksa yazı için boyut (Daha küçük)
            self.setFixedSize(150, 25)
        
        # Ekranin sağ üst köşesine konumlandır
        try:
            from PyQt5.QtWidgets import QApplication
            screen_geo = QApplication.primaryScreen().geometry()
            x = screen_geo.width() - self.width() - 20  # Sağdan 20px boşluk
            y = 20  # Yukarıdan 20px boşluk
            self.move(x, y)
        except Exception:
            self.move(100, 100) # Fallback
        
        # Ana timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(80)

    def load_image(self):
        """Image loading - looks for files like logo.png, watermark.png"""
        possible_names = ['logo.png', 'watermark.png', 'icon.png', 'defending_store.png']
        
        for name in possible_names:
            if os.path.exists(name):
                self.image_path = name
                self.pixmap = QPixmap(name)
                # Resmi daha büyük boyuta ölçekle
                if not self.pixmap.isNull():
                    self.pixmap = self.pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                break

    def update_animation(self):
        # Rainbow renk animasyonu
        self.rainbow_offset += 3
        if self.rainbow_offset > 360:
            self.rainbow_offset = 0
        
        self.update()  # Widget'ı yeniden çiz

    def get_rainbow_color(self, offset=0):
        """Rainbow color with HSV to RGB conversion"""
        hue = (self.rainbow_offset + offset) % 360
        
        # HSV to RGB conversion
        c = 1.0  # Chroma (doygunluk)
        x = c * (1 - abs((hue / 60) % 2 - 1))
        m = 0
        
        if 0 <= hue < 60:
            r, g, b = c, x, 0
        elif 60 <= hue < 120:
            r, g, b = x, c, 0
        elif 120 <= hue < 180:
            r, g, b = 0, c, x
        elif 180 <= hue < 240:
            r, g, b = 0, x, c
        elif 240 <= hue < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    def paintEvent(self, event):
        """Custom drawing - image and/or text"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.pixmap and not self.pixmap.isNull():
            # Resim varsa gradient efekti ile çiz
            painter.setOpacity(self.opacity)
            
            # Gradient overlay oluştur
            from PyQt5.QtGui import QLinearGradient, QBrush
            
            # Soldan sağa gradient oluştur
            gradient = QLinearGradient(0, 0, self.pixmap.width(), 0)
            
            # Gradient renkleri (sürekli değişen rainbow)
            r1, g1, b1 = self.get_rainbow_color(0)
            r2, g2, b2 = self.get_rainbow_color(120)
            r3, g3, b3 = self.get_rainbow_color(240)
            
            gradient.setColorAt(0.0, QColor(r1, g1, b1, 180))  # Sol taraf
            gradient.setColorAt(0.5, QColor(r2, g2, b2, 180))  # Orta
            gradient.setColorAt(1.0, QColor(r3, g3, b3, 180))  # Sağ taraf
            
            # Önce orijinal resmi çiz
            painter.drawPixmap(0, 0, self.pixmap)
            
            # Sadece renkli kısımlara gradient uygula (şeffaf kısımları korur)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(0, 0, self.pixmap.width(), self.pixmap.height(), QBrush(gradient))
            
            # Composition mode'u geri al
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
        else:
            # Resim yoksa koyu mavi yazı + rainbow çizgi çiz
            from PyQt5.QtGui import QLinearGradient, QBrush
            
            painter.setOpacity(self.opacity)
            
            # Font ayarları - KÜÇÜK VE KOMPAKT
            font = painter.font()
            font.setFamily("Consolas")
            font.setPointSize(9)  # Küçük font
            font.setBold(True)
            painter.setFont(font)
            
            # Yazı boyutunu hesapla
            text = "defendingstore.com"
            text_rect = painter.fontMetrics().boundingRect(text)
            text_width = text_rect.width()
            text_height = text_rect.height()
            
            # Siyah gölge efekti
            shadow_color = QColor(0, 0, 0, 180)  # Siyah gölge
            painter.setPen(shadow_color)
            painter.drawText(2, 16, text)  # Gölge pozisyonu
            
            # Ana yazı - beyaz
            white_color = QColor(255, 255, 255)  # Beyaz renk
            painter.setPen(white_color)
            painter.drawText(1, 15, text)
            
            # Rainbow çizgi için gradient oluştur
            line_y = 20  # Yazının altında çizgi
            line_gradient = QLinearGradient(1, line_y, 1 + text_width, line_y)
            
            # Soft rainbow gradient renkleri (daha az renk geçişi, daha yumuşak)
            r1, g1, b1 = self.get_rainbow_color(0)
            r2, g2, b2 = self.get_rainbow_color(90)
            r3, g3, b3 = self.get_rainbow_color(180)
            r4, g4, b4 = self.get_rainbow_color(270)
            
            # Daha yumuşak geçişler için daha az nokta kullan
            line_gradient.setColorAt(0.0, QColor(r1, g1, b1))
            line_gradient.setColorAt(0.33, QColor(r2, g2, b2))
            line_gradient.setColorAt(0.66, QColor(r3, g3, b3))
            line_gradient.setColorAt(1.0, QColor(r4, g4, b4))
            
            # Rainbow çizgiyi çiz (1 pixel kalınlık)
            painter.setPen(QPen(QBrush(line_gradient), 1))
            painter.drawLine(1, line_y, 1 + text_width, line_y)

    def close(self):
        self.timer.stop()
        super().close()
