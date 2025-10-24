"""
Create a standalone HTML file with everything embedded:
- Cookie Clicker game
- TAS mod
- BFS path data
- Auto-execution on page load
"""

import json

# Read the BFS path
with open('bfs_path.json', 'r') as f:
    bfs_data = json.load(f)

path_data = bfs_data['path']
goal = bfs_data['goal_cookies']
total_time = bfs_data['total_time_ms']
total_actions = bfs_data['total_actions']

print(f"Creating standalone HTML for {goal} cookies ({total_actions} actions, {total_time}ms)...")

# Create standalone HTML
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cookie Clicker Auto-Verification - {goal} Cookies</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Courier New', monospace;
            background: linear-gradient(to bottom, #2b5876, #4e4376);
            color: white;
        }}
        
        #info {{
            max-width: 1200px;
            margin: 0 auto 20px;
            background: rgba(0, 0, 0, 0.7);
            padding: 20px;
            border-radius: 10px;
        }}
        
        #gameContainer {{
            display: flex;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        #leftPanel {{
            flex: 1;
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
        }}
        
        #bigCookie {{
            width: 200px;
            height: 200px;
            background: radial-gradient(circle at 40% 40%, #f4a460, #d2691e);
            border: 5px solid #8b4513;
            border-radius: 50%;
            cursor: pointer;
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            user-select: none;
        }}
        
        #cookieCount {{
            font-size: 28px;
            text-align: center;
            margin: 20px 0;
            line-height: 1.6;
        }}
        
        #stats {{
            font-size: 16px;
            margin-top: 20px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            line-height: 1.8;
        }}
        
        #stats > div {{
            margin: 8px 0;
        }}
        
        #rightPanel {{
            flex: 1;
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
        }}
        
        .building {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            margin: 12px 0;
            border-radius: 5px;
            font-size: 16px;
            line-height: 1.7;
        }}
        
        .building > div {{
            margin: 5px 0;
        }}
        
        .building strong {{
            font-size: 19px;
        }}
        
        .building.unaffordable {{
            opacity: 0.5;
        }}
        
        #tasPanel {{
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10000;
            min-width: 250px;
            border: 2px solid #4CAF50;
        }}
        
        #log {{
            margin-top: 10px;
            padding: 10px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 5px;
            max-height: 200px;
            overflow-y: auto;
            font-size: 10px;
        }}
        
        .success {{ color: #4CAF50; }}
        .warning {{ color: #ff9800; }}
        .error {{ color: #f44336; }}
    </style>
</head>
<body>
    <div id="info">
        <h1 style="text-align: center; margin: 0;">🍪 Cookie Clicker Auto-Verification 🍪</h1>
        <p style="text-align: center; margin: 10px 0;">
            <strong>Goal:</strong> {goal} cookies | 
            <strong>Expected Time:</strong> {total_time}ms | 
            <strong>Actions:</strong> {total_actions}
        </p>
        <p id="autoExecMessage" style="text-align: center; margin: 10px 0; color: #4CAF50;">
            ⚡ Auto-execution will start in 2 seconds...
        </p>
    </div>
    
    <div id="gameContainer">
        <div id="leftPanel">
            <div id="cookieCount">
                <div>Cookies: <span id="cookiesDisplay">0</span></div>
                <div style="font-size: 16px; margin-top: 5px;">per second: <span id="cpsDisplay">0</span></div>
            </div>
            
            <div id="bigCookie">🍪</div>
            
            <div id="stats">
                <div><strong>Statistics</strong></div>
                <div>Cookies baked: <span id="cookiesBaked">0</span></div>
                <div>Hand-made cookies: <span id="handMadeCookies">0</span></div>
            </div>
        </div>
        
        <div id="rightPanel">
            <h2>Buildings</h2>
            <div id="buildingsContainer"></div>
        </div>
    </div>
    
    <div id="tasPanel">
        <div style="font-weight: bold; margin-bottom: 10px; font-size: 14px;">🎮 TAS Controller</div>
        <div id="tasTimeMs" style="font-size: 13px; margin: 3px 0;">Time: 0ms (0.00s)</div>
        <div id="tasFrame" style="font-size: 13px; margin: 3px 0;">Frame: 0</div>
        <div id="tasStatus" style="font-size: 13px; margin: 3px 0; padding: 5px 0; border-top: 1px solid #444;">Status: Initializing...</div>
        <div id="log"></div>
    </div>
    
    <script>
        // Embedded BFS path data
        const BFS_PATH = {json.dumps(path_data)};
        const GOAL_COOKIES = {goal};
        const EXPECTED_TIME = {total_time};
        
        // Cookie Clicker Game Object
        var Game = {{
            cookies: 0,
            cookiesEarned: 0,
            cookiesPs: 0,
            cookieClicks: 0,
            fps: 30,
            Objects: {{}},
            buildingProduction: {{}},  // Track production per building
            
            init: function(skipBuildUI) {{
                this.Objects = {{
                    'Cursor': {{ name: 'Cursor', id: 0, basePrice: 15, baseCps: 0.1, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Cursor'); }} }},
                    'Grandma': {{ name: 'Grandma', id: 1, basePrice: 100, baseCps: 1, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Grandma'); }} }},
                    'Farm': {{ name: 'Farm', id: 2, basePrice: 1100, baseCps: 8, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Farm'); }} }},
                    'Mine': {{ name: 'Mine', id: 3, basePrice: 12000, baseCps: 47, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Mine'); }} }},
                    'Factory': {{ name: 'Factory', id: 4, basePrice: 130000, baseCps: 260, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Factory'); }} }},
                    'Bank': {{ name: 'Bank', id: 5, basePrice: 1400000, baseCps: 1400, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Bank'); }} }},
                    'Temple': {{ name: 'Temple', id: 6, basePrice: 20000000, baseCps: 7800, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Temple'); }} }},
                    'Wizard tower': {{ name: 'Wizard tower', id: 7, basePrice: 330000000, baseCps: 44000, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Wizard tower'); }} }},
                    'Shipment': {{ name: 'Shipment', id: 8, basePrice: 5100000000, baseCps: 260000, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Shipment'); }} }},
                    'Alchemy lab': {{ name: 'Alchemy lab', id: 9, basePrice: 75000000000, baseCps: 1600000, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Alchemy lab'); }} }}
                }};
                if (!skipBuildUI) this.buildUI();
                this.startGameLoop();
            }},
            
            buildUI: function(buildingsUsed) {{
                var container = document.getElementById('buildingsContainer');
                
                // If buildingsUsed is provided, only show those buildings
                var buildingsToShow = buildingsUsed || Object.keys(this.Objects);
                
                for (var i = 0; i < buildingsToShow.length; i++) {{
                    var name = buildingsToShow[i];
                    var obj = this.Objects[name];
                    if (!obj) continue;
                    
                    var div = document.createElement('div');
                    div.className = 'building unaffordable';
                    div.id = 'building_' + name;
                    div.innerHTML = '<div><strong>' + obj.name + '</strong></div>' +
                                  '<div id="info1_' + name + '">Cost: <span id="cost_' + name + '">0</span></div>' +
                                  '<div>Owned: <span id="owned_' + name + '">0</span></div>' +
                                  '<div id="info2_' + name + '">+' + obj.baseCps + ' cps</div>';
                    
                    container.appendChild(div);
                }}
            }},
            getPrice: function(buildingName) {{
                var obj = this.Objects[buildingName];
                return Math.ceil(obj.basePrice * Math.pow(obj.priceIncrease, obj.amount));
            }},
            
            buyBuilding: function(buildingName) {{
                var obj = this.Objects[buildingName];
                var price = this.getPrice(buildingName);
                if (this.cookies >= price) {{
                    this.cookies -= price;
                    obj.amount++;
                    this.recalculateCps();
                    this.updateUI();
                    return true;
                }}
                return false;
            }},
            
            recalculateCps: function() {{
                this.cookiesPs = 0;
                for (var name in this.Objects) {{
                    var obj = this.Objects[name];
                    this.cookiesPs += obj.amount * obj.baseCps;
                }}
            }},
            
            ClickCookie: function() {{
                var clickPower = 1;
                this.cookies += clickPower;
                this.cookiesEarned += clickPower;
                this.cookieClicks++;
                this.updateUI();
            }},
            
            Logic: function() {{
                if (this.cookiesPs > 0) {{
                    var production = this.cookiesPs / this.fps;
                    this.cookies += production;
                    this.cookiesEarned += production;
                    
                    // Track production per building
                    for (var name in this.Objects) {{
                        var obj = this.Objects[name];
                        if (obj.amount > 0) {{
                            var buildingProduction = (obj.amount * obj.baseCps) / this.fps;
                            obj.produced += buildingProduction;
                        }}
                    }}
                }}
            }},
            
            startGameLoop: function() {{
                var self = this;
                this.gameLoopInterval = setInterval(function() {{
                    self.Logic();
                    self.updateUI();
                }}, 1000 / self.fps);
            }},
            
            stopGameLoop: function() {{
                if (this.gameLoopInterval) {{
                    clearInterval(this.gameLoopInterval);
                    this.gameLoopInterval = null;
                }}
            }},
            
            updateUI: function() {{
                document.getElementById('cookiesDisplay').textContent = Math.floor(this.cookies);
                document.getElementById('cpsDisplay').textContent = this.cookiesPs.toFixed(1);
                document.getElementById('cookiesBaked').textContent = Math.floor(this.cookiesEarned);
                document.getElementById('handMadeCookies').textContent = this.cookieClicks;
                
                for (var name in this.Objects) {{
                    var obj = this.Objects[name];
                    var price = this.getPrice(name);
                    var affordable = this.cookies >= price;
                    var buildingDiv = document.getElementById('building_' + name);
                    if (buildingDiv) buildingDiv.className = 'building' + (affordable ? '' : ' unaffordable');
                    var costSpan = document.getElementById('cost_' + name);
                    if (costSpan) costSpan.textContent = Math.ceil(price);
                    var ownedSpan = document.getElementById('owned_' + name);
                    if (ownedSpan) ownedSpan.textContent = obj.amount;
                }}
            }},
            
            updateUIAfterCompletion: function() {{
                // Update building display to show production instead of cost
                for (var name in this.Objects) {{
                    var obj = this.Objects[name];
                    var info1 = document.getElementById('info1_' + name);
                    var info2 = document.getElementById('info2_' + name);
                    
                    if (info1 && obj.amount > 0) {{
                        info1.textContent = 'Produced: ' + obj.produced.toFixed(2) + ' cookies';
                        info1.style.color = '#FFD700';
                    }} else if (info1) {{
                        info1.textContent = 'Not purchased';
                        info1.style.color = '#666';
                    }}
                    
                    if (info2 && obj.amount > 0) {{
                        var totalCps = obj.amount * obj.baseCps;
                        info2.textContent = 'Total CPS: ' + totalCps.toFixed(1);
                        info2.style.color = '#88ccff';
                    }} else if (info2) {{
                        info2.textContent = '+' + obj.baseCps + ' cps (base)';
                        info2.style.color = '#666';
                    }}
                }}
            }},
            
            registerMod: function(name, mod) {{
                console.log('Registering mod: ' + name);
                mod.init();
            }}
        }};
        
        // TAS Controller
        var TASController = {{
            timeMs: 0,
            cookiesBaked: 0,
            cookiesFromClicks: 0,  // Track clicks separately
            lastClickTimeMs: -20,
            lastProductionFrame: -1,
            fps: 30,
            msPerFrame: 1000 / 30,
            automatedPath: null,
            automatedCurrentStep: 0,
            automatedRunning: false,
            realStartTime: 0,  // Track actual execution time
            
            init: function() {{
                this.updateDisplay();
            }},
            
            log: function(msg, type) {{
                // Only log important messages (not initialization)
                if (msg === 'TAS Controller initialized') return;
                if (msg.startsWith('Path loaded:')) return;
                
                var logDiv = document.getElementById('log');
                var entry = document.createElement('div');
                entry.className = type || '';
                entry.textContent = msg;
                logDiv.appendChild(entry);
                logDiv.scrollTop = logDiv.scrollHeight;
                console.log(msg);
            }},
            
            advanceOneMs: function() {{
                this.timeMs += 1;
                var currentFrame = Math.floor(this.timeMs / this.msPerFrame);
                if (currentFrame > this.lastProductionFrame && Game.cookiesPs > 0) {{
                    var productionThisFrame = Game.cookiesPs / this.fps;
                    Game.cookies += productionThisFrame;
                    this.cookiesBaked += productionThisFrame;
                    this.lastProductionFrame = currentFrame;
                    
                    // Track production per building
                    for (var name in Game.Objects) {{
                        var obj = Game.Objects[name];
                        if (obj.amount > 0) {{
                            var buildingProduction = (obj.amount * obj.baseCps) / this.fps;
                            obj.produced += buildingProduction;
                        }}
                    }}
                }}
                this.updateDisplay();
            }},
            
            clickCookie: function() {{
                if (this.timeMs - this.lastClickTimeMs < 20) {{
                    return false;
                }}
                var clickPower = 1;
                Game.cookies += clickPower;
                Game.cookiesEarned += clickPower;
                Game.cookieClicks++;  // Count this as a hand-made cookie
                this.cookiesBaked += clickPower;
                this.cookiesFromClicks += clickPower;  // Track clicks separately
                this.lastClickTimeMs = this.timeMs;
                Game.updateUI();
                this.updateDisplay();
                return true;
            }},
            
            buyBuilding: function(buildingName) {{
                var buildingMap = {{
                    'cursor': 'Cursor', 'grandma': 'Grandma', 'farm': 'Farm',
                    'mine': 'Mine', 'factory': 'Factory', 'bank': 'Bank',
                    'temple': 'Temple', 'wizard_tower': 'Wizard tower',
                    'shipment': 'Shipment', 'alchemy_lab': 'Alchemy lab'
                }};
                var jsName = buildingMap[buildingName] || buildingName;
                if (Game.Objects[jsName]) {{
                    return Game.Objects[jsName].buy();
                }}
                return false;
            }},
            
            updateDisplay: function() {{
                var seconds = (this.timeMs / 1000).toFixed(2);
                document.getElementById('tasTimeMs').textContent = 'Time: ' + this.timeMs + 'ms (' + seconds + 's)';
                document.getElementById('tasFrame').textContent = 'Frame: ' + Math.floor(this.timeMs / this.msPerFrame);
            }},
            
            loadAndExecutePath: function(path) {{
                this.automatedPath = path;
                this.automatedCurrentStep = 0;
                this.log('Path loaded: ' + path.length + ' actions', 'success');
            }},
            
            startAutomatedPlayback: function() {{
                if (!this.automatedPath || this.automatedPath.length === 0) {{
                    this.log('ERROR: No path loaded!', 'error');
                    return;
                }}
                
                document.getElementById('tasStatus').textContent = 'Status: Running...';
                
                // Hide the auto-execution message
                var msg = document.getElementById('autoExecMessage');
                if (msg) msg.style.display = 'none';
                
                // Track real execution start time
                this.realStartTime = Date.now();
                
                this.automatedRunning = true;
                this.automatedCurrentStep = 0;
                this.executeNextAction();
            }},
            
            executeNextAction: function() {{
                if (!this.automatedRunning || this.automatedCurrentStep >= this.automatedPath.length) {{
                    if (this.automatedRunning) {{
                        // Stop the game loop
                        Game.stopGameLoop();
                        
                        // Calculate real execution time
                        var realEndTime = Date.now();
                        var realElapsedMs = realEndTime - this.realStartTime;
                        var realElapsedSec = (realElapsedMs / 1000).toFixed(2);
                        
                        this.log('=== VERIFICATION COMPLETE ===', 'success');
                        var timeDiff = this.timeMs - EXPECTED_TIME;
                        this.log('Simulated time: ' + this.timeMs + 'ms (' + (this.timeMs/1000).toFixed(2) + 's)', 'success');
                        this.log('Expected time: ' + EXPECTED_TIME + 'ms | Diff: ' + timeDiff + 'ms ' + (Math.abs(timeDiff) < 10 ? '✓' : '⚠'), 
                                 Math.abs(timeDiff) < 10 ? 'success' : 'warning');
                        this.log('Program run time: ' + realElapsedSec + 's (' + this.automatedPath.length + ' actions)', 'success');
                        this.log('Cookies: ' + this.cookiesBaked.toFixed(1) + ' / ' + GOAL_COOKIES + ' goal', 'success');
                        this.log('Clicks: ' + this.cookiesFromClicks + ' | Production: ' + (this.cookiesBaked - this.cookiesFromClicks).toFixed(2), 'success');
                        
                        document.getElementById('tasStatus').textContent = 'Status: Complete ✓';
                        this.automatedRunning = false;
                        
                        // Update building display to show production
                        Game.updateUIAfterCompletion();
                        
                        // Show celebration message
                        var msg = document.getElementById('autoExecMessage');
                        if (msg) {{
                            msg.innerHTML = '🎉 Verification Complete! 🎉<br>BFS path successfully executed!';
                            msg.style.display = 'block';
                            msg.style.color = '#FFD700';
                        }}
                    }}
                    return;
                }}
                
                var self = this;
                var action = this.automatedPath[this.automatedCurrentStep];
                var actionType = action[0];
                var actionValue = action[1];
                
                if (this.automatedCurrentStep % 200 === 0) {{
                    var progress = Math.floor(this.automatedCurrentStep * 100 / this.automatedPath.length);
                    document.getElementById('tasStatus').textContent = 'Status: ' + progress + '% (' + 
                        this.automatedCurrentStep + '/' + this.automatedPath.length + ')';
                }}
                
                if (actionType === 'click') {{
                    this.clickCookie();
                }} else if (actionType === 'buy') {{
                    this.buyBuilding(actionValue);
                }} else if (actionType === 'wait') {{
                    this.advanceOneMs();
                }}
                
                this.automatedCurrentStep++;
                setTimeout(function() {{ self.executeNextAction(); }}, 0);
            }}
        }};
        
        // Initialize and auto-start
        window.addEventListener('load', function() {{
            // Analyze BFS path to find which buildings are used
            var buildingsUsed = [];
            var buildingsSeen = {{}};
            for (var i = 0; i < BFS_PATH.length; i++) {{
                if (BFS_PATH[i][0] === 'buy') {{
                    var buildingName = BFS_PATH[i][1];
                    // Map to JavaScript names
                    var buildingMap = {{
                        'cursor': 'Cursor',
                        'grandma': 'Grandma',
                        'farm': 'Farm',
                        'mine': 'Mine',
                        'factory': 'Factory',
                        'bank': 'Bank',
                        'temple': 'Temple',
                        'wizard_tower': 'Wizard tower',
                        'shipment': 'Shipment',
                        'alchemy_lab': 'Alchemy lab'
                    }};
                    var jsName = buildingMap[buildingName] || buildingName;
                    if (!buildingsSeen[jsName]) {{
                        buildingsSeen[jsName] = true;
                        buildingsUsed.push(jsName);
                    }}
                }}
            }}
            
            // Initialize game with only the buildings that are used
            Game.init(true);  // Skip automatic buildUI call
            Game.buildUI(buildingsUsed.length > 0 ? buildingsUsed : null);
            
            TASController.init();
            TASController.loadAndExecutePath(BFS_PATH);
            
            // Auto-start after 2 seconds
            setTimeout(function() {{
                TASController.startAutomatedPlayback();
            }}, 2000);
        }});
    </script>
</body>
</html>'''

# Write to file
with open('standalone_verification.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Created standalone_verification.html")
print(f"  File size: {len(html_content)} bytes")
print(f"\nJust open this file in your browser - no server needed!")
print(f"It will auto-execute the BFS path after 2 seconds.")
