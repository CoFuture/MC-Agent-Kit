# MC-Agent-Kit Project Principles

## Core Principles

### 1. Progressive Iterative Development
- Each iteration focuses on limited goals
- Read documentation before iteration, understand vision
- Summarize and record after iteration, continuously improve
- Small steps, frequent delivery

### 2. Test-Driven Development
- All Python functional code must have tests
- Ensure all tests pass before committing
- Test coverage as quality indicator
- Tests as documentation

### 3. Documentation First
- Write documentation before important decisions
- Synchronize documentation updates with code changes
- Keep documentation and code consistent
- Documentation is part of the project

### 4. Workspace Isolation
- Work only in `E:\develop\MC-Agent-Kit` directory
- `resources/` directory is read-only, do not modify
- `resources/` is not uploaded to git
- Sensitive information is not committed

---

## Technical Specifications

### Python Specifications
- Python Version: 3.13
- Package Manager: uv
- Code Style: Follow PEP 8
- Type Annotations: Recommended

### Project Structure Specifications
```
MC-Agent-Kit/
├── docs/           # Documentation (must be maintained)
├── src/            # Source code
│   ├── mc_agent_kit/
│   └── tests/      # Tests (must be written)
├── resources/      # Reference materials (read-only)
└── pyproject.toml  # Project configuration
```

### Git Commit Specifications
- Commit messages clearly describe changes
- Each commit corresponds to one feature
- Run tests before committing
- Push to remote repository

---

## Iteration Process

### Before Iteration
1. Read documents in `docs/`
2. Understand overall project vision
3. Check `NEXT_ITERATION.md`
4. Plan current iteration tasks

### During Iteration
1. Write functional code
2. Write test cases
3. Run tests to ensure passing
4. Update related documentation

### After Iteration
1. Update `ITERATIONS.md`
2. Update `NEXT_ITERATION.md`
3. Commit and Push to GitHub
4. Generate iteration report
5. Send report via Feishu

---

## Code Quality Standards

### Must Follow
- ✅ All functional code has tests
- ✅ All tests pass
- ✅ Code has type annotations
- ✅ Key logic has comments

### Recommended
- 📝 Functions have docstrings
- 📝 Modules have descriptions
- 📝 Complex logic has comments

### Prohibited
- ❌ Committing untested code
- ❌ Committing failing tests
- ❌ Hardcoding sensitive information
- ❌ Modifying resources directory

---

## Boundaries with ModSDK

### This Project Is
- Development assistance tools
- AI Agent capability extension
- Automated testing and debugging

### This Project Is Not
- ModSDK itself
- Code running inside the game
- Python 2.7 code

### Version Distinction
| Environment | Python | Execution Location |
|-------------|--------|-------------------|
| ModSDK | 2.7 | Game process |
| MC-Agent-Kit | 3.13 | Development machine |

---

## Communication & Feedback

### Iteration Report
- Generated after each iteration completion
- Content includes: completed work, issues encountered, next steps
- Sent to project lead via Feishu

### Issue Handling
- Record blocking issues promptly
- Explain in iteration report
- Seek help or adjust plans

---

## Security Principles

### Sensitive Information
- User configuration files are not committed
- Account passwords managed through environment variables
- API Keys are not hardcoded

### Code Security
- Do not execute untrusted code
- File operations require path validation
- External input requires validation

---

*Document Version: v0.1.0*
*Last Updated: 2026-03-22*