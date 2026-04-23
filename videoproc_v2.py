import os
import sys
import cv2
from video_common import (
    CachedJson,
    auto_orient,
    fit_to_screen,
    get_capture_dimensions,
    make_corner_points,
    read_with_loop,
    render_overlay,
)

VIDEO_PATH = "videos/testvideo.mp4"


def main():
    print(f"[v2] cwd={os.getcwd()}")
    print(f"[v2] video exists: {os.path.exists(VIDEO_PATH)}  path={VIDEO_PATH}")
    print(f"[v2] output.json exists: {os.path.exists('output.json')}")

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"[v2] ERROR: cv2.VideoCapture could not open '{VIDEO_PATH}'.")
        print("[v2] Likely missing FFmpeg backend in your OpenCV build.")
        print("[v2] Check: python -c \"import cv2; print(cv2.getBuildInformation())\" | grep FFMPEG")
        return

    width, height = get_capture_dimensions(cap)
    print(f"[v2] opened. raw size={width}x{height}")
    if height > width:
        width, height = height, width
        print(f"[v2] auto-oriented to landscape {width}x{height}")

    corner_points = make_corner_points(width, height)
    json_cache = CachedJson("output.json")
    frames_read = 0

    while cap.isOpened():
        ret, frame = read_with_loop(cap)
        if not ret:
            print(f"[v2] cap.read() returned False after {frames_read} frames. Exiting loop.")
            break
        frame = auto_orient(frame)
        frames_read += 1

        try:
            data = json_cache.get()
        except (OSError, ValueError) as e:
            print(f"[v2] output.json read error: {e}")
            data = None

        if data is not None:
            try:
                render_overlay(frame, data, corner_points)
            except Exception as e:
                print(f"[v2] render_overlay failed: {e}", file=sys.stderr)

        display = fit_to_screen(frame)
        try:
            cv2.imshow('Video', display)
        except cv2.error as e:
            print(f"[v2] cv2.imshow failed: {e}")
            print("[v2] Your OpenCV build has no GUI (opencv-python-headless?).")
            print("[v2] Fix: pip uninstall -y opencv-python-headless && pip install opencv-python")
            break

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
