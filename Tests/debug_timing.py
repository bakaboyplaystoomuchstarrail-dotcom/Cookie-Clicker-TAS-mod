from main import CookieClickerOptimizer, GameState
import math

optimizer = CookieClickerOptimizer()

# Simulate the exact scenario from the output
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

print("=== Initial State ===")
print(f"Time: {state.time_ms}ms, Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}")
print(f"CPS: {state.cps}, Last frame: {state.last_production_frame}")
print()

# Advance to 280ms and buy first cursor
print("=== Advance to 280ms ===")
state = optimizer.advance_time(state, state.time_ms, 280)
print(f"Time: {state.time_ms}ms, Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}")
print(f"Last frame: {state.last_production_frame}, Clicks so far: {280//20}")
print()

print("=== Buy cursor #1 at 280ms ===")
state = optimizer.purchase_building(state, 'cursor')
print(f"Time: {state.time_ms}ms, Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}")
print(f"CPS: {state.cps}, Buildings: {state.buildings}")
print()

# Advance to 2040ms
print("=== Advance to 2040ms (buying cursors 2-5 along the way) ===")
# Cursor #2 at 640ms
state = optimizer.advance_time(state, state.time_ms, 640)
print(f"At 640ms: Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}, Frame: {state.last_production_frame}")
state = optimizer.purchase_building(state, 'cursor')
print(f"After cursor #2: CPS: {state.cps}")

# Cursor #3 at 1040ms  
state = optimizer.advance_time(state, state.time_ms, 1040)
print(f"At 1040ms: Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}, Frame: {state.last_production_frame}")
state = optimizer.purchase_building(state, 'cursor')
print(f"After cursor #3: CPS: {state.cps}")

# Cursor #4 at 1500ms
state = optimizer.advance_time(state, state.time_ms, 1500)
print(f"At 1500ms: Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}, Frame: {state.last_production_frame}")
state = optimizer.purchase_building(state, 'cursor')
print(f"After cursor #4: CPS: {state.cps}")

# Cursor #5 at 2040ms
state = optimizer.advance_time(state, state.time_ms, 2040)
print(f"At 2040ms BEFORE purchase: Cookies: {state.cookies:.2f}, Baked: {state.cookies_baked:.2f}, Frame: {state.last_production_frame}")
print(f"Expected cookies from clicks: {(2040//20 + 1)} clicks = {(2040//20 + 1)} cookies")
print(f"Frame 2040ms is in: {math.floor(2040 / (100/3))} = frame {math.floor(2040 / (100/3))}")
state = optimizer.purchase_building(state, 'cursor')
print(f"After cursor #5: CPS: {state.cps}, Cursors: {state.buildings.get('cursor', 0)}")
