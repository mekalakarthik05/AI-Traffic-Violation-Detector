import os

# Configuration for the AI Traffic Violation Detector

# Model paths
YOLO_MODEL_PATH = 'models/yolov8n.pt'  # Lightweight YOLOv8 nano model
DEEP_SORT_MODEL_PATH = 'models/deep_sort.ckpt'  # DeepSORT model

# Detection classes (COCO dataset indices)
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
PERSON_CLASS = 0  # person
HELMET_CLASS = None  # Custom model needed for helmet detection
TRAFFIC_LIGHT_CLASS = 9  # traffic light

# Violation thresholds
OVERSPEED_THRESHOLD = 60  # km/h
TRIPLE_RIDING_MAX_PERSONS = 3
SIGNAL_JUMP_DISTANCE = 50  # pixels from stop line

# Video settings
VIDEO_SOURCE = r"C:\Users\GoliReddy\Desktop\dhaka_traffic.mp4"  # Dhaka traffic video
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# Evidence storage
EVIDENCE_DIR = 'evidence/'
IMAGES_DIR = os.path.join(EVIDENCE_DIR, 'images/')
CLIPS_DIR = os.path.join(EVIDENCE_DIR, 'clips/')

# Dashboard settings
DASHBOARD_PORT = 8501

# Privacy settings
BLUR_FACES = False
FACE_BLUR_STRENGTH = 30

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/traffic_detector.log'
