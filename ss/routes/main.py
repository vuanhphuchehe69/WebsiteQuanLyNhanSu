"""Main application routes: Dashboard, Personal Information, and Reports."""
from datetime import date
from flask import Blueprint, session, redirect, url_for, render_template, request
from config import NV, QL, AD, NV_SEL, EMP_JOIN
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
    query_scalar = lambda query: db_conn.execute(query).fetchone()[0]
    current_month = date.today().strftime('%Y-%m')

    stats = [
        ('Nhân viên', query_scalar('SELECT COUNT(*) FROM NhanVien'), 'users'),
        ('Hợp đồng hiệu lực', query_scalar("SELECT COUNT(*) FROM HopDong WHERE TrangThai='Hiệu lực'"), 'file-text'),
        ('Phòng ban', query_scalar('SELECT COUNT(*) FROM PhongBan'), 'building'),
        ('Chức vụ', query_scalar('SELECT COUNT(*) FROM ChucVu'), 'briefcase'),
        (f'Lượt nghỉ phép tháng {current_month}', query_scalar(f"SELECT COUNT(*) FROM NghiPhep WHERE SUBSTRING(NgayBD,1,7)='{current_month}'"), 'calendar'),
        (f'Giờ tăng ca tháng {current_month}', query_scalar(f"SELECT COALESCE(SUM(SoGio),0) FROM TangCa WHERE SUBSTRING(Ngay,1,7)='{current_month}'"), 'clock')
    ]

    if session.get('role') == AD:
        stats.append(('Tài khoản', query_scalar('SELECT COUNT(*) FROM TaiKhoan'), 'key'))

    return render_template('dash.html', stats=stats)

@main_bp.route('/me')
@roles_required(NV, QL)
def me():
    """Personal view for employees and managers to see profile, salary, leaves, and overtime."""
    db_conn = get_db()
    mnv = session.get('mnv')

    emp = db_conn.execute(NV_SEL + ' WHERE n.MaNV=?', (mnv,)).fetchone()
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

    return render_template('me.html', emp=emp, L=salaries, P=leaves, T=overtimes, HD=contracts)

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
        WHERE SUBSTRING(x.NgayBD,1,7)=?
        GROUP BY n.MaNV, n.HoTen, c.TenCV, p.TenPB
        ORDER BY Ngay DESC
    """, (thang,)).fetchall()

    details = db_conn.execute(
        "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM NghiPhep x" + EMP_JOIN + " WHERE SUBSTRING(x.NgayBD,1,7)=? ORDER BY x.NgayBD",
        (thang,)
    ).fetchall()

    return render_template('report.html', rows=rows, det=details, thang=thang)

