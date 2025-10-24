"""
Config Bilgi Tab'ı
Konfigürasyon hakkında detaylı bilgi gösterir
"""

import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QTextEdit, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from models.config_model import AdvancedConfigManager
from models.color_palette import ColorTheme


class ConfigInfoTab(QWidget):
    """Config bilgi tab'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.config_manager = AdvancedConfigManager()
        self.current_theme = ColorTheme.LIGHT  # Varsayılan tema
        self.setup_ui()
        
        # Otomatik güncelleme timer'ı
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_info)
        self.update_timer.start(5000)  # 5 saniyede bir güncelle
    
    def setup_ui(self):
        """UI'ı kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)
        
        # Config genel bilgileri
        self.create_general_info_group(scroll_layout)
        
        # Config bölümleri
        self.create_sections_info_group(scroll_layout)
        
        # Config içeriği
        self.create_content_group(scroll_layout)
        
        # İstatistikler
        self.create_statistics_group(scroll_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # İlk güncelleme
        self.update_info()
    
    def create_general_info_group(self, parent_layout):
        """Genel bilgi grubu"""
        group = QGroupBox("Genel Bilgiler")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # Config dosyası yolu
        layout.addWidget(QLabel("Config Dosyası:"), 0, 0)
        self.config_path_label = QLabel()
        self.config_path_label.setWordWrap(True)
        self.config_path_label.setStyleSheet("font-family: 'Consolas', monospace; font-size: 10px;")
        layout.addWidget(self.config_path_label, 0, 1)
        
        # Dosya boyutu
        layout.addWidget(QLabel("Dosya Boyutu:"), 1, 0)
        self.file_size_label = QLabel()
        layout.addWidget(self.file_size_label, 1, 1)
        
        # Son değişiklik
        layout.addWidget(QLabel("Son Değişiklik:"), 2, 0)
        self.last_modified_label = QLabel()
        layout.addWidget(self.last_modified_label, 2, 1)
        
        # Config versiyonu
        layout.addWidget(QLabel("Config Versiyonu:"), 3, 0)
        self.config_version_label = QLabel()
        layout.addWidget(self.config_version_label, 3, 1)
        
        # Uygulama versiyonu
        layout.addWidget(QLabel("Uygulama Versiyonu:"), 4, 0)
        self.app_version_label = QLabel()
        layout.addWidget(self.app_version_label, 4, 1)
        
        parent_layout.addWidget(group)
    
    def create_sections_info_group(self, parent_layout):
        """Bölümler bilgi grubu"""
        group = QGroupBox("Config Bölümleri")
        layout = QVBoxLayout(group)
        
        self.sections_layout = QGridLayout()
        self.sections_layout.setSpacing(5)
        layout.addLayout(self.sections_layout)
        
        parent_layout.addWidget(group)
    
    def create_content_group(self, parent_layout):
        """Config içeriği grubu"""
        group = QGroupBox("Config İçeriği (JSON)")
        layout = QVBoxLayout(group)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Yenile")
        self.refresh_btn.clicked.connect(self.update_info)
        
        self.copy_btn = QPushButton("📋 Kopyala")
        self.copy_btn.clicked.connect(self.copy_config_content)
        
        self.validate_btn = QPushButton("✅ Doğrula")
        self.validate_btn.clicked.connect(self.validate_config)
        
        self.apply_btn = QPushButton("🔄 Ayarları Uygula")
        self.apply_btn.clicked.connect(self.apply_config_from_json)
        self.apply_btn.setToolTip("JSON içeriğindeki ayarları menüye uygula")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #4CAF50);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
        """)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Config içeriği text edit
        self.config_content = QTextEdit()
        self.config_content.setReadOnly(True)
        self.config_content.setFont(QFont("Consolas", 9))
        self.config_content.setMaximumHeight(300)
        layout.addWidget(self.config_content)
        
        parent_layout.addWidget(group)
    
    def create_statistics_group(self, parent_layout):
        """İstatistikler grubu"""
        group = QGroupBox("İstatistikler")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # Toplam çalışma süresi
        layout.addWidget(QLabel("Toplam Çalışma Süresi:"), 0, 0)
        self.runtime_label = QLabel()
        layout.addWidget(self.runtime_label, 0, 1)
        
        # Atılan mermi sayısı
        layout.addWidget(QLabel("Atılan Mermi:"), 1, 0)
        self.shots_label = QLabel()
        layout.addWidget(self.shots_label, 1, 1)
        
        # İsabet sayısı
        layout.addWidget(QLabel("İsabet Sayısı:"), 2, 0)
        self.hits_label = QLabel()
        layout.addWidget(self.hits_label, 2, 1)
        
        # Doğruluk oranı
        layout.addWidget(QLabel("Doğruluk Oranı:"), 3, 0)
        self.accuracy_label = QLabel()
        layout.addWidget(self.accuracy_label, 3, 1)
        
        # Oturum sayısı
        layout.addWidget(QLabel("Oturum Sayısı:"), 4, 0)
        self.sessions_label = QLabel()
        layout.addWidget(self.sessions_label, 4, 1)
        
        parent_layout.addWidget(group)
    
    def update_info(self):
        """Bilgileri güncelle"""
        try:
            config = self.config_manager.load_config()
            config_info = self.config_manager.get_config_info()
            
            # Genel bilgiler
            self.config_path_label.setText(config_info["config_path"])
            
            file_size = config_info["config_size"]
            if file_size > 1024 * 1024:
                size_text = f"{file_size / (1024 * 1024):.2f} MB"
            elif file_size > 1024:
                size_text = f"{file_size / 1024:.2f} KB"
            else:
                size_text = f"{file_size} bytes"
            self.file_size_label.setText(size_text)
            
            if config_info["last_modified"]:
                last_mod = datetime.fromtimestamp(config_info["last_modified"])
                self.last_modified_label.setText(last_mod.strftime("%d.%m.%Y %H:%M:%S"))
            else:
                self.last_modified_label.setText("Bilinmiyor")
            
            # Version bilgisi artık config'de tutulmuyor
            self.config_version_label.setText("2.0 (Sabit)")
            self.app_version_label.setText("1.0.0 (Sabit)")
            
            # Bölümler bilgisi
            self.update_sections_info(config)
            
            # Config içeriği
            self.update_config_content(config)
            
            # İstatistikler
            self.update_statistics(config)
            
        except Exception as e:
            print(f"Config info güncelleme hatası: {e}")
    
    def update_sections_info(self, config):
        """Bölümler bilgisini güncelle"""
        # Eski widget'ları temizle
        for i in reversed(range(self.sections_layout.count())):
            self.sections_layout.itemAt(i).widget().setParent(None)
        
        sections = [
            ("theme", "Tema Ayarları", "🎨"),
            ("color_detection", "Renk Algılama", "🌈"),
            ("aimbot", "Aimbot", "🎯"),
            ("triggerbot", "Triggerbot", "🔫"),
            ("anti_smoke", "Anti-Smoke", "💨"),
            ("general", "Genel", "⚙️"),
            ("hotkeys", "Kısayol Tuşları", "⌨️"),
            ("performance", "Performans", "⚡")
        ]
        
        row, col = 0, 0
        for section_key, section_name, icon in sections:
            if section_key in config:
                section_data = config[section_key]
                item_count = len(section_data) if isinstance(section_data, dict) else 1
                
                frame = QFrame()
                frame.setFrameStyle(QFrame.Box)
                frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 5px; }")
                
                frame_layout = QVBoxLayout(frame)
                frame_layout.setContentsMargins(5, 5, 5, 5)
                
                title_label = QLabel(f"{icon} {section_name}")
                title_label.setStyleSheet("font-weight: bold; font-size: 11px;")
                
                count_label = QLabel(f"{item_count} öğe")
                count_label.setStyleSheet("color: #666; font-size: 10px;")
                
                frame_layout.addWidget(title_label)
                frame_layout.addWidget(count_label)
                
                self.sections_layout.addWidget(frame, row, col)
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
    
    def update_config_content(self, config):
        """Config içeriğini güncelle"""
        try:
            formatted_json = json.dumps(config, indent=2, ensure_ascii=False)
            self.config_content.setPlainText(formatted_json)
        except Exception as e:
            self.config_content.setPlainText(f"JSON formatında hata: {e}")
    
    def update_statistics(self, config):
        """İstatistikleri güncelle - artık config'de tutulmuyor"""
        # İstatistikler artık config'de saklanmıyor
        self.runtime_label.setText("Mevcut değil")
        self.shots_label.setText("Mevcut değil")
        self.hits_label.setText("Mevcut değil")
        self.accuracy_label.setText("Mevcut değil")
        self.sessions_label.setText("Mevcut değil")
    
    def copy_config_content(self):
        """Config içeriğini panoya kopyala"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.config_content.toPlainText())
        
        if hasattr(self.parent_app, 'statusBar'):
            self.parent_app.statusBar.showMessage("Config içeriği panoya kopyalandı.", 2000)
    
    def validate_config(self):
        """Config'i doğrula"""
        try:
            config = self.config_manager.load_config()
            # Basit doğrulama
            required_sections = ["theme", "aimbot", "triggerbot", "general"]
            missing_sections = [s for s in required_sections if s not in config]
            
            if missing_sections:
                message = f"Eksik bölümler: {', '.join(missing_sections)}"
                status = "❌ Geçersiz"
            else:
                message = "Config dosyası geçerli görünüyor."
                status = "✅ Geçerli"
            
            if hasattr(self.parent_app, 'statusBar'):
                self.parent_app.statusBar.showMessage(f"{status} - {message}", 3000)
                
        except Exception as e:
            if hasattr(self.parent_app, 'statusBar'):
                self.parent_app.statusBar.showMessage(f"❌ Doğrulama hatası: {e}", 3000)
    
    def update_theme(self, theme: ColorTheme):
        """Tema güncellendiğinde çağrılır"""
        self.current_theme = theme
        # Config info tab'ı için özel tema güncellemesi gerekirse burada yapılabilir

    def apply_config_from_json(self):
        """JSON içeriğindeki ayarları menüye uygula - Asenkron versiyon"""
        try:
            print("🔄 === APPLYING CONFIG FROM JSON CONTENT ===")
            
            # JSON içeriğini al
            json_content = self.config_content.toPlainText()
            
            if not json_content.strip():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Hata", "JSON içeriği boş!")
                return
            
            # JSON'u parse et
            try:
                config_data = json.loads(json_content)
                print(f"📖 JSON parsed successfully: {list(config_data.keys())}")
            except json.JSONDecodeError as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "JSON Hatası", f"JSON formatında hata:\n\n{e}")
                return
            
            # Confirmation dialog
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Ayarları Uygula",
                "JSON içeriğindeki ayarlar menüye uygulanacak.\n\nDevam etmek istediğinizden emin misiniz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                print("🔄 User confirmed, starting async application...")
                
                # Butonu devre dışı bırak
                self.apply_btn.setEnabled(False)
                self.apply_btn.setText("⏳ Uygulanıyor...")
                
                # Asenkron olarak uygula
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._apply_config_async(config_data))
            else:
                print("❌ User cancelled config application")
                
        except Exception as e:
            print(f"❌ Apply config from JSON error: {e}")
            import traceback
            traceback.print_exc()
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Beklenmeyen Hata", f"Ayarları uygularken hata:\n\n{e}")
    
    def _apply_config_async(self, config_data):
        """Config'i asenkron olarak uygula"""
        try:
            print("🔄 Async config application started...")
            
            # Ana uygulamaya erişim
            if hasattr(self, 'parent_app') and self.parent_app:
                # Config'i geçici olarak kaydet
                temp_success, temp_message = self.config_manager.save_config(config_data)
                
                if temp_success:
                    print("💾 Temporary config saved")
                    
                    # Ana uygulamadaki ayarları güncelle
                    self.parent_app.apply_config_from_data(config_data)
                    
                    # Başarı mesajını asenkron göster
                    QTimer.singleShot(500, lambda: self._show_success_message())
                    
                    print("✅ === CONFIG APPLIED FROM JSON ===")
                else:
                    # Hata mesajını asenkron göster
                    QTimer.singleShot(100, lambda: self._show_error_message(f"Config kaydetme hatası:\n\n{temp_message}"))
            else:
                QTimer.singleShot(100, lambda: self._show_error_message("Ana uygulama referansı bulunamadı!"))
                
        except Exception as e:
            print(f"❌ Async config application error: {e}")
            import traceback
            traceback.print_exc()
            
            # Hata mesajını asenkron göster
            QTimer.singleShot(100, lambda: self._show_error_message(f"Ayarları uygularken hata:\n\n{e}"))
        finally:
            # Butonu yeniden etkinleştir
            QTimer.singleShot(1000, self._reset_apply_button)
    
    def _show_success_message(self):
        """Başarı mesajını göster"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Başarılı",
                "JSON içeriğindeki ayarlar başarıyla menüye uygulandı!"
            )
            
            # Notification göster
            try:
                from notification_system import show_success
                show_success("Ayarlar Uygulandı", "JSON içeriğinden ayarlar yüklendi", 2000)
            except:
                pass
        except Exception as e:
            print(f"❌ Error showing success message: {e}")
    
    def _show_error_message(self, message):
        """Hata mesajını göster"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", message)
        except Exception as e:
            print(f"❌ Error showing error message: {e}")
    
    def _reset_apply_button(self):
        """Apply butonunu sıfırla"""
        try:
            self.apply_btn.setEnabled(True)
            self.apply_btn.setText("🔄 Ayarları Uygula")
        except Exception as e:
            print(f"❌ Error resetting apply button: {e}")

    def cleanup(self):
        """Temizlik işlemleri"""
        if self.update_timer:
            self.update_timer.stop()