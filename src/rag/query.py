"""Stage 7.3 Retrieval Query Contract and Validation."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RetrievalQuery:
    """Validated query contract for RAG evidence retrieval."""

    query: str
    top_k: int = 5
    min_relevance: float = 0.0
    filters: Optional[Dict[str, Any]] = field(default=None)
    collection_name: str = "freightwise_knowledge_base"

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Validate query parameters strictly.

        Raises:
            ValueError: If query is empty/whitespace, top_k <= 0, or min_relevance is invalid.
        """
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("Retrieval query cannot be empty or whitespace-only.")

        if not isinstance(self.top_k, int) or self.top_k <= 0:
            raise ValueError("top_k must be a positive integer > 0.")

        if not isinstance(self.min_relevance, (int, float)) or self.min_relevance < 0.0 or self.min_relevance > 1.0:
            raise ValueError("min_relevance must be a numeric value between 0.0 and 1.0.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalQuery":
        return cls(
            query=data["query"],
            top_k=data.get("top_k", 5),
            min_relevance=data.get("min_relevance", 0.0),
            filters=data.get("filters"),
            collection_name=data.get("collection_name", "freightwise_knowledge_base"),
        )
