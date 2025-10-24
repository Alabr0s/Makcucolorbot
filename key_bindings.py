from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, QCheckBox
from PyQt5.QtCore import Qt
from utils import KeyCaptureButton


class KeyBindingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        group_box = QGroupBox("Key Bindings")
        form_layout = QFormLayout(group_box)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Key bindings
        key_settings = [
            ("fire_key", "Fire Key:"),
            ("toggle_key", "Toggle Key:"),
            ("hold_key", "Hold Key:")
        ]
        
        for key, label_text in key_settings:
            label = QLabel(label_text)
            widget = KeyCaptureButton()
            form_layout.addRow(label, widget)
            self.widgets[key] = widget
        
        # Checkbox setting
        use_holdkey_label = QLabel("Use Hold Key:")
        use_holdkey_checkbox = QCheckBox("Active")
        form_layout.addRow(use_holdkey_label, use_holdkey_checkbox)
        self.widgets["use_holdkey"] = use_holdkey_checkbox
        
        layout.addWidget(group_box)
        layout.addStretch()

    def get_widgets(self):
        """Return widgets to main application"""
        return self.widgets

    def load_settings(self, config):
        """Load settings"""
        for key, widget in self.widgets.items():
            if key in config:
                value_str = config[key]
                if isinstance(widget, QCheckBox):
                    widget.setChecked(value_str.lower() == 'true')
                elif isinstance(widget, KeyCaptureButton):
                    widget.setText(value_str)

    def save_settings(self):
        """Save settings"""
        settings = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, QCheckBox):
                settings[key] = 'true' if widget.isChecked() else 'false'
            elif isinstance(widget, KeyCaptureButton):
                settings[key] = widget.text()
        return settings