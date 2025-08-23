"""Parser for Form 16B PDF files (TDS certificate for property transactions)."""

from pathlib import Path
from typing import Dict, Any, List
from .base import BaseParser


class Form16BParser(BaseParser):
    """Parser for Form 16B PDF files.
    
    Handles PDF files containing Form 16B - TDS certificate for
    property transactions under Section 194IA.
    
    Note: This is a stub implementation that returns fixture data.
    A real implementation would use PDF parsing libraries like PyPDF2,
    pdfplumber, or OCR tools to extract actual data.
    """
    
    def __init__(self):
        super().__init__("Form16BParser")
    
    @property
    def supported_kinds(self) -> List[str]:
        return ["form16b", "form_16b", "tds_certificate"]
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]
    
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse Form 16B PDF file.
        
        Args:
            path: Path to the Form 16B PDF file
            
        Returns:
            Dictionary containing structured Form 16B data
        """
        self._validate_file(path)
        
        # For now, return predictable fixture data
        # In a real implementation, this would:
        # 1. Use PDF parsing library to extract text
        # 2. Use regex patterns to find specific fields
        # 3. Validate TAN, PAN formats
        # 4. Parse dates and amounts
        
        parsed_data = {
            "certificate_info": {
                "form_type": "Form 16B",
                "certificate_number": "16B/2024-25/001234",
                "financial_year": "2024-25",
                "quarter": "Q3",
                "date_of_issue": "2024-12-15",
            },
            "deductor_details": {
                "name": "ABC Property Developers Ltd",
                "tan": "ABCD12345E",
                "address": "123 Business District, Mumbai - 400001",
                "pan": "ABCDE1234F",
            },
            "deductee_details": {
                "name": "John Doe",
                "pan": "FGHIJ5678K",
                "address": "456 Residential Area, Mumbai - 400002",
            },
            "property_details": {
                "property_address": "Plot No. 789, Sector 15, Navi Mumbai",
                "property_type": "Residential Flat",
                "agreement_date": "2024-10-15",
                "registration_date": "2024-11-01",
                "stamp_duty_value": 5000000.0,
            },
            "payment_details": {
                "total_consideration": 4500000.0,
                "tds_rate": 1.0,  # 1% under Section 194IA
                "tds_amount": 45000.0,
                "payment_date": "2024-11-01",
                "challan_number": "1234567890123456",
                "bank_name": "State Bank of India",
                "bsr_code": "1234567",
            },
            "tax_deposit_details": {
                "date_of_deposit": "2024-11-05",
                "challan_serial_number": "12345",
                "amount_deposited": 45000.0,
                "book_identification_number": "BIN123456",
            },
            "verification": {
                "place": "Mumbai",
                "date": "2024-12-15",
                "authorized_signatory": "Authorized Signatory",
                "designation": "Company Secretary",
            },
            "summary": {
                "total_tds_deducted": 45000.0,
                "applicable_section": "194IA",
                "nature_of_payment": "Payment for immovable property",
            },
            "metadata": {
                "source": "form16b_pdf",
                "extraction_method": "stub_parser",
                "confidence_score": 1.0,  # Stub data is 100% confident
                **self._get_file_info(path),
            },
        }
        
        return parsed_data
    
    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF file.
        
        This is a placeholder method. In a real implementation,
        this would use libraries like:
        - PyPDF2 or PyPDF4 for simple text extraction
        - pdfplumber for more advanced parsing
        - OCR tools like Tesseract for scanned PDFs
        """
        # Placeholder implementation
        return "Form 16B stub text content"
    
    def _parse_certificate_number(self, text: str) -> str:
        """Extract certificate number from PDF text."""
        # Placeholder - would use regex patterns
        return "16B/2024-25/001234"
    
    def _parse_amounts(self, text: str) -> Dict[str, float]:
        """Extract monetary amounts from PDF text."""
        # Placeholder - would use regex patterns for currency amounts
        return {
            "total_consideration": 4500000.0,
            "tds_amount": 45000.0,
        }