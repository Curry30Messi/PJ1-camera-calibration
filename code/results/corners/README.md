# 角点实验与交接数据

负责人：卢远卓。输入为左相机4张原始图，11×7个内角点，方格30mm，保持1024×576分辨率。

## 复现

在仓库根目录使用 Python 3.12：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/detect_corners.py
python -m unittest discover -s code -p 'test_*.py' -v
```

默认输出为本目录。`--data-dir`、`--output-dir`可指定其他路径，`--repeats`控制计时重复数（默认30，至少5）。脚本从自身位置解析默认路径，可从任意工作目录运行。计时会随硬件和系统负载变化；角点数值应在同版本软件下保持一致。

## 数据接口

`corners.npz`为后续标定的主要输入，无pickle对象，使用`allow_pickle=False`加载：

```python
import numpy as np
with np.load('code/results/corners/corners.npz', allow_pickle=False) as z:
    object_points = [p.copy() for p in z['object_points']]
    image_points = [p.copy() for p in z['image_points_refined']]
    image_size = tuple(int(v) for v in z['image_size'])  # (width, height)
```

| 字段 | 形状／类型 | 含义 |
|---|---|---|
| image_names | (4,) Unicode | 固定顺序L1、L2、L3、L4 |
| image_size | (2,) int32 | [1024, 576]，先宽后高 |
| pattern_size | (2,) int32 | [11, 7]，内角点列数、行数 |
| square_size_mm | scalar float | 30.0 |
| object_points | (4, 77, 3) float32 | 毫米单位棋盘坐标 |
| image_points_initial | (4, 77, 1, 2) float32 | 初始检测坐标 |
| image_points_refined | (4, 77, 1, 2) float32 | 正式交付的细化后像素坐标 |

点号i=r×11+c；棋盘坐标为(30c,30r,0)，范围X=0…300mm，Y=0…180mm。这是内角点网格的尺寸，不是整块标定板的外形尺寸。图像坐标u向右、v向下，像素索引从0开始。各视图的首尾点以图像端点(v,u)字典序规范化；无标记棋盘存在180度物理原点歧义，允许各视图采用自己的棋盘坐标系，不应直接用于要求共同物理原点的双目标定。

## 结果文件

- `manifest.json`：参数、输入SHA-256、环境、计时方案及逐图汇总。
- `summary.csv`：4行检测、位移、计时指标。
- `points.csv`：308行，完整三维点、初始和细化后的二维点及位移。
- `timings.csv`：120行原始计时数据；每张图预热3次，正式重复30次。
- `window_sensitivity.csv`：12行，半窗口3、5、7的对照结果，包含相对正式5半窗口结果的差异。
- `figures/`：4张带编号的角点图、原始图汇总、位移与计时图、局部细化对照图。

初始点来自经典`findChessboardCorners`，不是人为取整的整数点。正式细化使用`cornerSubPix`、半窗口(5,5)、无死区、最多100次迭代或位移阈值0.001px。3和7半窗口仅作敏感性对照。检测与细化均在单线程下计时，细化每次从初始点副本启动，图像读取和可视化不计入。

4张图均成功检测77个角点，总计308个。细化位移衡量两次估计的变化，不是真实定位误差；由于没有人工高精度真值，本节不声称精度提升百分比。窗口变化反映估计敏感性，不提供最优窗口的真值证据。下一位成员应使用正式细化数据运行标定，保留原始数据用于后续对照。

## 验证

自动验证涵盖棋盘坐标毫米间距和顺序、合成棋盘的已知几何交点、空白图失败分支、细化不修改初始数组，以及真实数据NPZ与308行CSV的一致性。Word第1章包含本节实验设置、所有逐图汇总、12组窗口实验结果、关键代码和结果分析。
