"""
Tool implementations for UACB

All tools that can be called by AI.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List
import json
import hashlib

from .config import Config
from .security import SecurityPolicy
from .project import ProjectManager


class Tools:
    """Implementation of all UACB tools"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config.load()
        self.security = SecurityPolicy(self.config)
        self.project_manager = ProjectManager(self.config)
    
    async def inspect_project(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a project"""
        project_name = args.get("project")
        
        if not project_name:
            return {"ok": False, "error": "Missing 'project' argument"}
        
        if not self.security.validate_project_name(project_name):
            return {"ok": False, "error": f"Invalid project name: {project_name}"}
        
        try:
            files = self.project_manager.list_files(project_name)
            return {
                "ok": True,
                "result": {
                    "project": project_name,
                    "files": files
                }
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def read_file(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        project_name = args.get("project")
        file_path = args.get("path")
        
        if not project_name or not file_path:
            return {"ok": False, "error": "Missing 'project' or 'path' argument"}
        
        try:
            content = self.project_manager.read_file(project_name, file_path)
            return {
                "ok": True,
                "result": {
                    "project": project_name,
                    "path": file_path,
                    "content": content
                }
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def write_file(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Write/create a file"""
        project_name = args.get("project")
        file_path = args.get("path")
        content = args.get("content", "")
        
        if not project_name or not file_path:
            return {"ok": False, "error": "Missing 'project' or 'path' argument"}
        
        try:
            self.project_manager.write_file(project_name, file_path, content)
            return {
                "ok": True,
                "result": {
                    "project": project_name,
                    "path": file_path,
                    "written": True
                }
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def apply_patch(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply unified diff patch to a file"""
        project_name = args.get("project")
        file_path = args.get("path")
        patch = args.get("patch")
        
        if not project_name or not file_path or not patch:
            return {"ok": False, "error": "Missing required arguments"}
        
        try:
            result = self.project_manager.apply_patch(project_name, file_path, patch)
            return {
                "ok": True,
                "result": result
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def search(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Search code with grep"""
        project_name = args.get("project")
        pattern = args.get("pattern")
        
        if not project_name or not pattern:
            return {"ok": False, "error": "Missing 'project' or 'pattern' argument"}
        
        try:
            results = self.project_manager.search(project_name, pattern)
            return {
                "ok": True,
                "result": {
                    "project": project_name,
                    "pattern": pattern,
                    "matches": results
                }
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def run(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run arbitrary command (restricted)"""
        project_name = args.get("project")
        command = args.get("command")
        
        if not project_name or not command:
            return {"ok": False, "error": "Missing 'project' or 'command' argument"}
        
        # Security check
        if not self.security.is_command_allowed(command):
            return {"ok": False, "error": f"Command not allowed: {command}"}
        
        try:
            result = self.project_manager.run_command(project_name, command)
            return {
                "ok": result["exit_code"] == 0,
                "result": result
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def run_main(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run python3 main.py"""
        project_name = args.get("project")
        
        if not project_name:
            return {"ok": False, "error": "Missing 'project' argument"}
        
        try:
            result = self.project_manager.run_command(project_name, "python3 main.py")
            return {
                "ok": result["exit_code"] == 0,
                "result": result
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def run_pytest(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run pytest"""
        project_name = args.get("project")
        
        if not project_name:
            return {"ok": False, "error": "Missing 'project' argument"}
        
        try:
            result = self.project_manager.run_command(project_name, "pytest -v")
            return {
                "ok": result["exit_code"] == 0,
                "result": result
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def git_status(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get git status"""
        project_name = args.get("project")
        
        if not project_name:
            return {"ok": False, "error": "Missing 'project' argument"}
        
        try:
            result = self.project_manager.run_command(project_name, "git status")
            return {
                "ok": True,
                "result": result
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def git_diff(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get git diff"""
        project_name = args.get("project")
        
        if not project_name:
            return {"ok": False, "error": "Missing 'project' argument"}
        
        try:
            result = self.project_manager.run_command(project_name, "git diff")
            return {
                "ok": True,
                "result": result
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
