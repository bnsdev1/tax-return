"""Tests for PII redaction functionality."""

import pytest
from packages.llm.redact import redact_text, should_redact


class TestRedaction:
    """Test PII redaction functionality."""
    
    def test_pan_redaction(self):
        """Test PAN number redaction."""
        text = "My PAN is ABCDE1234F and income is high"
        redacted, counts = redact_text(text)
        
        assert "<PAN>" in redacted
        assert "ABCDE1234F" not in redacted
        assert counts["PAN"] == 1
    
    def test_aadhaar_redaction(self):
        """Test Aadhaar number redaction."""
        text = "Aadhaar: 1234 5678 9012 is my ID"
        redacted, counts = redact_text(text)
        
        assert "<AADHAAR>" in redacted
        assert "1234 5678 9012" not in redacted
        assert counts["AADHAAR"] == 1
    
    def test_account_number_redaction(self):
        """Test account number redaction."""
        text = "Account number 123456789012 for salary"
        redacted, counts = redact_text(text)
        
        assert "<ACCT>" in redacted
        assert "123456789012" not in redacted
        assert counts["ACCOUNT"] == 1
    
    def test_ifsc_redaction(self):
        """Test IFSC code redaction."""
        text = "IFSC code HDFC0001234 for transfer"
        redacted, counts = redact_text(text)
        
        assert "<IFSC>" in redacted
        assert "HDFC0001234" not in redacted
        assert counts["IFSC"] == 1
    
    def test_mobile_redaction(self):
        """Test mobile number redaction."""
        text = "Call me at 9876543210 for details"
        redacted, counts = redact_text(text)
        
        assert "<MOBILE>" in redacted
        assert "9876543210" not in redacted
        assert counts["MOBILE"] == 1
    
    def test_dob_redaction(self):
        """Test date of birth redaction."""
        text = "Born on 15/08/1990 in Mumbai"
        redacted, counts = redact_text(text)
        
        assert "<DOB>" in redacted
        assert "15/08/1990" not in redacted
        assert counts["DOB"] == 1
    
    def test_multiple_pii_redaction(self):
        """Test redaction of multiple PII types."""
        text = "PAN: ABCDE1234F, Aadhaar: 1234 5678 9012, Account: 123456789012"
        redacted, counts = redact_text(text)
        
        assert "<PAN>" in redacted
        assert "<AADHAAR>" in redacted
        assert "<ACCT>" in redacted
        assert counts["PAN"] == 1
        assert counts["AADHAAR"] == 1
        assert counts["ACCOUNT"] == 1
    
    def test_no_pii_text(self):
        """Test text with no PII."""
        text = "This is a normal text without any sensitive information"
        redacted, counts = redact_text(text)
        
        assert redacted == text
        assert len(counts) == 0
    
    def test_should_redact_logic(self):
        """Test redaction decision logic."""
        # Should redact when cloud allowed and PII redaction enabled
        assert should_redact("test", cloud_allowed=True, redact_pii=True) == True
        
        # Should not redact when cloud not allowed
        assert should_redact("test", cloud_allowed=False, redact_pii=True) == False
        
        # Should not redact when PII redaction disabled
        assert should_redact("test", cloud_allowed=True, redact_pii=False) == False
        
        # Should not redact when both disabled
        assert should_redact("test", cloud_allowed=False, redact_pii=False) == False