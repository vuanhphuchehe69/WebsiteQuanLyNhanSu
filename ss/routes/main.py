"""Main application routes: Dashboard, Personal Information, Announcements, Reports, and Admin Backup."""
import io
import csv
import json
import re
import os
import time
from datetime import date, datetime
from flask import Blueprint, session, redirect, url_for, render_template, request, flash, abort, Response, current_app
from config import NV, QL, AD, NV_SEL, EMP_JOIN, MSSQL_DATABASE, TONE, ROLE_NAME
from database import get_db
from utils import login_required, roles_required, log_activity

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dash():
    """Main dashboard displaying key HR statistics."""
    if session.get('role') == NV:
        return redirect(url_for('main.me'))

    db_conn = get_db()
    query_scalar = lambda query, args=None: db_conn.execute(query, args or ()).fetchone()[0]
    current_month = date.today().strftime('%Y-%m')
    today_str = date.today().strftime('%Y-%m-%d')
    role = session.get('role')
    mnv = session.get('mnv')

    # Department filter for manager
    mapb = None
    if role == QL:
        emp = db_conn.execute("SELECT c.MaPB, p.TenPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV LEFT JOIN PhongBan p ON c.MaPB=p.MaPB WHERE n.MaNV=?", (mnv,)).fetchone()
        mapb = emp['MaPB'] if emp else None

    if role == QL and mapb:
        stats = [
            ('Nhân sự phòng ban', query_scalar("SELECT COUNT(*) FROM NhanVien n JOIN ChucVu c ON n.MaCV=c.MaCV WHERE c.MaPB=?", (mapb,)), 'users'),
            ('Chấm công hôm nay', query_scalar("SELECT COUNT(*) FROM ChamCong x JOIN NhanVien n ON x.MaNV=n.MaNV JOIN ChucVu c ON n.MaCV=c.MaCV WHERE c.MaPB=? AND x.Ngay=?", (mapb, today_str)), 'check-square'),
            ('Đơn nghỉ chờ duyệt', query_scalar("SELECT COUNT(*) FROM NghiPhep x JOIN NhanVien n ON x.MaNV=n.MaNV JOIN ChucVu c ON n.MaCV=c.MaCV WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'", (mapb,)), 'calendar'),
            ('Đăng ký OT chờ duyệt', query_scalar("SELECT COUNT(*) FROM TangCa x JOIN NhanVien n ON x.MaNV=n.MaNV JOIN ChucVu c ON n.MaCV=c.MaCV WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'", (mapb,)), 'clock'),
            ('Giải trình công chờ duyệt', query_scalar("SELECT COUNT(*) FROM GiaiTrinhCong x JOIN NhanVien n ON x.MaNV=n.MaNV JOIN ChucVu c ON n.MaCV=c.MaCV WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'", (mapb,)), 'activity'),
            ('Tạm ứng chờ duyệt', query_scalar("SELECT COUNT(*) FROM TamUng x JOIN NhanVien n ON x.MaNV=n.MaNV JOIN ChucVu c ON n.MaCV=c.MaCV WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'", (mapb,)), 'dollar-sign'),
            ('Đề xuất nhân sự của tôi', query_scalar("SELECT COUNT(*) FROM DeXuatNhanSu WHERE NguoiDeXuat=?", (mnv,)), 'layers'),
            ('Khóa đào tạo đang mở', query_scalar("SELECT COUNT(*) FROM KhoaDaoTao WHERE TrangThai!=N'Hoàn thành'"), 'book-open'),
        ]
    else:
        stats = [
            ('Tổng nhân viên', query_scalar('SELECT COUNT(*) FROM NhanVien'), 'users'),
            ('Hợp đồng hiệu lực', query_scalar("SELECT COUNT(*) FROM HopDong WHERE TrangThai=N'Hiệu lực'"), 'file-text'),
            ('Phòng ban', query_scalar('SELECT COUNT(*) FROM PhongBan'), 'building'),
            ('Chức vụ', query_scalar('SELECT COUNT(*) FROM ChucVu'), 'briefcase'),
            ('Chấm công hôm nay', query_scalar("SELECT COUNT(*) FROM ChamCong WHERE Ngay=?", (today_str,)), 'check-square'),
            ('Đơn chờ duyệt (Toàn bộ)', query_scalar("SELECT (SELECT COUNT(*) FROM NghiPhep WHERE TrangThai=N'Chờ duyệt') + (SELECT COUNT(*) FROM TangCa WHERE TrangThai=N'Chờ duyệt') + (SELECT COUNT(*) FROM GiaiTrinhCong WHERE TrangThai=N'Chờ duyệt') + (SELECT COUNT(*) FROM TamUng WHERE TrangThai=N'Chờ duyệt')"), 'bell'),
            ('Đề xuất nhân sự chờ duyệt', query_scalar("SELECT COUNT(*) FROM DeXuatNhanSu WHERE TrangThai=N'Chờ HR phê duyệt'"), 'layers'),
            ('Khóa đào tạo', query_scalar('SELECT COUNT(*) FROM KhoaDaoTao'), 'book-open'),
            ('Yêu cầu tuyển dụng', query_scalar("SELECT COUNT(*) FROM YeuCauTuyenDung WHERE TrangThai=N'Đang tuyển'"), 'user-plus'),
            ('Tài khoản hệ thống', query_scalar('SELECT COUNT(*) FROM TaiKhoan'), 'key'),
        ]

    return render_template('dash.html', stats=stats)

@main_bp.route('/me')
@roles_required(NV, QL)
def me():
    """Personal view for employees and managers to see profile, documents, job info, salary, leaves, attendance, and overtime."""
    db_conn = get_db()
    mnv = session.get('mnv')
    current_month = date.today().strftime('%Y-%m')
    today_str = date.today().strftime('%Y-%m-%d')

    emp = db_conn.execute(NV_SEL + ' WHERE n.MaNV=?', (mnv,)).fetchone()
    if not emp:
        abort(404)

    salaries = db_conn.execute(
        'SELECT *, (LuongCung+LuongThuong+PhuCap-LuongUngTruoc-COALESCE(BaoHiem,0)-COALESCE(ThueTNCN,0)-COALESCE(KhauTruKhac,0)) AS ThucLinh FROM Luong WHERE MaNV=? ORDER BY ThangNam DESC',
        (mnv,)
    ).fetchall()
    leaves = db_conn.execute(
        'SELECT *, (DATEDIFF(day, CAST(NgayBD AS DATE), CAST(NgayKT AS DATE)) + 1) AS SoNgay FROM NghiPhep WHERE MaNV=? ORDER BY NgayBD DESC',
        (mnv,)
    ).fetchall()
    overtimes = db_conn.execute(
        'SELECT * FROM TangCa WHERE MaNV=? ORDER BY Ngay DESC',
        (mnv,)
    ).fetchall()
    contracts = db_conn.execute(
        'SELECT * FROM HopDong WHERE MaNV=? ORDER BY NgayBD DESC',
        (mnv,)
    ).fetchall()
    attendance = db_conn.execute(
        'SELECT * FROM ChamCong WHERE MaNV=? ORDER BY Ngay DESC',
        (mnv,)
    ).fetchall()
    evaluations = db_conn.execute(
        'SELECT * FROM DanhGia WHERE MaNV=? ORDER BY ThangNam DESC',
        (mnv,)
    ).fetchall()

    # Documents & Certificates
    documents = db_conn.execute('SELECT * FROM TaiLieuNhanVien WHERE MaNV=? ORDER BY NgayTai DESC', (mnv,)).fetchall()

    # Attendance explanations
    explanations = db_conn.execute('SELECT * FROM GiaiTrinhCong WHERE MaNV=? ORDER BY NgayGui DESC', (mnv,)).fetchall()

    # Rewards & Disciplines
    rewards_disciplines = db_conn.execute('SELECT * FROM KhenThuongKyLuat WHERE MaNV=? ORDER BY NgayQuyetDinh DESC', (mnv,)).fetchall()

    # Salary Advances
    advances = db_conn.execute('SELECT * FROM TamUng WHERE MaNV=? ORDER BY NgayYeuCau DESC', (mnv,)).fetchall()

    # Training enrollments
    trainings = db_conn.execute("""
        SELECT d.*, k.TenKhoa, k.GiangVien, k.ThoiGian, k.DiaDiem, k.TrangThai AS TrangThaiKhoa
        FROM DangKyDaoTao d
        JOIN KhoaDaoTao k ON d.MaKDT=k.MaKDT
        WHERE d.MaNV=?
        ORDER BY d.NgayDangKy DESC
    """, (mnv,)).fetchall()

    # Today's check-in status
    today_cc = db_conn.execute("SELECT * FROM ChamCong WHERE MaNV=? AND Ngay=?", (mnv, today_str)).fetchone()

    # Department manager info
    manager = None
    if emp.get('MaPB'):
        manager = db_conn.execute("""
            SELECT n.HoTen, n.Email, n.SDT
            FROM NhanVien n
            JOIN TaiKhoan t ON n.MaNV=t.MaNV
            JOIN ChucVu c ON n.MaCV=c.MaCV
            WHERE t.LoaiTK='QuanLy' AND c.MaPB=?
        """, (emp['MaPB'],)).fetchone()

    # Calculate attendance working days this month
    working_days = sum(
        1 for c in attendance
        if c.get('Ngay', '').startswith(current_month) and c.get('TrangThai') in ('Đúng giờ', 'Đi muộn', 'Về sớm')
    )

    return render_template(
        'me.html',
        emp=emp,
        L=salaries,
        P=leaves,
        T=overtimes,
        HD=contracts,
        CC=attendance,
        DG=evaluations,
        TL=documents,
        GT=explanations,
        KT=rewards_disciplines,
        TU=advances,
        DK_DT=trainings,
        today_cc=today_cc,
        today_str=today_str,
        manager=manager,
        working_days=working_days,
        current_month=current_month
    )

