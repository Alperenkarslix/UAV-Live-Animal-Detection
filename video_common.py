import cv2
import json
import os
from shapely.geometry import Point, Polygon

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)
EDGE_NAMES = ["Sag Taraf", "Ust Taraf", "Sol Taraf", "Alt Taraf"]


def calculate_pixel_coordinates(lat, lon, corner_coords, image_dimensions):
    (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4) = corner_coords
    image_width, image_height = image_dimensions

    lats = [lat1, lat2, lat3, lat4]
    lons = [lon1, lon2, lon3, lon4]
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)

    if lat_range == 0 or lon_range == 0:
        return image_width // 2, image_height // 2

    center_lat = sum(lats) / 4
    center_lon = sum(lons) / 4
    lat_scale = image_height / lat_range
    lon_scale = image_width / lon_range

    x = image_width / 2 + (lon - center_lon) * lon_scale
    y = image_height / 2 - (lat - center_lat) * lat_scale
    return int(x), int(y)


def load_output_data(path="output.json"):
    with open(path, "r") as f:
        return json.load(f)


class CachedJson:
    def __init__(self, path="output.json"):
        self.path = path
        self._mtime = 0
        self._data = None

    def get(self):
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            return self._data
        if mtime != self._mtime or self._data is None:
            with open(self.path, "r") as f:
                self._data = json.load(f)
            self._mtime = mtime
        return self._data


def draw_corner_labels(frame, camera_coords, corner_points):
    keys = list(corner_points.keys())
    for i, corner in enumerate(keys):
        if i >= len(camera_coords):
            break
        pos = corner_points[corner]
        x, y = camera_coords[i]
        text = f"{x:.6f}, {y:.6f}"
        cv2.putText(frame, text, pos, FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)


