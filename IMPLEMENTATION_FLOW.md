# Implementation Flow Documentation

## High-Level Architecture & Module Flow

This document provides a visual reference for the onboarding assistant's architecture, showing module dependencies, separation of concerns, and operational modes.

## 🔍 Architecture Overview (Simplified)

```mermaid
graph LR
    USER[User Input<br/>Turkish/English] --> PLANNER[PLANNER AGENT<br/>Strategic Health Logic]
    PLANNER --> TURKISH[Turkish Agent<br/>Context + Translation]
    TURKISH --> UI[User Interface<br/>Turkish Output]

    PLANNER --> WIDGETS[Widget System<br/>Data Collection]
    PLANNER --> RECOMMENDATIONS[Health Recommendations<br/>Priority-Based]
    WIDGETS --> TURKISH

    style PLANNER fill:#1976d2,stroke:#ffffff,color:#ffffff
    style TURKISH fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style WIDGETS fill:#f57c00,stroke:#ffffff,color:#ffffff
    style RECOMMENDATIONS fill:#4caf50,stroke:#ffffff,color:#ffffff
```

**Key Flow**: User speaks any language → PLANNER AGENT processes strategically → Turkish Agent adds empathy and translates → User sees warm Turkish responses with personalized health recommendations

## System Architecture Flow (Detailed)

```mermaid
graph TD
    CLI[CLI: python app.py --test --debug --core-agent] --> APP[app.py]

    subgraph "Entry Point & Orchestration"
        APP --> |"Creates & initializes"| AGENT[core/agent.py]
        APP --> |"Creates conversation handler"| CONV[ConversationHandler<br/>Turkish agent integration]
        APP --> |"Detects flags"| FLAGS{{"TEST_MODE = --test<br/>DEBUG_MODE = --debug<br/>CORE_AGENT_MODE = --core-agent"}}
        CONV --> |"Orchestrates widget timing"| WIDGET_EXEC[Widget Execution<br/>After LLM Response]
        CONV --> |"Routes through Turkish agent"| TURKISH_AGENT[core/turkish_persona_agent.py]
    end

    subgraph "Translation Layer (NEW)"
        TURKISH_AGENT --> |"Loads persona template"| TURKISH_PROMPT[prompts/templates/turkish_persona_prompt.txt]
        TURKISH_AGENT --> |"Analyzes conversation"| SESSION_CONTEXT[Session Context Analysis]
        TURKISH_AGENT --> |"Multi-message output"| TURKISH_RESPONSE[Turkish Multi-Message<br/>Response Generation]
        TURKISH_AGENT --> |"Integrates with telemetry"| TELEMETRY[monitoring/telemetry.py]
    end

    subgraph "PLANNER AGENT Layer (Enhanced)"
        AGENT --> |"Sets up kernel"| REGISTRY[core/tool_registry.py]
        AGENT --> |"Loads templates"| PROMPT[prompts/prompt_manager.py]
        AGENT --> |"Manages sessions"| SESSION[memory/session_manager.py]
        AGENT --> |"Direct chat completion"| CHAT[Direct Chat Service<br/>No competing functions]
        AGENT --> |"Tracks telemetry"| TELEMETRY
        SESSION --> |"Includes stage manager"| STAGE_MGR[ConversationStageManager<br/>Widget flagging & tracking]
        PROMPT --> |"Loads greeting instructions"| GREETING_TEMPLATES[prompts/templates/greeting_files]
    end

    subgraph "Enhanced Tool Layer"
        REGISTRY --> |"Registers functions"| DATAMGR[tools/data_manager.py<br/>BMI + Health Insights]
        DATAMGR --> |"Loads 13-field data"| DATA[("data/data.json")]
        DATAMGR --> |"Loads widget config"| WCONFIG[("data/widget_config.json")]
        DATAMGR --> |"Loads health actions"| ACTIONS[("data/actions.json")]
        DATAMGR --> |"Strategic recommendations"| RECOMMENDATIONS[("data/recommendations.json")]
        DATAMGR --> |"Flags widgets via stage manager"| STAGE_MGR
        STAGE_MGR --> |"Triggers post-response"| WIDGET[ui/widget_handler.py]
    end

    subgraph "UI Layer"
        TURKISH_RESPONSE --> |"Displays Turkish messages"| CHATUI[ui/chat_ui.py]
        WIDGET --> |"Uses display functions"| CHATUI
        CONV --> |"Loads test data"| TESTDATA[("data/test.json")]
    end

    subgraph "Enhanced Data Layer"
        DATA
        WCONFIG
        ACTIONS
        RECOMMENDATIONS
        TESTDATA
        SESSION_FILES[("data/sessions/*.json")]
        TELEMETRY_FILES[("data/telemetry/*")]
    end

    %% Mode Detection
    FLAGS -.->|"Module-level detection"| WIDGET
    FLAGS -.->|"Parameter threading"| AGENT
    FLAGS -.->|"Bypass Turkish agent"| CONV

    %% Data Flow
    SESSION --> SESSION_FILES
    TELEMETRY --> TELEMETRY_FILES

    %% Widget Flow
    DATAMGR -->|"Widget field detected"| WIDGET
    WIDGET -->|"Auto-selects in test mode"| WCONFIG
    WIDGET -->|"Reads test values"| TESTDATA

    %% Turkish Agent Flow
    SESSION_CONTEXT --> TURKISH_RESPONSE
    GREETING_TEMPLATES --> TURKISH_AGENT

    style TURKISH_AGENT fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style TURKISH_RESPONSE fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style GREETING_TEMPLATES fill:#f57c00,stroke:#ffffff,color:#ffffff
```

