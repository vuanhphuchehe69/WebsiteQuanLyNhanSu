"""Authentication routes: Login, Logout, Change Password."""
import secrets
from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from config import NV, QL, AD
from database import get_db
from utils import login_required, log_activity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user authentication for all roles."""
    if request.method == 'POST':
        role = request.form.get('role')
        user = request.form.get('user', '').strip()
        pw = request.form.get('pw', '')
        db_conn = get_db()

        if role == AD:
            row = db_conn.execute("SELECT * FROM TaiKhoan WHERE TenDN=? AND LoaiTK='Admin'", (user,)).fetchone() or \
                  db_conn.execute('SELECT * FROM TaiKhoanAdmin WHERE TenDN=?', (user,)).fetchone()
        elif role in (NV, QL):
            row = db_conn.execute('SELECT * FROM TaiKhoan WHERE TenDN=? AND LoaiTK=?', (user, role)).fetchone()
        else:
            row = None

        password_matched = False
        if row:
            db_pw = row['MatKhau']
            if db_pw == pw:
                password_matched = True
            elif str(db_pw).startswith(('scrypt:', 'pbkdf2:')) and check_password_hash(db_pw, pw):
                password_matched = True

        if password_matched:
            session.clear()
            session['_csrf'] = secrets.token_hex(16)
            session.update(
                uid=row['MaTK'],
                role=role,
                mnv=row['MaNV'] if role != AD else None,
                name=user
            )
            if role != AD:
                emp = db_conn.execute('SELECT HoTen FROM NhanVien WHERE MaNV=?', (row['MaNV'],)).fetchone()
                session['name'] = emp['HoTen'] if emp else user

            log_activity(db_conn, 'Đăng nhập hệ thống', f'Tài khoản: {user} ({role})')
            return redirect(url_for('main.me') if role == NV else url_for('main.dash'))

        flash('Sai tên đăng nhập, mật khẩu hoặc loại tài khoản.', 'err')

    return render_template('login.html', sel=request.form.get('role', NV))

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Log out user and clear current session."""
    db_conn = get_db()
    log_activity(db_conn, 'Đăng xuất hệ thống', f"Người dùng: {session.get('name')}")
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/password', methods=['GET', 'POST'])
@login_required
def change_pw():
    """Allow logged in user to change their password."""
    if request.method == 'POST':
        old = request.form.get('old', '')
        new = request.form.get('new', '')
        cf = request.form.get('cf', '')
        db_conn = get_db()
        table = 'TaiKhoanAdmin' if session['role'] == AD else 'TaiKhoan'
        row = db_conn.execute(f'SELECT MatKhau FROM {table} WHERE MaTK=?', (session['uid'],)).fetchone()

        old_matched = False
        if row:
            db_pw = row['MatKhau']
            if db_pw == old:
                old_matched = True
            elif str(db_pw).startswith(('scrypt:', 'pbkdf2:')) and check_password_hash(db_pw, old):
                old_matched = True

        if not old_matched:
            flash('Mật khẩu hiện tại không đúng.', 'err')
        elif len(new) < 6:
            flash('Mật khẩu mới phải từ 6 ký tự.', 'err')
        elif new != cf:
            flash('Xác nhận mật khẩu không khớp.', 'err')
        else:
            db_conn.execute(
                f'UPDATE {table} SET MatKhau=? WHERE MaTK=?',
                (new, session['uid'])
            )
            db_conn.commit()
            log_activity(db_conn, 'Đổi mật khẩu', f"Tài khoản ID: {session['uid']}")
            flash('Đổi mật khẩu thành công.', 'ok')
            return redirect(url_for('auth.change_pw'))

    return render_template('password.html')
