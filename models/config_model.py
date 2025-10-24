"""
Config Model - MVC Pattern
Veri yönetimi ve kalıcılık katmanı
"""

import os
import json
from typing import Dict, Any, Optional
from models.color_palette import ColorTheme


class AdvancedConfigManager:
    """
    Gelişmiş konfigürasyon yöneticisi
    JSON formatında tüm ayarları saklar
    """
    
    def __init__(self):
        appdata_path = os.path.expandvars(r'%APPDATA%')
        self.config_dir = os.path.join(appdata_path, "DefendingStoreConfig")
        self.config_path = os.path.join(self.config_dir, "settings.json")
        os.makedirs(self.config_dir, exist_ok=True)
        self._default_config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "theme": {
                "current_theme": ColorTheme.LIGHT.value,
                "custom_colors": {}
            },
            "color_detection": {
                "hue_min": 270,
                "hue_max": 330,
                "sat_min": 0.25,
                "sat_max": 1.0,
                "val_min": 100,
                "val_max": 255
            },
            "aimbot": {
                "enabled": True,
                "holdkey": "f",
                "toggle_key": "insert",
                "use_holdkey": False,
                "sensitivity": 1.0,
                "smoothing": 0.5,
                "fov_size": 100,
                "target_area_size": 6,
                "scan_fps": 200,
                "auto_shoot": False,
                "prediction": False,
                "prediction_strength": 1.0,
                "color_tolerance": 5,
                "debug_mode": False,
                "show_fov": False,
                "show_crosshair": True,
                "crosshair_size": 20,
                "crosshair_color": "#00ff00",
                "target_priority": "closest"
            },
            "triggerbot": {
                "enabled": False,
                "holdkey": "alt",
                "toggle_key": "home",
                "use_holdkey": True,
                "fire_delay_min": 170,
                "fire_delay_max": 480,
                "fire_key": "p",
                "burst_mode": False,
                "burst_count": 3,
                "burst_delay": 50,
                "recoil_control": False,
                "recoil_strength": 1.0,
                "target_area_size": 8,
                "scan_fps": 150,
                "color_tolerance": 10,
                "auto_reload": False,
                "reload_key": "r",
                "safety_delay": 100
            },
            "anti_smoke": {
                "enabled": False,
                "detection_sensitivity": 0.7,
                "scan_area_size": 50,
                "update_frequency": 30,
                "show_detection_area": False
            },
            "general": {
                "startup_theme": ColorTheme.LIGHT.value,
                "auto_start_services": False,
                "minimize_to_tray": True,
                "show_notifications": True,
                "language": "tr",
                "update_check": True,
                "debug_logging": False,
                "performance_mode": False
            },
            "hotkeys": {
                "toggle_visibility": "insert",
                "emergency_stop": "f12",
                "quick_settings": "f11",
                "screenshot": "f10"
            },
            "performance": {
                "cpu_priority": "normal",
                "memory_optimization": True,
                "gpu_acceleration": True,
                "thread_count": 4,
                "cache_size": 100,
                "auto_cleanup": True
            }
        }

    def load_config(self) -> Dict[str, Any]:
        print(f"🔧 Loading config from: {self.config_path}")
        print(f"📁 Config file exists: {os.path.exists(self.config_path)}")
        
        if not os.path.exists(self.config_path):
            print("📝 Config file not found, creating default config...")
            success, message = self.save_config(self._default_config)
            print(f"💾 Default config save result: {success} - {message}")
            return self._default_config.copy()

        try:
            print("📖 Reading existing config file...")
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            print(f"✅ Config loaded successfully. Sections: {list(loaded_config.keys())}")
            merged_config = self._merge_configs(self._default_config, loaded_config)
            print(f"🔀 Config merged. Final sections: {list(merged_config.keys())}")
            return merged_config

        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"❌ Config yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            self._backup_corrupted_config()
            return self._default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        try:
            print(f"💾 Saving config to: {self.config_path}")
            print(f"📁 Config dir exists: {os.path.exists(self.config_dir)}")
            print(f"🔧 Config sections to save: {list(config.keys())}")
            
            # Config dizininin var olduğundan emin ol
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Backup oluştur
            self._create_backup()
            
            # Config'i kaydet
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Dosyanın gerçekten kaydedildiğini kontrol et
            if os.path.exists(self.config_path):
                file_size = os.path.getsize(self.config_path)
                print(f"✅ Config saved successfully. File size: {file_size} bytes")
                return True, "Ayarlar başarıyla kaydedildi."
            else:
                print("❌ Config file was not created!")
                return False, "Config dosyası oluşturulamadı!"

        except Exception as e:
            print(f"❌ Config save error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Ayarlar kaydedilemedi: {e}"

    def get_section(self, section_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        if config is None:
            config = self.load_config()
        return config.get(section_name, {})

    def set_section(self, section_name: str, section_data: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        if config is None:
            config = self.load_config()
        config[section_name] = section_data
        return config

    def get_value(self, section: str, key: str, default: Any = None, config: Optional[Dict] = None) -> Any:
        if config is None:
            config = self.load_config()
        return config.get(section, {}).get(key, default)

    def set_value(self, section: str, key: str, value: Any, config: Optional[Dict] = None) -> Dict[str, Any]:
        if config is None:
            config = self.load_config()
        if section not in config:
            config[section] = {}
        config[section][key] = value
        return config

    def reset_to_defaults(self) -> Dict[str, Any]:
        default_config = self._default_config.copy()
        self.save_config(default_config)
        return default_config

    def reset_section(self, section_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        if config is None:
            config = self.load_config()
        if section_name in self._default_config:
            config[section_name] = self._default_config[section_name].copy()
        return config

    def export_config(self, export_path: str) -> tuple[bool, str]:
        try:
            print(f"📤 Exporting config to: {export_path}")
            config = self.load_config()
            print(f"🔧 Config sections to export: {list(config.keys())}")
            
            # Export dizininin var olduğundan emin ol
            export_dir = os.path.dirname(export_path)
            if export_dir and not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Dosyanın gerçekten oluştuğunu kontrol et
            if os.path.exists(export_path):
                file_size = os.path.getsize(export_path)
                print(f"✅ Config exported successfully. File size: {file_size} bytes")
                return True, f"Ayarlar {export_path} dosyasına aktarıldı."
            else:
                print("❌ Export file was not created!")
                return False, "Export dosyası oluşturulamadı!"
                
        except Exception as e:
            print(f"❌ Export error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Dışa aktarma hatası: {e}"

    def import_config(self, import_path: str) -> tuple[bool, str]:
        try:
            print(f"📥 Importing config from: {import_path}")
            print(f"📁 Import file exists: {os.path.exists(import_path)}")
            
            if not os.path.exists(import_path):
                return False, "İçe aktarılacak dosya bulunamadı!"
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            print(f"🔧 Imported config sections: {list(imported_config.keys())}")
            
            if self._validate_config(imported_config):
                print("✅ Config validation passed")
                success, message = self.save_config(imported_config)
                if success:
                    print("✅ Config imported and saved successfully")
                    return True, "Ayarlar başarıyla içe aktarıldı."
                else:
                    print(f"❌ Failed to save imported config: {message}")
                    return False, f"İçe aktarılan config kaydedilemedi: {message}"
            else:
                print("❌ Config validation failed")
                return False, "Geçersiz config dosyası. Gerekli bölümler eksik."

        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return False, f"Geçersiz JSON dosyası: {e}"
        except Exception as e:
            print(f"❌ Import error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"İçe aktarma hatası: {e}"

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        merged = default.copy()

        def deep_merge(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_merge(merged, loaded)
        return merged

    def _validate_config(self, config: Dict) -> bool:
        """Config'in geçerli olup olmadığını kontrol et"""
        required_sections = ["theme", "aimbot", "triggerbot", "general"]
        
        print(f"🔍 Validating config...")
        print(f"📋 Required sections: {required_sections}")
        print(f"📋 Available sections: {list(config.keys())}")
        
        missing_sections = []
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing sections: {missing_sections}")
            return False
        else:
            print("✅ All required sections found")
            return True

    def _create_backup(self):
        if os.path.exists(self.config_path):
            backup_path = self.config_path + ".backup"
            try:
                import shutil
                shutil.copy2(self.config_path, backup_path)
            except:
                pass

    def _backup_corrupted_config(self):
        if os.path.exists(self.config_path):
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted_path = f"{self.config_path}.corrupted_{timestamp}"
            try:
                import shutil
                shutil.move(self.config_path, corrupted_path)
            except:
                pass

    def get_config_info(self) -> Dict[str, Any]:
        config = self.load_config()
        return {
            "config_path": self.config_path,
            "config_size": os.path.getsize(self.config_path) if os.path.exists(self.config_path) else 0,
            "sections": list(config.keys()),
            "last_modified": os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
        }
    
    def clean_old_config_sections(self) -> tuple[bool, str]:
        """Eski config dosyasından istenmeyen bölümleri temizle"""
        try:
            if not os.path.exists(self.config_path):
                return True, "Config dosyası bulunamadı."
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            removed_sections = []
            unwanted_sections = ["version", "statistics", "profiles", "security", "ui"]
            
            for section in unwanted_sections:
                if section in config:
                    del config[section]
                    removed_sections.append(section)
            
            if removed_sections:
                self.save_config(config)
                return True, f"Temizlenen bölümler: {', '.join(removed_sections)}"
            else:
                return True, "Temizlenecek bölüm bulunamadı."
                
        except Exception as e:
            return False, f"Temizleme hatası: {e}"


# Global instance
advanced_config = AdvancedConfigManager()
