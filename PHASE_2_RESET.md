# PHASE 2 RESET: LLM-Driven Question Orchestration

## 🚨 CRITICAL: Read This First

**Previous Phase 2 Failed Because:**
1. **Function calling was completely bypassed** - The code creates ad-hoc functions instead of using registered ones
2. **Hardcoded regex extraction logic** interfered with LLM intelligence
3. **Manual prompt construction** prevented automatic function execution
4. **No proper orchestration** - just descriptive responses without action

**The Root Cause (THIS IS THE MOST IMPORTANT THING TO UNDERSTAND):**
```python
# ❌ CURRENT BROKEN APPROACH (health_agent.py lines 130-146)
filled_prompt = prompt.replace("{user_input}", user_input)
# ... manual prompt construction ...
simple_function = self.kernel.add_function(
    function_name="widget_chat",
    plugin_name="widget_chat_plugin", 
    prompt=filled_prompt + "\n\nAsistan:"
)
```
This creates a NEW function each time, bypassing ALL registered functions!

## 🎯 Primary Objective

Create an intelligent onboarding assistant that:
1. **Actually executes functions** (not just describes them)
2. **Populates user_data.json** through natural conversation
3. **Progresses through 13 questions** autonomously
4. **Triggers widgets** when appropriate
5. **Extracts free-form answers** using LLM intelligence  

## 🔴 ROOT CAUSE ANALYSIS

### The Core Problem Explained

The current implementation **completely bypasses Semantic Kernel's function calling mechanism**. Here's what happens:

1. Functions are properly registered with `@kernel_function` decorator ✅
2. Functions are added to the kernel ✅
3. **BUT**: The chat method creates a NEW ad-hoc function every time ❌
4. This ad-hoc function only has the prompt, no access to registered functions ❌
5. Result: LLM can only describe what it would do, never execute ❌

### What Should Happen Instead

```python
# ✅ CORRECT APPROACH
from semantic_kernel.connectors.ai.google.gemini import GeminiPromptExecutionSettings

execution_settings = GeminiPromptExecutionSettings(
    service_id=self.service_id,
    auto_invoke_kernel_functions=True,
    function_call_behavior="auto"  # or "required"
)

# Let kernel handle everything - it will route to registered functions
result = await self.kernel.invoke_prompt(
    function_name="main_chat",
    plugin_name="chat_plugin",
    user_input=user_input,
    settings=execution_settings
)
```

## 🚀 IMPLEMENTATION STRATEGY

### Phase 2A-1: Fix Function Calling (CRITICAL - Do This First!)

**Goal**: Make LLM actually invoke registered functions

**Test First Approach**:
1. Create `test_function_calling.py`
2. Test ONLY `get_user_status()` function
3. Verify console shows "Function called: get_user_status"
4. If this doesn't work, STOP and debug

**Key Implementation Points**:
- Use Gemini 2.0 Flash (supports function calling)
- Enable auto_invoke_kernel_functions
- Remove ALL manual prompt construction
- Let Semantic Kernel handle function routing

### Phase 2A-2: Refactor health_agent.py

**Critical Changes Required**:

1. **Remove Manual Prompt Construction**
   ```python
   # DELETE all the manual prompt building (lines 130-146)
   # DELETE the ad-hoc function creation
   # Use kernel's native function calling
   ```

2. **Implement Proper Execution Settings**
   ```python
   from semantic_kernel.connectors.ai.google.gemini import GeminiPromptExecutionSettings
   
   execution_settings = GeminiPromptExecutionSettings(
       service_id=self.service_id,
       auto_invoke_kernel_functions=True,
       function_call_behavior="auto"  # or "required"
   )
   ```

3. **Use Native Invocation**
   ```python
   # Let kernel handle everything
   result = await self.kernel.invoke_prompt(
       function_name="main_chat",
       plugin_name="chat_plugin",
       user_input=user_input,
       settings=execution_settings
   )
   ```

### Phase 2A-3: Enhance Functions for LLM

**Make Functions LLM-Friendly**:

1. **get_user_status()** - Return structured JSON:
   ```json
   {
     "completed_questions": ["age", "gender"],
     "next_question": "height",
     "progress_percentage": 15,
     "all_questions_answered": false
   }
   ```

2. **update_user_data()** - Add validation feedback:
   ```python
   # Return success/failure with context
   return {
     "success": true,
     "field": "age",
     "value": "25",
     "message": "Age updated successfully"
   }
   ```

3. **ask_question()** - Smart detection:
   ```python
   # Auto-detect widget vs free-form
   if field_info["type"] == "widget":
       return trigger_widget(field, contextual_message)
   else:
       return {"waiting_for": field, "prompt": question_text}
   ```

## 🧠 THINKING PATTERNS FOR CODER AGENTS

