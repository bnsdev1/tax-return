"""
Unit tests for ITR JSON Exporter and Schema Validation

Tests the complete JSON export workflow including:
- ITR JSON generation for ITR-1 and ITR-2
- Schema validation against local schemas
- Error handling and validation reporting
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime
from packages.core.src.core.exporter.itr_json import (
    ITRJSONBuilder, ITRFormType, SchemaVersion, build_itr_json
)
from packages.core.src.core.validate.schema_check import (
    SchemaRegistry, validate_itr_json, get_schema_registry
)

class TestITRJSONBuilder:
    """Test cases for ITR JSON Builder"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sample_totals = {
            'gross_total_income': 800000,
            'taxable_income': 650000,
            'total_deductions': 150000,
            'income_breakdown': {
                'salary': 800000,
                'house_property': 0,
                'capital_gains': 0,
                'other_sources': 0
            },
            'tax_liability': {
                'base_tax': 45000,
                'rebate_87a': 25000,
                'tax_after_rebate': 20000,
                'surcharge': 0,
                'cess': 800,
                'total_tax_liability': 20800,
                'interest_234a': 0,
                'interest_234b': 0,
                'interest_234c': 0,
                'total_interest': 0,
                'total_payable': 20800
            },
            'deductions_summary': {
                'section_80c': 100000,
                'section_80d': 25000,
                'section_80ccd1b': 25000,
                'total_deductions': 150000
            },
            'advance_tax_paid': 0,
            'total_taxes_paid': 30000
        }
        
        self.sample_prefill = {
            'taxpayer': {
                'first_name': 'John',
                'middle_name': '',
                'last_name': 'Doe',
                'pan': 'ABCDE1234F',
                'date_of_birth': '1990-01-01',
                'email': 'john.doe@example.com',
                'father_name': 'Father Name',
                'place': 'Mumbai',
                'address': {
                    'house_no': '123',
                    'street': 'Main Street',
                    'area': 'Central Area',
                    'city': 'Mumbai',
                    'state_code': '27',
                    'country_code': '91',
                    'pincode': '400001'
                },
                'phone': {
                    'std_code': '022',
                    'number': '12345678'
                }
            },
            'tds': {
                'salary_tds': 25000,
                'other_tds': 5000,
                'total_tds': 30000
            },
            'house_property': {},
            'capital_gains': {},
            'donations': {}
        }
        
        self.sample_form_data = {
            'form_type': 'ITR1',
            'assessment_year': '2025-26'
        }
    
    def test_itr1_json_generation(self):
        """Test ITR-1 JSON generation"""
        builder = ITRJSONBuilder(ITRFormType.ITR1, "2025-26", SchemaVersion.V2_0)
        
        result = builder.build_itr_json(
            self.sample_totals,
            self.sample_prefill,
            self.sample_form_data,
            "2025-26",
            "2.0"
        )
        
        assert result is not None
        assert result.form_type == "ITR1"
        assert result.assessment_year == "2025-26"
        assert result.schema_version == "2.0"
        assert isinstance(result.json_data, dict)
        assert isinstance(result.json_string, str)
        
        # Verify JSON structure
        json_data = result.json_data
        assert "ITR" in json_data
        assert "ITR1" in json_data["ITR"]
        
        itr1_data = json_data["ITR"]["ITR1"]
        assert "CreationInfo" in itr1_data
        assert "Form_ITR1" in itr1_data
        assert "PersonalInfo" in itr1_data
        assert "ITR1_IncomeDeductions" in itr1_data
        assert "ITR1_TaxComputation" in itr1_data
        
        # Verify form info
        form_info = itr1_data["Form_ITR1"]
        assert form_info["FormName"] == "ITR1"
        assert form_info["AssessmentYear"] == "2025-26"
        assert form_info["SchemaVer"] == "2.0"
        
        # Verify personal info
        personal_info = itr1_data["PersonalInfo"]
        assert personal_info["PAN"] == "ABCDE1234F"
        assert personal_info["AssesseeName"]["FirstName"] == "John"
        assert personal_info["AssesseeName"]["SurNameOrOrgName"] == "Doe"
        
        # Verify income data
        income_data = itr1_data["ITR1_IncomeDeductions"]
        assert income_data["Salary"] == 800000
        assert income_data["GrossTotalIncome"] == 800000
        assert income_data["TotalIncome"] == 650000
        
        # Verify tax computation
        tax_data = itr1_data["ITR1_TaxComputation"]
        assert tax_data["TotalIncome"] == 650000
        assert tax_data["TaxOnTotalIncome"] == 45000
        assert tax_data["Rebate87A"] == 25000
        assert tax_data["TotalTaxPayable"] == 20800
    
    def test_itr2_json_generation(self):
        """Test ITR-2 JSON generation"""
        # Add capital gains data for ITR-2
        totals_itr2 = self.sample_totals.copy()
        totals_itr2['income_breakdown']['capital_gains'] = 50000
        totals_itr2['income_breakdown']['stcg_15_percent'] = 30000
        totals_itr2['income_breakdown']['ltcg_10_percent'] = 20000
        
        form_data_itr2 = self.sample_form_data.copy()
        form_data_itr2['form_type'] = 'ITR2'
        
        builder = ITRJSONBuilder(ITRFormType.ITR2, "2025-26", SchemaVersion.V2_0)
        
        result = builder.build_itr_json(
            totals_itr2,
            self.sample_prefill,
            form_data_itr2,
            "2025-26",
            "2.0"
        )
        
        assert result is not None
        assert result.form_type == "ITR2"
        
        # Verify JSON structure
        json_data = result.json_data
        assert "ITR" in json_data
        assert "ITR2" in json_data["ITR"]
        
        itr2_data = json_data["ITR"]["ITR2"]
        assert "ITR2_IncomeDeductions" in itr2_data
        assert "ITR2_TaxComputation" in itr2_data
        assert "ScheduleCapitalGain" in itr2_data
        assert "ScheduleHouseProperty" in itr2_data
        
        # Verify ITR-2 specific fields
        personal_info = itr2_data["PersonalInfo"]
        assert "ResidentialStatus" in personal_info
        
        # Verify capital gains section
        income_data = itr2_data["ITR2_IncomeDeductions"]
        assert "CapitalGain" in income_data
    
    def test_json_serialization(self):
        """Test JSON serialization and formatting"""
        builder = ITRJSONBuilder(ITRFormType.ITR1, "2025-26", SchemaVersion.V2_0)
        
        result = builder.build_itr_json(
            self.sample_totals,
            self.sample_prefill,
            self.sample_form_data,
            "2025-26",
            "2.0"
        )
        
        # Verify JSON string is valid
        parsed_json = json.loads(result.json_string)
        assert parsed_json == result.json_data
        
        # Verify formatting (indented, sorted keys)
        assert result.json_string.count('\n') > 10  # Should be indented
        assert '"AssessmentYear"' in result.json_string
    
    def test_data_type_conversion(self):
        """Test proper data type conversion for JSON"""
        # Test with Decimal values
        totals_with_decimals = {
            'gross_total_income': Decimal('800000.50'),
            'taxable_income': Decimal('650000.75'),
            'tax_liability': {
                'base_tax': Decimal('45000.25'),
                'total_tax_liability': Decimal('20800.00')
            }
        }
        
        builder = ITRJSONBuilder(ITRFormType.ITR1, "2025-26", SchemaVersion.V2_0)
        
        result = builder.build_itr_json(
            totals_with_decimals,
            self.sample_prefill,
            self.sample_form_data,
            "2025-26",
            "2.0"
        )
        
        # Verify all amounts are converted to integers
        itr_data = result.json_data["ITR"]["ITR1"]
        income_data = itr_data["ITR1_IncomeDeductions"]
        tax_data = itr_data["ITR1_TaxComputation"]
        
        assert isinstance(income_data["GrossTotalIncome"], int)
        assert isinstance(income_data["TotalIncome"], int)
        assert isinstance(tax_data["TaxOnTotalIncome"], int)
        assert isinstance(tax_data["TotalTaxPayable"], int)
    
    def test_build_itr_json_function(self):
        """Test the main build_itr_json function"""
        result = build_itr_json(
            self.sample_totals,
            self.sample_prefill,
            self.sample_form_data,
            "2025-26",
            "2.0"
        )
        
        assert result is not None
        assert result.form_type == "ITR1"
        assert result.assessment_year == "2025-26"
        assert "ITR" in result.json_data

