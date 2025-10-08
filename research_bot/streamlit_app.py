import os
import uuid
from dotenv import load_dotenv
import streamlit as st

# LangChain / LangGraph
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
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


def build_agent():
    """Construct the LLM, tools, memory, and agent."""
    load_dotenv()

    llm = ChatGroq(
        model_name=os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct-0905"),
        temperature=0,
    )

    search = GoogleSerperAPIWrapper()
    arxiv = ArxivAPIWrapper(top_k_results=5, doc_content_chars_max=2000)

    @tool
    def combined_search(query: str) -> str:
        """Query both arXiv and the web for AI research. Returns two labeled sections."""
        arxiv_res = arxiv.run(query)
        web_res = search.run(query)
        return f"ARXIV_RESULTS:\n{arxiv_res}\n\nWEB_RESULTS:\n{web_res}"

    memory = MemorySaver()

    system_prompt = (
        "You are an AI Research Assistant focused strictly on AI topics (machine learning, deep "
        "learning, LLMs, AI safety, AI systems, optimization, datasets, benchmarks, and related "
        "academic or industry research). If a user query is outside AI research, politely refuse "
        "to answer and ask them to rephrase toward AI research.\n\n"
        "For every accepted query:\n"
        "- Use the `combined_search` tool exactly once to gather both arXiv and web results before answering.\n"
        "- Synthesize a concise, factual answer grounded only in the tool results.\n"
        "- Include inline citations like [1], [2] after the sentences they support.\n"
        "- End with a 'Sources' section listing each cited source with title and URL. Prefer arXiv links for papers.\n"
        "- If the tools return nothing relevant, say so and ask a clarifying question."
    )

    agent = create_react_agent(llm, [combined_search], checkpointer=memory)

    return agent, system_prompt


def init_session_state():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"streamlit_{uuid.uuid4()}"
    if "history" not in st.session_state:
        st.session_state.history = []  # list of {role, content}


def main():
    st.set_page_config(page_title="AI Research Bot (arXiv + Web)", page_icon="🧪", layout="wide")
    st.title("AI Research Bot (arXiv + Web)")
    st.caption("Answers only AI research questions. Cites arXiv + web sources.")

    init_session_state()
    agent, system_prompt = build_agent()

    # Sidebar controls
    with st.sidebar:
        st.subheader("Session")
        if st.button("New conversation"):
            st.session_state.thread_id = f"streamlit_{uuid.uuid4()}"
            st.session_state.history = []
            st.success("Started a new conversation.")
        st.markdown("---")
        st.markdown("Environment:")
        st.code(
            f"Model: {os.getenv('GROQ_MODEL', 'moonshotai/kimi-k2-instruct-0905')}\n"
            f"Serper key: {'set' if os.getenv('SERPER_API_KEY') else 'missing'}\n"
            f"Groq key: {'set' if os.getenv('GROQ_API_KEY') else 'missing'}",
            language="txt",
        )

    # Display history
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Ask an AI research question...")
    if prompt is not None:
        # Gate non-AI queries before invoking the agent
        if not is_ai_query(prompt):
            with st.chat_message("assistant"):
                st.write("I'm specialized in AI research topics only. Please rephrase your question to focus on AI (e.g., ML, LLMs, AI systems).")
            st.session_state.history.append({"role": "user", "content": prompt})
            st.session_state.history.append({"role": "assistant", "content": "I'm specialized in AI research topics only. Please rephrase your question to focus on AI (e.g., ML, LLMs, AI systems)."})
            st.stop()

        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching arXiv + web and composing answer..."):
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
                try:
                    result = agent.invoke({"messages": messages}, config=config)
                    bot_reply = result["messages"][-1].content
                except Exception as e:
                    bot_reply = f"Error: {e}"
                st.markdown(bot_reply)
                st.session_state.history.append({"role": "assistant", "content": bot_reply})


if __name__ == "__main__":
    main()
