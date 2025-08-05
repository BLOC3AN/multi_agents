"""
File Embedding Service for automatic text extraction and vector embedding.
Integrates with Qdrant for semantic search capabilities.
"""
import os
import io
import hashlib
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import numpy as np
from dotenv import load_dotenv

# Text extraction imports
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# LangChain PDF processor
try:
    from .langchain_pdf_processor import get_langchain_pdf_processor
    LANGCHAIN_PDF_AVAILABLE = True
except ImportError:
    LANGCHAIN_PDF_AVAILABLE = False

# Embedding imports
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Load environment variables
load_dotenv()

# Import Qdrant model
from ..database.model_qdrant import (
    get_qdrant_config,
    create_vector_document,
    VectorDocument
)


class TextExtractor:
    """Extract text from various file formats."""
    
    @staticmethod
    def extract_from_text(content: bytes) -> str:
        """Extract text from plain text files."""
        try:
            # Try UTF-8 first
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                return content.decode('latin-1')
            except UnicodeDecodeError:
                # Last resort: ignore errors
                return content.decode('utf-8', errors='ignore')
    
    @staticmethod
    def extract_from_docx(content: bytes) -> str:
        """Extract text from DOCX files."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available. Install with: pip install python-docx")
        
        try:
            doc = Document(io.BytesIO(content))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {e}")
    
    @staticmethod
    def extract_from_pdf(content: bytes, filename: str = "") -> str:
        """Extract text from PDF files using LangChain or fallback methods."""
        # Try LangChain PDF processor first (better quality)
        if LANGCHAIN_PDF_AVAILABLE:
            try:
                pdf_processor = get_langchain_pdf_processor()
                if pdf_processor.is_available():
                    print(f"📄 Using LangChain PDF processor for {filename}")
                    return pdf_processor.extract_text(content, filename)
            except Exception as e:
                print(f"⚠️ LangChain PDF processor failed: {e}")

        # Fallback to PyPDF2
        if not PDF_AVAILABLE:
            raise ImportError("PDF processing not available. Install with: pip install PyPDF2 langchain-community")

        try:
            print(f"📄 Using PyPDF2 fallback for {filename}")
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text.strip())

            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    @staticmethod
    def extract_from_markdown(content: bytes) -> str:
        """Extract text from Markdown files."""
        try:
            text = content.decode('utf-8')
            # Simple markdown processing - remove headers, links, etc.
            lines = text.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Remove markdown headers
                    if line.startswith('#'):
                        line = line.lstrip('#').strip()
                    # Remove markdown links [text](url) -> text
                    import re
                    line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
                    # Remove bold/italic markers
                    line = re.sub(r'\*\*([^\*]+)\*\*', r'\1', line)
                    line = re.sub(r'\*([^\*]+)\*', r'\1', line)
                    
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines)
        except Exception as e:
            raise Exception(f"Failed to extract text from Markdown: {e}")
    
    @classmethod
    def extract_text(cls, content: bytes, content_type: str, filename: str = "") -> str:
        """
        Extract text from file content based on content type.
        
        Args:
            content: File content as bytes
            content_type: MIME content type
            filename: Original filename for extension detection
            
        Returns:
            Extracted text content
        """
        # Determine file type
        filename_lower = filename.lower()
        
        if content_type.startswith('text/') or filename_lower.endswith(('.txt', '.log')):
            return cls.extract_from_text(content)
        
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or filename_lower.endswith('.docx'):
            return cls.extract_from_docx(content)
        
        elif content_type == 'application/pdf' or filename_lower.endswith('.pdf'):
            return cls.extract_from_pdf(content, filename)
        
        elif content_type == 'text/markdown' or filename_lower.endswith(('.md', '.markdown')):
            return cls.extract_from_markdown(content)
        
        elif filename_lower.endswith(('.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml')):
            return cls.extract_from_text(content)
        
        else:
            # Try as text file as fallback
            try:
                return cls.extract_from_text(content)
            except:
                raise Exception(f"Unsupported file type: {content_type} ({filename})")


class EmbeddingProvider:
    """Embedding provider using available models."""
    
    def __init__(self):
        self.model = None
        self.provider = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the best available embedding model."""
        
        # Try Sentence Transformers first (local, fast)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
                self.provider = "sentence_transformers"
                print("✅ Using Sentence Transformers for embeddings")
                return
            except Exception as e:
                print(f"⚠️ Failed to load Sentence Transformers: {e}")
        
        # Fallback to mock embeddings for development
        print("⚠️ Using mock embeddings (install sentence-transformers for real embeddings)")
        self.provider = "mock"
    
    def encode(self, text: str) -> List[float]:
        """
        Encode text to vector embedding.
        
        Args:
            text: Text to encode
            
        Returns:
            Vector embedding (1024 dimensions)
        """
        if self.provider == "sentence_transformers":
            # Get embedding from Sentence Transformers (384 dim)
            embedding = self.model.encode(text).tolist()
            
            # Pad or truncate to 1024 dimensions
            if len(embedding) < 1024:
                # Pad with zeros
                embedding.extend([0.0] * (1024 - len(embedding)))
            elif len(embedding) > 1024:
                # Truncate
                embedding = embedding[:1024]
            
            return embedding
        
        else:
            # Mock embedding based on text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()
            np.random.seed(int(text_hash[:8], 16))
            return np.random.rand(1024).tolist()


