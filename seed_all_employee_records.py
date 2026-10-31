"""
Kịch bản nạp toàn diện dữ liệu nghiệp vụ cho 50 nhân viên (NV001 - NV050)
Bao gồm đầy đủ các phân hệ chức năng:
1. Chấm công (ChamCong) chi tiết toàn bộ các ngày làm việc tháng 10/2026 (~1.000 bản ghi)
2. Đơn xin nghỉ phép (NghiPhep) đa dạng trạng thái và lý do
3. Đăng ký làm thêm giờ / Tăng ca (TangCa)
4. Đơn tạm ứng tiền lương (TamUng)
5. Đơn giải trình công (GiaiTrinhCong)
6. Đánh giá hiệu suất KPI (DanhGia) 2 tháng cho toàn bộ 50 nhân viên
7. Bằng cấp, chứng chỉ, giấy tờ (TaiLieuNhanVien) cho toàn bộ 50 nhân viên (~100 bản ghi)
8. Khóa đào tạo (KhoaDaoTao) và Đăng ký tham gia (DangKyDaoTao)
9. Khen thưởng và kỷ luật (KhenThuongKyLuat)
10. Đề xuất & Khiếu nại (DeXuatKhieuNai)
11. Phân ca làm việc (PhanCa) cho toàn bộ 50 nhân viên
12. Đề xuất nhân sự (DeXuatNhanSu) từ quản lý gửi admin
13. Yêu cầu tuyển dụng (YeuCauTuyenDung) & Hồ sơ ứng viên (UngVien)
14. Thông báo nội bộ toàn công ty & phòng ban (ThongBao)
15. Chốt công tháng (ChotCong)
"""
import sys
import random
from datetime import date, datetime
sys.path.insert(0, 'ss')
from app import app
from database import get_db

