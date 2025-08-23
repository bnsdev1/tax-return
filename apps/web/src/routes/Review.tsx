import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  CheckCircle, 
  AlertTriangle, 
  Edit3, 
  Save, 
  X, 
  ArrowLeft,
  ArrowRight,
  Info
} from 'lucide-react';
import { useReviewPreview, useSubmitConfirmations } from '../hooks/useReview';
import type { LineItem, LineItemEdit, TaxHead } from '../types/review';

export function Review() {
  const { returnId } = useParams<{ returnId: string }>();
  const navigate = useNavigate();
  const [confirmations, setConfirmations] = useState<Set<string>>(new Set());
  const [edits, setEdits] = useState<Map<string, LineItemEdit>>(new Map());
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editAmount, setEditAmount] = useState<string>('');
  const [editReason, setEditReason] = useState<string>('');

  const returnIdNum = returnId ? parseInt(returnId, 10) : 0;
  
  const { 
    data: preview, 
    isLoading, 
    error,
    refetch 
  } = useReviewPreview(returnIdNum);
  
  const submitConfirmationsMutation = useSubmitConfirmations();

  // Load existing confirmations when preview loads
  useEffect(() => {
    if (preview) {
      // In a real app, this would come from the server
      const existingConfirmations = new Set<string>();
      setConfirmations(existingConfirmations);
    }
  }, [preview]);

  const handleConfirmationToggle = (lineItemId: string) => {
    const newConfirmations = new Set(confirmations);
    if (newConfirmations.has(lineItemId)) {
      newConfirmations.delete(lineItemId);
    } else {
      newConfirmations.add(lineItemId);
    }
    setConfirmations(newConfirmations);
  };

  const handleEditStart = (lineItem: LineItem) => {
    setEditingItem(lineItem.id);
    setEditAmount(lineItem.amount.toString());
    setEditReason('');
  };

  const handleEditSave = () => {
    if (!editingItem) return;
    
    const newAmount = parseFloat(editAmount);
    if (isNaN(newAmount)) {
      alert('Please enter a valid amount');
      return;
    }

    const newEdits = new Map(edits);
    newEdits.set(editingItem, {
      line_item_id: editingItem,
      new_amount: newAmount,
      reason: editReason
    });
    
    setEdits(newEdits);
    setEditingItem(null);
    setEditAmount('');
    setEditReason('');
  };

  const handleEditCancel = () => {
    setEditingItem(null);
    setEditAmount('');
    setEditReason('');
  };

  const handleSubmitConfirmations = async () => {
    if (!preview) return;

    try {
      await submitConfirmationsMutation.mutateAsync({
        returnId: returnIdNum,
        confirmations: Array.from(confirmations),
        edits: Array.from(edits.values())
      });
      
      // Refresh the preview to get updated data
      refetch();
      
      // Show success message
      alert('Confirmations submitted successfully!');
    } catch (error) {
      console.error('Failed to submit confirmations:', error);
      alert('Failed to submit confirmations. Please try again.');
    }
  };

  const handleContinue = () => {
    // Navigate to next step (e.g., final review or submission)
    navigate(`/final-review/${returnId}`);
  };

  const canProceed = preview?.confirmations.can_proceed || false;
  const hasBlockingVariances = (preview?.confirmations.blocking_variances || 0) > 0;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading review data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto" />
          <p className="mt-4 text-red-600">Failed to load review data</p>
          <button 
            onClick={() => refetch()}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">No preview data available</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => navigate(`/documents/${returnId}`)}
                className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Documents
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Review & Confirm</h1>
              <p className="mt-2 text-gray-600">
                Review the computed values and confirm accuracy before proceeding
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Tax Return #{returnId}</div>
              <div className="text-lg font-semibold text-gray-900">
                Assessment Year: 2025-26
              </div>
            </div>
          </div>
        </div>

        {/* Progress Summary */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Confirmation Progress</h2>
              <p className="text-sm text-gray-600">
                {preview.confirmations.confirmed_items} of {preview.confirmations.total_items} items confirmed
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {preview.confirmations.confirmed_items}
                </div>
                <div className="text-xs text-gray-500">Confirmed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {preview.confirmations.total_items - preview.confirmations.confirmed_items}
                </div>
                <div className="text-xs text-gray-500">Remaining</div>
              </div>
              {hasBlockingVariances && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {preview.confirmations.blocking_variances}
                  </div>
                  <div className="text-xs text-gray-500">Blocking</div>
                </div>
              )}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-4">
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${(preview.confirmations.confirmed_items / preview.confirmations.total_items) * 100}%` 
                }}
              ></div>
            </div>
          </div>
        </div>

        {/* Tax Heads */}
        <div className="space-y-8">
          {Object.entries(preview.heads).map(([headKey, head]) => (
            <TaxHeadSection
              key={headKey}
              head={head}
              confirmations={confirmations}
              edits={edits}
              editingItem={editingItem}
              editAmount={editAmount}
              editReason={editReason}
              onConfirmationToggle={handleConfirmationToggle}
              onEditStart={handleEditStart}
              onEditSave={handleEditSave}
              onEditCancel={handleEditCancel}
              onEditAmountChange={setEditAmount}
              onEditReasonChange={setEditReason}
            />
          ))}
        </div>

        {/* Summary */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Tax Computation Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">Gross Total Income</div>
              <div className="text-lg font-semibold text-gray-900">
                ₹{preview.summary.gross_total_income?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">Total Deductions</div>
              <div className="text-lg font-semibold text-gray-900">
                ₹{preview.summary.total_deductions?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">Taxable Income</div>
              <div className="text-lg font-semibold text-gray-900">
                ₹{preview.summary.taxable_income?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">Tax Liability</div>
              <div className="text-lg font-semibold text-gray-900">
                ₹{preview.summary.tax_liability?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">Refund/Payable</div>
              <div className={`text-lg font-semibold ${
                (preview.summary.refund_or_payable || 0) < 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                ₹{Math.abs(preview.summary.refund_or_payable || 0).toLocaleString()}
                {(preview.summary.refund_or_payable || 0) < 0 ? ' (Refund)' : ' (Payable)'}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex justify-between">
          <button
            onClick={handleSubmitConfirmations}
            disabled={submitConfirmationsMutation.isPending}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Save className="h-4 w-4 mr-2" />
            {submitConfirmationsMutation.isPending ? 'Saving...' : 'Save Confirmations'}
          </button>
          
          {/* Show Tax Payment button if there's payable amount */}
          {(preview.summary.net_tax_payable || 0) > 0 ? (
            <button
              onClick={() => navigate(`/tax-payment/${returnId}`)}
              disabled={!canProceed}
              className={`px-6 py-3 rounded-lg flex items-center ${
                canProceed
                  ? 'bg-orange-600 text-white hover:bg-orange-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Pay Tax (₹{(preview.summary.net_tax_payable || 0).toLocaleString()})
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          ) : (
            <button
              onClick={handleContinue}
              disabled={!canProceed}
              className={`px-6 py-3 rounded-lg flex items-center ${
                canProceed
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Continue
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          )}
        </div>

        {!canProceed && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center">
              <Info className="h-5 w-5 text-yellow-600 mr-2" />
              <div className="text-sm text-yellow-800">
                {hasBlockingVariances 
                  ? 'Please resolve all blocking variances before continuing.'
                  : 'Please confirm all required items before continuing.'
                }
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface TaxHeadSectionProps {
  head: TaxHead;
  confirmations: Set<string>;
  edits: Map<string, LineItemEdit>;
  editingItem: string | null;
  editAmount: string;
  editReason: string;
  onConfirmationToggle: (lineItemId: string) => void;
  onEditStart: (lineItem: LineItem) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onEditAmountChange: (amount: string) => void;
  onEditReasonChange: (reason: string) => void;
}

function TaxHeadSection({
  head,
  confirmations,
  edits,
  editingItem,
  editAmount,
  editReason,
  onConfirmationToggle,
  onEditStart,
  onEditSave,
  onEditCancel,
  onEditAmountChange,
  onEditReasonChange,
}: TaxHeadSectionProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Head Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{head.head_name}</h3>
            <p className="text-sm text-gray-600">
              Total: ₹{head.total_amount.toLocaleString()}
            </p>
          </div>
          {head.variances.length > 0 && (
            <div className="flex items-center text-orange-600">
              <AlertTriangle className="h-4 w-4 mr-1" />
              <span className="text-sm">{head.variances.length} variance(s)</span>
            </div>
          )}
        </div>
      </div>

      {/* Variances */}
      {head.variances.length > 0 && (
        <div className="px-6 py-4 bg-orange-50 border-b border-gray-200">
          <h4 className="text-sm font-medium text-orange-800 mb-2">Variances Requiring Attention</h4>
          <div className="space-y-2">
            {head.variances.map((variance, index) => (
              <div key={index} className="flex items-start space-x-3">
                <AlertTriangle className={`h-4 w-4 mt-0.5 ${
                  variance.blocking ? 'text-red-500' : 'text-orange-500'
                }`} />
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{variance.description}</p>
                  <div className="text-xs text-gray-600 mt-1">
                    Expected: {variance.expected_range} | Actual: {variance.actual_value}
                  </div>
                  {variance.blocking && (
                    <div className="text-xs text-red-600 font-medium mt-1">
                      This variance blocks proceeding
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Line Items */}
      <div className="px-6 py-4">
        <div className="space-y-4">
          {head.line_items.map((lineItem) => (
            <LineItemRow
              key={lineItem.id}
              lineItem={lineItem}
              isConfirmed={confirmations.has(lineItem.id)}
              hasEdit={edits.has(lineItem.id)}
              editValue={edits.get(lineItem.id)}
              isEditing={editingItem === lineItem.id}
              editAmount={editAmount}
              editReason={editReason}
              onConfirmationToggle={onConfirmationToggle}
              onEditStart={onEditStart}
              onEditSave={onEditSave}
              onEditCancel={onEditCancel}
              onEditAmountChange={onEditAmountChange}
              onEditReasonChange={onEditReasonChange}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface LineItemRowProps {
  lineItem: LineItem;
  isConfirmed: boolean;
  hasEdit: boolean;
  editValue?: LineItemEdit;
  isEditing: boolean;
  editAmount: string;
  editReason: string;
  onConfirmationToggle: (lineItemId: string) => void;
  onEditStart: (lineItem: LineItem) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onEditAmountChange: (amount: string) => void;
  onEditReasonChange: (reason: string) => void;
}

function LineItemRow({
  lineItem,
  isConfirmed,
  hasEdit,
  editValue,
  isEditing,
  editAmount,
  editReason,
  onConfirmationToggle,
  onEditStart,
  onEditSave,
  onEditCancel,
  onEditAmountChange,
  onEditReasonChange,
}: LineItemRowProps) {
  const displayAmount = hasEdit ? editValue!.new_amount : lineItem.amount;

  if (isEditing) {
    return (
      <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-medium text-gray-900">{lineItem.label}</h4>
            <p className="text-sm text-gray-600">Source: {lineItem.source}</p>
          </div>
        </div>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New Amount
            </label>
            <input
              type="number"
              value={editAmount}
              onChange={(e) => onEditAmountChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter new amount"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason for Change
            </label>
            <input
              type="text"
              value={editReason}
              onChange={(e) => onEditReasonChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Explain why you're changing this value"
            />
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              onClick={onEditCancel}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              <X className="h-4 w-4" />
            </button>
            <button
              onClick={onEditSave}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Save className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-between p-4 rounded-lg border ${
      isConfirmed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-center space-x-4">
        {lineItem.needs_confirm && (
          <button
            onClick={() => onConfirmationToggle(lineItem.id)}
            className={`flex-shrink-0 ${
              isConfirmed ? 'text-green-600' : 'text-gray-400 hover:text-green-600'
            }`}
          >
            <CheckCircle className="h-5 w-5" />
          </button>
        )}
        
        <div>
          <h4 className="font-medium text-gray-900">{lineItem.label}</h4>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>Source: {lineItem.source}</span>
            {hasEdit && (
              <span className="text-blue-600 font-medium">
                Edited: {editValue!.reason}
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <div className={`font-semibold ${hasEdit ? 'text-blue-600' : 'text-gray-900'}`}>
            ₹{displayAmount.toLocaleString()}
          </div>
          {hasEdit && (
            <div className="text-xs text-gray-500 line-through">
              ₹{lineItem.amount.toLocaleString()}
            </div>
          )}
        </div>
        
        {lineItem.editable && (
          <button
            onClick={() => onEditStart(lineItem)}
            className="text-gray-400 hover:text-blue-600"
          >
            <Edit3 className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}