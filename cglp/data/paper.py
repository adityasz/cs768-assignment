from dataclasses import dataclass
from typing import Any


paperId = str
"""The unique identifier for a paper assigned by Semantic Scholar."""
arXivId = str
"""The unique identifier for a paper assigned by arXiv."""


@dataclass
class Paper:
    title: str
    """The title of the paper."""
    abstract: str
    """The abstract of the paper."""
    references: set[arXivId]
    """The arXivId of the paper's references."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Paper":
        """Create a Paper object from a dictionary."""
        references = data["references"]
        if not isinstance(references, set):
            references = set(references)

        return cls(
            title=data["title"],
            abstract=data["abstract"],
            references=references
        )


@dataclass
class IndexedPaper:
    title: str
    """The title of the paper."""
    abstract: str
    """The abstract of the paper."""
    references: set[int]
    """The IDs of the paper's references."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexedPaper":
        """Create a Paper object from a dictionary."""
        references = data["references"]
        if not isinstance(references, set):
            references = set(references)

        return cls(
            title=data["title"],
            abstract=data["abstract"],
            references=references
        )
