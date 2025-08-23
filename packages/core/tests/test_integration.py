"""Integration tests for tax models and schema registry."""

import json
import pytest
from pathlib import Path
from typing import Dict, Any

# Import all models to test import functionality
from core import (
    TaxBaseModel,
    AmountModel,
    ValidationMixin,
    PersonalInfo,
    ReturnContext,
    Salary,
    HouseProperty,
    CapitalGains,
    OtherSources,
    Deductions,
    TaxesPaid,
    Totals,
    SchemaRegistry,
)


def get_schemas_root():
    """Get the correct path to the schemas directory."""
    # From packages/core/tests/test_integration.py, go up to root, then to packages/schemas
    return Path(__file__).parent.parent.parent.parent / "packages" / "schemas"


class TestModelImports:
    """Test that all models can be imported successfully."""
    
    def test_all_models_importable(self):
        """Verify that all models can be imported without errors."""
        # Base models
        assert TaxBaseModel is not None
        assert AmountModel is not None
        assert ValidationMixin is not None
        
        # Personal models
        assert PersonalInfo is not None
        assert ReturnContext is not None
        
        # Income models
        assert Salary is not None
        assert HouseProperty is not None
        assert CapitalGains is not None
        assert OtherSources is not None
        
        # Other models
        assert Deductions is not None
        assert TaxesPaid is not None
        assert Totals is not None
        
        # Schema registry
        assert SchemaRegistry is not None
    
    def test_model_inheritance(self):
        """Verify that models inherit from correct base classes."""
        # Check that all models inherit from TaxBaseModel
        assert issubclass(PersonalInfo, TaxBaseModel)
        assert issubclass(ReturnContext, TaxBaseModel)
        assert issubclass(Salary, AmountModel)
        assert issubclass(HouseProperty, AmountModel)
        assert issubclass(CapitalGains, AmountModel)
        assert issubclass(OtherSources, AmountModel)
        assert issubclass(Deductions, AmountModel)
        assert issubclass(TaxesPaid, AmountModel)
        assert issubclass(Totals, AmountModel)
        
        # Check that AmountModel inherits from TaxBaseModel
        assert issubclass(AmountModel, TaxBaseModel)


class TestSchemaRegistryIntegration:
    """Test schema registry with actual schema files."""
    
    @pytest.fixture
    def registry(self):
        """Create a schema registry instance."""
        return SchemaRegistry(get_schemas_root())
    
    def test_registry_with_actual_files(self, registry):
        """Test that registry works with actual schema files."""
        # Test that we can list available schemas
        schemas = registry.list_available_schemas()
        assert len(schemas) > 0
        
        # Should have ITR1 and ITR2 for 2025-26
        expected_schemas = [("2025-26", "ITR1"), ("2025-26", "ITR2")]
        for expected in expected_schemas:
            assert expected in schemas
    
    def test_schema_loading(self, registry):
        """Test loading actual schema files."""
        # Load ITR1 schema
        itr1_schema = registry.load_schema("2025-26", "ITR1")
        assert isinstance(itr1_schema, dict)
        assert "version" in itr1_schema
        assert "type" in itr1_schema
        
        # Load ITR2 schema
        itr2_schema = registry.load_schema("2025-26", "ITR2")
        assert isinstance(itr2_schema, dict)
        assert "version" in itr2_schema
        assert "type" in itr2_schema
    
    def test_schema_version_retrieval(self, registry):
        """Test retrieving schema versions."""
        itr1_version = registry.get_schema_version("2025-26", "ITR1")
        assert isinstance(itr1_version, str)
        assert len(itr1_version) > 0
        
        itr2_version = registry.get_schema_version("2025-26", "ITR2")
        assert isinstance(itr2_version, str)
        assert len(itr2_version) > 0
    
    def test_path_resolution(self, registry):
        """Test that path resolution works correctly."""
        itr1_path = registry.get_schema_path("2025-26", "ITR1")
        assert itr1_path.exists()
        assert itr1_path.name == "schema.json"
        assert "ITR1" in str(itr1_path)
        assert "2025-26" in str(itr1_path)
        
        itr2_path = registry.get_schema_path("2025-26", "ITR2")
        assert itr2_path.exists()
        assert itr2_path.name == "schema.json"
        assert "ITR2" in str(itr2_path)
        assert "2025-26" in str(itr2_path)


