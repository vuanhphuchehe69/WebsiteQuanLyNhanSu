import sys
import secrets
from flask import Flask, session, render_template, url_for
from markupsafe import Markup
from jinja2 import BaseLoader

TEMPLATE_ALIASES = {
    'analytics.html': 'BaoCaoPhanTich.html',
    'BaoCaoPhanTich.html': 'analytics.html',
    'profile_edit.html': 'CapNhatThongTin.html',
    'CapNhatThongTin.html': 'profile_edit.html',
    'feedback.html': 'DexuatKhieunai.html',
    'DexuatKhieunai.html': 'feedback.html',
    'form_advance.html': 'Đonxinungluong.html',
    'Đonxinungluong.html': 'form_advance.html',
    'Donxinungluong.html': 'form_advance.html',
    'audit_log.html': 'NhatKyHD.html',
    'NhatKyHD.html': 'audit_log.html',
    'approvals.html': 'PheDuyet.html',
    'PheDuyet.html': 'approvals.html',
    'backup.html': 'SaoLuuData.html',
    'SaoLuuData.html': 'backup.html',
    'announcements.html': 'ThongBao.html',
    'ThongBao.html': 'announcements.html',
    'payroll_calc.html': 'TinhLuong.html',
    'TinhLuong.html': 'payroll_calc.html',
    'dash.html': 'TongQuanHeThong.html',
    'TongQuanHeThong.html': 'dash.html',
}

class AliasedLoader(BaseLoader):
    """Fallback loader to seamlessly map between canonical and localized template names."""
    def __init__(self, base_loader, aliases):
        self.base_loader = base_loader
        self.aliases = aliases

    def get_source(self, environment, template):
        try:
            return self.base_loader.get_source(environment, template)
        except Exception:
            alias = self.aliases.get(template)
            if alias:
                return self.base_loader.get_source(environment, alias)
            raise

    def list_templates(self):
        return self.base_loader.list_templates()

# Ensure stdout and stderr support UTF-8 on Windows terminals
if sys.platform == 'win32':
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr is not None:
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import (
    SECRET_KEY,
    NAV,
    NAV_GROUP,
    NAV_ICON,
    ICONS,
    TONE,
    ROLE_NAME
)
from database import close_db, init_db
from utils import csrf_guard, format_number, get_initial
from routes import register_blueprints

