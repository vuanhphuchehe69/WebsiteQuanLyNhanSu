# -*- coding: utf-8 -*-
"""Script to seed 50 employees, 8 departments, 16 positions, attendance, payroll, rewards & discipline."""
import os
import sys
import random
from datetime import date, datetime, timedelta

# Add ss to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ss'))
from app import create_app
from database import get_db, clean_all_duplicates
from config import NV, QL, AD

# 8 Departments
DEPARTMENTS = [
    ('PB01', 'Phòng Nhân sự'),
    ('PB02', 'Phòng Tài chính - Kế toán'),
    ('PB03', 'Phòng Kinh doanh & Tiếp thị'),
    ('PB04', 'Phòng Công nghệ Thông tin'),
    ('PB05', 'Phòng Kỹ thuật & Vận hành'),
    ('PB06', 'Phòng Chăm sóc Khách hàng'),
    ('PB07', 'Phòng Hành chính - Tổng hợp'),
    ('PB08', 'Ban Quản trị & Chiến lược')
]

# 16 Positions across 8 departments
POSITIONS = [
    ('CV01', 'Trưởng phòng Nhân sự', 'PB01'),
    ('CV02', 'Chuyên viên Tuyển dụng & Đào tạo', 'PB01'),
    ('CV03', 'Kế toán trưởng', 'PB02'),
    ('CV04', 'Kế toán viên Tổng hợp', 'PB02'),
    ('CV05', 'Trưởng phòng Kinh doanh', 'PB03'),
    ('CV06', 'Chuyên viên Kinh doanh B2B', 'PB03'),
    ('CV07', 'Trưởng phòng Công nghệ', 'PB04'),
    ('CV08', 'Kỹ sư Phần mềm Fullstack', 'PB04'),
    ('CV09', 'Trưởng phòng Kỹ thuật', 'PB05'),
    ('CV10', 'Chuyên viên Vận hành Hệ thống', 'PB05'),
    ('CV11', 'Trưởng nhóm CSKH', 'PB06'),
    ('CV12', 'Chuyên viên Hỗ trợ Khách hàng', 'PB06'),
    ('CV13', 'Trưởng phòng Hành chính', 'PB07'),
    ('CV14', 'Chuyên viên Hành chính Quản trị', 'PB07'),
    ('CV15', 'Giám đốc Điều hành (CEO)', 'PB08'),
    ('CV16', 'Phó Giám đốc Chiến lược', 'PB08')
]

