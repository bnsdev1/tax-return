"""Google Gemini client for long-context processing."""

import json
import os
from typing import Dict, Any, Optional
from pydantic import ValidationError
from .schema_map import get_schema_model, build_schema_prompt


class ClientResult:
    """Result from client call."""
    def __init__(self, ok: bool, model: str, json_data: Optional[Dict] = None, error: Optional[str] = None):
        self.ok = ok
        self.model = model
        self.json = json_data
        self.error = error


class GeminiClient:
    """Google Gemini client optimized for long-context processing."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = "gemini-2.0-flash-exp"  # Updated to use Gemini 2.0 Flash
        
    def call(self, task, text: str, schema_name: str, timeout_ms: int = 40000) -> ClientResult:
        """
        Call Gemini with structured output validation.
        
        Args:
            task: LLMTask instance
            text: Input text to process
            schema_name: Schema to validate against
            timeout_ms: Timeout in milliseconds
            
        Returns:
            ClientResult with validation
        """
        if not self.api_key:
            return ClientResult(ok=False, model=self.model, error="GEMINI_API_KEY not set")
        
        try:
            Model = get_schema_model(schema_name)
            system_prompt = build_schema_prompt(schema_name)
            user_prompt = f"TASK: {task.name}\nTEXT:\n{text}"
            
            # Call Gemini API (mock implementation for now)
            raw_response = self._call_gemini_api(system_prompt, user_prompt, timeout_ms)
            
            # Parse JSON strictly
            try:
                data = json.loads(raw_response.strip())
            except json.JSONDecodeError as e:
                return ClientResult(ok=False, model=self.model, error=f"Invalid JSON: {e}")
            
            # Validate against Pydantic schema
            try:
                validated = Model.model_validate(data)
                return ClientResult(ok=True, model=self.model, json_data=validated.model_dump())
            except ValidationError as ve:
                return ClientResult(ok=False, model=self.model, error=f"Schema validation failed: {ve}")
                
        except Exception as e:
            return ClientResult(ok=False, model=self.model, error=f"Gemini call failed: {e}")
    
    def _call_gemini_api(self, system_prompt: str, user_prompt: str, timeout_ms: int) -> str:
        """
        Mock Gemini API call. In production, this would use the Google AI SDK.
        
        Args:
            system_prompt: System message
            user_prompt: User message  
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Raw response text
        """
        # Mock response for development - replace with actual Gemini SDK call
        if "form16_extract" in user_prompt.lower():
            return '{"gross_salary": 1150000, "exemptions": {"hra": 180000, "lta": 45000}, "standard_deduction": 50000, "tds": 115000, "employer_name": "Global Tech Solutions", "period_from": "2024-04-01", "period_to": "2025-03-31", "confidence": 0.88}'
        elif "bank_line_classify" in user_prompt.lower():
            return '{"label": "FD_INTEREST", "confidence": 0.92, "rationale": "Fixed deposit interest credit transaction"}'
        elif "rules_explain" in user_prompt.lower():
            return '{"bullets": ["Income tax calculated using new tax regime rates", "No additional deductions claimed under Section 80C", "Advance tax payments will be adjusted in final computation"]}'
        else:
            return '{"confidence": 0.6}'


# Global instance
gemini_client = GeminiClient()