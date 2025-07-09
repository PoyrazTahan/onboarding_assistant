# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Onboarding Assistant** is a medical & psychological health app that uses LLM agents to collect user health data through conversational interactions and provides personalized health recommendations.

**Current Status**: Phase 1 ✅ Complete | Phase 2A ❌ FAILED - NEEDS RESET

## ⚠️ CRITICAL ISSUES TO ADDRESS

### 1. Function Calling Failure

- **Problem**: LLM describes actions but doesn't execute registered functions
- **Impact**: No data updates, no question progression, no widget integration
- **Status**: CRITICAL - blocks all functionality

### 2. Missing Orchestration

- **Problem**: No automatic question progression through 13 questions
- **Impact**: System requires manual user input for each step
- **Status**: CRITICAL - core functionality missing

### 3. Lost Update Capabilities

- **Problem**: Data values remain null, no updates to user_data.json
- **Impact**: No data persistence, no progress tracking
- **Status**: HIGH - fundamental feature broken

## Current Working State

### ✅ What Actually Works

- **Basic Chat**: `main.py` runs and can have conversations
- **API Integration**: Semantic Kernel with Gemini works with cost tracking
- **UI Components**: Terminal chat interface and widget UI implemented
- **Data Structure**: Unified `user_data.json` with permissions
- **Architecture**: Clean separation of `/agents/`, `/ui/`, `/utils/`

### ❌ What Doesn't Work

- **Function Calling**: LLM doesn't invoke registered functions
- **Data Updates**: All values remain null, no persistence
- **Question Flow**: No automatic progression through questions
- **Widget Integration**: Widget handler exists but isn't called
- **Auto-orchestration**: No autonomous operation

## Common Development Commands

### Setup & Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here  # optional

# Or create a .env file with:
# GEMINI_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
```

### Running the Application

```bash
# Run primary implementation (basic chat works)
python main.py
```

### Testing & Validation

```bash
# TODO: Add function calling tests
# TODO: Add question flow tests
# TODO: Add widget integration tests
```

## IMMEDIATE PRIORITY: Fix Function Calling

### 🚨 Critical Issue

The Semantic Kernel function calling mechanism is not working. LLM describes what it wants to do but doesn't execute registered functions. Also we would like to have an llm managed process flow where llm decide which actions to take but prompt chaining when necessary

### Required Testing

Before proceeding with any new features, we must verify:

1. **Function Registration**: Are functions properly registered with `@kernel_function`?
2. **Function Invocation**: Does LLM actually call registered functions?
3. **Data Updates**: Do function calls result in JSON updates?
4. **Widget Triggers**: Can LLM trigger widget interfaces?

### Test Case Requirements

```python
# Test 1: Simple function calling
def test_function_calling():
    # LLM should call get_user_status() automatically
    # Verify function is actually invoked, not just described

# Test 2: Data updates
def test_data_updates():
    # LLM should call update_user_data("age", "25")
    # Verify user_data.json is actually updated

# Test 3: Widget integration
def test_widget_integration():
    # LLM should call ask_question("gender", "contextual message")
    # Verify widget interface is triggered
```

## REVISED PHASE 2 BREAKDOWN

### Phase 2A-1: Fix Function Calling (CRITICAL)

**Goal**: Make LLM actually invoke registered functions
**Success Criteria**:

- [ ] LLM calls `get_user_status()` automatically
- [ ] LLM calls `update_user_data()` and JSON is updated
- [ ] LLM calls `ask_question()` and widget is triggered
- [ ] Test with simple, single-function scenarios

### Phase 2A-2: Single Question Flow

**Goal**: Complete one question end-to-end
**Success Criteria**:

- [ ] LLM asks one question (e.g., age)
- [ ] LLM extracts answer from user input
- [ ] LLM updates user_data.json with correct value
- [ ] Process works for both free-form and widget questions

### Phase 2A-3: Full Question Sequence

**Goal**: Complete all 13 questions automatically
**Success Criteria**:

- [ ] LLM progresses through questions 1-13 in order
- [ ] LLM provides contextual responses for each question
- [ ] All user_data.json fields are populated
- [ ] Process completes without manual intervention

### Phase 2A-4: Action Recommendations (FUTURE)

**Goal**: Only after questions work perfectly
**Success Criteria**:

- [ ] LLM analyzes completed user data
- [ ] LLM generates personalized health recommendations
- [ ] Actions are properly filtered and prioritized

## Current Architecture

### File Structure

```
/agents/
├── prompts/
│   └── main_prompt.txt       # ✅ Comprehensive LLM prompt
├── health_agent.py           # ✅ Main agent with Semantic Kernel
└── data_handler.py           # ✅ Data operations + function calling

/ui/
├── chat_ui.py                # ✅ Terminal UI formatting
└── widgets/
    └── widget_handler.py     # ✅ Widget interface logic

/utils/
├── api_tracker.py            # ✅ API cost tracking
└── conversation_manager.py   # ✅ Conversation history

