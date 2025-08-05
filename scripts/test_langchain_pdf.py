#!/usr/bin/env python3
"""
Test script for LangChain PDF processing.
Tests the new LangChain PDF processor against existing PDF files.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config
from src.services.langchain_pdf_processor import get_langchain_pdf_processor
from src.services.file_embedding_service import get_file_embedding_service
from src.database.model_s3 import get_s3_manager


def test_langchain_pdf_processor():
    """Test LangChain PDF processor directly."""
    print("🧪 Testing LangChain PDF Processor")
    print("=" * 50)
    
    try:
        pdf_processor = get_langchain_pdf_processor()
        
        print(f"✅ PDF Processor available: {pdf_processor.is_available()}")
        print(f"📋 Available methods: {pdf_processor.get_available_methods()}")
        
        return pdf_processor
        
    except Exception as e:
        print(f"❌ Error initializing PDF processor: {e}")
        return None


def test_pdf_files():
    """Test PDF processing on existing PDF files."""
    print("\n📄 Testing PDF Files")
    print("=" * 30)
    
    try:
        # Get PDF files from database
        db = get_db_config()
        pdf_files = list(db.file_metadata.find({
            "is_active": True,
            "$or": [
                {"content_type": "application/pdf"},
                {"file_name": {"$regex": r"\.pdf$", "$options": "i"}}
            ]
        }))
        
        if not pdf_files:
            print("❌ No PDF files found in database")
            return False
        
        print(f"📊 Found {len(pdf_files)} PDF files")
        
        # Get S3 manager and PDF processor
        s3_manager = get_s3_manager()
        pdf_processor = get_langchain_pdf_processor()
        
        if not pdf_processor.is_available():
            print("❌ LangChain PDF processor not available")
            return False
        
        for pdf_file in pdf_files:
            file_name = pdf_file['file_name']
            file_key = pdf_file['file_key']
            user_id = pdf_file['user_id']
            
            print(f"\n📄 Testing: {file_name} (user: {user_id})")
            
            try:
                # Download file from S3
                download_result = s3_manager.download_file(file_key)
                
                if not download_result.get('success'):
                    print(f"  ❌ Failed to download: {download_result.get('error', 'Unknown error')}")
                    continue
                
                file_content = download_result['file_data']
                print(f"  ✅ Downloaded {len(file_content)} bytes")
                
                # Test regular text extraction
                try:
                    text = pdf_processor.extract_text(file_content, file_name)
                    text_length = len(text.strip())
                    print(f"  ✅ Extracted {text_length} characters")
                    
                    if text_length > 0:
                        # Show first 200 characters
                        preview = text[:200].replace('\n', ' ').strip()
                        print(f"  📝 Preview: {preview}...")
                    else:
                        print(f"  ⚠️  No text extracted")
                        
                except Exception as e:
                    print(f"  ❌ Text extraction failed: {e}")
                    continue
                
                # Test chunked extraction
                try:
                    chunks = pdf_processor.extract_text_with_chunks(file_content, file_name)
                    print(f"  ✅ Extracted {len(chunks)} chunks")
                    
                    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                        chunk_text = chunk['text']
                        chunk_length = len(chunk_text.strip())
                        print(f"    Chunk {i+1}: {chunk_length} characters")
                        
                        if chunk_length > 0:
                            preview = chunk_text[:100].replace('\n', ' ').strip()
                            print(f"      Preview: {preview}...")
                    
                    if len(chunks) > 3:
                        print(f"    ... and {len(chunks) - 3} more chunks")
                        
                except Exception as e:
                    print(f"  ❌ Chunked extraction failed: {e}")
                
            except Exception as e:
                print(f"  ❌ Error processing {file_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PDF files: {e}")
        return False


def test_embedding_with_langchain():
    """Test embedding PDF files using LangChain processor."""
    print("\n🔢 Testing Embedding with LangChain")
    print("=" * 40)
    
    try:
        embedding_service = get_file_embedding_service()
        
        if not embedding_service.is_available():
            print("❌ Embedding service not available")
            return False
        
        # Get a PDF file to test
        db = get_db_config()
        pdf_file = db.file_metadata.find_one({
            "is_active": True,
            "$or": [
                {"content_type": "application/pdf"},
                {"file_name": {"$regex": r"\.pdf$", "$options": "i"}}
            ]
        })
        
        if not pdf_file:
            print("❌ No PDF file found for testing")
            return False
        
        file_name = pdf_file['file_name']
        file_key = pdf_file['file_key']
        user_id = pdf_file['user_id']
        
        print(f"📄 Testing embedding: {file_name}")
        
        # Download file
        s3_manager = get_s3_manager()
        download_result = s3_manager.download_file(file_key)
        
        if not download_result.get('success'):
            print(f"❌ Failed to download file: {download_result.get('error')}")
            return False
        
        file_content = download_result['file_data']
        
        # Test chunked embedding
        try:
            print("🔢 Testing chunked embedding...")
            embedding_ids = embedding_service.embed_file_chunked(
                user_id=f"test_{user_id}",  # Use test prefix to avoid conflicts
                filename=f"test_{file_name}",
                file_content=file_content,
                content_type="application/pdf",
                file_key=f"test_{file_key}",
                metadata={"test": True}
            )
            
            if embedding_ids:
                print(f"✅ Successfully embedded {len(embedding_ids)} chunks")
                print(f"📋 Embedding IDs: {embedding_ids[:3]}{'...' if len(embedding_ids) > 3 else ''}")
                
                # Test search
                print("\n🔍 Testing search...")
                from src.database.model_qdrant import get_qdrant_config
                qdrant = get_qdrant_config()
                
                # Search for content
                query_embedding = embedding_service.embedding_provider.encode("document")

                search_results = qdrant.search_similar(
                    query_vector=query_embedding,
                    limit=3,
                    filter_conditions={"user_id": f"test_{user_id}"}
                )
                
                print(f"✅ Found {len(search_results)} search results")
                for i, result in enumerate(search_results):
                    score = result.get('score', 0)
                    payload = result.get('payload', {})
                    title = payload.get('title', 'Unknown')
                    print(f"  {i+1}. {title} (score: {score:.3f})")
                
            else:
                print("❌ Failed to embed chunks")
                return False
                
        except Exception as e:
            print(f"❌ Chunked embedding failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing embedding: {e}")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing LangChain Dependencies")
    print("=" * 40)
    
    import subprocess
    
    dependencies = [
        "langchain-community>=0.3.0",
        "pypdf>=4.0.0",
        "pdfplumber>=0.11.0",
        "unstructured>=0.15.0"
    ]
    
    for dep in dependencies:
        try:
            print(f"📦 Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LangChain PDF processing")
    parser.add_argument("--install", action="store_true", help="Install required dependencies")
    parser.add_argument("--test-embedding", action="store_true", help="Test embedding functionality")
    
    args = parser.parse_args()
    
    print("LangChain PDF Processing Test")
    print("=" * 50)
    
    if args.install:
        if not install_dependencies():
            print("\n❌ Failed to install dependencies")
            sys.exit(1)
        print("\n✅ Dependencies installed successfully")
    
    # Test PDF processor
    pdf_processor = test_langchain_pdf_processor()
    if not pdf_processor:
        print("\n❌ PDF processor test failed")
        sys.exit(1)
    
    # Test PDF files
    if not test_pdf_files():
        print("\n❌ PDF files test failed")
        sys.exit(1)
    
    # Test embedding if requested
    if args.test_embedding:
        if not test_embedding_with_langchain():
            print("\n❌ Embedding test failed")
            sys.exit(1)
    
    print("\n✅ All tests completed successfully!")
    print("\n💡 Usage Tips:")
    print("1. Use chunked embedding for large PDF files")
    print("2. LangChain provides better text extraction than PyPDF2")
    print("3. Multiple extraction methods provide fallback options")
    print("4. Chunked embedding improves search accuracy")


if __name__ == "__main__":
    main()
