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

import re

def _clean_sql_for_sqlite(sql):
    """Normalize SQL syntax for SQLite compatibility when running without MSSQL."""
    if not sql:
        return sql
    # Strip N'...' -> '...'
    sql = re.sub(r"\bN'((?:[^']|'')*)'", r"'\1'", sql)
    # Quote datepart keyword in DATEDIFF for SQLite (e.g. DATEDIFF(day, ...) -> DATEDIFF('day', ...))
    sql = re.sub(r'\bDATEDIFF\s*\(\s*([a-zA-Z]+)\s*,', r"DATEDIFF('\1',", sql, flags=re.IGNORECASE)
    # Convert (SELECT TOP N ...) inside subqueries (handles nested parens like CAST(...))
    sql = re.sub(r'\(\s*SELECT\s+TOP\s+(\d+)\s+((?:[^()]+|\([^()]*\))*)\)', r'(SELECT \2 LIMIT \1)', sql, flags=re.IGNORECASE)
    # Convert outer SELECT TOP N ...
    if not sql.strip().startswith('('):
        top_match = re.search(r'^\s*SELECT\s+TOP\s+(\d+)\s+', sql, flags=re.IGNORECASE)
        if top_match:
            limit_val = top_match.group(1)
            sql = re.sub(r'^\s*SELECT\s+TOP\s+\d+\s+', 'SELECT ', sql, count=1, flags=re.IGNORECASE)
            if not re.search(r'\bLIMIT\b', sql, flags=re.IGNORECASE):
                sql = f"{sql} LIMIT {limit_val}"
    return sql

def setup_sqlite_conn(conn):
    """Register MSSQL compatibility functions in SQLite."""
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')

    def datediff_impl(unit, d1, d2):
        try:
            dt1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
            dt2 = datetime.strptime(str(d2)[:10], '%Y-%m-%d')
            return (dt2 - dt1).days
        except Exception:
            return 0

    def substring_impl(s, start, length=None):
        if s is None:
            return ''
        s_str = str(s)
        st = max(0, int(start) - 1)
        if length is not None:
            return s_str[st:st + int(length)]
        return s_str[st:]

    def concat_impl(*args):
        return ''.join(str(a) if a is not None else '' for a in args)

    conn.create_function('DATEDIFF', 3, datediff_impl)
    conn.create_function('SUBSTRING', 3, substring_impl)
    conn.create_function('SUBSTRING', 2, substring_impl)
    conn.create_function('CONCAT', -1, concat_impl)

class ConnectionWrapper:
    def __init__(self, raw_conn, is_mssql=True):
        self._conn = raw_conn
        self.is_mssql = is_mssql

    def execute(self, sql, params=None):
        if not self.is_mssql:
            sql = _clean_sql_for_sqlite(sql)
        cur = self._conn.cursor()
        if params is not None:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return CursorWrapper(cur)

    def executemany(self, sql, param_list):
        if not self.is_mssql:
            sql = _clean_sql_for_sqlite(sql)
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

_mssql_failed = False

def get_db():
    """Get or create database connection for the current Flask application context with automatic SQLite fallback."""
    global _mssql_failed
    if 'db' not in g:
        if DB_TYPE == 'mssql' and PYODBC_AVAILABLE and not _mssql_failed:
            try:
                raw_conn = pyodbc.connect(build_mssql_connection_string(), timeout=2, autocommit=True)
                g.db = ConnectionWrapper(raw_conn, is_mssql=True)
                return g.db
            except Exception as e:
                _mssql_failed = True
                print(f"[THÔNG BÁO CSDL] Không thể kết nối Microsoft SQL Server ({e}).\n-> Tự động chuyển sang chế độ SQLite ({DB_PATH}).")

        conn = sqlite3.connect(DB_PATH)
        setup_sqlite_conn(conn)
        init_sqlite_schema(conn)
        g.db = ConnectionWrapper(conn, is_mssql=False)
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
    HinhAnh NVARCHAR(500),
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
    MaNV NVARCHAR(50) NULL REFERENCES NhanVien(MaNV) ON DELETE CASCADE ON UPDATE CASCADE,
    LoaiTK NVARCHAR(50) NOT NULL CHECK(LoaiTK IN ('Admin', 'QuanLy', 'NhanVien'))
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

