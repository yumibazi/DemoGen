# Quick Reference: Using Custom PKL Data

## One-Page Quick Start

### Prerequisites
```bash
# Install DemoGen (see docs/0_install.md for full setup)
conda create -n demogen python=3.8
conda activate demogen
pip install imageio imageio-ffmpeg termcolor hydra-core==1.2.0 zarr==2.12.0 matplotlib setuptools==59.5.0 pynput h5py scikit-video tqdm
cd diffusion_policies && pip install -e . && cd ..
cd demo_generation && pip install -e . && cd ..
```

### PKL File Format
```python
# Each .pkl file = 1 demonstration trajectory
{
    'point_cloud': np.array((T, Np, 6)),  # [x,y,z,r,g,b], RGB in [0,1]
    'agent_pos': np.array((T, Nd)),       # Robot state
    'action': np.array((T, Nd))           # Robot actions
}
# T: trajectory length, Np: num points (e.g., 1024), Nd: robot dim (e.g., 7)
```

### Complete Workflow

```bash
# 1. Prepare your data
mkdir -p data/source_demos/my_task
# Place your demo_0.pkl, demo_1.pkl, etc. in the directory

# 2. Validate (optional but recommended)
python scripts/validate_pkl.py data/source_demos/my_task/

# 3. Convert to zarr
cd real_world
python merge_zarr.py my_task
cd ..

# 4. Create config
cp demo_generation/demo_generation/config/template.yaml \
   demo_generation/demo_generation/config/my_task.yaml
# Edit my_task.yaml (see minimal config below)

# 5. Generate
cd demo_generation
python gen_demo.py --config-name=my_task
cd ..
```

### Minimal Config Template

```yaml
_target_: demo_generation.demogen.DemoGen
data_root: data
source_name: my_task                    # Match your zarr filename
task_n_object: 1                        # Number of objects

use_manual_parsing_frames: true
parsing_frames:
  motion-1: 0                           # Start frame for approaching
  skill-1: 10                           # Start frame for manipulation

mask_names:
  object: red cup                       # Object description
  target: table                         # Target description

trans_range:
  test:
    object: [[-0.10, -0.10, 0], [0.10, 0.10, 0]]  # ±10cm range
    target: [[-0.10, -0.10, 0], [0.10, 0.10, 0]]

generation:
  range_name: test
  n_gen_per_source: 16                  # Must be perfect square for grid mode
  render_video: true                    # Set false for faster generation
  mode: grid                            # 'grid' or 'random'
```

### Finding parsing_frames

```bash
# 1. First, set in config: range_name: src, render_video: true
# 2. Run generation to see source video
cd demo_generation
python gen_demo.py --config-name=my_task
cd ..
# 3. Watch video in data/videos/, note frame numbers from top-left corner
# 4. Update parsing_frames in config with the correct values
```

### Common Robot Dimensions (Nd)
- 7: Panda + Gripper (6D pose + 1D gripper)
- 12: Panda + OYHand (6D + 6D hand)
- 14: Galaxea R1 dual-arm (2 × 7D)
- 22: Panda + Allegro Hand (6D + 16D hand)

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "ValueError: n_demos must be a squared number" | Use n_gen_per_source = 4, 9, 16, 25, 36... or mode: random |
| Poor object segmentation | Use more specific mask_names descriptions |
| Unnatural trajectories | Check parsing_frames by rendering source video |
| KeyError when loading | Ensure pkl has point_cloud, agent_pos, action |
| RGB values warning | Normalize RGB to [0, 1] range |

### Output Locations
- Generated datasets: `data/datasets/generated/my_task_test_*.zarr`
- Videos (if enabled): `data/videos/my_task_test_*.mp4`

### Tips
✓ Start with 1 demo file for testing  
✓ Validate before converting to zarr  
✓ Use render_video: true initially  
✓ Set render_video: false for large batches  
✓ Use n_gen_per_source: 4 or 9 for quick tests  
✓ Collect 2-3 source demos for better results  

### Getting Help
- Full guide: [docs/4_use_custom_pkl_data.md](../docs/4_use_custom_pkl_data.md)
- Chinese guide: [docs/4_use_custom_pkl_data_zh.md](../docs/4_use_custom_pkl_data_zh.md)
- Scripts README: [scripts/README.md](../scripts/README.md)
- Example configs: `demo_generation/demo_generation/config/`
