# Using Your Own PKL Data with DemoGen

This guide explains how to use your own `.pkl` (pickle) data files with the DemoGen method to generate synthetic demonstrations.

## ⚠️ Security Note

This workflow uses Python's `pickle` module to load demonstration data. **Only use PKL files from trusted sources that you created or verified.** Pickle files can execute arbitrary code when loaded, so never load PKL files from untrusted or unknown sources.

## Overview

DemoGen accepts demonstration data in `.zarr` format, but you can easily convert your own `.pkl` files to the required format. The workflow consists of three main steps:

1. **Prepare your `.pkl` files** with the correct data structure
2. **Convert `.pkl` files to `.zarr` format** using the provided script
3. **Create a configuration file** for your task
4. **Run DemoGen** to generate synthetic demonstrations

## Step 1: Prepare Your PKL Files

### Required Data Format

Each `.pkl` file should contain **one demonstration trajectory** saved as a Python dictionary with the following keys:

```python
{
    'point_cloud': np.ndarray,  # Shape: (T, Np, 6)
    'agent_pos': np.ndarray,    # Shape: (T, Nd)
    'action': np.ndarray,       # Shape: (T, Nd)
    # Optional fields:
    'image': np.ndarray,        # Shape: (T, H, W, 3) - RGB images
    'depth': np.ndarray,        # Shape: (T, H, W) - Depth images
}
```

Where:
- `T`: Trajectory length (number of timesteps)
- `Np`: Number of points in the point cloud (e.g., 1024)
- `Nd`: Dimension of robot state/action (e.g., 7 for Panda + Gripper)
- `6` in point cloud: [x, y, z, r, g, b] coordinates and RGB colors (normalized to 0-1)

### Detailed Field Descriptions

#### 1. `point_cloud` (Required)
- **Shape**: `(T, Np, 6)`
- **Description**: 3D point cloud observations at each timestep
- **Format**: Each point is [x, y, z, r, g, b] where:
  - `x, y, z`: 3D coordinates in meters
  - `r, g, b`: RGB color values normalized to [0, 1]
- **Important**: 
  - Point clouds should be cropped to the workspace (background removed)
  - Apply DBSCAN clustering to remove outliers
  - Use Farthest Point Sampling (FPS) to downsample to a fixed number (e.g., 1024 points)
  - We recommend using RealSense L515 for better quality point clouds

#### 2. `agent_pos` (Required)
- **Shape**: `(T, Nd)`
- **Description**: Robot state at each timestep
- **Common dimensions**:
  - `7`: Panda + Gripper (6D end-effector pose + 1D gripper)
  - `12`: Panda + OYHand (6D end-effector + 6D hand joints)
  - `22`: Panda + Allegro Hand (6D end-effector + 16D hand joints)
  - `14`: Galaxea R1 dual-arm (6D end-effector + 1D gripper per arm)

#### 3. `action` (Required)
- **Shape**: `(T, Nd)`
- **Description**: Actions taken at each timestep
- **Important**: Action dimension must match the robot state dimension

#### 4. `image` and `depth` (Optional)
- These fields are not used by DemoGen but can be saved for reference

### Example: Creating a PKL File

```python
import numpy as np
import pickle

# Example: Create a simple trajectory
T = 100  # 100 timesteps
Np = 1024  # 1024 points per cloud
Nd = 7  # Panda + Gripper

data = {
    'point_cloud': np.random.rand(T, Np, 6).astype(np.float32),  # Random example
    'agent_pos': np.random.rand(T, Nd).astype(np.float32),
    'action': np.random.rand(T, Nd).astype(np.float32),
}

# Save to pickle file
with open('demo_0.pkl', 'wb') as f:
    pickle.dump(data, f)

print("PKL file created successfully!")
```

### File Naming Convention

Name your demonstration files with sequential numbers:
- `demo_0.pkl`, `demo_1.pkl`, `demo_2.pkl`, etc.
- Or: `traj_0.pkl`, `traj_1.pkl`, `traj_2.pkl`, etc.

The conversion script will automatically sort and merge them in numerical order.

## Step 2: Convert PKL to ZARR Format

### Directory Structure

Organize your `.pkl` files in the following structure:

```
data/
└── source_demos/
    └── my_task/          # Your task name
        ├── demo_0.pkl
        ├── demo_1.pkl
        └── demo_2.pkl
```

### Run the Conversion Script

Use the provided `merge_zarr.py` script to convert your `.pkl` files to `.zarr` format:

```bash
cd real_world
python merge_zarr.py my_task
```

This will:
1. Read all `.pkl` files from `data/source_demos/my_task/`
2. Merge them into a single dataset
3. Save the result to `data/datasets/source/my_task.zarr`

