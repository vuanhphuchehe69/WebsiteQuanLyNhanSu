"""Module CRUD routes: Generic list, create, update, delete, pagination, and export for all entities."""
import io
import csv
from datetime import datetime, date
from flask import Blueprint, request, session, redirect, url_for, flash, render_template, abort, Response
from database import get_db, IntegrityError
from config import QL, AD
from utils import login_required, roles_required, get_module, get_form_options, parse_form_data, log_activity

modules_bp = Blueprint('modules', __name__)

@modules_bp.route('/m/<mod>')
@login_required
def mlist(mod):
    """Generic list view with search, month filter, status filter, sorting, and pagination."""
    module_config = get_module(mod)
    q = request.args.get('q', '').strip()
    thang = request.args.get('thang', '').strip()
    status = request.args.get('status', '').strip()
    sort = request.args.get('sort')
    desc = request.args.get('d') == '1'
    page = max(1, request.args.get('page', 1, type=int))
    per_page = 10

    sql = module_config['sel']
    where_clauses = []
    args = []

    if q:
        search_expr = ' OR '.join(f'CAST({c} AS NVARCHAR(MAX)) LIKE ?' for c in module_config['search'])
        where_clauses.append(f'({search_expr})')
        args += [f'%{q}%'] * len(module_config['search'])

    if thang and module_config.get('date'):
        where_clauses.append(f"SUBSTRING({module_config['date']},1,7)=?")
        args.append(thang)

    if status and any(c[0] == 'TrangThai' for c in module_config['cols']):
        where_clauses.append("x.TrangThai=?")
        args.append(status)

    if where_clauses:
        sql += ' WHERE ' + ' AND '.join(where_clauses)

    valid_columns = [col[0] for col in module_config['cols']]
    if sort in valid_columns:
        order_by = f'[{sort}] {"DESC" if desc else "ASC"}'
    else:
        order_by = module_config['order']

    db_conn = get_db()

    # Count total matching rows for pagination
    count_sql = f"SELECT COUNT(*) FROM ({sql}) AS _sub"
    total_records = db_conn.execute(count_sql, list(args)).fetchone()[0]
    total_pages = max(1, (total_records + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    is_mssql = getattr(db_conn, 'is_mssql', False)
    offset = (page - 1) * per_page
    if is_mssql:
        paged_sql = f"{sql} ORDER BY {order_by} OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY"
    else:
        paged_sql = f"{sql} ORDER BY {order_by} LIMIT {per_page} OFFSET {offset}"

    rows = db_conn.execute(paged_sql, args).fetchall()

    return render_template(
        'list.html',
        m=module_config,
        mod=mod,
        rows=rows,
        q=q,
        thang=thang,
        status=status,
        sort=sort,
        desc=desc,
        page=page,
        total_pages=total_pages,
        total_records=total_records,
        per_page=per_page
    )

@modules_bp.route('/m/<mod>/export')
@login_required
def mexport(mod):
    """Export filtered list data to Excel-compatible CSV with UTF-8 BOM."""
    module_config = get_module(mod)
    q = request.args.get('q', '').strip()
    thang = request.args.get('thang', '').strip()
    status = request.args.get('status', '').strip()
    sort = request.args.get('sort')
    desc = request.args.get('d') == '1'

    sql = module_config['sel']
    where_clauses = []
    args = []

    if q:
        search_expr = ' OR '.join(f'CAST({c} AS NVARCHAR(MAX)) LIKE ?' for c in module_config['search'])
        where_clauses.append(f'({search_expr})')
        args += [f'%{q}%'] * len(module_config['search'])

    if thang and module_config.get('date'):
        where_clauses.append(f"SUBSTRING({module_config['date']},1,7)=?")
        args.append(thang)

    if status and any(c[0] == 'TrangThai' for c in module_config['cols']):
        where_clauses.append("x.TrangThai=?")
        args.append(status)

    if where_clauses:
        sql += ' WHERE ' + ' AND '.join(where_clauses)

    valid_columns = [col[0] for col in module_config['cols']]
    if sort in valid_columns:
        order_by = f'[{sort}] {"DESC" if desc else "ASC"}'
    else:
        order_by = module_config['order']

    db_conn = get_db()
    rows = db_conn.execute(f"{sql} ORDER BY {order_by}", args).fetchall()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, lineterminator='\r\n')

    # Header row
    headers = [col_label for _, col_label in module_config['cols']]
    writer.writerow(headers)

    # Data rows
    for r in rows:
        row_vals = []
        for col_name, _ in module_config['cols']:
            val = r.get(col_name)
            if val is None:
                row_vals.append('')
            elif isinstance(val, (int, float)):
                row_vals.append(val)
            else:
                row_vals.append(str(val))
        writer.writerow(row_vals)

    filename = f"{mod}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    log_activity(db_conn, f"Xuất Excel/CSV phân hệ {module_config['title']}", f"File: {filename}")
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@modules_bp.route('/m/nghiphep/<int:lid>/approve', methods=['POST'])
@roles_required(QL, AD)
def approve_leave(lid):
    """Approve employee leave request."""
    db_conn = get_db()
    db_conn.execute("UPDATE NghiPhep SET TrangThai=N'Đã duyệt' WHERE MaNP=?", (lid,))
    db_conn.commit()
    log_activity(db_conn, 'Duyệt đơn nghỉ phép', f'Mã NP: {lid}')
    flash('Đã duyệt đơn nghỉ phép thành công.', 'ok')
    return redirect(url_for('modules.mlist', mod='nghiphep'))

@modules_bp.route('/m/nghiphep/<int:lid>/reject', methods=['POST'])
@roles_required(QL, AD)
def reject_leave(lid):
    """Reject employee leave request."""
    db_conn = get_db()
    db_conn.execute("UPDATE NghiPhep SET TrangThai=N'Từ chối' WHERE MaNP=?", (lid,))
    db_conn.commit()
    log_activity(db_conn, 'Từ chối đơn nghỉ phép', f'Mã NP: {lid}')
    flash('Đã từ chối đơn nghỉ phép.', 'ok')
    return redirect(url_for('modules.mlist', mod='nghiphep'))

@modules_bp.route('/m/tangca/<int:tid>/approve', methods=['POST'])
@roles_required(QL, AD)
def approve_ot(tid):
    """Approve employee overtime request."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("UPDATE TangCa SET TrangThai=N'Đã duyệt', NguoiDuyet=? WHERE MaTC=?", (approver, tid))
    db_conn.commit()
    log_activity(db_conn, 'Duyệt đăng ký tăng ca', f'Mã TC: {tid}')
    flash('Đã duyệt đăng ký tăng ca thành công.', 'ok')
    return redirect(url_for('modules.mlist', mod='tangca'))

@modules_bp.route('/m/tangca/<int:tid>/reject', methods=['POST'])
@roles_required(QL, AD)
def reject_ot(tid):
    """Reject employee overtime request."""
    db_conn = get_db()
    approver = session.get('name') or session.get('user')
    db_conn.execute("UPDATE TangCa SET TrangThai=N'Từ chối', NguoiDuyet=? WHERE MaTC=?", (approver, tid))
    db_conn.commit()
    log_activity(db_conn, 'Từ chối đăng ký tăng ca', f'Mã TC: {tid}')
    flash('Đã từ chối đăng ký tăng ca.', 'ok')
    return redirect(url_for('modules.mlist', mod='tangca'))

@modules_bp.route('/m/<mod>/new', methods=['GET', 'POST'])
@login_required
def mnew(mod):
    """Generic create view."""
    module_config = get_module(mod)
    row = {}
    db_conn = get_db()

    if request.method == 'POST':
        vals, errs = parse_form_data(module_config, request.form, editing=False)
        row = request.form

        if not errs:
            try:
                col_names = ','.join(vals.keys())
                placeholders = ','.join('?' * len(vals))
                db_conn.execute(
                    f"INSERT INTO {module_config['table']}({col_names}) VALUES({placeholders})",
                    list(vals.values())
                )
                db_conn.commit()
                log_activity(db_conn, f"Tạo mới {module_config['title']}", str(vals))
                flash('Thêm mới thành công.', 'ok')
                return redirect(url_for('modules.mlist', mod=mod))
            except IntegrityError:
                errs.append('Dữ liệu bị trùng (mã, tên đăng nhập, CCCD, tháng lương...) hoặc tham chiếu không hợp lệ.')

        for e in errs:
            flash(e, 'err')

    options = get_form_options(db_conn)
    return render_template('form.html', m=module_config, mod=mod, row=row, opts=options, editing=False)

@modules_bp.route('/m/<mod>/<rid>/edit', methods=['GET', 'POST'])
@login_required
def medit(mod, rid):
    """Generic edit view."""
    module_config = get_module(mod)
    db_conn = get_db()
    row = db_conn.execute(f"SELECT * FROM {module_config['table']} WHERE {module_config['pk']}=?", (rid,)).fetchone()
    if not row:
        abort(404)

    if request.method == 'POST':
        vals, errs = parse_form_data(module_config, request.form, editing=True)
        if not errs:
            try:
                if vals:
                    set_expr = ','.join(f'{k}=?' for k in vals.keys())
                    db_conn.execute(
                        f"UPDATE {module_config['table']} SET {set_expr} WHERE {module_config['pk']}=?",
                        list(vals.values()) + [rid]
                    )
                db_conn.commit()
                log_activity(db_conn, f"Cập nhật {module_config['title']}", f"ID: {rid}")
                flash('Cập nhật thành công.', 'ok')
                return redirect(url_for('modules.mlist', mod=mod))
            except IntegrityError:
                errs.append('Dữ liệu bị trùng hoặc tham chiếu không hợp lệ.')

        for e in errs:
            flash(e, 'err')
        row = request.form

    options = get_form_options(db_conn)
    return render_template('form.html', m=module_config, mod=mod, row=row, opts=options, editing=True, rid=rid)

@modules_bp.route('/m/<mod>/<rid>/delete', methods=['POST'])
@login_required
def mdel(mod, rid):
    """Generic delete view."""
    module_config = get_module(mod)
    db_conn = get_db()

    if mod == 'nhanvien' and rid == session.get('mnv'):
        flash('Không thể xóa chính tài khoản đang đăng nhập.', 'err')
    else:
        try:
            db_conn.execute(f"DELETE FROM {module_config['table']} WHERE {module_config['pk']}=?", (rid,))
            db_conn.commit()
            log_activity(db_conn, f"Xóa bản ghi {module_config['title']}", f"ID: {rid}")
            flash('Đã xóa.', 'ok')
        except IntegrityError:
            flash('Không thể xóa vì dữ liệu đang được sử dụng (ví dụ phòng ban còn chức vụ, chức vụ còn nhân viên).', 'err')

    return redirect(url_for('modules.mlist', mod=mod))
