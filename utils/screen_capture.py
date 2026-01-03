
import dxcam
import threading
import time
import numpy as np

class ScreenCapture:
    _instance = None
    _lock = threading.Lock()

    @staticmethod
    def get_instance():
        with ScreenCapture._lock:
            if ScreenCapture._instance is None:
                ScreenCapture._instance = ScreenCapture()
            return ScreenCapture._instance

    def __init__(self):
        self.camera = None
        self.width = 1920
        self.height = 1080
        self.initialized = False
        self._init_camera()
        
        # Auto-start streaming mode for performance
        if self.initialized:
            self.start_stream()

    def _init_camera(self):
        try:
            # Initialize with default settings (Output 0)
            self.camera = dxcam.create(output_idx=0, output_color="BGR")
            if self.camera:
                self.width = self.camera.width
                self.height = self.camera.height
                self.initialized = True
                print("✅ ScreenCapture: DXGI Camera initialized successfully")
        except Exception as e:
            print(f"❌ ScreenCapture Init Error: {e}")
            self.camera = None
            self.initialized = False

    def start_stream(self):
        """Start async capture thread"""
        if self.initialized and self.camera and not self.camera.is_capturing:
            try:
                # Start full screen capture at high FPS
                # video_mode=True allows getting latest frame without blocking/buffering issues
                self.camera.start(target_fps=144, video_mode=True)
                print("🚀 ScreenCapture: High-performance stream started")
            except Exception as e:
                print(f"❌ ScreenCapture Start Error: {e}")

    def stop_stream(self):
        """Stop async capture"""
        if self.camera and self.camera.is_capturing:
            self.camera.stop()

    def grab(self, region=None):
        """
        Smart grab method.
        If stream is running, slices from latest frame (Fast/Non-blocking).
        If stream is stopped, uses direct grab (Slow/Blocking).
        """
        if not self.initialized or not self.camera:
            return None
            
        if self.camera.is_capturing:
            # --- ASYNC MODE (FAST) ---
            frame = self.camera.get_latest_frame()
            if frame is None:
                return None
                
            if region:
                left, top, right, bottom = region
                # Numpy slicing [row_start:row_end, col_start:col_end]
                # Coords must be valid. Clamp to be safe?
                # Usually caller handles clamping, but let's be safe against crash
                try:
                    return frame[top:bottom, left:right]
                except Exception:
                    return None
            else:
                return frame
        else:
            # --- SYNC MODE (SLOW - FALLBACK) ---
            try:
                return self.camera.grab(region=region)
            except Exception as e:
                print(f"❌ ScreenCapture Direct Grab Error: {e}")
                return None

    def release(self):
        self.stop_stream()
