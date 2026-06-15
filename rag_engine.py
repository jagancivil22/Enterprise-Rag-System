import chromadb
from chromadb.utils import embedding_functions
from app.config import get_settings
from app.embeddings import get_embedding
from app.rbac import filter_by_roles
from typing import List, Dict
import uuid

settings = get_settings()

# Chroma client
client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
collection = client.get_or_create_collection(
    name="enterprise_docs",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
)

def add_document(text: str, metadata: Dict, doc_id: str = None):
    if doc_id is None:
        doc_id = str(uuid.uuid4())
    embedding = get_embedding(text)
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata]
    )
    return doc_id

def retrieve_context(question: str, user_roles: List[str], top_k: int = 5) -> str:
    query_embedding = get_embedding(question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    # results format: {'ids': [...], 'documents': [...], 'metadatas': [...], 'distances': [...]}
    docs = []
    if results and results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            docs.append({
                "text": doc,
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            })
    filtered = filter_by_roles(docs, user_roles)
    context = "\n\n---\n\n".join([d["text"] for d in filtered])
    return context

def generate_answer(question: str, context: str, user_roles: List[str]) -> str:
    # Simple local LLM or call OpenAI
    if settings.use_local_llm:
        from transformers import pipeline
        # Cache the pipeline (for performance)
        if not hasattr(generate_answer, "llm_pipeline"):
            generate_answer.llm_pipeline = pipeline("text2text-generation", model=settings.llm_model_name)
        prompt = f"""You are a helpful enterprise assistant. Use the context below to answer the question.
If the context does not contain the answer, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""
        result = generate_answer.llm_pipeline(prompt, max_length=200, do_sample=False)
        return result[0]['generated_text'].strip()
    else:
        import openai
        openai.api_key = settings.openai_api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a secure RAG assistant that only answers based on provided context."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ]
        )
        return response.choices[0].message.content