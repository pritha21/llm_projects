"""
Holistic Wellness Orchestrator CLI
Routes to exercise or mindfulness agents based on user input
Manages user profiles and memories with compaction
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import WellnessOrchestrator


def print_header():
    """Print application header"""
    print("=" * 80)
    print("🌟 HOLISTIC WELLNESS ORCHESTRATOR 🌟")
    print("=" * 80)
    print("\nYour personal wellness companion powered by AI")
    print("\nFeatures:")
    print("  🏋️  Exercise planning & workout recommendations")
    print("  🧘  Mindfulness, meditation & breathing exercises")
    print("  🥗  Nutrition guidance, meal planning & recipes")
    print("  🧠  Memory-based personalization")
    print("  ⚡  Intelligent routing to specialized agents")
    print("  🆘  Crisis support resources (available 24/7)")
    print("\nType 'exit', 'quit', or 'q' to end session")
    print("=" * 80)


def setup_user_profile(orchestrator: WellnessOrchestrator) -> str:
    """Interactive profile setup"""
    print("\n" + "=" * 80)
    print("👤 USER PROFILE SETUP")
    print("=" * 80)
    
    user_id = input("\nEnter a username (or press Enter for 'default_user'): ").strip()
    if not user_id:
        user_id = "default_user"
    
    # Check if profile exists
    if orchestrator.profile_exists(user_id):
        print(f"\n✅ Welcome back, {user_id}!")
        profile = orchestrator.get_user_profile(user_id)
        print("\n📋 Your Profile:")
        print(orchestrator.get_user_context(user_id))
        
        update = input("\nWould you like to update your profile? (y/n): ").strip().lower()
        if update == 'y':
            print("\nLeave blank to keep current value.")
            
            updates = {}
            
            # Demographics updates
            age = input(f"  Age [{profile['demographics']['age']}]: ").strip()
            if age:
                updates.setdefault('demographics', {})['age'] = int(age)
            
            weight = input(f"  Weight (kg) [{profile['demographics']['weight']}]: ").strip()
            if weight:
                updates.setdefault('demographics', {})['weight'] = float(weight)
            
            # Fitness updates
            fitness_level = input(f"  Fitness level [{profile['fitness']['level']}]: ").strip()
            if fitness_level:
                updates.setdefault('fitness', {})['level'] = fitness_level
            
            if updates:
                orchestrator.update_user_profile(user_id, updates)
                print("\n✅ Profile updated!")
        
        return user_id
    
    # Create new profile
    print(f"\n📝 Creating new profile for '{user_id}'...\n")
    
    try:
        age = int(input("Age (years): "))
        gender = input("Gender (male/female/other): ").strip().lower()
        weight = float(input("Weight (kg): "))
        fitness_level = input("Fitness level (beginner/intermediate/advanced) [beginner]: ").strip().lower() or "beginner"
        
        injuries_input = input("Any injuries or limitations? (comma-separated, or 'none'): ").strip()
        injuries = [i.strip() for i in injuries_input.split(",")] if injuries_input.lower() != 'none' else []
        
        goals_input = input("Fitness goals? (e.g., weight loss, strength, flexibility): ").strip()
        goals = [g.strip() for g in goals_input.split(",")] if goals_input else []
        
        mind_exp = input("Mindfulness experience (beginner/intermediate/experienced) [beginner]: ").strip().lower() or "beginner"
        
        # Create profile
        orchestrator.create_user_profile(
            user_id=user_id,
            age=age,
            gender=gender,
            weight=weight,
            fitness_level=fitness_level,
            injuries=injuries,
            fitness_goals=goals,
            mindfulness_experience=mind_exp
        )
        
        print(f"\n✅ Profile created successfully!")
        return user_id
        
    except ValueError as e:
        print(f"\n❌ Invalid input: {e}")
        print("Using default profile...")
        orchestrator.create_user_profile(
            user_id=user_id,
            age=30,
            gender="other",
            weight=70,
            fitness_level="beginner"
        )
        return user_id
    except KeyboardInterrupt:
        print("\n\nProfile setup cancelled. Using minimal profile.")
        orchestrator.create_user_profile(
            user_id=user_id,
            age=30,
            gender="other",
            weight=70
        )
        return user_id


def main():
    """Main application loop"""
    print_header()
    
    # Initialize orchestrator
    print("\n🔄 Initializing wellness orchestrator...")
    orchestrator = WellnessOrchestrator()
    print("✅ Ready!\n")
    
    # Setup user profile
    user_id = setup_user_profile(orchestrator)
    
    print("\n" + "=" * 80)
    print("💬 START CONVERSATION")
    print("=" * 80)
    print("\nI can help you with:")
    print("  • Workout plans and exercise guidance")
    print("  • Meditation and mindfulness practices")
    print("  • Meal plans, nutrition and healthy recipes")
    print("  • Stress relief and breathing exercises")
    print("  • Crisis support (if you're in distress)")
    print("\nWhat would you like help with today?")
    print("-" * 80)
    
    while True:
        try:
            user_input = input("\n You > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n" + "=" * 80)
                print("👋 Thank you for using the Wellness Orchestrator!")
                print("Take care of yourself! 💚")
                print("=" * 80)
                break
            
            # Special commands
            if user_input.lower() == 'profile':
                print("\n" + orchestrator.get_user_context(user_id))
                continue
            
            if user_input.lower() == 'help':
                print("\nCommands:")
                print("  profile  - View your profile and memory")
                print("  exit     - Exit the application")
                continue
            
            # Process request through orchestrator
            print("\n🔄 Processing with orchestrator...")
            result = orchestrator.invoke(user_id, user_input)
            
            # Display result
            print(f"\n🎯 Routed to: {result.get('agent_used', 'Unknown')}")
            print("-" * 80)
            print(f"\n🤖 Response:\n\n{result['response']}")
            print("-" * 80)
            
            # Check for errors
            if 'error' in result:
                print(f"\n⚠️  Note: {result['error']}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()

