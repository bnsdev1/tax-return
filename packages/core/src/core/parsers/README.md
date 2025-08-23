# Document Parsers

This module provides a comprehensive document parsing system for tax return artifacts. It implements a plugin-based architecture where different parsers can handle specific document types.

## Architecture

### Core Components

1. **ArtifactParser Protocol**: Defines the interface that all parsers must implement
2. **BaseParser**: Abstract base class providing common functionality
3. **ParserRegistry**: Central registry for managing and routing to appropriate parsers
4. **Individual Parsers**: Specific implementations for different document types

### Parser Protocol

All parsers must implement the `ArtifactParser` protocol:

```python
class ArtifactParser(Protocol):
    def supports(self, kind: str, path: Path) -> bool:
        """Check if this parser supports the given artifact kind and file."""
        
    def parse(self, path: Path) -> Dict[str, Any]:
        """Parse the artifact file and return structured data."""
        
    @property
    def supported_kinds(self) -> List[str]:
        """List of artifact kinds this parser supports."""
        
    @property
    def supported_extensions(self) -> List[str]:
        """List of file extensions this parser supports."""
```

## Available Parsers

### 1. PrefillParser
- **Kinds**: `prefill`, `prefill_data`
- **Extensions**: `.json`
- **Purpose**: Parse prefilled tax return data from JSON files
- **Output**: Structured personal info, income, deductions, and tax data

### 2. AISParser
- **Kinds**: `ais`, `tis`, `ais_data`, `tis_data`
- **Extensions**: `.json`
- **Purpose**: Parse Annual Information Statement (AIS) and Tax Information Statement (TIS) data
- **Output**: Statement info, salary details, interest details, tax payments, and summary

### 3. Form16BParser
- **Kinds**: `form16b`, `form_16b`, `tds_certificate`
- **Extensions**: `.pdf`
- **Purpose**: Parse Form 16B TDS certificates for property transactions
- **Output**: Certificate info, deductor/deductee details, property details, payment info

### 4. BankCSVParser
- **Kinds**: `bank_csv`, `bank_statement`, `transactions`
- **Extensions**: `.csv`
- **Purpose**: Parse bank statement CSV files
- **Output**: Account info, transactions, summary statistics, and categorized transactions

### 5. PnLCSVParser
- **Kinds**: `pnl_csv`, `pnl`, `profit_loss`, `income_statement`
- **Extensions**: `.csv`
- **Purpose**: Parse Profit & Loss statement CSV files
- **Output**: Revenue breakdown, expense categories, summary metrics, and financial ratios

## Usage

### Basic Usage

```python
from core.parsers import default_registry

# Parse a document
result = default_registry.parse('prefill', 'path/to/prefill.json')

# Get specific parser
parser = default_registry.get_parser('ais', 'path/to/ais.json')
if parser:
    result = parser.parse(Path('path/to/ais.json'))
```

### Custom Registry

```python
from core.parsers import ParserRegistry, PrefillParser

# Create custom registry
registry = ParserRegistry()
registry.register(PrefillParser())

# Use custom registry
result = registry.parse('prefill', 'data.json')
```

### Registry Information

```python
# List supported kinds
kinds = default_registry.list_supported_kinds()

# List registered parsers
parsers = default_registry.list_parsers()
```

## Output Structure

All parsers return a dictionary with:

- **Parsed Data**: Document-specific structured data
- **Metadata**: File information (size, extension, etc.)
- **Parser Info**: Parser name, artifact kind, parse timestamp

Example output structure:
```python
{
    "personal_info": {...},      # Document-specific data
    "income": {...},
    "deductions": {...},
    "metadata": {
        "source": "prefill",
        "file_name": "data.json",
        "file_size": 1024,
        "file_extension": ".json"
    },
    "_parser_info": {
        "parser_name": "PrefillParser",
        "artifact_kind": "prefill",
        "parsed_at": "2025-08-23T12:00:00+00:00"
    }
}
```

## Error Handling

The parser system provides robust error handling:

- **FileNotFoundError**: When the specified file doesn't exist
- **ValueError**: When the file format is invalid or parsing fails
- **UnicodeDecodeError**: When file encoding is not supported

```python
try:
    result = default_registry.parse('prefill', 'invalid.json')
except ValueError as e:
    print(f"Parsing failed: {e}")
```

## Implementation Notes

### Current Implementation Status

All parsers currently return **deterministic fixture data** rather than parsing actual file content. This provides:

- Predictable output for testing and development
- Consistent data structure examples
- Foundation for real parsing implementation

### Future Enhancements

For production use, parsers would be enhanced with:

1. **PrefillParser**: Real JSON parsing with validation
2. **AISParser**: Actual AIS/TIS JSON structure parsing
3. **Form16BParser**: PDF text extraction using libraries like PyPDF2 or pdfplumber
4. **BankCSVParser**: Enhanced CSV format detection and parsing
5. **PnLCSVParser**: Accounting software format recognition

### Adding New Parsers

To add a new parser:

1. Create a class implementing `ArtifactParser` protocol
2. Inherit from `BaseParser` for common functionality
3. Implement required methods and properties
4. Register with the default registry

```python
class MyCustomParser(BaseParser):
    def __init__(self):
        super().__init__("MyCustomParser")
    
    @property
    def supported_kinds(self) -> List[str]:
        return ["my_kind"]
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".xyz"]
    
    def parse(self, path: Path) -> Dict[str, Any]:
        # Implementation here
        pass

# Register the parser
default_registry.register(MyCustomParser())
```

## Testing

The parser system includes comprehensive unit tests covering:

- Parser registration and routing
- Individual parser functionality
- Error handling scenarios
- Default registry behavior

Run tests with:
```bash
python -m pytest tests/test_parsers.py -v
```

## Demonstration

Run the demonstration script to see the parser system in action:
```bash
python demo_parsers.py
```

This creates sample files and demonstrates parsing each document type with detailed output.