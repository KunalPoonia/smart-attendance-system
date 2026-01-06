# PR #001: Fix Security Issue - Remove Hardcoded Secret Key

## Description
This PR fixes a security vulnerability where a hardcoded fallback secret key was used in `config.py`.

## Related Issue
Fixes #001 - Security - Hardcoded Secret Key Fallback

## Type of Change
- [x] Bug fix
- [x] Security fix
- [ ] New feature
- [ ] Breaking change
- [x] Documentation update

## Changes Made
1. **config.py**: Added `get_secret_key()` function that:
   - Uses `SECRET_KEY` from environment if available
   - Raises error in production if `SECRET_KEY` not set
   - Generates secure random key for development (with warning)

2. **Added `.env.example`**: Template for environment variables

3. **Added `.gitignore`**: Prevents committing sensitive files

## Testing
- [x] Tested locally in development mode (auto-generates key)
- [x] Verified error is raised when `FLASK_ENV=production` without `SECRET_KEY`
- [x] Application starts normally with `SECRET_KEY` set

## Security Checklist
- [x] No hardcoded secrets
- [x] Sensitive files in `.gitignore`
- [x] Clear documentation for setup

## How to Test
```bash
# Development (should work with warning)
python app.py

# Production without SECRET_KEY (should fail)
FLASK_ENV=production python app.py

# Production with SECRET_KEY (should work)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") FLASK_ENV=production python app.py
```
