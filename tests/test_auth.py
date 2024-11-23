import pytest
from flask import session, g
from models import Employee, Admin

def test_register(client, db):
    """Test registration."""
    # Test successful registration
    response = client.post('/auth/register', data={
        'email': 'new@example.com',
        'name': 'New User',
        'password': 'newpassword123',
        'confirm_password': 'newpassword123'
    })
    assert response.status_code == 302  # Redirect after successful registration
    
    # Check if user was created
    user = Employee.query.filter_by(email='new@example.com').first()
    assert user is not None
    assert user.name == 'New User'
    
    # Test duplicate email
    response = client.post('/auth/register', data={
        'email': 'new@example.com',
        'name': 'Another User',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    assert b'Email already registered' in response.data

def test_login(client, auth_client):
    """Test login."""
    # Test successful login
    response = auth_client.login()
    assert response.status_code == 302  # Redirect after successful login
    
    with client:
        client.get('/')  # Get a page to trigger session handling
        assert session['user_id'] is not None
        assert session['user_type'] == 'employee'

def test_logout(client, auth_client):
    """Test logout."""
    auth_client.login()
    
    with client:
        auth_client.logout()
        assert 'user_id' not in session

def test_admin_login(client):
    """Test admin login."""
    response = client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    assert response.status_code == 302
    
    with client:
        client.get('/')
        assert session['user_type'] == 'admin'

def test_password_validation(client):
    """Test password validation rules."""
    # Test password too short
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'name': 'Test User',
        'password': 'short',
        'confirm_password': 'short'
    })
    assert b'Password must be at least 8 characters long' in response.data
    
    # Test password mismatch
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'name': 'Test User',
        'password': 'password123',
        'confirm_password': 'password456'
    })
    assert b'Passwords must match' in response.data

def test_login_required(client):
    """Test login_required decorator."""
    # Try accessing protected page
    response = client.get('/tax_calculator')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

def test_admin_required(client, auth_client):
    """Test admin_required decorator."""
    # Login as regular user
    auth_client.login()
    
    # Try accessing admin page
    response = client.get('/admin/dashboard')
    assert response.status_code == 302  # Redirect to login
    
    # Login as admin
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    # Try accessing admin page again
    response = client.get('/admin/dashboard')
    assert response.status_code == 200  # Success
