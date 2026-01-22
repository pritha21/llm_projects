"""
Mindfulness tools for meditation, breathing exercises, stress relief, and crisis support
"""

from typing import Dict, List
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from youtube_search import get_youtube_link


def recommend_meditation(
    goal: str,
    duration: int,
    experience_level: str = "beginner"
) -> Dict:
    """
    Recommend guided meditation with YouTube video
    
    Args:
        goal: Meditation goal (stress relief, sleep, focus, anxiety, etc.)
        duration: Duration in minutes
        experience_level: beginner, intermediate, or experienced
        
    Returns:
        Meditation recommendation with video link
    """
    goal = goal.lower()
    
    # Build search query
    search_query = f"guided meditation {goal} {duration} minutes {experience_level}"
    youtube_url = get_youtube_link(search_query, duration="medium")
    
    # Provide structured recommendation
    recommendation = {
        "title": f"{goal.title()} Meditation",
        "duration": f"{duration} minutes",
        "level": experience_level,
        "benefits": _get_meditation_benefits(goal),
        "instructions": _get_meditation_instructions(goal),
        "youtube_link": youtube_url or "No video found",
        "tips": [
            "Find a quiet, comfortable space",
            "Sit or lie down in a relaxed position",
            "Close your eyes or soften your gaze",
            "Focus on your breath and the guide's voice"
        ]
    }
    
    return recommendation


def _get_meditation_benefits(goal: str) -> List[str]:
    """Get benefits for specific meditation types"""
    benefits_map = {
        "stress": ["Reduces cortisol levels", "Calms nervous system", "Improves emotional regulation"],
        "sleep": ["Relaxes body and mind", "Reduces racing thoughts", "Promotes deeper sleep"],
        "focus": ["Improves concentration", "Enhances mental clarity", "Reduces distractions"],
        "anxiety": ["Reduces worry and fear", "Promotes calmness", "Builds resilience"],
        "general": ["Improves mental well-being", "Enhances self-awareness", "Reduces stress"]
    }
    
    for key in benefits_map:
        if key in goal:
            return benefits_map[key]
    
    return benefits_map["general"]


def _get_meditation_instructions(goal: str) -> str:
    """Get basic instructions for meditation type"""
    instructions_map = {
        "stress": "Focus on releasing tension with each exhale. Notice areas of tightness and breathe into them.",
        "sleep": "Progressive body scan from toes to head, releasing tension in each part.",
        "focus": "Return attention to breath whenever mind wanders. Count breaths if helpful.",
        "anxiety": "Observe anxious thoughts without judgment, then return to breath.",
        "general": "Follow the guided voice, returning to breath when mind wanders."
    }
    
    for key in instructions_map:
        if key in goal:
            return instructions_map[key]
    
    return instructions_map["general"]


def suggest_breathing_exercise(
    purpose: str = "relaxation",
    duration: int = 5
) -> Dict:
    """
    Suggest a breathing exercise technique
    
    Args:
        purpose: relaxation, energy, focus, or anxiety
        duration: Duration in minutes
        
    Returns:
        Breathing exercise details
    """
    purpose = purpose.lower()
    
    exercises = {
        "relaxation": {
            "name": "4-7-8 Breathing",
            "technique": "Inhale for 4 counts, hold for 7, exhale for 8",
            "repetitions": f"Repeat for {duration} minutes",
            "benefits": ["Activates parasympathetic nervous system", "Reduces stress", "Promotes relaxation"],
            "instructions": [
                "1. Sit comfortably with good posture",
                "2. Exhale completely through your mouth",
                "3. Inhale through nose for 4 counts",
                "4. Hold breath for 7 counts",
                "5. Exhale through mouth for 8 counts",
                "6. Repeat cycle"
            ]
        },
        "energy": {
            "name": "Bellows Breath (Bhastrika)",
            "technique": "Rapid, forceful breathing",
            "repetitions": f"{duration * 30} breaths total",
            "benefits": ["Increases energy", "Improves alertness", "Clears mind"],
            "instructions": [
                "1. Sit with straight spine",
                "2. Take a deep breath in",
                "3. Forcefully exhale through nose",
                "4. Quickly inhale through nose",
                "5. Continue rapid breathing rhythm",
                "6. Rest when needed"
            ]
        },
        "focus": {
            "name": "Box Breathing",
            "technique": "Equal counts for inhale, hold, exhale, hold",
            "repetitions": f"Repeat for {duration} minutes",
            "benefits": ["Improves concentration", "Reduces stress", "Enhances mental clarity"],
            "instructions": [
                "1. Sit comfortably",
                "2. Inhale for 4 counts",
                "3. Hold for 4 counts",
                "4. Exhale for 4 counts",
                "5. Hold for 4 counts",
                "6. Repeat cycle"
            ]
        },
        "anxiety": {
            "name": "Deep Belly Breathing",
            "technique": "Slow, deep diaphragmatic breathing",
            "repetitions": f"Continue for {duration} minutes",
            "benefits": ["Calms nervous system", "Reduces panic", "Grounds you in present"],
            "instructions": [
                "1. Place hand on belly",
                "2. Breathe deeply into belly (not chest)",
                "3. Feel belly expand on inhale",
                "4. Slowly exhale, belly contracts",
                "5. Focus on the physical sensation",
                "6. Let go of anxious thoughts"
            ]
        }
    }
    
    # Find matching exercise
    exercise = exercises.get(purpose, exercises["relaxation"])
    
    # Search for video guide
    search_query = f"{exercise['name']} breathing exercise tutorial"
    youtube_url = get_youtube_link(search_query, duration="short")
    
    exercise["youtube_link"] = youtube_url or "No video found"
    
    return exercise