The script outputs information about the merged data:
```
point_cloud shape: (300, 1024, 6), range: [0.0, 1.0]
state shape: (300, 7), range: [-1.0, 1.0]
action shape: (300, 7), range: [-1.0, 1.0]
Saved zarr file to data/datasets/source/my_task.zarr
```

### Optional: Save as HDF5

If you also want an HDF5 version:

```bash
python merge_zarr.py my_task --save_h5
```

## Step 3: Create Configuration File

Create a configuration file for your task in `demo_generation/demo_generation/config/`.

### Example: `my_task.yaml`

```yaml
_target_: demo_generation.demogen.DemoGen

data_root: data
source_name: my_task  # Must match your zarr file name

task_n_object: 1  # Number of objects manipulated in the task

use_linear_interpolation: false
interpolate_step_size: 0.01

# Option 1: Manual parsing (recommended)
use_manual_parsing_frames: true
parsing_frames:
  motion-1: 0      # Start frame for approaching the object
  skill-1: 10      # Start frame for manipulating the object
  # For tasks with multiple objects, add:
  # motion-2: 50
  # skill-2: 60

# Option 2: Automatic parsing (requires tuning)
# use_manual_parsing_frames: false

# Mask names for object segmentation (using language prompts)
mask_names:
  object: cup           # Description of the object to manipulate
  target: table         # Description of the target location (if applicable)
  # For single object tasks without a target, you can omit 'target'

# Translation ranges for data augmentation
trans_range:
  src:  # Source demos (no transformation)
    object: [[0, 0, 0], [0, 0, 0]]
    target: [[0, 0, 0], [0, 0, 0]]
  test:  # Generated demos (with spatial augmentation)
    object: [[-0.10, -0.10, 0], [0.10, 0.10, 0]]  # x, y, z range in meters
    target: [[-0.10, -0.10, 0], [0.10, 0.10, 0]]

generation:
  range_name: test  # Use 'test' for augmented data, 'src' to test without augmentation
  n_gen_per_source: 16  # Number of synthetic demos to generate per source demo
  render_video: True    # Set to False to skip video rendering (faster)
  mode: grid            # 'grid' for uniform grid, 'random' for random positions
```

### Configuration Details

#### Task Parameters

- `source_name`: Must match your `.zarr` file name (without extension)
- `task_n_object`: Number of objects manipulated (1 for single object, 2 for two objects, etc.)

#### Trajectory Parsing

DemoGen requires parsing the trajectory into segments:
- **Motion segment**: Robot approaches the object (typically smooth, continuous motion toward the object)
- **Skill segment**: Robot manipulates the object through contact (e.g., grasping, pushing, placing)

**How to identify the transition point:**
1. **Visual inspection**: Watch the robot movement - the transition occurs when the robot makes contact with the object
2. **Distance-based**: The transition is typically when the distance between end-effector and object becomes very small (< 2-5cm)
3. **Gripper state**: For grasping tasks, the transition often coincides with gripper state change (opening → closing)
4. **Velocity change**: Motion segments usually have higher velocity than skill segments which involve careful manipulation

**Option 1: Manual Parsing (Recommended)**
1. Set `use_manual_parsing_frames: true`
2. Run generation with `range_name: src` and `render_video: True`
3. Watch the generated video and note the frame numbers where:
   - Motion starts (usually frame 0)
   - Contact begins / gripper closes / object starts moving (skill starts)
   - The frame number is displayed in the top-left corner of the video
4. Update `parsing_frames` accordingly

**Example for a pick-and-place task:**
- Frame 0-15: Robot moves toward object (motion-1)
- Frame 16-30: Robot grasps object (skill-1)
- Frame 31-50: Robot moves toward target (motion-2)
- Frame 51-65: Robot places object (skill-2)

**Option 2: Automatic Parsing**
- Set `use_manual_parsing_frames: false`
- The system will try to detect contact based on distance thresholds
- May require tuning for your specific task
- Less reliable than manual specification

#### Object Segmentation

The `mask_names` section uses natural language descriptions for object segmentation:
- DemoGen uses models like Grounded-SAM or LangSAM
- Provide clear, descriptive names (e.g., "red mug", "wooden box")
- For single-object tasks without a target location, you can simplify this

#### Spatial Augmentation

The `trans_range` defines how objects are repositioned in synthetic demos:
- `src`: Use all zeros for no transformation (useful for testing)
- `test`: Define the range for random/grid sampling
  - Format: `[[x_min, y_min, z_min], [x_max, y_max, z_max]]`
  - Units are in meters
  - Example: `[[-0.10, -0.10, 0], [0.10, 0.10, 0]]` means ±10cm in x and y

