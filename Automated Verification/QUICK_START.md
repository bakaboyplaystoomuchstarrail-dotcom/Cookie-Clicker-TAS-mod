# 🚀 Quick Start - Automated Cookie Clicker Verification

## What Was Built

I've created a complete automated verification system for your Cookie Clicker BFS optimizer:

### 1. **HTML Cookie Clicker Replica** (`cookie_clicker_replica.html`)
   - Fully functional Cookie Clicker game with accurate mechanics
   - 30 FPS game loop, millisecond-precise timing
   - All 10 buildings with correct costs and CPS values
   - Click throttling (20ms minimum between clicks)

### 2. **Enhanced TAS Mod** (`tas_modAutomatedVerification.js`)
   - Manual frame-by-frame control (for testing)
   - **Automated playback** - executes BFS paths automatically
   - Real-time tracking of time, cookies baked, and game state
   - Visual TAS panel showing all metrics

### 3. **BFS Path Export Script** (`export_bfs_path.py`)
   - Runs your BFS optimizer
   - Exports optimal path to JSON format
   - Prints copy-paste friendly array for quick loading

### 4. **Automated Verification Interface** (`automated_verification.html`)
   - Load BFS paths from file or paste directly
   - One-click automated playback
   - Real-time status monitoring
   - Compare results with BFS predictions

### 5. **Quick Start Script** (`run_verification.ps1`)
   - One-command setup and launch
   - Generates path and opens verification system

## ⚡ Fastest Way to Use

### Option 1: All-in-One Script (Easiest)
```powershell
.\start_verification.ps1 100
```
This will:
1. Generate optimal path for 100 cookies
2. Start a local web server (required for iframe access)
3. Open the verification system in your browser automatically

**IMPORTANT:** Keep the terminal window open while using the system!

Then in the browser:
1. Click "Load Path File" → select `bfs_path.json`
2. Click "▶️ Start Automated Playback"
3. Watch it run!

When done, press `Ctrl+C` in the terminal to stop the server.

### Option 2: Manual Steps
```powershell
# Step 1: Generate path
python export_bfs_path.py 100

# Step 2: Start web server (in one terminal)
python serve.py

# The browser will open automatically
# Or manually visit: http://localhost:8000/automated_verification.html
```

**Note:** You MUST use the web server - opening files directly (file://) won't work due to browser security restrictions on iframe access.

Then follow the on-screen instructions in the browser.

## 📊 What You'll See

### During Execution:
- **TAS Panel (top-right):** Real-time metrics
  - Current time in milliseconds
  - Current frame number
  - Cookies in bank
  - Cookies baked (the goal!)
  - Click throttle status
  
- **Status Panel:** Execution log
  - Each action as it's executed
  - Timestamps and action types
  - Final results

### After Completion:
- Final time (should match BFS prediction)
- Final cookies baked (should reach goal)
- Complete action log for debugging

## 🎮 Controls

### Automated Mode (Default)
- Just load path and click "Start Automated Playback"
- System executes everything automatically

### Manual Mode (For Testing)
Press these keys in the game:
- **SPACE** - Wait until can click again
- **S** - Advance 1 millisecond
- **C** - Click the big cookie
- **1-9** - Buy buildings instantly
- **A** - Start auto-playback
- **P** - Pause/unpause
- **M** - Toggle manual/auto mode

## ✅ Verification Checklist

After running automation:
1. ✓ Check final time matches BFS prediction
2. ✓ Check cookies baked reaches goal
3. ✓ Review action log for any errors
4. ✓ Compare building purchases with BFS output

If everything matches → **Manual verification successful!** 🎉

## 📁 File Structure

```
Cookie Clicker Projekt/
├── main.py                          # BFS optimizer
├── export_bfs_path.py              # Export BFS to JSON
├── cookie_clicker_replica.html     # Game replica
├── tas_modAutomatedVerification.js # TAS mod with automation
├── automated_verification.html     # Main verification interface
├── run_verification.ps1            # Quick start script
├── bfs_path.json                   # Generated optimal path
├── AUTOMATED_VERIFICATION_README.md # Full documentation
└── QUICK_START.md                  # This file
```

## 🎯 Example: Test with 100 Cookies

```powershell
# Run the quick start script
.\run_verification.ps1 100
```

Expected result:
- BFS finds optimal path (probably ~2000ms)
- Automation executes all actions
- Final cookies baked: 100.0
- Verification: ✓ Success!

## 🔥 Try Different Goals

```powershell
# Small goal
.\run_verification.ps1 50

# Medium goal  
.\run_verification.ps1 500

# Large goal
.\run_verification.ps1 1000
```

## 🐛 Troubleshooting

**"TAS Controller not found"**
- The game iframe may need more time to load
- Try clicking "Reset Game" and wait 2-3 seconds

**"Path not loading"**
- Make sure `bfs_path.json` exists
- Check browser console (F12) for errors

**"Results don't match BFS"**
- Verify game mechanics match Python implementation
- Check console logs for execution order
- Try manual mode to step through actions

## 💡 Pro Tips

1. **Use browser console** (F12) to see detailed logs
2. **TAS panel is interactive** - buttons work too!
3. **Can paste paths directly** - no file needed
4. **Reset game** to try different strategies
5. **Manual mode** great for debugging specific actions

## 🎊 What This Achieves

You now have:
- ✅ Automated verification (no manual clicking!)
- ✅ Millisecond-precise timing
- ✅ Complete action replay
- ✅ Easy comparison with BFS predictions
- ✅ Visual feedback during execution
- ✅ One-command workflow

**No more manual verification fatigue!** 🎉

## 📚 More Info

See `AUTOMATED_VERIFICATION_README.md` for:
- Complete technical details
- API documentation
- Game mechanics explanation
- Advanced usage examples

---

**Ready to verify?** Run `.\run_verification.ps1 100` and watch the magic happen! ✨
