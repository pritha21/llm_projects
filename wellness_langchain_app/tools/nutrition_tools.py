"""
Nutrition tools for meal planning, calorie tracking, and dietary recommendations
"""

from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from youtube_search import get_youtube_link


def create_meal_plan(
    goal: str,
    calories_target: int,
    dietary_restrictions: List[str],
    meals_per_day: int = 3,
    days: int = 7
) -> Dict:
    """
    Create a personalized meal plan
    
    Args:
        goal: Nutrition goal (weight loss, muscle gain, maintenance, energy)
        calories_target: Target daily calories
        dietary_restrictions: List of restrictions (vegetarian, vegan, gluten-free, etc.)
        meals_per_day: Number of meals per day
        days: Number of days to plan
        
    Returns:
        Structured meal plan
    """
    goal = goal.lower()
    
    # Macro ratios based on goal
    if "weight loss" in goal or "fat loss" in goal:
        macros = {"protein": 40, "carbs": 30, "fat": 30}
        description = "Higher protein, moderate carbs for fat loss while preserving muscle"
    elif "muscle gain" in goal or "bulk" in goal:
        macros = {"protein": 30, "carbs": 45, "fat": 25}
        description = "Balanced macros with higher carbs for muscle building"
    elif "energy" in goal or "performance" in goal:
        macros = {"protein": 25, "carbs": 50, "fat": 25}
        description = "Carb-focused for sustained energy and performance"
    else:  # maintenance
        macros = {"protein": 30, "carbs": 40, "fat": 30}
        description = "Balanced macros for overall health and maintenance"
    
    # Meal examples based on dietary restrictions
    is_vegan = "vegan" in [r.lower() for r in dietary_restrictions]
    is_vegetarian = "vegetarian" in [r.lower() for r in dietary_restrictions] or is_vegan
    is_gluten_free = "gluten-free" in [r.lower() for r in dietary_restrictions]
    
    # Sample meals (simplified for POC)
    breakfast_options = []
    lunch_options = []
    dinner_options = []
    
    if is_vegan:
        breakfast_options = ["Oatmeal with berries and chia seeds", "Tofu scramble with vegetables", "Smoothie bowl with fruits and nuts"]
        lunch_options = ["Quinoa Buddha bowl", "Lentil soup with vegetables", "Chickpea salad wrap"]
        dinner_options = ["Vegetable stir-fry with tofu", "Black bean pasta", "Stuffed bell peppers with rice"]
    elif is_vegetarian:
        breakfast_options = ["Greek yogurt with granola", "Vegetable omelette", "Protein pancakes with fruit"]
        lunch_options = ["Caprese salad with mozzarella", "Vegetable curry with rice", "Quinoa and black bean bowl"]
        dinner_options = ["Eggplant parmesan", "Vegetable lasagna", "Paneer tikka with vegetables"]
    else:
        breakfast_options = ["Eggs with avocado toast", "Protein smoothie", "Oatmeal with nuts and berries"]
        lunch_options = ["Grilled chicken salad", "Salmon with quinoa", "Turkey wrap with vegetables"]
        dinner_options = ["Grilled fish with vegetables", "Chicken stir-fry", "Lean beef with sweet potato"]
    
    # Create daily plan
    weekly_plan = []
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for day_num in range(min(days, 7)):
        day_plan = {
            "day": days_of_week[day_num],
            "meals": [
                {
                    "meal_type": "Breakfast",
                    "suggestion": breakfast_options[day_num % len(breakfast_options)],
                    "calories": int(calories_target * 0.25)  # 25% of daily
                },
                {
                    "meal_type": "Lunch",
                    "suggestion": lunch_options[day_num % len(lunch_options)],
                    "calories": int(calories_target * 0.35)  # 35% of daily
                },
                {
                    "meal_type": "Dinner",
                    "suggestion": dinner_options[day_num % len(dinner_options)],
                    "calories": int(calories_target * 0.30)  # 30% of daily
                }
            ],
            "total_calories": calories_target
        }
        
        # Add snacks if more meals requested
        if meals_per_day > 3:
            snack_calories = int(calories_target * 0.10)
            day_plan["meals"].append({
                "meal_type": "Snack",
                "suggestion": "Nuts, fruits, or protein bar",
                "calories": snack_calories
            })
        
        weekly_plan.append(day_plan)
    
    # Search for meal prep video
    diet_type = "vegan" if is_vegan else "vegetarian" if is_vegetarian else ""
    search_query = f"{diet_type} meal prep {goal} easy recipes".strip()
    youtube_url = get_youtube_link(search_query, duration="medium")
    
    return {
        "goal": goal,
        "daily_calories": calories_target,
        "macros": macros,
        "macro_description": description,
        "dietary_restrictions": dietary_restrictions,
        "weekly_plan": weekly_plan,
        "meal_prep_video": youtube_url or "No video found",
        "tips": [
            "Meal prep on weekends to save time",
            "Stay hydrated - aim for 8 glasses of water daily",
            "Adjust portions based on hunger and energy levels",
            "Track your meals for the first week to understand portions"
        ]
    }