# ----------------- Check-in & Check-out -----------------
@main_bp.route('/me/checkin', methods=['POST'])
@roles_required(NV, QL)
def checkin():
    """Record employee arrival time for today."""
    db_conn = get_db()
    mnv = session.get('mnv')
    today_str = date.today().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M')

    status = 'Đúng giờ' if now_time <= '08:30' else 'Đi muộn'
    existing = db_conn.execute("SELECT * FROM ChamCong WHERE MaNV=? AND Ngay=?", (mnv, today_str)).fetchone()

    if existing:
        if existing['GioVao']:
            flash(f"Bạn đã check-in hôm nay lúc {existing['GioVao']}.", 'w')
        else:
            db_conn.execute("UPDATE ChamCong SET GioVao=?, TrangThai=? WHERE MaCC=?", (now_time, status, existing['MaCC']))
            db_conn.commit()
            log_activity(db_conn, 'Chấm công Check-in', f'Check-in lúc {now_time} ({status})')
            flash(f"Check-in thành công lúc {now_time} ({status})!", 'ok')
    else:
        db_conn.execute(
            "INSERT INTO ChamCong(MaNV, Ngay, GioVao, TrangThai, GhiChu) VALUES(?, ?, ?, ?, N'Check-in trực tuyến')",
            (mnv, today_str, now_time, status)
        )
        db_conn.commit()
        log_activity(db_conn, 'Chấm công Check-in', f'Check-in lúc {now_time} ({status})')
        flash(f"Check-in thành công lúc {now_time} ({status})!", 'ok')

    return redirect(url_for('main.me'))

@main_bp.route('/me/checkout', methods=['POST'])
@roles_required(NV, QL)
def checkout():
    """Record employee departure time for today."""
    db_conn = get_db()
    mnv = session.get('mnv')
    today_str = date.today().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M')

    existing = db_conn.execute("SELECT * FROM ChamCong WHERE MaNV=? AND Ngay=?", (mnv, today_str)).fetchone()

    if not existing or not existing['GioVao']:
        flash("Bạn chưa check-in hôm nay nên không thể check-out.", 'err')
    elif existing['GioRa']:
        flash(f"Bạn đã check-out hôm nay lúc {existing['GioRa']}.", 'w')
    else:
        status = existing['TrangThai']
        if now_time < '17:30' and status == 'Đúng giờ':
            status = 'Về sớm'
        db_conn.execute("UPDATE ChamCong SET GioRa=?, TrangThai=? WHERE MaCC=?", (now_time, status, existing['MaCC']))
        db_conn.commit()
        log_activity(db_conn, 'Chấm công Check-out', f'Check-out lúc {now_time} ({status})')
        flash(f"Check-out thành công lúc {now_time}! Chúc bạn một buổi tối vui vẻ.", 'ok')

    return redirect(url_for('main.me'))

# ----------------- Document & Certificate Upload -----------------
@main_bp.route('/me/document/upload', methods=['GET', 'POST'])
@roles_required(NV, QL)
def upload_document():
    """Upload degree, diploma, or personal certificate."""
    db_conn = get_db()
    mnv = session.get('mnv')

    if request.method == 'POST':
        ten_tl = request.form.get('TenTaiLieu', '').strip()
        loai = request.form.get('Loai', '').strip()
        ngay_cap = request.form.get('NgayCap', '').strip()
        noi_cap = request.form.get('NoiCap', '').strip()
        ghi_chu = request.form.get('GhiChu', '').strip()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not ten_tl or not loai:
            flash('Tên tài liệu và loại bằng cấp không được để trống.', 'err')
        else:
            db_conn.execute("""
                INSERT INTO TaiLieuNhanVien(MaNV, TenTaiLieu, Loai, NgayCap, NoiCap, TepDinhKem, NgayTai, GhiChu)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """, (mnv, ten_tl, loai, ngay_cap or None, noi_cap or None, None, now_str, ghi_chu or None))
            db_conn.commit()
            log_activity(db_conn, 'Tải lên bằng cấp / giấy tờ', f'{ten_tl} ({loai})')
            flash(f"Đã thêm bằng cấp/giấy tờ '{ten_tl}' thành công.", 'ok')
            return redirect(url_for('main.me'))

    return render_template('form_doc.html')

@main_bp.route('/me/document/<int:doc_id>/delete', methods=['POST'])
@roles_required(NV, QL, AD)
def delete_document(doc_id):
    """Delete a certificate/document."""
    db_conn = get_db()
    mnv = session.get('mnv')
    role = session.get('role')

    if role == AD:
        db_conn.execute("DELETE FROM TaiLieuNhanVien WHERE MaTL=?", (doc_id,))
    else:
        db_conn.execute("DELETE FROM TaiLieuNhanVien WHERE MaTL=? AND MaNV=?", (doc_id, mnv))
    db_conn.commit()
    log_activity(db_conn, 'Xóa bằng cấp / giấy tờ', f'ID: {doc_id}')
    flash('Đã xóa tài liệu.', 'ok')
    return redirect(url_for('main.me'))

# ----------------- Attendance Explanation -----------------
@main_bp.route('/me/attendance/explain', methods=['GET', 'POST'])
@roles_required(NV, QL)
def explain_attendance():
    """Submit attendance explanation for missed punches or discrepancies."""
    db_conn = get_db()
    mnv = session.get('mnv')

    if request.method == 'POST':
        ngay = request.form.get('Ngay', '').strip()
        gio_vao = request.form.get('GioVaoDeXuat', '').strip()
        gio_ra = request.form.get('GioRaDeXuat', '').strip()
        ly_do = request.form.get('LyDo', '').strip()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not ngay or not ly_do:
            flash('Vui lòng chọn ngày và ghi rõ lý do giải trình.', 'err')
        else:
            db_conn.execute("""
                INSERT INTO GiaiTrinhCong(MaNV, Ngay, GioVaoDeXuat, GioRaDeXuat, LyDo, TrangThai, NgayGui)
                VALUES(?, ?, ?, ?, ?, N'Chờ duyệt', ?)
            """, (mnv, ngay, gio_vao or '08:00', gio_ra or '17:30', ly_do, now_str))
            db_conn.commit()
            log_activity(db_conn, 'Gửi giải trình công', f'Ngày {ngay}: {ly_do}')
            flash('Đã gửi giải trình công thành công. Vui lòng chờ cấp quản lý phê duyệt.', 'ok')
            return redirect(url_for('main.me'))

    return render_template('form_explain.html')

# ----------------- Overtime Registration -----------------
@main_bp.route('/me/ot/register', methods=['GET', 'POST'])
@roles_required(NV, QL)
def register_ot():
    """Register overtime work in advance or for past work."""
    db_conn = get_db()
    mnv = session.get('mnv')

    if request.method == 'POST':
        ngay = request.form.get('Ngay', '').strip()
        so_gio = request.form.get('SoGio', '').strip()
        loai = request.form.get('Loai', 'Ngày thường').strip()
        ly_do = request.form.get('LyDo', '').strip()

        try:
            so_gio_f = float(so_gio)
            if so_gio_f <= 0 or so_gio_f > 24:
                raise ValueError
        except ValueError:
            flash('Số giờ tăng ca phải là số dương hợp lệ (từ 0.5 đến 24 giờ).', 'err')
            return render_template('form_ot.html')

        if not ngay:
            flash('Vui lòng chọn ngày tăng ca.', 'err')
        else:
            db_conn.execute("""
                INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai, TrangThai, LyDo)
                VALUES(?, ?, ?, ?, N'Chờ duyệt', ?)
            """, (mnv, so_gio_f, ngay, loai, ly_do or 'Làm thêm ngoài giờ'))
            db_conn.commit()
            log_activity(db_conn, 'Đăng ký làm thêm giờ (OT)', f'Ngày {ngay}, {so_gio_f}h')
            flash(f"Đã gửi đăng ký làm thêm {so_gio_f} giờ ngày {ngay}. Chờ quản lý phê duyệt.", 'ok')
            return redirect(url_for('main.me'))

    return render_template('form_ot.html')

