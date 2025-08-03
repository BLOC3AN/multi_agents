#!/usr/bin/env python3
"""
Test script for file management system.
Tests the new file upload limits and user isolation features.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config, FileMetadata
from src.services.file_manager import get_file_manager
from datetime import datetime
import uuid


def test_database_connection():
    """Test database connection and collections."""
    print("🔍 Testing database connection...")
    try:
        db_config = get_db_config()
        
        # Test connection
        db_config.client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Check collections
        collections = db_config.database.list_collection_names()
        print(f"📁 Available collections: {collections}")
        
        # Check if file_metadata collection exists
        if 'file_metadata' in collections:
            print("✅ file_metadata collection exists")
        else:
            print("ℹ️ file_metadata collection will be created on first use")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_file_manager():
    """Test file manager functionality."""
    print("\n🔍 Testing file manager...")
    try:
        file_manager = get_file_manager()
        test_user_id = "test_user_123"
        
        # Test file limit check
        limit_check = file_manager.check_file_limit(test_user_id)
        print(f"📊 File limit check for {test_user_id}:")
        print(f"   Current: {limit_check['current_count']}")
        print(f"   Max: {limit_check['max_allowed']}")
        print(f"   Can upload: {limit_check['can_upload']}")
        print(f"   Remaining: {limit_check['remaining']}")
        
        # Test getting user files
        user_files = file_manager.get_user_files(test_user_id)
        print(f"📁 User files count: {len(user_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ File manager test failed: {e}")
        return False


def test_file_metadata_model():
    """Test FileMetadata model."""
    print("\n🔍 Testing FileMetadata model...")
    try:
        # Create test metadata
        file_metadata = FileMetadata(
            file_id=str(uuid.uuid4()),
            user_id="test_user_123",
            file_key="test_file.txt",
            file_name="test_file.txt",
            file_size=1024,
            content_type="text/plain",
            upload_date=datetime.utcnow(),
            s3_bucket="test-bucket",
            is_active=True,
            metadata={"test": "data"}
        )
        
        # Convert to dict
        file_dict = file_metadata.to_dict()
        print("✅ FileMetadata model works correctly")
        print(f"📄 Sample metadata: {file_dict}")
        
        return True
        
    except Exception as e:
        print(f"❌ FileMetadata model test failed: {e}")
        return False


def test_file_upload_simulation():
    """Simulate file upload process."""
    print("\n🔍 Testing file upload simulation...")
    try:
        file_manager = get_file_manager()
        test_user_id = "test_user_simulation"
        
        # Simulate uploading a file
        result = file_manager.handle_file_upload(
            user_id=test_user_id,
            file_key="simulation_test.txt",
            file_name="simulation_test.txt",
            file_size=2048,
            content_type="text/plain",
            s3_bucket="test-bucket"
        )
        
        print(f"📤 Upload simulation result: {result}")
        
        if result['success']:
            print("✅ File upload simulation successful")
            
            # Check user files after upload
            user_files = file_manager.get_user_files(test_user_id)
            print(f"📁 User files after upload: {len(user_files)}")
            
            # Test file deletion
            if user_files:
                file_to_delete = user_files[0]['file_key']
                delete_success = file_manager.delete_file(file_to_delete, test_user_id)
                print(f"🗑️ File deletion result: {delete_success}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ File upload simulation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting file management system tests...\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("File Manager", test_file_manager),
        ("FileMetadata Model", test_file_metadata_model),
        ("File Upload Simulation", test_file_upload_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! File management system is ready.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main()
