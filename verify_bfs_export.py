"""
Python-based verification simulator for BFS exported paths.
Simulates the game millisecond-by-millisecond to verify BFS predictions.
"""

import json
from pathlib import Path
from main import CookieClickerOptimizer, GameState

def verify_bfs_export(export_path: str, verbose: bool = True):
    """
    Verify a BFS export by simulating it in Python.
    
    Args:
        export_path: Path to the exported JSON file
        verbose: If True, print detailed step-by-step output
    
    Returns:
        Dict with verification results
    """
    # Load the export
    with open(export_path, 'r') as f:
        data = json.load(f)
    
    if data['type'] != 'timeline_paths':
        raise ValueError(f"Unsupported export type: {data['type']}")
    
    path_data = data['paths'][0]
    events = path_data['events']
    goal = data['goal']
    expected_time = path_data['total_ms']
    
    if verbose:
        print("="*70)
        print(f"VERIFYING BFS EXPORT: {Path(export_path).name}")
        print("="*70)
        print(f"Goal: {goal} cookies")
        print(f"Expected time: {expected_time}ms")
        print(f"Events to process: {len(events)}")
        print()
    
    # Initialize optimizer and state
    optimizer = CookieClickerOptimizer()
    state = GameState(
        cookies=0,
        cookies_baked=0,
        buildings={},
        cps=0.0,
        time_ms=0,
        last_click_time_ms=-20,
        last_production_frame=-1,
        click_power=1.0,
        deferred_options=set()
    )
    
    # Extract purchase events
    purchases = [ev for ev in events if ev['kind'] == 'purchase']
    purchase_times = {ev['t']: ev for ev in purchases}
    
    # Simulate millisecond by millisecond
    discrepancies = []
    current_time = 0
    
    # Process all purchases in chronological order
    for purchase in purchases:
        t = purchase['t']
        building_name = purchase['item_key']
        expected_cost = purchase['cost']
        
        # Advance time from current_time to purchase time
        if t > current_time:
            state = optimizer.advance_time(state, current_time, t)
            current_time = t
        
        # Calculate actual cost
        current_count = state.buildings.get(building_name, 0)
        actual_cost = optimizer.get_building_cost(building_name, current_count)
        
        if verbose:
            print(f"\nt={t}ms: PURCHASE EVENT")
            print(f"  Building: {building_name}")
            print(f"  Expected cost: {expected_cost}")
            print(f"  Actual cost: {actual_cost}")
            print(f"  Cookies before: {state.cookies:.2f}")
            print(f"  Baked before: {state.cookies_baked:.2f}")
            print(f"  Can afford: {state.cookies >= actual_cost}")
        
        # Check affordability
        if state.cookies < actual_cost:
            discrepancy = {
                'time': t,
                'type': 'affordability',
                'message': f"Cannot afford {building_name} at t={t}ms",
                'expected_cost': expected_cost,
                'actual_cost': actual_cost,
                'cookies_available': state.cookies
            }
            discrepancies.append(discrepancy)
            if verbose:
                print(f"  ❌ ERROR: Cannot afford purchase!")
                print(f"     Need {actual_cost}, have {state.cookies:.2f}")
        else:
            # Make the purchase
            state = optimizer.purchase_building(state, building_name)
            if verbose:
                print(f"  ✓ Purchase successful")
                print(f"  Cookies after: {state.cookies:.2f}")
                print(f"  Baked after: {state.cookies_baked:.2f}")
                print(f"  Buildings: {dict(state.buildings)}")
                print(f"  CPS: {state.cps}")
    
    # Advance to final time
    if current_time < expected_time:
        state = optimizer.advance_time(state, current_time, expected_time)
    
    # Final verification
    final_baked = state.cookies_baked
    goal_met = final_baked >= goal
    
    if verbose:
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"Time: {state.time_ms}ms (expected: {expected_time}ms)")
        print(f"Cookies baked: {final_baked:.2f} (goal: {goal})")
        print(f"Cookies in bank: {state.cookies:.2f}")
        print(f"Buildings: {dict(state.buildings)}")
        print(f"CPS: {state.cps}")
        print()
        
        if goal_met and len(discrepancies) == 0:
            print("✓✓✓ VERIFICATION PASSED ✓✓✓")
        else:
            print("❌❌❌ VERIFICATION FAILED ❌❌❌")
            if not goal_met:
                print(f"  Goal not met: {final_baked:.2f} < {goal}")
            if discrepancies:
                print(f"  Discrepancies found: {len(discrepancies)}")
                for disc in discrepancies:
                    print(f"    - {disc['message']}")
        print("="*70)
    
    return {
        'passed': goal_met and len(discrepancies) == 0,
        'final_time': state.time_ms,
        'final_baked': final_baked,
        'goal': goal,
        'discrepancies': discrepancies,
        'final_buildings': dict(state.buildings)
    }

def verify_latest_export(verbose: bool = True):
    """Verify the most recent BFS export."""
    export_folder = Path(__file__).parent / 'bfs_data_exports'
    if not export_folder.exists():
        print("No exports folder found")
        return None
    
    exports = sorted(export_folder.glob('*.json'), key=lambda p: p.stat().st_mtime)
    if not exports:
        print("No exports found")
        return None
    
    latest = exports[-1]
    return verify_bfs_export(str(latest), verbose=verbose)

if __name__ == '__main__':
    # Verify the latest export
    result = verify_latest_export(verbose=True)
