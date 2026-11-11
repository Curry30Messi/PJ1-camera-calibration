"""Evaluate the 30 mm calibration against the saved subpixel observations."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


CODE_DIR = Path(__file__).resolve().parent
RESULTS = CODE_DIR / "results"
VECTOR_SCALE = 40
RMSE_TOLERANCE_PX = 1e-6


@dataclass(frozen=True)
class Reprojection:
    projected: np.ndarray
    residuals: np.ndarray
    distances: np.ndarray


def reprojection_errors(object_points, image_points, camera_matrix, dist_coeffs, rvecs, tvecs):
    """Return one Reprojection per view in input order.

    Residuals are observed minus projected (u, v), in pixels. Supply matching
    views and corresponding points in the same order. OpenCV's (N, 1, 2)
    observations and (N, 2) observations are both accepted.
    """
    results = []
    for objects, observations, rotation, translation in zip(
        object_points, image_points, rvecs, tvecs, strict=True
    ):
        objects = np.asarray(objects, dtype=np.float64).reshape(-1, 3)
        observed = np.asarray(observations, dtype=np.float64).reshape(-1, 2)
        if len(objects) == 0 or len(objects) != len(observed):
            raise ValueError("Each view needs an equal, nonzero number of 3D and 2D points.")
        projected, _ = cv2.projectPoints(
            objects, rotation, translation, camera_matrix, dist_coeffs
        )
        projected = projected.reshape(-1, 2)
        residuals = observed - projected
        distances = np.linalg.norm(residuals, axis=1)
        if not np.all(np.isfinite(distances)):
            raise ValueError("Reprojection distances must be finite.")
        results.append(Reprojection(projected, residuals, distances))
    if not results:
        raise ValueError("At least one view is required.")
    return results


def rmse_px(distances):
    """Compute RMSE over pointwise Euclidean distances, pooled across views if needed."""
    distances = np.asarray(distances, dtype=np.float64)
    if distances.size == 0:
        raise ValueError("At least one distance is required for RMSE.")
    return float(np.sqrt(np.mean(distances**2)))


def summarize(distances):
    count = len(distances)
    return (
        count,
        rmse_px(distances) if count else None,
        float(np.max(distances)) if count else None,
    )


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def plot_rmse(output, names, values, total):
    from matplotlib.figure import Figure

    fig = Figure(figsize=(7.2, 2.8), layout="constrained")
    ax = fig.subplots()
    bars = ax.bar(names, values, width=0.53, color="#225c83", label="Per-view RMSE")
    ax.bar_label(
        bars, labels=[f"{value:.4f}" for value in values], label_type="center", color="white"
    )
    ax.axhline(total, color="#9c451e", linestyle="--", label=f"Pooled RMSE = {total:.4f} px")
    ax.set(ylabel="RMSE (px)", ylim=(0, max(values) * 1.34))
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, ncols=2)
    fig.savefig(output, dpi=180, facecolor="white")


def plot_residuals(output, image, view, summary, bounds, name):
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle

    x_min, x_max, y_min, y_max = bounds
    height, width = image.shape
    fig = Figure(figsize=(7.2, 4.65), layout="constrained")
    ax = fig.subplots()
    ax.imshow(image, cmap="gray", vmin=-55, vmax=420, interpolation="nearest")
    ax.add_patch(Rectangle(
        (x_min, y_min), x_max - x_min, y_max - y_min,
        fill=False, edgecolor="#79e4ff", linewidth=0.95, linestyle="--",
    ))
    u, v = view.projected.T
    du, dv = (view.residuals * VECTOR_SCALE).T
    ax.scatter(u, v, s=5, color="#fff0a8", edgecolors="none")
    arrows = dict(
        angles="xy", scale_units="xy", scale=1, color="#fff0a8", width=0.002,
        minshaft=1, minlength=0,
    )
    ax.quiver(u, v, du, dv, **arrows)
    ax.quiver(width - 202, 39, 0.5 * VECTOR_SCALE, 0, **arrows)
    ax.text(width - 171, 39, f"0.5 px ({VECTOR_SCALE}x)", color="white", va="center", fontsize=9)
    ax.set(xlim=(-0.5, width - 0.5), ylim=(height - 0.5, -0.5), xlabel="u (px)", ylabel="v (px)")
    ax.set_title(f"{name}  |  RMSE {summary[1]:.4f} px  |  Max {summary[2]:.4f} px")
    fig.savefig(output, dpi=180, facecolor="white")


def main():
    corners_path = RESULTS / "corners" / "corners.npz"
    calibration_path = RESULTS / "calibration" / "calibration_30mm.json"
    params = json.loads(calibration_path.read_text(encoding="utf-8"))
    with np.load(corners_path, allow_pickle=False) as corners:
        names = corners["image_names"].tolist()
        width, height = corners["image_size"].tolist()
        columns, rows = corners["pattern_size"].tolist()
        square_size = corners["square_size_mm"].item()
        objects = corners["object_points"]
        observed = corners["image_points_refined"].astype(np.float64).reshape(len(names), -1, 2)

    if (
        params["image_size"] != [width, height]
        or params["square_mm"] != square_size
        or params["image_names"] != names
        or params["distortion_order"] != ["k1", "k2", "p1", "p2", "k3"]
        or observed.shape[1] != columns * rows
    ):
        raise ValueError("The corner data and 30 mm calibration metadata do not match.")

    views = reprojection_errors(
        objects, observed, np.asarray(params["K"]), np.asarray(params["dist_coeffs"]),
        np.asarray(params["rvecs"]), np.asarray(params["tvecs_mm"]),
    )
    all_distances = np.concatenate([view.distances for view in views])
    total = summarize(all_distances)
    delta = abs(total[1] - params["rmse_px"])
    if not np.isfinite(delta) or delta > RMSE_TOLERANCE_PX:
        raise ValueError(f"Pooled RMSE differs from calibrateCamera by {delta:.9g} px.")

    images = []
    for name in names:
        # imdecode supports non-ASCII project paths on Windows.
        data = (CODE_DIR / "data" / name).read_bytes()
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is None or image.shape != (height, width):
            raise ValueError(f"{name} is unreadable or has unexpected dimensions.")
        images.append(image)

    x_min, x_max = width / 4, 3 * width / 4
    y_min, y_max = height / 4, 3 * height / 4
    u, v = observed.transpose(2, 0, 1)
    is_center = (x_min <= u) & (u < x_max) & (y_min <= v) & (v < y_max)

    view_stats = [summarize(view.distances) for view in views]
    point_rows = []
    region_rows = []
    for name, pixels, view, center in zip(names, observed, views, is_center, strict=True):
        for index, (pixel, projected, residual, distance, inside) in enumerate(zip(
            pixels, view.projected, view.residuals, view.distances, center, strict=True
        )):
            row, col = divmod(index, columns)
            point_rows.append((
                name, index, row, col, *pixel, *projected, *residual, distance,
                "center" if inside else "periphery",
            ))
        region_rows.extend((
            (name, "center", *summarize(view.distances[center])),
            (name, "periphery", *summarize(view.distances[~center])),
        ))
    flat_center = is_center.ravel()
    region_rows.extend((
        ("all", "center", *summarize(all_distances[flat_center])),
        ("all", "periphery", *summarize(all_distances[~flat_center])),
    ))

    output = RESULTS / "evaluation"
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    stat_fields = ("point_count", "rmse_px", "max_error_px")
    write_csv(output / "summary.csv", ("image_name", *stat_fields), [
        *((name, *stats) for name, stats in zip(names, view_stats, strict=True)),
        ("all", *total),
    ])
    write_csv(output / "regions.csv", ("image_name", "region", *stat_fields), region_rows)
    write_csv(output / "points.csv", (
        "image_name", "point_index", "board_row", "board_col", "observed_u_px", "observed_v_px",
        "projected_u_px", "projected_v_px", "residual_u_px", "residual_v_px", "error_px", "region",
    ), point_rows)
    verification = {
        "calibration_file": calibration_path.relative_to(CODE_DIR.parent).as_posix(),
        "corners_file": corners_path.relative_to(CODE_DIR.parent).as_posix(),
        "image_names": names,
        "point_count": total[0],
        "recomputed_rmse_px": total[1],
        "calibration_rmse_px": params["rmse_px"],
        "absolute_difference_px": delta,
        "tolerance_px": RMSE_TOLERANCE_PX,
        "center_bounds_px": {"u": [x_min, x_max], "v": [y_min, y_max]},
        "center_bounds_convention": "Observed coordinates; inclusive lower, exclusive upper.",
        "residual_definition": "observed - projected",
        "vector_scale": VECTOR_SCALE,
    }
    (output / "verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )

    plot_rmse(figures / "per_view_rmse.png", [Path(name).stem for name in names],
              [stats[1] for stats in view_stats], total[1])
    for name, image, view, stats in zip(names, images, views, view_stats, strict=True):
        stem = Path(name).stem
        plot_residuals(figures / f"{stem}_residuals.png", image, view, stats,
                       (x_min, x_max, y_min, y_max), stem)
    print(f"{total[0]} points: RMSE {total[1]:.9f} px (difference {delta:.3g} px)")
    print(f"Results: {output}")


if __name__ == "__main__":
    main()