def create_stress_relief_plan(
    stress_level: str = "moderate",
    available_time: int = 20
) -> Dict:
    """
    Create a personalized stress relief plan
    
    Args:
        stress_level: low, moderate, or high
        available_time: Time available in minutes
        
    Returns:
        Structured stress relief plan
    """
    stress_level = stress_level.lower()
    
    plan = {
        "stress_level": stress_level,
        "duration": available_time,
        "activities": []
    }
    
    if stress_level == "high":
        # Urgent stress relief
        plan["activities"] = [
            {
                "activity": "Breathing Exercise",
                "duration": "5 minutes",
                "details": "Start with 4-7-8 breathing to calm nervous system"
            },
            {
                "activity": "Body Scan",
                "duration": f"{available_time - 10} minutes",
                "details": "Progressive muscle relaxation to release tension"
            },
            {
                "activity": "Grounding Exercise",
                "duration": "5 minutes",
                "details": "5-4-3-2-1 technique: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste"
            }
        ]
        plan["priority"] = "Immediate stress reduction"
        
    elif stress_level == "moderate":
        # Balanced approach
        plan["activities"] = [
            {
                "activity": "Light Movement",
                "duration": f"{available_time // 2} minutes",
                "details": "Gentle yoga or stretching to release physical tension"
            },
            {
                "activity": "Guided Meditation",
                "duration": f"{available_time // 2} minutes",
                "details": "Stress-relief meditation to calm mind"
            }
        ]
        plan["priority"] = "Balance mind and body"
        
    else:  # low
        # Preventive care
        plan["activities"] = [
            {
                "activity": "Mindful Walking",
                "duration": f"{available_time - 5} minutes",
                "details": "Walk slowly, focusing on each step and breath"
            },
            {
                "activity": "Gratitude Practice",
                "duration": "5 minutes",
                "details": "Write down 3 things you're grateful for today"
            }
        ]
        plan["priority"] = "Maintain well-being"
    
    # Add general recommendations
    plan["recommendations"] = [
        "Limit caffeine intake",
        "Stay hydrated",
        "Take regular breaks from screens",
        "Connect with supportive people",
        "Maintain consistent sleep schedule"
    ]
    
    return plan


def crisis_support(indicators: List[str]) -> Dict:
    """
    Provide crisis support resources when self-harm indicators detected
    
    Args:
        indicators: List of concerning phrases or concepts detected
        
    Returns:
        Emergency resources and support information
    """
    response = {
        "severity": "CRITICAL",
        "message": "I'm very concerned about what you've shared. Your safety is the top priority.",
        "immediate_actions": [
            "If you're in immediate danger, please call emergency services (911 in US, 112 in EU)",
            "Consider reaching out to a trusted friend or family member right now",
            "Contact a crisis helpline - they're available 24/7"
        ],
        "crisis_resources": [
            {
                "name": "National Suicide Prevention Lifeline (US)",
                "phone": "988",
                "text": "Text 'HELLO' to 741741",
                "available": "24/7"
            },
            {
                "name": "Crisis Text Line",
                "text": "Text 'HELLO' to 741741",
                "available": "24/7"
            },
            {
                "name": "International Association for Suicide Prevention",
                "website": "https://www.iasp.info/resources/Crisis_Centres/",
                "info": "Find crisis centers worldwide"
            },
            {
                "name": "Samaritans (UK)",
                "phone": "116 123",
                "email": "jo@samaritans.org",
                "available": "24/7"
            }
        ],
        "grounding_exercise": {
            "title": "Immediate Grounding: 5-4-3-2-1 Technique",
            "steps": [
                "Name 5 things you can SEE around you",
                "Name 4 things you can TOUCH",
                "Name 3 things you can HEAR",
                "Name 2 things you can SMELL",
                "Name 1 thing you can TASTE"
            ],
            "purpose": "This helps bring you back to the present moment and can reduce overwhelming feelings"
        },
        "follow_up": "Please reach out to a mental health professional as soon as possible. You don't have to face this alone.",
        "agent_limitation": "I'm an AI assistant and not equipped to provide crisis counseling. Please contact the resources above for professional help."
    }
    
    return response


if __name__ == "__main__":
    # Test the tools
    print("=== Meditation Recommendation ===")
    meditation = recommend_meditation("stress relief", 10, "beginner")
    print(f"Title: {meditation['title']}")
    print(f"Link: {meditation['youtube_link']}")
    
    print("\n=== Breathing Exercise ===")
    breathing = suggest_breathing_exercise("anxiety", 5)
    print(f"Name: {breathing['name']}")
    print(f"Technique: {breathing['technique']}")
    
    print("\n=== Stress Relief Plan ===")
    plan = create_stress_relief_plan("high", 20)
    print(f"Activities: {len(plan['activities'])}")
    
    print("\n=== Crisis Support ===")
    crisis = crisis_support(["self-harm"])
    print(f"Severity: {crisis['severity']}")
    print(f"Resources: {len(crisis['crisis_resources'])}")