## 🔍 Separation of Concerns (Simplified)

```mermaid
graph TB
    UI[🎯 UI Layer<br/>Display & Interaction]
    TRANSLATION[🌍 Translation Layer<br/>Turkish Persona Agent]
    BUSINESS[🧠 Business Logic<br/>Core Agent & Data]
    INFRA[🔧 Infrastructure<br/>Sessions & Monitoring]

    UI --> TRANSLATION
    TRANSLATION --> BUSINESS
    BUSINESS --> INFRA

    style TRANSLATION fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style BUSINESS fill:#1976d2,stroke:#ffffff,color:#ffffff
    style UI fill:#388e3c,stroke:#ffffff,color:#ffffff
    style INFRA fill:#f57c00,stroke:#ffffff,color:#ffffff
```

## Separation of Concerns (Detailed)

```mermaid
graph LR
    subgraph "🎯 UI Layer"
        UI1[chat_ui.py<br/>Pure Display Functions]
        UI2[widget_handler.py<br/>Widget UI & Automation]
    end

    subgraph "🌍 Translation Layer (NEW)"
        TL1[turkish_persona_agent.py<br/>Context-Aware Translation]
        TL2[turkish_persona_prompt.txt<br/>Personality & Empathy Rules]
        TL3[greeting_new.txt<br/>New User Instructions]
        TL4[greeting_return.txt<br/>Returning User Instructions]
    end

    subgraph "🧠 Business Logic"
        BL1[agent.py<br/>Conversation Flow]
        BL2[data_manager.py<br/>Data Operations]
        BL3[prompt_manager.py<br/>Template Management]
        BL4[system_prompt.txt<br/>English-Only Core Logic]
    end

    subgraph "🔧 Infrastructure"
        INF1[tool_registry.py<br/>Kernel Setup]
        INF2[session_manager.py<br/>Session Tracking]
        INF3[telemetry.py<br/>Monitoring]
    end

    subgraph "🎭 Orchestration"
        ORCH[app.py<br/>Main Entry Point<br/>ConversationHandler<br/>Turkish Agent Integration]
    end

    subgraph "💾 Data"
        DATA1[data.json<br/>User Data]
        DATA2[widget_config.json<br/>Widget Metadata]
        DATA3[test.json<br/>Test Responses]
    end

    ORCH --> TL1
    ORCH --> UI1
    ORCH --> BL1
    TL1 --> TL2
    TL1 --> UI1
    BL1 --> INF1
    BL1 --> BL3
    BL1 --> INF2
    BL3 --> TL3
    BL3 --> TL4
    BL3 --> BL4
    BL2 --> UI2
    BL2 --> DATA1
    BL2 --> DATA2
    UI2 --> DATA3
    INF1 --> BL2
    BL1 --> INF3
    TL1 --> INF3

    style TL1 fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style TL2 fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style TL3 fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style TL4 fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style BL4 fill:#1976d2,stroke:#ffffff,color:#ffffff
```

