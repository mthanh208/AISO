"""
Tests for UACB Bridge components
"""

import pytest
import sys
import os

# Add bridge to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bridge.config import Config
from bridge.protocol import UACBProtocol, ToolCall, ToolResult
from bridge.security import SecurityPolicy


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.bridge.host == "127.0.0.1"
        assert config.bridge.port == 8765
    
    def test_load_config(self):
        config = Config.load()
        assert config is not None


class TestProtocol:
    def test_tool_call_creation(self):
        call = ToolCall(id="test-1", tool="inspect_project", arguments={"project": "demo"})
        assert call.id == "test-1"
        assert call.tool == "inspect_project"
    
    def test_tool_result_creation(self):
        result = ToolResult(id="test-1", tool="inspect_project", ok=True, result={"files": []})
        assert result.ok == True
        assert result.result == {"files": []}
    
    def test_parse_tool_calls(self):
        text = '''
Here's a tool call:
```uacb-tool
{"id": "call-1", "tool": "inspect_project", "arguments": {"project": "demo"}}
```
Some more text
'''
        calls = UACBProtocol.parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0].id == "call-1"
        assert calls[0].tool == "inspect_project"
    
    def test_generate_call_id(self):
        call_id = UACBProtocol.generate_call_id()
        assert call_id.startswith("call-")
        assert len(call_id) > 10


class TestSecurity:
    def test_path_traversal_blocked(self):
        policy = SecurityPolicy()
        
        # These should be blocked - path with .. in it
        assert not policy.validate_project_name("../etc")
        assert not policy.validate_project_name("/root")
    
    def test_sanitize_path_blocks_traversal(self):
        policy = SecurityPolicy()
        
        # sanitize_path should raise ValueError for traversal attempts
        import pytest
        with pytest.raises(ValueError):
            policy.sanitize_path("../etc/passwd", "demo_project")
    
    def test_valid_path_allowed(self):
        policy = SecurityPolicy()
        
        # Valid paths within sandbox should be allowed
        assert policy.is_path_allowed("main.py", "demo_project")
    
    def test_command_allowlist(self):
        policy = SecurityPolicy()
        
        assert policy.is_command_allowed("python3 main.py")
        assert policy.is_command_allowed("pytest -v")
        assert not policy.is_command_allowed("rm -rf /")
        assert not policy.is_command_allowed("sudo bash")
    
    def test_project_name_validation(self):
        policy = SecurityPolicy()
        
        assert policy.validate_project_name("demo_project")
        assert policy.validate_project_name("my-project")
        assert not policy.validate_project_name("../etc")
        assert not policy.validate_project_name("/root")


class TestToolRegistry:
    def test_registry_creation(self):
        from bridge.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        assert registry.list_tools() == []
    
    def test_tool_registration(self):
        from bridge.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        @registry.register("test_tool", "A test tool")
        async def handler(args, context):
            return {"ok": True}
        
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
