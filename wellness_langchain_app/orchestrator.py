"""
Central Wellness Orchestrator
Routes user requests to appropriate agents (exercise or mindfulness)
Manages user profiles and memories
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
import os
import sys
import yaml
from typing import Dict, Optional, List

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
from agents.exercise_agent import create_exercise_agent
from agents.mindfulness_agent import create_mindfulness_agent
from agents.nutrition_agent import create_nutrition_agent
from memory.memory_manager import MemoryManager
from memory.profile_manager import ProfileManager

load_dotenv(dotenv_path=os.path.join(parent_dir, '.env'))


class WellnessOrchestrator:
    """
    Central orchestrator that routes requests to specialized agents
    and manages user context (profile + memories)
    """
    
    def __init__(self):
        """Initialize the orchestrator with agents and managers"""
        self.exercise_agent = create_exercise_agent()
        self.mindfulness_agent = create_mindfulness_agent()
        self.nutrition_agent = create_nutrition_agent()
        self.memory_manager = MemoryManager()
        self.profile_manager = ProfileManager()
        
        # Load routing examples from YAML
        self.routing_examples = self._load_routing_examples()
        
        # Router LLM for intent classification
        self.router_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,  # Deterministic routing - no creativity needed
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    
    def _load_routing_examples(self) -> List[Dict]:
        """Load routing examples from YAML configuration file"""
        config_path = os.path.join(parent_dir, 'config', 'routing_examples.yaml')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('examples', [])
        except FileNotFoundError:
            print(f"Warning: Routing examples file not found at {config_path}")
            return []
        except yaml.YAMLError as e:
            print(f"Warning: Error parsing routing examples YAML: {e}")
            return []
    
    def _build_examples_prompt(self) -> str:
        """Build few-shot examples section from YAML data"""
        if not self.routing_examples:
            return "No examples available."
        
        examples_text = "**Examples (Learn from these):**\n\n"
        for example in self.routing_examples:
            input_text = example.get('input', '')
            route = example.get('route', '')
            reasoning = example.get('reasoning', '')
            examples_text += f'User: "{input_text}"\n→ {route} ({reasoning})\n\n'
        
        return examples_text
    
    def _route_request(self, user_input: str, user_id: Optional[str] = None) -> str:
        """
        Determine which agent(s) to use based on user input and recent context
        
        Returns: 'exercise', 'mindfulness', 'nutrition', or combination like 'exercise+nutrition'
        """
        # Get recent conversation context if user_id provided
        recent_context = ""
        if user_id:
            recent_memories = self.memory_manager.get_memories(user_id, limit=2)
            if recent_memories:
                recent_context = "\n\nRecent conversation:\n"
                for mem in recent_memories:
                    recent_context += f"- {mem['content']}\n"
        
        # Build examples from YAML
        examples_section = self._build_examples_prompt()
        
        # Use few-shot learning for better routing
        routing_prompt = f"""You are a routing classifier for a wellness system with 3 specialized agents.

**Agents:**
- EXERCISE: Physical fitness, workouts, training
- MINDFULNESS: Mental wellness, meditation, breathing, crisis support  
- NUTRITION: Diet, meals, calories, recipes

**Routing Rules:**
1. CRISIS (suicide, self-harm) → MINDFULNESS (highest priority)
2. Physical movement/strength → EXERCISE
3. Food/eating → NUTRITION
4. Mental wellness → MINDFULNESS
5. Multiple domains → Use + (e.g., EXERCISE+NUTRITION)

{examples_section}
{recent_context}

**Current Request:** "{user_input}"

**Your Task:** Analyze the request and return ONLY the agent name(s).
Valid responses: EXERCISE, MINDFULNESS, NUTRITION, or combinations like EXERCISE+NUTRITION

Response:"""

        # Use temperature=0 for deterministic routing
        response = self.router_llm.invoke(routing_prompt)
        route = response.content.strip().upper()
        
        # Validate and normalize response
        valid_agents = ['EXERCISE', 'MINDFULNESS', 'NUTRITION']
        
        # Handle single agent
        if route in valid_agents:
            return route.lower()
        
        # Handle combinations (e.g., EXERCISE+NUTRITION)
        if '+' in route:
            agents = [a.strip() for a in route.split('+')]
            valid = all(a in valid_agents for a in agents)
            if valid:
                return '+'.join([a.lower() for a in agents])
        
        # Default to mindfulness if unsure (safer for crisis situations)
        return 'mindfulness'
    
    def _build_context(self, user_id: str) -> str:
        """Build context from profile and memories"""
        context_parts = []
        
        # Add profile
        profile_context = self.profile_manager.get_context_string(user_id)
        if profile_context != "No profile found.":
            context_parts.append(profile_context)
        
        # Add memory context
        memory_context = self.memory_manager.get_context(user_id)
        if memory_context != "No previous interactions.":
            context_parts.append("\n" + memory_context)
        
        return "\n".join(context_parts) if context_parts else ""
    
    def invoke(
        self, 
        user_id: str, 
        user_input: str,
        force_agent: Optional[str] = None
    ) -> Dict:
        """
        Main orchestration method
        
        Args:
            user_id: User identifier
            user_input: User's message/request
            force_agent: Optional - force specific agent ('exercise' or 'mindfulness')
            
        Returns:
            Response dictionary with agent output and metadata
        """
        # Build context from profile and memories
        context = self._build_context(user_id)
        
        # Determine routing
        if force_agent:
            route = force_agent
        else:
            route = self._route_request(user_input, user_id)
        
        # Prepare input with context
        full_input = f"""{context}

