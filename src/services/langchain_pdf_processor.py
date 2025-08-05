"""
LangChain PDF Processor for enhanced PDF text extraction.
Uses multiple LangChain document loaders for better PDF processing.
"""

import io
import tempfile
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

# LangChain imports
try:
    from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PDFPlumberLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Fallback imports
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class LangChainPDFProcessor:
    """Enhanced PDF processor using LangChain document loaders."""
    
    def __init__(self):
        self.text_splitter = None
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
    
    def is_available(self) -> bool:
        """Check if LangChain PDF processing is available."""
        return LANGCHAIN_AVAILABLE
    
    def extract_text_pypdf(self, pdf_content: bytes) -> str:
        """Extract text using PyPDFLoader (LangChain)."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            try:
                # Use LangChain PyPDFLoader
                loader = PyPDFLoader(temp_file_path)
                documents = loader.load()
                
                # Combine all pages
                text_parts = []
                for doc in documents:
                    if doc.page_content.strip():
                        text_parts.append(doc.page_content.strip())
                
                return '\n\n'.join(text_parts)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            raise Exception(f"PyPDFLoader failed: {e}")
    
    def extract_text_pdfplumber(self, pdf_content: bytes) -> str:
        """Extract text using PDFPlumberLoader (better for complex layouts)."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name

            try:
                # Use LangChain PDFPlumberLoader
                loader = PDFPlumberLoader(temp_file_path)
                documents = loader.load()

                # Combine all pages
                text_parts = []
                for doc in documents:
                    if doc.page_content.strip():
                        text_parts.append(doc.page_content.strip())

                return '\n\n'.join(text_parts)

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            raise Exception(f"PDFPlumberLoader failed: {e}")
    
    def extract_text_unstructured(self, pdf_content: bytes) -> str:
        """Extract text using UnstructuredPDFLoader (best for complex documents)."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            try:
                # Use LangChain UnstructuredPDFLoader
                loader = UnstructuredPDFLoader(temp_file_path)
                documents = loader.load()
                
                # Combine all pages
                text_parts = []
                for doc in documents:
                    if doc.page_content.strip():
                        text_parts.append(doc.page_content.strip())
                
                return '\n\n'.join(text_parts)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            raise Exception(f"UnstructuredPDFLoader failed: {e}")
    
    def extract_text_fallback(self, pdf_content: bytes) -> str:
        """Fallback extraction using PyPDF2."""
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 not available for fallback")
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_parts = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text.strip())
            
            return '\n\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"PyPDF2 fallback failed: {e}")
    
    def extract_text(self, pdf_content: bytes, filename: str = "") -> str:
        """
        Extract text from PDF using multiple methods with fallback.
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Extracted text content
        """
        if not pdf_content:
            raise ValueError("PDF content is empty")
        
        errors = []
        
        # Method 1: Try PDFPlumber (best for complex layouts)
        if LANGCHAIN_AVAILABLE and PDFPLUMBER_AVAILABLE:
            try:
                print(f"📄 Trying PDFPlumberLoader for {filename}")
                text = self.extract_text_pdfplumber(pdf_content)
                if text.strip():
                    print(f"✅ PDFPlumberLoader succeeded for {filename}")
                    return text
            except Exception as e:
                error_msg = f"PDFPlumberLoader failed: {e}"
                print(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # Method 2: Try UnstructuredPDFLoader (good for complex documents)
        if LANGCHAIN_AVAILABLE:
            try:
                print(f"📄 Trying UnstructuredPDFLoader for {filename}")
                text = self.extract_text_unstructured(pdf_content)
                if text.strip():
                    print(f"✅ UnstructuredPDFLoader succeeded for {filename}")
                    return text
            except Exception as e:
                error_msg = f"UnstructuredPDFLoader failed: {e}"
                print(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # Method 3: Try PyPDFLoader (LangChain wrapper)
        if LANGCHAIN_AVAILABLE:
            try:
                print(f"📄 Trying PyPDFLoader for {filename}")
                text = self.extract_text_pypdf(pdf_content)
                if text.strip():
                    print(f"✅ PyPDFLoader succeeded for {filename}")
                    return text
            except Exception as e:
                error_msg = f"PyPDFLoader failed: {e}"
                print(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # Method 4: Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                print(f"📄 Trying PyPDF2 fallback for {filename}")
                text = self.extract_text_fallback(pdf_content)
                if text.strip():
                    print(f"✅ PyPDF2 fallback succeeded for {filename}")
                    return text
            except Exception as e:
                error_msg = f"PyPDF2 fallback failed: {e}"
                print(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # All methods failed
        error_summary = f"All PDF extraction methods failed for {filename}:\n" + "\n".join(errors)
        raise Exception(error_summary)
    
    def extract_text_with_chunks(self, pdf_content: bytes, filename: str = "") -> List[Dict[str, Any]]:
        """
        Extract text and split into chunks for better embedding.
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            List of text chunks with metadata
        """
        # Extract full text
        full_text = self.extract_text(pdf_content, filename)
        
        if not self.text_splitter:
            # Return as single chunk if splitter not available
            return [{
                'text': full_text,
                'chunk_index': 0,
                'total_chunks': 1,
                'metadata': {
                    'source': filename,
                    'chunk_type': 'full_document'
                }
            }]
        
        # Split into chunks
        documents = [Document(page_content=full_text, metadata={'source': filename})]
        chunks = self.text_splitter.split_documents(documents)
        
        # Format chunks
        result_chunks = []
        for i, chunk in enumerate(chunks):
            result_chunks.append({
                'text': chunk.page_content,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'metadata': {
                    'source': filename,
                    'chunk_type': 'text_chunk',
                    'chunk_size': len(chunk.page_content)
                }
            })
        
        return result_chunks
    
    def get_available_methods(self) -> List[str]:
        """Get list of available PDF extraction methods."""
        methods = []
        
        if LANGCHAIN_AVAILABLE and PDFPLUMBER_AVAILABLE:
            methods.append("PDFPlumberLoader")
        
        if LANGCHAIN_AVAILABLE:
            methods.append("UnstructuredPDFLoader")
            methods.append("PyPDFLoader")
        
        if PYPDF2_AVAILABLE:
            methods.append("PyPDF2")
        
        return methods


# Global processor instance
_pdf_processor: Optional[LangChainPDFProcessor] = None


def get_langchain_pdf_processor() -> LangChainPDFProcessor:
    """Get or create LangChain PDF processor instance."""
    global _pdf_processor
    
    if _pdf_processor is None:
        _pdf_processor = LangChainPDFProcessor()
    
    return _pdf_processor
