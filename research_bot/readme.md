# AI Research Chatbot (arXiv + Web)

A specialized AI research assistant that:
- Searches both arXiv and the public web for each query
- Answers only AI research questions (e.g., ML, LLMs, AI systems)
- Provides inline citations and a Sources section

## Requirements
- Python 3.10+
- API keys in `.env`:
  - `GROQ_API_KEY` (for ChatGroq LLM)
  - `SERPER_API_KEY` (for Google Serper web search)

## Install
```bash
pip install -r requirements.txt
```

## Configure
Create a `.env` in the project root:
```
GROQ_API_KEY="<your_groq_key>"
SERPER_API_KEY="<your_serper_key>"
```

## Run
```bash
# CLI
python search_bot.py

# Streamlit UI
streamlit run streamlit_app.py
```

## Usage
- Ask AI research-focused questions, e.g.:
  - "Recent advances in retrieval-augmented generation for LLMs"
  - "Compare LoRA vs QLoRA for fine-tuning large models"
- Non-AI queries are politely refused.

## Notes
- Model: By default, the bot uses `moonshotai/kimi-k2-instruct-0905`. 
- The agent uses a combined tool to fetch both arXiv and web results before answering.
- Keep your API keys secret and do not commit `.env`.
