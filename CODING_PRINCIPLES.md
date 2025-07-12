# Coding Principles & Design Philosophy

## Core Philosophy

### **Reduce Over-Engineering**

- Keep functionality high while maintaining simplicity
- Follow what is going on - code should be easy to trace and understand
- Functionality first - never reduce features, only reduce complexity

### **Simplicity Guidelines**

- **Avoid nested loops** - Keep control flow straightforward
- **Minimize try-catch blocks** - Use them sparingly, prefer explicit checks
- **Avoid complex data type definitions** - Keep data structures simple
- **Keep things lean but functional** - Remove redundancy without losing capability

### **Development Approach**

- **Fail fast in development** - Don't hide problems with fallbacks
- **No silent failures** - If something is wrong, crash immediately with clear errors
- **Future-proof design** - Don't hardcode values that might expand (like field names)
- **Extensibility matters** - Code should handle new requirements without major rewrites

## Coding Style

### **Functions & Logic**

- **Concise implementations** - Prefer direct, readable code over complex abstractions
- **Unified error handling** - Consolidate repetitive error patterns into helper methods
- **Single responsibility** - Each function should do one thing well
- **Pythonic patterns** - Use list comprehensions, direct validation, EAFP principle

### **Comments & Documentation**

- **Concise but informative** - Explain the "why" not the "what"
- **Token-conscious** - Keep comments brief to avoid consuming too many tokens
- **Architectural clarity** - Document important design decisions (like dual tracking)
- **Future developer focused** - Comments should help someone understand intent quickly

### **Error Handling**

- **Explicit validation** - Check conditions directly rather than catching exceptions for control flow
- **Clear error messages** - Tell exactly what went wrong and what was expected
- **No redundant fallbacks** - If a core file/dependency is missing, fail immediately

### **Code Organization**

- **Helper methods for repetition** - Extract common patterns into reusable functions
- **Logical grouping** - Related functionality should be co-located
- **Consistent patterns** - Once you establish a pattern, follow it throughout
- **Avoid duplication** - Unless it serves different purposes (like dual tracking)
- **Code separation of concerns** - UI display, business logic, and orchestration should be in separate files
- **File responsibility clarity** - Each file should have one clear purpose (e.g., `chat_ui.py` for display only, not input handling)

### **Telemetry & Debugging**

- **Comprehensive but clean** - Capture everything needed but don't clutter the main logic
- **Unified logging patterns** - Consistent structure across all logging
- **Observability matters** - Track both requests and actual execution for full picture
- **Development vs Production** - Different approaches for different environments

## Session Starter Prompt

```
I follow these design principles:
- Reduce over-engineering while keeping functionality high
- Avoid nested loops, excessive try-catch blocks, and complex data types
- Fail fast in development - no silent fallbacks for missing core files
- Keep code concise, readable, and future-proof
- Use unified error handling and consistent patterns
- Comments should be brief but explain architectural decisions
- Prefer Pythonic approaches (list comprehensions, EAFP, direct validation)
- Don't remove features, only reduce complexity and redundancy
```

## Key Examples from This Codebase

### **Dual Tracking Architecture**

We implement two-stage function call tracking:

- **Stage 1 (Agent)**: Track what LLM requests
- **Stage 2 (DataManager)**: Track what actually executes
- **Purpose**: Debug LLM behavior vs execution failures vs routing issues

### **Fail-Fast Template Loading**

```python
# GOOD - Fail immediately with clear error
with open(filepath, 'r') as f:
    content = f.read()

# BAD - Silent fallback hides problems
try:
    with open(filepath, 'r') as f:
        content = f.read()
except FileNotFoundError:
    content = "fallback content"  # Hides real issues
```

### **Unified Helper Methods**

Extract repetitive patterns:

```python
def _handle_error(self, error_type, field, value, message):
    """Unified error handling with logging"""
    print(f"   ❌ {message}")
    self._log_function_call("function_name", inputs, {"result": message},
                           {"success": False, "error_type": error_type})
    return message
```

### **Concise Data Processing**

```python
# GOOD - List comprehension with clear intent
recorded_section = [
    "=== RECORDED USER DATA ===",
    "\n".join([f"- {field.capitalize()}: {value}" for field, value in filled.items()])
    if filled else "• No data recorded yet"
]

# BAD - Verbose loops with repetitive logic
for field, value in filled.items():
    if field == "age":
        status_report.append(f"- Age: {value}")
    elif field == "weight":
        status_report.append(f"- Weight: {value}")
    # ... repetitive patterns
```
