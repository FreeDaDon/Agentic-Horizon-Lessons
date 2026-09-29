"""
Data Types and Pydantic Models for Ultra Stream Agent
"""

from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Severity Levels
LogSeverity = Literal["low", "medium", "high"]


# Database Models
class ProducedLog(BaseModel):
    """Represents a processed log entry in the database"""

    id: Optional[int] = None
    log_index: int = Field(..., description="Line index in the original JSONL file")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    log_id: str = Field(..., description="Unique identifier for this log entry")
    log_summary: str = Field(..., description="Summarized version of the log entry")
    log_severity: LogSeverity = Field(..., description="Severity level of the log")
    raw_data: Dict[str, Any] = Field(..., description="Original raw log data")
    user_id: Optional[str] = Field(None, description="Associated user ID if available")


class ChatMessage(BaseModel):
    """Represents a message in the chat interface"""

    id: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    message: Optional[str] = Field(None, description="Text message content")
    produced_log: Optional[Dict[str, Any]] = Field(None, description="Associated produced log data")
    user_id: Optional[str] = Field(None, description="User who sent the message")
    message_type: Literal["user", "assistant", "alert", "system"] = Field("user")


class SessionInformation(BaseModel):
    """Stores session state for both agents"""

    current_line_index: int = Field(0, description="Current position in JSONL file")
    stream_agent_session_id: str = Field("", description="Session ID for Stream Agent")
    inspector_agent_session_id: str = Field("", description="Session ID for Inspector Agent")


# Tool Input/Output Models for Stream Agent
class ReadStreamFileInput(BaseModel):
    """Input for read_stream_file tool"""

    start_line_index: int = Field(..., description="Starting line index to read from")
    end_line_index: int = Field(..., description="Ending line index (exclusive)")


class ReadStreamFileOutput(BaseModel):
    """Output from read_stream_file tool"""

    data: List[Dict[str, Any]] = Field(..., description="Array of parsed log entries")
    next_index: int = Field(..., description="Next line index to read from")
    total_lines_read: int = Field(..., description="Number of lines actually read")


class SummarizedLogEntry(BaseModel):
    """A single summarized log entry"""

    line_index: int = Field(..., description="Original line index in JSONL file")
    log_id: str = Field(..., description="Unique identifier for this log")
    log_summary: str = Field(..., description="Concise summary of the log")
    log_severity: LogSeverity = Field(..., description="Severity classification")
    user_id: Optional[str] = Field(None, description="Associated user ID if present")


class ProduceSummarizedLogsInput(BaseModel):
    """Input for produce_summarized_logs tool"""

    summarized_logs: List[SummarizedLogEntry] = Field(..., description="List of summarized log entries")


class CreateAlertMessageInput(BaseModel):
    """Input for create_alert_message tool"""

    alert_message: str = Field(..., description="Alert message to display")
    relevant_start_index: int = Field(..., description="Start index of relevant logs")
    relevant_end_index: int = Field(..., description="End index of relevant logs")
    user_id: Optional[str] = Field(None, description="Associated user ID")


class ClearContextOutput(BaseModel):
    """Output from clear_context tool"""

    end_line_index: int = Field(..., description="Line index after context clear")
    message: str = Field(..., description="Status message")


# Tool Input/Output Models for Inspector Agent
class ReadProducedLogEntriesInput(BaseModel):
    """Input for read_produced_log_entries tool"""

    start_index: int = Field(..., description="Starting index in produced logs")
    end_index: int = Field(..., description="Ending index (exclusive)")


class ReadProducedLogEntriesOutput(BaseModel):
    """Output from read_produced_log_entries tool"""

    logs: List[ProducedLog] = Field(..., description="Array of produced log entries")
    next_index: int = Field(..., description="Next index to read from")
    total_count: int = Field(..., description="Total number of logs in database")


class FindLogsForUserInput(BaseModel):
    """Input for find_logs_for_user tool"""

    user_id: str = Field(..., description="User ID to search for")
    limit: int = Field(15, description="Maximum number of logs to return")
    order_by_newest_to_oldest: bool = Field(True, description="Sort order for results")


class FindLogsForUserOutput(BaseModel):
    """Output from find_logs_for_user tool"""

    logs: List[ProducedLog] = Field(..., description="Array of user's log entries")
    total_found: int = Field(..., description="Total number of logs found for user")


class NotifyTeamInput(BaseModel):
    """Input for notification tools"""

    alert_message: str = Field(..., description="Alert message to send")
    relevant_start_index: Optional[int] = Field(None, description="Start index of relevant logs")
    relevant_end_index: Optional[int] = Field(None, description="End index of relevant logs")
    user_id: Optional[str] = Field(None, description="Associated user ID")


# WebSocket Message Models
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""

    type: str = Field(..., description="Message type identifier")
    data: Any = Field(..., description="Message payload")


class StreamUpdateMessage(WebSocketMessage):
    """Message for stream agent updates"""

    type: Literal["stream_update"] = "stream_update"
    data: ProducedLog


class InspectorChatMessage(WebSocketMessage):
    """Message for inspector agent chat"""

    type: Literal["inspector_chat"] = "inspector_chat"
    data: ChatMessage


class AlertNotification(WebSocketMessage):
    """Alert notification message"""

    type: Literal["alert"] = "alert"
    data: Dict[str, Any]


class SystemStatusMessage(WebSocketMessage):
    """System status update message"""

    type: Literal["system_status"] = "system_status"
    data: Dict[str, str]


# API Request/Response Models
class StartAgentsRequest(BaseModel):
    """Request to start both agents"""

    jsonl_file_path: str = Field(..., description="Path to JSONL file to process")
    stream_criteria: Optional[str] = Field(None, description="Criteria for Stream Agent")
    inspector_prompt: Optional[str] = Field(None, description="Initial prompt for Inspector Agent")


class InspectorQueryRequest(BaseModel):
    """Request for Inspector Agent query"""

    query: str = Field(..., description="User's question for Inspector Agent")
    context_window: int = Field(50, description="Number of recent logs to consider")


class AgentStatusResponse(BaseModel):
    """Response with agent status information"""

    stream_agent_active: bool
    inspector_agent_active: bool
    current_line_index: int
    total_logs_processed: int
    last_update: str


# Configuration Models
class AgentConfiguration(BaseModel):
    """Configuration for an individual agent"""

    model: str = Field("claude-sonnet-4-20250514", description="Model to use")
    max_turns: int = Field(10, description="Maximum conversation turns")
    allowed_tools: List[str] = Field(..., description="List of allowed tool names")
    system_prompt_path: str = Field(..., description="Path to system prompt file")
    resume_session: bool = Field(False, description="Whether to resume previous session")


class UltraStreamConfig(BaseModel):
    """Overall configuration for Ultra Stream Agent system"""

    jsonl_file_path: str = Field("data/ultra_stream_agent.jsonl", description="Path to JSONL file")
    database_path: str = Field("ultra_stream.db", description="Path to SQLite database")
    stream_agent_config: AgentConfiguration
    inspector_agent_config: AgentConfiguration
    lines_to_read_per_batch: int = Field(5, description="Lines to read per Stream Agent iteration")
    max_lines_before_context_clear: int = Field(50, description="Lines before clearing context")
    notification_threshold: LogSeverity = Field("high", description="Minimum severity for notifications")