import cv2
import logging
from datetime import datetime
import time

import sys
import os
sys.path.append(os.path.dirname(__file__))

from config import *
from detection import ObjectDetector, LicensePlateDetector, HelmetDetector
from tracking import VehicleTracker, RiderTracker
from violations import ViolationDetector, SpeedEstimator
from evidence import EvidenceGenerator, EvidenceManager

# Set up logging
logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class TrafficViolationDetector:
    def __init__(self):
        self.config = self._load_config()
        self.detector = ObjectDetector()
        self.lp_detector = LicensePlateDetector()
        self.helmet_detector = HelmetDetector()
        self.vehicle_tracker = VehicleTracker()
        self.rider_tracker = RiderTracker()
        self.violation_detector = ViolationDetector(self.config)
        self.speed_estimator = SpeedEstimator()
        self.evidence_generator = EvidenceGenerator(self.config)
        self.evidence_manager = EvidenceManager(self.config)

        logger.info("Traffic Violation Detector initialized")

    def _load_config(self):
        """Load configuration (placeholder - using globals for now)"""
        class Config:
            OVERSPEED_THRESHOLD = 60
            TRIPLE_RIDING_MAX_PERSONS = 3
            SIGNAL_JUMP_DISTANCE = 50
            IMAGES_DIR = 'evidence/images/'
            CLIPS_DIR = 'evidence/clips/'
            BLUR_FACES = True
            FACE_BLUR_STRENGTH = 30
        return Config()

    def process_frame(self, frame):
        """Process a single frame for violations"""
        # Detect objects
        detections = self.detector.detect_objects(frame)

        # Separate detections
        vehicle_detections = self.detector.detect_vehicles(detections)
        person_detections = self.detector.detect_persons(detections)
        traffic_light_detections = self.detector.detect_traffic_lights(detections)

        # Track objects only if detections exist
        vehicle_tracks = []
        rider_tracks = []

        if vehicle_detections:
            vehicle_tracks = self.vehicle_tracker.update(vehicle_detections, frame)

        if person_detections:
            rider_tracks = self.rider_tracker.update(person_detections, frame)

        # Detect helmets only if riders exist
        helmet_detections = []
        if rider_tracks:
            helmet_detections = self.helmet_detector.detect_helmets(frame, rider_tracks)

        # Detect violations only if relevant objects exist
        violations = []
        current_time = datetime.now()

        # Signal jumping - only if vehicles and traffic lights exist
        if traffic_light_detections and vehicle_tracks:
            stop_line_y = frame.shape[0] // 2  # Placeholder stop line
            violations.extend(self.violation_detector.detect_signal_jump(
                vehicle_tracks, traffic_light_detections[0]['bbox'], stop_line_y))

        # Helmetless riding detection disabled as per user request
        # if rider_tracks:
        #     violations.extend(self.violation_detector.detect_helmetless_riding(
        #         rider_tracks, helmet_detections))

        # Overspeeding - only if vehicles exist
        if vehicle_tracks:
            violations.extend(self.violation_detector.detect_overspeeding(
                vehicle_tracks, current_time, self.speed_estimator))

        # Wrong lane detection disabled - focus on overspeeding and signal jumping only
        # if vehicle_tracks:
        #     violations.extend(self.violation_detector.detect_wrong_lane(vehicle_tracks, None))

        # Triple riding detection disabled - focus on overspeeding and signal jumping only
        # if vehicle_tracks and rider_tracks:
        #     violations.extend(self.violation_detector.detect_triple_riding(
        #         vehicle_tracks, rider_tracks))

        # Generate evidence for violations
        for violation in violations:
            # Extract license plate if vehicle violation
            lp_text = ""
            if 'vehicle_id' in violation and vehicle_tracks:
                vehicle_track = next((v for v in vehicle_tracks if v['id'] == violation['vehicle_id']), None)
                if vehicle_track:
                    lp_text = self.lp_detector.extract_license_plate(frame, vehicle_track['bbox'])

            evidence = self.evidence_generator.generate_evidence(violation, frame, lp_text)
            self.evidence_manager.add_evidence(evidence)

            logger.info(f"Violation detected: {violation['type']} at {violation['timestamp']}")

        return violations, vehicle_tracks, rider_tracks

    def run_live_detection(self, video_source=0):
        """Run live detection on video feed"""
        cap = cv2.VideoCapture(video_source)

        if not cap.isOpened():
            logger.error("Could not open video source")
            return

        logger.info("Starting live detection...")

        frame_count = 0
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize frame for processing
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # Process frame
            violations, vehicle_tracks, rider_tracks = self.process_frame(frame)

            # Draw results on frame
            display_frame = self._draw_results(frame, violations, vehicle_tracks, rider_tracks)

            # Add performance info
            frame_count += 1
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0

            cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Violations: {len(violations)}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Show frame
            cv2.imshow('Traffic Violation Detector', display_frame)

            # Add small delay to reduce CPU usage and improve responsiveness
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def _draw_results(self, frame, violations, vehicle_tracks, rider_tracks):
        """Draw detection results on frame"""
        # Draw vehicles
        for vehicle in vehicle_tracks:
            x1, y1, x2, y2 = vehicle['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"Vehicle {vehicle['id']}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Draw riders
        for rider in rider_tracks:
            x1, y1, x2, y2 = rider['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Rider {rider['id']}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Draw violations
        for violation in violations:
            x1, y1, x2, y2 = violation['evidence']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(frame, violation['type'].upper(), (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        return frame

if __name__ == "__main__":
    detector = TrafficViolationDetector()
    detector.run_live_detection('C:/Users/Medha Trust/Desktop/project/HTF25-Team-063/evidence/clips/vid4.mp4')
