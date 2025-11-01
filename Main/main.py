from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import math
import json
import os
import webbrowser
import subprocess
import sys

@dataclass
class Building:
    name: str
    id: int
    base_cost: float
    base_cps: float  # cookies per second
    cost_multiplier: float = 1.15

@dataclass
class Upgrade:
    name: str
    cost: float
    upgrade_type: str  # 'tiered', 'cookie', 'kitten', 'grandma_synergy', 'research', 'mouse', 'special'
    building_tie: Optional[str] = None  # Which building this upgrade affects (None for global)
    tier: int = 0  # Tier level (1, 2, 3, etc.)
    unlock_requirement: int = 0  # Number of buildings required to unlock
    power: float = 0.0  # Power multiplier for cookie upgrades
    affects_click_power: bool = False  # Whether this upgrade affects click power
    is_thousand_fingers: bool = False  # Special flag for Thousand Fingers upgrade
    is_grandma_synergy: bool = False  # Special flag for grandma synergy upgrades
    special_unlock_condition: Optional[str] = None  # e.g., "requires_grandmapocalypse", "requires_research"

@dataclass
class GameState:
    cookies: float  # current cookies in bank
    cookies_baked: float  # cumulative cookies produced (the actual goal!)
    buildings: dict  # building_name -> count
    cps: float  # current cookies per second (divided by 30 each frame)
    time_ms: int  # current time in milliseconds (not frames)
    last_click_time_ms: int  # time of last click in milliseconds
    last_production_frame: int  # last frame where production was applied
    click_power: float  # current click value
    deferred_options: set = field(default_factory=set)  # set of (building, qty) deferred until next purchase
    upgrades: set = field(default_factory=set)  # set of upgrade names that have been purchased
    
    def copy(self):
        return GameState(
            cookies=self.cookies,
            cookies_baked=self.cookies_baked,
            buildings=self.buildings.copy(),
            cps=self.cps,
            time_ms=self.time_ms,
            last_click_time_ms=self.last_click_time_ms,
            last_production_frame=self.last_production_frame,
            click_power=self.click_power,
            deferred_options=set(self.deferred_options),
            upgrades=set(self.upgrades)
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
                <div id="cpsLabel" style="font-size:16px; margin-top:5px;">Cookies Produced Per Second: <span id="cpsDisplay">0</span></div>
            </div>
            <div id="bigCookie">🍪</div>
            <div id="stats">
                <div><strong>Statistics</strong></div>
                <div>Cookies baked: <span id="cookiesBaked">0</span></div>
                <div>Hand-made cookies: <span id="handMadeCookies">0</span></div>
                <div>Production cookies: <span id="productionCookies">0</span></div>
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
                                    '<div id="info2_' + name + '">Total CPS: 0.0</div>';
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
                var prodEl = document.getElementById('productionCookies');
                if (prodEl) {{ var producedTotal = 0; for (var n in this.Objects) {{ var o=this.Objects[n]; if (o && o.produced) producedTotal += o.produced; }} prodEl.textContent = producedTotal.toFixed(1); }}
                for (var name in this.Objects) {{ var obj=this.Objects[name]; var price=this.getPrice(name); var buildingDiv=document.getElementById('building_'+name); if (buildingDiv) buildingDiv.className='building'+(this.cookies>=price?'':' unaffordable'); var costSpan=document.getElementById('cost_'+name); if (costSpan) costSpan.textContent=price; var ownedSpan=document.getElementById('owned_'+name); if (ownedSpan) ownedSpan.textContent=obj.amount; var info2=document.getElementById('info2_'+name); if (info2) {{ var totalCps=(obj.amount*obj.baseCps).toFixed(1); info2.textContent='Total CPS: '+totalCps; }} }}
            }},

            updateUIAfterCompletion: function() {{ var cpsLabel=document.getElementById('cpsLabel'); if (cpsLabel) {{ cpsLabel.innerHTML='Final CPS: <span id="cpsDisplay">'+this.cookiesPs.toFixed(1)+'</span>'; }} for (var name in this.Objects) {{ var obj=this.Objects[name]; var info1=document.getElementById('info1_'+name); var info2=document.getElementById('info2_'+name); if (info1 && obj.amount>0) {{ info1.textContent='Produced: '+obj.produced.toFixed(2)+' cookies'; info1.style.color='#FFD700'; }} else if (info1) {{ info1.textContent='Not purchased'; info1.style.color='#666'; }} if (info2 && obj.amount>0) {{ var totalCps=obj.amount*obj.baseCps; info2.textContent='Final Total CPS: '+totalCps.toFixed(1); info2.style.color='#88ccff'; }} else if (info2) {{ info2.textContent='+'+obj.baseCps+' cps (base)'; info2.style.color='#666'; }} }} }}
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

            advanceOneMs: function() {{ this.timeMs+=1; var currentFrame=Math.floor(this.timeMs/this.msPerFrame); if (currentFrame>this.lastProductionFrame && Game.cookiesPs>0) {{ var productionThisFrame=Game.cookiesPs/this.fps; Game.cookies+=productionThisFrame; Game.cookiesEarned+=productionThisFrame; this.cookiesBaked+=productionThisFrame; this.lastProductionFrame=currentFrame; for (var n in Game.Objects) {{ var o=Game.Objects[n]; if (o.amount>0) o.produced += (o.amount*o.baseCps)/this.fps; }} }} this.autoClick(); Game.updateUI(); this.updateDisplay(); }},

            autoClick: function() {{ if (this.timeMs % 20 === 0 && this.timeMs !== this.lastClickTimeMs) {{ var clickPower=1; Game.cookies+=clickPower; Game.cookiesEarned+=clickPower; Game.cookieClicks++; this.cookiesBaked+=clickPower; this.cookiesFromClicks+=clickPower; this.lastClickTimeMs=this.timeMs; }} }},

            clickCookie: function() {{ if (this.timeMs - this.lastClickTimeMs < 20) return false; var clickPower=1; Game.cookies+=clickPower; Game.cookiesEarned+=clickPower; Game.cookieClicks++; this.cookiesBaked+=clickPower; this.cookiesFromClicks+=clickPower; this.lastClickTimeMs=this.timeMs; Game.updateUI(); this.updateDisplay(); return true; }},

            buyBuilding: function(buildingName) {{ var map={{'cursor':'Cursor','grandma':'Grandma','farm':'Farm','mine':'Mine','factory':'Factory','bank':'Bank','temple':'Temple','wizard_tower':'Wizard tower','shipment':'Shipment','alchemy_lab':'Alchemy lab'}}; var jsName=map[buildingName]||buildingName; if (Game.Objects[jsName]) return Game.Objects[jsName].buy(); return false; }},

            updateDisplay: function() {{ var seconds=(this.timeMs/1000).toFixed(2); document.getElementById('tasTimeMs').textContent='Time: '+this.timeMs+'ms ('+seconds+'s)'; document.getElementById('tasFrame').textContent='Frame: '+Math.floor(this.timeMs/this.msPerFrame); }},

            loadAndExecutePath: function(path) {{ this.automatedPath=path; this.automatedCurrentStep=0; }},
            startAutomatedPlayback: function() {{ document.getElementById('tasStatus').textContent='Status: Running...'; var msg=document.getElementById('autoExecMessage'); if (msg) msg.style.display='none'; Game.stopGameLoop(); this.realStartTime=Date.now(); this.automatedRunning=true; this.automatedCurrentStep=0; this.executeNextAction(); }},

            executeNextAction: function() {{
                // Check if we've processed all actions
                if (this.automatedCurrentStep >= this.automatedPath.length) {{
                    // Check for initial click at current time (before any advancement)
                    this.autoClick();
                    
                    // Advance through all time up to the expected time
                    while (this.timeMs < EXPECTED_TIME) {{
                        this.advanceOneMs();
                    }}
                    
                    // We've reached the expected time - complete verification
                    if (this.automatedRunning) {{
                        Game.stopGameLoop();
                        var realElapsedMs = Date.now() - this.realStartTime; var realElapsedSec=(realElapsedMs/1000).toFixed(2);
                        this.log('=== VERIFICATION COMPLETE ===','success');
                        var timeDiff=this.timeMs-EXPECTED_TIME;
                        this.log('Simulated time: '+this.timeMs+'ms ('+(this.timeMs/1000).toFixed(2)+'s)','success');
                        this.log('Expected time: '+EXPECTED_TIME+'ms | Diff: '+timeDiff+'ms '+(Math.abs(timeDiff)<10?'✓':'⚠'), Math.abs(timeDiff)<10?'success':'warning');
                        this.log('Program run time: '+realElapsedSec+'s ('+this.automatedPath.length+' purchase actions)','success');
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
                
                var action=this.automatedPath[this.automatedCurrentStep];
                
                // Handle RLE-compressed format: [count, 'buy', building, time]
                var count = 1, actionType, actionValue, actionTime;
                if (typeof action[0] === 'number') {{
                    // RLE format
                    count = action[0];
                    actionType = action[1];
                    actionValue = action[2];
                    actionTime = action[3];
                }} else {{
                    // Legacy format: ['buy', building, time]
                    actionType = action[0];
                    actionValue = action[1];
                    actionTime = action[2];
                }}
                
                // Advance time to the action's timestamp (auto-clicking and production happen automatically)
                // Process the current time first (clicks/production at current moment)
                if (this.timeMs === 0 && actionTime > 0) {{
                    // Special case: process time 0 before advancing
                    this.autoClick();
                }}
                
                // Then advance millisecond-by-millisecond to the action time
                while (this.timeMs < actionTime) {{
                    this.advanceOneMs();
                }}
                
                // Execute the purchase action(s) (clicks are automatic, not in path)
                if (actionType==='buy') {{
                    for (var i = 0; i < count; i++) {{
                        this.buyBuilding(actionValue);
                    }}
                }}
                
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
        
        # Define upgrades from Cookie Clicker source code
        self.upgrades = self._initialize_upgrades()
        
        # Price increase multiplier from source: Game.priceIncrease (usually 1.15)
        self.price_increase = 1.15
        # Game runs at 30 FPS
        self.fps = 30
        # Allowed bulk purchase quantities
        self.purchase_quantities = [1, 10, 100]
        # Milliseconds per frame at 30 FPS
        self.ms_per_frame = 100 / 3
    
    def _initialize_upgrades(self) -> dict:
        """Initialize all upgrades from Cookie Clicker source code."""
        upgrades = {}
        
        # ===== CURSOR UPGRADES (Tiered) =====
        # Tiers 1-3: Double mouse and cursor efficiency
        upgrades['reinforced_index_finger'] = Upgrade('reinforced_index_finger', 100, 'tiered', 'cursor', 1, 1, 0, True, False)
        upgrades['carpal_tunnel_prevention_cream'] = Upgrade('carpal_tunnel_prevention_cream', 500, 'tiered', 'cursor', 2, 1, 0, True, False)
        upgrades['ambidextrous'] = Upgrade('ambidextrous', 10000, 'tiered', 'cursor', 3, 10, 0, True, False)
        
        # Tier 4+: Thousand Fingers variants
        upgrades['thousand_fingers'] = Upgrade('thousand_fingers', 100000, 'tiered', 'cursor', 4, 25, 0, True, True)
        upgrades['million_fingers'] = Upgrade('million_fingers', 10000000, 'tiered', 'cursor', 5, 50, 0, True, True)
        upgrades['billion_fingers'] = Upgrade('billion_fingers', 100000000, 'tiered', 'cursor', 6, 100, 0, True, True)
        upgrades['trillion_fingers'] = Upgrade('trillion_fingers', 1000000000, 'tiered', 'cursor', 7, 150, 0, True, True)
        upgrades['quadrillion_fingers'] = Upgrade('quadrillion_fingers', 10000000000, 'tiered', 'cursor', 8, 200, 0, True, True)
        upgrades['quintillion_fingers'] = Upgrade('quintillion_fingers', 10000000000000, 'tiered', 'cursor', 9, 250, 0, True, True)
        
        # ===== GRANDMA UPGRADES (Tiered) =====
        upgrades['forwards_from_grandma'] = Upgrade('forwards_from_grandma', 1000, 'tiered', 'grandma', 1, 1)
        upgrades['steel_plated_rolling_pins'] = Upgrade('steel_plated_rolling_pins', 5000, 'tiered', 'grandma', 2, 5)
        upgrades['lubricated_dentures'] = Upgrade('lubricated_dentures', 50000, 'tiered', 'grandma', 3, 25)
        upgrades['prune_juice'] = Upgrade('prune_juice', 5000000, 'tiered', 'grandma', 4, 50)
        
        # ===== FARM UPGRADES (Tiered) =====
        upgrades['cheap_hoes'] = Upgrade('cheap_hoes', 11000, 'tiered', 'farm', 1, 1)
        upgrades['fertilizer'] = Upgrade('fertilizer', 55000, 'tiered', 'farm', 2, 5)
        upgrades['cookie_trees'] = Upgrade('cookie_trees', 550000, 'tiered', 'farm', 3, 25)
        upgrades['genetically_modified_cookies'] = Upgrade('genetically_modified_cookies', 55000000, 'tiered', 'farm', 4, 50)
        
        # ===== MINE UPGRADES (Tiered) =====
        upgrades['sugar_gas'] = Upgrade('sugar_gas', 120000, 'tiered', 'mine', 1, 1)
        upgrades['megadrill'] = Upgrade('megadrill', 600000, 'tiered', 'mine', 2, 5)
        upgrades['ultradrill'] = Upgrade('ultradrill', 6000000, 'tiered', 'mine', 3, 25)
        upgrades['ultimadrill'] = Upgrade('ultimadrill', 600000000, 'tiered', 'mine', 4, 50)
        
        # ===== FACTORY UPGRADES (Tiered) =====
        upgrades['sturdier_conveyor_belts'] = Upgrade('sturdier_conveyor_belts', 1300000, 'tiered', 'factory', 1, 1)
        upgrades['child_labor'] = Upgrade('child_labor', 6500000, 'tiered', 'factory', 2, 5)
        upgrades['sweatshop'] = Upgrade('sweatshop', 65000000, 'tiered', 'factory', 3, 25)
        upgrades['radium_reactors'] = Upgrade('radium_reactors', 6500000000, 'tiered', 'factory', 4, 50)
        
        # ===== BANK UPGRADES (Tiered) =====
        upgrades['taller_tellers'] = Upgrade('taller_tellers', 14000000, 'tiered', 'bank', 1, 1)
        upgrades['scissor_resistant_credit_cards'] = Upgrade('scissor_resistant_credit_cards', 70000000, 'tiered', 'bank', 2, 5)
        upgrades['acid_proof_vaults'] = Upgrade('acid_proof_vaults', 700000000, 'tiered', 'bank', 3, 25)
        upgrades['chocolate_coins'] = Upgrade('chocolate_coins', 70000000000, 'tiered', 'bank', 4, 50)
        
        # ===== TEMPLE UPGRADES (Tiered) =====
        upgrades['golden_idols'] = Upgrade('golden_idols', 200000000, 'tiered', 'temple', 1, 1)
        upgrades['sacrifices'] = Upgrade('sacrifices', 1000000000, 'tiered', 'temple', 2, 5)
        upgrades['delicious_blessing'] = Upgrade('delicious_blessing', 10000000000, 'tiered', 'temple', 3, 25)
        upgrades['sun_festival'] = Upgrade('sun_festival', 1000000000000, 'tiered', 'temple', 4, 50)
        
        # ===== WIZARD TOWER UPGRADES (Tiered) =====
        upgrades['pointier_hats'] = Upgrade('pointier_hats', 3300000000, 'tiered', 'wizard_tower', 1, 1)
        upgrades['beardlier_beards'] = Upgrade('beardlier_beards', 16500000000, 'tiered', 'wizard_tower', 2, 5)
        upgrades['ancient_tablet'] = Upgrade('ancient_tablet', 165000000000, 'tiered', 'wizard_tower', 3, 25)
        upgrades['insane_oatling_workers'] = Upgrade('insane_oatling_workers', 16500000000000, 'tiered', 'wizard_tower', 4, 50)
        
        # ===== SHIPMENT UPGRADES (Tiered) =====
        upgrades['vanilla_nebulae'] = Upgrade('vanilla_nebulae', 51000000000, 'tiered', 'shipment', 1, 1)
        upgrades['wormholes'] = Upgrade('wormholes', 255000000000, 'tiered', 'shipment', 2, 5)
        upgrades['frequent_flyer'] = Upgrade('frequent_flyer', 2550000000000, 'tiered', 'shipment', 3, 25)
        upgrades['warp_drive'] = Upgrade('warp_drive', 255000000000000, 'tiered', 'shipment', 4, 50)
        
        # ===== ALCHEMY LAB UPGRADES (Tiered) =====
        upgrades['antimony'] = Upgrade('antimony', 750000000000, 'tiered', 'alchemy_lab', 1, 1)
        upgrades['essence_of_dough'] = Upgrade('essence_of_dough', 3750000000000, 'tiered', 'alchemy_lab', 2, 5)
        upgrades['true_chocolate'] = Upgrade('true_chocolate', 37500000000000, 'tiered', 'alchemy_lab', 3, 25)
        upgrades['ambrosia'] = Upgrade('ambrosia', 3750000000000000, 'tiered', 'alchemy_lab', 4, 50)
        
        # ===== COOKIE UPGRADES (Global CpS multipliers) =====
        # Power=1 means +1% global CpS, power=2 means +2%, etc.
        upgrades['plain_cookies'] = Upgrade('plain_cookies', 999999, 'cookie', None, 0, 0, 1)
        upgrades['sugar_cookies'] = Upgrade('sugar_cookies', 999999*5, 'cookie', None, 0, 0, 1)
        upgrades['oatmeal_raisin_cookies'] = Upgrade('oatmeal_raisin_cookies', 9999999, 'cookie', None, 0, 0, 1)
        upgrades['peanut_butter_cookies'] = Upgrade('peanut_butter_cookies', 9999999*5, 'cookie', None, 0, 0, 2)
        upgrades['coconut_cookies'] = Upgrade('coconut_cookies', 99999999, 'cookie', None, 0, 0, 2)
        upgrades['white_chocolate_cookies'] = Upgrade('white_chocolate_cookies', 99999999*5, 'cookie', None, 0, 0, 2)
        upgrades['macadamia_nut_cookies'] = Upgrade('macadamia_nut_cookies', 99999999, 'cookie', None, 0, 0, 2)
        
        # ===== KITTEN UPGRADES (Global CpS multipliers based on milk) =====
        # Note: Milk calculation not implemented yet - placeholder for now
        upgrades['kitten_helpers'] = Upgrade('kitten_helpers', 9000000, 'kitten', None, 1, 0, 0, False, False, False, 'requires_milk_calculation')
        upgrades['kitten_workers'] = Upgrade('kitten_workers', 9000000000, 'kitten', None, 2, 0, 0, False, False, False, 'requires_milk_calculation')
        upgrades['kitten_engineers'] = Upgrade('kitten_engineers', 90000000000000, 'kitten', None, 3, 0, 0, False, False, False, 'requires_milk_calculation')
        
        # ===== GRANDMA SYNERGY UPGRADES =====
        # These make grandmas 2x efficient AND give grandmas +1% CpS per synergy building
        upgrades['farmer_grandmas'] = Upgrade('farmer_grandmas', 55000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['miner_grandmas'] = Upgrade('miner_grandmas', 600000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['worker_grandmas'] = Upgrade('worker_grandmas', 6500000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['banker_grandmas'] = Upgrade('banker_grandmas', 70000000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['priestess_grandmas'] = Upgrade('priestess_grandmas', 1000000000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['witch_grandmas'] = Upgrade('witch_grandmas', 16500000000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['cosmic_grandmas'] = Upgrade('cosmic_grandmas', 255000000000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        upgrades['transmuted_grandmas'] = Upgrade('transmuted_grandmas', 3750000000000, 'grandma_synergy', 'grandma', 0, 1, 0, False, False, True)
        
        # ===== MOUSE/CLICKING UPGRADES =====
        upgrades['plastic_mouse'] = Upgrade('plastic_mouse', 50000, 'mouse', None, 1, 0, 0, True)
        upgrades['iron_mouse'] = Upgrade('iron_mouse', 5000000, 'mouse', None, 2, 0, 0, True)
        upgrades['titanium_mouse'] = Upgrade('titanium_mouse', 500000000, 'mouse', None, 3, 0, 0, True)
        upgrades['adamantium_mouse'] = Upgrade('adamantium_mouse', 50000000000, 'mouse', None, 4, 0, 0, True)
        
        # ===== RESEARCH/TECH TREE UPGRADES =====
        # Note: These require Bingo Center and progressive unlocking
        upgrades['bingo_center'] = Upgrade('bingo_center', 1000000000000000, 'research', 'grandma', 0, 15, 0, False, False, False, 'requires_15_grandmas')
        upgrades['specialized_chocolate_chips'] = Upgrade('specialized_chocolate_chips', 1000000000000000, 'research', None, 0, 0, 1, False, False, False, 'requires_bingo_center')
        upgrades['designer_cocoa_beans'] = Upgrade('designer_cocoa_beans', 2000000000000000, 'research', None, 0, 0, 2, False, False, False, 'requires_bingo_center')
        upgrades['ritual_rolling_pins'] = Upgrade('ritual_rolling_pins', 4000000000000000, 'research', 'grandma', 0, 0, 0, False, False, False, 'requires_bingo_center')
        upgrades['underworld_ovens'] = Upgrade('underworld_ovens', 8000000000000000, 'research', None, 0, 0, 3, False, False, False, 'requires_bingo_center')
        upgrades['one_mind'] = Upgrade('one_mind', 16000000000000000, 'research', 'grandma', 0, 0, 0, False, False, False, 'requires_bingo_center_and_starts_grandmapocalypse')
        upgrades['exotic_nuts'] = Upgrade('exotic_nuts', 32000000000000000, 'research', None, 0, 0, 4, False, False, False, 'requires_bingo_center')
        upgrades['communal_brainsweep'] = Upgrade('communal_brainsweep', 64000000000000000, 'research', 'grandma', 0, 0, 0, False, False, False, 'requires_bingo_center')
        upgrades['arcane_sugar'] = Upgrade('arcane_sugar', 128000000000000000, 'research', None, 0, 0, 5, False, False, False, 'requires_bingo_center')
        
        # ===== SPECIAL UPGRADES =====
        # Elder Pledge/Covenant - requires grandmapocalypse
        upgrades['elder_pledge'] = Upgrade('elder_pledge', 1, 'special', None, 0, 0, 0, False, False, False, 'requires_grandmapocalypse_active')
        upgrades['elder_covenant'] = Upgrade('elder_covenant', 66666666666666, 'special', None, 0, 0, 0, False, False, False, 'requires_elder_pledge_purchased')
        
        return upgrades
    
    def is_upgrade_unlocked(self, upgrade_name: str, state: GameState) -> bool:
        """Check if an upgrade is unlocked based on building requirements."""
        upgrade = self.upgrades[upgrade_name]
        # Check if already purchased
        if upgrade_name in state.upgrades:
            return False
        # Check building requirement
        building_count = state.buildings.get(upgrade.building_tie, 0)
        return building_count >= upgrade.unlock_requirement
    
    def get_upgrade_cost(self, upgrade_name: str) -> float:
        """Get the cost of an upgrade."""
        return self.upgrades[upgrade_name].cost
    
    def get_building_cost(self, building_name: str, current_count: int) -> float:
        """Calculate cost of next building using Cookie Clicker formula"""
        building = self.buildings[building_name]
        # From source: price = basePrice * pow(Game.priceIncrease, max(0, amount-free))
        # We assume no free buildings, so it's basePrice * pow(1.15, amount)
        return math.ceil(building.base_cost * (self.price_increase ** current_count))
    
    def cost_for_quantity(self, building_name: str, current_count: int, qty: int) -> int:
        """Sum of sequential costs for buying qty units starting from current_count."""
        total = 0
        for k in range(qty):
            total += self.get_building_cost(building_name, current_count + k)
        return total
    
    def max_affordable_qty_by_goal(self, building_name: str, start_count: int, goal_cookies: float) -> int:
        """Maximum quantity (>=0) such that cumulative cost from start_count does not exceed goal_cookies."""
        total = 0
        qty = 0
        # Geometric growth ensures this loop is small for realistic goals
        while True:
            price = self.get_building_cost(building_name, start_count + qty)
            if total + price > goal_cookies:
                break
            total += price
            qty += 1
        return qty
    
    def purchase_multiple(self, state: GameState, building_name: str, qty: int) -> Optional[GameState]:
        new_state = state.copy()
        for _ in range(qty):
            # Guard affordability to avoid rounding mismatches
            curr_count = new_state.buildings.get(building_name, 0)
            price = self.get_building_cost(building_name, curr_count)
            if new_state.cookies + 1e-9 < price:
                return None
            # Perform single purchase
            new_state = self.purchase_building(new_state, building_name)
        
        # Remove deferred options only for the building type we just purchased
        # Keep other building types deferred
        new_state.deferred_options = {opt for opt in new_state.deferred_options if opt[0] != building_name}
        return new_state
    
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
        
        # Recalculate total CPS with multiplicative upgrade bonuses
        new_state.cps = self.calculate_total_cps(new_state)
        
        # Purchase is INSTANT - does NOT advance time
        # (purchases happen within the same millisecond as other actions)
        
        # Update click power if necessary:
        # - Building purchases only affect click power if "Thousand Fingers" upgrade is active
        #   (Thousand Fingers makes click power scale with non-cursor buildings)
        # - Note: Cursor UPGRADES (not buildings) always affect click power, but those are handled separately
        if 'thousand_fingers' in new_state.upgrades:
            new_state.click_power = self.calculate_click_power(new_state)
        
        return new_state
    
    def purchase_upgrade(self, state: GameState, upgrade_name: str) -> GameState:
        """Create new state after purchasing an upgrade (instant, 0ms)"""
        new_state = state.copy()
        upgrade = self.upgrades[upgrade_name]
        
        # Make the purchase
        new_state.cookies -= upgrade.cost
        new_state.upgrades.add(upgrade_name)
        
        # Recalculate total CPS (upgrades are multiplicative)
        new_state.cps = self.calculate_total_cps(new_state)
        
        # Recalculate click power if this upgrade affects it
        if upgrade.affects_click_power:
            new_state.click_power = self.calculate_click_power(new_state)
        
        return new_state
    
    def calculate_total_cps(self, state: GameState) -> float:
        """Calculate total CPS with multiplicative upgrade bonuses.
        From source: CPS = base_cps * 2^(tier_upgrades_owned) per building type"""
        total_cps = 0.0
        
        for building_name, count in state.buildings.items():
            if count == 0:
                continue
            
            building = self.buildings[building_name]
            base_cps = building.base_cps
            
            # Count how many tier upgrades are owned for this building
            # Each tier upgrade doubles the CPS: 2^(upgrades_owned)
            tier_mult = 1.0
            for upgrade_name, upgrade in self.upgrades.items():
                if upgrade.building_tie == building_name and upgrade_name in state.upgrades:
                    # Don't count Thousand Fingers variants as tier upgrades for CPS
                    # (they affect click power, not building CPS)
                    if not upgrade.is_thousand_fingers:
                        tier_mult *= 2.0
            
            # Total CPS for this building type
            total_cps += base_cps * count * tier_mult
        
        return total_cps
    
    def apply_deterministic_clicks(self, state: GameState, target_time_ms: int) -> GameState:
        """Apply all deterministic clicks from current time up to (not including) target_time_ms.
        Clicks occur automatically every 20ms starting at 0ms: 0, 20, 40, 60, ..."""
        new_state = state.copy()
        
        # Calculate which clicks should have occurred
        # Clicks happen at: 0, 20, 40, 60, 80, ...
        # Find the first click >= current time
        current_click_time = ((state.time_ms + 19) // 20) * 20  # Round up to next multiple of 20
        
        # Apply all clicks from current_click_time up to (but not including) target_time_ms
        while current_click_time < target_time_ms:
            if current_click_time >= state.time_ms:  # Only apply clicks that haven't happened yet
                click_power = new_state.click_power
                new_state.cookies += click_power
                new_state.cookies_baked += click_power
                new_state.last_click_time_ms = current_click_time
            current_click_time += 20
        
        return new_state
    
    def calculate_click_power(self, state: GameState) -> float:
        """Calculate click power based on Cookie Clicker mouseCps formula"""
        # Base click power is 1 cookie per click
        base_power = 1.0
        
        # Count cursor upgrade tiers (each doubles click power)
        # From source: Game.ComputeCps(base, mult, bonus) = (base * 2^mult) + bonus
        cursor_upgrade_count = 0
        for upgrade_name in ['reinforced_index_finger', 'carpal_tunnel_prevention_cream', 'ambidextrous']:
            if upgrade_name in state.upgrades:
                cursor_upgrade_count += 1
        
        # Apply multiplicative bonus from cursor upgrades: 2^(upgrades_owned)
        click_power = base_power * (2 ** cursor_upgrade_count)
        
        # Thousand Fingers and its variants add bonus per non-cursor building
        # From source: add = 0.1 * (number of non-cursor buildings)
        # Then multiplied by: Million fingers (*5), Billion fingers (*10), Trillion fingers (*20), etc.
        if 'thousand_fingers' in state.upgrades:
            non_cursor_count = sum(count for bname, count in state.buildings.items() if bname != 'cursor')
            add = 0.1
            if 'million_fingers' in state.upgrades:
                add *= 5
            if 'billion_fingers' in state.upgrades:
                add *= 10
            if 'trillion_fingers' in state.upgrades:
                add *= 20
            click_power += add * non_cursor_count
        
        return click_power
    
    def advance_time(self, state: GameState, from_ms: int, to_ms: int) -> GameState:
        """
        Advance time from from_ms to to_ms, applying:
        1. Deterministic clicks (every 20ms: 0, 20, 40, ...)
        2. Frame production (every ~33.33ms)
        """
        new_state = state.copy()
        
        # Apply all deterministic clicks in this time range
        for t in range(from_ms, to_ms + 1):
            # Check if this is a click time (multiple of 20) AND we haven't already clicked at this time
            if t % 20 == 0 and t >= 0 and t != new_state.last_click_time_ms:
                click_power = new_state.click_power
                new_state.cookies += click_power
                new_state.cookies_baked += click_power
                new_state.last_click_time_ms = t
        
        # Advance time and apply production
        new_state.time_ms = to_ms
        
        # Calculate frames that should have production applied
        ms_per_frame = 100 / 3  # 33.333... ms per frame
        start_frame = state.last_production_frame
        end_frame = math.floor(new_state.time_ms / ms_per_frame)
        
        # Apply production when entering each new frame
        # JavaScript: if (currentFrame > lastProductionFrame) { produce; lastProductionFrame = currentFrame; }
        # This means we produce when ENTERING a frame, so if we're at time T in frame F,
        # we should have produced for all frames from (lastProductionFrame + 1) through F (inclusive)
        for frame in range(start_frame + 1, end_frame + 1):
            if new_state.cps > 0:
                production_this_frame = new_state.cps / self.fps
                new_state.cookies += production_this_frame
                new_state.cookies_baked += production_this_frame
            # Update last_production_frame to match JavaScript behavior
            new_state.last_production_frame = frame
        
        return new_state
    
    def _simulate_until_first_event(self, state: GameState, goal_cookies: Optional[float]) -> Tuple[int, str, set, float, float, int, int]:
        """
        Event-driven simulation from the current state until the first of:
          - Goal reached (cookies_baked >= goal_cookies) -> returns (dt, 'goal', set(), cookies, baked, last_click, last_frame)
          - One or more purchase options (building, qty) become affordable for the first time ->
            returns (dt, 'afford', A, cookies, baked, last_click, last_frame)
        Clicking is deterministic: occurs every 20ms starting at 0ms.
        """
        # Build cost map for non-deferred options
        options_costs = {}
        # Extract building names that are deferred (any quantity of that building is deferred)
        deferred_buildings = {opt[0] for opt in state.deferred_options}
        
        for bname in self.buildings.keys():
            # Skip this building entirely if ANY quantity of it has been deferred
            if bname in deferred_buildings:
                continue
                
            start_count = state.buildings.get(bname, 0)
            # Determine dynamic upper bound from goal
            ub = self.max_affordable_qty_by_goal(bname, start_count, goal_cookies) if goal_cookies is not None else 100
            # Incrementally accumulate costs for 1..ub
            running = 0
            for k in range(1, ub + 1):
                price_k = self.get_building_cost(bname, start_count + (k - 1))
                running += price_k
                opt = (bname, k)
                options_costs[opt] = running
        
        t0 = state.time_ms
        t = t0
        cookies = state.cookies
        baked = state.cookies_baked
        last_click = state.last_click_time_ms
        last_frame = state.last_production_frame
        cps = state.cps
        click_power = state.click_power
        
        # Deterministic click at current time if it's a click time (multiple of 20)
        if t % 20 == 0 and t >= 0 and t != last_click:
            cookies += click_power
            baked += click_power
            last_click = t
        
        # Check goal immediately
        if goal_cookies is not None and baked >= goal_cookies:
            return 0, 'goal', set(), cookies, baked, last_click, last_frame
        
        # Check affordability immediately
        A = {opt for opt, cost in options_costs.items() if cost <= cookies}
        if A:
            return 0, 'afford', A, cookies, baked, last_click, last_frame
        
        # Iterate events: next frame production or next click time
        while True:
            # Next frame production time: floor((last_frame+1)*ms_per_frame)
            # Frame N starts at floor(N * ms_per_frame) milliseconds
            t_frame = math.floor((last_frame + 1) * self.ms_per_frame)
            # Next click time (deterministic: next multiple of 20 after last_click)
            t_click = ((last_click // 20) + 1) * 20
            # If no CpS, ignore frame events by setting them after click time
            if cps <= 0:
                next_t = t_click
            else:
                next_t = t_frame if t_frame <= t_click else t_click
            
            # Advance virtual time to next_t and apply the event(s)
            t = next_t
            if cps > 0 and t == t_frame:
                prod = cps / self.fps
                cookies += prod
                baked += prod
                last_frame += 1
            if t == t_click:
                cookies += click_power
                baked += click_power
                last_click = t
            
            # Check goal
            if goal_cookies is not None and baked >= goal_cookies:
                return t - t0, 'goal', set(), cookies, baked, last_click, last_frame
            
            # Check affordability
            A = {opt for opt, cost in options_costs.items() if cost <= cookies}
            if A:
                return t - t0, 'afford', A, cookies, baked, last_click, last_frame
    
    def _advance_state_with_time(self, state: GameState, dt: int, base_path: List[Tuple[str, int, int]]) -> Tuple[GameState, List[Tuple[str, int, int]]]:
        """
        Advance the state forward by dt milliseconds, applying frame production and deterministic clicking.
        Returns the new state and an empty path extension (clicks and time are implicit, not stored).
        """
        actions: List[Tuple[str, int, int]] = []  # Empty - no actions to record
        new_state = self.advance_time(state, state.time_ms, state.time_ms + dt)
        return new_state, actions
    
    def bfs_optimize(self, goal_cookies: float, max_time_ms: Optional[int] = None, max_depth: Optional[int] = None) -> Optional[Tuple[List[Tuple[str, int, int]], int]]:
        """
        Event-driven BFS (first-opportunity rule):
        - Greedy, instantaneous clicking (no branching).
        - Jump to the earliest time t* when any purchase option (building, qty∈{1,10,100}) first becomes affordable.
        - At t*, branch into:
            • one child per newly affordable option (buy-now), and
            • one skip child that defers all those options until the next purchase occurs.
        - If goal is reached before any purchase becomes affordable, return immediately.
        """
        initial_state = GameState(
            cookies=0,
            cookies_baked=0,  # Track cumulative production
            buildings={},
            cps=0.0,  # Current cookies per second (divided by 30 each frame)
            time_ms=0,
            last_click_time_ms=-20,  # Start at -20 so first click at t=0 is valid
            last_production_frame=-1,  # Start at -1 so first frame (0) can produce
            click_power=1.0,
            deferred_options=set()
        )
        
        # States organized by time in milliseconds: {time_ms: [(state, path), ...]}
        states_by_time = {0: [(initial_state, [])]}
        visited = set()
        
        if max_time_ms is None:
            print(f"Starting BFS with goal: {goal_cookies} cookies (no time limit)")
        else:
            print(f"Starting BFS with goal: {goal_cookies} cookies (max {max_time_ms}ms)")
        
        depth = 0
        best_solution = None  # Track best solution found so far
        best_time = float('inf')
        
        while (max_depth is None or depth < max_depth) and states_by_time:
            depth += 1
            time_ms = min(states_by_time.keys())
            
            # Early termination: if we have a solution and all remaining states
            # are at times >= best solution time, we can stop
            if best_solution is not None and time_ms >= best_time:
                print(f"Early termination: best solution is {best_time}ms, remaining states at >={time_ms}ms")
                break
            
            if max_time_ms is not None and time_ms > max_time_ms:
                break
            current_states = states_by_time.pop(time_ms)
            
            if depth <= 20 or depth % 100 == 0:
                # Show cookies baked by current states
                cookies_baked_values = [state.cookies_baked for state, path in current_states]
                print(f"Depth {depth}: Time {time_ms}ms, {len(current_states)} states, cookies baked: {sorted(cookies_baked_values, reverse=True)[:10]}")
            
            # Keep strongest states per time
            current_states.sort(key=lambda x: x[0].cookies_baked, reverse=True)
            max_states_per_time = 50
            current_states = current_states[:max_states_per_time]
            
            for state, path in current_states:
                # Check if goal already met
                if state.cookies_baked >= goal_cookies:
                    if state.time_ms < best_time:
                        best_solution = (path, state.time_ms)
                        best_time = state.time_ms
                        if depth <= 10 or depth % 100 == 0:  # Log first few and periodically
                            print(f"Found solution at time {state.time_ms}ms (new best)")
                    continue  # Don't return yet, check if there's a better solution
                
                # Signature for pruning (time, cookies, baked, buildings, click, frame, deferred)
                # Use higher precision (6 decimal places) to capture small production differences
                state_sig = (
                    state.time_ms,
                    round(state.cookies * 1000000) / 1000000,
                    round(state.cookies_baked * 1000000) / 1000000,
                    tuple(sorted(state.buildings.items())),
                    state.last_click_time_ms,
                    state.last_production_frame,
                    tuple(sorted(state.deferred_options))
                )
                if state_sig in visited:
                    continue
                visited.add(state_sig)
                
                # Simulate forward to the first significant event (goal or affordability)
                dt, ev_type, A, virt_cookies, virt_baked, virt_last_click, virt_last_frame = \
                    self._simulate_until_first_event(state, goal_cookies)
                
                # Advance state (time and deterministic clicks are implicit, not stored)
                advanced_state, actions = self._advance_state_with_time(state, dt, path)
                new_path_base = path + actions
                
                # If goal is reached before any purchase is affordable
                if ev_type == 'goal':
                    if advanced_state.time_ms < best_time:
                        best_solution = (new_path_base, advanced_state.time_ms)
                        best_time = advanced_state.time_ms
                        if depth <= 10 or depth % 100 == 0:  # Log first few and periodically
                            print(f"Found solution at time {advanced_state.time_ms}ms (new best)")
                    continue  # Don't return yet, check if there's a better solution
                
                # ev_type == 'afford': create buy-now children and a skip child
                # A is set of (building, qty) that FIRST become affordable now
                
                # Generate skip child (defer these options until next purchase)
                skip_state = advanced_state.copy()
                for opt in A:
                    skip_state.deferred_options.add(opt)
                if max_time_ms is None or skip_state.time_ms <= max_time_ms:
                    states_by_time.setdefault(skip_state.time_ms, []).append((skip_state, new_path_base))
                
                # Generate buy-now children
                for (bname, qty) in A:
                    buy_state = advanced_state.copy()
                    buy_state = self.purchase_multiple(buy_state, bname, qty)
                    if buy_state is None:
                        continue  # safety guard against rounding issues
                    buy_path = list(new_path_base)
                    # Record each unit purchase to keep verifier unchanged
                    for _ in range(qty):
                        buy_path.append(('buy', bname, buy_state.time_ms))
                    if max_time_ms is None or buy_state.time_ms <= max_time_ms:
                        states_by_time.setdefault(buy_state.time_ms, []).append((buy_state, buy_path))
        
        # Return best solution found
        if best_solution is not None:
            print(f"\nReturning best solution: {best_time}ms after {depth} depth levels")
            return best_solution
        
        if max_time_ms is None:
            print(f"No solution found after {depth} depth levels")
        else:
            print(f"No solution found within {max_time_ms}ms after {depth} depth levels")
        return None

def export_bfs_path_to_visualization(path: List[Tuple], goal: float, total_time_ms: int, optimizer: 'CookieClickerOptimizer') -> str:
    """
    Export BFS path data to visualization format and save to bfs_data_exports folder.
    Returns the path to the exported file.
    
    Optimizations:
    - Clicks are NOT exported - the visualization generates them deterministically (every 20ms)
    - RLE (Run-Length Encoding) compression: Consecutive identical purchases are compressed
      Example: buying 10 cursors at once becomes {count: 10} instead of 10 separate events
    - Only purchase events and click_power changes are exported
    
    This dramatically reduces file size, write time, and read time for large BFS solutions.
    """
    from pathlib import Path
    from datetime import datetime
    
    # Create bfs_data_exports folder if it doesn't exist
    export_folder = Path(__file__).resolve().parent / 'bfs_data_exports'
    export_folder.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bfs_{int(goal)}_cookies_{timestamp}.json"
    filepath = export_folder / filename
    
    # Convert path to events format (no RLE compression to preserve accurate timestamps)
    # Note: RLE was causing issues where purchases at different timestamps
    # were being grouped together, breaking the verification
    compressed_path = [(1, action_type, action_value, action_time_ms) 
                       for action_type, action_value, action_time_ms in path]
    
    # Convert to events
    events = []
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
    
    for count, action_type, action_value, action_time_ms in compressed_path:
        if action_type == 'buy':
            building_name = action_value
            
            # IMPORTANT: Advance time to the purchase time to simulate cookie production
            if action_time_ms > state.time_ms:
                state = optimizer.advance_time(state, state.time_ms, action_time_ms)
            
            # Determine if this is a building or upgrade purchase
            is_upgrade = building_name not in optimizer.buildings
            is_cursor_upgrade = is_upgrade and building_name.startswith('cursor_')  # Cursor upgrades naming convention
            is_thousand_fingers = building_name == 'thousand_fingers'
            
            # Calculate cost for this single purchase
            current_count = state.buildings.get(building_name, 0)
            if not is_upgrade:
                cost = optimizer.get_building_cost(building_name, current_count)
            else:
                # Upgrades can only be bought once
                if building_name not in state.upgrades:
                    cost = optimizer.get_upgrade_cost(building_name)
                else:
                    cost = 0  # Already purchased
            
            # Make the purchase using the optimizer's method to ensure consistency
            state = optimizer.purchase_building(state, building_name)
            
            # Record single purchase event with state checkpoint AFTER purchase
            # Note: purchase_building() already recalculates CPS and click_power
            events.append({
                "kind": "purchase",
                "t": action_time_ms,
                "item_key": building_name,
                "cost": cost,
                "is_upgrade": is_upgrade,
                # State checkpoint after this purchase (with proper simulation)
                "state_after": {
                    "cookies": state.cookies,
                    "cookies_baked": state.cookies_baked,
                    "buildings": dict(state.buildings),
                    "cps": state.cps,
                    "click_power": state.click_power
                }
            })
    
    # Advance to final time to capture end state
    if total_time_ms > state.time_ms:
        state = optimizer.advance_time(state, state.time_ms, total_time_ms)
    
    # Create visualization data structure
    viz_data = {
        "type": "timeline_paths",
        "title": f"BFS Optimal Path to {int(goal)} Cookies",
        "goal": goal,
        "paths": [{
            "name": f"Optimal Path ({total_time_ms}ms)",
            "color": "BLUE_C",
            "events": events,
            "total_ms": total_time_ms,
            # Add final state at completion time for verification
            "final_state": {
                "cookies": state.cookies,
                "cookies_baked": state.cookies_baked,
                "buildings": dict(state.buildings),
                "cps": state.cps,
                "click_power": state.click_power,
                "time_ms": state.time_ms,
                "last_production_frame": state.last_production_frame
            }
        }]
    }
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(viz_data, f, indent=2)
    
    return str(filepath)

def compress_path(path):
    """Compress consecutive identical actions for cleaner output (using millisecond timestamps)
    Note: Clicks are now deterministic and not stored in the path."""
    if not path:
        return []
    
    compressed = []
    
    for action in path:
        action_type = action[0]
        
        if action_type == 'buy':
            # Purchases are the only actions stored now
            compressed.append({
                'type': 'buy',
                'count': 1,
                'building': action[1],
                'time_ms': action[2]
            })
    
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

        # Export BFS data for visualization
        try:
            viz_export_path = export_bfs_path_to_visualization(path, goal, total_time_ms, optimizer)
            print(f"\n✓ Exported BFS data for visualization: {viz_export_path}")
        except Exception as e:
            print(f"\n⚠ Failed to export BFS visualization data: {e}")

        # Prepare path for verification page with RLE compression
        # Group consecutive purchases of the same building at the same time
        json_path = []
        predicted_buildings_counts = {}
        
        i = 0
        while i < len(path):
            action_type, action_value, action_time_ms = path[i]
            
            if action_type == 'buy':
                # Count consecutive purchases of same building at same time
                building = action_value
                time = action_time_ms
                count = 1
                
                # Look ahead for consecutive same purchases
                while i + count < len(path):
                    next_type, next_building, next_time = path[i + count]
                    if next_type == 'buy' and next_building == building and next_time == time:
                        count += 1
                    else:
                        break
                
                # Store as: [count, 'buy', building, time]
                json_path.append([count, action_type, action_value, action_time_ms])
                
                js_name = _build_js_building_name(action_value)
                predicted_buildings_counts[js_name] = predicted_buildings_counts.get(js_name, 0) + count
                
                i += count
            else:
                # Non-buy actions stored as before (shouldn't happen with current optimization)
                json_path.append([action_type, action_value, action_time_ms])
                i += 1

        # Generate and launch verification HTML
        out_html = os.path.join('Automated Verification', 'auto_verification.html')
        _generate_verification_html(out_html, goal, total_time_ms, json_path, predicted_buildings_counts)

        try:
            webbrowser.open('file://' + os.path.abspath(out_html))
            print(f"Opened verification page: {out_html}")
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
            
            if action_type == 'buy':
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
        print(f"\nNote: Clicks occur deterministically every 20ms starting at 0ms (0, 20, 40, 60, ...).")
        print(f"      Building purchases are instant (0ms).")
        print(f"      Production applied each frame (~33.33ms) based on CpS at frame start.")
                
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.")

if __name__ == "__main__":
    main()
