#!/usr/bin/env python3
"""
LLM-as-Judge Implementation for Zwiggy Chatbot Evaluation

This module adds LLM-based evaluation to complement your existing 
semantic similarity approach. It's the current industry standard.

Usage:
    python llm_judge_implementation.py
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


class LLMJudge:
    """
    LLM-based evaluator for chatbot responses.
    Uses a strong LLM to judge response quality across multiple dimensions.
    """
    
    def __init__(self, model_name=None):
        """Initialize the LLM judge"""
        self.model_name = model_name or os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        self.llm = ChatGroq(temperature=0, model_name=self.model_name)
    
    def evaluate_response(self, scenario: str, user_input: str, agent_response: str, 
                         phase: int, tool_calls: list = None) -> dict:
        """
        Evaluate a single agent response using LLM judgment.
        
        Args:
            scenario: The scenario type (LATE, MISS, etc.)
            user_input: What the user said
            agent_response: What the agent replied
            phase: Conversation phase (1 or 2)
            tool_calls: List of tools the agent called
            
        Returns:
            Dictionary with scores and analysis
        """
        
        # Construct the evaluation prompt
        prompt = self._build_evaluation_prompt(
            scenario, user_input, agent_response, phase, tool_calls
        )
        
        # Get LLM judgment
        result = self.llm.invoke(prompt)
        
        # Parse the response
        try:
            scores = self._parse_llm_response(result.content)
            return scores
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return self._get_default_scores()
    
    def _build_evaluation_prompt(self, scenario, user_input, agent_response, 
                                 phase, tool_calls):
        """Build the evaluation prompt for the LLM judge"""
        
        tool_info = ""
        if tool_calls:
            tool_info = f"\n**Tools Called**: {', '.join(tool_calls)}"
        
        prompt = f"""You are an expert evaluator for customer support chatbot quality.

**Context:**
- Scenario Type: {scenario}
- Conversation Phase: {phase}
- User Query: "{user_input}"
- Agent Response: "{agent_response}"{tool_info}

**Evaluation Task:**
Rate the agent's response on the following dimensions (0-10 scale):

1. **Empathy (0-10)**: Does the agent acknowledge the customer's frustration with genuine care and understanding?
   - 0-3: Robotic, dismissive, or no empathy
   - 4-6: Basic acknowledgment but feels scripted
   - 7-8: Good empathy, feels genuine
   - 9-10: Exceptional empathy, makes customer feel truly heard

2. **Accuracy (0-10)**: Does the agent use correct, verified information?
   - 0-3: Hallucinated facts, wrong information
   - 4-6: Mostly accurate but vague
   - 7-8: Accurate with specific details
   - 9-10: Precise, verified information from tools

3. **Policy Compliance (0-10)**: Does the response follow company support policies?
   - 0-3: Major policy violations
   - 4-6: Minor deviations from policy
   - 7-8: Follows policy appropriately
   - 9-10: Perfect policy adherence with good judgment

4. **Resolution Quality (0-10)**: Is the proposed solution appropriate and effective?
   - 0-3: No solution or inappropriate solution
   - 4-6: Partial solution or unclear next steps
   - 7-8: Good solution, clearly communicated
   - 9-10: Optimal solution with clear confirmation

5. **Phase Compliance (0-10)**: Does the response follow phase-specific rules?
   - Phase 1: Must express empathy + ask clarifying question. Must NOT offer resolutions.
   - Phase 2: Must offer clear solution + ask for confirmation.
   
   - 0-3: Major phase violations (e.g., offering credits in Phase 1)
   - 4-6: Partial compliance with phase requirements
   - 7-8: Follows phase rules correctly
   - 9-10: Exemplary phase adherence

**Phase-Specific Requirements:**
{"- Phase 1: Start with empathy, gather information, ask ONE clarifying question. DO NOT offer solutions, credits, or resolutions." if phase == 1 else "- Phase 2: Provide a clear solution based on confirmed details, ask for final confirmation."}

**Output Format (JSON only, no other text):**
{{
    "empathy": <score 0-10>,
    "accuracy": <score 0-10>,
    "policy_compliance": <score 0-10>,
    "resolution_quality": <score 0-10>,
    "phase_compliance": <score 0-10>,
    "overall_score": <average of above>,
    "justification": "<2-3 sentence explanation of scores>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"],
    "failure_modes": ["<any detected failures, e.g., 'hallucination', 'phase_violation', 'empathy_failure'>"]
}}
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> dict:
        """Parse the LLM's JSON response"""
        # Extract JSON from response (in case LLM adds extra text)
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")
        
        json_str = response_text[start:end]
        scores = json.loads(json_str)
        
        return scores
    
    def _get_default_scores(self) -> dict:
        """Return default scores if parsing fails"""
        return {
            "empathy": 0,
            "accuracy": 0,
            "policy_compliance": 0,
            "resolution_quality": 0,
            "phase_compliance": 0,
            "overall_score": 0,
            "justification": "Error parsing LLM response",
            "strengths": [],
            "weaknesses": ["Evaluation failed"],
            "failure_modes": ["evaluation_error"]
        }
    
    def compare_responses(self, user_input: str, response_a: str, response_b: str) -> dict:
        """
        Pairwise comparison of two responses (useful for A/B testing).
        
        Returns which response is better and why.
        """
        prompt = f"""You are comparing two customer support chatbot responses.

**User Query**: "{user_input}"

**Response A**: "{response_a}"

**Response B**: "{response_b}"

**Task**: Determine which response is better for customer support.

**Output Format (JSON only):**
{{
    "winner": "A" or "B" or "tie",
    "confidence": <0.0-1.0, how confident are you>,
    "reasoning": "<2-3 sentences explaining your choice>",
    "dimension_comparison": {{
        "empathy": "A" or "B" or "tie",
        "accuracy": "A" or "B" or "tie",
        "clarity": "A" or "B" or "tie",
        "professionalism": "A" or "B" or "tie"
    }}
}}
"""
        result = self.llm.invoke(prompt)
        
        try:
            return self._parse_llm_response(result.content)
        except:
            return {"winner": "tie", "confidence": 0.0, "reasoning": "Error in comparison"}


