import sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app
from database import init_db, get_db

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

    # ---------------- 7. Test Pagination & Export CSV ----------------
    res = client.get('/m/nhanvien?page=1')
    assert res.status_code == 200
    assert 'Hiển thị' in res.text
    assert 'Xuất Excel/CSV' in res.text
    print('PASS 7: Pagination UI & Export link present in list view')

    res = client.get('/m/nhanvien/export')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    assert 'attachment' in res.headers.get('Content-Disposition', '')
    assert 'Nguyễn Văn An' in res.text
    print('PASS 8: Export module data to Excel-compatible CSV works')

    res = client.get('/report/leave?export=1')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    print('PASS 9: Export monthly leave report to CSV works')

    # ---------------- 8. Logout Admin ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    # ---------------- 9. Employee View (/me) & Leave Request ----------------
    # Clean up any leftover test leave for NV002
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM NghiPhep WHERE MaNV='NV002'")
        db.commit()

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'NhanVien', 'user': 'nv002', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/me')
    assert res.status_code == 200
    assert 'Xin nghỉ phép' in res.text
    print('PASS 10: Employee views /me with leave request button')

    # Employee submits invalid leave request (NgayKT < NgayBD)
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/leave/request', data={
        'NgayBD': '2026-11-10',
        'NgayKT': '2026-11-05',
        'LyDo': 'Nghỉ cá nhân',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu' in res.text
    print('PASS 11: Employee leave request date validation works')

    # Employee submits valid leave request
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/leave/request', data={
        'NgayBD': '2026-11-10',
        'NgayKT': '2026-11-12',
        'LyDo': 'Nghỉ việc gia đình',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Chờ duyệt' in res.text
    assert 'Nghỉ việc gia đình' in res.text
    assert 'Hủy đơn' in res.text
    print('PASS 12: Employee submitted leave request successfully (Pending status)')

    # ---------------- 10. Manager Leave Approval & Rejection ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'QuanLy', 'user': 'ql001', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    # Manager visits /m/nghiphep
    res = client.get('/m/nghiphep')
    assert res.status_code == 200
    assert 'Nghỉ việc gia đình' in res.text
    assert 'Duyệt' in res.text
    assert 'Từ chối' in res.text
    print('PASS 13: Manager sees pending leave with Approve & Reject buttons')

    # Get the pending leave ID from DB
    with app.app_context():
        db = get_db()
        pending_leave = db.execute("SELECT MaNP FROM NghiPhep WHERE MaNV='NV002' AND TrangThai=N'Chờ duyệt'").fetchone()
        assert pending_leave is not None
        lid = pending_leave['MaNP']

    # Manager approves the leave
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{lid}/approve', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã duyệt đơn nghỉ phép thành công' in res.text
    print('PASS 14: Manager approved leave successfully')

    # Verify status changed to Đã duyệt in DB
    with app.app_context():
        db = get_db()
        leave_row = db.execute("SELECT TrangThai FROM NghiPhep WHERE MaNP=?", (lid,)).fetchone()
        assert leave_row['TrangThai'] == 'Đã duyệt'

    # Manager rejects the leave
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{lid}/reject', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã từ chối đơn nghỉ phép' in res.text
    print('PASS 15: Manager rejected leave successfully')

    # Re-approve the leave
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{lid}/approve', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200

    # ---------------- 11. Employee verifies approved leave in /me ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'NhanVien', 'user': 'nv002', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/me')
    assert res.status_code == 200
    assert 'Đã duyệt' in res.text
    print('PASS 16: Employee sees approved status for leave request')

    # Cleanup test leave
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM NghiPhep WHERE MaNV='NV002'")
        db.commit()

print('\n=== ALL TESTS PASSED! ALL NEW FEATURES VERIFIED! ===')
