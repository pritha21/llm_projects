# food_agent_sim.py
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_groq import ChatGroq

# --- 1. Import the simulator and tools ---
from simulator import Simulator
from tools import OrderTrackerTool, IssueResolverTool
from database import create_db_and_tables, get_order
import yaml
import difflib
import re

# --- 2. Environment Setup ---
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file")
if not os.getenv("GROQ_MODEL"):
    raise ValueError("GROQ_MODEL not found in .env file")

# --- 3. Tools are imported from tools.py ---
# Custom tool implementations and input schemas are defined in tools.py and imported above.

# --- 4. Evaluation Function ---
def load_ideal_responses():
    """Load and parse ideal_responses.md into a dict of scenarios."""
    try:
        with open('ideal_responses.md', 'r') as file:
            content = file.read()
        # Parse sections by scenario (e.g., ## 1. LATE)
        sections = re.split(r'## \d+\. (\w+)', content)
        ideal_responses = {}
        for i in range(1, len(sections), 2):
            scenario = sections[i]
            text = sections[i+1]
            ideal_responses[scenario] = text.strip()
        return ideal_responses
    except FileNotFoundError:
        return {}

def evaluate_response(scenario: str, actual_response: str, ideal_responses: dict) -> str:
    """Evaluate actual response against ideal template for the scenario."""
    if scenario not in ideal_responses:
        return "No ideal template found for this scenario."
    
    ideal = ideal_responses[scenario]
    # Simple similarity score using difflib
    similarity = difflib.SequenceMatcher(None, actual_response.lower(), ideal.lower()).ratio() * 100
    score = round(similarity, 1)
    
    # Check for key elements
    key_elements = ["empathy", "verification", "tool", "policy", "confirmation"]
    matched_elements = [elem for elem in key_elements if elem in actual_response.lower()]
    
    feedback = f"Evaluation: {score}% similarity to ideal. Matched elements: {', '.join(matched_elements) if matched_elements else 'None'}."
    if score >= 80:
        feedback += " Excellent match!"
    elif score >= 60:
        feedback += " Good, but could improve on key elements."
    else:
        feedback += " Needs improvement—focus on empathy and verification."
    
    return feedback

def parse_few_shot_examples(adaptive_suffix: str):
    """Parse few-shot examples with improved robustness.
    
    Handles:
    - Markdown bold markers (**Few-shot examples:**)
    - Case variations (Few-Shot, few-shot, etc.)
    - Flexible delimiters (Example 1, Example A, etc.)
    - Empty content validation
    """
    # Case-insensitive search for few-shot delimiter, handling markdown bold
    pattern = r'\*\*?Few-?shot examples?:?\*\*?'
    match = re.search(pattern, adaptive_suffix, re.IGNORECASE)
    
    if not match:
        return [], adaptive_suffix
    
    prompt_part = adaptive_suffix[:match.start()].strip()
    examples_part = adaptive_suffix[match.end():].strip()
    
    few_shot_messages = []
    
    # More flexible example matching (Example 1, example A, etc.)
    example_blocks = re.split(r'Example\s+\w+\s*:', examples_part, flags=re.IGNORECASE)[1:]
    
    for i, block in enumerate(example_blocks, 1):
        # Case-insensitive, allows optional bold and spacing
        parts = re.split(r'\*\*?User\s*:\*\*?|\*\*?Agent\s*:\*\*?', block, flags=re.IGNORECASE)
        
        if len(parts) >= 3:
            user_turn = parts[1].strip()
            agent_turn = parts[2].strip()
            
            if user_turn and agent_turn:  # Ensure both are non-empty
                few_shot_messages.append(HumanMessage(content=user_turn))
                few_shot_messages.append(AIMessage(content=agent_turn))
            else:
                print(f"Warning: Example {i} has empty user or agent content, skipping")
        else:
            print(f"Warning: Example {i} doesn't have both User and Agent parts, skipping")
    
    return few_shot_messages, prompt_part

# --- 4. Agent Setup ---
def create_food_delivery_agent(simulator, issue_label=None):
    """Creates the agent with the CORRECT, updated system prompt."""
    tools = [OrderTrackerTool(), IssueResolverTool()]
    llm = ChatGroq(temperature=0, model_name=os.environ["GROQ_MODEL"])

    with open('scenarios.yaml', 'r') as file:
        scenarios = yaml.safe_load(file)
    adaptive_suffix = scenarios.get(issue_label, {}).get('prompt_suffix', "No specific instructions found.")
    
    few_shot_examples, clean_system_prompt = parse_few_shot_examples(adaptive_suffix)

    # REVISED AND STRICTER SYSTEM PROMPT
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are 'Zwiggy', a helpful and highly empathetic food delivery assistant.

You MUST operate in a strict, two-phase conversational model. This is your most important instruction.

**Phase 1: The Empathetic Inquiry (Your FIRST response to the user)**
- Your ONLY goal in this phase is to demonstrate empathy and ask a clarifying question.
- **This phase is MANDATORY and cannot be skipped, even if the user provides all details upfront.**
- Your response MUST be structured as follows:
    1. Start with a strong statement of empathy (e.g., "I'm so sorry to hear that," "That sounds incredibly frustrating").
    2. End with ONE clarifying question to gather or confirm a detail.
