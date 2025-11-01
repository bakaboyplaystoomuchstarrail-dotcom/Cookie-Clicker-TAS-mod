from main import CookieClickerOptimizer, GameState
import math

optimizer = CookieClickerOptimizer()

# Start fresh
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

print("=== Advance to 280ms and buy cursor #1 ===")
state = optimizer.advance_time(state, 0, 280)
print(f"At 280ms: cookies={state.cookies:.4f}, baked={state.cookies_baked:.4f}")
print(f"  Frame: {state.last_production_frame}, CPS: {state.cps}")

# Buy cursor #1
cost1 = optimizer.get_building_cost('cursor', 0)
print(f"  Cursor #1 cost: {cost1}")
state = optimizer.purchase_building(state, 'cursor')
print(f"After purchase: cookies={state.cookies:.4f}, CPS={state.cps}")
print()

print("=== Advance to 640ms and try to buy cursor #2 ===")
state = optimizer.advance_time(state, 280, 640)
print(f"At 640ms: cookies={state.cookies:.4f}, baked={state.cookies_baked:.4f}")
print(f"  Frame: {state.last_production_frame}, CPS: {state.cps}")

# Check cost of cursor #2
cost2 = optimizer.get_building_cost('cursor', 1)
print(f"  Cursor #2 cost: {cost2}")
print(f"  Can afford: {state.cookies >= cost2}")

# Calculate expected values
clicks_to_280 = len([t for t in range(0, 281) if t % 20 == 0])
clicks_280_to_640 = len([t for t in range(281, 641) if t % 20 == 0 and t != state.last_click_time_ms])
total_clicks = clicks_to_280 + clicks_280_to_640

# Production frames
# Cursor bought at 280ms (frame 8), produces starting frame 9
# At 640ms we're in frame 19
frame_280 = math.floor(280 / (100/3))
frame_640 = math.floor(640 / (100/3))
production_frames = list(range(frame_280 + 1, frame_640 + 1))

print(f"\nExpected:")
print(f"  Clicks from 0-280: {clicks_to_280}")
print(f"  Clicks from 281-640: {clicks_280_to_640}")
print(f"  Total clicks: {total_clicks}")
print(f"  Frame at 280ms: {frame_280}")
print(f"  Frame at 640ms: {frame_640}")
print(f"  Production frames: {len(production_frames)} frames (frames {production_frames[0]} to {production_frames[-1]})")
print(f"  Production: {len(production_frames)} * 0.1/30 = {len(production_frames) * 0.1 / 30:.4f}")
print(f"  Expected total: {total_clicks} - {cost1} + {len(production_frames) * 0.1 / 30:.4f} = {total_clicks - cost1 + len(production_frames) * 0.1 / 30:.4f}")