class TestModelSchemaCompatibility:
    """Test compatibility between Pydantic models and JSON schemas."""
    
    @pytest.fixture
    def registry(self):
        """Create a schema registry instance."""
        return SchemaRegistry(get_schemas_root())
    
    def test_model_serialization_matches_schema_structure(self, registry):
        """Test that model serialization produces data compatible with schemas."""
        # Create sample data for ITR1 (simpler form)
        personal_info = PersonalInfo(
            pan="ABCDE1234F",
            name="Test User",
            date_of_birth="1990-01-01",
            address="Test Address"
        )
        
        return_context = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1"
        )
        
        salary = Salary(
            gross_salary=500000.0,
            allowances=50000.0
        )
        
        deductions = Deductions(
            section_80c=150000.0,
            section_80d=25000.0
        )
        
        # Test that models can be serialized to JSON
        personal_json = personal_info.model_dump()
        context_json = return_context.model_dump()
        salary_json = salary.model_dump()
        deductions_json = deductions.model_dump()
        
        # Verify JSON serialization works
        assert isinstance(personal_json, dict)
        assert isinstance(context_json, dict)
        assert isinstance(salary_json, dict)
        assert isinstance(deductions_json, dict)
        
        # Test round-trip serialization
        personal_restored = PersonalInfo.model_validate(personal_json)
        assert personal_restored.pan == personal_info.pan
        assert personal_restored.name == personal_info.name
        
        # For validation, exclude computed fields from the JSON
        salary_json_for_validation = {k: v for k, v in salary_json.items() if k != 'total_salary'}
        salary_restored = Salary.model_validate(salary_json_for_validation)
        assert salary_restored.gross_salary == salary.gross_salary
        assert salary_restored.total_salary == salary.total_salary  # This is computed
    
    def test_comprehensive_tax_return_data(self, registry):
        """Test a complete tax return data structure."""
        # Create a comprehensive tax return
        tax_return_data = {
            "personal_info": PersonalInfo(
                pan="ABCDE1234F",
                name="Test User",
                date_of_birth="1990-01-01",
                address="Test Address",
                mobile="9876543210",
                email="test@example.com"
            ),
            "return_context": ReturnContext(
                assessment_year="2025-26",
                form_type="ITR2",
                revised_return=False
            ),
            "salary": Salary(
                gross_salary=800000.0,
                allowances=80000.0,
                perquisites=20000.0
            ),
            "house_property": HouseProperty(
                annual_value=240000.0,
                municipal_tax=12000.0,
                standard_deduction=72000.0,
                interest_on_loan=150000.0
            ),
            "capital_gains": CapitalGains(
                short_term=50000.0,
                long_term=100000.0
            ),
            "other_sources": OtherSources(
                interest_income=25000.0,
                dividend_income=15000.0
            ),
            "deductions": Deductions(
                section_80c=150000.0,
                section_80d=25000.0,
                section_80g=10000.0
            ),
            "taxes_paid": TaxesPaid(
                tds=45000.0,
                advance_tax=20000.0
            ),
            "totals": Totals(
                gross_total_income=1096000.0,
                total_deductions=185000.0,
                tax_on_taxable_income=91100.0,
                total_taxes_paid=65000.0
            )
        }
        
        # Test that all models can be serialized
        serialized_data = {}
        for key, model in tax_return_data.items():
            serialized_data[key] = model.model_dump()
            
        # Test that serialized data is valid JSON
        json_str = json.dumps(serialized_data, default=str)
        assert len(json_str) > 0
        
        # Test that data can be deserialized back
        deserialized_data = json.loads(json_str)
        assert len(deserialized_data) == len(tax_return_data)
        
        # Test specific model reconstruction (exclude computed fields)
        salary_data = {k: v for k, v in deserialized_data["salary"].items() 
                      if k not in ['total_salary']}
        restored_salary = Salary.model_validate(salary_data)
        assert restored_salary.gross_salary == tax_return_data["salary"].gross_salary
        
        totals_data = {k: v for k, v in deserialized_data["totals"].items() 
                      if k not in ['taxable_income', 'total_tax_liability', 'refund_or_payable']}
        restored_totals = Totals.model_validate(totals_data)
        assert restored_totals.taxable_income == tax_return_data["totals"].taxable_income  # This is computed


class TestEndToEndValidation:
    """End-to-end validation tests."""
    
    @pytest.fixture
    def registry(self):
        """Create a schema registry instance."""
        return SchemaRegistry(get_schemas_root())
    
    def test_complete_workflow(self, registry):
        """Test the complete workflow from model creation to schema validation."""
        # 1. Create models
        personal_info = PersonalInfo(
            pan="ABCDE1234F",
            name="Integration Test User",
            date_of_birth="1985-06-15",
            address="123 Test Street, Test City"
        )
        
        return_context = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1"
        )
        
        # 2. Serialize to JSON
        personal_json = personal_info.model_dump()
        context_json = return_context.model_dump()
        
        # 3. Load corresponding schema
        schema = registry.load_schema("2025-26", "ITR1")
        
        # 4. Verify schema structure
        assert "version" in schema
        assert "type" in schema
        
        # 5. Test that models maintain data integrity
        restored_personal = PersonalInfo.model_validate(personal_json)
        restored_context = ReturnContext.model_validate(context_json)
        
        assert restored_personal.pan == personal_info.pan
        assert restored_context.assessment_year == return_context.assessment_year
        
        # 6. Test registry functionality
        available_schemas = registry.list_available_schemas()
        assert ("2025-26", "ITR1") in available_schemas
        assert ("2025-26", "ITR2") in available_schemas
    
    def test_error_handling_integration(self, registry):
        """Test error handling in integration scenarios."""
        # Test invalid schema lookup
        from core.schemas.registry import SchemaNotFoundError
        with pytest.raises(SchemaNotFoundError):
            registry.load_schema("2024-25", "ITR3")
        
        # Test invalid model data
        with pytest.raises(ValueError):
            PersonalInfo(
                pan="INVALID_PAN",
                name="Test User",
                date_of_birth="invalid-date",
                address="Test Address"
            )
        
        # Test model validation with invalid amounts
        with pytest.raises(ValueError):
            Salary(gross_salary=-1000.0)  # Negative amount should fail
    
    def test_model_field_validation_integration(self):
        """Test that model field validation works correctly in integration scenarios."""
        # Test PAN validation
        with pytest.raises(ValueError):
            PersonalInfo(
                pan="INVALID",
                name="Test User",
                date_of_birth="1990-01-01",
                address="Test Address"
            )
        
        # Test amount validation
        salary = Salary(gross_salary=100000.50)
        assert salary.gross_salary == 100000.50
        
        # Test calculated fields
        totals = Totals(
            gross_total_income=1000000.0,
            total_deductions=200000.0,
            tax_on_taxable_income=80000.0,
            total_taxes_paid=75000.0
        )
        assert totals.gross_total_income == 1000000.0
        assert totals.total_deductions == 200000.0
        assert totals.taxable_income == 800000.0  # This is computed from gross - deductions


if __name__ == "__main__":
    pytest.main([__file__])