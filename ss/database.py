"""Database management supporting Microsoft SQL Server (MSSQL) with SQLite fallback."""
import sqlite3
from datetime import date, datetime
from flask import g
from werkzeug.security import generate_password_hash

from config import (
    DB_TYPE,
    DB_PATH,
    MSSQL_SERVER,
    MSSQL_DATABASE,
    MSSQL_DRIVER,
    MSSQL_TRUSTED_CONNECTION,
    MSSQL_USER,
    MSSQL_PASSWORD,
    NV,
    QL
)

try:
    import pyodbc
    PYODBC_AVAILABLE = True
    IntegrityError = (pyodbc.IntegrityError, sqlite3.IntegrityError)
except ImportError:
    PYODBC_AVAILABLE = False
    IntegrityError = (sqlite3.IntegrityError,)

# Unified Row wrapper to allow dictionary-like (row['key']), attribute (row.key), and indexed access (row[0])
class RowWrapper:
    def __init__(self, columns, values):
        self._data = dict(zip(columns, values))
        self._list = list(values)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._list[item]
        return self._data[item]

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(name)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __iter__(self):
        return iter(self._list)

    def __repr__(self):
        return f'<Row {self._data}>'

class CursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        cols = [col[0] for col in self._cursor.description]
        return RowWrapper(cols, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        cols = [col[0] for col in self._cursor.description]
        return [RowWrapper(cols, r) for r in rows]

    def __iter__(self):
        return iter(self.fetchall())

class ConnectionWrapper:
    def __init__(self, raw_conn, is_mssql=True):
        self._conn = raw_conn
        self.is_mssql = is_mssql

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        if params is not None:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return CursorWrapper(cur)

    def executemany(self, sql, param_list):
        cur = self._conn.cursor()
        cur.executemany(sql, param_list)
        return CursorWrapper(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

def build_mssql_connection_string(database=None):
    db_target = database or MSSQL_DATABASE
    if MSSQL_USER and MSSQL_PASSWORD:
        return (
            f"DRIVER={{{MSSQL_DRIVER}}};SERVER={MSSQL_SERVER};DATABASE={db_target};"
            f"UID={MSSQL_USER};PWD={MSSQL_PASSWORD};TrustServerCertificate=yes;"
        )
    return (
        f"DRIVER={{{MSSQL_DRIVER}}};SERVER={MSSQL_SERVER};DATABASE={db_target};"
        f"Trusted_Connection={MSSQL_TRUSTED_CONNECTION};TrustServerCertificate=yes;"
    )

def get_db():
    """Get or create database connection for the current Flask application context."""
    if 'db' not in g:
        if DB_TYPE == 'mssql' and PYODBC_AVAILABLE:
            raw_conn = pyodbc.connect(build_mssql_connection_string(), timeout=10)
            g.db = ConnectionWrapper(raw_conn, is_mssql=True)
        else:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys = ON')
            g.db = conn
    return g.db

def close_db(e=None):
    """Close the database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

MSSQL_SCHEMA = """
IF OBJECT_ID(N'PhongBan', N'U') IS NULL
CREATE TABLE PhongBan(
    MaPB NVARCHAR(50) PRIMARY KEY,
    TenPB NVARCHAR(255) NOT NULL
);

IF OBJECT_ID(N'ChucVu', N'U') IS NULL
CREATE TABLE ChucVu(
    MaCV NVARCHAR(50) PRIMARY KEY,
    TenCV NVARCHAR(255) NOT NULL,
    MaPB NVARCHAR(50) NOT NULL REFERENCES PhongBan(MaPB) ON DELETE NO ACTION ON UPDATE CASCADE
);

IF OBJECT_ID(N'NhanVien', N'U') IS NULL
CREATE TABLE NhanVien(
    MaNV NVARCHAR(50) PRIMARY KEY,
    HoTen NVARCHAR(255) NOT NULL,
    DiaChi NVARCHAR(255),
    SDT NVARCHAR(20),
    CCCD NVARCHAR(20) UNIQUE,
    Email NVARCHAR(100),
    NgaySinh NVARCHAR(20),
    NgayVaoCT NVARCHAR(20),
    GioiTinh NVARCHAR(10),
    TrinhDo NVARCHAR(100),
    ChuyenMon NVARCHAR(100),
    LoaiNhanVien NVARCHAR(50) DEFAULT N'Chính thức',
    SoBHXH NVARCHAR(50),
    MaSoThue NVARCHAR(50),
    MaCV NVARCHAR(50) NOT NULL REFERENCES ChucVu(MaCV) ON DELETE NO ACTION ON UPDATE CASCADE
);

IF OBJECT_ID(N'HopDong', N'U') IS NULL
CREATE TABLE HopDong(
    MaHD NVARCHAR(50) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    LoaiHD NVARCHAR(100) NOT NULL,
    NgayBD NVARCHAR(20) NOT NULL,
    NgayKT NVARCHAR(20),
    LuongCoBan FLOAT DEFAULT 0,
    TrangThai NVARCHAR(50) DEFAULT N'Hiệu lực',
    GhiChu NVARCHAR(MAX)
);

IF OBJECT_ID(N'Luong', N'U') IS NULL
CREATE TABLE Luong(
    MaLuong INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    ThangNam NVARCHAR(20) NOT NULL,
    LuongCung FLOAT DEFAULT 0,
    LuongThuong FLOAT DEFAULT 0,
    LuongUngTruoc FLOAT DEFAULT 0,
    PhuCap FLOAT DEFAULT 0,
    BaoHiem FLOAT DEFAULT 0,
    ThueTNCN FLOAT DEFAULT 0,
    KhauTruKhac FLOAT DEFAULT 0,
    CONSTRAINT UQ_Luong_NV_Thang UNIQUE(MaNV, ThangNam)
);

IF OBJECT_ID(N'NghiPhep', N'U') IS NULL
CREATE TABLE NghiPhep(
    MaNP INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    NgayBD NVARCHAR(20) NOT NULL,
    NgayKT NVARCHAR(20) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Chờ duyệt',
    LyDo NVARCHAR(255)
);

IF OBJECT_ID(N'TangCa', N'U') IS NULL
CREATE TABLE TangCa(
    MaTC INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    SoGio FLOAT NOT NULL,
    Ngay NVARCHAR(20) NOT NULL,
    Loai NVARCHAR(50),
    TrangThai NVARCHAR(50) DEFAULT N'Đã duyệt',
    LyDo NVARCHAR(255),
    NguoiDuyet NVARCHAR(100)
);

IF OBJECT_ID(N'TaiKhoan', N'U') IS NULL
CREATE TABLE TaiKhoan(
    MaTK INT IDENTITY(1,1) PRIMARY KEY,
    TenDN NVARCHAR(100) UNIQUE NOT NULL,
    MatKhau NVARCHAR(255) NOT NULL,
    MaNV NVARCHAR(50) NOT NULL UNIQUE REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    LoaiTK NVARCHAR(50) NOT NULL CHECK(LoaiTK IN ('NhanVien', 'QuanLy'))
);

IF OBJECT_ID(N'TaiKhoanAdmin', N'U') IS NULL
CREATE TABLE TaiKhoanAdmin(
    MaTK INT IDENTITY(1,1) PRIMARY KEY,
    TenDN NVARCHAR(100) UNIQUE NOT NULL,
    MatKhau NVARCHAR(255) NOT NULL
);

IF OBJECT_ID(N'ChamCong', N'U') IS NULL
CREATE TABLE ChamCong(
    MaCC INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    Ngay NVARCHAR(20) NOT NULL,
    GioVao NVARCHAR(10),
    GioRa NVARCHAR(10),
    TrangThai NVARCHAR(50) DEFAULT N'Đúng giờ',
    GhiChu NVARCHAR(255),
    CONSTRAINT UQ_ChamCong_NV_Ngay UNIQUE(MaNV, Ngay)
);

IF OBJECT_ID(N'DanhGia', N'U') IS NULL
CREATE TABLE DanhGia(
    MaDG INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    ThangNam NVARCHAR(20) NOT NULL,
    DiemKPI FLOAT NOT NULL,
    XepLoai NVARCHAR(50) NOT NULL,
    NhanXet NVARCHAR(MAX),
    NguoiDanhGia NVARCHAR(100),
    DiemTuDanhGia FLOAT,
    NhanXetCaNhan NVARCHAR(MAX),
    CONSTRAINT UQ_DanhGia_NV_Thang UNIQUE(MaNV, ThangNam)
);

IF OBJECT_ID(N'ThongBao', N'U') IS NULL
CREATE TABLE ThongBao(
    MaTB INT IDENTITY(1,1) PRIMARY KEY,
    TieuDe NVARCHAR(255) NOT NULL,
    NoiDung NVARCHAR(MAX) NOT NULL,
    NgayGui NVARCHAR(25) NOT NULL,
    NguoiGui NVARCHAR(100) NOT NULL,
    PhamVi NVARCHAR(50) DEFAULT N'Toàn công ty',
    MaPB NVARCHAR(50) REFERENCES PhongBan(MaPB) ON DELETE SET NULL ON UPDATE CASCADE
);

IF OBJECT_ID(N'TaiLieuNhanVien', N'U') IS NULL
CREATE TABLE TaiLieuNhanVien(
    MaTL INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    TenTaiLieu NVARCHAR(255) NOT NULL,
    Loai NVARCHAR(100) NOT NULL,
    NgayCap NVARCHAR(20),
    NoiCap NVARCHAR(255),
    TepDinhKem NVARCHAR(255),
    NgayTai NVARCHAR(25) NOT NULL,
    GhiChu NVARCHAR(MAX)
);

IF OBJECT_ID(N'GiaiTrinhCong', N'U') IS NULL
CREATE TABLE GiaiTrinhCong(
    MaGT INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    Ngay NVARCHAR(20) NOT NULL,
    GioVaoDeXuat NVARCHAR(10),
    GioRaDeXuat NVARCHAR(10),
    LyDo NVARCHAR(MAX) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Chờ duyệt',
    NguoiDuyet NVARCHAR(100),
    NgayGui NVARCHAR(25) NOT NULL,
    PhanHoi NVARCHAR(MAX)
);

IF OBJECT_ID(N'KhenThuongKyLuat', N'U') IS NULL
CREATE TABLE KhenThuongKyLuat(
    MaKTKL INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    Loai NVARCHAR(50) NOT NULL,
    SoQuyetDinh NVARCHAR(100) NOT NULL,
    NgayQuyetDinh NVARCHAR(20) NOT NULL,
    HinhThuc NVARCHAR(150) NOT NULL,
    SoTien FLOAT DEFAULT 0,
    LyDo NVARCHAR(MAX) NOT NULL,
    NguoiKy NVARCHAR(100)
);

IF OBJECT_ID(N'KhoaDaoTao', N'U') IS NULL
CREATE TABLE KhoaDaoTao(
    MaKDT INT IDENTITY(1,1) PRIMARY KEY,
    TenKhoa NVARCHAR(255) NOT NULL,
    GiangVien NVARCHAR(100),
    ThoiGian NVARCHAR(100),
    DiaDiem NVARCHAR(255),
    SoLuong INT DEFAULT 30,
    MoTa NVARCHAR(MAX),
    TrangThai NVARCHAR(50) DEFAULT N'Sắp diễn ra'
);

IF OBJECT_ID(N'DangKyDaoTao', N'U') IS NULL
CREATE TABLE DangKyDaoTao(
    MaDK INT IDENTITY(1,1) PRIMARY KEY,
    MaKDT INT NOT NULL REFERENCES KhoaDaoTao(MaKDT) ON DELETE CASCADE,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    NgayDangKy NVARCHAR(25) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Đã đăng ký',
    CONSTRAINT UQ_DangKy_KDT_NV UNIQUE(MaKDT, MaNV)
);

IF OBJECT_ID(N'DeXuatKhieuNai', N'U') IS NULL
CREATE TABLE DeXuatKhieuNai(
    MaDX INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    TieuDe NVARCHAR(255) NOT NULL,
    Loai NVARCHAR(100) NOT NULL,
    NoiDung NVARCHAR(MAX) NOT NULL,
    NgayGui NVARCHAR(25) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Chờ xử lý',
    PhanHoi NVARCHAR(MAX),
    NguoiXuLy NVARCHAR(100)
);

IF OBJECT_ID(N'TamUng', N'U') IS NULL
CREATE TABLE TamUng(
    MaTU INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    ThangNam NVARCHAR(20) NOT NULL,
    SoTien FLOAT NOT NULL,
    LyDo NVARCHAR(MAX) NOT NULL,
    NgayYeuCau NVARCHAR(25) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Chờ duyệt',
    NguoiDuyet NVARCHAR(100)
);

IF OBJECT_ID(N'PhanCa', N'U') IS NULL
CREATE TABLE PhanCa(
    MaPC INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    Ngay NVARCHAR(20) NOT NULL,
    CaLam NVARCHAR(100) NOT NULL,
    GhiChu NVARCHAR(255),
    CONSTRAINT UQ_PhanCa_NV_Ngay UNIQUE(MaNV, Ngay)
);

IF OBJECT_ID(N'DeXuatNhanSu', N'U') IS NULL
CREATE TABLE DeXuatNhanSu(
    MaDXNS INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    NguoiDeXuat NVARCHAR(50) NOT NULL,
    LoaiDeXuat NVARCHAR(100) NOT NULL,
    MucDeXuat NVARCHAR(255),
    LyDo NVARCHAR(MAX) NOT NULL,
    NgayDeXuat NVARCHAR(25) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Chờ HR phê duyệt',
    YKienPheDuyet NVARCHAR(MAX),
    NguoiPheDuyet NVARCHAR(100)
);

IF OBJECT_ID(N'YeuCauTuyenDung', N'U') IS NULL
CREATE TABLE YeuCauTuyenDung(
    MaYC INT IDENTITY(1,1) PRIMARY KEY,
    MaPB NVARCHAR(50) NOT NULL REFERENCES PhongBan(MaPB) ON DELETE CASCADE ON UPDATE CASCADE,
    ViTri NVARCHAR(100) NOT NULL,
    SoLuong INT NOT NULL,
    YeuCau NVARCHAR(MAX),
    LyDo NVARCHAR(MAX),
    HanTuyen NVARCHAR(20),
    TrangThai NVARCHAR(50) DEFAULT N'Chờ duyệt'
);

IF OBJECT_ID(N'UngVien', N'U') IS NULL
CREATE TABLE UngVien(
    MaUV INT IDENTITY(1,1) PRIMARY KEY,
    MaYC INT REFERENCES YeuCauTuyenDung(MaYC) ON DELETE NO ACTION ON UPDATE NO ACTION,
    HoTen NVARCHAR(255) NOT NULL,
    Email NVARCHAR(100),
    SDT NVARCHAR(20),
    ViTriUngTuyen NVARCHAR(100) NOT NULL,
    MaPB NVARCHAR(50) REFERENCES PhongBan(MaPB) ON DELETE NO ACTION ON UPDATE NO ACTION,
    NgayPV NVARCHAR(25),
    NguoiPV NVARCHAR(100),
    KetQua NVARCHAR(50) DEFAULT N'Chờ phỏng vấn',
    NhanXet NVARCHAR(MAX)
);

IF OBJECT_ID(N'QuyTrinhNhanSu', N'U') IS NULL
CREATE TABLE QuyTrinhNhanSu(
    MaQT INT IDENTITY(1,1) PRIMARY KEY,
    MaNV NVARCHAR(50) NOT NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    Loai NVARCHAR(50) NOT NULL,
    NgayBD NVARCHAR(20) NOT NULL,
    TrangThai NVARCHAR(50) DEFAULT N'Đang thực hiện',
    CacBuocJson NVARCHAR(MAX),
    GhiChu NVARCHAR(MAX)
);

IF OBJECT_ID(N'NhatKyHoatDong', N'U') IS NULL
CREATE TABLE NhatKyHoatDong(
    MaNK INT IDENTITY(1,1) PRIMARY KEY,
    ThoiGian NVARCHAR(25) NOT NULL,
    NguoiDung NVARCHAR(100) NOT NULL,
    VaiTro NVARCHAR(50) NOT NULL,
    HanhDong NVARCHAR(100) NOT NULL,
    ChiTiet NVARCHAR(MAX),
    IP NVARCHAR(50)
);

IF OBJECT_ID(N'ChotCong', N'U') IS NULL
CREATE TABLE ChotCong(
    MaCC_Thang INT IDENTITY(1,1) PRIMARY KEY,
    ThangNam NVARCHAR(20) UNIQUE NOT NULL,
    NgayChot NVARCHAR(25) NOT NULL,
    NguoiChot NVARCHAR(100) NOT NULL,
    TongSoCong FLOAT DEFAULT 0,
    GhiChu NVARCHAR(MAX)
);
"""

def init_db():
    """Initialize the database (create database, schema, and sample data if needed)."""
    if DB_TYPE == 'mssql' and PYODBC_AVAILABLE:
        # Step 1: Ensure QLNhanSu_Nhom9 database exists on MSSQL server
        master_conn = pyodbc.connect(build_mssql_connection_string(database='master'), autocommit=True, timeout=10)
        master_cur = master_conn.cursor()
        master_cur.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{MSSQL_DATABASE}') CREATE DATABASE [{MSSQL_DATABASE}]")
        master_conn.close()

        # Step 2: Connect to the project database and create tables
        raw_conn = pyodbc.connect(build_mssql_connection_string(), timeout=10)
        db = ConnectionWrapper(raw_conn, is_mssql=True)

        for stmt in MSSQL_SCHEMA.split(';'):
            s = stmt.strip()
            if s:
                db.execute(s)
        db.commit()

        # Step 2.1: Schema migration for existing databases
        migrations = [
            "IF COL_LENGTH('NghiPhep', 'TrangThai') IS NULL ALTER TABLE NghiPhep ADD TrangThai NVARCHAR(50) DEFAULT N'Đã duyệt' WITH VALUES",
            "IF COL_LENGTH('NghiPhep', 'LyDo') IS NULL ALTER TABLE NghiPhep ADD LyDo NVARCHAR(255)",
            "IF COL_LENGTH('NhanVien', 'TrinhDo') IS NULL ALTER TABLE NhanVien ADD TrinhDo NVARCHAR(100)",
            "IF COL_LENGTH('NhanVien', 'ChuyenMon') IS NULL ALTER TABLE NhanVien ADD ChuyenMon NVARCHAR(100)",
            "IF COL_LENGTH('NhanVien', 'LoaiNhanVien') IS NULL ALTER TABLE NhanVien ADD LoaiNhanVien NVARCHAR(50) DEFAULT N'Chính thức' WITH VALUES",
            "IF COL_LENGTH('NhanVien', 'SoBHXH') IS NULL ALTER TABLE NhanVien ADD SoBHXH NVARCHAR(50)",
            "IF COL_LENGTH('NhanVien', 'MaSoThue') IS NULL ALTER TABLE NhanVien ADD MaSoThue NVARCHAR(50)",
            "IF COL_LENGTH('TangCa', 'TrangThai') IS NULL ALTER TABLE TangCa ADD TrangThai NVARCHAR(50) DEFAULT N'Đã duyệt' WITH VALUES",
            "IF COL_LENGTH('TangCa', 'LyDo') IS NULL ALTER TABLE TangCa ADD LyDo NVARCHAR(255)",
            "IF COL_LENGTH('TangCa', 'NguoiDuyet') IS NULL ALTER TABLE TangCa ADD NguoiDuyet NVARCHAR(100)",
            "IF COL_LENGTH('DanhGia', 'DiemTuDanhGia') IS NULL ALTER TABLE DanhGia ADD DiemTuDanhGia FLOAT",
            "IF COL_LENGTH('DanhGia', 'NhanXetCaNhan') IS NULL ALTER TABLE DanhGia ADD NhanXetCaNhan NVARCHAR(MAX)",
            "IF COL_LENGTH('Luong', 'BaoHiem') IS NULL ALTER TABLE Luong ADD BaoHiem FLOAT DEFAULT 0 WITH VALUES",
            "IF COL_LENGTH('Luong', 'ThueTNCN') IS NULL ALTER TABLE Luong ADD ThueTNCN FLOAT DEFAULT 0 WITH VALUES",
            "IF COL_LENGTH('Luong', 'KhauTruKhac') IS NULL ALTER TABLE Luong ADD KhauTruKhac FLOAT DEFAULT 0 WITH VALUES",
        ]
        for mig in migrations:
            db.execute(mig)
        db.commit()

        # Step 3: Seed initial data if TaiKhoanAdmin is empty
        admin_row = db.execute("SELECT 1 FROM TaiKhoanAdmin").fetchone()
        if not admin_row:
            db.execute("INSERT INTO TaiKhoanAdmin(TenDN, MatKhau) VALUES(?, ?)", ('admin', 'admin123'))

            db.executemany("INSERT INTO PhongBan VALUES(?, ?)", [
                ('PB01', 'Nhân sự'),
                ('PB02', 'Kế toán'),
                ('PB03', 'Kinh doanh'),
                ('PB04', 'Kỹ thuật')
            ])

            db.executemany("INSERT INTO ChucVu VALUES(?, ?, ?)", [
                ('CV01', 'Trưởng phòng', 'PB01'),
                ('CV02', 'Chuyên viên nhân sự', 'PB01'),
                ('CV03', 'Kế toán viên', 'PB02'),
                ('CV04', 'Nhân viên kinh doanh', 'PB03'),
                ('CV05', 'Lập trình viên', 'PB04')
            ])

            db.executemany("INSERT INTO NhanVien(MaNV, HoTen, DiaChi, SDT, CCCD, Email, NgaySinh, NgayVaoCT, GioiTinh, TrinhDo, ChuyenMon, LoaiNhanVien, SoBHXH, MaSoThue, MaCV) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                ('NV001', 'Nguyễn Văn An', 'Hà Nội', '0901000001', '001090000001', 'an@vnm.vn', '1985-03-12', '2015-06-01', 'Nam', 'Thạc sĩ', 'Quản trị nhân sự', 'Chính thức', 'BH001859', 'MST001859', 'CV01'),
                ('NV002', 'Trần Thị Bình', 'Hà Nội', '0901000002', '001090000002', 'binh@vnm.vn', '1992-07-21', '2019-02-15', 'Nữ', 'Đại học', 'Quản lý lao động', 'Chính thức', 'BH002927', 'MST002927', 'CV02'),
                ('NV003', 'Lê Minh Cường', 'Hải Phòng', '0901000003', '001090000003', 'cuong@vnm.vn', '1994-11-02', '2020-09-01', 'Nam', 'Đại học', 'Kế toán doanh nghiệp', 'Chính thức', 'BH003941', 'MST003941', 'CV03'),
                ('NV004', 'Phạm Thu Dung', 'Bắc Ninh', '0901000004', '001090000004', 'dung@vnm.vn', '1996-01-30', '2021-04-12', 'Nữ', 'Đại học', 'Quản trị kinh doanh', 'Chính thức', 'BH004961', 'MST004961', 'CV04'),
                ('NV005', 'Hoàng Quốc Em', 'Nam Định', '0901000005', '001090000005', 'em@vnm.vn', '1998-05-18', '2022-08-08', 'Nam', 'Đại học', 'Kỹ thuật phần mềm', 'Chính thức', 'BH005985', 'MST005985', 'CV05')
            ])

            db.executemany("INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES(?, ?, ?, ?)",
                [('ql001', '123456', 'NV001', QL)] + [(f'nv00{i}', '123456', f'NV00{i}', NV) for i in range(2, 6)]
            )

            current_month = date.today().strftime('%Y-%m')
            day_prefix = date.today().strftime('%Y-%m-')

            for i in range(1, 6):
                base_sal = 12000000 + i * 2000000
                bh = base_sal * 0.105
                db.execute(
                    "INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap, BaoHiem, ThueTNCN, KhauTruKhac) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (f'NV00{i}', current_month, base_sal, 1000000, 0, 500000, bh, 200000, 0)
                )

            db.execute("INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, TrangThai, LyDo) VALUES(?, ?, ?, N'Đã duyệt', N'Việc gia đình')", ('NV003', day_prefix + '03', day_prefix + '04'))
            db.execute("INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai, TrangThai, LyDo, NguoiDuyet) VALUES(?, ?, ?, ?, N'Đã duyệt', N'Fix lỗi hệ thống', N'Nguyễn Văn An')", ('NV005', 3, day_prefix + '05', 'Ngày thường'))

            db.executemany(
                "INSERT INTO HopDong(MaHD, MaNV, LoaiHD, NgayBD, NgayKT, LuongCoBan, TrangThai, GhiChu) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    ('HD001', 'NV001', 'Không xác định thời hạn', '2015-06-01', None, 14000000, 'Hiệu lực', 'Hợp đồng chính thức'),
                    ('HD002', 'NV002', 'Xác định thời hạn (3 năm)', '2019-02-15', '2022-02-15', 16000000, 'Hiệu lực', 'Tái ký hợp đồng'),
                    ('HD003', 'NV003', 'Xác định thời hạn (1 năm)', '2020-09-01', '2021-09-01', 18000000, 'Hiệu lực', 'Hợp đồng 1 năm'),
                    ('HD004', 'NV004', 'Xác định thời hạn (1 năm)', '2021-04-12', '2022-04-12', 20000000, 'Hiệu lực', 'Hợp đồng 1 năm'),
                    ('HD005', 'NV005', 'Thử việc', '2022-08-08', '2022-10-08', 22000000, 'Hiệu lực', 'Hợp đồng thử việc')
                ]
            )

        # Seed initial data for new tables if empty
        cc_count = db.execute("SELECT COUNT(*) FROM ChamCong").fetchone()[0]
        if cc_count == 0:
            today_str = date.today().strftime('%Y-%m-%d')
            sample_cc = [
                ('NV001', today_str, '08:00', '17:30', 'Đúng giờ', 'Chấm công máy vân tay'),
                ('NV002', today_str, '08:05', '17:30', 'Đúng giờ', 'Chấm công máy vân tay'),
                ('NV003', today_str, '08:25', '17:30', 'Đi muộn', 'Muộn 25 phút'),
                ('NV004', today_str, '07:55', '17:30', 'Đúng giờ', 'Chấm công máy vân tay'),
                ('NV005', today_str, '08:00', '16:30', 'Về sớm', 'Có việc gia đình')
            ]
            for mnv_c, d_c, in_c, out_c, st_c, nt_c in sample_cc:
                db.execute(
                    "INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu) VALUES(?, ?, ?, ?, ?, ?)",
                    (mnv_c, d_c, in_c, out_c, st_c, nt_c)
                )

        # Seed training courses
        kdt_count = db.execute("SELECT COUNT(*) FROM KhoaDaoTao").fetchone()[0]
        if kdt_count == 0:
            sample_kdt = [
                ('Quản trị hiệu suất và thiết lập mục tiêu OKR', 'TS. Trần Minh Khoa', '15/11/2026 - 18/11/2026', 'Phòng Hội nghị A', 35, 'Nâng cao kỹ năng thiết lập mục tiêu và đo lường kết quả công việc then chốt.', 'Sắp diễn ra'),
                ('Phát triển ứng dụng Web Hiện đại & An toàn thông tin', 'ThS. Lê Hoàng Long', '20/11/2026 - 25/11/2026', 'Phòng Lab Kỹ thuật', 25, 'Kiến trúc bảo mật, tối ưu hóa cơ sở dữ liệu và bảo mật ứng dụng.', 'Sắp diễn ra'),
                ('Văn hóa doanh nghiệp & Kỹ năng giao tiếp chuyên nghiệp', 'ThS. Nguyễn Lan Hương', '05/11/2026 - 06/11/2026', 'Hội trường Tầng 3', 50, 'Xây dựng môi trường làm việc cởi mở, chuyên nghiệp và gắn kết đội ngũ.', 'Đang diễn ra')
            ]
            for tk, gv, tg, dd, sl, mt, st in sample_kdt:
                db.execute(
                    "INSERT INTO KhoaDaoTao(TenKhoa, GiangVien, ThoiGian, DiaDiem, SoLuong, MoTa, TrangThai) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (tk, gv, tg, dd, sl, mt, st)
                )

        # Seed sample documents/certificates
        tl_count = db.execute("SELECT COUNT(*) FROM TaiLieuNhanVien").fetchone()[0]
        if tl_count == 0:
            sample_tl = [
                ('NV002', 'Bằng Cử nhân Quản trị Nhân lực', 'Bằng đại học', '2014-06-20', 'Đại học Kinh tế Quốc dân', None, '2026-10-01 09:00', 'Bằng tốt nghiệp loại Giỏi'),
                ('NV002', 'Chứng chỉ Tiếng Anh TOEIC 850', 'Chứng chỉ', '2023-04-10', 'IIG Vietnam', None, '2026-10-01 09:05', 'Hiệu lực 2 năm'),
                ('NV005', 'Bằng Kỹ sư Công nghệ Thông tin', 'Bằng đại học', '2020-07-15', 'Đại học Bách Khoa Hà Nội', None, '2026-10-02 10:00', 'Bằng tốt nghiệp loại Xuất sắc')
            ]
            for mnv_t, ten_t, loai_t, nc_t, noic_t, tep_t, nt_t, gc_t in sample_tl:
                db.execute(
                    "INSERT INTO TaiLieuNhanVien(MaNV, TenTaiLieu, Loai, NgayCap, NoiCap, TepDinhKem, NgayTai, GhiChu) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                    (mnv_t, ten_t, loai_t, nc_t, noic_t, tep_t, nt_t, gc_t)
                )

        # Seed sample rewards & discipline
        kt_count = db.execute("SELECT COUNT(*) FROM KhenThuongKyLuat").fetchone()[0]
        if kt_count == 0:
            db.execute(
                "INSERT INTO KhenThuongKyLuat(MaNV, Loai, SoQuyetDinh, NgayQuyetDinh, HinhThuc, SoTien, LyDo, NguoiKy) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                ('NV002', 'Khen thưởng', 'QĐ-KT/2026-08', '2026-08-15', 'Giấy khen và tiền thưởng', 2000000, 'Hoàn thành xuất sắc kế hoạch tuyển dụng nhân sự quý 2/2026', 'Ban Giám Đốc')
            )

        # Seed sample recruitment
        yc_count = db.execute("SELECT COUNT(*) FROM YeuCauTuyenDung").fetchone()[0]
        if yc_count == 0:
            db.execute(
                "INSERT INTO YeuCauTuyenDung(MaPB, ViTri, SoLuong, YeuCau, LyDo, HanTuyen, TrangThai) VALUES(?, ?, ?, ?, ?, ?, ?)",
                ('PB04', 'Kỹ sư Lập trình Fullstack', 2, 'Kinh nghiệm 2 năm Python/Flask, React, SQL Server.', 'Mở rộng dự án ERP', '2026-12-01', 'Đang tuyển')
            )
            y_id = db.execute("SELECT @@IDENTITY").fetchone()[0] if PYODBC_AVAILABLE else 1
            db.execute(
                "INSERT INTO UngVien(MaYC, HoTen, Email, SDT, ViTriUngTuyen, MaPB, NgayPV, NguoiPV, KetQua, NhanXet) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (y_id, 'Vũ Đình Mạnh', 'manh.vu@gmail.com', '0912345678', 'Kỹ sư Lập trình Fullstack', 'PB04', '2026-11-05 14:00', 'Nguyễn Văn An', 'Chờ phỏng vấn', 'Hồ sơ ứng viên tiềm năng')
            )

        # Seed sample shift assignments
        pc_count = db.execute("SELECT COUNT(*) FROM PhanCa").fetchone()[0]
        if pc_count == 0:
            today_str = date.today().strftime('%Y-%m-%d')
            for i in range(1, 6):
                db.execute(
                    "INSERT INTO PhanCa(MaNV, Ngay, CaLam, GhiChu) VALUES(?, ?, ?, ?)",
                    (f'NV00{i}', today_str, 'Ca hành chính (08:00 - 17:30)', 'Ca làm việc tiêu chuẩn')
                )

        db.commit()
        db.close()
