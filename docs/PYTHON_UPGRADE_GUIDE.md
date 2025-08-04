# Python 3.10+ Upgrade Guide

## 🚨 Requirement
This project requires **Python 3.10+** due to the use of modern union type syntax (`str | None` instead of `Union[str, None]`).

## 🔍 Check Current Version
```bash
python3 --version
# or
make check-deps
```

## 🚀 Upgrade Options

### Option 1: Using Homebrew (macOS - Recommended)
```bash
# Install Python 3.11 (latest stable)
brew install python@3.11

# Update your PATH in ~/.zshrc or ~/.bash_profile
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
python3 --version
```

### Option 2: Using pyenv (Cross-platform)
```bash
# Install pyenv if not already installed
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.7
pyenv global 3.11.7

# Verify installation
python3 --version
```

### Option 3: Using Official Python Installer
1. Download Python 3.11+ from https://www.python.org/downloads/
2. Run the installer
3. Make sure to check "Add Python to PATH"
4. Restart terminal and verify: `python3 --version`

### Option 4: Using Conda/Miniconda
```bash
# Create new environment with Python 3.11
conda create -n multi_agents python=3.11
conda activate multi_agents

# Verify installation
python --version
```

## 🔧 After Upgrade

1. **Verify Python version**:
   ```bash
   make check-deps
   ```

2. **Reinstall dependencies**:
   ```bash
   make install
   ```

3. **Test the application**:
   ```bash
   make quick-start
   ```

## 🐳 Alternative: Use Docker

If you prefer not to upgrade your system Python, you can use Docker:

```bash
# Build and run with Docker
make docker-build
make docker-up

# Access GUI at http://localhost:8501
```

## 🛠️ Troubleshooting

### Multiple Python Versions
If you have multiple Python versions, you might need to:

```bash
# Check which python3 is being used
which python3

# Use specific version
python3.11 --version

# Create alias in ~/.zshrc or ~/.bash_profile
alias python3='python3.11'
```

### Virtual Environment
Create a virtual environment with the correct Python version:

```bash
# Using specific Python version
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### PATH Issues
Make sure the new Python version is in your PATH:

```bash
# Check PATH
echo $PATH

# Add to PATH (example for Homebrew)
export PATH="/opt/homebrew/bin:$PATH"
```

## ✅ Verification

After upgrading, run these commands to verify everything works:

```bash
# Check dependencies
make check-deps

# Should show Python 3.10+ and no errors

# Test installation
make dev-setup

# Start services
make quick-start
```

## 📝 Why Python 3.10+?

Python 3.10 introduced the new union type syntax:
- **Old**: `Union[str, None]` or `Optional[str]`
- **New**: `str | None`

This project uses the modern syntax for cleaner, more readable code. The benefits include:
- More concise type hints
- Better readability
- Follows modern Python best practices
- Future-proof code

## 🔗 Useful Links

- [Python 3.11 Download](https://www.python.org/downloads/)
- [Homebrew Python](https://formulae.brew.sh/formula/python@3.11)
- [pyenv Documentation](https://github.com/pyenv/pyenv)
- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
