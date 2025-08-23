# Tax Payment Feature Implementation

## Overview

This implementation adds self-assessment tax payment functionality to the tax return system. The feature allows users to pay outstanding tax liability and capture challan details when the computed tax liability exceeds the taxes already paid (TDS + Advance Tax).

## Key Components

### 1. API Implementation

#### New Schemas (`apps/api/schemas/challan.py`)
- `ChallanCreate`: Request schema for creating new challan
- `ChallanResponse`: Response schema with challan details
- `ChallanSummary`: Summary of all challans for a tax return
- `ChallanUpdate`: Schema for updating challan status

#### New Router (`apps/api/routers/challan.py`)
- `POST /api/challans/{return_id}`: Create new challan with optional PDF upload
- `GET /api/challans/{return_id}`: Get all challans for a tax return
- `GET /api/challans/{return_id}/summary`: Get challan summary statistics
- `PUT /api/challans/challan/{challan_id}`: Update challan status/remarks
- `DELETE /api/challans/challan/{challan_id}`: Soft delete challan

#### Database Updates (`apps/api/db/models.py`)
Enhanced `Challan` model with new fields:
- `cin_crn`: 16-digit CIN/CRN number from challan
- `bsr_code`: 7-digit BSR code of the bank
- `bank_reference`: Bank reference number
- `challan_file_path`: Path to uploaded challan PDF

#### Migration (`apps/api/alembic/versions/add_challan_fields.py`)
Database migration to add new challan fields.

### 2. Frontend Implementation

#### New Route (`apps/web/src/routes/TaxPayment.tsx`)
Complete tax payment interface with:
- Tax computation breakup display
- Static payment instructions (markdown-style)
- Challan form with validation
- PDF file upload capability
- Existing challan display
- Conditional rendering (only shows when net payable > 0)

#### Updated Review Route (`apps/web/src/routes/Review.tsx`)
- Added conditional "Pay Tax" button when net payable > 0
- Shows payable amount in button text
- Redirects to tax payment page

#### Updated App Routing (`apps/web/src/App.tsx`)
- Added `/tax-payment/:returnId` route

### 3. Integration Updates

#### Returns API (`apps/api/routers/returns.py`)
- Enhanced `/build` endpoint to include challan payments in tax computation
- Calculates `net_tax_payable` considering challan payments
- Updates `total_taxes_paid` to include challan amounts

#### Pipeline Service (`apps/api/services/pipeline.py`)
- Updated `PreviewResponse` to include challan payment fields
- Added `net_tax_payable` and `challan_payments` to summary

## Feature Flow

### 1. Tax Computation
1. User completes document upload and review
2. System computes tax liability using the tax engine
3. Calculates net payable = tax liability - (TDS + advance tax + challan payments)

### 2. Payment Decision
- If `net_tax_payable <= 0`: User proceeds directly to final review
- If `net_tax_payable > 0`: User is directed to tax payment page

### 3. Tax Payment Process
1. **Payment Instructions**: Static markdown-style instructions guide user through payment process
2. **External Payment**: User pays via Income Tax portal or bank
3. **Challan Capture**: User returns and enters challan details:
   - Payment amount
   - CIN/CRN number (16 digits)
   - BSR code (7 digits)
   - Bank reference number
   - Payment date
   - Bank name (optional)
   - Remarks (optional)
   - Challan PDF upload (optional)

### 4. Validation & Storage
- Form validation ensures required fields are provided
- File validation (PDF only, max 10MB)
- Challan stored with unique system-generated number
- Tax computation updated to reflect new payment

### 5. Export Blocking
- Export functionality remains blocked until all tax liability is covered
- System tracks total challan payments vs. tax liability

## API Endpoints

### Challan Management
```
POST   /api/challans/{return_id}           # Create challan
GET    /api/challans/{return_id}           # List challans
GET    /api/challans/{return_id}/summary   # Challan summary
PUT    /api/challans/challan/{challan_id}  # Update challan
DELETE /api/challans/challan/{challan_id}  # Delete challan
```

### Enhanced Returns
```
POST   /api/returns/{return_id}/build      # Now includes challan data
```

## Data Models

### Challan Fields
- `id`: Primary key
- `tax_return_id`: Foreign key to tax return
- `challan_number`: System-generated unique number
- `challan_type`: Type of payment (self_assessment, advance_tax, etc.)
- `amount`: Payment amount
- `cin_crn`: 16-digit CIN/CRN from challan
- `bsr_code`: 7-digit BSR code
- `bank_reference`: Bank reference number
- `payment_date`: Date of payment
- `bank_name`: Bank name (optional)
- `status`: Payment status (pending, paid, cancelled, expired)
- `assessment_year`: Assessment year
- `remarks`: Additional remarks
- `challan_file_path`: Path to uploaded PDF
- `created_at`, `updated_at`: Audit timestamps

## Testing

### Unit Tests (`apps/api/tests/test_challan.py`)
- Challan creation with valid data
- File upload functionality
- Validation error handling
- Challan retrieval and summary

### Integration Test (`test_tax_payment_integration.py`)
End-to-end test covering:
1. Tax return creation
2. Tax computation
3. Challan payment creation
4. Updated totals verification

## Security Considerations

1. **File Upload Security**:
   - Only PDF files allowed
   - File size limit (10MB)
   - Files stored outside web root
   - Unique filenames to prevent conflicts

2. **Data Validation**:
   - CIN/CRN format validation (16 digits)
   - BSR code format validation (7 digits)
   - Amount validation (positive numbers)
   - Date validation

3. **Access Control**:
   - Challans linked to specific tax returns
   - No cross-return access possible

## Usage Instructions

### For Users
1. Complete tax return review process
2. If payment is required, click "Pay Tax" button
3. Follow payment instructions to pay via official channels
4. Return and enter challan details
5. Upload challan PDF (optional but recommended)
6. Continue to final review once payment is recorded

### For Developers
1. Run database migration: `alembic upgrade head`
2. Ensure upload directories are writable
3. Configure file storage paths as needed
4. Run integration tests to verify functionality

## Future Enhancements

1. **Payment Gateway Integration**: Direct payment processing
2. **Challan Verification**: API integration with Income Tax systems
3. **Installment Payments**: Support for partial payments
4. **Payment Reminders**: Automated notifications for pending payments
5. **Bulk Upload**: Support for multiple challan uploads
6. **Payment Analytics**: Dashboard for payment tracking and reporting

## Dependencies

### Backend
- FastAPI for API endpoints
- SQLAlchemy for database operations
- Alembic for database migrations
- Pydantic for data validation

### Frontend
- React for UI components
- React Router for navigation
- Lucide React for icons
- Tailwind CSS for styling

### File Storage
- Local filesystem (configurable for cloud storage)
- PDF file handling
- Unique filename generation