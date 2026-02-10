# Contributing to Selenium2Playwright

First off, thank you for considering contributing to Selenium2Playwright! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our commitment to:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Collaborate towards common goals

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check if the issue already exists. When you create a bug report, include:

- **Clear title** - Describe the issue briefly
- **Steps to reproduce** - Numbered steps
- **Expected behavior** - What you expected
- **Actual behavior** - What actually happened
- **Screenshots** - If applicable
- **Environment details** - Python version, OS, LLM provider

Example:
```
**Bug: Conversion fails with ActionChains**

**Steps:**
1. Create file with ActionChains code
2. Run: python -m src test.py
3. See error

**Expected:** Successful conversion
**Actual:** AttributeError: 'NoneType'...

**Environment:**
- Python 3.11
- Windows 11
- Ollama with codellama
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Use case** - Why is this needed?
- **Proposed solution** - How should it work?
- **Alternatives** - What else could work?
- **Additional context** - Any other details

### Pull Requests

1. Fork the repository
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

#### Pull Request Guidelines

- Update README if needed
- Add tests for new features
- Follow existing code style
- Keep changes focused
- Reference related issues

## Development Setup

```bash
# Clone repository
git clone https://github.com/Qais7744/Selenium2PlaywrightConvertToLocalLLM.git
cd Selenium2PlaywrightConvertToLocalLLM

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install pytest black isort flake8

# Run tests
pytest tests/

# Format code
black src/ tests/
isort src/ tests/
```

## Project Structure

```
Selenium2PlaywrightConvertToLocalLLM/
├── src/                    # Main source code
│   ├── __init__.py
│   ├── converter.py        # Core conversion logic
│   ├── llm_client.py       # LLM integrations
│   ├── code_parser.py      # Code analysis
│   └── cli.py             # Command line interface
├── tests/                  # Test files
├── examples/               # Example files
├── docs/                   # Documentation
├── assets/                 # Images and media
├── requirements.txt        # Dependencies
├── config.yaml            # Configuration
└── README.md              # Documentation
```

## Style Guidelines

### Python Code Style

- Follow PEP 8
- Use black for formatting
- Use meaningful variable names
- Add docstrings to functions
- Type hints encouraged

Example:
```python
def convert_file(
    input_path: str, 
    output_path: Optional[str] = None
) -> str:
    """
    Convert a Selenium file to Playwright.
    
    Args:
        input_path: Path to input file
        output_path: Optional output path
        
    Returns:
        Path to converted file
    """
    # Implementation
    pass
```

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues when applicable

Examples:
```
Add support for ActionChains conversion

Fix bug with nested try-except blocks

Update README with Ollama setup instructions

Closes #123
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_converter.py::TestConverter::test_simple_navigation

# Run with verbose output
pytest -v
```

### Writing Tests

- Use pytest
- Name test functions descriptively
- Use fixtures for setup
- Test both success and error cases

Example:
```python
def test_find_element_conversion(converter):
    """Test that find_element is converted correctly."""
    code = 'driver.find_element(By.ID, "test")'
    result = converter.convert_code(code)
    assert '#test' in result
    assert 'By.ID' not in result
```

## Documentation

- Update README for user-facing changes
- Add docstrings for new functions
- Update config examples if needed
- Keep examples up to date

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion
- Contact maintainers

Thank you for contributing! 🎉