- **CRITICAL RESTRICTION:** You are FORBIDDEN from mentioning resolutions, credits, refunds, or escalations. You are FORBIDDEN from calling the `issue_resolver` tool. Your entire job is to be empathetic and ask one question.

**Phase 2: Resolution (All subsequent responses)**
- This phase begins ONLY AFTER the user has answered your first question.
- In this phase, you can use all available tools, including `issue_resolver`, to find a solution based on the confirmed details.
- Follow the specific plan provided to you for the user's issue.

---
**Your current task-specific instructions (for Phase 2) are:**
{clean_system_prompt}"""),
        *few_shot_examples,
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    memory = ConversationBufferWindowMemory(memory_key="chat_history", k=5, return_messages=True)
    # Set verbose to True for debugging if needed, False for clean output
    return AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True), memory

# --- 5. Main Chat Loop ---
class ChatSession:
    def __init__(self):
        create_db_and_tables()
        self.simulator = Simulator()
        self.assigned_order_id = None
        self.issue_label = None
        self.is_first_message = True
        self.ideal_responses = load_ideal_responses()  # Load ideal templates
        self.agent_executor, self.memory = create_food_delivery_agent(self.simulator, self.issue_label)
    def chat(self):
        print("Welcome to Zwiggy support!")
        # Issue menu
        menu = {
            1: "LATE", 2: "MISS", 3: "QUALITY", 4: "WRONG",
            5: "PAYMENT", 6: "ADDRESS", 7: "COLD"
        }
        print("\nPlease select your issue by number:")
        for num, label in menu.items():
            print(f"{num}. {label.replace('_', ' ').title()}")  # e.g., "1. Late"
        print("Type the number (1-7): ")
        
        while True:
            try:
                selection = int(input("You: "))
                if selection in menu:
                    self.issue_label = menu[selection]
                    break
                else:
                    print("Invalid number. Please choose 1-7.")
            except ValueError:
                print("Please enter a number.")
        
        # Assign order with label
        self.assigned_order_id, _ = self.simulator.assign_and_create_order(label=self.issue_label)
        print(f"[SYSTEM INFO]: Assigned to scenario for order {self.assigned_order_id} with issue '{self.issue_label}'.")
        # Create agent with issue_label for adaptive prompt
        self.agent_executor, self.memory = create_food_delivery_agent(self.simulator, self.issue_label)
        self.is_first_message = False
        print(f"\nThanks for selecting {selection}. Your order ID is {self.assigned_order_id}. Tell me more about the issue: ")
        
        resolved = False
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            processed_input = f"{user_input} (My order ID is {self.assigned_order_id}, Issue type: {self.issue_label})"
            try:
                response = self.agent_executor.invoke({"input": processed_input})
                agent_output = response['output']

                # Include tool intermediate steps in chat output
                if 'intermediate_steps' in response and response['intermediate_steps']:
                    for step in response['intermediate_steps']:
                        if len(step) >= 2:
                            tool_name = step[0].tool
                            tool_result = step[1]
                            print(f"[TOOL RESULT - {tool_name}]: {tool_result}")

            except Exception as e:
                # Fallback: Manually call tracker tool for status
                tracker = OrderTrackerTool()
                status_output = tracker._run(self.assigned_order_id)
                agent_output = f"I'm sorry, there was an issue processing your request. Here's the latest status: {status_output}. How can I assist further?"
            
            # Check for resolution: DB note or keywords in agent output
            order = get_order(self.assigned_order_id)
            resolved_via_db = order and order.get('resolution_note')
            
            # Keywords that indicate a resolution has been offered or completed
            resolution_keywords = [
                "has been issued", "has been credited", "has been filed", 
                "has been logged", "complaint has been logged", "is on its way",
                "has been rerouted", "have been added", "has been applied"
            ]
            
            # Check if the agent's output contains any resolution keywords
            resolved_via_keywords = any(keyword in agent_output.lower() for keyword in resolution_keywords)
            
            # Check if the agent is asking for a final confirmation
            is_final_confirmation = "has this resolved your issue" in agent_output.lower()

            if is_final_confirmation:
                print(f"Zwiggy: {agent_output}") # Print the agent's final question
                confirmation = input("You: ")
                if confirmation.lower() in ['yes', 'y']:
                    print("Zwiggy: Great! If you have more questions, feel free to start a new chat. Thank you for using Zwiggy!")
                    resolved = True
                    break
                else:
                    # If user says no, let the loop continue so the agent can respond
                    self.memory.chat_memory.add_user_message(confirmation)
                    continue
            
            print(f"Zwiggy: {agent_output}")
        
        if resolved:
            print("\n--- RESOLUTION CONFIRMED ---")
        print("\n--- CONVERSATION SUMMARY ---")
        print(f"Assigned Scenario Order: {self.assigned_order_id}, Issue: {self.issue_label}")
        print("--------------------------\n")
        print("Ending conversation...")

if __name__ == "__main__":
    session = ChatSession()
    session.chat()