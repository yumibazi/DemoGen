#!/usr/bin/env python3
"""
Validation script for checking if a PKL file has the correct format for DemoGen.

Usage:
    python validate_pkl.py path/to/your/demo.pkl
    python validate_pkl.py path/to/directory/  # Validates all .pkl files in directory
"""

import os
import sys
import pickle
import numpy as np
from pathlib import Path

# Try to import termcolor, fallback to regular print if not available
try:
    from termcolor import cprint
except ImportError:
    def cprint(text, color=None):
        """Fallback function when termcolor is not available."""
        print(text)


def validate_pkl_file(pkl_path):
    """Validate a single PKL file.
    
    Security Note: This function uses pickle.load() which can execute arbitrary code.
    Only use this tool with PKL files from trusted sources that you created or verified.
    """
    try:
        with open(pkl_path, 'rb') as f:
            # WARNING: pickle.load() can execute arbitrary code
            # Only load PKL files from trusted sources
            data = pickle.load(f)
    except Exception as e:
        cprint(f"❌ Error loading {pkl_path}: {e}", "red")
        return False
    
    if not isinstance(data, dict):
        cprint(f"❌ {pkl_path}: Data must be a dictionary, got {type(data)}", "red")
        return False
    
    # Check required keys
    required_keys = ['point_cloud', 'agent_pos', 'action']
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        cprint(f"❌ {pkl_path}: Missing required keys: {missing_keys}", "red")
        cprint(f"   Found keys: {list(data.keys())}", "yellow")
        return False
    
    # Validate shapes
    valid = True
    
    # Check point_cloud
    pcd = data['point_cloud']
    if not isinstance(pcd, np.ndarray):
        cprint(f"❌ {pkl_path}: 'point_cloud' must be a numpy array", "red")
        valid = False
    elif len(pcd.shape) != 3:
        cprint(f"❌ {pkl_path}: 'point_cloud' must have shape (T, Np, 6), got {pcd.shape}", "red")
        valid = False
    elif pcd.shape[2] != 6:
        cprint(f"❌ {pkl_path}: 'point_cloud' last dimension must be 6 [x,y,z,r,g,b], got {pcd.shape[2]}", "red")
        valid = False
    else:
        T_pcd, Np, _ = pcd.shape
        cprint(f"✓ point_cloud: shape {pcd.shape} (T={T_pcd}, Np={Np})", "green")
        
        # Check value ranges
        xyz = pcd[:, :, :3]
        rgb = pcd[:, :, 3:]
        cprint(f"  - XYZ range: [{xyz.min():.3f}, {xyz.max():.3f}]", "cyan")
        cprint(f"  - RGB range: [{rgb.min():.3f}, {rgb.max():.3f}]", "cyan")
        
        if rgb.min() < 0 or rgb.max() > 1:
            cprint(f"  ⚠ Warning: RGB values should be normalized to [0, 1]", "yellow")
    
    # Check agent_pos
    agent_pos = data['agent_pos']
    if not isinstance(agent_pos, np.ndarray):
        cprint(f"❌ {pkl_path}: 'agent_pos' must be a numpy array", "red")
        valid = False
    elif len(agent_pos.shape) != 2:
        cprint(f"❌ {pkl_path}: 'agent_pos' must have shape (T, Nd), got {agent_pos.shape}", "red")
        valid = False
    else:
        T_agent, Nd = agent_pos.shape
        cprint(f"✓ agent_pos: shape {agent_pos.shape} (T={T_agent}, Nd={Nd})", "green")
        cprint(f"  - Value range: [{agent_pos.min():.3f}, {agent_pos.max():.3f}]", "cyan")
        
        # Common robot configurations
        common_dims = {
            7: "Panda + Gripper (6D end-effector + 1D gripper)",
            12: "Panda + OYHand (6D end-effector + 6D hand joints)",
            14: "Galaxea R1 dual-arm (6D + 1D per arm)",
            22: "Panda + Allegro Hand (6D end-effector + 16D hand joints)"
        }
        if Nd in common_dims:
            cprint(f"  - Detected: {common_dims[Nd]}", "cyan")
    
    # Check action
    action = data['action']
    if not isinstance(action, np.ndarray):
        cprint(f"❌ {pkl_path}: 'action' must be a numpy array", "red")
        valid = False
    elif len(action.shape) != 2:
        cprint(f"❌ {pkl_path}: 'action' must have shape (T, Nd), got {action.shape}", "red")
        valid = False
    else:
        T_action, Nd_action = action.shape
        cprint(f"✓ action: shape {action.shape} (T={T_action}, Nd={Nd_action})", "green")
        cprint(f"  - Value range: [{action.min():.3f}, {action.max():.3f}]", "cyan")
    
    # Check trajectory length consistency
    if valid:
        T_values = []
        if isinstance(pcd, np.ndarray) and len(pcd.shape) == 3:
            T_values.append(('point_cloud', pcd.shape[0]))
        if isinstance(agent_pos, np.ndarray) and len(agent_pos.shape) == 2:
            T_values.append(('agent_pos', agent_pos.shape[0]))
        if isinstance(action, np.ndarray) and len(action.shape) == 2:
            T_values.append(('action', action.shape[0]))
        
        unique_T = set(t for _, t in T_values)
        if len(unique_T) > 1:
            cprint(f"❌ {pkl_path}: Trajectory lengths don't match:", "red")
            for key, t in T_values:
                cprint(f"   - {key}: {t}", "red")
            valid = False
        else:
            T = T_values[0][1] if T_values else 0
            cprint(f"✓ Trajectory length consistent: T={T}", "green")
    
    # Check action and agent_pos dimensions match
    if valid and isinstance(agent_pos, np.ndarray) and isinstance(action, np.ndarray):
        if len(agent_pos.shape) == 2 and len(action.shape) == 2:
            if agent_pos.shape[1] != action.shape[1]:
                cprint(f"❌ {pkl_path}: agent_pos and action dimensions don't match:", "red")
                cprint(f"   - agent_pos: {agent_pos.shape[1]}", "red")
                cprint(f"   - action: {action.shape[1]}", "red")
                valid = False
            else:
                cprint(f"✓ agent_pos and action dimensions match: Nd={agent_pos.shape[1]}", "green")
    
    # Check optional fields
    optional_keys = ['image', 'depth']
    for key in optional_keys:
        if key in data:
            cprint(f"✓ Optional field '{key}' present: shape {data[key].shape}", "green")
    
    # Check data types
    for key in ['point_cloud', 'agent_pos', 'action']:
        if key in data and isinstance(data[key], np.ndarray):
            dtype = data[key].dtype
            if dtype not in [np.float32, np.float64]:
                cprint(f"⚠ Warning: {key} has dtype {dtype}, recommend float32 or float64", "yellow")
    
    return valid


