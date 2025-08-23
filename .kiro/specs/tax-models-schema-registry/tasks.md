# Implementation Plan

- [x] 1. Set up base model infrastructure





  - Create base Pydantic models with common validation and configuration
  - Implement AmountModel with monetary validation
  - Add field validators for common tax-related constraints
  - _Requirements: 1.1, 1.4_
-

- [x] 2. Implement personal information models




  - Create PersonalInfo model with PAN validation
  - Implement ReturnContext model for assessment year and form type
  - Add date validation and format constraints
  - Write unit tests for personal info models
  - _Requirements: 1.1, 1.3, 4.1_

- [x] 3. Create income-related models





  - Implement Salary model with gross salary and allowances
  - Create HouseProperty model with annual value and deductions
  - Build CapitalGains model for short-term and long-term gains
  - Implement OtherSources model for interest and dividend income
  - Add validation for income calculations
  - _Requirements: 1.1, 1.3, 1.4_

- [x] 4. Build deductions and tax models





  - Create Deductions model with section-wise deductions (80C, 80D, 80G)
  - Implement TaxesPaid model for TDS, advance tax, and self-assessment
  - Build Totals model with calculated fields for tax liability
  - Add cross-field validation for tax calculations
  - _Requirements: 1.1, 1.3, 1.4_

- [x] 5. Implement schema registry system





  - Create SchemaRegistry class with path resolution logic
  - Implement schema loading and version retrieval methods
  - Add method to list available schemas
  - Handle file system errors gracefully
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 6. Create JSON schema stubs





  - Create directory structure for 2025-26 assessment year
  - Implement ITR1 JSON schema stub with basic structure
  - Create ITR2 JSON schema stub with extended fields
  - Add schema metadata and version information
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 7. Write comprehensive unit tests for models





  - Test round-trip serialization for all Pydantic models
  - Verify field validation rules and constraints
  - Test edge cases and invalid input handling
  - Add tests for calculated fields and business logic
  - _Requirements: 4.1, 4.4_

- [x] 8. Write unit tests for schema registry




  - Test path resolution for different AY/form combinations
  - Verify schema loading and version retrieval
  - Test error handling for missing files
  - Add tests for listing available schemas
  - _Requirements: 4.2, 4.4_

- [x] 9. Update package imports and dependencies





  - Add Pydantic dependency to core package requirements
  - Update __init__.py files to expose all models
  - Ensure proper module imports and exports
  - Update package configuration for new dependencies
  - _Requirements: 1.3_

- [x] 10. Integration testing and validation





  - Test model-schema compatibility
  - Verify registry works with actual schema files
  - Run complete test suite and ensure all tests pass
  - Validate that models can be imported successfully
  - _Requirements: 4.1, 4.2, 4.3_