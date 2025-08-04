import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import mammoth from 'mammoth';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

// Import react-pdf CSS
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Import Word document CSS
import '../styles/word-document.css';

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
  is_pdf?: boolean;
  is_docx?: boolean;
  raw_content?: string;
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
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);

  useEffect(() => {
    if (isOpen && fileKey) {
      loadFileContent();
    } else if (!isOpen) {
      // Reset state when modal closes
      setFileContent(null);
      setWordHtmlContent(null);
      setWordProcessing(false);
      setError(null);
      setPageNumber(1);
      setNumPages(0);
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

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const [wordHtmlContent, setWordHtmlContent] = useState<string | null>(null);
  const [wordProcessing, setWordProcessing] = useState(false);

  // Process Word document with mammoth if backend didn't provide HTML
  useEffect(() => {
    if (fileContent?.is_docx && !fileContent?.content && fileContent?.raw_content && !wordHtmlContent && !wordProcessing) {
      setWordProcessing(true);

      // Convert base64 to ArrayBuffer
      const base64Data = fileContent.raw_content;
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // Use mammoth to convert to HTML
      mammoth.convertToHtml({ arrayBuffer: bytes.buffer })
        .then((result) => {
          setWordHtmlContent(result.value);
          setWordProcessing(false);
          if (result.messages.length > 0) {
            console.warn('Mammoth conversion warnings:', result.messages);
          }
        })
        .catch((error) => {
          console.error('Error converting Word document:', error);
          setWordProcessing(false);
        });
    }
  }, [fileContent, wordHtmlContent, wordProcessing]);

  const renderWordDocument = () => {
    if (!fileContent?.content && !fileContent?.raw_content && !wordHtmlContent) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-6xl mb-4">📄</div>
            <div className="text-gray-600 dark:text-gray-400 mb-4">
              Word Document
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-500 mb-4">
              Unable to preview this document
            </div>
            <button
              onClick={() => {
                if (fileContent?.raw_content) {
                  const link = document.createElement('a');
                  link.href = `data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,${fileContent.raw_content}`;
                  link.download = fileName;
                  link.click();
                }
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Download to View
            </button>
          </div>
        </div>
      );
    }

    // Show loading while processing with mammoth
    if (wordProcessing) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <div className="text-gray-600 dark:text-gray-400">
              Processing Word document...
            </div>
          </div>
        </div>
      );
    }

    // Use backend HTML content if available, otherwise use mammoth-processed content
    const htmlContent = fileContent?.content || wordHtmlContent;

    if (htmlContent) {
      // Render HTML content from Word document
      return (
        <div className="word-document-container max-h-96 overflow-auto bg-gray-50 dark:bg-gray-900 rounded-lg">
          <div
            className="word-document bg-white dark:bg-gray-800 p-8 m-4 rounded-lg shadow-lg prose prose-lg max-w-none"
            style={{
              fontFamily: '"Times New Roman", serif',
              lineHeight: '1.6',
              color: '#333'
            }}
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
          <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Word Document Preview {!fileContent?.content && wordHtmlContent ? '(Client-side processed)' : ''}
            </span>
            <button
              onClick={() => {
                if (fileContent?.raw_content) {
                  const link = document.createElement('a');
                  link.href = `data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,${fileContent.raw_content}`;
                  link.download = fileName;
                  link.click();
                }
              }}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
            >
              Download Original
            </button>
          </div>
        </div>
      );
    }

    return null;
  };

  const renderPDFDocument = () => {
    if (!fileContent?.content) return null;

    const pdfData = `data:application/pdf;base64,${fileContent.content}`;

    return (
      <div className="flex flex-col items-center">
        <div className="mb-4 flex items-center space-x-4">
          <button
            onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
            disabled={pageNumber <= 1}
            className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {pageNumber} of {numPages}
          </span>
          <button
            onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
            disabled={pageNumber >= numPages}
            className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
        <div className="border border-gray-300 dark:border-gray-600 rounded">
          <Document
            file={pdfData}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span className="ml-2">Loading PDF...</span>
              </div>
            }
            error={
              <div className="flex items-center justify-center h-64">
                <div className="text-red-500">Failed to load PDF</div>
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              width={Math.min(800, window.innerWidth - 100)}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
        </div>
      </div>
    );
  };

  const renderMarkdownContent = () => {
    if (!fileContent?.content && !fileContent?.raw_content) return null;

    const markdownContent = fileContent.raw_content || fileContent.content || '';

    return (
      <div className="prose prose-sm max-w-none dark:prose-invert bg-white dark:bg-gray-800 p-6 rounded-lg">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={tomorrow}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {markdownContent}
        </ReactMarkdown>
      </div>
    );
  };

  const renderTextContent = () => {
    if (!fileContent?.content) return null;

    const fileExt = fileName.split('.').pop()?.toLowerCase();
    const isCodeFile = ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'css', 'html', 'json', 'xml'].includes(fileExt || '');

    if (isCodeFile) {
      return (
        <div className="bg-gray-900 rounded-lg overflow-hidden">
          <SyntaxHighlighter
            language={fileExt}
            style={tomorrow}
            showLineNumbers
            wrapLines
            customStyle={{
              margin: 0,
              padding: '1rem',
              background: 'transparent',
            }}
          >
            {fileContent.content}
          </SyntaxHighlighter>
        </div>
      );
    }

    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 max-h-96 overflow-auto">
        <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono">
          {fileContent.content}
        </pre>
      </div>
    );
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

    // Handle different content types with proper rendering
    if (fileContent.content_type.startsWith('image/')) {
      return (
        <div className="flex justify-center">
          <img
            src={`data:${fileContent.content_type};base64,${fileContent.content}`}
            alt={fileName}
            className="max-w-full max-h-96 object-contain rounded"
          />
        </div>
      );
    }

    if (fileContent.is_pdf) {
      return renderPDFDocument();
    }

    if (fileContent.is_docx) {
      return renderWordDocument();
    }

    if (fileName.toLowerCase().endsWith('.md')) {
      return renderMarkdownContent();
    }

    if (fileContent.is_text && fileContent.content) {
      return renderTextContent();
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
                {fileContent && (
                  <>
                    {fileContent.is_pdf && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                        PDF Viewer
                      </span>
                    )}
                    {fileContent.is_docx && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                        Word Document
                      </span>
                    )}
                    {fileName.toLowerCase().endsWith('.md') && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        Markdown Rendered
                      </span>
                    )}
                    {fileContent.is_text && !fileContent.is_pdf && !fileContent.is_docx && !fileName.toLowerCase().endsWith('.md') && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200">
                        {['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'css', 'html', 'json', 'xml'].includes(fileName.split('.').pop()?.toLowerCase() || '') ? 'Code Highlighted' : 'Text File'}
                      </span>
                    )}
                  </>
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
