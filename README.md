# PJ1 Camera Calibration

A six-member project for the Intelligent Information Processing course. The project uses Python and OpenCV to perform monocular calibration based on Zhang's planar calibration method, estimate camera intrinsics, distortion coefficients and per-view extrinsics, and evaluate the results through controlled experiments.

**Submission deadline: November 18, 2026, 23:59 (Asia/Shanghai).**

The repository currently contains the report template and calibration images. Experiment scripts and results will be added by the assigned module owners.

## Dataset and Method

| Item | Configuration |
|---|---|
| Dataset | Calibration board 2, left camera |
| Images | `Im_L_1.png` through `Im_L_4.png` |
| Resolution | 1024 × 576 pixels |
| Square size | 30 mm |
| Board coordinates | Z = 0; world coordinates in mm |
| Baseline model | Estimate k1 and k2; fix k3, p1, p2 and skew to zero |
| Metrics | Overall and per-view reprojection RMSE, line-fitting residuals and parameter variation |

The pipeline covers corner detection and subpixel refinement, baseline calibration, reprojection analysis, undistortion, distortion-model comparison and image-subset stability analysis. The corner grid dimensions and ordering must be verified during data preparation and used consistently throughout the project.

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

Experiment scripts belong in `code/`. Record dependency versions in `code/requirements.txt` and use portable relative paths. Preserve the original images. The report contains key code excerpts, results, figures and analysis; complete source files are maintained separately. The report body remains in Chinese for course submission.

## Responsibilities and Schedule

| Member | Module and experiment | Planned script | Report | Target date |
|---|---|---|---|---|
| Lu Yuanzhuo | Dataset verification, board coordinates, corner detection and refinement; detection rate, displacement and timing | `detect_corners.py` | Chapter 1 | Nov 8 |
| Yu Zhibo | Shared calibration function, baseline parameters and 30 mm versus 60 mm scale comparison | `calibrate.py` | Chapter 2 | Nov 9 |
| Zhu Qiancheng | Shared reprojection evaluation; per-view and central/peripheral residual analysis | `evaluate.py` | Chapter 3 | Nov 10 |
| Zhang Shuaiyu | Undistortion, image comparisons, detail views and board-line straightness evaluation | `undistort.py` | Chapter 4 | Nov 11 |
| Yang Xiaofang | Comparison of zero-distortion, radial-only and radial-plus-tangential models | `compare_models.py` | Chapter 5 | Nov 12–13 |
| Zheng Zhourui | Three-view subsets versus the full four-view set; parameter stability and result summary | `subset_stability.py` | Chapter 6 | Nov 14–15 |

Each member delivers the assigned code, experiments and report chapter in the listed order. Review and presentation preparation are scheduled for November 16–17. Script names are planned interfaces; the initial repository does not yet implement them.

## Module Interfaces and Evaluation

- **Corner data:** Save image names and sizes, grid dimensions, square size, initial and refined image points, and corresponding object points with consistent ordering.
- **Calibration output:** Save K, distortion coefficients and their ordering, per-view rotation and translation vectors, image selection and model settings. The shared function must support different subsets and distortion configurations.
- **Reprojection error:** Compute RMSE as the square root of the mean squared two-dimensional Euclidean distance per corner, in pixels. Apply the same definition to overall and per-view results.
- **Undistortion:** Record the output camera matrix and cropping settings. Transform the same detected points into corrected pixel coordinates before comparing line-fitting residuals.
- **Controlled comparisons:** Fix images and corners when comparing models; fix the model when comparing subsets. The 60 mm square size is a scale-control experiment only; use 30 mm for the reported calibration.
- **Interpretation:** Training reprojection error is not ground-truth calibration accuracy. Full-set estimates are a reference for stability analysis, not true camera parameters. Retain failed configurations with explanations.

## Versioning and Deliverables

Development follows sequential ownership on `main`. Each member starts from the latest remote revision and commits the code, outputs and assigned report chapter together, recording the revision and execution details. Later modules reuse shared functions.

Maintain one report at `report/camera-calibration.docx`, with each chapter starting on a new page. Edit the Word file sequentially to avoid binary merge conflicts. Preserve completed chapters and previous modules. Commit messages should identify the contributor, module and main change; use English for repository-facing names, descriptions and future commit messages.

Each module delivers:

1. Runnable source code and dependency information.
2. Parameter files, result tables and experiment figures.
3. A completed report chapter with settings, key code, results and analysis.
4. Execution commands, input/output locations and configuration required by subsequent modules.

## Execution Records

Module owners will add the actual entry points, dependency versions and output locations upon completion.

| Module | Command | Main outputs |
|---|---|---|
| Corner detection | Pending | Image/object points, overlays and detection statistics |
| Baseline calibration | Pending | Intrinsics, distortion, per-view extrinsics and scale comparison |
| Error evaluation | Pending | Point residuals, per-view/overall errors and regional statistics |
| Undistortion | Pending | Corrected images, detail comparisons and straightness metrics |
| Model comparison | Pending | Model parameters, errors and corrected-image comparisons |
| Subset stability | Pending | Subset parameters, errors and variation analysis |

## Course Submission

For the final course upload, rename the report according to the instructor's group-number naming convention. Keep the member contributions, method, monocular images and experimental results in the report. Package the report, complete code, input data, outputs and execution instructions into one ZIP file for submission by one member through Elearning. Exclude `.git`, virtual environments and temporary files.
