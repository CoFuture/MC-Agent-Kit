"""Code completer for MC-Agent-Kit."""

from dataclasses import dataclass, field
from enum import Enum


class CompletionKind(Enum):
    """Type of completion item."""
    API = "api"
    EVENT = "event"
    PARAMETER = "parameter"
    VARIABLE = "variable"
    KEYWORD = "keyword"
    SNIPPET = "snippet"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    PROPERTY = "property"


@dataclass
class Completion:
    """A single completion item."""
    label: str
    kind: CompletionKind
    detail: str | None = None
    documentation: str | None = None
    insert_text: str | None = None
    sort_text: str | None = None


@dataclass
class CompletionContext:
    """Context for code completion."""
    code: str
    cursor_line: int = 1
    cursor_column: int = 0
    prefix: str | None = None
    file_path: str | None = None


@dataclass
class CompletionResult:
    """Result of code completion."""
    completions: list[Completion] = field(default_factory=list)
    is_incomplete: bool = False

    @property
    def items(self) -> list[Completion]:
        """Alias for completions for backwards compatibility."""
        return self.completions


class CodeCompleter:
    """Code completion provider."""

    def __init__(self, knowledge_base=None):
        """Initialize the completer.

        Args:
            knowledge_base: Optional knowledge base for API/Event lookups.
        """
        self._knowledge_base = knowledge_base

    def complete(
        self,
        code: str,
        cursor_line: int = 1,
        cursor_column: int = 0,
        prefix: str | None = None,
    ) -> CompletionResult:
        """Get completion suggestions.

        Args:
            code: The source code.
            cursor_line: Current cursor line (1-indexed).
            cursor_column: Current cursor column (0-indexed).
            prefix: Optional prefix for filtering.

        Returns:
            CompletionResult with completion items.
        """
        completions = []

        # Simple keyword completions
        keywords = [
            "def", "class", "import", "from", "return", "if", "else", "elif",
            "for", "while", "try", "except", "finally", "with", "as", "pass",
            "True", "False", "None", "and", "or", "not", "in", "is",
        ]

        for kw in keywords:
            if prefix is None or kw.startswith(prefix):
                completions.append(Completion(
                    label=kw,
                    kind=CompletionKind.KEYWORD,
                    detail=f"Keyword: {kw}",
                ))

        return CompletionResult(completions=completions)

    def complete_member(self, code: str, cursor_line: int, cursor_column: int) -> CompletionResult:
        """Get member completions after a dot."""
        return CompletionResult()

    def complete_parameter(self, code: str, cursor_line: int, cursor_column: int) -> CompletionResult:
        """Get parameter completions in function calls."""
        return CompletionResult()