## 🔍 Mode Detection Overview (Simplified)

```mermaid
graph LR
    FLAGS[CLI Flags] --> TEST[--test<br/>Automated]
    FLAGS --> DEBUG[--debug<br/>Verbose]
    FLAGS --> CORE[--core-agent<br/>English Only]
    FLAGS --> NORMAL[Normal<br/>Turkish UI]

    style TEST fill:#388e3c,stroke:#ffffff,color:#ffffff
    style DEBUG fill:#f57c00,stroke:#ffffff,color:#ffffff
    style CORE fill:#1976d2,stroke:#ffffff,color:#ffffff
    style NORMAL fill:#7b1fa2,stroke:#ffffff,color:#ffffff
```

## Mode Detection & Control Flow (Detailed)

```mermaid
graph TD
    START[Application Start] --> DETECT{Detect CLI Flags}

    DETECT -->|"--test"| TEST_MODE[TEST_MODE = True]
    DETECT -->|"--debug"| DEBUG_MODE[DEBUG_MODE = True]
    DETECT -->|"--core-agent"| CORE_AGENT_MODE[CORE_AGENT_MODE = True]
    DETECT -->|"normal"| NORMAL_MODE[Normal Operation]

    subgraph "Test Mode Behavior"
        TEST_MODE --> TEST_APP[app.py: Uses test.json responses]
        TEST_MODE --> TEST_WIDGET[widget_handler.py: Auto-selects options]
        TEST_MODE --> TEST_TURKISH[Turkish agent: Context-aware responses]
        TEST_APP --> TEST_SEQ[Sequential test inputs]
        TEST_WIDGET --> TEST_AUTO[Automated widget selection]
        TEST_TURKISH --> TEST_EMPATHY[Empathetic Turkish output]
    end

    subgraph "Debug Mode Behavior"
        DEBUG_MODE --> DEBUG_AGENT[agent.py: Enhanced logging]
        DEBUG_MODE --> DEBUG_KERNEL[tool_registry.py: Function tracing]
        DEBUG_MODE --> DEBUG_TELEMETRY[telemetry.py: Full capture]
        DEBUG_MODE --> DEBUG_DATA[data_manager.py: Function logging]
        DEBUG_MODE --> DEBUG_TURKISH[turkish_persona_agent.py: Context logging]
    end

    subgraph "Core Agent Mode Behavior (NEW)"
        CORE_AGENT_MODE --> CORE_BYPASS[Bypass Turkish agent]
        CORE_AGENT_MODE --> CORE_ENGLISH[Show raw English responses]
        CORE_AGENT_MODE --> CORE_FUNCTIONS[Display function calls directly]
        CORE_AGENT_MODE --> CORE_DEBUG[Debug core logic without translation]
    end

    subgraph "Normal Mode Behavior"
        NORMAL_MODE --> NORMAL_CONV[Interactive conversation]
        NORMAL_MODE --> NORMAL_WIDGET[Manual widget selection]
        NORMAL_MODE --> NORMAL_TURKISH[Turkish persona responses]
        NORMAL_MODE --> NORMAL_MINIMAL[Minimal logging]
    end

    %% Override Options
    JUPYTER[Jupyter Override] -.->|"ui.widget_handler.TEST_MODE = True"| TEST_WIDGET

    style CORE_AGENT_MODE fill:#1976d2,stroke:#ffffff,color:#ffffff
    style CORE_BYPASS fill:#1976d2,stroke:#ffffff,color:#ffffff
    style CORE_ENGLISH fill:#1976d2,stroke:#ffffff,color:#ffffff
    style CORE_FUNCTIONS fill:#1976d2,stroke:#ffffff,color:#ffffff
    style CORE_DEBUG fill:#1976d2,stroke:#ffffff,color:#ffffff
    style TEST_TURKISH fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style DEBUG_TURKISH fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style NORMAL_TURKISH fill:#7b1fa2,stroke:#ffffff,color:#ffffff
```

