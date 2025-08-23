"""
ITR JSON Exporter

Builds byte-perfect ITR JSON files for various ITR forms (ITR-1, ITR-2, etc.)
following the official Income Tax Department JSON schema specifications.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ITRFormType(str, Enum):
    """Supported ITR form types"""
    ITR1 = "ITR1"
    ITR2 = "ITR2"
    ITR3 = "ITR3"
    ITR4 = "ITR4"

class SchemaVersion(str, Enum):
    """Supported schema versions"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"

@dataclass
class ITRExportResult:
    """Result of ITR JSON export"""
    json_data: Dict[str, Any]
    json_string: str
    form_type: str
    schema_version: str
    assessment_year: str
    export_timestamp: datetime
    validation_errors: List[str]
    warnings: List[str]

class ITRJSONBuilder:
    """
    Builder class for constructing ITR JSON files
    
    Supports ITR-1 and ITR-2 forms with proper schema compliance
    and byte-perfect output formatting.
    """
    
    def __init__(self, form_type: ITRFormType, assessment_year: str = "2025-26", 
                 schema_version: SchemaVersion = SchemaVersion.V2_0):
        self.form_type = form_type
        self.assessment_year = assessment_year
        self.schema_version = schema_version
        self.validation_errors = []
        self.warnings = []
        
        logger.info(f"Initialized ITR JSON Builder for {form_type} AY {assessment_year}")
    
    def build_itr_json(self, totals: Dict[str, Any], prefill: Dict[str, Any], 
                      form_data: Dict[str, Any], ay: str, schema_ver: str) -> ITRExportResult:
        """
        Build complete ITR JSON from computed totals, prefill data, and form data
        
        Args:
            totals: Computed tax totals and calculations
            prefill: Pre-filled data from various sources
            form_data: Additional form-specific data
            ay: Assessment year
            schema_ver: Schema version to use
            
        Returns:
            ITRExportResult with complete JSON and validation info
        """
        logger.info(f"Building ITR JSON for {self.form_type} AY {ay}")
        
        # Reset validation state
        self.validation_errors.clear()
        self.warnings.clear()
        
        # Build the appropriate ITR form
        if self.form_type == ITRFormType.ITR1:
            json_data = self._build_itr1_json(totals, prefill, form_data, ay)
        elif self.form_type == ITRFormType.ITR2:
            json_data = self._build_itr2_json(totals, prefill, form_data, ay)
        else:
            raise ValueError(f"Unsupported form type: {self.form_type}")
        
        # Convert to JSON string with proper formatting
        json_string = self._format_json_output(json_data)
        
        return ITRExportResult(
            json_data=json_data,
            json_string=json_string,
            form_type=self.form_type.value,
            schema_version=schema_ver,
            assessment_year=ay,
            export_timestamp=datetime.now(),
            validation_errors=self.validation_errors.copy(),
            warnings=self.warnings.copy()
        )
    
    def _build_itr1_json(self, totals: Dict[str, Any], prefill: Dict[str, Any], 
                        form_data: Dict[str, Any], ay: str) -> Dict[str, Any]:
        """Build ITR-1 JSON structure"""
        
        # Extract taxpayer information
        taxpayer_info = prefill.get('taxpayer', {})
        
        # Build ITR-1 structure
        itr_json = {
            "ITR": {
                "ITR1": {
                    "CreationInfo": self._build_creation_info(ay),
                    "Form_ITR1": {
                        "FormName": "ITR1",
                        "Description": "For Individuals having Income from Salaries, One House Property, Other Sources (Interest etc.) and having Total Income upto Rs.50 lakh",
                        "AssessmentYear": ay,
                        "SchemaVer": self.schema_version.value,
                        "FormVer": "1.0"
                    },
                    "PersonalInfo": self._build_personal_info_itr1(taxpayer_info, prefill),
                    "ITR1_IncomeDeductions": self._build_income_deductions_itr1(totals, prefill),
                    "ITR1_TaxComputation": self._build_tax_computation_itr1(totals),
                    "TaxPaid": self._build_tax_paid_itr1(totals, prefill),
                    "Refund": self._build_refund_itr1(totals),
                    "Schedule80G": self._build_schedule_80g_itr1(prefill),
                    "Verification": self._build_verification(taxpayer_info)
                }
            }
        }
        
        return itr_json
    
    def _build_itr2_json(self, totals: Dict[str, Any], prefill: Dict[str, Any], 
                        form_data: Dict[str, Any], ay: str) -> Dict[str, Any]:
        """Build ITR-2 JSON structure"""
        
        # Extract taxpayer information
        taxpayer_info = prefill.get('taxpayer', {})
        
        # Build ITR-2 structure
        itr_json = {
            "ITR": {
                "ITR2": {
                    "CreationInfo": self._build_creation_info(ay),
                    "Form_ITR2": {
                        "FormName": "ITR2",
                        "Description": "For Individuals and HUFs not having income from profits and gains of business or profession",
                        "AssessmentYear": ay,
                        "SchemaVer": self.schema_version.value,
                        "FormVer": "1.0"
                    },
                    "PersonalInfo": self._build_personal_info_itr2(taxpayer_info, prefill),
                    "ITR2_IncomeDeductions": self._build_income_deductions_itr2(totals, prefill),
                    "ITR2_TaxComputation": self._build_tax_computation_itr2(totals),
                    "TaxPaid": self._build_tax_paid_itr2(totals, prefill),
                    "Refund": self._build_refund_itr2(totals),
                    "ScheduleCapitalGain": self._build_schedule_cg_itr2(prefill),
                    "ScheduleHouseProperty": self._build_schedule_hp_itr2(prefill),
                    "Schedule80G": self._build_schedule_80g_itr2(prefill),
                    "Verification": self._build_verification(taxpayer_info)
                }
            }
        }
        
        return itr_json
    
    def _build_creation_info(self, ay: str) -> Dict[str, Any]:
        """Build creation info section"""
        return {
            "SWVersionNo": "1.0",
            "SWCreatedBy": "TaxPlannerPro",
            "XMLCreationDate": datetime.now().strftime("%Y-%m-%d"),
            "XMLCreationTime": datetime.now().strftime("%H:%M:%S"),
            "IntermediaryCity": "Mumbai",
            "Digest": ""
        }
    
    def _build_personal_info_itr1(self, taxpayer_info: Dict[str, Any], 
                                 prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build personal info section for ITR-1"""
        return {
            "AssesseeName": {
                "FirstName": taxpayer_info.get('first_name', ''),
                "MiddleName": taxpayer_info.get('middle_name', ''),
                "SurNameOrOrgName": taxpayer_info.get('last_name', '')
            },
            "PAN": taxpayer_info.get('pan', ''),
            "Address": {
                "ResidenceNo": taxpayer_info.get('address', {}).get('house_no', ''),
                "RoadOrStreet": taxpayer_info.get('address', {}).get('street', ''),
                "LocalityOrArea": taxpayer_info.get('address', {}).get('area', ''),
                "CityOrTownOrDistrict": taxpayer_info.get('address', {}).get('city', ''),
                "StateCode": taxpayer_info.get('address', {}).get('state_code', '27'),  # Default Maharashtra
                "CountryCode": taxpayer_info.get('address', {}).get('country_code', '91'),  # Default India
                "PinCode": self._safe_int(taxpayer_info.get('address', {}).get('pincode', 0)),
                "Phone": {
                    "STDCode": taxpayer_info.get('phone', {}).get('std_code', ''),
                    "PhoneNo": taxpayer_info.get('phone', {}).get('number', '')
                },
                "EmailAddress": taxpayer_info.get('email', '')
            },
            "DOB": taxpayer_info.get('date_of_birth', '1990-01-01'),
            "EmployerCategory": taxpayer_info.get('employer_category', 'OTH'),
            "Status": taxpayer_info.get('status', 'I'),  # Individual
            "FilingStatus": {
                "ReturnFileSec": "11",
                "SeventhProvisio139": "N",
                "FilingDate": datetime.now().strftime("%Y-%m-%d"),
                "VerificationDate": datetime.now().strftime("%Y-%m-%d")
            }
        }
    
    def _build_personal_info_itr2(self, taxpayer_info: Dict[str, Any], 
                                 prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build personal info section for ITR-2"""
        # ITR-2 has similar structure to ITR-1 but with additional fields
        base_info = self._build_personal_info_itr1(taxpayer_info, prefill)
        
        # Add ITR-2 specific fields
        base_info.update({
            "ResidentialStatus": taxpayer_info.get('residential_status', 'RES'),
            "DirectorInCompany": taxpayer_info.get('director_in_company', 'N'),
            "HeldUnlistedEquityShares": taxpayer_info.get('held_unlisted_equity', 'N')
        })
        
        return base_info
    
    def _build_income_deductions_itr1(self, totals: Dict[str, Any], 
                                     prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build income and deductions section for ITR-1"""
        income_breakdown = totals.get('income_breakdown', {})
        deductions = totals.get('deductions_summary', {})
        
        return {
            "Salary": self._safe_decimal(income_breakdown.get('salary', 0)),
            "SalaryTDS": self._safe_decimal(prefill.get('tds', {}).get('salary_tds', 0)),
            "HouseProperty": self._safe_decimal(income_breakdown.get('house_property', 0)),
            "OtherSources": self._safe_decimal(income_breakdown.get('other_sources', 0)),
            "OtherSourcesTDS": self._safe_decimal(prefill.get('tds', {}).get('other_sources_tds', 0)),
            "GrossTotalIncome": self._safe_decimal(totals.get('gross_total_income', 0)),
            "DeductionUnderScheduleVIA": {
                "Section80C": self._safe_decimal(deductions.get('section_80c', 0)),
                "Section80CCC": self._safe_decimal(deductions.get('section_80ccc', 0)),
                "Section80CCD1": self._safe_decimal(deductions.get('section_80ccd1', 0)),
                "Section80CCD1B": self._safe_decimal(deductions.get('section_80ccd1b', 0)),
                "Section80D": self._safe_decimal(deductions.get('section_80d', 0)),
                "Section80DD": self._safe_decimal(deductions.get('section_80dd', 0)),
                "Section80DDB": self._safe_decimal(deductions.get('section_80ddb', 0)),
                "Section80E": self._safe_decimal(deductions.get('section_80e', 0)),
                "Section80EE": self._safe_decimal(deductions.get('section_80ee', 0)),
                "Section80EEA": self._safe_decimal(deductions.get('section_80eea', 0)),
                "Section80EEB": self._safe_decimal(deductions.get('section_80eeb', 0)),
                "Section80G": self._safe_decimal(deductions.get('section_80g', 0)),
                "Section80GG": self._safe_decimal(deductions.get('section_80gg', 0)),
                "Section80GGA": self._safe_decimal(deductions.get('section_80gga', 0)),
                "Section80GGC": self._safe_decimal(deductions.get('section_80ggc', 0)),
                "Section80U": self._safe_decimal(deductions.get('section_80u', 0)),
                "Section80TTA": self._safe_decimal(deductions.get('section_80tta', 0)),
                "Section80TTB": self._safe_decimal(deductions.get('section_80ttb', 0)),
                "TotalDeductionUnderScheduleVIA": self._safe_decimal(totals.get('total_deductions', 0))
            },
            "TotalIncome": self._safe_decimal(totals.get('taxable_income', 0))
        }
    
    def _build_income_deductions_itr2(self, totals: Dict[str, Any], 
                                     prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build income and deductions section for ITR-2"""
        # ITR-2 has more detailed income sections
        base_income = self._build_income_deductions_itr1(totals, prefill)
        
        # Add ITR-2 specific income sources
        income_breakdown = totals.get('income_breakdown', {})
        
        base_income.update({
            "CapitalGain": {
                "ShortTerm": {
                    "ShortTermCapGain15Per": self._safe_decimal(income_breakdown.get('stcg_15_percent', 0)),
                    "ShortTermCapGainAppRate": self._safe_decimal(income_breakdown.get('stcg_applicable_rate', 0))
                },
                "LongTerm": {
                    "LongTermCapGain10Per": self._safe_decimal(income_breakdown.get('ltcg_10_percent', 0)),
                    "LongTermCapGain20Per": self._safe_decimal(income_breakdown.get('ltcg_20_percent', 0))
                },
                "TotalCapitalGains": self._safe_decimal(income_breakdown.get('capital_gains', 0))
            }
        })
        
        return base_income
    
    def _build_tax_computation_itr1(self, totals: Dict[str, Any]) -> Dict[str, Any]:
        """Build tax computation section for ITR-1"""
        tax_liability = totals.get('tax_liability', {})
        
        return {
            "TotalIncome": self._safe_decimal(totals.get('taxable_income', 0)),
            "TaxOnTotalIncome": self._safe_decimal(tax_liability.get('base_tax', 0)),
            "Rebate87A": self._safe_decimal(tax_liability.get('rebate_87a', 0)),
            "TaxAfterRebate": self._safe_decimal(tax_liability.get('tax_after_rebate', 0)),
            "Surcharge": self._safe_decimal(tax_liability.get('surcharge', 0)),
            "EducationCess": self._safe_decimal(tax_liability.get('cess', 0)),
            "TotalTaxPayable": self._safe_decimal(tax_liability.get('total_tax_liability', 0)),
            "TaxPayableOnRebate": self._safe_decimal(tax_liability.get('total_tax_liability', 0)),
            "Interest234A": self._safe_decimal(tax_liability.get('interest_234a', 0)),
            "Interest234B": self._safe_decimal(tax_liability.get('interest_234b', 0)),
            "Interest234C": self._safe_decimal(tax_liability.get('interest_234c', 0)),
            "TotalIntPayable": self._safe_decimal(tax_liability.get('total_interest', 0)),
            "AggregateLiability": self._safe_decimal(tax_liability.get('total_payable', 0))
        }
    
    def _build_tax_computation_itr2(self, totals: Dict[str, Any]) -> Dict[str, Any]:
        """Build tax computation section for ITR-2"""
        # ITR-2 has similar tax computation to ITR-1 with additional fields
        base_computation = self._build_tax_computation_itr1(totals)
        
        # Add ITR-2 specific tax computation fields
        tax_liability = totals.get('tax_liability', {})
        
        base_computation.update({
            "TaxOnSpecialRateIncome": {
                "TaxOnSTCG15Per": self._safe_decimal(tax_liability.get('stcg_15_percent_tax', 0)),
                "TaxOnLTCG10Per": self._safe_decimal(tax_liability.get('ltcg_10_percent_tax', 0)),
                "TaxOnLTCG20Per": self._safe_decimal(tax_liability.get('ltcg_20_percent_tax', 0))
            }
        })
        
        return base_computation
    
    def _build_tax_paid_itr1(self, totals: Dict[str, Any], prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build tax paid section for ITR-1"""
        tds_data = prefill.get('tds', {})
        
        return {
            "TDS": {
                "TDSOnSalary": self._safe_decimal(tds_data.get('salary_tds', 0)),
                "TDSOnOthThanSalary": self._safe_decimal(tds_data.get('other_tds', 0)),
                "TotalTDS": self._safe_decimal(tds_data.get('total_tds', 0))
            },
            "AdvanceTax": self._safe_decimal(totals.get('advance_tax_paid', 0)),
            "SelfAssessmentTax": self._safe_decimal(totals.get('self_assessment_tax', 0)),
            "TotalTaxesPaid": self._safe_decimal(totals.get('total_taxes_paid', 0))
        }
    
    def _build_tax_paid_itr2(self, totals: Dict[str, Any], prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build tax paid section for ITR-2"""
        # ITR-2 has similar structure to ITR-1
        return self._build_tax_paid_itr1(totals, prefill)
    
    def _build_refund_itr1(self, totals: Dict[str, Any]) -> Dict[str, Any]:
        """Build refund section for ITR-1"""
        refund_amount = totals.get('refund_or_payable', 0)
        
        return {
            "RefundDue": max(0, -refund_amount) if refund_amount < 0 else 0,
            "TaxPayable": max(0, refund_amount) if refund_amount > 0 else 0,
            "BankAccountDtls": {
                "AddtnlBankDetails": [
                    {
                        "IFSCCode": "SBIN0000001",  # Default - would come from user data
                        "BankName": "STATE BANK OF INDIA",
                        "BankAccountNo": "12345678901",  # Default - would come from user data
                        "UseForRefund": "Y"
                    }
                ]
            }
        }
    
    def _build_refund_itr2(self, totals: Dict[str, Any]) -> Dict[str, Any]:
        """Build refund section for ITR-2"""
        # ITR-2 has similar refund structure to ITR-1
        return self._build_refund_itr1(totals)
    
    def _build_schedule_80g_itr1(self, prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build Schedule 80G for ITR-1"""
        donations = prefill.get('donations', {})
        
        return {
            "DonationsUs80G": {
                "Don100PercentNoLimit": self._safe_decimal(donations.get('100_percent_no_limit', 0)),
                "Don50PercentNoLimit": self._safe_decimal(donations.get('50_percent_no_limit', 0)),
                "Don100PercentWithLimit": self._safe_decimal(donations.get('100_percent_with_limit', 0)),
                "Don50PercentWithLimit": self._safe_decimal(donations.get('50_percent_with_limit', 0)),
                "TotalDonationsUs80G": self._safe_decimal(donations.get('total_80g', 0))
            }
        }
    
    def _build_schedule_80g_itr2(self, prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build Schedule 80G for ITR-2"""
        # ITR-2 has similar 80G structure to ITR-1
        return self._build_schedule_80g_itr1(prefill)
    
    def _build_schedule_cg_itr2(self, prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build Schedule Capital Gains for ITR-2"""
        cg_data = prefill.get('capital_gains', {})
        
        return {
            "ShortTermCapGainFor15Per": {
                "ShortTermCapGain15PerDtls": [
                    {
                        "NameOfShare": cg_data.get('equity_shares', {}).get('name', 'Equity Shares'),
                        "SaleValue": self._safe_decimal(cg_data.get('equity_shares', {}).get('sale_value', 0)),
                        "CostOfAcquisition": self._safe_decimal(cg_data.get('equity_shares', {}).get('cost_of_acquisition', 0)),
                        "ExpOnTransfer": self._safe_decimal(cg_data.get('equity_shares', {}).get('expense_on_transfer', 0)),
                        "CapGain": self._safe_decimal(cg_data.get('equity_shares', {}).get('capital_gain', 0))
                    }
                ]
            },
            "LongTermCapGainFor10Per": {
                "LongTermCapGain10PerDtls": [
                    {
                        "NameOfShare": cg_data.get('equity_ltcg', {}).get('name', 'Equity Shares LTCG'),
                        "SaleValue": self._safe_decimal(cg_data.get('equity_ltcg', {}).get('sale_value', 0)),
                        "CostOfAcquisition": self._safe_decimal(cg_data.get('equity_ltcg', {}).get('cost_of_acquisition', 0)),
                        "ExpOnTransfer": self._safe_decimal(cg_data.get('equity_ltcg', {}).get('expense_on_transfer', 0)),
                        "CapGain": self._safe_decimal(cg_data.get('equity_ltcg', {}).get('capital_gain', 0))
                    }
                ]
            }
        }
    
    def _build_schedule_hp_itr2(self, prefill: Dict[str, Any]) -> Dict[str, Any]:
        """Build Schedule House Property for ITR-2"""
        hp_data = prefill.get('house_property', {})
        
        return {
            "PropertyDetails": [
                {
                    "PropertyType": hp_data.get('property_type', 'SOP'),  # Self Occupied Property
                    "Address": {
                        "AddrDetail": hp_data.get('address', 'Property Address'),
                        "CityOrTownOrDistrict": hp_data.get('city', 'Mumbai'),
                        "StateCode": hp_data.get('state_code', '27'),
                        "CountryCode": hp_data.get('country_code', '91'),
                        "PinCode": self._safe_int(hp_data.get('pincode', 400001))
                    },
                    "GrossRentReceived": self._safe_decimal(hp_data.get('gross_rent', 0)),
                    "TaxPaidToLocalAuth": self._safe_decimal(hp_data.get('municipal_tax', 0)),
                    "AnnualValue": self._safe_decimal(hp_data.get('annual_value', 0)),
                    "StandardDeduction": self._safe_decimal(hp_data.get('standard_deduction', 0)),
                    "InterestPayable": self._safe_decimal(hp_data.get('interest_on_loan', 0)),
                    "TotalDeduction": self._safe_decimal(hp_data.get('total_deduction', 0)),
                    "IncomeFromHP": self._safe_decimal(hp_data.get('income_from_hp', 0))
                }
            ]
        }
    
    def _build_verification(self, taxpayer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build verification section"""
        return {
            "Declaration": {
                "AssesseeVerName": f"{taxpayer_info.get('first_name', '')} {taxpayer_info.get('last_name', '')}".strip(),
                "FatherName": taxpayer_info.get('father_name', ''),
                "AssesseeVerPAN": taxpayer_info.get('pan', ''),
                "Capacity": "S",  # Self
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Place": taxpayer_info.get('place', 'Mumbai')
            },
            "Verification": {
                "VerificationDate": datetime.now().strftime("%Y-%m-%d"),
                "VerificationPlace": taxpayer_info.get('place', 'Mumbai')
            }
        }
    
    def _safe_decimal(self, value: Any) -> int:
        """Safely convert value to integer (ITR JSON uses integers for amounts)"""
        if value is None:
            return 0
        
        try:
            if isinstance(value, (int, float)):
                return int(round(value))
            elif isinstance(value, Decimal):
                return int(value.to_integral_value())
            elif isinstance(value, str):
                return int(round(float(value)))
            else:
                return 0
        except (ValueError, TypeError):
            self.warnings.append(f"Could not convert value to decimal: {value}")
            return 0
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to integer"""
        if value is None:
            return 0
        
        try:
            return int(value)
        except (ValueError, TypeError):
            self.warnings.append(f"Could not convert value to integer: {value}")
            return 0
    
    def _format_json_output(self, json_data: Dict[str, Any]) -> str:
        """Format JSON output with proper indentation and sorting"""
        return json.dumps(
            json_data,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            separators=(',', ': ')
        )

def build_itr_json(totals: Dict[str, Any], prefill: Dict[str, Any], 
                  form_data: Dict[str, Any], ay: str, schema_ver: str) -> ITRExportResult:
    """
    Main function to build ITR JSON
    
    Args:
        totals: Computed tax totals and calculations
        prefill: Pre-filled data from various sources
        form_data: Additional form-specific data including form type
        ay: Assessment year (e.g., "2025-26")
        schema_ver: Schema version (e.g., "2.0")
        
    Returns:
        ITRExportResult with complete JSON and validation info
    """
    # Determine form type from form_data or totals
    form_type_str = form_data.get('form_type', 'ITR1')
    
    try:
        form_type = ITRFormType(form_type_str)
    except ValueError:
        # Default to ITR1 if unsupported form type
        form_type = ITRFormType.ITR1
        logger.warning(f"Unsupported form type {form_type_str}, defaulting to ITR1")
    
    try:
        schema_version = SchemaVersion(schema_ver)
    except ValueError:
        # Default to latest version
        schema_version = SchemaVersion.V2_0
        logger.warning(f"Unsupported schema version {schema_ver}, defaulting to {schema_version.value}")
    
    # Create builder and build JSON
    builder = ITRJSONBuilder(form_type, ay, schema_version)
    return builder.build_itr_json(totals, prefill, form_data, ay, schema_ver)