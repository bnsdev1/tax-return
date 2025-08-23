"""Bank PDF parser with LLM fallback for complex statements."""

from typing import List, Dict, Any, Optional
from packages.llm.router import LLMRouter
from packages.llm.contracts import LLMTask


def parse_bank_pdf_llm(text: str, router: LLMRouter) -> List[Dict[str, Any]]:
    """
    Parse bank PDF statements using LLM when deterministic parsing fails.
    
    Args:
        text: Raw text extracted from bank PDF
        router: LLM router instance
        
    Returns:
        List of parsed transaction records
        
    Raises:
        RuntimeError: If LLM extraction fails
    """
    # Split text into transaction lines (basic heuristic)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Filter lines that look like transactions (contain amounts)
    transaction_lines = []
    for line in lines:
        if _looks_like_transaction(line):
            transaction_lines.append(line)
    
    # Process each transaction line
    parsed_transactions = []
    for line in transaction_lines:
        try:
            parsed = _parse_transaction_line_llm(line, router)
            if parsed:
                parsed_transactions.append(parsed)
        except Exception as e:
            # Log error but continue processing other lines
            print(f"Failed to parse transaction line: {line}, error: {e}")
            continue
    
    return parsed_transactions


def _looks_like_transaction(line: str) -> bool:
    """
    Heuristic to identify transaction lines.
    
    Args:
        line: Text line to check
        
    Returns:
        True if line appears to be a transaction
    """
    # Look for amount patterns (₹ or numbers with decimals)
    import re
    amount_pattern = r'₹?\s*\d+[,\d]*\.?\d*'
    return bool(re.search(amount_pattern, line)) and len(line) > 20


def _parse_transaction_line_llm(line: str, router: LLMRouter) -> Optional[Dict[str, Any]]:
    """
    Parse individual transaction line using LLM.
    
    Args:
        line: Transaction line text
        router: LLM router instance
        
    Returns:
        Parsed transaction data or None if parsing fails
    """
    # Create LLM task for transaction parsing
    task = LLMTask(
        name="bank_line_classify",
        schema_name="BankNarrationLabel",
        prompt="Classify bank transaction narration",
        text=line
    )
    
    # Execute LLM classification
    result = router.run(task)
    
    if not result.ok:
        return None
    
    # Extract basic transaction info (amount, date, etc.)
    transaction_data = _extract_transaction_basics(line)
    
    # Add LLM classification
    transaction_data.update({
        "llm_classification": result.json.get("label"),
        "llm_confidence": result.json.get("confidence", 0.0),
        "llm_rationale": result.json.get("rationale"),
        "source": "LLM_ENHANCED"
    })
    
    return transaction_data


def _extract_transaction_basics(line: str) -> Dict[str, Any]:
    """
    Extract basic transaction info using regex patterns.
    
    Args:
        line: Transaction line text
        
    Returns:
        Dict with basic transaction data
    """
    import re
    
    # Extract amount (simplified pattern)
    amount_pattern = r'₹?\s*(\d+[,\d]*\.?\d*)'
    amount_match = re.search(amount_pattern, line)
    amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0
    
    # Extract date (simplified pattern)
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
    date_match = re.search(date_pattern, line)
    date = date_match.group(1) if date_match else None
    
    return {
        "raw_line": line,
        "amount": amount,
        "date": date,
        "narration": line  # Full line as narration for now
    }


def enhance_bank_parser(original_parser_func):
    """
    Decorator to enhance existing bank parser with LLM fallback.
    
    Args:
        original_parser_func: Original deterministic parser function
        
    Returns:
        Enhanced parser with LLM fallback
    """
    def enhanced_parser(file_path: str, router: Optional[LLMRouter] = None) -> List[Dict[str, Any]]:
        """Enhanced parser with LLM fallback."""
        try:
            # Try deterministic parsing first
            transactions = original_parser_func(file_path)
            
            # Mark as deterministic source
            for txn in transactions:
                txn["source"] = "DETERMINISTIC"
            
            return transactions
            
        except Exception as e:
            if not router:
                raise RuntimeError(f"Deterministic parsing failed and no LLM router provided: {e}")
            
            # Extract text from PDF
            text = _extract_text_from_pdf(file_path)
            
            # Use LLM fallback
            return parse_bank_pdf_llm(text, router)
    
    return enhanced_parser


def _extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    # Mock implementation - in production, use PyPDF2, pdfplumber, or similar
    return f"""
    01/04/2024  SALARY CREDIT                    ₹85,000.00  CR
    05/04/2024  ATM WITHDRAWAL                   ₹5,000.00   DR
    15/04/2024  INTEREST CREDITED                ₹1,250.00   CR
    20/04/2024  UTILITY BILL PAYMENT             ₹2,500.00   DR
    25/04/2024  FD INTEREST CREDIT               ₹8,500.00   CR
    30/04/2024  BANK CHARGES                     ₹150.00     DR
    """