"""Chapter 1: deterministic chessboard observations and refinement experiments.

Run from any directory: python /path/to/code/detect_corners.py
No calibration or other chapters are performed by this module.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path
from time import perf_counter_ns

import cv2
import numpy as np

BASE = Path(__file__).resolve().parent
PATTERN = (11, 7)  # inner corners: columns, rows (12 x 8 squares)
FLAGS = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)


def object_grid(pattern=PATTERN, square_mm=30.0):
    """Row-major object points; x increases first. Origin is corner index 0."""
    cols, rows = pattern
    if cols < 2 or rows < 2 or not np.isfinite(square_mm) or square_mm <= 0:
        raise ValueError('Invalid grid dimensions or square size')
    points = np.zeros((cols * rows, 3), np.float32)
    points[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_mm
    return points


def read_image(path):
    """Unicode-path-safe loading, without implicit EXIF rotation."""
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f'Unreadable image: {path}')
    return img


def detect(gray, pattern=PATTERN):
    ok, corners = cv2.findChessboardCorners(gray, pattern, FLAGS)
    if not ok or corners is None or len(corners) != pattern[0] * pattern[1]:
        raise ValueError(f'Complete {pattern} inner-corner grid not detected')
    # Resolve the 180-degree ordering ambiguity consistently in the image.
    # This is not a guarantee of a common physical origin on an unmarked board.
    if tuple(corners[0, 0, ::-1]) > tuple(corners[-1, 0, ::-1]):
        corners = corners[::-1].copy()
    return np.ascontiguousarray(corners, dtype=np.float32)


def refine(gray, initial, half_window=5):
    if half_window < 1:
        raise ValueError('Window half size must be positive')
    return cv2.cornerSubPix(gray, initial.copy(), (half_window, half_window),
                            (-1, -1), CRITERIA)


def displacement(initial, refined):
    return np.linalg.norm(refined.reshape(-1, 2).astype(np.float64)
                          - initial.reshape(-1, 2), axis=1)


def benchmark(fn, repeats):
    for _ in range(3):
        fn()
    times = []
    for _ in range(repeats):
        t = perf_counter_ns()
        fn()
        times.append((perf_counter_ns() - t) / 1e6)
    return np.asarray(times)


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_image(path, img):
    ok, encoded = cv2.imencode('.png', img)
    if not ok:
        raise RuntimeError(f'Cannot encode {path}')
    encoded.tofile(path)


def make_overlay(image, points):
    canvas = image.copy()
    cv2.drawChessboardCorners(canvas, PATTERN, points, True)
    for i, xy in enumerate(points[:, 0]):
        x, y = np.rint(xy).astype(int)
        text = str(i)
        cv2.putText(canvas, text, (x + 3, y - 4), cv2.FONT_HERSHEY_SIMPLEX,
                    .27, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, text, (x + 3, y - 4), cv2.FONT_HERSHEY_SIMPLEX,
                    .27, (0, 0, 0), 1, cv2.LINE_AA)
    # Highlight the coordinate origin and positive board axes.
    p = np.rint(points[:, 0]).astype(int)
    for end, label in [(1, 'X'), (PATTERN[0], 'Y')]:
        cv2.arrowedLine(canvas, tuple(p[0]), tuple(p[end]), (0, 0, 255), 2)
        cv2.putText(canvas, label, tuple(p[end] + [3, 10]),
                    cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 0, 255), 1, cv2.LINE_AA)
    return canvas


def figures(out, images, initials, refineds, summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.dpi': 200})
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), layout='constrained')
    for ax, image, row in zip(axes.flat, images, summary):
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax.set_title(row['image']); ax.axis('off')
    fig.savefig(out / 'figures/originals.png'); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), layout='constrained')
    vals = [displacement(a, b) for a, b in zip(initials, refineds)]
    axes[0].boxplot(vals, tick_labels=['L1', 'L2', 'L3', 'L4'], showmeans=True)
    axes[0].set(ylabel='Refinement displacement (px)', title='Additional refinement: 77 corners/view')
    x = np.arange(4)
    for off, key, label in [(-.18,'detect_median_ms','Detection'),(.18,'refine_median_ms','Refinement')]:
        axes[1].bar(x+off,[r[key] for r in summary],width=.36,label=label)
    axes[1].set(xticks=x,xticklabels=['L1','L2','L3','L4'],ylabel='Median time (ms)',title='Single-thread timing; I/O excluded')
    axes[1].legend();fig.savefig(out/'figures/displacement_timing.png');plt.close(fig)
    # A fixed-size native-pixel patch per image, chosen at maximum displacement.
    fig, axes = plt.subplots(2,2,figsize=(9,7),layout='constrained')
    for ax,image,a,b,row in zip(axes.flat,images,initials,refineds,summary):
        k=int(np.argmax(displacement(a,b)));u,v=a[k,0];cx,cy=int(round(u)),int(round(v));radius=10
        patch=image[cy-radius:cy+radius+1,cx-radius:cx+radius+1]
        ax.imshow(cv2.cvtColor(patch,cv2.COLOR_BGR2RGB),extent=(cx-radius-.5,cx+radius+.5,cy+radius+.5,cy-radius-.5),interpolation='nearest')
        ax.plot(*a[k,0],marker='+',color='#ff8c00',ms=14,mew=2,label='Initial')
        ax.plot(*b[k,0],marker='x',color='#00bfff',ms=10,mew=2,label='Refined')
        ax.set_title(f"{row['image']}, ID {k}, shift {row['max_shift_px']:.4f} px")
        ax.set(xlabel='u (px)',ylabel='v (px)');ax.legend(fontsize=8)
    fig.savefig(out/'figures/refinement_details.png');plt.close(fig)


def run(data_dir, output_dir, repeats=30):
    if repeats < 5:
        raise ValueError('At least 5 timing repetitions are required')
    cv2.setNumThreads(1);cv2.setRNGSeed(0)
    paths = [data_dir/f'Im_L_{i}.png' for i in range(1,5)]
    images=[read_image(p) for p in paths]
    if any(im.shape[:2] != (576,1024) for im in images):
        raise ValueError('All four inputs must have original resolution 1024x576')
    grays=[cv2.cvtColor(im,cv2.COLOR_BGR2GRAY) for im in images]
    # Validate every detection before exporting a shared calibration dataset.
    initials=[detect(g) for g in grays]
    refineds=[refine(g,a) for g,a in zip(grays,initials)]
    grid=object_grid();summary=[];point_rows=[];sensitivity=[];timing=[]
    for path,g,a,b in zip(paths,grays,initials,refineds):
        det=benchmark(lambda:detect(g),repeats)
        sub=benchmark(lambda:refine(g,a),repeats)
        delta=displacement(a,b)
        summary.append(dict(image=path.name,width=1024,height=576,detected=True,corners=len(b),
                            mean_shift_px=float(delta.mean()),median_shift_px=float(np.median(delta)),
                            p95_shift_px=float(np.percentile(delta,95)),max_shift_px=float(delta.max()),
                            detect_median_ms=float(np.median(det)),detect_iqr_ms=float(np.percentile(det,75)-np.percentile(det,25)),
                            refine_median_ms=float(np.median(sub)),refine_iqr_ms=float(np.percentile(sub,75)-np.percentile(sub,25))))
        for trial,(dt,st) in enumerate(zip(det,sub)):
            timing.append(dict(image=path.name,trial=trial,detect_ms=float(dt),refine_ms=float(st)))
        for i,(obj,aa,bb,dd) in enumerate(zip(grid,a[:,0],b[:,0],delta)):
            point_rows.append(dict(image=path.name,index=i,row=i//11,column=i%11,
                                   X_mm=float(obj[0]),Y_mm=float(obj[1]),Z_mm=0.,
                                   initial_u=float(aa[0]),initial_v=float(aa[1]),refined_u=float(bb[0]),refined_v=float(bb[1]),shift_px=float(dd)))
        for w in [3,5,7]:
            c=refine(g,a,w);ds=displacement(a,c);diff=displacement(b,c)
            sensitivity.append(dict(image=path.name,half_window=w,full_window=2*w+1,
                                    mean_shift_px=float(ds.mean()),max_shift_px=float(ds.max()),
                                    mean_difference_to_w5_px=float(diff.mean()),max_difference_to_w5_px=float(diff.max())))
        for pts in (a,b):
            if not np.isfinite(pts).all() or np.any(pts[:,0,0]<0) or np.any(pts[:,0,0]>=1024) or np.any(pts[:,0,1]<0) or np.any(pts[:,0,1]>=576):
                raise ValueError('Invalid or out-of-bounds observations')
    out=output_dir; (out/'figures').mkdir(parents=True,exist_ok=True)
    manifest=dict(schema_version=1,pattern_size=list(PATTERN),square_size_mm=30.,image_size=[1024,576],
                  point_order='row-major, index=row*11+column; image topmost end is index 0',
                  origin_note='Per-view board frame; unmarked board has 180-degree physical-origin ambiguity',
                  detection_flags=int(FLAGS),subpix_half_window=[5,5],zero_zone=[-1,-1],
                  termination=dict(max_iterations=100,epsilon_px=.001),benchmark=dict(warmups=3,repetitions=repeats,threads=1,io_included=False,summary='median and IQR'),
                  environment=dict(python=sys.version.split()[0],opencv=cv2.__version__,numpy=np.__version__,platform=platform.platform(),machine=platform.machine()),
                  images=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths],summary=summary)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    np.savez_compressed(out/'corners.npz',image_names=np.array([p.name for p in paths]),image_size=np.array([1024,576],np.int32),pattern_size=np.array(PATTERN,np.int32),square_size_mm=np.array(30.),object_points=np.stack([grid.copy() for _ in paths]),image_points_initial=np.stack(initials),image_points_refined=np.stack(refineds))
    for name,rows in [('summary',summary),('points',point_rows),('timings',timing),('window_sensitivity',sensitivity)]:write_csv(out/f'{name}.csv',rows)
    for p,im,b in zip(paths,images,refineds):save_image(out/'figures'/f'{p.stem}_corners.png',make_overlay(im,b))
    figures(out,images,initials,refineds,summary)
    print(json.dumps(manifest,indent=2,ensure_ascii=False))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=BASE/'data')
    parser.add_argument('--output-dir',type=Path,default=BASE/'results'/'corners')
    parser.add_argument('--repeats',type=int,default=30)
    args=parser.parse_args()
    run(args.data_dir.resolve(),args.output_dir.resolve(),args.repeats)


if __name__=='__main__':main()
