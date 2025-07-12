# Implementation Flow Documentation

## High-Level Architecture & Module Flow

This document provides a visual reference for the onboarding assistant's architecture, showing module dependencies, separation of concerns, and operational modes.

## System Architecture Flow

```mermaid
graph TD
    CLI[CLI: python app.py --test --debug] --> APP[app.py]

    subgraph "Entry Point & Orchestration"
        APP --> |"Creates & initializes"| AGENT[core/agent.py]
        APP --> |"Creates conversation handler"| CONV[ConversationHandler<br/>Post-response widget execution]
        APP --> |"Detects flags"| FLAGS{{"TEST_MODE = --test<br/>DEBUG_MODE = --debug"}}
        CONV --> |"Orchestrates widget timing"| WIDGET_EXEC[Widget Execution<br/>After LLM Response]
    end

    subgraph "Core Logic Layer"
        AGENT --> |"Sets up kernel"| REGISTRY[core/tool_registry.py]
        AGENT --> |"Loads templates"| PROMPT[prompts/prompt_manager.py]
        AGENT --> |"Manages sessions"| SESSION[memory/session_manager.py]
        AGENT --> |"Tracks telemetry"| TELEMETRY[monitoring/telemetry.py]
        SESSION --> |"Includes stage manager"| STAGE_MGR[ConversationStageManager<br/>Widget flagging & tracking]
    end

    subgraph "Tool Layer"
        REGISTRY --> |"Registers functions"| DATAMGR[tools/data_manager.py]
        DATAMGR --> |"Loads data"| DATA[("data/data.json")]
        DATAMGR --> |"Loads widget config"| WCONFIG[("data/widget_config.json")]
        DATAMGR --> |"Flags widgets via stage manager"| STAGE_MGR
        STAGE_MGR --> |"Triggers post-response"| WIDGET[ui/widget_handler.py]
    end

    subgraph "UI Layer"
        CONV --> |"Uses display functions"| CHATUI[ui/chat_ui.py]
        WIDGET --> |"Uses display functions"| CHATUI
        CONV --> |"Loads test data"| TESTDATA[("data/test.json")]
    end

    subgraph "Data Layer"
        DATA
        WCONFIG
        TESTDATA
        SESSION_FILES[("data/sessions/*.json")]
        TELEMETRY_FILES[("data/telemetry/*")]
    end

    %% Mode Detection
    FLAGS -.->|"Module-level detection"| WIDGET
    FLAGS -.->|"Parameter threading"| AGENT

    %% Data Flow
    SESSION --> SESSION_FILES
    TELEMETRY --> TELEMETRY_FILES

    %% Widget Flow
    DATAMGR -->|"Widget field detected"| WIDGET
    WIDGET -->|"Auto-selects in test mode"| WCONFIG
    WIDGET -->|"Reads test values"| TESTDATA
```

## Separation of Concerns

```mermaid
graph LR
    subgraph "🎯 UI Layer"
        UI1[chat_ui.py<br/>Pure Display Functions]
        UI2[widget_handler.py<br/>Widget UI & Automation]
    end

    subgraph "🧠 Business Logic"
        BL1[agent.py<br/>Conversation Flow]
        BL2[data_manager.py<br/>Data Operations]
        BL3[prompt_manager.py<br/>Template Management]
    end

    subgraph "🔧 Infrastructure"
        INF1[tool_registry.py<br/>Kernel Setup]
        INF2[session_manager.py<br/>Session Tracking]
        INF3[telemetry.py<br/>Monitoring]
    end

    subgraph "🎭 Orchestration"
        ORCH[app.py<br/>Main Entry Point<br/>ConversationHandler]
    end

    subgraph "💾 Data"
        DATA1[data.json<br/>User Data]
        DATA2[widget_config.json<br/>Widget Metadata]
        DATA3[test.json<br/>Test Responses]
    end

    ORCH --> UI1
    ORCH --> BL1
    BL1 --> INF1
    BL1 --> BL3
    BL1 --> INF2
    BL2 --> UI2
    BL2 --> DATA1
    BL2 --> DATA2
    UI2 --> DATA3
    INF1 --> BL2
    BL1 --> INF3
```

## Mode Detection & Control Flow

