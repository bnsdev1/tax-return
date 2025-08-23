# Tax Planning API - Storage Layer

This directory contains the complete storage layer implementation for the tax planning application, built with SQLAlchemy and Alembic.

## 🏗️ Architecture

The storage layer follows a clean architecture pattern with:

- **Models**: SQLAlchemy ORM models defining the database schema
- **Repositories**: CRUD operations and business logic for each entity
- **Migrations**: Alembic migrations for database schema management
- **Tests**: Comprehensive unit and integration tests

## 📊 Database Schema

The database consists of 6 main tables:

### Core Tables

1. **taxpayers** - Individual taxpayer information
2. **returns** - Tax return filings
3. **artifacts** - Generated documents and files
4. **validations** - Validation results and checks
5. **rules_log** - Business rule execution logs
6. **challans** - Tax payment challans

### Relationships

```
taxpayers (1) ──→ (N) returns
returns (1) ──→ (N) artifacts
returns (1) ──→ (N) validations
returns (1) ──→ (N) rules_log
returns (1) ──→ (N) challans
returns (N) ──→ (1) returns (revised returns)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
# Initialize database
alembic upgrade head

# Check current migration
alembic current
```

### 3. Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_repositories.py -v
python -m pytest tests/test_integration.py -v
```

### 4. Try the Demo

```bash
python demo_storage_layer.py
```

## 📝 Usage Examples

### Basic CRUD Operations

```python
from db.base import get_db
from repo import TaxpayerRepository

# Get database session
db = next(get_db())

# Create repository
taxpayer_repo = TaxpayerRepository(db)

# Create taxpayer
taxpayer = taxpayer_repo.create_taxpayer(
    pan="ABCDE1234F",
    name="John Doe",
    email="john@example.com"
)

# Get by PAN
found = taxpayer_repo.get_by_pan("ABCDE1234F")

# Update
updated = taxpayer_repo.update(taxpayer.id, {"name": "John Smith"})

# Delete
deleted = taxpayer_repo.delete(taxpayer.id)
```

### Tax Return Workflow

```python
from repo import TaxReturnRepository, ValidationRepository
from db.models import ValidationStatus

# Create tax return
return_repo = TaxReturnRepository(db)
tax_return = return_repo.create_tax_return(
    taxpayer_id=taxpayer.id,
    assessment_year="2025-26",
    form_type="ITR2"
)

# Add validation
validation_repo = ValidationRepository(db)
validation_repo.create_validation(
    tax_return_id=tax_return.id,
    validation_type="schema",
    rule_name="pan_format",
    status=ValidationStatus.PASSED
)

# Submit return
submitted = return_repo.submit_return(
    tax_return.id,
    "ACK123456789"
)
```

## 🗃️ Repository Classes

### Base Repository

All repositories inherit from `BaseRepository` which provides:

- `create(obj_in)` - Create new record
- `get(id)` - Get by ID
- `get_multi(skip, limit, filters)` - Get multiple with pagination
- `update(id, obj_in)` - Update record
- `delete(id)` - Delete record
- `count(filters)` - Count records
- `exists(id)` - Check existence

### Specialized Repositories

#### TaxpayerRepository
- `get_by_pan(pan)` - Find by PAN number
- `get_by_email(email)` - Find by email
- `search_by_name(pattern)` - Search by name pattern
- `create_taxpayer(...)` - Create with validation

#### TaxReturnRepository
- `get_by_taxpayer(taxpayer_id)` - Get all returns for taxpayer
- `get_by_assessment_year(taxpayer_id, year)` - Get by year
- `submit_return(id, ack_number)` - Submit return
- `get_with_related_data(id)` - Get with all related data

#### ArtifactRepository
- `get_by_tax_return(return_id)` - Get all artifacts for return
- `get_by_type(return_id, type)` - Get by artifact type
- `search_by_tags(return_id, tag)` - Search by tags

#### ValidationRepository
- `get_by_status(return_id, status)` - Get by validation status
- `get_failed_validations(return_id)` - Get failed validations
- `get_validation_summary(return_id)` - Get summary statistics

#### RulesLogRepository
- `get_by_rule_name(return_id, rule)` - Get by rule name
- `get_failed_executions(return_id)` - Get failed executions
- `get_execution_stats(return_id)` - Get execution statistics

#### ChallanRepository
- `get_by_challan_number(number)` - Get by challan number
- `mark_as_paid(id, receipt)` - Mark as paid
- `get_total_amount_by_return(return_id)` - Get total amount
- `get_paid_amount_by_return(return_id)` - Get paid amount

## 🧪 Testing

The test suite includes:

### Unit Tests (`test_repositories.py`)
- Tests for all repository methods
- CRUD operations validation
- Business logic verification
- Error handling

### Integration Tests (`test_integration.py`)
- Complete workflow testing
- Database constraints validation
- Transaction integrity
- Relationship testing

### Test Coverage
- 23 test cases covering all repositories
- In-memory SQLite for fast testing
- Comprehensive error scenario testing

## 🔧 Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description"
```

### Running Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade
alembic downgrade -1
```

### Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show specific revision
alembic show <revision_id>
```

## 📋 Model Definitions

### Taxpayer
- Personal information (PAN, name, email, mobile)
- Address and date of birth
- Unique constraints on PAN and email

### TaxReturn
- Links to taxpayer
- Assessment year and form type
- Status tracking (draft, submitted, processed, rejected)
- JSON storage for return data
- Support for revised returns

### Artifact
- Generated documents and files
- File metadata (size, checksum, path)
- Content storage for small files
- Tagging system

### Validation
- Validation results and status
- Rule name and type
- Error messages and field paths
- Execution timing

### RulesLog
- Business rule execution tracking
- Input/output data logging
- Success/failure tracking
- Performance metrics

### Challan
- Tax payment tracking
- Multiple challan types
- Payment status and receipts
- Bank and quarter information

## 🔒 Security Considerations

- Input validation in repository methods
- SQL injection prevention through ORM
- Transaction rollback on errors
- Unique constraint enforcement
- Data integrity checks

## 📈 Performance Features

- Database indexing on key fields
- Lazy loading for relationships
- Pagination support in queries
- Connection pooling
- Query optimization

## 🛠️ Development

### Adding New Models

1. Define model in `db/models.py`
2. Create repository in `repo/`
3. Add to `__init__.py` files
4. Generate migration: `alembic revision --autogenerate`
5. Add tests

### Best Practices

- Use type hints throughout
- Follow repository pattern
- Write comprehensive tests
- Document complex queries
- Use transactions for multi-step operations

## 📚 Dependencies

- **SQLAlchemy 2.0.35** - ORM and database toolkit
- **Alembic 1.13.3** - Database migration tool
- **FastAPI 0.103.1** - Web framework
- **Pytest 7.4.2** - Testing framework

## 🎯 DoD Checklist

- ✅ SQLAlchemy models for all 6 tables
- ✅ Alembic migrations setup and working
- ✅ Repository classes with CRUD operations
- ✅ Unit tests using in-memory database
- ✅ Integration tests for complete workflows
- ✅ Migration runs successfully
- ✅ All CRUD tests pass (23/23)
- ✅ Comprehensive documentation
- ✅ Demo script showing functionality

## 🔗 Related Files

- `db/` - Database models and configuration
- `repo/` - Repository classes
- `alembic/` - Migration files
- `tests/` - Test files
- `demo_storage_layer.py` - Demonstration script