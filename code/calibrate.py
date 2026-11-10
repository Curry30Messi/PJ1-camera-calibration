"""Calibrate the left camera and compare board scales. Run from any directory."""
import json
from pathlib import Path

import cv2
import numpy as np


RESULTS = Path(__file__).resolve().parent / "results"
BASE_FLAGS = cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K3


def calibrate(object_points, image_points, image_size, flags=BASE_FLAGS):
    """Fit one model to the supplied views, preserving their input order."""
    objects = [np.asarray(view, dtype=np.float32).reshape(-1, 3) for view in object_points]
    pixels = [np.asarray(view, dtype=np.float32).reshape(-1, 2) for view in image_points]
    return cv2.calibrateCamera(objects, pixels, tuple(map(int, image_size)),
                               None, None, flags=flags)


def main():
    output = RESULTS / "calibration"
    output.mkdir(parents=True, exist_ok=True)
    with np.load(RESULTS / "corners" / "corners.npz", allow_pickle=False) as data:
        objects = data["object_points"]
        pixels = data["image_points_refined"]
        size = data["image_size"].tolist()
        names = data["image_names"].tolist()

    for square_mm in (30, 60):
        rms, matrix, distortion, rotations, translations = calibrate(
            objects * (square_mm / 30), pixels, size
        )
        result = {
            "square_mm": square_mm, "image_size": size, "image_names": names,
            "model": "radial k1 k2; p1 p2 k3 fixed at zero",
            "distortion_order": ["k1", "k2", "p1", "p2", "k3"],
            "K": matrix.tolist(), "dist_coeffs": distortion.ravel().tolist(),
            "rvecs": [r.ravel().tolist() for r in rotations],
            "tvecs_mm": [t.ravel().tolist() for t in translations],
            "rmse_px": rms,
        }
        path = output / f"calibration_{square_mm}mm.json"
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"{square_mm} mm: RMSE = {rms:.6f} px -> {path}")


if __name__ == "__main__":
    main()
