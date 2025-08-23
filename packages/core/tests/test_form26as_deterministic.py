"""Tests for Form 26AS deterministic parser."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import date

from core.parsers.form26as import (
    Form26ASParser, 
    Form26ASExtract, 
    TDSRow, 
    ChallanRow, 
    ParseMiss
)


class TestForm26ASParser:
    """Test cases for Form 26AS deterministic parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = Form26ASParser()
        self.sample_pdf_path = Path("fixtures/26AS_sample_clean.pdf")
    
    def test_parser_properties(self):
        """Test parser properties."""
        assert self.parser.name == "Form26ASParser"
        assert "form26as" in self.parser.supported_kinds
        assert "form_26as" in self.parser.supported_kinds
        assert "26as" in self.parser.supported_kinds
        assert ".pdf" in self.parser.supported_extensions
    
    def test_supports_method(self):
        """Test supports method."""
        # Create a mock PDF file
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.suffix = ".pdf"
        
        assert self.parser.supports("form26as", mock_path)
        assert self.parser.supports("form_26as", mock_path)
        assert self.parser.supports("26as", mock_path)
        assert not self.parser.supports("other", mock_path)
        assert not self.parser.supports("form26as", Mock(suffix=".txt", exists=lambda: True))
    
    @patch('pdfplumber.open')
    def test_parse_clean_pdf_success(self, mock_pdfplumber):
        """Test parsing a clean, well-structured PDF."""
        # Mock PDF content
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        FORM 26AS - TAX CREDIT STATEMENT
        Assessment Year: 2025-26
        PAN: ABCDE1234F
        
        PART A - TDS ON SALARY
        TAN         DEDUCTOR NAME           SECTION  PERIOD FROM  PERIOD TO    AMOUNT
        ABCD12345E  ABC COMPANY LTD         192      01/04/2024   31/03/2025   85,000
        
        TOTAL TDS ON SALARY: ₹85,000
        
        PART B - TDS ON OTHER THAN SALARY  
        TAN         DEDUCTOR NAME           SECTION  PERIOD FROM  PERIOD TO    AMOUNT
        BANK12345E  XYZ BANK LTD           194A     01/04/2024   31/03/2025   4,500
        
        TOTAL TDS ON OTHER THAN SALARY: ₹4,500
        
        PART D - ADVANCE TAX
        BSR CODE    CHALLAN NO      DATE PAID    AMOUNT
        1234567     123456789       15/06/2024   10,000
        1234567     987654321       15/09/2024   5,000
        
        TOTAL ADVANCE TAX: ₹15,000
        """
        
        mock_page.extract_tables.return_value = [
            [
                ['TAN', 'DEDUCTOR NAME', 'SECTION', 'PERIOD FROM', 'PERIOD TO', 'AMOUNT'],
                ['ABCD12345E', 'ABC COMPANY LTD', '192', '01/04/2024', '31/03/2025', '85,000']
            ],
            [
                ['TAN', 'DEDUCTOR NAME', 'SECTION', 'PERIOD FROM', 'PERIOD TO', 'AMOUNT'],
                ['BANK12345E', 'XYZ BANK LTD', '194A', '01/04/2024', '31/03/2025', '4,500']
            ],
            [
                ['BSR CODE', 'CHALLAN NO', 'DATE PAID', 'AMOUNT'],
                ['1234567', '123456789', '15/06/2024', '10,000'],
                ['1234567', '987654321', '15/09/2024', '5,000']
            ]
        ]
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Mock file validation
        with patch.object(self.parser, '_validate_file'):
            result = self.parser.parse(self.sample_pdf_path)
        
        # Verify result structure
        assert "form26as_data" in result
        assert "metadata" in result
        
        form26as_data = result["form26as_data"]
        assert len(form26as_data["tds_salary"]) >= 1
        assert len(form26as_data["tds_others"]) >= 1
        assert len(form26as_data["challans"]) >= 2
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["source"] == "form26as"
        assert metadata["parser"] == "deterministic"
        assert metadata["confidence"] == 1.0
    
    @patch('pdfplumber.open')
    def test_parse_pdf_extraction_failure(self, mock_pdfplumber):
        """Test handling of PDF extraction failure."""
        mock_pdfplumber.side_effect = Exception("PDF extraction failed")
        
        with patch.object(self.parser, '_validate_file'):
            with pytest.raises(ParseMiss):
                self.parser.parse(self.sample_pdf_path)
    
    def test_detect_sections(self):
        """Test section detection from text."""
        text = """
        FORM 26AS
        PART A - TDS ON SALARY
        Some salary data here
        PART B - TDS ON OTHER THAN SALARY
        Some other TDS data here
        PART C - TCS COLLECTED
        Some TCS data here
        PART D - ADVANCE TAX
        Some challan data here
        """
        
        sections = self.parser._detect_sections(text)
        
        assert 'tds_salary' in sections
        assert 'tds_others' in sections
        assert 'tcs' in sections
        assert 'challans' in sections
    
    def test_normalize_headers(self):
        """Test header normalization."""
        headers = ['TAN', 'DEDUCTOR NAME', 'SECTION', 'PERIOD FROM', 'PERIOD TO', 'AMOUNT']
        normalized = self.parser._normalize_headers(headers)
        
        assert normalized['tan'] == 0
        assert normalized['deductor'] == 1
        assert normalized['section'] == 2
        assert normalized['period_from'] == 3
        assert normalized['period_to'] == 4
        assert normalized['amount'] == 5
    
    def test_parse_tds_row(self):
        """Test parsing individual TDS row."""
        headers = {'tan': 0, 'deductor': 1, 'section': 2, 'amount': 5}
        row = ['ABCD12345E', 'ABC COMPANY LTD', '192', '', '', '85,000']
        
        tds_row = self.parser._parse_tds_row(row, headers)
        
        assert tds_row is not None
        assert tds_row.tan == 'ABCD12345E'
        assert tds_row.deductor == 'ABC COMPANY LTD'
        assert tds_row.section == '192'
        assert tds_row.amount == 85000
    
    def test_parse_challan_row(self):
        """Test parsing individual challan row."""
        headers = {'bsr_code': 0, 'challan_no': 1, 'paid_on': 2, 'amount': 3}
        row = ['1234567', '123456789', '15/06/2024', '10,000']
        section_text = "ADVANCE TAX"
        
        challan_row = self.parser._parse_challan_row(row, headers, section_text)
        
        assert challan_row is not None
        assert challan_row.bsr_code == '1234567'
        assert challan_row.challan_no == '123456789'
        assert challan_row.kind == 'ADVANCE'
        assert challan_row.amount == 10000
        assert challan_row.paid_on == date(2024, 6, 15)
    
    def test_parse_date_formats(self):
        """Test date parsing with various formats."""
        test_cases = [
            ('15/06/2024', date(2024, 6, 15)),
            ('15-06-2024', date(2024, 6, 15)),
            ('15.06.2024', date(2024, 6, 15)),
            ('2024-06-15', date(2024, 6, 15)),
            ('15/06/24', date(2024, 6, 15)),
            ('invalid', None),
            ('', None)
        ]
        
        for date_str, expected in test_cases:
            result = self.parser._parse_date(date_str)
            assert result == expected
    
    def test_extract_totals(self):
        """Test total extraction from text."""
        text = """
        TOTAL TDS ON SALARY: ₹85,000
        TOTAL TDS ON OTHER THAN SALARY: ₹4,500
        TOTAL TCS: ₹0
        TOTAL ADVANCE TAX: ₹15,000
        """
        
        totals = self.parser._extract_totals(text)
        
        assert totals.get('tds_salary_total') == 85000
        assert totals.get('tds_others_total') == 4500
        assert totals.get('advance_tax_total') == 15000
    
    def test_validate_invariants_success(self):
        """Test successful invariant validation."""
        extract = Form26ASExtract(
            tds_salary=[TDSRow(amount=85000)],
            tds_others=[TDSRow(amount=4500)],
            challans=[ChallanRow(kind='ADVANCE', amount=15000)],
            totals={'tds_salary_total': 85000, 'tds_others_total': 4500}
        )
        
        # Should not raise any exception
        self.parser._validate_invariants(extract)
    
    def test_validate_invariants_amount_mismatch(self):
        """Test invariant validation with amount mismatch."""
        extract = Form26ASExtract(
            tds_salary=[TDSRow(amount=85000)],
            totals={'tds_salary_total': 90000}  # Mismatch
        )
        
        # Should log warning but not raise exception
        with patch('core.parsers.form26as.logger') as mock_logger:
            self.parser._validate_invariants(extract)
            mock_logger.warning.assert_called()
    
    def test_validate_invariants_invalid_amount_type(self):
        """Test invariant validation with invalid amount type."""
        # This would be caught by Pydantic validation before reaching _validate_invariants
        with pytest.raises(ValueError):
            TDSRow(amount="invalid")
    
    def test_find_relevant_table(self):
        """Test finding relevant table for a section."""
        tables = [
            [['TAN', 'DEDUCTOR', 'AMOUNT'], ['ABC123', 'Company', '1000']],
            [['BSR', 'CHALLAN', 'AMOUNT'], ['123456', '789', '2000']],
            [['OTHER', 'DATA'], ['value1', 'value2']]
        ]
        
        section_text = "TDS section with deductor information"
        relevant_table = self.parser._find_relevant_table(section_text, tables)
        
        # Should find the first table with TAN, DEDUCTOR, AMOUNT
        assert relevant_table == tables[0]
    
    def test_parse_tds_from_text_fallback(self):
        """Test fallback TDS parsing from text."""
        text = "Some TDS entry with amount ₹85,000 and another ₹4,500"
        
        tds_rows = self.parser._parse_tds_from_text(text)
        
        assert len(tds_rows) == 2
        assert tds_rows[0].amount == 85000
        assert tds_rows[1].amount == 4500
    
    def test_parse_challans_from_text_fallback(self):
        """Test fallback challan parsing from text."""
        text = "ADVANCE TAX with BSR: 1234567 amount ₹10,000 and BSR: 7654321 amount ₹5,000"
        
        challan_rows = self.parser._parse_challans_from_text(text)
        
        assert len(challan_rows) == 2
        assert all(row.kind == 'ADVANCE' for row in challan_rows)
        assert challan_rows[0].amount == 10000
        assert challan_rows[1].amount == 5000


class TestTDSRow:
    """Test cases for TDSRow model."""
    
    def test_tds_row_creation(self):
        """Test TDS row creation with valid data."""
        row = TDSRow(
            tan="ABCD12345E",
            deductor="ABC Company Ltd",
            section="192",
            period_from=date(2024, 4, 1),
            period_to=date(2025, 3, 31),
            amount=85000
        )
        
        assert row.tan == "ABCD12345E"
        assert row.deductor == "ABC Company Ltd"
        assert row.section == "192"
        assert row.amount == 85000
    
    def test_tds_row_amount_parsing(self):
        """Test amount parsing from various formats."""
        test_cases = [
            (85000, 85000),
            (85000.0, 85000),
            ("85000", 85000),
            ("₹85,000", 85000),
            ("85,000", 85000),
            ("invalid", 0),
            ("", 0)
        ]
        
        for input_amount, expected in test_cases:
            row = TDSRow(amount=input_amount)
            assert row.amount == expected
    
    def test_tds_row_negative_amount(self):
        """Test TDS row with negative amount."""
        with pytest.raises(ValueError):
            TDSRow(amount=-1000)


class TestChallanRow:
    """Test cases for ChallanRow model."""
    
    def test_challan_row_creation(self):
        """Test challan row creation with valid data."""
        row = ChallanRow(
            kind="ADVANCE",
            bsr_code="1234567",
            challan_no="123456789",
            paid_on=date(2024, 6, 15),
            amount=10000
        )
        
        assert row.kind == "ADVANCE"
        assert row.bsr_code == "1234567"
        assert row.challan_no == "123456789"
        assert row.amount == 10000
    
    def test_challan_row_invalid_kind(self):
        """Test challan row with invalid kind."""
        with pytest.raises(ValueError):
            ChallanRow(kind="INVALID", amount=10000)
    
    def test_challan_row_amount_parsing(self):
        """Test amount parsing from various formats."""
        row = ChallanRow(kind="ADVANCE", amount="₹10,000")
        assert row.amount == 10000


class TestForm26ASExtract:
    """Test cases for Form26ASExtract model."""
    
    def test_form26as_extract_creation(self):
        """Test Form 26AS extract creation."""
        extract = Form26ASExtract(
            tds_salary=[TDSRow(amount=85000)],
            tds_others=[TDSRow(amount=4500)],
            challans=[ChallanRow(kind="ADVANCE", amount=10000)],
            totals={"tds_salary_total": 85000},
            confidence=1.0
        )
        
        assert len(extract.tds_salary) == 1
        assert len(extract.tds_others) == 1
        assert len(extract.challans) == 1
        assert extract.confidence == 1.0
        assert extract.source == "DETERMINISTIC"
    
    def test_form26as_extract_defaults(self):
        """Test Form 26AS extract with default values."""
        extract = Form26ASExtract()
        
        assert extract.tds_salary == []
        assert extract.tds_others == []
        assert extract.tcs == []
        assert extract.challans == []
        assert extract.totals == {}
        assert extract.source == "DETERMINISTIC"
        assert extract.confidence == 1.0
    
    def test_form26as_extract_invalid_confidence(self):
        """Test Form 26AS extract with invalid confidence."""
        with pytest.raises(ValueError):
            Form26ASExtract(confidence=1.5)
        
        with pytest.raises(ValueError):
            Form26ASExtract(confidence=-0.1)