# ----------------- Salary Advance Request -----------------
@main_bp.route('/me/advance/request', methods=['GET', 'POST'])
@roles_required(NV, QL)
def request_advance():
    """Submit salary advance request."""
    db_conn = get_db()
    mnv = session.get('mnv')
    current_month = date.today().strftime('%Y-%m')

    if request.method == 'POST':
        thang = request.form.get('ThangNam', current_month).strip()
        so_tien = request.form.get('SoTien', '').strip()
        ly_do = request.form.get('LyDo', '').strip()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        try:
            tien = float(so_tien)
            if tien <= 0:
                raise ValueError
        except ValueError:
            flash('Số tiền tạm ứng phải là một số dương hợp lệ.', 'err')
            return render_template('form_advance.html', current_month=current_month)

        if not ly_do:
            flash('Vui lòng ghi rõ lý do xin tạm ứng.', 'err')
        else:
            db_conn.execute("""
                INSERT INTO TamUng(MaNV, ThangNam, SoTien, LyDo, NgayYeuCau, TrangThai)
                VALUES(?, ?, ?, ?, ?, N'Chờ duyệt')
            """, (mnv, thang, tien, ly_do, now_str))
            db_conn.commit()
            log_activity(db_conn, 'Đề xuất tạm ứng lương', f'{tien:,.0f} đ cho tháng {thang}')
            flash(f"Đã gửi yêu cầu tạm ứng {tien:,.0f} VNĐ cho tháng {thang}. Đang chờ duyệt.", 'ok')
            return redirect(url_for('main.me'))

    return render_template('form_advance.html', current_month=current_month)

# ----------------- KPI Self-Assessment -----------------
@main_bp.route('/me/kpi/self-eval', methods=['GET', 'POST'])
@roles_required(NV, QL)
def self_eval_kpi():
    """Employee self-assesses KPI for current or specified month."""
    db_conn = get_db()
    mnv = session.get('mnv')
    current_month = request.args.get('thang') or date.today().strftime('%Y-%m')

    existing = db_conn.execute("SELECT * FROM DanhGia WHERE MaNV=? AND ThangNam=?", (mnv, current_month)).fetchone()

    if request.method == 'POST':
        diem_tu = request.form.get('DiemTuDanhGia', '').strip()
        nhan_xet = request.form.get('NhanXetCaNhan', '').strip()

        try:
            score = float(diem_tu)
            if not (0 <= score <= 100):
                raise ValueError
        except ValueError:
            flash('Điểm tự đánh giá phải là số từ 0 đến 100.', 'err')
            return render_template('form_kpi_self.html', current_month=current_month, existing=existing)

        if existing:
            db_conn.execute("""
                UPDATE DanhGia
                SET DiemTuDanhGia=?, NhanXetCaNhan=?
                WHERE MaDG=?
            """, (score, nhan_xet, existing['MaDG']))
        else:
            db_conn.execute("""
                INSERT INTO DanhGia(MaNV, ThangNam, DiemTuDanhGia, NhanXetCaNhan, DiemKPI, XepLoai, NhanXet, NguoiDanhGia)
                VALUES(?, ?, ?, ?, ?, N'Chờ đánh giá', N'Nhân viên đã tự đánh giá', N'Chưa duyệt')
            """, (mnv, current_month, score, nhan_xet, score))

        db_conn.commit()
        log_activity(db_conn, 'Tự đánh giá KPI', f'Tháng {current_month}: {score} điểm')
        flash(f'Tự đánh giá KPI tháng {current_month} thành công ({score} điểm)!', 'ok')
        return redirect(url_for('main.me'))

    return render_template('form_kpi_self.html', current_month=current_month, existing=existing)

# ----------------- Training Catalog & Registration -----------------
@main_bp.route('/training')
@login_required
def training_view():
    """Browse corporate training courses and enroll."""
    db_conn = get_db()
    mnv = session.get('mnv')
    role = session.get('role')

    courses = db_conn.execute("""
        SELECT k.*, (SELECT COUNT(*) FROM DangKyDaoTao d WHERE d.MaKDT=k.MaKDT) AS SoNguoiDK,
               (SELECT 1 FROM DangKyDaoTao d WHERE d.MaKDT=k.MaKDT AND d.MaNV=?) AS DaDangKy
        FROM KhoaDaoTao k
        ORDER BY k.MaKDT DESC
    """, (mnv or '',)).fetchall()

    my_courses = []
    if mnv:
        my_courses = db_conn.execute("""
            SELECT d.*, k.TenKhoa, k.GiangVien, k.ThoiGian, k.DiaDiem, k.TrangThai AS TrangThaiKhoa
            FROM DangKyDaoTao d
            JOIN KhoaDaoTao k ON d.MaKDT=k.MaKDT
            WHERE d.MaNV=?
            ORDER BY d.NgayDangKy DESC
        """, (mnv,)).fetchall()

    return render_template('training.html', courses=courses, my_courses=my_courses)

@main_bp.route('/training/register/<int:kid>', methods=['POST'])
@roles_required(NV, QL)
def register_course(kid):
    """Enroll in a training course."""
    db_conn = get_db()
    mnv = session.get('mnv')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    course = db_conn.execute("SELECT * FROM KhoaDaoTao WHERE MaKDT=?", (kid)).fetchone()
    if not course:
        abort(404)

    already = db_conn.execute("SELECT 1 FROM DangKyDaoTao WHERE MaKDT=? AND MaNV=?", (kid, mnv)).fetchone()
    if already:
        flash(f"Bạn đã đăng ký khóa học '{course['TenKhoa']}' trước đó rồi.", 'w')
    else:
        db_conn.execute("""
            INSERT INTO DangKyDaoTao(MaKDT, MaNV, NgayDangKy, TrangThai)
            VALUES(?, ?, ?, N'Đã đăng ký')
        """, (kid, mnv, now_str))
        db_conn.commit()
        log_activity(db_conn, 'Đăng ký đào tạo', f"Khóa: {course['TenKhoa']}")
        flash(f"Đăng ký thành công khóa đào tạo: '{course['TenKhoa']}'!", 'ok')

    return redirect(url_for('main.training_view'))

# ----------------- Suggestions & Complaints -----------------
@main_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback_view():
    """Employee submits proposals or complaints; management views and responds."""
    db_conn = get_db()
    mnv = session.get('mnv')
    role = session.get('role')

    if request.method == 'POST':
        tieu_de = request.form.get('TieuDe', '').strip()
        loai = request.form.get('Loai', 'Đề xuất cải tiến').strip()
        noi_dung = request.form.get('NoiDung', '').strip()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not tieu_de or not noi_dung:
            flash('Vui lòng nhập đầy đủ tiêu đề và nội dung ý kiến.', 'err')
        else:
            db_conn.execute("""
                INSERT INTO DeXuatKhieuNai(MaNV, TieuDe, Loai, NoiDung, NgayGui, TrangThai)
                VALUES(?, ?, ?, ?, ?, N'Chờ xử lý')
            """, (mnv, tieu_de, loai, noi_dung, now_str))
            db_conn.commit()
            log_activity(db_conn, f'Gửi {loai}', tieu_de)
            flash('Ý kiến của bạn đã được gửi thành công đến ban quản trị!', 'ok')
            return redirect(url_for('main.feedback_view'))

    if role == AD:
        feedbacks = db_conn.execute("""
            SELECT x.*, n.HoTen, c.TenCV, p.TenPB
            FROM DeXuatKhieuNai x""" + EMP_JOIN + """
            ORDER BY x.NgayGui DESC
        """).fetchall()
    elif role == QL:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        mapb = emp['MaPB'] if emp else None
        feedbacks = db_conn.execute("""
            SELECT x.*, n.HoTen, c.TenCV, p.TenPB
            FROM DeXuatKhieuNai x""" + EMP_JOIN + """
            WHERE p.MaPB=? OR x.MaNV=?
            ORDER BY x.NgayGui DESC
        """, (mapb, mnv)).fetchall()
    else:
        feedbacks = db_conn.execute("""
            SELECT x.*, n.HoTen, c.TenCV, p.TenPB
            FROM DeXuatKhieuNai x""" + EMP_JOIN + """
            WHERE x.MaNV=?
            ORDER BY x.NgayGui DESC
        """, (mnv,)).fetchall()

    return render_template('feedback.html', feedbacks=feedbacks)

# ----------------- Manager Approvals Center -----------------
@main_bp.route('/manager/approvals')
@roles_required(QL, AD)
def manager_approvals():
    """Unified approval hub for Managers & HR to review Leaves, OT, Explanations, and Advances."""
    db_conn = get_db()
    role = session.get('role')
    mnv = session.get('mnv')

    mapb = None
    if role == QL:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        mapb = emp['MaPB'] if emp else None

    # Leaves pending
    leave_sql = "SELECT x.*, n.HoTen, c.TenCV, p.TenPB, (DATEDIFF(day, CAST(x.NgayBD AS DATE), CAST(x.NgayKT AS DATE)) + 1) AS SoNgay FROM NghiPhep x" + EMP_JOIN + " WHERE x.TrangThai=N'Chờ duyệt'"
    ot_sql = "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM TangCa x" + EMP_JOIN + " WHERE x.TrangThai=N'Chờ duyệt'"
    explain_sql = "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM GiaiTrinhCong x" + EMP_JOIN + " WHERE x.TrangThai=N'Chờ duyệt'"
    advance_sql = "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM TamUng x" + EMP_JOIN + " WHERE x.TrangThai=N'Chờ duyệt'"

    if role == QL and mapb:
        leave_sql += " AND p.MaPB=?"
        ot_sql += " AND p.MaPB=?"
        explain_sql += " AND p.MaPB=?"
        advance_sql += " AND p.MaPB=?"
        leaves = db_conn.execute(leave_sql, (mapb,)).fetchall()
        ots = db_conn.execute(ot_sql, (mapb,)).fetchall()
        explains = db_conn.execute(explain_sql, (mapb,)).fetchall()
        advances = db_conn.execute(advance_sql, (mapb,)).fetchall()
    else:
        leaves = db_conn.execute(leave_sql).fetchall()
        ots = db_conn.execute(ot_sql).fetchall()
        explains = db_conn.execute(explain_sql).fetchall()
        advances = db_conn.execute(advance_sql).fetchall()

    return render_template(
        'approvals.html',
        leaves=leaves,
        ots=ots,
        explains=explains,
        advances=advances
    )

