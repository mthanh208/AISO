"""
Execution Engine for UACB v2.0
Handles command execution with security, timeouts, and output limits.
"""
import asyncio
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .config import settings
from .security import SecurityPolicy


class ExecutionEngine:
    """Async execution engine for running commands in sandbox"""
    
    def __init__(self):
        self.security = SecurityPolicy()
        self.sandbox_root = Path(settings.SANDBOX_ROOT).resolve()
    
    async def run(
        self,
        project_name: str,
        command: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Run a command in the project sandbox.
        
        Returns:
            dict with ok, exit_code, stdout, stderr
        """
        # Validate project name
        if not self.security.validate_project_name(project_name):
            return {"ok": False, "error": f"Invalid project name: {project_name}"}
        
        # Check command allowlist
        if not self.security.is_command_allowed(command):
            return {"ok": False, "error": f"Command not allowed: {command}"}
        
        # Build working directory
        work_dir = self.sandbox_root / project_name
        if not work_dir.exists():
            return {"ok": False, "error": f"Project not found: {project_name}"}
        
        try:
            # Run command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
                env=self._get_safe_environment()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return {
                    "ok": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds"
                }
            
            # Decode and limit output
            stdout_str = stdout.decode('utf-8', errors='replace')[:settings.OUTPUT_LIMIT]
            stderr_str = stderr.decode('utf-8', errors='replace')[:settings.OUTPUT_LIMIT]
            
            return {
                "ok": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str
            }
            
        except Exception as e:
            return {
                "ok": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def _get_safe_environment(self) -> Dict[str, str]:
        """
        Create a safe environment without sensitive variables.
        """
        # Start with minimal environment
        safe_env = {
            'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin'),
            'PYTHONUNBUFFERED': '1',
            'PYTHONDONTWRITEBYTECODE': '1'
        }
        
        # Copy only safe environment variables
        safe_prefixes = ['PYTHON', 'PIP']
        for key, value in os.environ.items():
            # Skip sensitive variables
            if any(sensitive in key.upper() for sensitive in [
                'SECRET', 'KEY', 'TOKEN', 'PASSWORD', 'PRIVATE', 
                'AWS_', 'GITHUB_', 'GITLAB_', 'SSH'
            ]):
                continue
            
            # Only include variables with safe prefixes or common ones
            if key in ['HOME', 'USER', 'LANG', 'LC_ALL'] or \
               any(key.startswith(prefix) for prefix in safe_prefixes):
                safe_env[key] = value
        
        return safe_env