/data/
├── questions.json            # ✅ 13 questions configuration
├── conversations/            # ✅ Session-based conversation files
└── user/
    └── user_data.json        # ✅ Unified data structure
```

### Data Structure (UPDATED)

```json
{
  "user_id": "user",
  "user_name": "Name",
  "data_fields": {
    "age": {
      "value": null,
      "type": "free_form",
      "permissions": "read_write"
    },
    "gender": {
      "value": null,
      "type": "widget",
      "permissions": "read_only"
    }
  }
}
```

### Function Calling Architecture

**Approach**: Semantic Kernel function calling (NOT MCP)
**Functions Available**:

- `get_user_status()` - Get curated progress summary
- `update_user_data()` - Update free-form fields (age, height, weight)
- `ask_question()` - Auto-detect widget vs free-form and handle
- `get_questions()` - Get questions overview
- `get_question_details()` - Get specific question details

## Key Architectural Decisions

### 1. Function Calling Over MCP

**Decision**: Use Semantic Kernel function calling instead of MCP
**Reason**: More direct integration, simpler architecture
**Status**: Implemented but not working

### 2. Unified Data Structure

**Decision**: Single `user_data.json` instead of separate mutable/immutable files
**Reason**: Simpler to manage, cleaner architecture
**Status**: Implemented and working

### 3. UI Separation

**Decision**: Move all UI components to `/ui/` folder
**Reason**: Better separation of concerns
**Status**: Implemented and working

### 4. Session-Based Conversations

**Decision**: Separate conversation files for each session
**Reason**: Better session management, cleaner history
**Status**: Implemented and working

## API Cost Tracking

The project includes comprehensive API cost tracking:

```python
from utils.api_tracker import APITracker, tracked_invoke

# Initialize tracker
api_tracker = APITracker(provider="gemini")

# Use tracked invoke for all API calls
result = await tracked_invoke(
    kernel, function, input_text, model_id,
    api_tracker, "Description"
)

# View usage summary
api_tracker.print_summary()
```

**Cost Comparison**:

- Gemini 2.0-flash-lite: ~$0.000005/call (PRIMARY - most cost-effective)
- OpenAI gpt-4o-mini: ~$0.000020/call (4x more expensive but 20% faster)

## Development Principles

1. **Fix Function Calling First**: Nothing else works without this
2. **Incremental Testing**: Test each component independently
3. **Small Scope**: Focus on questions only, not actions
4. **Cost Awareness**: Always use API tracker for monitoring
5. **Data Integrity**: Respect mutable/immutable boundaries
6. **User-Centric**: Focus on natural conversation flow
7. **⚠️ AVOID REGEX/HARD-CODED EXTRACTION**: Use LLM-based extraction

## Testing Strategy

### Critical Tests Needed

1. **Function Calling Tests**

   - Verify LLM actually invokes functions
   - Test each function independently
   - Validate return values and side effects

2. **Data Update Tests**

   - Test free-form field updates (age, height, weight)
   - Test widget field updates through ask_question
   - Validate JSON structure and persistence

3. **Question Flow Tests**
   - Test single question completion
   - Test question sequence progression
   - Test contextual responses

### Test Files to Create

```
/tests/
├── test_function_calling.py    # Test LLM function invocation
├── test_data_updates.py        # Test data persistence
├── test_question_flow.py       # Test question sequence
└── test_widget_integration.py  # Test widget workflow
```

## Data Model Reference

### Questions (13 total)

- **Free-form** (3): age, height, weight → LLM can read/write
- **Widget-based** (10): gender, sleep, stress, wellbeing, activity, sugar, water_consumption, smoking, supplements, parenting → LLM read-only

### Question Flow Order

1. age (free-form)
2. gender (widget)
3. height (free-form)
4. weight (free-form)
5. sleep (widget)
6. stress (widget)
7. wellbeing (widget)
8. activity (widget)
9. sugar (widget)
10. water_consumption (widget)
11. smoking (widget)
12. supplements (widget)
13. parenting (widget)

## Next Steps for Implementation

### Immediate Actions

1. **Debug Function Calling**: Why isn't LLM invoking functions?
2. **Test Simple Function**: Start with basic `get_user_status()` call
3. **Verify Data Updates**: Ensure JSON files are actually modified
4. **Test Widget Integration**: Verify widget interface triggers

### Success Metrics

- LLM automatically calls functions without being asked
- Data updates are persisted to JSON files
- Widget interface is triggered by LLM
- Question flow progresses automatically

### Risk Mitigation

- **Start Small**: Test one function at a time
- **Incremental Progress**: Don't attempt full flow until basics work
- **Document Failures**: Record what doesn't work and why
- **Test Frequently**: Validate each change before proceeding

## Important Notes

- **Main Issue**: Function calling is broken - LLM describes but doesn't execute
- **Data Structure**: Unified user_data.json with permissions model
- **Architecture**: Clean separation but function calling doesn't work
- **Testing**: Must verify function calling before any new features
- **Scope**: Focus on questions only, actions come later
