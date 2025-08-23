"""LLM Router with provider selection and fallback logic."""

import time
from typing import Dict, Any, List
from .clients import openai_client, gemini_client, ollama_client
from .redact import redact_text, should_redact
from .contracts import LLMTask, LLMResult


class LLMSettings:
    """LLM configuration settings."""
    
    def __init__(self, settings_dict: Dict[str, Any]):
        self.llm_enabled = settings_dict.get("llm_enabled", True)
        self.cloud_allowed = settings_dict.get("cloud_allowed", True)
        self.primary = settings_dict.get("primary", "openai")
        self.long_context_provider = settings_dict.get("long_context_provider", "gemini")
        self.local_provider = settings_dict.get("local_provider", "ollama")
        self.redact_pii = settings_dict.get("redact_pii", True)
        self.long_context_threshold_chars = settings_dict.get("long_context_threshold_chars", 8000)
        self.confidence_threshold = settings_dict.get("confidence_threshold", 0.7)
        self.max_retries = settings_dict.get("max_retries", 2)
        self.timeout_ms = settings_dict.get("timeout_ms", 40000)


class LLMRouter:
    """Router for LLM providers with policy-based selection and fallback."""
    
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.clients = {
            "openai": openai_client,
            "gemini": gemini_client,
            "ollama": ollama_client
        }
    
    def run(self, task: LLMTask) -> LLMResult:
        """
        Execute LLM task with provider selection and fallback.
        
        Args:
            task: LLM task to execute
            
        Returns:
            LLMResult with provider info and output
        """
        if not self.settings.llm_enabled:
            return LLMResult(
                ok=False, 
                provider="none", 
                model="none", 
                attempts=0, 
                error="LLM disabled in settings"
            )
        
        # Determine provider order based on policy
        provider_order = self._get_provider_order(task.text)
        
        # Apply redaction if needed
        text_to_process = task.text
        redaction_applied = False
        
        if should_redact(task.text, self.settings.cloud_allowed, self.settings.redact_pii):
            text_to_process, redaction_counts = redact_text(task.text)
            redaction_applied = True
        
        # Try providers in order with retries
        last_error = None
        total_attempts = 0
        
        for provider_name in provider_order:
            client = self.clients[provider_name]
            
            # For cloud providers, use redacted text if applicable
            if provider_name in ["openai", "gemini"] and redaction_applied:
                input_text = text_to_process
            else:
                input_text = task.text  # Use original text for local processing
            
            # Retry logic for current provider
            for retry in range(1 + self.settings.max_retries):
                total_attempts += 1
                
                try:
                    start_time = time.time()
                    result = client.call(task, input_text, task.schema_name, self.settings.timeout_ms)
                    end_time = time.time()
                    
                    if result.ok:
                        # Check confidence threshold if applicable
                        if self._meets_confidence_threshold(result.json):
                            return LLMResult(
                                ok=True,
                                provider=provider_name,
                                model=result.model,
                                attempts=total_attempts,
                                json=result.json
                            )
                        else:
                            last_error = f"Confidence below threshold ({self.settings.confidence_threshold})"
                            continue
                    else:
                        last_error = result.error
                        
                except Exception as e:
                    last_error = f"Provider {provider_name} error: {e}"
                
                # Exponential backoff for retries
                if retry < self.settings.max_retries:
                    time.sleep(min(2 ** retry, 10))
        
        return LLMResult(
            ok=False,
            provider="failover",
            model="",
            attempts=total_attempts,
            error=last_error or "All providers failed"
        )
    
    def _get_provider_order(self, text: str) -> List[str]:
        """
        Determine provider order based on text length and settings.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of provider names in order of preference
        """
        provider_order = []
        
        if self.settings.cloud_allowed:
            # For long context, prefer Gemini first
            if len(text) >= self.settings.long_context_threshold_chars:
                provider_order = [self.settings.long_context_provider, self.settings.primary]
            else:
                provider_order = [self.settings.primary, self.settings.long_context_provider]
        
        # Always add local provider as fallback
        if self.settings.local_provider not in provider_order:
            provider_order.append(self.settings.local_provider)
        
        return provider_order
    
    def _meets_confidence_threshold(self, json_output: Dict[str, Any]) -> bool:
        """
        Check if output meets confidence threshold.
        
        Args:
            json_output: LLM output JSON
            
        Returns:
            True if confidence is above threshold
        """
        if not json_output:
            return False
        
        confidence = json_output.get("confidence", 1.0)
        return confidence >= self.settings.confidence_threshold
    
    def ping_provider(self, provider_name: str) -> Dict[str, Any]:
        """
        Test connectivity to a specific provider.
        
        Args:
            provider_name: Name of provider to test
            
        Returns:
            Dict with test results
        """
        if provider_name not in self.clients:
            return {"ok": False, "error": f"Unknown provider: {provider_name}"}
        
        try:
            # Create a simple test task
            test_task = LLMTask(
                name="form16_extract",
                schema_name="Form16Extract", 
                prompt="Test connectivity",
                text="Test input"
            )
            
            client = self.clients[provider_name]
            start_time = time.time()
            result = client.call(test_task, "Test", "Form16Extract", 10000)
            end_time = time.time()
            
            return {
                "ok": result.ok,
                "provider": provider_name,
                "model": result.model,
                "response_time_ms": int((end_time - start_time) * 1000),
                "error": result.error
            }
            
        except Exception as e:
            return {
                "ok": False,
                "provider": provider_name,
                "error": str(e)
            }