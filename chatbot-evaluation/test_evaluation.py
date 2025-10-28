#!/usr/bin/env python3
"""
Test script to evaluate agent responses in a continuous conversation.
The agent's ability to handle the two-phase flow is guided by the prompt
and evaluated by the scoring function.

This version includes DUAL EVALUATION:
- Semantic Similarity (reference-based)
- LLM-as-Judge (model-based)
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_groq import ChatGroq

from sentence_transformers import SentenceTransformer, util
from simulator import Simulator
from tools import OrderTrackerTool, IssueResolverTool
from database import create_db_and_tables
import yaml
import difflib
import re

# Import LLM-as-Judge evaluator
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from llm_judge_implementation import LLMJudge

# Load environment
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file")
if not os.getenv("GROQ_MODEL"):
    raise ValueError("GROQ_MODEL not found in .env file")


def load_ideal_responses():
    """Load and parse ideal_responses.md into a dict of scenarios."""
    try:
        with open('ideal_responses.md', 'r', encoding='utf-8') as file:
            content = file.read()
        sections = re.split(r'## \d+\. (.+?)\n', content)
        ideal_responses = {}
        for i in range(1, len(sections), 2):
            scenario_title = sections[i].strip().split('(')[0].strip()
            text = sections[i+1].strip()
            flow_match = re.search(r'\*\*Ideal Flow\*\*:(.*)', text, re.DOTALL)
            flow_text = flow_match.group(1).strip() if flow_match else text
            ideal_responses[scenario_title.upper()] = {'flow': flow_text}
        return ideal_responses
    except FileNotFoundError:
        print("Error: ideal_responses.md not found.")
        return {}


# --- REWRITTEN EVALUATION FUNCTION ---
def evaluate_response(model: SentenceTransformer, scenario: str, actual_response: str, ideal_responses: dict, phase: int = 1) -> str:
    """Evaluate the agent's response using semantic similarity."""
    if scenario not in ideal_responses:
        return "No ideal template found for this scenario."

    flow_text = ideal_responses[scenario]['flow']
    agent_lines = re.findall(r'(?:Agent|Agent\*\*):\s*(.*)', flow_text, re.IGNORECASE)

    ideal_agent_response = ""
    if phase == 1 and len(agent_lines) > 0:
        ideal_agent_response = agent_lines[0].strip()
    elif phase == 2 and len(agent_lines) > 1:
        ideal_agent_response = agent_lines[1].strip()
    
    if not ideal_agent_response:
        return f"No ideal response found for Phase {phase} in the template."

    # Generate embeddings for both actual and ideal responses
    embedding_actual = model.encode(actual_response, convert_to_tensor=True)
    embedding_ideal = model.encode(ideal_agent_response, convert_to_tensor=True)

    # Compute cosine similarity (overall semantic alignment)
    cosine_score = util.cos_sim(embedding_actual, embedding_ideal)[0]
    semantic_score = round(float(cosine_score) * 100, 1)

    # Compute semantic rubric sub-scores
    rubric = semantic_rubric_scores(model, actual_response)

    # Weighted rubric score from ideal_responses.md rubric (Accuracy 30, Empathy 30, Resolution 25, Clarity 15)
    weights = {'accuracy': 0.3, 'empathy': 0.3, 'resolution': 0.25, 'clarity_tone': 0.15}
    rubric_weighted = round(sum(rubric[k] * weights[k] for k in weights), 1)

    feedback = (
        f"Phase {phase} Semantic Score: {semantic_score}% | "
        f"Accuracy: {rubric['accuracy']}%, Empathy: {rubric['empathy']}%, "
        f"Resolution: {rubric['resolution']}%, Clarity Tone: {rubric['clarity_tone']}% | "
        f"Rubric Score: {rubric_weighted}%"
    )
    return feedback

