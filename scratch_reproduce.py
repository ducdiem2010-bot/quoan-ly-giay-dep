import tempfile
from pathlib import Path
from app import create_app
import re

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = str(Path(tmpdir) / 'test_staff.sqlite3')
    app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite', 'DATABASE': db_path, 'FORCE_ACCOUNT_STATUS_GUARD': True})
    client = app.test_client()

    res = client.get('/login')
    token = re.search(r'name="csrf_token" value="([^"]+)"', res.get_data(as_text=True)).group(1)
    res_login = client.post('/login', data={'csrf_token': token, 'email': 'admin@shop.vn', 'password': 'Demo@12345'}, follow_redirects=True)
    print('Admin login:', res_login.status_code)

    res_form = client.get('/admin/staff/new')
    token = re.search(r'name="csrf_token" value="([^"]+)"', res_form.get_data(as_text=True)).group(1)

    res_create = client.post('/admin/staff/new', data={
        'csrf_token': token,
        'name': 'Nhân Viên Mới Test',
        'email': 'nhanvienmoi@shop.vn',
        'password': 'Password123'
    }, follow_redirects=True)
    print('Create staff:', res_create.status_code, [m for m in res_create.get_data(as_text=True).splitlines() if 'notice' in m])

    res_logout = client.post('/logout', data={'csrf_token': token}, follow_redirects=True)
    print('Admin logout:', res_logout.status_code)

    res = client.get('/login')
    token = re.search(r'name="csrf_token" value="([^"]+)"', res.get_data(as_text=True)).group(1)
    res_staff_login = client.post('/login', data={'csrf_token': token, 'email': 'nhanvienmoi@shop.vn', 'password': 'Password123'}, follow_redirects=True)
    print('Staff login status:', res_staff_login.status_code, 'Path:', res_staff_login.request.path)
    for line in res_staff_login.get_data(as_text=True).splitlines():
        if 'notice' in line or 'flash' in line or 'warning' in line or 'alert' in line:
            print('Message:', line)
