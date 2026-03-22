"""Code refactoring suggestions for MC-Agent-Kit."""

from dataclasses import dataclass
from enum import Enum

from mc_agent_kit.contrib.completion.smells import CodeSmell


class RefactorType(Enum):
    """Type of refactoring."""
    EXTRACT_FUNCTION = "extract_function"
    EXTRACT_VARIABLE = "extract_variable"
    EXTRACT_CLASS = "extract_class"
    INLINE = "inline"
    RENAME = "rename"
    REPLACE_MAGIC_NUMBER = "replace_magic_number"
    SIMPLIFY_CONDITION = "simplify_condition"
    REMOVE_UNUSED = "remove_unused"


@dataclass
class RefactorSuggestion:
    """A refactoring suggestion."""
    type: RefactorType
    message: str
    line: int | None = None
    original_code: str | None = None
    suggested_code: str | None = None
    auto_applicable: bool = False


class RefactorEngine:
    """Engine for generating refactoring suggestions."""

    def __init__(self):
        """Initialize the refactor engine."""
        pass

    def suggest(
        self,
        code: str,
        smells: list[CodeSmell] | None = None,
    ) -> list[RefactorSuggestion]:
        """Generate refactoring suggestions.

        Args:
            code: Source code to analyze.
            smells: Optional list of detected code smells.

        Returns:
            List of refactoring suggestions.
        """
        suggestions = []

        if not smells:
            return suggestions

        for smell in smells:
            if smell.type.value == "code_quality":
                if "bare except" in smell.message.lower():
                    suggestions.append(RefactorSuggestion(
                        type=RefactorType.SIMPLIFY_CONDITION,
                        message="Replace bare except with 'except Exception:'",
                        line=smell.line,
                        auto_applicable=True,
                    ))

                if "print statement" in smell.message.lower():
                    suggestions.append(RefactorSuggestion(
                        type=RefactorType.REMOVE_UNUSED,
                        message="Remove print debug statement",
                        line=smell.line,
                        auto_applicable=True,
                    ))

        return suggestions

    def apply(self, code: str, suggestion: RefactorSuggestion) -> str:
        """Apply a refactoring suggestion to code.

        Args:
            code: Source code.
            suggestion: Refactoring suggestion to apply.

        Returns:
            Refactored code.
        """
        if not suggestion.auto_applicable or not suggestion.line:
            return code

        lines = code.split("\n")
        line_idx = suggestion.line - 1

        if 0 <= line_idx < len(lines):
            line = lines[line_idx]

            # Apply simple replacements
            if suggestion.type == RefactorType.SIMPLIFY_CONDITION:
                if "except:" in line:
                    lines[line_idx] = line.replace("except:", "except Exception:")

            elif suggestion.type == RefactorType.REMOVE_UNUSED:
                if "print(" in line:
                    # Comment out the line
                    lines[line_idx] = "# " + line

        return "\n".join(lines)
