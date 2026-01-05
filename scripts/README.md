# Helper Scripts for DemoGen

This directory contains utility scripts to help you work with custom data in DemoGen.

## Scripts

### 1. `validate_pkl.py` - PKL File Validator

Validates that your `.pkl` files have the correct format for DemoGen.

**Usage:**
```bash
# Validate a single file
python scripts/validate_pkl.py path/to/demo_0.pkl

# Validate all files in a directory
python scripts/validate_pkl.py data/source_demos/my_task/
```

**Features:**
- Checks for required fields (`point_cloud`, `agent_pos`, `action`)
- Validates array shapes and dimensions
- Verifies trajectory length consistency
- Checks data type compatibility
- Provides detailed error messages and warnings

**Example output:**
```
✓ point_cloud: shape (100, 1024, 6) (T=100, Np=1024)
✓ agent_pos: shape (100, 7) (T=100, Nd=7)
  - Detected: Panda + Gripper (6D end-effector + 1D gripper)
✓ action: shape (100, 7) (T=100, Nd=7)
✓ Trajectory length consistent: T=100
✓ agent_pos and action dimensions match: Nd=7

✓ File is valid!
```

### 2. `create_example_pkl.py` - Example PKL Generator

Creates a simple example PKL file with dummy data for testing purposes.

**Usage:**
```bash
python scripts/create_example_pkl.py
```

**Output:**
Creates `data/source_demos/example_task/demo_0.pkl` with:
- 100 timesteps
- 1024 point cloud points
- 7D robot state (Panda + Gripper)
- Smooth trajectory with sine wave motion

**Note:** The generated data is random and for demonstration only. Replace it with real robot demonstrations for actual use.

## Workflow Example

Here's a complete workflow using these scripts:

```bash
# Step 1: Create an example PKL file (or use your own)
python scripts/create_example_pkl.py

# Step 2: Validate your PKL file
python scripts/validate_pkl.py data/source_demos/example_task/

# Step 3: Convert to zarr format
cd real_world
python merge_zarr.py example_task
cd ..

# Step 4: Copy and customize the template config
cp demo_generation/demo_generation/config/template.yaml \
   demo_generation/demo_generation/config/example_task.yaml
# Edit example_task.yaml as needed

# Step 5: Generate synthetic demos
cd demo_generation
python gen_demo.py --config-name=example_task
cd ..

# Step 6: Check the results
ls data/datasets/generated/
ls data/videos/
```

## Tips

- **Always validate** your PKL files before converting to zarr format
- **Start small**: Test with a single demo file first
- **Use the template**: Copy `config/template.yaml` for new tasks
- **Enable video rendering** initially to verify the generation process
- **Disable video rendering** when generating large datasets (much faster)

## Troubleshooting

If validation fails, check:
1. **File format**: Ensure it's a Python dictionary, not a list or other type
2. **Required keys**: Must have `point_cloud`, `agent_pos`, and `action`
3. **Array shapes**: 
   - `point_cloud`: (T, Np, 6)
   - `agent_pos`: (T, Nd)
   - `action`: (T, Nd)
4. **Trajectory length**: T must be the same across all fields
5. **Robot dimension**: Nd must match between `agent_pos` and `action`
6. **RGB normalization**: RGB values should be in [0, 1]

For more detailed guidance, see [docs/4_use_custom_pkl_data.md](../docs/4_use_custom_pkl_data.md).
