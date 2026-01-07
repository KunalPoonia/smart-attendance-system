# Issue #001: Security - Hardcoded Secret Key Fallback

## Type
🔒 Security / Bug

## Description
The `config.py` file contains a hardcoded fallback secret key (`'your-secret-key-here'`) which poses a security risk. If the `SECRET_KEY` environment variable is not set, the application will use this predictable default value.

## Location
- File: `config.py`
- Line: 6

## Current Code
```python
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
```

## Risk
- Session hijacking
- CSRF token prediction
- Cookie tampering
- Overall application security compromise

## Proposed Fix
1. Generate a secure random key if environment variable is not set (for development only)
2. Raise an error in production if SECRET_KEY is not configured
3. Add `.env.example` file for documentation
4. Update documentation

## Labels
- security
- bug
- priority: high
- configuration

## Acceptance Criteria
- [ ] No hardcoded secret key in production
- [ ] Clear error message if SECRET_KEY not set in production
- [ ] Development mode generates secure random key
- [ ] Documentation updated with setup instructions
