import os
import json
import pandas as pd
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader

def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = "\n".join([page.extract_text() or "" for page in reader.pages])
    return text

def load_csv(file_path: str) -> str:
    df = pd.read_csv(file_path)
    return df.to_string(index=False)

def load_json(file_path: str) -> str:
    with open(file_path, "r") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

def load_txt(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

def load_excel(file_path: str) -> str:
    df = pd.read_excel(file_path, sheet_name=None)
    text = ""
    for sheet, data in df.items():
        text += f"Sheet: {sheet}\n{data.to_string(index=False)}\n\n"
    return text

def load_any_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".csv":
        return load_csv(file_path)
    elif ext == ".json":
        return load_json(file_path)
    elif ext in [".txt", ".md", ".log"]:
        return load_txt(file_path)
    elif ext in [".xlsx", ".xls"]:
        return load_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)