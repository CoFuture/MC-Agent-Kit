"""Documentation formatter for MC-Agent-Kit.

This module provides formatting for documentation output:
- Markdown formatting
- HTML formatting
- JSON formatting
- Multi-language support
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from pathlib import Path


class OutputFormat(Enum):
    """Output format for documentation."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    RST = "rst"  # reStructuredText


@dataclass
class FormatterConfig:
    """Configuration for documentation formatter."""
    format: OutputFormat = OutputFormat.MARKDOWN
    language: str = "en"
    include_toc: bool = True
    include_version: bool = True
    code_highlight: bool = True
    line_width: int = 80


class DocFormatter:
    """Documentation formatter.

    Features:
    - Multiple output formats
    - Multi-language support
    - Code highlighting
    - Custom templates
    """

    def __init__(self, config: FormatterConfig | None = None):
        """Initialize formatter.

        Args:
            config: Formatter configuration
        """
        self.config = config or FormatterConfig()

    def format(
        self,
        doc_data: dict[str, Any],
        format: OutputFormat | None = None,
    ) -> str:
        """Format documentation data.

        Args:
            doc_data: Documentation data dictionary
            format: Output format (uses config default if not provided)

        Returns:
            Formatted documentation string
        """
        output_format = format or self.config.format

        if output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(doc_data)
        elif output_format == OutputFormat.HTML:
            return self._format_html(doc_data)
        elif output_format == OutputFormat.JSON:
            return self._format_json(doc_data)
        elif output_format == OutputFormat.RST:
            return self._format_rst(doc_data)
        else:
            return self._format_markdown(doc_data)

    def _format_markdown(self, data: dict[str, Any]) -> str:
        """Format as Markdown."""
        lines = []

        # Header
        if self.config.include_version and "version" in data:
            lines.append(f"# API Documentation")
            lines.append("")
            lines.append(f"**Version**: {data['version']}")
            lines.append("")

        if "generated" in data:
            lines.append(f"**Generated**: {data['generated']}")
            lines.append("")

        # Table of contents
        if self.config.include_toc and "apis" in data:
            lines.append("## Table of Contents")
            lines.append("")
            for name in sorted(data["apis"].keys()):
                lines.append(f"- [{name}](#{name.lower().replace('.', '-')})")
            lines.append("")

        # APIs
        if "apis" in data:
            lines.append("---")
            lines.append("")
            lines.append("## APIs")
            lines.append("")

            for name, api in sorted(data["apis"].items()):
                lines.append(f"### `{name}`")
                lines.append("")

                if api.get("deprecated"):
                    lines.append("> **⚠️ Deprecated**")
                    lines.append("")

                if api.get("module"):
                    lines.append(f"**Module**: `{api['module']}`")
                    lines.append("")

                if api.get("description"):
                    lines.append(api["description"])
                    lines.append("")

                # Parameters
                params = api.get("parameters", [])
                if params:
                    lines.append("**Parameters**")
                    lines.append("")
                    lines.append("| Name | Type | Required | Description |")
                    lines.append("|------|------|----------|-------------|")
                    for p in params:
                        required = "✓" if p.get("required") else ""
                        lines.append(
                            f"| `{p.get('name', '')}` | `{p.get('type', '')}` | {required} | {p.get('description', '')} |"
                        )
                    lines.append("")

                # Returns
                returns = api.get("returns")
                if returns:
                    lines.append("**Returns**")
                    lines.append("")
                    lines.append(f"`{returns.get('type', '')}`: {returns.get('description', '')}")
                    lines.append("")

                # Raises
                raises = api.get("raises", [])
                if raises:
                    lines.append("**Raises**")
                    lines.append("")
                    for r in raises:
                        lines.append(f"- {r}")
                    lines.append("")

                # Examples
                examples = api.get("examples", [])
                if examples:
                    lines.append("**Examples**")
                    lines.append("")
                    for ex in examples:
                        lines.append("```python")
                        lines.append(ex)
                        lines.append("```")
                        lines.append("")

        # Examples section
        if "examples" in data:
            lines.append("---")
            lines.append("")
            lines.append("## Examples")
            lines.append("")

            for ex in data["examples"]:
                lines.append(f"### {ex.get('title', 'Example')}")
                lines.append("")

                if ex.get("description"):
                    lines.append(ex["description"])
                    lines.append("")

                if ex.get("code"):
                    lang = ex.get("language", "python")
                    lines.append(f"```{lang}")
                    lines.append(ex["code"])
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)

    def _format_html(self, data: dict[str, Any]) -> str:
        """Format as HTML."""
        lines = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "  <meta charset='UTF-8'>",
            "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "  <title>API Documentation</title>",
            "  <style>",
            "    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
            "    h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }",
            "    h2 { color: #2c5282; }",
            "    h3 { color: #4a5568; }",
            "    code { background: #f7fafc; padding: 2px 6px; border-radius: 4px; }",
            "    pre { background: #f7fafc; padding: 15px; border-radius: 8px; overflow-x: auto; }",
            "    table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
            "    th, td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }",
            "    th { background: #f7fafc; }",
            "    .deprecated { background: #fffaf0; border-left: 4px solid #ed8936; padding: 10px; }",
            "  </style>",
            "</head>",
            "<body>",
            "",
            f"  <h1>API Documentation</h1>",
            "",
        ]

        if self.config.include_version and "version" in data:
            lines.append(f"  <p><strong>Version:</strong> {data['version']}</p>")
            lines.append("")

        # APIs
        if "apis" in data:
            lines.append("  <h2>APIs</h2>")
            lines.append("")

            for name, api in sorted(data["apis"].items()):
                lines.append(f"  <h3 id='{name.lower()}'><code>{name}</code></h3>")
                lines.append("")

                if api.get("deprecated"):
                    lines.append("  <div class='deprecated'>⚠️ <strong>Deprecated</strong></div>")
                    lines.append("")

                if api.get("description"):
                    lines.append(f"  <p>{api['description']}</p>")
                    lines.append("")

                # Parameters table
                params = api.get("parameters", [])
                if params:
                    lines.append("  <h4>Parameters</h4>")
                    lines.append("  <table>")
                    lines.append("    <tr><th>Name</th><th>Type</th><th>Required</th><th>Description</th></tr>")
                    for p in params:
                        required = "✓" if p.get("required") else ""
                        lines.append(
                            f"    <tr><td><code>{p.get('name', '')}</code></td>"
                            f"<td><code>{p.get('type', '')}</code></td>"
                            f"<td>{required}</td>"
                            f"<td>{p.get('description', '')}</td></tr>"
                        )
                    lines.append("  </table>")
                    lines.append("")

                # Examples
                examples = api.get("examples", [])
                if examples:
                    lines.append("  <h4>Examples</h4>")
                    for ex in examples:
                        lines.append("  <pre><code class='python'>")
                        lines.append(f"{ex}")
                        lines.append("  </code></pre>")
                    lines.append("")

        lines.extend([
            "",
            "</body>",
            "</html>",
        ])

        return "\n".join(lines)

    def _format_json(self, data: dict[str, Any]) -> str:
        """Format as JSON."""
        import json
        return json.dumps(data, indent=2)

    def _format_rst(self, data: dict[str, Any]) -> str:
        """Format as reStructuredText."""
        lines = []

        lines.append("=" * 60)
        lines.append("API Documentation")
        lines.append("=" * 60)
        lines.append("")

        if self.config.include_version and "version" in data:
            lines.append(f":Version: {data['version']}")
            lines.append("")

        # APIs
        if "apis" in data:
            for name, api in sorted(data["apis"].items()):
                lines.append(name)
                lines.append("-" * len(name))
                lines.append("")

                if api.get("description"):
                    lines.append(api["description"])
                    lines.append("")

                # Parameters
                params = api.get("parameters", [])
                if params:
                    lines.append("**Parameters:**")
                    lines.append("")
                    for p in params:
                        required = " (required)" if p.get("required") else ""
                        lines.append(
                            f"- ``{p.get('name', '')}`` ({p.get('type', '')}){required}: {p.get('description', '')}"
                        )
                    lines.append("")

        return "\n".join(lines)

    def format_api(
        self,
        api_data: dict[str, Any],
        format: OutputFormat | None = None,
    ) -> str:
        """Format a single API.

        Args:
            api_data: API data dictionary
            format: Output format

        Returns:
            Formatted API documentation
        """
        return self.format({"apis": {api_data.get("name", "api"): api_data}}, format)

    def format_example(
        self,
        example_data: dict[str, Any],
        format: OutputFormat | None = None,
    ) -> str:
        """Format an example.

        Args:
            example_data: Example data dictionary
            format: Output format

        Returns:
            Formatted example
        """
        return self.format({"examples": [example_data]}, format)

    def save(
        self,
        content: str,
        path: str,
    ) -> bool:
        """Save formatted documentation to file.

        Args:
            content: Formatted content
            path: Output path

        Returns:
            True if saved successfully
        """
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False


def create_formatter(config: FormatterConfig | None = None) -> DocFormatter:
    """Create a documentation formatter.

    Args:
        config: Formatter configuration

    Returns:
        DocFormatter instance
    """
    return DocFormatter(config)