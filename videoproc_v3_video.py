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
    read_with_loop,
    render_overlay,
    run_yolo_overlay,
)

VIDEO_PATH = "videos/testvideo.mp4"
MODEL_PATH = "yolomodel/model/detect/train/weights/best.pt"
PROCESS_EVERY_N_FRAMES = 5


def main():
    print(f"[v3] cwd={os.getcwd()}")
    print(f"[v3] video exists: {os.path.exists(VIDEO_PATH)}  path={VIDEO_PATH}")
    print(f"[v3] model exists: {os.path.exists(MODEL_PATH)}  path={MODEL_PATH}")
    print(f"[v3] output.json exists: {os.path.exists('output.json')}")

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"[v3] ERROR: cannot open video '{VIDEO_PATH}'")
        return

    try:
        print("[v3] Loading YOLO model (first run may take a while)...")
        model = YOLO(MODEL_PATH)
        print("[v3] Model loaded.")
    except Exception as e:
        print(f"[v3] YOLO load failed: {e}", file=sys.stderr)
        traceback.print_exc()
        cap.release()
        return

    width, height = get_capture_dimensions(cap)
    print(f"[v3] video raw size: {width}x{height}")
    if height > width:
        width, height = height, width
        print(f"[v3] auto-oriented to landscape {width}x{height}")
    corner_points = make_corner_points(width, height)
    json_cache = CachedJson("output.json")
    frames_read = 0

    while cap.isOpened():
        ret, frame = read_with_loop(cap)
        if not ret:
            print(f"[v3] cap.read() False after {frames_read} frames.")
            break
        frame = auto_orient(frame)
        frames_read += 1

        try:
            data = json_cache.get()
        except (OSError, ValueError) as e:
            print(f"[v3] output.json read error: {e}")
            data = None

        if data is not None:
            try:
                render_overlay(frame, data, corner_points)
            except Exception as e:
                print(f"[v3] render_overlay failed: {e}", file=sys.stderr)

        display = fit_to_screen(frame)
        try:
            cv2.imshow('Video', display)
        except cv2.error as e:
            print(f"[v3] cv2.imshow failed: {e}")
            print("[v3] Fix: pip uninstall -y opencv-python-headless && pip install opencv-python")
            break

        key = cv2.waitKey(25) & 0xFF
        if key == ord('y'):
            cv2.destroyWindow('Video')

            frame_count = 0
            while True:
                success, yolo_frame = read_with_loop(cap)
                if not success:
                    print("Video ended.")
                    break
                yolo_frame = auto_orient(yolo_frame)

                frame_count += 1
                if frame_count % PROCESS_EVERY_N_FRAMES == 0:
                    run_yolo_overlay(yolo_frame, model)

                cv2.imshow("YOLO", fit_to_screen(yolo_frame))

                if cv2.waitKey(25) & 0xFF == ord('y'):
                    cv2.destroyWindow("YOLO")
                    break

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