### ✅ DO Think Like This:

1. **"How can I let the LLM decide?"**
   - Don't hardcode logic, expose functions
   - Give LLM tools, not rules

2. **"What would make this function call obvious to an LLM?"**
   - Clear function names
   - Descriptive return values
   - Contextual information

3. **"How can I test the smallest unit first?"**
   - Start with one function
   - Verify it executes
   - Then add complexity

### ❌ DON'T Think Like This:

1. **"I'll extract the age with regex"**
   - NO! Let LLM extract naturally
   - Trust LLM intelligence

2. **"I'll manually check which question to ask"**
   - NO! Let LLM read status and decide
   - Functions provide info, LLM makes decisions

3. **"I'll build the full prompt manually"**
   - NO! Use kernel's prompt template system
   - Let functions inject their context

## 📋 STEP-BY-STEP IMPLEMENTATION

### Step 1: Verify Function Calling Works

```python
# test_function_calling.py
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.google.gemini import GoogleAIGeminiChatCompletion
from agents.data_handler import DataHandler

async def test_basic_function():
    kernel = Kernel()
    # Setup Gemini connector
    # Register data_handler plugin
    # Try to invoke with "Show me user status"
    # MUST see "Function called: get_user_status" in output
```

**Success Criteria**: Function actually executes, not just described

### Step 2: Minimal Working Chat

```python
# Start with ONLY get_user_status working
# User: "What's my progress?"
# LLM: Calls get_user_status() → "You haven't answered any questions yet"
```

### Step 3: Add Update Capability

```python
# Add update_user_data function
# User: "I'm 25 years old"
# LLM: Calls update_user_data("age", "25") → Updates JSON
```

### Step 4: Question Flow

```python
# LLM checks status → sees age is filled → asks next question
# No hardcoded progression, LLM decides based on status
```

## 🚨 CRITICAL WARNINGS

### 1. Function Calling Must Work First
- If functions don't execute, NOTHING else matters
- Test with simplest function first
- Don't proceed until this works

### 2. No Hardcoded Extraction
```python
# ❌ NEVER DO THIS
if "years old" in user_input:
    age = re.findall(r'\d+', user_input)[0]

# ✅ DO THIS INSTEAD
# Let LLM extract through update_user_data function
```

### 3. Trust LLM Intelligence
- LLM can understand "I'm twenty-five" → 25
- LLM can understand "around 30ish" → 30
- LLM can understand context and intent

### 4. Avoid State Machines
```python
# ❌ NEVER DO THIS
if current_question == 1:
    ask_age()
elif current_question == 2:
    ask_gender()

# ✅ DO THIS INSTEAD
# LLM reads status and decides what to ask
```

## 🎯 SUCCESS METRICS

1. **Function Execution**: Console shows "Function called: X" messages
2. **Data Persistence**: user_data.json values change from null
3. **Natural Flow**: Questions progress without explicit commands
4. **Widget Triggers**: Widget UI appears for widget-type questions
5. **Completion**: All 13 fields populated after conversation

## 🛠️ DEBUGGING CHECKLIST

When things don't work:

1. **Functions Not Executing?**
   - Check execution settings
   - Verify function registration
   - Test with Gemini 2.0 Flash (not flash-lite)
   - Enable verbose kernel logging

2. **Data Not Updating?**
   - Check file permissions
   - Verify function return values
   - Check JSON structure matches

3. **Questions Not Progressing?**
   - Verify get_user_status returns next question
   - Check prompt includes progression instructions
   - Ensure LLM has conversation context

## 📝 PROMPT ENGINEERING TIPS

### Main Prompt Structure
```
You are a health assistant collecting user data.

AVAILABLE FUNCTIONS:
- get_user_status(): Check progress and next question
- update_user_data(field, value): Update free-form fields
- ask_question(field, message): Trigger questions (widget or free-form)

YOUR TASK:
1. Check user status to see what's needed
2. Ask questions naturally in conversation
3. Extract answers and update data
4. Progress through all questions

IMPORTANT:
- Always check status before asking questions
- Extract values naturally from conversation
- Use ask_question for widget fields
- Update free-form fields directly
```

## 🚀 FINAL THOUGHTS

**Remember**: The goal is to create an intelligent assistant that autonomously manages the conversation flow through function calls, not a scripted state machine.

**Key Success Factor**: Fix function calling first. Everything else depends on this working correctly.

**Mental Model**: Think of the LLM as the conductor of an orchestra (functions), not a player following sheet music (hardcoded logic).

**The Most Important Thing**: The current code creates ad-hoc functions instead of using registered ones. This MUST be fixed first.

## 📊 DATA MODEL REFERENCE

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

### User Data Structure

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
    // ... other fields
  }
}
```

---

*Phase 2 Reset - Focus on Intelligence, Not Scripts*