import pytest
from models import Admin, Employee, TaxRule, TaxCalculation

def test_admin_dashboard(client, auth_client, db):
    """Test admin dashboard access and functionality."""
    # Login as admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
    assert b'Tax Rules' in response.data
    assert b'User Management' in response.data

def test_manage_tax_rules(client, db):
    """Test tax rule management."""
    # Login as admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    # Create new tax rule
    response = client.post('/admin/tax_rules', json={
        'min_income': 1000001,
        'max_income': 1500000,
        'tax_rate': 30,
        'description': 'New tax bracket',
        'is_active': True
    })
    assert response.status_code == 200
    
    # Verify rule was created
    rule = TaxRule.query.filter_by(min_income=1000001).first()
    assert rule is not None
    assert rule.tax_rate == 30
    
    # Update tax rule
    response = client.put(f'/admin/tax_rules/{rule.id}', json={
        'tax_rate': 25,
        'description': 'Updated tax bracket'
    })
    assert response.status_code == 200
    
    # Verify update
    rule = TaxRule.query.get(rule.id)
    assert rule.tax_rate == 25
    assert rule.description == 'Updated tax bracket'

def test_user_management(client, db):
    """Test user management functionality."""
    # Login as admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    # List users
    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b'test@example.com' in response.data
    
    # Create new user
    response = client.post('/admin/users', json={
        'email': 'newuser@example.com',
        'name': 'New User',
        'password': 'password123'
    })
    assert response.status_code == 200
    
    # Verify user was created
    user = Employee.query.filter_by(email='newuser@example.com').first()
    assert user is not None
    
    # Deactivate user
    response = client.put(f'/admin/users/{user.id}', json={
        'is_active': False
    })
    assert response.status_code == 200
    
    # Verify user was deactivated
    user = Employee.query.get(user.id)
    assert not user.is_active

def test_admin_reports(client, auth_client, db):
    """Test admin reporting functionality."""
    # Create some test data
    auth_client.login()
    for income in [300000, 500000, 750000]:
        client.post('/calculate_tax', json={
            'annual_income': income,
            'deductions': {'section_80c': 50000}
        })
    
    # Login as admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    # Test aggregate reports
    response = client.get('/admin/reports/aggregate')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_users' in data
    assert 'total_calculations' in data
    assert data['total_calculations'] == 3
    
    # Test detailed reports
    response = client.get('/admin/reports/detailed')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'

def test_audit_logging(client, db):
    """Test audit logging for admin actions."""
    # Login as admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    # Perform some actions
    client.post('/admin/tax_rules', json={
        'min_income': 2000001,
        'max_income': 2500000,
        'tax_rate': 35,
        'description': 'New tax bracket'
    })
    
    # Check audit logs
    response = client.get('/admin/audit_logs')
    assert response.status_code == 200
    assert b'Created tax rule' in response.data
    
def test_admin_security(client, auth_client):
    """Test admin security restrictions."""
    # Try accessing admin page without login
    response = client.get('/admin/dashboard')
    assert response.status_code == 302  # Redirect to login
    
    # Try accessing as regular user
    auth_client.login()
    response = client.get('/admin/dashboard')
    assert response.status_code == 403  # Forbidden
    
    # Try creating tax rule as regular user
    response = client.post('/admin/tax_rules', json={
        'min_income': 100000,
        'tax_rate': 10
    })
    assert response.status_code == 403
