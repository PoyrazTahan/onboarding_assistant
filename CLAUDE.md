# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Onboarding Assistant** is a medical & psychological health app that uses LLM agents to collect user health data through conversational interactions and provides personalized health recommendations. 

**Current Status**: Phase 1 ✅ Complete | Phase 2A 🎯 Ready to Start

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
# Run primary implementation (Gemini - more cost-effective)
python main.py

# Run alternative implementation (OpenAI - faster but 4x more expensive)
cd archive && python main_openai.py

# Run data validation tests
python tests/test_data_structure.py
```

### Testing & Validation
```bash
# Validate data structure
python tests/test_data_structure.py

# TODO: Add linting when configured
# TODO: Add type checking when configured
```

## IMMEDIATE PRIORITY: Phase 2A - Monolithic Agent Implementation

### 🎯 What to Build First

Create a **single monolithic agent** that handles ALL operations before splitting into multiple agents. This follows our iterative development principle.

### Monolithic Agent Requirements

1. **Core Functionality**
   - Read user data from `AI_mutable.json` and `AI_immutable.json`
   - Conduct conversational onboarding for 13 health questions
   - Extract structured data from natural language responses
   - Write updates to appropriate JSON files
   - Recommend health actions based on user data

2. **Data Access Patterns**
   ```python
   # Agent can READ and WRITE (3 free-form fields)
   AI_mutable.json = {
       "age": int,      # Extract from "I'm twenty years old" → 20
       "height": int,   # Extract from "about 180cm tall" → 180
       "weight": int    # Extract from "seventy kilos" → 70
   }
   
   # Agent can only READ (10 widget fields)
   AI_immutable.json = {
       "gender": str,
       "sleep": int (1-10),
       "stress": int (1-10),
       "wellbeing": int (1-10),
       "activity": str,
       "sugar": str,
       "water_consumption": int,
       "smoking": str,
       "supplements": list,
       "parenting": str
   }
   ```

3. **Implementation Steps**
   - Start with `main.py` as base (already has Semantic Kernel + Gemini setup)
   - Create agent prompt in `/agents/prompts/monolith_agent.txt`
   - Implement conversation state management
   - Add data reading/writing utilities
   - Test with sample conversations

### Code Architecture

```
/agents/
├── prompts/
│   └── monolith_agent.txt    # Main agent prompt (CREATE THIS FIRST)
├── agent_manager.py          # Agent orchestration logic
└── data_handler.py           # JSON read/write operations

/utils/
├── api_tracker.py            # ✅ Already exists - use for cost tracking
└── conversation_utils.py     # Text extraction utilities
```

### Sample Agent Prompt Structure

```
You are a friendly health assistant collecting user information.
You have access to user data and must:
1. Ask questions naturally and conversationally
2. Extract structured data from responses
3. Update user records appropriately
4. Suggest relevant health actions

Current user data: {user_data}
Questions remaining: {unanswered_questions}
Current context: {conversation_history}

[Further instructions...]
```

## Phase 2B: MCP Architecture Design (AFTER Monolith Works)

### Critical Design Questions to Resolve

1. **LLM Permission Model**
   - How to enforce read-only access to `AI_immutable.json`?
   - Field-level vs file-level permissions?
   - Validation before writes to `AI_mutable.json`?

2. **Widget Integration via MCP**
   - How to trigger widget operations from agent?
   - Communication protocol between LLM and widgets?
   - State synchronization strategy?

3. **Data Operations Protocol**
   - Direct file I/O vs API-mediated access?
   - Concurrent access handling?
   - Transaction/rollback capabilities?

### MCP Implementation Considerations

```
# Proposed MCP Tools Structure
/mcp_tools/
├── read_user_data      # Read from both JSON files
├── write_mutable_data  # Write ONLY to AI_mutable.json
├── trigger_widget      # Activate UI widgets
├── get_widget_state    # Read widget values
└── write_notes         # Append to AI_notes.txt
```

## High-Level Architecture

### Data Flow
```
User Input → Monolith Agent → Data Extraction → Validation → Storage
                    ↓
            Action Analysis → Health Recommendations
```

### File Structure & Permissions
```
/data/users/user_001/
├── AI_mutable.json      # LLM READ/WRITE (age, height, weight)
├── AI_immutable.json    # LLM READ-ONLY (10 widget fields)
├── AI_notes.txt         # Conversation history
└── session_state.json   # Session tracking (LLM READ-ONLY)
```

### API Cost Tracking

The project includes comprehensive API cost tracking:

```python
from utils.api_tracker import APITracker, tracked_invoke

# Initialize tracker
api_tracker = APITracker(provider="gemini")  # or "openai"

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

## Testing Strategy

### Current Tests
- `tests/test_data_structure.py` - Validates JSON structure and data integrity

### Tests to Add for Phase 2A
- Conversation flow testing
- Data extraction accuracy
- Session state management
- Action recommendation logic

## Development Principles

1. **Iterative Development**: Build monolith first, split later
2. **Simplicity First**: No over-engineering or premature optimization
3. **Cost Awareness**: Always use API tracker for monitoring
4. **Data Integrity**: Respect mutable/immutable boundaries
5. **User-Centric**: Focus on natural conversation flow

## Data Model Reference

### Questions (13 total)
- **Free-form** (3): age, height, weight → `AI_mutable.json`
- **Widget-based** (10): gender, sleep, stress, wellbeing, activity, sugar, water_consumption, smoking, supplements, parenting → `AI_immutable.json`

### Actions (12 health recommendations)
Each action has:
- `trigger_conditions`: When to recommend
- `exclude_conditions`: When NOT to recommend (e.g., mammogram for males)
- `priority`: critical, high, medium, low
- `category`: hydration, smoking, activity, sleep, etc.

## Next Steps for Coder Agent

1. **Start with Phase 2A**: Create the monolithic agent
2. **Use existing code**: Build on `main.py` and `api_tracker.py`
3. **Test incrementally**: Run after each major change
4. **Track costs**: Use the API tracker for all LLM calls
5. **Document decisions**: Note what's hardcoded for later improvement

## Future Phases (After Phase 2B)

- **Phase 3**: Data persistence layer with database sync
- **Phase 4**: Advanced session management
- **Phase 5**: Multi-agent architecture (split monolith)
- **Phase 6**: Advanced features and optimizations

## Important Notes

- The project uses Turkish UI labels with English field names for better LLM processing
- Text-to-number conversion is critical for free-form fields ("twenty" → 20)
- Widget data comes from UI, not from LLM extraction
- Always validate extracted data before writing to `AI_mutable.json`
- Session state helps track conversation progress and unanswered questions