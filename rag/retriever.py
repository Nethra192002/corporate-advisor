# rag/retriever.py
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq

client    = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL     = "llama-3.3-70b-versatile"
_embedder = SentenceTransformer("all-MiniLM-L6-v2")


def _embed(texts: list[str]) -> np.ndarray:
    return _embedder.encode(texts, convert_to_numpy=True)


async def query_index(
    question: str,
    index_data: list[dict],
    profile: dict,
    model: dict,
    simulation: dict,
) -> str:
    ticker   = profile["ticker"]
    contents = [c["content"] for c in index_data]

    # FAISS index from semantic embeddings
    embeddings = _embed(contents).astype(np.float32)
    dim        = embeddings.shape[1]
    index      = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Embed question and retrieve top 3 chunks
    q_embed        = _embed([question]).astype(np.float32)
    k              = min(3, len(contents))
    _, indices     = index.search(q_embed, k=k)
    top_chunks     = [index_data[i] for i in indices[0] if i < len(index_data)]

    context = "\n\n".join(
        f"[{c['topic'].upper()}]\n{c['content']}"
        for c in top_chunks
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a financial advisor answering questions about {ticker}. "
                        f"Use only the context provided. Be concise and specific. "
                        f"If the answer isn't in the context say so honestly. "
                        f"Never invent figures. "
                        f"Label all outputs as educational, not investment advice."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                }
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Chat unavailable: {e}"