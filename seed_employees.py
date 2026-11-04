# -*- coding: utf-8 -*-
"""Kịch bản khởi tạo dữ liệu chuẩn cho hệ thống Quản lý nhân sự (HRM):
- 4 Phòng ban: Nhân sự (PB01), Kế toán (PB02), Kinh doanh (PB03), Kỹ thuật (PB04)
- 13 Chức vụ (CV01 - CV13)
- 13 Nhân viên chuẩn (NV001 - NV013) gồm 4 Trưởng phòng và các chuyên viên phòng ban
- 15 Tài khoản đăng nhập: tên đăng nhập là mã nhân viên (nv001, nv006, nv007, nv008,...) mật khẩu 123456
- Đã loại bỏ hoàn toàn tính năng Khóa đào tạo và Phân ca làm việc.
- Tương thích 100% với cả SQLite và Microsoft SQL Server.
"""
import os
import sys
from datetime import date, timedelta

# Add ss to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ss'))
from app import create_app
from database import get_db, clean_all_duplicates
from config import NV, QL, AD

# 4 Departments chuẩn của hệ thống
DEPARTMENTS = [
    ('PB01', 'Nhân sự'),
    ('PB02', 'Kế toán'),
    ('PB03', 'Kinh doanh'),
    ('PB04', 'Kỹ thuật')
]

