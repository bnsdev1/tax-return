# ITR-2 Capital Gains + Interest Test Case

This fixture represents a complex ITR-2 return with multiple income sources, variances requiring confirmation, and net tax payable requiring challan payment.

## Scenario Details
- **Taxpayer**: Individual with salary + capital gains + interest income
- **Income Sources**: 
  - Salary: ₹15,00,000 (multiple employers)
  - Capital Gains: ₹2,50,000 (LTCG + STCG)
  - Interest: ₹45,000 (multiple banks with variance)
- **Variances**: AIS vs Bank statement interest difference (₹2,000)
- **Expected Outcome**: Net tax payable ₹25,000, requires challan payment

## Files Included
- `prefill.json` - Complex taxpayer information
- `form16b_primary.pdf` - Form 16B from primary employer
- `form16b_secondary.pdf` - Form 16B from secondary employer  
- `ais.json` - AIS data with multiple income sources
- `bank_statement.csv` - Bank CSV with interest details
- `broker_pnl.csv` - Broker P&L statement with capital gains
- `form26as.pdf` - Form 26AS with advance tax challans
- `expected_output.json` - Expected computation with variances
- `schema_validation.json` - Schema validation rules

## Test Objectives
- Verify complex multi-source reconciliation
- Test variance detection and confirmation workflow
- Validate tax payment flow with challan processing
- Ensure export totals match report totals
- Test LLM fallback scenarios (mocked)
- Verify 20+ business rules validation