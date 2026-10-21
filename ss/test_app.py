import sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app
from database import init_db

init_db()

with app.test_client() as client:
    # ---------------- 1. Login as Admin ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/login', data={'role': 'Admin', 'user': 'admin', 'pw': 'admin123', '_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    print('PASS 1: Admin login')

    # ---------------- 2. Check HopDong list view ----------------
    res = client.get('/m/hopdong')
    assert res.status_code == 200
    assert 'Hợp đồng' in res.text
    assert 'HD001' in res.text
    print('PASS 2: GET /m/hopdong (Seed contracts listed)')

    # ---------------- 3. Test Invalid Date Validation ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/new', data={
        'MaHD': 'HD_ERR',
        'MaNV': 'NV001',
        'LoaiHD': 'Thử việc',
        'NgayBD': '2026-05-10',
        'NgayKT': '2026-05-01',  # Earlier than NgayBD!
        'LuongCoBan': '15000000',
        'TrangThai': 'Hiệu lực',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu' in res.text
    print('PASS 3: Date range validation works on contract creation')

    # ---------------- 4. Add Valid Contract ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/new', data={
        'MaHD': 'HD099',
        'MaNV': 'NV001',
        'LoaiHD': 'Xác định thời hạn (1 năm)',
        'NgayBD': '2026-01-01',
        'NgayKT': '2027-01-01',
        'LuongCoBan': '25000000',
        'TrangThai': 'Hiệu lực',
        'GhiChu': 'Hop dong moi 2026',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'HD099' in res.text
    print('PASS 4: Created contract HD099 successfully')

    # ---------------- 5. Edit Contract ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/HD099/edit', data={
        'MaHD': 'HD099',
        'MaNV': 'NV001',
        'LoaiHD': 'Xác định thời hạn (3 năm)',
        'NgayBD': '2026-01-01',
        'NgayKT': '2029-01-01',
        'LuongCoBan': '30000000',
        'TrangThai': 'Hết hạn',
        'GhiChu': 'Gia han hop dong',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'HD099' in res.text
    print('PASS 5: Edited contract HD099 successfully')

    # ---------------- 6. Delete Contract ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/HD099/delete', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'HD099' not in res.text
    print('PASS 6: Deleted contract HD099 successfully')

    # ---------------- 7. Logout ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    # ---------------- 8. Employee View (/me) & Permission Check ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'NhanVien', 'user': 'nv002', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    # In /me, employee can view their contract (NV002 has HD002)
    res = client.get('/me')
    assert res.status_code == 200
    assert 'Hợp đồng lao động' in res.text
    assert 'HD002' in res.text
    print('PASS 7: Employee can view personal contract in /me')

    # Employee cannot access /m/hopdong -> 403
    res = client.get('/m/hopdong')
    assert res.status_code == 403
    print('PASS 8: Employee restricted from /m/hopdong (403 Forbidden)')

    # ---------------- 9. Manager Permission Check ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'QuanLy', 'user': 'ql001', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    # Manager can access /m/hopdong
    res = client.get('/m/hopdong')
    assert res.status_code == 200
    print('PASS 9: Manager has access to /m/hopdong (200 OK)')

print('\n=== ALL CONTRACT MANAGEMENT TESTS PASSED! ===')
