from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSlider, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, QInputDialog, 
                             QMessageBox, QSplitter, QFrame, QScrollArea, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QImage, QPixmap, QPainterPath
from controllers.theme_controller import WindowColorManager
from models.color_palette import ColorTheme
import colorsys
import cv2
import numpy as np
import json
import os


class ColorSpectrumWidget(QWidget):
    """Widget displaying HSV color spectrum
    
    Note: OpenCV Hue values range from 0-180.
    This widget converts OpenCV values to standard HSV (0-360) for display.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 60)
        self.setMaximumHeight(80)
        # OpenCV Hue values (0-180)
        self.hue_min = 140  # 280° (purple/violet)
        self.hue_max = 150  # 300° (purple/violet)
        
    def update_hue_range(self, hue_min, hue_max):
        """Update hue range (OpenCV format 0-180)"""
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.update()
        
    def paintEvent(self, event):
        """Draw the spectrum"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(40, 40, 40, 200))
        
        # Draw full spectrum (0-360 degrees)
        spectrum_height = 40
        spectrum_y = 10
        
        # Draw a color for each degree
        for i in range(360):
            h = i / 360.0
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            color = QColor(int(r * 255), int(g * 255), int(b * 255))
            
            x = int((i / 360.0) * (self.width() - 20)) + 10
            painter.setPen(QPen(color, 2))
            painter.drawLine(x, spectrum_y, x, spectrum_y + spectrum_height)
        
        # Convert OpenCV Hue values to standard HSV (0-180 -> 0-360)
        # Example: 140 -> 280°, 150 -> 300° (purple/violet region)
        hue_min_degrees = self.hue_min * 2
        hue_max_degrees = self.hue_max * 2
        
        # Highlight selected range
        min_x = int((hue_min_degrees / 360.0) * (self.width() - 20)) + 10
        max_x = int((hue_max_degrees / 360.0) * (self.width() - 20)) + 10
        
        # Selected range border
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(min_x, spectrum_y - 2, max_x - min_x, spectrum_height + 4)
        
        # Show selected color at bottom
        h = ((hue_min_degrees + hue_max_degrees) / 2.0) / 360.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.7, 0.9)
        selected_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        
        painter.setBrush(QBrush(selected_color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(10, spectrum_y + spectrum_height + 10, self.width() - 20, 15)


class ColorPreviewWidget(QWidget):
    """Widget displaying HSV color values as a human figure
    
    Note: OpenCV Hue values range from 0-180.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 400)
        # OpenCV Hue values (0-180)
        self.hue_min = 140  # 280° (purple/violet)
        self.hue_max = 150  # 300° (purple/violet)
        self.sat_min = 0.43  # Medium-high saturation
        self.sat_max = 0.76
        self.val_min = 150  # Bright
        self.val_max = 255
        
    def update_color_values(self, hue_min, hue_max, sat_min, sat_max, val_min, val_max):
        """Update color values"""
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.sat_min = sat_min
        self.sat_max = sat_max
        self.val_min = val_min
        self.val_max = val_max
        self.update()  # Redraw widget
        
    def get_preview_color(self):
        """Calculate average color for preview"""
        # Get average HSV values
        # OpenCV Hue (0-180) -> Standard HSV (0-360) -> Normalize (0-1)
        hue_opencv = (self.hue_min + self.hue_max) / 2.0
        hue_degrees = hue_opencv * 2  # 145 -> 290° (purple)
        h = hue_degrees / 360.0  # Normalize to 0-1 range
        
        s = (self.sat_min + self.sat_max) / 2.0
        v = (self.val_min + self.val_max) / 2.0 / 255.0  # Normalize to 0-1 range
        
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        return QColor(int(r * 255), int(g * 255), int(b * 255))
        
    def paintEvent(self, event):
        """Draw the widget"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background with grid effect for better contrast
        bg_color = QColor(30, 30, 30)
        painter.fillRect(self.rect(), bg_color)
        
        # Draw subtle grid
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
        grid_size = 20
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        # Get preview color
        color = self.get_preview_color()
        
        # Determine center
        cx = self.width() // 2
        cy = self.height() // 2 + 20
        scale = 1.2  # Scale up the character
        
        painter.translate(cx, cy)
        painter.scale(scale, scale)
        painter.translate(-cx, -cy)

        # Create tactical operator path
        path = QPainterPath()
        
        # Head (Helmet shape)
        path.addEllipse(cx - 25, cy - 140, 50, 55) # Base head
        
        # Body armor / Chest
        path.moveTo(cx - 30, cy - 90)
        path.lineTo(cx + 30, cy - 90)  # Shoulders
        path.lineTo(cx + 45, cy - 20)  # Chest sides
        path.lineTo(cx + 35, cy + 50)  # Waist
        path.lineTo(cx - 35, cy + 50)
        path.lineTo(cx - 45, cy - 20)
        path.closeSubpath()
        
        # Arms (Holding a weapon stance)
        # Left Arm
        path.moveTo(cx - 45, cy - 80)
        path.lineTo(cx - 70, cy - 20)  # Elbow
        path.lineTo(cx - 40, cy + 10)  # Hand
        path.lineTo(cx - 30, cy - 10)
        path.lineTo(cx - 38, cy - 75)
        path.closeSubpath()
        
        # Right Arm
        path.moveTo(cx + 45, cy - 80)
        path.lineTo(cx + 70, cy - 20)
        path.lineTo(cx + 40, cy + 10)
        path.lineTo(cx + 30, cy - 10)
        path.lineTo(cx + 38, cy - 75)
        path.closeSubpath()
        
        # Legs (Combat pants)
        # Left Leg
        path.moveTo(cx - 35, cy + 50)
        path.lineTo(cx - 45, cy + 140)
        path.lineTo(cx - 15, cy + 140)
        path.lineTo(cx - 5, cy + 60)
        path.closeSubpath()
        
        # Right Leg
        path.moveTo(cx + 35, cy + 50)
        path.lineTo(cx + 45, cy + 140)
        path.lineTo(cx + 15, cy + 140)
        path.lineTo(cx + 5, cy + 60)
        path.closeSubpath()

        # Fill with main color
        glow = QColor(color)
        glow.setAlpha(100)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(glow, 8))
        painter.drawPath(path) # Glow effect
        
        painter.setBrush(QBrush(color.darker(150))) # Darker inner fill
        painter.setPen(QPen(color, 3)) # Bright outline
        painter.drawPath(path)
        
        # Draw "Headshot" zone highlight (The most important part)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - 20, cy - 135, 40, 40) # Inner face/visor glow
        
        # Draw a simple weapon silhouette
        w_path = QPainterPath()
        w_path.moveTo(cx - 40, cy + 5)
        w_path.lineTo(cx + 40, cy + 5)
        w_path.lineTo(cx + 40, cy + 25)
        w_path.lineTo(cx - 10, cy + 25)
        w_path.lineTo(cx - 15, cy + 40) # Grip
        w_path.lineTo(cx - 25, cy + 40)
        w_path.lineTo(cx - 30, cy + 25)
        w_path.lineTo(cx - 40, cy + 25)
        w_path.closeSubpath()
        
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawPath(w_path)
        
        # Reset transform for text
        painter.resetTransform()
        
        # Color info text overlay
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        
        margin = 15
        line_height = 20
        y_pos = margin + 15
        
        # Helper to draw text with shadow
        def draw_shadowed_text(x, y, text):
            painter.setPen(QColor(0, 0, 0, 200))
            painter.drawText(x+1, y+1, text)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x, y, text)

        draw_shadowed_text(margin, y_pos, f"HSV: [{self.hue_min:.0f}-{self.hue_max:.0f}, {self.sat_min:.2f}-{self.sat_max:.2f}, {self.val_min:.0f}-{self.val_max:.0f}]")
        y_pos += line_height
        
        # Show Color Hex Code
        draw_shadowed_text(margin, y_pos, f"RGB: {color.name().upper()}")


