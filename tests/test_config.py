"""Tests for configuration module."""
import os
import pytest
from unittest.mock import patch


class TestSecretKey:
    """Test secret key configuration."""
    
    def test_secret_key_from_env(self):
        """Should use SECRET_KEY from environment."""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-123'}):
            # Re-import to get fresh config
            from config import get_secret_key
            # Clear any cached value
            import importlib
            import config
            importlib.reload(config)
            assert config.get_secret_key() == 'test-secret-123'
    
    def test_production_requires_secret_key(self):
        """Should raise error in production without SECRET_KEY."""
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=True):
            # Remove SECRET_KEY if present
            os.environ.pop('SECRET_KEY', None)
            
            from config import get_secret_key
            import importlib
            import config
            importlib.reload(config)
            
            with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
                get_secret_key()
    
    def test_development_generates_key(self):
        """Should generate random key in development."""
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}, clear=True):
            os.environ.pop('SECRET_KEY', None)
            
            from config import get_secret_key
            import importlib
            import config
            importlib.reload(config)
            
            key = get_secret_key()
            assert key is not None
            assert len(key) == 64  # 32 bytes = 64 hex chars
