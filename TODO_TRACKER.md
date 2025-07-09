# TODO Tracker - Onboarding Assistant

## Quick Status Overview

| Phase                             | Status           | Priority   | Progress |
| --------------------------------- | ---------------- | ---------- | -------- |
| Phase 1A: Data Foundation        | ✅ COMPLETED     | HIGH       | 100%     |
| Phase 1B: API Integration        | ✅ COMPLETED     | HIGH       | 100%     |
| **Phase 2A: Function Calling**   | ❌ **FAILED**    | **HIGH**   | **0%**   |
| Phase 2A-1: Fix Function Calling | 🚨 **CRITICAL**  | **HIGH**   | **0%**   |
| Phase 2A-2: Single Question Flow | ⏳ BLOCKED       | HIGH       | 0%       |
| Phase 2A-3: Full Question Seq    | ⏳ BLOCKED       | HIGH       | 0%       |
| Phase 2A-4: Action Recommend     | ⏳ BLOCKED       | MEDIUM     | 0%       |
| Phase 2B: Advanced Features      | ⏳ BLOCKED       | LOW        | 0%       |

---

## 🚨 CRITICAL ISSUE: Function Calling Broken

### Status: FAILED - NEEDS IMMEDIATE ATTENTION

### Problem: LLM describes actions but doesn't execute registered functions

### Impact: ALL functionality is blocked until this is resolved

### Evidence:
- LLM says "I will call get_user_status()" but never actually calls it
- Data values remain null in user_data.json
- Widget interface never gets triggered
- No automatic question progression

---

## 🎯 CURRENT PRIORITY: Phase 2A-1 - Fix Function Calling

### Status: CRITICAL - NOT STARTED

### Priority: HIGH - BLOCKS ALL OTHER WORK

### Description: Make LLM actually invoke registered Semantic Kernel functions

### Tasks:

#### 🔍 Investigation Tasks:
- [ ] **Debug function registration** - Are functions properly registered with kernel?
- [ ] **Test function accessibility** - Can functions be called manually?
- [ ] **Verify LLM configuration** - Is Semantic Kernel configured for function calling?
- [ ] **Check prompt instructions** - Does prompt explicitly instruct function calling?
- [ ] **Review Semantic Kernel docs** - Are we using the API correctly?

#### 🧪 Testing Tasks:
- [ ] **Create simple test** - LLM should call `get_user_status()` automatically
- [ ] **Test function response** - Verify function actually gets invoked
- [ ] **Test data updates** - Verify `update_user_data()` modifies JSON
- [ ] **Test widget triggers** - Verify `ask_question()` triggers widget interface
- [ ] **Test error handling** - What happens when functions fail?

#### 📋 Implementation Tasks:
- [ ] **Fix function calling mechanism** - Based on investigation results
- [ ] **Validate with simple functions** - Start with basic status calls
- [ ] **Test incremental complexity** - Build up to complex functions
- [ ] **Document working patterns** - Record what works and what doesn't

### Success Criteria:
- [ ] LLM automatically calls `get_user_status()` when asked about progress
- [ ] LLM calls `update_user_data("age", "25")` and user_data.json is updated
- [ ] LLM calls `ask_question("gender", "contextual message")` and widget appears
- [ ] Functions are invoked without manual intervention
- [ ] All function calls result in expected side effects

### Current Blockers:
- **Unknown Root Cause**: Don't know why function calling isn't working
- **No Testing Framework**: Can't verify function calling works
- **Lost Functionality**: Previous working features were removed

---

## 📋 NEXT PHASE: Phase 2A-2 - Single Question Flow

### Status: BLOCKED (depends on Phase 2A-1)

### Priority: HIGH

### Description: Complete one question end-to-end

### Planned Tasks:
- [ ] **Choose test question** - Start with simple free-form question (age)
- [ ] **Implement question flow** - LLM asks question, processes answer
- [ ] **Test data extraction** - Verify text-to-number conversion works
- [ ] **Test data persistence** - Verify user_data.json is updated
- [ ] **Test widget questions** - Verify widget interface works
- [ ] **Test error handling** - Handle invalid inputs gracefully

### Success Criteria:
- [ ] LLM asks "Kaç yaşındasınız?" automatically
- [ ] LLM extracts age from "I am twenty five years old" → 25
- [ ] user_data.json is updated with correct age value
- [ ] Process works for both free-form and widget questions
- [ ] Conversation flows naturally without manual intervention

---

## 📋 FUTURE PHASE: Phase 2A-3 - Full Question Sequence

### Status: BLOCKED (depends on Phase 2A-2)

### Priority: HIGH

### Description: Complete all 13 questions automatically

### Planned Tasks:
- [ ] **Implement question ordering** - Follow proper sequence 1-13
- [ ] **Test question progression** - Verify automatic advancement
- [ ] **Test contextual responses** - Verify appropriate responses to answers
- [ ] **Test widget integration** - Verify all 10 widget questions work
- [ ] **Test free-form extraction** - Verify age/height/weight extraction
- [ ] **Test completion detection** - Verify system knows when done

### Success Criteria:
- [ ] LLM progresses through all 13 questions in order
- [ ] LLM provides contextual responses for each answer
- [ ] All user_data.json fields are populated correctly
- [ ] Process completes automatically without manual intervention
- [ ] Widget questions display properly and record answers

---

## 📋 DEFERRED PHASE: Phase 2A-4 - Action Recommendations

### Status: BLOCKED (depends on Phase 2A-3)

### Priority: MEDIUM

### Description: Only implement after questions work perfectly

