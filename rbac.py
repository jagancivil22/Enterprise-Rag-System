from typing import List

def filter_by_roles(documents: List[dict], user_roles: List[str]) -> List[dict]:
    """
    Filter retrieved documents based on allowed_roles metadata.
    A document is accessible if any of the user's roles is in its allowed_roles list.
    """
    filtered = []
    for doc in documents:
        allowed = doc.get("metadata", {}).get("allowed_roles", [])
        if any(role in allowed for role in user_roles):
            filtered.append(doc)
    return filtered