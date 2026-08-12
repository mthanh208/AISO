"""
Session Manager for UACB

Manages agent sessions, state persistence, and iteration tracking.
"""

import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from .config import Config


class AgentState(str, Enum):
    """Agent loop states"""
    READY = "READY"
    INSPECTING = "INSPECTING"
    PLANNING = "PLANNING"
    CHECKPOINTING = "CHECKPOINTING"
    EDITING = "EDITING"
    RUNNING = "RUNNING"
    ANALYZING_FAILURE = "ANALYZING_FAILURE"
    TESTING = "TESTING"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    COMPLETED = "COMPLETED"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    REPEATED_FAILURE = "REPEATED_FAILURE"


class Session:
    """Represents an agent session"""
    
    def __init__(
        self,
        session_id: str = None,
        project: str = None,
        config: Config = None
    ):
        self.config = config or Config.load()
        self.session_id = session_id or self._generate_id()
        self.project = project
        self.state = AgentState.READY
        self.iteration = 0
        self.last_failure_hash: Optional[str] = None
        self.same_failure_count = 0
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.processed_call_ids: List[str] = []
        self.checkpoints: List[Dict[str, Any]] = []
        
        # Session directory
        self.sessions_dir = Path(__file__).parent.parent / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.session_dir = self.sessions_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Subdirectories
        self.executions_dir = self.session_dir / "executions"
        self.executions_dir.mkdir(exist_ok=True)
        
        self.checkpoints_dir = self.session_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        # Load existing state if available
        self._load_state()
    
    def _generate_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique}"
    
    def _load_state(self) -> None:
        """Load session state from disk"""
        state_file = self.session_dir / "state.json"
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                data = json.load(f)
            
            self.state = AgentState(data.get('state', 'READY'))
            self.iteration = data.get('iteration', 0)
            self.last_failure_hash = data.get('last_failure_hash')
            self.same_failure_count = data.get('same_failure_count', 0)
            self.processed_call_ids = data.get('processed_call_ids', [])
            self.project = data.get('project')
    
    def save_state(self) -> None:
        """Save session state to disk"""
        self.updated_at = datetime.utcnow().isoformat()
        
        state_data = {
            "session_id": self.session_id,
            "project": self.project,
            "state": self.state.value,
            "iteration": self.iteration,
            "last_failure_hash": self.last_failure_hash,
            "same_failure_count": self.same_failure_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processed_call_ids": self.processed_call_ids,
            "checkpoints": self.checkpoints
        }
        
        state_file = self.session_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def record_execution(self, execution_data: Dict[str, Any]) -> str:
        """Record a tool execution"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}.json"
        
        exec_file = self.executions_dir / filename
        with open(exec_file, 'w') as f:
            json.dump(execution_data, f, indent=2)
        
        return filename
    
    def add_checkpoint(self, checkpoint_name: str, checkpoint_data: Dict[str, Any]) -> str:
        """Add a checkpoint"""
        checkpoint = {
            "name": checkpoint_name,
            "timestamp": datetime.utcnow().isoformat(),
            "iteration": self.iteration,
            "data": checkpoint_data
        }
        
        self.checkpoints.append(checkpoint)
        
        # Save checkpoint to disk
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_name}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        self.save_state()
        
        return checkpoint_name
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Get the latest checkpoint"""
        if not self.checkpoints:
            return None
        
        return self.checkpoints[-1]
    
    def increment_iteration(self) -> int:
        """Increment iteration counter"""
        self.iteration += 1
        self.save_state()
        return self.iteration
    
    def track_failure(self, failure_hash: str) -> bool:
        """
        Track a failure and detect repeated failures.
        
        Returns True if this is a repeated failure (same hash).
        """
        if self.last_failure_hash == failure_hash:
            self.same_failure_count += 1
            return True
        else:
            self.last_failure_hash = failure_hash
            self.same_failure_count = 1
            return False
    
    def mark_call_processed(self, call_id: str) -> None:
        """Mark a tool call as processed"""
        if call_id not in self.processed_call_ids:
            self.processed_call_ids.append(call_id)
            self.save_state()
    
    def is_call_processed(self, call_id: str) -> bool:
        """Check if a tool call has been processed"""
        return call_id in self.processed_call_ids
    
    def set_state(self, state: AgentState) -> None:
        """Set the agent state"""
        self.state = state
        self.save_state()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "project": self.project,
            "state": self.state.value,
            "iteration": self.iteration,
            "last_failure_hash": self.last_failure_hash,
            "same_failure_count": self.same_failure_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processed_call_ids": self.processed_call_ids,
            "checkpoints": self.checkpoints
        }


class SessionManager:
    """Manages multiple sessions"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config.load()
        self.sessions: Dict[str, Session] = {}
        self.sessions_dir = Path(__file__).parent.parent / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
    
    def create_session(self, project: str = None) -> Session:
        """Create a new session"""
        session = Session(project=project, config=self.config)
        self.sessions[session.session_id] = session
        session.save_state()
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try to load from disk
        session_dir = self.sessions_dir / session_id
        if session_dir.exists():
            session = Session(session_id=session_id, config=self.config)
            self.sessions[session_id] = session
            return session
        
        return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        sessions = []
        
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        sessions.append(json.load(f))
        
        return sessions
    
    def cleanup_old_sessions(self, hours: int = 24) -> int:
        """Clean up old sessions"""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cleaned = 0
        
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        data = json.load(f)
                    
                    updated_at = datetime.fromisoformat(data.get('updated_at', ''))
                    
                    if updated_at < cutoff:
                        # Remove session directory
                        import shutil
                        shutil.rmtree(session_dir)
                        cleaned += 1
        
        return cleaned
