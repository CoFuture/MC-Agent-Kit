"""Best practices checker for MC-Agent-Kit."""

from dataclasses import dataclass
from enum import Enum


class PracticeCategory(Enum):
    """Category of best practice."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    MODSDK_SPECIFIC = "modsdk_specific"
    CODING_STYLE = "coding_style"
    ERROR_HANDLING = "error_handling"


class PracticeSeverity(Enum):
    """Severity of practice violation."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class BestPractice:
    """A best practice definition."""
    id: str
    name: str
    category: PracticeCategory
    description: str
    severity: PracticeSeverity = PracticeSeverity.WARNING
    rationale: str | None = None
    examples: list[str] | None = None


@dataclass
class BestPracticeResult:
    """Result of checking a best practice."""
    practice: BestPractice
    passed: bool
    message: str
    line: int | None = None
    column: int | None = None


# Built-in best practices
BUILTIN_PRACTICES = [
    BestPractice(
        id="PERF001",
        name="Avoid heavy operations in Tick",
        category=PracticeCategory.PERFORMANCE,
        description="Avoid heavy computations in OnTick events",
        severity=PracticeSeverity.WARNING,
        rationale="Heavy operations in tick events can cause lag",
    ),
    BestPractice(
        id="PERF002",
        name="Cache frequently used values",
        category=PracticeCategory.PERFORMANCE,
        description="Cache values that are accessed frequently",
        severity=PracticeSeverity.INFO,
        rationale="Caching improves performance",
    ),
    BestPractice(
        id="SEC001",
        name="Validate user input",
        category=PracticeCategory.SECURITY,
        description="Always validate user input before processing",
        severity=PracticeSeverity.ERROR,
        rationale="Input validation prevents security vulnerabilities",
    ),
    BestPractice(
        id="ERR001",
        name="Use try-except for error handling",
        category=PracticeCategory.ERROR_HANDLING,
        description="Wrap potentially failing operations in try-except",
        severity=PracticeSeverity.WARNING,
        rationale="Proper error handling prevents crashes",
    ),
    BestPractice(
        id="STYLE001",
        name="Follow PEP 8 style",
        category=PracticeCategory.CODING_STYLE,
        description="Follow PEP 8 coding style guidelines",
        severity=PracticeSeverity.INFO,
        rationale="Consistent style improves readability",
    ),
    BestPractice(
        id="MAIN001",
        name="Use meaningful names",
        category=PracticeCategory.MAINTAINABILITY,
        description="Use descriptive names for variables and functions",
        severity=PracticeSeverity.INFO,
        rationale="Meaningful names improve code readability",
    ),
]


class BestPracticeChecker:
    """Checker for best practices."""

    def __init__(self, practices: list[BestPractice] | None = None):
        """Initialize the checker.

        Args:
            practices: Optional list of practices to check.
        """
        self._practices = practices or BUILTIN_PRACTICES

    def list_practices(self) -> list[BestPractice]:
        """List all registered practices.

        Returns:
            List of best practices.
        """
        return self._practices

    def check(self, code: str) -> list[BestPracticeResult]:
        """Check code against best practices.

        Args:
            code: Source code to check.

        Returns:
            List of check results.
        """
        results = []
        lines = code.split("\n")

        for practice in self._practices:
            passed = True
            message = f"Follows best practice: {practice.name}"
            line = None

            # Simple pattern-based checks
            if practice.id == "ERR001":
                # Check for try-except usage
                if "try:" not in code and ("open(" in code or "request" in code):
                    passed = False
                    message = "Potentially failing operation without error handling"
                    for i, ln in enumerate(lines, 1):
                        if "open(" in ln or "request" in ln:
                            line = i
                            break

            elif practice.id == "STYLE001":
                # Check for basic PEP 8 violations
                for i, ln in enumerate(lines, 1):
                    # Check for tabs
                    if "\t" in ln:
                        passed = False
                        message = "Use spaces instead of tabs"
                        line = i
                        break
                    # Check for trailing whitespace
                    if ln.rstrip() != ln and ln.strip():
                        passed = False
                        message = "Trailing whitespace"
                        line = i
                        break

            results.append(BestPracticeResult(
                practice=practice,
                passed=passed,
                message=message,
                line=line,
            ))

        return results

    def get_practice(self, practice_id: str) -> BestPractice | None:
        """Get a practice by ID.

        Args:
            practice_id: The practice ID.

        Returns:
            The practice if found, None otherwise.
        """
        for practice in self._practices:
            if practice.id == practice_id:
                return practice
        return None