def _nearest_side_index(animal_x, animal_y, rect_coords):
    nearest_idx = 0
    min_distance = float('inf')
    for i, (start_x, start_y) in enumerate(rect_coords):
        end_x, end_y = rect_coords[(i + 1) % 4]
        side_cx = (start_x + end_x) / 2
        side_cy = (start_y + end_y) / 2
        distance = ((animal_x - side_cx) ** 2 + (animal_y - side_cy) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            nearest_idx = i
    return nearest_idx


def _draw_inside_animal(frame, animal_data, animal_x, animal_y, rect_coords, frame_w, frame_h, y_offset):
    cv2.putText(frame, f"{animal_data['name']} icinde", (0, y_offset), FONT, 0.5, TEXT_COLOR, 1, cv2.LINE_AA)
    px, py = calculate_pixel_coordinates(animal_x, animal_y, rect_coords, (frame_w, frame_h))
    cv2.rectangle(frame, (px - 10, py - 10), (px + 10, py + 10), (255, 0, 0), 1)
    text = f"{animal_data['name']}: Sicaklik{animal_data['temperature']:.2f}"
    tw, _ = cv2.getTextSize(text, FONT, 0.5, 1)[0]
    cv2.putText(frame, text, (px - tw // 2, py + 20), FONT, 0.5, TEXT_COLOR, 1, cv2.LINE_AA)


def _draw_outside_animal(frame, animal_data, animal_x, animal_y, rect_coords, frame_w, frame_h, y_offset):
    nearest_idx = _nearest_side_index(animal_x, animal_y, rect_coords)
    nearest_side_name = EDGE_NAMES[nearest_idx % len(EDGE_NAMES)]
    cv2.putText(
        frame,
        f"{animal_data['name']} disinda ({nearest_side_name})",
        (0, y_offset), FONT, 0.5, TEXT_COLOR, 1, cv2.LINE_AA,
    )

    target_x, target_y = calculate_pixel_coordinates(animal_x, animal_y, rect_coords, (frame_w, frame_h))
    center_x, center_y = frame_w // 2, frame_h // 2

    target_x = max(0, min(target_x, frame_w - 1))
    target_y = max(0, min(target_y, frame_h - 1))

    arrow_length = ((target_x - center_x) ** 2 + (target_y - center_y) ** 2) ** 0.5
    if arrow_length > 40:
        ratio = 40 / arrow_length
        start_x = int(target_x + (center_x - target_x) * ratio)
        start_y = int(target_y + (center_y - target_y) * ratio)
    else:
        start_x, start_y = center_x, center_y

    cv2.arrowedLine(frame, (start_x, start_y), (target_x, target_y), (0, 255, 0), 2)

    text = f"{animal_data['name']}: {animal_data['distance_metre']:.2f} metre Sicaklik{animal_data['temperature']:.2f}"
    tw, _ = cv2.getTextSize(text, FONT, 0.5, 1)[0]
    text_x = start_x if start_x + tw + 10 < frame_w else frame_w - tw - 10
    text_y = start_y + 20
    cv2.putText(frame, text, (text_x, text_y), FONT, 0.5, TEXT_COLOR, 1, cv2.LINE_AA)


def render_overlay(frame, data, corner_points):
    frame_h, frame_w = frame.shape[:2]
    camera_coords = data.get("camera_coords", [])
    animal_coords = data.get("animal_coords", {})

    if len(camera_coords) < 4:
        return

    draw_corner_labels(frame, camera_coords, corner_points)
    rect_coords = [list(camera_coords[i]) for i in range(4)]
    rect_polygon = Polygon(rect_coords)

    y_offset = 50
    for animal_data in animal_coords.values():
        animal_x = animal_data["x"]
        animal_y = animal_data["y"]
        animal_point = Point(animal_x, animal_y)

        if rect_polygon.contains(animal_point):
            _draw_inside_animal(frame, animal_data, animal_x, animal_y, rect_coords, frame_w, frame_h, y_offset)
        else:
            _draw_outside_animal(frame, animal_data, animal_x, animal_y, rect_coords, frame_w, frame_h, y_offset)
        y_offset += 30


def make_corner_points(width, height):
    return {
        "Sag Alt": (width - 260, height - 10),
        "Sag Ust": (width - 260, 20),
        "Sol Ust": (0, 20),
        "Sol Alt": (0, height - 7),
    }


def get_capture_dimensions(cap):
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        ret, frame = cap.read()
        if ret:
            height, width = frame.shape[:2]
    return width, height


def auto_orient(frame):
    h, w = frame.shape[:2]
    if h > w:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame


def fit_to_screen(frame, max_w=1280, max_h=720):
    h, w = frame.shape[:2]
    if w <= max_w and h <= max_h:
        return frame
    scale = min(max_w / w, max_h / h)
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def read_with_loop(cap):
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
    return ret, frame


def load_yolo(model_path, device=""):
    """Lazily import Ultralytics so modules that never run YOLO stay importable."""
    from ultralytics import YOLO
    model = YOLO(model_path)
    if device:
        try:
            model.to(device)
        except Exception as e:
            print(f"[yolo] could not move to device={device}: {e}")
    return model


def detect_yolo(frame, model, conf=0.4, imgsz=640, use_tracking=False, tracker="bytetrack.yaml"):
    """Run inference and return a list of (x1, y1, x2, y2, label, conf, track_id) tuples."""
    if use_tracking:
        results = model.track(frame, conf=conf, imgsz=imgsz, persist=True, tracker=tracker, verbose=False)
    else:
        results = model(frame, conf=conf, imgsz=imgsz, verbose=False)

    names = getattr(model, "names", {})
    detections = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            cls_id = int(box.cls[0]) if box.cls is not None else -1
            label = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(cls_id)
            track_id = int(box.id[0]) if getattr(box, "id", None) is not None else None
            detections.append((x1, y1, x2, y2, label, confidence, track_id))
    return detections


def draw_detections(frame, detections):
    for x1, y1, x2, y2, label, confidence, track_id in detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f"{label} {confidence:.2f}"
        if track_id is not None:
            text = f"#{track_id} " + text
        cv2.putText(frame, text, (x1, max(y1 - 10, 15)), FONT, 0.5, (0, 255, 0), 2)
    return frame


def run_yolo_overlay(frame, model, conf=0.4, imgsz=640, use_tracking=False, tracker="bytetrack.yaml"):
    detections = detect_yolo(frame, model, conf=conf, imgsz=imgsz, use_tracking=use_tracking, tracker=tracker)
    return draw_detections(frame, detections)