# 50 Vietnamese Employee Profiles
EMPLOYEES_RAW = [
    # Top 5 core employees (guaranteeing backward compatibility with tests)
    ('NV001', 'Nguyễn Văn An', 'Nam', '1985-03-12', '0901000001', '001090000001', 'an@vnm.vn', 'Hà Nội', '2015-06-01', 'Thạc sĩ', 'Quản trị nhân sự', 'Chính thức', 'BH001859', 'MST001859', 'CV01', 14000000),
    ('NV002', 'Trần Thị Bình', 'Nữ', '1992-07-21', '0901000002', '001090000002', 'binh@vnm.vn', 'Hà Nội', '2019-02-15', 'Đại học', 'Quản trị nhân lực', 'Chính thức', 'BH002927', 'MST002927', 'CV02', 16000000),
    ('NV003', 'Lê Minh Cường', 'Nam', '1994-11-02', '0901000003', '001090000003', 'cuong@vnm.vn', 'Hải Phòng', '2020-09-01', 'Đại học', 'Tài chính doanh nghiệp', 'Chính thức', 'BH003941', 'MST003941', 'CV04', 18000000),
    ('NV004', 'Phạm Thu Dung', 'Nữ', '1996-01-30', '0901000004', '001090000004', 'dung@vnm.vn', 'Bắc Ninh', '2021-04-12', 'Đại học', 'Quản trị kinh doanh', 'Chính thức', 'BH004961', 'MST004961', 'CV06', 20000000),
    ('NV005', 'Hoàng Quốc Em', 'Nam', '1998-05-18', '0901000005', '001090000005', 'em@vnm.vn', 'Nam Định', '2022-08-08', 'Đại học', 'Kỹ thuật phần mềm', 'Chính thức', 'BH005985', 'MST005985', 'CV08', 22000000),

    # 45 Additional Employees across departments
    ('NV006', 'Vũ Thị Phương Thảo', 'Nữ', '1990-09-15', '0901000006', '001090000006', 'thao.vu@vnm.vn', 'Hà Nội', '2018-03-01', 'Thạc sĩ', 'Kế toán kiểm toán', 'Chính thức', 'BH006901', 'MST006901', 'CV03', 28000000),
    ('NV007', 'Đặng Tuấn Anh', 'Nam', '1988-12-04', '0901000007', '001090000007', 'anh.dang@vnm.vn', 'Hưng Yên', '2017-05-10', 'Thạc sĩ', 'Thương mại quốc tế', 'Chính thức', 'BH007882', 'MST007882', 'CV05', 30000000),
    ('NV008', 'Bùi Đức Trọng', 'Nam', '1987-04-25', '0901000008', '001090000008', 'trong.bui@vnm.vn', 'Hà Nội', '2016-10-01', 'Thạc sĩ', 'Khoa học máy tính', 'Chính thức', 'BH008873', 'MST008873', 'CV07', 35000000),
    ('NV009', 'Ngô Quang Huy', 'Nam', '1989-08-14', '0901000009', '001090000009', 'huy.ngo@vnm.vn', 'Thái Bình', '2018-11-15', 'Đại học', 'Cơ điện tử & Tự động hóa', 'Chính thức', 'BH009894', 'MST009894', 'CV09', 26000000),
    ('NV010', 'Dương Thúy Hằng', 'Nữ', '1993-02-28', '0901000010', '001090000010', 'hang.duong@vnm.vn', 'Hà Nội', '2019-07-01', 'Đại học', 'Truyền thông & Quan hệ công chúng', 'Chính thức', 'BH010935', 'MST010935', 'CV11', 22000000),
    ('NV011', 'Lý Gia Bảo', 'Nam', '1991-06-20', '0901000011', '001090000011', 'bao.ly@vnm.vn', 'Vĩnh Phúc', '2018-09-01', 'Đại học', 'Quản lý hành chính', 'Chính thức', 'BH011916', 'MST011916', 'CV13', 24000000),
    ('NV012', 'Phan Văn Hùng', 'Nam', '1980-01-10', '0901000012', '001090000012', 'hung.phan@vnm.vn', 'Hà Nội', '2014-01-01', 'Tiến sĩ', 'Quản trị kinh doanh cấp cao', 'Chính thức', 'BH012807', 'MST012807', 'CV15', 50000000),
    ('NV013', 'Mai Hoàng Yến', 'Nữ', '1983-10-18', '0901000013', '001090000013', 'yen.mai@vnm.vn', 'Hải Dương', '2015-04-15', 'Thạc sĩ', 'Kinh tế đối ngoại', 'Chính thức', 'BH013838', 'MST013838', 'CV16', 42000000),
    ('NV014', 'Đỗ Thành Long', 'Nam', '1995-05-22', '0901000014', '001090000014', 'long.do@vnm.vn', 'Hà Nội', '2021-06-01', 'Đại học', 'Khoa học dữ liệu & AI', 'Chính thức', 'BH014959', 'MST014959', 'CV08', 24000000),
    ('NV015', 'Tạ Minh Khang', 'Nam', '1997-03-11', '0901000015', '001090000015', 'khang.ta@vnm.vn', 'Quảng Ninh', '2022-03-15', 'Đại học', 'Kỹ thuật mạng & An ninh thông tin', 'Chính thức', 'BH015970', 'MST015970', 'CV10', 18000000),
    ('NV016', 'Lương Diệu Linh', 'Nữ', '1996-12-08', '0901000016', '001090000016', 'linh.luong@vnm.vn', 'Hà Nội', '2021-08-01', 'Đại học', 'Ngôn ngữ Anh & CSKH', 'Chính thức', 'BH016961', 'MST016961', 'CV12', 15000000),
    ('NV017', 'Hà Ngọc Mai', 'Nữ', '1998-07-19', '0901000017', '001090000017', 'mai.ha@vnm.vn', 'Phú Thọ', '2022-10-01', 'Đại học', 'Quản trị văn phòng', 'Chính thức', 'BH017982', 'MST017982', 'CV14', 14000000),
    ('NV018', 'Chu Đình Trọng', 'Nam', '1994-09-05', '0901000018', '001090000018', 'trong.chu@vnm.vn', 'Bắc Giang', '2020-11-12', 'Đại học', 'Quản trị nhân sự', 'Chính thức', 'BH018943', 'MST018943', 'CV02', 16000000),
    ('NV019', 'Võ Hoàng Nam', 'Nam', '1995-11-30', '0901000019', '001090000019', 'nam.vo@vnm.vn', 'Nghệ An', '2021-02-20', 'Đại học', 'Kế toán thuế', 'Chính thức', 'BH019954', 'MST019954', 'CV04', 16500000),
    ('NV020', 'Trịnh Thanh Tùng', 'Nam', '1996-08-16', '0901000020', '001090000020', 'tung.trinh@vnm.vn', 'Thanh Hóa', '2021-09-15', 'Đại học', 'Marketing số & Tiếp thị nội dung', 'Chính thức', 'BH020965', 'MST020965', 'CV06', 15500000),
    ('NV021', 'Khổng Thị Kim Oanh', 'Nữ', '1997-04-03', '0901000021', '001090000021', 'oanh.khong@vnm.vn', 'Hà Nam', '2022-04-01', 'Đại học', 'Lập trình viên Frontend (React/Vue)', 'Chính thức', 'BH021976', 'MST021976', 'CV08', 21000000),
    ('NV022', 'Đoàn Viết Hưng', 'Nam', '1998-01-25', '0901000022', '001090000022', 'hung.doan@vnm.vn', 'Hà Nội', '2022-07-15', 'Đại học', 'Bảo trì hạ tầng thiết bị', 'Chính thức', 'BH022987', 'MST022987', 'CV10', 16000000),
    ('NV023', 'Thái Hà Phương', 'Nữ', '1999-06-14', '0901000023', '001090000023', 'phuong.thai@vnm.vn', 'Thái Nguyên', '2023-02-01', 'Đại học', 'Quan hệ khách hàng VIP', 'Chính thức', 'BH023998', 'MST023998', 'CV12', 14500000),
    ('NV024', 'Lâm Tuấn Kiệt', 'Nam', '1993-10-09', '0901000024', '001090000024', 'kiet.lam@vnm.vn', 'Hà Nội', '2019-12-01', 'Đại học', 'Luật kinh tế & Pháp chế', 'Chính thức', 'BH024939', 'MST024939', 'CV14', 19000000),
    ('NV025', 'Quách Ánh Tuyết', 'Nữ', '1995-02-17', '0901000025', '001090000025', 'tuyet.quach@vnm.vn', 'Yên Bái', '2021-05-10', 'Đại học', 'Chế độ & Chính sách tiền lương (C&B)', 'Chính thức', 'BH025950', 'MST025950', 'CV02', 17000000),
    ('NV026', 'Nghiêm Xuân Bách', 'Nam', '1994-06-28', '0901000026', '001090000026', 'bach.nghiem@vnm.vn', 'Hà Nội', '2020-04-01', 'Thạc sĩ', 'Kiểm toán tài chính', 'Chính thức', 'BH026941', 'MST026941', 'CV04', 18500000),
    ('NV027', 'Bạch Hồng Đăng', 'Nam', '1996-03-08', '0901000027', '001090000027', 'dang.bach@vnm.vn', 'Hải Phòng', '2021-10-15', 'Đại học', 'Phát triển thị trường miền Bắc', 'Chính thức', 'BH027962', 'MST027962', 'CV06', 16000000),
    ('NV028', 'Tôn Thất Dũng', 'Nam', '1997-12-12', '0901000028', '001090000028', 'dung.ton@vnm.vn', 'Huế', '2022-09-01', 'Đại học', 'Kỹ sư Backend (Python/NodeJS)', 'Chính thức', 'BH028973', 'MST028973', 'CV08', 23000000),
    ('NV029', 'Âu Dương Quân', 'Nam', '1998-09-29', '0901000029', '001090000029', 'quan.au@vnm.vn', 'Hà Nội', '2023-01-15', 'Cao đẳng', 'Kỹ thuật điện lạnh & Hệ thống', 'Chính thức', 'BH029984', 'MST029984', 'CV10', 14000000),
    ('NV030', 'Hồ Ngọc Hà My', 'Nữ', '1999-11-05', '0901000030', '001090000030', 'my.ho@vnm.vn', 'Đà Nẵng', '2023-03-01', 'Đại học', 'Chăm sóc khách hàng đa kênh', 'Chính thức', 'BH030995', 'MST030995', 'CV12', 13500000),
    ('NV031', 'Trần Đình Trọng', 'Nam', '1995-07-24', '0901000031', '001090000031', 'trong.tran@vnm.vn', 'Hà Nội', '2021-03-01', 'Đại học', 'Quản trị lễ tân & Hậu cần', 'Chính thức', 'BH031956', 'MST031956', 'CV14', 15000000),
    ('NV032', 'Lê Thị Thu Cúc', 'Nữ', '1996-05-19', '0901000032', '001090000032', 'cuc.le@vnm.vn', 'Hưng Yên', '2021-11-01', 'Đại học', 'Tuyển dụng tài năng công nghệ', 'Chính thức', 'BH032967', 'MST032967', 'CV02', 16500000),
    ('NV033', 'Nguyễn Tiến Minh', 'Nam', '1997-08-30', '0901000033', '001090000033', 'minh.nguyen@vnm.vn', 'Hà Nội', '2022-05-15', 'Đại học', 'Kế toán công nợ & Thanh toán', 'Chính thức', 'BH033978', 'MST033978', 'CV04', 15500000),
    ('NV034', 'Phạm Quỳnh Anh', 'Nữ', '1998-04-12', '0901000034', '001090000034', 'anh.pham@vnm.vn', 'Quảng Ninh', '2022-11-20', 'Đại học', 'Kinh doanh sản phẩm phần mềm', 'Chính thức', 'BH034989', 'MST034989', 'CV06', 15000000),
    ('NV035', 'Hoàng Gia Huy', 'Nam', '1999-02-18', '0901000035', '001090000035', 'huy.hoang@vnm.vn', 'Bắc Ninh', '2023-04-10', 'Đại học', 'Kiểm thử phần mềm (QA/QC)', 'Chính thức', 'BH035990', 'MST035990', 'CV08', 18000000),
    ('NV036', 'Đinh Khắc Tiệp', 'Nam', '1997-10-27', '0901000036', '001090000036', 'tiep.dinh@vnm.vn', 'Hà Nội', '2022-08-01', 'Cao đẳng', 'Kỹ thuật viên phòng máy chủ', 'Chính thức', 'BH036971', 'MST036971', 'CV10', 14500000),
    ('NV037', 'Vũ Khánh Linh', 'Nữ', '2000-01-15', '0901000037', '001090000037', 'linh.vk@vnm.vn', 'Hải Phòng', '2023-06-01', 'Đại học', 'Tư vấn viên giải pháp khách hàng', 'Thử việc', 'BH037002', 'MST037002', 'CV12', 12000000),
    ('NV038', 'Nguyễn Đức Phúc', 'Nam', '1996-11-09', '0901000038', '001090000038', 'phuc.nd@vnm.vn', 'Ninh Bình', '2021-12-15', 'Đại học', 'Quản trị trang thiết bị văn phòng', 'Chính thức', 'BH038963', 'MST038963', 'CV14', 14000000),
    ('NV039', 'Trần Bảo Ngọc', 'Nữ', '1998-03-22', '0901000039', '001090000039', 'ngoc.tb@vnm.vn', 'Hà Nội', '2022-10-10', 'Đại học', 'Văn hóa doanh nghiệp & Sự kiện', 'Chính thức', 'BH039984', 'MST039984', 'CV02', 15000000),
    ('NV040', 'Lê Tuấn Dũng', 'Nam', '1995-09-14', '0901000040', '001090000040', 'dung.lt@vnm.vn', 'Nam Định', '2021-04-25', 'Đại học', 'Kế toán quản trị & Báo cáo', 'Chính thức', 'BH040955', 'MST040955', 'CV04', 17000000),
    ('NV041', 'Phan Thanh Thảo', 'Nữ', '1999-07-07', '0901000041', '001090000041', 'thao.pt@vnm.vn', 'Hà Tĩnh', '2023-05-01', 'Đại học', 'Telesales & CSKH dự án', 'Chính thức', 'BH041996', 'MST041996', 'CV06', 14000000),
    ('NV042', 'Nguyễn Hoàng Sơn', 'Nam', '2000-08-20', '0901000042', '001090000042', 'son.nh@vnm.vn', 'Hà Nội', '2023-09-01', 'Đại học', 'Lập trình ứng dụng Di động (Flutter)', 'Thử việc', 'BH042007', 'MST042007', 'CV08', 15000000),
    ('NV043', 'Bùi Văn Hậu', 'Nam', '1996-06-11', '0901000043', '001090000043', 'hau.bv@vnm.vn', 'Thái Bình', '2022-01-10', 'Cao đẳng', 'Kỹ thuật giám sát camera an ninh', 'Chính thức', 'BH043968', 'MST043968', 'CV10', 13500000),
    ('NV044', 'Đặng Thùy Trang', 'Nữ', '2001-02-14', '0901000044', '001090000044', 'trang.dt@vnm.vn', 'Bắc Ninh', '2023-11-01', 'Đại học', 'Hỗ trợ khách hàng trực tuyến', 'Thực tập sinh', 'BH044019', 'MST044019', 'CV12', 8000000),
    ('NV045', 'Vũ Đức Thịnh', 'Nam', '1997-05-05', '0901000045', '001090000045', 'thinh.vd@vnm.vn', 'Hải Dương', '2022-06-20', 'Đại học', 'Quản lý kho tài sản & Lưu trữ', 'Chính thức', 'BH045970', 'MST045970', 'CV14', 13500000),
    ('NV046', 'Trịnh Cẩm Ly', 'Nữ', '2001-09-18', '0901000046', '001090000046', 'ly.tc@vnm.vn', 'Hà Nội', '2024-01-05', 'Đại học', 'Thực tập sinh Nhân sự & Tuyển dụng', 'Thực tập sinh', 'BH046011', 'MST046011', 'CV02', 8000000),
    ('NV047', 'Lý Quang Diệu', 'Nam', '1998-11-23', '0901000047', '001090000047', 'dieu.lq@vnm.vn', 'Vĩnh Phúc', '2023-08-15', 'Đại học', 'Kế toán tài sản cố định', 'Chính thức', 'BH047982', 'MST047982', 'CV04', 15000000),
    ('NV048', 'Phạm Minh Nhật', 'Nam', '1999-12-01', '0901000048', '001090000048', 'nhat.pm@vnm.vn', 'Hà Nội', '2023-10-01', 'Đại học', 'Chuyên viên Tư vấn Doanh nghiệp', 'Thử việc', 'BH048993', 'MST048993', 'CV06', 13000000),
    ('NV049', 'Nguyễn Trọng Đại', 'Nam', '2001-04-16', '0901000049', '001090000049', 'dai.nt@vnm.vn', 'Hải Phòng', '2024-02-15', 'Đại học', 'Lập trình viên Thực tập (Python/AI)', 'Thực tập sinh', 'BH049014', 'MST049014', 'CV08', 9000000),
    ('NV050', 'Tạ Bích Loan', 'Nữ', '1986-07-29', '0901000050', '001090000050', 'loan.tb@vnm.vn', 'Hà Nội', '2016-08-01', 'Thạc sĩ', 'Quản trị Dự án Doanh nghiệp', 'Chính thức', 'BH050865', 'MST050865', 'CV16', 36000000)
]

