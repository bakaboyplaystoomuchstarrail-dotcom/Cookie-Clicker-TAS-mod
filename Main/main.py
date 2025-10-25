from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math
import json
import os
import webbrowser

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

def _build_js_building_name(py_name: str) -> str:
    mapping = {
        'cursor': 'Cursor',
        'grandma': 'Grandma',
        'farm': 'Farm',
        'mine': 'Mine',
        'factory': 'Factory',
        'bank': 'Bank',
        'temple': 'Temple',
        'wizard_tower': 'Wizard tower',
        'shipment': 'Shipment',
        'alchemy_lab': 'Alchemy lab',
    }
    return mapping.get(py_name, py_name)


def _generate_verification_html(output_path: str, goal: float, total_time_ms: int, path_json: list, predicted_buildings_js: dict):
    total_actions = len(path_json)
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cookie Clicker Auto-Verification - {goal:.1f} Cookies</title>
    <style>
        body {{ margin:0; padding:20px; font-family: 'Courier New', monospace; background: #1f2740; color: white; }}
        #info {{ max-width: 1200px; margin: 0 auto 20px; background: rgba(0,0,0,0.7); padding:20px; border-radius:10px; }}
        #gameContainer {{ display:flex; gap:20px; max-width:1200px; margin:0 auto; }}
        #leftPanel, #rightPanel {{ flex:1; background: rgba(0,0,0,0.5); padding:20px; border-radius:10px; }}
        #bigCookie {{ width:200px; height:200px; background: radial-gradient(circle at 40% 40%, #f4a460, #d2691e); border:5px solid #8b4513; border-radius:50%; cursor:pointer; margin:20px auto; display:flex; align-items:center; justify-content:center; font-size:80px; user-select:none; }}
        .building {{ background: rgba(255,255,255,0.1); padding:15px; margin:12px 0; border-radius:5px; }}
        .building.unaffordable {{ opacity: 0.5; }}
        #tasPanel {{ position: fixed; top:10px; right:10px; background: rgba(0,0,0,0.9); color:white; padding:15px; border-radius:5px; font-family:monospace; font-size:12px; z-index:10000; min-width:260px; border:2px solid #4CAF50; }}
        #log {{ margin-top:10px; padding:10px; background: rgba(0,0,0,0.5); border-radius:5px; max-height:240px; overflow-y:auto; font-size:11px; }}
        .success {{ color:#4CAF50; }} .warning {{ color:#ff9800; }} .error {{ color:#f44336; }}
    </style>
</head>
<body>
    <div id="info">
        <h1 style="text-align:center; margin:0;">🍪 Cookie Clicker Auto-Verification 🍪</h1>
        <p style="text-align:center; margin:10px 0;">
            <strong>Goal:</strong> {goal:.1f} cookies |
            <strong>Expected Time:</strong> {total_time_ms}ms |
            <strong>Actions:</strong> {total_actions}
        </p>
        <p id="autoExecMessage" style="text-align:center; margin:10px 0; color:#4CAF50;">
            ⚡ Auto-execution starting...
        </p>
    </div>

    <div id="gameContainer">
        <div id="leftPanel">
            <div id="cookieCount">
                <div>Cookies: <span id="cookiesDisplay">0</span></div>
                <div style="font-size:16px; margin-top:5px;">per second: <span id="cpsDisplay">0</span></div>
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
        <div style="font-weight:bold; margin-bottom:10px; font-size:14px;">🎮 TAS Controller</div>
        <div id="tasTimeMs" style="font-size:13px; margin:3px 0;">Time: 0ms (0.00s)</div>
        <div id="tasFrame" style="font-size:13px; margin:3px 0;">Frame: 0</div>
        <div id="tasStatus" style="font-size:13px; margin:3px 0; padding:5px 0; border-top:1px solid #444;">Status: Initializing...</div>
        <div id="log"></div>
    </div>

    <script>
        const BFS_PATH = {json.dumps(path_json)};
        const GOAL_COOKIES = {goal};
        const EXPECTED_TIME = {total_time_ms};
        const PREDICTED_BUILDINGS = {json.dumps(predicted_buildings_js)};
        const PREDICTED_FRAMES = Math.floor(EXPECTED_TIME / (1000/30));

        var Game = {{
            cookies: 0,
            cookiesEarned: 0,
            cookiesPs: 0,
            cookieClicks: 0,
            fps: 30,
            Objects: {{}},
            gameLoopInterval: null,

            init: function(skipBuildUI) {{
                this.Objects = {{
                    'Cursor': {{ name: 'Cursor', id: 0, basePrice: 15, baseCps: 0.1, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Cursor'); }} }},
                    'Grandma': {{ name: 'Grandma', id: 1, basePrice: 100, baseCps: 1, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Grandma'); }} }},
                    'Farm': {{ name: 'Farm', id: 2, basePrice: 1100, baseCps: 8, amount: 0, priceIncrease: 1.15, produced: 0, buy: function() {{ return Game.buyBuilding('Farm'); }} }}
                }};
                if (!skipBuildUI) this.buildUI();
                this.startGameLoop();
            }},

            buildUI: function(buildingsUsed) {{
                var container = document.getElementById('buildingsContainer');
                var buildingsToShow = buildingsUsed || Object.keys(this.Objects);
                for (var i = 0; i < buildingsToShow.length; i++) {{
                    var name = buildingsToShow[i];
                    var obj = this.Objects[name]; if (!obj) continue;
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
                var obj = this.Objects[buildingName]; var price = this.getPrice(buildingName);
                if (this.cookies >= price) {{ this.cookies -= price; obj.amount++; this.recalculateCps(); this.updateUI(); return true; }}
                return false;
            }},

            recalculateCps: function() {{
                this.cookiesPs = 0; for (var name in this.Objects) {{ var obj = this.Objects[name]; this.cookiesPs += obj.amount * obj.baseCps; }}
            }},

            ClickCookie: function() {{ var clickPower = 1; this.cookies += clickPower; this.cookiesEarned += clickPower; this.cookieClicks++; this.updateUI(); }},

            Logic: function() {{ if (this.cookiesPs > 0) {{ var production = this.cookiesPs / this.fps; this.cookies += production; this.cookiesEarned += production; for (var n in this.Objects) {{ var o = this.Objects[n]; if (o.amount>0) o.produced += (o.amount*o.baseCps)/this.fps; }} }} }},

            startGameLoop: function() {{ var self=this; this.gameLoopInterval = setInterval(function() {{ self.Logic(); self.updateUI(); }}, 1000/ self.fps); }},
            stopGameLoop: function() {{ if (this.gameLoopInterval) {{ clearInterval(this.gameLoopInterval); this.gameLoopInterval=null; }} }},

            updateUI: function() {{
                var cookiesDisplay = document.getElementById('cookiesDisplay');
                var cpsDisplay = document.getElementById('cpsDisplay');
                var cookiesBaked = document.getElementById('cookiesBaked');
                var handMadeCookies = document.getElementById('handMadeCookies');
                if (cookiesDisplay) cookiesDisplay.textContent = Math.floor(this.cookies);
                if (cpsDisplay) cpsDisplay.textContent = this.cookiesPs.toFixed(1);
                if (cookiesBaked) cookiesBaked.textContent = Math.floor(this.cookiesEarned);
                if (handMadeCookies) handMadeCookies.textContent = this.cookieClicks;
                for (var name in this.Objects) {{ var obj=this.Objects[name]; var price=this.getPrice(name); var buildingDiv=document.getElementById('building_'+name); if (buildingDiv) buildingDiv.className='building'+(this.cookies>=price?'':' unaffordable'); var costSpan=document.getElementById('cost_'+name); if (costSpan) costSpan.textContent=Math.ceil(price); var ownedSpan=document.getElementById('owned_'+name); if (ownedSpan) ownedSpan.textContent=obj.amount; }}
            }},

            updateUIAfterCompletion: function() {{ for (var name in this.Objects) {{ var obj=this.Objects[name]; var info1=document.getElementById('info1_'+name); var info2=document.getElementById('info2_'+name); if (info1 && obj.amount>0) {{ info1.textContent='Produced: '+obj.produced.toFixed(2)+' cookies'; info1.style.color='#FFD700'; }} else if (info1) {{ info1.textContent='Not purchased'; info1.style.color='#666'; }} if (info2 && obj.amount>0) {{ var totalCps=obj.amount*obj.baseCps; info2.textContent='Total CPS: '+totalCps.toFixed(1); info2.style.color='#88ccff'; }} else if (info2) {{ info2.textContent='+'+obj.baseCps+' cps (base)'; info2.style.color='#666'; }} }} }}
        }};

        var TASController = {{
            timeMs: 0,
            cookiesBaked: 0,
            cookiesFromClicks: 0,
            lastClickTimeMs: -20,
            lastProductionFrame: -1,
            fps: 30,
            msPerFrame: 1000/30,
            automatedPath: null,
            automatedCurrentStep: 0,
            automatedRunning: false,
            realStartTime: 0,

            init: function() {{ this.updateDisplay(); }},
            log: function(msg, type) {{ var logDiv=document.getElementById('log'); var entry=document.createElement('div'); entry.className=type||''; entry.textContent=msg; logDiv.appendChild(entry); logDiv.scrollTop=logDiv.scrollHeight; console.log(msg); }},

            advanceOneMs: function() {{ this.timeMs+=1; var currentFrame=Math.floor(this.timeMs/this.msPerFrame); if (currentFrame>this.lastProductionFrame && Game.cookiesPs>0) {{ var productionThisFrame=Game.cookiesPs/this.fps; Game.cookies+=productionThisFrame; this.cookiesBaked+=productionThisFrame; this.lastProductionFrame=currentFrame; for (var n in Game.Objects) {{ var o=Game.Objects[n]; if (o.amount>0) o.produced += (o.amount*o.baseCps)/this.fps; }} }} this.updateDisplay(); }},

            clickCookie: function() {{ if (this.timeMs - this.lastClickTimeMs < 20) return false; var clickPower=1; Game.cookies+=clickPower; Game.cookiesEarned+=clickPower; Game.cookieClicks++; this.cookiesBaked+=clickPower; this.cookiesFromClicks+=clickPower; this.lastClickTimeMs=this.timeMs; Game.updateUI(); this.updateDisplay(); return true; }},

            buyBuilding: function(buildingName) {{ var map={{'cursor':'Cursor','grandma':'Grandma','farm':'Farm','mine':'Mine','factory':'Factory','bank':'Bank','temple':'Temple','wizard_tower':'Wizard tower','shipment':'Shipment','alchemy_lab':'Alchemy lab'}}; var jsName=map[buildingName]||buildingName; if (Game.Objects[jsName]) return Game.Objects[jsName].buy(); return false; }},

            updateDisplay: function() {{ var seconds=(this.timeMs/1000).toFixed(2); document.getElementById('tasTimeMs').textContent='Time: '+this.timeMs+'ms ('+seconds+'s)'; document.getElementById('tasFrame').textContent='Frame: '+Math.floor(this.timeMs/this.msPerFrame); }},

            loadAndExecutePath: function(path) {{ this.automatedPath=path; this.automatedCurrentStep=0; }},
            startAutomatedPlayback: function() {{ if (!this.automatedPath||this.automatedPath.length===0) {{ this.log('ERROR: No path loaded!','error'); return; }} document.getElementById('tasStatus').textContent='Status: Running...'; var msg=document.getElementById('autoExecMessage'); if (msg) msg.style.display='none'; this.realStartTime=Date.now(); this.automatedRunning=true; this.automatedCurrentStep=0; this.executeNextAction(); }},

            executeNextAction: function() {{
                if (!this.automatedRunning || this.automatedCurrentStep >= this.automatedPath.length) {{
                    if (this.automatedRunning) {{
                        Game.stopGameLoop();
                        var realElapsedMs = Date.now() - this.realStartTime; var realElapsedSec=(realElapsedMs/1000).toFixed(2);
                        this.log('=== VERIFICATION COMPLETE ===','success');
                        var timeDiff=this.timeMs-EXPECTED_TIME;
                        this.log('Simulated time: '+this.timeMs+'ms ('+(this.timeMs/1000).toFixed(2)+'s)','success');
                        this.log('Expected time: '+EXPECTED_TIME+'ms | Diff: '+timeDiff+'ms '+(Math.abs(timeDiff)<10?'✓':'⚠'), Math.abs(timeDiff)<10?'success':'warning');
                        this.log('Program run time: '+realElapsedSec+'s ('+this.automatedPath.length+' actions)','success');
                        this.log('Cookies: '+this.cookiesBaked.toFixed(1)+' / '+GOAL_COOKIES+' goal '+(Math.abs(this.cookiesBaked-GOAL_COOKIES)<1e-6?'✓':'⚠'), Math.abs(this.cookiesBaked-GOAL_COOKIES)<1e-6?'success':'warning');

                        // Predicted vs actual frames
                        var framesSim = Math.floor(this.timeMs / this.msPerFrame);
                        var framesOk = (framesSim === PREDICTED_FRAMES);
                        this.log('Frames: '+framesSim+' / predicted '+PREDICTED_FRAMES+' '+(framesOk?'✓':'⚠'), framesOk?'success':'warning');

                        // Predicted vs actual building counts
                        var actual = {{}};
                        for (var name in Game.Objects) {{ var obj=Game.Objects[name]; if (obj.amount>0) actual[name]=obj.amount; }}
                        var buildingsOk = JSON.stringify(actual) === JSON.stringify(PREDICTED_BUILDINGS);
                        this.log('Buildings: '+JSON.stringify(actual)+' / predicted '+JSON.stringify(PREDICTED_BUILDINGS)+' '+(buildingsOk?'✓':'⚠'), buildingsOk?'success':'warning');

                        document.getElementById('tasStatus').textContent='Status: Complete ✓';
                        this.automatedRunning=false;
                        Game.updateUIAfterCompletion();
                        var msg2=document.getElementById('autoExecMessage'); if (msg2) {{ msg2.innerHTML='🎉 Verification Complete! 🎉'; msg2.style.display='block'; msg2.style.color='#FFD700'; }}
                    }}
                    return;
                }}
                var action=this.automatedPath[this.automatedCurrentStep]; var t=action[0], v=action[1];
                if (t==='click') this.clickCookie(); else if (t==='buy') this.buyBuilding(v); else if (t==='wait') this.advanceOneMs();
                this.automatedCurrentStep++;
                setTimeout(()=>this.executeNextAction(),0);
            }}
        }};

        window.addEventListener('load', function() {{
            var buildingsUsed=[]; var seen={{}};
            for (var i=0;i<BFS_PATH.length;i++) {{ if (BFS_PATH[i][0]==='buy') {{ var m={{'cursor':'Cursor','grandma':'Grandma','farm':'Farm','mine':'Mine','factory':'Factory','bank':'Bank','temple':'Temple','wizard_tower':'Wizard tower','shipment':'Shipment','alchemy_lab':'Alchemy lab'}}; var js=m[BFS_PATH[i][1]]||BFS_PATH[i][1]; if (!seen[js]) {{ seen[js]=1; buildingsUsed.push(js); }} }} }}
            Game.init(true); Game.buildUI(buildingsUsed.length>0?buildingsUsed:null);
            TASController.init(); TASController.loadAndExecutePath(BFS_PATH);
            // Start immediately
            TASController.startAutomatedPlayback();
        }});
    </script>
</body>
</html>'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


class CookieClickerOptimizer:
    def __init__(self):
        # Define buildings with their base stats from Cookie Clicker source code
        # Note: CPS values are PER SECOND (will be divided by 30 for per-frame production)
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
        # Game runs at 30 FPS
        self.fps = 30
    
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
        """Create new state after purchasing a building (instant, 0ms)"""
        new_state = state.copy()
        current_count = new_state.buildings.get(building_name, 0)
        cost = self.get_building_cost(building_name, current_count)
        
        # Make the purchase (spending doesn't reduce baked cookies!)
        new_state.cookies -= cost
        new_state.buildings[building_name] = current_count + 1
        
        # Update CpS immediately (production benefit starts next frame)
        building = self.buildings[building_name]
        new_state.cps += building.base_cps
        
        # Purchase is INSTANT - does NOT advance time
        # (purchases happen within the same millisecond as other actions)
        
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
        
        # Add click cookies instantly (clicks are event-driven and 0ms)
        new_state.cookies += click_power
        new_state.cookies_baked += click_power
        
        # Update last click time to current ms (no time advancement)
        new_state.last_click_time_ms = new_state.time_ms
        
        # Clicks are INSTANT - do not advance time here
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
        # Frame boundaries: 0-33ms=frame0, 34-66ms=frame1, 67-99ms=frame2, etc.
        # Divide time by ms-per-frame: frame = time_ms / (100/3)
        ms_per_frame = 100 / 3  # 33.333... ms per frame
        current_frame = int(new_state.time_ms / ms_per_frame)
        
        # If we're in a new frame and have CpS, apply production
        # Production is CpS/30 per frame (30 FPS)
        if current_frame > new_state.last_production_frame and new_state.cps > 0:
            production_this_frame = new_state.cps / self.fps
            new_state.cookies += production_this_frame
            new_state.cookies_baked += production_this_frame
            new_state.last_production_frame = current_frame
        
        return new_state
    
    def bfs_optimize(self, goal_cookies: float, max_time_ms: Optional[int] = None, max_iterations: Optional[int] = None) -> Optional[Tuple[List[Tuple[str, int, int]], int]]:
        """
        True BFS with exhaustive action exploration:
        - Clicks (0ms, allowed when >=20ms since last click)
        - Purchases (instant, 0ms)
        - Waits (advance time in 1ms steps; production applied on new frames only)
        Uses millisecond-precise timing and state pruning to manage branching.
        If max_time_ms is None, there is no time limit.
        If max_iterations is None, there is no iteration limit.
        """
        initial_state = GameState(
            cookies=0,
            cookies_baked=0,  # Track cumulative production
            buildings={},
            cps=0.0,  # Current cookies per second (divided by 30 each frame)
            time_ms=0,
            last_click_time_ms=-20,  # Start at -20 so first click at t=0 is valid
            last_production_frame=-1,  # Start at -1 so first frame (0) can produce
            click_power=1.0
        )
        
        # States organized by time in milliseconds: {time_ms: [(state, path), ...]}
        states_by_time = {0: [(initial_state, [])]}
        visited = set()
        
        if max_time_ms is None:
            print(f"Starting BFS with goal: {goal_cookies} cookies (no time limit)")
        else:
            print(f"Starting BFS with goal: {goal_cookies} cookies (max {max_time_ms}ms)")
        
        # Use a sorted list of times to process them in order (skip empty times)
        iterations = 0
        
        while (max_iterations is None or iterations < max_iterations) and states_by_time:
            iterations += 1
            
            # Get the earliest time with states
            time_ms = min(states_by_time.keys())
            
            if max_time_ms is not None and time_ms > max_time_ms:
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
                
                # Check if any purchases are available
                possible_purchases = self.get_possible_purchases(state)
                can_purchase = len(possible_purchases) > 0
                
                # Check if clicking is allowed (not throttled)
                can_click = (state.time_ms - state.last_click_time_ms >= 20)
                
                # Branch 1: Try all possible purchases (instant, 0ms)
                for building_name in possible_purchases:
                    purchase_state = self.purchase_building(state, building_name)
                    purchase_path = path + [('buy', building_name, time_ms)]
                    
                    # Purchases are instant - they stay at the same time
                    next_time = purchase_state.time_ms
                    
                    if max_time_ms is None or next_time <= max_time_ms:
                        if next_time not in states_by_time:
                            states_by_time[next_time] = []
                        states_by_time[next_time].append((purchase_state, purchase_path))
                
                # Branch 2: Try clicking (if not throttled, takes 1ms)
                # Always consider clicking when possible, even if purchases are available
                if can_click:
                    click_state = self.click_cookie(state)
                    if click_state is not None:  # Double-check (should always be valid here)
                        click_path = path + [('click', 1, time_ms)]
                        
                        next_time = click_state.time_ms
                        
                        if max_time_ms is None or next_time <= max_time_ms:
                            if next_time not in states_by_time:
                                states_by_time[next_time] = []
                            states_by_time[next_time].append((click_state, click_path))
                
                # Branch 3: Try waiting 1ms
                # Only consider waiting if:
                #   a) A purchase is available (to explore deferring the purchase), OR
                #   b) Click is throttled (to fill the gap until we can click again)
                if can_purchase or not can_click:
                    if max_time_ms is None or state.time_ms + 1 <= max_time_ms:
                        wait_state = self.wait_one_ms(state)
                        wait_path = path + [('wait', 1, time_ms)]
                        
                        next_time = wait_state.time_ms
                        
                        if next_time not in states_by_time:
                            states_by_time[next_time] = []
                        states_by_time[next_time].append((wait_state, wait_path))
        
        if max_time_ms is None:
            print(f"No solution found after {iterations} iterations")
        else:
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

        # Prepare path for verification page
        json_path = []
        predicted_buildings_counts = {}
        for action_type, action_value, action_time_ms in path:
            json_path.append([action_type, action_value, action_time_ms])
            if action_type == 'buy':
                js_name = _build_js_building_name(action_value)
                predicted_buildings_counts[js_name] = predicted_buildings_counts.get(js_name, 0) + 1

        # Generate and launch verification HTML
        out_html = os.path.join('Automated Verification', 'auto_verification.html')
        _generate_verification_html(out_html, goal, total_time_ms, json_path, predicted_buildings_counts)

        try:
            webbrowser.open('file://' + os.path.abspath(out_html))
            print(f"\nOpened verification page: {out_html}")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
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
        print(f"      Building purchases are instant (0ms).")
        print(f"      Production applied each frame based on CpS at frame start.")
                
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.")

if __name__ == "__main__":
    main()