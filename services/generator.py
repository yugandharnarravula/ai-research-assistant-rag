from typing import Dict, List
import requests
import os
from config.settings import settings

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def build_context(docs: List[Dict]) -> str:
    blocks = []

    for i, d in enumerate(docs, start=1):
        text = d["text"].strip()

        # 🔥 skip very small or noisy chunks
        if len(text) < 50:
            continue

        # 🔥 truncate long chunks (important)
        text = text[:800]

        blocks.append(f"[{i}] Source: {d['source']} | Page: {d['page']}\n{text}")

    return "\n\n".join(blocks)


def call_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(url, headers=headers, json=data)

    # 🔥 DEBUG (important)
    print("Status:", response.status_code)
    print("Response:", response.text)

    result = response.json()

    if "choices" in result:
        return result["choices"][0]["message"]["content"]

    elif "error" in result:
        return f"LLM Error: {result['error']}"

    else:
        return "Unexpected response from Groq"


def generate_answer(query: str, docs: List[Dict], history: str = "") -> Dict:
    # 🔥 CASE 1: No docs → fallback
    if not docs:
        answer = call_groq(query)
        return {
            "answer": answer,
            "sources": [],
            "context": "",
        }

    # 🔥 CASE 2: Low relevance → fallback
    max_score = max(d.get("score", 0) for d in docs)

    if max_score < 0.4:
        answer = call_groq(query)
        return {
            "answer": answer,
            "sources": [],
            "context": "",
        }

    # 🔥 CASE 3: Try RAG
    context = build_context(docs[:5])

    prompt = f"""
You are an expert assistant.

Answer ONLY if the context directly contains the answer.

If the answer is NOT clearly present, reply ONLY with:
NOT_FOUND

Context:
{context}

Question:
{query}

Answer:
"""

    answer = call_groq(prompt).strip()

    # 🔥 CRITICAL FIX (DO NOT CHANGE)
    if answer == "NOT_FOUND":
        answer = call_groq(query)
        return {
            "answer": answer,
            "sources": [],
            "context": "",
        }

    # ✅ VALID RAG ANSWER
    sources = list(set([f"{d['source']} (page {d['page']})" for d in docs]))

    return {
        "answer": answer,
        "sources": sources,
        "context": context,
    }
