import React, { useState, useEffect } from 'react';

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileKey: string;
  fileName: string;
}

interface FileContent {
  success: boolean;
  file_key: string;
  file_name: string;
  content_type: string;
  size: number;
  is_text: boolean;
  content: string | null;
  error?: string;
}

const FilePreviewModal: React.FC<FilePreviewModalProps> = ({
  isOpen,
  onClose,
  fileKey,
  fileName,
}) => {
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && fileKey) {
      loadFileContent();
    }
  }, [isOpen, fileKey]);

  const loadFileContent = async () => {
    setLoading(true);
    setError(null);
    setFileContent(null);

    try {
      const response = await fetch(`/api/s3/content/${encodeURIComponent(fileKey)}`);
      const data = await response.json();

      if (data.success) {
        setFileContent(data);
      } else {
        setError(data.error || 'Failed to load file content');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error loading file content:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading file content...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-red-500 text-lg mb-2">❌ Error</div>
            <div className="text-gray-600 dark:text-gray-400">{error}</div>
          </div>
        </div>
      );
    }

    if (!fileContent) {
      return null;
    }

    // Handle different content types
    if (fileContent.content_type.startsWith('image/')) {
      return (
        <div className="flex justify-center">
          <img
            src={`data:${fileContent.content_type};base64,${fileContent.content}`}
            alt={fileName}
            className="max-w-full max-h-96 object-contain"
          />
        </div>
      );
    }

    if (fileContent.is_text && fileContent.content) {
      // Check if this is extracted content from a Word document
      const isWordDocument = fileName.toLowerCase().endsWith('.docx') ||
                             fileContent.content_type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

      return (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 max-h-96 overflow-auto">
          {isWordDocument ? (
            // For Word documents, use regular text formatting instead of monospace
            <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
              {fileContent.content}
            </div>
          ) : (
            // For code/text files, use monospace font
            <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono">
              {fileContent.content}
            </pre>
          )}
        </div>
      );
    }

    // For Word documents and other binary files that couldn't be processed
    if (!fileContent.is_text && (
        fileContent.content_type.includes('wordprocessingml') ||
        fileContent.content_type.includes('pdf') ||
        fileContent.content_type.includes('spreadsheet'))) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-6xl mb-4">📄</div>
            <div className="text-gray-600 dark:text-gray-400 mb-4">
              This file type cannot be previewed directly.
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-500">
              File type: {fileContent.content_type}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-500">
              Size: {formatFileSize(fileContent.size)}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-6xl mb-4">📁</div>
          <div className="text-gray-600 dark:text-gray-400">
            Preview not available for this file type
          </div>
        </div>
      </div>
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white dark:bg-gray-800 shadow-xl rounded-2xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <svg 
                width="24" 
                height="24" 
                viewBox="0 0 24 24" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg" 
                className="stroke-[2] text-gray-600 dark:text-gray-400"
              >
                <path
                  d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"
                  stroke="currentColor"
                />
                <polyline points="13,2 13,9 20,9" stroke="currentColor" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                File Preview
              </h3>
            </div>
            <button
              onClick={onClose}
              className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* File name and info */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
              {fileName}
            </h4>
            {fileContent && (
              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                <span>Size: {formatFileSize(fileContent.size)}</span>
                <span>Type: {fileContent.content_type}</span>
                {fileName.toLowerCase().endsWith('.docx') && fileContent.is_text && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    Text Extracted
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Content */}
          <div className="max-h-[70vh] overflow-auto">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilePreviewModal;