class TestSchemaValidation:
    """Test cases for Schema Validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.registry = get_schema_registry()
    
    def test_schema_registry_initialization(self):
        """Test schema registry initialization"""
        assert self.registry is not None
        
        # Check that schema stubs are created
        schemas = self.registry.get_available_schemas()
        assert len(schemas) >= 2  # At least ITR1 and ITR2
        
        schema_types = [s.form_type for s in schemas]
        assert "ITR1" in schema_types
        assert "ITR2" in schema_types
    
    def test_schema_loading(self):
        """Test schema loading from files"""
        # Load ITR1 schema
        itr1_schema = self.registry.load_schema("ITR1", "2.0")
        assert itr1_schema is not None
        assert itr1_schema["title"] == "ITR-1 Schema"
        assert "properties" in itr1_schema
        assert "ITR" in itr1_schema["properties"]
        
        # Load ITR2 schema
        itr2_schema = self.registry.load_schema("ITR2", "2.0")
        assert itr2_schema is not None
        assert itr2_schema["title"] == "ITR-2 Schema"
    
    def test_valid_json_validation(self):
        """Test validation of valid ITR JSON"""
        # Create a valid ITR-1 JSON
        valid_json = {
            "ITR": {
                "ITR1": {
                    "CreationInfo": {
                        "SWVersionNo": "1.0",
                        "SWCreatedBy": "TaxPlannerPro",
                        "XMLCreationDate": "2025-01-01"
                    },
                    "Form_ITR1": {
                        "FormName": "ITR1",
                        "AssessmentYear": "2025-26",
                        "SchemaVer": "2.0"
                    },
                    "PersonalInfo": {
                        "AssesseeName": {
                            "FirstName": "John",
                            "SurNameOrOrgName": "Doe"
                        },
                        "PAN": "ABCDE1234F",
                        "DOB": "1990-01-01",
                        "Status": "I"
                    },
                    "ITR1_IncomeDeductions": {
                        "GrossTotalIncome": 800000,
                        "TotalIncome": 650000
                    },
                    "ITR1_TaxComputation": {
                        "TotalIncome": 650000,
                        "TaxOnTotalIncome": 45000
                    }
                }
            }
        }
        
        result = self.registry.validate_json(valid_json, "ITR1", "2.0")
        
        assert result is not None
        assert result.form_type == "ITR1"
        assert result.schema_version == "2.0"
        assert result.is_valid == True
        assert result.error_count == 0
    
    def test_invalid_json_validation(self):
        """Test validation of invalid ITR JSON"""
        # Create an invalid ITR-1 JSON (missing required fields)
        invalid_json = {
            "ITR": {
                "ITR1": {
                    "Form_ITR1": {
                        "FormName": "ITR1"
                        # Missing AssessmentYear and SchemaVer
                    },
                    "PersonalInfo": {
                        "AssesseeName": {
                            "FirstName": "John"
                            # Missing SurNameOrOrgName
                        }
                        # Missing PAN, DOB, Status
                    }
                    # Missing required sections
                }
            }
        }
        
        result = self.registry.validate_json(invalid_json, "ITR1", "2.0")
        
        assert result is not None
        assert result.is_valid == False
        assert result.error_count > 0
        assert len(result.errors) > 0
    
    def test_pan_format_validation(self):
        """Test PAN format validation"""
        # Invalid PAN format
        json_with_invalid_pan = {
            "ITR": {
                "ITR1": {
                    "CreationInfo": {
                        "SWVersionNo": "1.0",
                        "SWCreatedBy": "TaxPlannerPro",
                        "XMLCreationDate": "2025-01-01"
                    },
                    "Form_ITR1": {
                        "FormName": "ITR1",
                        "AssessmentYear": "2025-26",
                        "SchemaVer": "2.0"
                    },
                    "PersonalInfo": {
                        "AssesseeName": {
                            "FirstName": "John",
                            "SurNameOrOrgName": "Doe"
                        },
                        "PAN": "INVALID_PAN",  # Invalid format
                        "DOB": "1990-01-01",
                        "Status": "I"
                    },
                    "ITR1_IncomeDeductions": {
                        "GrossTotalIncome": 800000,
                        "TotalIncome": 650000
                    },
                    "ITR1_TaxComputation": {
                        "TotalIncome": 650000,
                        "TaxOnTotalIncome": 45000
                    }
                }
            }
        }
        
        result = self.registry.validate_json(json_with_invalid_pan, "ITR1", "2.0")
        
        assert result.is_valid == False
        assert any("PAN" in error for error in result.errors)
    
    def test_business_logic_validation(self):
        """Test custom business logic validation"""
        # ITR-1 with income exceeding limit
        json_with_high_income = {
            "ITR": {
                "ITR1": {
                    "CreationInfo": {
                        "SWVersionNo": "1.0",
                        "SWCreatedBy": "TaxPlannerPro",
                        "XMLCreationDate": "2025-01-01"
                    },
                    "Form_ITR1": {
                        "FormName": "ITR1",
                        "AssessmentYear": "2025-26",
                        "SchemaVer": "2.0"
                    },
                    "PersonalInfo": {
                        "AssesseeName": {
                            "FirstName": "John",
                            "SurNameOrOrgName": "Doe"
                        },
                        "PAN": "ABCDE1234F",
                        "DOB": "1990-01-01",
                        "Status": "I"
                    },
                    "ITR1_IncomeDeductions": {
                        "GrossTotalIncome": 6000000,  # 60 lakh - exceeds ITR-1 limit
                        "TotalIncome": 6000000
                    },
                    "ITR1_TaxComputation": {
                        "TotalIncome": 6000000,  # Exceeds 50 lakh limit
                        "TaxOnTotalIncome": 1500000
                    }
                }
            }
        }
        
        result = self.registry.validate_json(json_with_high_income, "ITR1", "2.0")
        
        # Should have error about income limit
        assert any("50 lakh" in error or "limit" in error for error in result.errors)
    
    def test_validation_log_creation(self):
        """Test validation log creation"""
        valid_json = {
            "ITR": {
                "ITR1": {
                    "CreationInfo": {
                        "SWVersionNo": "1.0",
                        "SWCreatedBy": "TaxPlannerPro",
                        "XMLCreationDate": "2025-01-01"
                    },
                    "Form_ITR1": {
                        "FormName": "ITR1",
                        "AssessmentYear": "2025-26",
                        "SchemaVer": "2.0"
                    },
                    "PersonalInfo": {
                        "AssesseeName": {
                            "FirstName": "John",
                            "SurNameOrOrgName": "Doe"
                        },
                        "PAN": "ABCDE1234F",
                        "DOB": "1990-01-01",
                        "Status": "I"
                    },
                    "ITR1_IncomeDeductions": {
                        "GrossTotalIncome": 800000,
                        "TotalIncome": 650000
                    },
                    "ITR1_TaxComputation": {
                        "TotalIncome": 650000,
                        "TaxOnTotalIncome": 45000
                    }
                }
            }
        }
        
        result = self.registry.validate_json(valid_json, "ITR1", "2.0")
        validation_log = self.registry.create_validation_log(result)
        
        assert validation_log is not None
        assert "validation_summary" in validation_log
        assert "errors" in validation_log
        assert "warnings" in validation_log
        assert "validation_details" in validation_log
        
        summary = validation_log["validation_summary"]
        assert summary["form_type"] == "ITR1"
        assert summary["schema_version"] == "2.0"
        assert summary["is_valid"] == True
    
    def test_validate_itr_json_function(self):
        """Test the convenience validate_itr_json function"""
        valid_json = {
            "ITR": {
                "ITR1": {
                    "CreationInfo": {
                        "SWVersionNo": "1.0",
                        "SWCreatedBy": "TaxPlannerPro",
                        "XMLCreationDate": "2025-01-01"
                    },
                    "Form_ITR1": {
                        "FormName": "ITR1",
                        "AssessmentYear": "2025-26",
                        "SchemaVer": "2.0"
                    },
                    "PersonalInfo": {
                        "AssesseeName": {
                            "FirstName": "John",
                            "SurNameOrOrgName": "Doe"
                        },
                        "PAN": "ABCDE1234F",
                        "DOB": "1990-01-01",
                        "Status": "I"
                    },
                    "ITR1_IncomeDeductions": {
                        "GrossTotalIncome": 800000,
                        "TotalIncome": 650000
                    },
                    "ITR1_TaxComputation": {
                        "TotalIncome": 650000,
                        "TaxOnTotalIncome": 45000
                    }
                }
            }
        }
        
        result = validate_itr_json(valid_json, "ITR1", "2.0")
        
        assert result is not None
        assert result.is_valid == True
        assert result.form_type == "ITR1"

class TestIntegration:
    """Integration tests for export and validation"""
    
    def test_export_and_validate_workflow(self):
        """Test complete export and validation workflow"""
        # Sample data
        totals = {
            'gross_total_income': 800000,
            'taxable_income': 650000,
            'income_breakdown': {'salary': 800000, 'house_property': 0, 'capital_gains': 0, 'other_sources': 0},
            'tax_liability': {'base_tax': 45000, 'rebate_87a': 25000, 'total_tax_liability': 20800},
            'deductions_summary': {'section_80c': 100000, 'total_deductions': 150000}
        }
        
        prefill = {
            'taxpayer': {
                'first_name': 'John', 'last_name': 'Doe', 'pan': 'ABCDE1234F',
                'date_of_birth': '1990-01-01', 'email': 'john@example.com'
            },
            'tds': {'total_tds': 30000}
        }
        
        form_data = {'form_type': 'ITR1', 'assessment_year': '2025-26'}
        
        # Export JSON
        export_result = build_itr_json(totals, prefill, form_data, "2025-26", "2.0")
        
        assert export_result is not None
        assert export_result.form_type == "ITR1"
        
        # Validate exported JSON
        validation_result = validate_itr_json(export_result.json_data, "ITR1", "2.0")
        
        assert validation_result is not None
        assert validation_result.is_valid == True
        assert validation_result.error_count == 0
        
        # Verify JSON can be serialized and parsed
        json_string = export_result.json_string
        parsed_json = json.loads(json_string)
        assert parsed_json == export_result.json_data

if __name__ == "__main__":
    pytest.main([__file__])