# Contributing to Channels DVR Web Player

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment using the provided setup scripts
4. Create a new branch for your feature or bug fix

## Development Setup

### Quick Setup
```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/channels-dvr-player.git
cd channels-dvr-player

# Set up virtual environment and dependencies
./setup_venv.sh  # Linux/macOS
# or
setup_venv.bat   # Windows

# Activate the environment
source activate_venv.sh  # Linux/macOS
# or
activate_venv.bat        # Windows
```

### Detailed Setup
See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## How to Contribute

### Reporting Bugs
- Use the GitHub Issues page
- Include detailed steps to reproduce
- Include your environment details (OS, Python version, etc.)
- Include relevant log output

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain why it would be valuable to users

### Code Contributions

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/channels-dvr-player.git
   cd channels-dvr-player
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

3. **Make Changes**
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Run the application locally
   python app.py
   
   # Test different scenarios
   # See TESTING.md for testing guidelines
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Code Style Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small
- Update docstrings for new functions

## Testing

- Test your changes locally before submitting
- Ensure the application starts without errors
- Test with different Channels DVR server configurations
- See [TESTING.md](TESTING.md) for detailed testing procedures

## Documentation

- Update README.md if adding new features
- Update relevant documentation files
- Add inline comments for complex code
- Update QUICKSTART.md for setup changes

## Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what changes you made and why
- **Testing**: Describe how you tested the changes
- **Screenshots**: Include screenshots for UI changes
- **Breaking Changes**: Clearly mark any breaking changes

### Pull Request Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of the code completed
- [ ] Changes are tested locally
- [ ] Documentation updated if needed
- [ ] No merge conflicts

## Questions?

- Open an issue for questions about contributing
- Check existing issues and pull requests first
- Be patient and respectful in all interactions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
