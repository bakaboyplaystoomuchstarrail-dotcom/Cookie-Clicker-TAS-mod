from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

@dataclass
class Building:
    name: str
    id: int
    base_cost: float
    base_cps: float  # cookies per frame
    cost_multiplier: float = 1.15

@dataclass
class GameState:
    cookies: float  # current cookies in bank
    cookies_baked: float  # cumulative cookies produced (the actual goal!)
    buildings: dict  # building_name -> count
    cps: float  # current cookies per frame
    time_ms: int  # current time in milliseconds (not frames)
    last_click_time_ms: int  # time of last click in milliseconds
    last_production_frame: int  # last frame where production was applied
    click_power: float  # current click value
    
    def copy(self):
        return GameState(
            cookies=self.cookies,
            cookies_baked=self.cookies_baked,
            buildings=self.buildings.copy(),
            cps=self.cps,
            time_ms=self.time_ms,
            last_click_time_ms=self.last_click_time_ms,
            last_production_frame=self.last_production_frame,
            click_power=self.click_power
        )

class CookieClickerOptimizer:
    def __init__(self):
        # Define buildings with their base stats from Cookie Clicker source code
        # Note: CPS values are already per-frame due to TAS mod
        # Building costs follow: basePrice = (n+9+(n<5?0:pow(n-5,1.75)*5))*pow(10,n)*(max(1,n-14))
        self.buildings = {
            'cursor': Building('cursor', 0, 15, 0.1),
            'grandma': Building('grandma', 1, 100, 1),
            'farm': Building('farm', 2, 1100, 8),
            'mine': Building('mine', 3, 12000, 47),
            'factory': Building('factory', 4, 130000, 260),
            'bank': Building('bank', 5, 1400000, 1400),
            'temple': Building('temple', 6, 20000000, 7800),
            'wizard_tower': Building('wizard_tower', 7, 330000000, 44000),
            'shipment': Building('shipment', 8, 5100000000, 260000),
            'alchemy_lab': Building('alchemy_lab', 9, 75000000000, 1600000),
        }
        # Price increase multiplier from source: Game.priceIncrease (usually 1.15)
        self.price_increase = 1.15
    
    def get_building_cost(self, building_name: str, current_count: int) -> float:
        """Calculate cost of next building using Cookie Clicker formula"""
        building = self.buildings[building_name]
        # From source: price = basePrice * pow(Game.priceIncrease, max(0, amount-free))
        # We assume no free buildings, so it's basePrice * pow(1.15, amount)
        return math.ceil(building.base_cost * (self.price_increase ** current_count))
    
    def get_possible_purchases(self, state: GameState) -> List[str]:
        """Get list of buildings that can be purchased with current cookies.
        Sorted by cost (ascending) for early termination optimization."""
        possible = []
        # Build list with costs for sorting
        building_costs = []
        for building_name in self.buildings:
            current_count = state.buildings.get(building_name, 0)
            cost = self.get_building_cost(building_name, current_count)
            building_costs.append((cost, building_name))
        
        # Sort by cost ascending
        building_costs.sort()
        
        # Add affordable buildings until we hit an unaffordable one (early termination)
        for cost, building_name in building_costs:
            if state.cookies >= cost:
                possible.append(building_name)
            else:
                # All remaining buildings are unaffordable (cost is ascending)
                break
        
        return possible
    
    def purchase_building(self, state: GameState, building_name: str) -> GameState:
        """Create new state after purchasing a building (takes 1ms, CpS updated immediately)"""
        new_state = state.copy()
        current_count = new_state.buildings.get(building_name, 0)
        cost = self.get_building_cost(building_name, current_count)
        
        # Make the purchase (spending doesn't reduce baked cookies!)
        new_state.cookies -= cost
        new_state.buildings[building_name] = current_count + 1
        
        # Update CpS immediately (but production benefit starts next frame)
        building = self.buildings[building_name]
        new_state.cps += building.base_cps
        
        # Advance time by 1ms for the purchase action
        new_state.time_ms += 1
        
        # Update click power based on finger upgrades (simplified)
        if building_name == 'cursor':
            new_state.click_power = self.calculate_click_power(new_state)
        
        return new_state
    
    def click_cookie(self, state: GameState) -> GameState:
        """Create new state after clicking the big cookie (only if 20ms+ since last click)"""
        new_state = state.copy()
        
        # Check click throttling: need at least 20ms since last click
        if new_state.time_ms - new_state.last_click_time_ms < 20:
            # Click is throttled, don't process it
            return None
        
        # Use the calculated click power from the state
        click_power = state.click_power
        
        # Add click cookies
        new_state.cookies += click_power
        new_state.cookies_baked += click_power
        
        # Update last click time
        new_state.last_click_time_ms = new_state.time_ms
        
        # Advance time by 1ms for this click action
        new_state.time_ms += 1
        return new_state
    
    def calculate_click_power(self, state: GameState) -> float:
        """Calculate click power based on Cookie Clicker mouseCps formula"""
        # Base click power is 1 cookie per click
        base_power = 1.0
        
        # Cursors don't boost click power unless you have specific upgrades
        # Without the "Thousand fingers" upgrade (which costs much more than 100 cookies),
        # cursors only provide passive CPS, not click power bonuses
        
        # For now, click power is always 1 since we don't have upgrades
        click_power = base_power
        
        return click_power
    
    def wait_one_ms(self, state: GameState) -> GameState:
        """
        Create new state after waiting exactly 1 millisecond.
        Apply production if we cross a frame boundary.
        """
        new_state = state.copy()
        new_state.time_ms += 1
        
        # Calculate current frame (1000ms / 30fps = 33.333... ms per frame)
        current_frame = int(new_state.time_ms * 30 / 1000)
        
        # If we're in a new frame and have CpS, apply production
        if current_frame > new_state.last_production_frame and new_state.cps > 0:
            new_state.cookies += new_state.cps
            new_state.cookies_baked += new_state.cps
            new_state.last_production_frame = current_frame
        
        return new_state
    
    def bfs_optimize(self, goal_cookies: float, max_time_ms: int = 15000) -> Optional[Tuple[List[Tuple[str, int, int]], int]]:
        """
        True BFS with exhaustive action exploration:
        - Clicks (if not throttled: 20ms since last click)
        - Purchases (1ms action, no throttle)
        - Waits (1ms increments, always available)
        Uses millisecond-precise timing and state pruning to manage branching.
        """
        initial_state = GameState(
            cookies=0,
            cookies_baked=0,  # Track cumulative production
            buildings={},
            cps=0.0,  # Current cookies per frame
            time_ms=0,
            last_click_time_ms=-20,  # Start at -20 so first click at t=0 is valid
            last_production_frame=-1,  # Start at -1 so first frame (0) can produce
            click_power=1.0
        )
        
        # States organized by time in milliseconds: {time_ms: [(state, path), ...]}
        states_by_time = {0: [(initial_state, [])]}
        visited = set()
        
        print(f"Starting BFS with goal: {goal_cookies} cookies (max {max_time_ms}ms)")
        
        # Use a sorted list of times to process them in order (skip empty times)
        max_iterations = 100000
        iterations = 0
        
        while iterations < max_iterations and states_by_time:
            iterations += 1
            
            # Get the earliest time with states
            time_ms = min(states_by_time.keys())
            
            if time_ms > max_time_ms:
                break
            
            current_states = states_by_time.pop(time_ms)
            
            if iterations % 100 == 0:
                print(f"Iteration {iterations}: Time {time_ms}ms, {len(current_states)} states")
            
            # Limit states at each time point to prevent explosion (keep best performers)
            # Sort by cookies_baked (descending) to keep most promising states
            current_states.sort(key=lambda x: x[0].cookies_baked, reverse=True)
            max_states_per_time = 50  # Aggressive pruning
            current_states = current_states[:max_states_per_time]
            
            # Process states at this time level before moving to next time
            for idx, (state, path) in enumerate(current_states):
                # Check if goal reached (based on cookies baked, not banked)
                if state.cookies_baked >= goal_cookies:
                    print(f"Found optimal solution at time {time_ms}ms!")
                    return path, time_ms
                
                # Create state signature - include time_ms because the same state at different times can have different next actions
                # (e.g., time 1 vs time 20 both have 1 cookie from last click at 0, but at time 20 we can click again)
                state_sig = (
                    state.time_ms,
                    round(state.cookies * 100) / 100,
                    round(state.cookies_baked * 100) / 100,
                    tuple(sorted(state.buildings.items())),
                    state.last_click_time_ms,  # Include last click time in signature
                    state.last_production_frame  # Include last production frame
                )
                
                if state_sig in visited:
                    continue
                visited.add(state_sig)
                
                # Generate ALL possible successor states
                
                # Try all possible purchases (takes 1ms)
                possible_purchases = self.get_possible_purchases(state)
                for building_name in possible_purchases:
                    purchase_state = self.purchase_building(state, building_name)
                    purchase_path = path + [('buy', building_name, time_ms)]
                    
                    next_time = purchase_state.time_ms
                    
                    if next_time <= max_time_ms:
                        if next_time not in states_by_time:
                            states_by_time[next_time] = []
                        states_by_time[next_time].append((purchase_state, purchase_path))
                
                # Try clicking (if not throttled, takes 1ms)
                click_state = self.click_cookie(state)
                if click_state is not None:  # click_cookie returns None if throttled
                    click_path = path + [('click', 1, time_ms)]
                    
                    next_time = click_state.time_ms
                    
                    if next_time <= max_time_ms:
                        if next_time not in states_by_time:
                            states_by_time[next_time] = []
                        states_by_time[next_time].append((click_state, click_path))
                
                # Try waiting 1ms (always an option)
                if state.time_ms + 1 <= max_time_ms:
                    wait_state = self.wait_one_ms(state)
                    wait_path = path + [('wait', 1, time_ms)]
                    
                    next_time = wait_state.time_ms
                    
                    if next_time not in states_by_time:
                        states_by_time[next_time] = []
                    states_by_time[next_time].append((wait_state, wait_path))
        
        print(f"No solution found within {max_time_ms}ms after {iterations} iterations")
        return None

