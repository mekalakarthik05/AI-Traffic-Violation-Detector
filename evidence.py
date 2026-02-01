import cv2
import os
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EvidenceGenerator:
    def __init__(self, config):
        self.config = config
        self._create_directories()

    def _create_directories(self):
        """Create directories for storing evidence"""
        os.makedirs(self.config.IMAGES_DIR, exist_ok=True)
        os.makedirs(self.config.CLIPS_DIR, exist_ok=True)

    def generate_evidence(self, violation, frame, license_plate_text=""):
        """
        Generate evidence for a violation
        """
        timestamp = violation['timestamp'].strftime("%Y%m%d_%H%M%S")
        violation_type = violation['type']
        vehicle_id = violation.get('vehicle_id', violation.get('rider_id', 'unknown'))

        # Generate timestamped image
        image_filename = f"{violation_type}_{vehicle_id}_{timestamp}.jpg"
        image_path = os.path.join(self.config.IMAGES_DIR, image_filename)

        # Draw bounding box on frame
        evidence_frame = self._draw_violation_box(frame.copy(), violation)

        # Apply privacy blur if enabled
        if self.config.BLUR_FACES:
            evidence_frame = self._blur_faces(evidence_frame)

        cv2.imwrite(image_path, evidence_frame)

        # Generate clip (placeholder - would need frame buffer)
        clip_path = self._generate_clip(violation, timestamp)

        evidence = {
            'violation_type': violation_type,
            'timestamp': violation['timestamp'],
            'image_path': image_path,
            'clip_path': clip_path,
            'license_plate': license_plate_text,
            'bbox': violation['evidence']
        }

        logger.info(f"Evidence generated for {violation_type}: {image_path}")
        return evidence

    def _draw_violation_box(self, frame, violation):
        """Draw bounding box around violation area"""
        x1, y1, x2, y2 = violation['evidence']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # Add violation text
        text = f"{violation['type'].upper()}"
        cv2.putText(frame, text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        return frame

    def _blur_faces(self, frame):
        """Apply face blurring for privacy"""
        try:
            # Simple face detection using Haar cascades
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                # Blur the face region
                face_roi = frame[y:y+h, x:x+w]
                blurred_face = cv2.GaussianBlur(face_roi, (self.config.FACE_BLUR_STRENGTH, self.config.FACE_BLUR_STRENGTH), 0)
                frame[y:y+h, x:x+w] = blurred_face
        except cv2.error as e:
            logger.warning(f"Face blurring failed: {e}. Skipping face blur.")
            # Return original frame if face blurring fails
            pass

        return frame

    def _generate_clip(self, violation, timestamp):
        """Generate video clip of violation (placeholder)"""
        # In a real implementation, this would save a short video clip
        # For now, just return a placeholder path
        clip_filename = f"clip_{violation['type']}_{timestamp}.mp4"
        clip_path = os.path.join(self.config.CLIPS_DIR, clip_filename)
        return clip_path

class EvidenceManager:
    def __init__(self, config):
        self.config = config
        self.evidence_list = []

    def add_evidence(self, evidence):
        """Add evidence to the list"""
        self.evidence_list.append(evidence)

    def get_recent_violations(self, limit=10):
        """Get recent violations for dashboard"""
        return sorted(self.evidence_list, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def export_evidence(self, filepath):
        """Export evidence to CSV or JSON"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.evidence_list, f, default=str, indent=2)
