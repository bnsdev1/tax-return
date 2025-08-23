"""Tests for the schema registry system."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from core.schemas.registry import (
    SchemaRegistry,
    SchemaRegistryError,
    SchemaNotFoundError,
    SchemaLoadError,
)


class TestSchemaRegistry:
    """Test cases for SchemaRegistry class."""
    
    def test_init_default_path(self):
        """Test SchemaRegistry initialization with default path."""
        registry = SchemaRegistry()
        
        # Should resolve to packages/schemas relative to the registry file
        # From packages/core/tests/test_schema_registry.py to packages/schemas
        expected_path = Path(__file__).parent.parent.parent / "schemas"
        assert registry.schemas_root == expected_path
    
    def test_init_custom_path(self):
        """Test SchemaRegistry initialization with custom path."""
        custom_path = Path("/custom/schemas")
        registry = SchemaRegistry(schemas_root=custom_path)
        
        assert registry.schemas_root == custom_path
    
    def test_get_schema_path_valid(self):
        """Test get_schema_path with valid inputs."""
        registry = SchemaRegistry()
        
        path = registry.get_schema_path("2025-26", "ITR1")
        expected = registry.schemas_root / "2025-26" / "ITR1" / "schema.json"
        
        assert path == expected
    
    def test_get_schema_path_invalid_assessment_year(self):
        """Test get_schema_path with invalid assessment year format."""
        registry = SchemaRegistry()
        
        with pytest.raises(ValueError, match="Invalid assessment year format"):
            registry.get_schema_path("2025", "ITR1")
        
        with pytest.raises(ValueError, match="Invalid assessment year format"):
            registry.get_schema_path("25-26", "ITR1")
        
        with pytest.raises(ValueError, match="Invalid assessment year format"):
            registry.get_schema_path("2025-27", "ITR1")  # Invalid year sequence
    
    def test_get_schema_path_invalid_form_type(self):
        """Test get_schema_path with invalid form type format."""
        registry = SchemaRegistry()
        
        with pytest.raises(ValueError, match="Invalid form type"):
            registry.get_schema_path("2025-26", "FORM1")
        
        with pytest.raises(ValueError, match="Invalid form type"):
            registry.get_schema_path("2025-26", "ITR")
        
        with pytest.raises(ValueError, match="Invalid form type"):
            registry.get_schema_path("2025-26", "ITRabc")
    
    def test_load_schema_success(self):
        """Test successful schema loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test schema structure
            schema_dir = temp_path / "2025-26" / "ITR1"
            schema_dir.mkdir(parents=True)
            
            test_schema = {
                "version": "1.0.0",
                "type": "object",
                "properties": {"test": {"type": "string"}}
            }
            
            schema_file = schema_dir / "schema.json"
            with open(schema_file, 'w') as f:
                json.dump(test_schema, f)
            
            registry = SchemaRegistry(schemas_root=temp_path)
            loaded_schema = registry.load_schema("2025-26", "ITR1")
            
            assert loaded_schema == test_schema
    
    def test_load_schema_file_not_found(self):
        """Test schema loading when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = SchemaRegistry(schemas_root=Path(temp_dir))
            
            with pytest.raises(SchemaNotFoundError, match="Schema file not found"):
                registry.load_schema("2025-26", "ITR1")
    
    def test_load_schema_invalid_json(self):
        """Test schema loading with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test schema structure with invalid JSON
            schema_dir = temp_path / "2025-26" / "ITR1"
            schema_dir.mkdir(parents=True)
            
            schema_file = schema_dir / "schema.json"
            with open(schema_file, 'w') as f:
                f.write("{ invalid json }")
            
            registry = SchemaRegistry(schemas_root=temp_path)
            
            with pytest.raises(SchemaLoadError, match="Failed to parse JSON schema file"):
                registry.load_schema("2025-26", "ITR1")
    
    def test_load_schema_path_is_directory(self):
        """Test schema loading when path exists but is a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure but make schema.json a directory
            schema_dir = temp_path / "2025-26" / "ITR1"
            schema_dir.mkdir(parents=True)
            (schema_dir / "schema.json").mkdir()  # Create as directory, not file
            
            registry = SchemaRegistry(schemas_root=temp_path)
            
            with pytest.raises(SchemaNotFoundError, match="exists but is not a file"):
                registry.load_schema("2025-26", "ITR1")
    
    def test_get_schema_version_success(self):
        """Test successful schema version retrieval."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test schema structure
            schema_dir = temp_path / "2025-26" / "ITR1"
            schema_dir.mkdir(parents=True)
            
            test_schema = {"version": "2.1.0", "type": "object"}
            
            schema_file = schema_dir / "schema.json"
            with open(schema_file, 'w') as f:
                json.dump(test_schema, f)
            
            registry = SchemaRegistry(schemas_root=temp_path)
            version = registry.get_schema_version("2025-26", "ITR1")
            
            assert version == "2.1.0"
    
    def test_get_schema_version_default(self):
        """Test schema version retrieval with default version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test schema structure without version
            schema_dir = temp_path / "2025-26" / "ITR1"
            schema_dir.mkdir(parents=True)
            
            test_schema = {"type": "object"}  # No version field
            
            schema_file = schema_dir / "schema.json"
            with open(schema_file, 'w') as f:
                json.dump(test_schema, f)
            
            registry = SchemaRegistry(schemas_root=temp_path)
            version = registry.get_schema_version("2025-26", "ITR1")
            
            assert version == "1.0.0"  # Default version
    
    def test_get_schema_version_file_not_found(self):
        """Test schema version retrieval when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = SchemaRegistry(schemas_root=Path(temp_dir))
            
            with pytest.raises(SchemaNotFoundError):
                registry.get_schema_version("2025-26", "ITR1")
    
    def test_list_available_schemas_success(self):
        """Test successful listing of available schemas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple schema structures
            schemas_to_create = [
                ("2025-26", "ITR1"),
                ("2025-26", "ITR2"),
                ("2024-25", "ITR1"),
            ]
            
            for ay, form_type in schemas_to_create:
                schema_dir = temp_path / ay / form_type
                schema_dir.mkdir(parents=True)
                
                schema_file = schema_dir / "schema.json"
                with open(schema_file, 'w') as f:
                    json.dump({"type": "object"}, f)
            
            # Create a directory without schema.json (should be ignored)
            incomplete_dir = temp_path / "2023-24" / "ITR1"
            incomplete_dir.mkdir(parents=True)
            
            # Create a file in root (should be ignored)
            (temp_path / "not_a_directory.txt").touch()
            
            registry = SchemaRegistry(schemas_root=temp_path)
            available_schemas = registry.list_available_schemas()
            
            expected = [
                ("2024-25", "ITR1"),
                ("2025-26", "ITR1"),
                ("2025-26", "ITR2"),
            ]
            
            assert available_schemas == expected
    
    def test_list_available_schemas_empty_directory(self):
        """Test listing schemas in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = SchemaRegistry(schemas_root=Path(temp_dir))
            available_schemas = registry.list_available_schemas()
            
            assert available_schemas == []
    
    def test_list_available_schemas_nonexistent_directory(self):
        """Test listing schemas when root directory doesn't exist."""
        nonexistent_path = Path("/nonexistent/path")
        registry = SchemaRegistry(schemas_root=nonexistent_path)
        available_schemas = registry.list_available_schemas()
        
        assert available_schemas == []
    
    def test_list_available_schemas_invalid_assessment_years(self):
        """Test that invalid assessment year directories are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid schema
            valid_dir = temp_path / "2025-26" / "ITR1"
            valid_dir.mkdir(parents=True)
            with open(valid_dir / "schema.json", 'w') as f:
                json.dump({"type": "object"}, f)
            
            # Create invalid assessment year directories
            invalid_dirs = [
                "2025",      # Missing year range
                "25-26",     # Wrong format
                "2025-27",   # Invalid year sequence
                "invalid",   # Not a year at all
            ]
            
            for invalid_ay in invalid_dirs:
                invalid_dir = temp_path / invalid_ay / "ITR1"
                invalid_dir.mkdir(parents=True)
                with open(invalid_dir / "schema.json", 'w') as f:
                    json.dump({"type": "object"}, f)
            
            registry = SchemaRegistry(schemas_root=temp_path)
            available_schemas = registry.list_available_schemas()
            
            # Should only return the valid schema
            assert available_schemas == [("2025-26", "ITR1")]
    
    def test_is_valid_assessment_year(self):
        """Test assessment year validation."""
        registry = SchemaRegistry()
        
        # Valid cases
        assert registry._is_valid_assessment_year("2025-26") is True
        assert registry._is_valid_assessment_year("2024-25") is True
        assert registry._is_valid_assessment_year("2099-00") is True
        
        # Invalid cases
        assert registry._is_valid_assessment_year("2025") is False
        assert registry._is_valid_assessment_year("25-26") is False
        assert registry._is_valid_assessment_year("2025-27") is False  # Wrong sequence
        assert registry._is_valid_assessment_year("2025_26") is False  # Wrong separator
        assert registry._is_valid_assessment_year("invalid") is False
        assert registry._is_valid_assessment_year("") is False
        assert registry._is_valid_assessment_year(None) is False
        assert registry._is_valid_assessment_year(2025) is False  # Not a string
    
    def test_is_valid_form_type(self):
        """Test form type validation."""
        registry = SchemaRegistry()
        
        # Valid cases
        assert registry._is_valid_form_type("ITR1") is True
        assert registry._is_valid_form_type("ITR2") is True
        assert registry._is_valid_form_type("ITR12") is True
        assert registry._is_valid_form_type("ITR123") is True
        
        # Invalid cases
        assert registry._is_valid_form_type("ITR") is False  # No digits
        assert registry._is_valid_form_type("FORM1") is False  # Wrong prefix
        assert registry._is_valid_form_type("ITRabc") is False  # Non-digits after ITR
        assert registry._is_valid_form_type("ITR1a") is False  # Mixed digits and letters
        assert registry._is_valid_form_type("itr1") is False  # Wrong case
        assert registry._is_valid_form_type("") is False
        assert registry._is_valid_form_type(None) is False
        assert registry._is_valid_form_type(1) is False  # Not a string


class TestSchemaRegistryIntegration:
    """Integration tests using actual schema files."""
    
    def test_load_actual_schemas(self):
        """Test loading actual schema files from the project."""
        registry = SchemaRegistry()
        
        # Test loading ITR1 schema
        try:
            itr1_schema = registry.load_schema("2025-26", "ITR1")
            assert isinstance(itr1_schema, dict)
            assert "version" in itr1_schema
            assert itr1_schema["title"] == "ITR1 Schema"
        except (SchemaNotFoundError, SchemaLoadError):
            pytest.skip("ITR1 schema file not available for integration test")
        
        # Test loading ITR2 schema
        try:
            itr2_schema = registry.load_schema("2025-26", "ITR2")
            assert isinstance(itr2_schema, dict)
            assert "version" in itr2_schema
            assert itr2_schema["title"] == "ITR2 Schema"
        except (SchemaNotFoundError, SchemaLoadError):
            pytest.skip("ITR2 schema file not available for integration test")
    
    def test_list_actual_schemas(self):
        """Test listing actual schema files from the project."""
        registry = SchemaRegistry()
        
        available_schemas = registry.list_available_schemas()
        
        # Should be a list of tuples
        assert isinstance(available_schemas, list)
        for schema_info in available_schemas:
            assert isinstance(schema_info, tuple)
            assert len(schema_info) == 2
            ay, form_type = schema_info
            assert isinstance(ay, str)
            assert isinstance(form_type, str)
            # Validate format
            assert registry._is_valid_assessment_year(ay)
            assert registry._is_valid_form_type(form_type)