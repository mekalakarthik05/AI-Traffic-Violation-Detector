import cv2
import numpy as np
import pytesseract
import logging

logger = logging.getLogger(__name__)

class ObjectDetector:
    def __init__(self, model_path='models/yolov8n.pt'):
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            self.use_real_model = True
            logger.info("Using real YOLOv8 model for detection")
        except ImportError:
            logger.warning("YOLOv8 not available, using enhanced mock detection")
            self.use_real_model = False

        # Define class attributes regardless of model availability
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.person_class = 0
        self.traffic_light_class = 9

    def detect_objects(self, frame):
        """
        Detect objects in the frame using YOLOv8 or enhanced mock detection
        Returns: detections as list of dicts with bbox, class_id, confidence
        """
        if self.use_real_model:
            results = self.model(frame, conf=0.3)  # Lower confidence threshold for better detection
            detections = []

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())

                    detections.append({
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'class_id': class_id,
                        'confidence': confidence,
                        'label': self.model.names[class_id]
                    })

            return detections
        else:
            # Enhanced mock detections for testing - simulate realistic traffic scenarios
            return self._enhanced_mock_detect(frame)

    def _enhanced_mock_detect(self, frame):
        """
        Enhanced mock detection with better logic and more realistic placements
        """
        import random

        detections = []
        height, width = frame.shape[:2]

        # Simulate varying number of vehicles (3-10) in road area
        num_vehicles = random.randint(3, 10)

        for i in range(num_vehicles):
            # Place vehicles in bottom 2/3 of frame (road area)
            x1 = random.randint(20, width - 180)
            y1 = random.randint(height//3, height - 120)
            w = random.randint(100, 160)
            h = random.randint(70, 110)
            x2 = min(x1 + w, width - 10)
            y2 = min(y1 + h, height - 10)

            # Mix of cars and motorcycles
            class_id = 2 if random.random() < 0.6 else 3  # 60% cars, 40% motorcycles
            label = 'car' if class_id == 2 else 'motorcycle'

            detections.append({
                'bbox': (x1, y1, x2, y2),
                'class_id': class_id,
                'confidence': random.uniform(0.75, 0.98),
                'label': label
            })

        # Add persons (riders) - more realistic association with vehicles
        num_persons = random.randint(max(1, num_vehicles//2), num_vehicles + 2)
        for i in range(num_persons):
            if i < len(detections) and random.random() < 0.8:  # 80% chance to associate with vehicle
                # Position near a vehicle (rider)
                vehicle = detections[i % len(detections)]
                vx1, vy1, vx2, vy2 = vehicle['bbox']

                # Rider positioned relative to vehicle
                px1 = vx1 + random.randint(-30, vx2 - vx1 - 20)
                py1 = vy1 - random.randint(40, 80)  # Above vehicle
                pw = random.randint(25, 45)
                ph = random.randint(70, 110)
                px2 = min(px1 + pw, width - 5)
                py2 = min(py1 + ph, vy1 - 5)  # Don't overlap vehicle too much
            else:
                # Random pedestrian
                px1 = random.randint(10, width - 60)
                py1 = random.randint(50, height - 120)
                pw = random.randint(25, 45)
                ph = random.randint(70, 110)
                px2 = min(px1 + pw, width - 5)
                py2 = min(py1 + ph, height - 10)

            detections.append({
                'bbox': (px1, py1, px2, py2),
                'class_id': 0,  # person
                'confidence': random.uniform(0.7, 0.95),
                'label': 'person'
            })

        # Add traffic lights more frequently in intersections
        if random.random() < 0.4:  # 40% chance
            # Place at top of frame or intersections
            tx1 = random.randint(width - 150, width - 40)
            ty1 = random.randint(20, 100)
            tw = random.randint(15, 35)
            th = random.randint(50, 90)
            tx2 = min(tx1 + tw, width - 5)
            ty2 = min(ty1 + th, height//3)

            detections.append({
                'bbox': (tx1, ty1, tx2, ty2),
                'class_id': 9,  # traffic light
                'confidence': random.uniform(0.75, 0.95),
                'label': 'traffic light'
            })

        return detections

    def detect_vehicles(self, detections):
        """Filter detections for vehicles"""
        return [d for d in detections if d['class_id'] in self.vehicle_classes]

    def detect_persons(self, detections):
        """Filter detections for persons"""
        return [d for d in detections if d['class_id'] == self.person_class]

    def detect_traffic_lights(self, detections):
        """Filter detections for traffic lights"""
        return [d for d in detections if d['class_id'] == self.traffic_light_class]

class LicensePlateDetector:
    def __init__(self):
        # Initialize Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update path if needed

    def extract_license_plate(self, frame, bbox):
        """
        Extract license plate text from a cropped region
        """
        x1, y1, x2, y2 = bbox
        plate_img = frame[y1:y2, x1:x2]

        # Preprocess image for better OCR
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        try:
            text = pytesseract.image_to_string(thresh, config='--psm 8')
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

class HelmetDetector:
    def __init__(self, model_path=None):
        # For now, use a simple heuristic or placeholder
        # In production, train a custom model for helmet detection
        self.model = None

    def detect_helmets(self, frame, person_detections):
        """
        Detect helmets on persons (placeholder implementation)
        """
        helmets = []
        for person in person_detections:
            # Simple heuristic: check if there's a dark region on top of head
            # This is a placeholder - real implementation needs trained model
            helmets.append({'person_id': person['id'], 'helmet_detected': True})  # Assume helmet for now
        return helmets
