# PLANNER AGENT - Strategic Health Data Collection System

A sophisticated health data collection and recommendation system that uses strategic questioning, BMI calculation, and personalized health insights delivered through an empathetic Turkish persona.

## 🏗️ Architecture Overview

**PLANNER AGENT** → **Turkish Agent (Nora)** → **User Interface**

- **PLANNER AGENT**: Strategic health data collection with BMI calculation and intelligent question ordering
- **Turkish Agent (Nora)**: Empathetic Turkish persona that translates and adds warmth to interactions
- **Widget System**: Interactive UI components for data collection
- **Recommendation Engine**: Priority-based health advice using actions.json conditions

## 🚀 Quick Start

### Installation

#### 1. Open Terminal (macOS)
- Press `Cmd + Space`, type "Terminal", press Enter

#### 2. Create Setup Directory and Script
```bash
# Create heltia directory in your home folder
mkdir ~/heltia

# Create setup script file
touch ~/heltia/setup.sh

# Make it executable
chmod +x ~/heltia/setup.sh

# Open the heltia directory in Finder
open ~/heltia
```

#### 3. Copy Setup Script Content
1. **Open the setup.sh file** you just created (double-click it in Finder)
2. **Copy the setup script content** from: https://github.com/PoyrazTahan/onboarding_assistant/blob/main/setup.sh
3. **Paste the content** into your setup.sh file and save it

#### 4. Run Setup Script
```bash
# Navigate to heltia directory and run setup
cd ~/heltia
./setup.sh
```

#### 5. Add Your OpenAI API Key
**After setup completes, edit the .env file:**
```bash
# Open the environment file
nano ~/heltia/onboarding_assistant/.env
```

**Replace `your-openai-api-key-here` with your actual OpenAI API key from https://platform.openai.com/api-keys**

#### 6. Activate Environment and Start Using
```bash
# Activate the conda environment
conda activate planner_agent

# Navigate to project directory
cd ~/heltia/onboarding_assistant

# Run the PLANNER AGENT
python app.py
```

### Basic Usage
```bash
# Interactive mode with Turkish persona
python app.py

# Debug mode with telemetry
python app.py --debug

# Core agent mode (English only, no Turkish translation)
python app.py --core-agent
```

## 🎮 Operation Modes

### 1. **Interactive Mode (Default) - app.py**
```bash
python app.py
```

**What it does:**
- Real user interaction with Turkish persona (Nora)
- Strategic question ordering based on user responses
- Widget-based data collection for specific fields
- Empathetic responses with health insights
- Final personalized recommendations

**Input:** User types responses in Turkish or English
**Output:** 
- Turkish conversational responses from Nora
- Interactive widgets for data selection
- Personalized health recommendations
- Session saved to `data/sessions/session_YYYYMMDD_HHMMSS.json`

**Example Flow:**
```
🇹🇷 Turkish Persona Mode: Empathetic Turkish responses
Merhaba! Ben Nora. Sağlık hedeflerin için sana eşlik etmek üzere buradayım. Nasıl gidiyor? 😊
> [User input] Merhaba, iyiyim teşekkürler
```

### 2. **Automated Testing - test.py**
```bash
# Run all automated tests
python test.py

# List available test scenarios
python test.py list

# Run specific test by number
python test.py run <test_number>
```

**What it does:**
- Automated testing using predefined test scenarios from `data/test.json`
- **Core Agent only** (no Turkish translation) for faster, technical testing
- Widget auto-selection without user interaction
- Complete data collection simulation with validation

**Input:** Test scenarios with predefined inputs from `data/test.json`
**Output:**
- Raw English responses from PLANNER AGENT
- Test validation results (PASS/FAIL)
- Session results saved to `.test_results/` directory
- Data completion statistics

**Test Data Format (data/test.json):**
```json
{
  "test_scenarios": [
    {
      "name": "Young Female Professional",
      "profile": "young_professional",
      "existing_data": {
        "age": 25,
        "gender": "Female"
      },
      "inputs": {
        "weight": "65kg",
        "height": "170cm",
        "stress_level": "Often"
      },
      "expected_result": {
        "age": 25,
        "weight": 65.0,
        "height": 170.0,
        "gender": "Female",
        "stress_level": "Often"
      }
    }
  ]
}
```

