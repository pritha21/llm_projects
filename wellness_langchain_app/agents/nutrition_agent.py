"""
LangChain-based Nutrition Agent using Groq
Provides meal planning, calorie tracking, and dietary recommendations
"""

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import sys
from typing import Dict, List, Optional

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv

# Import tools
tools_path = os.path.join(os.path.dirname(__file__), '..', 'tools')
sys.path.insert(0, tools_path)

from nutrition_tools import (
    create_meal_plan,
    calculate_nutrition_needs,
    suggest_healthy_recipes
)

load_dotenv(dotenv_path=os.path.join(parent_dir, '.env'))


# Tool input schemas
class MealPlanInput(BaseModel):
    """Input for meal plan creation tool"""
    goal: str = Field(description="Nutrition goal: weight loss, muscle gain, maintenance, or energy")
    calories_target: int = Field(description="Target daily calories")
    dietary_restrictions: List[str] = Field(description="List of dietary restrictions (vegetarian, vegan, gluten-free, etc.)")
    meals_per_day: int = Field(default=3, description="Number of meals per day (3-4)")
    days: int = Field(default=7, description="Number of days to plan (1-7)")


class NutritionNeedsInput(BaseModel):
    """Input for nutrition needs calculation"""
    age: int = Field(description="Age in years")
    gender: str = Field(description="Gender: male or female")
    weight: float = Field(description="Weight in kg")
    height: Optional[float] = Field(default=None, description="Height in cm (optional)")
    activity_level: str = Field(description="Activity level: sedentary, light, moderate, active, or very_active")
    goal: str = Field(description="Goal: weight_loss, maintenance, or muscle_gain")


class RecipeInput(BaseModel):
    """Input for recipe suggestions"""
    meal_type: str = Field(description="Meal type: breakfast, lunch, dinner, or snack")
    dietary_preference: str = Field(default="any", description="Dietary preference: vegetarian, vegan, keto, paleo, or any")
    cuisine: str = Field(default="any", description="Cuisine type or 'any'")
    prep_time: int = Field(default=30, description="Maximum prep time in minutes")


# Wrapper functions
def meal_plan_wrapper(
    goal: str,
    calories_target: int,
    dietary_restrictions: List[str],
    meals_per_day: int = 3,
    days: int = 7
) -> Dict:
    """Create personalized meal plan"""
    return create_meal_plan(goal, calories_target, dietary_restrictions, meals_per_day, days)


def nutrition_needs_wrapper(
    age: int,
    gender: str,
    weight: float,
    height: Optional[float],
    activity_level: str,
    goal: str
) -> Dict:
    """Calculate daily nutrition needs"""
    return calculate_nutrition_needs(age, gender, weight, height, activity_level, goal)


def recipe_wrapper(
    meal_type: str,
    dietary_preference: str = "any",
    cuisine: str = "any",
    prep_time: int = 30
) -> Dict:
    """Suggest healthy recipes"""
    return suggest_healthy_recipes(meal_type, dietary_preference, cuisine, prep_time)


# Create tools
meal_plan_tool = StructuredTool.from_function(
    func=meal_plan_wrapper,
    name="create_meal_plan",
    description="""Create a personalized weekly meal plan with calorie targets and macro distribution.
    
Use this when the user wants a complete meal plan for the week. The tool provides:
- Daily meal suggestions based on dietary restrictions
- Calorie distribution across meals
- Macro ratios optimized for their goal
- Meal prep video links

IMPORTANT: Always call this tool when creating meal plans - it ensures proper nutrition balance.""",
    args_schema=MealPlanInput,
    return_direct=False
)

nutrition_calc_tool = StructuredTool.from_function(
    func=nutrition_needs_wrapper,
    name="calculate_nutrition_needs",
    description="""Calculate daily calorie and macro needs based on user stats and goals.
    
Use this when the user wants to know how many calories they should eat, or what their macro targets should be.
Calculates BMR, TDEE, and provides personalized recommendations.""",
    args_schema=NutritionNeedsInput,
    return_direct=False
)

recipe_tool = StructuredTool.from_function(
    func=recipe_wrapper,
    name="suggest_recipes",
    description="""Suggest healthy recipes for specific meals.
    
Use this when the user asks for recipe ideas, cooking suggestions, or wants alternatives for a specific meal.
Provides recipe suggestions with YouTube video links.""",
    args_schema=RecipeInput,
    return_direct=False
)


