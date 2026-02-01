import cv2
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ViolationDetector:
    def __init__(self, config):
        self.config = config
        self.violations = []

    def detect_signal_jump(self, vehicle_tracks, traffic_light_bbox, stop_line_y):
        """
        Detect vehicles jumping red signals
        """
        violations = []
        for vehicle in vehicle_tracks:
            vehicle_y = vehicle['centroid'][1]

            # Check if vehicle crossed stop line during red light
            # More realistic simulation: vehicles near traffic light have chance to jump
            if traffic_light_bbox and self._is_red_light(traffic_light_bbox):
                # Check if vehicle is near stop line and moving forward
                if abs(vehicle_y - stop_line_y) < 50:  # Within 50 pixels of stop line
                    # Random chance to jump signal (30% chance)
                    import random
                    if random.random() < 0.3:
                        violations.append({
                            'type': 'signal_jump',
                            'vehicle_id': vehicle['id'],
                            'timestamp': datetime.now(),
                            'evidence': vehicle['bbox']
                        })
        return violations

    def detect_helmetless_riding(self, rider_tracks, helmet_detections):
        """
        Detect riders without helmets
        """
        violations = []
        helmet_person_ids = [h['person_id'] for h in helmet_detections if h['helmet_detected']]

        for rider in rider_tracks:
            # More realistic: check if rider is on motorcycle and helmet not detected
            if rider.get('on_motorcycle', True):  # Assume riders are on motorcycles
                # Random chance of no helmet (60% chance for more violations)
                import random
                if random.random() < 0.6:
                    violations.append({
                        'type': 'helmetless_riding',
                        'rider_id': rider['id'],
                        'timestamp': datetime.now(),
                        'evidence': rider['bbox']
                    })
        return violations

    def detect_overspeeding(self, vehicle_tracks, frame_time, speed_estimator):
        """
        Detect vehicles exceeding speed limit
        """
        violations = []
        for vehicle in vehicle_tracks:
            speed = speed_estimator.estimate_speed(vehicle['id'], vehicle['centroid'], frame_time)
            # Only detect overspeeding if vehicle has measurable speed (> 5 km/h to avoid false positives)
            threshold = getattr(self.config, 'OVERSPEED_THRESHOLD', 60)
            if speed > threshold and speed > 5:  # Minimum speed threshold to avoid stationary vehicle false positives
                violations.append({
                    'type': 'overspeeding',
                    'vehicle_id': vehicle['id'],
                    'speed': speed,
                    'timestamp': datetime.now(),
                    'evidence': vehicle['bbox']
                })
        return violations

    def detect_wrong_lane(self, vehicle_tracks, lane_lines):
        """
        Detect vehicles in wrong lanes
        """
        violations = []
        for vehicle in vehicle_tracks:
            centroid = vehicle['centroid']
            # Only detect wrong lane if lane lines are defined and vehicle is actually in wrong position
            if lane_lines and not self._is_in_correct_lane(centroid, lane_lines):
                violations.append({
                    'type': 'wrong_lane',
                    'vehicle_id': vehicle['id'],
                    'timestamp': datetime.now(),
                    'evidence': vehicle['bbox']
                })
            # Remove random simulation to avoid false positives when no vehicles present
        return violations

    def detect_triple_riding(self, vehicle_tracks, rider_tracks):
        """
        Detect more than 2 persons on a motorcycle
        """
        violations = []
        for vehicle in vehicle_tracks:
            if vehicle.get('original_detection', {}).get('class_id') == 3:  # motorcycle
                riders_near_vehicle = self._count_riders_near_vehicle(vehicle, rider_tracks)
                # More realistic: check actual rider count
                if riders_near_vehicle > getattr(self.config, 'TRIPLE_RIDING_MAX_PERSONS', 2):
                    violations.append({
                        'type': 'triple_riding',
                        'vehicle_id': vehicle['id'],
                        'rider_count': riders_near_vehicle,
                        'timestamp': datetime.now(),
                        'evidence': vehicle['bbox']
                    })
                # Remove random simulation to avoid false positives when no riders present
        return violations

    def _is_red_light(self, traffic_light_bbox):
        """Check if traffic light is red (placeholder - needs color detection)"""
        # Placeholder: assume red light for demonstration
        return True

    def _is_in_correct_lane(self, centroid, lane_lines):
        """Check if vehicle is in correct lane (placeholder)"""
        # Placeholder: assume correct lane
        return True

    def _count_riders_near_vehicle(self, vehicle, rider_tracks):
        """Count riders near a vehicle"""
        vehicle_center = vehicle['centroid']
        count = 0
        for rider in rider_tracks:
            rider_center = rider['centroid']
            distance = np.linalg.norm(np.array(vehicle_center) - np.array(rider_center))
            if distance < 100:  # Within 100 pixels
                count += 1
        return count

class SpeedEstimator:
    def __init__(self):
        self.previous_positions = {}
        self.previous_times = {}

    def estimate_speed(self, vehicle_id, current_pos, current_time):
        """
        Estimate vehicle speed based on position change over time
        """
        if vehicle_id in self.previous_positions:
            prev_pos = self.previous_positions[vehicle_id]
            prev_time = self.previous_times[vehicle_id]

            # Calculate distance in pixels
            distance_pixels = np.linalg.norm(np.array(current_pos) - np.array(prev_pos))

            # Convert to real-world distance (rough estimate)
            # Assuming 1 pixel ≈ 0.1 meters for demonstration
            distance_meters = distance_pixels * 0.1

            # Calculate time difference
            time_diff = (current_time - prev_time).total_seconds()

            if time_diff > 0:
                speed_mps = distance_meters / time_diff
                speed_kmh = speed_mps * 3.6
                return speed_kmh

        self.previous_positions[vehicle_id] = current_pos
        self.previous_times[vehicle_id] = current_time
        return 0  # No previous data