```mermaid
graph TD
    START[Application Start] --> DETECT{Detect CLI Flags}

    DETECT -->|"--test"| TEST_MODE[TEST_MODE = True]
    DETECT -->|"--debug"| DEBUG_MODE[DEBUG_MODE = True]
    DETECT -->|"normal"| NORMAL_MODE[Normal Operation]

    subgraph "Test Mode Behavior"
        TEST_MODE --> TEST_APP[app.py: Uses test.json responses]
        TEST_MODE --> TEST_WIDGET[widget_handler.py: Auto-selects options]
        TEST_APP --> TEST_SEQ[Sequential test inputs]
        TEST_WIDGET --> TEST_AUTO[Automated widget selection]
    end

    subgraph "Debug Mode Behavior"
        DEBUG_MODE --> DEBUG_AGENT[agent.py: Enhanced logging]
        DEBUG_MODE --> DEBUG_KERNEL[tool_registry.py: Function tracing]
        DEBUG_MODE --> DEBUG_TELEMETRY[telemetry.py: Full capture]
        DEBUG_MODE --> DEBUG_DATA[data_manager.py: Function logging]
    end

    subgraph "Normal Mode Behavior"
        NORMAL_MODE --> NORMAL_CONV[Interactive conversation]
        NORMAL_MODE --> NORMAL_WIDGET[Manual widget selection]
        NORMAL_MODE --> NORMAL_MINIMAL[Minimal logging]
    end

    %% Override Options
    JUPYTER[Jupyter Override] -.->|"ui.widget_handler.TEST_MODE = True"| TEST_WIDGET
```

## Widget System Flow (POST-RESPONSE EXECUTION)

```mermaid
sequenceDiagram
    participant LLM as LLM (GPT-4o-mini)
    participant DM as DataManager
    participant SM as StageManager
    participant CH as ConversationHandler
    participant WH as WidgetHandler
    participant UI as ChatUI
    participant TD as test.json

    Note over LLM,TD: NEW: Widget Flagging & Post-Response Execution

    %% Block 1: LLM Question Phase
    LLM->>DM: ask_question(field="weight", message="What is your weight?")
    DM->>DM: _is_widget_field("weight") → True
    DM->>SM: flag_widget_needed(widget_info)
    Note over SM: Widget flagged for post-response execution
    DM-->>LLM: "[ASKING] weight: What is your weight?"
    LLM-->>CH: "Thank you! What's your weight?"

    Note over CH,UI: LLM response shown to user FIRST
    CH->>UI: print_agent_message("Thank you! What's your weight?")

    %% Block Separation: Widget executes AFTER LLM response
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
    LLM-->>CH: "Thank you! Now, could you tell me your height?"
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

    style OLD_LLM fill:#ffcccc
    style NEW_LLM fill:#ccffcc
    style NEW_WIDGET fill:#ffffcc
    style NEW_HIDDEN fill:#ccccff
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

### 1. **Module-Level Mode Detection**

- `TEST_MODE = "--test" in sys.argv` in `ui/widget_handler.py`
- Avoids parameter threading through multiple layers
- Supports Jupyter override: `ui.widget_handler.TEST_MODE = True`

### 2. **Dual Tracking Architecture**

- **Stage 1 (Agent)**: Tracks LLM requests and responses
- **Stage 2 (DataManager)**: Tracks actual function execution
- Purpose: Debug LLM behavior vs execution vs routing issues

### 3. **Lazy Loading Pattern**

- WidgetHandler only loaded when widget field detected
- Prevents unnecessary imports and initialization

### 4. **Fail-Fast Principle**

- Template loading fails immediately if files missing
- No silent fallbacks that hide configuration issues

### 5. **Hidden Context Injection Pattern**

- Widget completions inject hidden context to prevent duplicate LLM calls
- LLM receives: `"CRITICAL: DO NOT call update_data for weight - it was already updated via widget to 70kg"`
- Context is invisible to chat UI but guides LLM behavior
- Prevents double-updating data fields from widget automation

### 6. **Widget Block Separation**

- Each question-answer cycle gets its own conversation block
- Widget execution happens BETWEEN blocks, not within blocks
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

## File Responsibility Summary

| File                        | Primary Responsibility                    | Secondary Features                        |
| --------------------------- | ----------------------------------------- | ----------------------------------------- |
| `app.py`                    | ConversationHandler orchestration         | Post-response widget execution, CLI entry |
| `core/agent.py`             | LLM interaction, hidden context injection | Session management, block completion      |
| `core/tool_registry.py`     | Kernel setup, function registration       | Debug prints, telemetry setup             |
| `tools/data_manager.py`     | Data operations, widget flagging          | Stage manager integration, dual tracking  |
| `ui/widget_handler.py`      | Widget UI, test automation                | Post-response execution, auto-updates     |
| `ui/chat_ui.py`             | Pure display functions                    | Terminal formatting, widget boxes         |
| `memory/session_manager.py` | Session blocks, ConversationStageManager  | Widget flagging, hidden context storage   |
| `prompts/prompt_manager.py` | Template loading, prompt building         | Greeting selection, debug info            |
| `monitoring/telemetry.py`   | Event capture, performance tracking       | Widget execution tracking, file export    |

This architecture follows the **separation of concerns** principle with clear boundaries between UI, business logic, infrastructure, and data layers.
