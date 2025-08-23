"""Unit tests for document parsers."""

import json
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from core.parsers import (
    ParserRegistry,
    PrefillParser,
    AISParser,
    Form16BParser,
    BankCSVParser,
    PnLCSVParser,
    default_registry,
)


class TestParserRegistry:
    """Test the parser registry functionality."""
    
    def test_registry_creation(self):
        """Test creating a new registry."""
        registry = ParserRegistry()
        assert len(registry._parsers) == 0
    
    def test_parser_registration(self):
        """Test registering parsers."""
        registry = ParserRegistry()
        parser = PrefillParser()
        
        registry.register(parser)
        assert len(registry._parsers) == 1
        assert parser in registry._parsers
    
    def test_invalid_parser_registration(self):
        """Test registering invalid parser raises error."""
        registry = ParserRegistry()
        
        class InvalidParser:
            pass
        
        with pytest.raises(ValueError, match="must implement ArtifactParser protocol"):
            registry.register(InvalidParser())
    
    def test_get_parser_success(self):
        """Test getting appropriate parser."""
        registry = ParserRegistry()
        parser = PrefillParser()
        registry.register(parser)
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b'{"test": "data"}')
            temp_path = Path(f.name)
        
        try:
            found_parser = registry.get_parser('prefill', temp_path)
            assert found_parser is parser
        finally:
            temp_path.unlink()
    
    def test_get_parser_not_found(self):
        """Test getting parser when none matches."""
        registry = ParserRegistry()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            found_parser = registry.get_parser('unknown', temp_path)
            assert found_parser is None
        finally:
            temp_path.unlink()
    
    def test_parse_success(self):
        """Test parsing with registry."""
        registry = ParserRegistry()
        parser = PrefillParser()
        registry.register(parser)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"pan": "ABCDE1234F"}, f)
            temp_path = Path(f.name)
        
        try:
            result = registry.parse('prefill', temp_path)
            assert isinstance(result, dict)
            assert '_parser_info' in result
            assert result['_parser_info']['artifact_kind'] == 'prefill'
        finally:
            temp_path.unlink()
    
    def test_parse_no_parser(self):
        """Test parsing when no parser is found."""
        registry = ParserRegistry()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="No parser found"):
                registry.parse('unknown', temp_path)
        finally:
            temp_path.unlink()
    
    def test_list_supported_kinds(self):
        """Test listing supported kinds."""
        registry = ParserRegistry()
        registry.register(PrefillParser())
        registry.register(AISParser())
        
        kinds = registry.list_supported_kinds()
        assert 'prefill' in kinds
        assert 'ais' in kinds
        assert 'tis' in kinds
    
    def test_list_parsers(self):
        """Test listing parser information."""
        registry = ParserRegistry()
        registry.register(PrefillParser())
        
        parsers = registry.list_parsers()
        assert len(parsers) == 1
        assert parsers[0]['name'] == 'PrefillParser'
        assert 'prefill' in parsers[0]['supported_kinds']


class TestPrefillParser:
    """Test the prefill JSON parser."""
    
    def test_supported_kinds(self):
        """Test supported kinds."""
        parser = PrefillParser()
        assert 'prefill' in parser.supported_kinds
        assert 'prefill_data' in parser.supported_kinds
    
    def test_supported_extensions(self):
        """Test supported extensions."""
        parser = PrefillParser()
        assert '.json' in parser.supported_extensions
    
    def test_supports_valid_file(self):
        """Test supports method with valid file."""
        parser = PrefillParser()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b'{"test": "data"}')
            temp_path = Path(f.name)
        
        try:
            assert parser.supports('prefill', temp_path)
            assert not parser.supports('unknown', temp_path)
        finally:
            temp_path.unlink()
    
    def test_supports_invalid_extension(self):
        """Test supports method with invalid extension."""
        parser = PrefillParser()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            assert not parser.supports('prefill', temp_path)
        finally:
            temp_path.unlink()
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON file."""
        parser = PrefillParser()
        
        test_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "salary": {"gross": 800000},
            "deductions": {"80c": 150000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            
            assert isinstance(result, dict)
            assert 'personal_info' in result
            assert 'return_context' in result
            assert 'income' in result
            assert 'deductions' in result
            assert 'metadata' in result
            
            assert result['personal_info']['pan'] == 'ABCDE1234F'
            assert result['personal_info']['name'] == 'Test User'
            assert result['income']['salary']['gross_salary'] == 800000.0
            assert result['deductions']['section_80c'] == 150000.0
        finally:
            temp_path.unlink()
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON file."""
        parser = PrefillParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON format"):
                parser.parse(temp_path)
        finally:
            temp_path.unlink()
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        parser = PrefillParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse(Path('/nonexistent/file.json'))


