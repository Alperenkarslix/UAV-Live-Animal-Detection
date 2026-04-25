import json
import math
import os
import tempfile
import threading

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

OUTPUT_PATH = "output.json"
_file_lock = threading.Lock()


def hesapla_kus(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def hesapla_metre(coord1, coord2):
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371000
    return R * c


def _atomic_write_json(data, path=None):
    if path is None:
        path = OUTPUT_PATH
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".output_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _read_json(path=None):
    if path is None:
        path = OUTPUT_PATH
    with open(path) as f:
        return json.load(f)


def _build_dataset(marker_data_list, rectangle_data_list):
    if len(rectangle_data_list) < 4:
        raise ValueError("rectangleData must contain at least 4 corners")

    corners = rectangle_data_list[:4]
    sum_x = sum(coord[0] for coord in corners)
    sum_y = sum(coord[1] for coord in corners)
    center_x = sum_x / 4
    center_y = sum_y / 4

    animals_coords = {
        f"animal_coords_{i + 1}": {
            "x": coords[0],
            "y": coords[1],
            "name": f"Hayvan{i + 1}",
            "temperature": 15 + (i + 1) * 2,
            "distance_metre": hesapla_metre((center_x, center_y), coords),
        }
        for i, coords in enumerate(marker_data_list)
    }

    return {
        "center_x": center_x,
        "center_y": center_y,
        "animal_coords": animals_coords,
        "camera_coords": corners,
    }


@app.route("/sonuc", methods=["POST"])
def sonuc():
    try:
        marker_data = json.loads(request.form.get("markerData", "[]"))
        rectangle_data = json.loads(request.form.get("rectangleData", "[]"))

        if not isinstance(marker_data, list) or not isinstance(rectangle_data, list):
            return jsonify({"error": "Invalid data shape"}), 400
        if not marker_data or len(rectangle_data) < 4:
            return jsonify({"error": "Invalid or missing data"}), 400

        data = _build_dataset(marker_data, rectangle_data)

        with _file_lock:
            _atomic_write_json(data)

        return render_template(
            "sonuc.html",
            mdList=marker_data,
            rcList=data["camera_coords"],
            orta_nokta=(data["center_x"], data["center_y"]),
            data=data,
        )

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@app.route("/get_data", methods=["GET"])
def get_data():
    try:
        if not os.path.exists(OUTPUT_PATH):
            return jsonify({"error": "Data not found"}), 404
        with _file_lock:
            data = _read_json()
        return jsonify(data)
    except json.JSONDecodeError:
        return jsonify({"error": "Data corrupted"}), 500


@app.route("/save_coordinates", methods=["POST"])
def save_coordinates():
    data = request.get_json(silent=True) or {}
    camera_coords = data.get("camera_coords")
    center_coords = data.get("center_coords")

    if not camera_coords or not center_coords:
        return jsonify({"error": "Invalid or missing data"}), 400

    try:
        with _file_lock:
            existing_data = _read_json() if os.path.exists(OUTPUT_PATH) else {}
            existing_data.update(
                {
                    "camera_coords": camera_coords,
                    "center_x": center_coords[0],
                    "center_y": center_coords[1],
                }
            )
            _atomic_write_json(existing_data)

        return jsonify({"status": "success"}), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Data corrupted"}), 500


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
