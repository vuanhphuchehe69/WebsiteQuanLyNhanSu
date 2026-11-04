# -*- coding: utf-8 -*-
"""Wrapper tương thích ngược: tự động gọi kịch bản khởi tạo chuẩn seed_employees.py (13 nhân sự, 4 phòng ban)."""
import os
import sys

script_path = os.path.join(os.path.dirname(__file__), 'seed_employees.py')
with open(script_path, 'r', encoding='utf-8') as f:
    code = compile(f.read(), script_path, 'exec')
    exec(code, globals())