def calculate_nutrition_needs(
    age: int,
    gender: str,
    weight: float,
    height: Optional[float],
    activity_level: str,
    goal: str
) -> Dict:
    """
    Calculate daily calorie and macro needs
    
    Args:
        age: Age in years
        gender: male or female
        weight: Weight in kg
        height: Height in cm (optional, uses estimate if not provided)
        activity_level: sedentary, light, moderate, active, very_active
        goal: weight_loss, maintenance, or muscle_gain
        
    Returns:
        Calculated nutrition needs
    """
    # BMR calculation using Mifflin-St Jeor equation
    # Estimate height if not provided
    if height is None:
        height = 165 if gender.lower() == "female" else 175
    
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Activity multipliers
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    multiplier = activity_multipliers.get(activity_level.lower(), 1.55)
    tdee = bmr * multiplier  # Total Daily Energy Expenditure
    
    # Adjust for goal
    if "loss" in goal.lower():
        target_calories = int(tdee - 500)  # 500 calorie deficit
        goal_description = "Calorie deficit for gradual weight loss (~0.5kg/week)"
    elif "gain" in goal.lower():
        target_calories = int(tdee + 300)  # 300 calorie surplus
        goal_description = "Calorie surplus for muscle gain"
    else:
        target_calories = int(tdee)
        goal_description = "Maintenance calories to maintain current weight"
    
    # Calculate macros (grams)
    protein_grams = int(weight * 2)  # 2g per kg bodyweight
    fat_grams = int((target_calories * 0.25) / 9)  # 25% of calories from fat
    carb_grams = int((target_calories - (protein_grams * 4) - (fat_grams * 9)) / 4)
    
    return {
        "bmr": int(bmr),
        "tdee": int(tdee),
        "target_calories": target_calories,
        "goal_description": goal_description,
        "macros": {
            "protein_grams": protein_grams,
            "carbs_grams": max(carb_grams, 0),
            "fat_grams": fat_grams
        },
        "activity_level": activity_level,
        "recommendations": [
            f"Eat {protein_grams}g protein daily for muscle maintenance",
            f"Distribute calories across {3-4} meals",
            "Prioritize whole foods over processed options",
            "Adjust based on weekly progress"
        ]
    }


def suggest_healthy_recipes(
    meal_type: str,
    dietary_preference: str = "any",
    cuisine: str = "any",
    prep_time: int = 30
) -> Dict:
    """
    Suggest healthy recipes
    
    Args:
        meal_type: breakfast, lunch, dinner, or snack
        dietary_preference: vegetarian, vegan, keto, paleo, or any
        cuisine: Cuisine type or "any"
        prep_time: Maximum preparation time in minutes
        
    Returns:
        Recipe suggestions with video links
    """
    meal_type = meal_type.lower()
    dietary_preference = dietary_preference.lower()
    
    # Build search query
    search_terms = []
    if dietary_preference != "any":
        search_terms.append(dietary_preference)
    search_terms.append("healthy")
    search_terms.append(meal_type)
    if cuisine != "any":
        search_terms.append(cuisine)
    search_terms.append("recipe")
    
    search_query = " ".join(search_terms)
    youtube_url = get_youtube_link(search_query, duration="medium")
    
    # Generic recipe suggestions
    recipes = {
        "breakfast": {
            "vegetarian": ["Avocado toast with poached eggs", "Greek yogurt parfait", "Vegetable frittata"],
            "vegan": ["Overnight oats with berries", "Tofu scramble", "Chia pudding"],
            "keto": ["Keto egg muffins", "Bulletproof coffee with eggs", "Cheese and veggie omelette"],
            "any": ["Protein smoothie", "Oatmeal with fruits", "Whole grain toast with nut butter"]
        },
        "lunch": {
            "vegetarian": ["Quinoa Buddha bowl", "Caprese salad", "Vegetable stir-fry"],
            "vegan": ["Lentil curry", "Chickpea salad", "Vegetable sushi bowl"],
            "keto": ["Grilled chicken salad", "Cauliflower rice bowl", "Zucchini noodles with pesto"],
            "any": ["Grilled chicken wrap", "Salmon with vegetables", "Turkey sandwich"]
        },
        "dinner": {
            "vegetarian": ["Eggplant parmesan", "Stuffed bell peppers", "Vegetable lasagna"],
            "vegan": ["Tofu stir-fry", "Black bean tacos", "Vegetable curry"],
            "keto": ["Grilled steak with asparagus", "Baked salmon", "Chicken thighs with broccoli"],
            "any": ["Grilled fish with quinoa", "Chicken breast with sweet potato", "Lean beef stir-fry"]
        }
    }
    
    meal_recipes = recipes.get(meal_type, {})
    suggestions = meal_recipes.get(dietary_preference, meal_recipes.get("any", ["Balanced healthy meal"]))
    
    return {
        "meal_type": meal_type.title(),
        "dietary_preference": dietary_preference.title(),
        "suggestions": suggestions,
        "prep_time": f"Under {prep_time} minutes",
        "recipe_video": youtube_url or "No video found",
        "tips": [
            "Use fresh, seasonal ingredients when possible",
            "Prep ingredients in advance for faster cooking",
            "Cook in batches for meal prep",
            "Experiment with herbs and spices for flavor"
        ]
    }


if __name__ == "__main__":
    # Test the tools
    print("=== Meal Plan ===")
    plan = create_meal_plan("weight loss", 1800, ["vegetarian"], 3, 7)
    print(f"Goal: {plan['goal']}")
    print(f"Daily Calories: {plan['daily_calories']}")
    print(f"First day: {plan['weekly_plan'][0]['day']}")
    
    print("\n=== Nutrition Needs ===")
    needs = calculate_nutrition_needs(33, "female", 54, 160, "moderate", "weight_loss")
    print(f"Target Calories: {needs['target_calories']}")
    print(f"Protein: {needs['macros']['protein_grams']}g")
    
    print("\n=== Recipe Suggestions ===")
    recipes = suggest_healthy_recipes("dinner", "vegan", "indian", 30)
    print(f"Suggestions: {recipes['suggestions']}")
