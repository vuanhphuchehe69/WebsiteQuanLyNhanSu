"""Main application routes: Dashboard, Personal Information, Announcements, Reports, and Admin Backup."""
import io
import csv
import json
import re
from datetime import date, datetime
from flask import Blueprint, session, redirect, url_for, render_template, request, flash, abort, Response
from config import NV, QL, AD, NV_SEL, EMP_JOIN, MSSQL_DATABASE
from database import get_db
from utils import login_required, roles_required

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

    stats = [
        ('Nhân viên', query_scalar('SELECT COUNT(*) FROM NhanVien'), 'users'),
        ('Hợp đồng hiệu lực', query_scalar("SELECT COUNT(*) FROM HopDong WHERE TrangThai=N'Hiệu lực'"), 'file-text'),
        ('Phòng ban', query_scalar('SELECT COUNT(*) FROM PhongBan'), 'building'),
        ('Chức vụ', query_scalar('SELECT COUNT(*) FROM ChucVu'), 'briefcase'),
        ('Đơn nghỉ chờ duyệt', query_scalar("SELECT COUNT(*) FROM NghiPhep WHERE TrangThai=N'Chờ duyệt'"), 'calendar'),
        (f'Giờ tăng ca tháng {current_month}', query_scalar("SELECT COALESCE(SUM(SoGio),0) FROM TangCa WHERE SUBSTRING(Ngay,1,7)=?", (current_month,)), 'clock'),
        (f'Chấm công hôm nay ({today_str})', query_scalar("SELECT COUNT(*) FROM ChamCong WHERE Ngay=?", (today_str,)), 'check-square'),
        ('Thông báo', query_scalar('SELECT COUNT(*) FROM ThongBao'), 'bell'),
    ]

    if session.get('role') == AD:
        stats.append(('Tài khoản', query_scalar('SELECT COUNT(*) FROM TaiKhoan'), 'key'))

    return render_template('dash.html', stats=stats)

@main_bp.route('/me')
@roles_required(NV, QL)
def me():
    """Personal view for employees and managers to see profile, job info, salary, leaves, attendance, and overtime."""
    db_conn = get_db()
    mnv = session.get('mnv')
    current_month = date.today().strftime('%Y-%m')

    emp = db_conn.execute(NV_SEL + ' WHERE n.MaNV=?', (mnv,)).fetchone()
    if not emp:
        abort(404)

    salaries = db_conn.execute(
        'SELECT *, (LuongCung+LuongThuong+PhuCap-LuongUngTruoc) AS ThucLinh FROM Luong WHERE MaNV=? ORDER BY ThangNam DESC',
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
        manager=manager,
        working_days=working_days,
        current_month=current_month
    )

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

        errs = []
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
                SET SDT=?, Email=?, DiaChi=?, NgaySinh=?, GioiTinh=?
                WHERE MaNV=?
            """, (sdt or None, email or None, dia_chi or None, ngay_sinh or None, gioi_tinh or None, mnv))
            db_conn.commit()
            flash('Cập nhật thông tin cá nhân thành công.', 'ok')
            return redirect(url_for('main.me'))

    return render_template('profile_edit.html', emp=emp)

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
        # Get employee department
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
            # Check overlap with existing non-rejected leaves
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

    # Get department list for admin
    departments = db_conn.execute("SELECT * FROM PhongBan ORDER BY MaPB").fetchall()

    # Determine department filter
    selected_dept = request.args.get('dept', '')
    if role == QL:
        emp = db_conn.execute("SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?", (mnv,)).fetchone()
        selected_dept = emp['MaPB'] if emp else ''

    where_dept = " WHERE p.MaPB = ?" if selected_dept else ""
    dept_params = (selected_dept,) if selected_dept else ()

    # 1. Staff roster in department / company
    staff_sql = NV_SEL
    if selected_dept:
        staff_sql += " WHERE p.MaPB = ?"
    staff_sql += " ORDER BY n.MaNV"
    staff = db_conn.execute(staff_sql, dept_params).fetchall()

    # 2. Key metrics
    total_staff = len(staff)
    male_count = sum(1 for s in staff if s.get('GioiTinh') == 'Nam')
    female_count = sum(1 for s in staff if s.get('GioiTinh') == 'Nữ')

    # Attendance days in month
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

    # Overtime hours in month
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

    # Approved leave days in month
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

    # Average KPI
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

    # Export CSV report
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

    # Fetch active employees
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
        'NghiPhep', 'TangCa', 'ChamCong', 'DanhGia', 'ThongBao',
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
                val = r.get(col)
                record[col] = val
            table_records.append(record)
        backup_data['tables'][tbl] = table_records

    json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
    filename = f"backup_{MSSQL_DATABASE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
        'NghiPhep', 'TangCa', 'ChamCong', 'DanhGia', 'ThongBao',
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
    return Response(
        output.getvalue(),
        mimetype='text/plain; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
