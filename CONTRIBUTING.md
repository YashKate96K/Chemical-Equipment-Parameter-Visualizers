# Contributing to Chemical Equipment Parameter Visualizer

Thank you for your interest in contributing to this project! This guide will help you get started with contributing to the Chemical Equipment Parameter Visualizer.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git
- Basic knowledge of Django, React, and PyQt5

### Setup Instructions

1. **Fork the Repository**
   ```bash
   # Fork the repository on GitHub and clone your fork
   git clone https://github.com/your-username/chemical-equipment-parameter-visualizer.git
   cd chemical-equipment-parameter-visualizer
   ```

2. **Set Up Development Environment**
   ```bash
   # Backend setup
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   
   # Frontend setup
   cd ../frontend
   npm install
   
   # Desktop app setup
   cd ../desktop
   pip install -r requirements.txt
   ```

3. **Run Tests**
   ```bash
   # Backend tests
   cd backend
   python manage.py test
   
   # Frontend tests (if available)
   cd frontend
   npm test
   ```

## 📋 How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear title describing the bug
   - Detailed description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots if applicable

### Suggesting Features

1. **Check existing issues** for similar requests
2. **Create a feature request** with:
   - Clear title describing the feature
   - Detailed description of the proposed feature
   - Use case and benefits
   - Implementation suggestions (optional)

### Code Contributions

1. **Create an issue** (or comment on existing one) to discuss your planned changes
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the coding standards below
4. **Test your changes** thoroughly
5. **Commit your changes**:
   ```bash
   git commit -m "feat: add your feature description"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request** with:
   - Clear title and description
   - Reference to the related issue
   - Screenshots if applicable
   - Testing instructions

## 🎯 Areas for Contribution

### Backend (Django)
- [ ] API endpoint improvements
- [ ] Data processing optimizations
- [ ] Authentication enhancements
- [ ] Database schema improvements
- [ ] Performance optimizations

### Frontend (React)
- [ ] UI/UX improvements
- [ ] New chart types
- [ ] Mobile responsiveness
- [ ] Performance optimizations
- [ ] Accessibility improvements

### Desktop App (PyQt5)
- [ ] New chart types
- [ ] UI improvements
- [ ] Performance optimizations
- [ ] Cross-platform compatibility
- [ ] Additional export formats

### Documentation
- [ ] API documentation
- [ ] User guides
- [ ] Code comments
- [ ] Examples and tutorials

## 📝 Coding Standards

### Python (Backend & Desktop)
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Use type hints where appropriate

```python
def calculate_correlation_matrix(data: np.ndarray) -> np.ndarray:
    """
    Calculate correlation matrix for the given data.
    
    Args:
        data: Input data array
        
    Returns:
        Correlation matrix
    """
    return np.corrcoef(data.T)
```

### JavaScript/React (Frontend)
- Use ES6+ features
- Follow Airbnb style guide
- Use meaningful variable names
- Add JSDoc comments for functions
- Keep components focused and reusable

```javascript
/**
 * Renders a correlation heatmap component
 * @param {Object} props - Component props
 * @param {Array} props.data - Data for visualization
 * @param {Function} props.onUpdate - Update callback
 */
const CorrelationHeatmap = ({ data, onUpdate }) => {
  // Component implementation
};
```

### Git Commit Messages
Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for code style changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

Examples:
```bash
git commit -m "feat: add heatmap correlation analysis"
git commit -m "fix: resolve desktop app memory leak"
git commit -m "docs: update API documentation"
```

## 🧪 Testing

### Backend Testing
- Write unit tests for new functions
- Test API endpoints
- Test database operations
- Use Django's test framework

### Frontend Testing
- Write component tests
- Test user interactions
- Test responsive design
- Use Jest/React Testing Library

### Desktop App Testing
- Test chart rendering
- Test data processing
- Test UI interactions
- Test cross-platform compatibility

## 📸 Screenshots and Demos

When adding new features:
- Include screenshots in your PR
- Add GIFs for UI changes
- Provide clear testing instructions
- Document any configuration changes

## 🤝 Code Review Process

1. **Self-review** your code before submitting
2. **Ensure all tests pass**
3. **Update documentation** if needed
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Keep PR focused** on a single feature/fix

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Manual testing completed
- [ ] Cross-platform testing (desktop app)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or clearly documented)

## Screenshots
Add screenshots for UI changes.

## Issues
Closes #(issue number)
```

## 🚀 Release Process

Releases are managed by project maintainers:
1. Update version numbers
2. Update CHANGELOG.md
3. Create Git tag
4. Create GitHub release
5. Update documentation

## 💬 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For general questions and ideas
- **Email**: For private matters (if available)

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Chemical Equipment Parameter Visualizer! 🎉
