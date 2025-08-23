import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Upload, Download, CreditCard, AlertCircle, CheckCircle, FileText, Calendar, Building, Hash } from 'lucide-react';

interface TaxPaymentSummary {
  total_tax_liability: string;
  tds_paid: string;
  advance_tax_paid: string;
  net_payable: string;
  interest_234a: string;
  interest_234b: string;
  interest_234c: string;
  total_interest: string;
  total_amount_due: string;
  challan_present: boolean;
  challan_amount?: string;
  remaining_balance?: string;
}

interface ChallanData {
  id: number;
  cin_crn: string;
  bsr_code: string;
  bank_reference: string;
  payment_date: string;
  amount: string;
  challan_file_path?: string;
  created_at: string;
}

const TaxPayment: React.FC = () => {
  const { returnId } = useParams<{ returnId: string }>();
  const navigate = useNavigate();
  
  const [summary, setSummary] = useState<TaxPaymentSummary | null>(null);
  const [existingChallan, setExistingChallan] = useState<ChallanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    cin_crn: '',
    bsr_code: '',
    bank_reference: '',
    payment_date: '',
    amount_paid: ''
  });
  const [challanFile, setChallanFile] = useState<File | null>(null);

  useEffect(() => {
    fetchPaymentSummary();
    fetchExistingChallan();
  }, [returnId]);

  const fetchPaymentSummary = async () => {
    try {
      const response = await fetch(`/api/challan/payment-summary/${returnId}`);
      if (!response.ok) throw new Error('Failed to fetch payment summary');
      const data = await response.json();
      setSummary(data);
      
      // If no tax is payable, redirect back to review
      if (parseFloat(data.net_payable) <= 0) {
        navigate(`/returns/${returnId}/review`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payment summary');
    } finally {
      setLoading(false);
    }
  };

  const fetchExistingChallan = async () => {
    try {
      const response = await fetch(`/api/challan/${returnId}`);
      if (response.ok) {
        const data = await response.json();
        if (data) {
          setExistingChallan(data);
        }
      }
    } catch (err) {
      console.error('Error fetching existing challan:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Please upload a PDF file only');
        return;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        setError('File size must be less than 10MB');
        return;
      }
      setChallanFile(file);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('cin_crn', formData.cin_crn);
      formDataToSend.append('bsr_code', formData.bsr_code);
      formDataToSend.append('bank_reference', formData.bank_reference);
      formDataToSend.append('payment_date', formData.payment_date);
      formDataToSend.append('amount_paid', formData.amount_paid);
      
      if (challanFile) {
        formDataToSend.append('challan_file', challanFile);
      }

      const response = await fetch(`/api/challan/upload/${returnId}`, {
        method: 'POST',
        body: formDataToSend,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload challan');
      }

      setSuccess('Challan uploaded successfully!');
      fetchExistingChallan();
      fetchPaymentSummary();
      
      // Reset form
      setFormData({
        cin_crn: '',
        bsr_code: '',
        bank_reference: '',
        payment_date: '',
        amount_paid: ''
      });
      setChallanFile(null);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload challan');
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (amount: string) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(parseFloat(amount));
  };

  const downloadChallan = async () => {
    try {
      const response = await fetch(`/api/challan/download/${returnId}`);
      if (!response.ok) throw new Error('Failed to download challan');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `challan_${existingChallan?.cin_crn}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to download challan file');
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading payment summary...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Unable to load payment summary. Please try again.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Self-Assessment Tax Payment</h1>
        <p className="text-gray-600">Complete your tax payment to proceed with return filing</p>
      </div>

      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6 border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Tax Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Tax Payment Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Tax Liability:</span>
                <span className="font-medium">{formatCurrency(summary.total_tax_liability)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">TDS Paid:</span>
                <span className="font-medium text-green-600">-{formatCurrency(summary.tds_paid)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Advance Tax Paid:</span>
                <span className="font-medium text-green-600">-{formatCurrency(summary.advance_tax_paid)}</span>
              </div>
              <Separator />
              <div className="flex justify-between text-lg font-semibold">
                <span>Net Tax Payable:</span>
                <span className="text-red-600">{formatCurrency(summary.net_payable)}</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Interest u/s 234A:</span>
                <span className="font-medium">{formatCurrency(summary.interest_234a)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Interest u/s 234B:</span>
                <span className="font-medium">{formatCurrency(summary.interest_234b)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Interest u/s 234C:</span>
                <span className="font-medium">{formatCurrency(summary.interest_234c)}</span>
              </div>
              <Separator />
              <div className="flex justify-between text-lg font-semibold">
                <span>Total Amount Due:</span>
                <span className="text-red-600">{formatCurrency(summary.total_amount_due)}</span>
              </div>
            </div>
          </div>

          {summary.challan_present && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-800">Challan Uploaded</span>
                </div>
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Paid: {formatCurrency(summary.challan_amount || '0')}
                </Badge>
              </div>
              {summary.remaining_balance && parseFloat(summary.remaining_balance) > 0 && (
                <p className="text-sm text-green-700 mt-2">
                  Remaining balance: {formatCurrency(summary.remaining_balance)}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment Instructions */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Payment Instructions</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h4 className="font-semibold text-blue-900 mb-2">How to Pay Self-Assessment Tax</h4>
            <ol className="list-decimal list-inside space-y-2 text-blue-800">
              <li>Visit the <strong>NSDL TIN website</strong> or your bank's online portal</li>
              <li>Select <strong>"Challan No./ITNS 280"</strong> for Income Tax payment</li>
              <li>Choose <strong>"(0021) Income Tax (Other than companies)"</strong> as tax type</li>
              <li>Enter the <strong>total amount due: {formatCurrency(summary.total_amount_due)}</strong></li>
              <li>Complete the payment and <strong>download the challan PDF</strong></li>
              <li>Upload the challan details and PDF file below</li>
            </ol>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="bg-gray-50 p-3 rounded">
              <h5 className="font-semibold mb-2">Payment Details</h5>
              <ul className="space-y-1">
                <li><strong>Tax Type:</strong> 0021 - Income Tax</li>
                <li><strong>Assessment Year:</strong> 2025-26</li>
                <li><strong>Amount:</strong> {formatCurrency(summary.total_amount_due)}</li>
              </ul>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <h5 className="font-semibold mb-2">Important Notes</h5>
              <ul className="space-y-1 text-xs">
                <li>• Payment must be made before filing the return</li>
                <li>• Keep the challan PDF for your records</li>
                <li>• Interest may apply for late payments</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Existing Challan Display */}
      {existingChallan && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Uploaded Challan Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Hash className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">CIN/CRN:</span>
                  <span className="font-mono text-sm">{existingChallan.cin_crn}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Building className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">BSR Code:</span>
                  <span className="font-mono text-sm">{existingChallan.bsr_code}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Hash className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Bank Reference:</span>
                  <span className="font-mono text-sm">{existingChallan.bank_reference}</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Payment Date:</span>
                  <span className="text-sm">{new Date(existingChallan.payment_date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <CreditCard className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Amount Paid:</span>
                  <span className="font-semibold text-green-600">{formatCurrency(existingChallan.amount)}</span>
                </div>
                {existingChallan.challan_file_path && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={downloadChallan}
                    className="flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download Challan
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Challan Upload Form */}
      {!existingChallan && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Challan Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="cin_crn">CIN/CRN Number *</Label>
                  <Input
                    id="cin_crn"
                    name="cin_crn"
                    value={formData.cin_crn}
                    onChange={handleInputChange}
                    placeholder="Enter 16-digit CIN/CRN"
                    maxLength={16}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="bsr_code">BSR Code *</Label>
                  <Input
                    id="bsr_code"
                    name="bsr_code"
                    value={formData.bsr_code}
                    onChange={handleInputChange}
                    placeholder="Enter 7-digit BSR code"
                    maxLength={7}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="bank_reference">Bank Reference Number *</Label>
                  <Input
                    id="bank_reference"
                    name="bank_reference"
                    value={formData.bank_reference}
                    onChange={handleInputChange}
                    placeholder="Enter bank reference number"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="payment_date">Payment Date *</Label>
                  <Input
                    id="payment_date"
                    name="payment_date"
                    type="date"
                    value={formData.payment_date}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="amount_paid">Amount Paid (₹) *</Label>
                  <Input
                    id="amount_paid"
                    name="amount_paid"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.amount_paid}
                    onChange={handleInputChange}
                    placeholder="Enter amount paid"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="challan_file">Challan PDF File</Label>
                  <Input
                    id="challan_file"
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="cursor-pointer"
                  />
                  <p className="text-xs text-gray-500 mt-1">Upload PDF file (max 10MB)</p>
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="submit"
                  disabled={submitting}
                  className="flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      Upload Challan
                    </>
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate(`/returns/${returnId}/review`)}
                >
                  Back to Review
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TaxPayment;