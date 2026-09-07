"""Stage 7.2 Document Loader for safe loading of approved Markdown and text files."""

import hashlib
import os
from pathlib import Path
from typing import List, Optional, Sequence

from src.rag.contracts import DocumentRecord

ALLOWED_EXTENSIONS = {".md", ".txt"}
FORBIDDEN_EXTENSIONS = {
    ".joblib", ".csv", ".json", ".py", ".env", ".sh", ".exe", ".bin",
    ".db", ".sqlite", ".zip", ".tar", ".gz", ".7z", ".pdf", ".docx",
    ".xlsx", ".png", ".jpg", ".jpeg", ".pkl"
}
FORBIDDEN_DIRECTORIES = {
    ".git", "venv", ".venv", "__pycache__", "node_modules", "catboost_info", ".pytest_cache"
}


def calculate_sha256(content: str) -> str:
    """Calculate deterministic SHA-256 hex digest for string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_document_id(checksum: str, path_str: str) -> str:
    """Generate a deterministic document ID from content checksum and path."""
    clean_path = path_str.replace("\\", "/").lower()
    path_hash = hashlib.sha256(clean_path.encode("utf-8")).hexdigest()[:8]
    content_hash = checksum[:12]
    return f"doc_{path_hash}_{content_hash}"


def load_document(
    file_path: str,
    source: str = "INTERNAL",
    stage: str = "Stage 7.2",
    document_type: Optional[str] = None
) -> DocumentRecord:
    """Load an approved text or markdown file into a DocumentRecord.

    Raises:
        ValueError: If file extension is unsupported or file is invalid.
        FileNotFoundError: If file path does not exist.
    """
    path_obj = Path(file_path).resolve()
    if not path_obj.exists():
        raise FileNotFoundError(f"Document not found at path: {file_path}")

    ext = path_obj.suffix.lower()
    if ext in FORBIDDEN_EXTENSIONS or ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported or forbidden file extension '{ext}' for file '{file_path}'. "
            f"Allowed extensions are: {sorted(list(ALLOWED_EXTENSIONS))}"
        )

    # Check for forbidden parent directory patterns
    for parent in path_obj.parents:
        if parent.name in FORBIDDEN_DIRECTORIES:
            raise ValueError(
                f"File '{file_path}' is inside restricted directory '{parent.name}' and cannot be loaded."
            )

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    checksum = calculate_sha256(content)
    doc_id = generate_document_id(checksum, str(path_obj))
    doc_type = document_type or ("MARKDOWN" if ext == ".md" else "TEXT")

    return DocumentRecord(
        document_id=doc_id,
        path=str(path_obj),
        filename=path_obj.name,
        document_type=doc_type,
        source=source,
        stage=stage,
        content=content,
        checksum=checksum,
        metadata={
            "file_size": os.path.getsize(path_obj),
            "extension": ext,
        }
    )


def discover_and_load_documents(
    directory: str,
    allowed_extensions: Sequence[str] = (".md", ".txt"),
    source: str = "INTERNAL",
    stage: str = "Stage 7.2"
) -> List[DocumentRecord]:
    """Recursively discover and load all allowed documents in a directory."""
    documents: List[DocumentRecord] = []
    dir_path = Path(directory).resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        return documents

    allowed_set = {ext.lower() for ext in allowed_extensions if ext.lower() in ALLOWED_EXTENSIONS}

    for root, dirs, files in os.walk(dir_path):
        # Prune forbidden directories
        dirs[:] = [d for d in dirs if d not in FORBIDDEN_DIRECTORIES and not d.startswith(".")]

        for file in sorted(files):
            file_ext = Path(file).suffix.lower()
            if file_ext in allowed_set and file_ext not in FORBIDDEN_EXTENSIONS:
                full_path = os.path.join(root, file)
                try:
                    doc = load_document(full_path, source=source, stage=stage)
                    documents.append(doc)
                except ValueError:
                    continue

    return documents