def seed_database():
    app = create_app()
    with app.app_context():
        db = get_db()
        print("=== BẮT ĐẦU KHỞI TẠO 50 NHÂN VIÊN & 8 PHÒNG BAN ===")

        # 1. Seed 8 PhongBan
        for mpb, tpb in DEPARTMENTS:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM PhongBan WHERE MaPB = ?)
                    INSERT INTO PhongBan(MaPB, TenPB) VALUES(?, ?)
                ELSE
                    UPDATE PhongBan SET TenPB = ? WHERE MaPB = ?
            """, (mpb, mpb, tpb, tpb, mpb))
        print(f"-> Đã đảm bảo 8 phòng ban ({len(DEPARTMENTS)})")

        # 2. Seed 16 ChucVu
        for mcv, tcv, mpb in POSITIONS:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM ChucVu WHERE MaCV = ?)
                    INSERT INTO ChucVu(MaCV, TenCV, MaPB) VALUES(?, ?, ?)
                ELSE
                    UPDATE ChucVu SET TenCV = ?, MaPB = ? WHERE MaCV = ?
            """, (mcv, mcv, tcv, mpb, tcv, mpb, mcv))
        print(f"-> Đã đảm bảo 16 chức vụ ({len(POSITIONS)})")

        # Create avatar files in static/uploads/avatars
        avatar_dir = os.path.join(os.path.dirname(__file__), 'ss', 'static', 'uploads', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)

        current_month = date.today().strftime('%Y-%m')
        prev_month = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        today_str = date.today().strftime('%Y-%m-%d')

        # 3. Seed 50 Employees
        for emp in EMPLOYEES_RAW:
            (mnv, hoten, gt, ns, sdt, cccd, email, dc, nvct, td, cm, lnv, bhxh, mst, mcv, sal) = emp
            avatar_path = f"/static/uploads/avatars/avatar_{mnv}.svg"

            # Create SVG avatar file if missing
            svg_file = os.path.join(avatar_dir, f"avatar_{mnv}.svg")
            if not os.path.exists(svg_file):
                bg_color = random.choice(['#4f46e5', '#2563eb', '#0891b2', '#059669', '#d97706', '#7c3aed', '#db2777'])
                initials = hoten.strip().split()[-1][:1].upper()
                svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160">
  <rect width="120" height="160" rx="8" fill="{bg_color}"/>
  <circle cx="60" cy="62" r="32" fill="#ffffff" opacity="0.25"/>
  <text x="60" y="74" font-family="Arial, sans-serif" font-size="36" font-weight="bold" fill="#ffffff" text-anchor="middle">{initials}</text>
  <path d="M20 148 C 20 108, 100 108, 100 148 Z" fill="#ffffff" opacity="0.25"/>
  <rect x="0" y="142" width="120" height="18" fill="rgba(0,0,0,0.3)"/>
  <text x="60" y="154" font-family="Arial, sans-serif" font-size="10" font-weight="bold" fill="#ffffff" text-anchor="middle">Ảnh 3x4 • {mnv}</text>
