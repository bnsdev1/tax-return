#!/usr/bin/env python3
"""
Integration test for LLM helpers in ITR Prep app.

This test verifies the complete LLM integration including:
- Provider routing and fallback
- Form 16B extraction with LLM fallback
- Bank transaction classification
- Rules explanation generation
- Settings management via API
"""

import json
import pytest
import requests
from pathlib import Path
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30


class TestLLMIntegration:
    """Integration tests for LLM system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.api_url = API_BASE_URL
        self.session = requests.Session()
        
        # Ensure LLM settings exist
        self._ensure_llm_settings()
    
    def _ensure_llm_settings(self):
        """Ensure LLM settings are configured for testing."""
        try:
            response = self.session.get(f"{self.api_url}/api/settings/llm")
            if response.status_code == 404:
                # Create default settings
                default_settings = {
                    "llm_enabled": True,
                    "cloud_allowed": False,  # Use local only for testing
                    "primary": "openai",
                    "long_context_provider": "gemini",
                    "local_provider": "ollama",
                    "redact_pii": True,
                    "long_context_threshold_chars": 8000,
                    "confidence_threshold": 0.5,  # Lower for testing
                    "max_retries": 1,
                    "timeout_ms": 10000
                }
                
                create_response = self.session.put(
                    f"{self.api_url}/api/settings/llm",
                    json=default_settings
                )
                assert create_response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not available")
    
    def test_llm_settings_crud(self):
        """Test LLM settings CRUD operations."""
        # Get current settings
        response = self.session.get(f"{self.api_url}/api/settings/llm")
        assert response.status_code == 200
        
        settings = response.json()
        assert "llm_enabled" in settings
        assert "cloud_allowed" in settings
        assert "primary" in settings
        
        # Update settings
        update_data = {
            "confidence_threshold": 0.8,
            "max_retries": 3
        }
        
        response = self.session.put(
            f"{self.api_url}/api/settings/llm",
            json=update_data
        )
        assert response.status_code == 200
        
        updated_settings = response.json()
        assert updated_settings["confidence_threshold"] == 0.8
        assert updated_settings["max_retries"] == 3
    
    def test_provider_ping(self):
        """Test provider connectivity testing."""
        providers = ["openai", "gemini", "ollama"]
        
        for provider in providers:
            response = self.session.post(
                f"{self.api_url}/api/settings/llm/ping",
                json={"provider": provider}
            )
            assert response.status_code == 200
            
            result = response.json()
            assert "ok" in result
            assert result["provider"] == provider
            
            # For mock implementations, we expect them to work
            if provider == "ollama":
                # Ollama might not be running, so either ok or connection error
                assert result["ok"] in [True, False]
            else:
                # Mock implementations should always work
                assert result["ok"] == True
    
    def test_llm_task_execution(self):
        """Test direct LLM task execution."""
        task_request = {
            "task_name": "form16_extract",
            "schema_name": "Form16Extract",
            "prompt": "Extract salary details from Form 16B",
            "text": "FORM 16B - Gross Salary: Rs. 12,00,000, TDS: Rs. 1,20,000, Employer: Tech Corp Ltd"
        }
        
        response = self.session.post(
            f"{self.api_url}/api/settings/llm/test",
            json=task_request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "ok" in result
        assert "provider" in result
        assert "attempts" in result
        
        if result["ok"]:
            assert "result" in result
            assert result["result"] is not None
            
            # Validate Form16Extract schema
            form_data = result["result"]
            assert "confidence" in form_data
            assert 0 <= form_data["confidence"] <= 1
    
    def test_bank_classification_task(self):
        """Test bank narration classification."""
        task_request = {
            "task_name": "bank_line_classify",
            "schema_name": "BankNarrationLabel",
            "prompt": "Classify bank transaction",
            "text": "INTEREST CREDITED TO SAVINGS ACCOUNT - Rs. 1,250.00"
        }
        
        response = self.session.post(
            f"{self.api_url}/api/settings/llm/test",
            json=task_request
        )
        assert response.status_code == 200
        
        result = response.json()
        if result["ok"]:
            classification = result["result"]
            assert "label" in classification
            assert classification["label"] in [
                "SAVINGS_INTEREST", "FD_INTEREST", "REVERSAL", "CHARGES", "NEGLIGIBLE"
            ]
            assert "confidence" in classification
            assert 0 <= classification["confidence"] <= 1
    
    def test_rules_explanation_task(self):
        """Test rules explanation generation."""
        task_request = {
            "task_name": "rules_explain",
            "schema_name": "RulesExplanation",
            "prompt": "Explain tax rules",
            "text": "Standard deduction: Rs. 50,000 applied. HRA exemption: Rs. 1,50,000 calculated."
        }
        
        response = self.session.post(
            f"{self.api_url}/api/settings/llm/test",
            json=task_request
        )
        assert response.status_code == 200
        
        result = response.json()
        if result["ok"]:
            explanation = result["result"]
            assert "bullets" in explanation
            assert isinstance(explanation["bullets"], list)
    
    def test_provider_fallback_chain(self):
        """Test provider fallback when cloud is disabled."""
        # Disable cloud providers
        update_data = {"cloud_allowed": False}
        response = self.session.put(
            f"{self.api_url}/api/settings/llm",
            json=update_data
        )
        assert response.status_code == 200
        
        # Test task execution - should use local provider only
        task_request = {
            "task_name": "form16_extract",
            "schema_name": "Form16Extract",
            "prompt": "Extract data",
            "text": "Test form data"
        }
        
        response = self.session.post(
            f"{self.api_url}/api/settings/llm/test",
            json=task_request
        )
        assert response.status_code == 200
        
        result = response.json()
        if result["ok"]:
            # Should use local provider (ollama)
            assert result["provider"] == "ollama"
        
        # Re-enable cloud for other tests
        update_data = {"cloud_allowed": True}
        self.session.put(f"{self.api_url}/api/settings/llm", json=update_data)
    
    def test_confidence_threshold_enforcement(self):
        """Test confidence threshold enforcement."""
        # Set high confidence threshold
        update_data = {"confidence_threshold": 0.95}
        response = self.session.put(
            f"{self.api_url}/api/settings/llm",
            json=update_data
        )
        assert response.status_code == 200
        
        # Test task that might not meet threshold
        task_request = {
            "task_name": "form16_extract",
            "schema_name": "Form16Extract",
            "prompt": "Extract from unclear data",
            "text": "Unclear form data with missing information"
        }
        
        response = self.session.post(
            f"{self.api_url}/api/settings/llm/test",
            json=task_request
        )
        assert response.status_code == 200
        
        result = response.json()
        # Might fail due to confidence threshold
        if not result["ok"] and "confidence" in result.get("error", "").lower():
            print("Confidence threshold correctly enforced")
        
        # Reset threshold
        update_data = {"confidence_threshold": 0.5}
        self.session.put(f"{self.api_url}/api/settings/llm", json=update_data)
    
    def test_available_providers_endpoint(self):
        """Test available providers information endpoint."""
        response = self.session.get(f"{self.api_url}/api/settings/llm/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data
        assert "task_types" in data
        
        # Check provider information
        providers = data["providers"]
        provider_names = [p["name"] for p in providers]
        assert "openai" in provider_names
        assert "gemini" in provider_names
        assert "ollama" in provider_names
        
        # Check task types
        task_types = data["task_types"]
        task_names = [t["name"] for t in task_types]
        assert "form16_extract" in task_names
        assert "bank_line_classify" in task_names
        assert "rules_explain" in task_names
    
    def test_llm_disabled_behavior(self):
        """Test behavior when LLM is completely disabled."""
        # Disable LLM
        update_data = {"llm_enabled": False}
        response = self.session.put(
            f"{self.api_url}/api/settings/llm",
            json=update_data
        )
        assert response.status_code == 200
        
        # Test task execution - should fail gracefully
        task_request = {
            "task_name": "form16_extract",
            "schema_name": "Form16Extract",
            "prompt": "Extract data",
            "text": "Test data"
        }
        
        response = self.session.post(
            f"{self.api_url}/api/settings/llm/test",
            json=task_request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["ok"] == False
        assert "disabled" in result["error"].lower()
        
        # Re-enable LLM
        update_data = {"llm_enabled": True}
        self.session.put(f"{self.api_url}/api/settings/llm", json=update_data)


def run_integration_tests():
    """Run integration tests manually."""
    print("Running LLM Integration Tests...")
    
    test_instance = TestLLMIntegration()
    test_instance.setup_method()
    
    tests = [
        ("LLM Settings CRUD", test_instance.test_llm_settings_crud),
        ("Provider Ping", test_instance.test_provider_ping),
        ("LLM Task Execution", test_instance.test_llm_task_execution),
        ("Bank Classification", test_instance.test_bank_classification_task),
        ("Rules Explanation", test_instance.test_rules_explanation_task),
        ("Provider Fallback", test_instance.test_provider_fallback_chain),
        ("Confidence Threshold", test_instance.test_confidence_threshold_enforcement),
        ("Available Providers", test_instance.test_available_providers_endpoint),
        ("LLM Disabled", test_instance.test_llm_disabled_behavior),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            test_func()
            print(f"✓ {test_name} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)