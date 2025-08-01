# app.py

import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from datetime import date
import json
from langchain_groq import ChatGroq


# -------------- LLM INITIALIZATION ----------
if "GROQ_API_KEY" not in st.secrets:
    st.error("🚫 GROQ_API_KEY missing from Streamlit secrets.")
    st.stop()

llm = ChatGroq(
    model_name="llama3-8b-8192",
    temperature=0.3,
    api_key=st.secrets["GROQ_API_KEY"]
)

# -------------- URL SCRAPER ----------------
def fetch_article_from_url(url: str) -> str | None:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        main_content = soup.find('article') or soup.find('main')
        paragraphs = main_content.find_all('p') if main_content else soup.find_all('p')
        if not paragraphs:
            return None
        article_text = "\n".join(p.get_text() for p in paragraphs)
        return article_text.strip()
    except:
        return None

# -------------- LLM CHAIN LOGIC -------------
def summarize_article(article_text, llm):
    research_prompt = f"""
    You are an analytical assistant. Read the article below and extract the key ideas as concise bullet points.
    Be objective, avoid redundancy and don't miss out details.
    ARTICLE:
    {article_text.strip()}
    """
    bullet_points = llm.invoke(research_prompt).content.strip()

    summarizer_prompt = f"""
    You are a summarization expert. Using the bullet points below, write a concise, coherent summary in one paragraph.
    Maintain the original meaning and avoid introducing new information.
    BULLET POINTS:
    {bullet_points}
    """
    summary = llm.invoke(summarizer_prompt).content.strip()

    # Optional future step: extract image references
    return {
        "bullet_points": bullet_points,
        "summary": summary,
    }

# -------------- STREAMLIT UI ----------------
def main():
    st.title("🧠 Article Summarizer")

    url = st.text_input("Paste the article URL:")

    if st.button("Summarize Article"):
        if not url:
            st.warning("Please paste a URL.")
            return

        with st.spinner("Fetching article..."):
            article_text = fetch_article_from_url(url)
            if not article_text:
                st.error("Failed to extract article from URL.")
                return

        with st.spinner("Running LLM agent..."):
            result = summarize_article(article_text, llm)

        st.subheader("🔍 Summary")
        st.write(result["summary"])

        st.subheader("📌 Bullet Points")
        st.markdown(result["bullet_points"])

        st.success("✅ Done! Your summary is ready!")

if __name__ == "__main__":
    main()
