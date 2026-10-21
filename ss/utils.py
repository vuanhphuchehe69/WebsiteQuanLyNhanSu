"""Utility functions, authentication decorators, CSRF protection, and form validation."""
import re
import secrets
from datetime import datetime
from functools import wraps
from flask import session, request, redirect, url_for, abort
from werkzeug.security import generate_password_hash
from config import MODS, STATIC_OPT, DB_OPT

def login_required(f):
    """Decorator to require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    """Decorator to restrict access to specific user roles."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if session.get('role') not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def csrf_guard():
    """Verify CSRF token on POST requests."""
    session.setdefault('_csrf', secrets.token_hex(16))
    if request.method == 'POST':
        token = request.form.get('_csrf', '')
        session_token = session.get('_csrf', ' ')
        if not secrets.compare_digest(token, session_token):
            abort(400)

def get_module(mod_name):
    """Retrieve module metadata and verify current user has required role."""
    module_config = MODS.get(mod_name)
    if not module_config:
        abort(404)
    current_role = session.get('role')
    if current_role not in module_config['roles']:
        abort(403)
    return module_config

def get_form_options(db_conn):
    """Load dynamic options from database and merge with static options."""
    options = {
        key: [tuple(row) for row in db_conn.execute(sql).fetchall()]
        for key, sql in DB_OPT.items()
    }
    options.update(STATIC_OPT)
    return options

def parse_form_data(module_config, form, editing=False):
    """Validate and parse submitted form data according to module field definitions."""
    vals = {}
    errs = []

    for name, label, field_type, required, _ in module_config['fields']:
        val = form.get(name, '').strip()

        if editing and name == module_config['pk']:
            continue
        if editing and field_type == 'password' and not val:
            continue
        if required and not val:
            errs.append(f'{label} không được để trống.')
            continue

        if val:
            try:
                if field_type == 'number':
                    num_val = float(val)
                    if num_val < 0 or num_val != num_val:
                        raise ValueError
                    if name == 'SoGio' and not (0 < num_val <= 24):
                        raise ValueError
                    val = num_val
                elif field_type == 'date':
                    datetime.strptime(val, '%Y-%m-%d')
                elif field_type == 'month':
                    datetime.strptime(val, '%Y-%m')
                elif field_type == 'tel' and not re.fullmatch(r'0\d{8,10}', val):
                    raise ValueError
                elif field_type == 'cccd' and not re.fullmatch(r'\d{12}', val):
                    raise ValueError
                elif field_type == 'email' and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', val):
                    raise ValueError
                elif field_type == 'password' and len(val) < 6:
                    raise ValueError
            except ValueError:
                errs.append(f'{label} không hợp lệ.')
                continue

        vals[name] = val if val != '' else None

    # Module-specific cross-field validations
    if module_config['table'] in ('NghiPhep', 'HopDong') and vals.get('NgayBD') and vals.get('NgayKT'):
        if vals['NgayKT'] < vals['NgayBD']:
            errs.append('Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.')

    # Store plain password directly as requested
    pw_field = module_config.get('pw')
    if pw_field and vals.get(pw_field):
        vals[pw_field] = vals[pw_field]

    return vals, errs

def format_number(val):
    """Format numeric values for display in tables."""
    if val is None:
        return ''
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        if isinstance(val, int) and abs(val) >= 1000:
            return f'{val:,.0f}'
        return str(val)
    return str(val)

def get_initial(name):
    """Get the initial letter of the last word in a name."""
    words = str(name).split()
    if not words:
        return '?'
    return words[-1][:1].upper()

