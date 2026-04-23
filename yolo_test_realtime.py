import cv2
import config
from video_common import load_yolo, fit_to_screen, auto_orient


def main():
    print(f"[yolo_test_realtime] model={config.MODEL_PATH} conf={config.CONFIDENCE} imgsz={config.IMG_SIZE}")
    model = load_yolo(config.MODEL_PATH, device=config.DEVICE)
    print("classes:", model.names)

    webcamera = cv2.VideoCapture(config.CAMERA_INDEX)
    webcamera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcamera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_count = 0
    while True:
        success, frame = webcamera.read()
        if not success:
            print("Failed to capture frame from webcam. Exiting...")
            break
        frame = auto_orient(frame)

        frame_count += 1
        if frame_count % config.PROCESS_EVERY_N_FRAMES != 0:
            cv2.imshow("Live Camera", fit_to_screen(frame))
            if cv2.waitKey(1) == ord('q'):
                break
            continue

        results = model.track(frame, conf=config.CONFIDENCE, imgsz=config.IMG_SIZE,
                              tracker=config.TRACKER, persist=True, verbose=False)
        num_boxes = len(results[0].boxes) if results else 0
        plotted_frame = results[0].plot() if results else frame
        cv2.putText(plotted_frame, f"Total: {num_boxes}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Live Camera", fit_to_screen(plotted_frame))

        if cv2.waitKey(1) == ord('q'):
            break

    webcamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
