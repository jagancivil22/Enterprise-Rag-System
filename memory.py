from collections import defaultdict
from typing import List, Dict

# In‑memory conversation store (session_id -> list of {"role","content"})
conversation_store = defaultdict(list)

def add_to_history(session_id: str, role: str, content: str):
    conversation_store[session_id].append({"role": role, "content": content})
    # Keep only last 10 exchanges to avoid overflow
    if len(conversation_store[session_id]) > 20:
        conversation_store[session_id] = conversation_store[session_id][-20:]

def get_history(session_id: str) -> List[Dict]:
    return conversation_store.get(session_id, [])