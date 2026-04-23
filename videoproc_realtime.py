import os
import sys
import traceback
import cv2
import config
from video_common import (
    CachedJson,
    auto_orient,
    detect_yolo,
    draw_detections,
    fit_to_screen,
    get_capture_dimensions,
    load_yolo,
    make_corner_points,
    render_overlay,
)


def main():
    print(f"[v4] cwd={os.getcwd()}")
    print(f"[v4] model={config.MODEL_PATH}  conf={config.CONFIDENCE}  imgsz={config.IMG_SIZE}")
    print(f"[v4] output.json exists: {os.path.exists('output.json')}")

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[v4] ERROR: cannot open camera index {config.CAMERA_INDEX}")
        print("[v4] On macOS, grant Camera permission to Terminal/iTerm in System Settings → Privacy.")
        return

    try:
        print("[v4] Loading YOLO model (first run may download weights)...")
        model = load_yolo(config.MODEL_PATH, device=config.DEVICE)
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
            cached_detections = []
            while True:
                success, yolo_frame = cap.read()
                if not success:
                    print("Failed to capture frame from webcam.")
                    break
                yolo_frame = auto_orient(yolo_frame)

                frame_count += 1
                if frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                    cached_detections = detect_yolo(
                        yolo_frame, model,
                        conf=config.CONFIDENCE, imgsz=config.IMG_SIZE,
                        use_tracking=True, tracker=config.TRACKER,
                    )
                draw_detections(yolo_frame, cached_detections)

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
