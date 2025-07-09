# TODO Tracker - Onboarding Assistant

## Quick Status Overview

| Phase                          | Status         | Priority | Progress |
| ------------------------------ | -------------- | -------- | -------- |
| Phase 1A: Data Foundation      | ✅ COMPLETED   | HIGH     | 100%     |
| Phase 1B: API Integration      | ✅ COMPLETED   | HIGH     | 100%     |
| **Phase 2A: Monolithic Agent** | 🚧 IN PROGRESS | **HIGH** | **0%**   |
| Phase 2B: MCP Protocol Design  | ⏳ PENDING     | HIGH     | 0%       |
| Phase 3: Multi-Agent Split     | ⏳ PENDING     | MEDIUM   | 0%       |
| Phase 4: Advanced Features     | ⏳ PENDING     | LOW      | 0%       |

---

## 🎯 CURRENT PHASE: Phase 2A - Monolithic Agent Implementation

### Status: IN PROGRESS

### Priority: HIGH

### Description: Create single agent handling all operations before splitting

### Tasks:

- [ ] **Create agent prompt file** `/agents/prompts/monolith_agent.txt`
- [ ] **Implement conversation manager** with state tracking
- [ ] **Build data handler** for JSON read/write operations
- [ ] **Add text extraction utilities** for free-form fields (age, height, weight)
- [ ] **Create agent orchestration** logic in `agent_manager.py`
- [ ] **Test conversation flow** with all 13 questions
- [ ] **Implement action recommendation** based on user data
- [ ] **Add session state management**
- [ ] **Create integration tests** for full conversation

### Implementation Notes:

- Start with `main.py` as base (already has Semantic Kernel setup)
- Use `api_tracker.py` for all LLM calls
- Focus on natural conversation flow
- Handle both widget and free-form inputs

### Success Criteria:

- [ ] Agent can conduct full onboarding conversation
- [ ] Correctly extracts data from natural language
- [ ] Updates appropriate JSON files
- [ ] Recommends relevant health actions
- [ ] Maintains conversation context

---

## 📋 NEXT PHASE: Phase 2B - MCP Protocol Design

### Status: PENDING

### Priority: HIGH

### Description: Design MCP protocol for data operations and widget integration

### Planned Tasks:

- [ ] Define MCP tools structure
- [ ] Design LLM permission model
- [ ] Plan widget trigger operations
- [ ] Architect data access patterns
- [ ] Create MCP implementation spec
- [ ] Build prototype MCP tools
- [ ] Test permission boundaries
- [ ] Document MCP protocol

### Key Decisions Needed:

1. LLM permission enforcement strategy
2. Widget communication protocol
3. Data operation patterns (direct vs API-mediated)
4. Concurrent access handling

---

## 📅 FUTURE PHASES

### Phase 3: Multi-Agent Split

- **Status**: PENDING
- **Description**: Break monolith into specialized agents
- **Key Tasks**: Question agent, Answer agent, Action agent, Orchestrator

### Phase 4: Advanced Features

- **Status**: PENDING
- **Description**: Session recovery, database sync, advanced analytics
- **Key Tasks**: Two-layer persistence, timeout handling, performance optimization

---

## 📝 Notes for Current Work

### Working Directory Structure:

```
/agents/
├── prompts/
│   └── monolith_agent.txt    # CREATE FIRST
├── agent_manager.py          # Agent orchestration
└── data_handler.py           # JSON operations

/utils/
├── api_tracker.py            # ✅ Already exists
└── conversation_utils.py     # Text extraction
```

### Key Files to Reference:

- `main.py` - Semantic Kernel setup
- `data/questions.json` - 13 questions to ask
- `data/actions.json` - 12 actions to recommend
- `utils/api_tracker.py` - Cost tracking

### Remember:

1. Keep implementation simple and direct
2. Test with actual inputs/outputs
3. Document what works and what's placeholder
4. Note any discoveries or changes needed
5. Update this tracker with results

### Success Metrics:

- Phase produces working code
- Can demonstrate functionality with test cases
- Clear handoff to next phase
- No over-engineering or premature optimization

---

_Last Updated: Phase 2A started, ready for implementation_
