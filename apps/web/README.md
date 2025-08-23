# Tax Return Web Application

A React-based web application for managing tax returns and document uploads.

## Features

### Dashboard Route (`/`)
- **List Tax Returns**: View all existing tax returns with status badges
- **Create New Return**: Modal form to create a new tax return with:
  - PAN number input
  - Assessment year selection
  - Form type selection (ITR1, ITR2, ITR3, ITR4)
  - Tax regime selection (Old/New)
- **Navigation**: Click on any return to navigate to its documents page

### Documents Route (`/documents/:returnId`)
- **Return Information**: Display tax return details (form type, assessment year, regime, status)
- **Document Upload Cards**: Pre-configured cards for common tax documents:
  - `prefill.json` - Prefilled tax return data
  - `ais.json` - Annual Information Statement
  - `tis.json` - Tax Information Statement  
  - `form16b.pdf` - TDS certificate for property transactions
  - `bank.csv` / `bank.pdf` - Bank statements
  - `pnl.csv` - Profit & Loss statement
  - `cas.pdf` - Consolidated Account Statement
  - `loan_interest` - Home loan interest certificate
  - `deduction_proofs` - Supporting documents for deductions

- **Upload Functionality**: Each card supports:
  - File upload with appropriate file type restrictions
  - Upload status indicators (pending, completed, failed)
  - File size display
  - Replace existing files

- **Build Process**: 
  - Primary "Run Build" button to trigger tax return processing
  - Real-time progress tracking with progress bar
  - Status polling during build process
  - Success/failure notifications
  - Validation results display

## Technical Stack

- **React 18** with TypeScript
- **React Router** for navigation
- **TanStack Query** for state management and API calls
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Vite** for build tooling

## API Integration

The application integrates with the FastAPI backend through:

- **Tax Returns API**: Create, retrieve, and manage tax returns
- **Artifacts API**: Upload and manage document artifacts
- **Build Jobs API**: Trigger and monitor tax return processing
- **Status Polling**: Real-time updates during build process

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Ensure the FastAPI backend is running on `http://localhost:8000`

## Usage Flow

1. **Create Return**: Start on the Dashboard and click "Create New Return"
2. **Upload Documents**: Navigate to the Documents page and upload required files
3. **Run Build**: Click "Run Build" to process the tax return
4. **Monitor Progress**: Watch the progress bar and validation results
5. **Review Results**: Check for any validation warnings or errors

## File Upload Support

Each document type has specific file format restrictions:
- JSON files: `.json`
- PDF files: `.pdf` 
- CSV files: `.csv`
- Image files: `.jpg`, `.jpeg`, `.png` (for certificates and proofs)

## State Management

The application uses TanStack Query for:
- Caching API responses
- Automatic background refetching
- Optimistic updates
- Error handling
- Loading states
- Real-time polling for build status

## Development

- **Linting**: `npm run lint`
- **Formatting**: `npm run format`
- **Testing**: `npm run test`
- **Build**: `npm run build`