def compress_path(path):
    """Compress consecutive identical actions for cleaner output (using millisecond timestamps)"""
    if not path:
        return []
    
    compressed = []
    current_group = None
    
    for action in path:
        action_type = action[0]
        
        if action_type == 'click':
            # Group consecutive clicks
            if current_group and current_group['type'] == 'click':
                # Extend current click group
                current_group['count'] += 1
                current_group['end_time_ms'] = action[2]
            else:
                # Start new click group
                if current_group:
                    compressed.append(current_group)
                current_group = {
                    'type': 'click',
                    'count': 1,
                    'start_time_ms': action[2],
                    'end_time_ms': action[2]
                }
        
        elif action_type == 'buy':
            # Purchases don't get grouped, add individually
            if current_group:
                compressed.append(current_group)
                current_group = None
            
            compressed.append({
                'type': 'buy',
                'count': 1,
                'building': action[1],
                'time_ms': action[2]
            })
        
        elif action_type == 'wait':
            # Waits don't get grouped (shouldn't happen in current implementation)
            if current_group:
                compressed.append(current_group)
                current_group = None
            
            compressed.append({
                'type': 'wait',
                'count': 1,
                'time_ms': action[1],
                'end_time_ms': action[2]
            })
    
    # Don't forget the last group
    if current_group:
        compressed.append(current_group)
    
    return compressed

