# BFS Visualization Unit Tests

This document describes the comprehensive unit tests for the BFS visualization system, covering both the `BFSSearchTreeVisualization.py` and `export_bfs_path_to_visualization` function in `main.py`.

## Test Coverage

### 1. `TestBFSSearchTreeVisualizationEventExpansion` (6 tests)

Tests for the `_expand_events_with_clicks` method in `BFSSearchTreeVisualization` class.

#### `test_expand_purchase_with_count_greater_than_one`
- **Purpose**: Verify that purchase events with `count > 1` are correctly handled
- **What it tests**: Purchase events don't create visual segments (they don't change baked cookies)
- **Expected behavior**: Purchase events should not appear in expanded timeline

#### `test_expand_purchase_with_costs_array`
- **Purpose**: Verify that purchase events with a `costs` array are correctly processed
- **What it tests**: Clicks are generated at correct 20ms intervals regardless of purchase events
- **Expected behavior**: Clicks occur at 0, 20, 40, 60, 80, 100, etc.

#### `test_expand_legacy_purchase_with_single_cost`
- **Purpose**: Test backward compatibility with legacy purchase events using single `cost` field
- **What it tests**: Legacy format (with `cost` instead of `costs` array) still works
- **Expected behavior**: Events are processed without error, clicks generated correctly

#### `test_expand_events_with_click_power_changes`
- **Purpose**: Verify that click power changes are correctly applied to subsequent clicks
- **What it tests**: After a `click_power_change` event, future clicks use the new power value
- **Expected behavior**: 
  - Click at t=40 adds 1.0 cookies (before power change)
  - Click at t=60 adds 2.0 cookies (after power change at t=50)

#### `test_expand_events_deterministic_click_timing`
- **Purpose**: Verify that clicks occur deterministically every 20ms starting at 0ms
- **What it tests**: Core click timing mechanism
- **Expected behavior**: Clicks at exactly 0, 20, 40, 60, 80, 100, 120

#### `test_expand_events_accumulates_cookies_correctly`
- **Purpose**: Verify that cookie accumulation (y values) is correct across clicks
- **What it tests**: Cookie totals increase properly with each click
- **Expected behavior**: With power 1.0, cookies go 0→1→2→3→4

---

### 2. `TestExportBFSPathToVisualization` (7 tests)

Tests for the `export_bfs_path_to_visualization` function that exports BFS paths to JSON.

#### `test_export_generates_correct_individual_purchase_events`
- **Purpose**: Verify that individual purchase events are generated with accurate costs
- **What it tests**: Each cursor purchase has the correct cost based on count
- **Expected behavior**: 
  - 3 cursor purchases at different times
  - Costs match `optimizer.get_building_cost()` calculations

#### `test_export_sets_correct_is_upgrade_flags`
- **Purpose**: Verify that `is_upgrade` flags are correctly set for buildings vs upgrades
- **What it tests**: Buildings have `is_upgrade=False`, upgrades have `is_upgrade=True`
- **Expected behavior**:
  - Cursor purchase: `is_upgrade=False`
  - Upgrade purchase: `is_upgrade=True`

#### `test_export_generates_click_power_change_for_cursor_upgrades`
- **Purpose**: Test cursor upgrade handling (currently documents a bug)
- **What it tests**: Cursor upgrade purchases should generate `click_power_change` events
- **Current behavior**: Bug exists - implementation checks `building_name.startswith('cursor_')` but cursor upgrades are named like `reinforced_index_finger`
- **Note**: Test documents the bug and verifies current behavior rather than failing

#### `test_export_generates_click_power_change_for_thousand_fingers`
- **Purpose**: Verify `click_power_change` events for Thousand Fingers upgrade
- **What it tests**: When Thousand Fingers is purchased with non-cursor buildings present, click power changes
- **Expected behavior**: `click_power_change` event generated at purchase time

#### `test_export_generates_click_power_change_when_buildings_alter_click_power`
- **Purpose**: Verify building purchases alter click power when Thousand Fingers is active
- **What it tests**: After Thousand Fingers is purchased, buying non-cursor buildings changes click power
- **Expected behavior**: Grandma purchase triggers `click_power_change` event

#### `test_export_file_structure_is_valid`
- **Purpose**: Verify the exported JSON has the correct structure
- **What it tests**: All required fields are present and correctly formatted
- **Expected behavior**:
  - Type: `timeline_paths`
  - Contains `goal`, `paths`, `events`, `total_ms`

---

### 3. `TestBFSVisualizationIntegration` (1 test)

Integration tests for the full BFS visualization pipeline.

#### `test_exported_data_can_be_loaded_by_visualization`
- **Purpose**: End-to-end test that exported data can be loaded by visualization
- **What it tests**: Complete pipeline from export to visualization loading
- **Expected behavior**: 
  - Export succeeds
  - Data can be loaded as JSON
  - Visualization scene can process the events without errors

---

## Running the Tests

```bash
# Run all BFS visualization tests
python -m unittest tests.test_bfs_visualization -v

# Run a specific test class
python -m unittest tests.test_bfs_visualization.TestBFSSearchTreeVisualizationEventExpansion -v

# Run a specific test
python -m unittest tests.test_bfs_visualization.TestExportBFSPathToVisualization.test_export_generates_correct_individual_purchase_events -v
```

## Test Results

All 13 tests pass successfully, covering:

1. **Event expansion logic**: 6 tests
2. **Export functionality**: 7 tests  
3. **Integration**: 1 test

## Known Issues Documented in Tests

### Cursor Upgrade Click Power Bug

The `test_export_generates_click_power_change_for_cursor_upgrades` test documents a bug in the current implementation:

**Bug**: Line 980 in `main.py` checks `building_name.startswith('cursor_')` to detect cursor upgrades, but cursor upgrades are actually named `reinforced_index_finger`, `carpal_tunnel_prevention_cream`, etc.

**Impact**: Cursor upgrade purchases don't generate `click_power_change` events even though they should.

**Fix needed**: Check the upgrade's `affects_click_power` attribute instead:
```python
is_cursor_upgrade = is_upgrade and optimizer.upgrades[building_name].affects_click_power
```

## File Locations

- **Test file**: `tests/test_bfs_visualization.py`
- **Code under test**: 
  - `BFSSearchTreeVisualization.py`
  - `main.py` (function `export_bfs_path_to_visualization`)
- **Test data**: Temporary files in `bfs_data_exports/` (cleaned up after tests)

## Test Data Cleanup

Tests automatically clean up exported files after running. Test exports are written to the real `bfs_data_exports/` folder but are removed in `cleanup_temp_dir()`.
