"""
Script to fix auth_server_full.py by replacing global logger usage with lazy loading
"""
import re

def fix_auth_server():
    """Fix auth_server_full.py to use lazy loading for loggers."""
    
    # Read the file
    with open('auth_server_full.py', 'r') as f:
        content = f.read()
    
    # Pattern to find function definitions
    function_pattern = r'(@app\.(get|post|put|delete|patch)\([^)]+\)\s*(?:async\s+)?def\s+[^(]+\([^)]*\):)'
    
    # Find all functions that use api_logger or system_logger
    logger_usage_pattern = r'(api_logger|system_logger)\.'
    
    # Split content into lines for easier processing
    lines = content.split('\n')
    
    # Track which functions need logger initialization
    functions_needing_loggers = set()
    
    # Find functions that use loggers
    current_function = None
    for i, line in enumerate(lines):
        # Check if this is a function definition
        if re.search(r'@app\.(get|post|put|delete|patch)', line):
            # Look for the actual function definition in next few lines
            for j in range(i, min(i+5, len(lines))):
                if 'def ' in lines[j]:
                    current_function = j
                    break
        
        # Check if this line uses a logger
        if current_function is not None and re.search(logger_usage_pattern, line):
            functions_needing_loggers.add(current_function)
    
    # Add logger initialization to functions that need it
    for func_line_num in sorted(functions_needing_loggers, reverse=True):
        # Find the function definition line
        func_line = lines[func_line_num]
        
        # Find the first line of the function body (after the def line)
        body_start = func_line_num + 1
        while body_start < len(lines) and (lines[body_start].strip() == '' or lines[body_start].strip().startswith('"""') or lines[body_start].strip().startswith('"')):
            body_start += 1
            # Skip docstring
            if '"""' in lines[body_start-1]:
                while body_start < len(lines) and '"""' not in lines[body_start]:
                    body_start += 1
                body_start += 1
        
        # Get the indentation of the function body
        if body_start < len(lines):
            indent = len(lines[body_start]) - len(lines[body_start].lstrip())
            logger_init = ' ' * indent + 'api_logger, system_logger = get_loggers()'
            
            # Insert the logger initialization
            lines.insert(body_start, logger_init)
    
    # Join lines back together
    fixed_content = '\n'.join(lines)
    
    # Write the fixed content
    with open('auth_server_full.py', 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed auth_server_full.py with lazy logger loading")

if __name__ == "__main__":
    fix_auth_server()