def semantic_rubric_scores(model: SentenceTransformer, text: str) -> dict:
    """Compute rubric sub-scores using simple phrase-count matching per category.

    Scoring rule: if 5 phrases match => 100%; 4 => 80%; ..., 1 => 20%; 0 => 0%.
    More than 5 matches are capped at 100%.
    """
    # Normalize text for robust substring matching
    def norm(s: str) -> str:
        s = s.lower()
        # normalize fancy quotes/dashes
        s = s.replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    text_norm = norm(text)

    exemplars = {
        'accuracy': [
            "tracker shows", "current status", "eta", "items in your order", "confirm", "order id", "ord-",
            "was expected", "out for delivery", "driver is en route", "delivered", "preparing"
        ],
        'empathy': [
            "i'm sorry", "so sorry", "i understand", "i know this is frustrating", "thanks for your patience",
            "apologize for the inconvenience", "that sounds disappointing"
        ],
        'resolution': [
            "issued a credit", "partial credit", "processed a refund", "full refund", "replacement","partial refund","resolution",
            "resend the order", "updated the address", "escalated this", "logged the issue", "applied a voucher"
        ],
        'clarity_tone': [
            "please", "thank you", "could you", "can you", "let me", "i can help", "i'll take care of this",
            "here's what i've done", "anything else i can assist you with",
            "has this resolved your issue", "does this resolve your issue", "does this help", "has this been resolved",
            "let me know if you need anything else", "please confirm", "thanks for confirming", "please share",
            "please provide", "please let me know"
        ],
    }

    TARGET_MATCHES = {'default': 3, 'clarity_tone': 1}  # anchors per category (clarity uses 3)
    scores = {}
    for cat, phrases in exemplars.items():
        target = TARGET_MATCHES.get(cat, TARGET_MATCHES['default'])
        matches = 0
        for p in phrases:
            if norm(p) in text_norm:
                matches += 1
        pct = min(matches, target) / target * 100.0
        scores[cat] = round(pct, 1)

    # Ensure all keys present
    for k in ['accuracy', 'empathy', 'resolution', 'clarity_tone']:
        scores.setdefault(k, 0.0)
    return scores


def get_phase2_user_from_ideal(ideal_responses: dict, scenario: str) -> str:
    """Extract the second user turn from the ideal flow."""
    flow = ideal_responses.get(scenario, {}).get('flow', '')
    if not flow:
        return "Yes, that's correct. Can you fix it?"
    user_lines = re.findall(r'(?:User|User\*\*):\s*(.*)', flow, re.IGNORECASE)
    return user_lines[1].strip() if len(user_lines) > 1 else "Yes, that's correct. Can you fix it?"


def parse_few_shot_examples(adaptive_suffix: str):
    """Parse few-shot examples from the prompt suffix in scenarios.yaml."""
    # REFACTORED: Simplified logic to robustly split prompt from examples
    # Primary: match the YAML header style used in scenarios.yaml
    match = re.search(r"^\s*\[FEW-SHOT EXAMPLES\]\s*$", adaptive_suffix, re.IGNORECASE | re.MULTILINE)
    # Fallback: support the older $$ ... $$ marker if present
    if not match:
        match = re.search(r"\$\$\s*[\r\n]+\s*FEW-SHOT EXAMPLES\s*[\r\n]+\s*\$\$", adaptive_suffix, re.IGNORECASE)
    if not match:
        return [], adaptive_suffix

    prompt_part = adaptive_suffix[:match.start()].strip()
    examples_part = adaptive_suffix[match.end():].strip()
    
    few_shot_messages = []
    example_blocks = re.split(r'Example\s+\d+\s*:', examples_part, flags=re.IGNORECASE)[1:]
    for block in example_blocks:
        parts = re.split(r'User:|Agent:', block, flags=re.IGNORECASE)
        if len(parts) >= 3:
            user_turn, agent_turn = parts[1].strip(), parts[2].strip()
            if user_turn and agent_turn:
                few_shot_messages.append(HumanMessage(content=user_turn))
                few_shot_messages.append(AIMessage(content=agent_turn))
    return few_shot_messages, prompt_part

