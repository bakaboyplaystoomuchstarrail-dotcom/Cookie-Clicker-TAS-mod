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
        this.frameCounter = 0;
        this.cookiesBaked = 0;
        this.isPaused = true;  // Start paused for frame-by-frame control
        this.originalLogic = null;
        this.manualMode = true;  // When true, only advance on user input
        
        // Store original game functions
        this.originalLogic = Game.Logic;
        this.originalClickCookie = Game.ClickCookie;
        
        // Override Game.Logic to implement frame control
        var self = this;
        Game.Logic = function() {
            // Only run logic if we're not paused or if we're in auto mode
            if (!self.isPaused && !self.manualMode) {
                self.originalLogic();
                self.frameCounter++;
                self.updateDisplay();
            }
        };
        
        // Override ClickCookie to track frame advancement
        Game.ClickCookie = function() {
            var cookiesBefore = Game.cookiesEarned;
            self.originalClickCookie();
            var cookiesAfter = Game.cookiesEarned;
            
            // If in manual mode, advance one frame after clicking
            if (self.manualMode) {
                // Execute game logic and increment frame
                self.originalLogic();
                self.frameCounter++;
                
                // Track total gained from this click (click power + passive income per second)
                // Game.cookiesEarned tracks total production including passive
                var totalGained = cookiesAfter - cookiesBefore;
                self.cookiesBaked += totalGained;
                
                console.log("Frame " + self.frameCounter + " - Cookies gained: " + totalGained.toFixed(1) + ", Total baked: " + self.cookiesBaked.toFixed(1));
                
                self.updateDisplay();
            }
        };
        
        
        // Add keyboard controls
        document.addEventListener('keydown', function(e) {
            switch(e.key.toLowerCase()) {
                case ' ': // Spacebar - advance one frame
                    e.preventDefault();
                    if (self.manualMode) {
                        self.advanceOneFrame();
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
                        // Manually advance frame and track passive income (Game.cookiesPs is per second)
                        self.frameCounter++;
                        var passiveGain = Game.cookiesPs;
                        Game.cookies += passiveGain;
                        self.cookiesBaked += passiveGain;
                        console.log("Frame " + self.frameCounter + " - " + buildingNames[buildingIndex] + " purchased. Cookies baked: " + self.cookiesBaked.toFixed(1));
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
                        // Manually advance frame and track passive income (Game.cookiesPs is per second)
                        self.frameCounter++;
                        var passiveGain = Game.cookiesPs;
                        Game.cookies += passiveGain;
                        self.cookiesBaked += passiveGain;
                        console.log("Frame " + self.frameCounter + " - " + upgrade.name + " purchased. Cookies baked: " + self.cookiesBaked.toFixed(1));
                        self.updateDisplay();
                    }
                }
            }
        });
        
        // Create TAS display panel
        this.createTASPanel();
        
        console.log("TAS Controller ready! Controls:");
        console.log("SPACE - Advance one frame");
        console.log("C - Click big cookie");
        console.log("P - Toggle pause");
        console.log("M - Toggle manual/auto mode");
    },
    
    advanceOneFrame: function() {
        // Execute one frame of game logic
        this.originalLogic();
        
        // Normal frame advancement
        this.frameCounter++;
        
        // Track passive income this frame (Game.cookiesPs is per second)
        var passiveGain = Game.cookiesPs;
        this.cookiesBaked += passiveGain;
        
        console.log("Frame " + this.frameCounter + " - Cookies baked: " + this.cookiesBaked.toFixed(1));
        
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
            <div id="tasFrameCount">Frame: 0</div>
            <div id="tasCookiesBank">Cookies in Bank: 0</div>
            <div id="tasCookiesBaked">Cookies Baked: 0</div>
            <div id="tasMode">Mode: MANUAL</div>
            <div id="tasPauseState">State: READY</div>
            <hr style="margin: 10px 0;">
            <div style="font-size: 10px;">
                SPACE: Advance frame<br>
                C: Click cookie<br>
                1-9: Buy building (0-8)<br>
                !-(): Buy upgrade (0-8)<br>
                P: Pause/unpause<br>
                M: Manual/auto
            </div>
        `;
        
        document.body.appendChild(panel);
    },
    
    updateDisplay: function() {
        var frameEl = document.getElementById('tasFrameCount');
        var bankEl = document.getElementById('tasCookiesBank');
        var bakedEl = document.getElementById('tasCookiesBaked');
        var modeEl = document.getElementById('tasMode');
        var pauseEl = document.getElementById('tasPauseState');
        
        if (frameEl) frameEl.textContent = 'Frame: ' + this.frameCounter;
        if (bankEl) bankEl.textContent = 'Cookies in Bank: ' + Game.cookies.toFixed(1);
        if (bakedEl) bakedEl.textContent = 'Cookies Baked: ' + this.cookiesBaked.toFixed(1);
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
console.log("TAS mod loaded! The game is now in frame-by-frame mode.");
console.log("Press SPACE to advance frames, C to click, click buildings to buy them.");
console.log("The mod will track frames and cookies baked to verify your BFS calculations.");
