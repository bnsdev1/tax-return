"""Job schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration."""
    BUILD_RETURN = "build_return"
    VALIDATE_RETURN = "validate_return"
    GENERATE_PDF = "generate_pdf"
    SUBMIT_RETURN = "submit_return"


class BuildJobResponse(BaseModel):
    """Schema for build job response."""
    
    job_id: str = Field(
        ...,
        description="Unique job identifier",
        example="job_12345_build_return"
    )
    tax_return_id: int = Field(
        ...,
        description="Associated tax return ID",
        example=1
    )
    job_type: JobType = Field(
        ...,
        description="Type of job",
        example="build_return"
    )
    status: JobStatus = Field(
        ...,
        description="Current job status",
        example="queued"
    )
    
    # Progress information
    progress_percentage: int = Field(
        0,
        description="Job progress percentage",
        example=0,
        ge=0,
        le=100
    )
    current_step: str = Field(
        "",
        description="Current processing step",
        example="Initializing build process"
    )
    
    # Timing information
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated completion time"
    )
    
    # Results and errors
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Job result data (available when completed)"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )
    error_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed error information"
    )
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional job metadata"
    )
    
    class Config:
        from_attributes = True


class JobStep(BaseModel):
    """Individual job step information."""
    
    step_name: str = Field(..., description="Step name", example="validate_data")
    status: JobStatus = Field(..., description="Step status", example="completed")
    started_at: Optional[datetime] = Field(None, description="Step start time")
    completed_at: Optional[datetime] = Field(None, description="Step completion time")
    duration_ms: Optional[int] = Field(None, description="Step duration in milliseconds")
    result: Optional[Dict[str, Any]] = Field(None, description="Step result")
    error_message: Optional[str] = Field(None, description="Step error message")


class DetailedJobResponse(BuildJobResponse):
    """Extended job response with detailed step information."""
    
    steps: List[JobStep] = Field(
        default_factory=list,
        description="Detailed step information"
    )
    total_steps: int = Field(0, description="Total number of steps")
    completed_steps: int = Field(0, description="Number of completed steps")
    
    # Resource usage (optional)
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    
    class Config:
        from_attributes = True