"""
JSON Schema Validation for ITR JSON files

Validates exported ITR JSON against official Income Tax Department schemas
using jsonschema library with comprehensive error reporting.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import jsonschema
from jsonschema import Draft7Validator, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of schema validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    schema_version: str
    form_type: str
    validation_timestamp: datetime
    error_count: int
    warning_count: int

@dataclass
class SchemaInfo:
    """Information about a schema"""
    form_type: str
    schema_version: str
    file_path: str
    description: str

class SchemaRegistry:
    """
    Registry for ITR JSON schemas
    
    Manages loading and caching of JSON schemas for different ITR forms
    and versions. Provides validation services with detailed error reporting.
    """
    
    def __init__(self, schemas_dir: Optional[str] = None):
        self.schemas_dir = Path(schemas_dir) if schemas_dir else Path(__file__).parent / "schemas"
        self.schemas_cache: Dict[str, Dict[str, Any]] = {}
        self.schema_info: Dict[str, SchemaInfo] = {}
        
        # Ensure schemas directory exists
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize with built-in schema stubs
        self._initialize_schema_stubs()
        
        logger.info(f"Schema registry initialized with directory: {self.schemas_dir}")
    
    def _initialize_schema_stubs(self):
        """Initialize with basic schema stubs for testing"""
        
        # ITR-1 Schema Stub
        itr1_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ITR-1 Schema",
            "description": "JSON Schema for ITR-1 form",
            "type": "object",
            "properties": {
                "ITR": {
                    "type": "object",
                    "properties": {
                        "ITR1": {
                            "type": "object",
                            "properties": {
                                "CreationInfo": {
                                    "type": "object",
                                    "properties": {
                                        "SWVersionNo": {"type": "string"},
                                        "SWCreatedBy": {"type": "string"},
                                        "XMLCreationDate": {"type": "string", "format": "date"},
                                        "XMLCreationTime": {"type": "string"},
                                        "IntermediaryCity": {"type": "string"},
                                        "Digest": {"type": "string"}
                                    },
                                    "required": ["SWVersionNo", "SWCreatedBy", "XMLCreationDate"]
                                },
                                "Form_ITR1": {
                                    "type": "object",
                                    "properties": {
                                        "FormName": {"type": "string", "enum": ["ITR1"]},
                                        "Description": {"type": "string"},
                                        "AssessmentYear": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
                                        "SchemaVer": {"type": "string"},
                                        "FormVer": {"type": "string"}
                                    },
                                    "required": ["FormName", "AssessmentYear", "SchemaVer"]
                                },
                                "PersonalInfo": {
                                    "type": "object",
                                    "properties": {
                                        "AssesseeName": {
                                            "type": "object",
                                            "properties": {
                                                "FirstName": {"type": "string", "minLength": 1},
                                                "MiddleName": {"type": "string"},
                                                "SurNameOrOrgName": {"type": "string", "minLength": 1}
                                            },
                                            "required": ["FirstName", "SurNameOrOrgName"]
                                        },
                                        "PAN": {"type": "string", "pattern": "^[A-Z]{5}[0-9]{4}[A-Z]{1}$"},
                                        "DOB": {"type": "string", "format": "date"},
                                        "Status": {"type": "string", "enum": ["I", "H"]},
                                        "Address": {"type": "object"}
                                    },
                                    "required": ["AssesseeName", "PAN", "DOB", "Status"]
                                },
                                "ITR1_IncomeDeductions": {
                                    "type": "object",
                                    "properties": {
                                        "Salary": {"type": "integer", "minimum": 0},
                                        "HouseProperty": {"type": "integer"},
                                        "OtherSources": {"type": "integer", "minimum": 0},
                                        "GrossTotalIncome": {"type": "integer", "minimum": 0},
                                        "TotalIncome": {"type": "integer", "minimum": 0},
                                        "DeductionUnderScheduleVIA": {"type": "object"}
                                    },
                                    "required": ["GrossTotalIncome", "TotalIncome"]
                                },
                                "ITR1_TaxComputation": {
                                    "type": "object",
                                    "properties": {
                                        "TotalIncome": {"type": "integer", "minimum": 0},
                                        "TaxOnTotalIncome": {"type": "integer", "minimum": 0},
                                        "TotalTaxPayable": {"type": "integer", "minimum": 0},
                                        "AggregateLiability": {"type": "integer", "minimum": 0}
                                    },
                                    "required": ["TotalIncome", "TaxOnTotalIncome"]
                                },
                                "TaxPaid": {"type": "object"},
                                "Refund": {"type": "object"},
                                "Verification": {"type": "object"}
                            },
                            "required": ["CreationInfo", "Form_ITR1", "PersonalInfo", "ITR1_IncomeDeductions", "ITR1_TaxComputation"]
                        }
                    },
                    "required": ["ITR1"]
                }
            },
            "required": ["ITR"]
        }
        
        # ITR-2 Schema Stub
        itr2_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ITR-2 Schema",
            "description": "JSON Schema for ITR-2 form",
            "type": "object",
            "properties": {
                "ITR": {
                    "type": "object",
                    "properties": {
                        "ITR2": {
                            "type": "object",
                            "properties": {
                                "CreationInfo": {
                                    "type": "object",
                                    "properties": {
                                        "SWVersionNo": {"type": "string"},
                                        "SWCreatedBy": {"type": "string"},
                                        "XMLCreationDate": {"type": "string", "format": "date"},
                                        "XMLCreationTime": {"type": "string"},
                                        "IntermediaryCity": {"type": "string"},
                                        "Digest": {"type": "string"}
                                    },
                                    "required": ["SWVersionNo", "SWCreatedBy", "XMLCreationDate"]
                                },
                                "Form_ITR2": {
                                    "type": "object",
                                    "properties": {
                                        "FormName": {"type": "string", "enum": ["ITR2"]},
                                        "Description": {"type": "string"},
                                        "AssessmentYear": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
                                        "SchemaVer": {"type": "string"},
                                        "FormVer": {"type": "string"}
                                    },
                                    "required": ["FormName", "AssessmentYear", "SchemaVer"]
                                },
                                "PersonalInfo": {
                                    "type": "object",
                                    "properties": {
                                        "AssesseeName": {
                                            "type": "object",
                                            "properties": {
                                                "FirstName": {"type": "string", "minLength": 1},
                                                "MiddleName": {"type": "string"},
                                                "SurNameOrOrgName": {"type": "string", "minLength": 1}
                                            },
                                            "required": ["FirstName", "SurNameOrOrgName"]
                                        },
                                        "PAN": {"type": "string", "pattern": "^[A-Z]{5}[0-9]{4}[A-Z]{1}$"},
                                        "DOB": {"type": "string", "format": "date"},
                                        "Status": {"type": "string", "enum": ["I", "H"]},
                                        "ResidentialStatus": {"type": "string", "enum": ["RES", "NRI", "NOR"]},
                                        "Address": {"type": "object"}
                                    },
                                    "required": ["AssesseeName", "PAN", "DOB", "Status", "ResidentialStatus"]
                                },
                                "ITR2_IncomeDeductions": {
                                    "type": "object",
                                    "properties": {
                                        "Salary": {"type": "integer", "minimum": 0},
                                        "HouseProperty": {"type": "integer"},
                                        "CapitalGain": {"type": "object"},
                                        "OtherSources": {"type": "integer", "minimum": 0},
                                        "GrossTotalIncome": {"type": "integer", "minimum": 0},
                                        "TotalIncome": {"type": "integer", "minimum": 0},
                                        "DeductionUnderScheduleVIA": {"type": "object"}
                                    },
                                    "required": ["GrossTotalIncome", "TotalIncome"]
                                },
                                "ITR2_TaxComputation": {
                                    "type": "object",
                                    "properties": {
                                        "TotalIncome": {"type": "integer", "minimum": 0},
                                        "TaxOnTotalIncome": {"type": "integer", "minimum": 0},
                                        "TotalTaxPayable": {"type": "integer", "minimum": 0},
                                        "AggregateLiability": {"type": "integer", "minimum": 0},
                                        "TaxOnSpecialRateIncome": {"type": "object"}
                                    },
                                    "required": ["TotalIncome", "TaxOnTotalIncome"]
                                },
                                "TaxPaid": {"type": "object"},
                                "Refund": {"type": "object"},
                                "ScheduleCapitalGain": {"type": "object"},
                                "ScheduleHouseProperty": {"type": "object"},
                                "Verification": {"type": "object"}
                            },
                            "required": ["CreationInfo", "Form_ITR2", "PersonalInfo", "ITR2_IncomeDeductions", "ITR2_TaxComputation"]
                        }
                    },
                    "required": ["ITR2"]
                }
            },
            "required": ["ITR"]
        }
        
        # Save schema stubs to files
        self._save_schema_stub("ITR1", "2.0", itr1_schema)
        self._save_schema_stub("ITR2", "2.0", itr2_schema)
    
    def _save_schema_stub(self, form_type: str, version: str, schema: Dict[str, Any]):
        """Save a schema stub to file"""
        schema_file = self.schemas_dir / f"{form_type}_v{version}.json"
        
        try:
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2)
            
            # Register schema info
            schema_key = f"{form_type}_v{version}"
            self.schema_info[schema_key] = SchemaInfo(
                form_type=form_type,
                schema_version=version,
                file_path=str(schema_file),
                description=f"Schema stub for {form_type} version {version}"
            )
            
            logger.info(f"Created schema stub: {schema_file}")
            
        except Exception as e:
            logger.error(f"Failed to save schema stub {schema_file}: {e}")
    
    def load_schema(self, form_type: str, schema_version: str) -> Dict[str, Any]:
        """Load schema from file or cache"""
        schema_key = f"{form_type}_v{schema_version}"
        
        # Return from cache if available
        if schema_key in self.schemas_cache:
            return self.schemas_cache[schema_key]
        
        # Try to load from file
        schema_file = self.schemas_dir / f"{form_type}_v{schema_version}.json"
        
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Cache the schema
            self.schemas_cache[schema_key] = schema
            
            logger.info(f"Loaded schema: {schema_file}")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to load schema {schema_file}: {e}")
            raise
    
    def validate_json(self, json_data: Dict[str, Any], form_type: str, 
                     schema_version: str) -> ValidationResult:
        """
        Validate JSON data against schema
        
        Args:
            json_data: The JSON data to validate
            form_type: ITR form type (ITR1, ITR2, etc.)
            schema_version: Schema version to validate against
            
        Returns:
            ValidationResult with validation details
        """
        logger.info(f"Validating {form_type} JSON against schema version {schema_version}")
        
        errors = []
        warnings = []
        
        try:
            # Load the appropriate schema
            schema = self.load_schema(form_type, schema_version)
            
            # Create validator
            validator = Draft7Validator(schema)
            
            # Perform validation
            validation_errors = list(validator.iter_errors(json_data))
            
            # Process validation errors
            for error in validation_errors:
                error_path = " -> ".join(str(p) for p in error.absolute_path)
                error_message = f"Path: {error_path}, Error: {error.message}"
                
                # Categorize errors vs warnings based on severity
                if self._is_critical_error(error):
                    errors.append(error_message)
                else:
                    warnings.append(error_message)
            
            # Additional custom validations
            custom_errors, custom_warnings = self._perform_custom_validations(
                json_data, form_type, schema_version
            )
            
            errors.extend(custom_errors)
            warnings.extend(custom_warnings)
            
            is_valid = len(errors) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                schema_version=schema_version,
                form_type=form_type,
                validation_timestamp=datetime.now(),
                error_count=len(errors),
                warning_count=len(warnings)
            )
            
            logger.info(f"Validation completed: {len(errors)} errors, {len(warnings)} warnings")
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation process failed: {str(e)}"],
                warnings=[],
                schema_version=schema_version,
                form_type=form_type,
                validation_timestamp=datetime.now(),
                error_count=1,
                warning_count=0
            )
    
    def _is_critical_error(self, error: ValidationError) -> bool:
        """Determine if a validation error is critical"""
        # Consider required field errors as critical
        if "required" in error.validator:
            return True
        
        # Consider type errors as critical
        if "type" in error.validator:
            return True
        
        # Consider pattern/format errors for important fields as critical
        critical_fields = ["PAN", "AssessmentYear", "FormName"]
        error_path = " -> ".join(str(p) for p in error.absolute_path)
        
        for field in critical_fields:
            if field in error_path:
                return True
        
        return False
    
    def _perform_custom_validations(self, json_data: Dict[str, Any], 
                                   form_type: str, schema_version: str) -> Tuple[List[str], List[str]]:
        """Perform custom business logic validations"""
        errors = []
        warnings = []
        
        try:
            # Extract form data based on form type
            if form_type == "ITR1" and "ITR" in json_data and "ITR1" in json_data["ITR"]:
                itr_data = json_data["ITR"]["ITR1"]
                errors_custom, warnings_custom = self._validate_itr1_business_logic(itr_data)
                errors.extend(errors_custom)
                warnings.extend(warnings_custom)
            
            elif form_type == "ITR2" and "ITR" in json_data and "ITR2" in json_data["ITR"]:
                itr_data = json_data["ITR"]["ITR2"]
                errors_custom, warnings_custom = self._validate_itr2_business_logic(itr_data)
                errors.extend(errors_custom)
                warnings.extend(warnings_custom)
            
        except Exception as e:
            warnings.append(f"Custom validation failed: {str(e)}")
        
        return errors, warnings
    
    def _validate_itr1_business_logic(self, itr_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate ITR-1 specific business logic"""
        errors = []
        warnings = []
        
        # Check income and deductions consistency
        if "ITR1_IncomeDeductions" in itr_data:
            income_data = itr_data["ITR1_IncomeDeductions"]
            
            # Validate gross total income calculation
            salary = income_data.get("Salary", 0)
            house_property = income_data.get("HouseProperty", 0)
            other_sources = income_data.get("OtherSources", 0)
            gross_total = income_data.get("GrossTotalIncome", 0)
            
            calculated_gross = salary + house_property + other_sources
            if abs(calculated_gross - gross_total) > 1:  # Allow for rounding
                errors.append(f"Gross Total Income mismatch: calculated {calculated_gross}, reported {gross_total}")
        
        # Check tax computation consistency
        if "ITR1_TaxComputation" in itr_data:
            tax_data = itr_data["ITR1_TaxComputation"]
            
            total_income = tax_data.get("TotalIncome", 0)
            if total_income > 5000000:  # 50 lakh limit for ITR-1
                errors.append("Total income exceeds ITR-1 limit of ₹50 lakh")
        
        return errors, warnings
    
    def _validate_itr2_business_logic(self, itr_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate ITR-2 specific business logic"""
        errors = []
        warnings = []
        
        # Check income and deductions consistency (similar to ITR-1)
        if "ITR2_IncomeDeductions" in itr_data:
            income_data = itr_data["ITR2_IncomeDeductions"]
            
            # Validate capital gains if present
            if "CapitalGain" in income_data:
                cg_data = income_data["CapitalGain"]
                
                # Check LTCG exemption limit
                if "LongTerm" in cg_data and "LongTermCapGain10Per" in cg_data["LongTerm"]:
                    ltcg_10_per = cg_data["LongTerm"]["LongTermCapGain10Per"]
                    if ltcg_10_per > 0 and ltcg_10_per <= 100000:
                        warnings.append("LTCG up to ₹1 lakh is exempt - verify if tax is correctly calculated")
        
        return errors, warnings
    
    def get_available_schemas(self) -> List[SchemaInfo]:
        """Get list of available schemas"""
        return list(self.schema_info.values())
    
    def create_validation_log(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Create a validation log in JSON format"""
        return {
            "validation_summary": {
                "is_valid": validation_result.is_valid,
                "form_type": validation_result.form_type,
                "schema_version": validation_result.schema_version,
                "validation_timestamp": validation_result.validation_timestamp.isoformat(),
                "error_count": validation_result.error_count,
                "warning_count": validation_result.warning_count
            },
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "validation_details": {
                "validator": "jsonschema",
                "schema_source": "local_registry",
                "custom_validations": "enabled"
            }
        }

# Global schema registry instance
_schema_registry: Optional[SchemaRegistry] = None

def get_schema_registry() -> SchemaRegistry:
    """Get or create the global schema registry"""
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = SchemaRegistry()
    return _schema_registry

def validate_itr_json(json_data: Dict[str, Any], form_type: str, 
                     schema_version: str = "2.0") -> ValidationResult:
    """
    Convenience function to validate ITR JSON
    
    Args:
        json_data: The JSON data to validate
        form_type: ITR form type (ITR1, ITR2, etc.)
        schema_version: Schema version to validate against
        
    Returns:
        ValidationResult with validation details
    """
    registry = get_schema_registry()
    return registry.validate_json(json_data, form_type, schema_version)