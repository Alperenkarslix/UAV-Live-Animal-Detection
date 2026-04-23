"""Centralized configuration for model paths and inference parameters.

Override any value with an environment variable, e.g.:

    UAV_MODEL=yolo26s.pt python videoproc_realtime.py
    UAV_CONF=0.3 python yolo_test_video.py
"""
import os

# Model
# Default = your fine-tuned weights (domain-specific, much better for UAV animals).
# YOLO26 hub weights (yolo26n.pt / yolo26s.pt / yolo26m.pt) are COCO-pretrained:
#   they know only 10 animal classes and have never seen UAV aerial views,
#   so out-of-the-box they will detect FAR FEWER animals than your fine-tuned model.
# To truly benefit from YOLO26, retrain on your dataset (see yolo_train.ipynb / ROADMAP Faz 1.1).
FINE_TUNED_MODEL = "yolomodel/yolo26_animals/weights/best.pt"
YOLO26_PRETRAINED = "yolo26n.pt"  # COCO — use only as a baseline or after fine-tuning

MODEL_PATH = os.environ.get("UAV_MODEL", FINE_TUNED_MODEL)

# Inference
CONFIDENCE = float(os.environ.get("UAV_CONF", "0.4"))
IMG_SIZE = int(os.environ.get("UAV_IMGSZ", "640"))
TRACKER = os.environ.get("UAV_TRACKER", "bytetrack.yaml")
DEVICE = os.environ.get("UAV_DEVICE", "")  # "" = auto, "cpu", "mps", "0" (cuda:0)

# Frame skipping for expensive models
PROCESS_EVERY_N_FRAMES = int(os.environ.get("UAV_STRIDE", "1"))

# Sources
VIDEO_PATH = os.environ.get("UAV_VIDEO", "videos/testvideo.mp4")
CAMERA_INDEX = int(os.environ.get("UAV_CAM", "0"))
