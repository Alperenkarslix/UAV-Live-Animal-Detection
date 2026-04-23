import os
import cv2
from ultralytics import YOLO

MODEL_PATH = 'yolomodel/model/detect/train/weights/best.pt'
CONFIDENCE = 0.4


def detect_objects_in_video(input_video_path):
    if not os.path.isfile(input_video_path):
        print(f"Error: The input video file '{input_video_path}' does not exist.")
        return

    model = YOLO(MODEL_PATH)
    video = cv2.VideoCapture(input_video_path)

    if not video.isOpened():
        print(f"Error: Couldn't read video stream from file '{input_video_path}'.")
        return

    while video.isOpened():
        success, frame = video.read()
        if not success:
            print("Finished processing video.")
            break

        results = model(frame, conf=CONFIDENCE)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{confidence:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("YOLO", frame)
        if cv2.waitKey(1) == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_objects_in_video('videos/testvideo.mp4')
