"""
Project Manager for UACB

Handles project operations within the sandbox.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import difflib

from .config import Config
from .security import SecurityPolicy


class ProjectManager:
    """Manages projects within the sandbox"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config.load()
        self.security = SecurityPolicy(self.config)
        self.sandbox_root = self.config.get_sandbox_root()
    
    def get_project_path(self, project_name: str) -> Path:
        """Get absolute path to a project"""
        if not self.security.validate_project_name(project_name):
            raise ValueError(f"Invalid project name: {project_name}")
        
        project_path = self.sandbox_root / project_name
        
        if not project_path.exists():
            raise ValueError(f"Project not found: {project_name}")
        
        # Verify it's within sandbox
        resolved = project_path.resolve()
        sandbox_resolved = self.sandbox_root.resolve()
        
        try:
            resolved.relative_to(sandbox_resolved)
        except ValueError:
            raise ValueError(f"Project path outside sandbox: {project_name}")
        
        return resolved
    
    def list_files(self, project_name: str) -> List[str]:
        """List all files in a project"""
        project_path = self.get_project_path(project_name)
        
        files = []
        for root, dirs, filenames in os.walk(project_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if not filename.startswith('.'):
                    full_path = Path(root) / filename
                    rel_path = full_path.relative_to(project_path)
                    files.append(str(rel_path))
        
        return sorted(files)
    
    def read_file(self, project_name: str, file_path: str) -> str:
        """Read file contents"""
        project_path = self.get_project_path(project_name)
        
        # Sanitize and validate path
        safe_path = self.security.sanitize_path(file_path, project_name)
        
        full_path = Path(safe_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not full_path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        # Read with size limit
        output_limit = self.security.get_output_limit()
        
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(output_limit)
        
        return content
    
    def write_file(self, project_name: str, file_path: str, content: str) -> None:
        """Write/create a file"""
        project_path = self.get_project_path(project_name)
        
        # Sanitize and validate path
        safe_path = self.security.sanitize_path(file_path, project_name)
        
        full_path = Path(safe_path)
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def apply_patch(self, project_name: str, file_path: str, patch: str) -> Dict[str, Any]:
        """Apply unified diff patch to a file"""
        project_path = self.get_project_path(project_name)
        
        # Sanitize and validate path
        safe_path = self.security.sanitize_path(file_path, project_name)
        
        full_path = Path(safe_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read original content
        with open(full_path, 'r', encoding='utf-8') as f:
            original = f.read()
        
        # Try to apply patch using patch command
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "file"
            patch_file = Path(tmpdir) / "patch.diff"
            
            with open(tmp_file, 'w') as f:
                f.write(original)
            
            with open(patch_file, 'w') as f:
                f.write(patch)
            
            try:
                result = subprocess.run(
                    ['patch', '-p0', str(tmp_file)],
                    input=patch.encode(),
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    with open(tmp_file, 'r') as f:
                        new_content = f.read()
                    
                    with open(full_path, 'w') as f:
                        f.write(new_content)
                    
                    return {"applied": True, "message": "Patch applied successfully"}
                else:
                    return {
                        "applied": False,
                        "message": "Failed to apply patch",
                        "stderr": result.stderr.decode()
                    }
            except subprocess.TimeoutExpired:
                return {"applied": False, "message": "Patch timed out"}
            except Exception as e:
                return {"applied": False, "message": str(e)}
    
    def search(self, project_name: str, pattern: str) -> List[Dict[str, Any]]:
        """Search code with grep"""
        project_path = self.get_project_path(project_name)
        
        matches = []
        
        try:
            result = subprocess.run(
                ['grep', '-rn', '--include=*.py', pattern, str(project_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        matches.append({
                            "file": parts[0],
                            "line": int(parts[1]),
                            "content": parts[2]
                        })
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        return matches
    
    def run_command(self, project_name: str, command: str) -> Dict[str, Any]:
        """Run a command in the project directory"""
        project_path = self.get_project_path(project_name)
        
        timeout = self.security.get_timeout()
        output_limit = self.security.get_output_limit()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            stdout = result.stdout[:output_limit]
            stderr = result.stderr[:output_limit]
            
            return {
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }
