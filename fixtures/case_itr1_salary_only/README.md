# ITR-1 Salary Only Test Case

This fixture represents a simple ITR-1 return with only salary income, resulting in a net refund scenario.

## Scenario Details
- **Taxpayer**: Salaried individual with single employer
- **Income**: Only salary income (₹8,50,000 gross)
- **Deductions**: Standard deduction + basic exemptions
- **TDS**: Sufficient TDS deducted to result in refund
- **Expected Outcome**: Net refund, no self-assessment tax required

## Files Included
- `prefill.json` - Basic taxpayer information
- `form16b.pdf` - Clean Form 16B from single employer
- `ais.json` - AIS data with small interest income
- `expected_output.json` - Expected computation results
- `schema_validation.json` - Schema validation rules

## Test Objectives
- Verify deterministic parsing works correctly
- Ensure refund calculation is accurate
- Validate export JSON schema compliance
- Confirm no payment workflow is triggered