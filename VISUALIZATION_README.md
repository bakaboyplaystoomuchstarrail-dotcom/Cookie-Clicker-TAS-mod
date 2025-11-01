# The below README is written by Warp the ADE

# BFS Search Tree Visualization

## Overview
The BFS visualization system has been updated to work exclusively with real BFS data exports. Debug mode has been removed.

## How to Use

### 1. Run BFS Optimizer
Run `main.py` to find an optimal path:
```bash
python main.py
```

The program will **automatically export** the BFS data to the `bfs_data_exports/` folder after finding a solution.

Exported files are named: `bfs_{goal}_cookies_{timestamp}.json`

Example output:
```
✓ Exported BFS data for visualization: C:\...\bfs_data_exports\bfs_20_cookies_20251031_190036.json
```

### 2. Run Visualization
Execute the visualization program:
```bash
python BFSSearchTreeVisualization.py
```

### 3. Select Data File
The program will:
- Scan the `bfs_data_exports` folder
- Display all available JSON files with their sizes
- Prompt you to select which file to visualize

Example output:
```
BFS Search Tree Visualization
==================================================

Found 3 BFS data file(s):

  1) bfs_20_cookies.json (15.3 KB)
  2) bfs_100_cookies.json (142.7 KB)
  3) bfs_optimal_path.json (8.1 KB)

Select file to visualize [1-3]:
```

## Visualization Format

The visualization maintains your preferred layout settings:

### Axes
- **Size**: 11×5.5 units
- **Position**: Shifted RIGHT * 0.5 + UP * 0.2

### Labels
- **Font sizes**: 24 for axis labels, 32 for title
- **X-label buffer**: 0.5 units below axes
- **Y-label buffer**: 0.6 units left of axes
- **Title buffer**: 0.3 units from top

### Legend
- **Position**: Upper-left corner with buff=0.5
- **Shift**: RIGHT * 2.2 + DOWN * 0.5
- **Entry spacing**: 0.15 units between items
- **Font size**: 22

### Y-Axis: Cookies Baked
The y-axis tracks **cumulative cookies baked**, not cookies in bank:
- Lines only increase or stay flat (never decrease)
- **Wait events** (CPS production) shown as diagonal/horizontal lines
- **Click events** shown as vertical lines
- **Purchase events** not drawn (they don't affect baked total)

## Supported Data Formats

### Timeline Paths
```json
{
  "type": "timeline_paths",
  "goal": 20,
  "paths": [
    {
      "name": "Path Name",
      "color": "BLUE_C",
      "events": [
        {"kind": "wait", "t0": 0, "y0": 0, "t1": 20, "y1": 1},
        {"kind": "click", "t": 20, "y0": 0, "y1": 1},
        {"kind": "purchase", "t": 200, "y0": 10, "y1": 10, "item_key": "cursor"}
      ],
      "total_ms": 400
    }
  ]
}
```

### BFS Tree
```json
{
  "type": "bfs_tree",
  "root": "id0",
  "nodes": [
    {"id": "id0", "label": "Start", "depth": 0, "t": 0, "cookies": 0}
  ],
  "edges": [["id0", "id1"]]
}
```

## Quality Settings

The program defaults to low quality (`-pql`) for fast preview rendering.

To change quality, edit line 702 in `BFSSearchTreeVisualization.py`:
- `-pql` - Low quality (fast, default)
- `-pqm` - Medium quality
- `-pqh` - High quality (slow, best for final output)

## Folder Structure
```
Cookie Clicker Projekt/
├── BFSSearchTreeVisualization.py  # Visualization program
├── bfs_data_exports/               # Put your BFS JSON files here
│   ├── example_20.json
│   └── example_100.json
└── media/                          # Generated videos appear here
    └── videos/
        └── BFSSearchTreeVisualization/
```

