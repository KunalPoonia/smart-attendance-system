"""
Tests for Analytics Dashboard feature
"""
import pytest
from datetime import date, timedelta
import json


class TestAnalyticsDashboard:
    """Test cases for analytics dashboard"""
    
    def test_analytics_page_loads(self, client):
        """Test that analytics page loads successfully"""
        response = client.get('/analytics')
        assert response.status_code == 200
        assert b'Analytics Dashboard' in response.data
    
    def test_analytics_page_with_days_param(self, client):
        """Test analytics page with custom days parameter"""
        response = client.get('/analytics?days=7')
        assert response.status_code == 200
        
        response = client.get('/analytics?days=90')
        assert response.status_code == 200
    
    def test_analytics_trend_api(self, client):
        """Test attendance trend API endpoint"""
        response = client.get('/api/analytics/trend?days=30')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'trend' in data
        assert 'total_students' in data
        assert isinstance(data['trend'], list)
    
    def test_analytics_department_api(self, client):
        """Test department-wise analytics API"""
        response = client.get('/api/analytics/department?days=30')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'departments' in data
        assert isinstance(data['departments'], list)
    
    def test_analytics_status_distribution_api(self, client):
        """Test status distribution API"""
        response = client.get('/api/analytics/status_distribution?days=30')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'distribution' in data
        assert 'Present' in data['distribution']
        assert 'Absent' in data['distribution']
        assert 'Late' in data['distribution']
        assert 'On Leave' in data['distribution']
    
    def test_analytics_top_students_api(self, client):
        """Test top students API endpoint"""
        response = client.get('/api/analytics/top_students?days=30&limit=5')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'top_students' in data
        assert isinstance(data['top_students'], list)
    
    def test_analytics_at_risk_api(self, client):
        """Test at-risk students API endpoint"""
        response = client.get('/api/analytics/at_risk?days=30&threshold=75&limit=5')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'at_risk' in data
        assert 'threshold' in data
        assert data['threshold'] == 75
    
    def test_analytics_weekly_heatmap_api(self, client):
        """Test weekly heatmap API endpoint"""
        response = client.get('/api/analytics/weekly_heatmap?weeks=4')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'heatmap' in data
        assert isinstance(data['heatmap'], list)
    
    def test_analytics_recent_activity_api(self, client):
        """Test recent activity API endpoint"""
        response = client.get('/api/analytics/recent_activity?limit=10')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'activity' in data
        assert isinstance(data['activity'], list)


@pytest.fixture
def client():
    """Create test client"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import app
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            from src.database.models import db
            db.create_all()
        yield client
