import pytest
from decimal import Decimal
from models import TaxCalculation, TaxRule

def test_tax_calculation(client, auth_client, db):
    """Test tax calculation functionality."""
    # Login first
    auth_client.login()
    
    # Test calculation with no tax bracket
    response = client.post('/calculate_tax', json={
        'annual_income': 200000,
        'deductions': {
            'section_80c': 50000,
            'health_insurance': 25000
        }
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['tax_amount'] == 0
    
    # Test calculation with 5% tax bracket
    response = client.post('/calculate_tax', json={
        'annual_income': 400000,
        'deductions': {
            'section_80c': 50000,
            'health_insurance': 25000
        }
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['tax_amount'] > 0
    
    # Verify calculation is saved
    calc = TaxCalculation.query.filter_by(user_id=1).first()
    assert calc is not None
    assert calc.income_data['annual_income'] == 400000

def test_tax_saving_tips(client, auth_client):
    """Test tax saving recommendations."""
    auth_client.login()
    
    response = client.get('/tax_saving_tips')
    assert response.status_code == 200
    assert b'Section 80C' in response.data
    assert b'Health Insurance' in response.data

def test_tax_history(client, auth_client, db):
    """Test tax calculation history."""
    auth_client.login()
    
    # Create some test calculations
    for income in [300000, 500000]:
        client.post('/calculate_tax', json={
            'annual_income': income,
            'deductions': {
                'section_80c': 50000
            }
        })
    
    # Check history
    response = client.get('/tax_history')
    assert response.status_code == 200
    assert b'300,000' in response.data
    assert b'500,000' in response.data

def test_tax_report_generation(client, auth_client, db):
    """Test tax report generation."""
    auth_client.login()
    
    # Create a calculation first
    client.post('/calculate_tax', json={
        'annual_income': 600000,
        'deductions': {
            'section_80c': 150000
        }
    })
    
    calc = TaxCalculation.query.first()
    
    # Generate report
    response = client.get(f'/generate_report/{calc.id}')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'

def test_invalid_inputs(client, auth_client):
    """Test input validation."""
    auth_client.login()
    
    # Test negative income
    response = client.post('/calculate_tax', json={
        'annual_income': -50000,
        'deductions': {}
    })
    assert response.status_code == 400
    
    # Test excessive deductions
    response = client.post('/calculate_tax', json={
        'annual_income': 500000,
        'deductions': {
            'section_80c': 500000  # More than allowed limit
        }
    })
    assert response.status_code == 400

def test_tax_rule_changes(client, auth_client, db):
    """Test tax calculation with different tax rules."""
    # Login as admin to modify tax rules
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'admin_password'
    })
    
    # Add a new tax rule
    client.post('/admin/tax_rules', json={
        'min_income': 500001,
        'max_income': 1000000,
        'tax_rate': 20,
        'description': 'New tax bracket'
    })
    
    # Login as regular user
    auth_client.login()
    
    # Test calculation with new tax bracket
    response = client.post('/calculate_tax', json={
        'annual_income': 750000,
        'deductions': {}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['tax_amount'] > 0  # Should use new 20% bracket
