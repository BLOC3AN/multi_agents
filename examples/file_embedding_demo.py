"""
Demo script for File Embedding Integration.
Shows complete workflow from file upload to search.
"""
import sys
import os
import requests
import json
import time

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.file_manager import get_file_manager
from src.services.file_embedding_service import get_file_embedding_service
from src.database.model_qdrant import get_qdrant_config


def test_file_embedding_workflow():
    """Test complete file embedding workflow."""
    print("🚀 Testing File Embedding Integration Workflow")
    print("=" * 60)
    
    # Test data
    user_id = "demo_user_integration"
    test_files = [
        {
            "filename": "python_guide.txt",
            "content": """
Python Programming Guide

Python is a high-level, interpreted programming language with dynamic semantics.
Its high-level built-in data structures, combined with dynamic typing and dynamic binding,
make it very attractive for Rapid Application Development, as well as for use as a
scripting or glue language to connect existing components together.

Key Features:
- Easy to learn and use
- Powerful standard library
- Cross-platform compatibility
- Large community support
- Extensive third-party packages

Python is widely used in:
- Web development (Django, Flask)
- Data science and analytics
- Machine learning and AI
- Automation and scripting
- Scientific computing
            """.strip(),
            "content_type": "text/plain"
        },
        {
            "filename": "machine_learning.md",
            "content": """
# Machine Learning Overview

Machine Learning (ML) is a subset of artificial intelligence (AI) that provides systems 
the ability to automatically learn and improve from experience without being explicitly programmed.

## Types of Machine Learning

### 1. Supervised Learning
- Uses labeled training data
- Examples: Classification, Regression
- Algorithms: Linear Regression, Decision Trees, SVM

### 2. Unsupervised Learning
- Finds patterns in data without labels
- Examples: Clustering, Association Rules
- Algorithms: K-Means, Hierarchical Clustering

### 3. Reinforcement Learning
- Learns through interaction with environment
- Uses rewards and penalties
- Applications: Game playing, Robotics

## Popular ML Libraries
- **Scikit-learn**: General-purpose ML library
- **TensorFlow**: Deep learning framework
- **PyTorch**: Research-focused deep learning
- **Pandas**: Data manipulation and analysis
            """.strip(),
            "content_type": "text/markdown"
        },
        {
            "filename": "data_analysis.py",
            "content": """
# Data Analysis with Python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_explore_data(file_path):
    \"\"\"
    Load dataset and perform basic exploration.
    
    Args:
        file_path (str): Path to the data file
        
    Returns:
        pd.DataFrame: Loaded dataset
    \"\"\"
    # Load data
    df = pd.read_csv(file_path)
    
    # Basic info
    print("Dataset Shape:", df.shape)
    print("\\nColumn Info:")
    print(df.info())
    
    # Statistical summary
    print("\\nStatistical Summary:")
    print(df.describe())
    
    # Check for missing values
    print("\\nMissing Values:")
    print(df.isnull().sum())
    
    return df

def visualize_data(df, target_column):
    \"\"\"
    Create basic visualizations for the dataset.
    
    Args:
        df (pd.DataFrame): Dataset to visualize
        target_column (str): Target variable column name
    \"\"\"
    # Distribution of target variable
    plt.figure(figsize=(10, 6))
    
    plt.subplot(1, 2, 1)
    df[target_column].hist(bins=30)
    plt.title(f'Distribution of {target_column}')
    
    plt.subplot(1, 2, 2)
    df.boxplot(column=target_column)
    plt.title(f'Box Plot of {target_column}')
    
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Load and explore data
    data = load_and_explore_data("sample_data.csv")
    
    # Visualize target variable
    visualize_data(data, "target")
            """.strip(),
            "content_type": "text/x-python"
        }
    ]
    
    # Initialize services
    print("\n1️⃣ Initializing Services")
    file_manager = get_file_manager()
    embedding_service = get_file_embedding_service()
    
    if not embedding_service.is_available():
        print("❌ Embedding service not available")
        return
    
    print("✅ Services initialized")
    
    # Clean up any existing files first
    print("\n2️⃣ Cleaning up existing test files")
    for file_data in test_files:
        embedding_service.delete_file_embedding(user_id, file_data["filename"])
    
    # Upload and embed files
    print("\n3️⃣ Uploading and Embedding Files")
    uploaded_files = []
    
    for file_data in test_files:
        print(f"\n📄 Processing: {file_data['filename']}")
        
        # Simulate file upload through FileManager
        file_content = file_data["content"].encode('utf-8')
        
        upload_result = file_manager.handle_file_upload(
            user_id=user_id,
            file_key=file_data["filename"],
            file_name=file_data["filename"],
            file_size=len(file_content),
            content_type=file_data["content_type"],
            file_content=file_content
        )
        
        if upload_result["success"]:
            print(f"✅ Uploaded: {file_data['filename']}")
            if upload_result.get("embedding_id"):
                print(f"✅ Embedded: {upload_result['embedding_id']}")
            uploaded_files.append(file_data["filename"])
        else:
            print(f"❌ Failed to upload: {upload_result.get('error')}")
    
    print(f"\n📚 Successfully processed {len(uploaded_files)} files")
    
    # Test search functionality
    print("\n4️⃣ Testing Search Functionality")
    
    search_queries = [
        "Python programming language",
        "machine learning algorithms",
        "data analysis visualization",
        "supervised learning classification",
        "pandas numpy matplotlib"
    ]
    
    qdrant = get_qdrant_config()
    
    for query in search_queries:
        print(f"\n🔍 Searching: '{query}'")
        
        # Generate query embedding
        query_embedding = embedding_service.embedding_provider.encode(query)
        
        # Search in Qdrant
        search_results = qdrant.search_similar(
            query_vector=query_embedding,
            limit=3,
            score_threshold=0.3,
            filter_conditions={
                "must": [
                    {
                        "key": "user_id",
                        "match": {"value": user_id}
                    }
                ]
            }
        )
        
        if search_results:
            for i, result in enumerate(search_results, 1):
                doc = result['document']
                score = result['score']
                print(f"   {i}. {doc.title} (score: {score:.3f})")
                print(f"      Preview: {doc.text[:100]}...")
        else:
            print("   No results found")
    
    # Test file existence checking
    print("\n5️⃣ Testing File Existence Checking")
    
    for filename in uploaded_files:
        exists = embedding_service.check_file_embedded(user_id, filename)
        print(f"   {filename}: {'✅ Embedded' if exists else '❌ Not embedded'}")
    
    # Test user files listing
    print("\n6️⃣ Testing User Files Listing")
    
    user_files = qdrant.get_user_files(user_id)
    print(f"   Found {len(user_files)} files for user {user_id}")
    
    for doc in user_files:
        print(f"   - {doc.title} ({doc.metadata.get('category', 'unknown')})")
    
    # Test duplicate upload prevention
    print("\n7️⃣ Testing Duplicate Upload Prevention")
    
    # Try to embed the same file again
    test_file = test_files[0]
    file_content = test_file["content"].encode('utf-8')
    
    print(f"📄 Attempting to re-embed: {test_file['filename']}")
    
    doc_id = embedding_service.embed_file(
        user_id=user_id,
        filename=test_file["filename"],
        file_content=file_content,
        content_type=test_file["content_type"]
    )
    
    if doc_id is None:
        print("✅ Duplicate upload correctly prevented")
    else:
        print("⚠️ Duplicate upload was not prevented")
    
    # Clean up
    print("\n8️⃣ Cleaning Up")
    
    for filename in uploaded_files:
        success = embedding_service.delete_file_embedding(user_id, filename)
        if success:
            print(f"✅ Deleted: {filename}")
        else:
            print(f"❌ Failed to delete: {filename}")
    
    print("\n🎉 File Embedding Integration Test Completed!")
    print("=" * 60)


def test_api_endpoints():
    """Test API endpoints for file search."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 40)
    
    # Note: This requires the server to be running
    base_url = "http://localhost:8000"
    
    # Test search endpoint
    search_data = {
        "user_id": "demo_user_integration",
        "query": "Python programming",
        "limit": 5
    }
    
    try:
        response = requests.post(f"{base_url}/api/s3/search", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search API: Found {result.get('total_results', 0)} results")
            print(f"   Search type: {result.get('search_type', 'unknown')}")
        else:
            print(f"❌ Search API failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Search API test skipped: {e}")
        print("💡 Make sure the server is running: python auth_server.py")


if __name__ == "__main__":
    # Run the complete workflow test
    test_file_embedding_workflow()
    
    # Test API endpoints (optional)
    test_api_endpoints()
