"""Rules explanation generator using LLM for user-friendly explanations."""

from typing import List, Dict, Any
from packages.llm.router import LLMRouter
from packages.llm.contracts import LLMTask, RulesExplanation


class RulesExplainer:
    """LLM-powered rules explanation generator."""
    
    def __init__(self, router: LLMRouter):
        self.router = router
    
    def explain_rules_execution(self, rules_log: List[Dict[str, Any]]) -> RulesExplanation:
        """
        Generate user-friendly explanation of rules execution.
        
        Args:
            rules_log: List of rule execution records
            
        Returns:
            RulesExplanation with bullet points
        """
        # Format rules log for LLM processing
        formatted_log = self._format_rules_log(rules_log)
        
        # Create LLM task
        task = LLMTask(
            name="rules_explain",
            schema_name="RulesExplanation",
            prompt="Convert tax rule execution logs into user-friendly explanations",
            text=formatted_log
        )
        
        # Execute explanation generation
        result = self.router.run(task)
        
        if not result.ok:
            # Fallback to basic explanation
            return RulesExplanation(bullets=[
                f"Tax computation completed with {len(rules_log)} rules applied",
                "Detailed explanation unavailable due to processing error",
                f"Error: {result.error}"
            ])
        
        # Validate and return explanation
        explanation = RulesExplanation.model_validate(result.json)
        
        # Post-process to ensure quality
        explanation.bullets = self._post_process_bullets(explanation.bullets, rules_log)
        
        return explanation
    
    def explain_single_rule(self, rule_name: str, input_data: Dict, output_data: Dict) -> str:
        """
        Generate explanation for a single rule execution.
        
        Args:
            rule_name: Name of the rule
            input_data: Input data for the rule
            output_data: Output data from the rule
            
        Returns:
            Single explanation string
        """
        # Format single rule data
        rule_text = f"""
        Rule: {rule_name}
        Input: {input_data}
        Output: {output_data}
        """
        
        # Create LLM task
        task = LLMTask(
            name="rules_explain",
            schema_name="RulesExplanation",
            prompt="Explain this single tax rule execution",
            text=rule_text
        )
        
        # Execute explanation
        result = self.router.run(task)
        
        if result.ok and result.json.get("bullets"):
            return result.json["bullets"][0] if result.json["bullets"] else f"Applied rule: {rule_name}"
        else:
            return f"Applied rule: {rule_name}"
    
    def _format_rules_log(self, rules_log: List[Dict[str, Any]]) -> str:
        """
        Format rules log for LLM processing.
        
        Args:
            rules_log: List of rule execution records
            
        Returns:
            Formatted text for LLM
        """
        formatted_lines = []
        
        for i, rule in enumerate(rules_log, 1):
            rule_name = rule.get("rule_name", "Unknown")
            input_data = rule.get("input_data", {})
            output_data = rule.get("output_data", {})
            success = rule.get("success", False)
            
            formatted_lines.append(f"Rule {i}: {rule_name}")
            formatted_lines.append(f"  Success: {success}")
            
            if input_data:
                formatted_lines.append(f"  Input: {input_data}")
            
            if output_data:
                formatted_lines.append(f"  Output: {output_data}")
            
            if rule.get("error_message"):
                formatted_lines.append(f"  Error: {rule['error_message']}")
            
            formatted_lines.append("")  # Empty line between rules
        
        return "\n".join(formatted_lines)
    
    def _post_process_bullets(self, bullets: List[str], rules_log: List[Dict[str, Any]]) -> List[str]:
        """
        Post-process explanation bullets for quality and accuracy.
        
        Args:
            bullets: Generated bullet points
            rules_log: Original rules log for validation
            
        Returns:
            Processed bullet points
        """
        processed = []
        
        for bullet in bullets:
            # Remove empty bullets
            if not bullet.strip():
                continue
            
            # Ensure bullets don't start with bullet symbols
            bullet = bullet.strip()
            if bullet.startswith(('•', '-', '*')):
                bullet = bullet[1:].strip()
            
            # Limit bullet length
            if len(bullet) > 200:
                bullet = bullet[:197] + "..."
            
            processed.append(bullet)
        
        # Ensure we have at least one bullet
        if not processed:
            processed.append(f"Applied {len(rules_log)} tax computation rules successfully")
        
        # Limit total number of bullets
        return processed[:10]
    
    def generate_computation_summary(self, computation_result: Dict[str, Any]) -> List[str]:
        """
        Generate summary of tax computation results.
        
        Args:
            computation_result: Tax computation results
            
        Returns:
            List of summary bullet points
        """
        summary_text = f"""
        Tax Computation Summary:
        Gross Total Income: ₹{computation_result.get('gross_total_income', 0):,}
        Total Deductions: ₹{computation_result.get('total_deductions', 0):,}
        Taxable Income: ₹{computation_result.get('taxable_income', 0):,}
        Tax Before Relief: ₹{computation_result.get('tax_before_relief', 0):,}
        Tax After Relief: ₹{computation_result.get('tax_after_relief', 0):,}
        TDS/Advance Tax: ₹{computation_result.get('tds_advance_tax', 0):,}
        Tax Payable: ₹{computation_result.get('tax_payable', 0):,}
        """
        
        task = LLMTask(
            name="rules_explain",
            schema_name="RulesExplanation",
            prompt="Summarize tax computation results in user-friendly language",
            text=summary_text
        )
        
        result = self.router.run(task)
        
        if result.ok and result.json.get("bullets"):
            return result.json["bullets"]
        else:
            # Fallback summary
            return [
                f"Gross income: ₹{computation_result.get('gross_total_income', 0):,}",
                f"Taxable income after deductions: ₹{computation_result.get('taxable_income', 0):,}",
                f"Tax liability: ₹{computation_result.get('tax_after_relief', 0):,}",
                f"Tax payable: ₹{computation_result.get('tax_payable', 0):,}"
            ]


def create_fallback_explanation(rules_log: List[Dict[str, Any]]) -> RulesExplanation:
    """
    Create fallback explanation when LLM is unavailable.
    
    Args:
        rules_log: List of rule execution records
        
    Returns:
        Basic RulesExplanation
    """
    bullets = []
    
    successful_rules = [r for r in rules_log if r.get("success", False)]
    failed_rules = [r for r in rules_log if not r.get("success", False)]
    
    bullets.append(f"Successfully applied {len(successful_rules)} tax computation rules")
    
    if failed_rules:
        bullets.append(f"{len(failed_rules)} rules encountered issues and may need review")
    
    # Add specific rule mentions for important ones
    important_rules = ["standard_deduction", "tax_calculation", "hra_exemption"]
    for rule in successful_rules:
        rule_name = rule.get("rule_name", "").lower()
        if any(important in rule_name for important in important_rules):
            bullets.append(f"Applied {rule.get('rule_name', 'tax rule')}")
    
    return RulesExplanation(bullets=bullets[:5])  # Limit to 5 bullets