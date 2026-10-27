"""Phần mềm quản lý nhân sự - Nhóm 9 (Flask + SQLite).
Khởi chạy ứng dụng: python app.py -> http://127.0.0.1:5000
"""
import sys
import secrets
from flask import Flask, session, render_template, url_for
from markupsafe import Markup

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
