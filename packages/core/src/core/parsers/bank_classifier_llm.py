"""Bank narration classifier using LLM for complex transaction categorization."""

from typing import Dict, Any, List, Optional
from packages.llm.router import LLMRouter
from packages.llm.contracts import LLMTask, BankNarrationLabel


class BankClassifier:
    """LLM-powered bank transaction classifier."""
    
    def __init__(self, router: LLMRouter):
        self.router = router
        self.confidence_threshold = router.settings.confidence_threshold
    
    def classify_narration(self, narration: str) -> Dict[str, Any]:
        """
        Classify a single bank narration using LLM.
        
        Args:
            narration: Bank transaction narration text
            
        Returns:
            Classification result with label, confidence, and rationale
        """
        # Create LLM task
        task = LLMTask(
            name="bank_line_classify",
            schema_name="BankNarrationLabel",
            prompt="Classify bank transaction narration for tax purposes",
            text=narration
        )
        
        # Execute classification
        result = self.router.run(task)
        
        if not result.ok:
            return {
                "label": "NEGLIGIBLE",
                "confidence": 0.0,
                "rationale": f"Classification failed: {result.error}",
                "needs_review": True,
                "source": "LLM_FAILED"
            }
        
        # Extract classification data
        classification = BankNarrationLabel.model_validate(result.json)
        
        return {
            "label": classification.label,
            "confidence": classification.confidence,
            "rationale": classification.rationale,
            "needs_review": classification.confidence < self.confidence_threshold,
            "source": "LLM_CLASSIFIED",
            "provider": result.provider,
            "model": result.model
        }
    
    def classify_batch(self, narrations: List[str]) -> List[Dict[str, Any]]:
        """
        Classify multiple narrations in batch.
        
        Args:
            narrations: List of narration strings
            
        Returns:
            List of classification results
        """
        results = []
        for narration in narrations:
            try:
                result = self.classify_narration(narration)
                results.append(result)
            except Exception as e:
                results.append({
                    "label": "NEGLIGIBLE",
                    "confidence": 0.0,
                    "rationale": f"Error: {e}",
                    "needs_review": True,
                    "source": "ERROR"
                })
        
        return results
    
    def get_tax_relevant_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter transactions for tax-relevant items using LLM classification.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of tax-relevant transactions with classifications
        """
        tax_relevant = []
        
        for txn in transactions:
            narration = txn.get("narration", "")
            if not narration:
                continue
            
            # Classify the narration
            classification = self.classify_narration(narration)
            
            # Add classification to transaction
            txn.update(classification)
            
            # Include if tax-relevant
            if classification["label"] in ["SAVINGS_INTEREST", "FD_INTEREST"]:
                tax_relevant.append(txn)
            elif classification["needs_review"]:
                # Include uncertain classifications for manual review
                tax_relevant.append(txn)
        
        return tax_relevant


def enhance_bank_classifier(deterministic_classifier_func):
    """
    Decorator to enhance deterministic bank classifier with LLM fallback.
    
    Args:
        deterministic_classifier_func: Original rule-based classifier
        
    Returns:
        Enhanced classifier with LLM fallback
    """
    def enhanced_classifier(narration: str, router: Optional[LLMRouter] = None) -> Dict[str, Any]:
        """Enhanced classifier with LLM fallback."""
        try:
            # Try deterministic classification first
            result = deterministic_classifier_func(narration)
            result["source"] = "DETERMINISTIC"
            return result
            
        except Exception:
            if not router:
                return {
                    "label": "NEGLIGIBLE",
                    "confidence": 0.0,
                    "rationale": "Deterministic classification failed, no LLM available",
                    "needs_review": True,
                    "source": "FALLBACK"
                }
            
            # Use LLM fallback
            classifier = BankClassifier(router)
            return classifier.classify_narration(narration)
    
    return enhanced_classifier


# Predefined classification rules for common patterns
DETERMINISTIC_RULES = {
    "SAVINGS_INTEREST": [
        r"savings.*interest",
        r"sb.*interest",
        r"interest.*credited",
        r"int\.cr",
    ],
    "FD_INTEREST": [
        r"fd.*interest",
        r"fixed.*deposit.*interest",
        r"term.*deposit.*interest",
        r"td.*interest",
    ],
    "REVERSAL": [
        r"reversal",
        r"reversed",
        r"refund",
        r"chargeback",
    ],
    "CHARGES": [
        r"charges",
        r"fee",
        r"penalty",
        r"service.*charge",
    ]
}


def apply_deterministic_rules(narration: str) -> Optional[str]:
    """
    Apply deterministic rules for common transaction patterns.
    
    Args:
        narration: Transaction narration
        
    Returns:
        Classification label or None if no match
    """
    import re
    
    narration_lower = narration.lower()
    
    for label, patterns in DETERMINISTIC_RULES.items():
        for pattern in patterns:
            if re.search(pattern, narration_lower):
                return label
    
    return None