"""
Tests for Dark Mode feature
"""
import pytest
import os


class TestDarkMode:
    """Test cases for dark mode feature"""
    
    def test_dark_mode_css_exists(self):
        """Test that dark mode CSS file exists"""
        css_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'css', 'dark-mode.css'
        )
        assert os.path.exists(css_path), "dark-mode.css should exist"
    
    def test_dark_mode_js_exists(self):
        """Test that dark mode JS file exists"""
        js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'js', 'dark-mode.js'
        )
        assert os.path.exists(js_path), "dark-mode.js should exist"
    
    def test_dark_mode_css_has_theme_variables(self):
        """Test that CSS contains theme variables"""
        css_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'css', 'dark-mode.css'
        )
        with open(css_path, 'r') as f:
            content = f.read()
        
        # Check for dark theme selector
        assert '[data-theme="dark"]' in content
        
        # Check for key CSS variables
        assert '--bg-primary' in content
        assert '--text-primary' in content
        assert '--border-color' in content
    
    def test_dark_mode_js_has_toggle_function(self):
        """Test that JS contains toggle functionality"""
        js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'js', 'dark-mode.js'
        )
        with open(js_path, 'r') as f:
            content = f.read()
        
        # Check for key functions
        assert 'toggleTheme' in content
        assert 'setTheme' in content
        assert 'localStorage' in content
    
    def test_base_template_includes_dark_mode(self, client):
        """Test that base template includes dark mode files"""
        response = client.get('/')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        assert 'dark-mode.css' in html
        assert 'dark-mode.js' in html
    
    def test_dark_mode_respects_system_preference(self):
        """Test that JS checks for system preference"""
        js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'js', 'dark-mode.js'
        )
        with open(js_path, 'r') as f:
            content = f.read()
        
        assert 'prefers-color-scheme' in content


@pytest.fixture
def client():
    """Create test client"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import app
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            from src.database.models import db
            db.create_all()
        yield client
