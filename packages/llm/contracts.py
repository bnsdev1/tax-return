"""Pydantic contracts for LLM inputs and outputs."""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any


class LLMTask(BaseModel):
    """Task definition for LLM processing."""
    name: Literal["form16_extract", "bank_line_classify", "rules_explain"]
    schema_name: str  # which output schema to enforce
    prompt: str  # system + instructions
    text: str  # user text snippet


class LLMResult(BaseModel):
    """Result from LLM processing."""
    ok: bool
    provider: str
    model: str
    attempts: int
    json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Form16Extract(BaseModel):
    """Schema for Form 16B extraction results."""
    gross_salary: Optional[int] = None
    exemptions: Dict[str, int] = Field(default_factory=dict)
    standard_deduction: Optional[int] = None
    tds: Optional[int] = None
    employer_name: Optional[str] = None
    period_from: Optional[str] = None
    period_to: Optional[str] = None
    confidence: float = Field(ge=0, le=1, default=0.0)


class BankNarrationLabel(BaseModel):
    """Schema for bank narration classification."""
    label: Literal["SAVINGS_INTEREST", "FD_INTEREST", "REVERSAL", "CHARGES", "NEGLIGIBLE"]
    confidence: float = Field(ge=0, le=1, default=0.0)
    rationale: Optional[str] = None


class RulesExplanation(BaseModel):
    """Schema for rules explanation output."""
    bullets: List[str] = Field(default_factory=list)


# Schema registry mapping
SCHEMA_MODELS = {
    "Form16Extract": Form16Extract,
    "BankNarrationLabel": BankNarrationLabel,
    "RulesExplanation": RulesExplanation,
}