"""
Configuration management for UACB v2.0
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class BridgeConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765


class SandboxConfig(BaseModel):
    root: str = "./sandbox"


class SecurityConfig(BaseModel):
    max_iterations: int = 20
    timeout_seconds: int = 30
    output_limit: int = 10000
    allowed_commands: List[str] = Field(default_factory=lambda: ["python3", "python", "pytest", "git", "ls", "cat", "grep", "find"])
    blocked_commands: List[str] = Field(default_factory=lambda: ["rm -rf", "sudo", "chmod 777", "curl", "wget", "ssh", "nc"])
    blocked_paths: List[str] = Field(default_factory=lambda: ["/etc", "/home", "/root", "/var", "/usr", "/bin", "/sbin"])


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "./logs/bridge.log"


class SessionConfig(BaseModel):
    max_sessions: int = 10
    cleanup_after_hours: int = 24


class Settings(BaseModel):
    BRIDGE_HOST: str = "127.0.0.1"
    BRIDGE_PORT: int = 8765
    SANDBOX_ROOT: str = "./sandbox"
    MAX_ITERATIONS: int = 20
    TIMEOUT_SECONDS: int = 30
    OUTPUT_LIMIT: int = 10000
    
    class Config:
        arbitrary_types_allowed = True


# Global settings instance
settings = Settings()

# Legacy Config class for backward compatibility
class Config(BaseModel):
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    
    @classmethod
    def load(cls, config_path: str = None) -> "Config":
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        
        config_path = Path(config_path).resolve()
        
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            bridge=BridgeConfig(**data.get('bridge', {})),
            sandbox=SandboxConfig(**data.get('sandbox', {})),
            security=SecurityConfig(**data.get('security', {})),
            logging=LoggingConfig(**data.get('logging', {})),
            session=SessionConfig(**data.get('session', {}))
        )
    
    def get_sandbox_root(self) -> Path:
        """Get absolute path to sandbox root"""
        base_dir = Path(__file__).parent.parent
        return (base_dir / self.sandbox.root).resolve()
