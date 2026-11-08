# PJ1 Camera Calibration

A collaborative project for the Intelligent Information Processing course. The project uses Python and OpenCV to perform monocular camera calibration based on Zhang's planar calibration method, estimate intrinsic parameters, distortion coefficients and per-view extrinsics, and evaluate the results through controlled experiments.

**Submission deadline: November 18, 2026, 23:59 (Asia/Shanghai).**

The repository currently contains a report template and four input images. Experiment scripts and results will be added by the assigned contributors.

## Experimental Setup

| Item | Configuration |
|---|---|
| Dataset | Calibration board 2, left camera |
| Images | `Im_L_1.png` through `Im_L_4.png` |
| Resolution | 1024 × 576 pixels |
| Square size | 30 mm |
| Board coordinates | Z = 0; object coordinates in mm |
| Baseline model | Estimate k1 and k2; fix k3, p1, p2 and skew to zero |
| Metrics | Overall and per-view reprojection RMSE, line-fitting residuals, parameter variation |

The pipeline covers corner detection and subpixel refinement, baseline calibration, residual analysis, image undistortion, distortion-model comparison, and image-subset stability. Inner-corner dimensions and point ordering must be verified during data preparation and shared across all experiments.

## Repository Structure

```text
.
├── README.md
├── report/
│   └── camera-calibration.docx
└── code/
    ├── data/                 Original calibration images
    └── results/              Corners, parameters, tables and figures
```

Place experiment scripts under `code/` and record dependencies in `code/requirements.txt`. Resolve paths relative to the project or script location. Preserve the original input images. Include key code excerpts, result tables, figures and analysis in the report while retaining the complete source files separately.

Repository paths and identifiers use English. The report body remains in Chinese. Any directory references retained in the report template correspond to `report/`, `code/`, `code/data/` and `code/results/` in this repository.

## Contributors and Schedule

| Contributor | Responsibilities | Planned script | Report section | Target date |
|---|---|---|---|---|
| Lu Yuanzhuo | Dataset verification, object-point generation, corner detection and refinement; detection rate, displacement and runtime analysis | `detect_corners.py` | Chapter 1 | Nov 8 |
| Yu Zhibo | Shared calibration function, intrinsic and extrinsic estimation; 30 mm versus 60 mm scale comparison | `calibrate.py` | Chapter 2 | Nov 9 |
| Zhu Qiancheng | Shared reprojection-error function; per-view and central/peripheral residual analysis | `evaluate.py` | Chapter 3 | Nov 10 |
| Zhang Shuaiyu | Undistortion, before/after comparisons and detail views; board-row or column straightness evaluation | `undistort.py` | Chapter 4 | Nov 11 |
| Yang Xiaofang | Comparison of zero-distortion, radial-only and radial-plus-tangential models | `compare_models.py` | Chapter 5 | Nov 12–13 |
| Zheng Zhourui | Three-view subsets versus all four views; parameter stability and result summary | `subset_stability.py` | Chapter 6 | Nov 14–15 |

Each contributor owns the implementation, experiment and report section for their module. Delivery follows the order above. Content review and presentation preparation are scheduled for November 16–17. Script names are planned interfaces; the scripts have not yet been implemented.

## Interfaces and Evaluation

- **Corner data:** Store image names, image size, inner-corner dimensions, square size, initial and refined image points, and corresponding object points. Maintain consistent point ordering.
- **Calibration output:** Store K, distortion coefficients and their ordering, per-view rotation and translation vectors, selected images and model configuration. The shared function must support image subsets and distortion-model settings.
- **Reprojection error:** Compute RMSE as the square root of the mean squared two-dimensional Euclidean distance between detected and projected corners. Use the same definition for per-view and overall results, in pixels.
- **Undistortion:** Record the output intrinsic matrix and cropping configuration. Transform the same detected points into the corrected pixel coordinate system before fitting board lines.
- **Controlled comparisons:** Keep images and corners fixed when comparing distortion models. Keep the model fixed when comparing subsets. The 60 mm square size is a scale-control experiment; the formal calibration uses 30 mm.
- **Interpretation:** Training reprojection error is not ground-truth calibration accuracy. Treat the four-view estimate as a stability reference, not as true camera parameters. Retain failed configurations and document their causes.

## Collaboration and Deliverables

Development follows sequential delivery on `main`. Contributors start from the latest remote revision and submit source code, experiment outputs and the corresponding report section together. Record the commit identifier and execution details at each handover. Reuse shared functions in subsequent modules.

Maintain one report at `report/camera-calibration.docx`, with each chapter starting on a new page. Edit the Word document sequentially to avoid binary merge conflicts. Preserve completed sections and earlier modules. Use English commit messages identifying the contributor, module and main change.

Each module must deliver:

1. Runnable source code and dependency information.
2. Parameter files, numerical results and experiment figures.
3. A completed report section covering configuration, key code, results and analysis.
4. Execution commands, input/output locations and configuration needed by downstream modules.

## Execution Record

Complete this table as each module becomes available.

| Module | Command | Main outputs |
|---|---|---|
| Corner detection | Pending | Image/object points, detection visualizations and statistics |
| Baseline calibration | Pending | Intrinsics, distortion, per-view extrinsics and scale comparison |
| Error evaluation | Pending | Point residuals, per-view and overall errors, regional statistics |
| Undistortion | Pending | Corrected images, detail comparisons and straightness metrics |
| Model comparison | Pending | Model parameters, errors and corrected-image comparisons |
| Subset stability | Pending | Parameters, errors and variation across image combinations |

## Submission

For Elearning submission, rename the report using the course-required format: group identifier followed by the Chinese report title for camera calibration, separated by a hyphen, with the `.docx` extension. The English repository filename is for version control only.

The report must list members and contributions at the beginning and include the method, monocular images and experimental results. Package it with complete source code, input data, experiment outputs and execution instructions in one ZIP archive using the corresponding course-required name. One group member submits the archive. Exclude `.git`, virtual environments and temporary files.
