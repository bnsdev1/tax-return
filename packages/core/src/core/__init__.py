"""Core shared library for the monorepo."""

from .models import (
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
)
from .schemas import SchemaRegistry
from .parsers import (
    ArtifactParser,
    ParserRegistry,
    PrefillParser,
    AISParser,
    Form16BParser,
    Form26ASParser,
    BankCSVParser,
    PnLCSVParser,
    default_registry,
)
from .reconcile import DataReconciler, ReconciliationResult
from .compute import TaxCalculator, ComputationResult
# from .validate import TaxValidator, ValidationResult  # TODO: Implement these classes

__version__ = "0.1.0"

__all__ = [
    "TaxBaseModel",
    "AmountModel",
    "ValidationMixin",
    "PersonalInfo",
    "ReturnContext",
    "Salary",
    "HouseProperty",
    "CapitalGains",
    "OtherSources",
    "Deductions",
    "TaxesPaid",
    "Totals",
    "SchemaRegistry",
    "ArtifactParser",
    "ParserRegistry",
    "PrefillParser",
    "AISParser",
    "Form16BParser",
    "Form26ASParser",
    "BankCSVParser",
    "PnLCSVParser",
    "default_registry",
]