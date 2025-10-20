# Contributing to DB2 to Snowflake Table Converter

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information**:
   - DB2 DDL that causes the issue
   - Expected vs actual output
   - Error messages (if any)
   - Python version and operating system

### Suggesting Enhancements

1. **Open a discussion** for major feature requests
2. **Create an issue** with the "enhancement" label
3. **Describe the use case** and expected behavior
4. **Consider backward compatibility**

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠 Development Setup

### Prerequisites

- Python 3.7 or higher
- Git
- Text editor or IDE

### Local Setup

1. **Clone your fork**:
   ```bash
   git clone https://github.com/JoshKCIT/db2_tables_to_snowflake_tables_app.git
   cd db2_tables_to_snowflake_tables_app
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Run tests** to ensure everything works:
   ```bash
   python scripts/01_split_db2_ddl.py --selftest
   python scripts/02_convert_to_snowflake.py --selftest
   ```

## 📝 Coding Standards

### Python Code Style

- **Follow PEP 8** for Python code style
- **Use meaningful variable names**
- **Add docstrings** for all functions and classes
- **Keep functions focused** and reasonably sized
- **Use type hints** where appropriate

### Documentation

- **Update README.md** for user-facing changes
- **Add docstrings** for new functions
- **Update examples** if adding new features
- **Keep comments current** with code changes

### Testing

- **Test new features** with the self-test mode
- **Add example DDL** for new data types or features
- **Verify backward compatibility**
- **Test edge cases** and error conditions

## 🧪 Testing Guidelines

### Self-Test Mode

Both scripts support `--selftest` mode:

```bash
python scripts/01_split_db2_ddl.py --selftest
python scripts/02_convert_to_snowflake.py --selftest
```

### Manual Testing

1. **Use the examples** in the `examples/` directory
2. **Test with your own DDL** files
3. **Verify output** matches expected results
4. **Check issues log** for appropriate warnings

### Test Cases to Consider

- **Basic table structures** with common data types
- **Complex constraints** and primary keys
- **Various default values** and expressions
- **Edge cases** like empty tables or malformed DDL
- **Unicode and special characters** in table/column names

## 🔄 Pull Request Process

### Before Submitting

1. **Run self-tests** to ensure nothing is broken
2. **Check code style** and formatting
3. **Update documentation** as needed
4. **Test with example files**
5. **Verify backward compatibility**

### PR Description

Include in your pull request:

- **Summary** of changes
- **Motivation** for the change
- **Testing performed**
- **Breaking changes** (if any)
- **Screenshots** or examples (if applicable)

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** with various DDL files
4. **Documentation review**
5. **Approval and merge**

## 🏗 Project Structure

```
db2_tables_to_snowflake_tables_app/
├── scripts/                    # Main conversion scripts
│   ├── 01_split_db2_ddl.py    # DDL splitting logic
│   └── 02_convert_to_snowflake.py  # Conversion logic
├── examples/                   # Example files and expected outputs
├── data/                      # Input/output directories
├── tests/                     # Test files (future)
└── docs/                      # Additional documentation (future)
```

## 🎯 Areas for Contribution

### High Priority

- **Additional data type mappings** for DB2 types not yet supported
- **Improved error handling** and user feedback
- **Performance optimizations** for large DDL files
- **Better constraint handling** (foreign keys, check constraints)

### Medium Priority

- **Command-line interface improvements**
- **Configuration file support**
- **Batch processing enhancements**
- **Logging improvements**

### Low Priority

- **GUI interface** (if desired)
- **Integration with CI/CD pipelines**
- **Docker containerization**
- **Additional output formats**

## 📋 Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 💬 Communication

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Request Comments**: For code review feedback

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone, regardless of:

- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, nationality, personal appearance, race
- Religion, or sexual identity and orientation

### Our Standards

**Positive behavior includes**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes**:
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## 📄 License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

## 🙏 Recognition

Contributors will be recognized in:
- **README.md** contributors section
- **CHANGELOG.md** for significant contributions
- **Release notes** for major features

---

Thank you for contributing to make this tool better for the data engineering community! 🚀
