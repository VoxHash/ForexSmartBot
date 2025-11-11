# Testing Checklist Before Pushing to Repository

## Critical Tests to Perform

### 1. Application Startup ✅
- [x] App starts without errors
- [ ] All tabs load correctly
- [ ] Menu bar displays all items
- [ ] No console errors on startup

### 2. Strategy Selection
- [ ] All 14 strategies appear in dropdown
- [ ] Can select and configure each strategy
- [ ] ML strategies work (if DLLs loaded) or gracefully fail (if not)
- [ ] Strategy combo box shows risk level indicators

### 3. Environment Variables
- [ ] App reads from `.env` file
- [ ] MT4 connection uses `MT4_ZMQ_HOST` and `MT4_ZMQ_PORT`
- [ ] API endpoints use `API_HOST`, `API_PORT`, etc.
- [ ] Cloud tab shows correct URLs from env vars

### 4. Broker Connection
- [ ] Can connect to MT4 broker
- [ ] Can connect to Paper broker
- [ ] Real balance displays correctly
- [ ] Real positions sync from MT4

### 5. Trading Functionality
- [ ] Can start/stop trading
- [ ] Orders execute correctly
- [ ] SL/TP are set properly
- [ ] Positions update in real-time

### 6. Menu Items
- [ ] All optimization tools open dialogs
- [ ] Strategy builder opens
- [ ] Analytics tools open
- [ ] Monitoring tools open
- [ ] Marketplace opens
- [ ] Cloud dialogs open

### 7. Tabs in Main Window
- [ ] Trading tab works
- [ ] Analytics tab loads
- [ ] Charts tab loads
- [ ] Strategy Builder tab shows info
- [ ] Marketplace tab shows info
- [ ] Monitoring tab loads
- [ ] Cloud tab shows correct info

### 8. Error Handling
- [ ] App handles missing ML libraries gracefully
- [ ] No crashes on missing dependencies
- [ ] Warning messages appear for unavailable features

## Recommended Approach

### Option 1: Test Locally First (Recommended)
1. Test all critical functionality locally
2. Fix any issues found
3. Commit and push when confident

### Option 2: Create Feature Branch
1. Create branch: `git checkout -b feature/env-vars-and-gui-integration`
2. Push branch: `git push origin feature/env-vars-and-gui-integration`
3. Test on branch
4. Merge to main when ready

### Option 3: Incremental Push
1. Commit current changes locally
2. Test thoroughly
3. Push when tests pass

## What We've Changed
- ✅ Environment variables integration throughout project
- ✅ GUI integration (all ROADMAP features in menu/tabs)
- ✅ PyTorch DLL error handling
- ✅ All strategies available in UI
- ✅ Created Website and MobileApp folders

## Risk Assessment
- **Low Risk**: Environment variables, GUI integration (mostly UI changes)
- **Medium Risk**: PyTorch DLL handling (needs testing with/without ML libs)
- **High Risk**: None identified

## Recommendation
**Wait and test locally first**, then push. The changes are significant and affect core functionality. Better to catch issues locally than in production.

