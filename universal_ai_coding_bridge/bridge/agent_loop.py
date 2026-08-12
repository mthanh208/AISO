"""
Agent Loop State Machine for UACB

Implements the repair loop state machine.
"""

import asyncio
import hashlib
from typing import Dict, Any, Optional, Callable
from enum import Enum

from .config import Config
from .session import Session, AgentState, SessionManager
from .protocol import ToolCall, ToolResult, UACBProtocol, FailureHash
from .tool_registry import ToolRegistry
from .tools import Tools
from .records import ExecutionRecorder


class AgentLoop:
    """Agent loop state machine"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config.load()
        self.session_manager = SessionManager(self.config)
        self.tools_impl = Tools(self.config)
        self.registry = ToolRegistry()
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools"""
        self.registry.register(
            "inspect_project",
            "List files in a project",
            timeout=10
        )(self.tools_impl.inspect_project)
        
        self.registry.register(
            "read_file",
            "Read file contents",
            timeout=10
        )(self.tools_impl.read_file)
        
        self.registry.register(
            "write_file",
            "Write/create a file",
            timeout=10
        )(self.tools_impl.write_file)
        
        self.registry.register(
            "apply_patch",
            "Apply unified diff patch",
            timeout=30
        )(self.tools_impl.apply_patch)
        
        self.registry.register(
            "search",
            "Search code with grep",
            timeout=30
        )(self.tools_impl.search)
        
        self.registry.register(
            "run",
            "Run arbitrary command (restricted)",
            timeout=60
        )(self.tools_impl.run)
        
        self.registry.register(
            "run_main",
            "Run python3 main.py",
            timeout=60
        )(self.tools_impl.run_main)
        
        self.registry.register(
            "run_pytest",
            "Run pytest",
            timeout=120
        )(self.tools_impl.run_pytest)
        
        self.registry.register(
            "git_status",
            "Get git status",
            timeout=10
        )(self.tools_impl.git_status)
        
        self.registry.register(
            "git_diff",
            "Get git diff",
            timeout=10
        )(self.tools_impl.git_diff)
    
    async def execute_tool_call(
        self,
        session: Session,
        tool_call: ToolCall
    ) -> ToolResult:
        """Execute a single tool call"""
        # Check if already processed
        if session.is_call_processed(tool_call.id):
            return ToolResult(
                id=tool_call.id,
                tool=tool_call.tool,
                ok=False,
                error="Call already processed"
            )
        
        # Mark as processing
        session.mark_call_processed(tool_call.id)
        
        # Get tool
        tool_def = self.registry.get_tool(tool_call.tool)
        
        if not tool_def:
            result = ToolResult(
                id=tool_call.id,
                tool=tool_call.tool,
                ok=False,
                error=f"Unknown tool: {tool_call.tool}"
            )
            return result
        
        # Execute tool
        import time
        start_time = time.time()
        
        try:
            result_data = await self.registry.execute(
                tool_call.tool,
                tool_call.arguments,
                context={"session": session}
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Record execution
            session.record_execution({
                "call_id": tool_call.id,
                "tool": tool_call.tool,
                "arguments": tool_call.arguments,
                "iteration": session.iteration,
                "result": result_data,
                "duration_ms": duration_ms
            })
            
            result = ToolResult(
                id=tool_call.id,
                tool=tool_call.tool,
                ok=result_data.get("ok", False),
                result=result_data.get("result"),
                error=result_data.get("error")
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            session.record_execution({
                "call_id": tool_call.id,
                "tool": tool_call.tool,
                "arguments": tool_call.arguments,
                "iteration": session.iteration,
                "error": str(e),
                "duration_ms": duration_ms
            })
            
            result = ToolResult(
                id=tool_call.id,
                tool=tool_call.tool,
                ok=False,
                error=str(e)
            )
        
        return result
    
    async def process_ai_response(
        self,
        session: Session,
        ai_response: str
    ) -> list:
        """Process AI response and execute tool calls"""
        # Parse tool calls
        tool_calls = UACBProtocol.parse_tool_calls(ai_response)
        
        results = []
        
        for call in tool_calls:
            result = await self.execute_tool_call(session, call)
            results.append(result)
        
        return results
    
    def compute_failure_hash(
        self,
        traceback: str,
        stderr: str,
        exit_code: int
    ) -> str:
        """Compute hash for failure detection"""
        failure = FailureHash(
            traceback=traceback,
            stderr=stderr,
            exit_code=exit_code
        )
        return failure.compute_hash()
    
    def check_repeated_failure(
        self,
        session: Session,
        failure_hash: str
    ) -> bool:
        """Check if this is a repeated failure"""
        return session.track_failure(failure_hash)
    
    async def run_iteration(self, session: Session, ai_response: str) -> Dict[str, Any]:
        """Run a single iteration of the agent loop"""
        session.set_state(AgentState.RUNNING)
        
        # Process AI response
        results = await self.process_ai_response(session, ai_response)
        
        # Check for failures
        has_failure = any(not r.ok for r in results)
        
        if has_failure:
            # Extract failure info
            failed_results = [r for r in results if not r.ok]
            
            # Compute failure hash from first failure
            if failed_results:
                failure = failed_results[0]
                failure_hash = self.compute_failure_hash(
                    failure.error or "",
                    str(failure.result) if failure.result else "",
                    -1
                )
                
                if self.check_repeated_failure(session, failure_hash):
                    if session.same_failure_count >= 3:
                        session.set_state(AgentState.REPEATED_FAILURE)
                        return {
                            "status": "REPEATED_FAILURE",
                            "same_failure_count": session.same_failure_count
                        }
            
            session.set_state(AgentState.ANALYZING_FAILURE)
        else:
            session.set_state(AgentState.READY)
        
        return {
            "status": "COMPLETED" if not has_failure else "FAILED",
            "results": [r.model_dump() for r in results]
        }
    
    def create_session(self, project: str) -> Session:
        """Create a new session for a project"""
        session = self.session_manager.create_session(project=project)
        session.set_state(AgentState.INSPECTING)
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session"""
        return self.session_manager.get_session(session_id)
    
    async def checkpoint(self, session: Session, name: str) -> str:
        """Create a checkpoint"""
        session.set_state(AgentState.CHECKPOINTING)
        
        checkpoint_name = name or f"checkpoint_{session.iteration}"
        
        session.add_checkpoint(checkpoint_name, {
            "iteration": session.iteration,
            "state": session.state.value
        })
        
        session.set_state(AgentState.READY)
        
        return checkpoint_name
    
    async def rollback(self, session: Session, checkpoint_name: str = None) -> bool:
        """Rollback to a checkpoint"""
        session.set_state(AgentState.ROLLING_BACK)
        
        checkpoint = session.get_latest_checkpoint()
        
        if not checkpoint:
            session.set_state(AgentState.FAILED)
            return False
        
        # In v1.2, rollback just resets state
        # Full file rollback requires file backup implementation
        session.iteration = checkpoint.get("iteration", 0)
        session.save_state()
        
        session.set_state(AgentState.READY)
        
        return True
