"""
Universal AI Coding Bridge - Local Server (v2.0 Async)
High-performance async server for tool execution and session management.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import local modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from bridge.config import settings
from bridge.security import SecurityPolicy, validate_path_traversal
from bridge.tool_registry import ToolRegistry
from bridge.session import SessionManager
from bridge.executor import ExecutionEngine
from bridge.project import ProjectManager

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="UACB Local Bridge", version="2.0.0")

# Initialize Components
security_policy = SecurityPolicy()
tool_registry = ToolRegistry()
session_manager = SessionManager()
execution_engine = ExecutionEngine()
project_manager = ProjectManager()

# --- Models ---
class ToolCall(BaseModel):
    id: str
    tool: str
    arguments: Dict[str, Any]

class ProjectInspectRequest(BaseModel):
    project_name: str

class FileOperationRequest(BaseModel):
    project_name: str
    file_path: str
    content: Optional[str] = None
    patch: Optional[str] = None

class RunCommandRequest(BaseModel):
    project_name: str
    command: str
    timeout: int = 30

# --- Middleware & Security ---
@app.middleware("http")
async def security_middleware(request, call_next):
    # Basic CORS for localhost extension
    if request.url.port == 8765:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    return await call_next(request)

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "timestamp": datetime.now().isoformat()}

@app.get("/projects")
async def list_projects():
    try:
        projects = project_manager.list_sandbox_projects()
        return {"count": len(projects), "projects": projects}
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inspect_project")
async def inspect_project(req: ProjectInspectRequest):
    if not validate_path_traversal(req.project_name):
        raise HTTPException(status_code=403, detail="Invalid project name")
    
    try:
        result = await project_manager.inspect_project(req.project_name)
        return {"ok": True, "data": result}
    except Exception as e:
        logger.error(f"Inspect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/read_file")
async def read_file(req: FileOperationRequest):
    if not validate_path_traversal(req.project_name) or not validate_path_traversal(req.file_path):
        raise HTTPException(status_code=403, detail="Path traversal detected")
    
    try:
        content = await project_manager.read_file(req.project_name, req.file_path)
        return {"ok": True, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/write_file")
async def write_file(req: FileOperationRequest):
    if not validate_path_traversal(req.project_name) or not validate_path_traversal(req.file_path):
        raise HTTPException(status_code=403, detail="Path traversal detected")
    
    try:
        await project_manager.write_file(req.project_name, req.file_path, req.content)
        return {"ok": True, "message": "File written successfully"}
    except Exception as e:
        logger.error(f"Write failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_command")
async def run_command(req: RunCommandRequest):
    if not validate_path_traversal(req.project_name):
        raise HTTPException(status_code=403, detail="Invalid project name")
    
    # Security check for command
    if not security_policy.is_command_allowed(req.command):
        raise HTTPException(status_code=403, detail="Command blocked by security policy")

    try:
        result = await execution_engine.run(
            project_name=req.project_name,
            command=req.command,
            timeout=req.timeout
        )
        return {"ok": True, **result}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/create")
async def create_session(project_name: str):
    session_id = session_manager.create_session(project_name)
    return {"ok": True, "session_id": session_id}

@app.post("/tool/call")
async def handle_tool_call(call: ToolCall):
    """Direct tool call endpoint for internal or extension usage"""
    try:
        result = await tool_registry.execute(call.tool, call.arguments)
        return {"ok": True, "id": call.id, "result": result}
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {"ok": False, "id": call.id, "error": str(e)}

# --- Startup ---
def run_server():
    host = settings.BRIDGE_HOST
    port = settings.BRIDGE_PORT
    logger.info(f"Starting UACB Bridge v2.0 on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server()
