"""
RCS (Recoil Control System) Settings View
Provides UI controls for recoil control configuration with Weapon Patterns
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QSpinBox, QCheckBox, QGroupBox, QGridLayout,
    QFrame, QComboBox, QScrollArea, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor
from controllers.rcs_controller import RCSController

class RCSSettingsTab(QWidget):
    """RCS Settings Tab for recoil control configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.active_weapon_btn = None
        
        # Initialize Controller
        self.controller = RCSController()
        self.controller.connection_status_changed.connect(self.on_connection_status)
        self.controller.start()
        
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #333;")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        header_layout.setSpacing(15)
        
        title_label = QLabel("RECOIL CONTROL")
        title_label.setStyleSheet("color: #fff; font-size: 20px; font-weight: 900; letter-spacing: 2px;")
        
        # Status Badge
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setStyleSheet("""
            background-color: #2d2d2d; 
            color: #666; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-weight: bold; 
            font-size: 10px;
            letter-spacing: 1px;
        """)
        
        self.rcs_enabled_cb = QCheckBox("ACTIVATE SYSTEM")
        self.rcs_enabled_cb.setCursor(Qt.PointingHandCursor)
        self.rcs_enabled_cb.setStyleSheet("""
            QCheckBox { color: #fff; font-weight: bold; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 36px; height: 18px; border-radius: 9px; background: #333; }
            QCheckBox::indicator:checked { background: #00cc66; }
        """)
        self.rcs_enabled_cb.stateChanged.connect(self.on_rcs_enabled_changed)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.rcs_enabled_cb)
        
        main_layout.addWidget(header_frame)
        
        # --- Content Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background: #121212;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # 1. Weapon Support (Cards)
        preset_label = QLabel("WEAPON CONFIGURATION")
        preset_label.setStyleSheet("color: #666; font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        content_layout.addWidget(preset_label)
        
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(15)
        
        # Define weapon cards
        # Name, Icon(opt), Description, Color
        weapons = [
            ("VANDAL", "image/vandal.png", "High recoil, precise tap.", "#ecc94b"),
            ("PHANTOM", "image/phantom.png", "Fast fire rate, suppress.", "#4299e1"), 
            ("SPECTRE", "image/spectre.png", "Close range, run & gun.", "#805ad5")
        ]
        
        self.weapon_btns = {}
        for name, icon_path, desc, color in weapons:
            card = self.create_weapon_card(name, icon_path, desc, color)
            preset_layout.addWidget(card)
            self.weapon_btns[name] = card
            
        content_layout.addLayout(preset_layout)
        
        # Manual Selection (Combo)
        combo_layout = QHBoxLayout()
        combo_lbl = QLabel("Manual Selection:")
        combo_lbl.setStyleSheet("color: #888; font-weight: bold; font-size: 12px;")
        
        self.weapon_combo = QComboBox()
        self.weapon_combo.addItems(self.controller.db.get_all_names())
        self.weapon_combo.currentTextChanged.connect(self.on_weapon_changed)
        self.weapon_combo.setFixedSize(200, 35)
        self.weapon_combo.setStyleSheet("""
            QComboBox {
                background: #1a1a1a; border: 1px solid #333; border-radius: 5px; color: white; padding-left: 10px; font-weight: bold;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #252525; selection-background-color: #333; color: white; }
        """)
        
        combo_layout.addWidget(combo_lbl)
        combo_layout.addWidget(self.weapon_combo)
        combo_layout.addStretch()
        content_layout.addLayout(combo_layout)
        
        # 2. Control Parameters
        settings_frame = QFrame()
        settings_frame.setStyleSheet("background-color: #181818; border-radius: 15px;")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(25, 25, 25, 25)
        settings_layout.setSpacing(20)
        
        p_label = QLabel("CONTROL PARAMETERS")
        p_label.setStyleSheet("color: #666; font-weight: 900; letter-spacing: 2px; font-size: 11px;")
        settings_layout.addWidget(p_label)
        
        # Strength Slider
        self.strength_slider = self.create_slider("Recoil Control Strength", 0, 100, 100, "%")
        settings_layout.addWidget(self.strength_slider[0])
        self.strength_slider[1].valueChanged.connect(self.on_strength_changed)
        
        # Integration Settings
        int_lbl = QLabel("INTEGRATION & MISC")
        int_lbl.setStyleSheet("color: #666; font-weight: 900; letter-spacing: 2px; font-size: 11px; margin-top: 10px;")
        settings_layout.addWidget(int_lbl)
        
        checks_layout = QHBoxLayout()
        checks_layout.setSpacing(30)
        
        self.aimbot_integration_cb = QCheckBox("Cancel Aimbot Drag (Vertical)")
        self.aimbot_integration_cb.setChecked(True)
        self.aimbot_integration_cb.setStyleSheet(self.get_checkbox_style())
        
        self.reset_recoil_cb = QCheckBox("Reset Mouse Position")
        self.reset_recoil_cb.setChecked(True)
        self.reset_recoil_cb.setStyleSheet(self.get_checkbox_style())
        self.reset_recoil_cb.stateChanged.connect(self.on_reset_recoil_changed)
        
        checks_layout.addWidget(self.aimbot_integration_cb)
        checks_layout.addWidget(self.reset_recoil_cb)
        checks_layout.addStretch()
        
        settings_layout.addLayout(checks_layout)
        
        content_layout.addWidget(settings_frame)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Initial State
        current_wep = self.weapon_combo.currentText()
        if current_wep: 
            self.on_weapon_changed(current_wep)
            
        # Initialize Strength
        self.on_strength_changed(self.strength_slider[1].value())

    def create_weapon_card(self, name, icon, desc, color):
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(90)
        btn.clicked.connect(lambda: self.set_weapon_from_card(name))
        
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: white; font-weight: 900; font-size: 18px; letter-spacing: 1px; background: transparent;")
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; background: transparent; opacity: 0.8;")
        
        text_layout.addWidget(name_lbl)
        text_layout.addWidget(desc_lbl)
        text_layout.addStretch()
        
        # Icon
        icon_lbl = QLabel()
        if icon:
            pix = QPixmap(icon)
            if not pix.isNull():
                 icon_lbl.setPixmap(pix.scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_lbl.setStyleSheet("background: transparent;")
        
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(icon_lbl)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-left: 4px solid {color};
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #252525, stop:1 #1a1a1a);
                border: 1px solid {color};
                border-left: 6px solid {color};
            }}
            QPushButton:checked {{
                background-color: #222;
                border: 1px solid {color};
            }}
        """)
        return btn

    def create_slider(self, label_text, min_val, max_val, default_val, unit):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        header = QHBoxLayout()
        header_lbl = QLabel(label_text)
        header_lbl.setStyleSheet("color: #ccc; font-weight: 600; font-size: 12px;")
        
        val_lbl = QLabel(f"{default_val}{unit}")
        val_lbl.setStyleSheet("color: #fff; font-weight: bold; font-family: monospace;")
        
        header.addWidget(header_lbl)
        header.addStretch()
        header.addWidget(val_lbl)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #333; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00cc66; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
        """)
        
        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}{unit}"))
        
        layout.addLayout(header)
        layout.addWidget(slider)
        
        return container, slider

    def get_checkbox_style(self):
        return """
            QCheckBox { color: #ccc; font-weight: 600; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; background: #333; border: 1px solid #555; }
            QCheckBox::indicator:checked { background: #00cc66; border: 1px solid #00aa55; }
        """

    def set_weapon_from_card(self, weapon_name):
        # Update combo box, which triggers on_weapon_changed
        # We need to map card name (VANDAL) to combo name (Vandal likely)
        # Assuming case insensitive match or direct match
        
        # Find match in combo
        for i in range(self.weapon_combo.count()):
            if self.weapon_combo.itemText(i).upper() == weapon_name.upper():
                self.weapon_combo.setCurrentIndex(i)
                break
        
        self.update_active_card(weapon_name)

    def update_active_card(self, active_name):
        # Uncheck all first
        for name, btn in self.weapon_btns.items():
            btn.setChecked(False)
            
        # Check active if exists
        for name, btn in self.weapon_btns.items():
            if name.upper() == active_name.upper():
                btn.setChecked(True)

    def on_rcs_enabled_changed(self, state):
        enabled = (state == Qt.Checked)
        self.controller.set_enabled(enabled)
        if enabled:
            self.status_label.setText("SYSTEM ACTIVE")
            self.status_label.setStyleSheet("background-color: #00cc66; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;")
        else:
            self.status_label.setText("Howl-RCS OFF")
            self.status_label.setStyleSheet("background-color: #2d2d2d; color: #666; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;")

    def on_weapon_changed(self, text):
        self.controller.set_weapon(text)
        self.update_active_card(text)
    
    def on_strength_changed(self, val):
        self.controller.set_strength(val)
        
    def on_reset_recoil_changed(self, state):
        enabled = (state == Qt.Checked)
        self.controller.set_reset_enabled(enabled)
    
    def on_connection_status(self, connected):
        if connected:
            self.status_label.setText("CONNECTED")
        else:
            self.status_label.setText("DISCONNECTED")
            self.status_label.setStyleSheet("background-color: #e53e3e; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px;")

    def get_rcs_worker(self):
        # Compatibility method
        return self.controller.worker
    
    def is_aimbot_integration_enabled(self):
        return self.aimbot_integration_cb.isChecked()
    
    def cleanup(self):
        self.controller.stop()

    def load_settings(self, settings):
        if "rcs_enabled" in settings:
            self.rcs_enabled_cb.setChecked(settings["rcs_enabled"] == "true")
        if "recoil_strength" in settings:
            val = int(settings["recoil_strength"])
            # Tuple access
            self.strength_slider[1].setValue(val)
        if "weapon" in settings:
            self.weapon_combo.setCurrentText(settings["weapon"])
        if "rcs_reset_enabled" in settings:
             self.reset_recoil_cb.setChecked(settings["rcs_reset_enabled"] == "true")
        if "aimbot_integration_enabled" in settings:
             self.aimbot_integration_cb.setChecked(settings["aimbot_integration_enabled"] == "true")
        
        self.update_active_card(self.weapon_combo.currentText())

    def get_settings(self):
        return {
            "rcs_enabled": "true" if self.rcs_enabled_cb.isChecked() else "false",
            "recoil_strength": str(self.strength_slider[1].value()),
            "weapon": self.weapon_combo.currentText(),
            "rcs_reset_enabled": "true" if self.reset_recoil_cb.isChecked() else "false",
            "aimbot_integration_enabled": "true" if self.aimbot_integration_cb.isChecked() else "false"
        }
