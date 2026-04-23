import cv2
from ultralytics import YOLO

MODEL_PATH = 'yolomodel/model/detect/train/weights/best.pt'
CONFIDENCE = 0.4
IMG_SIZE = 640
PROCESS_EVERY_N_FRAMES = 5


def main():
    model = YOLO(MODEL_PATH)
    print(model.names)

    webcamera = cv2.VideoCapture(0)
    webcamera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcamera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_count = 0
    while True:
        success, frame = webcamera.read()
        if not success:
            print("Failed to capture frame from webcam. Exiting...")
            break

        frame_count += 1
        if frame_count % PROCESS_EVERY_N_FRAMES != 0:
            cv2.imshow("Live Camera", frame)
            if cv2.waitKey(1) == ord('q'):
                break
            continue

        results = model.track(frame, conf=CONFIDENCE, imgsz=IMG_SIZE)
        num_boxes = len(results[0].boxes)
        plotted_frame = results[0].plot()
        cv2.putText(plotted_frame, f"Total: {num_boxes}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Live Camera", plotted_frame)

        if cv2.waitKey(1) == ord('q'):
            break

    webcamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
