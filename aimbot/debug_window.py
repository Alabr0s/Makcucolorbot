"""
Debug window for showing detected pixels
"""

import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
import threading
import queue


class DebugWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aimbot Debug")
        self.setFixedSize(320, 320)
        
        # Position window at top left
        self.move(0, 0)
        
        # Make window non-interactive, frameless and always on top
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.WindowDoesNotAcceptFocus |
            Qt.Tool
        )
        
        # Disable interaction
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.NoFocus)
        
        # UI setup
        self.setup_ui()
        
        # Data storage
        self.current_image = None
        self.detected_pixels = []
        self.target_point = None  # Target point
        self.target_cluster = None  # Target cluster
        
        # Queue system for fast updates
        self.update_queue = queue.Queue(maxsize=2)  # Maximum 2 frame buffer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_update_queue)
        self.update_timer.start(16)  # ~60 FPS (16ms)
        
    def setup_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Info label
        self.info_label = QLabel("Detected pixels: 0")
        self.info_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1419);
                border: 2px solid #1e3a5f;
                border-radius: 6px;
                padding: 8px;
                font-weight: 600;
                color: #64b5f6;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.info_label)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setMinimumSize(310, 290)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #1e3a5f;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1419);
                border-radius: 8px;
                color: #b3d9ff;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("Waiting for scan...")
        
        layout.addWidget(self.image_label)
        
        # Apply style
        self.setStyleSheet("""
            QWidget {
                background-color: #0f1419;
                color: #e6f1ff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
        """)
    
    def update_debug_view(self, scan_image, detected_pixels, target_point=None, target_cluster=None):
        """Update debug view"""
        if scan_image is None or len(scan_image.shape) < 3:
            return
            
        self.current_image = scan_image.copy()
        self.detected_pixels = detected_pixels
        self.target_point = target_point  # Hedef nokta
        self.target_cluster = target_cluster  # Target cluster
        
        # Update info label
        pixel_count = len(detected_pixels) if detected_pixels else 0
        cluster_size = len(target_cluster) if target_cluster else 0
        target_info = f" | Target: ({target_point[0]},{target_point[1]})" if target_point else " | Target: None"
        cluster_info = f" | Cluster: {cluster_size}" if cluster_size > 0 else ""
        self.info_label.setText(f"Detection: {pixel_count}{target_info}{cluster_info}")
        
        # Process and display image
        self.display_debug_image()
    
    def queue_update(self, scan_image, detected_pixels, numbered_targets, center_x, center_y):
        """Add update to queue (asynchronous)"""
        if scan_image is None or len(scan_image.shape) < 3:
            return
        
        # If queue is full, discard old frame
        if self.update_queue.full():
            try:
                self.update_queue.get_nowait()
            except queue.Empty:
                pass
        
        # Add new frame
        try:
            self.update_queue.put_nowait({
                'image': scan_image.copy(),
                'pixels': detected_pixels[:500],  # Maximum 500 pixels (for performance)
                'targets': numbered_targets,
                'center_x': center_x,
                'center_y': center_y
            })
        except queue.Full:
            pass  # Skip if queue is full
    
    def process_update_queue(self):
        """Process updates in queue"""
        try:
            data = self.update_queue.get_nowait()
            self.update_debug_view_with_numbered_targets(
                data['image'], data['pixels'], data['targets'], 
                data['center_x'], data['center_y']
            )
        except queue.Empty:
            pass  # Do nothing if queue is empty
    
    def update_debug_view_with_numbered_targets(self, scan_image, detected_pixels, numbered_targets, center_x, center_y):
        """Update debug view with numbered targets"""
        if scan_image is None or len(scan_image.shape) < 3:
            return
            
        self.current_image = scan_image
        self.detected_pixels = detected_pixels
        self.numbered_targets = numbered_targets
        self.scan_center_x = center_x
        self.scan_center_y = center_y
        
        # Update info label
        pixel_count = len(detected_pixels) if detected_pixels else 0
        target_count = len(numbered_targets) if numbered_targets else 0
        primary_info = ""
        if numbered_targets:
            primary = numbered_targets[0]  # Closest target
            primary_info = f" | Primary Target: #{primary['number']} ({primary['center'][0]},{primary['center'][1]})"
        
        self.info_label.setText(f"Detection: {pixel_count} | Targets: {target_count}{primary_info}")
        
        # Process and display image
        self.display_numbered_targets_image()
    
    def display_debug_image(self):
        """Display debug image on screen"""
        if self.current_image is None:
            return
            
        try:
            height, width = self.current_image.shape[:2]
            
            # Copy original image
            display_image = self.current_image.copy()
            
            # Convert from BGRA format to RGB
            if display_image.shape[2] == 4:  # BGRA
                rgb_image = display_image[:, :, [2, 1, 0]]  # BGR -> RGB
            else:  # BGR
                rgb_image = display_image[:, :, [2, 1, 0]]  # BGR -> RGB
            
            # Mark detected pixels with green dot
            if self.detected_pixels:
                for pixel_x, pixel_y in self.detected_pixels:
                    if 0 <= pixel_x < width and 0 <= pixel_y < height:
                        rgb_image[pixel_y, pixel_x] = [0, 255, 0]  # Green dot
            
            # Frame target cluster with blue rectangle
            if self.target_cluster and len(self.target_cluster) > 1:
                # Find cluster boundaries
                min_x = min(pixel[0] for pixel in self.target_cluster)
                max_x = max(pixel[0] for pixel in self.target_cluster)
                min_y = min(pixel[1] for pixel in self.target_cluster)
                max_y = max(pixel[1] for pixel in self.target_cluster)
                
                # Draw rectangle frame (blue)
                for x in range(max(0, min_x-1), min(width, max_x+2)):
                    if 0 <= min_y-1 < height:
                        rgb_image[min_y-1, x] = [0, 100, 255]  # Top edge
                    if 0 <= max_y+1 < height:
                        rgb_image[max_y+1, x] = [0, 100, 255]  # Bottom edge
                
                for y in range(max(0, min_y-1), min(height, max_y+2)):
                    if 0 <= min_x-1 < width:
                        rgb_image[y, min_x-1] = [0, 100, 255]  # Left edge
                    if 0 <= max_x+1 < width:
                        rgb_image[y, max_x+1] = [0, 100, 255]  # Right edge
                
                # Make pixels inside cluster yellow
                for pixel_x, pixel_y in self.target_cluster:
                    if 0 <= pixel_x < width and 0 <= pixel_y < height:
                        rgb_image[pixel_y, pixel_x] = [255, 255, 0]  # Yellow
            
            # Mark target point with orange circle (cluster center)
            if self.target_point:
                target_x, target_y = self.target_point
                if 0 <= target_x < width and 0 <= target_y < height:
                    # Draw orange circle around target point (5x5)
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            new_x = target_x + dx
                            new_y = target_y + dy
                            if 0 <= new_x < width and 0 <= new_y < height:
                                # Orange marker in circle shape
                                distance = dx*dx + dy*dy
                                if distance <= 4:  # Inside circle
                                    rgb_image[new_y, new_x] = [255, 165, 0]  # Orange
            
            # Convert numpy array to uint8 format
            rgb_image = np.clip(rgb_image, 0, 255).astype(np.uint8)
            rgb_image = np.ascontiguousarray(rgb_image)
            
            # Create QImage
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale image (better view for debug)
            scale_factor = min(290 / width, 290 / height)
            if scale_factor < 1:
                scale_factor = max(scale_factor, 0.4)  # Minimum 0.4x scaling
            else:
                scale_factor = min(scale_factor, 6)  # Maximum 6x scaling
            
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
            
            scaled_pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.FastTransformation)
            
            # Assign image to label
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            # Show coordinates as text in error case
            coords_text = f"Scan area: {width}x{height}\n"
            if self.target_point:
                coords_text += f"🎯 Target: ({self.target_point[0]},{self.target_point[1]})\n"
            if self.detected_pixels:
                coords_text += f"Detected pixels ({len(self.detected_pixels)}):\n"
                for i, (x, y) in enumerate(self.detected_pixels[:15]):  # First 15 coordinates
                    coords_text += f"({x},{y}) "
                    if i % 5 == 4:  # New line every 5 coordinates
                        coords_text += "\n"
                if len(self.detected_pixels) > 15:
                    coords_text += f"\n... and {len(self.detected_pixels) - 15} more"
            else:
                coords_text += "No pixels detected yet"
            self.image_label.setText(coords_text)
            print(f"Debug window image error: {e}")
    
    def display_numbered_targets_image(self):
        """Display debug image with numbered targets on screen"""
        if self.current_image is None:
            return
            
        try:
            height, width = self.current_image.shape[:2]
            
            # Copy original image
            display_image = self.current_image.copy()
            
            # Convert from BGRA format to RGB
            if display_image.shape[2] == 4:  # BGRA
                rgb_image = display_image[:, :, [2, 1, 0]]  # BGR -> RGB
            else:  # BGR
                rgb_image = display_image[:, :, [2, 1, 0]]  # BGR -> RGB
            
            # Mark detected pixels with light green dot (optimized)
            if self.detected_pixels:
                # Fast pixel processing using numpy array
                pixels_array = np.array(self.detected_pixels)
                if len(pixels_array) > 0:
                    # Filter valid coordinates
                    valid_mask = (pixels_array[:, 0] >= 0) & (pixels_array[:, 0] < width) & \
                                (pixels_array[:, 1] >= 0) & (pixels_array[:, 1] < height)
                    valid_pixels = pixels_array[valid_mask]
                    
                    if len(valid_pixels) > 0:
                        # Bulk pixel assignment (much faster)
                        rgb_image[valid_pixels[:, 1], valid_pixels[:, 0]] = [144, 238, 144]
            
            # Draw center circle (indicator area)
            if hasattr(self, 'scan_center_x') and hasattr(self, 'scan_center_y'):
                center_x, center_y = self.scan_center_x, self.scan_center_y
                radius = min(width, height) // 4  # Circle radius
                
                # Draw circle outline (white)
                for angle in range(0, 360, 2):
                    x = int(center_x + radius * np.cos(np.radians(angle)))
                    y = int(center_y + radius * np.sin(np.radians(angle)))
                    if 0 <= x < width and 0 <= y < height:
                        rgb_image[y, x] = [255, 255, 255]  # White circle
            
            # Draw numbered targets
            if hasattr(self, 'numbered_targets') and self.numbered_targets:
                colors = [
                    [255, 0, 0],      # 1. Target: Red (Primary target)
                    [255, 165, 0],    # 2. Target: Orange
                    [255, 255, 0],    # 3. Target: Yellow
                    [0, 255, 0],      # 4. Target: Green
                    [0, 255, 255],    # 5. Target: Cyan
                    [0, 0, 255],      # 6. Target: Blue
                    [128, 0, 128],    # 7. Target: Purple
                    [255, 192, 203],  # 8. Target: Pink
                ]
                
                for target in self.numbered_targets[:10]:  # Show maximum 10 targets
                    if not isinstance(target, dict):
                        continue
                    
                    cluster = target.get('cluster', [])
                    center = target.get('center')
                    number = target.get('number', 1)
                    
                    if not cluster or not center:
                        continue
                    
                    # Select color (maximum 8 different colors)
                    color = colors[(number - 1) % len(colors)]
                    
                    # Color cluster pixels (optimized with numpy)
                    if len(cluster) > 0:
                        cluster_array = np.array(cluster[:50])  # Maximum 50 pixels
                        valid_mask = (cluster_array[:, 0] >= 0) & (cluster_array[:, 0] < width) & \
                                    (cluster_array[:, 1] >= 0) & (cluster_array[:, 1] < height)
                        valid_cluster = cluster_array[valid_mask]
                        
                        if len(valid_cluster) > 0:
                            rgb_image[valid_cluster[:, 1], valid_cluster[:, 0]] = color
                    
                    # Draw rectangle frame around cluster
                    if len(cluster) > 1:
                        try:
                            min_x = max(0, min(pixel[0] for pixel in cluster) - 1)
                            max_x = min(width - 1, max(pixel[0] for pixel in cluster) + 1)
                            min_y = max(0, min(pixel[1] for pixel in cluster) - 1)
                            max_y = min(height - 1, max(pixel[1] for pixel in cluster) + 1)
                        except (ValueError, TypeError):
                            continue
                        
                        # Draw rectangle frame
                        for x in range(min_x, max_x + 1):
                            if 0 <= min_y < height:
                                rgb_image[min_y, x] = [255, 255, 255]  # Top edge
                            if 0 <= max_y < height:
                                rgb_image[max_y, x] = [255, 255, 255]  # Bottom edge
                        
                        for y in range(min_y, max_y + 1):
                            if 0 <= min_x < width:
                                rgb_image[y, min_x] = [255, 255, 255]  # Left edge
                            if 0 <= max_x < width:
                                rgb_image[y, max_x] = [255, 255, 255]  # Right edge
                    
                    # Mark center point with large dot
                    center_x, center_y = center
                    for dy in range(-3, 4):
                        for dx in range(-3, 4):
                            new_x = center_x + dx
                            new_y = center_y + dy
                            if 0 <= new_x < width and 0 <= new_y < height:
                                distance = dx*dx + dy*dy
                                if distance <= 9:  # 3x3 circle
                                    rgb_image[new_y, new_x] = [0, 0, 0]  # Black center point
                    
                    # Write number near center (simple pixel text)
                    self.draw_number_on_image(rgb_image, center_x + 5, center_y - 5, number, width, height)
            
            # Convert numpy array to uint8 format
            rgb_image = np.clip(rgb_image, 0, 255).astype(np.uint8)
            rgb_image = np.ascontiguousarray(rgb_image)
            
            # Create QImage
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale image (better view for debug)
            scale_factor = min(290 / width, 290 / height)
            if scale_factor < 1:
                scale_factor = max(scale_factor, 0.4)  # Minimum 0.4x scaling
            else:
                scale_factor = min(scale_factor, 6)  # Maximum 6x scaling
            
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
            
            scaled_pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.FastTransformation)
            
            # Assign image to label
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            # Show information in error case
            info_text = f"Scan area: {width}x{height}\n"
            if hasattr(self, 'numbered_targets') and self.numbered_targets:
                info_text += f"Found targets ({len(self.numbered_targets)}):\n"
                for target in self.numbered_targets[:10]:  # First 10 targets
                    center = target['center']
                    info_text += f"#{target['number']}: ({center[0]},{center[1]}) - Distance: {target['distance']:.1f}\n"
            else:
                info_text += "No targets detected yet"
            self.image_label.setText(info_text)
            print(f"Debug window numbered targets error: {e}")
    
    def draw_number_on_image(self, image, x, y, number, width, height):
        """Draw number on image (simple pixel text)"""
        # Simple 3x5 pixel number patterns
        number_patterns = {
            1: [[0,1,0], [1,1,0], [0,1,0], [0,1,0], [1,1,1]],
            2: [[1,1,1], [0,0,1], [1,1,1], [1,0,0], [1,1,1]],
            3: [[1,1,1], [0,0,1], [1,1,1], [0,0,1], [1,1,1]],
            4: [[1,0,1], [1,0,1], [1,1,1], [0,0,1], [0,0,1]],
            5: [[1,1,1], [1,0,0], [1,1,1], [0,0,1], [1,1,1]],
            6: [[1,1,1], [1,0,0], [1,1,1], [1,0,1], [1,1,1]],
            7: [[1,1,1], [0,0,1], [0,0,1], [0,0,1], [0,0,1]],
            8: [[1,1,1], [1,0,1], [1,1,1], [1,0,1], [1,1,1]],
            9: [[1,1,1], [1,0,1], [1,1,1], [0,0,1], [1,1,1]],
        }
        
        if number in number_patterns:
            pattern = number_patterns[number]
            for row_idx, row in enumerate(pattern):
                for col_idx, pixel in enumerate(row):
                    if pixel == 1:
                        px = x + col_idx
                        py = y + row_idx
                        if 0 <= px < width and 0 <= py < height:
                            image[py, px] = [255, 255, 255]  # White number
    
    def clear_debug_view(self):
        """Clear debug view"""
        self.image_label.setText("Waiting for scan...")
        self.info_label.setText("Detection: 0 | Target: None | Cluster: 0")
        self.current_image = None
        self.detected_pixels = []
        self.target_point = None
        self.target_cluster = None
        
        # Clear queue
        while not self.update_queue.empty():
            try:
                self.update_queue.get_nowait()
            except queue.Empty:
                break
    
    def closeEvent(self, event):
        """Stop timer when window is closed"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        super().closeEvent(event)