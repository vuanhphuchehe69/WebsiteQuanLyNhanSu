# -*- coding: utf-8 -*-
"""Kịch bản khởi tạo và nạp toàn bộ dữ liệu chuẩn cho hệ thống Quản lý nhân sự (HRM):
- 4 Phòng ban: Nhân sự (PB01), Kế toán (PB02), Kinh doanh (PB03), Kỹ thuật (PB04)
- 13 Chức vụ chuyên môn (CV01 - CV13)
- 13 Nhân viên chuẩn (NV001 - NV013) gồm 4 Trưởng phòng và các chuyên viên phòng ban
- 15 Tài khoản đăng nhập: tên đăng nhập là mã nhân viên (nv001, nv006, nv007, nv008,...) mật khẩu 123456
- Toàn bộ nghiệp vụ: Hợp đồng, Bảng lương, Chấm công, Nghỉ phép, Tăng ca, Tạm ứng, KPI, Bằng cấp, Đề xuất, Tuyển dụng, Thông báo
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

def seed_transaction_records(db):
    """Nạp toàn diện dữ liệu nghiệp vụ: chấm công, đơn từ, KPI, tuyển dụng, thông báo."""
    print("\n=== BẮT ĐẦU NẠP DỮ LIỆU NGHIỆP VỤ CHO CÁC PHÒNG BAN ===")
    employees = db.execute("SELECT MaNV, HoTen, GioiTinh, TrinhDo, ChuyenMon, MaCV FROM NhanVien ORDER BY MaNV").fetchall()

    # 1. Chấm công chi tiết tháng 10/2026
    print("[1/11] Nạp dữ liệu Chấm công (ChamCong) chi tiết tháng 10/2026...")
    work_days = [
        '2026-10-01', '2026-10-02', '2026-10-05', '2026-10-06', '2026-10-07',
        '2026-10-08', '2026-10-09', '2026-10-12', '2026-10-13', '2026-10-14',
        '2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21',
        '2026-10-22', '2026-10-23', '2026-10-26', '2026-10-27', '2026-10-28',
        '2026-10-29', '2026-10-30'
    ]
    for emp in employees:
        mnv = emp['MaNV']
        emp_seed = int(mnv[2:])
        for idx, d_str in enumerate(work_days):
            hash_val = (emp_seed * 37 + idx * 19) % 100
            if hash_val < 86:
                gio_vao = f"07:{45 + (hash_val % 14):02d}"
                gio_ra = f"17:{30 + (hash_val % 16):02d}"
                trang_thai = 'Đúng giờ'
                ghi_chu = 'Chấm công máy vân tay'
            elif hash_val < 94:
                gio_vao = f"08:{10 + (hash_val % 25):02d}"
                gio_ra = '17:35'
                trang_thai = 'Đi muộn'
                ghi_chu = 'Ùn tắc giao thông tuyến đường chính'
            else:
                if hash_val % 2 == 0:
                    gio_vao = '08:00'
                    gio_ra = '16:30'
                    trang_thai = 'Về sớm'
                    ghi_chu = 'Có đơn xin về sớm đã phê duyệt'
                else:
                    gio_vao = None
                    gio_ra = None
                    trang_thai = 'Nghỉ'
                    ghi_chu = 'Nghỉ phép hưởng lương'

            row = db.execute("SELECT 1 FROM ChamCong WHERE MaNV = ? AND Ngay = ?", (mnv, d_str)).fetchone()
            if not row:
                db.execute(
                    "INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu) VALUES(?, ?, ?, ?, ?, ?)",
                    (mnv, d_str, gio_vao, gio_ra, trang_thai, ghi_chu)
                )
    db.commit()

    # 2. Đơn nghỉ phép
    print("[2/11] Nạp dữ liệu Đơn nghỉ phép (NghiPhep)...")
    leave_samples = [
        ('NV002', '2026-10-08', '2026-10-09', 'Đã duyệt', 'Nghỉ phép thường niên đi du lịch cùng gia đình'),
        ('NV003', '2026-10-14', '2026-10-15', 'Đã duyệt', 'Giải quyết việc riêng đột xuất tại quê nhà'),
        ('NV004', '2026-10-21', '2026-10-22', 'Đã duyệt', 'Nghỉ ốm sốt phát ban có giấy chỉ định của bác sĩ'),
        ('NV007', '2026-10-26', '2026-10-26', 'Đã duyệt', 'Khám sức khỏe tổng quát định kỳ'),
        ('NV009', '2026-10-19', '2026-10-20', 'Đã duyệt', 'Tham dự lễ tốt nghiệp khóa cao học'),
        ('NV010', '2026-10-27', '2026-10-28', 'Chờ duyệt', 'Về quê có việc gia đình hiếu hỉ'),
        ('NV011', '2026-10-29', '2026-10-30', 'Chờ duyệt', 'Đăng ký nghỉ phép cá nhân cuối tháng'),
        ('NV012', '2026-10-12', '2026-10-13', 'Từ chối', 'Bộ phận đang cao điểm triển khai dự án hạ tầng'),
        ('NV013', '2026-10-23', '2026-10-23', 'Đã duyệt', 'Giải quyết thủ tục hành chính công chứng cá nhân')
    ]
    for mnv_l, nbd, nkt, tt_l, ld_l in leave_samples:
        row = db.execute("SELECT 1 FROM NghiPhep WHERE MaNV = ? AND NgayBD = ?", (mnv_l, nbd)).fetchone()
        if not row:
            db.execute("INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, TrangThai, LyDo) VALUES(?, ?, ?, ?, ?)", (mnv_l, nbd, nkt, tt_l, ld_l))
    db.commit()

    # 3. Đăng ký tăng ca
    print("[3/11] Nạp dữ liệu Tăng ca (TangCa)...")
    ot_samples = [
        ('NV002', 3.0, '2026-10-06', 'Ngày thường', 'Đã duyệt', 'Hoàn tất hồ sơ nhân sự chuẩn bị kiểm toán quý 3', 'Nguyễn Văn An'),
        ('NV003', 4.0, '2026-10-10', 'Thứ 7 / CN', 'Đã duyệt', 'Khóa sổ và đối chiếu công nợ khách hàng cuối quý', 'Vũ Thị Hoa'),
        ('NV004', 2.5, '2026-10-16', 'Ngày thường', 'Đã duyệt', 'Hỗ trợ khách hàng doanh nghiệp chốt hợp đồng B2B', 'Bùi Quang Huy'),
        ('NV005', 3.5, '2026-10-23', 'Ngày thường', 'Đã duyệt', 'Triển khai hotfix hệ thống phân quyền', 'Đỗ Hoàng Long'),
        ('NV009', 3.0, '2026-10-15', 'Ngày thường', 'Đã duyệt', 'Lập báo cáo tài chính nội bộ định kỳ', 'Vũ Thị Hoa'),
        ('NV010', 2.0, '2026-10-22', 'Ngày thường', 'Đã duyệt', 'Chuẩn bị tài liệu tiếp thị cho sự kiện hội thảo', 'Bùi Quang Huy'),
        ('NV011', 4.0, '2026-10-24', 'Thứ 7 / CN', 'Đã duyệt', 'Kiểm thử tải hiệu năng và bảo mật hệ thống', 'Đỗ Hoàng Long'),
        ('NV012', 3.0, '2026-10-28', 'Ngày thường', 'Chờ duyệt', 'Bảo trì máy chủ và cấu hình dự phòng đám mây', 'Đỗ Hoàng Long')
    ]
    for mnv_o, sg, n_ot, loai_ot, tt_o, ld_o, ng_o in ot_samples:
        row = db.execute("SELECT 1 FROM TangCa WHERE MaNV = ? AND Ngay = ?", (mnv_o, n_ot)).fetchone()
        if not row:
            db.execute("INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai, TrangThai, LyDo, NguoiDuyet) VALUES(?, ?, ?, ?, ?, ?, ?)", (mnv_o, sg, n_ot, loai_ot, tt_o, ld_o, ng_o))
    db.commit()

    # 4. Tạm ứng tiền lương
    print("[4/11] Nạp dữ liệu Tạm ứng lương (TamUng)...")
    advance_samples = [
        ('NV002', '2026-10', 3000000, 'Chi trả viện phí cho người thân nằm viện đột xuất', '2026-10-10', 'Đã duyệt', 'Vũ Thị Hoa'),
        ('NV003', '2026-10', 4000000, 'Đóng học phí đầu năm cho con', '2026-10-12', 'Đã duyệt', 'Vũ Thị Hoa'),
        ('NV004', '2026-10', 2500000, 'Sửa chữa phương tiện xe máy đi lại làm việc', '2026-10-15', 'Đã duyệt', 'Bùi Quang Huy'),
        ('NV010', '2026-10', 3000000, 'Đóng tiền thuê nhà trọ theo chu kỳ', '2026-10-18', 'Chờ duyệt', 'Bùi Quang Huy'),
        ('NV011', '2026-10', 2000000, 'Chi phí phát sinh sinh hoạt gia đình trong tháng', '2026-10-20', 'Chờ duyệt', 'Đỗ Hoàng Long')
    ]
    for mnv_u, t_u, st_u, ld_u, ny_u, tt_u, nd_u in advance_samples:
        row = db.execute("SELECT 1 FROM TamUng WHERE MaNV = ? AND ThangNam = ?", (mnv_u, t_u)).fetchone()
        if not row:
            db.execute("INSERT INTO TamUng(MaNV, ThangNam, SoTien, LyDo, NgayYeuCau, TrangThai, NguoiDuyet) VALUES(?, ?, ?, ?, ?, ?, ?)", (mnv_u, t_u, st_u, ld_u, ny_u, tt_u, nd_u))
    db.commit()

    # 5. Giải trình công
    print("[5/11] Nạp dữ liệu Giải trình công (GiaiTrinhCong)...")
    explain_samples = [
        ('NV002', '2026-10-05', 'Quên quẹt thẻ do vội vào cuộc họp nhân sự đầu tuần', 'Đã duyệt', 'Nguyễn Văn An'),
        ('NV004', '2026-10-09', 'Đi gặp khách hàng đối tác ký hợp đồng từ sáng sớm', 'Đã duyệt', 'Bùi Quang Huy'),
        ('NV003', '2026-10-13', 'Máy chấm công vân tay không nhận cảm biến quang học', 'Đã duyệt', 'Vũ Thị Hoa'),
        ('NV011', '2026-10-16', 'Tham gia hỗ trợ sự kiện kỹ thuật tại cơ sở 2', 'Đã duyệt', 'Đỗ Hoàng Long'),
        ('NV012', '2026-10-21', 'Thẻ nhân viên bị gãy chưa kịp cấp lại thẻ mới', 'Chờ duyệt', 'Đỗ Hoàng Long')
    ]
    for mnv_g, d_g, ld_g, tt_g, nd_g in explain_samples:
        row = db.execute("SELECT 1 FROM GiaiTrinhCong WHERE MaNV = ? AND Ngay = ?", (mnv_g, d_g)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO GiaiTrinhCong(MaNV, Ngay, GioVaoDeXuat, GioRaDeXuat, LyDo, TrangThai, NguoiDuyet, NgayGui)
                VALUES(?, ?, '08:00', '17:30', ?, ?, ?, '2026-10-22')
            """, (mnv_g, d_g, ld_g, tt_g, nd_g))
    db.commit()

    # 6. Đánh giá KPI
    print("[6/11] Nạp dữ liệu Đánh giá KPI (DanhGia)...")
    kpi_evals = [
        ('NV001', '2026-10', 95.0, 'Xuất sắc', 'Lãnh đạo xuất sắc hoàn thành kế hoạch nhân sự toàn công ty.', 'Ban Giám Đốc', 95.0, 'Đạt 100% chỉ tiêu phòng.'),
        ('NV002', '2026-10', 92.0, 'Xuất sắc', 'Hoàn thành xuất sắc kế hoạch tuyển dụng và quản lý hồ sơ.', 'Nguyễn Văn An', 90.0, 'Nỗ lực hoàn thành công việc đúng tiến độ.'),
        ('NV003', '2026-10', 85.0, 'Tốt', 'Thực hiện đối soát số liệu kế toán chính xác, kịp thời.', 'Vũ Thị Hoa', 85.0, 'Hoàn thành tốt các báo cáo được giao.'),
        ('NV004', '2026-10', 88.0, 'Tốt', 'Chủ động phát triển tệp khách hàng mới, vượt chỉ tiêu doanh số.', 'Bùi Quang Huy', 90.0, 'Đạt chỉ tiêu doanh thu tháng.'),
        ('NV005', '2026-10', 91.0, 'Xuất sắc', 'Lập trình tính năng nhanh, chất lượng mã nguồn tốt, ít lỗi.', 'Đỗ Hoàng Long', 92.0, 'Hoàn thành mọi task đúng hạn.'),
        ('NV006', '2026-10', 94.0, 'Xuất sắc', 'Quản trị ngân sách tài chính chặt chẽ, tối ưu chi phí vận hành.', 'Ban Giám Đốc', 95.0, 'Kế hoạch tài chính minh bạch.'),
        ('NV007', '2026-10', 96.0, 'Xuất sắc', 'Dẫn dắt phòng Kinh doanh đạt 135% chỉ tiêu tháng.', 'Ban Giám Đốc', 98.0, 'Doanh thu phòng tăng trưởng vượt bậc.'),
        ('NV008', '2026-10', 93.0, 'Xuất sắc', 'Đảm bảo hệ thống hạ tầng và phần mềm vận hành ổn định 99.9%.', 'Ban Giám Đốc', 95.0, 'Hệ thống vận hành an toàn.'),
        ('NV009', '2026-10', 86.0, 'Tốt', 'Báo cáo tổng hợp thuế và hóa đơn rõ ràng, không sai sót.', 'Vũ Thị Hoa', 85.0, 'Hoàn thành sổ sách đúng hạn.'),
        ('NV010', '2026-10', 87.0, 'Tốt', 'Chiến dịch tiếp thị số đạt lượng tiếp cận và tương tác cao.', 'Bùi Quang Huy', 88.0, 'Hoàn thành kế hoạch truyền thông.'),
        ('NV011', '2026-10', 89.0, 'Tốt', 'Kiểm thử chặt chẽ, phát hiện sớm các lỗi nghiệp vụ quan trọng.', 'Đỗ Hoàng Long', 90.0, 'Bắt lỗi chính xác, phối hợp tốt.'),
        ('NV012', '2026-10', 88.0, 'Tốt', 'Tự động hóa quy trình CI/CD mượt mà, hỗ trợ tốt dev team.', 'Đỗ Hoàng Long', 88.0, 'Deploy hệ thống an toàn.'),
        ('NV013', '2026-10', 86.0, 'Tốt', 'Hỗ trợ tuyển dụng và sàng lọc ứng viên chu đáo, chuyên nghiệp.', 'Nguyễn Văn An', 85.0, 'Phản hồi ứng viên kịp thời.')
    ]
    for mnv_k, t_k, dk, xl, nx, ng_d, dtd, nxc in kpi_evals:
        row = db.execute("SELECT 1 FROM DanhGia WHERE MaNV = ? AND ThangNam = ?", (mnv_k, t_k)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO DanhGia(MaNV, ThangNam, DiemKPI, XepLoai, NhanXet, NguoiDanhGia, DiemTuDanhGia, NhanXetCaNhan)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """, (mnv_k, t_k, dk, xl, nx, ng_d, dtd, nxc))
    db.commit()

    # 7. Bằng cấp, chứng chỉ
    print("[7/11] Nạp Bằng cấp, Chứng chỉ (TaiLieuNhanVien)...")
    docs = [
        ('NV001', 'Bằng Thạc sĩ Quản trị Nhân lực', 'Bằng cấp', '2013-06-25', 'Đại học Kinh tế Quốc dân', 'Bằng thạc sĩ loại Giỏi'),
        ('NV002', 'Bằng Cử nhân Quản lý Lao động', 'Bằng cấp', '2014-06-20', 'Đại học Lao động - Xã hội', 'Bằng cử nhân chính quy'),
        ('NV003', 'Chứng chỉ Kế toán trưởng Quốc gia', 'Chứng chỉ', '2021-08-15', 'Hội Kế toán & Kiểm toán Việt Nam', 'Chứng chỉ hành nghề kế toán'),
        ('NV004', 'Chứng chỉ Tiếng Anh TOEIC 850', 'Chứng chỉ', '2022-04-10', 'IIG Vietnam', 'Chứng chỉ ngoại ngữ quốc tế'),
        ('NV005', 'Bằng Kỹ sư Công nghệ Thông tin', 'Bằng cấp', '2020-07-15', 'Đại học Bách Khoa Hà Nội', 'Bằng kỹ sư loại Xuất sắc'),
        ('NV006', 'Chứng chỉ Kiểm toán viên Quốc tế CPA', 'Chứng chỉ', '2019-11-20', 'Bộ Tài Chính', 'Chứng chỉ kiểm toán viên'),
        ('NV007', 'Bằng Thạc sĩ Quản trị Kinh doanh (MBA)', 'Bằng cấp', '2016-12-10', 'Đại học Ngoại Thương', 'Bằng thạc sĩ MBA'),
        ('NV008', 'Chứng chỉ Kiến trúc sư Đám mây AWS Solutions Architect', 'Chứng chỉ', '2021-05-18', 'Amazon Web Services', 'Chứng chỉ đám mây cấp chuyên nghiệp'),
        ('NV011', 'Chứng chỉ Kiểm thử Quốc tế ISTQB Certified Tester', 'Chứng chỉ', '2022-09-05', 'ISTQB International', 'Chứng chỉ kiểm thử phần mềm'),
        ('NV012', 'Chứng chỉ Quản trị Container Kubernetes CKA', 'Chứng chỉ', '2023-03-12', 'Cloud Native Computing Foundation', 'Chứng chỉ DevOps chuyên nghiệp')
    ]
    for mnv_d, ten_d, loai_d, n_cap, noi_cap, gc_d in docs:
        row = db.execute("SELECT 1 FROM TaiLieuNhanVien WHERE MaNV = ? AND TenTaiLieu = ?", (mnv_d, ten_d)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO TaiLieuNhanVien(MaNV, TenTaiLieu, Loai, NgayCap, NoiCap, NgayTai, GhiChu)
                VALUES(?, ?, ?, ?, ?, '2026-10-01 09:00', ?)
            """, (mnv_d, ten_d, loai_d, n_cap, noi_cap, gc_d))
    db.commit()

    # 8. Đề xuất & Khiếu nại
    print("[8/13] Nạp Đề xuất & Khiếu nại (DeXuatKhieuNai)...")
    feedbacks = [
        ('NV005', 'Đề xuất trang bị màn hình máy tính phụ cho đội Lập trình & QA', 'Đề xuất cơ sở vật chất', 'Giúp nhân viên đối chiếu mã nguồn và tài liệu thiết kế nhanh hơn, tăng 30% hiệu suất.', '2026-10-05', 'Đã xử lý', 'Phòng Hành chính đã bàn giao màn hình phụ Dell 24 inch.'),
        ('NV004', 'Đề xuất tài trợ chi phí thi chứng chỉ quốc tế cho nhân viên đạt loại Tốt', 'Đề xuất chế độ', 'Khuyến khích nhân viên tự học và nâng cao năng lực chuyên môn đạt chuẩn quốc tế.', '2026-10-12', 'Đã xử lý', 'Ban Giám đốc đồng ý hỗ trợ 70% lệ phí thi cho nhân viên đạt kết quả.'),
        ('NV010', 'Đề xuất mua sách chuyên môn bổ sung cho Tủ sách công ty', 'Đề xuất văn hóa', 'Bổ sung các đầu sách về AI, Clean Code, Thiết kế hệ thống phân tán và Marketing số.', '2026-10-18', 'Đang xử lý', 'Đang tổng hợp danh sách sách đặt mua tại Fahasa.')
    ]
    for mnv_f, td_f, l_f, nd_f, ng_f, tt_f, ph_f in feedbacks:
        row = db.execute("SELECT 1 FROM DeXuatKhieuNai WHERE TieuDe = ?", (td_f,)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO DeXuatKhieuNai(MaNV, TieuDe, Loai, NoiDung, NgayGui, TrangThai, PhanHoi, NguoiXuLy)
                VALUES(?, ?, ?, ?, ?, ?, ?, N'Ban Quản lý & Nhân sự')
            """, (mnv_f, td_f, l_f, nd_f, ng_f, tt_f, ph_f))
    db.commit()

    # 9. Đề xuất nhân sự
    print("[9/13] Nạp Đề xuất nhân sự từ Quản lý gửi Admin (DeXuatNhanSu)...")
    proposals = [
        ('NV008', 'NV005', 'Tăng lương', 'Tăng mức lương lên 25.000.000đ', 'Đảm nhiệm vai trò Fullstack Lead kiến trúc hệ thống ổn định cao', 'Đã duyệt', 'Đã phê duyệt điều chỉnh hợp đồng lao động mới.'),
        ('NV007', 'NV004', 'Khen thưởng', 'Thưởng nóng 5.000.000đ', 'Dẫn dắt chiến dịch ra mắt dịch vụ mới đạt 140% chỉ tiêu doanh số', 'Đã duyệt', 'Khen thưởng và tuyên dương toàn công ty.'),
        ('NV006', 'NV009', 'Tăng lương', 'Tăng 15% lương cơ sở', 'Nhân viên có năng lực vượt trội, đảm nhiệm xuất sắc cả phần báo cáo thuế và quản trị dòng tiền', 'Đang xử lý', 'Đang thẩm định hồ sơ cùng Ban Giám đốc.'),
        ('NV001', 'NV002', 'Khen thưởng', 'Danh hiệu Nhân viên Nhân sự xuất sắc', 'Đạt chỉ tiêu hoàn thành rà soát hồ sơ toàn công ty', 'Đã duyệt', 'Trao bằng khen và phần thưởng 3.000.000đ.')
    ]
    for n_dx, mnv_tgt, loai_p, muc_p, lydo_p, tt_p, yk_p in proposals:
        row = db.execute("SELECT 1 FROM DeXuatNhanSu WHERE MaNV = ? AND LoaiDeXuat = ? AND MucDeXuat = ?", (mnv_tgt, loai_p, muc_p)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO DeXuatNhanSu(MaNV, NguoiDeXuat, LoaiDeXuat, MucDeXuat, LyDo, NgayDeXuat, TrangThai, YKienPheDuyet, NguoiPheDuyet)
                VALUES(?, ?, ?, ?, ?, '2026-10-18', ?, ?, N'Ban Giám Đốc')
            """, (mnv_tgt, n_dx, loai_p, muc_p, lydo_p, tt_p, yk_p))
    db.commit()

    # 10. Khóa đào tạo & Đăng ký tham gia
    print("[10/13] Nạp Khóa đào tạo (KhoaDaoTao) & Đăng ký tham gia (DangKyDaoTao)...")
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
        row = db.execute("SELECT 1 FROM KhoaDaoTao WHERE TenKhoa = ?", (ten_k,)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO KhoaDaoTao(TenKhoa, GiangVien, ThoiGian, DiaDiem, SoLuong, MoTa, TrangThai)
                VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (ten_k, gv_k, tg_k, dd_k, sl_k, mt_k, tt_k))
        else:
            db.execute("""
                UPDATE KhoaDaoTao SET GiangVien = ?, ThoiGian = ?, DiaDiem = ?, SoLuong = ?, MoTa = ?, TrangThai = ? WHERE TenKhoa = ?
            """, (gv_k, tg_k, dd_k, sl_k, mt_k, tt_k, ten_k))
    db.commit()

    # Đăng ký khóa học cho nhân viên
    kdt_rows = db.execute("SELECT MaKDT, TenKhoa FROM KhoaDaoTao ORDER BY MaKDT").fetchall()
    kdt_map = {c[0]: None for c in courses}
    for kr in kdt_rows:
        if kr['TenKhoa'] in kdt_map:
            kdt_map[kr['TenKhoa']] = kr['MaKDT']

    sample_dk = [
        # Course 0: An toàn thông tin ISO 27001
        (courses[0][0], 'NV001', '2026-10-15 08:30', 'Đang học'),
        (courses[0][0], 'NV005', '2026-10-15 09:15', 'Đang học'),
        (courses[0][0], 'NV008', '2026-10-15 10:20', 'Đang học'),
        (courses[0][0], 'NV011', '2026-10-15 11:00', 'Đang học'),
        (courses[0][0], 'NV012', '2026-10-15 14:10', 'Đang học'),
        (courses[0][0], 'NV006', '2026-10-15 15:30', 'Đang học'),
        # Course 1: Giao tiếp & Đàm phán
        (courses[1][0], 'NV002', '2026-10-16 10:00', 'Đã đăng ký'),
        (courses[1][0], 'NV004', '2026-10-16 14:20', 'Đã đăng ký'),
        (courses[1][0], 'NV007', '2026-10-16 15:00', 'Đã đăng ký'),
        (courses[1][0], 'NV010', '2026-10-16 16:45', 'Đã đăng ký'),
        (courses[1][0], 'NV013', '2026-10-16 17:10', 'Đã đăng ký'),
        # Course 2: Agile & Scrum
        (courses[2][0], 'NV005', '2026-10-17 08:45', 'Đang học'),
        (courses[2][0], 'NV008', '2026-10-17 09:30', 'Đang học'),
        (courses[2][0], 'NV011', '2026-10-17 10:15', 'Đang học'),
        (courses[2][0], 'NV012', '2026-10-17 11:40', 'Đang học'),
        (courses[2][0], 'NV010', '2026-10-17 14:00', 'Đang học'),
        # Course 3: Generative AI
        (courses[3][0], 'NV001', '2026-10-18 09:00', 'Đã đăng ký'),
        (courses[3][0], 'NV002', '2026-10-18 09:40', 'Đã đăng ký'),
        (courses[3][0], 'NV004', '2026-10-18 10:25', 'Đã đăng ký'),
        (courses[3][0], 'NV005', '2026-10-18 11:10', 'Đã đăng ký'),
        (courses[3][0], 'NV007', '2026-10-18 14:15', 'Đã đăng ký'),
        (courses[3][0], 'NV009', '2026-10-18 15:00', 'Đã đăng ký'),
        (courses[3][0], 'NV010', '2026-10-18 15:45', 'Đã đăng ký'),
        (courses[3][0], 'NV012', '2026-10-18 16:30', 'Đã đăng ký'),
        # Course 4: Kỹ năng thuyết trình
        (courses[4][0], 'NV002', '2026-10-19 09:30', 'Đã đăng ký'),
        (courses[4][0], 'NV004', '2026-10-19 10:15', 'Đã đăng ký'),
        (courses[4][0], 'NV007', '2026-10-19 11:00', 'Đã đăng ký'),
        (courses[4][0], 'NV013', '2026-10-19 14:30', 'Đã đăng ký'),
        # Course 5: Quản trị tài chính
        (courses[5][0], 'NV003', '2026-09-05 08:30', 'Hoàn thành'),
        (courses[5][0], 'NV006', '2026-09-05 09:15', 'Hoàn thành'),
        (courses[5][0], 'NV009', '2026-09-05 10:00', 'Hoàn thành'),
        (courses[5][0], 'NV007', '2026-09-05 14:00', 'Hoàn thành'),
        (courses[5][0], 'NV001', '2026-09-05 15:30', 'Hoàn thành'),
        # Course 6: Power BI
        (courses[6][0], 'NV003', '2026-10-20 09:10', 'Đã đăng ký'),
        (courses[6][0], 'NV004', '2026-10-20 10:00', 'Đã đăng ký'),
        (courses[6][0], 'NV009', '2026-10-20 11:30', 'Đã đăng ký'),
        (courses[6][0], 'NV010', '2026-10-20 14:15', 'Đã đăng ký'),
        (courses[6][0], 'NV002', '2026-10-20 16:00', 'Đã đăng ký'),
        # Course 7: Lãnh đạo cho Quản lý
        (courses[7][0], 'NV001', '2026-10-21 08:45', 'Đang học'),
        (courses[7][0], 'NV006', '2026-10-21 09:30', 'Đang học'),
        (courses[7][0], 'NV007', '2026-10-21 10:15', 'Đang học'),
        (courses[7][0], 'NV008', '2026-10-21 11:00', 'Đang học'),
    ]
    for ten_khoa, mnv_d, ng_d, tt_d in sample_dk:
        mkdt_d = kdt_map.get(ten_khoa)
        if mkdt_d:
            row = db.execute("SELECT 1 FROM DangKyDaoTao WHERE MaKDT = ? AND MaNV = ?", (mkdt_d, mnv_d)).fetchone()
            if not row:
                db.execute("""
                    INSERT INTO DangKyDaoTao(MaKDT, MaNV, NgayDangKy, TrangThai)
                    VALUES(?, ?, ?, ?)
                """, (mkdt_d, mnv_d, ng_d, tt_d))
    db.commit()

    # 11. Phân ca làm việc
    print("[11/13] Nạp Phân ca làm việc chi tiết (PhanCa)...")
    start_shift_date = date(2026, 11, 1)
    shift_dates_14 = [(start_shift_date + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(14)]
    if date.today().strftime('%Y-%m-%d') not in shift_dates_14:
        shift_dates_14.append(date.today().strftime('%Y-%m-%d'))

    for d_idx, d_str in enumerate(shift_dates_14):
        day_num = d_idx + 1

        # PB01 - Nhân sự
        shifts_for_day = [
            ('NV001', 'Ca hành chính (08:00 - 17:30)', 'Quản lý và điều hành nhân sự toàn công ty'),
            ('NV002', 'Ca hành chính (08:00 - 17:30)', 'Trực tiếp nhận hồ sơ, BHXH và hợp đồng lao động'),
            ('NV013', 'Ca hành chính (08:00 - 17:30)', 'Tổ chức phỏng vấn và tiếp đón ứng viên mới'),
            # PB02 - Kế toán
            ('NV006', 'Ca hành chính (08:00 - 17:30)', 'Phê duyệt chứng từ tài chính và dòng tiền'),
            ('NV003', 'Ca hành chính (08:00 - 17:30)', 'Đối soát hóa đơn và hạch toán sổ sách hàng ngày'),
            ('NV009', 'Ca hành chính (08:00 - 17:30)', 'Báo cáo thuế, tài sản cố định và chi phí vận hành'),
            # PB03 - Kinh doanh
            ('NV007', 'Ca hành chính (08:00 - 17:30)', 'Chỉ đạo kinh doanh và đàm phán hợp đồng lớn'),
            ('NV004', 'Ca sáng (06:00 - 14:00)' if day_num % 2 == 1 else 'Ca chiều (14:00 - 22:00)',
             'Trực tổng đài tư vấn khách hàng ca sáng' if day_num % 2 == 1 else 'Chăm sóc khách hàng VIP và chốt hợp đồng'),
            ('NV010', 'Ca chiều (14:00 - 22:00)' if day_num in (6, 7, 13, 14) else 'Ca hành chính (08:00 - 17:30)',
             'Quản lý sự kiện hội thảo trực tuyến cuối tuần' if day_num in (6, 7, 13, 14) else 'Vận hành chiến dịch truyền thông đa kênh'),
            # PB04 - Kỹ thuật
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

        for mnv_s, ca_s, gc_s in shifts_for_day:
            row = db.execute("SELECT 1 FROM PhanCa WHERE MaNV = ? AND Ngay = ?", (mnv_s, d_str)).fetchone()
            if not row:
                db.execute("""
                    INSERT INTO PhanCa(MaNV, Ngay, CaLam, GhiChu)
                    VALUES(?, ?, ?, ?)
                """, (mnv_s, d_str, ca_s, gc_s))
            else:
                db.execute("""
                    UPDATE PhanCa SET CaLam = ?, GhiChu = ? WHERE MaNV = ? AND Ngay = ?
                """, (ca_s, gc_s, mnv_s, d_str))
    db.commit()

    # 12. Tuyển dụng & Ứng viên
    print("[12/13] Nạp Yêu cầu tuyển dụng & Hồ sơ ứng viên...")
    recruit_reqs = [
        ('PB04', 'Kỹ sư Lập trình Backend (Python/Flask/SQL)', 2, 'Kinh nghiệm với Python, RESTful API, SQL Server/SQLite, Docker.', 'Mở rộng đội ngũ phát triển sản phẩm HRM thế hệ mới.', '2026-11-30', 'Đang tuyển'),
        ('PB03', 'Chuyên viên Kinh doanh B2B', 2, 'Giao tiếp tốt, có kinh nghiệm đàm phán giải pháp phần mềm doanh nghiệp.', 'Đẩy mạnh phát triển thị trường khách hàng doanh nghiệp.', '2026-11-25', 'Đang tuyển'),
        ('PB02', 'Kế toán viên Tổng hợp', 1, 'Tốt nghiệp Đại học chuyên ngành Kế toán, thành thạo MISA, nắm vững luật thuế.', 'Thay thế nhân sự nghỉ chế độ thai sản.', '2026-11-15', 'Đang tuyển'),
        ('PB01', 'Chuyên viên Tuyển dụng Nhân tài (HR Talent)', 1, 'Kinh nghiệm tuyển dụng IT/Tech, xây dựng thương hiệu nhà tuyển dụng.', 'Đáp ứng kế hoạch tuyển thêm nhân sự chất lượng cao.', '2026-12-10', 'Đang tuyển')
    ]
    for mpb, vt, sl, yc, ld, ht, tt in recruit_reqs:
        row = db.execute("SELECT 1 FROM YeuCauTuyenDung WHERE ViTri = ? AND MaPB = ?", (vt, mpb)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO YeuCauTuyenDung(MaPB, ViTri, SoLuong, YeuCau, LyDo, HanTuyen, TrangThai)
                VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (mpb, vt, sl, yc, ld, ht, tt))
    db.commit()

    yc_list = db.execute("SELECT MaYC, ViTri, MaPB FROM YeuCauTuyenDung").fetchall()
    candidates = [
        ('Nguyễn Hoàng Nam', 'nam.nh@gmail.com', '0912345678', 'Kỹ sư Lập trình Backend (Python/Flask/SQL)', 'PB04', '2026-11-05', 'Đỗ Hoàng Long', 'Trúng tuyển', 'Nắm vững kiến thức thuật toán và kiến trúc backend. Pass vòng phỏng vấn kỹ thuật.'),
        ('Trần Thảo Ly', 'ly.tt@gmail.com', '0923456789', 'Kỹ sư Lập trình Backend (Python/Flask/SQL)', 'PB04', '2026-11-06', 'Đỗ Hoàng Long', 'Chờ phỏng vấn', 'CV đẹp, từng làm dự án quản lý nhân sự. Đã gửi thư mời phỏng vấn vòng 2.'),
        ('Phạm Thùy Dương', 'duong.pt@gmail.com', '0945678901', 'Chuyên viên Kinh doanh B2B', 'PB03', '2026-11-07', 'Bùi Quang Huy', 'Trúng tuyển', 'Kỹ năng đàm phán rất xuất sắc, có sẵn tệp khách hàng doanh nghiệp sản xuất.'),
        ('Hoàng Mai Lan', 'lan.hm@gmail.com', '0967890123', 'Kế toán viên Tổng hợp', 'PB02', '2026-11-02', 'Vũ Thị Hoa', 'Trúng tuyển', 'Kinh nghiệm 4 năm kế toán tổng hợp, nắm chắc chính sách hóa đơn điện tử.'),
        ('Vũ Đình Mạnh', 'manh.vu@gmail.com', '0978901234', 'Chuyên viên Tuyển dụng Nhân tài (HR Talent)', 'PB01', '2026-11-09', 'Nguyễn Văn An', 'Chờ phỏng vấn', 'Có kinh nghiệm Headhunter, giao tiếp tiếng Anh lưu loát.')
    ]
    for hoten, em, sdt, vt, mpb, ngay_pv, npv, kq, nx in candidates:
        matching_yc = [y['MaYC'] for y in yc_list if y['ViTri'] == vt]
        myc = matching_yc[0] if matching_yc else None
        row = db.execute("SELECT 1 FROM UngVien WHERE HoTen = ? AND Email = ?", (hoten, em)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO UngVien(MaYC, HoTen, Email, SDT, ViTriUngTuyen, MaPB, NgayPV, NguoiPV, KetQua, NhanXet)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (myc, hoten, em, sdt, vt, mpb, ngay_pv, npv, kq, nx))
    db.commit()

    # 13. Thông báo nội bộ & chốt công
    print("[13/13] Nạp Thông báo nội bộ công ty (ThongBao)...")
    announcements = [
        ('Kế hoạch nghỉ lễ và kế hoạch công tác dịp Tết Dương Lịch 2027',
         'Ban Giám đốc thông báo toàn thể cán bộ nhân viên lịch nghỉ Tết Dương Lịch từ ngày 01/01/2027 đến hết ngày 03/01/2027. Bộ phận Kỹ thuật bố trí nhân sự trực online đảm bảo hệ thống vận hành liên tục 24/7.',
         '2026-10-25', 'Ban Giám Đốc', 'Toàn công ty', None),
        ('Quy định rà soát hồ sơ nhân sự và hoàn thiện chứng chỉ chuyên môn',
         'Yêu cầu toàn thể nhân sự cập nhật thông tin cá nhân, ảnh đại diện và hồ sơ văn bằng chứng chỉ mới nhất lên cổng thông tin cá nhân /me.',
         '2026-10-20', 'Phòng Nhân sự', 'Toàn công ty', None),
        ('Thông báo về lịch làm việc và đăng ký nghỉ phép trực tuyến',
         'Đề nghị cán bộ nhân viên thực hiện đúng quy định nộp đơn xin nghỉ phép, giải trình công và đăng ký tăng ca trực tuyến trên hệ thống quản lý nhân sự.',
         '2026-10-15', 'Phòng Nhân sự', 'Toàn công ty', None),
        ('Kế hoạch đánh giá hiệu suất công việc KPI định kỳ tháng',
         'Thông báo tới các nhân sự thuộc phòng ban về việc hoàn thành tự đánh giá KPI tháng đúng thời hạn quy định trên cổng thông tin.',
         '2026-10-10', 'Trưởng phòng Nhân sự', 'Theo phòng ban', 'PB01')
    ]
    for td, nd, ng, nguoi, pv, mpb in announcements:
        row = db.execute("SELECT 1 FROM ThongBao WHERE TieuDe = ?", (td,)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO ThongBao(TieuDe, NoiDung, NgayGui, NguoiGui, PhamVi, MaPB)
                VALUES(?, ?, ?, ?, ?, ?)
            """, (td, nd, ng, nguoi, pv, mpb))

    row_cc = db.execute("SELECT 1 FROM ChotCong WHERE ThangNam = '2026-09'").fetchone()
    if not row_cc:
        db.execute("""
            INSERT INTO ChotCong(ThangNam, NgayChot, NguoiChot)
            VALUES('2026-09', '2026-10-01 17:00:00', N'Admin Quản Trị')
        """)
    db.commit()
    print("=======================================================")
    print("🎉 HOÀN THÀNH NẠP ĐẦY ĐỦ TOÀN BỘ NGHIỆP VỤ HỆ THỐNG!")
    print("=======================================================")

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
                    VALUES(?, ?, '08:00', '17:30', N'Đúng giờ', N'Chấm công máy vân tay')
                """, (mnv, today_str))

        # 7. Tài khoản đăng nhập (TaiKhoan)
        accounts = [
            ('admin', 'admin123', None, AD),
            ('nv001', '123456', 'NV001', QL),
            ('ql001', '123456', 'NV001', QL),
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

        print(f"-> Đã đảm bảo 13 hồ sơ nhân viên, 13 hợp đồng, bảng lương, chấm công và 15 tài khoản truy cập!")

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

        # Clean duplicates
        clean_all_duplicates(db)
        db.commit()

        # 9. Tự động nạp toàn bộ các giao dịch nghiệp vụ chi tiết
        seed_transaction_records(db)

        # 10. Báo cáo tổng kết
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
