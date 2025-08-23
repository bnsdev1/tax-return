"""
Rules Engine for Tax Return Validation and Processing

Evaluates YAML-defined rules against tax return data and maintains
an audit log of all rule applications with pass/fail status.
"""

import yaml
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RuleResult:
    """Result of a single rule evaluation"""
    rule_code: str
    description: str
    input_values: Dict[str, Any]
    output_value: Any
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RuleDefinition:
    """Definition of a rule from YAML"""
    code: str
    description: str
    expression: str
    severity: str = "info"
    message_pass: str = ""
    message_fail: str = ""
    enabled: bool = True
    category: str = "general"

class RulesEngine:
    """
    YAML-driven rules engine for tax return validation
    
    Evaluates simple expressions against tax return data and maintains
    a comprehensive audit log of all rule applications.
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        self.rules: List[RuleDefinition] = []
        self.rules_log: List[RuleResult] = []
        
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str) -> None:
        """Load rules from YAML file"""
        try:
            rules_path = Path(rules_file)
            if not rules_path.exists():
                # Try relative to this file
                rules_path = Path(__file__).parent / rules_file
            
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules_data = yaml.safe_load(f)
            
            self.rules = []
            for rule_data in rules_data.get('rules', []):
                rule = RuleDefinition(
                    code=rule_data['code'],
                    description=rule_data['description'],
                    expression=rule_data['expression'],
                    severity=rule_data.get('severity', 'info'),
                    message_pass=rule_data.get('message_pass', ''),
                    message_fail=rule_data.get('message_fail', ''),
                    enabled=rule_data.get('enabled', True),
                    category=rule_data.get('category', 'general')
                )
                self.rules.append(rule)
            
            logger.info(f"Loaded {len(self.rules)} rules from {rules_file}")
            
        except Exception as e:
            logger.error(f"Failed to load rules from {rules_file}: {e}")
            raise
    
    def evaluate_expression(self, expression: str, context: Dict[str, Any]) -> tuple[Any, Dict[str, Any]]:
        """
        Evaluate a simple expression against context data
        
        Supports:
        - Basic arithmetic: +, -, *, /, %, **
        - Comparisons: ==, !=, <, <=, >, >=
        - Logical: and, or, not
        - Functions: min(), max(), abs()
        - Variables from context
        
        Returns: (result, input_values_used)
        """
        # Track which variables were accessed
        input_values = {}
        
        # Create safe evaluation context with all context variables
        safe_context = {
            '__builtins__': {},
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'Decimal': Decimal,
        }
        
        # Add all context variables directly to safe_context
        for key, value in context.items():
            safe_context[key] = value
            input_values[key] = value
        
        # Also add context dict for backward compatibility
        safe_context['context'] = context
        
        try:
            # Evaluate the expression directly
            result = eval(expression, safe_context)
            return result, input_values
        except Exception as e:
            logger.error(f"Failed to evaluate expression '{expression}': {e}")
            return False, input_values
    
    def evaluate_rule(self, rule: RuleDefinition, context: Dict[str, Any]) -> RuleResult:
        """Evaluate a single rule against context data"""
        if not rule.enabled:
            return RuleResult(
                rule_code=rule.code,
                description=rule.description,
                input_values={},
                output_value=None,
                passed=True,
                message="Rule disabled",
                severity="info"
            )
        
        try:
            result, input_values = self.evaluate_expression(rule.expression, context)
            passed = bool(result)
            
            message = rule.message_pass if passed else rule.message_fail
            if not message:
                message = f"Rule {'passed' if passed else 'failed'}"
            
            return RuleResult(
                rule_code=rule.code,
                description=rule.description,
                input_values=input_values,
                output_value=result,
                passed=passed,
                message=message,
                severity=rule.severity
            )
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.code}: {e}")
            return RuleResult(
                rule_code=rule.code,
                description=rule.description,
                input_values={},
                output_value=None,
                passed=False,
                message=f"Evaluation error: {e}",
                severity="error"
            )
    
    def evaluate_all_rules(self, context: Dict[str, Any]) -> List[RuleResult]:
        """Evaluate all loaded rules against context data"""
        results = []
        
        for rule in self.rules:
            result = self.evaluate_rule(rule, context)
            results.append(result)
            self.rules_log.append(result)
        
        logger.info(f"Evaluated {len(results)} rules")
        return results
    
    def get_rules_log(self, 
                     category: Optional[str] = None,
                     severity: Optional[str] = None,
                     passed: Optional[bool] = None) -> List[RuleResult]:
        """Get filtered rules log"""
        filtered_log = self.rules_log
        
        if category:
            # Find rules in category
            category_rules = {r.code for r in self.rules if r.category == category}
            filtered_log = [r for r in filtered_log if r.rule_code in category_rules]
        
        if severity:
            filtered_log = [r for r in filtered_log if r.severity == severity]
        
        if passed is not None:
            filtered_log = [r for r in filtered_log if r.passed == passed]
        
        return filtered_log
    
    def clear_log(self) -> None:
        """Clear the rules log"""
        self.rules_log.clear()
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary statistics of rule evaluations"""
        if not self.rules_log:
            return {
                'total_rules': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'by_severity': {},
                'by_category': {}
            }
        
        total = len(self.rules_log)
        passed = sum(1 for r in self.rules_log if r.passed)
        failed = total - passed
        errors = sum(1 for r in self.rules_log if r.severity == 'error')
        
        by_severity = {}
        by_category = {}
        
        for result in self.rules_log:
            # Count by severity
            by_severity[result.severity] = by_severity.get(result.severity, 0) + 1
            
            # Count by category (need to look up rule definition)
            rule_def = next((r for r in self.rules if r.code == result.rule_code), None)
            if rule_def:
                category = rule_def.category
                by_category[category] = by_category.get(category, 0) + 1
        
        return {
            'total_rules': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'by_severity': by_severity,
            'by_category': by_category
        }

def create_default_engine(assessment_year: str = "2025-26") -> RulesEngine:
    """Create a rules engine with default rules for the given assessment year"""
    rules_file = f"{assessment_year}/rules.yaml"
    engine = RulesEngine()
    
    try:
        engine.load_rules(rules_file)
    except Exception as e:
        logger.warning(f"Could not load rules file {rules_file}: {e}")
        # Continue with empty rules - they can be loaded later
    
    return engine