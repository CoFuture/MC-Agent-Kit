"""Code smell detection for MC-Agent-Kit."""

from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum


class SmellType(Enum):
    """Type of code smell."""
    NAMING = "naming"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    STRUCTURE = "structure"
    MODSDK_SPECIFIC = "modsdk_specific"
    CODE_QUALITY = "code_quality"


class SmellSeverity(Enum):
    """Severity of code smell."""
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class SmellCategory(Enum):
    """Category of code smell."""
    STYLE = "style"
    DESIGN = "design"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


@dataclass
class CodeSmell:
    """A detected code smell."""
    type: SmellType
    severity: SmellSeverity
    message: str
    line: int | None = None
    column: int | None = None
    category: SmellCategory = SmellCategory.STYLE
    suggestion: str | None = None


@dataclass
class SmellDetectorConfig:
    """Configuration for smell detection."""
    max_line_length: int = 100
    max_function_length: int = 50
    max_parameters: int = 5
    max_nesting: int = 4
    detect_magic_numbers: bool = True
    detect_print_debug: bool = True


class SmellDetector:
    """Detector for code smells."""

    def __init__(self, config: SmellDetectorConfig | None = None):
        """Initialize the detector.

        Args:
            config: Optional configuration.
        """
        self._config = config or SmellDetectorConfig()

    def detect(self, code: str) -> list[CodeSmell]:
        """Detect code smells in the given code.

        Args:
            code: Source code to analyze.

        Returns:
            List of detected code smells.
        """
        smells = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > self._config.max_line_length:
                smells.append(CodeSmell(
                    type=SmellType.CODE_QUALITY,
                    severity=SmellSeverity.MINOR,
                    message=f"Line too long ({len(line)} > {self._config.max_line_length})",
                    line=i,
                    category=SmellCategory.STYLE,
                ))

            # Check for print debug
            if self._config.detect_print_debug and "print(" in line:
                smells.append(CodeSmell(
                    type=SmellType.CODE_QUALITY,
                    severity=SmellSeverity.INFO,
                    message="Print statement found (potential debug code)",
                    line=i,
                    category=SmellCategory.MAINTAINABILITY,
                ))

            # Check for bare except
            if re.search(r"except\s*:", line):
                smells.append(CodeSmell(
                    type=SmellType.CODE_QUALITY,
                    severity=SmellSeverity.MAJOR,
                    message="Bare except clause",
                    line=i,
                    category=SmellCategory.DESIGN,
                ))

        return smells
