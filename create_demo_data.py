#!/usr/bin/env python3
"""
Script to create demo sessions and messages for testing
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config

def create_demo_data():
    """Create demo sessions and messages for testing."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Demo sessions data
        demo_sessions = [
            {
                "session_id": "session_demo_math_001",
                "user_id": "admin",
                "title": "Math Problem Solving",
                "total_messages": 3,
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "is_active": True
            },
            {
                "session_id": "session_demo_writing_002", 
                "user_id": "admin",
                "title": "Creative Writing Help",
                "total_messages": 2,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "is_active": True
            },
            {
                "session_id": "session_demo_code_003",
                "user_id": "admin", 
                "title": "Python Coding Assistance",
                "total_messages": 4,
                "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "is_active": True
            }
        ]
        
        # Demo messages data
        demo_messages = [
            # Math session messages
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_demo_math_001",
                "user_id": "admin",
                "user_input": "Can you help me solve this quadratic equation: x² + 5x + 6 = 0?",
                "agent_response": "I'll help you solve the quadratic equation x² + 5x + 6 = 0.\n\nUsing the factoring method:\nWe need to find two numbers that multiply to 6 and add to 5.\nThose numbers are 2 and 3.\n\nSo: x² + 5x + 6 = (x + 2)(x + 3) = 0\n\nTherefore: x = -2 or x = -3\n\nThe solutions are x = -2 and x = -3.",
                "created_at": (datetime.utcnow() - timedelta(days=2, hours=1)).isoformat(),
                "processing_time": 1250,
                "primary_intent": "math_solving",
                "processing_mode": "single_agent",
                "success": True
            },
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_demo_math_001",
                "user_id": "admin",
                "user_input": "Great! Can you also show me the quadratic formula method?",
                "agent_response": "Absolutely! Let me show you the quadratic formula method for x² + 5x + 6 = 0.\n\nThe quadratic formula is: x = (-b ± √(b² - 4ac)) / 2a\n\nFor our equation x² + 5x + 6 = 0:\n- a = 1\n- b = 5  \n- c = 6\n\nSubstituting:\nx = (-5 ± √(5² - 4(1)(6))) / 2(1)\nx = (-5 ± √(25 - 24)) / 2\nx = (-5 ± √1) / 2\nx = (-5 ± 1) / 2\n\nSo: x = (-5 + 1)/2 = -4/2 = -2\nOr: x = (-5 - 1)/2 = -6/2 = -3\n\nSame solutions: x = -2 and x = -3! ✓",
                "created_at": (datetime.utcnow() - timedelta(days=2, minutes=30)).isoformat(),
                "processing_time": 1800,
                "primary_intent": "math_solving",
                "processing_mode": "single_agent",
                "success": True
            },
            
            # Writing session messages
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_demo_writing_002",
                "user_id": "admin",
                "user_input": "I need help writing a short story about a robot discovering emotions. Can you give me some ideas?",
                "agent_response": "What a fascinating concept! Here are some creative ideas for your robot-emotions story:\n\n**Plot Ideas:**\n1. **The Glitch**: A maintenance robot experiences a programming error that accidentally gives it emotional responses\n2. **The Mirror**: A companion robot starts mimicking human emotions so well it begins to actually feel them\n3. **The Memory**: An old robot finds archived human memories in its databank and experiences emotions through them\n\n**Key Emotional Moments:**\n- First experience of loneliness when left alone\n- Joy from helping someone and seeing their smile\n- Sadness when witnessing loss or saying goodbye\n- Fear when facing potential shutdown/deletion\n- Love when forming a deep connection with a human\n\n**Themes to explore:**\n- What makes emotions 'real'?\n- The beauty and burden of feeling\n- Connection between consciousness and emotion\n\nWould you like me to help develop any of these ideas further?",
                "created_at": (datetime.utcnow() - timedelta(days=1, hours=2)).isoformat(),
                "processing_time": 2100,
                "primary_intent": "creative_writing",
                "processing_mode": "multi_agent",
                "success": True
            },
            
            # Code session messages  
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_demo_code_003",
                "user_id": "admin",
                "user_input": "How do I create a simple REST API with FastAPI?",
                "agent_response": "I'll show you how to create a simple REST API with FastAPI! Here's a basic example:\n\n```python\nfrom fastapi import FastAPI\nfrom pydantic import BaseModel\nfrom typing import List, Optional\n\n# Create FastAPI instance\napp = FastAPI(title=\"My API\", version=\"1.0.0\")\n\n# Data model\nclass Item(BaseModel):\n    id: Optional[int] = None\n    name: str\n    description: Optional[str] = None\n    price: float\n\n# In-memory storage (use database in production)\nitems = []\n\n# Routes\n@app.get(\"/\")\ndef read_root():\n    return {\"message\": \"Welcome to my API!\"}\n\n@app.get(\"/items\", response_model=List[Item])\ndef get_items():\n    return items\n\n@app.post(\"/items\", response_model=Item)\ndef create_item(item: Item):\n    item.id = len(items) + 1\n    items.append(item)\n    return item\n\n@app.get(\"/items/{item_id}\", response_model=Item)\ndef get_item(item_id: int):\n    for item in items:\n        if item.id == item_id:\n            return item\n    return {\"error\": \"Item not found\"}\n```\n\nTo run: `uvicorn main:app --reload`\nDocs available at: http://localhost:8000/docs",
                "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "processing_time": 1950,
                "primary_intent": "code_generation",
                "processing_mode": "single_agent",
                "success": True
            }
        ]
        
        # Create sessions
        created_sessions = 0
        for session_data in demo_sessions:
            existing_session = db_config.sessions.find_one({"session_id": session_data["session_id"]})
            if not existing_session:
                db_config.sessions.insert_one(session_data)
                created_sessions += 1
                print(f"✅ Created session: {session_data['title']}")
        
        # Create messages
        created_messages = 0
        for message_data in demo_messages:
            existing_message = db_config.messages.find_one({"message_id": message_data["message_id"]})
            if not existing_message:
                db_config.messages.insert_one(message_data)
                created_messages += 1
                print(f"✅ Created message in session: {message_data['session_id']}")
        
        print("\n" + "="*50)
        print(f"🎉 Created {created_sessions} sessions and {created_messages} messages")
        print("\n📋 Demo Data Summary:")
        print("-" * 30)
        for session in demo_sessions:
            print(f"  📝 {session['title']} ({session['total_messages']} messages)")
        
        print("\n🌐 Test at: http://localhost:3000")
        print("🔑 Login: admin / admin123")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("💬 Creating demo data for Multi-Agent System...")
    print("=" * 50)
    
    success = create_demo_data()
    
    if success:
        print("\n✅ Demo data created successfully!")
    else:
        print("\n❌ Failed to create demo data")
        sys.exit(1)
