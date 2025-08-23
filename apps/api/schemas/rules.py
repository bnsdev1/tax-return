"""
Pydantic schemas for Rules API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RuleSeverity(str, Enum):
    """Rule severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class RuleCategory(str, Enum):
    """Rule categories"""
    GENERAL = "general"
    DEDUCTIONS = "deductions"
    INCOME = "income"
    TAX = "tax"
    REBATE = "rebate"
    CAPITAL_GAINS = "capital_gains"
    HOUSE_PROPERTY = "house_property"
    TDS = "tds"
    REFUND = "refund"
    AGE = "age"

class RuleResultResponse(BaseModel):
    """Response model for a single rule evaluation result"""
    rule_code: str = Field(..., description="Unique rule identifier")
    description: str = Field(..., description="Human-readable rule description")
    input_values: Dict[str, Any] = Field(..., description="Input values used in evaluation")
    output_value: Any = Field(..., description="Result of rule evaluation")
    passed: bool = Field(..., description="Whether the rule passed")
    message: str = Field(..., description="Human-readable result message")
    severity: RuleSeverity = Field(..., description="Rule severity level")
    timestamp: datetime = Field(..., description="When the rule was evaluated")

class RuleDefinitionResponse(BaseModel):
    """Response model for rule definition"""
    code: str = Field(..., description="Unique rule identifier")
    description: str = Field(..., description="Human-readable rule description")
    expression: str = Field(..., description="Rule evaluation expression")
    severity: RuleSeverity = Field(..., description="Rule severity level")
    message_pass: str = Field(..., description="Message when rule passes")
    message_fail: str = Field(..., description="Message when rule fails")
    enabled: bool = Field(..., description="Whether the rule is enabled")
    category: RuleCategory = Field(..., description="Rule category")

class RulesEvaluationRequest(BaseModel):
    """Request model for evaluating rules"""
    context: Dict[str, Any] = Field(..., description="Context data for rule evaluation")
    assessment_year: Optional[str] = Field("2025-26", description="Assessment year for rules")
    categories: Optional[List[RuleCategory]] = Field(None, description="Filter by categories")

class RulesEvaluationResponse(BaseModel):
    """Response model for rules evaluation"""
    results: List[RuleResultResponse] = Field(..., description="Rule evaluation results")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    assessment_year: str = Field(..., description="Assessment year used")

class RulesLogRequest(BaseModel):
    """Request model for fetching rules log"""
    category: Optional[RuleCategory] = Field(None, description="Filter by category")
    severity: Optional[RuleSeverity] = Field(None, description="Filter by severity")
    passed: Optional[bool] = Field(None, description="Filter by pass/fail status")
    limit: Optional[int] = Field(100, description="Maximum number of results")
    offset: Optional[int] = Field(0, description="Offset for pagination")

class RulesLogResponse(BaseModel):
    """Response model for rules log"""
    results: List[RuleResultResponse] = Field(..., description="Rule evaluation results")
    total_count: int = Field(..., description="Total number of results")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")

class RulesSummaryResponse(BaseModel):
    """Response model for rules summary"""
    total_rules: int = Field(..., description="Total number of rules evaluated")
    passed: int = Field(..., description="Number of rules that passed")
    failed: int = Field(..., description="Number of rules that failed")
    errors: int = Field(..., description="Number of error-level failures")
    by_severity: Dict[str, int] = Field(..., description="Count by severity level")
    by_category: Dict[str, int] = Field(..., description="Count by category")

class RulesDefinitionsResponse(BaseModel):
    """Response model for rules definitions"""
    rules: List[RuleDefinitionResponse] = Field(..., description="Rule definitions")
    assessment_year: str = Field(..., description="Assessment year")
    total_count: int = Field(..., description="Total number of rules")