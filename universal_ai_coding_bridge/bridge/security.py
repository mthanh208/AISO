"""
Security policies for UACB v2.0

Implements path traversal protection, command allowlist/blocklist,
and credential filtering.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Set
from .config import Config


def validate_path_traversal(path: str) -> bool:
    """
    Quick validation to check if path contains traversal attempts.
    Returns True if path is safe, False if it contains '..' or starts with '/'
    """
    if not path:
        return False
    
    # Check for null bytes
    if '\x00' in path:
        return False
    
    # Check for path traversal
    if '..' in path:
        return False
    
    # Check for absolute paths (we only want relative paths within sandbox)
    if path.startswith('/') or path.startswith('\\'):
        return False
    
    return True


class SecurityPolicy:
    """Security policy enforcement for UACB"""
    
    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS = [
        r'(?i)password\s*[=:]\s*["\']?[^\s"\']+',
        r'(?i)secret\s*[=:]\s*["\']?[^\s"\']+',
        r'(?i)api[_-]?key\s*[=:]\s*["\']?[^\s"\']+',
        r'(?i)token\s*[=:]\s*["\']?[^\s"\']+',
        r'(?i)aws[_-]?secret',
        r'(?i)private[_-]?key',
        r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----',
        r'sk-[a-zA-Z0-9]{48}',  # OpenAI API key pattern
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub token pattern
    ]
    
    def __init__(self, config: Config = None):
        self.config = config or Config.load()
        self.allowed_commands = set(self.config.security.allowed_commands)
        self.blocked_commands = set(self.config.security.blocked_commands)
        self.blocked_paths = set(self.config.security.blocked_paths)
        self.sandbox_root = self.config.get_sandbox_root()
        
    def is_path_allowed(self, path: str, project_name: str = None) -> bool:
        """
        Check if a path is within allowed sandbox boundaries.
        
        Prevents:
        - Path traversal (../)
        - Access to system directories
        - Access outside sandbox
        """
        # Normalize the path
        if project_name:
            base_path = self.sandbox_root / project_name
        else:
            base_path = self.sandbox_root
        
        # Resolve to absolute path
        try:
            resolved = (base_path / path).resolve()
        except (ValueError, OSError):
            return False
        
        # Check if resolved path is within sandbox
        sandbox_resolved = self.sandbox_root.resolve()
        
        try:
            resolved.relative_to(sandbox_resolved)
        except ValueError:
            # Path is outside sandbox
            return False
        
        # Check against blocked paths
        path_str = str(resolved)
        for blocked in self.blocked_paths:
            if blocked.startswith('~'):
                blocked = os.path.expanduser(blocked)
            if path_str.startswith(blocked):
                return False
        
        return True
    
    def sanitize_path(self, path: str, project_name: str) -> str:
        """
        Sanitize a path to prevent traversal attacks.
        
        Returns sanitized path or raises ValueError if invalid.
        """
        # Remove any null bytes
        path = path.replace('\x00', '')
        
        # Check for obvious traversal attempts
        if '..' in path.split(os.sep):
            raise ValueError(f"Path traversal not allowed: {path}")
        
        if path.startswith('/'):
            raise ValueError(f"Absolute paths not allowed: {path}")
        
        # Construct full path
        full_path = self.sandbox_root / project_name / path
        
        # Verify it's within sandbox
        if not self.is_path_allowed(path, project_name):
            raise ValueError(f"Path outside sandbox: {path}")
        
        return str(full_path)
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is in the allowlist"""
        # Extract base command
        base_cmd = command.split()[0] if command else ""
        
        # Check blocklist first
        for blocked in self.blocked_commands:
            if blocked in command:
                return False
        
        # Check allowlist
        return base_cmd in self.allowed_commands
    
    def filter_sensitive_data(self, text: str) -> str:
        """Remove or mask sensitive data from text"""
        result = text
        
        for pattern in self.SENSITIVE_PATTERNS:
            result = re.sub(pattern, '[REDACTED]', result, flags=re.IGNORECASE)
        
        return result
    
    def validate_project_name(self, project_name: str) -> bool:
        """Validate project name is safe"""
        if not project_name:
            return False
        
        # Only allow alphanumeric, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', project_name):
            return False
        
        # No path separators
        if '/' in project_name or '\\' in project_name:
            return False
        
        # Not too long
        if len(project_name) > 100:
            return False
        
        return True
    
    def get_timeout(self) -> int:
        """Get execution timeout in seconds"""
        return self.config.security.timeout_seconds
    
    def get_output_limit(self) -> int:
        """Get output size limit in bytes"""
        return self.config.security.output_limit
    
    def get_max_iterations(self) -> int:
        """Get maximum iterations allowed"""
        return self.config.security.max_iterations
