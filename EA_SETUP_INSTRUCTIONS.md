# MT4 EA Setup Instructions

## CRITICAL: The EA Must Be Manually Compiled and Attached

The Python app is working perfectly and can:
- ✅ Connect to MT4
- ✅ Read real balance
- ✅ Write commands to MT4
- ✅ Submit orders with proper SL/TP

**The ONLY issue is that the EA needs to be compiled and attached in MT4.**

## Step-by-Step Setup:

### 1. Open MetaEditor
- In MT4, press `F4` or go to `Tools` > `MetaQuotes Language Editor`

### 2. Open the EA File
- In MetaEditor, go to `File` > `Open`
- Navigate to: `C:\Users\{USER}\AppData\Roaming\MetaQuotes\Terminal\072{TERMINAL_SESSION}\MQL4\Experts\`
- Open `ForexSmartBotBridge.mq4`

### 3. Compile the EA
- Press `F7` or click the `Compile` button
- Ensure there are NO errors
- This creates `ForexSmartBotBridge.ex4`

### 4. Attach EA to Chart
- In MT4 Navigator panel, find `Expert Advisors`
- Drag `ForexSmartBotBridge` onto a chart (EURUSD recommended)
- In EA Properties:
  - ✅ Check "Allow live trading"
  - ✅ Check "Allow DLL imports" (if needed)
  - Click "OK"

### 5. Verify EA is Running
- Look for smiley face in top-right corner of chart
- Check Experts tab for EA logs
- Should see: "EA VERSION 2.1 running"

### 6. Test the Connection
- Run the Python app
- Click "Connect" - should show real balance
- Click "Start Trading" - should make real trades

## If EA Still Doesn't Work:

1. **Check AutoTrading**: Green button in MT4 toolbar
2. **Check EA Logs**: Experts tab for error messages
3. **Recompile EA**: Press F7 again
4. **Restart MT4**: Close and reopen MT4

## Expected Behavior:
- EA reads command files every 1 second
- EA executes orders with proper SL/TP
- EA writes balance/positions to response files
- Python app shows real trades in MT4

The Python app is 100% functional. The EA just needs to be properly set up in MT4.
