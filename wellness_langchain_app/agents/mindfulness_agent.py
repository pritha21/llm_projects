"""
LangChain-based Mindfulness Agent using Groq
Provides meditation, breathing exercises, stress relief, and crisis support
"""

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import sys
from typing import Dict, List

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv

# Import tools
tools_path = os.path.join(os.path.dirname(__file__), '..', 'tools')
sys.path.insert(0, tools_path)

from mindfulness_tools import (
    recommend_meditation,
    suggest_breathing_exercise,
    create_stress_relief_plan,
    crisis_support
)

load_dotenv(dotenv_path=os.path.join(parent_dir, '.env'))


# Tool input schemas
class MeditationInput(BaseModel):
    """Input for meditation recommendation tool"""
    goal: str = Field(description="Meditation goal (stress relief, sleep, focus, anxiety relief, etc.)")
    duration: int = Field(description="Duration in minutes")
    experience_level: str = Field(default="beginner", description="beginner, intermediate, or experienced")


class BreathingInput(BaseModel):
    """Input for breathing exercise tool"""
    purpose: str = Field(description="Purpose: relaxation, energy, focus, or anxiety")
    duration: int = Field(default=5, description="Duration in minutes")


class StressReliefInput(BaseModel):
    """Input for stress relief plan tool"""
    stress_level: str = Field(description="Stress level: low, moderate, or high")
    available_time: int = Field(description="Available time in minutes")


class CrisisInput(BaseModel):
    """Input for crisis support tool"""
    indicators: List[str] = Field(description="List of concerning phrases or self-harm indicators detected")


# Wrapper functions
def meditation_wrapper(goal: str, duration: int, experience_level: str = "beginner") -> Dict:
    """Recommend guided meditation"""
    return recommend_meditation(goal, duration, experience_level)


def breathing_wrapper(purpose: str, duration: int = 5) -> Dict:
    """Suggest breathing exercise"""
    return suggest_breathing_exercise(purpose, duration)


def stress_relief_wrapper(stress_level: str, available_time: int) -> Dict:
    """Create stress relief plan"""
    return create_stress_relief_plan(stress_level, available_time)


def crisis_wrapper(indicators: List[str]) -> Dict:
    """Provide crisis support resources"""
    return crisis_support(indicators)


# Create tools
meditation_tool = StructuredTool.from_function(
    func=meditation_wrapper,
    name="recommend_meditation",
    description="""Recommend a guided meditation with YouTube video link.
    
Use this when the user wants meditation guidance for stress, sleep, focus, anxiety, or general mindfulness.
The tool will provide a structured meditation recommendation with video link, benefits, and instructions.""",
    args_schema=MeditationInput,
    return_direct=False
)

breathing_tool = StructuredTool.from_function(
    func=breathing_wrapper,
    name="suggest_breathing_exercise",
    description="""Suggest a breathing exercise technique.
    
Use this for immediate stress relief, energy boost, focus improvement, or anxiety reduction.
Provides specific breathing patterns with step-by-step instructions.""",
    args_schema=BreathingInput,
    return_direct=False
)

stress_relief_tool = StructuredTool.from_function(
    func=stress_relief_wrapper,
    name="create_stress_relief_plan",
    description="""Create a comprehensive stress relief plan.
    
Use this when the user is experiencing stress and needs a structured approach.
The plan adapts to stress level (low/moderate/high) and available time.""",
    args_schema=StressReliefInput,
    return_direct=False
)

crisis_tool = StructuredTool.from_function(
    func=crisis_wrapper,
    name="crisis_support",
    description="""CRITICAL: Provide crisis support resources for self-harm or suicidal ideation.
    
⚠️ USE THIS IMMEDIATELY if the user mentions:
- Self-harm, suicide, or hurting themselves
- Feeling like they want to die or disappear
- Feeling hopeless or having no reason to live
- Having a plan to harm themselves

This provides emergency resources, crisis hotlines, and immediate grounding techniques.
This is NOT a replacement for professional help but provides urgent support.""",
    args_schema=CrisisInput,
    return_direct=True  # Return directly for crisis situations
)