def main():
    optimizer = CookieClickerOptimizer()
    
    print("Cookie Clicker Optimizer (Millisecond-precise)")
    print("=" * 50)
    
    try:
        goal = float(input("Enter your target cookie count: "))
        if goal <= 0:
            print("Please enter a positive number.")
            return
        
        print(f"\nSearching for optimal path to reach {goal:,.0f} cookies...")
        print("Using millisecond-precise timing with 20ms click throttling.")
        print("This may take a moment for large goals...\n")
        
        result = optimizer.bfs_optimize(goal)
        
        if result is None:
            print("No solution found within reasonable time limits.")
            return
        
        path, total_time_ms = result
        total_seconds = total_time_ms / 1000.0
        total_frames = total_time_ms * 30 / 1000.0
        
        print(f"\nOptimal solution found!")
        print(f"Total time: {total_time_ms:,.0f}ms ({total_seconds:.3f} seconds, {total_frames:.2f} frames)")
        print("\nOptimal path:")
        print("-" * 60)
        
        # Compress consecutive actions for cleaner output
        compressed_path = compress_path(path)
        
        current_cookies = 0
        buildings_owned = {}
        action_number = 1
        
        for action_group in compressed_path:
            action_type = action_group['type']
            count = action_group['count']
            
            if action_type == 'click':
                # For click sequences, show summary
                start_time = action_group['start_time_ms']
                end_time = action_group['end_time_ms']
                
                if count == 1:
                    print(f"{action_number:2d}. Click at {end_time}ms")
                else:
                    print(f"{action_number:2d}. [{count} Clicks] ({start_time}ms-{end_time}ms)")
                
            elif action_type == 'buy':
                building = action_group['building']
                time_ms = action_group['time_ms']
                buildings_owned[building] = buildings_owned.get(building, 0) + 1
                
                # Calculate cost
                cost = optimizer.get_building_cost(building, buildings_owned[building] - 1)
                current_cookies -= cost
                
                print(f"{action_number:2d}. Buy {building} #{buildings_owned[building]} for {cost:,.0f} cookies at {time_ms}ms")
            
            action_number += 1
        
        print(f"\nFinal state:")
        print("Buildings owned:")
        for building, count in buildings_owned.items():
            if count > 0:
                print(f"  {building}: {count}")
        print(f"\nNote: Click throttling enforced at 20ms minimum interval between clicks.")
        print(f"      Building purchases take 1ms each.")
        print(f"      Production applied each frame based on CpS at frame start.")
                
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.")

if __name__ == "__main__":
    main()
