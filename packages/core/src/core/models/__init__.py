"""Tax return data models."""

from .base import TaxBaseModel, AmountModel, ValidationMixin
from .personal import PersonalInfo, ReturnContext
from .income import Salary, HouseProperty, CapitalGains, OtherSources
from .deductions import Deductions
from .taxes import TaxesPaid
from .totals import Totals

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
]