# --- REFACTORED AGENT CREATION ---
def create_food_delivery_agent(issue_label: str):
    """
    Builds a single, unified agent that uses the instructions from scenarios.yaml.
    """
    tools = [OrderTrackerTool(), IssueResolverTool()]
    llm = ChatGroq(temperature=0, model_name=os.environ["GROQ_MODEL"])

    with open('scenarios.yaml', 'r', encoding='utf-8') as file:
        scenarios = yaml.safe_load(file)
    
    adaptive_suffix = scenarios.get(issue_label, {}).get('prompt_suffix', "No specific instructions found.")
    few_shot_examples, clean_system_prompt = parse_few_shot_examples(adaptive_suffix)

    # Mirror Streamlit: single system message with strict two-phase rules and Phase-2-scoped scenario instructions
    system_message = (
        "You are 'Zwiggy', a helpful and highly empathetic food delivery assistant.\n\n"
        "You MUST operate in a strict, two-phase conversational model.\n\n"
        "**Phase 1: Information Gathering (Your FIRST response ONLY)**\n"
        "- Your ONLY objective in this phase is to understand the user's problem.\n"
        "- Your response MUST start with empathy.\n"
        "- Your response MUST end with ONE clarifying question.\n"
        "- You MUST call the `order_tracker` tool in this phase to check status/items/ETA BEFORE replying.\n"
        "- You MUST always produce a short, user-facing reply after using tools. Never return an empty output.\n"
        "- **CRITICAL RESTRICTION:** You are FORBIDDEN from calling the `issue_resolver` tool in this phase. Do not offer solutions, credits, refunds, or resolutions of any kind. Do NOT claim to have taken any resolution action. Your entire goal is to ask a question.\n"
        "- Compliance Check (apply before sending your reply): Ensure your reply (1) starts with one short apology, (2) ends with exactly one clarifying question, (3) contains no credits/refunds/resolutions, (4) does not claim tool actions you didn't actually perform. If any check fails, rewrite it to comply.\n\n"
        "**Phase 2: Resolution (All subsequent responses)**\n"
        "- After the user has answered your first question, you enter this phase.\n"
        "- In this phase, you can use all available tools, including `issue_resolver`, to find a solution.\n"
        "- Follow the specific plan provided to you for the user's issue.\n"
        "- Propose a clear solution and ask for confirmation.\n\n"
        "---\n"
        "**Your current task-specific instructions (for Phase 2) are:**\n"
        f"{clean_system_prompt}"
    )

    # Use few-shot examples in their original order (no reordering), matching Streamlit

    # UNIFIED PROMPT: This is the single source of truth for the agent's behavior.
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        *few_shot_examples,
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    memory = ConversationBufferWindowMemory(memory_key="chat_history", k=5, return_messages=True)
    return AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True, return_intermediate_steps=True)