## 🔍 Widget Flow Overview (Simplified)

```mermaid
graph LR
    PLANNER[PLANNER AGENT<br/>Ask Question] --> WIDGET[Widget<br/>Collects Data]
    WIDGET --> TURKISH[Turkish Agent<br/>Translates Response]
    TURKISH --> USER[User Sees<br/>Turkish UI]

    style PLANNER fill:#1976d2,stroke:#ffffff,color:#ffffff
    style WIDGET fill:#f57c00,stroke:#ffffff,color:#ffffff
    style TURKISH fill:#7b1fa2,stroke:#ffffff,color:#ffffff
    style USER fill:#388e3c,stroke:#ffffff,color:#ffffff
```

## Widget System Flow with Turkish Agent (Detailed)

```mermaid
sequenceDiagram
    participant LLM as Core Agent (English)
    participant DM as DataManager
    participant SM as StageManager
    participant CH as ConversationHandler
    participant TA as TurkishAgent
    participant WH as WidgetHandler
    participant UI as ChatUI
    participant TD as test.json

    Note over LLM,TD: Turkish Agent Integration with Widget System

    %% Block 1: LLM Question Phase
    LLM->>DM: ask_question(field="weight", message="What is your weight?")
    DM->>DM: _is_widget_field("weight") → True
    DM->>SM: flag_widget_needed(widget_info)
    Note over SM: Widget flagged for post-response execution
    DM-->>LLM: "[ASKING] weight: What is your weight?"
    LLM-->>CH: "Thank you! What's your weight?" (English)

    %% NEW: Turkish Agent Translation
    Note over CH,TA: Turkish Agent Processes English Response
    CH->>TA: translate_to_persona(english_response, session_context)
    TA->>TA: analyze_conversation_context()
    TA->>TA: determine_data_status(age/weight/height)
    TA->>TA: generate_empathetic_response()
    TA-->>CH: ["Süper! 😊", "Şimdi de kilondan bahsedelim mi?"] (Turkish, Multi-message)

    Note over CH,UI: Turkish response shown to user FIRST
    CH->>UI: print_agent_message("Süper! 😊")
    CH->>UI: print_agent_message("Şimdi de kilondan bahsedelim mi?")

    %% Block Separation: Widget executes AFTER Turkish response
    CH->>SM: get_pending_widget()
    SM-->>CH: widget_info (flagged widget)
    CH->>WH: _execute_widget_and_get_user_input(widget_info)
    WH->>WH: WidgetHandler() (lazy load)
    WH->>WH: show_widget_interface(question_structure)

    alt TEST_MODE = True
        WH->>TD: Load test data
        TD-->>WH: {"weight": "70kg"}
        WH->>UI: print_widget_box(options, selected="70kg")
        WH-->>CH: return "70kg"
    else Interactive Mode
        WH->>UI: print_widget_box(options)
        WH->>WH: input("Select option:")
        WH->>UI: print_widget_box(options, selected)
        WH-->>CH: return selected_value
    end

    %% Widget completion handling
    CH->>DM: update_data("weight", "70kg")
    DM-->>CH: "Updated weight to 70kg"
    CH->>SM: Store widget_completion (hidden context)

    %% Block 2: User Response Phase (NEW BLOCK)
    CH->>CH: Use widget selection as next user_input
    CH->>UI: print_user_message("70kg")

    %% Hidden context injection prevents duplicate updates
    CH->>LLM: process_user_input("70kg") + HIDDEN_CONTEXT
    Note over LLM: "CRITICAL: DO NOT call update_data for weight - already updated"
    LLM-->>CH: "Thank you! Now, could you tell me your height?" (English)

    %% Turkish Agent processes next response
    CH->>TA: translate_to_persona("Thank you! Now, could you tell me your height?", updated_context)
    TA-->>CH: ["Perfect! Kilonu kaydettim 📝", "Şimdi boyunu merak ediyorum!"] (Turkish)
    CH->>UI: print_agent_message("Perfect! Kilonu kaydettim 📝")
    CH->>UI: print_agent_message("Şimdi boyunu merak ediyorum!")

```

