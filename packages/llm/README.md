# LLM Helpers

AI-powered helpers for the ITR Prep application, providing intelligent fallbacks for document parsing, transaction classification, and user-friendly explanations.

## Features

- **Multi-Provider Support**: OpenAI, Google Gemini, and local Ollama
- **Intelligent Routing**: Automatic provider selection based on context and settings
- **Privacy Controls**: PII redaction for cloud providers
- **Schema Validation**: Strict Pydantic validation for all outputs
- **Fallback Chain**: Graceful degradation when providers fail
- **Confidence Scoring**: Quality assessment for all AI outputs

## Quick Start

```python
from packages.llm import LLMRouter, LLMSettings, LLMTask

# Configure settings
settings = LLMSettings({
    "llm_enabled": True,
    "cloud_allowed": True,
    "primary": "openai",
    "confidence_threshold": 0.7
})

# Create router
router = LLMRouter(settings)

# Execute task
task = LLMTask(
    name="form16_extract",
    schema_name="Form16Extract",
    prompt="Extract salary details",
    text="Form 16B content..."
)

result = router.run(task)
if result.ok:
    print(f"Extracted data: {result.json}")
    print(f"Provider: {result.provider}")
    print(f"Confidence: {result.json.get('confidence')}")
```

## Supported Tasks

### Form 16B Extraction
Extract salary, TDS, and employer details from Form 16B documents.

```python
from packages.core.src.core.parsers.form16b_llm import parse_form16b_llm

result = parse_form16b_llm(form_text, router)
print(f"Gross Salary: ₹{result.gross_salary:,}")
print(f"TDS: ₹{result.tds:,}")
```

### Bank Transaction Classification
Classify bank narrations for tax relevance.

```python
from packages.core.src.core.parsers.bank_classifier_llm import BankClassifier

classifier = BankClassifier(router)
result = classifier.classify_narration("INTEREST CREDITED - Rs. 1,250")
print(f"Category: {result['label']}")
print(f"Confidence: {result['confidence']}")
```

### Rules Explanation
Generate user-friendly explanations of tax rules.

```python
from packages.core.src.core.explain.rules_explainer_llm import RulesExplainer

explainer = RulesExplainer(router)
explanation = explainer.explain_rules_execution(rules_log)
for bullet in explanation.bullets:
    print(f"• {bullet}")
```

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
OLLAMA_BASE_URL=http://localhost:11434
```

### Settings
```python
settings = {
    "llm_enabled": True,
    "cloud_allowed": True,
    "primary": "openai",
    "long_context_provider": "gemini",
    "local_provider": "ollama",
    "redact_pii": True,
    "long_context_threshold_chars": 8000,
    "confidence_threshold": 0.7,
    "max_retries": 2,
    "timeout_ms": 40000
}
```

## Privacy & Security

### PII Redaction
Automatically redacts sensitive information before sending to cloud providers:
- PAN numbers
- Aadhaar numbers
- Account numbers
- IFSC codes
- Mobile numbers
- Dates of birth

### Local Processing
When cloud providers are disabled, all processing happens locally using Ollama.

## Testing

Run the test suite:
```bash
pytest packages/llm/tests/
```

Run integration tests:
```bash
python test_llm_integration.py
```

## Development

Install in development mode:
```bash
pip install -e packages/llm[dev]
```

Format code:
```bash
black packages/llm/
ruff format packages/llm/
```

Type checking:
```bash
mypy packages/llm/
```