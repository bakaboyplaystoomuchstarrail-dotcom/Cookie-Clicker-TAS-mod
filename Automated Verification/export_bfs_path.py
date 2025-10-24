"""
Export BFS optimal path to JSON format for automated TAS playback
"""
import json
from main import CookieClickerOptimizer

def export_path_to_json(goal_cookies, output_file='bfs_path.json'):
    """Run BFS optimizer and export path to JSON file"""
    print(f"Running BFS optimizer for {goal_cookies} cookies...")
    optimizer = CookieClickerOptimizer()
    result = optimizer.bfs_optimize(goal_cookies)
    
    if result is None:
        print("No solution found!")
        return None
    
    path, total_time_ms = result
    
    # Convert path to JSON-serializable format
    json_path = []
    for action in path:
        action_type, action_value, action_time_ms = action
        json_path.append([action_type, action_value, action_time_ms])
    
    # Create output data
    output_data = {
        'goal_cookies': goal_cookies,
        'total_time_ms': total_time_ms,
        'total_actions': len(path),
        'path': json_path
    }
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nPath exported to {output_file}")
    print(f"Total time: {total_time_ms}ms ({total_time_ms/1000:.3f} seconds)")
    print(f"Total actions: {len(path)}")
    
    # Also print the path array for easy copy-paste
    print("\n" + "="*60)
    print("Copy the following JSON array to load into TAS Controller:")
    print("="*60)
    print(json.dumps(json_path))
    print("="*60)
    
    return output_data

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        goal = float(sys.argv[1])
    else:
        goal = float(input("Enter target cookie count (default 100): ") or "100")
    
    export_path_to_json(goal)
