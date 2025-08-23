"""Document parsers for tax return artifacts."""

from .base import ArtifactParser, ParserRegistry
from .prefill import PrefillParser
from .ais import AISParser
from .form16b import Form16BParser
from .form26as import Form26ASParser
from .bank_csv import BankCSVParser
from .pnl_csv import PnLCSVParser

# Create default registry with all parsers
default_registry = ParserRegistry()
default_registry.register(PrefillParser())
default_registry.register(AISParser())
default_registry.register(Form16BParser())
default_registry.register(Form26ASParser())
default_registry.register(BankCSVParser())
default_registry.register(PnLCSVParser())

__all__ = [
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