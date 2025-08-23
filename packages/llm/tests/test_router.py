"""Tests for LLM router functionality."""

import pytest
from unittest.mock import Mock, patch
from packages.llm.router import LLMRouter, LLMSettings
from packages.llm.contracts import LLMTask, LLMResult


class TestLLMRouter:
    """Test LLM router functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.settings_dict = {
            "llm_enabled": True,
            "cloud_allowed": True,
            "primary": "openai",
            "long_context_provider": "gemini",
            "local_provider": "ollama",
            "redact_pii": True,
            "long_context_threshold_chars": 8000,
            "confidence_threshold": 0.7,
            "max_retries": 2,
            "timeout_ms": 40000
        }
        self.settings = LLMSettings(self.settings_dict)
        self.router = LLMRouter(self.settings)
    
    def test_llm_disabled(self):
        """Test behavior when LLM is disabled."""
        disabled_settings = LLMSettings({**self.settings_dict, "llm_enabled": False})
        router = LLMRouter(disabled_settings)
        
        task = LLMTask(
            name="form16_extract",
            schema_name="Form16Extract",
            prompt="Test",
            text="Test input"
        )
        
        result = router.run(task)
        
        assert result.ok == False
        assert result.provider == "none"
        assert "disabled" in result.error.lower()
    
    def test_provider_order_short_text(self):
        """Test provider order for short text."""
        short_text = "Short text"
        provider_order = self.router._get_provider_order(short_text)
        
        # For short text, primary should come first
        assert provider_order[0] == "openai"
        assert "ollama" in provider_order  # Local fallback always included
    
    def test_provider_order_long_text(self):
        """Test provider order for long text."""
        long_text = "x" * 10000  # Exceeds threshold
        provider_order = self.router._get_provider_order(long_text)
        
        # For long text, long context provider should come first
        assert provider_order[0] == "gemini"
        assert "ollama" in provider_order  # Local fallback always included
    
    def test_provider_order_cloud_disabled(self):
        """Test provider order when cloud is disabled."""
        no_cloud_settings = LLMSettings({**self.settings_dict, "cloud_allowed": False})
        router = LLMRouter(no_cloud_settings)
        
        provider_order = router._get_provider_order("test text")
        
        # Only local provider should be in order
        assert provider_order == ["ollama"]
    
    def test_confidence_threshold_check(self):
        """Test confidence threshold validation."""
        # Above threshold
        high_confidence = {"confidence": 0.8}
        assert self.router._meets_confidence_threshold(high_confidence) == True
        
        # Below threshold
        low_confidence = {"confidence": 0.5}
        assert self.router._meets_confidence_threshold(low_confidence) == False
        
        # No confidence field (defaults to 1.0)
        no_confidence = {"result": "test"}
        assert self.router._meets_confidence_threshold(no_confidence) == True
        
        # Empty result
        assert self.router._meets_confidence_threshold({}) == False
    
    @patch('packages.llm.clients.openai_client.call')
    def test_successful_execution(self, mock_openai_call):
        """Test successful LLM execution."""
        # Mock successful OpenAI response
        mock_result = Mock()
        mock_result.ok = True
        mock_result.model = "gpt-4o-mini"
        mock_result.json = {"confidence": 0.8, "result": "test"}
        mock_openai_call.return_value = mock_result
        
        task = LLMTask(
            name="form16_extract",
            schema_name="Form16Extract",
            prompt="Test",
            text="Test input"
        )
        
        result = self.router.run(task)
        
        assert result.ok == True
        assert result.provider == "openai"
        assert result.model == "gpt-4o-mini"
        assert result.json == {"confidence": 0.8, "result": "test"}
    
    @patch('packages.llm.clients.openai_client.call')
    @patch('packages.llm.clients.gemini_client.call')
    @patch('packages.llm.clients.ollama_client.call')
    def test_fallback_chain(self, mock_ollama_call, mock_gemini_call, mock_openai_call):
        """Test fallback chain when providers fail."""
        # Mock all providers failing except Ollama
        mock_failed_result = Mock()
        mock_failed_result.ok = False
        mock_failed_result.error = "Provider failed"
        
        mock_openai_call.return_value = mock_failed_result
        mock_gemini_call.return_value = mock_failed_result
        
        # Mock Ollama success
        mock_success_result = Mock()
        mock_success_result.ok = True
        mock_success_result.model = "llama3.1:8b"
        mock_success_result.json = {"confidence": 0.75, "result": "test"}
        mock_ollama_call.return_value = mock_success_result
        
        task = LLMTask(
            name="form16_extract",
            schema_name="Form16Extract",
            prompt="Test",
            text="Test input"
        )
        
        result = self.router.run(task)
        
        assert result.ok == True
        assert result.provider == "ollama"
        assert result.model == "llama3.1:8b"
    
    def test_ping_provider(self):
        """Test provider ping functionality."""
        # Test unknown provider
        result = self.router.ping_provider("unknown")
        assert result["ok"] == False
        assert "Unknown provider" in result["error"]
        
        # Test known provider (will use mock implementation)
        result = self.router.ping_provider("openai")
        assert "provider" in result
        assert result["provider"] == "openai"