"""Query using Groq for fast chat + Ollama for reliable embeddings."""

from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from app.rag.indexer import CHROMA_DIR

embeddings = OllamaEmbeddings(model="all-minilm")

PROMPT_TEMPLATE = """You are RepoX, an AI code analyst. Answer based on the repository content provided.

Rules:
- Always use bullet points for lists
- Use **bold** for key terms
- Keep answers clear and structured
- Include file paths when referencing code
- If the answer isn't in the context, say so honestly

Context from repository:
{context}

Question: {question}

Answer (use bullet points and structure):"""


async def query_repository_stream(owner: str, repo: str, question: str):
    collection_name = f"{owner}_{repo}"

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    docs = retriever.invoke(question)

    context_parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"File: {source}\n{doc.page_content}")
    context = "\n\n---\n\n".join(context_parts)

    prompt_text = PROMPT_TEMPLATE.format(context=context, question=question)

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

    # Try streaming, fallback to invoke
    try:
        async for chunk in llm.astream(prompt_text):
            if chunk.content:
                yield chunk.content
    except Exception:
        result = llm.invoke(prompt_text)
        yield result.content