"""
Universal AI Coding Bridge Protocol

Defines the protocol for communication between AI and Local Bridge.
"""

import json
import hashlib
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ToolCall(BaseModel):
    """Represents a tool call from AI to Bridge"""
    id: str = Field(..., description="Unique call identifier")
    tool: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    
    def to_json(self) -> str:
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> "ToolCall":
        data = json.loads(json_str)
        return cls(**data)


class ToolResult(BaseModel):
    """Represents a tool result from Bridge to AI"""
    id: str = Field(..., description="Call identifier (matches ToolCall.id)")
    tool: str = Field(..., description="Tool name")
    ok: bool = Field(..., description="Whether the tool execution succeeded")
    result: Any = Field(default=None, description="Tool result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ToolResult":
        data = json.loads(json_str)
        return cls(**data)
    
    def to_markdown_block(self) -> str:
        """Convert to markdown code block format"""
        return f"```uacb-result\n{self.to_json()}\n```"


class ExecutionRecord(BaseModel):
    """Records execution details for logging and replay"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tool: str
    arguments: Dict[str, Any]
    iteration: int = 0
    result: Any = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration_ms: Optional[int] = None


class FailureHash(BaseModel):
    """Hash for detecting repeated failures"""
    traceback: str = ""
    stderr: str = ""
    exit_code: int = 0
    
    def compute_hash(self) -> str:
        content = f"{self.traceback}|{self.stderr}|{self.exit_code}"
        return hashlib.sha256(content.encode()).hexdigest()


class UACBProtocol:
    """Protocol utilities for UACB communication"""
    
    TOOL_CALL_MARKER = "uacb-tool"
    RESULT_MARKER = "uacb-result"
    
    @staticmethod
    def parse_tool_calls(text: str) -> List[ToolCall]:
        """Extract tool calls from AI response text"""
        calls = []
        
        # Find all uacb-tool blocks
        start_marker = f"```{UACBProtocol.TOOL_CALL_MARKER}"
        end_marker = "```"
        
        start_idx = 0
        while True:
            start_pos = text.find(start_marker, start_idx)
            if start_pos == -1:
                break
            
            # Find the end of the block
            content_start = start_pos + len(start_marker)
            end_pos = text.find(end_marker, content_start)
            
            if end_pos == -1:
                break
            
            # Extract JSON content
            json_str = text[content_start:end_pos].strip()
            
            try:
                call = ToolCall.from_json(json_str)
                calls.append(call)
            except json.JSONDecodeError as e:
                # Invalid JSON, skip this block
                pass
            
            start_idx = end_pos + len(end_marker)
        
        return calls
    
    @staticmethod
    def create_tool_call(id: str, tool: str, arguments: Dict[str, Any]) -> str:
        """Create a tool call markdown block"""
        call = ToolCall(id=id, tool=tool, arguments=arguments)
        return f"```{UACBProtocol.TOOL_CALL_MARKER}\n{call.to_json()}\n```"
    
    @staticmethod
    def create_result_block(result: ToolResult) -> str:
        """Create a result markdown block"""
        return result.to_markdown_block()
    
    @staticmethod
    def generate_call_id() -> str:
        """Generate a unique call ID"""
        import uuid
        return f"call-{uuid.uuid4().hex[:8]}"
