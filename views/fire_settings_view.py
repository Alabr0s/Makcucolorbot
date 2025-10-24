from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSlider, 
                             QHBoxLayout, QLabel, QCheckBox, QPushButton, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
from aimbot.key_capture import KeyCaptureButton
from controllers.theme_controller import WindowColorManager
from models.color_palette import ColorTheme
import time
import random
import numpy as np
import mss
import cv2
import keyboard
from tcp_client import AimTCPClient


class TriggerbotScanner(QThread):
    """Ayrı triggerbot tarayıcısı - aimbot'tan bağımsız"""
    target_detected = pyqtSignal(bool)
    toggle_state_changed = pyqtSignal(bool)  # Thread-safe UI güncellemesi için yeni signal
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.enabled = False
        
        # Triggerbot ayarları
        self.fire_delay_min = 170
        self.fire_delay_max = 480
        self.area_size = 6
        self.scan_fps = 200
        self.last_fire_time = 0
        
        # Hold key ve toggle key ayarları
        self.holdkey_enabled = False
        self.holdkey = 'g'  # Aimbot'tan farklı (aimbot: f)
        self.toggle_key = 'home'  # Aimbot'tan farklı (aimbot: insert)
        self.last_toggle_time = 0
        
        # Color settings referansı
        self.color_settings = None
        
        # UI callback referansı (checkbox güncellemesi için)
        self.ui_callback = None
        
        # TCP client
        self.tcp_client = AimTCPClient()
        
    def run(self):
        self.running = True
        # Toggle key kontrolü için ayrı loop
        last_toggle_check = 0
        
        with mss.mss() as sct:
            while self.running:
                current_time = time.time()
                
                # Toggle key kontrolü - her 50ms'de bir kontrol et
                if current_time - last_toggle_check >= 0.05:  # 50ms = 20 FPS
                    self.check_toggle_key()
                    last_toggle_check = current_time
                
                if not self.enabled:
                    time.sleep(0.05)  # Daha kısa bekleme
                    continue
                
                # Hold key kontrolü
                if self.holdkey_enabled:
                    if not self.is_key_pressed(self.holdkey):
                        time.sleep(0.01)
                        continue
                
                # Ekran merkezinden küçük alan tara
                screen = sct.monitors[1]
                center_x = screen['width'] // 2
                center_y = screen['height'] // 2
                
                monitor = {
                    'top': center_y - self.area_size // 2,
                    'left': center_x - self.area_size // 2,
                    'width': self.area_size,
                    'height': self.area_size
                }
                
                # Ekran görüntüsü al
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                
                # Hedef rengi ara
                target_found = self.detect_target_color(img)
                
                if target_found:
                    self.handle_fire()
                    self.target_detected.emit(True)
                else:
                    self.target_detected.emit(False)
                
                # FPS kontrolü
                time.sleep(1.0 / self.scan_fps)
    
    def detect_target_color(self, img):
        """Hedef rengi tespit et - Color settings'den renk al"""
        if img.shape[2] == 4:  # BGRA
            img_bgr = img[:, :, :3]
        else:
            img_bgr = img
        
        # BGR'den HSV'ye çevir
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        # Color settings'den HSV aralıklarını al
        if self.color_settings:
            try:
                widgets = self.color_settings.get_widgets()
                
                # HSV aralıklarını color_settings'den al
                hue_min = widgets['hue_min'].value()
                hue_max = widgets['hue_max'].value()
                sat_min = widgets['sat_min'].value() / 100.0 * 255  # Yüzde'den 0-255'e çevir
                sat_max = widgets['sat_max'].value() / 100.0 * 255
                val_min = widgets['val_min'].value()
                val_max = widgets['val_max'].value()
                
                # OpenCV HSV formatına çevir (H: 0-179)
                if hue_min > 179:
                    hue_min = hue_min // 2
                if hue_max > 179:
                    hue_max = hue_max // 2
                
                lower_hsv = np.array([hue_min, sat_min, val_min])
                upper_hsv = np.array([hue_max, sat_max, val_max])
                
            except Exception as e:
                print(f"Color settings error, using default: {e}")
                # Hata durumunda varsayılan değerleri kullan
                lower_hsv = np.array([135, 64, 100])  # Varsayılan mor
                upper_hsv = np.array([165, 255, 255])
        else:
            # Color settings yoksa varsayılan değerleri kullan
            lower_hsv = np.array([135, 64, 100])  # Varsayılan mor
            upper_hsv = np.array([165, 255, 255])
        
        # Maske oluştur
        mask = cv2.inRange(img_hsv, lower_hsv, upper_hsv)
        
        # Hedef piksel var mı?
        return np.any(mask == 255)
    
    def handle_fire(self):
        """Ateşleme mantığı"""
        current_time = time.time() * 1000
        
        # Gecikme kontrolü
        if current_time - self.last_fire_time < self.fire_delay_min:
            return
        
        # Rastgele gecikme
        delay = random.randint(self.fire_delay_min, self.fire_delay_max)
        
        if current_time - self.last_fire_time >= delay:
            # 1515 portuna firecmds mesajı gönder
            if self.tcp_client.send_fire_command():
                self.last_fire_time = current_time
    
    def set_enabled(self, enabled):
        self.enabled = enabled
        
        # Notification göster
        self._show_triggerbot_notification()
    
    def _show_triggerbot_notification(self):
        """Triggerbot durum notification'ı göster"""
        try:
            print(f"🔔 Showing triggerbot notification: enabled={self.enabled}")
            
            # Önce basit bir test notification dene
            from utils.notification_system import notification_manager, show_success, show_info
            
            # Test notification
            print("📤 Sending test notification...")
            show_info("Test", "Bu bir test notification", 2000)
            
            # Triggerbot notification
            print("📤 Sending triggerbot notification...")
            notification_manager.show_triggerbot_status(self.enabled)
            
            # Alternatif olarak basit notification dene
            if self.enabled:
                show_success("Triggerbot Aktif", "Triggerbot sistemi etkinleştirildi", 2000)
            else:
                show_info("Triggerbot Pasif", "Triggerbot sistemi devre dışı bırakıldı", 2000)
            
            print(f"✅ All notifications sent successfully")
            
        except Exception as e:
            print(f"❌ Triggerbot notification hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_holdkey_notification(self, enabled: bool, key: str):
        """Holdkey durum notification'ı göster"""
        try:
            from utils.notification_system import show_info, show_success, show_warning
            
            if enabled:
                show_success(
                    "Triggerbot Holdkey Aktif", 
                    f"Holdkey modu etkinleştirildi (Tuş: {key.upper()})", 
                    2000
                )
            else:
                show_warning(
                    "Triggerbot Holdkey Pasif", 
                    "Holdkey modu devre dışı bırakıldı", 
                    2000
                )
        except Exception as e:
            print(f"Holdkey notification hatası: {e}")
    
    def set_fire_settings(self, delay_min, delay_max):
        self.fire_delay_min = max(50, delay_min)
        self.fire_delay_max = max(self.fire_delay_min, delay_max)
    
    def set_scan_settings(self, area_size, fps):
        self.area_size = max(1, min(50, area_size))
        self.scan_fps = max(1, min(500, fps))
    
    def set_color_settings_reference(self, color_settings):
        """Set color settings reference"""
        self.color_settings = color_settings
    
    def set_holdkey_settings(self, enabled, key):
        """Hold key ayarlarını güncelle"""
        old_enabled = self.holdkey_enabled
        self.holdkey_enabled = enabled
        self.holdkey = key.lower() if key else 'f'
        
        # Holdkey durumu değiştiyse notification göster
        if old_enabled != enabled:
            self._show_holdkey_notification(enabled, key)
    
    def set_toggle_key(self, key):
        """Toggle key ayarla"""
        old_key = self.toggle_key
        self.toggle_key = key.lower() if key else 'insert'
        print(f"Triggerbot toggle key changed: {old_key} -> {self.toggle_key}")
    
    def set_ui_callback(self, callback):
        """UI checkbox güncellemesi için callback ayarla"""
        self.ui_callback = callback
    
    def check_toggle_key(self):
        """Toggle key kontrolü"""
        current_time = time.time()
        
        # Spam önleme: 0.3 saniye aralık (daha hızlı tepki)
        if current_time - self.last_toggle_time < 0.3:
            return
        
        # Toggle tuşuna basıldı mı kontrol et
        key_pressed = self.is_key_pressed(self.toggle_key)
        
        if key_pressed:
            old_enabled = self.enabled
            self.enabled = not self.enabled
            self.last_toggle_time = current_time
            
            # Debug log
            print(f"🔥 TRIGGERBOT TOGGLE ACTIVATED! Key: '{self.toggle_key}', Old: {old_enabled}, New: {self.enabled}")
            
            # Thread-safe signal emit - UI güncellenir
            try:
                print(f"📡 Emitting toggle_state_changed signal with enabled={self.enabled}")
                self.toggle_state_changed.emit(self.enabled)
                print(f"✅ Signal emitted successfully")
            except Exception as e:
                print(f"❌ Signal emit hatası: {e}")
                import traceback
                traceback.print_exc()
            
            # Notification göster
            self._show_triggerbot_notification()
    
    def is_key_pressed(self, key):
        """Gelişmiş tuş kontrol sistemi - Mouse tuşları destekli"""
        try:
            key = key.lower().strip()
            is_toggle_key = (key == self.toggle_key)
            
            # Debug için
            if is_toggle_key and not hasattr(self, '_last_debug_time'):
                self._last_debug_time = 0
            
            # Mouse tuşları kontrolü
            if key in ['left', 'right', 'middle', 'x1', 'x2']:
                return self._check_mouse_button(key)
            
            # Önce Windows API ile dene (daha güvenilir)
            result = self._check_key_with_winapi(key)
            
            # Windows API başarısız olursa keyboard kütüphanesi dene
            if not result:
                try:
                    import keyboard
                    
                    # Tuş ismi düzeltmeleri
                    key_corrections = {
                        'alt_l': 'alt', 'alt_r': 'alt',
                        'ctrl_l': 'ctrl', 'ctrl_r': 'ctrl', 
                        'shift_l': 'shift', 'shift_r': 'shift',
                        'caps_lock': 'caps lock',
                        'page_up': 'page up', 'page_down': 'page down'
                    }
                    
                    corrected_key = key_corrections.get(key, key)
                    result = keyboard.is_pressed(corrected_key)
                    
                except Exception as kb_error:
                    if is_toggle_key:
                        print(f"⚠️ Keyboard library error: {kb_error}")
                    result = False
            
            # Debug log
            if is_toggle_key:
                current_time = time.time()
                if result:
                    print(f"🎯 TOGGLE KEY '{key}' PRESSED!")
                elif current_time - self._last_debug_time > 5:
                    print(f"🔍 Toggle key '{key}' not pressed (checking...)")
                    self._last_debug_time = current_time
            
            return result
                
        except Exception as e:
            print(f"❌ Key check error: {e}")
            return False
    
    def _check_mouse_button(self, button):
        """Mouse tuşu kontrolü - Windows API kullanır"""
        try:
            import ctypes
            
            # Windows mouse button codes
            mouse_vk_codes = {
                'left': 0x01,    # VK_LBUTTON
                'right': 0x02,   # VK_RBUTTON
                'middle': 0x04,  # VK_MBUTTON
                'x1': 0x05,      # VK_XBUTTON1 (yan tuş)
                'x2': 0x06       # VK_XBUTTON2 (yan tuş)
            }
            
            vk_code = mouse_vk_codes.get(button)
            if vk_code:
                # GetAsyncKeyState ile mouse tuşu kontrol et
                result = ctypes.windll.user32.GetAsyncKeyState(vk_code)
                is_pressed = (result & 0x8000) != 0
                
                # Debug log
                if button == self.toggle_key or button == self.holdkey:
                    if is_pressed:
                        print(f"🔎 MOUSE BUTTON '{button}' PRESSED! (VK={hex(vk_code)})")
                
                return is_pressed
            
            return False
            
        except Exception as e:
            print(f"❌ Mouse button check error for '{button}': {e}")
            return False
    
    def _check_key_with_winapi(self, key):
        """Windows API ile tuş kontrolü"""
        try:
            import ctypes
            
            # Windows virtual key codes - genişletilmiş liste
            vk_codes = {
                # Özel tuşlar
                'home': 0x24, 'end': 0x23, 'insert': 0x2D, 'delete': 0x2E,
                'page up': 0x21, 'page down': 0x22,
                'ctrl': 0x11, 'alt': 0x12, 'shift': 0x10,
                'space': 0x20, 'tab': 0x09, 'enter': 0x0D, 'esc': 0x1B,
                'caps lock': 0x14, 'num lock': 0x90, 'scroll lock': 0x91,
                'pause': 0x13, 'print screen': 0x2C,
                
                # F tuşları
                'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
                'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
                'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
                
                # Sayılar
                '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
                '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
                
                # Harfler (A-Z)
                'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
                'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
                'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
                'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
                'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A
            }
            
            # VK kodu al
            vk_code = vk_codes.get(key.lower())
            
            if vk_code:
                # GetAsyncKeyState ile kontrol et
                result = ctypes.windll.user32.GetAsyncKeyState(vk_code)
                is_pressed = (result & 0x8000) != 0
                
                # Toggle key için debug
                if key == self.toggle_key:
                    if is_pressed:
                        print(f"🎯 TOGGLE KEY '{key}' PRESSED! (Windows API, VK={hex(vk_code)})")
                    # Her 10 saniyede bir durum yazdır
                    if not hasattr(self, '_last_winapi_debug') or time.time() - self._last_winapi_debug > 10:
                        print(f"🪟 Windows API: key='{key}', vk_code={hex(vk_code)}, pressed={is_pressed}")
                        self._last_winapi_debug = time.time()
                
                return is_pressed
            else:
                if key == self.toggle_key:
                    print(f"❌ VK code not found for toggle key: '{key}'")
            
            return False
            
        except Exception as e:
            if key == self.toggle_key:
                print(f"❌ Windows API error for toggle key '{key}': {e}")
            return False
    
    def stop(self):
        self.running = False
        self.tcp_client.disconnect()
        self.wait()


class FireSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.widgets = {}
        self.current_theme = ColorTheme.LIGHT  # Varsayılan tema
        
        # Triggerbot scanner - ÖNCE UI'yı oluştur, SONRA thread'i başlat
        self.triggerbot = TriggerbotScanner()
        self.triggerbot.target_detected.connect(self.on_target_detected)
        
        # Thread-safe UI güncellemesi için signal bağlantısı
        self.triggerbot.toggle_state_changed.connect(self.update_checkbox_from_toggle)
        
        # ÖNEMLİ: Thread'i henüz başlatma - UI oluştuktan sonra başlat
        # self.triggerbot.start() -> Bu satır setup_ui() sonrasına taşındı
        
        self.setup_ui()
        
        # UI hazır olduktan SONRA thread'i başlat
        self.triggerbot.start()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Ana grup
        main_group = self.create_main_group()
        scroll_area.setWidget(main_group)
        main_layout.addWidget(scroll_area)
        
        self.apply_styles()

    def create_main_group(self):
        group = QGroupBox("Triggerbot Settings")
        layout = QFormLayout(group)
        layout.setSpacing(18)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === MAIN CONTROL ===
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        layout.addRow("Triggerbot Active:", self.enabled_checkbox)
        
        # Status indicator
        self.status_label = QLabel("Disabled")
        self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        layout.addRow("Status:", self.status_label)
        
        # === FIRING SETTINGS ===
        self.fire_delay_min_slider = self.create_slider(50, 1000, 170, "ms")
        layout.addRow("Min Fire Delay:", self.fire_delay_min_slider[0])
        self.widgets["fire_delay_min"] = self.fire_delay_min_slider[1]
        
        self.fire_delay_max_slider = self.create_slider(100, 1000, 480, "ms")
        layout.addRow("Max Fire Delay:", self.fire_delay_max_slider[0])
        self.widgets["fire_delay_max"] = self.fire_delay_max_slider[1]
        
        # === SCAN SETTINGS ===
        self.area_size_slider = self.create_slider(1, 50, 6, "px")
        layout.addRow("Scan Area:", self.area_size_slider[0])
        self.widgets["area_size"] = self.area_size_slider[1]
        
        self.scan_fps_slider = self.create_slider(1, 500, 200, "fps")
        layout.addRow("Scan FPS:", self.scan_fps_slider[0])
        self.widgets["scan_fps"] = self.scan_fps_slider[1]
        
        # === KEY SETTINGS ===
        # Hold key checkbox
        self.holdkey_checkbox = QCheckBox()
        self.holdkey_checkbox.stateChanged.connect(self.update_key_settings)
        layout.addRow("Hold Key Active:", self.holdkey_checkbox)
        
        # Hold key selector
        holdkey_layout = QHBoxLayout()
        holdkey_layout.setSpacing(12)
        self.holdkey_button = KeyCaptureButton("g")
        self.holdkey_button.setFixedHeight(35)
        self.holdkey_button.key_captured.connect(self.on_holdkey_captured)
        
        holdkey_info_label = QLabel("Hold key")
        holdkey_info_label.setProperty('info_type', 'key')
        
        holdkey_layout.addWidget(self.holdkey_button)
        holdkey_layout.addWidget(holdkey_info_label)
        holdkey_layout.addStretch()
        layout.addRow("Hold Key:", holdkey_layout)
        
        # Toggle key selector
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(12)
        self.toggle_button = KeyCaptureButton("home")
        self.toggle_button.setFixedHeight(35)
        self.toggle_button.key_captured.connect(self.on_toggle_captured)
        
        toggle_info_label = QLabel("Toggle key")
        toggle_info_label.setProperty('info_type', 'key')
        
        toggle_layout.addWidget(self.toggle_button)
        toggle_layout.addWidget(toggle_info_label)
        toggle_layout.addStretch()
        layout.addRow("Toggle Key:", toggle_layout)
        
        # === INFORMATION ===
        color_info = QLabel("Color settings are taken from the 'Color Settings' tab")
        color_info.setStyleSheet("color: #42a5f5; font-size: 11px; font-style: italic;")
        layout.addRow("Color Settings:", color_info)
        
        return group
    
    def create_slider(self, min_val, max_val, default_val, unit):
        """Create modern slider"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        
        value_label = QLabel(f"{default_val}{unit}")
        value_label.setMinimumWidth(50)
        value_label.setAlignment(Qt.AlignCenter)
        
        def update_label(value):
            value_label.setText(f"{value}{unit}")
            self.update_triggerbot_settings()
        
        slider.valueChanged.connect(update_label)
        
        layout.addWidget(slider)
        layout.addWidget(value_label)
        
        return container, slider
    
    def update_checkbox_from_toggle(self, enabled):
        """Update checkbox when toggle key is pressed"""
        try:
            print(f"🔄 UPDATE_CHECKBOX_FROM_TOGGLE called with enabled={enabled}")
            
            # Check if widget is still valid
            if not hasattr(self, 'enabled_checkbox') or not self.enabled_checkbox:
                print("❌ enabled_checkbox not available!")
                return
            
            print(f"📋 Current checkbox state: {self.enabled_checkbox.isChecked()}")
            
            # Temporarily disable checkbox signal
            self.enabled_checkbox.blockSignals(True)
            self.enabled_checkbox.setChecked(enabled)
            self.enabled_checkbox.blockSignals(False)
            
            print(f"✅ Checkbox updated to: {self.enabled_checkbox.isChecked()}")
            
            # Status label'ı güncelle
            self.update_status_label(enabled)
            
            print(f"🎯 Checkbox successfully updated from toggle key: {enabled}")
            
        except Exception as e:
            print(f"❌ Checkbox güncelleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def save_settings(self):
        """Save settings for config"""
        try:
            settings = {
                # Main control
                'enabled': str(self.enabled_checkbox.isChecked()).lower(),
                
                # Ateşleme ayarları
                'fire_delay_min': str(self.widgets["fire_delay_min"].value()),
                'fire_delay_max': str(self.widgets["fire_delay_max"].value()),
                
                # Tarama ayarları
                'area_size': str(self.widgets["area_size"].value()),
                'scan_fps': str(self.widgets["scan_fps"].value()),
                
                # Key settings
                'use_holdkey': str(self.holdkey_checkbox.isChecked()).lower(),
                'holdkey': self.holdkey_button.current_key,
                'toggle_key': self.toggle_button.current_key
            }
            
            print(f"💾 Triggerbot settings saved: {len(settings)} items")
            return settings
            
        except Exception as e:
            print(f"❌ Error saving triggerbot settings: {e}")
            return {}
    
    def update_status_label(self, enabled):
        """Update status label"""
        if enabled:
            self.status_label.setText("Active - Scanning")
            self.status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
        else:
            self.status_label.setText("Disabled")
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")

    def on_enabled_changed(self):
        """Triggerbot active/inactive status"""
        enabled = self.enabled_checkbox.isChecked()
        self.triggerbot.set_enabled(enabled)
        
        # Show notification for UI checkbox change
        try:
            from utils.notification_system import notification_manager
            notification_manager.show_triggerbot_status(enabled)
        except Exception as e:
            print(f"Triggerbot UI notification hatası: {e}")
        
        # Status label'ı güncelle
        self.update_status_label(enabled)
    
    def update_triggerbot_settings(self):
        """Update triggerbot settings - Safe version"""
        try:
            if not hasattr(self, 'triggerbot') or not self.triggerbot:
                print("⚠️ Triggerbot not available, skipping settings update")
                return
            
            # Ateşleme ayarları
            delay_min = self.widgets["fire_delay_min"].value()
            delay_max = self.widgets["fire_delay_max"].value()
            self.triggerbot.set_fire_settings(delay_min, delay_max)
            
            # Tarama ayarları
            area_size = self.widgets["area_size"].value()
            fps = self.widgets["scan_fps"].value()
            self.triggerbot.set_scan_settings(area_size, fps)
            
            print(f"🔥 Triggerbot settings updated: delay={delay_min}-{delay_max}, area={area_size}, fps={fps}")
            
        except Exception as e:
            print(f"❌ Error updating triggerbot settings: {e}")
    
    def on_target_detected(self, detected):
        """When target is detected"""
        if detected:
            self.status_label.setText("🎯 TARGET DETECTED!")
            self.status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        else:
            # Check triggerbot's real status
            if self.triggerbot.enabled:
                self.status_label.setText("Active - Scanning")
                self.status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
    
    def apply_styles(self):
        """Apply gray theme styling"""
        gray_theme_style = """
        QScrollArea {
            border: none;
            background: transparent;
        }
        
        QGroupBox {
            color: white;
            font-weight: bold;
            font-size: 14px;
            border: 2px solid rgba(100, 100, 100, 0.4);
            border-radius: 15px;
            margin-top: 10px;
            padding-top: 10px;
            background: rgba(35, 35, 35, 80);
        }
        
        QGroupBox::title {
            color: #a0a0a0;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            font-weight: bold;
        }
        
        QCheckBox {
            color: white;
            font-weight: bold;
            spacing: 12px;
            font-size: 13px;
        }
        
        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border-radius: 12px;
            border: 3px solid rgba(70, 70, 70, 0.9);
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(50, 50, 50, 200), stop:1 rgba(30, 30, 30, 200));
        }
        
        QCheckBox::indicator:hover {
            border: 3px solid rgba(100, 100, 100, 1.0);
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(60, 60, 60, 220), stop:1 rgba(40, 40, 40, 220));
            box-shadow: 0 0 12px rgba(100, 100, 100, 0.3);
        }
        
        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(160, 160, 160, 255), stop:1 rgba(120, 120, 120, 255));
            border: 3px solid rgba(180, 180, 180, 1.0);
            box-shadow: 0 0 16px rgba(140, 140, 140, 0.6), inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        QCheckBox::indicator:checked:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(180, 180, 180, 255), stop:1 rgba(140, 140, 140, 255));
            border: 3px solid rgba(200, 200, 200, 1.0);
            box-shadow: 0 0 20px rgba(160, 160, 160, 0.7), inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        QLabel {
            color: white;
            font-family: 'Roboto', 'Arial';
            background: transparent;
            font-weight: bold;
            font-size: 13px;
        }
        
        QSlider::groove:horizontal {
            background: rgba(30, 30, 30, 200);
            height: 8px;
            border-radius: 4px;
            border: none;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(160, 160, 160, 255), 
                stop:0.5 rgba(180, 180, 180, 255),
                stop:1 rgba(160, 160, 160, 255));
            border: none;
            width: 26px;
            height: 26px;
            margin: -9px 0;
            border-radius: 13px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6), 0 0 0 4px rgba(40, 40, 40, 0.8);
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(180, 180, 180, 255), 
                stop:0.5 rgba(200, 200, 200, 255),
                stop:1 rgba(180, 180, 180, 255));
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.7), 0 0 0 4px rgba(60, 60, 60, 1.0), 0 0 20px rgba(160, 160, 160, 0.4);
        }
        
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 100, 100, 255), 
                stop:0.5 rgba(140, 140, 140, 255),
                stop:1 rgba(120, 120, 120, 255));
            border-radius: 4px;
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(90, 90, 90, 120), stop:1 rgba(70, 70, 70, 120));
            border: 1px solid rgba(110, 110, 110, 0.6);
            border-radius: 8px;
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            margin: 2px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(110, 110, 110, 180), stop:1 rgba(90, 90, 90, 180));
            border: 1px solid rgba(120, 120, 120, 0.8);
            box-shadow: 0 0 15px rgba(100, 100, 100, 0.4);
        }
        
        QPushButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(120, 120, 120, 220), stop:1 rgba(100, 100, 100, 220));
            border: 2px solid rgba(130, 130, 130, 0.9);
            box-shadow: 0 0 15px rgba(110, 110, 110, 0.6);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(70, 70, 70, 200), stop:1 rgba(90, 90, 90, 200));
        }
        
        QLabel[info_type="key"] {
            color: #cccccc;
            font-size: 11px;
            font-style: italic;
            font-weight: normal;
        }
        
        QSlider::groove:horizontal {
            background: rgba(30, 30, 30, 200);
            height: 8px;
            border-radius: 4px;
            border: none;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(160, 160, 160, 255), 
                stop:0.5 rgba(180, 180, 180, 255),
                stop:1 rgba(160, 160, 160, 255));
            border: none;
            width: 26px;
            height: 26px;
            margin: -9px 0;
            border-radius: 13px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6), 0 0 0 4px rgba(40, 40, 40, 0.8);
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(180, 180, 180, 255), 
                stop:0.5 rgba(200, 200, 200, 255),
                stop:1 rgba(180, 180, 180, 255));
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.7), 0 0 0 4px rgba(60, 60, 60, 1.0), 0 0 20px rgba(160, 160, 160, 0.4);
        }
        
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 100, 100, 255), 
                stop:0.5 rgba(140, 140, 140, 255),
                stop:1 rgba(120, 120, 120, 255));
            border-radius: 4px;
        }
        
        /* Scrollbar styling for long tables */
        QScrollBar:vertical {
            background: rgba(35, 35, 35, 150);
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(120, 120, 120, 200), stop:1 rgba(100, 100, 100, 200));
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
        
        QScrollBar:horizontal {
            background: rgba(35, 35, 35, 150);
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(100, 100, 100, 180), stop:1 rgba(80, 80, 80, 180));
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(120, 120, 120, 200), stop:1 rgba(100, 100, 100, 200));
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: transparent;
        }
        """
        
        self.setStyleSheet(gray_theme_style)

    def get_widgets(self):
        """For backward compatibility"""
        return self.widgets

    def load_settings(self, config):
        """Load settings - COMPREHENSIVE UPDATE"""
        print(f"🔥 FireSettings load_settings called with: {config}")
        
        try:
            # Load widget settings
            for key, widget in self.widgets.items():
                if key in config:
                    try:
                        value = int(float(config[key]))
                        widget.setValue(value)
                        print(f"🔥 Set {key} = {value}")
                    except ValueError as e:
                        print(f"❌ Error setting {key}: {e}")
            
            # Load triggerbot enabled status
            if 'triggerbot_enabled' in config:
                enabled = config['triggerbot_enabled'].lower() == 'true'
                print(f"🔥 Setting triggerbot enabled: {enabled}")
                
                # Update checkbox
                self.enabled_checkbox.blockSignals(True)
                self.enabled_checkbox.setChecked(enabled)
                self.enabled_checkbox.blockSignals(False)
                
                # Update triggerbot
                if hasattr(self, 'triggerbot') and self.triggerbot:
                    self.triggerbot.set_enabled(enabled)
                
                # Update status label
                self.update_status_label(enabled)
            
            # Load hold key settings
            if 'use_holdkey' in config:
                holdkey_enabled = config['use_holdkey'].lower() == 'true'
                print(f"🔥 Setting holdkey enabled: {holdkey_enabled}")
                
                self.holdkey_checkbox.blockSignals(True)
                self.holdkey_checkbox.setChecked(holdkey_enabled)
                self.holdkey_checkbox.blockSignals(False)
            
            if 'hold_key' in config:
                holdkey = config['hold_key']
                print(f"🔥 Setting holdkey: {holdkey}")
                
                self.holdkey_button.current_key = holdkey
                self.holdkey_button.update_text()
                
                # Triggerbot'a da bildir
                if hasattr(self, 'triggerbot') and self.triggerbot:
                    holdkey_enabled = self.holdkey_checkbox.isChecked()
                    self.triggerbot.set_holdkey_settings(holdkey_enabled, holdkey)
            
            if 'toggle_key' in config:
                toggle_key = config['toggle_key']
                print(f"🔥 Setting toggle key: {toggle_key}")
                
                self.toggle_button.current_key = toggle_key
                self.toggle_button.update_text()
                
                # Also inform triggerbot
                if hasattr(self, 'triggerbot') and self.triggerbot:
                    self.triggerbot.set_toggle_key(toggle_key)
            
            # Apply all settings to triggerbot (only once)
            self.update_triggerbot_settings()
            
            print("✅ FireSettings load_settings completed successfully")
            
        except Exception as e:
            print(f"❌ Error in FireSettings load_settings: {e}")
            import traceback
            traceback.print_exc()
        
        print("✅ Fire settings loaded successfully")
    
    def set_color_settings_reference(self, color_settings):
        """Set color settings reference"""
        self.triggerbot.set_color_settings_reference(color_settings)
    
    def update_key_settings(self):
        """Update key settings"""
        enabled = self.holdkey_checkbox.isChecked()
        key = self.holdkey_button.current_key
        
        print(f"🔥 Updating key settings: enabled={enabled}, key={key}")
        
        if hasattr(self, 'triggerbot') and self.triggerbot:
            self.triggerbot.set_holdkey_settings(enabled, key)
    
    def on_holdkey_captured(self, key):
        """Called when hold key is captured"""
        try:
            print(f"Hold key captured: {key}")
            self.update_key_settings()
            
            # Key capture notification
            from utils.notification_system import show_info
            show_info("Key Assigned", f"Triggerbot holdkey: {key.upper()}", 1500)
            
        except Exception as e:
            print(f"Hold key handler error: {e}")
    
    def on_toggle_captured(self, key):
        """Called when toggle key is captured"""
        try:
            print(f"Toggle key captured: {key}")
            if hasattr(self, 'triggerbot') and self.triggerbot:
                self.triggerbot.set_toggle_key(key)
                print(f"Triggerbot toggle key set to: {key}")
            
            # Key capture notification
            from utils.notification_system import show_info
            show_info("Key Assigned", f"Triggerbot toggle: {key.upper()}", 1500)
            
        except Exception as e:
            print(f"Toggle key handler error: {e}")
    
    def debug_triggerbot_status(self):
        """Print triggerbot status for debug"""
        if hasattr(self, 'triggerbot'):
            print(f"=== TRIGGERBOT DEBUG ===")
            print(f"Enabled: {self.triggerbot.enabled}")
            print(f"Toggle Key: {self.triggerbot.toggle_key}")
            print(f"Checkbox Checked: {self.enabled_checkbox.isChecked()}")
            print(f"Running: {self.triggerbot.running}")
            print(f"========================")
    
    def update_theme(self, theme: ColorTheme):
        """Called when theme is updated"""
        self.current_theme = theme
        # Special theme update for fire settings tab can be done here if needed
        # Key capture buttons automatically detect theme changes

    def cleanup(self):
        """Cleanup operations"""
        try:
            # Stop key capture operations
            if hasattr(self, 'holdkey_button'):
                self.holdkey_button.is_capturing = False
                if hasattr(self.holdkey_button, '_cleanup_listeners'):
                    self.holdkey_button._cleanup_listeners()
            
            if hasattr(self, 'toggle_button'):
                self.toggle_button.is_capturing = False
                if hasattr(self.toggle_button, '_cleanup_listeners'):
                    self.toggle_button._cleanup_listeners()
            
            # Stop triggerbot
            if hasattr(self, 'triggerbot') and self.triggerbot:
                self.triggerbot.stop()
                
        except Exception as e:
            print(f"Fire settings cleanup error: {e}")