class HSVToolWindow(QWidget):
    """Separate window for fine-tuning HSV values on a real image"""
    
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window) # Fix: Parent + Window flag prevents app exit
        self.setWindowTitle("HSV Tuning Tool")
        self.resize(1100, 750)
        self.image = None
        self.processed_image = None
        self.original_pixmap = None
        
        # Default HSV values
        self.h_min = 0
        self.h_max = 180
        self.s_min = 0
        self.s_max = 255  
        self.v_min = 0
        self.v_max = 255
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        # Main Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # --- Left Panel: Controls ---
        left_card = QFrame()
        left_card.setObjectName("controlPanel")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        # Title
        title = QLabel("TUNING CONTROLS")
        title.setObjectName("sectionTitle")
        left_layout.addWidget(title)
        
        # Image Load Section
        img_layout = QHBoxLayout()
        load_btn = QPushButton("LOAD IMAGE")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.setObjectName("actionBtn")
        load_btn.clicked.connect(self.load_image)
        img_layout.addWidget(load_btn)
        left_layout.addLayout(img_layout)
        
        # Presets
        presets_label = QLabel("QUICK PRESETS")
        presets_label.setObjectName("subTitle")
        left_layout.addWidget(presets_label)
        
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(10)
        for name, color in [("Purple", "#805ad5"), ("Red", "#e53e3e"), ("Yellow", "#ecc94b")]:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                    min-width: 60px;
                }}
                QPushButton:hover {{ background-color: {color}DD; }}
            """)
            btn.clicked.connect(lambda checked, n=name: self.apply_base_preset(n))
            presets_layout.addWidget(btn)
        left_layout.addLayout(presets_layout)
        
        # Sliders Section
        sliders_scroll = QScrollArea()
        sliders_scroll.setWidgetResizable(True)
        sliders_scroll.setFrameShape(QFrame.NoFrame)
        sliders_scroll.setStyleSheet("background: transparent;")
        
        sliders_content = QWidget()
        sliders_content.setStyleSheet("background: transparent;")
        sliders_layout = QVBoxLayout(sliders_content)
        sliders_layout.setSpacing(15)
        
        self.sliders = {}
        slider_configs = [
            ("Hue Min", 0, 180, "h_min", 1),
            ("Hue Max", 0, 180, "h_max", 1),
            ("Sat Min", 0, 255, "s_min", 255.0),
            ("Sat Max", 0, 255, "s_max", 255.0),
            ("Val Min", 0, 255, "v_min", 255.0),
            ("Val Max", 0, 255, "v_max", 255.0)
        ]
        
        for label, min_v, max_v, key, divisor in slider_configs:
            # Container
            container = QFrame()
            container.setStyleSheet("background: #252525; border-radius: 8px; padding: 5px;")
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(10, 5, 10, 5)
            v_layout.setSpacing(5)
            
            # Header
            h_row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold;")
            
            val_lbl = QLabel()
            val_lbl.setStyleSheet("color: #00cc66; font-weight: bold; font-family: monospace;")
            
            h_row.addWidget(lbl)
            h_row.addStretch()
            h_row.addWidget(val_lbl)
            v_layout.addLayout(h_row)
            
            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(getattr(self, key))
            
            # Initial text
            val = slider.value()
            if divisor != 1:
                val_lbl.setText(f"{val/divisor:.2f}")
            else:
                val_lbl.setText(str(val))
                
            slider.valueChanged.connect(lambda v, k=key, l=val_lbl, d=divisor: self.update_val(k, v, l, d))
            self.sliders[key] = slider
            v_layout.addWidget(slider)
            
            sliders_layout.addWidget(container)
            
        sliders_scroll.setWidget(sliders_content)
        left_layout.addWidget(sliders_scroll)
        
        # Save Button
        save_btn = QPushButton("SAVE CONFIGURATION")
        save_btn.setObjectName("saveBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_preset)
        left_layout.addWidget(save_btn)
        
        # --- Right Panel: Preview ---
        right_panel = QFrame()
        right_panel.setObjectName("previewPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #333; width: 2px; }
        """)
        
        self.orig_lbl = QLabel("No Image Loaded")
        self.orig_lbl.setAlignment(Qt.AlignCenter)
        self.orig_lbl.setStyleSheet("color: #555; font-weight: bold;")
        
        self.proc_lbl = QLabel("Result Preview")
        self.proc_lbl.setAlignment(Qt.AlignCenter)
        self.proc_lbl.setStyleSheet("color: #555; font-weight: bold;")
        
        orig_container = QFrame()
        orig_container.setStyleSheet("background: #151515;")
        QVBoxLayout(orig_container).addWidget(self.orig_lbl)
        
        proc_container = QFrame()
        proc_container.setStyleSheet("background: #151515;")
        QVBoxLayout(proc_container).addWidget(self.proc_lbl)
        
        splitter.addWidget(orig_container)
        splitter.addWidget(proc_container)
        splitter.setSizes([450, 450])
        
        right_layout.addWidget(splitter)
        
        # Add panels to Main
        # Left panel fixed width
        left_card.setFixedWidth(320)
        main_layout.addWidget(left_card)
        main_layout.addWidget(right_panel, stretch=1)
        
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { 
                background-color: #121212; 
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#controlPanel {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 12px;
            }
            QFrame#previewPanel {
                border: 1px solid #2d2d2d;
                border-radius: 12px;
                overflow: hidden;
            }
            QLabel#sectionTitle {
                color: #fff;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            QLabel#subTitle {
                color: #666;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-top: 10px;
            }
            QPushButton#actionBtn {
                background-color: #252525;
                color: #fff;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton#actionBtn:hover {
                background-color: #333;
                border: 1px solid #555;
            }
            QPushButton#saveBtn {
                background-color: #00cc66;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: 900;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton#saveBtn:hover {
                background-color: #00dd77;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #1a1a1a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #00cc66;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)

    def update_val(self, key, value, label_widget, divisor):
        setattr(self, key, value)
        if divisor != 1:
            label_widget.setText(f"{value/divisor:.2f}")
        else:
            label_widget.setText(str(value))
        self.process_image()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                max_h = 600
                h, w = img.shape[:2]
                if h > max_h:
                    scale = max_h / h
                    new_w = int(w * scale)
                    img = cv2.resize(img, (new_w, max_h))
                
                self.image = img
                self.process_image()
                
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = img_rgb.shape
                bytes_per_line = ch * w
                qimg = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.orig_lbl.setPixmap(QPixmap.fromImage(qimg).scaled(
                    self.orig_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def process_image(self):
        if self.image is None:
            return
            
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        lower = np.array([self.h_min, self.s_min, self.v_min])
        upper = np.array([self.h_max, self.s_max, self.v_max])
        mask = cv2.inRange(hsv, lower, upper)
        res = cv2.bitwise_and(self.image, self.image, mask=mask)
        
        res_rgb = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
        h, w, ch = res_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(res_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        self.proc_lbl.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.proc_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name:
            config_dir = os.path.join(os.getenv('APPDATA'), 'ds-color')
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, 'config.json')
            
            presets = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        presets = json.load(f)
                except:
                    pass
            
            preset_data = {
                "hue_min": self.h_min,
                "hue_max": self.h_max,
                "sat_min": int(self.s_min / 2.55),
                "sat_max": int(self.s_max / 2.55),
                "val_min": self.v_min,
                "val_max": self.v_max
            }
            
            presets[name] = preset_data
            
            with open(config_file, 'w') as f:
                json.dump(presets, f, indent=4)
                
            QMessageBox.information(self, "Success", f"Preset '{name}' saved successfully!")
            self.settings_saved.emit()

    def apply_base_preset(self, name):
        if name == "Purple":
            self.h_min, self.h_max = 140, 150
            self.s_min, self.s_max = 110, 194
            self.v_min, self.v_max = 150, 255
        elif name == "Red":
            self.h_min, self.h_max = 0, 10
            self.s_min, self.s_max = 179, 255
            self.v_min, self.v_max = 180, 255
        elif name == "Yellow":
            self.h_min, self.h_max = 20, 30
            self.s_min, self.s_max = 153, 255
            self.v_min, self.v_max = 180, 255
            
        for key in self.sliders:
            self.sliders[key].blockSignals(True)
            self.sliders[key].setValue(getattr(self, key))
            self.sliders[key].blockSignals(False)
            
        self.process_image()




class ColorSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.widgets = {}
        self.color_manager = WindowColorManager()
        self.current_theme = ColorTheme.LIGHT
        self.setup_ui()
    
    def get_slider_style(self, slider_type):
        """Return CSS style based on slider type"""
        base_style = """
            QSlider::groove:horizontal {
                height: 10px;
                border-radius: 5px;
                border: 1px solid rgba(100, 100, 100, 0.5);
                %s
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 255), 
                    stop:0.5 rgba(220, 220, 220, 255),
                    stop:1 rgba(255, 255, 255, 255));
                border: 2px solid rgba(100, 100, 100, 200);
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 255), 
                    stop:0.5 rgba(240, 240, 255, 255),
                    stop:1 rgba(255, 255, 255, 255));
                border: 2px solid rgba(150, 150, 200, 255);
            }
        """
        
        if slider_type == 'hue':
            gradient = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0.00 #FF0000,
                    stop:0.17 #FFFF00,
                    stop:0.33 #00FF00,
                    stop:0.50 #00FFFF,
                    stop:0.67 #0000FF,
                    stop:0.83 #FF00FF,
                    stop:1.00 #FF0000);
            """
        elif slider_type == 'saturation':
            gradient = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #808080,
                    stop:1 #9966CC);
            """
        elif slider_type == 'value':
            gradient = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #000000,
                    stop:1 #FFFFFF);
            """
        else:
            gradient = "background: rgba(30, 30, 30, 200);"
        
        return base_style % gradient

    def setup_ui(self):
        # Main layout container
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Hidden State Management (Compatibility) ---
        # We keep the sliders invisible so save/load/preview logic continues to work
        self.hidden_container = QWidget(self)
        self.hidden_container.setVisible(False)
        self.widgets = {}
        
        slider_configs = [
            ("hue_min", 0, 180), ("hue_max", 0, 180),
            ("sat_min", 0, 100), ("sat_max", 0, 100),
            ("val_min", 0, 255), ("val_max", 0, 255)
        ]
        
        default_values = {
            "hue_min": 140, "hue_max": 150,
            "sat_min": 43, "sat_max": 76,
            "val_min": 150, "val_max": 255
        }
        
        for key, min_v, max_v in slider_configs:
            slider = QSlider(Qt.Horizontal, self.hidden_container)
            slider.setRange(min_v, max_v)
            if key in default_values:
                slider.setValue(default_values[key])
            slider.valueChanged.connect(self.update_preview)
            self.widgets[key] = slider

        # --- Left Panel: Controls & Presets ---
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #1a1a1a; border-right: 1px solid #333;")
        left_panel.setFixedWidth(340)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 25, 20, 25)
        left_layout.setSpacing(15)
        
        # Header
        header = QLabel("COLOR CONFIG")
        header.setStyleSheet("color: #555; font-weight: 900; font-size: 12px; letter-spacing: 3px;")
        left_layout.addWidget(header)
        
        # Editor Action Card
        editor_card = QFrame()
        editor_card.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #333;
                border-radius: 12px;
            }
        """)
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setSpacing(10)
        editor_layout.setContentsMargins(15, 15, 15, 15)
        
        edit_title = QLabel("Advanced Editor")
        edit_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;")
        
        edit_desc = QLabel("Fine-tune your color extraction settings using the visual HSV tool.")
        edit_desc.setStyleSheet("color: #888; font-size: 12px; border: none; line-height: 1.4;")
        edit_desc.setWordWrap(True)
        
        self.hsv_tool_btn = QPushButton("OPEN HSV TOOL")
        self.hsv_tool_btn.clicked.connect(self.open_hsv_tool)
        self.hsv_tool_btn.setCursor(Qt.PointingHandCursor)
        self.hsv_tool_btn.setFixedHeight(40)
        self.hsv_tool_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0066cc, stop:1 #0099ff);
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077dd, stop:1 #00aaff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0055bb, stop:1 #0088ee);
            }
        """)
        
        editor_layout.addWidget(edit_title)
        editor_layout.addWidget(edit_desc)
        editor_layout.addWidget(self.hsv_tool_btn)
        left_layout.addWidget(editor_card)
        
        # Presets Section
        presets_header = QLabel("PRESETS LIBRARY")
        presets_header.setStyleSheet("color: #555; font-weight: 900; font-size: 11px; letter-spacing: 2px; margin-top: 15px;")
        left_layout.addWidget(presets_header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #333;
                min-height: 20px;
                border-radius: 3px;
            }
        """)
        
        preset_container = QWidget()
        preset_container.setStyleSheet("background: transparent;")
        self.preset_layout = QVBoxLayout(preset_container)
        self.preset_layout.setSpacing(8)
        self.preset_layout.setContentsMargins(0, 0, 5, 0)
        
        # Default Presets
        self.purple_btn = QPushButton("Purple (Enemy)")
        self.red_btn = QPushButton("Red (Enemy)")
        self.yellow_btn = QPushButton("Yellow (Ally)")
        
        # Base buttons style - simple list item look
        base_style = """
            QPushButton {
                background-color: #2a2a2a;
                text-align: left;
                padding: 10px 15px;
                border-radius: 8px;
                border: 1px solid #333;
                color: #ccc;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #333;
                border: 1px solid #444;
                color: white;
            }
        """
        
        # Add color indicator to buttons using border-left
        for btn, color, indicator in [
            (self.purple_btn, self.set_purple_preset, "#805ad5"),
            (self.red_btn, self.set_red_preset, "#e53e3e"), 
            (self.yellow_btn, self.set_yellow_preset, "#ecc94b")
        ]:
            btn.clicked.connect(color)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(base_style + f"QPushButton {{ border-left: 4px solid {indicator}; }}")
            self.preset_layout.addWidget(btn)
        
        # Separator for Custom Presets
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #333;")
        self.preset_layout.addWidget(line)

        self.custom_preset_buttons = []
        self.load_custom_presets()
        
        scroll.setWidget(preset_container)
        left_layout.addWidget(scroll)

        # --- Right Panel: Preview ---
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #121212;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(25)
        
        preview_label = QLabel("VISUAL PREVIEW")
        preview_label.setStyleSheet("color: #444; font-weight: 900; font-size: 14px; letter-spacing: 4px;")
        right_layout.addWidget(preview_label)
        
        # Preview Container with shadow-like border
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border: 1px solid #222;
                border-radius: 20px;
            }
        """)
        frame_layout = QVBoxLayout(preview_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_widget = ColorPreviewWidget()
        frame_layout.addWidget(self.preview_widget)
        
        right_layout.addWidget(preview_frame, stretch=1)
        
        # Spectrum
        self.spectrum_widget = ColorSpectrumWidget()
        self.spectrum_widget.setFixedHeight(40)
        # Using a container for spectrum to round it nicely
        spectrum_container = QFrame()
        spectrum_container.setFixedHeight(40)
        spectrum_container.setStyleSheet("border-radius: 10px; overflow: hidden;")
        sc_layout = QVBoxLayout(spectrum_container)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.addWidget(self.spectrum_widget)
        
        right_layout.addWidget(spectrum_container)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Initialize
        self.update_preview()

    def update_preview(self):
        """Update preview widget and spectrum"""
        hue_min = self.widgets["hue_min"].value()
        hue_max = self.widgets["hue_max"].value()
        sat_min = self.widgets["sat_min"].value() / 100.0
        sat_max = self.widgets["sat_max"].value() / 100.0
        val_min = self.widgets["val_min"].value()
        val_max = self.widgets["val_max"].value()
        
        self.preview_widget.update_color_values(
            hue_min, hue_max, sat_min, sat_max, val_min, val_max
        )
        
        self.spectrum_widget.update_hue_range(hue_min, hue_max)

    def get_widgets(self):
        """Return widgets to main application"""
        return self.widgets


    
    def update_theme(self, theme: ColorTheme):
        """Called when theme is updated"""
        self.current_theme = theme
    
    def set_purple_preset(self):
        """Set purple color preset (Valorant enemy outline)"""
        preset_values = {
            "hue_min": 140,  # 280° (purple/violet)
            "hue_max": 150,  # 300° (purple/violet)
            "sat_min": 43,   # 0.43
            "sat_max": 76,   # 0.76
            "val_min": 150,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def set_red_preset(self):
        """Set red color preset (Valorant enemy outline)"""
        preset_values = {
            "hue_min": 0,    # 0° (red)
            "hue_max": 10,   # 20° (red)
            "sat_min": 70,   # 0.70 (high saturation)
            "sat_max": 100,  # 1.00 (full saturation)
            "val_min": 180,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def set_yellow_preset(self):
        """Set yellow color preset (Valorant teammate outline)"""
        preset_values = {
            "hue_min": 20,   # 40° (yellow)
            "hue_max": 30,   # 60° (yellow)
            "sat_min": 60,   # 0.60
            "sat_max": 100,  # 1.00 (full saturation)
            "val_min": 180,
            "val_max": 255
        }
        self.apply_preset(preset_values)
    
    def apply_preset(self, values):
        """Apply preset values to sliders"""
        for key, value in values.items():
            if key in self.widgets:
                self.widgets[key].setValue(value)
        # Update preview after applying preset
        self.update_preview()
            
    def open_hsv_tool(self):
        self.hsv_window = HSVToolWindow(self)
        self.hsv_window.settings_saved.connect(self.load_custom_presets)
        self.hsv_window.show()
        
    def load_custom_presets(self):
        # Clear existing custom buttons from layout
        for btn in self.custom_preset_buttons:
            self.preset_layout.removeWidget(btn)
            btn.deleteLater()
        self.custom_preset_buttons = []
        
        config_file = os.path.join(os.getenv('APPDATA'), 'ds-color', 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    presets = json.load(f)
                    
                button_style = """
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(60, 140, 60, 120), stop:1 rgba(40, 90, 40, 120));
                        border: 1px solid rgba(80, 150, 80, 0.6);
                        border-radius: 8px;
                        color: white;
                        font-weight: bold;
                        padding: 5px 15px;
                        min-height: 25px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(80, 160, 80, 180), stop:1 rgba(60, 110, 60, 180));
                    }
                """
                
                for name, data in presets.items():
                    btn = QPushButton(name)
                    btn.setStyleSheet(button_style)
                    btn.setToolTip("Right-click to delete")
                    
                    # Connect click for applying preset
                    btn.clicked.connect(lambda checked, d=data: self.apply_preset(d))
                    
                    # Setup Context Menu for Deletion
                    btn.setContextMenuPolicy(Qt.CustomContextMenu)
                    btn.customContextMenuRequested.connect(lambda pos, n=name: self.show_preset_context_menu(pos, n))
                    
                    self.preset_layout.addWidget(btn)
                    self.custom_preset_buttons.append(btn)
            except Exception as e:
                print(f"Error loading presets: {e}")

    def show_preset_context_menu(self, pos, name):
        """Show context menu to delete preset"""
        sender = self.sender()
        menu = QMenu()
        delete_action = QAction(f"Delete '{name}'", self)
        delete_action.triggered.connect(lambda: self.delete_preset(name))
        menu.addAction(delete_action)
        menu.exec_(sender.mapToGlobal(pos))
        
    def delete_preset(self, name):
        """Delete a custom preset"""
        confirm = QMessageBox.question(self, "Delete Preset", 
                                     f"Are you sure you want to delete preset '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            config_file = os.path.join(os.getenv('APPDATA'), 'ds-color', 'config.json')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        presets = json.load(f)
                    
                    if name in presets:
                        del presets[name]
                        
                        with open(config_file, 'w') as f:
                            json.dump(presets, f, indent=4)
                            
                        self.load_custom_presets()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete preset: {e}")
    
    def apply_styles(self):
        """Apply gray theme styling"""
        self.setStyleSheet("""
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
        
        QLabel {
            color: #d0d0d0;
            font-weight: bold;
            font-size: 13px;
            padding: 2px;
            font-family: 'Roboto', 'Arial';
        }
        
        /* Scrollbar styling */
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
        """)
        
    def get_settings(self):
        """Get settings for config"""
        settings = {}
        for key, widget in self.widgets.items():
            if key in ["sat_min", "sat_max"]:
                # Convert back to float for saving if that's the convention, 
                # but aimbot tab seems to use strings. 
                # Let's check ColorSettings in main.py load_comprehensive_color_settings
                # It expects strings. 
                factor = 100
                value = widget.value() / factor
                settings[key] = f"{value:.2f}"
            else:
                settings[key] = str(widget.value())
        return settings

    def load_settings(self, settings):
        """Load settings from config"""
        # Block signals to prevent update_preview spam
        for widget in self.widgets.values():
            widget.blockSignals(True)
            
        try:
            for key, widget in self.widgets.items():
                if key in settings:
                    value_str = settings[key]
                    # Calculate factor for decimal values
                    if key in ["sat_min", "sat_max"]:
                        factor = 100
                        try:
                            value = int(float(value_str) * factor)
                            widget.setValue(value)
                        except ValueError:
                            widget.setValue(0)
                    else:
                        try:
                            value = int(float(value_str))
                            widget.setValue(value)
                        except ValueError:
                            widget.setValue(0)
                            
        finally:
            # Unblock signals
            for widget in self.widgets.values():
                widget.blockSignals(False)
        
        # Update preview after loading settings
        self.update_preview()