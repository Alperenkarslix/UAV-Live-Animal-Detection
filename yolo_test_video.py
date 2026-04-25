import os

import cv2

import config
from video_common import auto_orient, fit_to_screen, load_yolo, read_with_loop, run_yolo_overlay


def detect_objects_in_video(input_video_path):
    if not os.path.isfile(input_video_path):
        print(f"Error: The input video file '{input_video_path}' does not exist.")
        return

    print(
        f"[yolo_test_video] model={config.MODEL_PATH} conf={config.CONFIDENCE} imgsz={config.IMG_SIZE}"
    )
    model = load_yolo(config.MODEL_PATH, device=config.DEVICE)
    video = cv2.VideoCapture(input_video_path)

    if not video.isOpened():
        print(f"Error: Couldn't read video stream from file '{input_video_path}'.")
        return

    while video.isOpened():
        success, frame = read_with_loop(video)
        if not success:
            print("Finished processing video.")
            break
        frame = auto_orient(frame)

        run_yolo_overlay(frame, model, conf=config.CONFIDENCE, imgsz=config.IMG_SIZE)

        cv2.imshow("YOLO", fit_to_screen(frame))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_objects_in_video(config.VIDEO_PATH)
