"""
Exercise tools for LangChain version
Standalone version to avoid import issues
"""

from typing import Dict
import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import youtube_search from parent directory
from youtube_search import get_youtube_link


def build_workout_plan(
    goal: str,
    minutes_per_day: int,
    days_per_week: int,
    fitness_level: str,
    age: int,
    weight: float,
    gender: str,
    injuries: str = "none",
) -> Dict:
    """Build a workout plan with YouTube links."""
    
    goal = goal.lower()
    fitness_level = fitness_level.lower()

    plan = {
        "summary": "",
        "schedule": [],
        "guidelines": [],
        "personalization": f"Plan customized for {gender}, age {age}, weight {weight}kg",
    }

    # Check for back pain/injury and prioritize appropriate exercises
    has_back_issue = injuries and any(word in injuries.lower() for word in ['back', 'spine', 'lower back', 'upper back'])
    
    if has_back_issue:
        # Back-friendly exercises take priority
        intensities = ["Very Light", "Light"]
        activities_pool = ["Gentle Yoga", "Stretching", "Pilates", "Swimming", "Walking"]
        plan["summary"] = "Back-friendly exercises focusing on gentle movement, flexibility, and core strengthening to support your back."
    elif "stress" in goal or "mobility" in goal:
        intensities = ["Very Light", "Light", "Moderate"]
        activities_pool = ["Yoga Flow", "Walking", "Breathing Exercises", "Stretching", "Pilates"]
        plan["summary"] = f"To help with {goal}, this plan focuses on gentle movement and mobility."
    elif "muscle" in goal or "strength" in goal:
        intensities = ["Moderate", "Hard"]
        activities_pool = ["Bodyweight Strength", "Resistance Training", "Calisthenics"]
        plan["summary"] = "Focus on progressive overload with strength movements."
    else:
        intensities = ["Light", "Moderate"]
        activities_pool = ["Brisk Walking", "Circuit Training", "Cardio", "Zumba", "Aerobics"]
        plan["summary"] = "A balanced mix of cardio and light resistance to boost metabolism."

    if fitness_level == "beginner":
        base_duration = min(minutes_per_day, 20)
        activities_pool = [a for a in activities_pool if "Hard" not in a]
    elif fitness_level == "intermediate":
        base_duration = min(minutes_per_day, 40)
    else:
        base_duration = minutes_per_day

    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if days_per_week >= 5:
        workout_indices = [0, 1, 2, 3, 4]
    elif days_per_week == 4:
        workout_indices = [0, 2, 4, 6]
    elif days_per_week == 3:
        workout_indices = [0, 2, 4]
    else:
        workout_indices = range(days_per_week)

    for i, day_name in enumerate(week_days):
        day_plan = {"day": day_name}
        if i in workout_indices:
            activity = activities_pool[i % len(activities_pool)]
            # Search for YouTube video
            search_query = f"{activity} workout {fitness_level} {base_duration} minutes"
            youtube_url = get_youtube_link(search_query, duration="medium")
            
            day_plan.update({
                "type": "Workout",
                "activity": activity,
                "duration": f"{base_duration} mins",
                "intensity": intensities[0] if i == 0 else intensities[1 % len(intensities)], 
                "youtube_link": youtube_url or "No video found",
            })
        else:
            day_plan.update({
                "type": "Rest",
                "activity": "Light active recovery (optional walk)",
                "duration": "-",
            })
        plan["schedule"].append(day_plan)

    # Age-based adjustments
    if age > 50:
        plan["guidelines"].append("Focus on joint-friendly movements and proper warm-up.")
        plan["summary"] += " Age-appropriate modifications included."
    
    # Weight-based guidance
    if weight > 90:
        plan["guidelines"].append("Consider low-impact exercises to protect joints.")
    
    plan["guidelines"].append("Hydrate before and after sessions.")
    if injuries and injuries.lower() != "none":
        plan["guidelines"].append(f"CAUTION: Modify exercises to accommodate your {injuries}.")
        plan["summary"] += f" Please be careful with your {injuries}."

    if "stress" in goal:
        plan["guidelines"].append("Focus on deep breathing during movement.")

    return plan
