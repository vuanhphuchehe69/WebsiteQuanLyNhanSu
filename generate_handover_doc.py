# -*- coding: utf-8 -*-
"""Script to generate professional handover document in Word (.docx) format."""
import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tc_pr.append(tcMar)

def create_document():
    doc = docx.Document()

    # Page setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False

        # Footer
        footer_para = section.footer.paragraphs[0]
        footer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = footer_para.add_run("Tài liệu Bàn giao HRM System - Nhóm 2 • Trang ")
        f_run.font.name = "Arial"
        f_run.font.size = Pt(9)
        f_run.font.color.rgb = RGBColor(148, 163, 184)

    # Styles setup
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Arial'
    font.size = Pt(11)
    font.color.rgb = RGBColor(30, 41, 59)

    # --- COVER / TITLE BLOCK ---
    title_box = doc.add_table(rows=1, cols=1)
    title_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    title_box.autofit = False
    title_cell = title_box.cell(0, 0)
    title_cell.width = Inches(6.5)
    set_cell_background(title_cell, "1E3A8A")
    set_cell_margins(title_cell, top=400, bottom=400, left=300, right=300)

    p_badge = title_cell.paragraphs[0]
    p_badge.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_badge = p_badge.add_run("BÁO CÁO KỸ THUẬT & HỒ SƠ BÀN GIAO")
    r_badge.font.name = 'Arial'
    r_badge.font.size = Pt(11)
    r_badge.font.bold = True
    r_badge.font.color.rgb = RGBColor(191, 219, 254)

    p_title = title_cell.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("HỆ THỐNG QUẢN TRỊ NHÂN SỰ DOANH NGHIỆP\n(HRM SYSTEM - VERSION 2.5 SAAS)")
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(20)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(255, 255, 255)

    p_sub = title_cell.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Tài liệu Giới thiệu Website, Hướng dẫn Vận hành, Cấu trúc Thư mục,\nDanh mục Chức năng, Các Cải tiến Mới & Đề xuất Nâng cấp")
    r_sub.font.name = 'Arial'
    r_sub.font.size = Pt(11.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(226, 232, 240)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Meta table
    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Đơn vị thực hiện:", "Nhóm 2 - Dự án Phát triển Ứng dụng Web Quản lý Nhân sự"),
        ("Nền tảng công nghệ:", "Python 3.13, Flask Framework, Microsoft SQL Server (MSSQL), SQLite"),
        ("Ngày lập tài liệu:", "31/10/2026 (Phiên bản nghiệm thu & hoàn thiện)"),
        ("Trạng thái kiểm thử:", "Đạt 54/54 Kịch bản Kiểm thử Tự động (100% Pass Test Suite)")
    ]
    for idx, (lbl, val) in enumerate(meta_data):
        c1 = meta_tbl.cell(idx, 0)
        c2 = meta_tbl.cell(idx, 1)
        c1.width = Inches(2.2)
        c2.width = Inches(4.3)
        set_cell_background(c1, "F8FAFC")
        set_cell_background(c2, "FFFFFF")
        set_cell_margins(c1, top=80, bottom=80, left=120, right=120)
        set_cell_margins(c2, top=80, bottom=80, left=120, right=120)

        p1 = c1.paragraphs[0]
        r1 = p1.add_run(lbl)
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = RGBColor(71, 85, 105)

        p2 = c2.paragraphs[0]
        r2 = p2.add_run(val)
        r2.font.size = Pt(10)
        r2.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # Helper function for Section Headings
    def add_heading_1(title_text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(title_text)
        r.font.name = 'Arial'
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        # underline style via XML
        pPr = h._p.get_or_add_pPr()
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="3B82F6"/></w:pBdr>')
        pPr.append(pBdr)
        return h

    def add_heading_2(title_text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(title_text)
        r.font.name = 'Arial'
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(79, 70, 229)
        return h

    def add_callout(text, title="LƯU Ý QUAN TRỌNG:"):
        box = doc.add_table(rows=1, cols=1)
        box.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = box.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_background(cell, "EFF6FF")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:color="3B82F6"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
        tcPr.append(tcBorders)

        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r_t = p.add_run(title + " ")
        r_t.font.bold = True
        r_t.font.size = Pt(10)
        r_t.font.color.rgb = RGBColor(29, 78, 216)
        r_c = p.add_run(text)
        r_c.font.size = Pt(10)
        r_c.font.color.rgb = RGBColor(30, 41, 59)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ================= PHẦN 1 =================
    add_heading_1("PHẦN 1: GIỚI THIỆU TỔNG QUAN WEBSITE & MỤC TIÊU DỰ ÁN")

    p = doc.add_paragraph()
    p.add_run("Website Quản Lý Nhân Sự (HRM System) là giải pháp phần mềm quản trị nguồn nhân lực toàn diện, được thiết kế chuyên biệt cho các doanh nghiệp vừa và nhỏ (SME) cũng như các phòng ban chuyên môn. Hệ thống giải quyết các vấn đề thủ công trong quản trị nhân sự truyền thống như: chấm công rườm rà, sai số tính lương, thất lạc bằng cấp hợp đồng, chậm trễ xét duyệt đơn từ và thiếu hụt các báo cáo số liệu phân tích trực quan.")

    p2 = doc.add_paragraph()
    p2.add_run("Hệ thống hoạt động theo mô hình phân quyền chặt chẽ theo 3 tác nhân (Actor): ")
    p2.add_run("Nhân viên (Employee)").bold = True
    p2.add_run(", ")
    p2.add_run("Quản lý bộ phận (Department Manager)").bold = True
    p2.add_run(" và ")
    p2.add_run("Quản trị viên (HR Admin / Super Administrator)").bold = True
    p2.add_run(". Mỗi vai trò được cấp quyền truy cập các mô-đun và chức năng riêng biệt, đảm bảo an toàn dữ liệu và tối ưu trải nghiệm người dùng.")

    add_heading_2("1.1. Công nghệ Cốt lõi & Kiến trúc Hệ thống")
    tech_table = doc.add_table(rows=6, cols=3)
    tech_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Thành phần", "Công nghệ / Thư viện", "Mô tả vai trò & Tính năng"]
    for i, h_text in enumerate(headers):
        c = tech_table.cell(0, i)
        set_cell_background(c, "1E3A8A")
        set_cell_margins(c, top=100, bottom=100, left=120, right=120)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(10)

    tech_rows = [
        ("Backend Framework", "Python 3.13 + Flask 3.1", "Xử lý nghiệp vụ MVC, định tuyến Blueprint, Middleware CSRF, Quản lý Session."),
        ("Cơ sở dữ liệu chính", "Microsoft SQL Server (pyodbc)", "Hệ quản trị CSDL chuẩn doanh nghiệp, lưu trữ bảng giao dịch, quan hệ khóa ngoại."),
        ("CSDL dự phòng", "SQLite 3 (nhansu.db)", "Tự động chuyển đổi nếu môi trường chạy không có SQL Server, đảm bảo tính sẵn sàng."),
        ("Giao diện Frontend", "Jinja2 + HTML5 / CSS3 / ES6+", "Thiết kế hiện đại chuẩn SaaS (Linear/Stripe), hỗ trợ Dark/Light mode, không phụ thuộc nặng JS nặng."),
        ("Trợ lý ảo & Phân tích", "AI Chatbot Assistant + SVG Donut", "Trợ lý giải đáp phép năm/tạm ứng, tự động tóm tắt hồ sơ và vẽ biểu đồ hình tròn SVG."),
    ]
    for row_idx, data in enumerate(tech_rows, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = tech_table.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ================= PHẦN 2 =================
    add_heading_1("PHẦN 2: HƯỚNG DẪN CÀI ĐẶT & VẬN HÀNH HỆ THỐNG")

    add_heading_2("2.1. Yêu cầu Môi trường Phần cứng & Phần mềm")
    p = doc.add_paragraph()
    p.add_run("• Hệ điều hành: Windows 10/11, Windows Server, Linux hoặc macOS.\n")
    p.add_run("• Python: Phiên bản Python 3.10 trở lên (khuyến nghị Python 3.12 hoặc 3.13).\n")
    p.add_run("• Hệ quản trị CSDL: Microsoft SQL Server (2019/2022 hoặc Express Edition) có cài ODBC Driver 18/17 for SQL Server.\n")
    p.add_run("• Trình duyệt Web: Google Chrome, Microsoft Edge, Firefox hoặc Safari phiên bản mới.")

    add_heading_2("2.2. Các bước Cài đặt & Khởi động")
    steps = [
        ("Bước 1: Mở Terminal / PowerShell", "Điều hướng vào thư mục dự án: cd d:\\Ghost\\WebsiteQuanLyNhanSu"),
        ("Bước 2: Cài đặt các thư viện cần thiết", "Chạy lệnh: pip install -r requirements.txt (hoặc: pip install flask pyodbc python-docx)"),
        ("Bước 3: Cấu hình Cơ sở dữ liệu", "Hệ thống mặc định kết nối .\\SQLEXPRESS, database QLNhanSuNhom2. Nếu muốn đổi máy chủ, cấu hình biến môi trường MSSQL_SERVER hoặc ứng dụng sẽ tự động fallback sang SQLite nếu không có MSSQL."),
        ("Bước 4: Khởi động ứng dụng", "Chạy lệnh: python ss/app.py\nHệ thống sẽ hiển thị: Khởi động hệ thống Quản lý nhân sự tại: http://127.0.0.1:5000"),
        ("Bước 5: Truy cập hệ thống", "Mở trình duyệt web và truy cập địa chỉ: http://127.0.0.1:5000")
    ]
    for s_title, s_desc in steps:
        p = doc.add_paragraph()
        r1 = p.add_run(s_title + ": ")
        r1.font.bold = True
        r1.font.color.rgb = RGBColor(30, 41, 59)
        r2 = p.add_run(s_desc)
        r2.font.color.rgb = RGBColor(71, 85, 105)

    add_heading_2("2.3. Danh sách Tài khoản Đăng nhập Mặc định")
    acc_table = doc.add_table(rows=4, cols=4)
    acc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    acc_headers = ["Vai trò", "Tên đăng nhập", "Mật khẩu mặc định", "Ghi chú quyền hạn"]
    for i, h_text in enumerate(acc_headers):
        c = acc_table.cell(0, i)
        set_cell_background(c, "1E3A8A")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9.5)

    acc_rows = [
        ("Quản trị viên (Admin)", "admin", "admin123", "Toàn quyền quản trị hệ thống, tài khoản, lương, danh mục, báo cáo"),
        ("Quản lý bộ phận (Manager)", "ql001", "123456", "Trưởng phòng Nhân sự (NV001), quản lý hồ sơ, duyệt đơn, chấm công phòng"),
        ("Nhân viên (Employee)", "nv002 (hoặc nv003, nv004, nv005)", "123456", "Nhân viên chuyên viên, tra cứu thông tin, điểm danh, nộp đơn từ cá nhân"),
    ]
    for row_idx, data in enumerate(acc_rows, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = acc_table.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            if col_idx == 0:
                r.font.bold = True

    add_callout("Để đẩy toàn bộ mã nguồn lên kho lưu trữ GitHub/GitLab của bạn, chạy các lệnh: git remote add origin <URL_REPO_CUA_BAN> -> git branch -M master -> git push -u origin master", "HƯỚNG DẪN KẾT NỐI GIT TỪ XA:")

    # ================= PHẦN 3 =================
    add_heading_1("PHẦN 3: BẢN ĐỒ CẤU TRÚC THƯ MỤC & CHỨC NĂNG TỪNG TỆP TIN")

    p = doc.add_paragraph()
    p.add_run("Mã nguồn dự án được tổ chức theo cấu trúc mô-đun hóa (Modular Architecture) chặt chẽ, tách bạch rõ ràng giữa tầng dữ liệu, tầng định tuyến nghiệp vụ và tầng giao diện:")

    tree_text = (
        "WebsiteQuanLyNhanSu/\n"
        "│\n"
        "├── ss/                                  # Thư mục gốc gói ứng dụng Flask\n"
        "│   ├── app.py                           # Application Factory, khởi tạo Flask, Jinja Loader, CSRF, Context Processor\n"
        "│   ├── config.py                        # Cấu hình hệ thống, NAV menu, định nghĩa các mô-đun bảng, phân quyền\n"
        "│   ├── database.py                      # Kết nối MSSQL & SQLite, thực thi SQL, cơ chế chống lặp clean_all_duplicates\n"
        "│   ├── utils.py                         # Tiện ích bảo mật, CSRF guard, validate form, phân trang, ghi nhật ký hoạt động\n"
        "│   ├── test_app.py                      # Bộ kiểm thử tự động toàn diện gồm 54 kịch bản kiểm tra chức năng\n"
        "│   │\n"
        "│   ├── routes/                          # Tầng định tuyến (Flask Blueprints)\n"
        "│   │   ├── __init__.py                  # Đăng ký Blueprints vào Flask app\n"
        "│   │   ├── auth.py                      # Xác thực: Đăng nhập phân quyền, Đăng xuất, Đổi mật khẩu đồng bộ\n"
        "│   │   ├── main.py                      # Nghiệp vụ Dashboard, Cá nhân (/me), Chấm công, Báo cáo, AI Chatbot API\n"
        "│   │   └── modules.py                   # Quản lý dữ liệu động các bảng (/m/<mod>): danh sách, thêm, sửa, xóa, xuất Excel\n"
        "│   │\n"
        "│   ├── templates/                       # Giao diện Jinja2 Templates\n"
        "│   │   ├── base.html                    # Layout chuẩn: Sidebar, Header, Theme Switch, Command Palette, AI Chatbot\n"
        "│   │   ├── login.html                   # Trang đăng nhập chia đôi màn hình (Split screen) phong cách SaaS cao cấp\n"
        "│   │   ├── dash.html                    # Dashboard chính: Thẻ số liệu count-up, 2 Biểu đồ hình tròn SVG, Cảnh báo nghỉ việc\n"
        "│   │   ├── me.html                      # Cổng thông tin nhân viên: Hồ sơ cá nhân, phiếu lương, điểm danh, phép năm\n"
        "│   │   ├── list.html                    # Bảng dữ liệu thông minh: Ảnh thẻ 3x4, phân trang, tìm kiếm tức thì, xuất CSV\n"
        "│   │   ├── form.html                    # Biểu mẫu thêm/sửa dữ liệu dùng chung hỗ trợ upload ảnh\n"
        "│   │   ├── form_doc.html                # Biểu mẫu tải lên bằng cấp, chứng chỉ, scan hợp đồng cho nhân viên\n"
        "│   │   ├── analytics.html               # Báo cáo phân tích nâng cao, biểu đồ biến động nhân sự, tỷ lệ nghỉ việc\n"
        "│   │   ├── report_hr.html               # Báo cáo cơ cấu nhân sự theo phòng ban và xuất Excel\n"
        "│   │   ├── report_leave.html            # Báo cáo thống kê tình hình nghỉ phép năm và chi tiết đơn\n"
        "│   │   ├── backup.html                  # Trung tâm sao lưu dữ liệu SQL Script và JSON Snapshot\n"
        "│   │   ├── audit_log.html               # Nhật ký hoạt động người dùng và lịch sử truy vết hệ thống\n"
        "│   │   ├── announcements.html           # Bảng tin thông báo nội bộ toàn công ty và phòng ban\n"
        "│   │   └── training.html                # Cổng thông tin các khóa đào tạo nội bộ và đăng ký học\n"
        "│   │\n"
        "│   └── static/                          # Tài nguyên tĩnh\n"
        "│       ├── css/style.css                # Bộ stylesheet cao cấp: Dark/Light Mode, Glassmorphism, 3x4 wrap, Animation\n"
        "│       └── uploads/                     # Thư mục lưu trữ tệp tin upload\n"
        "│           ├── avatars/                 # Ảnh thẻ chân dung 3x4 của nhân viên\n"
        "│           └── documents/               # Tệp scan văn bằng, chứng chỉ, hợp đồng đính kèm\n"
        "│\n"
        "├── .gitignore                           # Cấu hình bỏ qua file rác, bytecode pycache, database cục bộ\n"
        "└── TAI_LIEU_BAN_GIAO_HE_THONG_QUAN_LY_NHAN_SU.docx  # Tài liệu bàn giao chính thức\n"
    )
    p_code = doc.add_paragraph()
    r_code = p_code.add_run(tree_text)
    r_code.font.name = "Consolas"
    r_code.font.size = Pt(8.5)
    r_code.font.color.rgb = RGBColor(30, 41, 59)
    pPr = p_code._p.get_or_add_pPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
    pPr.append(shd)

    # ================= PHẦN 4 =================
    add_heading_1("PHẦN 4: MA TRẬN CHỨC NĂNG CHI TIẾT THEO 3 TÁC NHÂN (ACTOR)")

    func_table = doc.add_table(rows=1, cols=3)
    func_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    f_headers = ["Phân hệ / Nghiệp vụ", "Đối tượng sử dụng", "Mô tả tính năng chi tiết"]
    for i, h_text in enumerate(f_headers):
        c = func_table.cell(0, i)
        set_cell_background(c, "1E3A8A")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9.5)

    func_list = [
        ("Cổng thông tin cá nhân (/me)", "Nhân viên, Quản lý", "Xem lý lịch 360°, hợp đồng hiện tại, lịch sử công việc, chi tiết phiếu lương (lương cứng, thưởng, phụ cấp, BHXH, thuế TNCN, thực lĩnh), lịch sử chấm công theo tháng, số ngày phép đã nghỉ."),
        ("Điểm danh trực tuyến (Check-in / Check-out)", "Nhân viên, Quản lý", "Điểm danh vào làm lúc sáng và ra về lúc chiều chỉ bằng 1 bấm chuột. Tự động ghi nhận giờ, xác định trạng thái 'Đúng giờ', 'Đi muộn' hoặc 'Về sớm'."),
        ("Đăng ký & Xin nghỉ phép", "Nhân viên, Quản lý", "Tạo đơn xin nghỉ phép (nghỉ phép năm, ốm đau, việc riêng), chọn khoảng ngày, nhập lý do. Kiểm tra logic ngày kết thúc không được trước ngày bắt đầu. Theo dõi trạng thái Chờ duyệt / Đã duyệt / Từ chối."),
        ("Giải trình công & Đăng ký OT", "Nhân viên, Quản lý", "Gửi giải trình bổ sung công khi quên quẹt thẻ. Đăng ký làm thêm ngoài giờ (OT thường, cuối tuần, ngày lễ) để quản lý phê duyệt và tính vào bảng lương."),
        ("Xin tạm ứng lương", "Nhân viên, Quản lý", "Nộp phiếu yêu cầu tạm ứng tiền lương hàng tháng kèm lý do chính đáng để quản lý xét duyệt trước khi chốt công."),
        ("Tải lên Bằng cấp & Giấy tờ scan", "Nhân viên, Quản lý, Admin", "Upload ảnh chụp / file scan chứng chỉ, bằng tốt nghiệp, CCCD scan vào hồ sơ cá nhân. Quản lý và HR có thể xem và tải về."),
        ("Đánh giá KPI cá nhân", "Nhân viên, Quản lý", "Nhân viên tự chấm điểm hiệu suất công việc theo kỳ đánh giá, viết tự nhận xét để quản lý xem xét chấm điểm chính thức."),
        ("Đăng ký Khóa đào tạo", "Tất cả các vai trò", "Xem danh sách các khóa đào tạo nội bộ do công ty tổ chức, nắm bắt chỉ tiêu, giảng viên, thời gian và bấm đăng ký tham gia."),
        ("Trợ lý AI Nhân sự nội bộ", "Tất cả các vai trò", "Chatbot AI hỗ trợ 24/7 giải đáp số ngày phép còn lại, hướng dẫn quy trình xin tạm ứng lương 4 bước, tóm tắt hồ sơ ứng viên tuyển dụng và gợi ý nhận xét KPI."),
        ("Dashboard Phòng ban & Biểu đồ", "Quản lý bộ phận", "Xem số liệu nhân sự trong phòng ban, tỷ lệ đi làm hôm nay, biểu đồ hình tròn cơ cấu chức vụ phòng và tình trạng điểm danh trong ngày."),
        ("Theo dõi & Chấm công nhanh", "Quản lý bộ phận", "Giám sát bảng công nhân viên trong phòng hôm nay, thực hiện nút 'Chấm công nhanh' tự động ghi nhận đúng giờ cho các nhân viên chưa quẹt thẻ."),
        ("Phê duyệt đơn từ phòng ban", "Quản lý bộ phận, Admin", "Duyệt hoặc từ chối các đơn nghỉ phép, đơn tăng ca OT, giải trình công và đơn xin tạm ứng lương của nhân viên cấp dưới trực tiếp."),
        ("Báo cáo & Thống kê nhân sự", "Quản lý bộ phận, Admin", "Xem tổng quan nhân sự, cơ cấu phòng ban, danh sách nhân viên và xuất toàn bộ dữ liệu ra tệp Excel (.CSV tương thích UTF-8 BOM)."),
        ("Dashboard Admin & Cảnh báo rủi ro", "Quản trị viên (Admin)", "Theo dõi toàn bộ chỉ số công ty, 2 biểu đồ hình tròn cơ cấu phòng ban và phân loại nhân sự, bảng cảnh báo thông minh các nhân viên có dấu hiệu nghỉ việc (Flight Risk Detector)."),
        ("Chốt công & Tính lương tự động", "Quản trị viên (Admin)", "Tự động quét toàn bộ bảng công, ngày nghỉ, giờ tăng ca, tạm ứng để tính toán ra bảng lương tháng chính xác 100%, tự tính tiền đóng BHXH và thuế TNCN."),
        ("Quản lý Hồ sơ, Hợp đồng & Tài khoản", "Quản trị viên (Admin)", "Thêm mới, sửa, xóa, tìm kiếm nhân viên (ảnh thẻ 3x4), hợp đồng lao động (kèm ảnh scan), cấp phát tài khoản và mật khẩu truy cập."),
        ("Sao lưu & Phục hồi CSDL", "Quản trị viên (Admin)", "Tải về bản sao lưu toàn bộ dữ liệu dưới dạng JSON Snapshot hoặc SQL Script chứa toàn bộ câu lệnh INSERT để phục hồi khi cần."),
        ("Nhật ký Hoạt động (Audit Log)", "Quản trị viên (Admin)", "Truy vết toàn bộ thao tác người dùng: ai đăng nhập, tạo mới, sửa đổi, xóa bản ghi nào, vào lúc mấy giờ và từ địa chỉ IP nào.")
    ]

    for item in func_list:
        row_cells = func_table.add_row().cells
        set_cell_background(row_cells[0], "F8FAFC")
        set_cell_background(row_cells[1], "FFFFFF")
        set_cell_background(row_cells[2], "FFFFFF")
        for i, text in enumerate(item):
            set_cell_margins(row_cells[i], top=70, bottom=70, left=100, right=100)
            p = row_cells[i].paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            if i == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ================= PHẦN 5 =================
    add_heading_1("PHẦN 5: CÁC TÍNH NĂNG MỚI ĐÃ ĐƯỢC BỔ SUNG & CẢI TIẾN ĐẶC SẮC")

    innovations = [
        ("1. Tái thiết kế Giao diện Chuẩn Premium SaaS (Linear, Notion, Stripe)",
         "Giao diện được nâng cấp toàn diện theo xu hướng thiết kế SaaS cao cấp năm 2026: trang đăng nhập chia đôi màn hình (Split screen) với gradient mesh lung linh, hiệu ứng kính mờ (glassmorphism), typography phông chữ Inter & Be Vietnam Pro sắc nét, bo góc lớn rounded-2xl (16-20px) và đổ bóng nổi khối tự nhiên."),

        ("2. Chuyển đổi Dark Mode / Light Mode Mượt mà",
         "Tích hợp nút chuyển đổi giao diện Sáng / Tối trên thanh Header. Hệ thống tự động lưu lựa chọn vào localStorage và áp dụng bảng màu tối ưu độ tương phản, giúp bảo vệ mắt khi làm việc ban đêm."),

        ("3. Phím tắt Command Palette (Ctrl + K) Tìm kiếm Tức thì",
         "Người dùng có thể bấm phím Ctrl + K bất kỳ lúc nào để mở cửa sổ tìm kiếm nhanh toàn hệ thống, hỗ trợ điều hướng tức thì tới bất kỳ phân hệ, bảng biểu, danh sách nhân viên hoặc chức năng nào chỉ trong vài phần nghìn giây."),

        ("4. Hệ thống Chấm đỏ Thông báo & Huy hiệu Xung nhịp (Red Dot / Badge)",
         "Thanh menu và chuông thông báo được tích hợp chấm đỏ xung nhịp (pulsing animation) tự động tính toán số đơn từ đang 'Chờ duyệt' (nghỉ phép, tăng ca, tạm ứng) hoặc thông báo mới ban hành, giúp người dùng không bao giờ bỏ lỡ công việc cần xử lý."),

        ("5. Biểu đồ Thống kê Hình tròn (Donut SVG Chart) Tương tác",
         "Trên Dashboard của Quản lý và Admin đã được bổ sung trực tiếp các biểu đồ hình tròn trực quan hiển thị tỷ trọng cơ cấu phòng ban, tình trạng chấm công và phân loại nhân sự. Biểu đồ có hiệu ứng xoay hoạt họa và hiển thị chi tiết số lượng cùng phần trăm (%)."),

        ("6. Chuẩn hóa Khung Ảnh thẻ Nhân viên Định dạng 3x4",
         "Tại danh sách nhân viên và hồ sơ, ảnh đại diện đã được chuẩn hóa theo tỷ lệ khung hình 3:4 chuẩn chân dung công vụ (kích thước 38x50px trên bảng và 105x140px trong modal), có nhãn chỉ báo 3x4 và hiệu ứng zoom nhẹ khi rê chuột."),

        ("7. Tính năng Tải tệp Scan Hợp đồng & Bằng cấp Giấy tờ",
         "Mô-đun Hợp đồng lao động và Bằng cấp cá nhân đã được bổ sung tính năng tải tệp ảnh scan hoặc nhập URL ảnh trực tuyến, lưu trữ an toàn trong thư mục static/uploads/ và hiển thị trực quan trong hồ sơ."),

        ("8. Cơ chế Tự động Dọn dẹp & Triệt tiêu Lỗi Lặp Bản ghi (clean_all_duplicates)",
         "Hệ thống trang bị giải pháp tự động rà soát và xóa sạch các bản ghi trùng lặp (trùng tên đăng nhập tài khoản, trùng ngày chấm công, trùng hợp đồng, trùng nhật ký) mỗi khi người dùng đăng nhập hoặc khi khởi động máy chủ, đảm bảo tính toàn vẹn dữ liệu."),

        ("9. Hiệu ứng Số đếm Tăng dần (Count-up Counter Animation)",
         "Toàn bộ con số thống kê trên Dashboard (tổng nhân viên, hợp đồng, phòng ban, chấm công) được tích hợp hiệu ứng số đếm chạy mượt mà theo hàm gia tốc easing tự nhiên, mang lại cảm giác sống động và chuyên nghiệp."),

        ("10. Trợ lý AI Hỏi đáp & Phân tích Nhân sự Thông minh",
         "Cửa sổ Trợ lý AI nổi ở góc phải màn hình sẵn sàng trả lời tự động các câu hỏi thường gặp: tra cứu số ngày phép còn lại, hướng dẫn quy trình xin tạm ứng lương 4 bước, phân tích hồ sơ ứng viên và gợi ý nội dung nhận xét KPI chuẩn chỉnh.")
    ]

    for title_inno, desc_inno in innovations:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        r_t = p.add_run(title_inno + "\n")
        r_t.font.bold = True
        r_t.font.size = Pt(11)
        r_t.font.color.rgb = RGBColor(79, 70, 229)
        r_d = p.add_run(desc_inno)
        r_d.font.size = Pt(10)
        r_d.font.color.rgb = RGBColor(51, 65, 85)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ================= PHẦN 6 =================
    add_heading_1("PHẦN 6: ĐỀ XUẤT CẢI TIẾN & ĐỊNH HƯỚNG PHÁT TRIỂN TƯƠNG LAI")

    p = doc.add_paragraph()
    p.add_run("Nhằm tiếp tục nâng cao giá trị sử dụng và mở rộng quy mô hệ thống đáp ứng nhu cầu của các doanh nghiệp lớn hàng nghìn nhân sự, nhóm phát triển xin đề xuất các định hướng nâng cấp trong các giai đoạn tiếp theo như sau:")

    proposals = [
        ("1. Chấm công Thông minh bằng Khuôn mặt (Face ID AI) & Định vị GPS:",
         "Tích hợp mô hình nhận diện khuôn mặt qua Camera Web/Mobile và xác thực vị trí địa lý (Geofencing GPS / Wi-Fi BSSID) để nhân viên làm việc tại văn phòng hoặc công trường có thể chấm công chính xác tuyệt đối mà không cần đầu tư máy quẹt vân tay đắt tiền."),

        ("2. Tự động hóa Chi trả Lương qua Cổng Ngân hàng (Open Banking / Napas):",
         "Kết nối API với các hệ thống ngân hàng (VietinBank, Vietcombank, MB Bank) hoặc cổng thanh toán Napas/VietQR để thực hiện chi lương tự động hàng loạt chỉ bằng 1 lệnh duyệt từ Ban Giám đốc."),

        ("3. Tích hợp Chữ ký số Điện tử (Digital Signature - PKI / OTP):",
         "Áp dụng quy chuẩn ký số điện tử theo Luật Giao dịch Điện tử cho Hợp đồng lao động và Quyết định bổ nhiệm/khen thưởng, giúp doanh nghiệp hoàn toàn không cần in ấn giấy tờ vật lý (Paperless Enterprise)."),

        ("4. Nâng cấp Trợ lý AI với Mô hình Ngôn ngữ Lớn (LLM RAG - Retrieval-Augmented Generation):",
         "Kết nối API Gemini Pro / OpenAI để huấn luyện mô hình học toàn bộ Sổ tay Nhân viên, Thỏa ước Lao động tập thể và Quy chế lương thưởng của riêng doanh nghiệp, cho phép AI giải đáp mọi chính sách phức tạp và hỗ trợ soạn thảo văn bản tự động."),

        ("5. Ứng dụng Di động Dành cho Nhân viên (Mobile App iOS & Android):",
         "Đóng gói phiên bản Progressive Web App (PWA) hoặc phát triển ứng dụng di động Flutter/React Native để nhân viên nhận thông báo đẩy tức thì (Push Notification) khi đơn được duyệt hoặc khi có bảng lương mới."),

        ("6. Đồng bộ Lịch làm việc với Google Calendar & Microsoft Outlook:",
         "Tự động đồng bộ lịch phỏng vấn tuyển dụng, lịch các khóa đào tạo nội bộ và ngày nghỉ phép của nhân viên vào ứng dụng lịch cá nhân của từng thành viên.")
    ]

    for p_title, p_desc in proposals:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        r_t = p.add_run(p_title + " ")
        r_t.font.bold = True
        r_t.font.size = Pt(10.5)
        r_t.font.color.rgb = RGBColor(30, 58, 138)
        r_d = p.add_run(p_desc)
        r_d.font.size = Pt(10)
        r_d.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(20)

    # Sign-off box
    sign_table = doc.add_table(rows=2, cols=2)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sign_c1 = sign_table.cell(0, 0)
    sign_c2 = sign_table.cell(0, 1)
    sign_c1.width = Inches(3.2)
    sign_c2.width = Inches(3.3)

    p_s1 = sign_c1.paragraphs[0]
    p_s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_s1.add_run("ĐẠI DIỆN ĐƠN VỊ TIẾP NHẬN\n")
    r.font.bold = True
    r.font.size = Pt(11)
    p_s1.add_run("(Ký, ghi rõ họ tên và đóng dấu)").italic = True

    p_s2 = sign_c2.paragraphs[0]
    p_s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_s2.add_run("ĐẠI DIỆN ĐỘI NGŨ PHÁT TRIỂN (NHÓM 2)\n")
    r.font.bold = True
    r.font.size = Pt(11)
    p_s2.add_run("(Ký, ghi rõ họ tên)").italic = True

    p_blank1 = sign_table.cell(1, 0).paragraphs[0]
    p_blank1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_blank1.add_run("\n\n\n...........................................................")

    p_blank2 = sign_table.cell(1, 1).paragraphs[0]
    p_blank2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_blank2.add_run("\n\n\n...........................................................")

    output_path = os.path.abspath("TAI_LIEU_BAN_GIAO_HE_THONG_QUAN_LY_NHAN_SU.docx")
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == '__main__':
    create_document()