### Planned Tasks:
- [ ] **Implement action analysis** - Analyze completed user data
- [ ] **Test action filtering** - Apply trigger/exclude conditions
- [ ] **Test action prioritization** - Sort by priority levels
- [ ] **Test action presentation** - Format recommendations nicely
- [ ] **Test action accuracy** - Verify recommendations are appropriate

### Success Criteria:
- [ ] LLM analyzes completed user data
- [ ] LLM generates personalized health recommendations
- [ ] Actions are properly filtered and prioritized
- [ ] Recommendations are presented clearly to user

---

## 📝 LESSONS LEARNED FROM PHASE 2A FAILURE

### What We Attempted:
1. **Function Calling Architecture** - Semantic Kernel with registered functions
2. **Data Consolidation** - Unified user_data.json structure
3. **Auto-orchestration** - LLM-driven question progression
4. **Widget Integration** - Intelligent ask_question() function
5. **UI Separation** - Clean architecture with /ui/ folder

### What Failed:
1. **Function Invocation** - LLM doesn't actually call functions
2. **Data Updates** - No persistence, all values remain null
3. **Question Flow** - No automatic progression through questions
4. **Widget Triggers** - Widget interface never gets called
5. **Orchestration** - System requires manual input for each step

### Critical Mistakes:
1. **Over-ambitious Scope** - Tried to do too much at once
2. **Insufficient Testing** - Made large changes without validation
3. **Lost Functionality** - Removed working features without replacement
4. **Regex/Hardcoded Logic** - Created brittle extraction patterns
5. **Architecture Over Features** - Focused on structure instead of functionality

### Key Insights:
1. **Function Calling First** - Must work before any other features
2. **Incremental Testing** - Test each component independently
3. **Smaller Scope** - Focus on questions only, not actions
4. **Working Code** - Don't remove working features
5. **Test Early** - Validate each change before proceeding

---

## 📋 CURRENT WORKING STATE

### ✅ What Actually Works:
- **Basic Chat**: main.py runs and can have conversations
- **API Integration**: Semantic Kernel with Gemini works with cost tracking
- **UI Components**: Terminal chat interface and widget UI implemented
- **Data Structure**: Unified user_data.json with permissions model
- **Architecture**: Clean separation of /agents/, /ui/, /utils/

### ❌ What Doesn't Work:
- **Function Calling**: LLM describes but doesn't execute functions
- **Data Updates**: All values remain null, no persistence
- **Question Flow**: No automatic progression through questions
- **Widget Integration**: Widget handler exists but isn't called
- **Auto-orchestration**: No autonomous operation

### 🚨 Critical Issues:
1. **Function Calling Broken** - LLM doesn't invoke registered functions
2. **Data Updates Lost** - No mechanism to update user_data.json
3. **Question Progression Missing** - No automatic advancement
4. **Widget Integration Broken** - Widget interface never triggered
5. **Testing Debt** - No verification of core functionality

---

## 📋 TESTING REQUIREMENTS

### Function Calling Tests (CRITICAL):
```python
def test_function_calling():
    # Test: LLM calls get_user_status() automatically
    # Expected: Function is actually invoked, not just described
    
def test_data_updates():
    # Test: LLM calls update_user_data("age", "25")
    # Expected: user_data.json is updated with age=25
    
def test_widget_integration():
    # Test: LLM calls ask_question("gender", "message")
    # Expected: Widget interface appears and records answer
```

### Question Flow Tests:
```python
def test_single_question():
    # Test: Complete one question end-to-end
    # Expected: Question asked, answer processed, data updated
    
def test_question_sequence():
    # Test: Progress through questions 1-13
    # Expected: All questions completed, all data populated
```

### Data Persistence Tests:
```python
def test_data_persistence():
    # Test: Data updates are saved to user_data.json
    # Expected: File is modified and values are correct
```

---

## 📋 SUCCESS METRICS

### Phase 2A-1 Success:
- LLM automatically calls functions without being asked
- Function calls result in expected side effects
- Data updates are persisted to JSON files
- Widget interfaces are triggered by LLM

### Phase 2A-2 Success:
- Single question completed end-to-end
- Data extraction works for natural language
- Data persistence works correctly
- Process flows naturally

### Phase 2A-3 Success:
- All 13 questions completed automatically
- Contextual responses provided for each answer
- All user_data.json fields populated
- Process completes without manual intervention

---

## 📋 RISK MITIGATION

### Risks Identified:
1. **Function Calling May Not Work** - Semantic Kernel issues
2. **Data Updates May Be Complex** - JSON handling problems
3. **Widget Integration May Fail** - UI synchronization issues
4. **Question Flow May Be Brittle** - LLM decision-making problems

### Mitigation Strategies:
1. **Start Small** - Test one function at a time
2. **Incremental Progress** - Don't attempt full flow until basics work
3. **Document Failures** - Record what doesn't work and why
4. **Test Frequently** - Validate each change before proceeding
5. **Have Backup Plans** - Alternative approaches if current doesn't work

---

## 📋 NOTES FOR NEXT SESSION

### Immediate Focus:
1. **Debug Function Calling** - This is the critical blocker
2. **Create Simple Tests** - Verify basic functionality works
3. **Document Findings** - Record what works and what doesn't
4. **Stay Focused** - Don't get distracted by other features

### Key Files to Focus On:
- `agents/health_agent.py` - Function registration
- `agents/data_handler.py` - Function implementations
- `agents/prompts/main_prompt.txt` - LLM instructions
- `data/user/user_data.json` - Data persistence target

### Critical Questions to Answer:
1. Why doesn't LLM call registered functions?
2. How can we verify function calling works?
3. What's the minimal test case that should work?
4. Are we using Semantic Kernel correctly?

---

_Last Updated: Phase 2A marked as FAILED, Phase 2A-1 (Fix Function Calling) is now CRITICAL priority_