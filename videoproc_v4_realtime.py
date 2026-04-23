import os
import sys
import traceback
import cv2
from ultralytics import YOLO
from video_common import (
    CachedJson,
    auto_orient,
    fit_to_screen,
    get_capture_dimensions,
    make_corner_points,
    render_overlay,
    run_yolo_overlay,
)

MODEL_PATH = "yolomodel/model/detect/train/weights/best.pt"
PROCESS_EVERY_N_FRAMES = 5
CAMERA_INDEX = 0


def main():
    print(f"[v4] cwd={os.getcwd()}")
    print(f"[v4] model exists: {os.path.exists(MODEL_PATH)}  path={MODEL_PATH}")
    print(f"[v4] output.json exists: {os.path.exists('output.json')}")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[v4] ERROR: cannot open camera index {CAMERA_INDEX}")
        print("[v4] On macOS, grant Camera permission to Terminal/iTerm in System Settings → Privacy.")
        return

    try:
        print("[v4] Loading YOLO model...")
        model = YOLO(MODEL_PATH)
        print("[v4] Model loaded.")
    except Exception as e:
        print(f"[v4] YOLO load failed: {e}", file=sys.stderr)
        traceback.print_exc()
        cap.release()
        return

    width, height = get_capture_dimensions(cap)
    print(f"[v4] camera raw size: {width}x{height}")
    if height > width:
        width, height = height, width
        print(f"[v4] auto-oriented to landscape {width}x{height}")
    corner_points = make_corner_points(width, height)
    json_cache = CachedJson("output.json")
    frames_read = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print(f"[v4] cap.read() False after {frames_read} frames.")
            break
        frame = auto_orient(frame)
        frames_read += 1

        try:
            data = json_cache.get()
        except (OSError, ValueError) as e:
            print(f"[v4] output.json read error: {e}")
            data = None

        if data is not None:
            try:
                render_overlay(frame, data, corner_points)
            except Exception as e:
                print(f"[v4] render_overlay failed: {e}", file=sys.stderr)

        try:
            cv2.imshow('Video', fit_to_screen(frame))
        except cv2.error as e:
            print(f"[v4] cv2.imshow failed: {e}")
            print("[v4] Fix: pip uninstall -y opencv-python-headless && pip install opencv-python")
            break

        key = cv2.waitKey(1) & 0xFF
        if key == ord('y'):
            cv2.destroyWindow('Video')

            frame_count = 0
            while True:
                success, yolo_frame = cap.read()
                if not success:
                    print("Failed to capture frame from webcam.")
                    break
                yolo_frame = auto_orient(yolo_frame)

                frame_count += 1
                if frame_count % PROCESS_EVERY_N_FRAMES == 0:
                    run_yolo_overlay(yolo_frame, model)

                cv2.imshow("YOLO", fit_to_screen(yolo_frame))

                if cv2.waitKey(1) & 0xFF == ord('y'):
                    cv2.destroyWindow("YOLO")
                    break

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
