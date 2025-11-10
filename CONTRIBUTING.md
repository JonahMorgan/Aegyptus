# Contributing to Aegyptus

Thank you for your interest in contributing to Aegyptus! This document provides guidelines for contributing to this Egyptian hieroglyphics translation project.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (Python version, OS, etc.)
- Any relevant code snippets or error messages

### Suggesting Enhancements

We welcome suggestions for new features or improvements! Please open an issue with:
- A clear description of the enhancement
- The motivation or use case
- Any relevant examples or mockups

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Commit your changes** with clear, descriptive commit messages
6. **Push to your fork** and submit a pull request

#### Pull Request Guidelines

- Keep changes focused and atomic
- Include relevant tests if adding new functionality
- Update the README.md if adding new features
- Follow existing code style and conventions
- Write clear commit messages

## Code Style

### Python Code

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise
- Add comments for complex logic

Example:
```python
def parse_hieroglyphic_text(text: str) -> List[str]:
    """
    Parse hieroglyphic text into individual tokens.
    
    Args:
        text: The hieroglyphic text to parse
        
    Returns:
        A list of tokenized hieroglyphic elements
    """
    # Implementation here
    pass
```

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Keep the first line under 72 characters
- Reference issues and pull requests when relevant

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/JonahMorgan/Aegyptus.git
cd Aegyptus
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Testing

Before submitting a pull request:
- Test your changes with various inputs
- Ensure existing functionality still works
- Verify that data processing pipelines run correctly

## Project Areas

Here are some areas where contributions are especially welcome:

- **Data Collection**: Improving Wiktionary parsers and adding new data sources
- **Tokenization**: Enhancing hieroglyphic tokenization algorithms
- **Translation Models**: Improving model architecture and training
- **Documentation**: Expanding usage examples and tutorials
- **Testing**: Adding test coverage for existing functionality

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Reach out to the maintainers

## Code of Conduct

Please note that this project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

By contributing to Aegyptus, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Aegyptus! Your efforts help preserve and make accessible ancient Egyptian language and culture.