# --- REFACTORED AND SIMPLIFIED TEST SCENARIO ---
# --- UPDATED TEST SCENARIO FUNCTION ---
def test_scenario(model: SentenceTransformer, llm_judge: LLMJudge, issue_label: str, user_input: str, ideal_responses: dict):
    """
    Run one scenario using a single, persistent agent instance.
    Evaluates responses using BOTH semantic similarity and LLM-as-judge.
    """

    print(f"\n--- Testing Scenario: {issue_label} ---")
    
    # Setup the environment for this test
    create_db_and_tables()
    simulator = Simulator()
    assigned_order_id, _ = simulator.assign_and_create_order(label=issue_label)
    print(f"  [System]: Order {assigned_order_id} created for '{issue_label}'.")

    # The input now includes the order ID, as it would in a real scenario
    processed_input = f"{user_input} (My order ID is {assigned_order_id}). This is the initial description of the issue."

    try:
        # 1. Create ONE agent that will handle the entire conversation
        agent_executor = create_food_delivery_agent(issue_label)

        # 2. Invoke for Phase 1
        response1 = agent_executor.invoke({"input": processed_input})
        agent_output1 = response1['output']
        print(f"  [User]: {user_input}")
        print(f"  [Agent Phase 1]: {agent_output1}")
        
        # Extract tool calls from intermediate steps
        tool_calls_phase1 = [step[0].tool for step in response1.get('intermediate_steps', [])]
        
        # Phase-1 non-compliance guard: if the reply claims a resolution, ask for a compliant rewrite once
        resolution_cues = [
            "issued a credit", "processed a refund", "full refund", "credited", "voucher",
            "delivery credits", "added a credit", "replacement is on its way", "resend the order",
            "has been applied", "have been added", "has been issued", "has been credited"
        ]
        if any(cue in (agent_output1 or "").lower() for cue in resolution_cues):
            print("  [Guard]: Phase 1 reply mentioned a resolution. Requesting compliant rewrite...")
            correction_prompt = (
                "Phase 1 compliance check: Rewrite your previous reply to strictly follow Phase 1. "
                "Start with one short apology. Use the 'order_tracker' tool to state current status/items/ETA. "
                "End with exactly one clarifying question. Do NOT claim credits, refunds, replacements, or resolutions."
            )
            response1b = agent_executor.invoke({"input": correction_prompt})
            agent_output1 = response1b['output']
            tool_calls_phase1 = [step[0].tool for step in response1b.get('intermediate_steps', [])]
            print(f"  [Agent Phase 1 - Corrected]: {agent_output1}")

        # DUAL EVALUATION - Phase 1
        # 1. Semantic Similarity Evaluation (reference-based)
        semantic_eval1 = evaluate_response(model, issue_label, agent_output1, ideal_responses, phase=1)
        print(f"  [Semantic Eval Phase 1]: {semantic_eval1}")
        
        # 2. LLM-as-Judge Evaluation (model-based)
        llm_eval1 = llm_judge.evaluate_response(
            scenario=issue_label,
            user_input=user_input,
            agent_response=agent_output1,
            phase=1,
            tool_calls=tool_calls_phase1
        )
        print(f"  [LLM Judge Phase 1]: Overall={llm_eval1['overall_score']:.1f}/10")
        print(f"    Empathy: {llm_eval1['empathy']}/10, Accuracy: {llm_eval1['accuracy']}/10, Phase Compliance: {llm_eval1['phase_compliance']}/10")
        print(f"    Justification: {llm_eval1['justification']}")
        if llm_eval1.get('failure_modes'):
            print(f"    ⚠️ Failure Modes: {', '.join(llm_eval1['failure_modes'])}")

        # 3. Get simulated user reply for Phase 2
        phase2_user_input = get_phase2_user_from_ideal(ideal_responses, issue_label) + " Confirmed."
        
        # 4. Invoke for Phase 2 - The SAME agent continues the conversation
        response2 = agent_executor.invoke({"input": phase2_user_input})
        agent_output2 = response2['output']
        print(f"  [User]: {phase2_user_input}")
        print(f"  [Agent Phase 2]: {agent_output2}")
        
        # Extract tool calls from Phase 2 intermediate steps
        tool_calls_phase2 = [step[0].tool for step in response2.get('intermediate_steps', [])]
        
        # DUAL EVALUATION - Phase 2
        # 1. Semantic Similarity Evaluation (reference-based)
        semantic_eval2 = evaluate_response(model, issue_label, agent_output2, ideal_responses, phase=2)
        print(f"  [Semantic Eval Phase 2]: {semantic_eval2}")
        
        # 2. LLM-as-Judge Evaluation (model-based)
        llm_eval2 = llm_judge.evaluate_response(
            scenario=issue_label,
            user_input=phase2_user_input,
            agent_response=agent_output2,
            phase=2,
            tool_calls=tool_calls_phase2
        )
        print(f"  [LLM Judge Phase 2]: Overall={llm_eval2['overall_score']:.1f}/10")
        print(f"    Resolution Quality: {llm_eval2['resolution_quality']}/10, Policy Compliance: {llm_eval2['policy_compliance']}/10")
        print(f"    Justification: {llm_eval2['justification']}")
        if llm_eval2.get('failure_modes'):
            print(f"    ⚠️ Failure Modes: {', '.join(llm_eval2['failure_modes'])}")

        return {
            'scenario': issue_label,
            'user_input': user_input,
            'phase1_response': agent_output1,
            'phase1_semantic_eval': semantic_eval1,
            'phase1_llm_eval': llm_eval1,
            'phase2_response': agent_output2,
            'phase2_semantic_eval': semantic_eval2,
            'phase2_llm_eval': llm_eval2
        }
    except Exception as e:
        print(f"  [Error]: An error occurred during the test for {issue_label}: {e}")
        import traceback
        traceback.print_exc()
        return {"scenario": issue_label, "error": str(e)}


