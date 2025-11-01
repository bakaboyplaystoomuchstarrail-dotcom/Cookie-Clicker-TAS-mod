# Cookie Clicker BFS Optimizer - Complete Workflow

## Quick Start

### Step 1: Find Optimal Path
```bash
python main.py
```

Enter your target cookie count when prompted. The program will:
1. Run BFS to find the optimal path
2. **Automatically export visualization data** to `bfs_data_exports/`
3. Generate and open an HTML verification page

Example:
```
Cookie Clicker Optimizer (Millisecond-precise)
==================================================
Enter your target cookie count: 20

Starting BFS with goal: 20.0 cookies (no time limit)
Found optimal solution at time 380ms!

✓ Exported BFS data for visualization: C:\...\bfs_20_cookies_20251031_190036.json
```

### Step 2: Visualize the Path
```bash
python BFSSearchTreeVisualization.py
```

The program will:
1. Scan `bfs_data_exports/` for available data files
2. Display a numbered list of files
3. Prompt you to select which one to visualize
4. Generate an animated Manim video showing the optimal path

Example:
```
BFS Search Tree Visualization
==================================================

Found 1 BFS data file(s):

  1) bfs_20_cookies_20251031_190036.json (2.5 KB)

Select file to visualize [1-1]: 1

Selected: bfs_20_cookies_20251031_190036.json
Launching Manim visualization...
```

## What You'll See

### The Visualization Shows:
- **Title**: "BFS Optimal Path to {goal} Cookies"
- **X-axis**: Time in milliseconds
- **Y-axis**: Cumulative cookies baked
- **Graph**: A single optimal path showing:
  - Vertical jumps for click events
  - Diagonal slopes for CPS production (after buying buildings)
  - No drops (purchases don't decrease baked count)

### Legend
- Shows "Optimal Path ({time}ms)"
- Positioned in upper-left, clear of axes

### Animation
- Axes and labels fade in first
- Legend appears
- Path draws progressively (click by click)
- Total animation time: ~10-15 seconds

## File Organization

```
Cookie Clicker Projekt/
├── main.py                         # BFS optimizer (run first)
├── BFSSearchTreeVisualization.py   # Visualization tool (run second)
├── bfs_data_exports/               # Auto-generated BFS data
│   ├── bfs_20_cookies_20251031_190036.json
│   ├── bfs_50_cookies_20251031_190512.json
│   └── bfs_100_cookies_20251031_191023.json
└── media/videos/                   # Generated visualization videos
    └── BFSSearchTreeVisualization/
        └── 480p15/
            └── BFSSearchTreeVisualization.mp4
```

## Export Format

Each BFS run creates a JSON file with this structure:

```json
{
  "type": "timeline_paths",
  "title": "BFS Optimal Path to 20 Cookies",
  "goal": 20.0,
  "paths": [{
    "name": "Optimal Path (380ms)",
    "color": "BLUE_C",
    "events": [
      {"kind": "click", "t": 0, "y0": 0.0, "y1": 1.0},
      {"kind": "click", "t": 20, "y0": 1.0, "y1": 2.0},
      {"kind": "purchase", "t": 200, "y0": 10.0, "y1": 10.0, "item_key": "cursor"},
      {"kind": "wait", "t0": 200, "y0": 10.0, "t1": 300, "y1": 10.1}
    ],
    "total_ms": 380
  }]
}
```

### Event Types:
- **click**: Instant cookie gain (vertical line)
- **wait**: CPS production over time (diagonal line)
- **purchase**: Building purchase (no visual - doesn't affect baked count)

## Tips

### For Faster Visualization
Edit line 702 of `BFSSearchTreeVisualization.py`:
- Change `-pql` to `-pqm` or `-pqh` for better quality (slower)
- Default `-pql` is fast preview quality

### Managing Exports
- Files are timestamped, so you can run multiple optimizations
- Delete old exports to keep the folder clean
- File sizes are typically 1-10 KB for reasonable goals

### Troubleshooting

**No BFS data files found?**
- Make sure you ran `main.py` first
- Check that `bfs_data_exports/` folder exists
- Verify the BFS found a solution (didn't fail or timeout)

**Visualization looks wrong?**
- Check that the JSON file is not corrupted
- Verify events have correct `y0` and `y1` values
- Remember: y-axis is **cumulative baked**, not banked cookies

**LaTeX warnings?**
- These are harmless MiKTeX update notices
- Doesn't affect the visualization output
- Can be ignored

## Advanced Usage

### Custom Visualization Data
You can manually create or edit JSON files in `bfs_data_exports/` following the format above.

### Multiple Paths
To compare different strategies, create a JSON with multiple paths:
```json
{
  "type": "timeline_paths",
  "goal": 20,
  "paths": [
    {"name": "Strategy A", "color": "BLUE_C", "events": [...], "total_ms": 400},
    {"name": "Strategy B", "color": "RED_C", "events": [...], "total_ms": 450}
  ]
}
```

## Summary

1. **`python main.py`** → Find optimal path → Auto-export to `bfs_data_exports/`
2. **`python BFSSearchTreeVisualization.py`** → Select file → Watch animation
3. Video saved to `media/videos/BFSSearchTreeVisualization/480p15/`

That's it! The workflow is now fully automated.
