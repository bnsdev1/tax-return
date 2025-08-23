"""Privacy controls for redacting PII from text before sending to cloud LLMs."""

import re
from typing import Dict, Tuple


# Regex patterns for Indian PII
PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")
IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
DOB_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b")
MOBILE_PATTERN = re.compile(r"\b[6-9]\d{9}\b")


def redact_text(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Redact PII from text for cloud safety.
    
    Args:
        text: Input text that may contain PII
        
    Returns:
        Tuple of (redacted_text, redaction_counts)
    """
    redacted = text
    counts = {}
    
    # PAN numbers
    pan_matches = PAN_PATTERN.findall(redacted)
    if pan_matches:
        redacted = PAN_PATTERN.sub("<PAN>", redacted)
        counts["PAN"] = len(pan_matches)
    
    # Aadhaar numbers
    aadhaar_matches = AADHAAR_PATTERN.findall(redacted)
    if aadhaar_matches:
        redacted = AADHAAR_PATTERN.sub("<AADHAAR>", redacted)
        counts["AADHAAR"] = len(aadhaar_matches)
    
    # Account numbers
    account_matches = ACCOUNT_PATTERN.findall(redacted)
    if account_matches:
        redacted = ACCOUNT_PATTERN.sub("<ACCT>", redacted)
        counts["ACCOUNT"] = len(account_matches)
    
    # IFSC codes
    ifsc_matches = IFSC_PATTERN.findall(redacted)
    if ifsc_matches:
        redacted = IFSC_PATTERN.sub("<IFSC>", redacted)
        counts["IFSC"] = len(ifsc_matches)
    
    # Date of birth patterns
    dob_matches = DOB_PATTERN.findall(redacted)
    if dob_matches:
        redacted = DOB_PATTERN.sub("<DOB>", redacted)
        counts["DOB"] = len(dob_matches)
    
    # Mobile numbers
    mobile_matches = MOBILE_PATTERN.findall(redacted)
    if mobile_matches:
        redacted = MOBILE_PATTERN.sub("<MOBILE>", redacted)
        counts["MOBILE"] = len(mobile_matches)
    
    return redacted, counts


def should_redact(text: str, cloud_allowed: bool, redact_pii: bool) -> bool:
    """
    Determine if text should be redacted based on settings.
    
    Args:
        text: Input text
        cloud_allowed: Whether cloud providers are allowed
        redact_pii: Whether PII redaction is enabled
        
    Returns:
        True if redaction should be applied
    """
    return cloud_allowed and redact_pii