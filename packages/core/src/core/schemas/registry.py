"""Schema registry for managing tax form schemas by assessment year and form type."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class SchemaRegistryError(Exception):
    """Base exception for schema registry errors."""
    pass


class SchemaNotFoundError(SchemaRegistryError):
    """Raised when a requested schema cannot be found."""
    pass


class SchemaLoadError(SchemaRegistryError):
    """Raised when a schema file cannot be loaded or parsed."""
    pass


class SchemaRegistry:
    """Registry for managing tax form schemas by assessment year and form type.
    
    This class provides methods to resolve schema file paths, load schemas,
    retrieve version information, and list available schemas. It handles
    file system errors gracefully and provides meaningful error messages.
    """
    
    def __init__(self, schemas_root: Optional[Path] = None):
        """Initialize the schema registry.
        
        Args:
            schemas_root: Root directory containing schema files. If None,
                         defaults to packages/schemas relative to this file.
        """
        if schemas_root is None:
            # Default to packages/schemas directory
            current_file = Path(__file__)
            # Navigate from packages/core/src/core/schemas/registry.py to packages/schemas
            self.schemas_root = current_file.parent.parent.parent.parent.parent / "schemas"
        else:
            self.schemas_root = Path(schemas_root)
        
        logger.debug(f"SchemaRegistry initialized with schemas_root: {self.schemas_root}")
    
    def get_schema_path(self, assessment_year: str, form_type: str) -> Path:
        """Get the file path for a specific schema.
        
        Args:
            assessment_year: Assessment year in format "YYYY-YY" (e.g., "2025-26")
            form_type: Form type (e.g., "ITR1", "ITR2")
            
        Returns:
            Path to the schema file
            
        Raises:
            ValueError: If assessment_year or form_type format is invalid
        """
        # Validate assessment year format
        if not self._is_valid_assessment_year(assessment_year):
            raise ValueError(f"Invalid assessment year format: {assessment_year}. Expected format: YYYY-YY")
        
        # Validate form type format
        if not self._is_valid_form_type(form_type):
            raise ValueError(f"Invalid form type: {form_type}. Expected format: ITR followed by digits")
        
        schema_path = self.schemas_root / assessment_year / form_type / "schema.json"
        logger.debug(f"Resolved schema path: {schema_path}")
        return schema_path
    
    def load_schema(self, assessment_year: str, form_type: str) -> Dict[str, Any]:
        """Load and return the JSON schema.
        
        Args:
            assessment_year: Assessment year in format "YYYY-YY"
            form_type: Form type (e.g., "ITR1", "ITR2")
            
        Returns:
            Dictionary containing the parsed JSON schema
            
        Raises:
            SchemaNotFoundError: If the schema file doesn't exist
            SchemaLoadError: If the schema file cannot be loaded or parsed
        """
        try:
            schema_path = self.get_schema_path(assessment_year, form_type)
            
            if not schema_path.exists():
                raise SchemaNotFoundError(
                    f"Schema file not found: {schema_path}. "
                    f"Assessment year: {assessment_year}, Form type: {form_type}"
                )
            
            if not schema_path.is_file():
                raise SchemaNotFoundError(
                    f"Schema path exists but is not a file: {schema_path}"
                )
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            logger.debug(f"Successfully loaded schema from {schema_path}")
            return schema_data
            
        except json.JSONDecodeError as e:
            raise SchemaLoadError(
                f"Failed to parse JSON schema file {schema_path}: {e}"
            ) from e
        except OSError as e:
            raise SchemaLoadError(
                f"Failed to read schema file {schema_path}: {e}"
            ) from e
        except ValueError as e:
            # Re-raise validation errors from get_schema_path
            raise SchemaRegistryError(str(e)) from e
    
    def get_schema_version(self, assessment_year: str, form_type: str) -> str:
        """Get the version of a specific schema.
        
        Args:
            assessment_year: Assessment year in format "YYYY-YY"
            form_type: Form type (e.g., "ITR1", "ITR2")
            
        Returns:
            Version string from the schema, defaults to "1.0.0" if not specified
            
        Raises:
            SchemaNotFoundError: If the schema file doesn't exist
            SchemaLoadError: If the schema file cannot be loaded or parsed
        """
        try:
            schema = self.load_schema(assessment_year, form_type)
            version = schema.get('version', '1.0.0')
            logger.debug(f"Schema version for {assessment_year}/{form_type}: {version}")
            return version
        except (SchemaNotFoundError, SchemaLoadError) as e:
            logger.error(f"Failed to get schema version: {e}")
            raise
    
    def list_available_schemas(self) -> List[Tuple[str, str]]:
        """List all available (assessment_year, form_type) combinations.
        
        Returns:
            List of tuples containing (assessment_year, form_type) pairs
            for all available schemas
        """
        schemas = []
        
        try:
            if not self.schemas_root.exists():
                logger.warning(f"Schemas root directory does not exist: {self.schemas_root}")
                return schemas
            
            if not self.schemas_root.is_dir():
                logger.warning(f"Schemas root path is not a directory: {self.schemas_root}")
                return schemas
            
            # Iterate through assessment year directories
            for ay_dir in self.schemas_root.iterdir():
                if not ay_dir.is_dir():
                    continue
                
                # Skip directories that don't match assessment year format
                if not self._is_valid_assessment_year(ay_dir.name):
                    logger.debug(f"Skipping invalid assessment year directory: {ay_dir.name}")
                    continue
                
                # Iterate through form type directories
                for form_dir in ay_dir.iterdir():
                    if not form_dir.is_dir():
                        continue
                    
                    # Check if schema.json exists
                    schema_file = form_dir / "schema.json"
                    if schema_file.exists() and schema_file.is_file():
                        schemas.append((ay_dir.name, form_dir.name))
                        logger.debug(f"Found schema: {ay_dir.name}/{form_dir.name}")
            
            logger.info(f"Found {len(schemas)} available schemas")
            return sorted(schemas)  # Sort for consistent ordering
            
        except OSError as e:
            logger.error(f"Error accessing schemas directory {self.schemas_root}: {e}")
            return schemas
    
    def _is_valid_assessment_year(self, assessment_year: str) -> bool:
        """Validate assessment year format (YYYY-YY).
        
        Args:
            assessment_year: Assessment year string to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not isinstance(assessment_year, str):
            return False
        
        if len(assessment_year) != 7:
            return False
        
        if assessment_year[4] != '-':
            return False
        
        try:
            start_year = int(assessment_year[:4])
            end_year = int(assessment_year[5:7])
            
            # Check if it's a valid year range (end year should be start year + 1)
            expected_end = (start_year + 1) % 100
            return end_year == expected_end and 2000 <= start_year <= 2099
            
        except ValueError:
            return False
    
    def _is_valid_form_type(self, form_type: str) -> bool:
        """Validate form type format (ITR followed by digits).
        
        Args:
            form_type: Form type string to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not isinstance(form_type, str):
            return False
        
        if not form_type.startswith('ITR'):
            return False
        
        if len(form_type) < 4:  # At least ITR + one digit
            return False
        
        # Check if the part after ITR contains only digits
        suffix = form_type[3:]
        return suffix.isdigit()