IF OBJECT_ID(N'ThongBaoDaDoc', N'U') IS NULL
CREATE TABLE ThongBaoDaDoc(
    MaTB INT NOT NULL,
    TenDN NVARCHAR(100) NOT NULL,
    ThoiGianDoc NVARCHAR(25) NOT NULL,
    CONSTRAINT PK_ThongBaoDaDoc PRIMARY KEY (MaTB, TenDN)
);
"""

def clean_all_duplicates(db):
    """Purge duplicate records across all core and transaction tables."""
    try:
        # Deduplicate TaiKhoan by TenDN
        db.execute("DELETE FROM TaiKhoan WHERE MaTK NOT IN (SELECT MIN(MaTK) FROM TaiKhoan GROUP BY TenDN);")
    except Exception:
        pass
    try:
        # Deduplicate ChamCong by MaNV, Ngay
        db.execute("DELETE FROM ChamCong WHERE MaCC NOT IN (SELECT MIN(MaCC) FROM ChamCong GROUP BY MaNV, Ngay);")
    except Exception:
        pass
    try:
        # Deduplicate Luong by MaNV, ThangNam
        db.execute("DELETE FROM Luong WHERE MaLuong NOT IN (SELECT MIN(MaLuong) FROM Luong GROUP BY MaNV, ThangNam);")
    except Exception:
        pass
    try:
        # Deduplicate HopDong by MaHD
        db.execute("DELETE FROM HopDong WHERE MaHD NOT IN (SELECT MIN(MaHD) FROM HopDong GROUP BY MaHD);")
    except Exception:
        pass
    try:
        # Deduplicate transactions
        db.execute("""
            DELETE FROM TangCa WHERE MaTC NOT IN (SELECT MIN(MaTC) FROM TangCa GROUP BY MaNV, Ngay, SoGio, LyDo);
            DELETE FROM TamUng WHERE MaTU NOT IN (SELECT MIN(MaTU) FROM TamUng GROUP BY MaNV, ThangNam, SoTien);
            DELETE FROM GiaiTrinhCong WHERE MaGT NOT IN (SELECT MIN(MaGT) FROM GiaiTrinhCong GROUP BY MaNV, Ngay, LyDo);
            DELETE FROM TaiLieuNhanVien WHERE MaTL NOT IN (SELECT MIN(MaTL) FROM TaiLieuNhanVien GROUP BY MaNV, TenTaiLieu);
        """)
    except Exception:
        pass
    try:
        # Deduplicate KhoaDaoTao, DangKyDaoTao, PhanCa
        db.execute("DELETE FROM KhoaDaoTao WHERE MaKDT NOT IN (SELECT MIN(MaKDT) FROM KhoaDaoTao GROUP BY TenKhoa);")
        db.execute("DELETE FROM DangKyDaoTao WHERE MaDK NOT IN (SELECT MIN(MaDK) FROM DangKyDaoTao GROUP BY MaKDT, MaNV);")
        db.execute("DELETE FROM PhanCa WHERE MaPC NOT IN (SELECT MIN(MaPC) FROM PhanCa GROUP BY MaNV, Ngay);")
    except Exception:
        pass
    try:
        # Deduplicate NhatKyHoatDong
        db.execute("DELETE FROM NhatKyHoatDong WHERE MaNK NOT IN (SELECT MIN(MaNK) FROM NhatKyHoatDong GROUP BY ThoiGian, NguoiDung, HanhDong);")
    except Exception:
        pass
    try:
        db.commit()
    except Exception:
        pass

def init_sqlite_schema(conn):
    """Create complete SQLite tables if running in SQLite fallback mode."""
    schema = """
    CREATE TABLE IF NOT EXISTS PhongBan(MaPB TEXT PRIMARY KEY, TenPB TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ChucVu(MaCV TEXT PRIMARY KEY, TenCV TEXT NOT NULL, MaPB TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS NhanVien(MaNV TEXT PRIMARY KEY, HoTen TEXT NOT NULL, DiaChi TEXT, SDT TEXT, CCCD TEXT UNIQUE, Email TEXT, NgaySinh TEXT, NgayVaoCT TEXT, GioiTinh TEXT, TrinhDo TEXT, ChuyenMon TEXT, LoaiNhanVien TEXT DEFAULT 'Chính thức', SoBHXH TEXT, MaSoThue TEXT, HinhAnh TEXT, MaCV TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS HopDong(MaHD TEXT PRIMARY KEY, MaNV TEXT NOT NULL, LoaiHD TEXT NOT NULL, NgayBD TEXT NOT NULL, NgayKT TEXT, LuongCoBan REAL DEFAULT 0, TrangThai TEXT DEFAULT 'Hiệu lực', GhiChu TEXT, HinhAnh TEXT);
    CREATE TABLE IF NOT EXISTS Luong(MaLuong INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, ThangNam TEXT NOT NULL, LuongCung REAL DEFAULT 0, LuongThuong REAL DEFAULT 0, LuongUngTruoc REAL DEFAULT 0, PhuCap REAL DEFAULT 0, BaoHiem REAL DEFAULT 0, ThueTNCN REAL DEFAULT 0, KhauTruKhac REAL DEFAULT 0, UNIQUE(MaNV, ThangNam));
    CREATE TABLE IF NOT EXISTS NghiPhep(MaNP INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, NgayBD TEXT NOT NULL, NgayKT TEXT NOT NULL, TrangThai TEXT DEFAULT 'Chờ duyệt', LyDo TEXT);
    CREATE TABLE IF NOT EXISTS TangCa(MaTC INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, SoGio REAL NOT NULL, Ngay TEXT NOT NULL, Loai TEXT, TrangThai TEXT DEFAULT 'Đã duyệt', LyDo TEXT, NguoiDuyet TEXT);
    CREATE TABLE IF NOT EXISTS ChamCong(MaCC INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, Ngay TEXT NOT NULL, GioVao TEXT, GioRa TEXT, TrangThai TEXT, GhiChu TEXT, UNIQUE(MaNV, Ngay));
    CREATE TABLE IF NOT EXISTS DanhGia(MaDG INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, ThangNam TEXT NOT NULL, DiemKPI REAL, XepLoai TEXT, NhanXet TEXT, NguoiDanhGia TEXT, DiemTuDanhGia REAL, NhanXetCaNhan TEXT, UNIQUE(MaNV, ThangNam));
    CREATE TABLE IF NOT EXISTS TaiLieuNhanVien(MaTL INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, TenTaiLieu TEXT NOT NULL, Loai TEXT, NgayCap TEXT, NoiCap TEXT, TepDinhKem TEXT, HinhAnh TEXT, NgayTai TEXT, GhiChu TEXT);
    CREATE TABLE IF NOT EXISTS GiaiTrinhCong(MaGT INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, Ngay TEXT NOT NULL, GioVaoDeXuat TEXT, GioRaDeXuat TEXT, LyDo TEXT, TrangThai TEXT DEFAULT 'Chờ duyệt', NguoiDuyet TEXT, NgayGui TEXT);
    CREATE TABLE IF NOT EXISTS KhenThuongKyLuat(MaKTKL INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, Loai TEXT, SoQuyetDinh TEXT, NgayQuyetDinh TEXT, HinhThuc TEXT, SoTien REAL DEFAULT 0, LyDo TEXT, NguoiKy TEXT);
    CREATE TABLE IF NOT EXISTS KhoaDaoTao(MaKDT INTEGER PRIMARY KEY AUTOINCREMENT, TenKhoa TEXT NOT NULL, GiangVien TEXT, ThoiGian TEXT, DiaDiem TEXT, SoLuong INTEGER, MoTa TEXT, TrangThai TEXT DEFAULT 'Sắp diễn ra');
    CREATE TABLE IF NOT EXISTS DangKyDaoTao(MaDK INTEGER PRIMARY KEY AUTOINCREMENT, MaKDT INTEGER NOT NULL, MaNV TEXT NOT NULL, NgayDangKy TEXT, TrangThai TEXT DEFAULT 'Đã đăng ký');
    CREATE TABLE IF NOT EXISTS DeXuatKhieuNai(MaDX INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, TieuDe TEXT NOT NULL, Loai TEXT, NoiDung TEXT, NgayGui TEXT, TrangThai TEXT DEFAULT 'Chờ xử lý', PhanHoi TEXT, NguoiXuLy TEXT);
    CREATE TABLE IF NOT EXISTS TamUng(MaTU INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, ThangNam TEXT NOT NULL, SoTien REAL NOT NULL, LyDo TEXT, NgayYeuCau TEXT, TrangThai TEXT DEFAULT 'Chờ duyệt', NguoiDuyet TEXT);
    CREATE TABLE IF NOT EXISTS PhanCa(MaPC INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, Ngay TEXT NOT NULL, CaLam TEXT, GhiChu TEXT);
    CREATE TABLE IF NOT EXISTS DeXuatNhanSu(MaDXNS INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, NguoiDeXuat TEXT, LoaiDeXuat TEXT, MucDeXuat TEXT, LyDo TEXT, NgayDeXuat TEXT, TrangThai TEXT DEFAULT 'Chờ HR phê duyệt', YKienPheDuyet TEXT, NguoiPheDuyet TEXT);
    CREATE TABLE IF NOT EXISTS YeuCauTuyenDung(MaYC INTEGER PRIMARY KEY AUTOINCREMENT, MaPB TEXT NOT NULL, ViTri TEXT NOT NULL, SoLuong INTEGER DEFAULT 1, YeuCau TEXT, LyDo TEXT, HanTuyen TEXT, TrangThai TEXT DEFAULT 'Chờ duyệt');
    CREATE TABLE IF NOT EXISTS UngVien(MaUV INTEGER PRIMARY KEY AUTOINCREMENT, MaYC INTEGER, HoTen TEXT NOT NULL, Email TEXT, SDT TEXT, ViTriUngTuyen TEXT, MaPB TEXT, NgayPV TEXT, NguoiPV TEXT, KetQua TEXT DEFAULT 'Chờ phỏng vấn', NhanXet TEXT);
    CREATE TABLE IF NOT EXISTS QuyTrinhNhanSu(MaQT INTEGER PRIMARY KEY AUTOINCREMENT, MaNV TEXT NOT NULL, Loai TEXT NOT NULL, NgayBD TEXT NOT NULL, TrangThai TEXT DEFAULT 'Đang thực hiện', GhiChu TEXT);
    CREATE TABLE IF NOT EXISTS NhatKyHoatDong(MaNK INTEGER PRIMARY KEY AUTOINCREMENT, ThoiGian TEXT NOT NULL, NguoiDung TEXT NOT NULL, VaiTro TEXT, HanhDong TEXT NOT NULL, ChiTiet TEXT, IP TEXT);
    CREATE TABLE IF NOT EXISTS ChotCong(MaCC_Thang INTEGER PRIMARY KEY AUTOINCREMENT, ThangNam TEXT NOT NULL UNIQUE, NgayChot TEXT NOT NULL, NguoiChot TEXT NOT NULL, TongSoCong REAL, GhiChu TEXT);
    CREATE TABLE IF NOT EXISTS ThongBao(MaTB INTEGER PRIMARY KEY AUTOINCREMENT, TieuDe TEXT NOT NULL, NoiDung TEXT NOT NULL, PhamVi TEXT DEFAULT 'Toàn công ty', MaPB TEXT, NguoiGui TEXT NOT NULL, NgayGui TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ThongBaoDaDoc(MaTB INTEGER NOT NULL, TenDN TEXT NOT NULL, ThoiGianDoc TEXT NOT NULL, PRIMARY KEY(MaTB, TenDN));
    CREATE TABLE IF NOT EXISTS TaiKhoanAdmin(MaTK INTEGER PRIMARY KEY AUTOINCREMENT, TenDN TEXT NOT NULL UNIQUE, MatKhau TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS TaiKhoan(MaTK INTEGER PRIMARY KEY AUTOINCREMENT, TenDN TEXT NOT NULL UNIQUE, MatKhau TEXT NOT NULL, MaNV TEXT, LoaiTK TEXT NOT NULL);
    """
    for stmt in schema.strip().split(';'):
        s = stmt.strip()
        if s:
            conn.execute(s)
    conn.commit()

def ensure_department_heads_and_staff(db):
    """Ensure all department heads (Trưởng phòng) and multiple departmental staff accounts exist."""
    # 1. Ensure Positions (Chức vụ) for all departments
    positions = [
        ('CV01', 'Trưởng phòng', 'PB01'),
        ('CV02', 'Chuyên viên nhân sự', 'PB01'),
        ('CV03', 'Kế toán viên', 'PB02'),
        ('CV04', 'Nhân viên kinh doanh', 'PB03'),
        ('CV05', 'Lập trình viên', 'PB04'),
        ('CV06', 'Trưởng phòng Kế toán', 'PB02'),
        ('CV07', 'Trưởng phòng Kinh doanh', 'PB03'),
        ('CV08', 'Trưởng phòng Kỹ thuật', 'PB04'),
        ('CV09', 'Kế toán tổng hợp', 'PB02'),
        ('CV10', 'Chuyên viên Marketing', 'PB03'),
        ('CV11', 'Kỹ sư Kiểm thử (QA)', 'PB04'),
        ('CV12', 'Kỹ sư DevOps', 'PB04'),
        ('CV13', 'Chuyên viên Tuyển dụng', 'PB01')
    ]
    for mcv, tencv, mapb in positions:
        row = db.execute("SELECT 1 FROM ChucVu WHERE MaCV=?", (mcv,)).fetchone()
        if not row:
            db.execute("INSERT INTO ChucVu(MaCV, TenCV, MaPB) VALUES(?, ?, ?)", (mcv, tencv, mapb))

    # 2. Ensure Employees (Nhân viên)
    employees = [
        ('NV001', 'Nguyễn Văn An', 'Hà Nội', '0901000001', '001090000001', 'an@vnm.vn', '1985-03-12', '2015-06-01', 'Nam', 'Thạc sĩ', 'Quản trị nhân sự', 'Chính thức', 'BH001859', 'MST001859', '/static/uploads/avatars/avatar_NV001.svg', 'CV01'),
        ('NV002', 'Trần Thị Bình', 'Hà Nội', '0901000002', '001090000002', 'binh@vnm.vn', '1992-07-21', '2019-02-15', 'Nữ', 'Đại học', 'Quản lý lao động', 'Chính thức', 'BH002927', 'MST002927', '/static/uploads/avatars/avatar_NV002.svg', 'CV02'),
        ('NV003', 'Lê Minh Cường', 'Hải Phòng', '0901000003', '001090000003', 'cuong@vnm.vn', '1994-11-02', '2020-09-01', 'Nam', 'Đại học', 'Kế toán doanh nghiệp', 'Chính thức', 'BH003941', 'MST003941', '/static/uploads/avatars/avatar_NV003.svg', 'CV03'),
        ('NV004', 'Phạm Thu Dung', 'Bắc Ninh', '0901000004', '001090000004', 'dung@vnm.vn', '1996-01-30', '2021-04-12', 'Nữ', 'Đại học', 'Quản trị kinh doanh', 'Chính thức', 'BH004961', 'MST004961', '/static/uploads/avatars/avatar_NV004.svg', 'CV04'),
        ('NV005', 'Hoàng Quốc Em', 'Nam Định', '0901000005', '001090000005', 'em@vnm.vn', '1998-05-18', '2022-08-08', 'Nam', 'Đại học', 'Kỹ thuật phần mềm', 'Chính thức', 'BH005985', 'MST005985', '/static/uploads/avatars/avatar_NV005.svg', 'CV05'),
        ('NV006', 'Vũ Thị Hoa', 'Hà Nội', '0901000006', '001090000006', 'hoa.vu@vnm.vn', '1988-04-15', '2017-03-01', 'Nữ', 'Thạc sĩ', 'Tài chính kế toán', 'Chính thức', 'BH006123', 'MST006123', '/static/uploads/avatars/avatar_NV006.svg', 'CV06'),
        ('NV007', 'Bùi Quang Huy', 'Hải Phòng', '0901000007', '001090000007', 'huy.bui@vnm.vn', '1989-08-20', '2018-05-10', 'Nam', 'Thạc sĩ', 'Quản trị kinh doanh', 'Chính thức', 'BH007234', 'MST007234', '/static/uploads/avatars/avatar_NV007.svg', 'CV07'),
        ('NV008', 'Đỗ Hoàng Long', 'Hà Nội', '0901000008', '001090000008', 'long.do@vnm.vn', '1987-11-12', '2016-10-01', 'Nam', 'Thạc sĩ', 'Công nghệ thông tin', 'Chính thức', 'BH008345', 'MST008345', '/static/uploads/avatars/avatar_NV008.svg', 'CV08'),
        ('NV009', 'Trương Mai Phương', 'Nam Định', '0901000009', '001090000009', 'phuong.truong@vnm.vn', '1995-02-18', '2021-06-15', 'Nữ', 'Đại học', 'Kiểm toán', 'Chính thức', 'BH009456', 'MST009456', '/static/uploads/avatars/avatar_NV009.svg', 'CV09'),
        ('NV010', 'Nguyễn Đức Thắng', 'Bắc Ninh', '0901000010', '001090000010', 'thang.nguyen@vnm.vn', '1997-09-05', '2022-01-10', 'Nam', 'Đại học', 'Marketing số', 'Chính thức', 'BH010567', 'MST010567', '/static/uploads/avatars/avatar_NV010.svg', 'CV10'),
        ('NV011', 'Lý Thu Trang', 'Hà Nội', '0901000011', '001090000011', 'trang.ly@vnm.vn', '1996-12-25', '2021-09-01', 'Nữ', 'Đại học', 'Đảm bảo chất lượng phần mềm', 'Chính thức', 'BH011678', 'MST011678', '/static/uploads/avatars/avatar_NV011.svg', 'CV11'),
        ('NV012', 'Vũ Tuấn Kiệt', 'Hải Dương', '0901000012', '001090000012', 'kiet.vu@vnm.vn', '1998-07-14', '2023-03-01', 'Nam', 'Đại học', 'Điện toán đám mây & DevOps', 'Chính thức', 'BH012789', 'MST012789', '/static/uploads/avatars/avatar_NV012.svg', 'CV12'),
        ('NV013', 'Phan Mỹ Linh', 'Hà Nội', '0901000013', '001090000013', 'linh.phan@vnm.vn', '1999-03-30', '2023-07-15', 'Nữ', 'Đại học', 'Quản trị nhân sự', 'Chính thức', 'BH013890', 'MST013890', '/static/uploads/avatars/avatar_NV013.svg', 'CV13')
    ]
    for emp in employees:
        row = db.execute("SELECT 1 FROM NhanVien WHERE MaNV=?", (emp[0],)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO NhanVien(MaNV, HoTen, DiaChi, SDT, CCCD, Email, NgaySinh, NgayVaoCT, GioiTinh, TrinhDo, ChuyenMon, LoaiNhanVien, SoBHXH, MaSoThue, HinhAnh, MaCV)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, emp)
        else:
            db.execute("UPDATE NhanVien SET HinhAnh=? WHERE (HinhAnh IS NULL OR HinhAnh='') AND MaNV=?", (emp[14], emp[0]))

    # 3. Ensure Contracts (Hợp đồng)
    contracts = [
        ('HD006', 'NV006', 'Không xác định thời hạn', '2017-03-01', None, 22000000, 'Hiệu lực', 'Hợp đồng cán bộ quản lý'),
        ('HD007', 'NV007', 'Không xác định thời hạn', '2018-05-10', None, 24000000, 'Hiệu lực', 'Hợp đồng cán bộ quản lý'),
        ('HD008', 'NV008', 'Không xác định thời hạn', '2016-10-01', None, 26000000, 'Hiệu lực', 'Hợp đồng cán bộ quản lý'),
        ('HD009', 'NV009', 'Xác định thời hạn (3 năm)', '2021-06-15', '2024-06-15', 17000000, 'Hiệu lực', 'Tái ký hợp đồng'),
        ('HD010', 'NV010', 'Xác định thời hạn (1 năm)', '2022-01-10', '2023-01-10', 16000000, 'Hiệu lực', 'Hợp đồng 1 năm'),
        ('HD011', 'NV011', 'Xác định thời hạn (1 năm)', '2021-09-01', '2022-09-01', 18000000, 'Hiệu lực', 'Hợp đồng 1 năm'),
        ('HD012', 'NV012', 'Xác định thời hạn (1 năm)', '2023-03-01', '2024-03-01', 19000000, 'Hiệu lực', 'Hợp đồng 1 năm'),
        ('HD013', 'NV013', 'Xác định thời hạn (1 năm)', '2023-07-15', '2024-07-15', 15000000, 'Hiệu lực', 'Hợp đồng 1 năm')
    ]
    for hd in contracts:
        row = db.execute("SELECT 1 FROM HopDong WHERE MaHD=?", (hd[0],)).fetchone()
        if not row:
            db.execute("INSERT INTO HopDong(MaHD, MaNV, LoaiHD, NgayBD, NgayKT, LuongCoBan, TrangThai, GhiChu) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", hd)

    # 4. Ensure Salaries (Lương) for current month
    current_month = date.today().strftime('%Y-%m')
    for hd in contracts:
        mnv_i = hd[1]
        base_sal = hd[5]
        bh = round(base_sal * 0.105, 0)
        thue = round((base_sal - 11000000) * 0.05, 0) if base_sal > 11000000 else 0
        if not db.execute("SELECT 1 FROM Luong WHERE MaNV=? AND ThangNam=?", (mnv_i, current_month)).fetchone():
            db.execute(
                "INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap, BaoHiem, ThueTNCN, KhauTruKhac) VALUES(?, ?, ?, 1000000, 0, 500000, ?, ?, 0)",
                (mnv_i, current_month, base_sal, bh, thue)
            )

    # 5. Ensure Attendance (Chấm công hôm nay)
    today_str = date.today().strftime('%Y-%m-%d')
    for i in range(6, 14):
        mnv_i = f'NV{i:03d}'
        if not db.execute("SELECT 1 FROM ChamCong WHERE MaNV=? AND Ngay=?", (mnv_i, today_str)).fetchone():
            db.execute(
                "INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu) VALUES(?, ?, '08:00', '17:30', 'Đúng giờ', 'Chấm công máy vân tay')",
                (mnv_i, today_str)
            )

    # 6. Ensure Accounts (Tài khoản) - Username = Mã nhân viên, Mật khẩu = 123456
    # Trưởng phòng: LoaiTK = 'QuanLy'
    # Nhân viên: LoaiTK = 'NhanVien'
    accounts = [
        # Trưởng phòng (Quản lý)
        ('nv001', '123456', 'NV001', 'QuanLy'),
        ('ql001', '123456', 'NV001', 'QuanLy'),
        ('nv006', '123456', 'NV006', 'QuanLy'),
        ('nv007', '123456', 'NV007', 'QuanLy'),
        ('nv008', '123456', 'NV008', 'QuanLy'),
        # Nhân viên các phòng ban khác
        ('nv002', '123456', 'NV002', 'NhanVien'),
        ('nv003', '123456', 'NV003', 'NhanVien'),
        ('nv004', '123456', 'NV004', 'NhanVien'),
        ('nv005', '123456', 'NV005', 'NhanVien'),
        ('nv009', '123456', 'NV009', 'NhanVien'),
        ('nv010', '123456', 'NV010', 'NhanVien'),
        ('nv011', '123456', 'NV011', 'NhanVien'),
        ('nv012', '123456', 'NV012', 'NhanVien'),
        ('nv013', '123456', 'NV013', 'NhanVien'),
    ]
    for tdn, mk, mnv_acc, loai in accounts:
        acc_row = db.execute("SELECT MaTK FROM TaiKhoan WHERE TenDN=?", (tdn,)).fetchone()
        if not acc_row:
            db.execute("INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES(?, ?, ?, ?)", (tdn, mk, mnv_acc, loai))
        else:
            db.execute("UPDATE TaiKhoan SET MatKhau=?, MaNV=?, LoaiTK=? WHERE TenDN=?", (mk, mnv_acc, loai, tdn))

    # 7. Ensure Corporate Training & Shifts
    ensure_training_and_shifts(db)

    db.commit()

def ensure_training_and_shifts(db):
    """Ensure sample courses, registrations, and shifts exist."""
    courses = [
        ('An toàn thông tin & Bảo mật dữ liệu doanh nghiệp (ISO 27001)', 'TS. Nguyễn Văn Hưng (Chuyên gia An ninh mạng)', 'Thứ 7 hàng tuần (08:30 - 11:30)', 'Hội trường Tầng 5 - Trụ sở chính', 50, 'Trang bị kiến thức phòng vệ mã độc, lừa đảo phishing, mã hóa dữ liệu khách hàng và tuân thủ tiêu chuẩn an ninh thông tin ISO 27001.', 'Đang diễn ra'),
        ('Kỹ năng giao tiếp, lắng nghe & Đàm phán trong công sở', 'ThS. Lê Hoàng Yến (Chuyên gia Dale Carnegie)', '18:30 - 20:30 (Thứ 3 & Thứ 5)', 'Phòng Đào tạo A201', 40, 'Nâng cao năng lực kết nối đồng nghiệp, thấu hiểu khách hàng, giải quyết xung đột tích cực và nghệ thuật thuyết phục trong đàm phán hợp đồng.', 'Sắp diễn ra'),
        ('Quản trị dự án Agile & Scrum thực chiến', 'Chuyên gia Scrum Master Trần Quốc Toản', 'Chủ nhật cả ngày (09:00 - 17:00)', 'Trung tâm Hội thảo Innovation Hub Tầng 3', 35, 'Ứng dụng thực tế Jira, Sprint Planning, Daily Scrum, Retrospective và User Story Mapping vào vận hành dự án công nghệ & kinh doanh.', 'Đang diễn ra'),
        ('Ứng dụng Trí tuệ Nhân tạo (Generative AI) nâng cao hiệu suất làm việc', 'Kỹ sư AI Phan Thanh Hải (AI Research Lead)', 'Thứ 6 (14:00 - 17:00)', 'Phòng Lab Công nghệ Tầng 4', 45, 'Khai thác ChatGPT, Claude và GitHub Copilot để soạn thảo văn bản, phân tích dữ liệu, tự động hóa tác vụ lặp và tối ưu hóa quy trình làm việc.', 'Sắp diễn ra'),
        ('Kỹ năng thuyết trình chuyên nghiệp và làm chủ cuộc họp', 'ThS. Đoàn Minh Tâm (Giảng viên Kỹ năng truyền thông)', 'Thứ 7 (13:30 - 17:00)', 'Hội trường Tầng 5', 40, 'Kỹ thuật diễn đạt gãy gọn, thiết kế slide trực quan ấn tượng và nghệ thuật điều phối tương tác trong các cuộc họp điều hành quan trọng.', 'Sắp diễn ra'),
        ('Quản trị tài chính cá nhân & Lập kế hoạch ngân sách phòng ban', 'CPA Phạm Minh Tú (Giám đốc Tài chính CFO Club)', 'Chủ nhật (08:30 - 11:30)', 'Phòng Hội nghị B302', 30, 'Kiểm soát dòng tiền cá nhân và doanh nghiệp, dự toán ngân sách hoạt động, tối ưu chi phí và phân tích báo cáo tài chính quản trị.', 'Hoàn thành'),
        ('Phân tích dữ liệu kinh doanh & Dashboard trực quan với Microsoft Power BI', 'ThS. Vũ Thành Đạt (Data Analytics Specialist)', 'Thứ 2 & Thứ 4 (18:30 - 21:00)', 'Phòng Lab Máy tính Tầng 3', 35, 'Thực hành xây dựng mô hình dữ liệu (Data Modeling), viết hàm DAX và thiết kế dashboard tương tác trực quan cho báo cáo kinh doanh & nhân sự.', 'Sắp diễn ra'),
        ('Kỹ năng lãnh đạo & Phát triển năng lực nhân viên dành cho Quản lý', 'TS. Hoàng Thu Thảo (Cố vấn Quản trị Nhân sự VCCI)', 'Thứ 7 (09:00 - 16:30)', 'Phòng Hội thảo Executive B401', 25, 'Phát triển tư duy lãnh đạo dẫn dắt, kỹ năng giao việc & ủy quyền, coaching nhân viên và xây dựng văn hóa đội ngũ gắn kết vững mạnh.', 'Đang diễn ra')
    ]

    for ten_k, gv_k, tg_k, dd_k, sl_k, mt_k, tt_k in courses:
        try:
            row = db.execute("SELECT 1 FROM KhoaDaoTao WHERE TenKhoa = ?", (ten_k,)).fetchone()
            if not row:
                db.execute("""
                    INSERT INTO KhoaDaoTao(TenKhoa, GiangVien, ThoiGian, DiaDiem, SoLuong, MoTa, TrangThai)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                """, (ten_k, gv_k, tg_k, dd_k, sl_k, mt_k, tt_k))
        except Exception:
            pass

    # Ensure registrations
    try:
        cnt_dk = db.execute("SELECT COUNT(*) FROM DangKyDaoTao").fetchone()[0]
    except Exception:
        cnt_dk = 0

    if cnt_dk < 20:
        try:
            kdt_rows = db.execute("SELECT MaKDT, TenKhoa FROM KhoaDaoTao ORDER BY MaKDT").fetchall()
            kdt_map = {kr['TenKhoa']: kr['MaKDT'] for kr in kdt_rows}
            sample_dk = [
                (courses[0][0], 'NV001', '2026-10-15 08:30', 'Đang học'),
                (courses[0][0], 'NV005', '2026-10-15 09:15', 'Đang học'),
                (courses[0][0], 'NV008', '2026-10-15 10:20', 'Đang học'),
                (courses[0][0], 'NV011', '2026-10-15 11:00', 'Đang học'),
                (courses[0][0], 'NV012', '2026-10-15 14:10', 'Đang học'),
                (courses[0][0], 'NV006', '2026-10-15 15:30', 'Đang học'),
                (courses[1][0], 'NV002', '2026-10-16 10:00', 'Đã đăng ký'),
                (courses[1][0], 'NV004', '2026-10-16 14:20', 'Đã đăng ký'),
                (courses[1][0], 'NV007', '2026-10-16 15:00', 'Đã đăng ký'),
                (courses[1][0], 'NV010', '2026-10-16 16:45', 'Đã đăng ký'),
                (courses[1][0], 'NV013', '2026-10-16 17:10', 'Đã đăng ký'),
                (courses[2][0], 'NV005', '2026-10-17 08:45', 'Đang học'),
                (courses[2][0], 'NV008', '2026-10-17 09:30', 'Đang học'),
                (courses[2][0], 'NV011', '2026-10-17 10:15', 'Đang học'),
                (courses[2][0], 'NV012', '2026-10-17 11:40', 'Đang học'),
                (courses[2][0], 'NV010', '2026-10-17 14:00', 'Đang học'),
                (courses[3][0], 'NV001', '2026-10-18 09:00', 'Đã đăng ký'),
                (courses[3][0], 'NV002', '2026-10-18 09:40', 'Đã đăng ký'),
                (courses[3][0], 'NV004', '2026-10-18 10:25', 'Đã đăng ký'),
                (courses[3][0], 'NV005', '2026-10-18 11:10', 'Đã đăng ký'),
                (courses[3][0], 'NV007', '2026-10-18 14:15', 'Đã đăng ký'),
                (courses[3][0], 'NV009', '2026-10-18 15:00', 'Đã đăng ký'),
                (courses[3][0], 'NV010', '2026-10-18 15:45', 'Đã đăng ký'),
                (courses[3][0], 'NV012', '2026-10-18 16:30', 'Đã đăng ký'),
                (courses[4][0], 'NV002', '2026-10-19 09:30', 'Đã đăng ký'),
                (courses[4][0], 'NV004', '2026-10-19 10:15', 'Đã đăng ký'),
                (courses[4][0], 'NV007', '2026-10-19 11:00', 'Đã đăng ký'),
                (courses[4][0], 'NV013', '2026-10-19 14:30', 'Đã đăng ký'),
                (courses[5][0], 'NV003', '2026-09-05 08:30', 'Hoàn thành'),
                (courses[5][0], 'NV006', '2026-09-05 09:15', 'Hoàn thành'),
                (courses[5][0], 'NV009', '2026-09-05 10:00', 'Hoàn thành'),
                (courses[5][0], 'NV007', '2026-09-05 14:00', 'Hoàn thành'),
                (courses[5][0], 'NV001', '2026-09-05 15:30', 'Hoàn thành'),
                (courses[6][0], 'NV003', '2026-10-20 09:10', 'Đã đăng ký'),
                (courses[6][0], 'NV004', '2026-10-20 10:00', 'Đã đăng ký'),
                (courses[6][0], 'NV009', '2026-10-20 11:30', 'Đã đăng ký'),
                (courses[6][0], 'NV010', '2026-10-20 14:15', 'Đã đăng ký'),
                (courses[6][0], 'NV002', '2026-10-20 16:00', 'Đã đăng ký'),
                (courses[7][0], 'NV001', '2026-10-21 08:45', 'Đang học'),
                (courses[7][0], 'NV006', '2026-10-21 09:30', 'Đang học'),
                (courses[7][0], 'NV007', '2026-10-21 10:15', 'Đang học'),
                (courses[7][0], 'NV008', '2026-10-21 11:00', 'Đang học'),
            ]
            for tk, mnv_d, ng_d, tt_d in sample_dk:
                kid = kdt_map.get(tk)
                if kid and not db.execute("SELECT 1 FROM DangKyDaoTao WHERE MaKDT=? AND MaNV=?", (kid, mnv_d)).fetchone():
                    db.execute("INSERT INTO DangKyDaoTao(MaKDT, MaNV, NgayDangKy, TrangThai) VALUES(?, ?, ?, ?)", (kid, mnv_d, ng_d, tt_d))
        except Exception:
            pass

    # Ensure shifts
    try:
        cnt_pc = db.execute("SELECT COUNT(*) FROM PhanCa").fetchone()[0]
    except Exception:
        cnt_pc = 0

    if cnt_pc < 50:
        try:
            from datetime import timedelta
            start_shift_date = date(2026, 11, 1)
            shift_dates_14 = [(start_shift_date + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(14)]
            for d_idx, d_str in enumerate(shift_dates_14):
                day_num = d_idx + 1
                shifts_day = [
                    ('NV001', 'Ca hành chính (08:00 - 17:30)', 'Quản lý và điều hành nhân sự toàn công ty'),
                    ('NV002', 'Ca hành chính (08:00 - 17:30)', 'Trực tiếp nhận hồ sơ, BHXH và hợp đồng lao động'),
                    ('NV013', 'Ca hành chính (08:00 - 17:30)', 'Tổ chức phỏng vấn và tiếp đón ứng viên mới'),
                    ('NV006', 'Ca hành chính (08:00 - 17:30)', 'Phê duyệt chứng từ tài chính và dòng tiền'),
                    ('NV003', 'Ca hành chính (08:00 - 17:30)', 'Đối soát hóa đơn và hạch toán sổ sách hàng ngày'),
                    ('NV009', 'Ca hành chính (08:00 - 17:30)', 'Báo cáo thuế, tài sản cố định và chi phí vận hành'),
                    ('NV007', 'Ca hành chính (08:00 - 17:30)', 'Chỉ đạo kinh doanh và đàm phán hợp đồng lớn'),
                    ('NV004', 'Ca sáng (06:00 - 14:00)' if day_num % 2 == 1 else 'Ca chiều (14:00 - 22:00)',
                     'Trực tổng đài tư vấn khách hàng ca sáng' if day_num % 2 == 1 else 'Chăm sóc khách hàng VIP và chốt hợp đồng'),
                    ('NV010', 'Ca chiều (14:00 - 22:00)' if day_num in (6, 7, 13, 14) else 'Ca hành chính (08:00 - 17:30)',
                     'Quản lý sự kiện hội thảo trực tuyến cuối tuần' if day_num in (6, 7, 13, 14) else 'Vận hành chiến dịch truyền thông đa kênh'),
                    ('NV008', 'Ca hành chính (08:00 - 17:30)', 'Giám sát hạ tầng kỹ thuật và điều phối sprint'),
                    ('NV005', [('Ca sáng (06:00 - 14:00)', 'Release mã nguồn và kiểm tra hiệu năng hệ thống'),
                               ('Ca chiều (14:00 - 22:00)', 'Xử lý sự cố ứng dụng và hỗ trợ tích hợp API'),
                               ('Ca hành chính (08:00 - 17:30)', 'Phát triển tính năng sprint mới theo Jira'),
                               ('Ca đêm (22:00 - 06:00)', 'Trực giám sát vận hành hạ tầng máy chủ 24/7')][d_idx % 4][0],
                              [('Ca sáng (06:00 - 14:00)', 'Release mã nguồn và kiểm tra hiệu năng hệ thống'),
                               ('Ca chiều (14:00 - 22:00)', 'Xử lý sự cố ứng dụng và hỗ trợ tích hợp API'),
                               ('Ca hành chính (08:00 - 17:30)', 'Phát triển tính năng sprint mới theo Jira'),
                               ('Ca đêm (22:00 - 06:00)', 'Trực giám sát vận hành hạ tầng máy chủ 24/7')][d_idx % 4][1]),
                    ('NV011', 'Ca sáng (06:00 - 14:00)' if day_num % 2 == 1 else 'Ca hành chính (08:00 - 17:30)',
                     'Kiểm thử nghiệm thu sản phẩm trước giờ phát hành' if day_num % 2 == 1 else 'Thực hiện test case hồi quy tự động'),
                    ('NV012', [('Ca chiều (14:00 - 22:00)', 'Giám sát hệ thống Cloud Kubernetes và container'),
                               ('Ca đêm (22:00 - 06:00)', 'Sao lưu dữ liệu định kỳ và rà quét bảo mật máy chủ'),
                               ('Ca hành chính (08:00 - 17:30)', 'Cấu hình tối ưu đường ống CI/CD GitLab/Docker')][d_idx % 3][0],
                              [('Ca chiều (14:00 - 22:00)', 'Giám sát hệ thống Cloud Kubernetes và container'),
                               ('Ca đêm (22:00 - 06:00)', 'Sao lưu dữ liệu định kỳ và rà quét bảo mật máy chủ'),
                               ('Ca hành chính (08:00 - 17:30)', 'Cấu hình tối ưu đường ống CI/CD GitLab/Docker')][d_idx % 3][1]),
                ]
                for mnv_s, ca_s, gc_s in shifts_day:
                    if not db.execute("SELECT 1 FROM PhanCa WHERE MaNV=? AND Ngay=?", (mnv_s, d_str)).fetchone():
                        db.execute("INSERT INTO PhanCa(MaNV, Ngay, CaLam, GhiChu) VALUES(?, ?, ?, ?)", (mnv_s, d_str, ca_s, gc_s))
        except Exception:
            pass

    db.commit()

def init_db():
    """Initialize the database (create database, schema, and sample data if needed)."""
    global _mssql_failed
    db = None
    if DB_TYPE == 'mssql' and PYODBC_AVAILABLE and not _mssql_failed:
        try:
            # Step 1: Ensure QLNhanSuNhom2 database exists on MSSQL server
            master_conn = pyodbc.connect(build_mssql_connection_string(database='master'), autocommit=True, timeout=2)
            master_cur = master_conn.cursor()
            master_cur.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{MSSQL_DATABASE}') CREATE DATABASE [{MSSQL_DATABASE}]")
            master_conn.close()

            # Step 2: Connect to the project database and create tables
            raw_conn = pyodbc.connect(build_mssql_connection_string(), timeout=2)
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
                "IF COL_LENGTH('NhanVien', 'HinhAnh') IS NULL ALTER TABLE NhanVien ADD HinhAnh NVARCHAR(500)",
                "IF COL_LENGTH('TangCa', 'TrangThai') IS NULL ALTER TABLE TangCa ADD TrangThai NVARCHAR(50) DEFAULT N'Đã duyệt' WITH VALUES",
                "IF COL_LENGTH('TangCa', 'LyDo') IS NULL ALTER TABLE TangCa ADD LyDo NVARCHAR(255)",
                "IF COL_LENGTH('TangCa', 'NguoiDuyet') IS NULL ALTER TABLE TangCa ADD NguoiDuyet NVARCHAR(100)",
                "IF COL_LENGTH('DanhGia', 'DiemTuDanhGia') IS NULL ALTER TABLE DanhGia ADD DiemTuDanhGia FLOAT",
                "IF COL_LENGTH('DanhGia', 'NhanXetCaNhan') IS NULL ALTER TABLE DanhGia ADD NhanXetCaNhan NVARCHAR(MAX)",
                "IF COL_LENGTH('Luong', 'BaoHiem') IS NULL ALTER TABLE Luong ADD BaoHiem FLOAT DEFAULT 0 WITH VALUES",
                "IF COL_LENGTH('Luong', 'ThueTNCN') IS NULL ALTER TABLE Luong ADD ThueTNCN FLOAT DEFAULT 0 WITH VALUES",
                "IF COL_LENGTH('Luong', 'KhauTruKhac') IS NULL ALTER TABLE Luong ADD KhauTruKhac FLOAT DEFAULT 0 WITH VALUES",
                "IF COL_LENGTH('HopDong', 'HinhAnh') IS NULL ALTER TABLE HopDong ADD HinhAnh NVARCHAR(500)",
                "IF COL_LENGTH('TaiLieuNhanVien', 'HinhAnh') IS NULL ALTER TABLE TaiLieuNhanVien ADD HinhAnh NVARCHAR(500)",
            ]
            for mig in migrations:
                db.execute(mig)
            db.commit()

            # Update avatars for default staff if currently empty
            for m in ('NV001', 'NV002', 'NV003', 'NV004', 'NV005'):
                db.execute("UPDATE NhanVien SET HinhAnh=? WHERE (HinhAnh IS NULL OR HinhAnh='') AND MaNV=?", (f'/static/uploads/avatars/avatar_{m}.svg', m))
            db.commit()

            # Correct any corrupted LuongCung (restore to exact contract LuongCoBan)
            db.execute("""
                UPDATE l
                SET l.LuongCung = h.LuongCoBan,
                    l.BaoHiem = ROUND(h.LuongCoBan * 0.105, 0)
                FROM Luong l
                JOIN HopDong h ON l.MaNV = h.MaNV AND h.TrangThai = N'Hiệu lực'
                WHERE l.LuongCung < 10000000
            """)
            db.commit()

            # Ensure TaiKhoan allows Admin role and NULL MaNV
            try:
                db.execute("""
                    DECLARE @chk_name NVARCHAR(256);
                    SELECT @chk_name = name FROM sys.check_constraints WHERE parent_object_id = OBJECT_ID('TaiKhoan') AND definition LIKE '%LoaiTK%';
                    IF @chk_name IS NOT NULL
                        EXEC('ALTER TABLE TaiKhoan DROP CONSTRAINT ' + @chk_name);
                    ALTER TABLE TaiKhoan ALTER COLUMN MaNV NVARCHAR(50) NULL;
                    ALTER TABLE TaiKhoan ADD CONSTRAINT CK_TaiKhoan_LoaiTK CHECK(LoaiTK IN ('Admin', 'QuanLy', 'NhanVien'));
                """)
                db.commit()
            except Exception:
                pass

            # Seed or sync admin in TaiKhoan
            try:
                admin_tk = db.execute("SELECT 1 FROM TaiKhoan WHERE TenDN='admin'").fetchone()
                if not admin_tk:
                    db.execute("INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES('admin', 'admin123', NULL, 'Admin')")
                    db.commit()
            except Exception:
                pass
        except Exception as e:
            _mssql_failed = True
            print(f"[THÔNG BÁO] Không thể kết nối SQL Server khi khởi tạo ({e}).\n-> Tự động chuyển sang sử dụng SQLite ({DB_PATH}).")
            db = None

    if db is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        setup_sqlite_conn(conn)
        init_sqlite_schema(conn)
        db = ConnectionWrapper(conn, is_mssql=False)
        try:
            admin_tk = db.execute("SELECT 1 FROM TaiKhoan WHERE TenDN='admin'").fetchone()
            if not admin_tk:
                db.execute("INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES('admin', 'admin123', NULL, 'Admin')")
                db.commit()
        except Exception:
            pass

    # Clean duplicate records across all core & transaction tables
    clean_all_duplicates(db)

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

        db.execute("INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, TrangThai, LyDo) VALUES(?, ?, ?, 'Đã duyệt', 'Việc gia đình')", ('NV003', day_prefix + '03', day_prefix + '04'))
        db.execute("INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai, TrangThai, LyDo, NguoiDuyet) VALUES(?, ?, ?, ?, 'Đã duyệt', 'Fix lỗi hệ thống', 'Nguyễn Văn An')", ('NV005', 3, day_prefix + '05', 'Ngày thường'))

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

    # Ensure deprecated tables (KhoaDaoTao, PhanCa) are completely cleared
    try:
        db.execute("DELETE FROM DangKyDaoTao")
        db.execute("DELETE FROM KhoaDaoTao")
        db.execute("DELETE FROM PhanCa")
        db.commit()
    except Exception:
        pass

    # Ensure all department heads (Trưởng phòng) and departmental staff accounts
    ensure_department_heads_and_staff(db)

    db.commit()
    db.close()
