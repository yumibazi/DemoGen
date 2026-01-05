#!/usr/bin/env python3
"""
Example script showing how to create a simple PKL file for testing DemoGen.

This creates a minimal valid PKL file with random data for demonstration purposes.
For real usage, replace the random data with actual robot demonstrations.

Usage:
    python create_example_pkl.py
    
This will create:
    - data/source_demos/example_task/demo_0.pkl
"""

import os
import numpy as np
import pickle
from pathlib import Path

def create_example_pkl():
    """Create an example PKL file with the correct format."""
    
    # Parameters
    T = 100          # Trajectory length (100 timesteps)
    Np = 1024        # Number of points in point cloud
    Nd = 7           # Robot dimension (Panda + Gripper: 6D pose + 1D gripper)
    
    print("Creating example PKL file...")
    print(f"Parameters: T={T}, Np={Np}, Nd={Nd}")
    
    # Create dummy data
    # In a real scenario, these would be actual observations and actions
    
    # Point cloud: random points in a workspace with RGB colors
    # Shape: (T, Np, 6) where 6 = [x, y, z, r, g, b]
    point_cloud = np.zeros((T, Np, 6), dtype=np.float32)
    # XYZ: random positions in a 0.5m x 0.5m x 0.3m workspace
    point_cloud[:, :, 0] = np.random.uniform(0.0, 0.5, (T, Np))  # x
    point_cloud[:, :, 1] = np.random.uniform(-0.25, 0.25, (T, Np))  # y
    point_cloud[:, :, 2] = np.random.uniform(0.0, 0.3, (T, Np))  # z
    # RGB: random colors normalized to [0, 1]
    point_cloud[:, :, 3:] = np.random.uniform(0.0, 1.0, (T, Np, 3))
    
    # Agent position: smoothly varying robot state
    # Shape: (T, Nd) where Nd=7 for Panda + Gripper
    agent_pos = np.zeros((T, Nd), dtype=np.float32)
    # Create a smooth trajectory using sine waves
    t = np.linspace(0, 2*np.pi, T)
    agent_pos[:, 0] = 0.5 + 0.1 * np.sin(t)      # x position
    agent_pos[:, 1] = 0.0 + 0.1 * np.cos(t)      # y position
    agent_pos[:, 2] = 0.3 + 0.05 * np.sin(2*t)   # z position
    agent_pos[:, 3] = 3.14                        # roll (constant)
    agent_pos[:, 4] = 0.0                         # pitch
    agent_pos[:, 5] = 0.0                         # yaw
    # Gripper: starts open (1.0), closes halfway through (0.0)
    agent_pos[:, 6] = np.where(t < np.pi, 1.0, 0.0)
    
    # Action: similar to agent_pos but represents deltas or target positions
    # For this example, we'll use the same as agent_pos (position control)
    action = agent_pos.copy()
    
    # Optional: add some noise to make it more realistic
    action += np.random.normal(0, 0.01, action.shape).astype(np.float32)
    
    # Create the data dictionary
    data = {
        'point_cloud': point_cloud,
        'agent_pos': agent_pos,
        'action': action,
        # Optional fields (not required but can be included):
        # 'image': np.random.randint(0, 255, (T, 480, 640, 3), dtype=np.uint8),
        # 'depth': np.random.uniform(0, 2, (T, 480, 640), dtype=np.float32),
    }
    
    # Create output directory
    output_dir = Path("data/source_demos/example_task")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to pickle file
    output_path = output_dir / "demo_0.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"\n✓ Created example PKL file: {output_path}")
    print("\nData shapes:")
    print(f"  - point_cloud: {data['point_cloud'].shape}")
    print(f"  - agent_pos: {data['agent_pos'].shape}")
    print(f"  - action: {data['action'].shape}")
    
    print("\nNext steps:")
    print("  1. Validate the file:")
    print(f"     python scripts/validate_pkl.py {output_path}")
    print("  2. Convert to zarr format:")
    print("     cd real_world && python merge_zarr.py example_task && cd ..")
    print("  3. Create a config file:")
    print("     cp demo_generation/demo_generation/config/template.yaml \\")
    print("        demo_generation/demo_generation/config/example_task.yaml")
    print("     # Edit the config file as needed")
    print("  4. Generate synthetic demos:")
    print("     cd demo_generation && python gen_demo.py --config-name=example_task")
    
    return output_path


if __name__ == "__main__":
    create_example_pkl()