### 3. **Debug Mode - app.py** 
```bash
# Interactive mode with debug logging
python app.py --debug

# Interactive mode with debug + core agent (no Turkish)
python app.py --debug --core-agent
```

**What it does:**
- All functionality of interactive mode
- Comprehensive telemetry logging
- Detailed function call tracking
- Prompt evolution monitoring
- Performance metrics collection

**Input:** Same as interactive mode
**Output:**
- Same as interactive mode PLUS:
- `data/telemetry/telemetry_structured_YYYYMMDD_HHMMSS.log`
- `data/telemetry/telemetry_data.json`
- `data/telemetry/telemetry_dump_YYYYMMDD_HHMMSS.log`
- Console output with detailed logging

**Debug Information Includes:**
- LLM prompt evolution tracking
- Function call execution details
- Token usage statistics
- Session block analysis
- Turkish agent processing logs

### 4. **Core Agent Mode - app.py**
```bash
# Interactive mode without Turkish translation  
python app.py --core-agent
```

**What it does:**
- Bypasses Turkish agent completely
- Shows raw PLANNER AGENT responses in English
- Direct function call visibility
- Debugging without translation layer

**Input:** User types responses (any language)
**Output:**
- Raw English responses from PLANNER AGENT
- Direct function call results
- No Turkish translation or empathy layer
- Technical/strategic decision visibility

**Example Output:**
```
⚙️ Core Agent Mode: Raw English responses with function calls
Thank you for providing your age. Based on your profile, I'd like to ask about your weight next to calculate your BMI for health insights. What is your current weight in kilograms?
```

## 🔄 Available Modes Summary

### Interactive Modes (app.py)
```bash
# Default: Turkish persona with Nora
python app.py

# English only (no Turkish translation)
python app.py --core-agent

# Turkish with debug logging
python app.py --debug

# English with debug logging
python app.py --debug --core-agent
```

### Automated Testing (test.py - Separate Script)
```bash
# Run all automated tests
python test.py

# List available test scenarios
python test.py list

# Run specific test by number  
python test.py run 3
```

**Note**: Testing is handled by a separate `test.py` script, not through `app.py --test`. The test script automatically runs in Core Agent mode (English only) for faster, technical validation.

## 🧪 Complete Test Suite Usage

### Understanding Test Structure
The test suite loads scenarios from `data/test.json` where each scenario can:
- Pre-fill some data fields (`existing_data`)
- Provide automated responses (`inputs`) 
- Validate final results (`expected_result`)

### Test Commands
```bash
# See all available tests with profiles
python test.py list

# Run all tests (gets summary with pass/fail counts)
python test.py

# Run a specific test (e.g., test #3)
python test.py run 3
```

### Test Output
- ✅/❌ Pass/Fail status for each test
- Data completion statistics  
- Mismatch details for failed tests
- Session results saved to `.test_results/` directory

## 📊 Data Management

### Input Data Files
- **`data/data.json`**: Current user data (13 health fields)
- **`data/test.json`**: Test automation responses
- **`data/widget_config.json`**: Widget UI configurations
- **`data/actions.json`**: Health recommendation conditions

### Output Data Files
- **`data/sessions/session_*.json`**: Complete conversation logs
- **`data/recommendations.json`**: Final health recommendations with justifications
- **`data/telemetry/*`**: Debug logs and performance metrics

### 13 Health Data Fields
1. **age** (integer)
2. **weight** (float, kg)
3. **height** (float, cm)
4. **gender** (string)
5. **has_children** (string)
6. **sleep_quality** (string)
7. **stress_level** (string)
8. **mood_level** (string)
9. **activity_level** (string)
10. **sugar_intake** (string)
11. **water_intake** (string)
12. **smoking_status** (string)
13. **supplement_usage** (string)

## 🎯 PLANNER AGENT Features

### Strategic Question Ordering
- **Context-Aware**: Responds to user mentions (e.g., "stressed" → immediate stress_level question)
- **Health Pattern Clustering**: Groups related questions (stress→sleep→mood)
- **BMI-Driven Decisions**: Calculates BMI and prioritizes relevant follow-ups
- **Pregnancy Priority**: Immediate focus on sleep and supplements for pregnant users

