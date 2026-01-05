# 使用自己的 PKL 数据运行 DemoGen

本指南说明如何使用您自己的 `.pkl` (pickle) 数据文件与 DemoGen 方法生成合成演示数据。

## 快速开始

DemoGen 接受 `.zarr` 格式的演示数据，但您可以轻松将自己的 `.pkl` 文件转换为所需格式。完整工作流程包括四个主要步骤：

### 1. 准备 PKL 文件

每个 `.pkl` 文件应包含**一个演示轨迹**，保存为 Python 字典：

```python
{
    'point_cloud': np.ndarray,  # 形状: (T, Np, 6) - [x, y, z, r, g, b]
    'agent_pos': np.ndarray,    # 形状: (T, Nd) - 机器人状态
    'action': np.ndarray,       # 形状: (T, Nd) - 机器人动作
}
```

其中：
- `T`：轨迹长度（时间步数）
- `Np`：点云中的点数（例如 1024）
- `Nd`：机器人状态/动作维度（例如 Panda + 夹爪为 7）

**重要说明：**
- 点云的 RGB 值应归一化到 [0, 1]
- 应裁剪到工作空间（去除背景）
- 推荐使用 RealSense L515 获得更好的点云质量
- `agent_pos` 和 `action` 的维度必须匹配

### 2. 组织文件结构

将您的 `.pkl` 文件按以下结构组织：

```
data/
└── source_demos/
    └── my_task/          # 您的任务名称
        ├── demo_0.pkl
        ├── demo_1.pkl
        └── demo_2.pkl
```

### 3. 转换为 ZARR 格式

使用提供的脚本转换您的 `.pkl` 文件：

```bash
cd real_world
python merge_zarr.py my_task
cd ..
```

这将创建 `data/datasets/source/my_task.zarr`

### 4. 创建配置文件

复制并编辑模板配置文件：

```bash
cp demo_generation/demo_generation/config/template.yaml \
   demo_generation/demo_generation/config/my_task.yaml
```

编辑 `my_task.yaml` 文件，主要修改以下参数：

```yaml
source_name: my_task  # 必须与您的 zarr 文件名匹配

task_n_object: 1  # 任务中操作的物体数量

parsing_frames:
  motion-1: 0      # 机器人开始接近物体的帧
  skill-1: 10      # 机器人开始操作物体的帧

mask_names:
  object: 红色杯子        # 要操作的物体描述
  target: 木制桌子        # 目标位置描述

trans_range:
  test:
    object: [[-0.10, -0.10, 0], [0.10, 0.10, 0]]  # x,y 方向 ±10cm
    target: [[-0.10, -0.10, 0], [0.10, 0.10, 0]]
```

### 5. 生成合成演示数据

```bash
cd demo_generation
python gen_demo.py --config-name=my_task
cd ..
```

生成的数据将保存到：
- **数据集**: `data/datasets/generated/my_task_test_*.zarr`
- **视频** (如果启用): `data/videos/my_task_test_*.mp4`

## 辅助工具

我们提供了两个辅助脚本来帮助您：

### 1. 验证 PKL 文件格式

```bash
# 验证单个文件
python scripts/validate_pkl.py path/to/demo_0.pkl

# 验证目录中的所有文件
python scripts/validate_pkl.py data/source_demos/my_task/
```

### 2. 创建示例 PKL 文件

```bash
python scripts/create_example_pkl.py
```

这将创建一个示例文件用于测试工作流程。

## 完整工作流程示例

```bash
# 1. 创建示例 PKL 文件（或使用您自己的）
python scripts/create_example_pkl.py

# 2. 验证您的 PKL 文件
python scripts/validate_pkl.py data/source_demos/example_task/

# 3. 转换为 zarr 格式
cd real_world
python merge_zarr.py example_task
cd ..

# 4. 复制并自定义配置文件
cp demo_generation/demo_generation/config/template.yaml \
   demo_generation/demo_generation/config/example_task.yaml
# 根据需要编辑 example_task.yaml

# 5. 生成合成演示数据
cd demo_generation
python gen_demo.py --config-name=example_task
cd ..

# 6. 检查结果
ls data/datasets/generated/
ls data/videos/
```

## 常见问题

### 问题：如何确定 parsing_frames 的值？

**解决方案：**
1. 在配置文件中设置 `range_name: src` 和 `render_video: True`
2. 运行生成脚本查看源演示视频
3. 观看视频并记录以下帧号：
   - 机器人开始移动向物体的帧（通常为 0）
   - 机器人开始接触并操作物体的帧
4. 更新配置文件中的 `parsing_frames`

### 问题：点云分割效果不好

**解决方案：**
- 在 `mask_names` 中使用更具体的描述
- 例如："蓝色圆柱形杯子" 而不是 "杯子"

### 问题：生成的轨迹看起来不自然

**解决方案：**
- 检查轨迹解析是否正确
- 渲染源视频并手动检查帧号
- 确保 motion 和 skill 段落的分界准确

### 问题：验证时出现 KeyError

**解决方案：**
- 确保 pkl 文件包含 `point_cloud`、`agent_pos` 和 `action`
- 使用验证脚本检查文件格式

## 高级技巧

1. **多个演示数据**：收集 2-3 个略有变化的源演示可以获得更好的结果
2. **空间增强范围**：根据您的工作空间大小调整 `trans_range`
3. **视频渲染**：
   - 初始测试时启用以验证结果
   - 生成大型数据集时禁用以加快速度（约快 10 倍）
4. **生成模式**：
   - `grid`：均匀网格采样（更系统化）
   - `random`：随机采样（更多样化）

## 更多信息

完整的英文指南请参阅：[docs/4_use_custom_pkl_data.md](./4_use_custom_pkl_data.md)

其他文档：
- [安装指南](./0_install.md)
- [数据收集](./1_data_collection.md)
- [数据生成](./2_data_generation.md)
- [训练策略](./3_train_policies.md)

如有问题，请在 GitHub 上提交 issue。
