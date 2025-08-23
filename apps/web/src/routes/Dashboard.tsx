import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FileText, Calendar, User } from 'lucide-react';
import { useCreateTaxReturn } from '../hooks/useApi';

// Mock data for existing returns - in a real app, this would come from an API
const mockReturns = [
  {
    id: 1,
    taxpayer_id: 1,
    assessment_year: '2025-26',
    form_type: 'ITR2',
    regime: 'new' as const,
    status: 'draft' as const,
    filing_date: null,
    acknowledgment_number: null,
    revised_return: false,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-20T14:45:00Z',
  },
  {
    id: 2,
    taxpayer_id: 2,
    assessment_year: '2024-25',
    form_type: 'ITR1',
    regime: 'old' as const,
    status: 'submitted' as const,
    filing_date: '2024-07-31T23:59:00Z',
    acknowledgment_number: 'ITR123456789',
    revised_return: false,
    created_at: '2024-07-15T09:00:00Z',
    updated_at: '2024-07-31T23:59:00Z',
  },
];

export function Dashboard() {
  const navigate = useNavigate();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    pan: '',
    assessment_year: '2025-26',
    form_type: 'ITR2',
    regime: 'new' as const,
  });

  const createTaxReturnMutation = useCreateTaxReturn();

  const handleCreateReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const newReturn = await createTaxReturnMutation.mutateAsync(formData);
      navigate(`/documents/${newReturn.id}`);
    } catch (error) {
      console.error('Failed to create tax return:', error);
    }
  };

  const handleReturnClick = (returnId: number) => {
    navigate(`/documents/${returnId}`);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', label: 'Draft' },
      submitted: { color: 'bg-blue-100 text-blue-800', label: 'Submitted' },
      processed: { color: 'bg-green-100 text-green-800', label: 'Processed' },
      rejected: { color: 'bg-red-100 text-red-800', label: 'Rejected' },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Tax Returns Dashboard</h1>
          <p className="mt-2 text-gray-600">Manage your tax returns and documents</p>
        </div>

        {/* Create New Return Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create New Return
          </button>
        </div>

        {/* Create Form Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Tax Return</h3>
                
                <form onSubmit={handleCreateReturn} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">PAN Number</label>
                    <input
                      type="text"
                      value={formData.pan}
                      onChange={(e) => setFormData({ ...formData, pan: e.target.value.toUpperCase() })}
                      placeholder="ABCDE1234F"
                      maxLength={10}
                      className="form-input"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Assessment Year</label>
                    <select
                      value={formData.assessment_year}
                      onChange={(e) => setFormData({ ...formData, assessment_year: e.target.value })}
                      className="form-select"
                    >
                      <option value="2025-26">2025-26</option>
                      <option value="2024-25">2024-25</option>
                      <option value="2023-24">2023-24</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Form Type</label>
                    <select
                      value={formData.form_type}
                      onChange={(e) => setFormData({ ...formData, form_type: e.target.value })}
                      className="form-select"
                    >
                      <option value="ITR1">ITR-1 (Sahaj)</option>
                      <option value="ITR2">ITR-2</option>
                      <option value="ITR3">ITR-3</option>
                      <option value="ITR4">ITR-4 (Sugam)</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tax Regime</label>
                    <select
                      value={formData.regime}
                      onChange={(e) => setFormData({ ...formData, regime: e.target.value as 'old' | 'new' })}
                      className="form-select"
                    >
                      <option value="new">New Tax Regime</option>
                      <option value="old">Old Tax Regime</option>
                    </select>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createTaxReturnMutation.isPending}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
                    >
                      {createTaxReturnMutation.isPending ? 'Creating...' : 'Create Return'}
                    </button>
                  </div>
                </form>
                
                {createTaxReturnMutation.error && (
                  <div className="mt-3 text-sm text-red-600">
                    {createTaxReturnMutation.error.message}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Returns List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {mockReturns.map((taxReturn) => (
              <li key={taxReturn.id}>
                <div
                  onClick={() => handleReturnClick(taxReturn.id)}
                  className="px-4 py-4 hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <FileText className="h-8 w-8 text-gray-400" />
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center">
                          <p className="text-sm font-medium text-gray-900">
                            {taxReturn.form_type} - {taxReturn.assessment_year}
                          </p>
                          <div className="ml-2">
                            {getStatusBadge(taxReturn.status)}
                          </div>
                        </div>
                        <div className="mt-1 flex items-center text-sm text-gray-500">
                          <User className="flex-shrink-0 mr-1.5 h-4 w-4" />
                          <span>Taxpayer ID: {taxReturn.taxpayer_id}</span>
                          <Calendar className="flex-shrink-0 ml-4 mr-1.5 h-4 w-4" />
                          <span>Created: {new Date(taxReturn.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-500 capitalize">
                        {taxReturn.regime} regime
                      </span>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {mockReturns.length === 0 && (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tax returns</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new tax return.</p>
          </div>
        )}
      </div>
    </div>
  );
}