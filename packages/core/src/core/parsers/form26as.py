"""Form 26AS deterministic parser with table extraction."""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import pdfplumber
from pydantic import BaseModel, Field, field_validator

from .base import BaseParser

logger = logging.getLogger(__name__)


class TDSRow(BaseModel):
    """TDS row data from Form 26AS."""
    tan: Optional[str] = None
    deductor: Optional[str] = None
    section: Optional[str] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    amount: int = Field(ge=0)  # Amount in rupees
    
    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        """Parse amount from various formats."""
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[₹,\s]', '', v)
            try:
                return int(float(cleaned))
            except (ValueError, InvalidOperation):
                return 0
        return 0


class ChallanRow(BaseModel):
    """Challan row data from Form 26AS."""
    kind: str = Field(pattern=r'^(ADVANCE|SELF_ASSESSMENT)$')
    bsr_code: Optional[str] = None
    challan_no: Optional[str] = None
    paid_on: Optional[date] = None
    amount: int = Field(ge=0)  # Amount in rupees
    
    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        """Parse amount from various formats."""
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[₹,\s]', '', v)
            try:
                return int(float(cleaned))
            except (ValueError, InvalidOperation):
                return 0
        return 0


class Form26ASExtract(BaseModel):
    """Complete Form 26AS extraction result."""
    tds_salary: List[TDSRow] = Field(default_factory=list)
    tds_others: List[TDSRow] = Field(default_factory=list)
    tcs: List[TDSRow] = Field(default_factory=list)
    challans: List[ChallanRow] = Field(default_factory=list)
    totals: Dict[str, int] = Field(default_factory=dict)
    source: str = "DETERMINISTIC"
    confidence: float = Field(ge=0, le=1, default=1.0)


class ParseMiss(Exception):
    """Exception raised when deterministic parsing fails."""
    pass


