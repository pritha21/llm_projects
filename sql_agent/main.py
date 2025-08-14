# main.py

import os
import kagglehub
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

# --- 1. SETUP: Load Environment Variables and API Key ---
# (This part is correct and remains unchanged)
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")
print("✓ API Key loaded.")

# --- 2. SETUP: Download Dataset and Connect to Database ---
print("Downloading dataset from Kaggle Hub...")
download_path = kagglehub.dataset_download("alperenmyung/social-media-advertisement-performance")
print(f"✓ Dataset downloaded to: {download_path}")
db_filename = "ad_campaign_db.sqlite"
db_file_path = os.path.join(download_path, db_filename)
if not os.path.exists(db_file_path):
    raise FileNotFoundError(f"File not found at: {db_file_path}")
print(f"✓ Found database file at: {db_file_path}")
db = SQLDatabase.from_uri(f"sqlite:///{db_file_path}")
print("✓ Database connection established in READ-ONLY mode.")

# --- 3. SETUP: Initialize LLM ---
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0, api_key=groq_api_key)
print("✓ LLM Initialized (llama-3.3-70b-versatile).")

# (The get_schema_summary function remains unchanged)
def get_schema_summary(db: SQLDatabase, llm) -> str:
    """
    Analyzes the database schema and returns a human-readable summary.
    This function is kept separate to be called once per session.
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    template = """
    You are a data analyst expert. Your task is to analyze the provided SQL database schema and explain the relationships between the tables in a clear, concise, and easy-to-understand way.

    Here is the database schema:
    {schema}

    Based on this schema, please provide a summary that includes:
    1.  A brief description of what each major table likely contains.
    2.  A clear explanation of how the tables are connected via foreign keys. Use Markdown for formatting, especially lists.

    Your summary should give a user a good starting point for asking questions about the data.
    """
    prompt = PromptTemplate.from_template(template)
    schema_info = db.get_table_info()
    print("DEBUG: schema_info =\n", schema_info)

    # 2. Create the chain.
    chain = prompt | llm | StrOutputParser()

    # 3. Invoke the chain, passing the schema_info as a concrete value.
    summary = chain.invoke({"schema": schema_info})
    
    return summary.strip()

# --- START OF NEW HELPER FUNCTION ---
def get_distinct_values(db: SQLDatabase, table_name: str, column_name: str) -> str:
    """
    Queries the database to get all unique values from a specific column
    and returns them as a comma-separated string.
    """
    try:
        query = f"SELECT DISTINCT {column_name} FROM {table_name};"
        result = db.run(query)
        # The result from db.run is a string that looks like a list of tuples.
        # We need to clean it up.
        import ast
        try:
            # Safely evaluate the string to a Python object (list of tuples)
            values_list = ast.literal_eval(result)
            # Extract the first element from each tuple and join into a string
            distinct_values = ", ".join([val[0] for val in values_list if val[0]])
            return distinct_values
        except (ValueError, SyntaxError):
            return "Could not parse values."
    except Exception as e:
        print(f"Error fetching distinct values: {e}")
        return "Not available"
# --- END OF NEW HELPER FUNCTION ---


def main():
    """Main function to run the CLI application."""
    print("\n--- Social Media Ad Performance SQL Assistant ---")
    
    # We will skip the schema summary for now to simplify the prompt
    # schema_summary = get_schema_summary(db, llm)
    # print(schema_summary)

    # --- Pre-fetch the distinct event types for our "cheat sheet" ---
    print("\nFetching context from database...")
    schema_summary = get_schema_summary(db, llm)
    event_types = get_distinct_values(db, "ad_events", "event_type")
    print("--- Schema Analysis Complete ---")
    print(schema_summary)
    print("\n--- Context Fetch Complete ---")
    print(f"✓ Found event types: {event_types}")
    print("--------------------------------\n")

    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=SQLDatabaseToolkit(db=db, llm=llm),
        agent_type="tool-calling",
        verbose=True,
    )

    print("Agent is ready. Ask questions about the ad performance data.")
    print("Type 'exit' or 'quit' to end the session.")

    while True:
        try:
            user_question = input("\n> Ask your question: ")
            if user_question.lower() in ["exit", "quit"]:
                print("Exiting. Goodbye!")
                break

            # --- START OF NEW, IMPROVED PROMPT WITH "CHEAT SHEET" ---
            full_prompt = f"""
You are an expert SQL data analyst. Your job is to answer the user's question by querying the database.

First, to understand the database structure, here is the schema summary:
<schema_summary>
{schema_summary}
</schema_summary>

Next, here is important context about specific values in the columns. You MUST use these exact, case-sensitive values in your `WHERE` clauses:
- The `event_type` column in the `ad_events` table can contain these values: {event_types}.

Finally, follow these rules:
1. You have READ-ONLY access. You MUST NOT issue any data-modifying commands (DELETE, UPDATE, etc.).
2. After running a query, your final answer MUST be based *only* on the result you received.

User Question:
{user_question}
"""

            # --- END OF NEW, IMPROVED PROMPT ---

            response = agent_executor.invoke({"input": full_prompt})
            print("\n--- Agent's Answer ---")
            print(response["output"])
            print("----------------------")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please try rephrasing your question.")

if __name__ == "__main__":
    main()
