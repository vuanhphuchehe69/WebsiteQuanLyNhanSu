"""Phần mềm quản lý nhân sự - Nhóm 9 (Flask + SQLite).
Khởi chạy ứng dụng: python app.py -> http://127.0.0.1:5000
"""
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
        nav, prev = [], None
        for title, endpoint, mod, roles in NAV:
            if role in roles:
                group = NAV_GROUP[title]
                url = url_for(endpoint, mod=mod) if mod else url_for(endpoint)
                nav.append((group if group != prev and group else None, title, url, NAV_ICON[title]))
                prev = group

        return dict(
            csrf=session['_csrf'],
            nav=nav,
            fmt=format_number,
            role=role,
            role_name=ROLE_NAME.get(role),
            uname=session.get('name')
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

    return app

app = create_app()

if __name__ == '__main__':
    init_db()
    try:
        print("Khởi động hệ thống Quản lý nhân sự tại: http://127.0.0.1:5000")
    except UnicodeEncodeError:
        print("He thong Quan ly nhan su khoi dong tai: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
