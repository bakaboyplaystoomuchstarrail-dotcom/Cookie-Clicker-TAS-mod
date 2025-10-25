# Cookie Clicker TAS (Tool-Assisted Speedrun) Mod

This mod allows you to verify the BFS optimizer calculations by running Cookie Clicker in frame-by-frame mode.

## Files

- `tas_mod.js` - The TAS mod that freezes time and enables frame-by-frame control
- `test_tas.html` - Test page that loads Cookie Clicker with the TAS mod
- `main.py` - The BFS optimizer that calculates optimal strategies

## How to Use the TAS Mod

### Method 1: Direct Console Injection (Recommended)

1. Open Cookie Clicker in your browser: https://orteil.dashnet.org/cookieclicker/
2. Wait for the game to fully load
3. Open browser console (F12)
4. Copy and paste the entire contents of `tas_mod.js` into the console
5. Press Enter to execute

### Method 2: Local Testing (if CORS allows)

1. Open `test_tas.html` in your browser
2. The mod will attempt to auto-inject (may be blocked by CORS)
3. If blocked, use Method 1 instead

## TAS Controls

Once the mod is loaded:

- **SPACE** - Advance one frame (when in manual mode)
- **C** - Click the big cookie (automatically advances 1 frame)
- **Click Buildings** - Buy buildings (automatically advances 1 frame per purchase)
- **P** - Toggle pause/unpause
- **M** - Toggle manual/auto mode
- **R** - Reset frame and cookie counters

## Verifying BFS Results

The BFS optimizer found that the optimal path to 100 cookies baked takes **87 frames**:

```
Frame  1-15: Click 15 times to get 15 cookies
Frame 15: Buy cursor #1 (cost: 15 cookies, +0.1 CPS)
Frame 16-33: Click until you can afford cursor #2
Frame 33: Buy cursor #2 (cost: ~18 cookies, +0.1 CPS, total 0.2 CPS)
Frame 34-51: Click until you can afford cursor #3  
Frame 51: Buy cursor #3 (cost: ~21 cookies, +0.1 CPS, total 0.3 CPS)
Frame 52-69: Click until you can afford cursor #4
Frame 69: Buy cursor #4 (cost: ~24 cookies, +0.1 CPS, total 0.4 CPS)
Frame 70-87: Click with 1.4 cookies per frame until 100 cookies baked
```

### Step-by-Step Verification

1. Load the TAS mod and reset counters (press R)
2. Press C 15 times to click the big cookie (or press SPACE then C repeatedly)
3. At frame 15, click on the cursor building to buy cursor #1
4. Continue clicking (C key) and buying cursors at the specified frames
5. Watch the "Cookies Baked" counter in the TAS panel
6. Verify that you reach 100 cookies baked at exactly frame 87

## TAS Panel Display

The mod shows a panel in the top-right corner with:
- Current frame number
- Total cookies baked (cumulative production)
- Current mode (MANUAL/AUTO)
- Current state (READY/PAUSED/RUNNING)

## Understanding the Results

- **Cookies Banked**: Current cookies in your account (can go up and down)
- **Cookies Baked**: Cumulative cookies produced (only goes up) - this is the BFS goal!
- **Frame**: Each action takes exactly 1 frame (1/30th of a second)
- **CPS**: Cookies per second (divide by 30 to get cookies per frame)

The key insight is that the BFS optimizes for **cookies baked** (cumulative production), not cookies banked. Spending cookies on buildings doesn't reduce your progress toward the goal!

## Troubleshooting

- If the mod doesn't load automatically, use the console injection method
- Make sure Cookie Clicker is fully loaded before injecting the mod
- If keyboard controls don't work, click on the Cookie Clicker game area first
- The mod requires a modern browser with ES6 support

## Technical Details

The mod works by:
1. Overriding `Game.Logic()` to control when time advances
2. Intercepting clicks and purchases to advance frames manually
3. Tracking cumulative cookie production separately from the game's built-in counters
4. Providing precise frame-by-frame control for verification

This allows you to verify that the BFS calculations are correct and that the optimal strategy really does reach 100 cookies baked in exactly 87 frames.