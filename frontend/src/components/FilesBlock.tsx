import React, { useState, useEffect, useRef } from 'react';
import FilePreviewModal from './FilePreviewModal';

interface FileItem {
  key: string;
  name: string;
  size: number;
  last_modified: string;
  folder: string;
  // New fields from file management system
  file_id?: string;
  content_type?: string;
  metadata?: any;
}

interface FilesBlockProps {
  className?: string;
  userId: string;
}

const FilesBlock: React.FC<FilesBlockProps> = ({ className = "", userId }) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [previewModal, setPreviewModal] = useState<{isOpen: boolean, fileKey: string, fileName: string}>({
    isOpen: false,
    fileKey: '',
    fileName: ''
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load files on component mount and when userId changes
  useEffect(() => {
    if (userId) {
      loadFiles();
    }
  }, [userId]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadFiles = async () => {
    if (!userId) {
      setFiles([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/s3/files?user_id=${encodeURIComponent(userId)}`);
      const data = await response.json();

      if (data.success) {
        setFiles(data.files || []);
      } else {
        setError(data.error || 'Failed to load files');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error loading files:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (fileList: FileList) => {
    if (!fileList || fileList.length === 0) return;

    if (!userId) {
      setError('User not logged in');
      return;
    }

    // Check file limit
    const maxFiles = 50;
    if (files.length + fileList.length > maxFiles) {
      setError(`Cannot upload more than ${maxFiles} files. You currently have ${files.length} files.`);
      return;
    }

    setUploading(true);
    setError(null);

    try {
      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);

        const response = await fetch('/api/s3/upload', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (!data.success) {
          throw new Error(data.error || `Failed to upload ${file.name}`);
        }
      }

      // Reload files after successful upload
      await loadFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (file: FileItem) => {
    try {
      const response = await fetch(`/api/s3/download/${encodeURIComponent(file.key)}`);
      
      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Download failed');
      console.error('Download error:', err);
    }
  };

  const handleDelete = async (file: FileItem) => {
    if (!confirm(`Are you sure you want to delete "${file.name}"?`)) {
      return;
    }

    if (!userId) {
      setError('User not logged in');
      return;
    }

    try {
      const response = await fetch(`/api/s3/delete/${encodeURIComponent(file.key)}?user_id=${encodeURIComponent(userId)}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (data.success) {
        await loadFiles(); // Reload files after deletion
      } else {
        throw new Error(data.error || 'Delete failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
      console.error('Delete error:', err);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };



  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    handleFileUpload(files);
  };

  const handleFileClick = (file: FileItem) => {
    setPreviewModal({
      isOpen: true,
      fileKey: file.key,
      fileName: file.name
    });
  };

  const closePreviewModal = () => {
    setPreviewModal({
      isOpen: false,
      fileKey: '',
      fileName: ''
    });
  };

  return (
    <div
      className={`w-full flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-gray-600 transition-all duration-200 overflow-hidden ${className}`}
      style={{
        minHeight: isCollapsed ? 'auto' : 'calc(100vh * 0.2)',
        maxHeight: isCollapsed ? 'auto' : 'calc(100vh * 0.3)'
      }}
    >
      {/* Files Header */}
      <div
        className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 flex-shrink-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        style={{ padding: 'calc(100vw / 7 * 0.04)' }}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center" style={{ gap: 'calc(100vw / 7 * 0.02)' }}>
          <svg
            style={{
              width: 'calc(100vw / 7 * 0.065)',
              height: 'calc(100vw / 7 * 0.065)'
            }}
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
          <h3
            className="font-medium text-gray-900 dark:text-white"
            style={{ fontSize: 'calc(100vw / 7 * 0.06)' }}
          >
            Files
          </h3>
        </div>
        <div className="flex items-center" style={{ gap: 'calc(100vw / 7 * 0.02)' }}>
          <div
            className={`font-light ${
              files.length >= 45
                ? 'text-red-500 dark:text-red-400'
                : files.length >= 40
                ? 'text-yellow-500 dark:text-yellow-400'
                : 'text-gray-500 dark:text-gray-400'
            }`}
            style={{ fontSize: 'calc(100vw / 7 * 0.035)' }}
            title={`${files.length} files uploaded, maximum 50 allowed`}
          >
            ({files.length}/50)
          </div>
          {!isCollapsed && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (files.length < 50) {
                    fileInputRef.current?.click();
                  }
                }}
                disabled={uploading || files.length >= 50}
                className={`rounded transition-colors ${
                  files.length >= 50
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
                style={{ padding: 'calc(100vw / 7 * 0.01)' }}
                title={files.length >= 50 ? 'Maximum files reached (50/50)' : 'Upload files'}
              >
                <svg
                  style={{
                    width: 'calc(100vw / 7 * 0.055)',
                    height: 'calc(100vw / 7 * 0.055)'
                  }}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7,10 12,5 17,10" />
                  <line x1="12" y1="5" x2="12" y2="15" />
                </svg>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  loadFiles();
                }}
                disabled={loading}
                className="rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                style={{ padding: 'calc(100vw / 7 * 0.01)' }}
                title="Refresh"
              >
                <svg
                  style={{
                    width: 'calc(100vw / 7 * 0.055)',
                    height: 'calc(100vw / 7 * 0.055)'
                  }}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className={loading ? 'animate-spin' : ''}
                >
                  <polyline points="23,4 23,10 17,10" />
                  <polyline points="1,20 1,14 7,14" />
                  <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                </svg>
              </button>
            </>
          )}
          {/* Collapse/Expand Icon */}
          <svg
            style={{
              width: 'calc(100vw / 7 * 0.06)',
              height: 'calc(100vw / 7 * 0.06)'
            }}
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={`stroke-[2] text-gray-400 transition-transform duration-200 ${
              isCollapsed ? 'rotate-180' : ''
            }`}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Files Content - Collapsible */}
      {!isCollapsed && (
        <>
          {/* Upload Area */}
          <div
            className={`border-2 border-dashed rounded-lg transition-colors ${
              dragOver
                ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
            }`}
            style={{
              margin: 'calc(100vw / 7 * 0.02)',
              padding: 'calc(100vw / 7 * 0.04)'
            }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => {
              if (files.length < 50) {
                fileInputRef.current?.click();
              }
            }}
          >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
        />
        {uploading ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Uploading...</span>
          </div>
        ) : (
          <div className="cursor-pointer flex items-center justify-center">
            <svg
              className="text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              style={{
                width: 'calc(100vw / 7 * 0.08)',
                height: 'calc(100vw / 7 * 0.08)'
              }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
            <div className="mx-2 mb-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Files List */}
          <div
            className="flex-1 overflow-y-auto files-list-scrollbar"
            style={{ padding: 'calc(100vw / 7 * 0.02)' }}
          >
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          </div>
        ) : files.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
            <div>
              <div
                className="mb-2"
                style={{ fontSize: 'calc(100vw / 7 * 0.07)' }}
              >
                📁 No files yet
              </div>
              <div
                className="font-light"
                style={{ fontSize: 'calc(100vw / 7 * 0.05)' }}
              >
                Upload some files to get started (max 50 files)
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {files.map((file) => (
              <div
                key={file.key}
                className="group px-3 py-2 rounded-lg hover:bg-gray-100/50 dark:hover:bg-gray-700/50 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-600 cursor-pointer"
                onClick={() => handleFileClick(file)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div
                      className="text-sm font-medium text-gray-900 dark:text-white truncate"
                      title={`${file.name} (${formatFileSize(file.size)})`}
                    >
                      {file.name}
                    </div>
                  </div>
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(file);
                      }}
                      className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                      title="Download"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-15" />
                        <polyline points="7,10 12,15 17,10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(file);
                      }}
                      className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3,6 5,6 21,6" />
                        <path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6m3,0V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
          </div>
        </>
      )}

      {/* File Preview Modal */}
      <FilePreviewModal
        isOpen={previewModal.isOpen}
        onClose={closePreviewModal}
        fileKey={previewModal.fileKey}
        fileName={previewModal.fileName}
      />
    </div>
  );
};

export default FilesBlock;
