**LangChain SQL Agent with Dynamic Context Injection**

This project demonstrates how to build a powerful, conversational SQL agent using LangChain, Groq, and a local SQLite database. The agent can answer natural language questions about a social media advertising dataset by dynamically generating and executing SQL queries.

The key technique highlighted here is Dynamic Context Injection. Before passing the user's question to the agent, the script first queries the database to fetch a schema summary and a "cheat sheet" of important categorical values (e.g., all possible event_type values). This context is injected into the agent's prompt, significantly improving its accuracy and ability to write correct SQL queries on the first try.

**✨ Key Features**

Natural Language to SQL: Ask complex questions about your data in plain English.
High-Speed Inference: Leverages the Groq API for incredibly fast LLM responses.
Dynamic Context Injection: Improves agent accuracy by providing a "cheat sheet" of schema information and valid column values directly in the prompt.
Automated Dataset Handling: Uses the kagglehub library to automatically download and access the required dataset.
Agentic Workflow: Built with langchain_community.agent_toolkits to create a robust agent that can use tools (like a SQL query tool) to find answers.
Read-Only Safeguards: The agent is configured for read-only database access, preventing accidental data modification.
**⚙️ How It Works**

The application follows a simple but powerful workflow:

Initialization: The script loads the Groq API key, downloads the Kaggle dataset, and establishes a connection to the SQLite database.
Context Generation:
An LLM call is made to get_schema_summary to generate a human-readable summary of the database tables and their relationships.
The get_distinct_values helper function queries the database to get a list of all unique values for critical columns (in this case, event_type).
User Interaction: The user is prompted to ask a question in the command line.
Prompt Engineering: A detailed prompt is constructed for the agent, containing:
The generated schema summary.
The "cheat sheet" of distinct values.
Clear instructions and rules.
The user's original question.
Agent Execution: The LangChain SQL Agent receives the enhanced prompt. It uses the LLM (llama-3.3-70b-versatile) to understand the request, generate the correct SQL query, and execute it against the database.
Response: The agent synthesizes the query result into a final, natural-language answer and prints it to the user.
**🚀 Getting Started**
Follow these instructions to set up and run the project locally.

Prerequisites
Python 3.8+
A Groq API Key

**1. Clone the Repository**

bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

**2. Set Up a Virtual Environment**

It's recommended to use a virtual environment to manage dependencies.

bash
For macOS / Linux-
python3 -m venv venv
source venv/bin/activate

For Windows-
python -m venv venv
.\venv\Scripts\activate

**3. Install Dependencies**

Create a requirements.txt file with the following content:

requirements.txt

txt
langchain-groq
langchain-community
langchain-core
kagglehub
python-dotenv
langchain # A core dependency for some toolkits
Now, install the packages:

bash
pip install -r requirements.txt

**4. Configure Environment Variables**

Create a file named .env in the root of the project directory. Add your Groq API key to this file.

.env

env
GROQ_API_KEY="gsk_YourGroqApiKeyHere"
Note: The script will also require your Kaggle API credentials to be set up for the kagglehub library to work. Follow the Kaggle API documentation to place your kaggle.json file in the correct location (~/.kaggle/kaggle.json).

**5. Run the Application**

Execute the main script from your terminal:

bash
python main.py
The script will first download the dataset (a one-time operation) and then present you with a prompt to start asking questions.