@main_bp.route('/manager/approve/ot/<int:otid>', methods=['POST'])
@roles_required(QL, AD)
def approve_ot(otid):
    """Manager approves overtime work request."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("UPDATE TangCa SET TrangThai=N'Đã duyệt', NguoiDuyet=? WHERE MaTC=?", (approver, otid))
    db_conn.commit()
    log_activity(db_conn, 'Phê duyệt Tăng ca (OT)', f'Mã TC: {otid}')
    flash('Đã phê duyệt đăng ký tăng ca thành công.', 'ok')
    return redirect(request.referrer or url_for('main.manager_approvals'))

@main_bp.route('/manager/reject/ot/<int:otid>', methods=['POST'])
@roles_required(QL, AD)
def reject_ot(otid):
    """Manager rejects overtime work request."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("UPDATE TangCa SET TrangThai=N'Từ chối', NguoiDuyet=? WHERE MaTC=?", (approver, otid))
    db_conn.commit()
    log_activity(db_conn, 'Từ chối Tăng ca (OT)', f'Mã TC: {otid}')
    flash('Đã từ chối đăng ký tăng ca.', 'w')
    return redirect(request.referrer or url_for('main.manager_approvals'))

@main_bp.route('/manager/approve/explain/<int:gtid>', methods=['POST'])
@roles_required(QL, AD)
def approve_explain(gtid):
    """Manager approves attendance explanation and updates ChamCong."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    gt = db_conn.execute("SELECT * FROM GiaiTrinhCong WHERE MaGT=?", (gtid,)).fetchone()
    if not gt:
        abort(404)

    db_conn.execute("UPDATE GiaiTrinhCong SET TrangThai=N'Đã duyệt', NguoiDuyet=? WHERE MaGT=?", (approver, gtid))

    # Update or insert ChamCong record
    existing = db_conn.execute("SELECT MaCC FROM ChamCong WHERE MaNV=? AND Ngay=?", (gt['MaNV'], gt['Ngay'])).fetchone()
    if existing:
        db_conn.execute("""
            UPDATE ChamCong
            SET GioVao=?, GioRa=?, TrangThai=N'Đúng giờ', GhiChu=N'Đã duyệt giải trình công'
            WHERE MaCC=?
        """, (gt['GioVaoDeXuat'] or '08:00', gt['GioRaDeXuat'] or '17:30', existing['MaCC']))
    else:
        db_conn.execute("""
            INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu)
            VALUES(?, ?, ?, ?, N'Đúng giờ', N'Đã duyệt giải trình công')
        """, (gt['MaNV'], gt['Ngay'], gt['GioVaoDeXuat'] or '08:00', gt['GioRaDeXuat'] or '17:30'))

    db_conn.commit()
    log_activity(db_conn, 'Phê duyệt giải trình công', f"Mã GT: {gtid}, NV: {gt['MaNV']}")
    flash(f"Đã duyệt giải trình công ngày {gt['Ngay']} cho nhân viên {gt['MaNV']}. Dữ liệu công đã được cập nhật!", 'ok')
    return redirect(request.referrer or url_for('main.manager_approvals'))

@main_bp.route('/manager/reject/explain/<int:gtid>', methods=['POST'])
@roles_required(QL, AD)
def reject_explain(gtid):
    """Manager rejects attendance explanation."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("UPDATE GiaiTrinhCong SET TrangThai=N'Từ chối', NguoiDuyet=? WHERE MaGT=?", (approver, gtid))
    db_conn.commit()
    log_activity(db_conn, 'Từ chối giải trình công', f'Mã GT: {gtid}')
    flash('Đã từ chối đơn giải trình công.', 'w')
    return redirect(request.referrer or url_for('main.manager_approvals'))

@main_bp.route('/manager/approve/advance/<int:tuid>', methods=['POST'])
@roles_required(QL, AD)
def approve_advance(tuid):
    """Manager approves salary advance request."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    tu = db_conn.execute("SELECT * FROM TamUng WHERE MaTU=?", (tuid,)).fetchone()
    if not tu:
        abort(404)

    db_conn.execute("UPDATE TamUng SET TrangThai=N'Đã duyệt', NguoiDuyet=? WHERE MaTU=?", (approver, tuid))

    # Add to Luong table for the given month if exists
    sal = db_conn.execute("SELECT MaLuong, LuongUngTruoc FROM Luong WHERE MaNV=? AND ThangNam=?", (tu['MaNV'], tu['ThangNam'])).fetchone()
    if sal:
        db_conn.execute("UPDATE Luong SET LuongUngTruoc=LuongUngTruoc+? WHERE MaLuong=?", (tu['SoTien'], sal['MaLuong']))

    db_conn.commit()
    log_activity(db_conn, 'Phê duyệt tạm ứng lương', f"Mã TU: {tuid}, Số tiền: {tu['SoTien']:,.0f}")
    flash(f"Đã phê duyệt tạm ứng {tu['SoTien']:,.0f} VNĐ cho nhân viên {tu['MaNV']}.", 'ok')
    return redirect(request.referrer or url_for('main.manager_approvals'))

@main_bp.route('/manager/reject/advance/<int:tuid>', methods=['POST'])
@roles_required(QL, AD)
def reject_advance(tuid):
    """Manager rejects salary advance request."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("UPDATE TamUng SET TrangThai=N'Từ chối', NguoiDuyet=? WHERE MaTU=?", (approver, tuid))
    db_conn.commit()
    log_activity(db_conn, 'Từ chối tạm ứng lương', f'Mã TU: {tuid}')
    flash('Đã từ chối đơn xin tạm ứng lương.', 'w')
    return redirect(request.referrer or url_for('main.manager_approvals'))

# ----------------- HR Proposals (Manager submits, Admin approves) -----------------
@main_bp.route('/manager/proposals', methods=['GET', 'POST'])
@roles_required(QL, AD)
def manager_proposals():
    """Manager creates HR proposal (raise, promotion, reward, transfer, termination) to HR/Admin."""
    db_conn = get_db()
    mnv = session.get('mnv')
    role = session.get('role')

    if request.method == 'POST':
        target_nv = request.form.get('MaNV', '').strip()
        loai = request.form.get('LoaiDeXuat', 'Tăng lương').strip()
        muc = request.form.get('MucDeXuat', '').strip()
        ly_do = request.form.get('LyDo', '').strip()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not target_nv or not ly_do:
            flash('Vui lòng chọn nhân viên và nhập lý do đề xuất.', 'err')
        else:
            db_conn.execute("""
                INSERT INTO DeXuatNhanSu(MaNV, NguoiDeXuat, LoaiDeXuat, MucDeXuat, LyDo, NgayDeXuat, TrangThai)
                VALUES(?, ?, ?, ?, ?, ?, N'Chờ HR phê duyệt')
            """, (target_nv, mnv or 'admin', loai, muc or None, ly_do, now_str))
            db_conn.commit()
            log_activity(db_conn, f'Tạo đề xuất nhân sự: {loai}', f'Đối tượng: {target_nv}')
            flash(f"Đã gửi đề xuất '{loai}' cho nhân viên {target_nv} đến phòng HR/Admin!", 'ok')
            return redirect(url_for('main.manager_proposals'))

    # Load proposals
    if role == AD:
        proposals = db_conn.execute("""
            SELECT x.*, n.HoTen, c.TenCV, p.TenPB, q.HoTen AS TenNguoiDeXuat
            FROM DeXuatNhanSu x""" + EMP_JOIN + """
            LEFT JOIN NhanVien q ON x.NguoiDeXuat=q.MaNV
            ORDER BY x.NgayDeXuat DESC
        """).fetchall()
    else:
        proposals = db_conn.execute("""
            SELECT x.*, n.HoTen, c.TenCV, p.TenPB, q.HoTen AS TenNguoiDeXuat
            FROM DeXuatNhanSu x""" + EMP_JOIN + """
            LEFT JOIN NhanVien q ON x.NguoiDeXuat=q.MaNV
            WHERE x.NguoiDeXuat=?
            ORDER BY x.NgayDeXuat DESC
        """, (mnv,)).fetchall()

    # Load employee list for select option
    if role == QL:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        mapb = emp['MaPB'] if emp else None
        staff = db_conn.execute(NV_SEL + " WHERE p.MaPB=?", (mapb,)).fetchall()
    else:
        staff = db_conn.execute(NV_SEL).fetchall()

    return render_template('proposals.html', proposals=proposals, staff=staff)

