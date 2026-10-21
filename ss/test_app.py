import sys
import json
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

    res = client.get('/m/nghiphep')
    assert res.status_code == 200
    assert 'Nghỉ việc gia đình' in res.text
    assert 'Duyệt' in res.text
    assert 'Từ chối' in res.text
    print('PASS 13: Manager sees pending leave with Approve & Reject buttons')

    with app.app_context():
        db = get_db()
        pending_leave = db.execute("SELECT MaNP FROM NghiPhep WHERE MaNV='NV002' AND TrangThai=N'Chờ duyệt'").fetchone()
        assert pending_leave is not None
        lid = pending_leave['MaNP']

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{lid}/approve', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã duyệt đơn nghỉ phép thành công' in res.text
    print('PASS 14: Manager approved leave successfully')

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{lid}/reject', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã từ chối đơn nghỉ phép' in res.text
    print('PASS 15: Manager rejected leave successfully')

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{lid}/approve', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200

    # ---------------- 11. Employee Updates Profile & Checks Info ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'NhanVien', 'user': 'nv002', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    # 11.1 Check Profile Edit GET & POST
    res = client.get('/me/profile/edit')
    assert res.status_code == 200
    assert 'Cập nhật thông tin cá nhân' in res.text

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/profile/edit', data={
        'SDT': '0901888999',
        'Email': 'binh_new@vnm.vn',
        'DiaChi': 'Số 10 Hoàn Kiếm, Hà Nội',
        'NgaySinh': '1992-07-21',
        'GioiTinh': 'Nữ',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Cập nhật thông tin cá nhân thành công' in res.text
    print('PASS 16: Employee updated personal contact info')

    # 11.2 Check /me for Job Info, Attendance, and Performance KPI
    res = client.get('/me')
    assert res.status_code == 200
    assert 'Thông tin công việc' in res.text
    assert '0901888999' in res.text
    assert 'Lịch sử chấm công & Ngày công' in res.text
    assert 'Đánh giá hiệu suất công việc & KPI' in res.text
    print('PASS 17: Employee views Job Info, Attendance history, and KPI evaluations in /me')

    # 11.3 Check Announcements for Employee
    res = client.get('/announcements')
    assert res.status_code == 200
    assert 'Thông báo nội bộ' in res.text
    print('PASS 18: Employee views announcements')

    # ---------------- 12. Manager HR Management Features ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'QuanLy', 'user': 'ql001', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    # 12.1 Attendance monitoring & Quick checkin
    res = client.get('/m/chamcong')
    assert res.status_code == 200
    assert 'Chấm công' in res.text

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/attendance/quick-checkin', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã ghi nhận chấm công nhanh' in res.text
    print('PASS 19: Manager monitors attendance & executes quick check-in')

    # 12.2 Performance evaluation (KPI)
    res = client.get('/m/danhgia')
    assert res.status_code == 200
    assert 'Đánh giá KPI' in res.text

    # 12.3 Department HR Report & Export
    res = client.get('/report/hr')
    assert res.status_code == 200
    assert 'Báo cáo nhân sự' in res.text
    assert 'Cơ cấu giới tính' in res.text
    print('PASS 20: Manager views Department HR report')

    res = client.get('/report/hr?export=1')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    print('PASS 21: Manager exports Department HR report to CSV')

    # ---------------- 13. Admin Management & Backup Center ----------------
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/logout', data={'_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'Admin', 'user': 'admin', 'pw': 'admin123', '_csrf': csrf_token}, follow_redirects=True)

    # 13.1 Company-wide HR Report
    res = client.get('/report/hr')
    assert res.status_code == 200
    assert 'Toàn công ty' in res.text
    print('PASS 22: Admin views company-wide HR report')

    # 13.2 Announcements Management
    res = client.get('/m/thongbao')
    assert res.status_code == 200
    assert 'Thông báo' in res.text
    print('PASS 23: Admin manages announcements')

    # 13.3 Backup Center & Exports
    res = client.get('/admin/backup')
    assert res.status_code == 200
    assert 'Sao lưu & Quản lý dữ liệu hệ thống' in res.text
    assert 'ChamCong' in res.text
    assert 'DanhGia' in res.text
    assert 'ThongBao' in res.text
    print('PASS 24: Admin accesses Backup Center and views table statistics')

    res = client.get('/admin/backup/export')
    assert res.status_code == 200
    assert res.mimetype == 'application/json'
    backup_obj = json.loads(res.data.decode('utf-8'))
    assert 'tables' in backup_obj
    assert 'NhanVien' in backup_obj['tables']
    assert len(backup_obj['tables']['NhanVien']) >= 5
    print('PASS 25: Admin downloads complete JSON database backup snapshot')

    res = client.get('/admin/backup/sql')
    assert res.status_code == 200
    assert 'INSERT INTO [NhanVien]' in res.text
    print('PASS 26: Admin downloads complete SQL script backup')

    # Cleanup test leave for NV002
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM NghiPhep WHERE MaNV='NV002'")
        db.commit()

print('\n=== ALL 26 TESTS PASSED! ALL FEATURES FOR ALL 3 ACTORS VERIFIED! ===')