def create_app():
    """Application factory for the Flask app."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Configure aliased template loader for localized template names
    if app.jinja_loader:
        app.jinja_loader = AliasedLoader(app.jinja_loader, TEMPLATE_ALIASES)

    # Database teardown
    app.teardown_appcontext(close_db)

    # CSRF protection middleware
    app.before_request(csrf_guard)

    # Context processor for navigation, CSRF, and user session
    @app.context_processor
    def inject():
        session.setdefault('_csrf', secrets.token_hex(16))
        role = session.get('role')
        badges = {}
        total_badge_count = 0

        if role:
            from database import get_db
            try:
                db_conn = get_db()
                user = session.get('username') or session.get('user', '')
                mnv = session.get('mnv', '')

                # Đảm bảo bảng ThongBaoDaDoc tồn tại
                try:
                    is_mssql = getattr(db_conn, 'is_mssql', False)
                    if is_mssql:
                        db_conn.execute("""
                            IF OBJECT_ID(N'ThongBaoDaDoc', N'U') IS NULL
                            CREATE TABLE ThongBaoDaDoc(
                                MaTB INT NOT NULL,
                                TenDN NVARCHAR(100) NOT NULL,
                                ThoiGianDoc NVARCHAR(25) NOT NULL,
                                CONSTRAINT PK_ThongBaoDaDoc PRIMARY KEY (MaTB, TenDN)
                            );
                        """)
                    else:
                        db_conn.execute("""
                            CREATE TABLE IF NOT EXISTS ThongBaoDaDoc(
                                MaTB INTEGER NOT NULL,
                                TenDN TEXT NOT NULL,
                                ThoiGianDoc TEXT NOT NULL,
                                PRIMARY KEY (MaTB, TenDN)
                            );
                        """)
                    db_conn.commit()
                except Exception:
                    pass

                # 1. Thông báo nội bộ: Đếm chính xác số thông báo CHƯA ĐỌC của tài khoản hiện tại
                mapb = None
                if mnv:
                    emp_pb = db_conn.execute(
                        "SELECT c.MaPB FROM NhanVien n LEFT JOIN ChucVu c ON n.MaCV=c.MaCV WHERE n.MaNV=?",
                        (mnv,)
                    ).fetchone()
                    mapb = emp_pb['MaPB'] if emp_pb else None

                if role == 'Admin':
                    unread_tb = db_conn.execute("""
                        SELECT COUNT(*) FROM ThongBao x
                        WHERE x.MaTB NOT IN (SELECT d.MaTB FROM ThongBaoDaDoc d WHERE d.TenDN=?)
                    """, (user,)).fetchone()[0]
                else:
                    unread_tb = db_conn.execute("""
                        SELECT COUNT(*) FROM ThongBao x
                        WHERE (x.PhamVi=N'Toàn công ty' OR (x.PhamVi=N'Theo phòng ban' AND x.MaPB=?))
                          AND x.MaTB NOT IN (SELECT d.MaTB FROM ThongBaoDaDoc d WHERE d.TenDN=?)
                    """, (mapb, user)).fetchone()[0]

                if unread_tb > 0:
                    badges['Thông báo'] = unread_tb
                    total_badge_count += unread_tb

                # 2. Đơn từ chờ duyệt cho Quản lý & Admin
                if role == 'QuanLy' and mapb:
                    # Quản lý: Chỉ đếm các đơn của nhân viên thuộc đúng phòng ban mình quản lý
                    np_pend = db_conn.execute("""
                        SELECT COUNT(*) FROM NghiPhep x
                        JOIN NhanVien n ON x.MaNV=n.MaNV
                        JOIN ChucVu c ON n.MaCV=c.MaCV
                        WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'
                    """, (mapb,)).fetchone()[0]

                    ot_pend = db_conn.execute("""
                        SELECT COUNT(*) FROM TangCa x
                        JOIN NhanVien n ON x.MaNV=n.MaNV
                        JOIN ChucVu c ON n.MaCV=c.MaCV
                        WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'
                    """, (mapb,)).fetchone()[0]

                    tu_pend = db_conn.execute("""
                        SELECT COUNT(*) FROM TamUng x
                        JOIN NhanVien n ON x.MaNV=n.MaNV
                        JOIN ChucVu c ON n.MaCV=c.MaCV
                        WHERE c.MaPB=? AND x.TrangThai=N'Chờ duyệt'
                    """, (mapb,)).fetchone()[0]

                    dx_pend = db_conn.execute("""
                        SELECT COUNT(*) FROM DeXuatKhieuNai x
                        JOIN NhanVien n ON x.MaNV=n.MaNV
                        JOIN ChucVu c ON n.MaCV=c.MaCV
                        WHERE c.MaPB=? AND x.TrangThai=N'Chờ xử lý'
                    """, (mapb,)).fetchone()[0]
                elif role == 'Admin':
                    # Admin: Đếm toàn bộ đơn chờ duyệt của toàn công ty
                    np_pend = db_conn.execute("SELECT COUNT(*) FROM NghiPhep WHERE TrangThai=N'Chờ duyệt'").fetchone()[0]
                    ot_pend = db_conn.execute("SELECT COUNT(*) FROM TangCa WHERE TrangThai=N'Chờ duyệt'").fetchone()[0]
                    tu_pend = db_conn.execute("SELECT COUNT(*) FROM TamUng WHERE TrangThai=N'Chờ duyệt'").fetchone()[0]
                    dx_pend = db_conn.execute("SELECT COUNT(*) FROM DeXuatKhieuNai WHERE TrangThai=N'Chờ xử lý'").fetchone()[0]
                else:
                    np_pend = ot_pend = tu_pend = dx_pend = 0

                if np_pend > 0:
                    badges['Nghỉ phép'] = np_pend
                    total_badge_count += np_pend

                if ot_pend > 0:
                    badges['Tăng ca'] = ot_pend
                    total_badge_count += ot_pend

                if tu_pend > 0:
                    badges['Tạm ứng lương'] = tu_pend
                    total_badge_count += tu_pend

                if dx_pend > 0:
                    badges['Quản lý đề xuất & khiếu nại'] = dx_pend
                    total_badge_count += dx_pend

            except Exception:
                pass

        nav, prev = [], None
        for title, endpoint, mod, roles in NAV:
            if role in roles:
                group = NAV_GROUP.get(title)
                url = url_for(endpoint, mod=mod) if mod else url_for(endpoint)
                badge_num = badges.get(title, 0)
                nav.append((group if group != prev and group else None, title, url, NAV_ICON.get(title, 'circle'), badge_num))
                prev = group

        return dict(
            csrf=session['_csrf'],
            nav=nav,
            fmt=format_number,
            role=role,
            role_name=ROLE_NAME.get(role),
            uname=session.get('name'),
            badges=badges,
            total_badge_count=total_badge_count
        )

    # Template filters & globals
    @app.template_filter('ini')
    def filter_ini(name):
        return get_initial(name)

    app.jinja_env.globals['icon'] = lambda icon_name: Markup(
        f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(icon_name, "")}</svg>'
    )
    app.jinja_env.globals.update(TONE=TONE, ROLE_NAME=ROLE_NAME)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(_):
        return render_template('msg.html', msg='Bạn không có quyền truy cập chức năng này.'), 403

    @app.errorhandler(400)
    def bad_request(_):
        return render_template('msg.html', msg='Yêu cầu không hợp lệ (phiên làm việc hết hạn). Hãy tải lại trang.'), 400

    # Auto-resolve un-prefixed blueprint endpoints (backward compatibility)
    def url_build_error_resolver(error, endpoint, values):
        if '.' in endpoint:
            return None
        for bp_name in app.blueprints:
            candidate = f'{bp_name}.{endpoint}'
            if candidate in app.view_functions:
                return url_for(candidate, **values)
        return None

    app.url_build_error_handlers.append(url_build_error_resolver)

    # Register blueprints
    register_blueprints(app)

    # Ensure all department heads and staff accounts exist on app startup
    with app.app_context():
        try:
            from database import get_db, ensure_department_heads_and_staff
            db_conn = get_db()
            ensure_department_heads_and_staff(db_conn)
        except Exception:
            pass

    return app

app = create_app()

if __name__ == '__main__':
    init_db()
    try:
        print("Khởi động hệ thống Quản lý nhân sự tại: http://127.0.0.1:5000")
    except UnicodeEncodeError:
        print("He thong Quan ly nhan su khoi dong tai: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