# 13 Positions across 4 departments
POSITIONS = [
    ('CV01', 'Trưởng phòng Nhân sự', 'PB01'),
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

# 13 Employee Profiles chuẩn
EMPLOYEES = [
    # PB01 - Nhân sự
    ('NV001', 'Nguyễn Văn An', 'Nam', '1985-03-12', '0901000001', '001090000001', 'an@vnm.vn', 'Hà Nội', '2015-06-01', 'Thạc sĩ', 'Quản trị nhân sự', 'Chính thức', 'BH001859', 'MST001859', 'CV01', 14000000),
    ('NV002', 'Trần Thị Bình', 'Nữ', '1992-07-21', '0901000002', '001090000002', 'binh@vnm.vn', 'Hà Nội', '2019-02-15', 'Đại học', 'Quản lý lao động', 'Chính thức', 'BH002927', 'MST002927', 'CV02', 16000000),
    ('NV013', 'Phan Mỹ Linh', 'Nữ', '1999-03-30', '0901000013', '001090000013', 'linh.phan@vnm.vn', 'Hà Nội', '2023-07-15', 'Đại học', 'Quản trị nhân sự', 'Chính thức', 'BH013890', 'MST013890', 'CV13', 15000000),

    # PB02 - Kế toán
    ('NV006', 'Vũ Thị Hoa', 'Nữ', '1988-04-15', '0901000006', '001090000006', 'hoa.vu@vnm.vn', 'Hà Nội', '2017-03-01', 'Thạc sĩ', 'Tài chính kế toán', 'Chính thức', 'BH006123', 'MST006123', 'CV06', 22000000),
    ('NV003', 'Lê Minh Cường', 'Nam', '1994-11-02', '0901000003', '001090000003', 'cuong@vnm.vn', 'Hải Phòng', '2020-09-01', 'Đại học', 'Kế toán doanh nghiệp', 'Chính thức', 'BH003941', 'MST003941', 'CV03', 18000000),
    ('NV009', 'Trương Mai Phương', 'Nữ', '1995-02-18', '0901000009', '001090000009', 'phuong.truong@vnm.vn', 'Nam Định', '2021-06-15', 'Đại học', 'Kiểm toán', 'Chính thức', 'BH009456', 'MST009456', 'CV09', 17000000),

    # PB03 - Kinh doanh
    ('NV007', 'Bùi Quang Huy', 'Nam', '1989-08-20', '0901000007', '001090000007', 'huy.bui@vnm.vn', 'Hải Phòng', '2018-05-10', 'Thạc sĩ', 'Quản trị kinh doanh', 'Chính thức', 'BH007234', 'MST007234', 'CV07', 24000000),
    ('NV004', 'Phạm Thu Dung', 'Nữ', '1996-01-30', '0901000004', '001090000004', 'dung@vnm.vn', 'Bắc Ninh', '2021-04-12', 'Đại học', 'Quản trị kinh doanh', 'Chính thức', 'BH004961', 'MST004961', 'CV04', 20000000),
    ('NV010', 'Nguyễn Đức Thắng', 'Nam', '1997-09-05', '0901000010', '001090000010', 'thang.nguyen@vnm.vn', 'Bắc Ninh', '2022-01-10', 'Đại học', 'Marketing số', 'Chính thức', 'BH010567', 'MST010567', 'CV10', 16000000),

    # PB04 - Kỹ thuật
    ('NV008', 'Đỗ Hoàng Long', 'Nam', '1987-11-12', '0901000008', '001090000008', 'long.do@vnm.vn', 'Hà Nội', '2016-10-01', 'Thạc sĩ', 'Công nghệ thông tin', 'Chính thức', 'BH008345', 'MST008345', 'CV08', 26000000),
    ('NV005', 'Hoàng Quốc Em', 'Nam', '1998-05-18', '0901000005', '001090000005', 'em@vnm.vn', 'Nam Định', '2022-08-08', 'Đại học', 'Kỹ thuật phần mềm', 'Chính thức', 'BH005985', 'MST005985', 'CV05', 22000000),
    ('NV011', 'Lý Thu Trang', 'Nữ', '1996-12-25', '0901000011', '001090000011', 'trang.ly@vnm.vn', 'Hà Nội', '2021-09-01', 'Đại học', 'Đảm bảo chất lượng phần mềm', 'Chính thức', 'BH011678', 'MST011678', 'CV11', 18000000),
    ('NV012', 'Vũ Tuấn Kiệt', 'Nam', '1998-07-14', '0901000012', '001090000012', 'kiet.vu@vnm.vn', 'Hải Dương', '2023-03-01', 'Đại học', 'Điện toán đám mây & DevOps', 'Chính thức', 'BH012789', 'MST012789', 'CV12', 19000000),
]

def seed_database():
    app = create_app()
    with app.app_context():
        db = get_db()
        print("=== BẮT ĐẦU KHỞI TẠO DỮ LIỆU NHÂN SỰ & 4 PHÒNG BAN ===")

        # 1. Seed 4 PhongBan
        for mpb, tpb in DEPARTMENTS:
            row = db.execute("SELECT 1 FROM PhongBan WHERE MaPB = ?", (mpb,)).fetchone()
            if not row:
                db.execute("INSERT INTO PhongBan(MaPB, TenPB) VALUES(?, ?)", (mpb, tpb))
            else:
                db.execute("UPDATE PhongBan SET TenPB = ? WHERE MaPB = ?", (tpb, mpb))
        print(f"-> Đã đảm bảo 4 phòng ban ({len(DEPARTMENTS)})")

        # 2. Seed 13 ChucVu
        for mcv, tcv, mpb in POSITIONS:
            row = db.execute("SELECT 1 FROM ChucVu WHERE MaCV = ?", (mcv,)).fetchone()
            if not row:
                db.execute("INSERT INTO ChucVu(MaCV, TenCV, MaPB) VALUES(?, ?, ?)", (mcv, tcv, mpb))
            else:
                db.execute("UPDATE ChucVu SET TenCV = ?, MaPB = ? WHERE MaCV = ?", (tcv, mpb, mcv))
        print(f"-> Đã đảm bảo 13 chức vụ ({len(POSITIONS)})")

        avatar_dir = os.path.join(os.path.dirname(__file__), 'ss', 'static', 'uploads', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)

        current_month = date.today().strftime('%Y-%m')
        prev_month = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        today_str = date.today().strftime('%Y-%m-%d')

        # 3. Seed Nhân viên, Hợp đồng, Lương, Chấm công
        for emp in EMPLOYEES:
            (mnv, hoten, gt, ns, sdt, cccd, email, dc, nvct, td, cm, lnv, bhxh, mst, mcv, sal) = emp
            avatar_path = f"/static/uploads/avatars/avatar_{mnv}.svg"

            # Insert or update NhanVien
            row = db.execute("SELECT 1 FROM NhanVien WHERE MaNV = ?", (mnv,)).fetchone()
            if not row:
                db.execute("""
                    INSERT INTO NhanVien(MaNV, HoTen, GioiTinh, NgaySinh, SDT, CCCD, Email, DiaChi, NgayVaoCT, TrinhDo, ChuyenMon, LoaiNhanVien, SoBHXH, MaSoThue, MaCV, HinhAnh)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (mnv, hoten, gt, ns, sdt, cccd, email, dc, nvct, td, cm, lnv, bhxh, mst, mcv, avatar_path))
            else:
                db.execute("""
                    UPDATE NhanVien
                    SET HoTen=?, GioiTinh=?, NgaySinh=?, SDT=?, CCCD=?, Email=?, DiaChi=?, NgayVaoCT=?, TrinhDo=?, ChuyenMon=?, LoaiNhanVien=?, SoBHXH=?, MaSoThue=?, MaCV=?, HinhAnh=?
                    WHERE MaNV=?
                """, (hoten, gt, ns, sdt, cccd, email, dc, nvct, td, cm, lnv, bhxh, mst, mcv, avatar_path, mnv))

            # 4. Hợp đồng lao động
            hd_code = f"HD{mnv[2:]}"
            start_date = '2026-10-01' if mnv in ('NV001', 'NV002', 'NV003', 'NV004', 'NV005') else nvct
            hd_row = db.execute("SELECT 1 FROM HopDong WHERE MaHD = ?", (hd_code,)).fetchone()
            if not hd_row:
                db.execute("""
                    INSERT INTO HopDong(MaHD, MaNV, LoaiHD, NgayBD, NgayKT, LuongCoBan, TrangThai, GhiChu, HinhAnh)
                    VALUES(?, ?, ?, ?, ?, ?, N'Hiệu lực', N'Hợp đồng lao động tiêu chuẩn', ?)
                """, (
                    hd_code, mnv, 'Không xác định thời hạn' if mcv in ('CV01', 'CV06', 'CV07', 'CV08') else 'Xác định thời hạn (3 năm)',
                    start_date, '2028-12-31' if mcv not in ('CV01', 'CV06', 'CV07', 'CV08') else None,
                    sal, avatar_path
                ))
            else:
                db.execute("UPDATE HopDong SET LuongCoBan = ?, TrangThai = N'Hiệu lực' WHERE MaHD = ?", (sal, hd_code))

            # 5. Bảng lương
            bh = round(sal * 0.105, 0)
            thuong = 2000000 if lnv == 'Chính thức' else 1000000
            phucap = 1500000 if lnv == 'Chính thức' else 1000000
            thue = round((sal - 11000000) * 0.05, 0) if sal > 11000000 else 0

            # Tháng hiện tại
            l_row = db.execute("SELECT 1 FROM Luong WHERE MaNV = ? AND ThangNam = ?", (mnv, current_month)).fetchone()
            if not l_row:
                db.execute("""
                    INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap, BaoHiem, ThueTNCN, KhauTruKhac)
                    VALUES(?, ?, ?, ?, 0, ?, ?, ?, 0)
                """, (mnv, current_month, sal, thuong, phucap, bh, thue))
            else:
                db.execute("""
                    UPDATE Luong SET LuongCung = ?, LuongThuong = ?, PhuCap = ?, BaoHiem = ?, ThueTNCN = ? WHERE MaNV = ? AND ThangNam = ?
                """, (sal, thuong, phucap, bh, thue, mnv, current_month))

            # Tháng trước
            prev_l_row = db.execute("SELECT 1 FROM Luong WHERE MaNV = ? AND ThangNam = ?", (mnv, prev_month)).fetchone()
            if not prev_l_row:
                db.execute("""
                    INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap, BaoHiem, ThueTNCN, KhauTruKhac)
                    VALUES(?, ?, ?, ?, 0, ?, ?, ?, 0)
                """, (mnv, prev_month, sal, thuong, phucap, bh, thue))

            # 6. Chấm công hôm nay
            cc_row = db.execute("SELECT 1 FROM ChamCong WHERE MaNV = ? AND Ngay = ?", (mnv, today_str)).fetchone()
            if not cc_row:
                db.execute("""
                    INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu)
                    VALUES(?, ?, '08:00', '17:30', 'Đúng giờ', 'Chấm công máy vân tay')
                """, (mnv, today_str))

        # 7. Tài khoản đăng nhập (TaiKhoan)
        # Trưởng phòng: LoaiTK = 'QuanLy', Username = mã nhân viên (nv001, nv006, nv007, nv008)
        # Nhân viên: LoaiTK = 'NhanVien', Username = mã nhân viên (nv002, nv003, nv004, nv005, nv009, nv010, nv011, nv012, nv013)
        # Admin: LoaiTK = 'Admin', admin / admin123
        accounts = [
            ('admin', 'admin123', None, AD),
            ('nv001', '123456', 'NV001', QL),
            ('ql001', '123456', 'NV001', QL), # Giữ bí danh tương thích
            ('nv006', '123456', 'NV006', QL),
            ('nv007', '123456', 'NV007', QL),
            ('nv008', '123456', 'NV008', QL),
            ('nv002', '123456', 'NV002', NV),
            ('nv003', '123456', 'NV003', NV),
            ('nv004', '123456', 'NV004', NV),
            ('nv005', '123456', 'NV005', NV),
            ('nv009', '123456', 'NV009', NV),
            ('nv010', '123456', 'NV010', NV),
            ('nv011', '123456', 'NV011', NV),
            ('nv012', '123456', 'NV012', NV),
            ('nv013', '123456', 'NV013', NV),
        ]
        for tdn, mk, mnv_acc, loai in accounts:
            acc_row = db.execute("SELECT MaTK FROM TaiKhoan WHERE TenDN = ?", (tdn,)).fetchone()
            if not acc_row:
                db.execute("INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES(?, ?, ?, ?)", (tdn, mk, mnv_acc, loai))
            else:
                db.execute("UPDATE TaiKhoan SET MatKhau = ?, MaNV = ?, LoaiTK = ? WHERE TenDN = ?", (mk, mnv_acc, loai, tdn))

        print(f"-> Đã khởi tạo đầy đủ 13 hồ sơ nhân viên, 13 hợp đồng, bảng lương, chấm công và 15 tài khoản truy cập!")

        # 8. Khen thưởng & Kỷ luật (KhenThuongKyLuat)
        rewards = [
            ('NV001', 'Khen thưởng', 'QĐ-KT/2026-01', '2026-01-15', 'Bằng khen & Tiền thưởng', 5000000, 'Lãnh đạo xuất sắc hoàn thành kế hoạch nhân sự năm 2025', 'Ban Giám Đốc'),
            ('NV002', 'Khen thưởng', 'QĐ-KT/2026-03', '2026-03-20', 'Tiền thưởng nóng', 2000000, 'Đạt chỉ tiêu tuyển dụng 15 chuyên viên chất lượng cao trong quý 1', 'Ban Giám Đốc'),
            ('NV005', 'Khen thưởng', 'QĐ-KT/2026-04', '2026-04-10', 'Bằng khen & Cúp vinh danh', 3000000, 'Sáng kiến tối ưu hóa hệ thống ERP giúp giảm 40% thời gian xử lý', 'Ban Giám Đốc'),
            ('NV006', 'Khen thưởng', 'QĐ-KT/2026-05', '2026-05-18', 'Bằng khen Ban Giám Đốc', 4000000, 'Quyết toán và hoàn thành báo cáo kiểm toán tài chính trước hạn', 'Ban Giám Đốc'),
            ('NV007', 'Khen thưởng', 'QĐ-KT/2026-06', '2026-06-30', 'Tiền thưởng doanh số', 10000000, 'Đột phá doanh thu quý 2 vượt 140% chỉ tiêu kế hoạch', 'Tổng Giám Đốc'),
            ('NV008', 'Khen thưởng', 'QĐ-KT/2026-07', '2026-07-15', 'Khen thưởng chuyên môn', 5000000, 'Triển khai thành công hạ tầng kỹ thuật bảo mật an toàn thông tin', 'Ban Giám Đốc'),
            ('NV011', 'Khen thưởng', 'QĐ-KT/2026-08', '2026-08-20', 'Tiền thưởng dự án', 2500000, 'Phát hiện sớm các lỗi trọng yếu đảm bảo chất lượng phát hành ứng dụng', 'Trưởng phòng Kỹ thuật'),
            ('NV010', 'Khen thưởng', 'QĐ-KT/2026-09', '2026-09-15', 'Tiền thưởng chiến dịch', 3000000, 'Dẫn đầu chiến dịch quảng bá thu hút 1.000 khách hàng tiềm năng', 'Trưởng phòng Kinh doanh'),
            ('NV003', 'Kỷ luật', 'QĐ-KL/2026-05', '2026-05-12', 'Khiển trách bằng văn bản', 0, 'Vi phạm quy định giờ giấc đi muộn quá 4 lần trong tháng', 'Trưởng phòng Kế toán')
        ]
        for mnv, loai, sqd, nqd, ht, tien, ld, nk in rewards:
            r_row = db.execute("SELECT 1 FROM KhenThuongKyLuat WHERE SoQuyetDinh = ?", (sqd,)).fetchone()
            if not r_row:
                db.execute("""
                    INSERT INTO KhenThuongKyLuat(MaNV, Loai, SoQuyetDinh, NgayQuyetDinh, HinhThuc, SoTien, LyDo, NguoiKy)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """, (mnv, loai, sqd, nqd, ht, tien, ld, nk))

        # 9. Clean any duplicates and clear deprecated tables
        clean_all_duplicates(db)
        db.commit()

        # 10. Automatically run comprehensive functional record seeding if available
        try:
            from seed_all_employee_records import run_seed as seed_all_functions
            seed_all_functions()
        except Exception as e:
            print(f"Lưu ý: Không thể chạy seed_all_employee_records: {e}")

        # Stats summary
        nv_cnt = db.execute("SELECT COUNT(*) FROM NhanVien").fetchone()[0]
        pb_cnt = db.execute("SELECT COUNT(*) FROM PhongBan").fetchone()[0]
        cv_cnt = db.execute("SELECT COUNT(*) FROM ChucVu").fetchone()[0]
        hd_cnt = db.execute("SELECT COUNT(*) FROM HopDong").fetchone()[0]
        l_cnt = db.execute("SELECT COUNT(*) FROM Luong").fetchone()[0]
        cc_cnt = db.execute("SELECT COUNT(*) FROM ChamCong").fetchone()[0]
        kt_cnt = db.execute("SELECT COUNT(*) FROM KhenThuongKyLuat").fetchone()[0]
        tk_cnt = db.execute("SELECT COUNT(*) FROM TaiKhoan").fetchone()[0]

        print("=== HOÀN TẤT KHỞI TẠO DỮ LIỆU CSDL THÀNH CÔNG ===")
        print(f"• Tổng số Nhân viên: {nv_cnt}")
        print(f"• Tổng số Phòng ban: {pb_cnt}")
        print(f"• Tổng số Chức vụ: {cv_cnt}")
        print(f"• Tổng số Hợp đồng: {hd_cnt}")
        print(f"• Tổng số Bảng lương: {l_cnt}")
        print(f"• Tổng số Bản ghi chấm công: {cc_cnt}")
        print(f"• Tổng số Khen thưởng/Kỷ luật: {kt_cnt}")
        print(f"• Tổng số Tài khoản truy cập: {tk_cnt}")

if __name__ == '__main__':
    seed_database()

