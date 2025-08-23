"""Pydantic schemas for LLM settings API."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class LLMSettingsBase(BaseModel):
    """Base LLM settings schema."""
    llm_enabled: bool = Field(default=True, description="Enable LLM processing")
    cloud_allowed: bool = Field(default=True, description="Allow cloud LLM providers")
    primary: str = Field(default="openai", description="Primary LLM provider")
    long_context_provider: str = Field(default="gemini", description="Provider for long context")
    local_provider: str = Field(default="ollama", description="Local LLM provider")
    redact_pii: bool = Field(default=True, description="Redact PII for cloud providers")
    long_context_threshold_chars: int = Field(default=8000, description="Threshold for long context")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_retries: int = Field(default=2, ge=0, le=5, description="Maximum retry attempts")
    timeout_ms: int = Field(default=40000, ge=1000, le=120000, description="Timeout in milliseconds")


class LLMSettingsCreate(LLMSettingsBase):
    """Schema for creating LLM settings."""
    pass


class LLMSettingsUpdate(BaseModel):
    """Schema for updating LLM settings."""
    llm_enabled: Optional[bool] = None
    cloud_allowed: Optional[bool] = None
    primary: Optional[str] = None
    long_context_provider: Optional[str] = None
    local_provider: Optional[str] = None
    redact_pii: Optional[bool] = None
    long_context_threshold_chars: Optional[int] = None
    confidence_threshold: Optional[float] = None
    max_retries: Optional[int] = None
    timeout_ms: Optional[int] = None


class LLMSettings(LLMSettingsBase):
    """Schema for LLM settings response."""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProviderPingRequest(BaseModel):
    """Schema for provider ping request."""
    provider: str = Field(description="Provider name to ping")


class ProviderPingResponse(BaseModel):
    """Schema for provider ping response."""
    ok: bool
    provider: str
    model: Optional[str] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None


class LLMTaskRequest(BaseModel):
    """Schema for LLM task execution request."""
    task_name: str = Field(description="Task name")
    schema_name: str = Field(description="Output schema name")
    prompt: str = Field(description="Task prompt")
    text: str = Field(description="Input text")


class LLMTaskResponse(BaseModel):
    """Schema for LLM task execution response."""
    ok: bool
    provider: str
    model: str
    attempts: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None