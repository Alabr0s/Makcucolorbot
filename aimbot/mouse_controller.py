"""
Mouse movement controller module
Handles mouse movement calculations and TCP communication
"""

import time
from tcp_client import AimTCPClient


class MouseController:
    def __init__(self):
        """
        Constructor. Variables are configured for faster and more stable movement.
        """
        self.tcp_client = AimTCPClient()
        self.aim_speed = 3.0  # Default aim speed. Decimal value allows for more precise adjustment.
        self.last_target = None  # Last locked target position
        self.min_movement_threshold = 3  # Minimum movement threshold (reduced for more sensitive responses)
        
        # Smoothing/Soft Aim properties
        self.soft_aim_value = 0  # Soft aim value (0-100, 0=disabled)
        self.smoothing_enabled = False  # Is smoothing active
        self.movement_history = []  # History of recent movements
        self.max_history_size = 5  # Maximum history size
        
        # Adaptive aim prediction system
        self.prediction_enabled = False  # Is prediction system active
        self.prediction_strength = 50  # Prediction strength (0-100)
        self.target_velocity = None  # Target's velocity vector
        
        # RCS integration
        self.rcs_worker = None
        self.rcs_integration_enabled = True
        
        # Yeni eklenen özellikler
        self.last_send_time = time.time()
        self.send_cooldown = 0.001  # 1ms bekleme süresi
        self.send_queue = []  # Gönderim kuyruğu

    def calculate_direct_movement(self, target_x, target_y, center_x, center_y):
        """
        Enhanced mouse movement calculation - With Smoothing and Prediction support.
        """
        # Raw distance to target (vector)
        raw_move_x = target_x - center_x
        raw_move_y = target_y - center_y

        # If the distance to the target is less than the minimum threshold, no movement is needed.
        distance = (raw_move_x ** 2 + raw_move_y ** 2) ** 0.5
        if distance < self.min_movement_threshold:
            return 0, 0

        # Apply adaptive aim prediction
        if self.prediction_enabled and self.target_velocity:
            predicted_x, predicted_y = self.apply_prediction(target_x, target_y)
            raw_move_x = predicted_x - center_x
            raw_move_y = predicted_y - center_y
            
        # Calculate speed factor
        speed_factor = self.aim_speed / 10.0

        # Calculate basic movement
        move_x = raw_move_x * speed_factor
        move_y = raw_move_y * speed_factor
        
        # Apply soft aim/smoothing
        if self.smoothing_enabled and self.soft_aim_value > 0:
            move_x, move_y = self.apply_smoothing(move_x, move_y, distance)

        # Dynamically adjust maximum movement speed
        max_movement = 120.0
        
        # Limit movement to maximum value
        move_x = max(-max_movement, min(max_movement, move_x))
        move_y = max(-max_movement, min(max_movement, move_y))
        
        # Add to movement history for debug information
        self.add_to_movement_history(move_x, move_y)

        return int(move_x), int(move_y)

    def find_closest_target(self, positions, center_x, center_y):
        """
        Simpler, faster and more stable target selection that finds the closest target to the center.
        Directly finds the closest target instead of complex filtering.
        """
        if not positions:
            self.last_target = None
            return None

        # If we have previously locked onto a target and it's still on screen, prioritize it.
        # This prevents meaningless transitions (flickering) between targets.
        last_target = self.last_target
        if last_target is not None and isinstance(last_target, (list, tuple)) and len(last_target) >= 2:
            # Check if there's a point near `last_target` in `positions`
            is_last_target_still_visible = any(
                ((pos[0] - last_target[0]) ** 2 + (pos[1] - last_target[1]) ** 2) ** 0.5 < 25 # Stability threshold
                for pos in positions
            )
            if is_last_target_still_visible:
                 # Find the closest new position but still close to the last target
                closest_to_last = min(positions, key=lambda pos: ((pos[0] - last_target[0])**2 + (pos[1] - last_target[1])**2)**0.5)
                self.last_target = closest_to_last
                return closest_to_last

        # If a new target is to be selected, find the one closest to the screen center.
        closest_target = min(positions, key=lambda pos: ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5)
        
        self.last_target = closest_target
        return closest_target

    def send_movement(self, move_x, move_y):
        """
        Sends the calculated mouse movement to the TCP server.
        Prevents unnecessary data transmission by checking the minimum movement threshold.
        Cancels up/down movements when RCS is active with RCS integration.
        """
        current_time = time.time()
        
        # Gönderim sıklığını sınırla
        if current_time - self.last_send_time < self.send_cooldown:
            return False
            
        # RCS integration check
        if (self.rcs_integration_enabled and self.rcs_worker and 
            hasattr(self.rcs_worker, 'is_sending_rcs_down') and 
            self.rcs_worker.is_sending_rcs_down()):
            # RCS is active, only send horizontal movement
            move_y = 0
        
        if abs(move_x) >= self.min_movement_threshold or abs(move_y) >= self.min_movement_threshold:
            # For debug information
            debug_info = f"Movement: ({move_x}, {move_y}) | Smoothing: {self.smoothing_enabled} | Soft Aim: {self.soft_aim_value}%"
            # Simple retry mechanism against connection issues.
            success = self.tcp_client.send_movement(move_x, move_y)
            if not success:
                time.sleep(0.001)  # Short wait time
                success = self.tcp_client.send_movement(move_x, move_y)
                
            if success:
                self.last_send_time = current_time
                
            return success
        return False

    def apply_smoothing(self, move_x, move_y, distance):
        """
        Applies soft aim/smoothing - Compliant with memory specifications.
        """
        # Slowing factor based on soft aim value (maximum 50% slowing)
        smoothing_factor = 1.0 - (self.soft_aim_value / 100.0) * 0.5
        
        # Extra smoothing for small movements (< 30 pixels)
        if distance < 30:
            extra_smoothing = 0.8  # 20% extra smoothing
            smoothing_factor *= extra_smoothing
            
        # Apply smoothing
        smooth_x = move_x * smoothing_factor
        smooth_y = move_y * smoothing_factor
        
        return smooth_x, smooth_y

    def apply_prediction(self, target_x, target_y):
        """
        Adaptive aim prediction system - predicts target movement.
        """
        if not self.target_velocity:
            return target_x, target_y
            
        # Apply prediction based on prediction strength
        prediction_factor = self.prediction_strength / 100.0
        
        predicted_x = target_x + (self.target_velocity[0] * prediction_factor)
        predicted_y = target_y + (self.target_velocity[1] * prediction_factor)
        
        return predicted_x, predicted_y

    def update_target_velocity(self, current_target, previous_target):
        """
        Updates the target's velocity vector.
        """
        if current_target and previous_target:
            velocity_x = current_target[0] - previous_target[0]
            velocity_y = current_target[1] - previous_target[1]
            self.target_velocity = (velocity_x, velocity_y)
        else:
            self.target_velocity = None

    def add_to_movement_history(self, move_x, move_y):
        """
        Adds to movement history (for debug).
        """
        self.movement_history.append((move_x, move_y, time.time()))
        
        # Limit history size
        while len(self.movement_history) > self.max_history_size:
            self.movement_history.pop(0)

    def set_smoothing(self, soft_aim_value):
        """
        Updates smoothing settings - Compliant with memory specifications.
        """
        self.soft_aim_value = max(0, min(100, soft_aim_value))
        
        # Automatically enable/disable smoothing
        if self.soft_aim_value > 0:
            self.smoothing_enabled = True
        else:
            self.smoothing_enabled = False
            
    def set_prediction(self, enabled, strength=50):
        """
        Updates adaptive aim prediction settings.
        """
        self.prediction_enabled = enabled
        self.prediction_strength = max(0, min(100, strength))
        
    def get_debug_info(self):
        """
        Returns debug information.
        """
        return {
            'soft_aim_value': self.soft_aim_value,
            'smoothing_enabled': self.smoothing_enabled,
            'prediction_enabled': self.prediction_enabled,
            'prediction_strength': self.prediction_strength,
            'movement_history': self.movement_history[-3:] if self.movement_history else [],
            'target_velocity': self.target_velocity
        }

    def set_aim_speed(self, speed):
        """Sets aim speed (between 2-5000)."""
        self.aim_speed = float(max(2, min(5000, speed)))
    
    def set_rcs_worker(self, rcs_worker):
        """Sets RCS worker reference"""
        self.rcs_worker = rcs_worker
    
    def set_rcs_integration(self, enabled):
        """Enables/disables RCS integration"""
        self.rcs_integration_enabled = enabled

    def send_click(self):
        """Sends click command to TCP server."""
        return self.tcp_client.send_click()

    def send_fire_command(self):
        """Sends fire command to TCP server."""
        return self.tcp_client.send_fire_command()

    def reset_tracking(self):
        """
        Resets target tracking. This should be called when target is lost or
        when a new scan begins.
        """
        self.last_target = None

    def disconnect(self):
        """Safely closes TCP connection."""
        self.tcp_client.disconnect()
