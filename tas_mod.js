/*
 * Cookie Clicker TAS (Tool-Assisted Speedrun) Mod
 * 
 * This mod freezes time and allows frame-by-frame execution to verify BFS calculations
 * 
 * Usage:
 * 1. Load this mod in Cookie Clicker
 * 2. Press SPACE to advance one frame
 * 3. Press 'C' to click the big cookie
 * 4. Click on buildings to buy them (costs one frame)
 * 5. Press 'P' to pause/unpause automatic mode
 * 
 * The mod tracks frames and cookies baked to verify against BFS predictions
 */

Game.registerMod("TAS Controller", {
    init: function() {
        console.log("TAS Controller mod initialized!");
        
        // TAS state variables
        this.timeMs = 0;  // Track time in milliseconds instead of frames
        this.cookiesBaked = 0;
        this.lastClickTimeMs = -20;  // Start at -20 so first click at t=0 is valid
        this.lastProductionFrame = -1;  // Track which frame last had production applied
        this.isPaused = true;  // Start paused for ms-by-ms control
        this.originalLogic = null;
        this.manualMode = true;  // When true, only advance on user input
        this.fps = 30;  // Game runs at 30 FPS
        this.msPerFrame = 1000 / this.fps;  // 33.333... ms per frame
        
        // Store original game functions
        this.originalLogic = Game.Logic;
        this.originalClickCookie = Game.ClickCookie;
        
        // Override Game.Logic to prevent automatic time advancement
        var self = this;
        Game.Logic = function() {
            // Only run logic if we're not paused or if we're in auto mode
            // In TAS mode, time advancement is manual via advanceOneMs()
            if (!self.isPaused && !self.manualMode) {
                self.originalLogic();
                self.updateDisplay();
            }
        };
        
        // Override ClickCookie to make clicks instantaneous with throttling
        Game.ClickCookie = function() {
            if (self.manualMode) {
                // Check click throttling: need at least 20ms since last click
                if (self.timeMs - self.lastClickTimeMs < 20) {
                    console.log("Click throttled! Need " + (20 - (self.timeMs - self.lastClickTimeMs)) + "ms more.");
                    return;
                }
                
                // Execute the click (adds cookies instantly, no time advancement)
                var cookiesBefore = Game.cookiesEarned;
                self.originalClickCookie();
                var cookiesAfter = Game.cookiesEarned;
                
                var clickGain = cookiesAfter - cookiesBefore;
                self.cookiesBaked += clickGain;
                
                // Update last click time (click happens at current time, doesn't advance time)
                self.lastClickTimeMs = self.timeMs;
                
                console.log("Time " + self.timeMs + "ms - Click! Gained: " + clickGain.toFixed(1) + ", Total baked: " + self.cookiesBaked.toFixed(1));
                
                self.updateDisplay();
            } else {
                // Auto mode - use original behavior
                self.originalClickCookie();
            }
        };
        
        
        // Add keyboard controls
        document.addEventListener('keydown', function(e) {
            switch(e.key.toLowerCase()) {
                case ' ': // Spacebar - advance one millisecond (wait action)
                    e.preventDefault();
                    if (self.manualMode) {
                        self.advanceOneMs();
                    }
                    break;
                case 'c': // C key - click cookie
                    e.preventDefault();
                    Game.ClickCookie();
                    break;
                case 'p': // P key - toggle pause
                    e.preventDefault();
                    self.togglePause();
                    break;
                case 'm': // M key - toggle manual/auto mode
                    e.preventDefault();
                    self.toggleMode();
                    break;
            }
            
            // Building purchase keybindings: 1-9 for first 9 buildings
            var buildingKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
            var buildingIndex = buildingKeys.indexOf(e.key);
            if (buildingIndex !== -1 && self.manualMode) {
                e.preventDefault();
                var buildingNames = Object.keys(Game.Objects);
                if (buildingIndex < buildingNames.length) {
                    var building = Game.Objects[buildingNames[buildingIndex]];
                    if (building && building.buy) {
                        building.buy();
                        // Purchases are INSTANT - no time advancement
                        console.log("Time " + self.timeMs + "ms - " + buildingNames[buildingIndex] + " purchased. Cookies baked: " + self.cookiesBaked.toFixed(1));
                        self.updateDisplay();
                    }
                }
            }
            
            // Upgrade purchase keybindings: ! @ # $ % ^ & * ( for upgrades
            var upgradeKeys = ['!', '@', '#', '$', '%', '^', '&', '*', '('];
            var upgradeIndex = upgradeKeys.indexOf(e.key);
            if (upgradeIndex !== -1 && self.manualMode) {
                e.preventDefault();
                var upgradeList = Game.UpgradesInStore || [];
                if (upgradeIndex < upgradeList.length) {
                    var upgrade = upgradeList[upgradeIndex];
                    if (upgrade && upgrade.buy) {
                        upgrade.buy();
                        // Purchases are INSTANT - no time advancement
                        console.log("Time " + self.timeMs + "ms - " + upgrade.name + " purchased. Cookies baked: " + self.cookiesBaked.toFixed(1));
                        self.updateDisplay();
                    }
                }
            }
        });
        
        // Create TAS display panel
        this.createTASPanel();
        
        console.log("TAS Controller ready! Controls:");
        console.log("SPACE - Advance one millisecond (wait)");
        console.log("C - Click big cookie (instant, 20ms throttle)");
        console.log("1-9 - Buy building (instant)");
        console.log("!-( - Buy upgrade (instant)");
        console.log("P - Toggle pause");
        console.log("M - Toggle manual/auto mode");
    },
    
    advanceOneMs: function() {
        // Advance time by exactly 1 millisecond
        this.timeMs += 1;
        
        // Calculate current frame (ms / msPerFrame)
        // Frame boundaries: 0-33ms=frame0, 34-66ms=frame1, etc.
        var currentFrame = Math.floor(this.timeMs / this.msPerFrame);
        
        // If we're in a new frame and have CpS, apply production
        // Production is CpS/30 per frame (30 FPS)
        if (currentFrame > this.lastProductionFrame && Game.cookiesPs > 0) {
            var productionThisFrame = Game.cookiesPs / this.fps;
            Game.cookies += productionThisFrame;
            this.cookiesBaked += productionThisFrame;
            this.lastProductionFrame = currentFrame;
            
            console.log("Time " + this.timeMs + "ms (Frame " + currentFrame + ") - Production: " + productionThisFrame.toFixed(2) + ", Total baked: " + this.cookiesBaked.toFixed(1));
        }
        
        this.updateDisplay();
    },
    
    
    togglePause: function() {
        this.isPaused = !this.isPaused;
        console.log("TAS " + (this.isPaused ? "PAUSED" : "UNPAUSED"));
        this.updateDisplay();
    },
    
    toggleMode: function() {
        this.manualMode = !this.manualMode;
        console.log("TAS Mode: " + (this.manualMode ? "MANUAL" : "AUTO"));
        this.updateDisplay();
    },
    
    
    
    getBuildingCounts: function() {
        var counts = {};
        for (var i in Game.Objects) {
            if (Game.Objects[i].amount > 0) {
                counts[i] = Game.Objects[i].amount;
            }
        }
        return counts;
    },
    
    createTASPanel: function() {
        // Create a TAS control panel in the game UI
        var panel = document.createElement('div');
        panel.id = 'tasPanel';
        panel.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10000;
            min-width: 200px;
        `;
        
        panel.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 10px;">🎮 TAS Controller</div>
            <div id="tasTimeMs">Time: 0ms</div>
            <div id="tasFrame">Frame: 0</div>
            <div id="tasCookiesBank">Cookies in Bank: 0</div>
            <div id="tasCookiesBaked">Cookies Baked: 0</div>
            <div id="tasClickThrottle">Can click: Yes</div>
            <div id="tasMode">Mode: MANUAL</div>
            <div id="tasPauseState">State: READY</div>
            <hr style="margin: 10px 0;">
            <div style="font-size: 10px;">
                SPACE: Wait 1ms<br>
                C: Click cookie (instant)<br>
                1-9: Buy building (instant)<br>
                !-(): Buy upgrade (instant)<br>
                P: Pause/unpause<br>
                M: Manual/auto
            </div>
        `;
        
        document.body.appendChild(panel);
    },
    
    updateDisplay: function() {
        var timeEl = document.getElementById('tasTimeMs');
        var frameEl = document.getElementById('tasFrame');
        var bankEl = document.getElementById('tasCookiesBank');
        var bakedEl = document.getElementById('tasCookiesBaked');
        var clickThrottleEl = document.getElementById('tasClickThrottle');
        var modeEl = document.getElementById('tasMode');
        var pauseEl = document.getElementById('tasPauseState');
        
        var currentFrame = Math.floor(this.timeMs / this.msPerFrame);
        var canClick = (this.timeMs - this.lastClickTimeMs >= 20);
        var msUntilClick = canClick ? 0 : 20 - (this.timeMs - this.lastClickTimeMs);
        
        if (timeEl) timeEl.textContent = 'Time: ' + this.timeMs + 'ms';
        if (frameEl) frameEl.textContent = 'Frame: ' + currentFrame;
        if (bankEl) bankEl.textContent = 'Cookies in Bank: ' + Game.cookies.toFixed(1);
        if (bakedEl) bakedEl.textContent = 'Cookies Baked: ' + this.cookiesBaked.toFixed(1);
        if (clickThrottleEl) clickThrottleEl.textContent = 'Can click: ' + (canClick ? 'Yes' : 'No (' + msUntilClick + 'ms)');
        if (modeEl) modeEl.textContent = 'Mode: ' + (this.manualMode ? 'MANUAL' : 'AUTO');
        
        // Show current state
        if (pauseEl) {
            if (this.isPaused) {
                pauseEl.textContent = 'State: PAUSED';
            } else {
                pauseEl.textContent = 'State: RUNNING';
            }
        }
    },
    
    // Verification function to check against BFS predictions
    verifyPath: function(expectedPath) {
        console.log("=== TAS VERIFICATION ===");
        console.log("Expected path for 100 cookies baked:");
        for (var i = 0; i < expectedPath.length; i++) {
            var action = expectedPath[i];
            console.log("Frame " + action.frame + ": " + action.action);
        }
        console.log("========================");
        
        // You can call this with the BFS results to compare
        // Example: Game.mods["TAS Controller"].verifyPath([
        //   {frame: 15, action: "Buy cursor #1"},
        //   {frame: 33, action: "Buy cursor #2"},
        //   // etc...
        // ]);
    }
});

// Auto-load instructions
console.log("TAS mod loaded! The game is now in millisecond-by-millisecond mode.");
console.log("Press SPACE to wait 1ms, C to click (instant, 20ms throttle), 1-9 to buy buildings (instant).");
console.log("The mod will track time and cookies baked to verify your BFS calculations.");
