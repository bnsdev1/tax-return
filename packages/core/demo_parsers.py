#!/usr/bin/env python3
"""
Demonstration script for the document parser system.
Shows how to use the parser registry to parse different types of tax documents.
"""

import json
import csv
import tempfile
from pathlib import Path

from src.core.parsers import default_registry


def create_sample_files():
    """Create sample files for demonstration."""
    files = {}
    
    # 1. Create sample prefill JSON
    prefill_data = {
        "pan": "ABCDE1234F",
        "name": "John Doe",
        "assessment_year": "2025-26",
        "salary": {
            "gross": 800000,
            "allowances": 50000
        },
        "deductions": {
            "80c": 150000,
            "80d": 25000
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_prefill.json', delete=False) as f:
        json.dump(prefill_data, f, indent=2)
        files['prefill'] = Path(f.name)
    
    # 2. Create sample AIS JSON
    ais_data = {
        "pan": "ABCDE1234F",
        "assessment_year": "2025-26",
        "statement_type": "AIS",
        "salary_details": [
            {
                "employer": "ABC Company",
                "gross_salary": 850000,
                "tds": 45000
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_ais.json', delete=False) as f:
        json.dump(ais_data, f, indent=2)
        files['ais'] = Path(f.name)
    
    # 3. Create sample Form 16B PDF (dummy)
    with tempfile.NamedTemporaryFile(suffix='_form16b.pdf', delete=False) as f:
        f.write(b'%PDF-1.4\n%Dummy Form 16B PDF content for demonstration')
        files['form16b'] = Path(f.name)
    
    # 4. Create sample bank CSV
    bank_data = [
        ['Date', 'Description', 'Credit', 'Debit', 'Balance'],
        ['2024-01-01', 'Opening Balance', '100000', '', '100000'],
        ['2024-01-02', 'Salary Credit', '50000', '', '150000'],
        ['2024-01-03', 'ATM Withdrawal', '', '5000', '145000'],
        ['2024-01-04', 'Interest Credit', '500', '', '145500'],
        ['2024-01-05', 'Online Payment', '', '2000', '143500'],
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_bank.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(bank_data)
        files['bank_csv'] = Path(f.name)
    
    # 5. Create sample P&L CSV
    pnl_data = [
        ['Account', 'Amount', 'Category'],
        ['Sales Revenue', '2500000', 'Revenue'],
        ['Service Revenue', '750000', 'Revenue'],
        ['Cost of Goods Sold', '1200000', 'Expense'],
        ['Salaries', '800000', 'Expense'],
        ['Rent', '240000', 'Expense'],
        ['Utilities', '60000', 'Expense'],
        ['Marketing', '120000', 'Expense'],
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_pnl.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(pnl_data)
        files['pnl_csv'] = Path(f.name)
    
    return files


def demonstrate_parser_registry():
    """Demonstrate the parser registry functionality."""
    print("🚀 Document Parser System Demonstration")
    print("=" * 50)
    
    # Show registry information
    print("\n📋 Registry Information:")
    print(f"Supported kinds: {', '.join(default_registry.list_supported_kinds())}")
    
    print("\n🔧 Registered Parsers:")
    for parser_info in default_registry.list_parsers():
        print(f"  • {parser_info['name']}")
        print(f"    Kinds: {', '.join(parser_info['supported_kinds'])}")
        print(f"    Extensions: {', '.join(parser_info['supported_extensions'])}")
    
    # Create sample files
    print("\n📁 Creating sample files...")
    sample_files = create_sample_files()
    
    # Test each parser
    test_cases = [
        ('prefill', sample_files['prefill'], 'Prefill JSON'),
        ('ais', sample_files['ais'], 'AIS JSON'),
        ('form16b', sample_files['form16b'], 'Form 16B PDF'),
        ('bank_csv', sample_files['bank_csv'], 'Bank Statement CSV'),
        ('pnl_csv', sample_files['pnl_csv'], 'P&L Statement CSV'),
    ]
    
    print("\n🔍 Testing Parsers:")
    for kind, file_path, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"File: {file_path.name}")
        print(f"Kind: {kind}")
        
        try:
            # Get appropriate parser
            parser = default_registry.get_parser(kind, file_path)
            if parser:
                print(f"✅ Parser found: {type(parser).__name__}")
                
                # Parse the file
                result = default_registry.parse(kind, file_path)
                
                # Show key results
                print("📊 Parse Results:")
                if kind == 'prefill':
                    print(f"  PAN: {result['personal_info']['pan']}")
                    print(f"  Name: {result['personal_info']['name']}")
                    print(f"  Salary: ₹{result['income']['salary']['gross_salary']:,.2f}")
                    print(f"  80C Deduction: ₹{result['deductions']['section_80c']:,.2f}")
                
                elif kind == 'ais':
                    print(f"  Statement Type: {result['statement_info']['type']}")
                    print(f"  PAN: {result['statement_info']['pan']}")
                    print(f"  Total Salary: ₹{result['summary']['total_salary']:,.2f}")
                    print(f"  Total TDS: ₹{result['summary']['total_tds']:,.2f}")
                
                elif kind == 'form16b':
                    print(f"  Certificate: {result['certificate_info']['certificate_number']}")
                    print(f"  TDS Amount: ₹{result['payment_details']['tds_amount']:,.2f}")
                    print(f"  Property Value: ₹{result['property_details']['stamp_duty_value']:,.2f}")
                
                elif kind == 'bank_csv':
                    print(f"  Total Transactions: {result['summary']['total_transactions']}")
                    print(f"  Total Credits: ₹{result['summary']['total_credits']:,.2f}")
                    print(f"  Total Debits: ₹{result['summary']['total_debits']:,.2f}")
                    print(f"  Net Amount: ₹{result['summary']['net_amount']:,.2f}")
                
                elif kind == 'pnl_csv':
                    print(f"  Total Revenue: ₹{result['revenue']['total_revenue']:,.2f}")
                    print(f"  Net Profit: ₹{result['summary']['net_profit']:,.2f}")
                    print(f"  Profit Margin: {result['summary']['net_profit_margin']:.1f}%")
                
                print(f"  Parser: {result['_parser_info']['parser_name']}")
                print(f"  Parsed at: {result['_parser_info']['parsed_at']}")
                
            else:
                print("❌ No suitable parser found")
                
        except Exception as e:
            print(f"❌ Error parsing file: {e}")
    
    # Test error handling
    print("\n🚨 Testing Error Handling:")
    
    # Test unsupported file type
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'This is a text file')
        txt_path = Path(f.name)
    
    try:
        parser = default_registry.get_parser('unknown_type', txt_path)
        print(f"❌ Unexpected: Found parser for unknown type")
    except:
        print("✅ Correctly handled unknown file type")
    finally:
        txt_path.unlink()
    
    # Test invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json content')
        invalid_json_path = Path(f.name)
    
    try:
        result = default_registry.parse('prefill', invalid_json_path)
        print("❌ Unexpected: Parsed invalid JSON")
    except ValueError as e:
        print(f"✅ Correctly handled invalid JSON: {str(e)[:50]}...")
    finally:
        invalid_json_path.unlink()
    
    # Cleanup sample files
    print("\n🧹 Cleaning up sample files...")
    for file_path in sample_files.values():
        try:
            file_path.unlink()
        except:
            pass
    
    print("\n✨ Demonstration completed successfully!")
    print("\n💡 Key Features Demonstrated:")
    print("  • Parser protocol and registry system")
    print("  • Automatic parser selection by file type and kind")
    print("  • Deterministic extraction with fixture data")
    print("  • Error handling for invalid files")
    print("  • Structured output with metadata")
    print("  • Support for JSON, PDF, and CSV formats")


if __name__ == "__main__":
    demonstrate_parser_registry()