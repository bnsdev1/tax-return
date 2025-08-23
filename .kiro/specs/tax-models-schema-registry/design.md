# Design Document

## Overview

This design implements a comprehensive tax return data modeling system using Pydantic for validation and serialization, combined with a schema registry for managing different assessment years and form types. The system provides type-safe models for Indian tax returns (ITR1/ITR2) with proper validation and schema versioning.

## Architecture

The system consists of three main components:

1. **Pydantic Models** - Type-safe data models with validation
2. **Schema Registry** - Dynamic schema resolution and management
3. **JSON Schemas** - Form-specific validation schemas

```
packages/core/
├── models/
│   ├── __init__.py
│   ├── base.py          # Base model classes
│   ├── personal.py      # PersonalInfo, ReturnContext
│   ├── income.py        # Salary, HouseProperty, CapitalGains, OtherSources
│   ├── deductions.py    # Deductions model
│   ├── taxes.py         # TaxesPaid model
│   └── totals.py        # Totals model
├── schemas/
│   └── registry.py      # SchemaRegistry class
└── tests/
    ├── test_models.py
    └── test_registry.py

packages/schemas/
└── 2025-26/
    ├── ITR1/
    │   └── schema.json
    └── ITR2/
        └── schema.json
```

## Components and Interfaces

### Base Models

```python
# packages/core/models/base.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class TaxBaseModel(BaseModel):
    """Base model for all tax-related models."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

class AmountModel(TaxBaseModel):
    """Base model for monetary amounts."""
    amount: float = 0.0
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return round(v, 2)
```

### Personal Information Models

```python
# packages/core/models/personal.py
class PersonalInfo(TaxBaseModel):
    pan: str
    name: str
    father_name: Optional[str] = None
    date_of_birth: date
    address: str
    mobile: Optional[str] = None
    email: Optional[str] = None

class ReturnContext(TaxBaseModel):
    assessment_year: str  # e.g., "2025-26"
    form_type: str       # e.g., "ITR1", "ITR2"
    filing_date: Optional[date] = None
    revised_return: bool = False
```

### Income Models

```python
# packages/core/models/income.py
class Salary(AmountModel):
    gross_salary: float = 0.0
    allowances: float = 0.0
    perquisites: float = 0.0
    profits_in_lieu: float = 0.0
    total_salary: float = 0.0

class HouseProperty(AmountModel):
    annual_value: float = 0.0
    municipal_tax: float = 0.0
    standard_deduction: float = 0.0
    interest_on_loan: float = 0.0
    net_income: float = 0.0

class CapitalGains(AmountModel):
    short_term: float = 0.0
    long_term: float = 0.0
    total_capital_gains: float = 0.0

class OtherSources(AmountModel):
    interest_income: float = 0.0
    dividend_income: float = 0.0
    other_income: float = 0.0
    total_other_sources: float = 0.0
```

### Deductions and Tax Models

```python
# packages/core/models/deductions.py
class Deductions(AmountModel):
    section_80c: float = 0.0
    section_80d: float = 0.0
    section_80g: float = 0.0
    other_deductions: float = 0.0
    total_deductions: float = 0.0

# packages/core/models/taxes.py
class TaxesPaid(AmountModel):
    tds: float = 0.0
    advance_tax: float = 0.0
    self_assessment_tax: float = 0.0
    total_taxes_paid: float = 0.0

# packages/core/models/totals.py
class Totals(AmountModel):
    gross_total_income: float = 0.0
    total_deductions: float = 0.0
    taxable_income: float = 0.0
    tax_on_taxable_income: float = 0.0
    total_tax_liability: float = 0.0
    refund_or_payable: float = 0.0
```

### Schema Registry

```python
# packages/core/schemas/registry.py
from pathlib import Path
from typing import Dict, Optional, Tuple
import json

class SchemaRegistry:
    """Registry for managing tax form schemas by assessment year and form type."""
    
    def __init__(self, schemas_root: Optional[Path] = None):
        self.schemas_root = schemas_root or Path(__file__).parent.parent.parent / "schemas"
    
    def get_schema_path(self, assessment_year: str, form_type: str) -> Path:
        """Get the file path for a specific schema."""
        return self.schemas_root / assessment_year / form_type / "schema.json"
    
    def load_schema(self, assessment_year: str, form_type: str) -> Dict:
        """Load and return the JSON schema."""
        schema_path = self.get_schema_path(assessment_year, form_type)
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    def get_schema_version(self, assessment_year: str, form_type: str) -> str:
        """Get the version of a specific schema."""
        schema = self.load_schema(assessment_year, form_type)
        return schema.get('version', '1.0.0')
    
    def list_available_schemas(self) -> List[Tuple[str, str]]:
        """List all available (assessment_year, form_type) combinations."""
        schemas = []
        for ay_dir in self.schemas_root.iterdir():
            if ay_dir.is_dir():
                for form_dir in ay_dir.iterdir():
                    if form_dir.is_dir() and (form_dir / "schema.json").exists():
                        schemas.append((ay_dir.name, form_dir.name))
        return schemas
```

## Data Models

### Model Relationships

```
PersonalInfo + ReturnContext
    ↓
Income Models (Salary, HouseProperty, CapitalGains, OtherSources)
    ↓
Deductions
    ↓
Totals (calculated from above)
    ↓
TaxesPaid
```

### Validation Rules

1. **Amount Validation**: All monetary fields must be non-negative and rounded to 2 decimal places
2. **PAN Validation**: PAN must follow the standard format (AAAAA9999A)
3. **Date Validation**: Dates must be valid and within reasonable ranges
4. **Assessment Year**: Must follow the format "YYYY-YY" (e.g., "2025-26")
5. **Form Type**: Must be one of the supported form types (ITR1, ITR2, etc.)

## Error Handling

### Model Validation Errors
- Use Pydantic's built-in validation with custom error messages
- Provide field-level validation for complex business rules
- Return structured error responses with field names and error descriptions

### Schema Registry Errors
- Handle missing schema files gracefully
- Validate assessment year and form type formats
- Provide meaningful error messages for invalid lookups

### File System Errors
- Handle missing directories or files
- Provide fallback mechanisms for schema loading
- Log errors appropriately for debugging

## Testing Strategy

### Unit Tests for Models
1. **Serialization Tests**: Verify round-trip JSON serialization/deserialization
2. **Validation Tests**: Test field validation rules and constraints
3. **Business Logic Tests**: Verify calculated fields and relationships
4. **Edge Case Tests**: Test boundary conditions and invalid inputs

### Unit Tests for Schema Registry
1. **Path Resolution Tests**: Verify correct file path generation
2. **Schema Loading Tests**: Test schema file loading and parsing
3. **Version Retrieval Tests**: Verify version information extraction
4. **Error Handling Tests**: Test behavior with missing files/invalid inputs

### Integration Tests
1. **Model-Schema Compatibility**: Verify models match their JSON schemas
2. **Registry-File System**: Test registry with actual schema files
3. **End-to-End Validation**: Test complete tax return data flow

### Test Data Strategy
- Use realistic but anonymized tax return data
- Create fixtures for different scenarios (ITR1 vs ITR2, different income types)
- Test with edge cases (zero income, maximum deductions, etc.)
- Validate against actual ITR form requirements where possible