@main_bp.route('/admin/proposals/approve/<int:pid>', methods=['POST'])
@roles_required(AD)
def admin_approve_proposal(pid):
    """Admin approves HR proposal and automatically applies changes."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    p = db_conn.execute("SELECT * FROM DeXuatNhanSu WHERE MaDXNS=?", (pid,)).fetchone()
    if not p:
        abort(404)

    db_conn.execute("""
        UPDATE DeXuatNhanSu
        SET TrangThai=N'Đã phê duyệt', NguoiPheDuyet=?, YKienPheDuyet=N'Đồng ý với đề xuất'
        WHERE MaDXNS=?
    """, (approver, pid))

    # Apply changes according to proposal type
    loai = p['LoaiDeXuat']
    target_nv = p['MaNV']
    muc = p['MucDeXuat'] or ''

    if loai == 'Khen thưởng':
        now_date = date.today().strftime('%Y-%m-%d')
        so_qd = f"QĐ-KT/{date.today().strftime('%Y%m')}-{pid}"
        db_conn.execute("""
            INSERT INTO KhenThuongKyLuat(MaNV, Loai, SoQuyetDinh, NgayQuyetDinh, HinhThuc, SoTien, LyDo, NguoiKy)
            VALUES(?, N'Khen thưởng', ?, ?, ?, 1000000, ?, ?)
        """, (target_nv, so_qd, now_date, muc or 'Khen thưởng thành tích xuất sắc', p['LyDo'], approver))
    elif loai == 'Kỷ luật':
        now_date = date.today().strftime('%Y-%m-%d')
        so_qd = f"QĐ-KL/{date.today().strftime('%Y%m')}-{pid}"
        db_conn.execute("""
            INSERT INTO KhenThuongKyLuat(MaNV, Loai, SoQuyetDinh, NgayQuyetDinh, HinhThuc, SoTien, LyDo, NguoiKy)
            VALUES(?, N'Kỷ luật', ?, ?, ?, 0, ?, ?)
        """, (target_nv, so_qd, now_date, muc or 'Khiển trách', p['LyDo'], approver))

    db_conn.commit()
    log_activity(db_conn, 'Admin phê duyệt đề xuất nhân sự', f"Mã ĐX: {pid}, Loại: {loai}")
    flash(f"Đã phê duyệt đề xuất '{loai}' cho nhân viên {target_nv}!", 'ok')
    return redirect(url_for('main.manager_proposals'))

@main_bp.route('/admin/proposals/reject/<int:pid>', methods=['POST'])
@roles_required(AD)
def admin_reject_proposal(pid):
    """Admin rejects HR proposal."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("""
        UPDATE DeXuatNhanSu
        SET TrangThai=N'Từ chối', NguoiPheDuyet=?, YKienPheDuyet=N'Chưa phù hợp với định hướng hiện tại'
        WHERE MaDXNS=?
    """, (approver, pid))
    db_conn.commit()
    log_activity(db_conn, 'Admin từ chối đề xuất nhân sự', f"Mã ĐX: {pid}")
    flash('Đã từ chối đề xuất nhân sự.', 'w')
    return redirect(url_for('main.manager_proposals'))

# ----------------- Monthly Attendance Closing -----------------
@main_bp.route('/admin/attendance/close', methods=['POST'])
@roles_required(AD)
def attendance_close():
    """Admin closes attendance for the month to freeze attendance records."""
    db_conn = get_db()
    current_month = request.form.get('thang') or date.today().strftime('%Y-%m')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    approver = session.get('name') or 'Admin'

    total_records = db_conn.execute(
        "SELECT COUNT(*) FROM ChamCong WHERE SUBSTRING(Ngay, 1, 7)=? AND TrangThai IN (N'Đúng giờ', N'Đi muộn', N'Về sớm')",
        (current_month,)
    ).fetchone()[0]

    existing = db_conn.execute("SELECT * FROM ChotCong WHERE ThangNam=?", (current_month,)).fetchone()
    if existing:
        db_conn.execute("""
            UPDATE ChotCong
            SET NgayChot=?, NguoiChot=?, TongSoCong=?, GhiChu=N'Cập nhật chốt công'
            WHERE MaCC_Thang=?
        """, (now_str, approver, float(total_records), existing['MaCC_Thang']))
    else:
        db_conn.execute("""
            INSERT INTO ChotCong(ThangNam, NgayChot, NguoiChot, TongSoCong, GhiChu)
            VALUES(?, ?, ?, ?, N'Đã chốt công tháng hoàn tất')
        """, (current_month, now_str, approver, float(total_records)))

    db_conn.commit()
    log_activity(db_conn, f'Chốt công tháng {current_month}', f'Tổng ngày công: {total_records}')
    flash(f"Đã chốt công tháng {current_month} thành công với tổng cộng {total_records} lượt công!", 'ok')
    return redirect(request.referrer or url_for('main.payroll_calc_view'))

# ----------------- Automatic Batch Payroll Calculator -----------------
@main_bp.route('/admin/payroll/calculate', methods=['GET', 'POST'])
@roles_required(AD)
def payroll_calc_view():
    """Batch compute and update payroll records based on attendance, OT, contracts, taxes, and insurance."""
    db_conn = get_db()
    current_month = request.args.get('thang') or date.today().strftime('%Y-%m')

    if request.method == 'POST':
        target_month = request.form.get('thang') or current_month
        employees = db_conn.execute("""
            SELECT n.MaNV, n.HoTen,
                   COALESCE((SELECT TOP 1 LuongCoBan FROM HopDong WHERE MaNV=n.MaNV ORDER BY CASE WHEN TrangThai=N'Hiệu lực' THEN 0 ELSE 1 END, NgayBD DESC), 12000000) AS LuongCoBan
            FROM NhanVien n
        """).fetchall()

        computed_count = 0
        for e in employees:
            mnv = e['MaNV']
            # Mức lương cứng chuẩn xác theo Hợp đồng lao động, không bị chia nhỏ làm sai số
            luong_cung = float(e['LuongCoBan'] or 12000000)

            # Count actual working days in month
            work_days = db_conn.execute(
                "SELECT COUNT(*) FROM ChamCong WHERE MaNV=? AND SUBSTRING(Ngay, 1, 7)=? AND TrangThai IN (N'Đúng giờ', N'Đi muộn', N'Về sớm')",
                (mnv, target_month)
            ).fetchone()[0]

            # Count approved OT hours in month
            ot_hours = db_conn.execute(
                "SELECT COALESCE(SUM(SoGio), 0) FROM TangCa WHERE MaNV=? AND SUBSTRING(Ngay, 1, 7)=? AND TrangThai=N'Đã duyệt'",
                (mnv, target_month)
            ).fetchone()[0]

            # Sum approved advances in month
            advances = db_conn.execute(
                "SELECT COALESCE(SUM(SoTien), 0) FROM TamUng WHERE MaNV=? AND ThangNam=? AND TrangThai=N'Đã duyệt'",
                (mnv, target_month)
            ).fetchone()[0]

            # Lương OT tính trên mức lương cứng: (LuongCung / (22 ngày * 8h)) * 1.5
            ot_pay = round(ot_hours * (luong_cung / 176.0) * 1.5, 0)
            bonus = 1000000
            allowance = 500000
            # Trích nộp BHXH/BHYT/BHTN bắt buộc: 10.5% mức lương cứng
            insurance = round(luong_cung * 0.105, 0)
            taxable = max(0, luong_cung + bonus + allowance + ot_pay - insurance - 11000000)
            tax = round(taxable * 0.05, 0)

            # Check if payroll record already exists
            existing_sal = db_conn.execute("SELECT MaLuong FROM Luong WHERE MaNV=? AND ThangNam=?", (mnv, target_month)).fetchone()
            if existing_sal:
                db_conn.execute("""
                    UPDATE Luong
                    SET LuongCung=?, LuongThuong=?, PhuCap=?, LuongUngTruoc=?, BaoHiem=?, ThueTNCN=?, KhauTruKhac=?
                    WHERE MaLuong=?
                """, (luong_cung, bonus + ot_pay, allowance, advances, insurance, tax, 0, existing_sal['MaLuong']))
            else:
                db_conn.execute("""
                    INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, PhuCap, LuongUngTruoc, BaoHiem, ThueTNCN, KhauTruKhac)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (mnv, target_month, luong_cung, bonus + ot_pay, allowance, advances, insurance, tax, 0))

            computed_count += 1

        db_conn.commit()
        log_activity(db_conn, f'Tính bảng lương tự động tháng {target_month}', f'Đã tính cho {computed_count} nhân viên')
        flash(f"Đã hoàn thành tính bảng lương tháng {target_month} tự động cho {computed_count} nhân viên!", 'ok')
        return redirect(url_for('main.payroll_calc_view', thang=target_month))

    # Fetch existing payroll records for current_month
    salaries = db_conn.execute("""
        SELECT x.*, n.HoTen, c.TenCV, p.TenPB,
               (x.LuongCung + x.LuongThuong + x.PhuCap - x.LuongUngTruoc - COALESCE(x.BaoHiem,0) - COALESCE(x.ThueTNCN,0) - COALESCE(x.KhauTruKhac,0)) AS ThucLinh
        FROM Luong x""" + EMP_JOIN + """
        WHERE x.ThangNam=?
        ORDER BY x.MaNV
    """, (current_month,)).fetchall()

    close_record = db_conn.execute("SELECT * FROM ChotCong WHERE ThangNam=?", (current_month,)).fetchone()

    total_payout = sum(s['ThucLinh'] for s in salaries) if salaries else 0
    total_insurance = sum(s['BaoHiem'] or 0 for s in salaries) if salaries else 0
    total_tax = sum(s['ThueTNCN'] or 0 for s in salaries) if salaries else 0

    return render_template(
        'payroll_calc.html',
        salaries=salaries,
        current_month=current_month,
        close_record=close_record,
        total_payout=total_payout,
        total_insurance=total_insurance,
        total_tax=total_tax
    )

