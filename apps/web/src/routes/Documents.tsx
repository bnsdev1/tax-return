import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { ArtifactTile } from '../components/ArtifactTile';
import { useTaxReturn, useTaxReturnStatus, useArtifacts, useStartBuildJob } from '../hooks/useApi';

const ARTIFACT_TYPES = [
  'prefill.json',
  'ais.json',
  'tis.json',
  'form16b.pdf',
  'bank.csv',
  'bank.pdf',
  'pnl.csv',
  'cas.pdf',
  'loan_interest',
  'deduction_proofs',
] as const;

export function Documents() {
  const { returnId } = useParams<{ returnId: string }>();
  const navigate = useNavigate();
  const returnIdNum = returnId ? parseInt(returnId, 10) : 0;

  const { data: taxReturn, isLoading: isLoadingReturn } = useTaxReturn(returnIdNum);
  const { data: artifacts, isLoading: isLoadingArtifacts } = useArtifacts(returnIdNum);
  const { data: status, isLoading: isLoadingStatus } = useTaxReturnStatus(returnIdNum);
  const startBuildMutation = useStartBuildJob();

  const handleStartBuild = async () => {
    try {
      await startBuildMutation.mutateAsync(returnIdNum);
    } catch (error) {
      console.error('Failed to start build:', error);
    }
  };

  const getBuildButtonState = () => {
    if (startBuildMutation.isPending) {
      return { disabled: true, text: 'Starting Build...', icon: Clock };
    }
    
    if (status?.status === 'in_progress') {
      return { disabled: true, text: 'Build in Progress...', icon: Clock };
    }
    
    if (status?.status === 'completed') {
      return { disabled: false, text: 'Rebuild', icon: Play };
    }
    
    if (status?.status === 'failed') {
      return { disabled: false, text: 'Retry Build', icon: AlertCircle };
    }
    
    return { disabled: false, text: 'Run Build', icon: Play };
  };

  const getProgressBar = () => {
    if (!status || status.status === 'pending') return null;
    
    const progressColor = status.status === 'failed' ? 'bg-red-500' : 
                         status.status === 'completed' ? 'bg-green-500' : 'bg-blue-500';
    
    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Build Progress</span>
          <span className="text-sm text-gray-500">{status.progress_percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${progressColor}`}
            style={{ width: `${status.progress_percentage}%` }}
          />
        </div>
        <div className="mt-2 text-sm text-gray-600">
          {status.current_step}
        </div>
        
        {status.status === 'failed' && status.error_message && (
          <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Build Failed</h3>
                <div className="mt-2 text-sm text-red-700">
                  {status.error_message}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {status.status === 'completed' && (
          <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center justify-between">
              <div className="flex">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">Build Completed Successfully</h3>
                  <div className="mt-2 text-sm text-green-700">
                    Your tax return has been processed and is ready for review.
                  </div>
                </div>
              </div>
              <button
                onClick={() => navigate(`/review/${returnId}`)}
                className="ml-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
              >
                Review & Confirm
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (isLoadingReturn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading tax return...</p>
        </div>
      </div>
    );
  }

  if (!taxReturn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Tax Return Not Found</h2>
          <p className="mt-2 text-gray-600">The requested tax return could not be found.</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const buttonState = getBuildButtonState();
  const ButtonIcon = buttonState.icon;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Dashboard
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {taxReturn.form_type} - {taxReturn.assessment_year}
              </h1>
              <p className="mt-2 text-gray-600">
                Tax regime: {taxReturn.regime} • Status: {taxReturn.status}
              </p>
            </div>
            
            <button
              onClick={handleStartBuild}
              disabled={buttonState.disabled}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ButtonIcon className="h-5 w-5 mr-2" />
              {buttonState.text}
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        {getProgressBar()}

        {/* Documents Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Documents & Artifacts</h2>
          
          {isLoadingArtifacts ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading artifacts...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {ARTIFACT_TYPES.map((artifactType) => {
                const existingArtifact = artifacts?.find(
                  (artifact) => artifact.name.includes(artifactType) || 
                               (artifact as any).tags?.includes(artifactType)
                );
                
                return (
                  <ArtifactTile
                    key={artifactType}
                    returnId={returnIdNum}
                    artifactType={artifactType}
                    existingArtifact={existingArtifact}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Validation Results */}
        {status?.validations && status.validations.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Validation Results</h3>
            <div className="space-y-3">
              {status.validations.map((validation, index) => (
                <div key={index} className="flex items-start space-x-3">
                  {validation.status === 'passed' && (
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  )}
                  {validation.status === 'warning' && (
                    <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                  )}
                  {validation.status === 'failed' && (
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {validation.rule_name}
                    </p>
                    {validation.message && (
                      <p className="text-sm text-gray-600">{validation.message}</p>
                    )}
                    {validation.field_path && (
                      <p className="text-xs text-gray-500">Field: {validation.field_path}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}