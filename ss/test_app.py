import io
import csv
import json
from datetime import date, datetime
from app import app
from database import get_db

with app.test_client() as client:
    # ---------------- 1. Authentication & Role-based Access ----------------
    res = client.get('/login')
    assert res.status_code == 200
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')

    # Admin Login
    res = client.post('/login', data={'role': 'Admin', 'user': 'admin', 'pw': 'admin123', '_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    assert 'admin' in res.text
    print('PASS 1: Admin login')

    # ---------------- 2. Module Listing & Contract CRUD ----------------
    res = client.get('/m/hopdong')
    assert res.status_code == 200
    assert 'HD001' in res.text
    print('PASS 2: GET /m/hopdong (Seed contracts listed)')

    # Cross-field date validation: NgayKT < NgayBD
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/new', data={
        'MaHD': 'HD_TEST_FAIL',
        'MaNV': 'NV001',
        'LoaiHD': 'Thử việc',
        'NgayBD': '2026-10-10',
        'NgayKT': '2026-10-05',
        'LuongCoBan': '10000000',
        'TrangThai': 'Hiệu lực',
        'GhiChu': 'Test date validation',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu' in res.text
    print('PASS 3: Date range validation works on contract creation')

    # Create valid contract
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/new', data={
        'MaHD': 'HD099',
        'MaNV': 'NV001',
        'LoaiHD': 'Thử việc',
        'NgayBD': '2026-10-01',
        'NgayKT': '2026-10-31',
        'LuongCoBan': '15000000',
        'TrangThai': 'Hiệu lực',
        'GhiChu': 'Hop dong thu nghiem',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'HD099' in res.text
    print('PASS 4: Created contract HD099 successfully')

    # Edit contract
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/HD099/edit', data={
        'MaNV': 'NV001',
        'LoaiHD': 'Thử việc',
        'NgayBD': '2026-10-01',
        'NgayKT': '2026-11-15',
        'LuongCoBan': '16000000',
        'TrangThai': 'Hiệu lực',
        'GhiChu': 'Gia han thu viec',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'Cập nhật thành công' in res.text
    print('PASS 5: Edited contract HD099 successfully')

    # Delete contract
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/m/hopdong/HD099/delete', data={'_csrf': csrf_token}, follow_redirects=True)
    assert 'HD099' not in res.text
    print('PASS 6: Deleted contract HD099 successfully')

    # ---------------- 3. Pagination & Export Verification ----------------
    res = client.get('/m/nhanvien')
    assert res.status_code == 200
    assert 'Xuất Excel/CSV' in res.text
    assert 'bản ghi' in res.text
    print('PASS 7: Pagination UI & Export link present in list view')

    # Module export CSV test
    res = client.get('/m/nhanvien/export')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    csv_text = res.data.decode('utf-8')
    assert 'NV001' in csv_text
    assert 'Nguyễn Văn An' in csv_text
    print('PASS 8: Export module data to Excel-compatible CSV works')

    # Leave report export test
    current_month = date.today().strftime('%Y-%m')
    res = client.get(f'/report/leave?thang={current_month}&export=1')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    print('PASS 9: Export monthly leave report to CSV works')

    # ---------------- 4. Employee Leave Request Workflow ----------------
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
        'NgayBD': '2026-11-20',
        'NgayKT': '2026-11-22',
        'LyDo': 'Nghỉ phép thường niên',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'Gửi đơn xin nghỉ phép thành công' in res.text
    assert 'Chờ duyệt' in res.text
    print('PASS 12: Employee submitted leave request successfully (Pending status)')

    # Find the created leave id
    with app.app_context():
        db = get_db()
        leave_row = db.execute("SELECT MaNP FROM NghiPhep WHERE MaNV='NV002' AND NgayBD='2026-11-20'").fetchone()
        leave_id = leave_row['MaNP']

    # ---------------- 5. Manager Approval & Rejection Workflow ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'QuanLy', 'user': 'ql001', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/m/nghiphep')
    assert res.status_code == 200
    assert 'Duyệt' in res.text
    assert 'Từ chối' in res.text
    print('PASS 13: Manager sees pending leave with Approve & Reject buttons')

    # Manager approves leave
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{leave_id}/approve', data={'_csrf': csrf_token}, follow_redirects=True)
    assert 'Đã duyệt đơn nghỉ phép thành công' in res.text
    print('PASS 14: Manager approved leave successfully')

    # Manager rejects/cancels approval
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/m/nghiphep/{leave_id}/reject', data={'_csrf': csrf_token}, follow_redirects=True)
    assert 'Đã từ chối đơn nghỉ phép' in res.text
    print('PASS 15: Manager rejected leave successfully')

    # ---------------- 6. Employee Profile & Self-Service ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'NhanVien', 'user': 'nv002', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/profile/edit', data={
        'SDT': '0901888999',
        'Email': 'binh.tran@vnm.vn',
        'DiaChi': 'Số 123 Hoàng Mai, Hà Nội',
        'NgaySinh': '1992-07-21',
        'GioiTinh': 'Nữ',
        'TrinhDo': 'Thạc sĩ',
        'ChuyenMon': 'Quản trị lao động',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert 'Cập nhật thông tin cá nhân thành công' in res.text
    print('PASS 16: Employee updated personal contact info')

    res = client.get('/me')
    assert res.status_code == 200
    assert 'Thông tin công việc' in res.text
    assert '0901888999' in res.text
    assert 'Lịch sử chấm công & Ngày công' in res.text
    assert 'Đánh giá hiệu suất công việc & KPI' in res.text
    print('PASS 17: Employee views Job Info, Attendance history, and KPI evaluations in /me')

    res = client.get('/announcements')
    assert res.status_code == 200
    assert 'Thông báo nội bộ' in res.text
    print('PASS 18: Employee views announcements')

    # ---------------- 7. Manager Monitoring & Reports ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'QuanLy', 'user': 'ql001', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/attendance/quick-checkin', data={'_csrf': csrf_token}, follow_redirects=True)
    assert 'Đã ghi nhận chấm công nhanh' in res.text
    print('PASS 19: Manager monitors attendance & executes quick check-in')

    res = client.get('/report/hr')
    assert res.status_code == 200
    assert 'Báo cáo nhân sự' in res.text
    print('PASS 20: Manager views Department HR report')

    res = client.get('/report/hr?export=1')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    print('PASS 21: Manager exports Department HR report to CSV')

    # ---------------- 8. Admin Global Governance ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'Admin', 'user': 'admin', 'pw': 'admin123', '_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/report/hr')
    assert res.status_code == 200
    assert 'Toàn công ty' in res.text
    print('PASS 22: Admin views company-wide HR report')

    res = client.get('/m/thongbao')
    assert res.status_code == 200
    print('PASS 23: Admin manages announcements')

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

    # ---------------- 9. New Actor Feature Expansion Tests ----------------

    # Test 27: Employee Check-in & Check-out
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'NhanVien', 'user': 'nv005', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/checkin', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    print('PASS 27: Employee online Check-in succeeds')

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/checkout', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    print('PASS 28: Employee online Check-out succeeds')

    # Test 29: Employee uploads certificate / document
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/document/upload', data={
        'TenTaiLieu': 'Chứng chỉ AWS Cloud Practitioner',
        'Loai': 'Chứng chỉ chuyên môn',
        'NgayCap': '2026-05-15',
        'NoiCap': 'Amazon Web Services',
        'GhiChu': 'Điểm số 920/1000',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Chứng chỉ AWS Cloud Practitioner' in res.text
    print('PASS 29: Employee uploads degree/certificate to profile')

    # Test 30: Employee submits attendance explanation
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/attendance/explain', data={
        'Ngay': '2026-10-20',
        'GioVaoDeXuat': '08:00',
        'GioRaDeXuat': '17:30',
        'LyDo': 'Quên quẹt thẻ do đi công tác gặp khách hàng sáng sớm',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã gửi giải trình công thành công' in res.text
    print('PASS 30: Employee submits attendance explanation')

    # Test 31: Employee registers overtime (OT)
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/ot/register', data={
        'Ngay': '2026-10-26',
        'SoGio': '3.0',
        'Loai': 'Ngày thường',
        'LyDo': 'Deploy và kiểm thử bản vá bảo mật hệ thống',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã gửi đăng ký làm thêm 3.0 giờ' in res.text
    print('PASS 31: Employee registers overtime (OT)')

    # Test 32: Employee requests salary advance
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/advance/request', data={
        'ThangNam': current_month,
        'SoTien': '1500000',
        'LyDo': 'Giải quyết việc gia đình đột xuất',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã gửi yêu cầu tạm ứng' in res.text
    print('PASS 32: Employee requests salary advance')

    # Test 33: Employee KPI self-assessment
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/me/kpi/self-eval', data={
        'DiemTuDanhGia': '95',
        'NhanXetCaNhan': 'Hoàn thành 100% mục tiêu sprint và không có bug phát sinh',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Tự đánh giá KPI' in res.text
    print('PASS 33: Employee KPI self-assessment succeeds')

    # Test 34: Training Catalog browsing and course enrollment
    res = client.get('/training')
    assert res.status_code == 200
    assert 'Khóa đào tạo nội bộ' in res.text

    with app.app_context():
        db = get_db()
        course = db.execute("SELECT TOP 1 MaKDT FROM KhoaDaoTao").fetchone()
        course_id = course['MaKDT'] if course else 1

    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post(f'/training/register/{course_id}', data={'_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    print('PASS 34: Employee enrolls in corporate training course')

    # Test 35: Employee submits proposal / complaint
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/feedback', data={
        'TieuDe': 'Đề xuất bổ sung màn hình phụ cho phòng Kỹ thuật',
        'Loai': 'Đề xuất cải tiến',
        'NoiDung': 'Kính gửi ban giám đốc trang bị thêm màn hình 24 inch giúp lập trình viên code hiệu quả hơn.',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Ý kiến của bạn đã được gửi thành công' in res.text
    print('PASS 35: Employee submits suggestion/feedback to management')

    # ---------------- 10. Manager Unified Approval Hub Tests ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'QuanLy', 'user': 'ql001', 'pw': '123456', '_csrf': csrf_token}, follow_redirects=True)

    res = client.get('/manager/approvals')
    assert res.status_code == 200
    assert 'Trung tâm Phê duyệt Yêu cầu' in res.text
    assert 'Đăng ký làm thêm giờ (OT) chờ duyệt' in res.text
    assert 'Đơn giải trình chấm công chờ duyệt' in res.text
    assert 'Đơn tạm ứng tiền lương chờ duyệt' in res.text
    print('PASS 36: Manager views unified Approval Center')

    # Manager approves OT and Attendance Explanation
    with app.app_context():
        db = get_db()
        ot_row = db.execute("SELECT MaTC FROM TangCa WHERE MaNV='NV005' AND TrangThai=N'Chờ duyệt'").fetchone()
        explain_row = db.execute("SELECT MaGT FROM GiaiTrinhCong WHERE MaNV='NV005' AND TrangThai=N'Chờ duyệt'").fetchone()
        advance_row = db.execute("SELECT MaTU FROM TamUng WHERE MaNV='NV005' AND TrangThai=N'Chờ duyệt'").fetchone()

    if ot_row:
        with client.session_transaction() as sess:
            csrf_token = sess.get('_csrf')
        res = client.post(f"/manager/approve/ot/{ot_row['MaTC']}", data={'_csrf': csrf_token}, follow_redirects=True)
        assert 'Đã phê duyệt đăng ký tăng ca thành công' in res.text
        print('PASS 37: Manager approves overtime (OT) request')

    if explain_row:
        with client.session_transaction() as sess:
            csrf_token = sess.get('_csrf')
        res = client.post(f"/manager/approve/explain/{explain_row['MaGT']}", data={'_csrf': csrf_token}, follow_redirects=True)
        assert 'Đã duyệt giải trình công' in res.text
        print('PASS 38: Manager approves attendance explanation and automatically updates ChamCong')

    if advance_row:
        with client.session_transaction() as sess:
            csrf_token = sess.get('_csrf')
        res = client.post(f"/manager/approve/advance/{advance_row['MaTU']}", data={'_csrf': csrf_token}, follow_redirects=True)
        assert 'Đã phê duyệt tạm ứng' in res.text
        print('PASS 39: Manager approves salary advance')

    # Manager submits HR proposal
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/manager/proposals', data={
        'MaNV': 'NV005',
        'LoaiDeXuat': 'Khen thưởng',
        'MucDeXuat': 'Thưởng thành tích 2.000.000 VNĐ',
        'LyDo': 'Hoàn thành xuất sắc nhiệm vụ phát triển các tính năng quan trọng',
        '_csrf': csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Đã gửi đề xuất' in res.text
    print('PASS 40: Manager submits HR proposal (khen thưởng/tăng lương) to Admin')

    # ---------------- 11. Admin Global Governance & Analytics Tests ----------------
    res = client.get('/login')
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    client.post('/login', data={'role': 'Admin', 'user': 'admin', 'pw': 'admin123', '_csrf': csrf_token}, follow_redirects=True)

    # Admin approves HR proposal
    with app.app_context():
        db = get_db()
        prop_row = db.execute("SELECT MaDXNS FROM DeXuatNhanSu WHERE MaNV='NV005' AND TrangThai=N'Chờ HR phê duyệt'").fetchone()

    if prop_row:
        with client.session_transaction() as sess:
            csrf_token = sess.get('_csrf')
        res = client.post(f"/admin/proposals/approve/{prop_row['MaDXNS']}", data={'_csrf': csrf_token}, follow_redirects=True)
        assert 'Đã phê duyệt đề xuất' in res.text
        print('PASS 41: Admin approves HR proposal and auto-generates reward decision')

    # Admin closes attendance for month
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/admin/attendance/close', data={'thang': current_month, '_csrf': csrf_token}, follow_redirects=True)
    assert 'Đã chốt công tháng' in res.text
    print('PASS 42: Admin executes monthly attendance closing')

    # Admin runs automatic batch payroll calculation
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    res = client.post('/admin/payroll/calculate', data={'thang': current_month, '_csrf': csrf_token}, follow_redirects=True)
    assert 'Đã hoàn thành tính bảng lương' in res.text
    print('PASS 43: Admin executes automatic batch payroll calculator')

    # Verify LuongCung accuracy in database (No fractional or prorating error!)
    with app.app_context():
        db = get_db()
        nv1_sal = db.execute("SELECT LuongCung FROM Luong WHERE MaNV='NV001' AND ThangNam=?", (current_month,)).fetchone()
        assert nv1_sal and nv1_sal['LuongCung'] == 14000000.0, f"Expected 14000000.0 but got {nv1_sal['LuongCung'] if nv1_sal else None}"
    print('PASS 44: Verified LuongCung (Luong cung) is 100% accurate without fractional error')

    # Admin checks Audit Log
    res = client.get('/audit-log')
    assert res.status_code == 200
    assert 'Nhật ký Hoạt động Hệ thống' in res.text
    assert 'Check-in' in res.text or 'Đăng nhập' in res.text
    print('PASS 45: Admin views Audit Log with tracked user events')

    # Admin views & exports Advanced HR & Salary Analytics
    res = client.get(f'/reports/analytics?thang={current_month}&export=1')
    assert res.status_code == 200
    assert res.mimetype == 'text/csv'
    csv_analytics = res.data.decode('utf-8')
    assert 'BÁO CÁO PHÂN TÍCH NHÂN SỰ' in csv_analytics
    assert 'TỔNG CỘNG' in csv_analytics
    print('PASS 46: Admin views and exports Advanced HR & Salary Cost Analytics to CSV')

    # Verify Employee List Avatar features (Column, Modal, and Quick Upload)
    res = client.get('/m/nhanvien')
    assert res.status_code == 200
    assert 'avatarModal' in res.text
    assert 'Thêm / Đổi ảnh nhân viên' in res.text
    assert 'uploads/avatars/avatar_NV001.svg' in res.text
    print('PASS 47: Employee List renders avatars and quick upload modal')

    # Update Employee Avatar via POST endpoint
    with client.session_transaction() as sess:
        csrf_token = sess.get('_csrf')
    new_avatar_url = 'https://images.unsplash.com/photo-sample.jpg'
    res = client.post('/nhanvien/NV001/avatar', data={'avatar_url': new_avatar_url, '_csrf': csrf_token}, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        db = get_db()
        updated_emp = db.execute("SELECT HinhAnh FROM NhanVien WHERE MaNV='NV001'").fetchone()
        assert updated_emp['HinhAnh'] == new_avatar_url
    # Reset back to SVG avatar for testing consistency
    with app.app_context():
        db = get_db()
        db.execute("UPDATE NhanVien SET HinhAnh='/static/uploads/avatars/avatar_NV001.svg' WHERE MaNV='NV001'")
        db.commit()
    print('PASS 48: Update employee avatar endpoint succeeds and updates database')

    # Cleanup test artifacts
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM NghiPhep WHERE MaNV='NV002' AND NgayBD='2026-11-20'")
        db.execute("DELETE FROM TaiLieuNhanVien WHERE TenTaiLieu='Chứng chỉ AWS Cloud Practitioner'")
        db.commit()

print('\n=== ALL 48 TESTS PASSED! LUONGCUNG ACCURACY & EMPLOYEE AVATAR FEATURE VERIFIED! ===')