# ----------------- System Audit Log -----------------
@main_bp.route('/audit-log')
@roles_required(AD)
def audit_log_view():
    """View system audit and activity log."""
    db_conn = get_db()
    logs = db_conn.execute("SELECT TOP 200 * FROM NhatKyHoatDong ORDER BY MaNK DESC").fetchall()
    return render_template('audit_log.html', logs=logs)

# ----------------- HR Analytics & Salary Cost Reports -----------------
@main_bp.route('/reports/analytics')
@roles_required(QL, AD)
def analytics_view():
    """Advanced HR Analytics: Headcount, turnover, payroll costs by department."""
    db_conn = get_db()
    current_month = request.args.get('thang') or date.today().strftime('%Y-%m')

    # Headcount by department
    dept_stats = db_conn.execute("""
        SELECT p.TenPB, COUNT(n.MaNV) AS SoLuong,
               SUM(CASE WHEN n.GioiTinh=N'Nam' THEN 1 ELSE 0 END) AS Nam,
               SUM(CASE WHEN n.GioiTinh=N'Nữ' THEN 1 ELSE 0 END) AS Nu
        FROM PhongBan p
        LEFT JOIN ChucVu c ON p.MaPB=c.MaPB
        LEFT JOIN NhanVien n ON c.MaCV=n.MaCV
        GROUP BY p.TenPB
    """).fetchall()

    # Payroll costs by department
    payroll_dept = db_conn.execute("""
        SELECT p.TenPB,
               COALESCE(SUM(l.LuongCung), 0) AS TongLuongCung,
               COALESCE(SUM(l.LuongThuong + l.PhuCap), 0) AS TongThuongPhuCap,
               COALESCE(SUM(l.BaoHiem), 0) AS TongBaoHiem,
               COALESCE(SUM(l.LuongCung + l.LuongThuong + l.PhuCap - l.LuongUngTruoc - COALESCE(l.BaoHiem,0) - COALESCE(l.ThueTNCN,0)), 0) AS TongChiPhi
        FROM PhongBan p
        LEFT JOIN ChucVu c ON p.MaPB=c.MaPB
        LEFT JOIN NhanVien n ON c.MaCV=n.MaCV
        LEFT JOIN Luong l ON n.MaNV=l.MaNV AND l.ThangNam=?
        GROUP BY p.TenPB
    """, (current_month,)).fetchall()

    total_payroll = sum(r['TongChiPhi'] for r in payroll_dept)

    # Export analytics
    if request.args.get('export') == '1':
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, lineterminator='\r\n')
        writer.writerow([f'BÁO CÁO PHÂN TÍCH NHÂN SỰ & CHI PHÍ LƯƠNG - THÁNG {current_month}'])
        writer.writerow([])
        writer.writerow(['1. CƠ CẤU NHÂN SỰ THEO PHÒNG BAN'])
        writer.writerow(['Phòng ban', 'Tổng nhân sự', 'Nam', 'Nữ'])
        for d in dept_stats:
            writer.writerow([d['TenPB'], d['SoLuong'], d['Nam'], d['Nu']])
        writer.writerow([])
        writer.writerow(['2. CHI PHÍ LƯƠNG THEO PHÒNG BAN'])
        writer.writerow(['Phòng ban', 'Lương cơ bản', 'Thưởng & Phụ cấp', 'Bảo hiểm doanh nghiệp', 'Tổng chi phí thực lĩnh'])
        for p in payroll_dept:
            writer.writerow([p['TenPB'], p['TongLuongCung'], p['TongThuongPhuCap'], p['TongBaoHiem'], p['TongChiPhi']])
        writer.writerow(['TỔNG CỘNG', '', '', '', total_payroll])

        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="bao_cao_chi_phi_luong_{current_month}.csv"'}
        )

    return render_template(
        'analytics.html',
        dept_stats=dept_stats,
        payroll_dept=payroll_dept,
        total_payroll=total_payroll,
        current_month=current_month
    )

# ----------------- Profile Edit & Announcements -----------------
@main_bp.route('/me/profile/edit', methods=['GET', 'POST'])
@roles_required(NV, QL)
def edit_profile():
    """Allow employee to update their personal contact information."""
    db_conn = get_db()
    mnv = session.get('mnv')
    emp = db_conn.execute("SELECT * FROM NhanVien WHERE MaNV=?", (mnv,)).fetchone()
    if not emp:
        abort(404)

    if request.method == 'POST':
        sdt = request.form.get('SDT', '').strip()
        email = request.form.get('Email', '').strip()
        dia_chi = request.form.get('DiaChi', '').strip()
        ngay_sinh = request.form.get('NgaySinh', '').strip()
        gioi_tinh = request.form.get('GioiTinh', '').strip()
        trinh_do = request.form.get('TrinhDo', '').strip()
        chuyen_mon = request.form.get('ChuyenMon', '').strip()
        hinh_anh = request.form.get('HinhAnh', '').strip() or emp['HinhAnh']

        errs = []
        # Handle avatar file upload
        file = request.files.get('HinhAnh_file')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if ext in ('jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'):
                filename = f"avatar_{mnv}_{int(time.time())}.{ext}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                hinh_anh = f"/static/uploads/avatars/{filename}"
            else:
                errs.append('Định dạng ảnh không hợp lệ (hỗ trợ JPG, PNG, WEBP, GIF, SVG).')

        if sdt and not re.fullmatch(r'0\d{8,10}', sdt):
            errs.append('Số điện thoại không hợp lệ (cần bắt đầu bằng số 0, từ 9-11 số).')
        if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            errs.append('Email không đúng định dạng.')
        if ngay_sinh:
            try:
                datetime.strptime(ngay_sinh, '%Y-%m-%d')
            except ValueError:
                errs.append('Ngày sinh không hợp lệ.')

        if errs:
            for e in errs:
                flash(e, 'err')
        else:
            db_conn.execute("""
                UPDATE NhanVien
                SET SDT=?, Email=?, DiaChi=?, NgaySinh=?, GioiTinh=?, TrinhDo=?, ChuyenMon=?, HinhAnh=?
                WHERE MaNV=?
            """, (sdt or None, email or None, dia_chi or None, ngay_sinh or None, gioi_tinh or None, trinh_do or None, chuyen_mon or None, hinh_anh or None, mnv))
            db_conn.commit()
            log_activity(db_conn, 'Cập nhật hồ sơ cá nhân', f'Nhân viên: {mnv}')
            flash('Cập nhật thông tin cá nhân thành công.', 'ok')
            return redirect(url_for('main.me'))

    return render_template('profile_edit.html', emp=emp)

@main_bp.route('/nhanvien/<mnv>/avatar', methods=['POST'])
@login_required
def update_employee_avatar(mnv):
    """Update employee avatar via file upload or image URL (from Employee List modal)."""
    db_conn = get_db()
    current_role = session.get('role')
    user_mnv = session.get('mnv')

    # Authorization: Admin, Manager, or Employee updating their own avatar
    if current_role not in (AD, QL) and user_mnv != mnv:
        abort(403)

    emp = db_conn.execute("SELECT * FROM NhanVien WHERE MaNV=?", (mnv,)).fetchone()
    if not emp:
        abort(404)

    avatar_url = request.form.get('avatar_url', '').strip()
    file = request.files.get('avatar_file')

    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext in ('jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'):
            filename = f"avatar_{mnv}_{int(time.time())}.{ext}"
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            avatar_url = f"/static/uploads/avatars/{filename}"
        else:
            flash('Định dạng ảnh không hợp lệ (hỗ trợ JPG, PNG, WEBP, GIF, SVG).', 'err')
            return redirect(request.referrer or url_for('modules.mlist', mod='nhanvien'))

    if avatar_url:
        db_conn.execute("UPDATE NhanVien SET HinhAnh=? WHERE MaNV=?", (avatar_url, mnv))
        db_conn.commit()
        log_activity(db_conn, 'Cập nhật ảnh đại diện nhân viên', f'Mã NV: {mnv}')
        flash(f"Đã cập nhật ảnh đại diện cho nhân viên {emp['HoTen']} ({mnv}) thành công!", 'ok')
    else:
        flash('Vui lòng chọn tệp ảnh hoặc nhập đường dẫn ảnh hợp lệ.', 'warn')

    return redirect(request.referrer or url_for('modules.mlist', mod='nhanvien'))

@main_bp.route('/announcements')
@login_required
def announcements():
    """View announcements for employees, managers, and admin."""
    db_conn = get_db()
    role = session.get('role')
    mnv = session.get('mnv')

    if role == AD:
        rows = db_conn.execute("""
            SELECT x.*, p.TenPB
            FROM ThongBao x
            LEFT JOIN PhongBan p ON x.MaPB=p.MaPB
            ORDER BY x.NgayGui DESC
        """).fetchall()
    else:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        mapb = emp['MaPB'] if emp else None

        rows = db_conn.execute("""
            SELECT x.*, p.TenPB
            FROM ThongBao x
            LEFT JOIN PhongBan p ON x.MaPB=p.MaPB
            WHERE x.PhamVi=N'Toàn công ty' OR (x.PhamVi=N'Theo phòng ban' AND x.MaPB=?)
            ORDER BY x.NgayGui DESC
        """, (mapb,)).fetchall()

    return render_template('announcements.html', rows=rows)

