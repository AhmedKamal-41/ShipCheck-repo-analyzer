# Manual Test Cases - HireLens

## TC-001: Analyze Valid GitHub Repository

**Priority**: P0 (Critical)  
**Severity**: Critical  
**Preconditions**: 
- Backend running on localhost:8000
- Frontend running on localhost:3000
- Database initialized

**Steps**:
1. Navigate to http://localhost:3000
2. Enter a valid GitHub repository URL (e.g., `https://github.com/vercel/next.js`)
3. Click "Generate report" or "Try it now" button
4. Wait for analysis to complete
5. Verify redirect to report page

**Expected Result**:
- URL is accepted without validation errors
- Report ID is returned
- Page redirects to `/reports/{report_id}`
- Report displays with score, sections, and checks
- Status shows "done"

---

## TC-002: Analyze Invalid GitHub URL

**Priority**: P0 (Critical)  
**Severity**: High  
**Preconditions**: Frontend running

**Steps**:
1. Navigate to home page
2. Enter invalid URL (e.g., `not-a-url` or `https://gitlab.com/user/repo`)
3. Click "Generate report" button

**Expected Result**:
- Validation error displayed inline
- Error message indicates URL must be a GitHub URL
- No API call made (or API returns 400)
- User can correct and retry

---

## TC-003: View Report with All Checks

**Priority**: P0 (Critical)  
**Severity**: Critical  
**Preconditions**: Report exists with status "done"

**Steps**:
1. Navigate to report page (e.g., `/reports/{id}`)
2. Review score summary section
3. Scroll through all sections (Runability, Engineering, Security, Docs)
4. Expand check details for multiple checks

**Expected Result**:
- Score displays correctly (0-100)
- All sections visible with correct names
- Checks show correct status badges (pass/warn/fail)
- Expanding details shows evidence and recommendations
- Interview pack section visible (if present)

---

## TC-004: Filter Checks by Status

**Priority**: P1 (High)  
**Severity**: Medium  
**Preconditions**: Report page loaded with multiple checks

**Steps**:
1. Navigate to report page
2. Click "All" filter button (verify all checks visible)
3. Click "Fail" filter button
4. Click "Warn" filter button
5. Click "Pass" filter button

**Expected Result**:
- Filter buttons toggle correctly
- Only checks matching selected status are visible
- Check count updates (if displayed)
- URL or state persists filter selection

---

## TC-005: Search Checks by Name

**Priority**: P1 (High)  
**Severity**: Medium  
**Preconditions**: Report page loaded

**Steps**:
1. Navigate to report page
2. Locate search input box
3. Type "README" in search box
4. Verify filtered results
5. Clear search box

**Expected Result**:
- Search input is visible and functional
- Checks containing "README" are shown
- Other checks are hidden
- Clearing search shows all checks again
- Search is case-insensitive

---

## TC-006: Copy Share Link

**Priority**: P2 (Medium)  
**Severity**: Low  
**Preconditions**: Report page loaded

**Steps**:
1. Navigate to report page
2. Click "Copy link" button
3. Verify clipboard contains report URL
4. Paste URL in new tab and verify it loads

**Expected Result**:
- Copy button is visible and clickable
- Clipboard contains full report URL
- Visual feedback shows "Copied!" message
- Pasted URL loads correct report

---

## TC-007: Handle Pending Report

**Priority**: P0 (Critical)  
**Severity**: High  
**Preconditions**: Analysis in progress

**Steps**:
1. Submit analyze request
2. Immediately navigate to report page (before completion)
3. Observe loading state
4. Wait for analysis to complete

**Expected Result**:
- Report page shows "pending" status
- Skeleton/loading UI displayed
- Page polls for updates
- Automatically updates when status changes to "done"
- Full report displays after completion

---

## TC-008: Handle Failed Report

**Priority**: P0 (Critical)  
**Severity**: High  
**Preconditions**: Report with status "failed"

**Steps**:
1. Navigate to failed report page
2. Review error message
3. Click "Retry Analysis" button
4. Verify retry initiates new analysis

**Expected Result**:
- Error card displayed with clear message
- Error details visible (e.g., "Repository not found")
- Retry button is visible and functional
- Clicking retry creates new report or re-analyzes
- User can navigate back to home

---

## TC-009: Re-analyze Repository

**Priority**: P1 (High)  
**Severity**: Medium  
**Preconditions**: Report page loaded

**Steps**:
1. Navigate to existing report page
2. Click "Re-analyze" button
3. Wait for new analysis to complete
4. Verify report updates

**Expected Result**:
- Re-analyze button visible in header
- Clicking button initiates new analysis
- Status changes to "pending" then "done"
- Report data updates with latest analysis
- Score and findings reflect current repo state

---

## TC-010: Navigate Back to Home

**Priority**: P1 (High)  
**Severity**: Low  
**Preconditions**: On report page

**Steps**:
1. Navigate to report page
2. Click "← Back" or "Analyze another repo" link
3. Verify navigation to home page

**Expected Result**:
- Back link visible in header
- Clicking link navigates to home page
- Home page loads correctly
- Input field is empty and ready for new URL

---

## TC-011: View Example Report Preview

**Priority**: P2 (Medium)  
**Severity**: Low  
**Preconditions**: Home page loaded

**Steps**:
1. Navigate to home page
2. Scroll to "Example Preview" section
3. Review example report display

**Expected Result**:
- Example section visible on home page
- Mock report displays score, badges, checks
- Example looks realistic and informative
- Section helps users understand output format

---

## TC-012: Responsive Design (Mobile)

**Priority**: P2 (Medium)  
**Severity**: Medium  
**Preconditions**: Frontend running

**Steps**:
1. Open browser DevTools
2. Set viewport to mobile (375x667)
3. Navigate to home page
4. Test analyze flow
5. Navigate to report page
6. Test filters and search

**Expected Result**:
- Layout adapts to mobile viewport
- Text is readable (not too small)
- Buttons are tappable (adequate size)
- Navigation works correctly
- No horizontal scrolling
- Filters/search accessible on mobile

---

## TC-013: Error Handling - Network Failure

**Priority**: P1 (High)  
**Severity**: High  
**Preconditions**: Backend stopped or unreachable

**Steps**:
1. Stop backend server
2. Navigate to home page
3. Submit analyze request
4. Observe error handling

**Expected Result**:
- Error message displayed to user
- Error is user-friendly (not technical)
- User can retry or navigate away
- No application crash or blank screen

---

## TC-014: Error Handling - Invalid Report ID

**Priority**: P1 (High)  
**Severity**: Medium  
**Preconditions**: Frontend running

**Steps**:
1. Navigate to `/reports/invalid-uuid-format`
2. Observe error handling
3. Navigate to `/reports/00000000-0000-0000-0000-000000000000` (non-existent)
4. Observe error handling

**Expected Result**:
- Invalid UUID shows validation error
- Non-existent report shows "Report not found" message
- Error page allows navigation back to home
- No application crash

---

## TC-015: Rate Limiting Behavior

**Priority**: P2 (Medium)  
**Severity**: Low  
**Preconditions**: Backend running

**Steps**:
1. Submit 11 analyze requests rapidly (within 60 seconds)
2. Observe 11th request behavior
3. Wait 60 seconds
4. Submit another request

**Expected Result**:
- First 10 requests succeed
- 11th request returns 429 (Too Many Requests)
- Error message indicates rate limit exceeded
- After waiting, requests succeed again
- Rate limit is per IP address
