"""
Tests for API Documentation (Swagger) feature
"""
import pytest
import os


class TestAPIDocumentation:
    """Test cases for API documentation"""
    
    def test_swagger_yaml_exists(self):
        """Test that swagger.yaml file exists"""
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'swagger.yaml'
        )
        assert os.path.exists(yaml_path), "swagger.yaml should exist"
    
    def test_swagger_yaml_valid(self):
        """Test that swagger.yaml has valid structure"""
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'swagger.yaml'
        )
        with open(yaml_path, 'r') as f:
            content = f.read()
        
        assert 'openapi: 3.0' in content
        assert 'info:' in content
        assert 'paths:' in content
        assert 'tags:' in content
    
    def test_swagger_ui_endpoint(self, client):
        """Test that Swagger UI endpoint is accessible"""
        response = client.get('/api/docs/')
        assert response.status_code == 200
    
    def test_swagger_yaml_endpoint(self, client):
        """Test that swagger.yaml is served"""
        response = client.get('/static/swagger.yaml')
        assert response.status_code == 200
        assert b'openapi' in response.data
    
    def test_api_docs_link_in_nav(self, client):
        """Test that API docs link exists in navigation"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'/api/docs' in response.data


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
            from database.models import db
            db.create_all()
        yield client
