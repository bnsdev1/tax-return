"""Pydantic contracts for LLM inputs and outputs."""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from datetime import date


class LLMTask(BaseModel):
    """Task definition for LLM processing."""
    name: Literal["form16_extract", "bank_line_classify", "rules_explain", "form26as_extract"]
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


class TDSRow(BaseModel):
    """TDS row data from Form 26AS."""
    tan: Optional[str] = None
    deductor: Optional[str] = None
    section: Optional[str] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    amount: int = Field(ge=0)


class ChallanRow(BaseModel):
    """Challan row data from Form 26AS."""
    kind: str = Field(pattern=r'^(ADVANCE|SELF_ASSESSMENT)$')
    bsr_code: Optional[str] = None
    challan_no: Optional[str] = None
    paid_on: Optional[date] = None
    amount: int = Field(ge=0)


class Form26ASExtract(BaseModel):
    """Complete Form 26AS extraction result."""
    tds_salary: List[TDSRow] = Field(default_factory=list)
    tds_others: List[TDSRow] = Field(default_factory=list)
    tcs: List[TDSRow] = Field(default_factory=list)
    challans: List[ChallanRow] = Field(default_factory=list)
    totals: Dict[str, int] = Field(default_factory=dict)
    source: str = "LLM_FALLBACK"
    confidence: float = Field(ge=0, le=1, default=0.7)


# Schema registry mapping
SCHEMA_MODELS = {
    "Form16Extract": Form16Extract,
    "BankNarrationLabel": BankNarrationLabel,
    "RulesExplanation": RulesExplanation,
    "Form26ASExtract": Form26ASExtract,
}