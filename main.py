from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os

from app.auth import authenticate_user, create_access_token, get_current_user, User, LoginRequest, Token, hash_password, fake_users_db
from app.rag_engine import add_document, retrieve_context, generate_answer
from app.data_loaders import load_any_document, chunk_text
from app.config import get_settings
from app.memory import add_to_history, get_history

app = FastAPI(title="Enterprise RAG with RBAC")
security = HTTPBearer()
settings = get_settings()

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"

class QueryResponse(BaseModel):
    answer: str
    context_used: str

# ------------------- Auth Endpoints -------------------
@app.post("/auth/login", response_model=Token)
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register")
def register(username: str, password: str, roles: List[str]):
    """Register a new user (simplified, for demo)."""
    if username in fake_users_db:
        raise HTTPException(status_code=400, detail="User exists")
    fake_users_db[username] = {
        "username": username,
        "hashed_password": hash_password(password),
        "roles": roles
    }
    return {"msg": f"User {username} created with roles {roles}"}

# ------------------- Ingestion Endpoint -------------------
@app.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    allowed_roles: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a document and assign allowed roles (comma-separated)."""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only admin can ingest documents")
    
    roles_list = [role.strip() for role in allowed_roles.split(",")]
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        text = load_any_document(tmp_path)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        for idx, chunk in enumerate(chunks):
            metadata = {
                "source": file.filename,
                "allowed_roles": roles_list,
                "chunk_index": idx
            }
            add_document(chunk, metadata)
    finally:
        os.unlink(tmp_path)
    
    return {"message": f"Ingested {len(chunks)} chunks from {file.filename}", "roles": roles_list}

# ------------------- Query Endpoint -------------------
@app.post("/query", response_model=QueryResponse)
async def query_rag(
    req: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    context = retrieve_context(req.question, current_user.roles)
    if not context.strip():
        answer = "I cannot answer because no accessible documents contain relevant information."
    else:
        answer = generate_answer(req.question, context, current_user.roles)
    
    add_to_history(req.session_id, "user", req.question)
    add_to_history(req.session_id, "assistant", answer)
    
    return QueryResponse(answer=answer, context_used=context)

# ------------------- History Endpoint -------------------
@app.get("/history/{session_id}")
def get_chat_history(session_id: str, current_user: User = Depends(get_current_user)):
    return get_history(session_id)