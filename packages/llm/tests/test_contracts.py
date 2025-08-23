"""Tests for LLM contracts and schemas."""

import pytest
from pydantic import ValidationError
from packages.llm.contracts import (
    LLMTask, 
    LLMResult, 
    Form16Extract, 
    BankNarrationLabel, 
    RulesExplanation,
    SCHEMA_MODELS
)


class TestLLMContracts:
    """Test LLM contract schemas."""
    
    def test_llm_task_validation(self):
        """Test LLMTask validation."""
        # Valid task
        task = LLMTask(
            name="form16_extract",
            schema_name="Form16Extract",
            prompt="Extract data",
            text="Sample text"
        )
        assert task.name == "form16_extract"
        assert task.schema_name == "Form16Extract"
        
        # Invalid task name
        with pytest.raises(ValidationError):
            LLMTask(
                name="invalid_task",
                schema_name="Form16Extract",
                prompt="Extract data",
                text="Sample text"
            )
    
    def test_llm_result_validation(self):
        """Test LLMResult validation."""
        # Successful result
        result = LLMResult(
            ok=True,
            provider="openai",
            model="gpt-4o-mini",
            attempts=1,
            json={"confidence": 0.8}
        )
        assert result.ok == True
        assert result.provider == "openai"
        assert result.json == {"confidence": 0.8}
        
        # Failed result
        result = LLMResult(
            ok=False,
            provider="openai",
            model="gpt-4o-mini",
            attempts=2,
            error="API error"
        )
        assert result.ok == False
        assert result.error == "API error"
    
    def test_form16_extract_validation(self):
        """Test Form16Extract schema validation."""
        # Valid extraction
        extract = Form16Extract(
            gross_salary=1200000,
            exemptions={"hra": 200000, "lta": 50000},
            standard_deduction=50000,
            tds=120000,
            employer_name="Tech Corp",
            period_from="2024-04-01",
            period_to="2025-03-31",
            confidence=0.85
        )
        assert extract.gross_salary == 1200000
        assert extract.exemptions["hra"] == 200000
        assert extract.confidence == 0.85
        
        # Invalid confidence (out of range)
        with pytest.raises(ValidationError):
            Form16Extract(confidence=1.5)
        
        # Valid with minimal data
        minimal_extract = Form16Extract(confidence=0.5)
        assert minimal_extract.gross_salary is None
        assert minimal_extract.exemptions == {}
    
    def test_bank_narration_label_validation(self):
        """Test BankNarrationLabel schema validation."""
        # Valid classification
        label = BankNarrationLabel(
            label="SAVINGS_INTEREST",
            confidence=0.9,
            rationale="Contains interest credit keywords"
        )
        assert label.label == "SAVINGS_INTEREST"
        assert label.confidence == 0.9
        
        # Invalid label
        with pytest.raises(ValidationError):
            BankNarrationLabel(
                label="INVALID_LABEL",
                confidence=0.8
            )
        
        # Valid with minimal data
        minimal_label = BankNarrationLabel(
            label="NEGLIGIBLE",
            confidence=0.5
        )
        assert minimal_label.rationale is None
    
    def test_rules_explanation_validation(self):
        """Test RulesExplanation schema validation."""
        # Valid explanation
        explanation = RulesExplanation(
            bullets=[
                "Standard deduction applied",
                "HRA exemption calculated",
                "Tax computed using new regime"
            ]
        )
        assert len(explanation.bullets) == 3
        assert "Standard deduction" in explanation.bullets[0]
        
        # Empty explanation (valid)
        empty_explanation = RulesExplanation()
        assert explanation.bullets == []
        
        # Explanation with empty bullets
        explanation_with_empty = RulesExplanation(bullets=["", "Valid bullet", ""])
        assert len(explanation_with_empty.bullets) == 3
    
    def test_schema_models_registry(self):
        """Test schema models registry."""
        # Check all expected schemas are registered
        expected_schemas = ["Form16Extract", "BankNarrationLabel", "RulesExplanation"]
        
        for schema_name in expected_schemas:
            assert schema_name in SCHEMA_MODELS
            assert issubclass(SCHEMA_MODELS[schema_name], BaseModel)
        
        # Test schema instantiation
        for schema_name, model_class in SCHEMA_MODELS.items():
            # Should be able to create instance with defaults
            instance = model_class()
            assert isinstance(instance, BaseModel)
    
    def test_confidence_field_constraints(self):
        """Test confidence field constraints across schemas."""
        # Test Form16Extract confidence constraints
        with pytest.raises(ValidationError):
            Form16Extract(confidence=-0.1)  # Below 0
        
        with pytest.raises(ValidationError):
            Form16Extract(confidence=1.1)   # Above 1
        
        # Test BankNarrationLabel confidence constraints
        with pytest.raises(ValidationError):
            BankNarrationLabel(label="SAVINGS_INTEREST", confidence=-0.1)
        
        with pytest.raises(ValidationError):
            BankNarrationLabel(label="SAVINGS_INTEREST", confidence=1.1)
        
        # Valid confidence values
        Form16Extract(confidence=0.0)  # Minimum
        Form16Extract(confidence=1.0)  # Maximum
        Form16Extract(confidence=0.5)  # Middle
        
        BankNarrationLabel(label="SAVINGS_INTEREST", confidence=0.0)
        BankNarrationLabel(label="SAVINGS_INTEREST", confidence=1.0)
        BankNarrationLabel(label="SAVINGS_INTEREST", confidence=0.5)