#### Generation Settings

- `n_gen_per_source`: 
  - For `mode: grid`, must be a perfect square (e.g., 4, 9, 16, 25)
  - For `mode: random`, can be any number
- `render_video`: Set to `False` to speed up generation (no videos created)
- `mode`:
  - `grid`: Uniform grid sampling (more systematic)
  - `random`: Random sampling (more diverse)

## Step 4: Run DemoGen

### Generate Synthetic Demonstrations

```bash
cd demo_generation
python gen_demo.py --config-name=my_task
```

### Output

Generated data will be saved to:
- **Dataset**: `data/datasets/generated/my_task_test_*.zarr`
- **Videos** (if enabled): `data/videos/my_task_test_*.mp4`

The video filenames indicate the transformations applied, making it easy to verify the results.

## Step 5: Verify Your Data

### Check the Generated Data

1. **Inspect the zarr files**:
```python
import zarr
z = zarr.open('data/datasets/generated/my_task_test_0.zarr', 'r')
print(z.tree())
print(f"Point cloud shape: {z['data/point_cloud'].shape}")
print(f"Agent pos shape: {z['data/agent_pos'].shape}")
print(f"Action shape: {z['data/action'].shape}")
```

2. **Watch the videos** (if generated):
   - Check if the objects are positioned correctly
   - Verify that the robot motion looks reasonable
   - Ensure the point clouds are clean (no artifacts)

### Troubleshooting

#### Issue: "ValueError: n_demos must be a squared number"
- **Cause**: Using `mode: grid` with `n_gen_per_source` that's not a perfect square
- **Solution**: Change `n_gen_per_source` to 4, 9, 16, 25, etc., or use `mode: random`

#### Issue: Poor object segmentation
- **Cause**: Mask names are too generic or ambiguous
- **Solution**: Use more specific descriptions in `mask_names` (e.g., "blue cylindrical mug" instead of "mug")

#### Issue: Generated trajectories look unnatural
- **Cause**: Incorrect trajectory parsing
- **Solution**: 
  1. Render source video with `range_name: src`
  2. Manually check frame numbers for motion/skill transitions
  3. Update `parsing_frames` in config

#### Issue: "KeyError" when loading zarr
- **Cause**: Missing required fields in pkl files
- **Solution**: Ensure your pkl files contain `point_cloud`, `agent_pos`, and `action`

#### Issue: Point clouds look noisy
- **Cause**: Insufficient preprocessing
- **Solution**: 
  1. Apply DBSCAN clustering to remove outliers
  2. Crop to workspace boundaries
  3. Use Farthest Point Sampling (FPS)

## Advanced: Multiple Demonstrations

For better results, collect 2-3 source demonstrations with slight variations:

1. **Collect multiple demos**:
   ```
   data/source_demos/my_task/
   ├── demo_0.pkl
   ├── demo_1.pkl
   └── demo_2.pkl
   ```

2. **Merge them**:
   ```bash
   python merge_zarr.py my_task
   ```

3. **Generate from each**:
   DemoGen will automatically generate synthetic demos from each source demo.

## Next Steps

After generating synthetic demonstrations, you can:

1. **Train visuomotor policies** using the generated data
   - See `docs/3_train_policies.md` for instructions
   - DemoGen-generated data works with DP3 and other policies

2. **Combine with real data**
   - Merge generated and real demonstrations for better performance
   - Use `real_world/merge_zarr.py` to combine datasets

3. **Iterate and improve**
   - Experiment with different `trans_range` values
   - Adjust `n_gen_per_source` based on your needs
   - Try both `grid` and `random` modes

## Summary

The complete workflow:

```bash
# 1. Organize your pkl files
mkdir -p data/source_demos/my_task
# (Place your demo_0.pkl, demo_1.pkl, etc. here)

# 2. Convert to zarr
cd real_world
python merge_zarr.py my_task
cd ..

# 3. Create config file
# (Create demo_generation/demo_generation/config/my_task.yaml)

# 4. Generate synthetic demos
cd demo_generation
python gen_demo.py --config-name=my_task
cd ..

# 5. Check results
ls data/datasets/generated/
ls data/videos/
```

## References

- For data collection from real robots: `docs/1_data_collection.md`
- For detailed generation process: `docs/2_data_generation.md`
- For training policies: `docs/3_train_policies.md`

## Questions?

If you encounter issues not covered in this guide, please check:
1. The example config files in `demo_generation/demo_generation/config/`
2. The example datasets in `data/datasets/source/`
3. Open an issue on GitHub with details about your setup and error messages