## Stage Manager & Widget Flagging Architecture

```mermaid
graph TD
    subgraph "Session Management Layer"
        SESSION[Session] --> BLOCKS[Conversation Blocks]
        SESSION --> SM[ConversationStageManager]
    end

    subgraph "Stage Manager Components"
        SM --> CORE_TRACKING[Core Stage Tracking<br/>• current_stage<br/>• last_question_field<br/>• function_call_log]
        SM --> TEST_MODE[Test Automation<br/>• test_data<br/>• pending_test_response]
        SM --> WIDGET_MGT[Widget Management<br/>• pending_widget<br/>• widget_completion]
    end

    subgraph "Widget Flagging Flow"
        DM[DataManager.ask_question] -->|Widget detected| FLAG[flag_widget_needed]
        FLAG --> PENDING[pending_widget stores:<br/>• field<br/>• message<br/>• widget_config<br/>• question_structure]

        CH[ConversationHandler] -->|Post-response| CHECK[get_pending_widget]
        CHECK --> EXECUTE[_execute_widget_and_get_user_input]
        EXECUTE --> COMPLETION[Store widget_completion]
        COMPLETION --> HIDDEN[Hidden LLM context injection]
    end

    subgraph "Block Separation Pattern"
        BLOCK1[Block 1: LLM Question<br/>• ask_question flagged<br/>• LLM responds<br/>• Widget executed]
        BLOCK2[Block 2: User Response<br/>• Widget selection as input<br/>• Hidden context injected<br/>• LLM continues]

        BLOCK1 --> WIDGET_EXECUTION[Widget Execution<br/>Between Blocks]
        WIDGET_EXECUTION --> BLOCK2
    end

    %% Connections
    SM -->|Manages| WIDGET_MGT
    WIDGET_MGT -->|Enables| FLAG
    PENDING -->|Retrieved by| CH
    COMPLETION -->|Prevents duplicate| HIDDEN
```

## Block Separation & Conversation Flow

```mermaid
graph LR
    subgraph "OLD: Immediate Widget Execution"
        OLD_LLM[LLM Response] --> OLD_WIDGET[Widget Executes<br/>SAME BLOCK]
        OLD_WIDGET --> OLD_UPDATE[Update Data<br/>SAME BLOCK]
        OLD_UPDATE --> OLD_CONTINUE[Continue Response<br/>SAME BLOCK]
    end

    subgraph "NEW: Post-Response Widget Execution"
        NEW_LLM[LLM Response] --> NEW_BLOCK_END[Block 1 Complete]
        NEW_BLOCK_END --> NEW_WIDGET[Widget Executes<br/>BETWEEN BLOCKS]
        NEW_WIDGET --> NEW_UPDATE[Update Data<br/>BETWEEN BLOCKS]
        NEW_UPDATE --> NEW_BLOCK_START[Block 2 Starts]
        NEW_BLOCK_START --> NEW_HIDDEN[Hidden Context<br/>Prevents Duplicates]
    end

    style OLD_LLM fill:#d32f2f,stroke:#ffffff,color:#ffffff
    style NEW_LLM fill:#388e3c,stroke:#ffffff,color:#ffffff
    style NEW_WIDGET fill:#f57c00,stroke:#ffffff,color:#ffffff
    style NEW_HIDDEN fill:#1976d2,stroke:#ffffff,color:#ffffff
```

## Data Flow & Dependencies

