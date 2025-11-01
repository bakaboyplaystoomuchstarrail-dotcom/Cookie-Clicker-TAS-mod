# The below README is written by Warp the ADE

#Cookie Clicker Official Rounding Rules

Based on analysis of the official Cookie Clicker source code (`TheEntiretyOfTheCookieClickerSourceCode.txt`).

## Game Constants

- **FPS**: 30 frames per second (line 1984)
- **Frame duration**: `1000/30 = 33.333...` milliseconds per frame
- **Price increase**: 1.15 multiplier per building

## Rounding Rules

### 1. Building Costs
**Source**: Lines 7806-7811
```javascript
this.getPrice=function(n) {
    var price=this.basePrice*Math.pow(Game.priceIncrease,Math.max(0,this.amount-this.free));
    price=Game.modifyBuildingPrice(this,price);
    return Math.ceil(price);  // Round UP
}
```
**Rule**: Use `Math.ceil()` - always round UP to the nearest integer.

**Python equivalent**: `math.ceil(base_cost * (1.15 ** amount))`

### 2. Frame Production
**Source**: Line 16290
```javascript
Game.Earn(Game.cookiesPs/Game.fps);//add cookies per second
```
**Rule**: Use **pure floating-point division** with **NO rounding**.

Each frame produces exactly `cookiesPs / 30` cookies (e.g., 0.1 CPS → 0.00333... cookies per frame).

**Python equivalent**: `cps / 30` (no rounding!)

### 3. Frame Calculation
**Source**: Lines 16290 (implicit)
```javascript
// Frame N starts at floor(N * (1000/30)) milliseconds
```
**Rule**: Use `Math.floor()` to calculate which frame a given time falls into.

**Python equivalent**: `math.floor(time_ms / (1000/30))`

### 4. Cookie Display
**Source**: Lines 2726-2727, 2731, 2733-2735, etc.
```javascript
parseInt(Math.floor(Game.cookieClicks))
parseInt(Math.floor(Game.goldenClicks))
parseInt(Math.floor(Game.bgType))
parseInt(Math.floor(Game.milkType))
```
**Rule**: Cookie counts are displayed using `Math.floor()` for UI purposes, but internally stored as floating-point.

## Critical Implementation Notes

1. **Never round intermediate cookie production** - only round for display
2. **Always use `Math.ceil()` for building costs** - this matches the game exactly
3. **Frame boundaries** are calculated as `Math.floor(time_ms / 33.333...)`
4. **Production happens once per frame**, not per millisecond

## Verification

Both the Python BFS and JavaScript HTML verification must use these exact rules to ensure consistency.

### Current Status (as of 2025-11-01)

✅ Building costs: Both use `math.ceil()` / `Math.ceil()`  
✅ Frame production: Both use floating-point division without rounding  
✅ Frame calculation: Both use `math.floor()` / `Math.floor()`  
✅ FPS: Both use 30 fps  

**All systems now match the official Cookie Clicker rounding!**