class FileEmbeddingService:
    """Service for automatic file embedding and management."""
    
    def __init__(self):
        self.text_extractor = TextExtractor()
        self.embedding_provider = EmbeddingProvider()
        self.qdrant = None
        
        try:
            self.qdrant = get_qdrant_config()
            print("✅ File embedding service initialized with Qdrant")
        except Exception as e:
            print(f"⚠️ Qdrant not available for file embedding: {e}")
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        return self.qdrant is not None
    
    def should_embed_file(self, content_type: str, filename: str) -> bool:
        """
        Check if a file type should be embedded.
        
        Args:
            content_type: MIME content type
            filename: Original filename
            
        Returns:
            True if file should be embedded
        """
        embeddable_types = [
            'text/',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/markdown'
        ]
        
        embeddable_extensions = [
            '.txt', '.md', '.markdown', '.py', '.js', '.html', '.css', 
            '.json', '.xml', '.yaml', '.yml', '.log', '.docx', '.pdf'
        ]
        
        # Check content type
        for embeddable_type in embeddable_types:
            if content_type.startswith(embeddable_type):
                return True
        
        # Check file extension
        filename_lower = filename.lower()
        for ext in embeddable_extensions:
            if filename_lower.endswith(ext):
                return True
        
        return False
    
    def check_file_embedded(self, user_id: str, filename: str, file_key: str = None) -> bool:
        """
        Check if a file has already been embedded.
        
        Args:
            user_id: User ID
            filename: File name
            file_key: Optional file key for more specific matching
            
        Returns:
            True if file is already embedded
        """
        if not self.is_available():
            return False
        
        existing_doc = self.qdrant.check_file_exists(user_id, filename, file_key)
        return existing_doc is not None
    
    def embed_file_chunked(self, user_id: str, filename: str, file_content: bytes,
                          content_type: str, file_key: str = None,
                          metadata: Dict[str, Any] = None) -> List[str]:
        """
        Extract text and embed a PDF file in chunks for better processing.

        Args:
            user_id: User ID
            filename: File name
            file_content: File content as bytes
            content_type: MIME content type
            file_key: Optional file key
            metadata: Additional metadata

        Returns:
            List of document IDs if successful, empty list otherwise
        """
        if not self.is_available():
            print("❌ File embedding service not available")
            return []

        # Only use chunked embedding for PDFs
        if not (content_type == 'application/pdf' or filename.lower().endswith('.pdf')):
            # Use regular embedding for non-PDF files
            doc_id = self.embed_file(user_id, filename, file_content, content_type, file_key, metadata)
            return [doc_id] if doc_id else []

        if not LANGCHAIN_PDF_AVAILABLE:
            print("⚠️ LangChain PDF processor not available, using regular embedding")
            doc_id = self.embed_file(user_id, filename, file_content, content_type, file_key, metadata)
            return [doc_id] if doc_id else []

        # Check if already embedded
        if self.check_file_embedded(user_id, filename, file_key):
            print(f"⏭️ File {filename} already embedded for user {user_id}")
            return []

        try:
            # Extract text in chunks using LangChain
            pdf_processor = get_langchain_pdf_processor()
            chunks = pdf_processor.extract_text_with_chunks(file_content, filename)

            if not chunks:
                print(f"⚠️ No text chunks extracted from {filename}")
                return []

            print(f"📄 Extracted {len(chunks)} chunks from {filename}")

            doc_ids = []
            doc_metadata = metadata.copy() if metadata else {}
            doc_category = doc_metadata.pop('category', 'file')

            # Embed each chunk
            for chunk_info in chunks:
                chunk_text = chunk_info['text']
                chunk_index = chunk_info['chunk_index']
                total_chunks = chunk_info['total_chunks']

                if not chunk_text.strip():
                    continue

                # Create embedding for chunk
                print(f"🔢 Creating embedding for chunk {chunk_index + 1}/{total_chunks}")
                embedding = self.embedding_provider.encode(chunk_text)

                # Create unique title for chunk
                chunk_title = f"{filename} (Part {chunk_index + 1}/{total_chunks})"
                chunk_source = f"{file_key or filename}#chunk_{chunk_index}"

                # Add chunk metadata
                chunk_metadata = doc_metadata.copy()
                chunk_metadata.update({
                    'chunk_index': chunk_index,
                    'total_chunks': total_chunks,
                    'is_chunk': True,
                    'parent_file': filename
                })

                # Create vector document for chunk
                doc = create_vector_document(
                    text=chunk_text,
                    user_id=user_id,
                    title=chunk_title,
                    source=chunk_source,
                    file_name=filename,  # Original file name without prefixes/suffixes
                    category=doc_category,
                    language="vi",
                    summary=chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                    **chunk_metadata
                )

                # Store in Qdrant
                success = self.qdrant.upsert_document(doc, embedding)
                doc_id = doc.id if success else None
                if doc_id:
                    doc_ids.append(doc_id)
                    print(f"✅ Chunk {chunk_index + 1} embedded with ID: {doc_id}")
                else:
                    print(f"❌ Failed to embed chunk {chunk_index + 1}")

            if doc_ids:
                print(f"✅ Successfully embedded {len(doc_ids)} chunks from {filename}")
            else:
                print(f"❌ Failed to embed any chunks from {filename}")

            return doc_ids

        except Exception as e:
            print(f"❌ Error embedding file {filename}: {e}")
            return []

    def embed_file(self, user_id: str, filename: str, file_content: bytes,
                   content_type: str, file_key: str = None,
                   metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Extract text and embed a file.
        
        Args:
            user_id: User ID
            filename: File name
            file_content: File content as bytes
            content_type: MIME content type
            file_key: Optional file key
            metadata: Additional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_available():
            print("❌ File embedding service not available")
            return None
        
        if not self.should_embed_file(content_type, filename):
            print(f"⏭️ Skipping embedding for {filename} (unsupported type: {content_type})")
            return None
        
        # Check if already embedded
        if self.check_file_embedded(user_id, filename, file_key):
            print(f"⏭️ File {filename} already embedded for user {user_id}")
            return None
        
        try:
            # Extract text
            print(f"📄 Extracting text from {filename}")
            text = self.text_extractor.extract_text(file_content, content_type, filename)
            
            if not text.strip():
                print(f"⚠️ No text extracted from {filename}")
                return None
            
            # Create embedding
            print(f"🔢 Creating embedding for {filename}")
            embedding = self.embedding_provider.encode(text)
            
            # Create vector document
            # Extract category from metadata if exists, otherwise use default
            doc_metadata = metadata.copy() if metadata else {}
            doc_category = doc_metadata.pop('category', 'file')

            doc = create_vector_document(
                text=text,
                user_id=user_id,
                title=filename,
                source=file_key or filename,
                file_name=filename,  # Original file name without prefixes/suffixes
                category=doc_category,
                language="vi",
                summary=text[:200] + "..." if len(text) > 200 else text,
                **doc_metadata
            )
            
            # Store in Qdrant
            success = self.qdrant.upsert_document(doc, embedding)
            
            if success:
                print(f"✅ File {filename} embedded successfully for user {user_id}")
                return doc.id
            else:
                print(f"❌ Failed to store embedding for {filename}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to embed file {filename}: {e}")
            return None
    
    def delete_file_embedding(self, user_id: str, filename: str, file_key: str = None) -> bool:
        """
        Delete file embedding from Qdrant.
        
        Args:
            user_id: User ID
            filename: File name
            file_key: Optional file key
            
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            success = self.qdrant.delete_user_file_vectors(user_id, filename, file_key)
            if success:
                print(f"✅ Deleted embedding for {filename} (user: {user_id})")
            return success
        except Exception as e:
            print(f"❌ Failed to delete embedding for {filename}: {e}")
            return False


# Global service instance
_file_embedding_service: Optional[FileEmbeddingService] = None


def get_file_embedding_service() -> FileEmbeddingService:
    """Get or create file embedding service instance."""
    global _file_embedding_service
    
    if _file_embedding_service is None:
        _file_embedding_service = FileEmbeddingService()
    
    return _file_embedding_service
