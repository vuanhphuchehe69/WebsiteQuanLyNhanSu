"""Configuration and constants for the Human Resource Management application."""
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database Configuration (Microsoft SQL Server)
DB_TYPE = os.environ.get('DB_TYPE', 'mssql')  # 'mssql' (mặc định CSDL thật) hoặc 'sqlite'
MSSQL_SERVER = os.environ.get('MSSQL_SERVER', r'.\SQLEXPRESS')
MSSQL_DATABASE = os.environ.get('MSSQL_DATABASE', 'QLNhanSu_Nhom9')
MSSQL_DRIVER = os.environ.get('MSSQL_DRIVER', 'ODBC Driver 18 for SQL Server')
MSSQL_TRUSTED_CONNECTION = os.environ.get('MSSQL_TRUSTED_CONNECTION', 'yes')
MSSQL_USER = os.environ.get('MSSQL_USER', '')
MSSQL_PASSWORD = os.environ.get('MSSQL_PASSWORD', '')

# SQLite Fallback File
DB_PATH = os.path.join(BASE_DIR, 'nhansu.db')
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)

# User Roles
NV, QL, AD = 'NhanVien', 'QuanLy', 'Admin'
ROLE_NAME = {
    NV: 'Nhân viên',
    QL: 'Quản lý',
    AD: 'Admin'
}

# Reusable SQL Query fragments
NV_SEL = (
    "SELECT n.*, c.TenCV, p.TenPB FROM NhanVien n "
    "LEFT JOIN ChucVu c ON n.MaCV=c.MaCV "
    "LEFT JOIN PhongBan p ON c.MaPB=p.MaPB"
)
EMP_JOIN = (
    " JOIN NhanVien n ON n.MaNV=x.MaNV "
    "LEFT JOIN ChucVu c ON n.MaCV=c.MaCV "
    "LEFT JOIN PhongBan p ON c.MaPB=p.MaPB"
)