def run_seed():
    with app.app_context():
        db = get_db()
        print("=== BẮT ĐẦU NẠP DỮ LIỆU ĐẦY ĐỦ 50 NHÂN VIÊN CHO MỌI CHỨC NĂNG ===")

        # Lấy danh sách 50 nhân viên hiện có
        employees = db.execute("SELECT MaNV, HoTen, GioiTinh, TrinhDo, ChuyenMon, MaCV FROM NhanVien ORDER BY MaNV").fetchall()
        print(f"-> Đã tải {len(employees)} nhân viên từ CSDL.")

        departments = db.execute("SELECT MaPB, TenPB FROM PhongBan").fetchall()
        dept_map = {p['MaPB']: p['TenPB'] for p in departments}

        # -------------------------------------------------------------
        # 1. BẢNG CHẤM CÔNG (ChamCong) - Nạp chi tiết tháng 10/2026
        # -------------------------------------------------------------
        print("\n[1/13] Nạp dữ liệu Chấm công (ChamCong) chi tiết tháng 10/2026...")
        # Các ngày làm việc (Thứ 2 đến Thứ 6) trong tháng 10/2026
        work_days = [
            '2026-10-01', '2026-10-02', '2026-10-05', '2026-10-06', '2026-10-07',
            '2026-10-08', '2026-10-09', '2026-10-12', '2026-10-13', '2026-10-14',
            '2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21',
            '2026-10-22', '2026-10-23', '2026-10-26', '2026-10-27', '2026-10-28',
            '2026-10-29', '2026-10-30'
        ]

        cc_inserted = 0
        for emp in employees:
            mnv = emp['MaNV']
            emp_seed = int(mnv[2:])
            for idx, d_str in enumerate(work_days):
                # Pseudo-deterministic randomization based on employee id & day index
                hash_val = (emp_seed * 37 + idx * 19) % 100

                if hash_val < 86:
                    # Đúng giờ
                    m_in = 45 + (hash_val % 14)
                    gio_vao = f"07:{m_in:02d}"
                    gio_ra = f"17:{30 + (hash_val % 16):02d}"
                    trang_thai = 'Đúng giờ'
                    ghi_chu = 'Chấm công máy vân tay'
                elif hash_val < 94:
                    # Đi muộn
                    m_in = 10 + (hash_val % 25)
                    gio_vao = f"08:{m_in:02d}"
                    gio_ra = '17:35'
                    trang_thai = 'Đi muộn'
                    ghi_chu = 'Ùn tắc giao thông tuyến đường chính'
                else:
                    # Về sớm hoặc nghỉ phép
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

                db.execute("""
                    IF NOT EXISTS (SELECT 1 FROM ChamCong WHERE MaNV = ? AND Ngay = ?)
                        INSERT INTO ChamCong(MaNV, Ngay, GioVao, GioRa, TrangThai, GhiChu)
                        VALUES(?, ?, ?, ?, ?, ?)
                """, (mnv, d_str, mnv, d_str, gio_vao, gio_ra, trang_thai, ghi_chu))
                cc_inserted += 1

        db.commit()
        total_cc = db.execute("SELECT COUNT(*) FROM ChamCong").fetchone()[0]
        print(f"-> Tổng số bản ghi Chấm công hiện tại: {total_cc}")

        # -------------------------------------------------------------
        # 2. ĐƠN NGHỈ PHÉP (NghiPhep)
        # -------------------------------------------------------------
        print("\n[2/13] Nạp dữ liệu Đơn nghỉ phép (NghiPhep)...")
        leave_reasons = [
            ('Nghỉ phép năm thường niên', 'Đã duyệt'),
            ('Nghỉ ốm điều trị tại bệnh viện có giấy khám', 'Đã duyệt'),
            ('Nghỉ việc gia đình có tang lễ', 'Đã duyệt'),
            ('Nghỉ chuẩn bị đám cưới', 'Đã duyệt'),
            ('Nghỉ phép đưa người thân đi khám sức khỏe', 'Đã duyệt'),
            ('Nghỉ phép giải quyết thủ tục nhà đất', 'Chờ duyệt'),
            ('Nghỉ cá nhân đi du lịch', 'Chờ duyệt'),
            ('Nghỉ phép vào đợt cao điểm dự án', 'Từ chối'),
            ('Nghỉ phép năm thăm quê', 'Đã duyệt'),
            ('Nghỉ chăm con ốm', 'Đã duyệt')
        ]

        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            if mnv == 'NV002':
                continue # Giữ nguyên cho test case 10-12
            
            # Mỗi nhân viên có 1 đơn trong quá khứ hoặc tương lai
            reason_idx = (int(mnv[2:]) + i) % len(leave_reasons)
            ly_do, trang_thai = leave_reasons[reason_idx]
            d_start = f"2026-10-{(10 + (i % 15)):02d}"
            d_end = f"2026-10-{(11 + (i % 15)):02d}"

            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM NghiPhep WHERE MaNV = ? AND NgayBD = ?)
                    INSERT INTO NghiPhep(MaNV, NgayBD, NgayKT, TrangThai, LyDo)
                    VALUES(?, ?, ?, ?, ?)
            """, (mnv, d_start, mnv, d_start, d_end, trang_thai, ly_do))

        db.commit()
        total_np = db.execute("SELECT COUNT(*) FROM NghiPhep").fetchone()[0]
        print(f"-> Tổng số bản ghi Đơn nghỉ phép: {total_np}")

        # -------------------------------------------------------------
        # 3. LÀM THÊM GIỜ / TĂNG CA (TangCa)
        # -------------------------------------------------------------
        print("\n[3/13] Nạp dữ liệu Làm thêm giờ (TangCa)...")
        ot_reasons = [
            ('Deploy bản phát hành phần mềm lên server chính', 3.0, 'Ngày thường', 'Đã duyệt'),
            ('Hỗ trợ khách hàng trong chiến dịch Flash Sale ban đêm', 4.0, 'Ngày thường', 'Đã duyệt'),
            ('Quyết toán báo cáo tài chính quý cho ban kiểm toán', 3.5, 'Cuối tuần', 'Đã duyệt'),
            ('Khắc phục sự cố mạng và bảo trì hạ tầng cáp quang', 4.0, 'Cuối tuần', 'Đã duyệt'),
            ('Nhập liệu hồ sơ tuyển dụng nhân sự mới cho các chi nhánh', 2.5, 'Ngày thường', 'Đã duyệt'),
            ('Hoàn thiện tài liệu nghiệm thu dự án theo yêu cầu đối tác', 3.0, 'Ngày thường', 'Chờ duyệt'),
            ('Trực hotline kỹ thuật 24/7 phiên cuối tuần', 5.0, 'Cuối tuần', 'Chờ duyệt'),
            ('Kiểm thử tải hệ thống ERP trước giờ mở bán', 3.5, 'Ngày thường', 'Đã duyệt')
        ]

        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            if mnv == 'NV005':
                continue # Tránh đụng kịch bản test 31

            if i % 2 == 0: # Nửa số nhân viên có bản ghi tăng ca
                ot_item = ot_reasons[(int(mnv[2:]) + i) % len(ot_reasons)]
                d_ot = f"2026-10-{(1 + (i % 28)):02d}"
                db.execute("""
                    IF NOT EXISTS (SELECT 1 FROM TangCa WHERE MaNV = ? AND Ngay = ?)
                        INSERT INTO TangCa(MaNV, SoGio, Ngay, Loai, TrangThai, LyDo, NguoiDuyet)
                        VALUES(?, ?, ?, ?, ?, ?, N'Trưởng phòng duyệt')
                """, (mnv, d_ot, mnv, ot_item[1], d_ot, ot_item[2], ot_item[3], ot_item[0]))

        db.commit()
        total_tc = db.execute("SELECT COUNT(*) FROM TangCa").fetchone()[0]
        print(f"-> Tổng số bản ghi Làm thêm giờ (OT): {total_tc}")

        # -------------------------------------------------------------
        # 4. TẠM ỨNG TIỀN LƯƠNG (TamUng)
        # -------------------------------------------------------------
        print("\n[4/13] Nạp dữ liệu Tạm ứng lương (TamUng)...")
        tu_reasons = [
            ('Chi trả viện phí cho người thân nằm viện đột xuất', 3000000, 'Đã duyệt'),
            ('Đóng học phí cho con đầu năm học mới', 4000000, 'Đã duyệt'),
            ('Sửa chữa phương tiện đi lại phục vụ công việc', 2000000, 'Đã duyệt'),
            ('Giải quyết chi phí sinh hoạt phát sinh trong tháng', 2500000, 'Chờ duyệt'),
            ('Đóng tiền thuê nhà trọ theo kỳ 6 tháng', 5000000, 'Đã duyệt'),
            ('Chi phí mua sắm thiết bị cá nhân phục vụ làm việc tại nhà', 2000000, 'Chờ duyệt')
        ]

        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            if mnv == 'NV005':
                continue
            if i % 3 == 0: # 1/3 nhân sự có đơn tạm ứng
                tu_item = tu_reasons[(int(mnv[2:]) + i) % len(tu_reasons)]
                db.execute("""
                    IF NOT EXISTS (SELECT 1 FROM TamUng WHERE MaNV = ? AND ThangNam = '2026-10')
                        INSERT INTO TamUng(MaNV, ThangNam, SoTien, LyDo, NgayYeuCau, TrangThai, NguoiDuyet)
                        VALUES(?, '2026-10', ?, ?, '2026-10-15', ?, N'Kế toán trưởng duyệt')
                """, (mnv, mnv, tu_item[1], tu_item[0], tu_item[2]))

        db.commit()
        total_tu = db.execute("SELECT COUNT(*) FROM TamUng").fetchone()[0]
        print(f"-> Tổng số bản ghi Tạm ứng lương: {total_tu}")

        # -------------------------------------------------------------
        # 5. GIẢI TRÌNH CÔNG (GiaiTrinhCong)
        # -------------------------------------------------------------
        print("\n[5/13] Nạp dữ liệu Giải trình công (GiaiTrinhCong)...")
        gt_reasons = [
            ('Quên quẹt thẻ do vội vào họp giao ban ban giám đốc', 'Đã duyệt'),
            ('Đi công tác gặp đối tác khách hàng từ sáng sớm', 'Đã duyệt'),
            ('Máy chấm công vân tay không nhận cảm biến quang học', 'Đã duyệt'),
            ('Mất điện cục bộ tại sảnh quẹt thẻ lúc 8h sáng', 'Đã duyệt'),
            ('Ùn tắc giao thông nghiêm trọng do cây đổ sau mưa lớn', 'Đã duyệt'),
            ('Tham gia hỗ trợ sự kiện xúc tiến thương mại ngoài công ty', 'Chờ duyệt'),
            ('Thẻ nhân viên bị gãy chưa kịp cấp lại thẻ mới', 'Chờ duyệt')
        ]

        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            if mnv == 'NV005':
                continue
            if i % 3 == 1:
                gt_item = gt_reasons[(int(mnv[2:]) + i) % len(gt_reasons)]
                d_gt = f"2026-10-{(5 + (i % 20)):02d}"
                db.execute("""
                    IF NOT EXISTS (SELECT 1 FROM GiaiTrinhCong WHERE MaNV = ? AND Ngay = ?)
                        INSERT INTO GiaiTrinhCong(MaNV, Ngay, GioVaoDeXuat, GioRaDeXuat, LyDo, TrangThai, NguoiDuyet, NgayGui, PhanHoi)
                        VALUES(?, ?, '08:00', '17:30', ?, ?, N'Trưởng phòng duyệt', '2026-10-21', N'Đã xác minh và đồng ý điều chỉnh công')
                """, (mnv, d_gt, mnv, d_gt, gt_item[0], gt_item[1]))

        db.commit()
        total_gt = db.execute("SELECT COUNT(*) FROM GiaiTrinhCong").fetchone()[0]
        print(f"-> Tổng số bản ghi Giải trình công: {total_gt}")

        # -------------------------------------------------------------
        # 6. ĐÁNH GIÁ HIỆU SUẤT KPI (DanhGia) - Đủ 50 nhân viên
        # -------------------------------------------------------------
        print("\n[6/13] Nạp dữ liệu Đánh giá KPI (DanhGia) 2 tháng cho 50 nhân viên...")
        months = ['2026-10', '2026-09']
        for emp in employees:
            mnv = emp['MaNV']
            emp_num = int(mnv[2:])
            for m_str in months:
                # Random score depending on employee & month
                base_score = 75 + ((emp_num * 17 + (1 if m_str == '2026-10' else 2)) % 24)
                if base_score >= 90:
                    xep_loai = 'Xuất sắc'
                    nx = 'Hoàn thành vượt mức các mục tiêu trọng tâm; tinh thần trách nhiệm và tính chủ động rất cao.'
                    self_nx = 'Tôi đã nỗ lực hoàn thành tất cả task đúng tiến độ và không có sai sót phát sinh.'
                elif base_score >= 80:
                    xep_loai = 'Tốt'
                    nx = 'Hoàn thành tốt nhiệm vụ được giao; phối hợp nhóm hiệu quả và hòa đồng.'
                    self_nx = 'Hoàn thành chỉ tiêu được giao đúng hẹn, tích cực hỗ trợ đồng nghiệp trong nhóm.'
                else:
                    xep_loai = 'Khá'
                    nx = 'Cơ bản đáp ứng yêu cầu công việc, cần nâng cao tốc độ phản hồi và tính chủ động hơn.'
                    self_nx = 'Cần rèn luyện thêm kỹ năng quản lý thời gian và nâng cao năng suất xử lý task.'

                self_score = min(100.0, base_score + 2.0)

                db.execute("""
                    IF NOT EXISTS (SELECT 1 FROM DanhGia WHERE MaNV = ? AND ThangNam = ?)
                        INSERT INTO DanhGia(MaNV, ThangNam, DiemKPI, XepLoai, NhanXet, NguoiDanhGia, DiemTuDanhGia, NhanXetCaNhan)
                        VALUES(?, ?, ?, ?, ?, N'Hội đồng Đánh giá', ?, ?)
                    ELSE
                        UPDATE DanhGia SET DiemKPI = ?, XepLoai = ?, NhanXet = ?, DiemTuDanhGia = ?, NhanXetCaNhan = ?
                        WHERE MaNV = ? AND ThangNam = ?
                """, (
                    mnv, m_str, mnv, m_str, float(base_score), xep_loai, nx, float(self_score), self_nx,
                    float(base_score), xep_loai, nx, float(self_score), self_nx, mnv, m_str
                ))

        db.commit()
        total_dg = db.execute("SELECT COUNT(*) FROM DanhGia").fetchone()[0]
        print(f"-> Tổng số bản ghi Đánh giá KPI: {total_dg}")

        # -------------------------------------------------------------
        # 7. BẰNG CẤP, CHỨNG CHỈ (TaiLieuNhanVien) - Đủ 50 nhân viên
        # -------------------------------------------------------------
        print("\n[7/13] Nạp Bằng cấp, Chứng chỉ (TaiLieuNhanVien) cho 50 nhân viên...")
        uni_list = [
            'Đại học Bách Khoa Hà Nội', 'Đại học Kinh Tế Quốc Dân', 'Đại học Ngoại Thương',
            'Đại học Công Nghiệp Hà Nội', 'Đại học Quốc Gia Hà Nội', 'Học viện Công nghệ Bưu chính Viễn thông',
            'Học viện Tài Chính', 'Đại học Thương Mại', 'Đại học Giao Thông Vận Tải'
        ]
        cert_list = [
            ('Chứng chỉ Tiếng Anh TOEIC 850', 'Chứng chỉ ngoại ngữ', 'Viện Khảo thí Giáo dục Hoa Kỳ (ETS)'),
            ('Chứng chỉ Tiếng Anh IELTS 7.5', 'Chứng chỉ ngoại ngữ', 'Hội đồng Anh (British Council)'),
            ('Chứng chỉ AWS Certified Solutions Architect', 'Chứng chỉ chuyên môn', 'Amazon Web Services'),
            ('Chứng chỉ Quản lý Dự án Chuyên nghiệp PMP', 'Chứng chỉ chuyên môn', 'Project Management Institute (PMI)'),
            ('Chứng chỉ Kế toán viên Công chứng CPA', 'Chứng chỉ chuyên môn', 'Bộ Tài Chính Việt Nam'),
            ('Chứng chỉ Chuyên viên Phân tích Dữ liệu Google Data Analytics', 'Chứng chỉ chuyên môn', 'Google Cloud'),
            ('Chứng chỉ Agile Certified Practitioner (PMI-ACP)', 'Chứng chỉ chuyên môn', 'PMI Global'),
            ('Chứng chỉ An toàn Thông tin Doanh nghiệp CompTIA Security+', 'Chứng chỉ chuyên môn', 'CompTIA')
        ]

        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            emp_num = int(mnv[2:])
            trinh_do = emp['TrinhDo'] or 'Đại học'
            chuyen_mon = emp['ChuyenMon'] or 'Quản trị'

            # 1. Bằng tốt nghiệp đại học / thạc sĩ
            uni = uni_list[emp_num % len(uni_list)]
            bang_ten = f"Bằng {trinh_do} ngành {chuyen_mon}"
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM TaiLieuNhanVien WHERE MaNV = ? AND Loai = N'Bằng tốt nghiệp')
                    INSERT INTO TaiLieuNhanVien(MaNV, TenTaiLieu, Loai, NgayCap, NoiCap, TepDinhKem, NgayTai, GhiChu)
                    VALUES(?, ?, N'Bằng tốt nghiệp', '2018-06-25', ?, '', '2026-01-10', N'Xếp loại: Giỏi. Đã đối soát hồ sơ gốc.')
            """, (mnv, mnv, bang_ten, uni))

            # 2. Chứng chỉ chuyên môn hoặc ngoại ngữ
            cert = cert_list[emp_num % len(cert_list)]
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM TaiLieuNhanVien WHERE MaNV = ? AND TenTaiLieu = ?)
                    INSERT INTO TaiLieuNhanVien(MaNV, TenTaiLieu, Loai, NgayCap, NoiCap, TepDinhKem, NgayTai, GhiChu)
                    VALUES(?, ?, ?, '2023-04-18', ?, '', '2026-02-15', N'Chứng chỉ quốc tế còn hiệu lực.')
            """, (mnv, cert[0], mnv, cert[0], cert[1], cert[2]))

        db.commit()
        total_tl = db.execute("SELECT COUNT(*) FROM TaiLieuNhanVien").fetchone()[0]
        print(f"-> Tổng số bản ghi Bằng cấp, Chứng chỉ: {total_tl}")

        # -------------------------------------------------------------
        # 8. KHÓA ĐÀO TẠO & ĐĂNG KÝ (KhoaDaoTao & DangKyDaoTao)
        # -------------------------------------------------------------
        print("\n[8/13] Nạp Khóa đào tạo và Đăng ký tham gia...")
        courses = [
            (1, 'An toàn thông tin & Bảo mật dữ liệu doanh nghiệp (ISO 27001)', 'TS. Nguyễn Văn Hưng', 'Thứ 7 hàng tuần (8h00 - 11h30)', 'Hội trường Tầng 5 - Trụ sở chính', 50, 'Trang bị kiến thức phòng vệ mã độc, lừa đảo phishing và bảo vệ dữ liệu nhạy cảm của khách hàng.', 'Đang diễn ra'),
            (2, 'Kỹ năng giao tiếp, lắng nghe và đàm phán trong công sở', 'ThS. Lê Hoàng Yến', '18h30 - 20h30 (Thứ 3 & Thứ 5)', 'Phòng Đào tạo A201', 40, 'Nâng cao năng lực kết nối đội ngũ, giải quyết xung đột tích cực và thuyết phục đối tác.', 'Sắp diễn ra'),
            (3, 'Quản trị dự án theo phương pháp Agile & Scrum thực chiến', 'Chuyên gia Scrum Trần Quốc Toản', 'Cả ngày Chủ nhật (09h00 - 17h00)', 'Trung tâm Hội thảo Innovation Hub', 35, 'Ứng dụng Jira, Sprint Planning, Daily Scrum vào quy trình phát triển sản phẩm công nghệ.', 'Đang diễn ra'),
            (4, 'Ứng dụng Trí tuệ Nhân tạo (Generative AI) nâng cao hiệu suất làm việc', 'Kỹ sư AI Phan Thanh Hải', 'Thứ 6 (14h00 - 17h00)', 'Phòng Lab Công nghệ Tầng 4', 45, 'Khai thác ChatGPT, Claude và công cụ AI hỗ trợ viết báo cáo, lập trình và sáng tạo nội dung.', 'Sắp diễn ra'),
            (5, 'Kỹ năng thuyết trình chuyên nghiệp và làm chủ cuộc họp', 'ThS. Đoàn Minh Tâm', 'Thứ 7 (13h30 - 17h00)', 'Hội trường Tầng 5', 40, 'Kỹ thuật diễn đạt gãy gọn, thiết kế slide ấn tượng và điều phối tương tác trong cuộc họp cấp cao.', 'Sắp diễn ra'),
            (6, 'Quản trị tài chính cá nhân & Lập kế hoạch ngân sách phòng ban', 'CPA Phạm Minh Tú', 'Chủ nhật (08h30 - 11h30)', 'Phòng Hội nghị B302', 30, 'Kiểm soát dòng tiền, tối ưu hóa chi phí vận hành và lập báo cáo tài chính hiệu quả.', 'Đã kết thúc')
        ]

        for cid, ten, gv, tg, dd, sl, mt, tt in courses:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM KhoaDaoTao WHERE TenKhoa = ?)
                    INSERT INTO KhoaDaoTao(TenKhoa, GiangVien, ThoiGian, DiaDiem, SoLuong, MoTa, TrangThai)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (ten, ten, gv, tg, dd, sl, mt, tt))
        db.commit()

        # Đăng ký cho nhân viên vào các khóa
        kdt_rows = db.execute("SELECT MaKDT FROM KhoaDaoTao").fetchall()
        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            emp_num = int(mnv[2:])
            target_kdt = kdt_rows[emp_num % len(kdt_rows)]['MaKDT']
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM DangKyDaoTao WHERE MaKDT = ? AND MaNV = ?)
                    INSERT INTO DangKyDaoTao(MaKDT, MaNV, NgayDangKy, TrangThai)
                    VALUES(?, ?, '2026-10-10', N'Đã đăng ký')
            """, (target_kdt, mnv, target_kdt, mnv))

        db.commit()
        total_kdt = db.execute("SELECT COUNT(*) FROM KhoaDaoTao").fetchone()[0]
        total_dk = db.execute("SELECT COUNT(*) FROM DangKyDaoTao").fetchone()[0]
        print(f"-> Tổng số Khóa đào tạo: {total_kdt}, Tổng số lượt Đăng ký: {total_dk}")

        # -------------------------------------------------------------
        # 9. PHÂN CA LÀM VIỆC (PhanCa) - Đủ 50 nhân viên
        # -------------------------------------------------------------
        print("\n[9/13] Nạp dữ liệu Phân ca làm việc (PhanCa) cho 50 nhân viên...")
        shift_types = [
            ('Ca hành chính (08:00 - 17:30)', 'Làm việc cố định văn phòng từ Thứ 2 đến Thứ 6'),
            ('Ca sáng (06:00 - 14:00)', 'Ca trực vận hành hệ thống và chăm sóc khách hàng buổi sáng'),
            ('Ca chiều (14:00 - 22:00)', 'Ca trực vận hành hỗ trợ kỹ thuật và CSKH buổi chiều tối'),
            ('Ca linh hoạt (Flexible 8h/ngày)', 'Linh động giờ vào từ 8h00 - 9h00 cho đội ngũ R&D')
        ]

        for i, emp in enumerate(employees):
            mnv = emp['MaNV']
            emp_num = int(mnv[2:])
            stype, snote = shift_types[emp_num % len(shift_types)]
            d_shift = '2026-10-01'
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM PhanCa WHERE MaNV = ? AND Ngay = ?)
                    INSERT INTO PhanCa(MaNV, Ngay, CaLam, GhiChu)
                    VALUES(?, ?, ?, ?)
                ELSE
                    UPDATE PhanCa SET CaLam = ?, GhiChu = ? WHERE MaNV = ? AND Ngay = ?
            """, (mnv, d_shift, mnv, d_shift, stype, snote, stype, snote, mnv, d_shift))

        db.commit()
        total_pc = db.execute("SELECT COUNT(*) FROM PhanCa").fetchone()[0]
        print(f"-> Tổng số bản ghi Phân ca làm việc: {total_pc}")

        # -------------------------------------------------------------
        # 10. ĐỀ XUẤT & Ý KIẾN KHIẾU NẠI (DeXuatKhieuNai)
        # -------------------------------------------------------------
        print("\n[10/13] Nạp Đề xuất & Khiếu nại (DeXuatKhieuNai)...")
        feedback_list = [
            ('Đề xuất trang bị màn hình máy tính phụ cho đội Lập trình & QA', 'Đề xuất cải tiến', 'Giúp nhân viên đối chiếu mã nguồn và tài liệu thiết kế nhanh hơn, tăng 30% hiệu suất.', 'Đã xử lý', 'Phòng Hành chính đã mua sắm và bàn giao 20 màn hình Dell 24 inch.'),
            ('Đề xuất tổ chức workshop chia sẻ kiến thức công nghệ nội bộ', 'Đề xuất đào tạo', 'Tổ chức định kỳ thứ 6 tuần thứ 3 mỗi tháng để các team chia sẻ công nghệ mới.', 'Đã xử lý', 'Ban Giám đốc đã đồng ý và cấp kinh phí 2.000.000đ/buổi.'),
            ('Đề xuất lắp đặt thêm máy lọc nước nóng lạnh tại khu Pantry tầng 4', 'Đề xuất cơ sở vật chất', 'Khu vực tầng 4 đông người nhưng máy lọc nước thường xuyên bị hết nước nóng.', 'Đã xử lý', 'Đã lắp đặt thêm máy lọc nước Kangaroo công suất lớn.'),
            ('Đề xuất chính sách làm việc linh hoạt (Flexible hours) cho khối kỹ thuật', 'Đề xuất chính sách', 'Cho phép nhân viên check-in từ 8h00 đến 9h00 và về sau khi đủ 8 tiếng làm việc.', 'Đang xử lý', 'Phòng Nhân sự đang xây dựng dự thảo quy chế trình Giám đốc.'),
            ('Khiếu nại về điều hòa phòng Marketing làm lạnh không đồng đều', 'Khiếu nại cơ sở vật chất', 'Vị trí góc phòng quá lạnh trong khi khu vực cửa ra vào lại khá ngột ngạt.', 'Đã xử lý', 'Đội bảo trì đã bảo dưỡng hệ thống gió và đảo hướng quạt trần.'),
            ('Đề xuất mua sách chuyên môn bổ sung cho Tủ sách công ty', 'Đề xuất văn hóa', 'Bổ sung các đầu sách về AI, Clean Code, Thiết kế hệ thống phân tán và Quản trị kinh doanh.', 'Đã xử lý', 'Đã phê duyệt mua 35 đầu sách chuyên ngành tại Tiki/Fahasa.'),
            ('Đề xuất tài trợ chi phí thi chứng chỉ quốc tế cho nhân viên đạt loại Tốt', 'Đề xuất chế độ', 'Khuyến khích nhân viên tự học và nâng cao năng lực chuyên môn đạt chuẩn quốc tế.', 'Chờ xử lý', 'Đang tổng hợp ý kiến từ các Trưởng bộ phận.'),
            ('Đề xuất thành lập câu lạc bộ bóng đá & cầu lông giao lưu gắn kết', 'Đề xuất phong trào', 'Gắn kết các thành viên giữa các phòng ban thông qua hoạt động thể thao cuối tuần.', 'Đã xử lý', 'Công ty hỗ trợ 50% tiền thuê sân định kỳ mỗi tuần.'),
            ('Đề xuất nâng cấp đường truyền Internet cáp quang dự phòng', 'Đề xuất hạ tầng', 'Hạn chế tình trạng giật lag khi nhiều phòng ban đồng thời họp trực tuyến Zoom/Teams.', 'Đã xử lý', 'Đã ký hợp đồng bổ sung đường truyền VNPT 300Mbps.'),
            ('Đề xuất trang bị thêm ghế công thái học cho nhân viên ngồi máy tính nhiều', 'Đề xuất sức khỏe', 'Giúp phòng ngừa các bệnh văn phòng về cột sống và tăng cường tập trung làm việc.', 'Đang xử lý', 'Đang lấy báo giá từ các nhà cung cấp nội thất.')
        ]

        for i, (tieude, loai, noidung, tt, phanhoi) in enumerate(feedback_list):
            emp = employees[i % len(employees)]
            mnv = emp['MaNV']
            d_gui = f"2026-10-{(10 + i):02d}"
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM DeXuatKhieuNai WHERE TieuDe = ?)
                    INSERT INTO DeXuatKhieuNai(MaNV, TieuDe, Loai, NoiDung, NgayGui, TrangThai, PhanHoi, NguoiXuLy)
                    VALUES(?, ?, ?, ?, ?, ?, ?, N'Ban Quản trị & Hành chính')
            """, (tieude, mnv, tieude, loai, noidung, d_gui, tt, phanhoi))

        db.commit()
        total_dx = db.execute("SELECT COUNT(*) FROM DeXuatKhieuNai").fetchone()[0]
        print(f"-> Tổng số bản ghi Đề xuất & Khiếu nại: {total_dx}")

        # -------------------------------------------------------------
        # 11. ĐỀ XUẤT NHÂN SỰ TỪ QUẢN LÝ (DeXuatNhanSu)
        # -------------------------------------------------------------
        print("\n[11/13] Nạp Đề xuất nhân sự từ Quản lý gửi Admin (DeXuatNhanSu)...")
        proposals = [
            ('NV008', 'NV014', 'Khen thưởng', 'Thưởng nóng 3.000.000đ', 'Đã nỗ lực hoàn thành module bảo mật vượt tiến độ 10 ngày', 'Đã duyệt', 'Đồng ý khen thưởng theo đề xuất của Trưởng phòng.'),
            ('NV006', 'NV019', 'Tăng lương', 'Tăng 20% lương cơ bản', 'Nhân viên có năng lực vượt trội, đảm nhiệm xuất sắc cả phần kế toán thuế và quản trị dòng tiền', 'Đã duyệt', 'Đã phê duyệt điều chỉnh tăng lương áp dụng từ tháng 11/2026.'),
            ('NV007', 'NV020', 'Thăng chức', 'Bổ nhiệm Trưởng nhóm Marketing số', 'Dẫn dắt chiến dịch ra mắt sản phẩm mới đạt 150% KPI doanh số', 'Đã duyệt', 'Đồng ý bổ nhiệm và giao quyết định chính thức.'),
            ('NV008', 'NV021', 'Khen thưởng', 'Thưởng sáng kiến 2.500.000đ', 'Thiết kế hệ thống Design System chuẩn UX/UI giúp tăng tốc độ dựng giao diện', 'Đã duyệt', 'Khen thưởng và tuyên dương toàn công ty.'),
            ('NV011', 'NV024', 'Tăng lương', 'Tăng 15% lương cơ sở', 'Hoàn thành xuất sắc việc rà soát pháp lý 45 hợp đồng kinh tế lớn không có rủi ro', 'Chờ HR phê duyệt', 'Đang thẩm định hồ sơ cùng Ban Giám đốc.'),
            ('NV010', 'NV030', 'Khen thưởng', 'Danh hiệu Ngôi sao CSKH xuất sắc tháng', 'Duy trì tỷ lệ khách hàng hài lòng CSAT 100% trong 3 tháng liên tiếp', 'Đã duyệt', 'Trao bằng khen và phần thưởng 2.000.000đ.'),
            ('NV008', 'NV028', 'Tăng lương', 'Tăng mức lương lên 26.000.000đ', 'Đảm nhiệm vai trò Tech Lead kiến trúc vi dịch vụ (Microservices) ổn định cao', 'Đã duyệt', 'Phê duyệt điều chỉnh hợp đồng lao động mới.'),
            ('NV006', 'NV026', 'Thăng chức', 'Bổ nhiệm Trưởng nhóm Kiểm toán nội bộ', 'Có chứng chỉ CPA và kinh nghiệm 6 năm kiểm soát tài chính chính xác tuyệt đối', 'Đã duyệt', 'Ban Giám đốc đã ký quyết định bổ nhiệm.')
        ]

        for n_dx, mnv_tgt, loai, muc, lydo, tt, yk in proposals:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM DeXuatNhanSu WHERE MaNV = ? AND LoaiDeXuat = ? AND MucDeXuat = ?)
                    INSERT INTO DeXuatNhanSu(MaNV, NguoiDeXuat, LoaiDeXuat, MucDeXuat, LyDo, NgayDeXuat, TrangThai, YKienPheDuyet, NguoiPheDuyet)
                    VALUES(?, ?, ?, ?, ?, '2026-10-18', ?, ?, N'Giám đốc Nhân sự')
            """, (mnv_tgt, loai, muc, mnv_tgt, n_dx, loai, muc, lydo, tt, yk))

        db.commit()
        total_dxns = db.execute("SELECT COUNT(*) FROM DeXuatNhanSu").fetchone()[0]
        print(f"-> Tổng số Đề xuất Nhân sự: {total_dxns}")

        # -------------------------------------------------------------
        # 12. TUYỂN DỤNG & ỨNG VIÊN (YeuCauTuyenDung & UngVien)
        # -------------------------------------------------------------
        print("\n[12/13] Nạp Yêu cầu tuyển dụng & Hồ sơ ứng viên...")
        recruit_reqs = [
            ('PB02', 'Kỹ sư Lập trình Backend (Python/Django/FastAPI)', 3, 'Tối thiểu 2 năm kinh nghiệm với Python, SQL Server/PostgreSQL, Docker, RESTful APIs.', 'Mở rộng đội ngũ phát triển sản phẩm SaaS quản trị nhân sự thế hệ mới.', '2026-11-30', 'Đang tuyển'),
            ('PB03', 'Chuyên viên Kinh doanh Doanh nghiệp (B2B Sales)', 2, 'Giao tiếp tốt, có kinh nghiệm bán phần mềm B2B hoặc giải pháp chuyển đổi số.', 'Đẩy mạnh phát triển thị trường khách hàng doanh nghiệp vừa và lớn.', '2026-11-25', 'Đang tuyển'),
            ('PB04', 'Kế toán Tổng hợp & Thuế Doanh nghiệp', 1, 'Tốt nghiệp Đại học chuyên ngành Kế toán, thành thạo MISA/Fast, nắm vững luật thuế.', 'Thay thế nhân sự nghỉ chế độ thai sản.', '2026-11-15', 'Đang tuyển'),
            ('PB05', 'Chuyên viên Tuyển dụng & Đào tạo Nhân tài (HR Talent)', 2, 'Kinh nghiệm tuyển dụng IT/Tech, xây dựng thương hiệu nhà tuyển dụng.', 'Đáp ứng kế hoạch tăng trưởng quy mô công ty lên 100 nhân sự trong năm 2027.', '2026-12-10', 'Đang tuyển'),
            ('PB06', 'Chuyên viên Marketing Hiệu suất (Performance Ads)', 1, 'Thành thạo chạy quảng cáo Facebook, Google Ads, TikTok Ads và tối ưu chuyển đổi.', 'Triển khai chiến dịch tiếp thị số quý 4.', '2026-11-20', 'Đang tuyển')
        ]

        for mpb, vt, sl, yc, ld, ht, tt in recruit_reqs:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM YeuCauTuyenDung WHERE ViTri = ? AND MaPB = ?)
                    INSERT INTO YeuCauTuyenDung(MaPB, ViTri, SoLuong, YeuCau, LyDo, HanTuyen, TrangThai)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (vt, mpb, mpb, vt, sl, yc, ld, ht, tt))

        db.commit()

        # Nạp danh sách ứng viên
        yc_list = db.execute("SELECT MaYC, ViTri, MaPB FROM YeuCauTuyenDung").fetchall()
        candidates = [
            ('Nguyễn Hoàng Nam', 'nam.nh@gmail.com', '0912345678', 'Kỹ sư Lập trình Backend (Python/Django/FastAPI)', 'PB02', '2026-11-05', 'Trưởng phòng CNTT Bùi Đức Trọng', 'Trúng tuyển', 'Nắm vững kiến thức thuật toán và kiến trúc microservices. Pass vòng phỏng vấn kỹ thuật.'),
            ('Trần Thảo Ly', 'ly.tt@gmail.com', '0923456789', 'Kỹ sư Lập trình Backend (Python/Django/FastAPI)', 'PB02', '2026-11-06', 'Trưởng phòng CNTT Bùi Đức Trọng', 'Chờ phỏng vấn', 'CV đẹp, từng làm dự án thương mại điện tử lớn. Đã gửi thư mời phỏng vấn vòng 2.'),
            ('Lê Văn Hùng', 'hung.lv@gmail.com', '0934567890', 'Kỹ sư Lập trình Backend (Python/Django/FastAPI)', 'PB02', '2026-10-28', 'Kỹ sư Phan Thanh Hải', 'Không đạt', 'Kỹ năng giải quyết bài toán concurrency và tối ưu truy vấn SQL chưa đáp ứng kỳ vọng.'),
            ('Phạm Thùy Dương', 'duong.pt@gmail.com', '0945678901', 'Chuyên viên Kinh doanh Doanh nghiệp (B2B Sales)', 'PB03', '2026-11-07', 'Trưởng phòng KD Đặng Tuấn Anh', 'Trúng tuyển', 'Kỹ năng đàm phán rất xuất sắc, có sẵn tệp khách hàng doanh nghiệp sản xuất.'),
            ('Vũ Đình Quang', 'quang.vd@gmail.com', '0956789012', 'Chuyên viên Kinh doanh Doanh nghiệp (B2B Sales)', 'PB03', '2026-11-08', 'Trưởng phòng KD Đặng Tuấn Anh', 'Chờ phỏng vấn', 'Đã vượt qua bài kiểm tra tình huống bán hàng sơ bộ.'),
            ('Hoàng Mai Lan', 'lan.hm@gmail.com', '0967890123', 'Kế toán Tổng hợp & Thuế Doanh nghiệp', 'PB04', '2026-11-02', 'Kế toán trưởng Vũ Thị Phương Thảo', 'Trúng tuyển', 'Kinh nghiệm 4 năm kế toán tổng hợp, nắm chắc chính sách hóa đơn điện tử.'),
            ('Đỗ Tuấn Kiệt', 'kiet.dt@gmail.com', '0978901234', 'Chuyên viên Tuyển dụng & Đào tạo Nhân tài (HR Talent)', 'PB05', '2026-11-09', 'Trưởng phòng NS Trần Thị Bình', 'Chờ phỏng vấn', 'Có kinh nghiệm Headhunter chuyên mảng Tech, giao tiếp tiếng Anh lưu loát.'),
            ('Ngô Bích Hạnh', 'hanh.nb@gmail.com', '0989012345', 'Chuyên viên Marketing Hiệu suất (Performance Ads)', 'PB06', '2026-11-04', 'Trưởng phòng MKT Dương Thúy Hằng', 'Trúng tuyển', 'Có số liệu case study thực tế ấn tượng, tư duy đo lường chỉ số ROI/ROAS sắc bén.')
        ]

        for hoten, em, sdt, vt, mpb, npv, ngpv, kq, nx in candidates:
            # Map MaYC tương ứng
            matching_yc = [y['MaYC'] for y in yc_list if y['ViTri'] == vt]
            myc = matching_yc[0] if matching_yc else None

            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM UngVien WHERE HoTen = ? AND Email = ?)
                    INSERT INTO UngVien(MaYC, HoTen, Email, SDT, ViTriUngTuyen, MaPB, NgayPV, NguoiPV, KetQua, NhanXet)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (hoten, em, myc, hoten, em, sdt, vt, mpb, npv, ngpv, kq, nx))

        db.commit()
        total_yc = db.execute("SELECT COUNT(*) FROM YeuCauTuyenDung").fetchone()[0]
        total_uv = db.execute("SELECT COUNT(*) FROM UngVien").fetchone()[0]
        print(f"-> Tổng số Yêu cầu tuyển dụng: {total_yc}, Tổng số Ứng viên: {total_uv}")

        # -------------------------------------------------------------
        # 13. THÔNG BÁO NỘI BỘ (ThongBao)
        # -------------------------------------------------------------
        print("\n[13/13] Nạp Thông báo nội bộ công ty (ThongBao)...")
        announcements = [
            ('Kế hoạch nghỉ lễ và phân công trực vận hành dịp Tết Dương Lịch 2027',
             'Ban Giám đốc thông báo toàn thể cán bộ nhân viên lịch nghỉ Tết Dương Lịch từ ngày 01/01/2027 đến hết ngày 03/01/2027. Các bộ phận Kỹ thuật và CSKH bố trí nhân sự trực online đảm bảo hệ thống vận hành liên tục 24/7.',
             '2026-10-25', 'Ban Giám Đốc', 'Toàn công ty', None),
            ('Phát động chiến dịch "90 ngày thi đua hoàn thành xuất sắc mục tiêu năm 2026"',
             'Toàn thể công ty bước vào giai đoạn tăng tốc cuối năm. Các phòng ban đạt và vượt kế hoạch doanh số, dự án sẽ được khen thưởng đột xuất và nhận hệ số thưởng tháng lương thứ 13 hấp dẫn.',
             '2026-10-15', 'Tổng Giám Đốc', 'Toàn công ty', None),
            ('Thông báo tổ chức khám sức khỏe định kỳ năm 2026 cho cán bộ nhân viên',
             'Phòng Nhân sự phối hợp cùng Bệnh viện Đa khoa Quốc tế tổ chức khám sức khỏe định kỳ vào ngày 15/11/2026 tại Trụ sở chính. Đề nghị các phòng ban sắp xếp công việc để nhân viên tham gia đầy đủ.',
             '2026-10-20', 'Phòng Nhân sự', 'Toàn công ty', None),
            ('Ban hành Quy định Quản lý An toàn Thông tin và Sử dụng thiết bị CNTT',
             'Yêu cầu 100% cán bộ nhân viên không cài đặt phần mềm không có bản quyền, kích hoạt xác thực hai yếu tố (2FA) trên tài khoản công ty và đổi mật khẩu định kỳ 90 ngày một lần.',
             '2026-10-10', 'Phòng CNTT & Bảo mật', 'Toàn công ty', 'PB02'),
            ('Tổ chức Giải bóng đá Cúp Tứ Hùng chào mừng ngày truyền thống công ty',
             'Công đoàn công ty trân trọng thông báo khai mạc giải bóng đá mini nam - nữ giữa 4 khối phòng ban vào ngày 08/11/2026 tại sân bóng Thành Phát. Giải thưởng nhất trị giá 10.000.000đ.',
             '2026-10-28', 'Công đoàn Công ty', 'Toàn công ty', None),
            ('Chính sách khen thưởng sáng kiến cải tiến quy trình công việc năm 2026',
             'Khuyến khích mọi nhân sự đóng góp giải pháp tiết kiệm chi phí, tối ưu tự động hóa và nâng cao năng suất. Mỗi sáng kiến được áp dụng thực tế sẽ được thưởng nóng từ 1.000.000đ đến 10.000.000đ.',
             '2026-10-05', 'Hội đồng Sáng kiến', 'Toàn công ty', None)
        ]

        for td, nd, ng, nguoi, pv, mpb in announcements:
            db.execute("""
                IF NOT EXISTS (SELECT 1 FROM ThongBao WHERE TieuDe = ?)
                    INSERT INTO ThongBao(TieuDe, NoiDung, NgayGui, NguoiGui, PhamVi, MaPB)
                    VALUES(?, ?, ?, ?, ?, ?)
            """, (td, td, nd, ng, nguoi, pv, mpb))

        # Chốt công tháng cũ
        db.execute("""
            IF NOT EXISTS (SELECT 1 FROM ChotCong WHERE ThangNam = '2026-09')
                INSERT INTO ChotCong(ThangNam, NgayChot, NguoiChot)
                VALUES('2026-09', '2026-10-01 17:00:00', N'Admin Quản Trị')
        """)

        db.commit()
        total_tb = db.execute("SELECT COUNT(*) FROM ThongBao").fetchone()[0]
        print(f"-> Tổng số Thông báo: {total_tb}")

        print("\n=======================================================")
        print("🎉 HOÀN THÀNH NẠP DỮ LIỆU ĐỦ 50 NHÂN VIÊN CHO TOÀN BỘ CHỨC NĂNG!")
        print("=======================================================")

if __name__ == '__main__':
    run_seed()
