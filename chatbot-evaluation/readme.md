
# Food Delivery Support Chatbot with Evaluation Framework

## Overview
This is a comprehensive customer support chatbot system for a food delivery service, named "Groq-Feast". It features both an intelligent conversational AI agent and a sophisticated evaluation framework to ensure quality interactions.

### Core Components:
1. **Intelligent Chatbot**: Uses LangChain with Groq LLM (Llama-3.3-70b-versatile) to handle customer issues
2. **Evaluation Framework**: Dual evaluation system combining semantic similarity analysis and LLM-as-judge methodology
3. **Two-Phase Protocol**: Enforces empathy-first engagement before problem resolution
4. **YAML-Driven Configuration**: Scenario-based behavior management through configuration files

The system handles common issues like late deliveries, missing items, quality problems, and payment issues. The bot is empathetic, conservative with refunds, and uses verification tools before proposing resolutions.

## Setup
1. **Dependencies**: Install from `requirements.txt` (includes langchain, langchain-groq, pydantic, sqlite3, pyyaml, python-dotenv, numpy, scikit-learn).
   ```
   pip install -r requirements.txt
   ```

2. **Environment Variables**: Create `.env` with your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

3. **Database**: Runs automatically on start (creates `food_delivery.db`).

4. **Run the Chatbot**:
   ```
   python main.py
   ```
   - Select an issue by number (1-7).
   - Interact with the bot; type 'exit' to end.

5. **Run Evaluation Tests**:
   ```
   python test_evaluation.py
   ```
   - Automated testing across all scenarios
   - Performance analysis and reporting
   - Quality metrics and insights

## File Structure
### Core Application
- **main.py**: Core app. Sets up LangChain agent, memory, prompts, and chat loop with menu selection, error handling, and resolution confirmation.
- **simulator.py**: Generates order IDs, assigns scenarios from `scenarios.yaml` (via menu or keywords), creates orders in DB.
- **tools.py**: Custom LangChain tools:
  - `OrderTrackerTool`: Fetches order status/ETA from DB.
  - `IssueResolverTool`: Logs resolutions (e.g., refunds, credits) with aliases (e.g., 'LATE' → 'late_delivery') and conditional messages.
- **database.py**: SQLite operations for orders table (order_id, status, items, eta, issue_label, resolution_note).

### Evaluation Framework
- **test_evaluation.py**: Automated testing system with dual evaluation methodology
- **evaluation_metrics.py**: Semantic similarity calculation and LLM-as-judge evaluation
- **scenario_performance.py**: Performance analysis across different issue types
- **evaluation_results.json**: Automated test results and metrics storage

### Configuration & Data
- **scenarios.yaml**: Templates for issues (LATE, MISS, QUALITY, WRONG, PAYMENT, ADDRESS, COLD) with status, items, ETA.
- **requirements.txt**: Dependencies (langchain, langchain-groq, pydantic, pyyaml, python-dotenv, numpy, scikit-learn).
- **.env**: API keys (GROQ_API_KEY).
- **food_delivery.db**: Auto-generated SQLite DB.

## How It Works

### Two-Phase Conversational Protocol
The chatbot follows a novel two-phase approach:
1. **Phase 1 - Gathering**: Empathetic information collection and user acknowledgment
2. **Phase 2 - Resolution**: Problem-solving and solution implementation

This ensures customers feel heard before receiving practical solutions.

### Core Application Flow
The chatbot is a LangChain agent that uses tools to interact with a simulated environment. When a user selects a scenario, the `Simulator` creates an order in the database with the corresponding issue. The agent's prompt is dynamically updated with a `prompt_suffix` from `scenarios.yaml` providing scenario-specific guidance.

### Evaluation Framework
The system includes a comprehensive evaluation framework:

1. **Semantic Similarity Analysis**: Measures response accuracy using sentence embeddings
2. **LLM-as-Judge Evaluation**: Uses AI to evaluate empathy, clarity, and resolution quality
3. **Multi-dimensional Scoring**: Evaluates responses across:
   - **Accuracy**: Factual correctness and relevance
   - **Empathy**: Emotional connection and understanding
   - **Resolution**: Problem-solving effectiveness
   - **Clarity**: Communication quality and completeness

### Automated Testing
The `test_evaluation.py` script enables:
- Automated conversation testing across all scenarios
- Performance benchmarking and trend analysis
- Quality assurance for production deployment
- Regression testing for system improvements

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## Testing & Evaluation

### Manual Testing
- Select 1 (LATE), input "my order is 50 mins late" → Verifies tool (40 min), probes, suggests alternatives.
- Insist "asap" → Escalates with 'late_delivery' (credits if >15 min).
- Errors (e.g., API fail) → Graceful fallback.
- End: Yes/no confirmation, summary.

### Automated Evaluation Framework

Run comprehensive testing:
```bash
python test_evaluation.py
```

**Evaluation Metrics:**
- **Semantic Similarity**: Cosine similarity between expected and actual responses
- **LLM-as-Judge**: AI-powered evaluation of conversation quality
- **Multi-dimensional Scoring**: Performance across accuracy, empathy, resolution, and clarity
- **Scenario Performance**: Comparison across different issue types (late delivery, missing items, quality issues, etc.)

**Output**: Detailed performance reports with actionable insights for chatbot improvement.

**Example Results**:
- Late Delivery Scenario: 85% accuracy, 90% empathy score
- Missing Items: 78% accuracy, 92% empathy score  
- Quality Issues: 82% accuracy, 88% empathy score

### Evaluation Benefits
- **Quality Assurance**: Ensures consistent, high-quality customer interactions
- **Regression Testing**: Validates improvements don't break existing functionality
- **Performance Benchmarking**: Track progress over time
- **Production Readiness**: Data-driven confidence for deployment decisions

## Key Features & Innovations

### Two-Phase Conversational Protocol
- **Empathy-First Approach**: Forces customer acknowledgment before problem-solving
- **Constraint-Based Design**: Prevents rushed resolutions through structured interaction
- **User Experience Enhancement**: Ensures customers feel heard and valued

### Evaluation Framework Innovations
- **Dual Evaluation Methodology**: Combines semantic similarity with LLM-as-judge for comprehensive assessment
- **Multi-dimensional Metrics**: Goes beyond simple keyword matching to evaluate conversation quality
- **Automated Testing Pipeline**: Enables continuous quality assurance and regression testing
- **Production-Ready Evaluation**: Data-driven insights for deployment decisions

### Technical Achievements
- **YAML-Driven Configuration**: Scenario-based behavior management for non-technical modifications
- **Tool-Augmented Architecture**: Clean separation of business logic and conversation management
- **Adaptive Prompting**: Dynamic prompt adjustment based on selected scenarios
- **Error-Resilient Design**: Graceful handling of API failures and edge cases

For production, consider adding logging, more scenarios, real API integrations (e.g., Twilio for SMS), or enhanced metrics (resolution rates, customer satisfaction scores).

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

### Areas for Contribution:
- Additional evaluation scenarios and test cases
- Enhanced LLM-as-judge prompts for better evaluation accuracy
- Performance optimizations for large-scale testing
- Integration with real-world APIs and databases
- Extended metrics and analytics capabilities

## License

Built with LangChain & Groq for demonstration purposes. The evaluation framework is designed to be reusable for other conversational AI projects.
