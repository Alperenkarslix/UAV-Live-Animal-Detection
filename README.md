# UAV Live Animal Detection

This project aims to track and monitor wild animals using UAV (Unmanned Aerial Vehicle) cameras. It involves advanced image processing techniques to detect and visualize animals' positions within the UAV camera's field of view.

## Project Overview

The main objective is to locate and track animals within a UAV image and visualize their positions. If an animal is outside the UAV image, a cursor indicates its position and distance.

### Key Features
- **Real-Time Animal Tracking**: Detects and tracks animals in real-time using UAV camera imagery.
- **Distance Calculation**: Calculates the distance of animals from the UAV camera using the Haversine formula.
- **Visualization**: Displays animals' positions within the image or indicates their positions and distances if outside the image frame.
- **Web-Based Simulation**: Uses Python's Flask library for a web-based simulation of UAV camera and animal positions.
- **YOLOv8 Model**: Employs the YOLOv8 model for high-performance animal detection and classification.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Alperenkarslix/UAV-Live-Animal-Detection.git
   cd UAV-Live-Animal-Detection
   ```

2. Create a virtual environment and activate it:
   ```
   python3 -m venv env
   source env/bin/activate   # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the web application (creates/updates `output.json`):
   ```
   python testdatas.py
   ```
   Open `http://localhost:5000` in your browser, enter the number of animals, place markers, drag the camera rectangle, and click **Kaydet**.

2. (Optional) Simulate animal movement over time:
   ```
   python hareket.py
   ```
   This periodically mutates `output.json`.

3. Start the video processor:
   - Without YOLO: `python videoproc_v2.py`
   - Video file with YOLO toggle (press `y`): `python videoproc_v3_video.py`
   - Live camera with YOLO toggle: `python videoproc_v4_realtime.py`

## Project Structure

- `testdatas.py` — Flask application that captures animal/camera coordinates from the map.
- `hareket.py` — Background simulator that perturbs animal coordinates in `output.json`.
- `video_common.py` — Shared overlay/rendering helpers used by the video processors.
- `videoproc_v1.py` — Legacy pixel-space demo with random animal positions.
- `videoproc_v2.py` — Video overlay using real `output.json` coordinates.
- `videoproc_v3_video.py` — Same as v2 plus toggleable YOLO detection on the video file.
- `videoproc_v4_realtime.py` — Same as v3 but reads from a live webcam.
- `yolo_test_video.py` / `yolo_test_realtime.py` — Standalone YOLO testers.
- `yolomodel/` — Trained YOLOv8 weights (`yolomodel/model/detect/train/weights/best.pt`).
- `templates/` — Flask Jinja templates (`index.html`, `sonuc.html`).
- `videos/` — Sample input videos.
- `output.json` — Shared state: camera polygon, animal coordinates, distances.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

## Contact

For any questions or inquiries, please contact the project contributors:
- Anıl Taha ADAK: tahaadak94@gmail.com
- Alperen KARSLI: alperenkarsliceng@gmail.com
- Asil FINDIK: asilfndk@gmail.com

Academic Advisor: Doç. Dr. Fatih AYDIN
Industrial Advisor: Dr. Muhterem Özgür KIZILKAYA
