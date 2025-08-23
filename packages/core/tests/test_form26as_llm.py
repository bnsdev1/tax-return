"""Tests for Form 26AS LLM fallback parser."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import date

from core.parsers.form26as_llm import (
    parse_form26as_llm,
    parse_form26as_with_fallback,
    _extract_text_from_pdf,
    _validate_form26as_data,
    enhance_form26as_parser
)
from core.parsers.form26as import Form26ASExtract, TDSRow, ChallanRow, ParseMiss


class MockLLMResult:
    """Mock LLM result for testing."""
    def __init__(self, ok=True, provider="openai", model="gpt-4", attempts=1, json=None, error=None):
        self.ok = ok
        self.provider = provider
        self.model = model
        self.attempts = attempts
        self.json = json or {}
        self.error = error


class TestForm26ASLLMParser:
    """Test cases for Form 26AS LLM fallback parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_pdf_path = Path("fixtures/26AS_sample_odd.pdf")
        self.mock_router = Mock()
    
    def test_parse_form26as_llm_success(self):
        """Test successful LLM parsing."""
        # Mock LLM response
        mock_result = MockLLMResult(
            ok=True,
            json={
                "tds_salary": [
                    {
                        "tan": "ABCD12345E",
                        "deductor": "ABC COMPANY LTD",
                        "section": "192",
                        "amount": 85000
                    }
                ],
                "tds_others": [
                    {
                        "tan": "BANK12345E",
                        "deductor": "XYZ BANK LTD",
                        "section": "194A",
                        "amount": 4500
                    }
                ],
                "tcs": [],
                "challans": [
                    {
                        "kind": "ADVANCE",
                        "bsr_code": "1234567",
                        "challan_no": "123456789",
                        "amount": 10000
                    }
                ],
                "totals": {
                    "tds_salary_total": 85000,
                    "tds_others_total": 4500
                },
                "confidence": 0.85
            }
        )
        
        self.mock_router.run.return_value = mock_result
        
        # Test LLM parsing
        text = "Sample Form 26AS text content"
        result = parse_form26as_llm(text, self.mock_router)
        
        # Verify result
        assert isinstance(result, Form26ASExtract)
        assert result.source == "LLM_FALLBACK"
        assert result.confidence == 0.85
        assert len(result.tds_salary) == 1
        assert len(result.tds_others) == 1
        assert len(result.challans) == 1
        assert result.tds_salary[0].amount == 85000
        assert result.challans[0].kind == "ADVANCE"
    
    def test_parse_form26as_llm_failure(self):
        """Test LLM parsing failure."""
        # Mock LLM failure
        mock_result = MockLLMResult(
            ok=False,
            error="API rate limit exceeded"
        )
        
        self.mock_router.run.return_value = mock_result
        
        # Test LLM parsing failure
        text = "Sample Form 26AS text content"
        with pytest.raises(RuntimeError, match="LLM Form 26AS extraction failed"):
            parse_form26as_llm(text, self.mock_router)
    
    @patch('core.parsers.form26as_llm._extract_text_from_pdf')
    def test_parse_form26as_with_fallback_deterministic_success(self, mock_extract_text):
        """Test fallback when deterministic parsing succeeds."""
        # Mock successful deterministic parsing
        with patch('core.parsers.form26as_llm.Form26ASParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.return_value = {
                "form26as_data": {"tds_salary": [], "confidence": 1.0},
                "metadata": {"parser": "deterministic", "confidence": 1.0}
            }
            mock_parser_class.return_value = mock_parser
            
            result = parse_form26as_with_fallback(self.sample_pdf_path, self.mock_router)
            
            # Should use deterministic result
            assert result["metadata"]["parser"] == "deterministic"
            mock_extract_text.assert_not_called()
    
    @patch('core.parsers.form26as_llm._extract_text_from_pdf')
    def test_parse_form26as_with_fallback_llm_success(self, mock_extract_text):
        """Test fallback when deterministic parsing fails and LLM succeeds."""
        mock_extract_text.return_value = "Extracted PDF text"
        
        # Mock deterministic parsing failure
        with patch('core.parsers.form26as_llm.Form26ASParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.side_effect = ParseMiss("Table extraction failed")
            mock_parser_class.return_value = mock_parser
            
            # Mock successful LLM parsing
            with patch('core.parsers.form26as_llm.parse_form26as_llm') as mock_llm_parse:
                mock_extract = Form26ASExtract(
                    tds_salary=[TDSRow(amount=85000)],
                    source="LLM_FALLBACK",
                    confidence=0.8
                )
                mock_llm_parse.return_value = mock_extract
                
                result = parse_form26as_with_fallback(self.sample_pdf_path, self.mock_router)
                
                # Should use LLM result
                assert result["metadata"]["parser"] == "llm_fallback"
                assert result["metadata"]["confidence"] == 0.8
                mock_extract_text.assert_called_once()
                mock_llm_parse.assert_called_once()
    
    def test_parse_form26as_with_fallback_no_router(self):
        """Test fallback when no router is provided."""
        # Mock deterministic parsing failure
        with patch('core.parsers.form26as_llm.Form26ASParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.side_effect = ParseMiss("Table extraction failed")
            mock_parser_class.return_value = mock_parser
            
            with pytest.raises(RuntimeError, match="no LLM router provided"):
                parse_form26as_with_fallback(self.sample_pdf_path, None)
    
    @patch('pdfplumber.open')
    def test_extract_text_from_pdf_success(self, mock_pdfplumber):
        """Test successful text extraction from PDF."""
        # Mock PDF pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        result = _extract_text_from_pdf(self.sample_pdf_path)
        
        expected = "--- Page 1 ---\nPage 1 content\n\n--- Page 2 ---\nPage 2 content"
        assert result == expected
    
    @patch('pdfplumber.open')
    def test_extract_text_from_pdf_no_text(self, mock_pdfplumber):
        """Test text extraction when PDF has no extractable text."""
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        with pytest.raises(Exception, match="No text could be extracted"):
            _extract_text_from_pdf(self.sample_pdf_path)
    
    @patch('pdfplumber.open')
    def test_extract_text_from_pdf_failure(self, mock_pdfplumber):
        """Test text extraction failure."""
        mock_pdfplumber.side_effect = Exception("PDF reading failed")
        
        with pytest.raises(Exception):
            _extract_text_from_pdf(self.sample_pdf_path)
    
    def test_validate_form26as_data_success(self):
        """Test successful data validation."""
        data = Form26ASExtract(
            tds_salary=[TDSRow(tan="ABCD12345E", amount=85000)],
            challans=[ChallanRow(kind="ADVANCE", bsr_code="1234567", amount=10000)],
            confidence=0.8
        )
        
        # Should not raise any exception
        _validate_form26as_data(data)
    
    def test_validate_form26as_data_low_confidence(self):
        """Test validation with low confidence."""
        data = Form26ASExtract(confidence=0.3)
        
        with pytest.raises(ValueError, match="Extraction confidence.*too low"):
            _validate_form26as_data(data)
    
    def test_validate_form26as_data_warnings(self):
        """Test validation that generates warnings."""
        data = Form26ASExtract(
            tds_salary=[TDSRow(tan="INVALID_TAN", amount=85000)],
            challans=[ChallanRow(kind="ADVANCE", bsr_code="INVALID_BSR", amount=10000)],
            confidence=0.8
        )
        
        # Should log warnings but not raise exceptions
        with patch('core.parsers.form26as_llm.logger') as mock_logger:
            _validate_form26as_data(data)
            assert mock_logger.warning.call_count >= 2  # TAN and BSR warnings
    
    def test_enhance_form26as_parser_success(self):
        """Test parser enhancement decorator with successful original parsing."""
        # Mock original parser function
        original_parser = Mock()
        original_parser.return_value = {"result": "success"}
        
        enhanced_parser = enhance_form26as_parser(original_parser)
        
        result = enhanced_parser(self.sample_pdf_path, self.mock_router)
        
        assert result == {"result": "success"}
        original_parser.assert_called_once_with(self.sample_pdf_path)
    
    def test_enhance_form26as_parser_fallback(self):
        """Test parser enhancement decorator with fallback."""
        # Mock original parser failure
        original_parser = Mock()
        original_parser.side_effect = ParseMiss("Original parsing failed")
        
        # Mock fallback success
        with patch('core.parsers.form26as_llm.parse_form26as_with_fallback') as mock_fallback:
            mock_fallback.return_value = {"result": "fallback_success"}
            
            enhanced_parser = enhance_form26as_parser(original_parser)
            result = enhanced_parser(self.sample_pdf_path, self.mock_router)
            
            assert result == {"result": "fallback_success"}
            mock_fallback.assert_called_once_with(self.sample_pdf_path, self.mock_router)
    
    def test_enhance_form26as_parser_no_router(self):
        """Test parser enhancement decorator without router."""
        # Mock original parser failure
        original_parser = Mock()
        original_parser.side_effect = ParseMiss("Original parsing failed")
        
        enhanced_parser = enhance_form26as_parser(original_parser)
        
        with pytest.raises(RuntimeError, match="no LLM router provided"):
            enhanced_parser(self.sample_pdf_path, None)


class TestLLMPromptGeneration:
    """Test cases for LLM prompt generation."""
    
    def test_get_form26as_prompt(self):
        """Test Form 26AS prompt generation."""
        from core.parsers.form26as_llm import _get_form26as_prompt
        
        prompt = _get_form26as_prompt()
        
        # Verify prompt contains key instructions
        assert "Form 26AS" in prompt
        assert "TDS" in prompt
        assert "TCS" in prompt
        assert "ADVANCE" in prompt
        assert "SELF_ASSESSMENT" in prompt
        assert "Form26ASExtract" in prompt
        assert "confidence" in prompt.lower()


class TestIntegrationScenarios:
    """Integration test scenarios for Form 26AS parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_router = Mock()
    
    def test_clean_pdf_deterministic_path(self):
        """Test clean PDF going through deterministic path."""
        # This would be an integration test with actual PDF processing
        # For now, we'll mock the components
        
        with patch('core.parsers.form26as_llm.Form26ASParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.return_value = {
                "form26as_data": {
                    "tds_salary": [{"amount": 85000}],
                    "tds_others": [{"amount": 4500}],
                    "challans": [{"kind": "ADVANCE", "amount": 15000}],
                    "confidence": 1.0
                },
                "metadata": {"parser": "deterministic", "confidence": 1.0}
            }
            mock_parser_class.return_value = mock_parser
            
            result = parse_form26as_with_fallback(Path("clean.pdf"), self.mock_router)
            
            assert result["metadata"]["parser"] == "deterministic"
            assert result["metadata"]["confidence"] == 1.0
    
    def test_odd_pdf_llm_fallback_path(self):
        """Test odd PDF going through LLM fallback path."""
        # Mock deterministic failure and LLM success
        with patch('core.parsers.form26as_llm.Form26ASParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.side_effect = ParseMiss("Complex layout")
            mock_parser_class.return_value = mock_parser
            
            with patch('core.parsers.form26as_llm._extract_text_from_pdf') as mock_extract:
                mock_extract.return_value = "Complex PDF text"
                
                with patch('core.parsers.form26as_llm.parse_form26as_llm') as mock_llm:
                    mock_extract_obj = Form26ASExtract(
                        tds_salary=[TDSRow(amount=85000)],
                        source="LLM_FALLBACK",
                        confidence=0.7
                    )
                    mock_llm.return_value = mock_extract_obj
                    
                    result = parse_form26as_with_fallback(Path("odd.pdf"), self.mock_router)
                    
                    assert result["metadata"]["parser"] == "llm_fallback"
                    assert result["metadata"]["confidence"] == 0.7
    
    def test_both_parsers_fail(self):
        """Test scenario where both deterministic and LLM parsing fail."""
        # Mock deterministic failure
        with patch('core.parsers.form26as_llm.Form26ASParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.parse.side_effect = ParseMiss("Complex layout")
            mock_parser_class.return_value = mock_parser
            
            # Mock text extraction failure
            with patch('core.parsers.form26as_llm._extract_text_from_pdf') as mock_extract:
                mock_extract.side_effect = Exception("PDF corrupted")
                
                with pytest.raises(RuntimeError, match="Failed to extract text"):
                    parse_form26as_with_fallback(Path("corrupted.pdf"), self.mock_router)