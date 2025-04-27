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
    arxiv_id: arXivId
    """The arXiv ID of the paper."""
    references: set[paperId]
    """The paperIds of the paper's references."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Paper":
        """Create a Paper object from a dictionary."""
        references = data['references']
        if not isinstance(references, set):
            references = set(references)

        return cls(
            title=data['title'],
            abstract=data['abstract'],
            arxiv_id=data['arxiv_id'],
            references=references
        )
