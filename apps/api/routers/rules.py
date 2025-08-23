"""
API routes for Rules Engine functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..schemas.rules import (
    RulesEvaluationRequest,
    RulesEvaluationResponse,
    RulesLogRequest,
    RulesLogResponse,
    RulesSummaryResponse,
    RulesDefinitionsResponse,
    RuleCategory,
    RuleSeverity,
    RuleResultResponse,
    RuleDefinitionResponse
)

# Import the rules engine
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from packages.core.src.core.rules.engine import create_default_engine, RulesEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["rules"])

# Global rules engine instance
_rules_engine: Optional[RulesEngine] = None

def get_rules_engine() -> RulesEngine:
    """Get or create the global rules engine instance"""
    global _rules_engine
    if _rules_engine is None:
        _rules_engine = create_default_engine()
    return _rules_engine

@router.post("/evaluate", response_model=RulesEvaluationResponse)
async def evaluate_rules(request: RulesEvaluationRequest):
    """
    Evaluate all rules against the provided context data
    
    This endpoint runs all enabled rules for the specified assessment year
    against the provided context data and returns detailed results.
    """
    try:
        engine = get_rules_engine()
        
        # Load rules for the specified assessment year if different
        if request.assessment_year != "2025-26":
            try:
                engine.load_rules(f"{request.assessment_year}/rules.yaml")
            except Exception as e:
                logger.warning(f"Could not load rules for {request.assessment_year}: {e}")
        
        # Clear previous log to avoid mixing results
        engine.clear_log()
        
        # Evaluate rules
        results = engine.evaluate_all_rules(request.context)
        
        # Filter by categories if specified
        if request.categories:
            category_codes = set()
            for rule in engine.rules:
                if rule.category in request.categories:
                    category_codes.add(rule.code)
            results = [r for r in results if r.rule_code in category_codes]
        
        # Convert to response format
        result_responses = [
            RuleResultResponse(
                rule_code=result.rule_code,
                description=result.description,
                input_values=result.input_values,
                output_value=result.output_value,
                passed=result.passed,
                message=result.message,
                severity=result.severity,
                timestamp=result.timestamp
            )
            for result in results
        ]
        
        # Get summary
        summary = engine.get_rule_summary()
        
        return RulesEvaluationResponse(
            results=result_responses,
            summary=summary,
            assessment_year=request.assessment_year
        )
        
    except Exception as e:
        logger.error(f"Error evaluating rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate rules: {str(e)}")

@router.get("/log", response_model=RulesLogResponse)
async def get_rules_log(
    category: Optional[RuleCategory] = Query(None, description="Filter by category"),
    severity: Optional[RuleSeverity] = Query(None, description="Filter by severity"),
    passed: Optional[bool] = Query(None, description="Filter by pass/fail status"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get the rules evaluation log with optional filtering
    
    Returns a paginated list of rule evaluation results from the current session.
    """
    try:
        engine = get_rules_engine()
        
        # Get filtered log
        filtered_log = engine.get_rules_log(
            category=category.value if category else None,
            severity=severity.value if severity else None,
            passed=passed
        )
        
        # Apply pagination
        total_count = len(filtered_log)
        paginated_log = filtered_log[offset:offset + limit]
        
        # Convert to response format
        result_responses = [
            RuleResultResponse(
                rule_code=result.rule_code,
                description=result.description,
                input_values=result.input_values,
                output_value=result.output_value,
                passed=result.passed,
                message=result.message,
                severity=result.severity,
                timestamp=result.timestamp
            )
            for result in paginated_log
        ]
        
        # Get summary
        summary = engine.get_rule_summary()
        
        return RulesLogResponse(
            results=result_responses,
            total_count=total_count,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error fetching rules log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rules log: {str(e)}")

@router.get("/summary", response_model=RulesSummaryResponse)
async def get_rules_summary():
    """
    Get summary statistics of rule evaluations
    
    Returns aggregate statistics about rule evaluations from the current session.
    """
    try:
        engine = get_rules_engine()
        summary = engine.get_rule_summary()
        
        return RulesSummaryResponse(
            total_rules=summary['total_rules'],
            passed=summary['passed'],
            failed=summary['failed'],
            errors=summary['errors'],
            by_severity=summary['by_severity'],
            by_category=summary['by_category']
        )
        
    except Exception as e:
        logger.error(f"Error getting rules summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rules summary: {str(e)}")

@router.get("/definitions", response_model=RulesDefinitionsResponse)
async def get_rules_definitions(
    assessment_year: str = Query("2025-26", description="Assessment year"),
    category: Optional[RuleCategory] = Query(None, description="Filter by category")
):
    """
    Get all rule definitions for the specified assessment year
    
    Returns the complete list of rule definitions including their expressions,
    descriptions, and configuration.
    """
    try:
        engine = get_rules_engine()
        
        # Load rules for the specified assessment year if different
        if assessment_year != "2025-26":
            try:
                engine.load_rules(f"{assessment_year}/rules.yaml")
            except Exception as e:
                logger.warning(f"Could not load rules for {assessment_year}: {e}")
        
        # Filter by category if specified
        rules = engine.rules
        if category:
            rules = [r for r in rules if r.category == category.value]
        
        # Convert to response format
        rule_responses = [
            RuleDefinitionResponse(
                code=rule.code,
                description=rule.description,
                expression=rule.expression,
                severity=rule.severity,
                message_pass=rule.message_pass,
                message_fail=rule.message_fail,
                enabled=rule.enabled,
                category=rule.category
            )
            for rule in rules
        ]
        
        return RulesDefinitionsResponse(
            rules=rule_responses,
            assessment_year=assessment_year,
            total_count=len(rule_responses)
        )
        
    except Exception as e:
        logger.error(f"Error getting rules definitions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rules definitions: {str(e)}")

@router.post("/clear-log")
async def clear_rules_log():
    """
    Clear the rules evaluation log
    
    Removes all rule evaluation results from the current session.
    """
    try:
        engine = get_rules_engine()
        engine.clear_log()
        
        return {"message": "Rules log cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing rules log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear rules log: {str(e)}")

@router.get("/categories")
async def get_rule_categories():
    """
    Get all available rule categories
    
    Returns a list of all rule categories that can be used for filtering.
    """
    return {
        "categories": [category.value for category in RuleCategory],
        "severities": [severity.value for severity in RuleSeverity]
    }