@main_bp.route('/me/leave/request', methods=['GET', 'POST'])
@roles_required(NV, QL)
def leave_request():
    """Allow employee to request a new leave of absence."""
    db_conn = get_db()
    mnv = session.get('mnv')

    if request.method == 'POST':
        ngay_bd = request.form.get('NgayBD', '').strip()
        ngay_kt = request.form.get('NgayKT', '').strip()
        ly_do = request.form.get('LyDo', '').strip()

        errs = []
        if not ngay_bd or not ngay_kt:
            errs.append('Vui lòng chọn ngày bắt đầu và ngày kết thúc.')
        elif ngay_kt < ngay_bd:
            errs.append('Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.')

        if not errs:
            overlap = db_conn.execute(
                "SELECT 1 FROM NghiPhep WHERE MaNV=? AND TrangThai!=N'Từ chối' AND NOT (NgayKT < ? OR NgayBD > ?)",
                (mnv, ngay_bd, ngay_kt)
            ).fetchone()
            if overlap:
                errs.append('Bạn đã có đơn nghỉ phép trong khoảng thời gian này.')

        if errs:
            for e in errs:
                flash(e, 'err')
        else:
            db_conn.execute(
                "INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, LyDo, TrangThai) VALUES(?, ?, ?, ?, N'Chờ duyệt')",
                (mnv, ngay_bd, ngay_kt, ly_do)
            )
            db_conn.commit()
            log_activity(db_conn, 'Tạo đơn xin nghỉ phép', f'Từ {ngay_bd} đến {ngay_kt}')
            flash('Gửi đơn xin nghỉ phép thành công. Vui lòng chờ quản lý duyệt.', 'ok')
            return redirect(url_for('main.me'))

    return render_template('leave_request.html')

@main_bp.route('/me/leave/<int:lid>/cancel', methods=['POST'])
@roles_required(NV, QL)
def leave_cancel(lid):
    """Allow employee to cancel their pending leave request."""
    db_conn = get_db()
    mnv = session.get('mnv')

    leave = db_conn.execute("SELECT * FROM NghiPhep WHERE MaNP=? AND MaNV=?", (lid, mnv)).fetchone()
    if not leave:
        abort(404)

    if leave['TrangThai'] != 'Chờ duyệt':
        flash('Chỉ có thể hủy đơn nghỉ phép đang ở trạng thái Chờ duyệt.', 'err')
    else:
        db_conn.execute("DELETE FROM NghiPhep WHERE MaNP=?", (lid,))
        db_conn.commit()
        log_activity(db_conn, 'Hủy đơn nghỉ phép', f'Mã NP: {lid}')
        flash('Đã hủy đơn xin nghỉ phép.', 'ok')

    return redirect(url_for('main.me'))

@main_bp.route('/report/leave')
@roles_required(QL, AD)
def report_leave():
    """Monthly leave report and details summary."""
    thang = request.args.get('thang') or date.today().strftime('%Y-%m')
    db_conn = get_db()

    rows = db_conn.execute("""
        SELECT n.MaNV, n.HoTen, c.TenCV, p.TenPB, COUNT(*) AS Lan,
               SUM(DATEDIFF(day, CAST(x.NgayBD AS DATE), CAST(x.NgayKT AS DATE)) + 1) AS Ngay
        FROM NghiPhep x""" + EMP_JOIN + """
        WHERE SUBSTRING(x.NgayBD,1,7)=? AND x.TrangThai=N'Đã duyệt'
        GROUP BY n.MaNV, n.HoTen, c.TenCV, p.TenPB
        ORDER BY Ngay DESC
    """, (thang,)).fetchall()

    details = db_conn.execute(
        "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM NghiPhep x" + EMP_JOIN + " WHERE SUBSTRING(x.NgayBD,1,7)=? ORDER BY x.NgayBD",
        (thang,)
    ).fetchall()

    if request.args.get('export') == '1':
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, lineterminator='\r\n')
        writer.writerow([f'BÁO CÁO NGHỈ PHÉP THÁNG {thang}'])
        writer.writerow([])
        writer.writerow(['1. TỔNG HỢP THEO NHÂN VIÊN'])
        writer.writerow(['Mã NV', 'Họ tên', 'Chức vụ', 'Phòng ban', 'Số lần nghỉ', 'Tổng số ngày nghỉ'])
        for r in rows:
            writer.writerow([r['MaNV'], r['HoTen'], r['TenCV'], r['TenPB'], r['Lan'], r['Ngay']])

        writer.writerow([])
        writer.writerow(['2. CHI TIẾT TỪNG LẦN NGHỈ'])
        writer.writerow(['Họ tên', 'Chức vụ', 'Phòng ban', 'Từ ngày', 'Đến ngày', 'Lý do', 'Trạng thái'])
        for d in details:
            writer.writerow([d['HoTen'], d['TenCV'], d['TenPB'], d['NgayBD'], d['NgayKT'], d.get('LyDo') or '', d.get('TrangThai') or ''])

        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="bao_cao_nghi_phep_{thang}.csv"'}
        )

    return render_template('report.html', rows=rows, det=details, thang=thang)

@main_bp.route('/report/hr')
@roles_required(QL, AD)
def report_hr():
    """Department / Company HR analytics and reporting."""
    db_conn = get_db()
    role = session.get('role')
    mnv = session.get('mnv')
    current_month = request.args.get('thang') or date.today().strftime('%Y-%m')

    departments = db_conn.execute("SELECT * FROM PhongBan ORDER BY MaPB").fetchall()

    selected_dept = request.args.get('dept', '')
    if role == QL:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        selected_dept = emp['MaPB'] if emp else ''

    staff_sql = NV_SEL
    dept_params = ()
    if selected_dept:
        staff_sql += " WHERE p.MaPB = ?"
        dept_params = (selected_dept,)
    staff_sql += " ORDER BY n.MaNV"
    staff = db_conn.execute(staff_sql, dept_params).fetchall()

    total_staff = len(staff)
    male_count = sum(1 for s in staff if s.get('GioiTinh') == 'Nam')
    female_count = sum(1 for s in staff if s.get('GioiTinh') == 'Nữ')

    cc_sql = """
        SELECT COUNT(*)
        FROM ChamCong x
        JOIN NhanVien n ON x.MaNV=n.MaNV
        LEFT JOIN ChucVu c ON n.MaCV=c.MaCV
        LEFT JOIN PhongBan p ON c.MaPB=p.MaPB
        WHERE SUBSTRING(x.Ngay, 1, 7)=? AND x.TrangThai IN (N'Đúng giờ', N'Đi muộn', N'Về sớm')
    """
    if selected_dept:
        cc_sql += " AND p.MaPB=?"
        total_working_days = db_conn.execute(cc_sql, (current_month, selected_dept)).fetchone()[0]
    else:
        total_working_days = db_conn.execute(cc_sql, (current_month,)).fetchone()[0]

    tc_sql = """
        SELECT COALESCE(SUM(x.SoGio), 0)
        FROM TangCa x
        JOIN NhanVien n ON x.MaNV=n.MaNV
        LEFT JOIN ChucVu c ON n.MaCV=c.MaCV
        LEFT JOIN PhongBan p ON c.MaPB=p.MaPB
        WHERE SUBSTRING(x.Ngay, 1, 7)=?
    """
    if selected_dept:
        tc_sql += " AND p.MaPB=?"
        total_ot = db_conn.execute(tc_sql, (current_month, selected_dept)).fetchone()[0]
    else:
        total_ot = db_conn.execute(tc_sql, (current_month,)).fetchone()[0]

    np_sql = """
        SELECT COALESCE(SUM(DATEDIFF(day, CAST(x.NgayBD AS DATE), CAST(x.NgayKT AS DATE)) + 1), 0)
        FROM NghiPhep x
        JOIN NhanVien n ON x.MaNV=n.MaNV
        LEFT JOIN ChucVu c ON n.MaCV=c.MaCV
        LEFT JOIN PhongBan p ON c.MaPB=p.MaPB
        WHERE SUBSTRING(x.NgayBD, 1, 7)=? AND x.TrangThai=N'Đã duyệt'
    """
    if selected_dept:
        np_sql += " AND p.MaPB=?"
        total_leave_days = db_conn.execute(np_sql, (current_month, selected_dept)).fetchone()[0]
    else:
        total_leave_days = db_conn.execute(np_sql, (current_month,)).fetchone()[0]

    kpi_sql = """
        SELECT COALESCE(AVG(x.DiemKPI), 0)
        FROM DanhGia x
        JOIN NhanVien n ON x.MaNV=n.MaNV
        LEFT JOIN ChucVu c ON n.MaCV=c.MaCV
        LEFT JOIN PhongBan p ON c.MaPB=p.MaPB
        WHERE x.ThangNam=?
    """
    if selected_dept:
        kpi_sql += " AND p.MaPB=?"
        avg_kpi = db_conn.execute(kpi_sql, (current_month, selected_dept)).fetchone()[0]
    else:
        avg_kpi = db_conn.execute(kpi_sql, (current_month,)).fetchone()[0]

    if request.args.get('export') == '1':
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, lineterminator='\r\n')
        dept_name = next((d['TenPB'] for d in departments if d['MaPB'] == selected_dept), 'Toàn công ty')
        writer.writerow([f'BÁO CÁO NHÂN SỰ: {dept_name.upper()} - THÁNG {current_month}'])
        writer.writerow([])
        writer.writerow(['1. CÁC CHỈ SỐ TỔNG HỢP'])
        writer.writerow(['Chỉ số', 'Giá trị'])
        writer.writerow(['Tổng số nhân sự', total_staff])
        writer.writerow(['Nhân sự Nam', male_count])
        writer.writerow(['Nhân sự Nữ', female_count])
        writer.writerow(['Tổng ngày công trong tháng', total_working_days])
        writer.writerow(['Tổng giờ tăng ca', total_ot])
        writer.writerow(['Số ngày nghỉ phép đã duyệt', total_leave_days])
        writer.writerow(['Điểm KPI trung bình', f"{avg_kpi:.1f}"])
        writer.writerow([])
        writer.writerow(['2. DANH SÁCH NHÂN SỰ'])
        writer.writerow(['Mã NV', 'Họ tên', 'Giới tính', 'Chức vụ', 'Phòng ban', 'Số điện thoại', 'Email', 'Ngày vào công ty'])
        for s in staff:
            writer.writerow([s['MaNV'], s['HoTen'], s.get('GioiTinh') or '', s.get('TenCV') or '', s.get('TenPB') or '', s.get('SDT') or '', s.get('Email') or '', s.get('NgayVaoCT') or ''])

        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="bao_cao_nhan_su_{selected_dept or "toan_cty"}_{current_month}.csv"'}
        )

    return render_template(
        'report_hr.html',
        staff=staff,
        departments=departments,
        selected_dept=selected_dept,
        current_month=current_month,
        total_staff=total_staff,
        male_count=male_count,
        female_count=female_count,
        total_working_days=total_working_days,
        total_ot=total_ot,
        total_leave_days=total_leave_days,
        avg_kpi=avg_kpi
    )

