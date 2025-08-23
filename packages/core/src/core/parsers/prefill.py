"""Parser for prefill JSON files containing tax return data."""

import json
from pathlib import Path
from typing import Dict, Any, List
from .base import BaseParser


class PrefillParser(BaseParser):
    """Parser for prefill JSON files.
    
    Handles JSON files containing prefilled tax return data,
    typically from previous year returns or third-party sources.
    """
    
    def __init__(self):
        super().__init__("PrefillParser")
    
    @property
    def supported_kinds(self) -> List[str]:
        return ["prefill", "prefill_data"]
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".json"]
    
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse prefill JSON file.
        
        Args:
            path: Path to the prefill JSON file
            
        Returns:
            Dictionary containing structured prefill data
        """
        self._validate_file(path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"File encoding error: {e}")
        
        # Return predictable fixture data for now
        # In a real implementation, this would parse the actual JSON structure
        parsed_data = {
            "personal_info": {
                "pan": raw_data.get("pan", "ABCDE1234F"),
                "name": raw_data.get("name", "John Doe"),
                "date_of_birth": raw_data.get("dob", "1985-01-01"),
                "address": raw_data.get("address", "123 Main Street, City"),
                "mobile": raw_data.get("mobile", "9876543210"),
                "email": raw_data.get("email", "john.doe@example.com"),
            },
            "return_context": {
                "assessment_year": raw_data.get("assessment_year", "2025-26"),
                "form_type": raw_data.get("form_type", "ITR2"),
                "regime": raw_data.get("regime", "new"),
                "revised_return": raw_data.get("revised_return", False),
            },
            "income": {
                "salary": {
                    "gross_salary": float(raw_data.get("salary", {}).get("gross", 800000.0)),
                    "allowances": float(raw_data.get("salary", {}).get("allowances", 50000.0)),
                    "perquisites": float(raw_data.get("salary", {}).get("perquisites", 0.0)),
                },
                "house_property": {
                    "annual_value": float(raw_data.get("house_property", {}).get("annual_value", 0.0)),
                    "municipal_tax": float(raw_data.get("house_property", {}).get("municipal_tax", 0.0)),
                    "interest_on_loan": float(raw_data.get("house_property", {}).get("interest", 0.0)),
                },
                "capital_gains": {
                    "short_term": float(raw_data.get("capital_gains", {}).get("short_term", 0.0)),
                    "long_term": float(raw_data.get("capital_gains", {}).get("long_term", 0.0)),
                },
                "other_sources": {
                    "interest_income": float(raw_data.get("other_income", {}).get("interest", 0.0)),
                    "dividend_income": float(raw_data.get("other_income", {}).get("dividend", 0.0)),
                },
            },
            "deductions": {
                "section_80c": float(raw_data.get("deductions", {}).get("80c", 150000.0)),
                "section_80d": float(raw_data.get("deductions", {}).get("80d", 25000.0)),
                "section_80g": float(raw_data.get("deductions", {}).get("80g", 0.0)),
            },
            "taxes_paid": {
                "tds": float(raw_data.get("taxes", {}).get("tds", 0.0)),
                "advance_tax": float(raw_data.get("taxes", {}).get("advance", 0.0)),
                "self_assessment": float(raw_data.get("taxes", {}).get("self_assessment", 0.0)),
            },
            "metadata": {
                "source": raw_data.get("source", "prefill"),
                "version": raw_data.get("version", "1.0"),
                "created_date": raw_data.get("created_date"),
                **self._get_file_info(path),
            },
        }
        
        return parsed_data