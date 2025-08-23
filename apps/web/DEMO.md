# Tax Return Application Demo

This document outlines how to demo the tax return application and its key features.

## Prerequisites

1. **Backend Running**: Ensure the FastAPI backend is running on `http://localhost:8000`
2. **Frontend Running**: Start the React app with `npm run dev` (runs on `http://localhost:5173`)

## Demo Flow

### 1. Dashboard - Creating a New Return

**URL**: `http://localhost:5173/`

**Steps**:
1. Click "Create New Return" button
2. Fill in the form:
   - **PAN**: Enter a valid PAN (e.g., "ABCDE1234F")
   - **Assessment Year**: Select "2025-26"
   - **Form Type**: Select "ITR2"
   - **Tax Regime**: Select "New Tax Regime"
3. Click "Create Return"
4. Application navigates to the Documents page

**What to highlight**:
- Clean, professional UI
- Form validation (PAN format)
- Loading states during creation
- Automatic navigation after creation

### 2. Documents Page - File Upload

**URL**: `http://localhost:5173/documents/1` (or the ID of created return)

**Steps**:
1. **Show Document Cards**: Point out the pre-configured document types:
   - JSON files (prefill.json, ais.json, tis.json)
   - PDF files (form16b.pdf, bank.pdf, cas.pdf)
   - CSV files (bank.csv, pnl.csv)
   - Certificate files (loan_interest, deduction_proofs)

2. **Upload Files**:
   - Click "Upload" on any card
   - Select appropriate file type (respects file restrictions)
   - Show upload progress and status changes
   - Demonstrate file replacement functionality

3. **Status Indicators**:
   - Not uploaded (gray icon)
   - Uploading (spinning clock)
   - Completed (green checkmark with file size)
   - Failed (red alert icon)

**What to highlight**:
- File type restrictions per document type
- Real-time upload status
- File size display
- Replace functionality for existing files

### 3. Build Process - Tax Return Processing

**Still on Documents page**

**Steps**:
1. **Start Build**: Click the primary "Run Build" button
2. **Show Progress**: 
   - Progress bar appears
   - Real-time percentage updates
   - Current step descriptions
   - Button changes to "Build in Progress..."

3. **Completion States**:
   - **Success**: Green success message with checkmark
   - **Failure**: Red error message with details
   - **Button Updates**: Changes to "Rebuild" or "Retry Build"

**What to highlight**:
- Real-time progress tracking
- Status polling (updates every 2 seconds)
- Clear success/failure feedback
- Validation results display

### 4. Navigation and State Management

**Steps**:
1. **Back Navigation**: Use "Back to Dashboard" link
2. **Return List**: Show existing returns with status badges
3. **State Persistence**: Navigate between returns to show data persistence
4. **Error Handling**: Demonstrate 404 page with invalid URLs

**What to highlight**:
- Smooth navigation between routes
- State management with TanStack Query
- Data caching and background updates
- Error boundaries and 404 handling

## Key Features to Emphasize

### 1. **User Experience**
- Intuitive workflow: Create → Upload → Build
- Real-time feedback and progress tracking
- Professional, clean interface
- Responsive design

### 2. **Technical Implementation**
- React Router for navigation
- TanStack Query for state management
- TypeScript for type safety
- Tailwind CSS for styling
- Error boundaries for reliability

### 3. **API Integration**
- RESTful API calls to FastAPI backend
- File upload with multipart form data
- Real-time status polling
- Proper error handling

### 4. **Document Management**
- Pre-configured document types for tax returns
- File type validation
- Upload status tracking
- File replacement capability

### 5. **Build Process**
- Asynchronous job processing
- Progress tracking with percentage and steps
- Validation results display
- Success/failure handling

## Demo Script

> "Let me show you our tax return application. We start on the Dashboard where users can see all their tax returns and create new ones."

> "I'll create a new return by clicking this button. Notice how the form validates the PAN format and provides clear options for assessment year, form type, and tax regime."

> "Once created, we're taken to the Documents page where users can upload all their tax documents. Each card represents a specific document type with appropriate file restrictions."

> "Let me upload a few files to show the real-time status updates... Notice how the status changes from 'Not uploaded' to 'Uploading' to 'Completed' with file size."

> "Now for the key feature - the Build process. When I click 'Run Build', it starts processing the tax return with real-time progress updates."

> "The progress bar shows percentage completion and current step. This polls the backend every 2 seconds for updates until completion."

> "Finally, we get validation results and can see any warnings or errors. The system provides clear feedback on the tax return processing."

## Troubleshooting

- **API Connection Issues**: Check that backend is running on port 8000
- **CORS Errors**: Ensure backend has CORS configured for localhost:5173
- **File Upload Failures**: Backend needs file upload endpoints implemented
- **Build Process**: Backend needs job processing endpoints implemented

## Next Steps

After the demo, you can discuss:
- Additional document types
- Integration with tax calculation engines
- PDF generation and download
- E-filing integration
- User authentication and multi-tenancy