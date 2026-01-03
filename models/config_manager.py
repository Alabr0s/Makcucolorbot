
import os
import json
import shutil
from datetime import datetime

class ConfigManager:
    def __init__(self):
        self.app_data_path = os.path.join(os.getenv('APPDATA'), 'ds-color')
        self.config_path = os.path.join(self.app_data_path, 'config')
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure config directories exist"""
        os.makedirs(self.config_path, exist_ok=True)
        
    def get_all_configs(self):
        """Get list of all saved config names"""
        if not os.path.exists(self.config_path):
            return []
            
        configs = []
        for file in os.listdir(self.config_path):
            if file.endswith('.json'):
                configs.append(file.replace('.json', ''))
        return sorted(configs)
    
    def save_config(self, name, data):
        """Save configuration to file"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['meta'] = {
                'name': name,
                'last_updated': timestamp,
                'version': '2.4.0'
            }
            
            filename = f"{name}.json"
            filepath = os.path.join(self.config_path, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return True, f"Config '{name}' saved successfully"
            
        except Exception as e:
            return False, str(e)
            
    def load_config(self, name):
        """Load configuration from file"""
        try:
            filename = f"{name}.json"
            filepath = os.path.join(self.config_path, filename)
            
            if not os.path.exists(filepath):
                return None, "Config file not found"
                
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data, "Success"
            
        except Exception as e:
            return None, str(e)
            
    def delete_config(self, name):
        """Delete configuration file"""
        try:
            filename = f"{name}.json"
            filepath = os.path.join(self.config_path, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, f"Config '{name}' deleted"
            return False, "Config not found"
            
        except Exception as e:
            return False, str(e)
            
    def import_config(self, source_path):
        """Import config from external file"""
        try:
            if not os.path.exists(source_path):
                return False, "Source file not found"
                
            # Validate JSON first
            with open(source_path, 'r') as f:
                try:
                    json.load(f)
                except json.JSONDecodeError:
                    return False, "Invalid JSON file"
            
            filename = os.path.basename(source_path)
            dest_path = os.path.join(self.config_path, filename)
            
            shutil.copy2(source_path, dest_path)
            return True, f"Imported {filename}"
            
        except Exception as e:
            return False, str(e)
            
    def get_config_path(self, name):
        return os.path.join(self.config_path, f"{name}.json")
