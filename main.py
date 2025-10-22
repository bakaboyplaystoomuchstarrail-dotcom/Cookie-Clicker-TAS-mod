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
    production_schedule: dict  # building_name -> next frame when it produces (Bus Tech)
    frame: int
    click_power: float  # current click value
    
    def copy(self):
        return GameState(
            cookies=self.cookies,
            cookies_baked=self.cookies_baked,
            buildings=self.buildings.copy(),
            production_schedule=self.production_schedule.copy(),
            frame=self.frame,
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
        """Get list of buildings that can be purchased with current cookies"""
        possible = []
        for building_name in self.buildings:
            current_count = state.buildings.get(building_name, 0)
            cost = self.get_building_cost(building_name, current_count)
            if state.cookies >= cost:
                possible.append(building_name)
        return possible
    
    def purchase_building(self, state: GameState, building_name: str) -> GameState:
        """Create new state after purchasing a building (Bus Tech: no immediate production)"""
        new_state = state.copy()
        current_count = new_state.buildings.get(building_name, 0)
        cost = self.get_building_cost(building_name, current_count)
        
        # Make the purchase (spending doesn't reduce baked cookies!)
        new_state.cookies -= cost
        new_state.buildings[building_name] = current_count + 1
        
        # Bus Tech: if first building of this type, schedule its first production
        if current_count == 0:
            # First building: will produce 30 frames from now
            new_state.production_schedule[building_name] = new_state.frame + 30
        # If not first, production schedule stays the same (bus already scheduled)
        
        # Update click power based on finger upgrades (simplified)
        if building_name == 'cursor':
            new_state.click_power = self.calculate_click_power(new_state)
        
        return new_state
    
    def click_cookie(self, state: GameState) -> GameState:
        """Create new state after clicking the big cookie (single click per frame)"""
        new_state = state.copy()
        # Use the calculated click power from the state
        click_power = state.click_power
        
        # Add click cookies
        new_state.cookies += click_power
        new_state.cookies_baked += click_power
        
        # Check for Bus Tech production at this frame
        buildings_producing = []
        for building_name, next_prod_frame in new_state.production_schedule.items():
            if next_prod_frame == new_state.frame:
                buildings_producing.append(building_name)
        
        # Apply production from buildings that produce this frame
        for building_name in buildings_producing:
            building_count = new_state.buildings.get(building_name, 0)
            production_gain = self.buildings[building_name].base_cps * building_count
            new_state.cookies += production_gain
            new_state.cookies_baked += production_gain
            # Schedule next production 30 frames later
            new_state.production_schedule[building_name] = new_state.frame + 30
        
        new_state.frame += 1
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
    
    def wait_frames(self, state: GameState, frames: int) -> GameState:
        """Create new state after waiting specified frames"""
        new_state = state.copy()
        new_state.cookies += new_state.total_cps * frames
        new_state.frame += frames
        return new_state
    
    def frames_to_afford(self, state: GameState, building_name: str) -> int:
        """Calculate frames needed to afford a building"""
        current_count = state.buildings.get(building_name, 0)
        cost = self.get_building_cost(building_name, current_count)
        
        if state.cookies >= cost:
            return 0
        
        if state.total_cps <= 0:
            return float('inf')
        
        return math.ceil((cost - state.cookies) / state.total_cps)
    
    def frames_to_afford_amount(self, state: GameState, target_amount: float) -> int:
        """Calculate frames needed to reach a specific cookie amount"""
        if state.cookies >= target_amount:
            return 0
        
        if state.total_cps <= 0:
            return float('inf')
        
        return math.ceil((target_amount - state.cookies) / state.total_cps)
    
    
    def bfs_optimize(self, goal_cookies: float, max_frames: int = 200) -> Optional[List[Tuple[str, int]]]:
        """
        True BFS: Process all states at frame N completely before moving to frame N+1
        """
        initial_state = GameState(
            cookies=0,
            cookies_baked=0,  # Track cumulative production
            buildings={},
            production_schedule={},  # Bus Tech: tracks next production frame for each building
            frame=0,
            click_power=1.0
        )
        
        # States organized by frame number: {frame_num: [(state, path), ...]}
        states_by_frame = {0: [(initial_state, [])]}
        visited = set()
        
        print(f"Starting true BFS with goal: {goal_cookies} cookies")
        
        for frame in range(max_frames + 1):
            if frame not in states_by_frame:
                continue
                
            current_states = states_by_frame[frame]
            if not current_states:
                continue
                
            print(f"Frame {frame}: Processing {len(current_states)} states")
            
            # Process ALL states at this frame level before moving to next frame
            for state, path in current_states:
                # Check if goal reached (based on cookies baked, not banked)
                if state.cookies_baked >= goal_cookies:
                    print(f"Found optimal solution at frame {frame}!")
                    return path, frame
                
                # Create state signature (exclude frame since we're organizing by frame)
                state_sig = (
                    round(state.cookies * 100) / 100,
                    round(state.cookies_baked * 100) / 100,
                    tuple(sorted(state.buildings.items())),
                    tuple(sorted(state.production_schedule.items()))
                )
                
                if state_sig in visited:
                    continue
                visited.add(state_sig)
                
                # Generate ALL possible successor states
                
                # Try all possible purchases (these happen AT this frame)
                possible_purchases = self.get_possible_purchases(state)
                for building_name in possible_purchases:
                    purchase_state = self.purchase_building(state, building_name)
                    purchase_path = path + [('buy', building_name, frame)]
                    
                    next_frame = frame + 1
                    purchase_state.frame = next_frame
                    
                    if next_frame not in states_by_frame:
                        states_by_frame[next_frame] = []
                    states_by_frame[next_frame].append((purchase_state, purchase_path))
                
                # Try clicking (this happens AT this frame)
                click_state = self.click_cookie(state)
                click_path = path + [('click', 1, frame)]
                
                # Add click state to NEXT frame
                next_frame = frame + 1
                if next_frame not in states_by_frame:
                    states_by_frame[next_frame] = []
                states_by_frame[next_frame].append((click_state, click_path))
                
        
        print(f"No solution found within {max_frames} frames")
        return None
        
        # If we get here, no solution was found
        return None

def compress_path(path):
    """Compress consecutive identical actions for cleaner output"""
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
                current_group['end_frame'] = action[2]
            else:
                # Start new click group
                if current_group:
                    compressed.append(current_group)
                current_group = {
                    'type': 'click',
                    'count': 1,
                    'start_frame': action[2],
                    'end_frame': action[2]
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
                'frame': action[2]
            })
        
        elif action_type == 'wait':
            # Waits don't get grouped (shouldn't happen in current implementation)
            if current_group:
                compressed.append(current_group)
                current_group = None
            
            compressed.append({
                'type': 'wait',
                'count': 1,
                'frames': action[1],
                'end_frame': action[2]
            })
    
    # Don't forget the last group
    if current_group:
        compressed.append(current_group)
    
    return compressed