def main():
    print("--- Running Zwiggy Agent Evaluation Suite (Dual Evaluation Mode) ---")
    
    # 1. Load the sentence-transformer model for semantic similarity
    print("Loading semantic similarity model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Semantic model loaded.")
    
    # 2. Initialize LLM-as-Judge evaluator
    print("Initializing LLM-as-Judge evaluator...")
    llm_judge = LLMJudge()
    print("LLM Judge initialized.")

    test_cases = [
        ("LATE", "my order is late by 50 mins"),
        ("MISS", "missing Chicken Burger"),
        ("QUALITY", "The sushi was warm and stale."),
        ("WRONG", "I got a pepperoni pizza instead of a veggie one."),
        ("PAYMENT", "I was charged twice for my order."),
        ("ADDRESS", "My order is going to the wrong address!"),
        ("COLD", "My hot wings arrived cold."),
        ("TRACK", "Where is my food?")
    ]
    results = []
    ideal_responses = load_ideal_responses()

    for issue_label, user_input in test_cases:
        # Pass both evaluators to the test scenario
        result = test_scenario(model, llm_judge, issue_label, user_input, ideal_responses)
        results.append(result)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"evaluation_report_{timestamp}.md"
    md_content = f"# Agent Evaluation Report (Dual Evaluation Mode)\n"
    md_content += f"**Generated:** {timestamp}\n\n"
    md_content += "This report includes **two evaluation methods**:\n"
    md_content += "1. **Semantic Similarity**: Reference-based comparison against ideal responses\n"
    md_content += "2. **LLM-as-Judge**: Model-based evaluation across multiple dimensions\n\n"
    md_content += "---\n\n"
    
    for res in results:
        if "error" in res:
            md_content += f"## Scenario: {res['scenario']}\n- **Error**: {res['error']}\n\n"
        else:
            md_content += f"## Scenario: {res['scenario']}\n\n"
            md_content += f"### User Input\n`{res['user_input']}`\n\n"
            
            # Phase 1
            md_content += f"### Phase 1: Information Gathering\n\n"
            md_content += f"**Agent Response:**\n> {res['phase1_response']}\n\n"
            
            md_content += f"**Semantic Evaluation:**\n- `{res['phase1_semantic_eval']}`\n\n"
            
            llm1 = res['phase1_llm_eval']
            md_content += f"**LLM-as-Judge Evaluation:**\n"
            md_content += f"- **Overall Score:** {llm1['overall_score']:.1f}/10\n"
            md_content += f"- **Empathy:** {llm1['empathy']}/10\n"
            md_content += f"- **Accuracy:** {llm1['accuracy']}/10\n"
            md_content += f"- **Phase Compliance:** {llm1['phase_compliance']}/10\n"
            md_content += f"- **Policy Compliance:** {llm1['policy_compliance']}/10\n"
            md_content += f"- **Justification:** {llm1['justification']}\n"
            if llm1.get('strengths'):
                md_content += f"- **Strengths:** {', '.join(llm1['strengths'])}\n"
            if llm1.get('weaknesses'):
                md_content += f"- **Weaknesses:** {', '.join(llm1['weaknesses'])}\n"
            if llm1.get('failure_modes'):
                md_content += f"- ⚠️ **Failure Modes:** {', '.join(llm1['failure_modes'])}\n"
            md_content += "\n"
            
            # Phase 2
            md_content += f"### Phase 2: Resolution\n\n"
            md_content += f"**Agent Response:**\n> {res['phase2_response']}\n\n"
            
            md_content += f"**Semantic Evaluation:**\n- `{res['phase2_semantic_eval']}`\n\n"
            
            llm2 = res['phase2_llm_eval']
            md_content += f"**LLM-as-Judge Evaluation:**\n"
            md_content += f"- **Overall Score:** {llm2['overall_score']:.1f}/10\n"
            md_content += f"- **Resolution Quality:** {llm2['resolution_quality']}/10\n"
            md_content += f"- **Accuracy:** {llm2['accuracy']}/10\n"
            md_content += f"- **Phase Compliance:** {llm2['phase_compliance']}/10\n"
            md_content += f"- **Policy Compliance:** {llm2['policy_compliance']}/10\n"
            md_content += f"- **Justification:** {llm2['justification']}\n"
            if llm2.get('strengths'):
                md_content += f"- **Strengths:** {', '.join(llm2['strengths'])}\n"
            if llm2.get('weaknesses'):
                md_content += f"- **Weaknesses:** {', '.join(llm2['weaknesses'])}\n"
            if llm2.get('failure_modes'):
                md_content += f"- ⚠️ **Failure Modes:** {', '.join(llm2['failure_modes'])}\n"
            
            md_content += "\n---\n\n"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"\n--- Evaluation Complete. Report saved: {report_filename} ---")
    print(f"Report includes both Semantic Similarity and LLM-as-Judge evaluations!")


if __name__ == "__main__":
    main()

