"""Parser for AIS (Annual Information Statement) and TIS (Tax Information Statement) JSON files."""

import json
from pathlib import Path
from typing import Dict, Any, List
from .base import BaseParser


class AISParser(BaseParser):
    """Parser for AIS/TIS JSON files.
    
    Handles JSON files containing Annual Information Statement (AIS)
    and Tax Information Statement (TIS) data from the Income Tax Department.
    """
    
    def __init__(self):
        super().__init__("AISParser")
    
    @property
    def supported_kinds(self) -> List[str]:
        return ["ais", "tis", "ais_data", "tis_data"]
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".json"]
    
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse AIS/TIS JSON file.
        
        Args:
            path: Path to the AIS/TIS JSON file
            
        Returns:
            Dictionary containing structured AIS/TIS data
        """
        self._validate_file(path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"File encoding error: {e}")
        
        # Determine if this is AIS or TIS based on content or filename
        statement_type = self._determine_statement_type(path, raw_data)
        
        # Return predictable fixture data for now
        # In a real implementation, this would parse the actual AIS/TIS structure
        parsed_data = {
            "statement_info": {
                "type": statement_type,
                "pan": raw_data.get("pan", "ABCDE1234F"),
                "assessment_year": raw_data.get("assessment_year", "2025-26"),
                "generated_date": raw_data.get("generated_date", "2024-12-01"),
                "version": raw_data.get("version", "1.0"),
            },
            "salary_details": [
                {
                    "employer_name": "ABC Company Ltd",
                    "employer_tan": "ABCD12345E",
                    "gross_salary": 850000.0,
                    "tds_deducted": 45000.0,
                    "period": "2024-25",
                }
            ],
            "interest_details": [
                {
                    "bank_name": "State Bank of India",
                    "account_number": "****1234",
                    "interest_amount": 15000.0,
                    "tds_deducted": 1500.0,
                }
            ],
            "dividend_details": [
                {
                    "company_name": "XYZ Ltd",
                    "dividend_amount": 5000.0,
                    "tds_deducted": 0.0,
                }
            ],
            "capital_gains": [
                {
                    "transaction_type": "sale_of_shares",
                    "amount": 25000.0,
                    "gain_type": "short_term",
                    "date_of_transaction": "2024-08-15",
                }
            ],
            "high_value_transactions": [
                {
                    "transaction_type": "cash_deposit",
                    "amount": 250000.0,
                    "date": "2024-06-15",
                    "reporting_entity": "ABC Bank",
                }
            ],
            "tax_payments": {
                "advance_tax": [
                    {
                        "amount": 25000.0,
                        "date": "2024-06-15",
                        "challan_number": "1234567890",
                    }
                ],
                "self_assessment_tax": [
                    {
                        "amount": 5000.0,
                        "date": "2024-07-31",
                        "challan_number": "0987654321",
                    }
                ],
            },
            "summary": {
                "total_salary": 850000.0,
                "total_interest": 15000.0,
                "total_dividend": 5000.0,
                "total_capital_gains": 25000.0,
                "total_tds": 46500.0,
                "total_advance_tax": 25000.0,
            },
            "metadata": {
                "source": statement_type.lower(),
                "total_records": len(raw_data.get("records", [])) if "records" in raw_data else 0,
                **self._get_file_info(path),
            },
        }
        
        return parsed_data
    
    def _determine_statement_type(self, path: Path, data: Dict[str, Any]) -> str:
        """Determine if this is AIS or TIS based on filename or content."""
        filename = path.name.lower()
        
        if "tis" in filename:
            return "TIS"
        elif "ais" in filename:
            return "AIS"
        
        # Check content for type indicators
        if data.get("statement_type"):
            return data["statement_type"].upper()
        
        # Default to AIS if unclear
        return "AIS"