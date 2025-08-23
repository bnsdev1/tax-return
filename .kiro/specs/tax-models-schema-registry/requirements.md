# Requirements Document

## Introduction

This feature adds comprehensive Pydantic models for Indian tax return data structures and implements a schema registry system to manage different assessment years and form types. The system will support ITR1 and ITR2 forms with proper validation, serialization, and schema versioning capabilities.

## Requirements

### Requirement 1

**User Story:** As a developer, I want strongly typed Pydantic models for tax return data, so that I can ensure data validation and type safety across the application.

#### Acceptance Criteria

1. WHEN creating tax return data THEN the system SHALL validate all fields using Pydantic models
2. WHEN serializing model data THEN the system SHALL produce valid JSON that can be round-trip deserialized
3. WHEN importing models THEN the system SHALL expose PersonalInfo, ReturnContext, Salary, HouseProperty, CapitalGains, OtherSources, Deductions, TaxesPaid, and Totals models
4. WHEN validating model fields THEN the system SHALL enforce appropriate data types and constraints

### Requirement 2

**User Story:** As a developer, I want a schema registry system, so that I can dynamically resolve schema files based on assessment year and form type.

#### Acceptance Criteria

1. WHEN querying the registry with assessment year and form type THEN the system SHALL return the correct file path
2. WHEN requesting schema version information THEN the system SHALL provide version metadata
3. WHEN looking up ITR1 or ITR2 schemas THEN the system SHALL resolve to the appropriate JSON schema file
4. WHEN the registry is initialized THEN the system SHALL validate that required schema files exist

### Requirement 3

**User Story:** As a developer, I want JSON schema stubs for ITR1 and ITR2 forms, so that I can validate form-specific data structures.

#### Acceptance Criteria

1. WHEN accessing ITR1 schema THEN the system SHALL provide a valid JSON schema structure
2. WHEN accessing ITR2 schema THEN the system SHALL provide a valid JSON schema structure
3. WHEN schemas are organized THEN the system SHALL use assessment year directories (e.g., 2025-26)
4. WHEN schema files are created THEN the system SHALL include proper metadata and version information

### Requirement 4

**User Story:** As a developer, I want comprehensive unit tests, so that I can verify model serialization and registry functionality work correctly.

#### Acceptance Criteria

1. WHEN running model tests THEN the system SHALL verify round-trip serialization for all models
2. WHEN testing the registry THEN the system SHALL verify correct path resolution for different AY/form combinations
3. WHEN executing test suite THEN all tests SHALL pass without errors
4. WHEN testing edge cases THEN the system SHALL handle invalid inputs gracefully