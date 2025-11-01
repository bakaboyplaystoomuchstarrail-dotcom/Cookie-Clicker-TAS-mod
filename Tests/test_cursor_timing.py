import sys
from main import CookieClickerOptimizer, GameState

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

# Buy cursors at 280ms, 640ms, 1040ms
state = optimizer.advance_time(state, 0, 280)
state = optimizer.purchase_building(state, 'cursor')

state = optimizer.advance_time(state, 280, 640)
state = optimizer.purchase_building(state, 'cursor')

state = optimizer.advance_time(state, 640, 1040)
state = optimizer.purchase_building(state, 'cursor')

# Find exact time to reach 100
t = 1040
while state.cookies_baked < 100:
    t += 1
    state = optimizer.advance_time(state, state.time_ms, t)

print(f'Cursor strategy reaches 100 at t={t}ms (baked={state.cookies_baked:.4f})')
print(f'Pure clicking reaches 100 at t=1980ms')
print(f'Difference: {1980 - t}ms faster!')