# Agent instructions
NUTRITION_AGENT_INSTRUCTIONS = """You are a certified nutritionist and dietary expert helping users with their nutrition goals.

## Your Core Responsibilities:
1. **Meal Planning**: Create balanced, sustainable meal plans
2. **Calorie Guidance**: Calculate appropriate calorie and macro targets
3. **Recipe Suggestions**: Provide healthy recipe ideas
4. **Nutrition Education**: Explain nutrition concepts clearly

## CRITICAL: Always Clarify Nutrition Goals
⚠️ NEVER assume the user's nutrition goal! Exercise goals ≠ Nutrition goals.

- "strengthen core" (exercise) ≠ muscle gain (nutrition)
- User might want: weight loss, maintenance, muscle gain, or just energy
- **ALWAYS ASK** what their nutrition goal is before calculating calories or creating meal plans

## Workflow:

### For Meal Planning Requests:
1. **Clarify nutrition goal first**: "What's your nutrition goal? Options:
   - Weight loss
   - Muscle gain/building
   - Weight maintenance
   - Improved energy/performance"
2. **Gather info**:
   - What are their dietary restrictions? (vegetarian, vegan, gluten-free, etc.)
   - How many calories should they target? (may need to calculate first)
   - How many meals per day do they prefer?
3. **Calculate if needed**: If they don't know calories, use calculate_nutrition_needs
4. **Create plan**: Call create_meal_plan with all parameters
5. **Present clearly**: Show the plan with meal suggestions AND the meal_prep_video link from the tool
   - Format: "🎥 Meal Prep Video: [URL]"

### For Calorie/Macro Questions:
1. **Gather stats**: Age, gender, weight, height (optional), activity level
2. **Clarify nutrition goal**: Weight loss, maintenance, or muscle gain (ASK, don't assume!)
3. **Calculate**: Use calculate_nutrition_needs tool
4. **Explain**: Present the numbers with clear explanations

### For Recipe Requests:
1. **Clarify meal type**: Breakfast, lunch, dinner, or snack
2. **Ask preferences**: Dietary preference, cuisine type, time constraints
3. **Suggest recipes**: Use suggest_recipes tool
4. **Include recipe_video**: ALWAYS show the YouTube recipe link from tool's response
   - Format: "🎥 Watch recipe: [URL]"

## Communication Style:
- Be supportive and non-judgmental
- Focus on sustainable, balanced approaches (no extreme diets)
- Emphasize whole foods and nutrition quality
- Provide practical, actionable advice
- Always include video links when available
- **Ask clarifying questions** - don't make assumptions!

## Important Notes:
- Never recommend extremely low calories (< 1200 for women, < 1500 for men)
- Consider dietary restrictions seriously
- Promote balanced nutrition, not restriction
- Encourage consulting a doctor for medical conditions
- **NEVER assume goals** - always ask!

## Example Flow:

User: "do I need a diet plan?"
You: "I'd be happy to help with a nutrition plan! First, what's your primary nutrition goal?
- Weight loss
- Muscle gain
- Maintain current weight
- Improve energy/performance"

User: "I want to maintain weight"
You: "Great! To create a personalized plan, I need some info. From your profile, I see you're 33F, 54kg, moderately active. Is that correct?"

User: "Yes"
You: [Call calculate_nutrition_needs with goal="maintenance"]
You: [Show calorie target and explanation]
You: "Based on your stats, you need about 1650 calories daily for maintenance. Would you like me to create a meal plan? If so, any dietary restrictions?"
"""


def create_nutrition_agent():
    """Create and return the LangChain nutrition agent"""
    
    # Initialize Groq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4,  # Slightly creative for recipe suggestions
        groq_api_key=os.getenv("GROQ_API_KEY"),
        max_tokens=2000
    )
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", NUTRITION_AGENT_INSTRUCTIONS),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    # List of tools
    tools = [meal_plan_tool, nutrition_calc_tool, recipe_tool]
    
    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8,  # Allow more iterations for multi-tool workflows
        return_intermediate_steps=False  # Clean output
    )
    
    return agent_executor


if __name__ == "__main__":
    print("Testing LangChain Nutrition Agent with Groq...")
    print("=" * 60)
    
    agent = create_nutrition_agent()
    
    # Test: Nutrition calculation
    print("\n=== Test: Calculate Nutrition Needs ===")
    result = agent.invoke({
        "input": "I'm 33 years old, female, 54kg, moderately active. I want to lose weight. How many calories should I eat?"
    })
    print("\nAgent Response:")
    print(result['output'])
