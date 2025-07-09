# Medical & Psychological Health App - Implementation Plan

## Core Development Principles

- **Iterative Development**: No one-shot solutions, build incrementally
- **Simplicity First**: Avoid over-engineering, add complexity only when needed
- **Minimal Error Handling**: Start with happy path, add robustness later
- **Direct Implementation**: No custom types or complex data structures initially
- **Continuous Testing**: Run and verify each phase before moving forward

## Phase 1: Basic Pipeline Setup

**Goal**: Establish working connection between Semantic Kernel and Gemini API

### Tasks:

1. Set up basic Python project structure
2. Install Semantic Kernel and required dependencies
3. Create simple Gemini API integration
4. Test basic prompt-response flow

### Deliverables:

- `main.py` with basic Semantic Kernel setup
- `config.yaml` with API keys and basic settings
- Working API call that returns a response
- Simple test prompt: "Hello, I'm a health assistant"

### Placeholder Code Needed:

```python
# TODO: User needs to provide Gemini API integration code for Semantic Kernel
# Basic structure:
# kernel = semantic_kernel.Kernel()
# kernel.add_text_completion_service("gemini", ...)
# response = await kernel.run_async(prompt)
```

### Success Criteria:

- Can send a prompt to Gemini via Semantic Kernel
- Receives and prints response
- No complex error handling, just basic connection

## Phase 2: Simple Agent Structure

**Goal**: Create basic multi-agent system with fixed responses

### Tasks:

1. Create folder structure for agents
2. Implement simple agent loader
3. Create 3 basic agents with hardcoded behavior:
   - Question Picker (returns questions in fixed order)
   - Answer Handler (echoes user input with acknowledgment)
   - Action Picker (returns fixed action based on simple rules)

### Folder Structure:

```
/agents
  /prompts
    question_picker.txt
    answer_handler.txt
    action_picker.txt
/data
  questions.json
  actions.json
  sample_user_data.json
```

### Implementation Notes:

- Question Picker: Just return questions 1-13 in order
- Answer Handler: "Thank you for sharing that your [field] is [value]"
- Action Picker: If water < 8, suggest "Drink more water"

### Success Criteria:

- Can load and call different agents
- Each agent returns expected fixed response
- Basic orchestration works (call agents in sequence)

## Phase 3: Data Flow Implementation

**Goal**: Add basic read/write capabilities

### Tasks:

1. Create data folder structure as specified
2. Implement simple JSON read/write functions
3. Allow agents to read from data files
4. Create basic data update mechanism

### Data Structure:

```
/data
  /users
    /user_123
      AI_notes.txt
      AI_immutable.json
      AI_mutable.json
      session_state.json
```

### Implementation:

- Simple file I/O, no database yet
- JSON files with basic structure
- Direct read/write, no validation

### Success Criteria:

- Agents can read user data
- Answer Handler can write to AI_mutable.json
- Data persists between runs

## Phase 4: Answer Handler Agent (Priority)

**Goal**: Implement conversational interface

### Tasks:

1. Create prompt template for natural conversation
2. Implement widget vs free-form input detection
3. Add basic response generation
4. Connect to data writing capability

### Prompt Structure:

```
You are a friendly health assistant collecting user information.
Current question: {question}
User response: {user_input}
Previous context: {context}

Generate a warm, conversational response and extract the data value.
```

### Implementation Notes:

- Focus on conversation quality
- Extract structured data from responses
- Handle both widget inputs and free text
- Write updates to appropriate JSON files

### Success Criteria:

- Natural conversation flow
- Correctly extracts data from responses
- Updates user data files
- Handles all 13 question types

## Phase 5: Question State Management

**Goal**: Track conversation progress

### Tasks:

1. Implement question state tracker
2. Add logic to skip answered questions
3. Handle returning users
4. Create session persistence

### State Structure:

```json
{
  "questions_asked": ["age", "height"],
  "questions_answered": ["age"],
  "last_question": "height",
  "session_start": "2024-01-01T10:00:00"
}
```

### Implementation:

- Simple state file per user
- Check before asking questions
- Update after receiving answers

## Phase 6: Action Recommendation System

**Goal**: Basic health action suggestions

### Tasks:

1. Implement simple rule engine
2. Create action priority logic
3. Add recommendation tracking

### Simple Rules:

- If water_intake < 8: "Drink 8 glasses of water"
- If activity == "low": "Remember to move every hour"
- If stress > 7: "Try meditation for 10 minutes"

### Implementation:

- Hardcoded rules initially
- Simple if-then logic
- Track which actions were suggested

## Phase 7: Data Persistence Layer

**Goal**: Two-layer storage system

### Tasks:

1. Implement JSON layer for immediate updates
2. Add database sync placeholder
3. Create conflict resolution logic

### Note:

- Focus on JSON layer first
- Database integration can be mocked
- Simple timestamp-based conflict resolution

## Phase 8: Session Management

**Goal**: Handle interrupted sessions

### Tasks:

1. Add timeout detection
2. Implement session recovery
3. Create context restoration

## Phase 9: Advanced Features

**Goal**: Remaining functionality

### Potential Features:

- Dynamic question ordering
- Sophisticated action prioritization
- Advanced error handling
- Full database integration

## Instructions for Implementation Teams

### General Approach:

1. **Start Simple**: Each phase should produce working code, even if limited
2. **Test Continuously**: Run the system after each major change
3. **Document Assumptions**: Note what's hardcoded for later improvement
4. **Avoid Premature Optimization**: No complex error handling or type systems initially

### Code Style:

- Direct, readable code
- Minimal abstraction
- Comments only where necessary
- Focus on functionality over elegance

### Testing Each Phase:

- Create simple test scripts
- Use console output to verify behavior
- Manual testing is fine initially
- Document what works and what doesn't

### Missing Information Needed:

1. Exact Semantic Kernel + Gemini integration code
2. Specific data schema for user information
3. Complete list of 12 health actions
4. Widget interface specifications

### Next Steps:

- User provides missing integration details
- Start with Phase 1 implementation
- Iterate based on what works
- Adjust plan as system evolves
