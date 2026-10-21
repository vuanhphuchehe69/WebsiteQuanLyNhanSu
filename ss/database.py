"""Database management supporting Microsoft SQL Server (MSSQL) with SQLite fallback."""
import sqlite3
from datetime import date
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
    Loai NVARCHAR(50)
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
        db.execute("IF COL_LENGTH('NghiPhep', 'TrangThai') IS NULL ALTER TABLE NghiPhep ADD TrangThai NVARCHAR(50) DEFAULT N'Đã duyệt' WITH VALUES")
        db.execute("IF COL_LENGTH('NghiPhep', 'LyDo') IS NULL ALTER TABLE NghiPhep ADD LyDo NVARCHAR(255)")
        db.execute("UPDATE NghiPhep SET TrangThai=N'Đã duyệt' WHERE TrangThai IS NULL")
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

            db.executemany("INSERT INTO NhanVien VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                ('NV001', 'Nguyễn Văn An', 'Hà Nội', '0901000001', '001090000001', 'an@vnm.vn', '1985-03-12', '2015-06-01', 'Nam', 'CV01'),
                ('NV002', 'Trần Thị Bình', 'Hà Nội', '0901000002', '001090000002', 'binh@vnm.vn', '1992-07-21', '2019-02-15', 'Nữ', 'CV02'),
                ('NV003', 'Lê Minh Cường', 'Hải Phòng', '0901000003', '001090000003', 'cuong@vnm.vn', '1994-11-02', '2020-09-01', 'Nam', 'CV03'),
                ('NV004', 'Phạm Thu Dung', 'Bắc Ninh', '0901000004', '001090000004', 'dung@vnm.vn', '1996-01-30', '2021-04-12', 'Nữ', 'CV04'),
                ('NV005', 'Hoàng Quốc Em', 'Nam Định', '0901000005', '001090000005', 'em@vnm.vn', '1998-05-18', '2022-08-08', 'Nam', 'CV05')
            ])

            db.executemany("INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES(?, ?, ?, ?)",
                [('ql001', '123456', 'NV001', QL)] + [(f'nv00{i}', '123456', f'NV00{i}', NV) for i in range(2, 6)]
            )

            current_month = date.today().strftime('%Y-%m')
            day_prefix = date.today().strftime('%Y-%m-')

            for i in range(1, 6):
                db.execute(
                    "INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap) VALUES(?, ?, ?, ?, ?, ?)",
                    (f'NV00{i}', current_month, 12000000 + i * 2000000, 1000000, 0, 500000)
                )

            db.execute("INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, TrangThai, LyDo) VALUES(?, ?, ?, N'Đã duyệt', N'Việc gia đình')", ('NV003', day_prefix + '03', day_prefix + '04'))
            db.execute("INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai) VALUES(?, ?, ?, ?)", ('NV005', 3, day_prefix + '05', 'Ngày thường'))

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

        db.commit()
        db.close()
