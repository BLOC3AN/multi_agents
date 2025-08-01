#!/usr/bin/env python3
"""
Test script to create a message with inline code for testing
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config.database import DatabaseConfig
import uuid
from datetime import datetime, timedelta

def create_inline_code_test():
    """Create a test message with inline code"""
    
    # Initialize database
    db_config = DatabaseConfig()
    
    # Test session
    test_session = {
        "session_id": "session_inline_code_test_001",
        "user_id": "admin",
        "session_name": "🧪 Inline Code Test",
        "title": "Inline Code Test Session",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Test message with inline code
    test_message = {
        "message_id": str(uuid.uuid4()),
        "session_id": "session_inline_code_test_001",
        "user_id": "admin",
        "user_input": "Test inline code rendering",
        "agent_response": """# Test Inline Code Rendering

Để tính tổng `a + b` trong Python, bạn có thể sử dụng đoạn code sau:

```python
def add_numbers(a, b):
    return a + b

result = add_numbers(5, 3)
print(f"Kết quả: {result}")
```

Một số ví dụ khác với inline code:

- Sử dụng hàm `print()` để in ra màn hình
- Biến `result` chứa kết quả tính toán
- Phương thức `len()` trả về độ dài của chuỗi
- Import module với `import numpy as np`
- Tạo list với `my_list = [1, 2, 3]`

## Các toán tử cơ bản

- Phép cộng: `a + b`
- Phép trừ: `a - b` 
- Phép nhân: `a * b`
- Phép chia: `a / b`
- Phép chia lấy phần nguyên: `a // b`
- Phép chia lấy dư: `a % b`
- Lũy thừa: `a ** b`

Trong JavaScript, bạn có thể sử dụng `console.log()` thay vì `print()`.

**Lưu ý**: Inline code như `variable_name` nên được viết rõ ràng và dễ hiểu.""",
        "created_at": datetime.utcnow().isoformat(),
        "processing_time": 1500,
        "primary_intent": "inline_code_test",
        "processing_mode": "single_agent",
        "success": True
    }
    
    try:
        # Create session if not exists
        existing_session = db_config.sessions.find_one({"session_id": test_session["session_id"]})
        if not existing_session:
            db_config.sessions.insert_one(test_session)
            print(f"✅ Created session: {test_session['title']}")
        else:
            print(f"🔄 Session already exists: {test_session['title']}")
        
        # Create message
        existing_message = db_config.messages.find_one({"message_id": test_message["message_id"]})
        if not existing_message:
            db_config.messages.insert_one(test_message)
            print(f"✅ Created test message with inline code")
        
        print("\n" + "="*50)
        print("🧪 Inline Code Test Message Created!")
        print("\n📋 Test Content:")
        print("-" * 30)
        print("  📝 Inline code examples: `a + b`, `print()`, etc.")
        print("  💻 Mixed with code blocks")
        print("  📊 Lists with inline code")
        
        print("\n🌐 Test at: http://localhost:3003")
        print("🔑 Login: admin / admin123")
        print("📖 Look for '🧪 Inline Code Test' session")
        
        print("\n✅ Test message created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating test message: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_inline_code_test()
