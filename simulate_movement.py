import json
import math
import os
import random
import tempfile
import time

OUTPUT_PATH = "output.json"


def hesapla_metre(coord1, coord2):
    lat1 = math.radians(coord1[0])
    lon1 = math.radians(coord1[1])
    lat2 = math.radians(coord2[0])
    lon2 = math.radians(coord2[1])

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371000
    return R * c


def move_animals(animal_coords, center_lat, center_lon, verbose=False):
    for animal_info in animal_coords.values():
        animal_info["x"] += random.uniform(-0.00009, 0.00009)
        animal_info["y"] += random.uniform(-0.00009, 0.00009)

        distance = hesapla_metre(
            [animal_info["x"], animal_info["y"]],
            [center_lat, center_lon],
        )
        animal_info["distance_metre"] = distance

        if verbose:
            print(
                f"{animal_info['name']} konumu güncellendi: ({animal_info['x']}, {animal_info['y']})"
            )

    return animal_coords


def write_to_json(data, path=None):
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


def main():
    with open(OUTPUT_PATH) as f:
        data = json.load(f)

    center_lat = data["center_x"]
    center_lon = data["center_y"]

    while True:
        data["animal_coords"] = move_animals(
            data["animal_coords"], center_lat, center_lon, verbose=True
        )
        write_to_json(data)
        time.sleep(5)


if __name__ == "__main__":
    main()
