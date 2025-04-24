from dataclasses import dataclass

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
