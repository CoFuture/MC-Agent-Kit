# Frequently Asked Questions (FAQ)

## Installation

### Q: What Python version do I need?

**A:** MC-Agent-Kit requires Python 3.13 or higher.

### Q: How do I upgrade to the latest version?

**A:** Run:
```bash
pip install --upgrade mc-agent-kit
```

### Q: I get import errors. What should I do?

**A:** Try reinstalling:
```bash
pip uninstall mc-agent-kit
pip install mc-agent-kit
```

## CLI Usage

### Q: How do I list available commands?

**A:** Run:
```bash
mc-agent --help
```

### Q: The CLI says "command not found". What's wrong?

**A:** Make sure the package is installed and your PATH includes the Python scripts directory.

### Q: How do I get JSON output?

**A:** Add `--output json` to any command:
```bash
mc-agent api search GetConfig --output json
```

## Knowledge Base

### Q: How do I build the knowledge base?

**A:** Run:
```bash
mc-agent kb build --docs-path /path/to/docs
```

### Q: Search returns no results. Why?

**A:** Check that:
1. The knowledge base index exists
2. The search query is correct
3. Filters are not too restrictive

### Q: How do I update the knowledge base?

**A:** Rebuild the index:
```bash
mc-agent kb build --rebuild
```

## Code Generation

### Q: What templates are available?

**A:** Run:
```bash
mc-agent gen list
```

### Q: How do I use custom templates?

**A:** Place your Jinja2 templates in a directory and specify:
```bash
mc-agent gen template my_template --templates-path ./my_templates
```

### Q: Generated code has issues. What should I do?

**A:** Use the code quality checker:
```bash
mc-agent check check --code "your code"
```

## Debugging

### Q: How do I diagnose an error?

**A:** Use the debug command:
```bash
mc-agent debug diagnose --log "your error log"
```

### Q: What error patterns are supported?

**A:** Run:
```bash
mc-agent debug patterns
```

### Q: Can I auto-fix errors?

**A:** Yes, use:
```bash
mc-agent autofix fix --code "your code" --error "error message"
```

## Performance

### Q: Search is slow. How can I speed it up?

**A:** Try:
1. Enable caching
2. Use more specific filters
3. Increase cache size in configuration

### Q: Memory usage is high. What can I do?

**A:** Reduce cache size and batch size in configuration:
```yaml
performance:
  cache_size: 500
  batch_size: 50
```

## OpenClaw Integration

### Q: How do I use MC-Agent-Kit with OpenClaw?

**A:** Install MC-Agent-Kit and the skills will be automatically available to OpenClaw agents.

### Q: Where are the skill definitions?

**A:** Skills are in the `skills/` directory of the package.

## Development

### Q: How do I contribute?

**A:** See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

### Q: How do I run tests?

**A:** Clone the repository and run:
```bash
uv sync
uv run pytest
```

### Q: How do I report a bug?

**A:** Open an issue on GitHub: https://github.com/your-username/mc-agent-kit/issues