</svg>"""
                with open(svg_file, 'w', encoding='utf-8') as f:
                    f.write(svg_content)

            # Insert or update NhanVien
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM NhanVien WHERE MaNV = ?)
                    INSERT INTO NhanVien(MaNV, HoTen, GioiTinh, NgaySinh, SDT, CCCD, Email, DiaChi, NgayVaoCT, TrinhDo, ChuyenMon, LoaiNhanVien, SoBHXH, MaSoThue, MaCV, HinhAnh)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ELSE
                    UPDATE NhanVien
                    SET HoTen=?, GioiTinh=?, NgaySinh=?, SDT=?, CCCD=?, Email=?, DiaChi=?, NgayVaoCT=?, TrinhDo=?, ChuyenMon=?, LoaiNhanVien=?, SoBHXH=?, MaSoThue=?, MaCV=?, HinhAnh=?
                    WHERE MaNV=?
            """, (
                mnv, mnv, hoten, gt, ns, sdt, cccd, email, dc, nvct, td, cm, lnv, bhxh, mst, mcv, avatar_path,
                hoten, gt, ns, sdt, cccd, email, dc, nvct, td, cm, lnv, bhxh, mst, mcv, avatar_path, mnv
            ))

            # 4. Create Contract (HopDong)
            hd_code = f"HD{mnv[2:]}"
            start_date = '2026-10-01' if mnv in ('NV001', 'NV002', 'NV003', 'NV004', 'NV005') else nvct
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM HopDong WHERE MaHD = ?)
                    INSERT INTO HopDong(MaHD, MaNV, LoaiHD, NgayBD, NgayKT, LuongCoBan, TrangThai, GhiChu, HinhAnh)
                    VALUES(?, ?, ?, ?, ?, ?, N'Hiệu lực', N'Hợp đồng lao động tiêu chuẩn', ?)
                ELSE
                    UPDATE HopDong SET LuongCoBan = ?, NgayBD = ?, TrangThai = N'Hiệu lực' WHERE MaHD = ?
            """, (
                hd_code, hd_code, mnv, 'Xác định thời hạn (3 năm)' if lnv == 'Chính thức' else ('Thử việc' if lnv == 'Thử việc' else 'Học việc'),
                start_date, '2028-12-31', sal, avatar_path, sal, start_date, hd_code
            ))

            # 5. Create Payroll (Luong) for current month and previous month
            bh = round(sal * 0.105, 0)
            thuong = 2000000 if lnv == 'Chính thức' else (1000000 if lnv == 'Thử việc' else 500000)
            phucap = 1500000 if lnv == 'Chính thức' else 1000000
            thue = round((sal - 11000000) * 0.05, 0) if sal > 11000000 else 0

            # Current month
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM Luong WHERE MaNV = ? AND ThangNam = ?)
                    INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap, BaoHiem, ThueTNCN, KhauTruKhac)
                    VALUES(?, ?, ?, ?, 0, ?, ?, ?, 0)
                ELSE
                    UPDATE Luong SET LuongCung = ?, LuongThuong = ?, PhuCap = ?, BaoHiem = ?, ThueTNCN = ? WHERE MaNV = ? AND ThangNam = ?
            """, (
                mnv, current_month, mnv, current_month, sal, thuong, phucap, bh, thue,
                sal, thuong, phucap, bh, thue, mnv, current_month
            ))

            # Previous month
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM Luong WHERE MaNV = ? AND ThangNam = ?)
                    INSERT INTO Luong(MaNV, ThangNam, LuongCung, LuongThuong, LuongUngTruoc, PhuCap, BaoHiem, ThueTNCN, KhauTruKhac)
                    VALUES(?, ?, ?, ?, 0, ?, ?, ?, 0)
            """, (mnv, prev_month, mnv, prev_month, sal, thuong, phucap, bh, thue))

            # 6. Create Attendance (ChamCong) for today
            # Vary times: mostly on time, some late or early
            i_num = int(mnv[2:])
            if i_num % 12 == 0:
                st, in_t, out_t, note = 'Đi muộn', '08:25', '17:30', 'Kẹt xe tuyến đường Giải Phóng'
            elif i_num % 17 == 0:
                st, in_t, out_t, note = 'Về sớm', '08:00', '16:30', 'Xin phép về sớm đi khám bệnh'
            elif i_num % 25 == 0:
                st, in_t, out_t, note = 'Nghỉ', None, None, 'Nghỉ phép năm đã duyệt'
            else:
                st, in_t, out_t, note = 'Đúng giờ', f"07:{50 + (i_num % 10):02d}", '17:30', 'Chấm công máy vân tay'

            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM ChamCong WHERE MaNV = ? AND Ngay = ?)
                    INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu)
                    VALUES(?, ?, ?, ?, ?, ?)
                ELSE
                    UPDATE ChamCong SET GioVao=?, GioRa=?, TrangThai=?, GhiChu=? WHERE MaNV=? AND Ngay=?
            """, (
                mnv, today_str, mnv, today_str, in_t, out_t, st, note,
                in_t, out_t, st, note, mnv, today_str
            ))

            # 7. Create Accounts (TaiKhoan)
            # Manager accounts for department heads (NV001, NV006, NV007, NV008, NV009, NV010, NV011, NV012)
            is_manager = mcv in ('CV01', 'CV03', 'CV05', 'CV07', 'CV09', 'CV11', 'CV13', 'CV15')
            user_dn = f"ql{mnv[2:]}" if is_manager else f"nv{mnv[2:]}"
            user_role = QL if is_manager else NV

            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM TaiKhoan WHERE TenDN = ?)
                    INSERT INTO TaiKhoan(TenDN, MatKhau, MaNV, LoaiTK) VALUES(?, ?, ?, ?)
                ELSE
                    UPDATE TaiKhoan SET MaNV = ?, LoaiTK = ? WHERE TenDN = ?
            """, (user_dn, user_dn, '123456', mnv, user_role, mnv, user_role, user_dn))

        print(f"-> Đã khởi tạo đầy đủ 50 hồ sơ nhân viên, 50 hợp đồng, 100 bảng lương, 50 chấm công hôm nay!")

        # 8. Seed Khen thưởng & Kỷ luật (KhenThuongKyLuat)
        rewards = [
            ('NV001', 'Khen thưởng', 'QĐ-KT/2026-01', '2026-01-15', 'Bằng khen & Tiền thưởng', 5000000, 'Lãnh đạo xuất sắc hoàn thành kế hoạch nhân sự năm 2025', 'Ban Giám Đốc'),
            ('NV002', 'Khen thưởng', 'QĐ-KT/2026-03', '2026-03-20', 'Tiền thưởng nóng', 2000000, 'Đạt chỉ tiêu tuyển dụng 15 chuyên viên chất lượng cao trong quý 1', 'Ban Giám Đốc'),
            ('NV005', 'Khen thưởng', 'QĐ-KT/2026-04', '2026-04-10', 'Bằng khen & Cúp vinh danh', 3000000, 'Sáng kiến tối ưu hóa hệ thống ERP giúp giảm 40% thời gian xử lý', 'Ban Giám Đốc'),
            ('NV007', 'Khen thưởng', 'QĐ-KT/2026-06', '2026-06-30', 'Tiền thưởng doanh số', 10000000, 'Đột phá doanh thu quý 2 vượt 140% chỉ tiêu kế hoạch', 'Tổng Giám Đốc'),
            ('NV008', 'Khen thưởng', 'QĐ-KT/2026-07', '2026-07-15', 'Khen thưởng chuyên môn', 4000000, 'Triển khai thành công hệ thống Cloud bảo mật theo chuẩn ISO 27001', 'Ban Giám Đốc'),
            ('NV012', 'Khen thưởng', 'QĐ-KT/2026-08', '2026-08-19', 'Kỷ niệm chương & Cổ phiếu ESOP', 15000000, 'Đóng góp 10 năm cống hiến xây dựng và phát triển công ty', 'Hội đồng Quản trị'),
            ('NV014', 'Khen thưởng', 'QĐ-KT/2026-09', '2026-09-02', 'Tiền thưởng dự án', 3500000, 'Hoàn thành module AI Chatbot vượt tiến độ 2 tuần', 'Trưởng phòng CNTT'),
            ('NV021', 'Khen thưởng', 'QĐ-KT/2026-09', '2026-09-25', 'Tiền thưởng UI/UX', 2500000, 'Thiết kế giao diện Dark Mode & Dashboard hiện đại nhận đánh giá xuất sắc', 'Trưởng phòng CNTT'),
            ('NV027', 'Khen thưởng', 'QĐ-KT/2026-10', '2026-10-15', 'Tiền thưởng hợp đồng', 5000000, 'Ký kết thành công hợp đồng cung cấp phần mềm giá trị 2.5 tỷ VNĐ', 'Trưởng phòng KD'),
            ('NV030', 'Khen thưởng', 'QĐ-KT/2026-10', '2026-10-20', 'Ngôi sao CSKH tháng', 2000000, 'Đạt chỉ số hài lòng khách hàng CSAT 99.5% trong tháng', 'Trưởng phòng CSKH'),
            ('NV018', 'Kỷ luật', 'QĐ-KL/2026-05', '2026-05-12', 'Khiển trách bằng văn bản', 0, 'Vi phạm quy định giờ giấc đi muộn quá 4 lần trong tháng mà không có lý do', 'Trưởng phòng NS'),
            ('NV029', 'Kỷ luật', 'QĐ-KL/2026-08', '2026-08-22', 'Trừ 50% thưởng hiệu quả', 1000000, 'Bất cẩn trong việc ngắt nguồn điện máy lạnh phòng kỹ thuật ngoài giờ làm', 'Trưởng phòng KT')
        ]
        for mnv, loai, sqd, nqd, ht, tien, ld, nk in rewards:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM KhenThuongKyLuat WHERE SoQuyetDinh = ?)
                    INSERT INTO KhenThuongKyLuat(MaNV, Loai, SoQuyetDinh, NgayQuyetDinh, HinhThuc, SoTien, LyDo, NguoiKy)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """, (sqd, mnv, loai, sqd, nqd, ht, tien, ld, nk))
        print(f"-> Đã khởi tạo {len(rewards)} quyết định khen thưởng & kỷ luật mẫu!")

        # 9. Clean any duplicates
        clean_all_duplicates(db)
        db.commit()

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
