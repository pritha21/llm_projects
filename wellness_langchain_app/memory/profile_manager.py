"""
User profile management system
"""

import json
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path


class ProfileManager:
    """Manages user profiles with CRUD operations"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_profile_file(self, user_id: str) -> Path:
        """Get the profile file path for a user"""
        return self.data_dir / f"{user_id}_profile.json"
    
    def create_profile(
        self, 
        user_id: str,
        age: int,
        gender: str,
        weight: float,
        fitness_level: str = "beginner",
        injuries: Optional[List[str]] = None,
        fitness_goals: Optional[List[str]] = None,
        mindfulness_experience: str = "beginner",
        mindfulness_preferences: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new user profile
        
        Args:
            user_id: Unique user identifier
            age: User's age in years
            gender: male, female, or other
            weight: Weight in kg
            fitness_level: beginner, intermediate, or advanced
            injuries: List of injuries or physical limitations
            fitness_goals: List of fitness goals
            mindfulness_experience: beginner, intermediate, or experienced
            mindfulness_preferences: Meditation types preferred
            
        Returns:
            Created profile dictionary
        """
        profile = {
            "user_id": user_id,
            "demographics": {
                "age": age,
                "gender": gender,
                "weight": weight
            },
            "fitness": {
                "level": fitness_level,
                "injuries": injuries or [],
                "goals": fitness_goals or []
            },
            "mindfulness": {
                "experience": mindfulness_experience,
                "preferences": mindfulness_preferences or []
            },
            "preferences": {
                "workout_times": [],
                "notification_settings": {}
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_profile(user_id, profile)
        return profile
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """
        Retrieve a user's profile
        
        Args:
            user_id: User identifier
            
        Returns:
            Profile dictionary or None if not found
        """
        file_path = self._get_profile_file(user_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Check if file is empty
                if not content:
                    return None
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            # File is corrupted or empty, return None
            print(f"Warning: Corrupted profile file for {user_id}: {e}")
            return None
    
    def update_profile(self, user_id: str, updates: Dict) -> Dict:
        """
        Update a user's profile
        
        Args:
            user_id: User identifier
            updates: Dictionary of updates to apply (supports nested updates)
            
        Returns:
            Updated profile
        """
        profile = self.get_profile(user_id)
        
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        
        # Apply updates recursively
        self._deep_update(profile, updates)
        
        profile["updated_at"] = datetime.now().isoformat()
        self._save_profile(user_id, profile)
        
        return profile
    
    def _deep_update(self, base: Dict, updates: Dict):
        """Recursively update nested dictionaries"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _save_profile(self, user_id: str, profile: Dict):
        """Save profile to file"""
        file_path = self._get_profile_file(user_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
    
    def profile_exists(self, user_id: str) -> bool:
        """Check if a profile exists"""
        return self._get_profile_file(user_id).exists()
    
    def delete_profile(self, user_id: str):
        """Delete a user's profile"""
        file_path = self._get_profile_file(user_id)
        if file_path.exists():
            file_path.unlink()
    
    def get_context_string(self, user_id: str) -> str:
        """
        Build a formatted context string for agents
        
        Args:
            user_id: User identifier
            
        Returns:
            Formatted profile context
        """
        profile = self.get_profile(user_id)
        
        if not profile:
            return "No profile found."
        
        demo = profile.get("demographics", {})
        fitness = profile.get("fitness", {})
        mindfulness = profile.get("mindfulness", {})
        preferences = profile.get("preferences", {})
        workout_freq = preferences.get("workout_frequency", {})
        
        context = f"""## User Profile:
- Age: {demo.get('age')} years
- Gender: {demo.get('gender')}
- Weight: {demo.get('weight')} kg

## Fitness:
- Level: {fitness.get('level')}
- Goals: {', '.join(fitness.get('goals', [])) or 'Not specified'}
- Injuries/Limitations: {', '.join(fitness.get('injuries', [])) or 'None'}

## Workout Preferences:
- Days per week: {workout_freq.get('days_per_week', 'Not set')}
- Minutes per day: {workout_freq.get('minutes_per_day', 'Not set')}

## Mindfulness:
- Experience: {mindfulness.get('experience')}
- Preferences: {', '.join(mindfulness.get('preferences', [])) or 'Not specified'}
"""
        
        return context


if __name__ == "__main__":
    # Test the profile manager
    pm = ProfileManager()
    
    test_user = "test_user_123"
    
    # Create a profile
    profile = pm.create_profile(
        user_id=test_user,
        age=33,
        gender="female",
        weight=54,
        fitness_level="intermediate",
        injuries=["back pain"],
        fitness_goals=["mobility", "flexibility"]
    )
    
    print("Created profile:")
    print(json.dumps(profile, indent=2))
    
    # Update the profile
    pm.update_profile(test_user, {
        "demographics": {"weight": 53},
        "fitness": {"goals": ["mobility", "flexibility", "strength"]}
    })
    
    print("\nProfile context:")
    print(pm.get_context_string(test_user))
