"""
LangChain-based Exercise Agent using Groq
This is a proof-of-concept to test reliable tool calling with Groq models.
"""

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import sys
from typing import Dict

# Add parent directory to path to access existing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv

# Import from langchain_version's own tools
tools_path = os.path.join(os.path.dirname(__file__), '..', 'tools')
sys.path.insert(0, tools_path)

from exercise_tools import build_workout_plan

load_dotenv(dotenv_path=os.path.join(parent_dir, '.env'))


# Define input schema for the tool
class WorkoutPlanInput(BaseModel):
    """Input for generate_workout_plan tool."""
    goal: str = Field(description="Fitness goal (fat loss, muscle gain, mobility, endurance, etc.)")
    minutes_per_day: int = Field(description="Exercise duration per day in minutes")
    days_per_week: int = Field(description="Number of workout days per week")
    fitness_level: str = Field(description="beginner, intermediate, or advanced")
    age: int = Field(description="User's age in years")
    weight: float = Field(description="User's weight in kg")
    gender: str = Field(description="male, female, or other")
    injuries: str = Field(default="none", description="Any injuries or physical limitations")


def generate_workout_plan_wrapper(
    goal: str,
    minutes_per_day: int,
    days_per_week: int,
    fitness_level: str,
    age: int,
    weight: float,
    gender: str,
    injuries: str = "none"
) -> Dict:
    """Generate a personalized workout plan with YouTube video links."""
    return build_workout_plan(
        goal=goal,
        minutes_per_day=minutes_per_day,
        days_per_week=days_per_week,
        fitness_level=fitness_level,
        age=age,
        weight=weight,
        gender=gender,
        injuries=injuries
    )


# Create the tool
workout_tool = StructuredTool.from_function(
    func=generate_workout_plan_wrapper,
    name="generate_workout_plan",
    description="""Generate a personalized workout plan with YouTube video links for each workout day.
    
This tool creates a complete weekly workout schedule tailored to the user's goals, fitness level, 
and constraints. Each workout day includes a YouTube video link for easy follow-along.

IMPORTANT: Always call this tool when creating workout plans - it ensures YouTube links are included.""",
    args_schema=WorkoutPlanInput,
    return_direct=False
)


# Agent instructions
EXERCISE_AGENT_INSTRUCTIONS = """You are a certified personal trainer helping users with their fitness goals.

## Your Workflow:
1. **Understand the goal**: Identify what the user wants (fat loss, muscle gain, mobility, stress relief, etc.)
2. **Check user context**: The user's profile information will be provided in the context, including:
   - Age, gender, weight, fitness level, injuries
   - Workout preferences (days per week, minutes per day) - if available
3. **Collect ONLY missing info**: 
   - If days/week and minutes/day are in the profile preferences → use them directly
   - If NOT in profile → ask the user
4. **Use the tool**: Once you have the goal, minutes, and days, CALL the `generate_workout_plan` tool
5. **Present the plan**: Display the workout schedule INCLUDING the YouTube links from the tool

## Critical Rules:
- **Check profile first** - don't ask for info that's already there!
- **ALWAYS use the generate_workout_plan tool** - never create plans manually
- The tool automatically fetches YouTube video links - make sure to show them!
- Format YouTube links clearly: "🎥 Follow along: [URL]"
- Be encouraging and supportive in your responses

## Example Flow (when preferences exist):
User: "I want to improve my mobility"
You: [See profile has: 3 days/week, 30 min/day]
You: [Call generate_workout_plan with goal="mobility", days=3, minutes=30]
You: [Present plan]

## Example Flow (when preferences DON'T exist):
User: "I want to improve my mobility"
You: "Great goal! How many days per week can you commit? And how many minutes per day?"
User: "3 days, 30 minutes"
You: [Call generate_workout_plan]
"""


def create_exercise_agent():
    """Create and return the LangChain exercise agent."""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        max_tokens=2000
    )
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", EXERCISE_AGENT_INSTRUCTIONS),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    # Create agent
    agent = create_tool_calling_agent(llm, [workout_tool], prompt)
    
    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[workout_tool],
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )
    
    return agent_executor


if __name__ == "__main__":
    print("Testing LangChain Exercise Agent with Groq...")
    print("=" * 60)
    
    agent = create_exercise_agent()
    
    # Test conversation
    test_input = """I'm a 33-year-old female, 54kg, intermediate fitness level with back pain. 
    I want a low-impact workout to help with mobility, 20 minutes per day, 3 days a week."""
    
    print(f"\nTest Input: {test_input}\n")
    
    result = agent.invoke({"input": test_input})
    
    print("\n" + "=" * 60)
    print("Agent Response:")
    print(result['output'])