User Request: {user_input}""" if context else user_input
        
        # Invoke appropriate agent(s)
        result = {
            "user_id": user_id,
            "route": route,
            "response": ""
        }
        
        try:
            if route == 'exercise':
                agent_response = self.exercise_agent.invoke({"input": full_input})
                result["response"] = agent_response['output']
                result["agent_used"] = "Exercise Agent"
                
            elif route == 'mindfulness':
                agent_response = self.mindfulness_agent.invoke({"input": full_input})
                result["response"] = agent_response['output']
                result["agent_used"] = "Mindfulness Agent"
                
            elif route == 'nutrition':
                agent_response = self.nutrition_agent.invoke({"input": full_input})
                result["response"] = agent_response['output']
                result["agent_used"] = "Nutrition Agent"
                
            elif '+' in route:
                # Handle multiple agents
                agents = route.split('+')
                responses = []
                agent_names = []
                
                for agent_name in agents:
                    if agent_name == 'exercise':
                        resp = self.exercise_agent.invoke({"input": full_input})
                        responses.append(("💪 Exercise Guidance", resp['output']))
                        agent_names.append("Exercise")
                    elif agent_name == 'mindfulness':
                        resp = self.mindfulness_agent.invoke({"input": full_input})
                        responses.append(("🧘 Mindfulness Guidance", resp['output']))
                        agent_names.append("Mindfulness")
                    elif agent_name == 'nutrition':
                        resp = self.nutrition_agent.invoke({"input": full_input})
                        responses.append(("🥗 Nutrition Guidance", resp['output']))
                        agent_names.append("Nutrition")
                
                # Combine responses
                combined = []
                for title, content in responses:
                    combined.append(f"**{title}:**\n{content}")
                
                result["response"] = "\n\n" + "─" * 80 + "\n\n".join(combined)
                result["agent_used"] = " + ".join(agent_names) + " Agents"
            
            elif route == 'both':  # Legacy support for old 'both' routing
                # Handle both agents - mindfulness first for stress, then exercise
                mind_response = self.mindfulness_agent.invoke({
                    "input": f"{full_input}\n\nNote: User also needs exercise guidance. Provide mindfulness support first."
                })
                
                exercise_response = self.exercise_agent.invoke({
                    "input": f"{full_input}\n\nNote: Mindfulness support has been provided. Now provide exercise guidance."
                })
                
                result["response"] = f"""**Mindfulness Guidance:**
{mind_response['output']}

---

**Exercise Guidance:**
{exercise_response['output']}"""
                result["agent_used"] = "Mindfulness + Exercise Agents"
            
            # Store interaction in memory
            self.memory_manager.add_memory(
                user_id,
                memory_type="interaction",
                content=f"User asked: {user_input[:100]}... | Response provided via {result['agent_used']}",
                metadata={"route": route}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            result["response"] = error_msg
            result["error"] = str(e)
            return result
    
    # Profile management methods
    def create_user_profile(
        self,
        user_id: str,
        age: int,
        gender: str,
        weight: float,
        **kwargs
    ) -> Dict:
        """Create a new user profile"""
        return self.profile_manager.create_profile(
            user_id, age, gender, weight, **kwargs
        )
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        return self.profile_manager.get_profile(user_id)
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Dict:
        """Update user profile"""
        return self.profile_manager.update_profile(user_id, updates)
    
    def profile_exists(self, user_id: str) -> bool:
        """Check if profile exists"""
        return self.profile_manager.profile_exists(user_id)
    
    # Memory management methods
    def record_action(self, user_id: str, action: str, metadata: Optional[Dict] = None):
        """Record a user action"""
        self.memory_manager.add_memory(
            user_id,
            memory_type="action",
            content=action,
            metadata=metadata
        )
    
    def record_preference(self, user_id: str, preference: str, metadata: Optional[Dict] = None):
        """Record a user preference"""
        self.memory_manager.add_memory(
            user_id,
            memory_type="preference",
            content=preference,
            metadata=metadata
        )
    
    def get_user_context(self, user_id: str) -> str:
        """Get full context for user (profile + memories)"""
        return self._build_context(user_id)


if __name__ == "__main__":
    # Test the orchestrator
    print("Testing Wellness Orchestrator...")
    print("=" * 70)
    
    orchestrator = WellnessOrchestrator()
    
    test_user = "test_user_456"
    
    # Create profile
    print("\n1. Creating user profile...")
    profile = orchestrator.create_user_profile(
        user_id=test_user,
        age=28,
        gender="female",
        weight=60,
        fitness_level="beginner",
        injuries=["none"],
        fitness_goals=["weight loss", "stress relief"]
    )
    print(f"Profile created: {profile['user_id']}")
    
    # Test exercise routing
    print("\n2. Testing exercise request...")
    result = orchestrator.invoke(
        test_user,
        "I want to lose weight. I can exercise 30 minutes a day, 4 days a week."
    )
    print(f"Route: {result['route']}")
    print(f"Agent: {result['agent_used']}")
    print(f"Response: {result['response'][:200]}...")
    
    # Test mindfulness routing
    print("\n3. Testing mindfulness request...")
    result = orchestrator.invoke(
        test_user,
        "I'm feeling very stressed and anxious. I need help relaxing."
    )
    print(f"Route: {result['route']}")
    print(f"Agent: {result['agent_used']}")
    print(f"Response: {result['response'][:200]}...")
    
    # Check memories
    print("\n4. Checking stored memories...")
    context = orchestrator.get_user_context(test_user)
    print(context)
