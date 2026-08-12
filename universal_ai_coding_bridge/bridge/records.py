"""
Execution Records for UACB

Records all tool executions for audit and replay.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ExecutionRecord(BaseModel):
    """Single execution record"""
    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f"))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str
    tool: str
    arguments: Dict[str, Any]
    iteration: int = 0
    result: Any = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class ExecutionRecorder:
    """Records and manages execution records"""
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.records_dir = session_dir / "executions"
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self._records: List[ExecutionRecord] = []
    
    def record(
        self,
        tool: str,
        arguments: Dict[str, Any],
        iteration: int,
        result: Any = None,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> ExecutionRecord:
        """Record a tool execution"""
        record = ExecutionRecord(
            session_id=self.session_dir.name,
            tool=tool,
            arguments=arguments,
            iteration=iteration,
            result=result,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            success=success,
            error=error
        )
        
        # Save to disk
        self._save_record(record)
        self._records.append(record)
        
        return record
    
    def _save_record(self, record: ExecutionRecord) -> None:
        """Save record to disk"""
        filename = f"{record.id}.json"
        filepath = self.records_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(record.model_dump_json(indent=2))
    
    def get_records(self, limit: int = 100) -> List[ExecutionRecord]:
        """Get recent execution records"""
        records = []
        
        # Load from disk
        for filepath in sorted(self.records_dir.glob("*.json"), reverse=True)[:limit]:
            with open(filepath, 'r') as f:
                data = json.load(f)
                records.append(ExecutionRecord(**data))
        
        return records
    
    def get_events_log(self) -> List[Dict[str, Any]]:
        """Get events in JSONL format"""
        events = []
        
        for record in self.get_records():
            events.append({
                "timestamp": record.timestamp,
                "tool": record.tool,
                "iteration": record.iteration,
                "success": record.success,
                "exit_code": record.exit_code
            })
        
        return events
    
    def save_events_log(self) -> None:
        """Save events log as JSONL file"""
        events_file = self.session_dir / "events.jsonl"
        
        with open(events_file, 'w') as f:
            for event in self.get_events_log():
                f.write(json.dumps(event) + "\n")
    
    def clear(self) -> None:
        """Clear all records"""
        for filepath in self.records_dir.glob("*.json"):
            filepath.unlink()
        self._records.clear()