class TestAISParser:
    """Test the AIS/TIS JSON parser."""
    
    def test_supported_kinds(self):
        """Test supported kinds."""
        parser = AISParser()
        assert 'ais' in parser.supported_kinds
        assert 'tis' in parser.supported_kinds
    
    def test_parse_ais_file(self):
        """Test parsing AIS file."""
        parser = AISParser()
        
        test_data = {
            "pan": "ABCDE1234F",
            "assessment_year": "2025-26",
            "statement_type": "AIS"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_ais.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            
            assert result['statement_info']['type'] == 'AIS'
            assert result['statement_info']['pan'] == 'ABCDE1234F'
            assert 'salary_details' in result
            assert 'interest_details' in result
            assert 'summary' in result
        finally:
            temp_path.unlink()
    
    def test_parse_tis_file(self):
        """Test parsing TIS file."""
        parser = AISParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_tis.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            assert result['statement_info']['type'] == 'TIS'
        finally:
            temp_path.unlink()


class TestForm16BParser:
    """Test the Form 16B PDF parser."""
    
    def test_supported_kinds(self):
        """Test supported kinds."""
        parser = Form16BParser()
        assert 'form16b' in parser.supported_kinds
        assert 'tds_certificate' in parser.supported_kinds
    
    def test_supported_extensions(self):
        """Test supported extensions."""
        parser = Form16BParser()
        assert '.pdf' in parser.supported_extensions
    
    def test_parse_pdf_file(self):
        """Test parsing PDF file (stub implementation)."""
        parser = Form16BParser()
        
        # Create a dummy PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 dummy pdf content')
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            
            assert 'certificate_info' in result
            assert 'deductor_details' in result
            assert 'deductee_details' in result
            assert 'property_details' in result
            assert 'payment_details' in result
            assert 'summary' in result
            
            assert result['certificate_info']['form_type'] == 'Form 16B'
            assert result['summary']['total_tds_deducted'] == 45000.0
        finally:
            temp_path.unlink()


class TestBankCSVParser:
    """Test the bank CSV parser."""
    
    def test_supported_kinds(self):
        """Test supported kinds."""
        parser = BankCSVParser()
        assert 'bank_csv' in parser.supported_kinds
        assert 'bank_statement' in parser.supported_kinds
    
    def test_parse_csv_file(self):
        """Test parsing CSV file."""
        parser = BankCSVParser()
        
        # Create test CSV data
        csv_data = [
            ['Date', 'Description', 'Credit', 'Debit', 'Balance'],
            ['2024-01-01', 'Opening Balance', '100000', '', '100000'],
            ['2024-01-02', 'Salary Credit', '50000', '', '150000'],
            ['2024-01-03', 'ATM Withdrawal', '', '5000', '145000'],
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            
            assert 'account_info' in result
            assert 'statement_period' in result
            assert 'transactions' in result
            assert 'summary' in result
            assert 'categories' in result
            
            assert len(result['transactions']) > 0
            assert result['summary']['total_transactions'] > 0
        finally:
            temp_path.unlink()
    
    def test_parse_empty_csv(self):
        """Test parsing empty CSV file."""
        parser = BankCSVParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="empty"):
                parser.parse(temp_path)
        finally:
            temp_path.unlink()


class TestPnLCSVParser:
    """Test the P&L CSV parser."""
    
    def test_supported_kinds(self):
        """Test supported kinds."""
        parser = PnLCSVParser()
        assert 'pnl_csv' in parser.supported_kinds
        assert 'profit_loss' in parser.supported_kinds
    
    def test_parse_csv_file(self):
        """Test parsing P&L CSV file."""
        parser = PnLCSVParser()
        
        # Create test P&L CSV data
        csv_data = [
            ['Account', 'Amount', 'Category'],
            ['Sales Revenue', '2500000', 'Revenue'],
            ['Cost of Goods Sold', '1200000', 'Expense'],
            ['Salaries', '800000', 'Expense'],
            ['Rent', '240000', 'Expense'],
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse(temp_path)
            
            assert 'statement_info' in result
            assert 'revenue' in result
            assert 'expenses' in result
            assert 'summary' in result
            assert 'ratios' in result
            
            assert result['statement_info']['statement_type'] == 'Profit & Loss Statement'
            assert result['revenue']['total_revenue'] > 0
            assert result['summary']['net_profit_margin'] is not None
        finally:
            temp_path.unlink()


class TestDefaultRegistry:
    """Test the default registry with all parsers."""
    
    def test_default_registry_has_all_parsers(self):
        """Test that default registry includes all parsers."""
        parsers = default_registry.list_parsers()
        parser_names = [p['name'] for p in parsers]
        
        assert 'PrefillParser' in parser_names
        assert 'AISParser' in parser_names
        assert 'Form16BParser' in parser_names
        assert 'BankCSVParser' in parser_names
        assert 'PnLCSVParser' in parser_names
    
    def test_default_registry_routing(self):
        """Test that default registry routes correctly by kind."""
        # Test prefill routing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = Path(f.name)
        
        try:
            parser = default_registry.get_parser('prefill', temp_path)
            assert isinstance(parser, PrefillParser)
        finally:
            temp_path.unlink()
        
        # Test AIS routing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = Path(f.name)
        
        try:
            parser = default_registry.get_parser('ais', temp_path)
            assert isinstance(parser, AISParser)
        finally:
            temp_path.unlink()
        
        # Test Form 16B routing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'dummy pdf')
            temp_path = Path(f.name)
        
        try:
            parser = default_registry.get_parser('form16b', temp_path)
            assert isinstance(parser, Form16BParser)
        finally:
            temp_path.unlink()
        
        # Test bank CSV routing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Date,Amount\n2024-01-01,1000')
            temp_path = Path(f.name)
        
        try:
            parser = default_registry.get_parser('bank_csv', temp_path)
            assert isinstance(parser, BankCSVParser)
        finally:
            temp_path.unlink()
        
        # Test P&L CSV routing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Account,Amount\nRevenue,1000')
            temp_path = Path(f.name)
        
        try:
            parser = default_registry.get_parser('pnl_csv', temp_path)
            assert isinstance(parser, PnLCSVParser)
        finally:
            temp_path.unlink()
    
    def test_supported_kinds_coverage(self):
        """Test that all expected kinds are supported."""
        supported_kinds = default_registry.list_supported_kinds()
        
        expected_kinds = [
            'prefill', 'prefill_data',
            'ais', 'tis', 'ais_data', 'tis_data',
            'form16b', 'form_16b', 'tds_certificate',
            'bank_csv', 'bank_statement', 'transactions',
            'pnl_csv', 'pnl', 'profit_loss', 'income_statement'
        ]
        
        for kind in expected_kinds:
            assert kind in supported_kinds