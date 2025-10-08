import os
from dotenv import load_dotenv

# Import LangChain + LangGraph components
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver  # built-in conversation memory
from langchain_core.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper, ArxivAPIWrapper

def is_ai_query(text: str) -> bool:
    """Heuristic gate to allow only AI-related queries."""
    text_l = text.lower()
    keywords = [
        "ai", "artificial intelligence", "machine learning", "ml", "deep learning", "dl",
        "neural", "neural network", "transformer", "llm", "large language model", "gpt",
        "diffusion", "reinforcement learning", "rl", "supervised", "unsupervised",
        "self-supervised", "fine-tune", "fine tuning", "prompt", "rag", "retrieval",
        "embedding", "token", "inference", "optimizer", "backprop", "gradient",
        "adam", "sgd", "dataset", "benchmark", "hugging face", "langchain", "langgraph",
        "computer vision", "nlp", "speech", "multimodal", "neurips", "icml", "iclr",
        "anthropic", "openai", "mistral", "meta ai", "groq"
    ]
    return any(k in text_l for k in keywords)

def main():
    """
    Main function to run the chatbot.
    """
    # Load environment variables from .env file
    load_dotenv()
    print("Chatbot Initializing...")

    # 1. Initialize the LLM (Groq-hosted model)
    llm = ChatGroq(
        model_name="moonshotai/kimi-k2-instruct-0905",
        temperature=0,  # 0 → more deterministic/factual responses
        api_key=os.getenv("GROQ_API_KEY")
    )

    # 2. Initialize the search utilities
    search = GoogleSerperAPIWrapper()
    arxiv = ArxivAPIWrapper(top_k_results=5, doc_content_chars_max=2000)

    @tool
    def google_search(query: str) -> str:
        """Search the web for AI research context (news, blogs, official pages). Return titles and links."""
        return search.run(query)

    @tool
    def arxiv_search(query: str) -> str:
        """Search arXiv for AI-related papers. Returns titles, authors, summaries and arXiv links."""
        return arxiv.run(query)

    @tool
    def combined_search(query: str) -> str:
        """Query both arXiv and the web for AI research. Returns two labeled sections."""
        arxiv_res = arxiv.run(query)
        web_res = search.run(query)
        return f"ARXIV_RESULTS:\n{arxiv_res}\n\nWEB_RESULTS:\n{web_res}"

    tools = [combined_search]

    # 4. Initialize memory for conversation persistence
    memory = MemorySaver()

    # System instructions to enforce AI research scope and citation requirements
    SYSTEM_PROMPT = (
        "You are an AI Research Assistant focused strictly on AI topics (machine learning, deep "
        "learning, LLMs, AI safety, AI systems, optimization, datasets, benchmarks, and related "
        "academic or industry research). If a user query is outside AI research, politely refuse "
        "to answer and ask them to rephrase toward AI research.\n\n"
        "For every accepted query:\n"
        "- Use the `combined_search` tool exactly once to gather both arXiv and web results before answering.\n"
        "- Synthesize a concise, factual answer grounded only in the tool results.\n"
        "- Include inline citations like [1], [2] after the sentences they support.\n"
        "- End with a 'Sources' section listing each cited source with title and URL. Prefer arXiv "
        "links for papers.\n"
        "- If the tools return nothing relevant, say so and ask a clarifying question."
    )

    # 5. Build the ReAct agent using LangGraph
    agent = create_react_agent(llm, tools, checkpointer=memory)

    print("Chatbot is ready! Type 'exit' or 'quit' to end the session.")

    # Config for threading — ensures all messages stay in the same conversation
    config = {"configurable": {"thread_id": "chat_session"}}

    # 6. Start the conversation loop
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Strict gate: refuse non-AI queries before invoking the agent
        if not is_ai_query(user_input):
            print("Bot: I'm specialized in AI research topics only. Please rephrase your question to focus on AI (e.g., ML, LLMs, AI systems).")
            continue

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        result = agent.invoke({"messages": messages}, config=config)

        # Extract the assistant’s latest reply
        messages = result["messages"]
        bot_reply = messages[-1].content
        print("Bot:", bot_reply)

if __name__ == "__main__":
    main()
