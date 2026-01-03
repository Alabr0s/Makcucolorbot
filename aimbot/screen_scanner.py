"""
Screen scanning module
Handles screen capture and target detection
"""

import time
import random
import numpy as np
import mss
import keyboard
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from .mouse_controller import MouseController
from anti_smoke_detector import AntiSmokeDetector


class ScreenScanner(QThread):
    target_found = pyqtSignal(int, int)

    def __init__(self, indicator_window):
        super().__init__()
        self.indicator_window = indicator_window
        self.running = False
        self.paused = False  # Scan pause status
        self.target_color_hsv = (293, 54.5, 82.5)  # In HSV format (default)
        # Scan area will now be the same as indicator FOV (scan_area_size removed)

        # Color settings reference
        self.color_settings = None
        self.mouse_controller = MouseController()
        self.holdkey_enabled = False  # Is holdkey active
        self.holdkey = 'f'  # Default holdkey key
        self.color_tolerance = 5  # Color tolerance (0-50 range)
        self.debug_window = None  # Debug window reference
        self.numbered_targets = []  # Numbered targets list
        self.primary_target = None  # Target number 1 (primary target)

        # Target type setting
        self.target_type = "body"  # "head" or "body"

        # Anti-smoke detector
        self.anti_smoke_detector = AntiSmokeDetector()

        # Toggle settings
        self.aimbot_enabled = True  # Aimbot on/off status
        self.toggle_key = 'insert'  # Default toggle key
        self.last_toggle_time = 0  # Last toggle time (spam prevention)



        # Target determination settings
        self.target_type = "body"  # "head" or "body"
        self.y_offset = 0  # Y offset (0-10 px range)
        
        # Fast scan optimizations
        self.scan_speed = 100  # Scan speed (1-100, high = fast)
        self.adaptive_sleep = True  # Adaptive sleep time
        self.frame_skip = 0  # Frame skip count
        self.last_scan_time = 0  # Last scan time
        self.performance_mode = False  # Performance mode
        
        # Silent Aim Settings
        self.silent_aim_enabled = False

        
        # FPS (Frame Rate) settings - New Feature
        self.target_fps = 60  # Target FPS (default 60)
        self.frame_time = 1.0 / 60.0  # Frame time (seconds)
        
        # New previous target tracking (for prediction)
        self.previous_target = None

    def run(self):
        self.running = True
        with mss.mss() as sct:
            while self.running:
                try:
                    # Toggle key check
                    self.check_toggle_key()

                    # Pause check
                    if self.paused:
                        time.sleep(0.1)
                        continue

                    # Indicator check - Safe version
                    if not self.indicator_window or not self.indicator_window.isVisible():
                        time.sleep(0.1)
                        continue
                    
                    # Check indicator dimensions
                    indicator_width = getattr(self.indicator_window, 'indicator_width', 0)
                    indicator_height = getattr(self.indicator_window, 'indicator_height', 0)
                    
                    if indicator_width <= 0 or indicator_height <= 0:
                        time.sleep(0.1)
                        continue

                    # Don't scan if aimbot is disabled
                    if not self.aimbot_enabled:
                        time.sleep(0.1)
                        continue

                    # Holdkey check
                    if self.holdkey_enabled:
                        if not self.is_key_pressed(self.holdkey):
                            time.sleep(0.01)
                            continue

                    # Ekran merkezini al
                    screen = sct.monitors[1]  # Main monitor
                    center_x = screen['width'] // 2
                    center_y = screen['height'] // 2

                    # Determine scan area - Same as Indicator FOV (X×Y)
                    # Scan area will be 10 pixels larger than indicator dimensions
                    scan_width = indicator_width + 20  # 10 pixels from each side (total 20)
                    scan_height = indicator_height + 20  # 10 pixels from each side (total 20)
                    
                    # Safety check - minimum size
                    if scan_width < 1 or scan_height < 1:
                        time.sleep(0.1)
                        continue

                    monitor = {
                        'top': center_y - scan_height // 2,
                        'left': center_x - scan_width // 2,
                        'width': scan_width,
                        'height': scan_height
                    }

                    # Take screenshot
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)

                    # Hedef rengi ara
                    target_positions = self.find_target_color(img)

                    # Scan area center coordinates (always needed for debug)
                    scan_center_x = scan_width // 2
                    scan_center_y = scan_height // 2

                    # Multi-target detection and numbering
                    self.numbered_targets = []
                    self.primary_target = None

                    if target_positions:
                        # Find all clusters
                        all_clusters = self.find_all_clusters(target_positions)

                        if all_clusters:
                            # Sort clusters by distance to center and number them

                            # Calculate center and distance for each cluster
                            cluster_data = []
                            for cluster in all_clusters:
                                # 1. Anti-smoke check
                                if not self.anti_smoke_detector.is_valid_target(cluster):
                                    continue  # Skip this cluster (could be smoke)

                                center = self.get_cluster_center(cluster)
                                if center:
                                    distance = ((center[0] - scan_center_x) ** 2 + (center[1] - scan_center_y) ** 2) ** 0.5

                                    # 2. Add circle check information (to be used for movement)
                                    touching_indicator = self.is_cluster_touching_indicator(cluster, scan_center_x, scan_center_y)

                                    cluster_data.append({
                                        'cluster': cluster,
                                        'center': center,
                                        'distance': distance,
                                        'touching_indicator': touching_indicator  # Is it touching the circle?
                                    })

                            # Sort by distance (closest first)
                            cluster_data.sort(key=lambda x: x['distance'])

                            # Number them
                            for i, data in enumerate(cluster_data):
                                numbered_target = {
                                    'number': i + 1,
                                    'cluster': data['cluster'],
                                    'center': data['center'],
                                    'distance': data['distance'],
                                    'touching_indicator': data['touching_indicator']  # Circle check information
                                }
                                self.numbered_targets.append(numbered_target)

                                # First target (closest) becomes primary target
                                if i == 0:
                                    self.primary_target = numbered_target

                    # Update image in debug mode (high speed)
                    if self.debug_window and self.debug_window.isVisible():
                        try:
                            # Use QTimer for asynchronous update
                            self.debug_window.queue_update(
                                img, target_positions, self.numbered_targets, scan_center_x, scan_center_y
                            )
                        except Exception as e:
                            print(f"Debug window update error: {e}")

                    # Dynamic wait time with FPS control
                    frame_start_time = time.time()
                    
                    # Lock onto primary target (number 1)
                    if self.primary_target:
                        target_point = self.primary_target['center']
                        real_x = monitor['left'] + target_point[0]
                        real_y = monitor['top'] + target_point[1]
                        
                        # Silent Aim Logic
                        if self.silent_aim_enabled:
                            # 1. Instant move to target
                            # Align with IndicatorWindow offset (-1, -1 from center)
                            raw_dx = (real_x - center_x) + 1
                            raw_dy = (real_y - center_y) + 1
                            
                            # Apply Sensitivity/Scaling (mickeys per pixel)
                            # We must use the same scaling as the normal aimbot to match game sensitivity
                            damage_scaling = self.mouse_controller.aim_speed / 10.0
                            
                            move_dx = int(raw_dx * damage_scaling)
                            move_dy = int(raw_dy * damage_scaling)
                            
                            if self.mouse_controller.tcp_client.send_movement(move_dx, move_dy):
                                # 2. Wait 300-500ms random
                                wait_time = random.uniform(0.30, 0.50)
                                time.sleep(wait_time)
                                
                                # 3. Fire command
                                self.mouse_controller.send_fire_command()
                                
                                # 4. Return to start position (inverse movement)
                                self.mouse_controller.tcp_client.send_movement(-move_dx, -move_dy)
                                
                                # Emit target found for debug/status
                                self.target_found.emit(move_dx, move_dy)
                                
                                # cooldown to prevent spamming in same frame
                                time.sleep(0.05) 
                        else:
                            # Normal Aimbot Logic
                            # Circle check: Move mouse if any point touches the circle
                            if self.primary_target.get('touching_indicator', False):
                                # Aim calculation - ERROR WAS HERE, FIXED
                                move_x, move_y = self.mouse_controller.calculate_direct_movement(
                                    real_x, real_y, center_x, center_y
                                )

                                # Send mouse movement
                                if self.mouse_controller.send_movement(move_x, move_y):
                                    self.target_found.emit(move_x, move_y)
                            else:
                                # Target is not touching circle, tracking can be reset.
                                self.mouse_controller.reset_tracking()
                    else:
                        # Reset last target when target is not found
                        self.mouse_controller.reset_tracking()

                    # FPS-based frame timing
                    frame_end_time = time.time()
                    frame_duration = frame_end_time - frame_start_time
                    
                    # Calculate required wait time to reach target frame time
                    sleep_time = max(0, self.frame_time - frame_duration)
                    
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        
                except Exception as e:
                    print(f"❌ Screen scanner error: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.1)  # Short wait in case of error

    def find_target_color(self, img):
        """Search for target color - In HSV format"""
        target_positions = []

        # Convert from BGRA format to BGR (mss uses BGRA)
        if img.shape[2] == 4:  # BGRA
            img_bgr = img[:, :, :3]  # Remove alpha channel
        else:  # BGR
            img_bgr = img

        # Convert from BGR to HSV
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Get HSV ranges from color settings
        if self.color_settings:
            try:
                widgets = self.color_settings.get_widgets()

                # Get HSV ranges from color_settings
                hue_min = widgets['hue_min'].value()
                hue_max = widgets['hue_max'].value()
                sat_min = widgets['sat_min'].value() / 100.0 * 255  # Convert from percentage to 0-255
                sat_max = widgets['sat_max'].value() / 100.0 * 255
                val_min = widgets['val_min'].value()
                val_max = widgets['val_max'].value()

                # Convert to OpenCV HSV format (H: 0-179)
                if hue_min > 179:
                    hue_min = hue_min // 2
                if hue_max > 179:
                    hue_max = hue_max // 2

                lower_hsv = np.array([hue_min, sat_min, val_min])
                upper_hsv = np.array([hue_max, sat_max, val_max])

            except Exception as e:
                print(f"Color settings error, using default: {e}")
                # Use default values in case of error
                target_h, target_s, target_v = self.target_color_hsv
                h_tolerance = self.color_tolerance
                s_tolerance = self.color_tolerance * 2.55
                v_tolerance = self.color_tolerance * 2.55

                lower_hsv = np.array([
                    max(0, target_h - h_tolerance),
                    max(0, (target_s / 100.0) * 255 - s_tolerance),
                    max(0, (target_v / 100.0) * 255 - v_tolerance)
                ])

                upper_hsv = np.array([
                    min(179, target_h + h_tolerance),
                    min(255, (target_s / 100.0) * 255 + s_tolerance),
                    min(255, (target_v / 100.0) * 255 + v_tolerance)
                ])
        else:
            # Use default values if color settings are not available
            target_h, target_s, target_v = self.target_color_hsv
            h_tolerance = self.color_tolerance
            s_tolerance = self.color_tolerance * 2.55
            v_tolerance = self.color_tolerance * 2.55

            lower_hsv = np.array([
                max(0, target_h - h_tolerance),
                max(0, (target_s / 100.0) * 255 - s_tolerance),
                max(0, (target_v / 100.0) * 255 - v_tolerance)
            ])

            upper_hsv = np.array([
                min(179, target_h + h_tolerance),
                min(255, (target_s / 100.0) * 255 + s_tolerance),
                min(255, (target_v / 100.0) * 255 + v_tolerance)
            ])

        # Create HSV mask
        mask = cv2.inRange(img_hsv, lower_hsv, upper_hsv)

        # Find coordinates of white pixels in mask
        y_coords, x_coords = np.where(mask == 255)

        return list(zip(x_coords, y_coords))

    def is_key_pressed(self, key):
        """Advanced key control system - Supports mouse buttons"""
        try:
            key = key.lower().strip()
            
            # Mouse button check
            if key in ['left', 'right', 'middle', 'x1', 'x2']:
                return self._check_mouse_button(key)
            
            # Use keyboard library for keyboard keys
            return keyboard.is_pressed(key)
            
        except Exception as e:
            if not hasattr(self, '_last_error') or self._last_error != str(e):
                print(f"Key check error: {e}")
                self._last_error = str(e)
            return False
    
    def _check_mouse_button(self, button):
        """Mouse button check - Uses Windows API"""
        try:
            import ctypes
            
            # Windows mouse button codes
            mouse_vk_codes = {
                'left': 0x01,    # VK_LBUTTON
                'right': 0x02,   # VK_RBUTTON
                'middle': 0x04,  # VK_MBUTTON
                'x1': 0x05,      # VK_XBUTTON1 (side button)
                'x2': 0x06       # VK_XBUTTON2 (side button)
            }
            
            vk_code = mouse_vk_codes.get(button)
            if vk_code:
                # Check mouse button with GetAsyncKeyState
                result = ctypes.windll.user32.GetAsyncKeyState(vk_code)
                is_pressed = (result & 0x8000) != 0
                
                return is_pressed
            
            return False
            
        except Exception as e:
            print(f"Mouse button check error for '{button}': {e}")
            return False

    def set_aim_speed(self, speed):
        """Set aim speed"""
        self.mouse_controller.set_aim_speed(speed)

    def set_holdkey_settings(self, enabled, key):
        """Update holdkey settings"""
        old_enabled = self.holdkey_enabled
        self.holdkey_enabled = enabled
        self.holdkey = key.lower() if key else 'f'

        # Show notification if holdkey status changed
        if old_enabled != enabled:
            self._show_holdkey_notification(enabled, key)

    def set_color_tolerance(self, tolerance):
        """Set color tolerance (0-50 range)"""
        self.color_tolerance = max(0, min(50, tolerance))

    def set_target_color_hsv(self, hsv_tuple):
        """Hedef rengi ayarla (H, S%, V%)"""
        self.target_color_hsv = hsv_tuple

    def set_target_color(self, rgba_tuple):
        """Set target color (R, G, B, A) - Converts from RGBA to HSV"""
        r, g, b, a = rgba_tuple

        # Normalize RGB to 0-1 range
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0

        # Convert from RGB to HSV
        max_val = max(r_norm, g_norm, b_norm)
        min_val = min(r_norm, g_norm, b_norm)
        diff = max_val - min_val

        # Calculate Value (V)
        v = max_val * 100  # In percentage format

        # Calculate Saturation (S)
        if max_val == 0:
            s = 0
        else:
            s = (diff / max_val) * 100  # In percentage format

        # Calculate Hue (H)
        if diff == 0:
            h = 0
        elif max_val == r_norm:
            h = (60 * ((g_norm - b_norm) / diff) + 360) % 360
        elif max_val == g_norm:
            h = (60 * ((b_norm - r_norm) / diff) + 120) % 360
        else:  # max_val == b_norm
            h = (60 * ((r_norm - g_norm) / diff) + 240) % 360

        # Set HSV value
        self.target_color_hsv = (h, s, v)

    def set_paused(self, paused):
        """Pause/resume scanning"""
        self.paused = paused

    def set_debug_window(self, debug_window):
        """Set debug window reference"""
        self.debug_window = debug_window

    def set_color_settings(self, color_settings):
        """Set color settings reference"""
        self.color_settings = color_settings

    def set_target_type(self, target_type):
        """Set target type ('head' or 'body')"""
        if target_type in ["head", "body"]:
            self.target_type = target_type
        else:
            print(f"Invalid target type: {target_type}. Use 'head' or 'body'.")

    def set_y_offset(self, offset):
        """Set Y offset value (0-10 px range)"""
        self.y_offset = max(0, min(10, offset))

    def set_anti_smoke(self, enabled):
        """Enable/disable anti-smoke feature"""
        self.anti_smoke_detector.set_enabled(enabled)

    def check_toggle_key(self):
        """Toggle key check"""
        current_time = time.time()

        # Spam prevention: 0.5 second interval
        if current_time - self.last_toggle_time < 0.5:
            return

        # Check if toggle key is pressed
        if self.is_key_pressed(self.toggle_key):
            self.aimbot_enabled = not self.aimbot_enabled
            self.last_toggle_time = current_time

            # Inform indicator of status
            if hasattr(self.indicator_window, 'set_aimbot_status'):
                self.indicator_window.set_aimbot_status(self.aimbot_enabled)

            # Show notification
            self._show_aimbot_notification()

    def set_toggle_key(self, key):
        """Set toggle key"""
        self.toggle_key = key.lower() if key else 'insert'

    def get_aimbot_status(self):
        """Return aimbot status"""
        return self.aimbot_enabled

    def set_aimbot_enabled(self, enabled):
        """Manually set aimbot status"""
        self.aimbot_enabled = enabled
        if hasattr(self.indicator_window, 'set_aimbot_status'):
            self.indicator_window.set_aimbot_status(self.aimbot_enabled)

        # Show notification
        self._show_aimbot_notification()

    def set_silent_aim(self, enabled):
        """Enable/Disable Silent Aim"""
        self.silent_aim_enabled = enabled


    def _show_aimbot_notification(self):
        """Show aimbot status notification"""
        try:
            from utils.notification_system import notification_manager
            notification_manager.show_aimbot_status(self.aimbot_enabled)
        except Exception as e:
            print(f"Aimbot notification error: {e}")

    def _show_holdkey_notification(self, enabled: bool, key: str):
        """Show holdkey status notification"""
        try:
            from utils.notification_system import show_info, show_success, show_warning

            if enabled:
                show_success(
                    "Aimbot Holdkey Active",
                    f"Holdkey mode enabled (Key: {key.upper()})",
                    2000
                )
            else:
                show_warning(
                    "Aimbot Holdkey Inactive",
                    "Holdkey mode disabled",
                    2000
                )
        except Exception as e:
            print(f"Holdkey notification error: {e}")

    def get_target_debug_info(self, cluster, scan_center_x=None, scan_center_y=None):
        """Return debug information about target"""
        if not cluster:
            return "Cluster not found"

        # Calculate dimensions
        min_x = min(pixel[0] for pixel in cluster)
        max_x = max(pixel[0] for pixel in cluster)
        min_y = min(pixel[1] for pixel in cluster)
        max_y = max(pixel[1] for pixel in cluster)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        aspect_ratio = width / max(height, 1)

        # Checks
        touching_indicator = True
        if scan_center_x is not None and scan_center_y is not None:
            touching_indicator = self.is_cluster_touching_indicator(cluster, scan_center_x, scan_center_y)

        is_valid_smoke = self.anti_smoke_detector.is_valid_target(cluster)

        debug_info = f"""
🎯 Target Analysis:
├─ Size: {width}x{height}
├─ Aspect Ratio: {aspect_ratio:.2f}
├─ Touching Circle: {'✅ Yes' if touching_indicator else '❌ No'}
├─ Anti-Smoke: {'✅ Valid' if is_valid_smoke else '❌ Smoke'} ({'On' if self.anti_smoke_detector.is_enabled() else 'Off'})
└─ Result: {'✅ TARGET ACQUIRE' if touching_indicator and is_valid_smoke else '❌ FILTER'}
        """
        return debug_info.strip()

    def find_all_clusters(self, pixels, cluster_distance=10):
        """Cluster pixels and return all clusters - Improved algorithm"""
        if not pixels:
            return []

        # Limit maximum pixel count for performance
        if len(pixels) > 1000:
            pixels = pixels[:1000]

        clusters = []
        used_pixels = set()

        for start_pixel in pixels:
            if start_pixel in used_pixels:
                continue

            # Create cluster with BFS (Breadth-First Search)
            cluster = []
            queue = [start_pixel]
            used_pixels.add(start_pixel)

            while queue:
                current_pixel = queue.pop(0)
                cluster.append(current_pixel)

                # Only check nearby pixels (for performance)
                for other_pixel in pixels:
                    if other_pixel in used_pixels:
                        continue

                    # Distance check
                    dx = abs(current_pixel[0] - other_pixel[0])
                    dy = abs(current_pixel[1] - other_pixel[1])

                    # First simple distance check (fast)
                    if dx <= cluster_distance and dy <= cluster_distance:
                        # Calculate actual distance
                        distance = (dx * dx + dy * dy) ** 0.5
                        if distance <= cluster_distance:
                            queue.append(other_pixel)
                            used_pixels.add(other_pixel)

            # Minimum cluster size check (filter noise)
            if len(cluster) >= 3:  # At least 3 pixels required
                clusters.append(cluster)

        # Split large clusters (separate side-by-side enemies)
        final_clusters = []
        for cluster in clusters:
            split_clusters = self.split_large_cluster(cluster)
            final_clusters.extend(split_clusters)

        # Sort clusters by size (largest to smallest)
        final_clusters.sort(key=len, reverse=True)

        # Return maximum 10 clusters (for performance)
        return final_clusters[:10]

    def split_large_cluster(self, cluster):
        """Split large clusters into smaller parts (separate side-by-side enemies)"""
        if not cluster or len(cluster) < 20:  # Don't split small clusters
            return [cluster]

        # Calculate cluster dimensions
        min_x = min(pixel[0] for pixel in cluster)
        max_x = max(pixel[0] for pixel in cluster)
        min_y = min(pixel[1] for pixel in cluster)
        max_y = max(pixel[1] for pixel in cluster)

        width = max_x - min_x
        height = max_y - min_y

        # If cluster is too wide (side-by-side enemies), split vertically
        if width > height * 1.5 and width > 40:  # Width is 1.5 times greater than height and greater than 40 pixels
            return self.split_cluster_vertically(cluster, min_x, max_x, min_y, max_y)

        # If cluster is too tall (stacked enemies), split horizontally
        elif height > width * 1.5 and height > 40:  # Height is 1.5 times greater than width and greater than 40 pixels
            return self.split_cluster_horizontally(cluster, min_x, max_x, min_y, max_y)

        # Don't split if normal size
        return [cluster]

    def split_cluster_vertically(self, cluster, min_x, max_x, min_y, max_y):
        """Split cluster vertically (for side-by-side enemies)"""
        width = max_x - min_x
        split_points = []

        # Split cluster into 3 equal parts and find empty areas
        for i in range(1, 3):  # 2 split points
            split_x = min_x + (width * i // 3)

            # Check pixel density at this x coordinate
            pixels_at_x = [p for p in cluster if abs(p[0] - split_x) <= 2]

            # Use as split point if few pixels in this region
            if len(pixels_at_x) < len(cluster) * 0.1:  # Less than 10% pixels
                split_points.append(split_x)

        if not split_points:
            return [cluster]

        # Separate cluster based on split points
        sub_clusters = []
        current_min_x = min_x

        for split_x in split_points:
            sub_cluster = [p for p in cluster if current_min_x <= p[0] < split_x]
            if len(sub_cluster) >= 3:  # Minimum size check
                sub_clusters.append(sub_cluster)
            current_min_x = split_x

        # Add final piece
        final_cluster = [p for p in cluster if p[0] >= current_min_x]
        if len(final_cluster) >= 3:
            sub_clusters.append(final_cluster)

        return sub_clusters if sub_clusters else [cluster]

    def split_cluster_horizontally(self, cluster, min_x, max_x, min_y, max_y):
        """Split cluster horizontally (for stacked enemies)"""
        height = max_y - min_y
        split_points = []

        # Split cluster into 3 equal parts and find empty areas
        for i in range(1, 3):  # 2 split points
            split_y = min_y + (height * i // 3)

            # Check pixel density at this y coordinate
            pixels_at_y = [p for p in cluster if abs(p[1] - split_y) <= 2]

            # Use as split point if few pixels in this region
            if len(pixels_at_y) < len(cluster) * 0.1:  # Less than 10% pixels
                split_points.append(split_y)

        if not split_points:
            return [cluster]

        # Separate cluster based on split points
        sub_clusters = []
        current_min_y = min_y

        for split_y in split_points:
            sub_cluster = [p for p in cluster if current_min_y <= p[1] < split_y]
            if len(sub_cluster) >= 3:  # Minimum size check
                sub_clusters.append(sub_cluster)
            current_min_y = split_y

        # Add final piece
        final_cluster = [p for p in cluster if p[1] >= current_min_y]
        if len(final_cluster) >= 3:
            sub_clusters.append(final_cluster)

        return sub_clusters if sub_clusters else [cluster]

    def is_cluster_touching_indicator(self, cluster, scan_center_x, scan_center_y):
        """Check if any point of the cluster touches the indicator rectangle"""
        if not cluster:
            return False

        # Get indicator rectangle dimensions (original dimensions)
        indicator_width = self.indicator_window.indicator_width
        indicator_height = self.indicator_window.indicator_height
        
        # Calculate rectangle boundaries (from center point)
        # 10 pixels smaller area (original indicator area)
        half_width = indicator_width // 2
        half_height = indicator_height // 2
        
        rect_left = scan_center_x - half_width
        rect_right = scan_center_x + half_width
        rect_top = scan_center_y - half_height
        rect_bottom = scan_center_y + half_height

        # Check if any pixel of the cluster is inside the rectangle
        for pixel_x, pixel_y in cluster:
            # If any pixel is inside the rectangle
            if (rect_left <= pixel_x <= rect_right and 
                rect_top <= pixel_y <= rect_bottom):
                return True  # Touching rectangle

        return False  # No pixel touches the rectangle

    def get_anti_smoke_debug_info(self, cluster):
        """Anti-smoke debug bilgilerini al"""
        return self.anti_smoke_detector.get_debug_info(cluster)

    def get_cluster_center(self, cluster):
        """Calculate target point based on target type"""
        if not cluster:
            return None

        # Find cluster boundaries
        min_x = min(pixel[0] for pixel in cluster)
        max_x = max(pixel[0] for pixel in cluster)
        min_y = min(pixel[1] for pixel in cluster)
        max_y = max(pixel[1] for pixel in cluster)

        # X coordinate is always centered
        center_x = (min_x + max_x) // 2

        # Y coordinate changes based on target type
        if self.target_type == "head":
            # Head: Top center of rectangle + Y offset
            center_y = min_y + self.y_offset
        else:  # body (default)
            # Body: Center of rectangle
            center_y = (min_y + max_y) // 2

        return (center_x, center_y)

    def stop(self):
        self.running = False
        self.mouse_controller.disconnect()
        self.wait()
        
    def calculate_adaptive_sleep(self):
        """
        Calculate adaptive sleep time based on scan speed.
        """
        # Scan speed 1-100 range, 100 = fastest (minimum sleep)
        if self.scan_speed >= 90:
            return 0.0001  # Very fast
        elif self.scan_speed >= 70:
            return 0.001   # Fast
        elif self.scan_speed >= 50:
            return 0.005   # Medium
        elif self.scan_speed >= 30:
            return 0.01    # Slow
        else:
            return 0.02    # Very slow
            
    def set_scan_speed(self, speed):
        """
        Set scan speed (1-100).
        """
        self.scan_speed = max(1, min(100, speed))
        
    def set_fps(self, fps):
        """
        Set target FPS value and calculate frame time.
        Supported FPS values: 60, 75, 125, 160, 175, 200
        """
        # Check valid FPS values
        valid_fps_values = [60, 75, 125, 160, 175, 200]
        if fps in valid_fps_values:
            self.target_fps = fps
            self.frame_time = 1.0 / fps
            print(f"📈 FPS set: {fps} (Frame time: {self.frame_time:.4f}s)")
        else:
            print(f"⚠️ Invalid FPS value: {fps}. Supported values: {valid_fps_values}")
            print(f"📈 Using default FPS: {self.target_fps}")
        
    def set_smoothing(self, soft_aim_value):
        """
        Pass smoothing settings to mouse controller - Compatible with memory specifications.
        """
        self.mouse_controller.set_smoothing(soft_aim_value)
        
    def set_prediction(self, enabled, strength=50):
        """
        Pass adaptive aim prediction settings to mouse controller.
        """
        self.mouse_controller.set_prediction(enabled, strength)
        
    def get_performance_info(self):
        """
        Return performance information.
        """
        return {
            'target_fps': self.target_fps,
            'frame_time': self.frame_time,
            'scan_speed': self.scan_speed,
            'adaptive_sleep': self.adaptive_sleep,
            'performance_mode': self.performance_mode,
            'mouse_controller_debug': self.mouse_controller.get_debug_info()
        }
