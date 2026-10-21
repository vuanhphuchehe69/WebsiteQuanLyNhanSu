"""Module CRUD routes: Generic list, create, update, and delete for all entities."""
from flask import Blueprint, request, session, redirect, url_for, flash, render_template, abort
from database import get_db, IntegrityError
from utils import login_required, get_module, get_form_options, parse_form_data

modules_bp = Blueprint('modules', __name__)

@modules_bp.route('/m/<mod>')
@login_required
def mlist(mod):
    """Generic list view with search, month filter, and sorting."""
    module_config = get_module(mod)
    q = request.args.get('q', '').strip()
    thang = request.args.get('thang', '').strip()
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

    if where_clauses:
        sql += ' WHERE ' + ' AND '.join(where_clauses)

    valid_columns = [col[0] for col in module_config['cols']]
    if sort in valid_columns:
        sql += f' ORDER BY [{sort}] {"DESC" if desc else "ASC"}'
    else:
        sql += ' ORDER BY ' + module_config['order']

    db_conn = get_db()
    rows = db_conn.execute(sql, args).fetchall()

    return render_template(
        'list.html',
        m=module_config,
        mod=mod,
        rows=rows,
        q=q,
        thang=thang,
        sort=sort,
        desc=desc
    )

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
            flash('Đã xóa.', 'ok')
        except IntegrityError:
            flash('Không thể xóa vì dữ liệu đang được sử dụng (ví dụ phòng ban còn chức vụ, chức vụ còn nhân viên).', 'err')

    return redirect(url_for('modules.mlist', mod=mod))