def demo_llm_judge():
    """Demonstrate LLM-as-judge evaluation"""
    
    judge = LLMJudge()
    
    # Example 1: Phase 1 response (Good)
    print("=" * 80)
    print("EXAMPLE 1: Phase 1 - Good Response")
    print("=" * 80)
    
    result1 = judge.evaluate_response(
        scenario="LATE",
        user_input="my order is late by 50 mins",
        agent_response="I'm so sorry to hear your order is running this late. My tracker shows it's out for delivery and was expected about 40 minutes ago. Does that match what you're seeing?",
        phase=1,
        tool_calls=["order_tracker"]
    )
    
    print(json.dumps(result1, indent=2))
    
    # Example 2: Phase 1 response (Bad - offers resolution too early)
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Phase 1 - Bad Response (Offers Resolution)")
    print("=" * 80)
    
    result2 = judge.evaluate_response(
        scenario="LATE",
        user_input="my order is late by 50 mins",
        agent_response="I'm sorry for the delay. I've just added a credit to your account for the inconvenience. Is there anything else I can help with?",
        phase=1,
        tool_calls=["issue_resolver"]  # Wrong tool for Phase 1!
    )
    
    print(json.dumps(result2, indent=2))
    
    # Example 3: Pairwise comparison
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Pairwise Comparison")
    print("=" * 80)
    
    comparison = judge.compare_responses(
        user_input="my order is late by 50 mins",
        response_a="I'm so sorry to hear your order is running this late. My tracker shows it's out for delivery and was expected about 40 minutes ago. Does that match what you're seeing?",
        response_b="Sorry for the delay. Your order should arrive soon. Can I help with anything else?"
    )
    
    print(json.dumps(comparison, indent=2))


# Integration with existing test_evaluation.py
def integrate_with_existing_tests():
    """
    Example of how to add LLM-judge to your existing test_evaluation.py
    """
    
    code_example = '''
# In your test_evaluation.py, add this:

from llm_judge_implementation import LLMJudge

# Initialize once
llm_judge = LLMJudge()

# In your test_scenario function, after semantic evaluation:
def test_scenario(model, issue_label, user_input, ideal_responses):
    """Run one scenario using both semantic similarity AND LLM-as-judge"""
    
    # ... existing code ...
    
    # Phase 1 evaluation
    response1 = agent_executor.invoke({"input": processed_input})
    agent_output1 = response1['output']
    
    # Existing semantic evaluation
    semantic_eval1 = evaluate_response(model, issue_label, agent_output1, ideal_responses, phase=1)
    
    # NEW: LLM-as-judge evaluation
    llm_eval1 = llm_judge.evaluate_response(
        scenario=issue_label,
        user_input=user_input,
        agent_response=agent_output1,
        phase=1,
        tool_calls=[step[0].tool for step in response1.get('intermediate_steps', [])]
    )
    
    # Print both evaluations
    print(f"  [Semantic Eval Phase 1]: {semantic_eval1}")
    print(f"  [LLM Judge Phase 1]: Overall={llm_eval1['overall_score']:.1f}/10")
    print(f"    Empathy: {llm_eval1['empathy']}/10, Phase Compliance: {llm_eval1['phase_compliance']}/10")
    print(f"    Justification: {llm_eval1['justification']}")
    if llm_eval1['failure_modes']:
        print(f"    ⚠️ Failures: {', '.join(llm_eval1['failure_modes'])}")
    
    # Continue with Phase 2...
    
    return {
        'scenario': issue_label,
        'user_input': user_input,
        'phase1_response': agent_output1,
        'phase1_semantic_eval': semantic_eval1,
        'phase1_llm_eval': llm_eval1,  # NEW
        # ... Phase 2 results ...
    }
'''
    
    print("\n" + "=" * 80)
    print("INTEGRATION GUIDE")
    print("=" * 80)
    print(code_example)


if __name__ == "__main__":
    print("🧪 LLM-as-Judge Evaluation Demo\n")
    
    # Run demonstration
    demo_llm_judge()
    
    # Show integration guide
    integrate_with_existing_tests()
    
    print("\n" + "=" * 80)
    print("✅ Demo Complete!")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Copy this file to your project")
    print("2. Import LLMJudge in test_evaluation.py")
    print("3. Add llm_judge.evaluate_response() calls after semantic evaluation")
    print("4. Compare both evaluation methods in your reports")
    print("\nThis gives you both reference-based AND model-based evaluation!")
