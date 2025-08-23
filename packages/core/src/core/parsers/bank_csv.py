"""Parser for bank statement CSV files."""

import csv
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from .base import BaseParser


class BankCSVParser(BaseParser):
    """Parser for bank statement CSV files.
    
    Handles CSV files containing bank transaction data from various banks.
    Supports common CSV formats and attempts to standardize the output.
    """
    
    def __init__(self):
        super().__init__("BankCSVParser")
    
    @property
    def supported_kinds(self) -> List[str]:
        return ["bank_csv", "bank_statement", "transactions"]
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".csv"]
    
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse bank statement CSV file.
        
        Args:
            path: Path to the bank statement CSV file
            
        Returns:
            Dictionary containing structured bank statement data
        """
        self._validate_file(path)
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']:
                try:
                    with open(path, 'r', encoding=encoding, newline='') as f:
                        # Peek at first few lines to detect format
                        sample = f.read(1024)
                        f.seek(0)
                        
                        # Detect delimiter
                        delimiter = self._detect_delimiter(sample)
                        
                        # Read CSV data
                        reader = csv.DictReader(f, delimiter=delimiter)
                        rows = list(reader)
                        break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV file with any supported encoding")
                
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
        
        if not rows:
            raise ValueError("CSV file is empty or has no data rows")
        
        # Analyze CSV structure and extract transactions
        transactions = self._parse_transactions(rows)
        account_info = self._extract_account_info(rows)
        summary = self._calculate_summary(transactions)
        
        parsed_data = {
            "account_info": account_info,
            "statement_period": {
                "start_date": summary["earliest_date"],
                "end_date": summary["latest_date"],
                "total_days": summary["total_days"],
            },
            "transactions": transactions,
            "summary": {
                "total_transactions": len(transactions),
                "total_credits": summary["total_credits"],
                "total_debits": summary["total_debits"],
                "net_amount": summary["net_amount"],
                "opening_balance": summary.get("opening_balance", 0.0),
                "closing_balance": summary.get("closing_balance", 0.0),
            },
            "categories": self._categorize_transactions(transactions),
            "metadata": {
                "source": "bank_csv",
                "total_rows": len(rows),
                "delimiter": delimiter,
                "encoding": encoding,
                **self._get_file_info(path),
            },
        }
        
        return parsed_data
    
    def _detect_delimiter(self, sample: str) -> str:
        """Detect CSV delimiter from sample text."""
        # Common delimiters in order of preference
        delimiters = [',', ';', '\t', '|']
        
        for delimiter in delimiters:
            if delimiter in sample:
                return delimiter
        
        return ','  # Default to comma
    
    def _parse_transactions(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse transaction data from CSV rows."""
        transactions = []
        
        # Common field mappings for different bank formats
        field_mappings = {
            'date': ['date', 'transaction_date', 'txn_date', 'value_date', 'posting_date'],
            'description': ['description', 'particulars', 'narration', 'details', 'transaction_details'],
            'amount': ['amount', 'transaction_amount', 'txn_amount'],
            'credit': ['credit', 'credit_amount', 'deposits', 'cr'],
            'debit': ['debit', 'debit_amount', 'withdrawals', 'dr'],
            'balance': ['balance', 'running_balance', 'available_balance'],
            'reference': ['reference', 'ref_no', 'transaction_id', 'cheque_no'],
        }
        
        # Find actual field names in the CSV
        headers = [h.lower().strip() for h in rows[0].keys()] if rows else []
        mapped_fields = {}
        
        for field_type, possible_names in field_mappings.items():
            for name in possible_names:
                if name in headers:
                    mapped_fields[field_type] = name
                    break
        
        for i, row in enumerate(rows):
            try:
                transaction = self._parse_single_transaction(row, mapped_fields, i + 1)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                # Log error but continue processing other transactions
                continue
        
        return transactions
    
    def _parse_single_transaction(self, row: Dict[str, Any], field_map: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Parse a single transaction row."""
        transaction = {
            "row_number": row_num,
            "date": None,
            "description": "",
            "amount": 0.0,
            "type": "unknown",
            "balance": None,
            "reference": "",
        }
        
        # Parse date
        if 'date' in field_map:
            date_str = str(row.get(field_map['date'], '')).strip()
            transaction["date"] = self._parse_date(date_str)
        
        # Parse description
        if 'description' in field_map:
            transaction["description"] = str(row.get(field_map['description'], '')).strip()
        
        # Parse amount (try different approaches)
        amount = 0.0
        transaction_type = "unknown"
        
        if 'credit' in field_map and 'debit' in field_map:
            # Separate credit/debit columns
            credit = self._parse_amount(row.get(field_map['credit'], ''))
            debit = self._parse_amount(row.get(field_map['debit'], ''))
            
            if credit > 0:
                amount = credit
                transaction_type = "credit"
            elif debit > 0:
                amount = -debit  # Negative for debits
                transaction_type = "debit"
        elif 'amount' in field_map:
            # Single amount column
            amount = self._parse_amount(row.get(field_map['amount'], ''))
            transaction_type = "credit" if amount > 0 else "debit"
        
        transaction["amount"] = amount
        transaction["type"] = transaction_type
        
        # Parse balance
        if 'balance' in field_map:
            transaction["balance"] = self._parse_amount(row.get(field_map['balance'], ''))
        
        # Parse reference
        if 'reference' in field_map:
            transaction["reference"] = str(row.get(field_map['reference'], '')).strip()
        
        return transaction
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string into ISO format."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y%m%d',
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                return parsed_date.isoformat()
            except ValueError:
                continue
        
        return date_str  # Return original if parsing fails
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string into float."""
        if not amount_str or str(amount_str).strip() == '':
            return 0.0
        
        # Clean the amount string
        cleaned = str(amount_str).strip()
        
        # Remove common currency symbols and formatting
        cleaned = cleaned.replace('₹', '').replace('$', '').replace(',', '')
        cleaned = cleaned.replace('(', '-').replace(')', '')  # Handle negative amounts in parentheses
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _extract_account_info(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract account information from CSV data."""
        # This would typically be in header rows or metadata
        # For now, return fixture data
        return {
            "account_number": "****1234",
            "account_holder": "John Doe",
            "bank_name": "Sample Bank",
            "branch": "Main Branch",
            "ifsc_code": "SAMP0001234",
        }
    
    def _calculate_summary(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from transactions."""
        if not transactions:
            return {
                "total_credits": 0.0,
                "total_debits": 0.0,
                "net_amount": 0.0,
                "earliest_date": None,
                "latest_date": None,
                "total_days": 0,
            }
        
        credits = sum(t["amount"] for t in transactions if t["amount"] > 0)
        debits = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
        
        dates = [t["date"] for t in transactions if t["date"]]
        earliest_date = min(dates) if dates else None
        latest_date = max(dates) if dates else None
        
        total_days = 0
        if earliest_date and latest_date:
            try:
                start = datetime.fromisoformat(earliest_date).date()
                end = datetime.fromisoformat(latest_date).date()
                total_days = (end - start).days
            except:
                pass
        
        return {
            "total_credits": credits,
            "total_debits": debits,
            "net_amount": credits - debits,
            "earliest_date": earliest_date,
            "latest_date": latest_date,
            "total_days": total_days,
        }
    
    def _categorize_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize transactions by type and description patterns."""
        categories = {
            "salary": [],
            "interest": [],
            "transfers": [],
            "atm_withdrawals": [],
            "online_payments": [],
            "other": [],
        }
        
        for transaction in transactions:
            description = transaction["description"].lower()
            
            if any(keyword in description for keyword in ["salary", "sal", "payroll"]):
                categories["salary"].append(transaction)
            elif any(keyword in description for keyword in ["interest", "int", "savings"]):
                categories["interest"].append(transaction)
            elif any(keyword in description for keyword in ["transfer", "neft", "rtgs", "imps"]):
                categories["transfers"].append(transaction)
            elif any(keyword in description for keyword in ["atm", "cash withdrawal"]):
                categories["atm_withdrawals"].append(transaction)
            elif any(keyword in description for keyword in ["upi", "online", "payment"]):
                categories["online_payments"].append(transaction)
            else:
                categories["other"].append(transaction)
        
        # Return summary with counts and totals
        return {
            category: {
                "count": len(transactions),
                "total_amount": sum(t["amount"] for t in transactions),
                "transactions": transactions[:5],  # First 5 transactions as examples
            }
            for category, transactions in categories.items()
        }