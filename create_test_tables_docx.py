import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

doc = docx.Document()

# Set standard A4 page layout
for section in doc.sections:
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.79)
    section.bottom_margin = Inches(0.79)
    section.left_margin = Inches(0.79)
    section.right_margin = Inches(0.79)

# Default font Times New Roman
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(11)
font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

def set_cell_background(cell, fill_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="B0C4DE", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_header(title, level=1):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    run = h.add_run(title)
    run.font.name = 'Times New Roman'
    run.bold = True
    if level == 1:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    elif level == 2:
        run.font.size = Pt(12.5)
        run.font.color.rgb = RGBColor(0x0F, 0x4C, 0x81)
    else:
        run.font.size = Pt(11.5)
        run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    return h

def add_caption(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.bold = True
    run.italic = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    return p

def create_styled_table(headers, data, col_widths, table_caption):
    add_caption(table_caption)
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="CBD5E1", sz="4")
    
    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        cell = hdr_cells[i]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    # Data Rows
    for r_idx, row_data in enumerate(data):
        row_cells = table.rows[r_idx + 1].cells
        bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row_cells[c_idx]
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            
            # Text alignment
            if c_idx == 0 or c_idx == len(row_data) - 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                
            run = p.add_run(val)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            
            if c_idx == 0:
                run.bold = True
            elif c_idx == len(row_data) - 1:
                run.bold = True
                run.font.color.rgb = RGBColor(0x16, 0x65, 0x34)  # Green for PASS / ĐẠT
    
    # Set widths
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = Inches(w)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    return table

# ----------------- DOCUMENT CONTENT -----------------

# Main Header
p_title = doc.add_paragraph()
p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_t = p_title.add_run("BÁO CÁO KẾT QUẢ KIỂM THỬ HỆ THỐNG")
run_t.font.name = 'Times New Roman'
run_t.font.size = Pt(16)
run_t.bold = True
run_t.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

p_sub = doc.add_paragraph()
p_sub.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sub.paragraph_format.space_after = Pt(14)
run_s = p_sub.add_run("Mục 3.2.5: Kiểm thử hệ thống | Đề tài: Xây dựng hệ thống Quản lý nhân sự - Nhóm 2")
run_s.font.name = 'Times New Roman'
run_s.font.size = Pt(11)
run_s.italic = True
run_s.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

add_header("3.2.5.3. Kịch bản kiểm thử theo 3 tác nhân (Nhân viên, Quản lý, Admin)", level=1)

# TABLE 1: NHÂN VIÊN
add_header("A. Kịch bản kiểm thử dành cho Nhân viên (Employee)", level=2)
headers_nv = ["Mã Kịch bản", "Tên chức năng kiểm thử", "Các bước thực hiện & Dữ liệu nhập", "Kết quả kỳ vọng", "Đánh giá"]
col_widths_nv = [0.95, 1.45, 2.3, 1.5, 0.6]
data_nv = [
    [
        "TC_NV01",
        "Cập nhật hồ sơ cá nhân",
        "1. Đăng nhập tài khoản nv002\n2. Vào trang /me -> Bấm 'Cập nhật hồ sơ'\n3. Đổi SĐT: 0901000002, Địa chỉ: Hà Nội\n4. Bấm 'Lưu thông tin'",
        "Dữ liệu cập nhật vào CSDL, thông báo thành công; Mã NV và Họ tên bị khóa cố định.",
        "ĐẠT"
    ],
    [
        "TC_NV02",
        "Đổi ảnh đại diện 3x4",
        "1. Tại trang cá nhân, bấm icon 'Đổi ảnh'\n2. Chọn tệp ảnh JPG/PNG/SVG chuẩn 3x4\n3. Bấm xác nhận lưu",
        "Ảnh đại diện cập nhật ngay lập tức theo đúng khung hình 3x4 tiêu chuẩn.",
        "ĐẠT"
    ],
    [
        "TC_NV03",
        "Chấm công trực tuyến\n(Check-in / Check-out)",
        "1. Tại trang cá nhân, bấm 'Check-in vào ca' lúc 08:15\n2. Cuối ngày, bấm 'Check-out ra ca'",
        "Ghi nhận giờ vào thực tế, nhãn 'Đúng giờ'; tự động tính tổng số giờ làm việc trong ngày.",
        "ĐẠT"
    ],
    [
        "TC_NV04",
        "Tải lên Bằng cấp, Giấy tờ chứng chỉ",
        "1. Cuộn đến 'Bằng cấp & Giấy tờ' -> Bấm 'Thêm mới'\n2. Nhập: Chứng chỉ AWS Cloud, Nơi cấp: Amazon, Ngày cấp: 15/05/2026\n3. Bấm 'Lưu dữ liệu'",
        "Bằng cấp xuất hiện ngay trong danh mục hồ sơ năng lực cá nhân của nhân viên.",
        "ĐẠT"
    ],
    [
        "TC_NV05",
        "Bắt lỗi ngày khi nộp đơn nghỉ phép",
        "1. Bấm 'Xin nghỉ phép'\n2. Chọn Từ ngày: 22/11/2026, Đến ngày: 20/11/2026 (Ngày kết thúc < Ngày bắt đầu)\n3. Bấm 'Gửi đơn xin nghỉ'",
        "Hệ thống chặn gửi, báo lỗi đỏ: 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu'.",
        "ĐẠT"
    ],
    [
        "TC_NV06",
        "Nộp đơn xin nghỉ phép hợp lệ",
        "1. Chọn Từ ngày: 20/11/2026, Đến ngày: 22/11/2026\n2. Nhập lý do: 'Việc gia đình'\n3. Bấm 'Gửi đơn xin nghỉ'",
        "Tạo đơn thành công với trạng thái 'Chờ duyệt', tự động chuyển đến hàng đợi của Quản lý.",
        "ĐẠT"
    ],
    [
        "TC_NV07",
        "Đăng ký làm thêm giờ (OT) & Giải trình công",
        "1. Bấm 'Đăng ký OT' -> Chọn ngày, số giờ: 3.0h, loại ngày thường (x1.5)\n2. Nhập nội dung: 'Fix lỗi bảo mật hệ thống'\n3. Bấm 'Gửi đăng ký'",
        "Gửi yêu cầu thành công, lưu vào bảng TangCa với trạng thái 'Chờ duyệt'.",
        "ĐẠT"
    ]
]
create_styled_table(headers_nv, data_nv, col_widths_nv, "Bảng 3.2. Kịch bản kiểm thử chức năng dành cho Nhân viên (Employee)")

# TABLE 2: QUẢN LÝ
add_header("B. Kịch bản kiểm thử dành cho Người quản lý (Manager)", level=2)
headers_ql = ["Mã Kịch bản", "Tên chức năng kiểm thử", "Các bước thực hiện & Dữ liệu nhập", "Kết quả kỳ vọng", "Đánh giá"]
col_widths_ql = [0.95, 1.45, 2.3, 1.5, 0.6]
data_ql = [
    [
        "TC_QL01",
        "Giám sát Dashboard phòng ban",
        "1. Đăng nhập tài khoản ql001\n2. Quan sát số liệu nhân sự, tỷ lệ có mặt, đơn chờ duyệt trên trang chủ quản lý",
        "Hiển thị chính xác số liệu phòng ban phụ trách (3 nhân sự); không bị lộ dữ liệu phòng ban khác.",
        "ĐẠT"
    ],
    [
        "TC_QL02",
        "Trung tâm Phê duyệt tập trung (Approval Hub)",
        "1. Truy cập /manager/approvals\n2. Xem chi tiết đơn nghỉ phép của NV002\n3. Bấm nút 'Phê duyệt' (hoặc 'Từ chối')",
        "Trạng thái đơn đổi thành 'Đã duyệt' (hoặc 'Từ chối'); đồng bộ tự động vào số ngày phép năm của nhân sự.",
        "ĐẠT"
    ],
    [
        "TC_QL03",
        "Chấm công nhanh cho phòng ban",
        "1. Truy cập mục Chấm công\n2. Bấm nút 'Chấm công nhanh hôm nay'\n3. Xác nhận thao tác",
        "Toàn bộ nhân sự thuộc quyền quản lý chưa quẹt thẻ được ghi nhận có mặt đúng giờ trong ngày.",
        "ĐẠT"
    ],
    [
        "TC_QL04",
        "Đề xuất nhân sự gửi lên Admin",
        "1. Vào menu 'Đề xuất & Khiếu nại'\n2. Chọn nhân viên NV005, loại: Khen thưởng (Thưởng 2.000.000 VNĐ)\n3. Bấm 'Gửi đến Ban Quản lý'",
        "Khởi tạo đề xuất thành công với trạng thái 'Chờ HR/Admin phê duyệt'.",
        "ĐẠT"
    ],
    [
        "TC_QL05",
        "Xuất Báo cáo Nhân sự phòng ban",
        "1. Truy cập trang Báo cáo nhân sự (/report/hr)\n2. Chọn kỳ tháng 11/2026\n3. Bấm nút 'Xuất Excel/CSV'",
        "Tải xuống tệp tin CSV chứa dữ liệu nhân sự phòng ban, mở bằng Excel hiển thị đúng chuẩn tiếng Việt UTF-8.",
        "ĐẠT"
    ]
]
create_styled_table(headers_ql, data_ql, col_widths_ql, "Bảng 3.3. Kịch bản kiểm thử chức năng dành cho Người quản lý (Manager)")

# TABLE 3: ADMIN
add_header("C. Kịch bản kiểm thử dành cho Quản trị viên (Admin)", level=2)
headers_ad = ["Mã Kịch bản", "Tên chức năng kiểm thử", "Các bước thực hiện & Dữ liệu nhập", "Kết quả kỳ vọng", "Đánh giá"]
col_widths_ad = [0.95, 1.45, 2.3, 1.5, 0.6]
data_ad = [
    [
        "TC_AD01",
        "Tổng quan điều hành & Cảnh báo Flight Risk",
        "1. Đăng nhập tài khoản admin\n2. Kiểm tra chỉ số tổng nhân sự (13), quỹ lương\n3. Kiểm tra thẻ cảnh báo nguy cơ nghỉ việc",
        "Hệ thống phát hiện và hiển thị các nhân sự có nguy cơ thôi việc (đi muộn tăng, lâu chưa tăng lương).",
        "ĐẠT"
    ],
    [
        "TC_AD02",
        "Biểu đồ Phân tích Tài chính - Nhân sự",
        "1. Vào Báo cáo Phân tích Nhân sự & Tài chính\n2. Kiểm tra Biểu đồ tròn tỷ lệ giữ chân, Biểu đồ cột chi phí lương các tháng",
        "Trực quan hóa chính xác tỷ lệ giữ chân 92.9%, thời gian tuyển 18.5 ngày, quỹ lương dao động 253M - 277M.",
        "ĐẠT"
    ],
    [
        "TC_AD03",
        "Quản lý Tài khoản & Phân quyền",
        "1. Truy cập danh mục Tài khoản (/m/taikhoan)\n2. Kiểm tra danh sách 15 tài khoản\n3. Thử tạo mới hoặc phân lại vai trò truy cập",
        "Hiển thị danh sách đầy đủ, phân đúng 3 vai trò (Admin, Quản lý, Nhân viên), không phát sinh lỗi 500.",
        "ĐẠT"
    ],
    [
        "TC_AD04",
        "Chốt công & Tính bảng lương tự động",
        "1. Chọn kỳ lương Tháng 11/2026\n2. Bấm 'Chốt công tháng'\n3. Bấm nút '⚡ Tính bảng lương tự động'",
        "Hệ thống tự động quét công, OT, tính BHXH (10.5%), Thuế và ra Lương thực lĩnh chính xác 100%, không sai số.",
        "ĐẠT"
    ],
    [
        "TC_AD05",
        "Giám sát Nhật ký hoạt động (Audit Log)",
        "1. Mở menu 'Nhật ký Hoạt động (Audit Log)'\n2. Tra cứu 200 sự kiện gần nhất",
        "Ghi vết đầy đủ mọi thao tác đăng nhập, đăng xuất, phê duyệt, sửa hồ sơ kèm mốc thời gian và địa chỉ IP 127.0.0.1.",
        "ĐẠT"
    ],
    [
        "TC_AD06",
        "Trung tâm Sao lưu CSDL (Backup Center)",
        "1. Truy cập chức năng Sao lưu dữ liệu\n2. Bấm 'Tải bản sao lưu JSON'\n3. Bấm 'Tải bản sao lưu SQL'",
        "Tải về thành công tệp sao lưu JSON snapshot và tệp kịch bản T-SQL đầy đủ cấu trúc và dữ liệu bảng.",
        "ĐẠT"
    ]
]
create_styled_table(headers_ad, data_ad, col_widths_ad, "Bảng 3.4. Kịch bản kiểm thử chức năng dành cho Quản trị viên (Admin)")

# Save documents to both locations
out_path_1 = r"c:\Users\DELL\Downloads\WebsiteQuanLyNhanSu\3_Bang_Kich_Ban_Kiem_Thu.docx"
out_path_2 = r"c:\Users\DELL\Downloads\WebsiteQuanLyNhanSu\WebsiteQuanLyNhanSu\3_Bang_Kich_Ban_Kiem_Thu.docx"

doc.save(out_path_1)
doc.save(out_path_2)

print(f"Successfully generated DOCX files:")
print(f"1. {out_path_1} ({os.path.getsize(out_path_1)} bytes)")
print(f"2. {out_path_2} ({os.path.getsize(out_path_2)} bytes)")
