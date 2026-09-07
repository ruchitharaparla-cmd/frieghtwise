"""Stage 7.2 Text Cleaner for normalizing markdown and text documents without semantic edits."""

import re


def clean_text(text: str) -> str:
    """Perform deterministic text cleaning on document contents.

    Operations:
    1. Normalize line endings (\r\n -> \n, \r -> \n)
    2. Strip trailing whitespace from each line while keeping markdown formatting
    3. Collapse 3 or more consecutive newlines into 2 (preserving section spacing)
    4. Strip leading and trailing document whitespace

    Preserves:
    - Headings (# Header)
    - Code blocks (```code```)
    - Markdown tables (| col | col |)
    - Bullet points (- item, * item)
    - Technical terminology and numerical constants
    """
    if not text:
        return ""

    # 1. Normalize line endings
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Trim trailing whitespace from each line
    lines = [line.rstrip() for line in normalized.split("\n")]
    cleaned_lines = "\n".join(lines)

    # 3. Collapse 3+ consecutive newlines to 2 newlines (\n\n)
    collapsed = re.sub(r"\n{3,}", "\n\n", cleaned_lines)

    # 4. Strip surrounding whitespace
    return collapsed.strip()
