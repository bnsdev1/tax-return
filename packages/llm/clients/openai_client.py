"""OpenAI client for structured JSON extraction."""

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


class OpenAIClient:
    """OpenAI client with JSON-only responses and schema validation."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"  # Updated to use GPT-4o mini
        
    def call(self, task, text: str, schema_name: str, timeout_ms: int = 40000) -> ClientResult:
        """
        Call OpenAI with structured output validation.
        
        Args:
            task: LLMTask instance
            text: Input text to process
            schema_name: Schema to validate against
            timeout_ms: Timeout in milliseconds
            
        Returns:
            ClientResult with validation
        """
        if not self.api_key:
            return ClientResult(ok=False, model=self.model, error="OPENAI_API_KEY not set")
        
        try:
            Model = get_schema_model(schema_name)
            system_prompt = build_schema_prompt(schema_name)
            user_prompt = f"TASK: {task.name}\nTEXT:\n{text}"
            
            # Call OpenAI API (mock implementation for now)
            raw_response = self._call_openai_api(system_prompt, user_prompt, timeout_ms)
            
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
            return ClientResult(ok=False, model=self.model, error=f"OpenAI call failed: {e}")
    
    def _call_openai_api(self, system_prompt: str, user_prompt: str, timeout_ms: int) -> str:
        """
        Mock OpenAI API call. In production, this would use the OpenAI SDK.
        
        Args:
            system_prompt: System message
            user_prompt: User message  
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Raw response text
        """
        # Mock response for development - replace with actual OpenAI SDK call
        if "form16_extract" in user_prompt.lower():
            return '{"gross_salary": 1200000, "exemptions": {"hra": 200000, "lta": 50000}, "standard_deduction": 50000, "tds": 120000, "employer_name": "Tech Corp Ltd", "period_from": "2024-04-01", "period_to": "2025-03-31", "confidence": 0.85}'
        elif "bank_line_classify" in user_prompt.lower():
            return '{"label": "SAVINGS_INTEREST", "confidence": 0.9, "rationale": "Contains interest credit keywords"}'
        elif "rules_explain" in user_prompt.lower():
            return '{"bullets": ["Standard deduction of ₹50,000 applied automatically", "HRA exemption calculated based on actual rent paid", "TDS deducted by employer will be adjusted against final tax liability"]}'
        else:
            return '{"confidence": 0.5}'


# Global instance
openai_client = OpenAIClient()