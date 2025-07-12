# Implementation Flow Documentation

## High-Level Architecture & Module Flow

This document provides a visual reference for the onboarding assistant's architecture, showing module dependencies, separation of concerns, and operational modes.

## System Architecture Flow

```mermaid
graph TD
    CLI[CLI: python app.py --test --debug] --> APP[app.py]

    subgraph "Entry Point & Orchestration"
        APP --> |"Creates & initializes"| AGENT[core/agent.py]
        APP --> |"Creates UI handler"| CONV[ConversationHandler]
        APP --> |"Detects flags"| FLAGS{{"TEST_MODE = --test<br/>DEBUG_MODE = --debug"}}
    end

    subgraph "Core Logic Layer"
        AGENT --> |"Sets up kernel"| REGISTRY[core/tool_registry.py]
        AGENT --> |"Loads templates"| PROMPT[prompts/prompt_manager.py]
        AGENT --> |"Manages sessions"| SESSION[memory/session_manager.py]
        AGENT --> |"Tracks telemetry"| TELEMETRY[monitoring/telemetry.py]
    end

    subgraph "Tool Layer"
        REGISTRY --> |"Registers functions"| DATAMGR[tools/data_manager.py]
        DATAMGR --> |"Loads data"| DATA[("data/data.json")]
        DATAMGR --> |"Loads widget config"| WCONFIG[("data/widget_config.json")]
        DATAMGR --> |"Lazy loads for widgets"| WIDGET[ui/widget_handler.py]
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

## Widget System Flow

```mermaid
sequenceDiagram
    participant LLM as LLM (GPT-4o-mini)
    participant DM as DataManager
    participant WH as WidgetHandler
    participant UI as ChatUI
    participant TD as test.json

    Note over LLM,TD: Widget Automation Flow

    LLM->>DM: ask_question(field="weight", message="What is your weight?")
    DM->>DM: _is_widget_field("weight") → True
    DM->>WH: WidgetHandler() (lazy load)
    DM->>WH: show_widget_interface(question)

    alt TEST_MODE = True
        WH->>TD: Load test data
        TD-->>WH: {"weight": "70kg"}
        WH->>UI: print_widget_box(options, selected="70kg")
        WH-->>DM: return "70kg"
        DM->>DM: update_data("weight", "70kg")
        DM-->>LLM: "[USER_ANSWERED] weight: User selected 70kg via widget"
    else Normal Mode
        WH->>UI: print_widget_box(options)
        WH->>WH: input("Select option:")
        WH->>UI: print_widget_box(options, selected)
        WH-->>DM: return selected_value
        DM->>DM: update_data("weight", selected_value)
        DM-->>LLM: "[USER_ANSWERED] weight: User selected {value} via widget"
    end
```

## Data Flow & Dependencies

```mermaid
graph TD
    subgraph "Configuration Files"
        WC[widget_config.json<br/>Field: weight<br/>Options: 50kg-100kg]
        TD[test.json<br/>age: "I'm 25 years old"<br/>weight: "70kg"<br/>height: "I'm 170cm tall"]
    end

    subgraph "Runtime Data"
        UD[data.json<br/>age: 25<br/>weight: "70kg"<br/>height: null]
        SF[session_files<br/>Conversation blocks<br/>Function calls<br/>Token usage]
        TF[telemetry_files<br/>LLM requests<br/>Function execution<br/>Performance metrics]
    end

    subgraph "Application Flow"
        APP[app.py] --> |"TEST_MODE reads"| TD
        DM[data_manager.py] --> |"Reads/writes"| UD
        DM --> |"Reads config"| WC
        WH[widget_handler.py] --> |"TEST_MODE reads"| TD
        AGENT[agent.py] --> |"Saves sessions"| SF
        TEL[telemetry.py] --> |"Saves metrics"| TF
    end

    %% Show data relationships
    TD -.->|"Provides test responses"| WH
    WC -.->|"Defines widget fields"| DM
    UD -.->|"Current user state"| AGENT
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

### 5. **Widget Transparency to LLM**

- Widgets appear as completed `ask_question + update_data` calls
- LLM sees: `"[USER_ANSWERED] weight: User selected 70kg via widget"`
- Prevents re-asking for already completed widget fields

## File Responsibility Summary

| File                        | Primary Responsibility                  | Secondary Features                    |
| --------------------------- | --------------------------------------- | ------------------------------------- |
| `app.py`                    | Main orchestration, ConversationHandler | Test mode detection, CLI entry        |
| `core/agent.py`             | Conversation flow, LLM interaction      | Debug logging, session management     |
| `core/tool_registry.py`     | Kernel setup, function registration     | Debug prints, telemetry setup         |
| `tools/data_manager.py`     | Data operations, widget detection       | Function logging, session tracking    |
| `ui/widget_handler.py`      | Widget UI, test automation              | Test mode detection, option selection |
| `ui/chat_ui.py`             | Pure display functions                  | Terminal formatting, widget boxes     |
| `memory/session_manager.py` | Session blocks, conversation history    | Token tracking, debug info            |
| `prompts/prompt_manager.py` | Template loading, prompt building       | Greeting selection, debug info        |
| `monitoring/telemetry.py`   | Event capture, performance tracking     | File export, structured logging       |

This architecture follows the **separation of concerns** principle with clear boundaries between UI, business logic, infrastructure, and data layers.
