import os
os.environ["JWT_SECRET"]="test"
from fastapi.testclient import TestClient
from backend.main import app
def test_menu_and_auth_and_order():
    with TestClient(app) as client:
        run_order_test(client)
def run_order_test(client):
    assert client.get('/api/menu').status_code==200
    email='testcustomer@example.com'
    r=client.post('/api/auth/register',json={'name':'Test','email':email,'password':'password123'})
    if r.status_code==400:r=client.post('/api/auth/login',json={'email':email,'password':'password123'})
    token=r.json()['token']; menu=client.get('/api/menu').json()
    order=client.post('/api/orders',headers={'Authorization':'Bearer '+token},json={'items':[{'id':menu[0]['id'],'quantity':1}],'order_type':'Pickup'}); assert order.status_code==200
    assert order.json()['paymentStatus'] == 'Not collected'
