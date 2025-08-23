"""FastAPI router for LLM settings management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..db.base import get_db
from ..schemas.llm_settings import (
    LLMSettings,
    LLMSettingsCreate,
    LLMSettingsUpdate,
    ProviderPingRequest,
    ProviderPingResponse,
    LLMTaskRequest,
    LLMTaskResponse
)
from ..repo.llm_settings import LLMSettingsRepository
from packages.llm.router import LLMRouter, LLMSettings as LLMSettingsModel
from packages.llm.contracts import LLMTask

router = APIRouter(prefix="/api/settings/llm", tags=["LLM Settings"])


@router.get("/", response_model=LLMSettings)
async def get_llm_settings(db: Session = Depends(get_db)) -> LLMSettings:
    """Get current LLM settings."""
    repo = LLMSettingsRepository(db)
    settings = repo.get_settings()
    
    if not settings:
        # Return default settings if none exist
        default_settings = {
            "llm_enabled": True,
            "cloud_allowed": True,
            "primary": "openai",
            "long_context_provider": "gemini",
            "local_provider": "ollama",
            "redact_pii": True,
            "long_context_threshold_chars": 8000,
            "confidence_threshold": 0.7,
            "max_retries": 2,
            "timeout_ms": 40000
        }
        settings = repo.create_settings(default_settings)
    
    return settings


@router.put("/", response_model=LLMSettings)
async def update_llm_settings(
    settings_update: LLMSettingsUpdate,
    db: Session = Depends(get_db)
) -> LLMSettings:
    """Update LLM settings."""
    repo = LLMSettingsRepository(db)
    
    # Get current settings
    current_settings = repo.get_settings()
    if not current_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM settings not found"
        )
    
    # Update settings
    update_data = settings_update.model_dump(exclude_unset=True)
    updated_settings = repo.update_settings(current_settings.id, update_data)
    
    return updated_settings


@router.post("/ping", response_model=ProviderPingResponse)
async def ping_provider(
    ping_request: ProviderPingRequest,
    db: Session = Depends(get_db)
) -> ProviderPingResponse:
    """Test connectivity to a specific LLM provider."""
    repo = LLMSettingsRepository(db)
    settings_data = repo.get_settings()
    
    if not settings_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM settings not found"
        )
    
    # Convert to LLM settings model
    settings_dict = {
        "llm_enabled": settings_data.llm_enabled,
        "cloud_allowed": settings_data.cloud_allowed,
        "primary": settings_data.primary,
        "long_context_provider": settings_data.long_context_provider,
        "local_provider": settings_data.local_provider,
        "redact_pii": settings_data.redact_pii,
        "long_context_threshold_chars": settings_data.long_context_threshold_chars,
        "confidence_threshold": settings_data.confidence_threshold,
        "max_retries": settings_data.max_retries,
        "timeout_ms": settings_data.timeout_ms
    }
    
    llm_settings = LLMSettingsModel(settings_dict)
    router_instance = LLMRouter(llm_settings)
    
    # Ping the provider
    result = router_instance.ping_provider(ping_request.provider)
    
    return ProviderPingResponse(**result)


@router.post("/test", response_model=LLMTaskResponse)
async def test_llm_task(
    task_request: LLMTaskRequest,
    db: Session = Depends(get_db)
) -> LLMTaskResponse:
    """Test LLM task execution."""
    repo = LLMSettingsRepository(db)
    settings_data = repo.get_settings()
    
    if not settings_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM settings not found"
        )
    
    # Convert to LLM settings model
    settings_dict = {
        "llm_enabled": settings_data.llm_enabled,
        "cloud_allowed": settings_data.cloud_allowed,
        "primary": settings_data.primary,
        "long_context_provider": settings_data.long_context_provider,
        "local_provider": settings_data.local_provider,
        "redact_pii": settings_data.redact_pii,
        "long_context_threshold_chars": settings_data.long_context_threshold_chars,
        "confidence_threshold": settings_data.confidence_threshold,
        "max_retries": settings_data.max_retries,
        "timeout_ms": settings_data.timeout_ms
    }
    
    llm_settings = LLMSettingsModel(settings_dict)
    router_instance = LLMRouter(llm_settings)
    
    # Create and execute task
    task = LLMTask(
        name=task_request.task_name,
        schema_name=task_request.schema_name,
        prompt=task_request.prompt,
        text=task_request.text
    )
    
    result = router_instance.run(task)
    
    return LLMTaskResponse(
        ok=result.ok,
        provider=result.provider,
        model=result.model,
        attempts=result.attempts,
        result=result.json,
        error=result.error
    )


@router.get("/providers")
async def get_available_providers() -> Dict[str, Any]:
    """Get list of available LLM providers and their status."""
    return {
        "providers": [
            {
                "name": "openai",
                "display_name": "OpenAI GPT-4o Mini",
                "type": "cloud",
                "description": "Primary cloud model for structured extraction"
            },
            {
                "name": "gemini",
                "display_name": "Google Gemini 2.0 Flash",
                "type": "cloud",
                "description": "Long-context processing with caching"
            },
            {
                "name": "ollama",
                "display_name": "Llama 3.1 8B Instruct",
                "type": "local",
                "description": "Offline fallback via Ollama"
            }
        ],
        "task_types": [
            {
                "name": "form16_extract",
                "schema": "Form16Extract",
                "description": "Extract salary and tax details from Form 16B"
            },
            {
                "name": "bank_line_classify",
                "schema": "BankNarrationLabel",
                "description": "Classify bank transaction narrations"
            },
            {
                "name": "rules_explain",
                "schema": "RulesExplanation",
                "description": "Generate user-friendly rule explanations"
            }
        ]
    }