def main():
    optimizer = CookieClickerOptimizer()
    
    print("Cookie Clicker Optimizer")
    print("=" * 40)
    
    try:
        goal = float(input("Enter your target cookie count: "))
        if goal <= 0:
            print("Please enter a positive number.")
            return
        
        print(f"\nSearching for optimal path to reach {goal:,.0f} cookies...")
        print("This may take a moment for large goals...")
        
        result = optimizer.bfs_optimize(goal)
        
        if result is None:
            print("No solution found within reasonable time limits.")
            return
        
        path, total_frames = result
        total_seconds = total_frames / 30  # Convert frames to seconds
        
        print(f"\nOptimal solution found!")
        print(f"Total time: {total_frames:,.0f} frames ({total_seconds:.1f} seconds)")
        print("\nOptimal path:")
        print("-" * 50)
        
        # Compress consecutive actions for cleaner output
        compressed_path = compress_path(path)
        
        current_cookies = 0
        buildings_owned = {}
        action_number = 1
        
        for action_group in compressed_path:
            action_type = action_group['type']
            count = action_group['count']
            
            if action_type == 'click':
                # For click sequences, just show summary (Bus Tech makes detailed tracking complex)
                start_frame = action_group['start_frame']
                end_frame = action_group['end_frame']
                
                if count == 1:
                    print(f"{action_number:2d}. Click (Frame {end_frame})")
                else:
                    print(f"{action_number:2d}. [{count} Clicks] (Frames {start_frame}-{end_frame})")
                
            elif action_type == 'buy':
                building = action_group['building']
                frame = action_group['frame']
                buildings_owned[building] = buildings_owned.get(building, 0) + 1
                
                # Calculate cost
                cost = optimizer.get_building_cost(building, buildings_owned[building] - 1)
                current_cookies -= cost
                
                print(f"{action_number:2d}. Buy {building} #{buildings_owned[building]} for {cost:,.0f} cookies (Frame {frame})")
            
            action_number += 1
        
        print(f"\nFinal state:")
        print("Buildings owned:")
        for building, count in buildings_owned.items():
            if count > 0:
                print(f"  {building}: {count}")
        print(f"\nNote: With Bus Tech mechanics, passive production occurs at specific frame intervals")
        print(f"      based on when each building type is first purchased.")
                
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.")

if __name__ == "__main__":
    main()