# Agent instructions
MINDFULNESS_AGENT_INSTRUCTIONS = """You are a compassionate mindfulness and mental wellness coach.

## Your Core Responsibilities:
1. **Crisis Detection (HIGHEST PRIORITY)**: If ANY indication of self-harm or suicidal thoughts:
   - IMMEDIATELY call the crisis_support tool
   - Do NOT try to counsel the user yourself
   - Provide professional resources
   
2. **Meditation Guidance**: Recommend appropriate meditations for various goals
3. **Breathing Techniques**: Teach breathing exercises for different needs
4. **Stress Management**: Create personalized stress relief plans

## Crisis Indicators to Watch For:
- Mentions of self-harm, suicide, or wanting to die
- Expressions of hopelessness or worthlessness
- Statements about having no reason to live
- Talk of making plans to hurt themselves

⚠️ If you detect ANY of these, call crisis_support tool IMMEDIATELY with the concerning phrases.

## Workflow for Non-Crisis Situations:
1. **Understand the need**: What is the user seeking? (relaxation, sleep, stress relief, etc.)
2. **Assess urgency**: Is this immediate stress or general wellness?
3. **Gather info**:
   - How much time do they have?
   - What's their experience level?
   - What's their current state? (stressed/anxious/calm)
4. **Use appropriate tool**:
   - Meditation: For general mindfulness, sleep, or specific goals
   - Breathing: For immediate relief or energy
   - Stress relief plan: For comprehensive stress management
5. **Present guidance**: Show the recommendations WITH video links when available

## Communication Style:
- Be warm, empathetic, and non-judgmental
- Use calming language
- Validate their feelings
- Provide clear, actionable guidance
- Always include YouTube links when tools provide them

## Example Flows:

**General Meditation Request:**
User: "I need help relaxing"
You: "I'd love to help you relax. How much time do you have available, and have you practiced meditation before?"
User: "15 minutes, I'm a beginner"
You: [Call recommend_meditation with goal="relaxation", duration=15, experience_level="beginner"]
You: [Present recommendation with video link]

**Immediate Stress:**
User: "I'm really stressed right now"
You: "I hear you. Let's get you some immediate relief. Would you like a quick breathing exercise or a longer stress relief plan?"
User: "Quick breathing"
You: [Call suggest_breathing_exercise with purpose="anxiety", duration=5]

**CRISIS:**
User: "I don't want to be here anymore"
You: [IMMEDIATELY call crisis_support with indicators=["suicidal ideation"]]
"""


def create_mindfulness_agent():
    """Create and return the LangChain mindfulness agent"""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.5,  # Slightly higher for empathetic responses
        groq_api_key=os.getenv("GROQ_API_KEY"),
        max_tokens=2000
    )
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", MINDFULNESS_AGENT_INSTRUCTIONS),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    # List of tools
    tools = [meditation_tool, breathing_tool, stress_relief_tool, crisis_tool]
    
    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )
    
    return agent_executor


if __name__ == "__main__":
    print("Testing LangChain Mindfulness Agent with Groq...")
    print("=" * 60)
    
    agent = create_mindfulness_agent()
    
    # Test 1: Meditation request
    print("\n=== Test 1: Meditation Request ===")
    result = agent.invoke({
        "input": "I'm having trouble sleeping. I'm a beginner at meditation. I have 15 minutes."
    })
    print("\nAgent Response:")
    print(result['output'])
    
    # Test 2: Breathing exercise
    print("\n" + "=" * 60)
    print("\n=== Test 2: Breathing Exercise ===")
    result = agent.invoke({
        "input": "I'm feeling anxious right now and need something quick, maybe 5 minutes."
    })
    print("\nAgent Response:")
    print(result['output'])
