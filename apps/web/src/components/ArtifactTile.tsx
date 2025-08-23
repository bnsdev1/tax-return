import React, { useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import type { ArtifactMetadata } from '../types/api';
import { useCreateArtifact, useUploadFile } from '../hooks/useApi';

interface ArtifactTileProps {
  returnId: number;
  artifactType: 'prefill.json' | 'ais.json' | 'tis.json' | 'form16b.pdf' | 'bank.csv' | 'bank.pdf' | 'pnl.csv' | 'cas.pdf' | 'loan_interest' | 'deduction_proofs';
  existingArtifact?: ArtifactMetadata;
}

const ARTIFACT_CONFIG = {
  'prefill.json': {
    title: 'Prefill Data',
    description: 'JSON file with prefilled tax return data',
    accept: '.json',
    type: 'json' as const,
  },
  'ais.json': {
    title: 'AIS Data',
    description: 'Annual Information Statement JSON',
    accept: '.json',
    type: 'json' as const,
  },
  'tis.json': {
    title: 'TIS Data',
    description: 'Tax Information Statement JSON',
    accept: '.json',
    type: 'json' as const,
  },
  'form16b.pdf': {
    title: 'Form 16B',
    description: 'TDS certificate for property transactions',
    accept: '.pdf',
    type: 'pdf' as const,
  },
  'bank.csv': {
    title: 'Bank Statement (CSV)',
    description: 'Bank statement in CSV format',
    accept: '.csv',
    type: 'other' as const,
  },
  'bank.pdf': {
    title: 'Bank Statement (PDF)',
    description: 'Bank statement in PDF format',
    accept: '.pdf',
    type: 'pdf' as const,
  },
  'pnl.csv': {
    title: 'P&L Statement',
    description: 'Profit & Loss statement CSV',
    accept: '.csv',
    type: 'other' as const,
  },
  'cas.pdf': {
    title: 'CAS Statement',
    description: 'Consolidated Account Statement',
    accept: '.pdf',
    type: 'pdf' as const,
  },
  'loan_interest': {
    title: 'Loan Interest Certificate',
    description: 'Home loan interest certificate',
    accept: '.pdf,.jpg,.jpeg,.png',
    type: 'pdf' as const,
  },
  'deduction_proofs': {
    title: 'Deduction Proofs',
    description: 'Supporting documents for deductions',
    accept: '.pdf,.jpg,.jpeg,.png',
    type: 'pdf' as const,
  },
};

export function ArtifactTile({ returnId, artifactType, existingArtifact }: ArtifactTileProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const config = ARTIFACT_CONFIG[artifactType];
  
  const createArtifactMutation = useCreateArtifact();
  const uploadFileMutation = useUploadFile();

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      if (!existingArtifact) {
        // Create artifact metadata first
        const artifactData = {
          name: file.name,
          artifact_type: config.type,
          description: config.description,
          file_size: file.size,
          mime_type: file.type,
          tags: artifactType,
        };

        const artifact = await createArtifactMutation.mutateAsync({
          returnId,
          data: artifactData,
        });

        // Then upload the file
        await uploadFileMutation.mutateAsync({
          returnId,
          artifactId: artifact.id,
          file,
        });
      } else {
        // Upload to existing artifact
        await uploadFileMutation.mutateAsync({
          returnId,
          artifactId: existingArtifact.id,
          file,
        });
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const getStatusIcon = () => {
    if (createArtifactMutation.isPending || uploadFileMutation.isPending) {
      return <Clock className="h-5 w-5 text-yellow-500 animate-spin" />;
    }
    
    if (existingArtifact?.upload_status === 'completed') {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
    
    if (existingArtifact?.upload_status === 'failed') {
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
    
    return <FileText className="h-5 w-5 text-gray-400" />;
  };

  const getStatusText = () => {
    if (createArtifactMutation.isPending || uploadFileMutation.isPending) {
      return 'Uploading...';
    }
    
    if (existingArtifact?.upload_status === 'completed') {
      return `Uploaded (${formatFileSize(existingArtifact.file_size)})`;
    }
    
    if (existingArtifact?.upload_status === 'failed') {
      return 'Upload failed';
    }
    
    return 'Not uploaded';
  };

  const isUploading = createArtifactMutation.isPending || uploadFileMutation.isPending;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <div>
            <h3 className="font-medium text-gray-900">{config.title}</h3>
            <p className="text-sm text-gray-500">{config.description}</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">{getStatusText()}</span>
        
        <button
          onClick={handleUploadClick}
          disabled={isUploading}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload className="h-4 w-4 mr-1" />
          {existingArtifact ? 'Replace' : 'Upload'}
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept={config.accept}
        onChange={handleFileSelect}
        className="hidden"
      />

      {(createArtifactMutation.error || uploadFileMutation.error) && (
        <div className="mt-2 text-sm text-red-600">
          {createArtifactMutation.error?.message || uploadFileMutation.error?.message}
        </div>
      )}
    </div>
  );
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '';
  
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}