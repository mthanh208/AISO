# Universal AI Coding Bridge (UACB)

## Overview

Universal AI Coding Bridge is a system that connects any web-based AI (ChatGPT, Claude, Gemini, Qwen, etc.) to your local development environment through a browser extension and local bridge server.

## Architecture

```
USER
 ↓
AI WEB (ChatGPT, Claude, Gemini, etc.)
 ↓
BROWSER EXTENSION / BROWSER BRIDGE
 ↓
UNIVERSAL AI PROTOCOL (uacb-tool / uacb-result blocks)
 ↓
LOCAL BRIDGE SERVER (127.0.0.1:8765)
 ↓
TOOL REGISTRY
 ↓
PROJECT SANDBOX
 ↓
EXECUTION ENGINE
 ↓
RESULT → AI WEB → NEXT TOOL CALL
```

## Quick Start

### Installation

```bash
chmod +x install.sh
./install.sh
```

### Running the Bridge

```bash
./run.sh
```

### Browser Extension

1. Open Chrome/Chromium
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `browser-extension/` directory

## Project Structure

```
universal_ai_coding_bridge/
├── bridge/                 # Local Bridge Server (Python/FastAPI)
│   ├── __init__.py
│   ├── server.py          # FastAPI server
│   ├── config.py          # Configuration
│   ├── security.py        # Security policies
│   ├── protocol.py        # UACP Protocol definitions
│   ├── tool_registry.py   # Tool registration
│   ├── tools.py           # Tool implementations
│   ├── executor.py        # Command execution
│   ├── project.py         # Project management
│   ├── session.py         # Session management
│   ├── records.py         # Execution records
│   └── agent_loop.py      # Agent state machine
│
├── browser-extension/      # Browser Extension
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── protocol.js
│   ├── bridge-client.js
│   ├── site-adapters.js
│   ├── popup.html
│   └── popup.js
│
├── sandbox/                # Project sandbox (only accessible projects)
│   └── demo_project/      # Demo project for testing
│
├── sessions/               # Session storage
├── logs/                   # Execution logs
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── examples/               # Examples and documentation
├── install.sh             # Installation script
├── run.sh                 # Run script
├── requirements.txt       # Python dependencies
├── config.yaml            # Configuration file
└── README.md
```

## Security

- Bridge only binds to `127.0.0.1:8765` (not exposed to internet)
- Only projects in `sandbox/` are accessible
- Path traversal protection (`../`, `/etc`, etc. blocked)
- No credentials/tokens transmitted to AI
- Command allowlist/blocklist
- Timeout limits on all executions
- Output size limits

## Tools

| Tool | Description |
|------|-------------|
| `inspect_project` | List files in a project |
| `read_file` | Read file contents |
| `write_file` | Write/create a file |
| `apply_patch` | Apply unified diff patch |
| `search` | Search code with grep |
| `run` | Run arbitrary command (restricted) |
| `run_main` | Run `python3 main.py` |
| `run_pytest` | Run pytest |
| `git_status` | Get git status |
| `git_diff` | Get git diff |
| `checkpoint` | Create checkpoint |
| `rollback` | Rollback to checkpoint |

## Protocol

### Tool Call Block (AI → Bridge)

```json
```uacb-tool
{
  "id": "call-001",
  "tool": "inspect_project",
  "arguments": {
    "project": "demo_project"
  }
}
```
```

### Result Block (Bridge → AI)

```json
```uacb-result
{
  "id": "call-001",
  "tool": "inspect_project",
  "ok": true,
  "result": {...}
}
```
```

## Agent Loop States

- `READY` - Initial state
- `INSPECTING` - Inspecting project
- `PLANNING` - Planning changes
- `CHECKPOINTING` - Creating checkpoint
- `EDITING` - Modifying files
- `RUNNING` - Executing code
- `ANALYZING_FAILURE` - Analyzing errors
- `TESTING` - Running tests
- `FAILED` - Execution failed
- `ROLLING_BACK` - Rolling back
- `COMPLETED` - All tests pass
- `MAX_ITERATIONS` - Max iterations reached
- `REPEATED_FAILURE` - Same failure detected

## Testing

Run all tests:

```bash
cd universal_ai_coding_bridge
python -m pytest tests/ -v
```

E2E test:

```bash
./scripts/sandbox_e2e.sh
```

## Configuration

Edit `config.yaml`:

```yaml
bridge:
  host: 127.0.0.1
  port: 8765
  
sandbox:
  root: ./sandbox
  
security:
  max_iterations: 20
  timeout_seconds: 30
  output_limit: 10000
```


## License

MIT