class Form26ASParser(BaseParser):
    """Deterministic Form 26AS parser with table extraction."""
    
    def __init__(self):
        super().__init__("Form26ASParser")
        self.section_patterns = {
            'tds_salary': [
                r'TDS.*SALARY',
                r'PART.*A.*SALARY',
                r'SECTION.*192'
            ],
            'tds_others': [
                r'TDS.*(?:OTHER|NON.?SALARY)',
                r'PART.*B.*TDS',
                r'SECTION.*(?:194|195|196)'
            ],
            'tcs': [
                r'TCS.*COLLECTED',
                r'PART.*C.*TCS',
                r'TAX.*COLLECTED'
            ],
            'challans': [
                r'ADVANCE.*TAX',
                r'SELF.*ASSESSMENT',
                r'CHALLAN',
                r'PART.*D'
            ]
        }
    
    @property
    def supported_kinds(self) -> List[str]:
        return ["form26as", "form_26as", "26as"]
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]
    
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse Form 26AS PDF using deterministic table extraction."""
        self._validate_file(path)
        
        try:
            with pdfplumber.open(path) as pdf:
                # Extract text from all pages
                full_text = ""
                tables = []
                
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                # Parse sections
                extract = self._parse_sections(full_text, tables)
                
                # Validate invariants
                self._validate_invariants(extract)
                
                return {
                    "form26as_data": extract.model_dump(),
                    "metadata": {
                        "source": "form26as",
                        "parser": "deterministic",
                        "confidence": extract.confidence,
                        **self._get_file_info(path)
                    }
                }
                
        except Exception as e:
            logger.error(f"Deterministic parsing failed for {path}: {e}")
            raise ParseMiss(f"Table extraction failed: {e}")
    
    def _parse_sections(self, text: str, tables: List[List[List[str]]]) -> Form26ASExtract:
        """Parse different sections from text and tables."""
        extract = Form26ASExtract()
        
        # Detect sections in text
        sections = self._detect_sections(text)
        
        # Parse tables for each section
        for section_name, section_text in sections.items():
            if section_name == 'tds_salary':
                extract.tds_salary = self._parse_tds_section(section_text, tables, 'salary')
            elif section_name == 'tds_others':
                extract.tds_others = self._parse_tds_section(section_text, tables, 'others')
            elif section_name == 'tcs':
                extract.tcs = self._parse_tds_section(section_text, tables, 'tcs')
            elif section_name == 'challans':
                extract.challans = self._parse_challan_section(section_text, tables)
        
        # Extract totals
        extract.totals = self._extract_totals(text)
        
        return extract
    
    def _detect_sections(self, text: str) -> Dict[str, str]:
        """Detect different sections in the text."""
        sections = {}
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line_upper = line.upper()
            
            # Check for section headers
            for section_name, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line_upper):
                        # Save previous section
                        if current_section and section_content:
                            sections[current_section] = '\n'.join(section_content)
                        
                        # Start new section
                        current_section = section_name
                        section_content = [line]
                        break
                else:
                    continue
                break
            else:
                # Add to current section
                if current_section:
                    section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    def _parse_tds_section(self, section_text: str, tables: List[List[List[str]]], section_type: str) -> List[TDSRow]:
        """Parse TDS section from text and tables."""
        tds_rows = []
        
        # Try to find relevant table
        relevant_table = self._find_relevant_table(section_text, tables)
        
        if relevant_table:
            # Parse table rows
            headers = self._normalize_headers(relevant_table[0] if relevant_table else [])
            
            for row in relevant_table[1:]:
                if len(row) < 3:  # Skip incomplete rows
                    continue
                
                try:
                    tds_row = self._parse_tds_row(row, headers)
                    if tds_row and tds_row.amount > 0:
                        tds_rows.append(tds_row)
                except Exception as e:
                    logger.warning(f"Failed to parse TDS row {row}: {e}")
                    continue
        
        # Fallback: parse from text patterns
        if not tds_rows:
            tds_rows = self._parse_tds_from_text(section_text)
        
        return tds_rows
    
    def _parse_challan_section(self, section_text: str, tables: List[List[List[str]]]) -> List[ChallanRow]:
        """Parse challan section from text and tables."""
        challan_rows = []
        
        # Try to find relevant table
        relevant_table = self._find_relevant_table(section_text, tables)
        
        if relevant_table:
            headers = self._normalize_headers(relevant_table[0] if relevant_table else [])
            
            for row in relevant_table[1:]:
                if len(row) < 3:
                    continue
                
                try:
                    challan_row = self._parse_challan_row(row, headers, section_text)
                    if challan_row and challan_row.amount > 0:
                        challan_rows.append(challan_row)
                except Exception as e:
                    logger.warning(f"Failed to parse challan row {row}: {e}")
                    continue
        
        # Fallback: parse from text patterns
        if not challan_rows:
            challan_rows = self._parse_challans_from_text(section_text)
        
        return challan_rows
    
    def _find_relevant_table(self, section_text: str, tables: List[List[List[str]]]) -> Optional[List[List[str]]]:
        """Find the most relevant table for a section."""
        if not tables:
            return None
        
        # Simple heuristic: find table with most matching keywords
        best_table = None
        best_score = 0
        
        keywords = ['TAN', 'DEDUCTOR', 'AMOUNT', 'CHALLAN', 'BSR', 'DATE']
        
        for table in tables:
            if not table or not table[0]:
                continue
            
            # Score based on header matches
            header_text = ' '.join(table[0]).upper()
            score = sum(1 for keyword in keywords if keyword in header_text)
            
            if score > best_score:
                best_score = score
                best_table = table
        
        return best_table
    
    def _normalize_headers(self, headers: List[str]) -> Dict[str, int]:
        """Normalize table headers to standard column indices."""
        header_map = {}
        
        for i, header in enumerate(headers):
            header_upper = header.upper()
            
            if 'TAN' in header_upper:
                header_map['tan'] = i
            elif 'DEDUCTOR' in header_upper or 'NAME' in header_upper:
                header_map['deductor'] = i
            elif 'SECTION' in header_upper:
                header_map['section'] = i
            elif 'PERIOD' in header_upper and 'FROM' in header_upper:
                header_map['period_from'] = i
            elif 'PERIOD' in header_upper and 'TO' in header_upper:
                header_map['period_to'] = i
            elif 'AMOUNT' in header_upper or '₹' in header_upper:
                header_map['amount'] = i
            elif 'BSR' in header_upper:
                header_map['bsr_code'] = i
            elif 'CHALLAN' in header_upper:
                header_map['challan_no'] = i
            elif 'DATE' in header_upper or 'PAID' in header_upper:
                header_map['paid_on'] = i
        
        return header_map
    
    def _parse_tds_row(self, row: List[str], headers: Dict[str, int]) -> Optional[TDSRow]:
        """Parse a single TDS row from table data."""
        try:
            data = {}
            
            if 'tan' in headers and headers['tan'] < len(row):
                data['tan'] = row[headers['tan']].strip()
            
            if 'deductor' in headers and headers['deductor'] < len(row):
                data['deductor'] = row[headers['deductor']].strip()
            
            if 'section' in headers and headers['section'] < len(row):
                data['section'] = row[headers['section']].strip()
            
            if 'period_from' in headers and headers['period_from'] < len(row):
                data['period_from'] = self._parse_date(row[headers['period_from']])
            
            if 'period_to' in headers and headers['period_to'] < len(row):
                data['period_to'] = self._parse_date(row[headers['period_to']])
            
            if 'amount' in headers and headers['amount'] < len(row):
                data['amount'] = row[headers['amount']].strip()
            
            return TDSRow(**data)
            
        except Exception as e:
            logger.warning(f"Failed to parse TDS row: {e}")
            return None
    
    def _parse_challan_row(self, row: List[str], headers: Dict[str, int], section_text: str) -> Optional[ChallanRow]:
        """Parse a single challan row from table data."""
        try:
            data = {}
            
            # Determine challan kind from section context
            if 'ADVANCE' in section_text.upper():
                data['kind'] = 'ADVANCE'
            elif 'SELF' in section_text.upper():
                data['kind'] = 'SELF_ASSESSMENT'
            else:
                data['kind'] = 'ADVANCE'  # Default
            
            if 'bsr_code' in headers and headers['bsr_code'] < len(row):
                data['bsr_code'] = row[headers['bsr_code']].strip()
            
            if 'challan_no' in headers and headers['challan_no'] < len(row):
                data['challan_no'] = row[headers['challan_no']].strip()
            
            if 'paid_on' in headers and headers['paid_on'] < len(row):
                data['paid_on'] = self._parse_date(row[headers['paid_on']])
            
            if 'amount' in headers and headers['amount'] < len(row):
                data['amount'] = row[headers['amount']].strip()
            
            return ChallanRow(**data)
            
        except Exception as e:
            logger.warning(f"Failed to parse challan row: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date from various formats."""
        if not date_str or not date_str.strip():
            return None
        
        date_str = date_str.strip()
        
        # Common date formats in Form 26AS
        formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y-%m-%d',
            '%d/%m/%y',
            '%d-%m-%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_tds_from_text(self, text: str) -> List[TDSRow]:
        """Fallback: parse TDS from text patterns."""
        tds_rows = []
        
        # Look for amount patterns
        amount_pattern = r'₹\s*([0-9,]+)'
        amounts = re.findall(amount_pattern, text)
        
        for amount_str in amounts:
            try:
                amount = int(amount_str.replace(',', ''))
                if amount > 0:
                    tds_rows.append(TDSRow(amount=amount))
            except ValueError:
                continue
        
        return tds_rows
    
    def _parse_challans_from_text(self, text: str) -> List[ChallanRow]:
        """Fallback: parse challans from text patterns."""
        challan_rows = []
        
        # Look for BSR code and amount patterns
        bsr_pattern = r'BSR[:\s]*([0-9]+)'
        amount_pattern = r'₹\s*([0-9,]+)'
        
        bsr_codes = re.findall(bsr_pattern, text)
        amounts = re.findall(amount_pattern, text)
        
        # Determine kind from text
        kind = 'ADVANCE' if 'ADVANCE' in text.upper() else 'SELF_ASSESSMENT'
        
        for i, amount_str in enumerate(amounts):
            try:
                amount = int(amount_str.replace(',', ''))
                if amount > 0:
                    data = {
                        'kind': kind,
                        'amount': amount
                    }
                    if i < len(bsr_codes):
                        data['bsr_code'] = bsr_codes[i]
                    
                    challan_rows.append(ChallanRow(**data))
            except ValueError:
                continue
        
        return challan_rows
    
    def _extract_totals(self, text: str) -> Dict[str, int]:
        """Extract section totals from text."""
        totals = {}
        
        # Look for total patterns
        total_patterns = [
            (r'TOTAL.*TDS.*SALARY[:\s]*₹\s*([0-9,]+)', 'tds_salary_total'),
            (r'TOTAL.*TDS.*OTHER[:\s]*₹\s*([0-9,]+)', 'tds_others_total'),
            (r'TOTAL.*TCS[:\s]*₹\s*([0-9,]+)', 'tcs_total'),
            (r'TOTAL.*ADVANCE[:\s]*₹\s*([0-9,]+)', 'advance_tax_total'),
            (r'TOTAL.*SELF.*ASSESSMENT[:\s]*₹\s*([0-9,]+)', 'self_assessment_total'),
        ]
        
        for pattern, key in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    totals[key] = int(matches[0].replace(',', ''))
                except ValueError:
                    continue
        
        return totals
    
    def _validate_invariants(self, extract: Form26ASExtract) -> None:
        """Validate data invariants."""
        # Check per-section sums against displayed totals
        if extract.totals.get('tds_salary_total'):
            calculated_total = sum(row.amount for row in extract.tds_salary)
            displayed_total = extract.totals['tds_salary_total']
            
            if abs(calculated_total - displayed_total) > 1:  # ₹1 tolerance
                logger.warning(f"TDS salary total mismatch: calculated={calculated_total}, displayed={displayed_total}")
        
        if extract.totals.get('tds_others_total'):
            calculated_total = sum(row.amount for row in extract.tds_others)
            displayed_total = extract.totals['tds_others_total']
            
            if abs(calculated_total - displayed_total) > 1:
                logger.warning(f"TDS others total mismatch: calculated={calculated_total}, displayed={displayed_total}")
        
        # Validate all amounts are integers (₹1 rounding)
        all_amounts = []
        all_amounts.extend([row.amount for row in extract.tds_salary])
        all_amounts.extend([row.amount for row in extract.tds_others])
        all_amounts.extend([row.amount for row in extract.tcs])
        all_amounts.extend([row.amount for row in extract.challans])
        
        for amount in all_amounts:
            if not isinstance(amount, int):
                raise ValueError(f"Amount must be integer: {amount}")
        
        # Validate dates
        all_dates = []
        for row in extract.tds_salary + extract.tds_others + extract.tcs:
            if row.period_from:
                all_dates.append(row.period_from)
            if row.period_to:
                all_dates.append(row.period_to)
        
        for row in extract.challans:
            if row.paid_on:
                all_dates.append(row.paid_on)
        
        for dt in all_dates:
            if not isinstance(dt, date):
                raise ValueError(f"Invalid date: {dt}")