# Module Configurations
# field definition: (name, label, type, required, select_source)
MODS = {
    'nhanvien': {
        'title': 'Nhân viên',
        'table': 'NhanVien',
        'pk': 'MaNV',
        'auto': False,
        'roles': (QL, AD),
        'sel': NV_SEL,
        'cols': [
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('GioiTinh', 'Giới tính'),
            ('NgaySinh', 'Ngày sinh'),
            ('SDT', 'SĐT'),
            ('TenCV', 'Chức vụ'),
            ('TenPB', 'Phòng ban'),
            ('NgayVaoCT', 'Ngày vào'),
        ],
        'search': ['n.MaNV', 'n.HoTen', 'n.SDT', 'n.Email', 'n.CCCD', 'c.TenCV', 'p.TenPB'],
        'order': 'MaNV',
        'fields': [
            ('MaNV', 'Mã nhân viên', 'text', 1, None),
            ('HoTen', 'Họ tên', 'text', 1, None),
            ('GioiTinh', 'Giới tính', 'select', 1, 'gt'),
            ('NgaySinh', 'Ngày sinh', 'date', 1, None),
            ('DiaChi', 'Địa chỉ', 'text', 0, None),
            ('SDT', 'Số điện thoại', 'tel', 0, None),
            ('CCCD', 'Căn cước công dân', 'cccd', 1, None),
            ('Email', 'Email', 'email', 0, None),
            ('NgayVaoCT', 'Ngày vào công ty', 'date', 1, None),
            ('MaCV', 'Chức vụ', 'select', 1, 'cv'),
        ]
    },
    'luong': {
        'title': 'Lương',
        'table': 'Luong',
        'pk': 'MaLuong',
        'auto': True,
        'roles': (QL, AD),
        'date': 'x.ThangNam',
        'sel': "SELECT x.*, n.HoTen, c.TenCV, p.TenPB, (x.LuongCung+x.LuongThuong+x.PhuCap-x.LuongUngTruoc) AS ThucLinh FROM Luong x" + EMP_JOIN,
        'cols': [
            ('MaLuong', 'Mã'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('TenPB', 'Phòng ban'),
            ('ThangNam', 'Tháng'),
            ('LuongCung', 'Lương cứng'),
            ('LuongThuong', 'Thưởng'),
            ('PhuCap', 'Phụ cấp'),
            ('LuongUngTruoc', 'Ứng trước'),
            ('ThucLinh', 'Thực lĩnh'),
        ],
        'search': ['x.MaNV', 'n.HoTen', 'c.TenCV', 'p.TenPB', 'x.ThangNam'],
        'order': 'ThangNam DESC, MaNV',
        'fields': [
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('ThangNam', 'Tháng/năm', 'month', 1, None),
            ('LuongCung', 'Lương cứng', 'number', 1, None),
            ('LuongThuong', 'Lương thưởng', 'number', 0, None),
            ('LuongUngTruoc', 'Lương ứng trước', 'number', 0, None),
            ('PhuCap', 'Phụ cấp', 'number', 0, None),
        ]
    },
    'nghiphep': {
        'title': 'Nghỉ phép',
        'table': 'NghiPhep',
        'pk': 'MaNP',
        'auto': True,
        'roles': (QL, AD),
        'date': 'x.NgayBD',
        'sel': "SELECT x.*, n.HoTen, c.TenCV, p.TenPB, (DATEDIFF(day, CAST(x.NgayBD AS DATE), CAST(x.NgayKT AS DATE)) + 1) AS SoNgay FROM NghiPhep x" + EMP_JOIN,
        'cols': [
            ('MaNP', 'Mã'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('TenCV', 'Chức vụ'),
            ('TenPB', 'Phòng ban'),
            ('NgayBD', 'Từ ngày'),
            ('NgayKT', 'Đến ngày'),
            ('SoNgay', 'Số ngày'),
            ('LyDo', 'Lý do'),
            ('TrangThai', 'Trạng thái'),
        ],
        'search': ['x.MaNV', 'n.HoTen', 'c.TenCV', 'p.TenPB', 'x.MaNP', 'x.TrangThai', 'x.LyDo'],
        'order': 'NgayBD DESC',
        'fields': [
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('NgayBD', 'Nghỉ từ ngày', 'date', 1, None),
            ('NgayKT', 'Nghỉ đến ngày', 'date', 1, None),
            ('LyDo', 'Lý do nghỉ', 'text', 0, None),
            ('TrangThai', 'Trạng thái', 'select', 1, 'tt_np'),
        ]
    },
    'tangca': {
        'title': 'Tăng ca',
        'table': 'TangCa',
        'pk': 'MaTC',
        'auto': True,
        'roles': (QL, AD),
        'date': 'x.Ngay',
        'sel': "SELECT x.*, n.HoTen, p.TenPB FROM TangCa x" + EMP_JOIN,
        'cols': [
            ('MaTC', 'Mã'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('TenPB', 'Phòng ban'),
            ('Ngay', 'Ngày'),
            ('SoGio', 'Số giờ'),
            ('Loai', 'Loại'),
        ],
        'search': ['x.MaNV', 'n.HoTen', 'x.MaTC', 'x.Loai', 'p.TenPB'],
        'order': 'Ngay DESC',
        'fields': [
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('Ngay', 'Ngày tăng ca', 'date', 1, None),
            ('SoGio', 'Số giờ', 'number', 1, None),
            ('Loai', 'Loại', 'select', 1, 'loai_tc'),
        ]
    },
    'phongban': {
        'title': 'Phòng ban',
        'table': 'PhongBan',
        'pk': 'MaPB',
        'auto': False,
        'roles': (AD,),
        'sel': "SELECT p.*, (SELECT COUNT(*) FROM ChucVu c WHERE c.MaPB=p.MaPB) AS SoCV FROM PhongBan p",
        'cols': [
            ('MaPB', 'Mã phòng ban'),
            ('TenPB', 'Tên phòng ban'),
            ('SoCV', 'Số chức vụ'),
        ],
        'search': ['p.MaPB', 'p.TenPB'],
        'order': 'MaPB',
        'fields': [
            ('MaPB', 'Mã phòng ban', 'text', 1, None),
            ('TenPB', 'Tên phòng ban', 'text', 1, None),
        ]
    },
    'chucvu': {
        'title': 'Chức vụ',
        'table': 'ChucVu',
        'pk': 'MaCV',
        'auto': False,
        'roles': (AD,),
        'sel': "SELECT c.*, p.TenPB FROM ChucVu c LEFT JOIN PhongBan p ON c.MaPB=p.MaPB",
        'cols': [
            ('MaCV', 'Mã chức vụ'),
            ('TenCV', 'Tên chức vụ'),
            ('MaPB', 'Mã PB'),
            ('TenPB', 'Phòng ban'),
        ],
        'search': ['c.MaCV', 'c.TenCV', 'c.MaPB', 'p.TenPB'],
        'order': 'MaCV',
        'fields': [
            ('MaCV', 'Mã chức vụ', 'text', 1, None),
            ('TenCV', 'Tên chức vụ', 'text', 1, None),
            ('MaPB', 'Phòng ban', 'select', 1, 'pb'),
        ]
    },
    'taikhoan': {
        'title': 'Tài khoản',
        'table': 'TaiKhoan',
        'pk': 'MaTK',
        'auto': True,
        'roles': (AD,),
        'pw': 'MatKhau',
        'sel': "SELECT x.MaTK, x.TenDN, x.MatKhau, x.MaNV, x.LoaiTK, n.HoTen FROM TaiKhoan x JOIN NhanVien n ON n.MaNV=x.MaNV",
        'cols': [
            ('MaTK', 'Mã TK'),
            ('TenDN', 'Tên đăng nhập'),
            ('MatKhau', 'Mật khẩu'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('LoaiTK', 'Loại tài khoản'),
        ],
        'search': ['x.TenDN', 'x.MaNV', 'n.HoTen', 'x.LoaiTK'],
        'order': 'MaTK',
        'fields': [
            ('TenDN', 'Tên đăng nhập', 'text', 1, None),
            ('MatKhau', 'Mật khẩu', 'password', 1, None),
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('LoaiTK', 'Loại tài khoản', 'select', 1, 'loai_tk'),
        ]
    },
    'hopdong': {
        'title': 'Hợp đồng',
        'table': 'HopDong',
        'pk': 'MaHD',
        'auto': False,
        'roles': (QL, AD),
        'sel': "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM HopDong x" + EMP_JOIN,
        'cols': [
            ('MaHD', 'Mã HĐ'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('TenPB', 'Phòng ban'),
            ('LoaiHD', 'Loại HĐ'),
            ('NgayBD', 'Từ ngày'),
            ('NgayKT', 'Đến ngày'),
            ('LuongCoBan', 'Lương cơ bản'),
            ('TrangThai', 'Trạng thái'),
        ],
        'search': ['x.MaHD', 'x.MaNV', 'n.HoTen', 'x.LoaiHD', 'x.TrangThai', 'p.TenPB'],
        'order': 'x.NgayBD DESC, x.MaHD',
        'fields': [
            ('MaHD', 'Mã hợp đồng', 'text', 1, None),
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('LoaiHD', 'Loại hợp đồng', 'select', 1, 'loai_hd'),
            ('NgayBD', 'Ngày bắt đầu', 'date', 1, None),
            ('NgayKT', 'Ngày kết thúc', 'date', 0, None),
            ('LuongCoBan', 'Lương cơ bản', 'number', 0, None),
            ('TrangThai', 'Trạng thái', 'select', 1, 'tt_hd'),
            ('GhiChu', 'Ghi chú', 'text', 0, None),
        ]
    },
}

STATIC_OPT = {
    'gt': [('Nam', 'Nam'), ('Nữ', 'Nữ')],
    'loai_tk': [(NV, 'Nhân viên'), (QL, 'Quản lý')],
    'loai_tc': [('Ngày thường', 'Ngày thường'), ('Cuối tuần', 'Cuối tuần'), ('Ngày lễ', 'Ngày lễ')],
    'loai_hd': [
        ('Thử việc', 'Thử việc'),
        ('Xác định thời hạn (1 năm)', 'Xác định thời hạn (1 năm)'),
        ('Xác định thời hạn (3 năm)', 'Xác định thời hạn (3 năm)'),
        ('Không xác định thời hạn', 'Không xác định thời hạn'),
        ('Học việc', 'Học việc')
    ],
    'tt_hd': [
        ('Hiệu lực', 'Hiệu lực'),
        ('Hết hạn', 'Hết hạn'),
        ('Đã chấm dứt', 'Đã chấm dứt')
    ],
    'tt_np': [
        ('Chờ duyệt', 'Chờ duyệt'),
        ('Đã duyệt', 'Đã duyệt'),
        ('Từ chối', 'Từ chối')
    ]
}

DB_OPT = {
    'nv': "SELECT MaNV, CONCAT(MaNV, ' - ', HoTen) FROM NhanVien ORDER BY MaNV",
    'cv': "SELECT c.MaCV, CONCAT(c.MaCV, ' - ', c.TenCV, ' (', COALESCE(p.TenPB, ''), ')') FROM ChucVu c LEFT JOIN PhongBan p ON c.MaPB=p.MaPB ORDER BY c.MaCV",
    'pb': "SELECT MaPB, CONCAT(MaPB, ' - ', TenPB) FROM PhongBan ORDER BY MaPB"
}

NAV = [
    ('Trang chủ', 'dash', None, (QL, AD)),
    ('Thông tin cá nhân', 'me', None, (NV, QL)),
    ('Nhân viên', 'mlist', 'nhanvien', (QL, AD)),
    ('Hợp đồng', 'mlist', 'hopdong', (QL, AD)),
    ('Lương', 'mlist', 'luong', (QL, AD)),
    ('Nghỉ phép', 'mlist', 'nghiphep', (QL, AD)),
    ('Chi tiết nghỉ phép', 'report_leave', None, (QL, AD)),
    ('Tăng ca', 'mlist', 'tangca', (QL, AD)),
    ('Phòng ban', 'mlist', 'phongban', (AD,)),
    ('Chức vụ', 'mlist', 'chucvu', (AD,)),
    ('Tài khoản', 'mlist', 'taikhoan', (AD,)),
    ('Đổi mật khẩu', 'change_pw', None, (NV, QL, AD)),
]

NAV_ICON = {
    'Trang chủ': 'home',
    'Thông tin cá nhân': 'user',
    'Nhân viên': 'users',
    'Hợp đồng': 'file-text',
    'Lương': 'wallet',
    'Nghỉ phép': 'calendar',
    'Chi tiết nghỉ phép': 'list',
    'Tăng ca': 'clock',
    'Phòng ban': 'building',
    'Chức vụ': 'briefcase',
    'Tài khoản': 'key',
    'Đổi mật khẩu': 'lock',
}

NAV_GROUP = {
    'Trang chủ': None,
    'Thông tin cá nhân': None,
    'Nhân viên': 'Nghiệp vụ',
    'Hợp đồng': 'Nghiệp vụ',
    'Lương': 'Nghiệp vụ',
    'Nghỉ phép': 'Nghiệp vụ',
    'Chi tiết nghỉ phép': 'Nghiệp vụ',
    'Tăng ca': 'Nghiệp vụ',
    'Phòng ban': 'Danh mục',
    'Chức vụ': 'Danh mục',
    'Tài khoản': 'Hệ thống',
    'Đổi mật khẩu': 'Hệ thống',
}

TONE = {
    'QuanLy': 'b',
    'NhanVien': 'n',
    'Ngày lễ': 'w',
    'Cuối tuần': 'b',
    'Ngày thường': 'n',
    'Hiệu lực': 'ok',
    'Hết hạn': 'bad',
    'Đã chấm dứt': 'n',
    'Thử việc': 'w',
    'Không xác định thời hạn': 'b',
    'Chờ duyệt': 'w',
    'Đã duyệt': 'ok',
    'Từ chối': 'bad'
}

ICONS = {
    'home': '<path d="M3 11l9-8 9 8v10a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    'user': '<circle cx="12" cy="7" r="4"/><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>',
    'users': '<circle cx="9" cy="7" r="4"/><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    'wallet': '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20M16 14h2"/>',
    'calendar': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    'clock': '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    'building': '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>',
    'briefcase': '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    'file-text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
    'key': '<circle cx="7.5" cy="15.5" r="5.5"/><path d="M11.5 11.5L21 2M16 7l3 3"/>',
    'lock': '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    'list': '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    'logout': '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    'search': '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'edit': '<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    'trash': '<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
    'refresh': '<path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/>',
    'menu': '<path d="M3 6h18M3 12h18M3 18h18"/>',
    'check': '<polyline points="20 6 9 17 4 12"/>',
    'x': '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    'chevron-left': '<polyline points="15 18 9 12 15 6"/>',
    'chevron-right': '<polyline points="9 18 15 12 9 6"/>',
}

