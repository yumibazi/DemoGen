# DemoGen Custom PKL Data Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEMOGEN CUSTOM PKL DATA WORKFLOW                     │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: PREPARE YOUR DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━
  Your PKL Files (demo_0.pkl, demo_1.pkl, ...)
  │
  │  Each file contains:
  │  ┌─────────────────────────────────────────┐
  │  │ {                                       │
  │  │   'point_cloud': (T, Np, 6)  [x,y,z,r,g,b] │
  │  │   'agent_pos': (T, Nd)       robot state   │
  │  │   'action': (T, Nd)          robot actions │
  │  │ }                                       │
  │  └─────────────────────────────────────────┘
  │
  ▼
  Place in: data/source_demos/my_task/


STEP 2: VALIDATE (OPTIONAL BUT RECOMMENDED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  $ python scripts/validate_pkl.py data/source_demos/my_task/
  │
  │  Checks:
  │  ✓ Required keys present
  │  ✓ Correct array shapes
  │  ✓ Consistent trajectory lengths
  │  ✓ Matching dimensions
  │  ✓ RGB normalization
  │
  ▼
  [VALID] ✓ All checks passed!


STEP 3: CONVERT TO ZARR FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  $ cd real_world
  $ python merge_zarr.py my_task
  │
  │  Process:
  │  • Reads all .pkl files
  │  • Sorts by number
  │  • Concatenates trajectories
  │  • Compresses with Blosc
  │
  ▼
  Output: data/datasets/source/my_task.zarr
  ┌─────────────────────────────────────┐
  │ my_task.zarr/                       │
  │ ├── data/                           │
  │ │   ├── point_cloud/                │
  │ │   ├── agent_pos/                  │
  │ │   └── action/                     │
  │ └── meta/                           │
  │     └── episode_ends/               │
  └─────────────────────────────────────┘


STEP 4: CREATE CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  $ cp demo_generation/demo_generation/config/template.yaml \
       demo_generation/demo_generation/config/my_task.yaml
  │
  │  Edit my_task.yaml:
  │  ┌─────────────────────────────────────────┐
  │  │ source_name: my_task                    │
  │  │ task_n_object: 1                        │
  │  │ parsing_frames:                         │
  │  │   motion-1: 0                           │
  │  │   skill-1: 10                           │
  │  │ mask_names:                             │
  │  │   object: red cup                       │
  │  │   target: table                         │
  │  │ trans_range: ...                        │
  │  │ generation:                             │
  │  │   n_gen_per_source: 16                  │
  │  │   mode: grid                            │
  │  └─────────────────────────────────────────┘
  │
  ▼
  Config ready: demo_generation/demo_generation/config/my_task.yaml


STEP 5: GENERATE SYNTHETIC DEMOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  $ cd demo_generation
  $ python gen_demo.py --config-name=my_task
  │
  │  DemoGen Process:
  │  1. Load source demos from zarr
  │  2. Parse trajectory into segments
  │  3. Segment point clouds (objects/robot)
  │  4. Generate transformation vectors
  │  5. Transform point clouds (3D editing)
  │  6. Adapt actions (TAMP-inspired)
  │  7. Render videos (optional)
  │
  ▼
  Outputs:
  ┌─────────────────────────────────────────┐
  │ Generated Datasets:                     │
  │ data/datasets/generated/                │
  │ ├── my_task_test_0.zarr                 │
  │ ├── my_task_test_1.zarr                 │
  │ └── ...                                 │
  │                                         │
  │ Rendered Videos (if enabled):           │
  │ data/videos/                            │
  │ ├── my_task_test_0.mp4                  │
  │ ├── my_task_test_1.mp4                  │
  │ └── ...                                 │
  └─────────────────────────────────────────┘


STEP 6: VERIFY RESULTS
━━━━━━━━━━━━━━━━━━━━━
  1. Check generated zarr files
  2. Watch rendered videos
  3. Verify object positions
  4. Ensure robot motion is smooth
  │
  ▼
  [SUCCESS] Ready to train policies!


═══════════════════════════════════════════════════════════════════════════

HELPER TOOLS AVAILABLE:
━━━━━━━━━━━━━━━━━━━━━━━

📋 scripts/validate_pkl.py       Validate PKL file format
🔧 scripts/create_example_pkl.py Create example PKL for testing
📖 docs/4_use_custom_pkl_data.md Comprehensive guide (English)
📖 docs/4_use_custom_pkl_data_zh.md Complete guide (Chinese)
📄 docs/QUICK_REFERENCE.md       One-page quick reference
⚙️  demo_generation/demo_generation/config/template.yaml  Config template

═══════════════════════════════════════════════════════════════════════════

COMMON TROUBLESHOOTING:
━━━━━━━━━━━━━━━━━━━━━━━

Issue: ValueError about squared number
Fix:   Use n_gen_per_source = 4, 9, 16, 25... or mode: random

Issue: Poor object segmentation
Fix:   Use more specific mask_names (e.g., "blue cylindrical mug")

Issue: Unnatural trajectories
Fix:   Check parsing_frames by rendering source video first

Issue: KeyError when loading
Fix:   Ensure pkl has point_cloud, agent_pos, action keys

Issue: RGB values warning
Fix:   Normalize RGB to [0, 1] range

═══════════════════════════════════════════════════════════════════════════

NEXT STEPS AFTER GENERATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Train visuomotor policies with generated data (see docs/3_train_policies.md)
2. Test on real robot
3. Iterate and improve:
   • Adjust trans_range for better coverage
   • Experiment with grid vs random mode
   • Collect more source demos if needed

═══════════════════════════════════════════════════════════════════════════
```

## Key Concepts

### PKL Format
The pickle files must be Python dictionaries with specific numpy arrays for point clouds, robot states, and actions.

### Zarr Format
Zarr is a chunked, compressed array storage format used by DemoGen for efficient loading of demonstration data.

### Trajectory Parsing
DemoGen needs to know where the robot transitions from approaching the object to manipulating it. This is done through `parsing_frames`.

### Point Cloud Segmentation
To transform objects in the scene, DemoGen segments the point cloud into objects and robot parts using natural language descriptions.

### Spatial Augmentation
The `trans_range` parameter defines how much objects should be moved in the x, y, z directions to create diverse demonstrations.

### TAMP-inspired Action Adaptation
DemoGen adapts the robot actions according to the new object positions using Task and Motion Planning principles.

## Time Estimates

- **Validation**: ~1 second per file
- **Zarr Conversion**: ~5-10 seconds for typical datasets
- **Generation (no video)**: ~2-5 seconds per trajectory
- **Generation (with video)**: ~10-15 seconds per trajectory
- **Total for 16 demos**: ~30 seconds (no video) or ~3 minutes (with video)

## Resources

For detailed information, see:
- **Full Documentation**: `docs/4_use_custom_pkl_data.md`
- **Chinese Guide**: `docs/4_use_custom_pkl_data_zh.md`
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Scripts README**: `scripts/README.md`
