from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QTimer
from utils.utils import get_application_path
from models.color_palette import ColorTheme
import qtawesome as qta
import os
import ctypes


class ServiceWorker(QObject):
    finished = pyqtSignal()
    status_updated = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.process_started = False

    def run_start_services(self):
        if self.process_started:
            self.status_updated.emit("Defending Store is already running", "running")
            self.finished.emit()
            return

        exe_path = os.path.join(get_application_path(), "DefendingStoreX64.exe")
        key_param = "keysys=s65e1a35wr51s5g1s3h5gs53f1s23eg13sg1s351ag168sgs31hj6d5g2d3vs065est"

        if not os.path.exists(exe_path):
            self.error.emit(f"Defending Store file not found!\nPath: {exe_path}")
            self.finished.emit()
            return

        try:
            # Run as administrator
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                exe_path,
                key_param,
                None,
                1
            )
            self.process_started = True
            self.status_updated.emit("Defending Store Started", "running")
        except Exception as e:
            self.error.emit(f"Defending Store could not be started:\n{str(e)}")

        self.finished.emit()

    def run_stop_services(self):
        import psutil
        killed = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == "DefendingStoreX64.exe":
                try:
                    proc.terminate()
                    killed = True
                except Exception:
                    pass

        if killed:
            self.status_updated.emit("Defending Store Durduruldu", "stopped")
            self.process_started = False
        else:
            self.status_updated.emit("Defending Store is already closed", "stopped")
        self.finished.emit()


class ServiceControlTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = ServiceWorker()
        self.worker_thread = None
        self.current_theme = ColorTheme.LIGHT  # Default theme
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Defending Store Durduruldu")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("statusLabel")

        self.stop_button = QPushButton(qta.icon('fa5s.stop-circle', color='lightcoral'), " Defending Store'u Durdur")
        self.stop_button.clicked.connect(self.stop_services_thread)

        layout.addStretch()
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

    def start_services_thread(self):
        self.update_status_ui("Starting...", "busy")
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run_start_services)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.status_updated.connect(self.update_status_ui)
        self.worker.status_updated.connect(self.on_status_updated)
        self.worker.error.connect(self.on_service_error)
        self.worker_thread.start()

    def stop_services_thread(self):
        self.update_status_ui("Durduruluyor...", "busy")
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run_stop_services)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.status_updated.connect(self.update_status_ui)
        self.worker_thread.start()

    def update_status_ui(self, message: str, status: str):
        self.status_label.setText(message)
        color_map = {"stopped": "#f44336", "running": "#2196f3", "busy": "#ff9800"}
        self.status_label.setStyleSheet(
            f"color: {color_map.get(status, '#e6f1ff')}; font-size: 16px; font-weight: 600;"
        )
        self.stop_button.setEnabled(status != "busy")

    def on_status_updated(self, message, status):
        try:
            from utils.notification_system import show_success, show_warning
            if status == "running":
                show_success("Started", message, 2000)
            elif status == "stopped":
                show_warning("Durduruldu", message, 2000)
        except Exception as e:
            print(f"Notification error: {e}")

    def on_service_error(self, message: str):
        QMessageBox.critical(self, "Hata", message)
        self.update_status_ui("Error Occurred", "stopped")
        try:
            from utils.notification_system import show_error
            show_error("Service Error", message, 3000)
        except Exception as e:
            print(f"Error notification error: {e}")

    def update_theme(self, theme: ColorTheme):
        """Called when theme is updated"""
        self.current_theme = theme
        self.update_button_icons()
    
    def update_button_icons(self):
        """Update button icons based on theme"""
        try:
            # Determine icon color based on theme color
            if self.current_theme == ColorTheme.DARK:
                icon_color = '#ffffff'
            elif self.current_theme == ColorTheme.BLUE:
                icon_color = '#1a365d'
            elif self.current_theme == ColorTheme.GREEN:
                icon_color = '#1a202c'
            elif self.current_theme == ColorTheme.PURPLE:
                icon_color = '#1a202c'
            else:  # LIGHT theme
                icon_color = '#666666'
            
            # Update stop button icon
            if hasattr(self, 'stop_button'):
                self.stop_button.setIcon(qta.icon('fa5s.stop-circle', color='lightcoral'))
                
        except Exception as e:
            print(f"Service control tab icon update error: {e}")

    def cleanup(self):
        pass