def validate_directory(dir_path):
    """Validate all PKL files in a directory."""
    pkl_files = list(Path(dir_path).glob("*.pkl"))
    
    if not pkl_files:
        cprint(f"❌ No .pkl files found in {dir_path}", "red")
        return False
    
    cprint(f"\nFound {len(pkl_files)} PKL file(s) in {dir_path}", "blue")
    cprint("=" * 80, "blue")
    
    results = {}
    for pkl_file in sorted(pkl_files):
        cprint(f"\nValidating: {pkl_file.name}", "blue")
        cprint("-" * 80, "blue")
        results[pkl_file.name] = validate_pkl_file(pkl_file)
    
    cprint("\n" + "=" * 80, "blue")
    cprint("SUMMARY", "blue")
    cprint("=" * 80, "blue")
    
    valid_count = sum(results.values())
    total_count = len(results)
    
    for filename, is_valid in sorted(results.items()):
        status = "✓ VALID" if is_valid else "❌ INVALID"
        color = "green" if is_valid else "red"
        cprint(f"{status}: {filename}", color)
    
    cprint(f"\n{valid_count}/{total_count} files are valid", 
           "green" if valid_count == total_count else "yellow")
    
    return valid_count == total_count


def print_usage():
    """Print usage instructions."""
    cprint("\n" + "=" * 80, "cyan")
    cprint("DemoGen PKL File Validator", "cyan")
    cprint("=" * 80, "cyan")
    print("\n⚠️  SECURITY WARNING:")
    print("  This tool uses pickle.load() which can execute arbitrary code.")
    print("  Only use with PKL files from trusted sources that you created or verified.")
    print("\nUsage:")
    print("  python validate_pkl.py <path>")
    print("\nExamples:")
    print("  python validate_pkl.py demo_0.pkl                    # Validate single file")
    print("  python validate_pkl.py data/source_demos/my_task/    # Validate directory")
    print("\nRequired PKL format:")
    print("  - Dictionary with keys: 'point_cloud', 'agent_pos', 'action'")
    print("  - point_cloud: shape (T, Np, 6) - [x, y, z, r, g, b]")
    print("  - agent_pos: shape (T, Nd) - robot state")
    print("  - action: shape (T, Nd) - robot actions")
    print("  - T (trajectory length) must be consistent across all fields")
    print("  - Nd (robot dimension) must match between agent_pos and action")
    cprint("=" * 80 + "\n", "cyan")


def main():
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    
    path = sys.argv[1]
    
    if not os.path.exists(path):
        cprint(f"❌ Path does not exist: {path}", "red")
        sys.exit(1)
    
    if os.path.isfile(path):
        if not path.endswith('.pkl'):
            cprint(f"❌ File must have .pkl extension: {path}", "red")
            sys.exit(1)
        
        cprint(f"\nValidating: {path}", "blue")
        cprint("=" * 80, "blue")
        valid = validate_pkl_file(path)
        cprint("=" * 80, "blue")
        
        if valid:
            cprint("\n✓ File is valid!", "green")
            sys.exit(0)
        else:
            cprint("\n❌ File validation failed!", "red")
            sys.exit(1)
    
    elif os.path.isdir(path):
        valid = validate_directory(path)
        sys.exit(0 if valid else 1)
    
    else:
        cprint(f"❌ Invalid path: {path}", "red")
        sys.exit(1)


if __name__ == "__main__":
    main()