```mermaid
graph TD
    subgraph "Configuration Files"
        WC[widget_config.json<br/>Field: weight<br/>Options: 50kg-100kg]
        TD[test.json<br/>age: I am 25 years old<br/>weight: 70kg<br/>height: I am 170cm tall]
    end

    subgraph "Runtime Data"
        UD[data.json<br/>age: 25<br/>weight: 70kg<br/>height: null]
        SF[session_files<br/>Conversation blocks<br/>Function calls<br/>Token usage]
        TF[telemetry_files<br/>LLM requests<br/>Function execution<br/>Performance metrics]
    end

    subgraph "Application Flow"
        APP[app.py] --> |"TEST_MODE reads"| TD
        DM[data_manager.py] --> |"Reads/writes"| UD
        DM --> |"Reads config"| WC
        DM --> |"Flags widgets"| SM[stage_manager.py]
        SM --> |"Post-response execution"| WH[widget_handler.py]
        WH --> |"TEST_MODE reads"| TD
        AGENT[agent.py] --> |"Saves sessions"| SF
        TEL[telemetry.py] --> |"Saves metrics"| TF
    end

    subgraph "Widget Completion Flow"
        WH --> |"Auto-updates data"| UD
        WH --> |"Stores completion"| SM
        SM --> |"Hidden context injection"| AGENT
    end

    %% Show data relationships
    TD -.->|"Provides test responses"| WH
    WC -.->|"Defines widget fields"| DM
    UD -.->|"Current user state"| AGENT
    SM -.->|"Prevents duplicate updates"| AGENT
```

## Key Design Patterns

### 1. **PLANNER AGENT Strategic Architecture (NEW)**

- Strategic question ordering based on user context (stress→sleep, pregnancy→supplements)
- BMI calculation and health insights for intelligent recommendations
- Priority-based recommendation system (HIGH/MEDIUM/LOW)
- Actions.json condition matching for personalized advice

### 2. **Direct Chat Completion (Critical Fix)**

- Eliminated competing chat_plugin functions causing random LLM behavior
- Direct `chat_service.get_chat_message_contents()` with FunctionChoiceBehavior.Auto()
- Fixes inconsistent widget chains and data persistence issues

### 3. **13-Field Enhanced Data Model**

- Expanded from basic fields to comprehensive health data collection
- Enhanced field validation and type conversion (BMI calculation)
- Strategic completion detection for recommendation phase

### 4. **Module-Level Mode Detection**

- `TEST_MODE = "--test" in sys.argv` in `ui/widget_handler.py`
- Avoids parameter threading through multiple layers
- Supports Jupyter override: `ui.widget_handler.TEST_MODE = True`

### 5. **Dual Tracking Architecture**

- **Stage 1 (Agent)**: Tracks LLM requests and responses
- **Stage 2 (DataManager)**: Tracks actual function execution
- Purpose: Debug LLM behavior vs execution vs routing issues

### 6. **Hidden Context Injection Pattern**

- Widget completions inject hidden context to prevent duplicate LLM calls
- LLM receives: `"CRITICAL: DO NOT call update_data for weight - it was already updated via widget to 70kg"`
- Context is invisible to chat UI but guides LLM behavior
- Prevents double-updating data fields from widget automation

### 7. **Widget Block Separation with Recursion**

- Each question-answer cycle gets its own conversation block
- Widget execution happens BETWEEN blocks, not within blocks
- Recursive widget handling for broken widget call chains
- Maintains clean conversation flow while preserving all functionality

## Hidden Context Injection Mechanism

```mermaid
sequenceDiagram
    participant WH as WidgetHandler
    participant SM as StageManager
    participant CH as ConversationHandler
    participant AGENT as Agent
    participant LLM as LLM

    Note over WH,LLM: Preventing Duplicate LLM Updates

    WH->>SM: Store widget_completion<br/>{field: "weight", selected_value: "70kg", update_result: "Updated weight to 70kg"}
    CH->>AGENT: process_user_input("70kg", turn_number)
    AGENT->>SM: get_and_clear_widget_completion()
    SM-->>AGENT: widget_completion data

    AGENT->>AGENT: Build hidden_context string<br/>"CRITICAL: DO NOT call update_data for weight - already updated via widget to 70kg"
    AGENT->>AGENT: Append to prompt<br/>prompt = prompt + hidden_context

    AGENT->>LLM: Send prompt with hidden context
    Note over LLM: Sees hidden instructions, skips duplicate update
    LLM-->>AGENT: "Thank you for providing your weight of 70kg! Now, could you tell me your height?"

    Note over CH: User sees normal conversation<br/>Hidden context is invisible
```

