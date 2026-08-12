"""
Tool Registry for UACB

Manages registration and execution of tools.
"""

from typing import Dict, Callable, Any, Optional, List
from pydantic import BaseModel, Field
import json


class ToolDefinition(BaseModel):
    """Definition of a tool"""
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    handler: Optional[Callable] = None
    timeout: int = 30
    requires_approval: bool = False


class ToolRegistry:
    """Registry for all available tools"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        
    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any] = None,
        output_schema: Dict[str, Any] = None,
        timeout: int = 30,
        requires_approval: bool = False
    ):
        """Decorator to register a tool handler"""
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema or {},
                output_schema=output_schema or {},
                handler=func,
                timeout=timeout,
                requires_approval=requires_approval
            )
            return func
        return decorator
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
                "timeout": tool.timeout,
                "requires_approval": tool.requires_approval
            }
            for tool in self._tools.values()
        ]
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names"""
        return list(self._tools.keys())
    
    async def execute(self, name: str, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        """Execute a tool with given arguments"""
        tool = self._tools.get(name)
        
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        
        if not tool.handler:
            raise ValueError(f"Tool {name} has no handler")
        
        # Execute the handler
        if context is None:
            context = {}
        
        result = await tool.handler(arguments, context)
        return result
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools
