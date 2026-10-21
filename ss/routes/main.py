"""Main application routes: Dashboard, Personal Information, and Reports."""
import io
import csv
from datetime import date
from flask import Blueprint, session, redirect, url_for, render_template, request, flash, abort, Response
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
    query_scalar = lambda query, args=None: db_conn.execute(query, args or ()).fetchone()[0]
    current_month = date.today().strftime('%Y-%m')

    stats = [
        ('Nhân viên', query_scalar('SELECT COUNT(*) FROM NhanVien'), 'users'),
        ('Hợp đồng hiệu lực', query_scalar("SELECT COUNT(*) FROM HopDong WHERE TrangThai=N'Hiệu lực'"), 'file-text'),
        ('Phòng ban', query_scalar('SELECT COUNT(*) FROM PhongBan'), 'building'),
        ('Chức vụ', query_scalar('SELECT COUNT(*) FROM ChucVu'), 'briefcase'),
        ('Đơn nghỉ chờ duyệt', query_scalar("SELECT COUNT(*) FROM NghiPhep WHERE TrangThai=N'Chờ duyệt'"), 'calendar'),
        (f'Giờ tăng ca tháng {current_month}', query_scalar("SELECT COALESCE(SUM(SoGio),0) FROM TangCa WHERE SUBSTRING(Ngay,1,7)=?", (current_month,)), 'clock')
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