This mechanism ensures:

- **No duplicate updates**: Widget auto-updates are not repeated by LLM
- **Seamless UX**: Hidden context is invisible to chat interface
- **LLM guidance**: Clear instructions prevent confused behavior
- **State synchronization**: Widget completion data is properly cleared after use

## Additional Design Patterns (Updated)

### 8. **Turkish Agent Translation Layer with PLANNER Integration (Enhanced)**

- **PLANNER-Aware Translation**: Turkish agent understands PLANNER's strategic decisions and explains them naturally
- **Context-Aware Empathy**: Analyzes BMI, health insights, and strategic question choices for appropriate responses
- **Multi-Message Responses**: Single English response becomes multiple Turkish messages for natural WhatsApp-style flow
- **Strategic Explanation**: Explains why PLANNER chose specific questions (stress→sleep, BMI→activity)
- **Core Agent Bypass**: `--core-agent` mode allows debugging without translation layer

### 9. **Recommendation Processing Pipeline (NEW)**

- **XML Parsing**: Structured recommendation parsing from PLANNER AGENT responses
- **Priority Filtering**: Only HIGH priority recommendations shown to users
- **File Persistence**: Saves structured recommendations to `data/recommendations.json`
- **Justification Tracking**: Records decision rationale and risk factor analysis

## File Responsibility Summary (Updated)

| File                                           | Primary Responsibility                                               | Secondary Features                                                   |
| ---------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `app.py`                                       | ConversationHandler orchestration, Turkish agent integration         | Post-response widget execution, CLI entry, mode detection            |
| `core/agent.py`                                | **Direct chat completion, hidden context injection**                 | **Session management, block completion**                             |
| `core/turkish_persona_agent.py`                | **PLANNER-aware Turkish translation, strategic empathy**             | **Multi-message generation, BMI context analysis**                   |
| `core/tool_registry.py`                        | **Kernel setup, function registration (no competing functions)**     | Debug prints, telemetry setup                                        |
| `tools/data_manager.py`                        | **PLANNER AGENT operations, BMI calculation, recommendation engine** | **13-field validation, actions.json processing, strategic insights** |
| `ui/widget_handler.py`                         | Widget UI, test automation                                           | Post-response execution, auto-updates                                |
| `ui/chat_ui.py`                                | Pure display functions                                               | Terminal formatting, widget boxes                                    |
| `memory/session_manager.py`                    | Session blocks, ConversationStageManager                             | Widget flagging, hidden context storage                              |
| `prompts/prompt_manager.py`                    | Template loading, prompt building                                    | Greeting selection, debug info                                       |
| `prompts/templates/system_prompt.txt`          | **PLANNER AGENT strategic health logic**                             | **BMI-driven decisions, actions.json awareness**                     |
| `prompts/templates/turkish_persona_prompt.txt` | **Empathetic Turkish persona with PLANNER integration**              | **Strategic explanation, WhatsApp-style responses**                  |
| `prompts/templates/greeting_new.txt`           | **Instructions to Turkish agent for new users**                      | **Architectural clarity**                                            |
| `prompts/templates/greeting_return.txt`        | **Instructions to Turkish agent for returning users**                | **User state awareness**                                             |
| `monitoring/telemetry.py`                      | Event capture, performance tracking                                  | Widget execution tracking, Turkish agent logging                     |

## Architecture Principles

This architecture follows the **separation of concerns** principle with clear boundaries between:

- **🎯 UI Layer**: Pure display functions
- **🌍 Translation Layer**: Turkish persona with context awareness
- **🧠 Business Logic**: English-only core agent and data operations
- **🔧 Infrastructure**: Sessions, monitoring, and widget management

**Key Innovation**: The Turkish Agent layer provides a sophisticated translation and personalization interface while maintaining clean separation between backend logic and frontend personality.