### Health Insights & Recommendations
- **BMI Calculation**: Automatic calculation with category classification
- **Risk Factor Analysis**: Identifies high-priority health concerns
- **Condition Matching**: Uses actions.json to match user profile to recommendations
- **Priority Classification**: HIGH/MEDIUM/LOW priority recommendations

### Example Strategic Decisions
```
User says: "I'm pregnant" 
→ PLANNER immediately asks about sleep_quality (pregnancy priority)

User BMI calculated as 27
→ PLANNER prioritizes activity_level and sugar_intake questions

User mentions: "I feel stressed"
→ PLANNER jumps to stress_level assessment
```

## 🌍 Turkish Agent (Nora) Features

### Personality & Communication
- **Empathetic Responses**: "Bu aralar stresli hissetmen ne kadar zor olmalı..."
- **Strategic Explanation**: Explains why PLANNER chose specific questions
- **WhatsApp-Style Flow**: Multiple short messages for natural conversation
- **Health Context Awareness**: BMI reactions, pregnancy empathy, age-appropriate responses

### Multi-Message Response Examples
```xml
<ChatBox>
25! Çok gençsin! 🎉
</ChatBox>
<ChatBox>
BMI'ni hesaplamak için kilonu öğrenmek istiyorum. Bu hem genel sağlığın hem de özel öneriler için çok değerli.
</ChatBox>
<ChatBox>
Kilon kaç kilo? 😊
</ChatBox>
```

## 🛠️ Troubleshooting

### Common Issues

**1. Setup Script Permission Denied**
```bash
# Make sure the script is executable
chmod +x setup.sh
```

**2. Conda Command Not Found (After Setup)**
```bash
# Restart terminal or source conda
source ~/.bashrc  # or ~/.zshrc for zsh users
# OR restart Terminal app completely
```

**3. OpenAI API Key Missing**
```bash
# Edit the .env file and add your key
nano ~/heltia/onboarding_assistant/.env
```

**4. Environment Activation Issues**
```bash
# If conda activate doesn't work, try:
source ~/miniconda3/etc/profile.d/conda.sh
conda activate planner_agent
```

**5. Widget Not Displaying**
- Check `data/widget_config.json` for field configuration
- Verify field is enabled: `"enabled": true`

**6. Test Mode Not Working**
- Verify `data/test.json` contains test scenarios
- Check JSON syntax validity

**7. Turkish Agent Errors**
- Ensure `prompts/templates/turkish_persona_prompt.txt` exists
- Check for template variable mismatches

**8. Setup Script Fails**
```bash
# If setup fails, try running individual steps:
cd ~/heltia
git clone https://github.com/PoyrazTahan/onboarding_assistant.git
cd onboarding_assistant
conda create -n planner_agent python=3.11 -y
conda activate planner_agent
pip install -r requirements.txt
```

### Debug Commands
```bash
# Test specific mode combinations
python app.py --debug --test --core-agent

# Check session output
cat data/sessions/session_*.json | jq '.'

# Verify data collection
cat data/data.json

# Check recommendations
cat data/recommendations.json | jq '.recommendations'
```

## 📋 Development

### Project Structure
```
onboarding_assistant/
├── app.py                          # Main entry point
├── core/
│   ├── agent.py                    # PLANNER AGENT logic
│   ├── turkish_persona_agent.py    # Nora (Turkish agent)
│   └── tool_registry.py            # Kernel setup
├── tools/
│   └── data_manager.py             # Data operations, BMI, recommendations
├── prompts/templates/
│   ├── system_prompt.txt           # PLANNER AGENT instructions
│   └── turkish_persona_prompt.txt  # Nora's personality
├── data/
│   ├── data.json                   # User data
│   ├── test.json                   # Test responses
│   ├── actions.json                # Health recommendations
│   └── widget_config.json          # UI configurations
└── ui/
    ├── chat_ui.py                  # Display functions
    └── widget_handler.py           # Interactive widgets
```

### Adding New Features
1. **New Health Field**: Update `data.json`, `test.json`, and widget config
2. **New Recommendation**: Add conditions to `data/actions.json`
3. **New Widget**: Configure in `data/widget_config.json`
4. **New Strategic Logic**: Modify PLANNER AGENT in `prompts/templates/system_prompt.txt`

---

**Built with ❤️ for strategic health data collection and personalized wellness recommendations.**