@main_bp.route('/attendance/quick-checkin', methods=['POST'])
@roles_required(QL, AD)
def quick_checkin():
    """Quickly record on-time check-in for employees today who haven't checked in yet."""
    db_conn = get_db()
    today_str = date.today().strftime('%Y-%m-%d')
    role = session.get('role')
    mnv = session.get('mnv')

    if role == QL:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        mapb = emp['MaPB'] if emp else None
        employees = db_conn.execute(NV_SEL + " WHERE p.MaPB=?", (mapb,)).fetchall()
    else:
        employees = db_conn.execute("SELECT MaNV FROM NhanVien").fetchall()

    checked_count = 0
    for e in employees:
        emp_id = e['MaNV']
        exists = db_conn.execute("SELECT 1 FROM ChamCong WHERE MaNV=? AND Ngay=?", (emp_id, today_str)).fetchone()
        if not exists:
            db_conn.execute(
                "INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu) VALUES(?, ?, '08:00', '17:30', N'Đúng giờ', N'Chấm công tự động')",
                (emp_id, today_str)
            )
            checked_count += 1

    db_conn.commit()
    log_activity(db_conn, 'Ghi nhận chấm công nhanh', f'{checked_count} nhân viên')
    flash(f"Đã ghi nhận chấm công nhanh ngày {today_str} cho {checked_count} nhân viên.", 'ok')
    return redirect(url_for('modules.mlist', mod='chamcong'))

@main_bp.route('/admin/backup')
@roles_required(AD)
def backup_view():
    """Admin database backup and data management center."""
    db_conn = get_db()
    tables = [
        ('NhanVien', 'Nhân viên'),
        ('PhongBan', 'Phòng ban'),
        ('ChucVu', 'Chức vụ'),
        ('HopDong', 'Hợp đồng lao động'),
        ('Luong', 'Bảng lương'),
        ('NghiPhep', 'Nghỉ phép'),
        ('TangCa', 'Tăng ca'),
        ('ChamCong', 'Chấm công'),
        ('DanhGia', 'Đánh giá KPI'),
        ('TaiLieuNhanVien', 'Bằng cấp & Giấy tờ'),
        ('GiaiTrinhCong', 'Giải trình chấm công'),
        ('KhenThuongKyLuat', 'Khen thưởng & Kỷ luật'),
        ('KhoaDaoTao', 'Khóa đào tạo'),
        ('DeXuatKhieuNai', 'Đề xuất & Khiếu nại'),
        ('TamUng', 'Tạm ứng lương'),
        ('PhanCa', 'Phân ca làm việc'),
        ('DeXuatNhanSu', 'Đề xuất nhân sự'),
        ('YeuCauTuyenDung', 'Yêu cầu tuyển dụng'),
        ('UngVien', 'Ứng viên phỏng vấn'),
        ('QuyTrinhNhanSu', 'Onboarding / Offboarding'),
        ('NhatKyHoatDong', 'Nhật ký hoạt động'),
        ('ChotCong', 'Chốt công tháng'),
        ('ThongBao', 'Thông báo'),
        ('TaiKhoan', 'Tài khoản người dùng'),
        ('TaiKhoanAdmin', 'Tài khoản Admin'),
    ]

    table_stats = []
    total_records = 0
    for tbl, lbl in tables:
        cnt = db_conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        table_stats.append((tbl, lbl, cnt))
        total_records += cnt

    return render_template(
        'backup.html',
        table_stats=table_stats,
        total_records=total_records,
        database_name=MSSQL_DATABASE,
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@main_bp.route('/admin/backup/export')
@roles_required(AD)
def backup_export():
    """Export complete database contents to structured JSON archive."""
    db_conn = get_db()
    tables = [
        'PhongBan', 'ChucVu', 'NhanVien', 'HopDong', 'Luong',
        'NghiPhep', 'TangCa', 'ChamCong', 'DanhGia', 'TaiLieuNhanVien',
        'GiaiTrinhCong', 'KhenThuongKyLuat', 'KhoaDaoTao', 'DangKyDaoTao',
        'DeXuatKhieuNai', 'TamUng', 'PhanCa', 'DeXuatNhanSu', 'YeuCauTuyenDung',
        'UngVien', 'QuyTrinhNhanSu', 'NhatKyHoatDong', 'ChotCong', 'ThongBao',
        'TaiKhoan', 'TaiKhoanAdmin'
    ]

    backup_data = {
        'database': MSSQL_DATABASE,
        'exported_at': datetime.now().isoformat(),
        'system': 'Quản lý nhân sự - Nhóm 9',
        'tables': {}
    }

    for tbl in tables:
        rows = db_conn.execute(f"SELECT * FROM {tbl}").fetchall()
        cols = [col[0] for col in db_conn.execute(f"SELECT TOP 1 * FROM {tbl}").description] if rows else []
        table_records = []
        for r in rows:
            record = {}
            for col in cols:
                record[col] = r.get(col)
            table_records.append(record)
        backup_data['tables'][tbl] = table_records

    json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
    filename = f"backup_{MSSQL_DATABASE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_activity(db_conn, 'Sao lưu CSDL (JSON)', filename)
    return Response(
        json_str,
        mimetype='application/json; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@main_bp.route('/admin/backup/sql')
@roles_required(AD)
def backup_sql():
    """Export complete database as an executable SQL script."""
    db_conn = get_db()
    tables = [
        'PhongBan', 'ChucVu', 'NhanVien', 'HopDong', 'Luong',
        'NghiPhep', 'TangCa', 'ChamCong', 'DanhGia', 'TaiLieuNhanVien',
        'GiaiTrinhCong', 'KhenThuongKyLuat', 'KhoaDaoTao', 'DangKyDaoTao',
        'DeXuatKhieuNai', 'TamUng', 'PhanCa', 'DeXuatNhanSu', 'YeuCauTuyenDung',
        'UngVien', 'QuyTrinhNhanSu', 'NhatKyHoatDong', 'ChotCong', 'ThongBao',
        'TaiKhoan', 'TaiKhoanAdmin'
    ]

    output = io.StringIO()
    output.write(f"-- BẢN SAO LƯU CƠ SỞ DỮ LIỆU {MSSQL_DATABASE}\n")
    output.write(f"-- Thời gian sao lưu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for tbl in tables:
        rows = db_conn.execute(f"SELECT * FROM {tbl}").fetchall()
        if not rows:
            continue

        cols = [col[0] for col in db_conn.execute(f"SELECT TOP 1 * FROM {tbl}").description]
        output.write(f"-- Bảng {tbl} ({len(rows)} bản ghi)\n")
        cols_str = ', '.join(f'[{c}]' for c in cols)

        for r in rows:
            vals = []
            for c in cols:
                v = r.get(c)
                if v is None:
                    vals.append('NULL')
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                else:
                    escaped = str(v).replace("'", "''")
                    vals.append(f"N'{escaped}'")
            vals_str = ', '.join(vals)
            output.write(f"INSERT INTO [{tbl}]({cols_str}) VALUES({vals_str});\n")
        output.write("\n")

    filename = f"backup_{MSSQL_DATABASE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    log_activity(db_conn, 'Sao lưu CSDL (SQL)', filename)
    return Response(
        output.getvalue(),
        mimetype='text/plain; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
