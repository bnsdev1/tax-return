"""Schema mapping and prompt generation for LLM clients."""

from typing import Dict, Tuple, Type
from pydantic import BaseModel
from ..contracts import SCHEMA_MODELS


def get_schema_model(schema_name: str) -> Type[BaseModel]:
    """Get Pydantic model class for schema name."""
    if schema_name not in SCHEMA_MODELS:
        raise ValueError(f"Unknown schema: {schema_name}")
    return SCHEMA_MODELS[schema_name]


def build_schema_prompt(schema_name: str) -> str:
    """Build system prompt for JSON-only output with schema validation."""
    Model = get_schema_model(schema_name)
    schema = Model.model_json_schema()
    
    base_prompt = (
        "You are a strict JSON extractor. Return ONLY minified JSON that matches the provided schema. "
        "Do not include any text outside JSON. Do not invent values; use null if absent. "
        "Do not include explanations or extra keys. Missing values should be null."
    )
    
    # Add schema-specific instructions
    if schema_name == "Form16Extract":
        specific = (
            "Extract salary totals, exemptions (hra, lta, others), standard_deduction, tds, "
            "employer_name, period_from/period_to, and a confidence (0..1) reflecting certainty."
        )
    elif schema_name == "BankNarrationLabel":
        specific = (
            "Classify the narration into one of: SAVINGS_INTEREST, FD_INTEREST, REVERSAL, CHARGES, NEGLIGIBLE. "
            "Provide confidence (0..1) and brief rationale."
        )
    elif schema_name == "RulesExplanation":
        specific = (
            "Convert rule logs into bullet points. Do not restate numbers differently; keep them as-is. "
            "Focus on explaining the logic, not changing values."
        )
    else:
        specific = "Follow the schema exactly."
    
    return f"{base_prompt}\n\n{specific}\n\nSchema: {schema}"


def get_schema_json(schema_name: str) -> Dict:
    """Get JSON schema for validation."""
    Model = get_schema_model(schema_name)
    return Model.model_json_schema()