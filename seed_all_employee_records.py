# -*- coding: utf-8 -*-
"""
Kịch bản nạp toàn diện dữ liệu nghiệp vụ cho 13 nhân sự (NV001 - NV013) thuộc 4 phòng ban chuẩn:
- PB01: Phòng Nhân sự
- PB02: Phòng Kế toán
- PB03: Phòng Kinh doanh
- PB04: Phòng Kỹ thuật

Bao gồm đầy đủ các phân hệ chức năng:
1. Chấm công (ChamCong) chi tiết tháng 10/2026
2. Đơn xin nghỉ phép (NghiPhep) đa dạng trạng thái
3. Đăng ký làm thêm giờ / Tăng ca (TangCa)
4. Đơn tạm ứng tiền lương (TamUng)
5. Đơn giải trình công (GiaiTrinhCong)
6. Đánh giá hiệu suất KPI (DanhGia) 2 tháng
7. Bằng cấp, chứng chỉ, giấy tờ (TaiLieuNhanVien)
8. Đề xuất & Khiếu nại (DeXuatKhieuNai)
9. Đề xuất nhân sự (DeXuatNhanSu) từ quản lý các phòng gửi Admin
10. Yêu cầu tuyển dụng (YeuCauTuyenDung) & Hồ sơ ứng viên (UngVien)
11. Thông báo nội bộ toàn công ty & phòng ban (ThongBao)
12. Chốt công tháng (ChotCong)

Đã loại bỏ hoàn toàn Khóa đào tạo (KhoaDaoTao) và Phân ca làm việc (PhanCa).
Hỗ trợ tương thích đồng thời cả SQLite và MS SQL Server.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ss'))
from app import create_app
from database import get_db

def run_seed():
    app = create_app()
    with app.app_context():
        db = get_db()
        print("=== BẮT ĐẦU NẠP DỮ LIỆU NGHIỆP VỤ CHO CÁC PHÒNG BAN ===")

        # Lấy danh sách nhân viên hiện có trong CSDL
        employees = db.execute("SELECT MaNV, HoTen, GioiTinh, TrinhDo, ChuyenMon, MaCV FROM NhanVien ORDER BY MaNV").fetchall()
        print(f"-> Đã tải {len(employees)} nhân sự từ CSDL.")

        # -------------------------------------------------------------
        # 1. BẢNG CHẤM CÔNG (ChamCong) - Nạp chi tiết tháng 10/2026
        # -------------------------------------------------------------
        print("\n[1/11] Nạp dữ liệu Chấm công (ChamCong) chi tiết tháng 10/2026...")
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
        total_cc = db.execute("SELECT COUNT(*) FROM ChamCong").fetchone()[0]
        print(f"-> Tổng số bản ghi Chấm công: {total_cc}")

        # -------------------------------------------------------------
        # 2. ĐƠN NGHỈ PHÉP (NghiPhep)
        # -------------------------------------------------------------
        print("\n[2/11] Nạp dữ liệu Đơn nghỉ phép (NghiPhep)...")
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
                db.execute(
                    "INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, TrangThai, LyDo) VALUES(?, ?, ?, ?, ?)",
                    (mnv_l, nbd, nkt, tt_l, ld_l)
                )

        db.commit()
        total_np = db.execute("SELECT COUNT(*) FROM NghiPhep").fetchone()[0]
        print(f"-> Tổng số bản ghi Đơn nghỉ phép: {total_np}")

        # -------------------------------------------------------------
        # 3. ĐĂNG KÝ TĂNG CA / LÀM THÊM GIỜ (TangCa)
        # -------------------------------------------------------------
        print("\n[3/11] Nạp dữ liệu Tăng ca (TangCa)...")
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
                db.execute(
                    "INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai, TrangThai, LyDo, NguoiDuyet) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (mnv_o, sg, n_ot, loai_ot, tt_o, ld_o, ng_o)
                )

        db.commit()
        total_tc = db.execute("SELECT COUNT(*) FROM TangCa").fetchone()[0]
        print(f"-> Tổng số bản ghi Tăng ca: {total_tc}")

        # -------------------------------------------------------------
        # 4. TẠM ỨNG TIỀN LƯƠNG (TamUng)
        # -------------------------------------------------------------
        print("\n[4/11] Nạp dữ liệu Tạm ứng lương (TamUng)...")
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
                db.execute(
                    "INSERT INTO TamUng(MaNV, ThangNam, SoTien, LyDo, NgayYeuCau, TrangThai, NguoiDuyet) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (mnv_u, t_u, st_u, ld_u, ny_u, tt_u, nd_u)
                )

        db.commit()
        total_tu = db.execute("SELECT COUNT(*) FROM TamUng").fetchone()[0]
        print(f"-> Tổng số bản ghi Tạm ứng lương: {total_tu}")

        # -------------------------------------------------------------
        # 5. GIẢI TRÌNH CÔNG (GiaiTrinhCong)
        # -------------------------------------------------------------
        print("\n[5/11] Nạp dữ liệu Giải trình công (GiaiTrinhCong)...")
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
        total_gt = db.execute("SELECT COUNT(*) FROM GiaiTrinhCong").fetchone()[0]
        print(f"-> Tổng số bản ghi Giải trình công: {total_gt}")

        # -------------------------------------------------------------
        # 6. ĐÁNH GIÁ HIỆU SUẤT KPI (DanhGia)
        # -------------------------------------------------------------
        print("\n[6/11] Nạp dữ liệu Đánh giá KPI (DanhGia)...")
        kpi_evals = [
            ('NV001', '2026-10', 95.0, 'Xuất sắc', 'Lãnh đạo xuất sắc hoàn thành kế hoạch nhân sự toàn công ty.', 'Ban Giám Đốc', 95.0, 'Đạt 100% KPI phòng.'),
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
        total_dg = db.execute("SELECT COUNT(*) FROM DanhGia").fetchone()[0]
        print(f"-> Tổng số bản ghi Đánh giá KPI: {total_dg}")

        # -------------------------------------------------------------
        # 7. BẰNG CẤP, CHỨNG CHỈ (TaiLieuNhanVien)
        # -------------------------------------------------------------
        print("\n[7/11] Nạp Bằng cấp, Chứng chỉ (TaiLieuNhanVien)...")
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
        total_tl = db.execute("SELECT COUNT(*) FROM TaiLieuNhanVien").fetchone()[0]
        print(f"-> Tổng số bản ghi Bằng cấp, Chứng chỉ: {total_tl}")

        # -------------------------------------------------------------
        # 8. ĐỀ XUẤT & Ý KIẾN KHIẾU NẠI (DeXuatKhieuNai)
        # -------------------------------------------------------------
        print("\n[8/11] Nạp Đề xuất & Khiếu nại (DeXuatKhieuNai)...")
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
        total_dx = db.execute("SELECT COUNT(*) FROM DeXuatKhieuNai").fetchone()[0]
        print(f"-> Tổng số bản ghi Đề xuất & Khiếu nại: {total_dx}")

        # -------------------------------------------------------------
        # 9. ĐỀ XUẤT NHÂN SỰ TỪ QUẢN LÝ (DeXuatNhanSu)
        # -------------------------------------------------------------
        print("\n[9/11] Nạp Đề xuất nhân sự từ Quản lý gửi Admin (DeXuatNhanSu)...")
        proposals = [
            ('NV008', 'NV005', 'Tăng lương', 'Tăng mức lương lên 25.000.000đ', 'Đảm nhiệm vai trò Fullstack Lead kiến trúc hệ thống ổn định cao', 'Đã duyệt', 'Đã phê duyệt điều chỉnh hợp đồng lao động mới.'),
            ('NV007', 'NV004', 'Khen thưởng', 'Thưởng nóng 5.000.000đ', 'Dẫn dắt chiến dịch ra mắt dịch vụ mới đạt 140% KPI doanh số', 'Đã duyệt', 'Khen thưởng và tuyên dương toàn công ty.'),
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
        total_dxns = db.execute("SELECT COUNT(*) FROM DeXuatNhanSu").fetchone()[0]
        print(f"-> Tổng số Đề xuất Nhân sự: {total_dxns}")

        # -------------------------------------------------------------
        # 10. TUYỂN DỤNG & ỨNG VIÊN (YeuCauTuyenDung & UngVien)
        # -------------------------------------------------------------
        print("\n[10/11] Nạp Yêu cầu tuyển dụng & Hồ sơ ứng viên...")
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
        total_yc = db.execute("SELECT COUNT(*) FROM YeuCauTuyenDung").fetchone()[0]
        total_uv = db.execute("SELECT COUNT(*) FROM UngVien").fetchone()[0]
        print(f"-> Tổng số Yêu cầu tuyển dụng: {total_yc}, Tổng số Ứng viên: {total_uv}")

        # -------------------------------------------------------------
        # 11. THÔNG BÁO NỘI BỘ (ThongBao)
        # -------------------------------------------------------------
        print("\n[11/11] Nạp Thông báo nội bộ công ty (ThongBao)...")
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

        # Chốt công tháng cũ
        row_cc = db.execute("SELECT 1 FROM ChotCong WHERE ThangNam = '2026-09'").fetchone()
        if not row_cc:
            db.execute("""
                INSERT INTO ChotCong(ThangNam, NgayChot, NguoiChot)
                VALUES('2026-09', '2026-10-01 17:00:00', N'Admin Quản Trị')
            """)

        db.commit()
        total_tb = db.execute("SELECT COUNT(*) FROM ThongBao").fetchone()[0]
        print(f"-> Tổng số Thông báo: {total_tb}")

        print("\n=======================================================")
        print("🎉 HOÀN THÀNH NẠP DỮ LIỆU ĐỒNG BỘ CHO TOÀN BỘ CHỨC NĂNG!")
        print("=======================================================")

if __name__ == '__main__':
    run_seed()
