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
        'icon': 'users',
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
        'icon': 'wallet',
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
        'icon': 'calendar',
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
        'icon': 'clock',
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
        'icon': 'building',
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
        'icon': 'briefcase',
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
        'icon': 'key',
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
        'icon': 'file-text',
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
    'chamcong': {
        'title': 'Chấm công',
        'icon': 'check-square',
        'table': 'ChamCong',
        'pk': 'MaCC',
        'auto': True,
        'roles': (QL, AD),
        'date': 'x.Ngay',
        'sel': "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM ChamCong x" + EMP_JOIN,
        'cols': [
            ('MaCC', 'Mã'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('TenPB', 'Phòng ban'),
            ('Ngay', 'Ngày'),
            ('GioVao', 'Giờ vào'),
            ('GioRa', 'Giờ ra'),
            ('TrangThai', 'Trạng thái'),
            ('GhiChu', 'Ghi chú'),
        ],
        'search': ['x.MaNV', 'n.HoTen', 'c.TenCV', 'p.TenPB', 'x.TrangThai'],
        'order': 'x.Ngay DESC, x.MaNV',
        'fields': [
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('Ngay', 'Ngày chấm công', 'date', 1, None),
            ('GioVao', 'Giờ vào (HH:MM)', 'text', 0, None),
            ('GioRa', 'Giờ ra (HH:MM)', 'text', 0, None),
            ('TrangThai', 'Trạng thái', 'select', 1, 'tt_cc'),
            ('GhiChu', 'Ghi chú', 'text', 0, None),
        ]
    },
    'danhgia': {
        'title': 'Đánh giá KPI',
        'icon': 'award',
        'table': 'DanhGia',
        'pk': 'MaDG',
        'auto': True,
        'roles': (QL, AD),
        'date': 'x.ThangNam',
        'sel': "SELECT x.*, n.HoTen, c.TenCV, p.TenPB FROM DanhGia x" + EMP_JOIN,
        'cols': [
            ('MaDG', 'Mã'),
            ('MaNV', 'Mã NV'),
            ('HoTen', 'Họ tên'),
            ('TenPB', 'Phòng ban'),
            ('ThangNam', 'Tháng'),
            ('DiemKPI', 'Điểm KPI'),
            ('XepLoai', 'Xếp loại'),
            ('NhanXet', 'Nhận xét'),
            ('NguoiDanhGia', 'Người đánh giá'),
        ],
        'search': ['x.MaNV', 'n.HoTen', 'c.TenCV', 'p.TenPB', 'x.XepLoai', 'x.ThangNam'],
        'order': 'x.ThangNam DESC, x.DiemKPI DESC',
        'fields': [
            ('MaNV', 'Nhân viên', 'select', 1, 'nv'),
            ('ThangNam', 'Tháng đánh giá', 'month', 1, None),
            ('DiemKPI', 'Điểm KPI (0 - 100)', 'number', 1, None),
            ('XepLoai', 'Xếp loại', 'select', 1, 'loai_xl'),
            ('NhanXet', 'Nhận xét / Đánh giá', 'text', 0, None),
            ('NguoiDanhGia', 'Người đánh giá', 'text', 1, None),
        ]
    },
    'thongbao': {
        'title': 'Quản lý thông báo',
        'icon': 'send',
        'table': 'ThongBao',
        'pk': 'MaTB',
        'auto': True,
        'roles': (QL, AD),
        'date': 'x.NgayGui',
        'sel': "SELECT x.*, p.TenPB FROM ThongBao x LEFT JOIN PhongBan p ON x.MaPB=p.MaPB",
        'cols': [
            ('MaTB', 'Mã'),
            ('TieuDe', 'Tiêu đề'),
            ('PhamVi', 'Phạm vi'),
            ('TenPB', 'Phòng ban nhận'),
            ('NguoiGui', 'Người gửi'),
            ('NgayGui', 'Ngày gửi'),
        ],
        'search': ['x.TieuDe', 'x.NguoiGui', 'x.PhamVi', 'p.TenPB'],
        'order': 'x.NgayGui DESC',
        'fields': [
            ('TieuDe', 'Tiêu đề thông báo', 'text', 1, None),
            ('NoiDung', 'Nội dung thông báo', 'text', 1, None),
            ('PhamVi', 'Phạm vi áp dụng', 'select', 1, 'pham_vi_tb'),
            ('MaPB', 'Phòng ban nhận (nếu theo phòng ban)', 'select', 0, 'pb'),
            ('NguoiGui', 'Người gửi', 'text', 1, None),
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
    ],
    'tt_cc': [
        ('Đúng giờ', 'Đúng giờ'),
        ('Đi muộn', 'Đi muộn'),
        ('Về sớm', 'Về sớm'),
        ('Nghỉ', 'Nghỉ')
    ],
    'loai_xl': [
        ('Xuất sắc', 'Xuất sắc'),
        ('Tốt', 'Tốt'),
        ('Khá', 'Khá'),
        ('Trung bình', 'Trung bình'),
        ('Yếu', 'Yếu')
    ],
    'pham_vi_tb': [
        ('Toàn công ty', 'Toàn công ty'),
        ('Theo phòng ban', 'Theo phòng ban')
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
    ('Thông báo', 'announcements', None, (NV, QL, AD)),
    ('Nhân viên', 'mlist', 'nhanvien', (QL, AD)),
    ('Chấm công', 'mlist', 'chamcong', (QL, AD)),
    ('Nghỉ phép', 'mlist', 'nghiphep', (QL, AD)),
    ('Tăng ca', 'mlist', 'tangca', (QL, AD)),
    ('Lương', 'mlist', 'luong', (QL, AD)),
    ('Hợp đồng', 'mlist', 'hopdong', (QL, AD)),
    ('Đánh giá KPI', 'mlist', 'danhgia', (QL, AD)),
    ('Báo cáo nghỉ phép', 'report_leave', None, (QL, AD)),
    ('Báo cáo nhân sự', 'report_hr', None, (QL, AD)),
    ('Phòng ban', 'mlist', 'phongban', (AD,)),
    ('Chức vụ', 'mlist', 'chucvu', (AD,)),
    ('Tài khoản', 'mlist', 'taikhoan', (AD,)),
    ('Quản lý thông báo', 'mlist', 'thongbao', (QL, AD)),
    ('Sao lưu dữ liệu', 'backup_view', None, (AD,)),
    ('Đổi mật khẩu', 'change_pw', None, (NV, QL, AD)),
]

NAV_ICON = {
    'Trang chủ': 'home',
    'Thông tin cá nhân': 'user',
    'Thông báo': 'bell',
    'Nhân viên': 'users',
    'Chấm công': 'check-square',
    'Hợp đồng': 'file-text',
    'Lương': 'wallet',
    'Nghỉ phép': 'calendar',
    'Chi tiết nghỉ phép': 'list',
    'Báo cáo nghỉ phép': 'list',
    'Báo cáo nhân sự': 'pie-chart',
    'Tăng ca': 'clock',
    'Đánh giá KPI': 'award',
    'Phòng ban': 'building',
    'Chức vụ': 'briefcase',
    'Tài khoản': 'key',
    'Quản lý thông báo': 'send',
    'Sao lưu dữ liệu': 'database',
    'Đổi mật khẩu': 'lock',
}

NAV_GROUP = {
    'Trang chủ': None,
    'Thông tin cá nhân': None,
    'Thông báo': None,
    'Nhân viên': 'Nghiệp vụ',
    'Chấm công': 'Nghiệp vụ',
    'Hợp đồng': 'Nghiệp vụ',
    'Lương': 'Nghiệp vụ',
    'Nghỉ phép': 'Nghiệp vụ',
    'Tăng ca': 'Nghiệp vụ',
    'Đánh giá KPI': 'Nghiệp vụ',
    'Báo cáo nghỉ phép': 'Báo cáo',
    'Báo cáo nhân sự': 'Báo cáo',
    'Phòng ban': 'Danh mục',
    'Chức vụ': 'Danh mục',
    'Tài khoản': 'Hệ thống',
    'Quản lý thông báo': 'Hệ thống',
    'Sao lưu dữ liệu': 'Hệ thống',
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
    'Từ chối': 'bad',
    'Đúng giờ': 'ok',
    'Đi muộn': 'w',
    'Về sớm': 'w',
    'Nghỉ': 'bad',
    'Xuất sắc': 'ok',
    'Tốt': 'b',
    'Khá': 'n',
    'Trung bình': 'w',
    'Yếu': 'bad',
    'Toàn công ty': 'b',
    'Theo phòng ban': 'n'
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
    'bell': '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    'check-square': '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    'award': '<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>',
    'pie-chart': '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
    'send': '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    'database': '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    'info': '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    'mail': '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'map-pin': '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    'trending-up': '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    'sparkles': '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>',
    'zap': '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    'external-link': '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    'bar-chart-2': '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    'log-in': '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>',
    'hard-drive': '<line x1="22" y1="12" x2="2" y2="12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><line x1="6" y1="16" x2="6.01" y2="16"/><line x1="10" y1="16" x2="10.01" y2="16"/>',
    'server': '<rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
}

