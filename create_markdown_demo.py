#!/usr/bin/env python3
"""
Script to create demo messages with markdown and LaTeX for testing
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config

def create_markdown_demo():
    """Create demo messages with markdown and LaTeX content."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Demo session for markdown/LaTeX
        demo_session = {
            "session_id": "session_markdown_demo_001",
            "user_id": "admin",
            "title": "Markdown & LaTeX Demo",
            "total_messages": 4,
            "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Demo messages with rich content
        demo_messages = [
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_markdown_demo_001",
                "user_id": "admin",
                "user_input": "Can you show me some **markdown formatting** and LaTeX math like $x^2 + y^2 = z^2$?",
                "agent_response": """# Markdown & LaTeX Demo

I'll show you various formatting options!

## Text Formatting
- **Bold text** and *italic text*
- `inline code` and regular text
- ~~strikethrough~~ text

## Math Examples
Here's the Pythagorean theorem: $a^2 + b^2 = c^2$

And here's a more complex equation:
$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$

## Code Block
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
```

## Lists
1. First item
2. Second item
   - Nested bullet
   - Another nested item
3. Third item

> This is a blockquote with some important information!

## Table
| Feature | Supported | Notes |
|---------|-----------|-------|
| Markdown | ✅ | Full GFM support |
| LaTeX | ✅ | KaTeX rendering |
| Code | ✅ | Syntax highlighting |""",
                "created_at": (datetime.utcnow() - timedelta(minutes=25)).isoformat(),
                "processing_time": 2100,
                "primary_intent": "markdown_demo",
                "processing_mode": "single_agent",
                "success": True
            },
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_markdown_demo_001",
                "user_id": "admin",
                "user_input": "Show me more advanced LaTeX formulas and mathematical expressions",
                "agent_response": """# Advanced Mathematics with LaTeX

## Calculus
The derivative of $f(x) = x^n$ is:
$$\\frac{d}{dx}x^n = nx^{n-1}$$

## Linear Algebra
Matrix multiplication:
$$\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix} \\begin{pmatrix} x \\\\ y \\end{pmatrix} = \\begin{pmatrix} ax + by \\\\ cx + dy \\end{pmatrix}$$

## Statistics
The normal distribution probability density function:
$$f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{1}{2}\\left(\\frac{x-\\mu}{\\sigma}\\right)^2}$$

## Complex Numbers
Euler's formula: $e^{i\\pi} + 1 = 0$

## Summation and Integration
$$\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}$$

$$\\int_0^1 x^2 dx = \\frac{1}{3}$$

## Greek Letters and Symbols
- Alpha: $\\alpha$, Beta: $\\beta$, Gamma: $\\gamma$
- Delta: $\\Delta$, Theta: $\\theta$, Lambda: $\\lambda$
- Pi: $\\pi$, Sigma: $\\sigma$, Omega: $\\omega$

These formulas render beautifully with KaTeX! 🎯""",
                "created_at": (datetime.utcnow() - timedelta(minutes=20)).isoformat(),
                "processing_time": 1800,
                "primary_intent": "math_latex",
                "processing_mode": "single_agent",
                "success": True
            },
            {
                "message_id": str(uuid.uuid4()),
                "session_id": "session_markdown_demo_001",
                "user_id": "admin",
                "user_input": "Can you show me code examples in different programming languages?",
                "agent_response": """# Programming Examples

## Python
```python
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def factorial(self, n):
        if n <= 1:
            return 1
        return n * self.factorial(n - 1)

calc = Calculator()
print(calc.add(5, 3))
print(calc.factorial(5))
```

## JavaScript
```javascript
const fetchData = async (url) => {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

// Usage
fetchData('/api/users')
    .then(result => console.log(result))
    .catch(err => console.error(err));
```

## SQL
```sql
SELECT 
    u.name,
    u.email,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at >= '2024-01-01'
GROUP BY u.id, u.name, u.email
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC
LIMIT 10;
```

## Bash
```bash
#!/bin/bash

# Function to backup database
backup_database() {
    local db_name=$1
    local backup_dir="/backups"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    echo "Starting backup of $db_name..."
    
    if mysqldump "$db_name" > "$backup_dir/${db_name}_${timestamp}.sql"; then
        echo "✅ Backup completed: ${db_name}_${timestamp}.sql"
        return 0
    else
        echo "❌ Backup failed!"
        return 1
    fi
}

backup_database "production_db"
```

Each language gets proper syntax highlighting! 🎨""",
                "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "processing_time": 2200,
                "primary_intent": "code_examples",
                "processing_mode": "single_agent",
                "success": True
            }
        ]
        
        # Create session
        existing_session = db_config.sessions.find_one({"session_id": demo_session["session_id"]})
        if not existing_session:
            db_config.sessions.insert_one(demo_session)
            print(f"✅ Created session: {demo_session['title']}")
        else:
            print(f"🔄 Session already exists: {demo_session['title']}")
        
        # Create messages
        created_messages = 0
        for message_data in demo_messages:
            existing_message = db_config.messages.find_one({"message_id": message_data["message_id"]})
            if not existing_message:
                db_config.messages.insert_one(message_data)
                created_messages += 1
                print(f"✅ Created message: {message_data['primary_intent']}")
        
        print("\n" + "="*50)
        print(f"🎉 Created {created_messages} markdown/LaTeX demo messages")
        print("\n📋 Demo Content:")
        print("-" * 30)
        print("  📝 Markdown formatting examples")
        print("  🧮 LaTeX mathematical expressions")
        print("  💻 Code blocks with syntax highlighting")
        print("  📊 Tables, lists, and blockquotes")
        
        print("\n🌐 Test at: http://localhost:3000")
        print("🔑 Login: admin / admin123")
        print("📖 Look for 'Markdown & LaTeX Demo' session")
        
    except Exception as e:
        print(f"❌ Error creating markdown demo: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("📝 Creating markdown & LaTeX demo messages...")
    print("=" * 50)
    
    success = create_markdown_demo()
    
    if success:
        print("\n✅ Markdown demo created successfully!")
    else:
        print("\n❌ Failed to create markdown demo")
        sys.exit(1)
