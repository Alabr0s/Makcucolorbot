
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
                             QPushButton, QLineEdit, QListWidget, QListWidgetItem, 
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from models.config_manager import ConfigManager
import os

class ConfigSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # This should be MainWindow
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.refresh_config_list()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Header ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #333;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        header_layout.setSpacing(15)
        
        title_label = QLabel("CONFIGURATION")
        title_label.setStyleSheet("color: #fff; font-size: 20px; font-weight: 900; letter-spacing: 2px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addWidget(header_frame)
        
        # --- Content ---
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #121212;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        # New Config Section
        new_config_frame = QFrame()
        new_config_frame.setStyleSheet("""
            QFrame {
                background-color: #181818;
                border-radius: 12px;
                border: 1px solid #333;
            }
        """)
        new_layout = QHBoxLayout(new_config_frame)
        new_layout.setContentsMargins(20, 20, 20, 20)
        
        self.config_name_input = QLineEdit()
        self.config_name_input.setPlaceholderText("Enter config name...")
        self.config_name_input.setFixedHeight(40)
        self.config_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: white;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 0 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 1px solid #00cc66;
            }
        """)
        
        save_btn = QPushButton("SAVE NEW CONFIG")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_current_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00cc66, stop:1 #00aa55);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00dd77, stop:1 #00bb66);
            }
            QPushButton:pressed {
                background-color: #009944;
            }
        """)
        
        new_layout.addWidget(self.config_name_input)
        new_layout.addWidget(save_btn)
        
        content_layout.addWidget(new_config_frame)
        
        # Config List & Actions
        list_container = QWidget()
        list_layout = QHBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(20)
        
        # List
        self.config_list = QListWidget()
        self.config_list.setStyleSheet("""
            QListWidget {
                background-color: #181818;
                border-radius: 12px;
                border: 1px solid #333;
                outline: none;
                padding: 10px;
            }
            QListWidget::item {
                background-color: #252525;
                color: white;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 8px;
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: #333;
                border-left: 3px solid #00cc66;
            }
            QListWidget::item:hover:!selected {
                background-color: #2d2d2d;
            }
        """)
        self.config_list.itemDoubleClicked.connect(self.load_selected_config)
        
        list_layout.addWidget(self.config_list)
        
        # Action Buttons
        actions_frame = QFrame()
        actions_frame.setFixedWidth(200)
        # actions_frame.setStyleSheet("background-color: #181818; border-radius: 12px; border: 1px solid #333;")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(15)
        
        def create_action_btn(text, color, callback):
            btn = QPushButton(text)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #252525;
                    border: 1px solid {color};
                    border-left: 4px solid {color};
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    text-align: left;
                    padding-left: 20px;
                }}
                QPushButton:hover {{
                    background-color: #333;
                    border-left: 6px solid {color};
                }}
            """)
            return btn
            
        load_btn = create_action_btn("LOAD SELECTED", "#00cc66", self.load_selected_config)
        delete_btn = create_action_btn("DELETE", "#e53e3e", self.delete_selected_config)
        import_btn = create_action_btn("IMPORT FILE", "#4299e1", self.import_config_file)
        
        actions_layout.addWidget(load_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addWidget(import_btn)
        actions_layout.addStretch()
        
        list_layout.addWidget(actions_frame)
        
        content_layout.addWidget(list_container)
        
        main_layout.addWidget(content_widget)

    def refresh_config_list(self):
        """Reload config list"""
        self.config_list.clear()
        configs = self.config_manager.get_all_configs()
        for name in configs:
            item = QListWidgetItem(name)
            self.config_list.addItem(item)
            
    def save_current_config(self):
        """Collect data from all tabs and save"""
        name = self.config_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a config name")
            return
            
        if not self.parent_window:
            print("❌ Parent window not linked!")
            return
            
        # Collect Data
        full_config = {}
        
        # 1. Color Settings
        if hasattr(self.parent_window, 'color_tab'):
            full_config['color_settings'] = self.parent_window.color_tab.get_settings()
            
        # 2. Triggerbot Settings
        if hasattr(self.parent_window, 'fire_tab'):
            full_config['triggerbot_settings'] = self.parent_window.fire_tab.get_settings()
            
        # 3. RCS Settings
        if hasattr(self.parent_window, 'rcs_tab'):
            full_config['rcs_settings'] = self.parent_window.rcs_tab.get_settings()
            
        # 4. Aimbot Settings
        if hasattr(self.parent_window, 'aimbot_tab'):
            full_config['aimbot_settings'] = self.parent_window.aimbot_tab.get_settings()
            
        # 5. Spike Timer Settings
        if hasattr(self.parent_window, 'spike_timer_tab'):
            full_config['spike_timer_settings'] = self.parent_window.spike_timer_tab.get_settings()
            
        # Save
        success, msg = self.config_manager.save_config(name, full_config)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.refresh_config_list()
            self.config_name_input.clear()
        else:
            QMessageBox.warning(self, "Error", msg)

    def load_selected_config(self):
        """Load selected config to all tabs"""
        item = self.config_list.currentItem()
        if not item:
            return
            
        name = item.text()
        data, msg = self.config_manager.load_config(name)
        
        if not data:
            QMessageBox.warning(self, "Error", msg)
            return
            
        if not self.parent_window:
            return
            
        try:
            # Distribute Data
            if 'color_settings' in data and hasattr(self.parent_window, 'color_tab'):
                self.parent_window.color_tab.load_settings(data['color_settings'])
                
            if 'triggerbot_settings' in data and hasattr(self.parent_window, 'fire_tab'):
                self.parent_window.fire_tab.load_settings(data['triggerbot_settings'])
                
            if 'rcs_settings' in data and hasattr(self.parent_window, 'rcs_tab'):
                self.parent_window.rcs_tab.load_settings(data['rcs_settings'])
                
            if 'aimbot_settings' in data and hasattr(self.parent_window, 'aimbot_tab'):
                self.parent_window.aimbot_tab.load_settings(data['aimbot_settings'])
                
            if 'spike_timer_settings' in data and hasattr(self.parent_window, 'spike_timer_tab'):
                self.parent_window.spike_timer_tab.load_settings(data['spike_timer_settings'])
                
            QMessageBox.information(self, "Success", f"Config '{name}' loaded successfully!")
            
        except Exception as e:
             QMessageBox.warning(self, "Error", f"Error applying config: {e}")
             import traceback
             traceback.print_exc()

    def delete_selected_config(self):
        """Delete config"""
        item = self.config_list.currentItem()
        if not item:
            return
            
        name = item.text()
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete '{name}'?", QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            success, msg = self.config_manager.delete_config(name)
            if success:
                self.refresh_config_list()
            else:
                QMessageBox.warning(self, "Error", msg)

    def import_config_file(self):
        """Import from file"""
        path, _ = QFileDialog.getOpenFileName(self, "Import Config", "", "JSON Files (*.json)")
        if path:
            success, msg = self.config_manager.import_config(path)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.refresh_config_list()
            else:
                QMessageBox.warning(self, "Error", msg)
