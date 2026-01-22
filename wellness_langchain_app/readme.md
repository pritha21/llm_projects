# Holistic Wellness Orchestrator 🌟

A comprehensive AI-powered wellness system that orchestrates specialized agents (Exercise, Mindfulness, Nutrition) to provide personalized health guidance.

## Features

### 🏋️ **Exercise Agent**
- **Personalized Workout Plans**: Custom weekly schedules based on fitness level (beginner-advanced)
- **Smart Context**: Adapts to available time (e.g., "3 days/week, 30 mins") and injuries
- **Video Integration**: Automatically provides YouTube follow-alongs for every exercise

### 🧘 **Mindfulness Agent**
- **Mental Wellness Support**: Guided meditations for stress, focus, sleep
- **Breathing Exercises**: Quick techniques for immediate relief
- **Crisis Support**: High-priority detection of self-harm/crisis keywords with immediate resource provision

### 🥗 **Nutrition Agent** (New!)
- **Meal Planning**: Weekly plans with calorie/macro targets
- **Smart Calculation**: auto-calculates BMR/TDEE based on profile
- **Goal Alignment**: Differentiates between weight loss, maintenance, and muscle gain
- **Recipe Suggestions**: Healthy recipes with cooking video links

### 🧠 **Intelligent Core**
- **Orchestrator Pattern**: Central brain routes requests using **Few-Shot Learning** (YAML-configured)
- **Multi-Agent Routing**: Handles complex requests (e.g., "workout plan + diet") by activating multiple agents
- **Memory Management**: 
  - Short-term conversation history
  - **Auto-Compaction**: Summarizes older conversations into long-term insights
- **User Profiles**: Persists demographics, injuries, and preferences

---

## Architecture

The system uses a **Hub-and-Spoke** architecture where the Orchestrator manages specialized sub-agents.

```mermaid
graph TD
    User[User Input] --> Orchestrator
    
    subgraph Core "The Brain"
        Orchestrator --> Router[YAML Router]
        Orchestrator --> Memory[Memory Manager]
        Orchestrator --> Profile[Profile Manager]
    end
    
    subgraph Agents "The Experts"
        Orchestrator --> Exercise[🏋️ Exercise Agent]
        Orchestrator --> Mindfulness[🧘 Mindfulness Agent]
        Orchestrator --> Nutrition[🥗 Nutrition Agent]
    end
    
    subgraph Tools "Capabilities"
        Exercise --> YT1[YouTube Search]
        Exercise --> GenPlan[Workout Planner]
        
        Mindfulness --> YT2[YouTube Search]
        Mindfulness --> Crisis[Crisis Resources]
        
        Nutrition --> YT3[YouTube Search]
        Nutrition --> Calc[Calorie Calc]
        Nutrition --> Plans[Meal Planner]
    end
```

---

## Project Structure

```text
wellness_langchain_app/
├── app_langchain.py          # Main CLI entry point
├── orchestrator.py           # Central logic & agent coordination
├── youtube_search.py         # Shared video search utility
├── requirements.txt
├── .env
│
├── config/
│   └── routing_examples.yaml # Few-shot routing examples
│
├── agents/                   # Specialized LangGraph/LangChain agents
│   ├── exercise_agent.py
│   ├── mindfulness_agent.py
│   └── nutrition_agent.py
│
├── tools/                    # Functional tools used by agents
│   ├── exercise_tools.py
│   ├── mindfulness_tools.py
│   └── nutrition_tools.py
│
├── memory/
│   ├── memory_manager.py     # Conversation history & compaction
│   └── profile_manager.py    # User JSON profile CRUD
│
└── data/                     # Local storage (git-ignored)
    ├── profiles/             # User profiles (json)
    └── memories/             # User interaction history (json)
```

---

## Setup & Usage

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file with your Groq API key:
```env
GROQ_API_KEY=your_key_here
```

### 3. Run
```bash
python app_langchain.py
```

### 4. Interactions
**First Run**: The app will interview you to create a wellness profile (age, weight, goals, injuries).

**Example Commands**:
- *"I want to strengthen my core"* (Routes to **Exercise**)
- *"I'm stressed and can't sleep"* (Routes to **Mindfulness**)
- *"Calculate my calories for weight loss"* (Routes to **Nutrition**)
- *"Give me a workout and meal plan for muscle gain"* (Routes to **Exercise + Nutrition**)
- *"I want to die"* (Routes to **Crisis Support** immediately)

---

## Memory Compaction Explained

To handle long conversations efficiently, the system implements **Memory Compaction**:
1.  **Buffer**: Keeps the last 10 interactions verbatim.
2.  **Trigger**: When buffer fills, an LLM summarizes the history.
3.  **Storage**: The summary is moved to `long_term` memory, and the buffer is cleared.

This allows agents to remember context ("You mentioned back pain last week") without exceeding token limits.

---

## Technology Stack

- **Framework**: LangChain
- **LLM**: Llama 3.3 70B (via Groq)
- **Configuration**: YAML (for routing logic)
- **Storage**: Local JSON (Profiles/Memories)
- **Search**: YouTube Search Python

## License
MIT License

