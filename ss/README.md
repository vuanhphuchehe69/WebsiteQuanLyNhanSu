# Phần mềm quản lý nhân sự – Nhóm 9

Flask + Microsoft SQL Server (MSSQL), xây dựng theo phân tích trong báo cáo (8 module, 3 actor).

## Cấu trúc thư mục (Đã module hóa chuyên nghiệp)

```text
ss/
├── config.py              # Cấu hình app, kết nối Microsoft SQL Server, quyền actor, 8 module, menu
├── database.py            # Kết nối MSSQL qua pyodbc, DDL Schema và hàm khởi tạo CSDL/dữ liệu mẫu (init_db)
├── utils.py               # Decorators (@login_required, @roles_required), CSRF guard, validate & parse form
│
├── routes/                # Các routes chia theo nghiệp vụ (Flask Blueprints)
│   ├── __init__.py        # Đăng ký các blueprints vào ứng dụng
│   ├── auth.py            # Đăng nhập, đăng xuất, đổi mật khẩu
│   ├── main.py            # Bảng điều khiển (Dashboard), hồ sơ cá nhân (me), xin nghỉ phép, báo cáo nghỉ phép
│   └── modules.py         # Quản lý CRUD chung (Nhân viên, Hợp đồng, Lương, Nghỉ phép, Tăng ca...), phân trang, xuất Excel/CSV, duyệt đơn
│
├── templates/             # Giao diện Jinja2 HTML tách rời
│   ├── base.html          # Khung layout tổng thể (Sidebar, Header, Flash Toast)
│   ├── login.html         # Màn hình đăng nhập
│   ├── dash.html          # Màn hình tổng quan / Dashboard
│   ├── me.html            # Thông tin cá nhân, lịch sử hợp đồng, lương, nghỉ phép, tăng ca
│   ├── leave_request.html # Form gửi đơn xin nghỉ phép của nhân viên
│   ├── list.html          # Danh sách dữ liệu, phân trang (pagination), tìm kiếm, lọc trạng thái, duyệt đơn, xuất Excel/CSV
│   ├── form.html          # Form thêm mới / chỉnh sửa dữ liệu động
│   ├── report.html        # Chi tiết và tổng hợp nghỉ phép (hỗ trợ xuất CSV/Excel)
│   ├── password.html      # Form đổi mật khẩu
│   └── msg.html           # Màn hình thông báo lỗi (403, 400)
│
├── static/                # Tài nguyên tĩnh
│   └── css/
│       └── style.css      # Toàn bộ CSS giao diện hiện đại, responsive
│
├── app.py                 # File thực thi chính của ứng dụng Flask
├── test_app.py            # Script kiểm thử tự động toàn bộ tính năng và phân quyền (16 test cases)
├── requirements.txt       # Danh sách thư viện phụ thuộc (Flask, pyodbc)
└── README.md              # Tài liệu hướng dẫn
```

## Các tính năng mới bổ sung
1. **Phân trang dữ liệu (Pagination)**:
   - Các danh sách dữ liệu (Nhân viên, Hợp đồng, Bảng lương, Nghỉ phép, Tăng ca...) tự động chia trang (10 bản ghi/trang), kèm thanh chuyển trang, số trang hiện tại và tổng số bản ghi.
2. **Xuất file Excel / CSV**:
   - Nút **"Xuất Excel/CSV"** ở đầu mỗi trang danh mục và trang báo cáo nghỉ phép.
   - Định dạng CSV có UTF-8 BOM (`\ufeff`) hiển thị tiếng Việt có dấu chuẩn xác 100% khi mở trực tiếp bằng Microsoft Excel.
3. **Quy trình Quản lý Nghỉ phép (Workflow Đơn nghỉ phép)**:
   - **Actor Nhân viên**:
     - Vào trang **Thông tin cá nhân (`/me`)**, bấm **"Xin nghỉ phép"** để tạo đơn với ngày bắt đầu, ngày kết thúc và lý do.
     - Kiểm tra tính hợp lệ: ngày kết thúc $\ge$ ngày bắt đầu, ngăn chặn đăng ký trùng lịch nghỉ.
     - Đơn tạo mới có trạng thái **"Chờ duyệt"**. Nhân viên có thể bấm **"Hủy đơn"** khi đang chờ duyệt.
   - **Actor Quản lý / Admin**:
     - Vào trang **Nghỉ phép (`/m/nghiphep`)**: Lọc theo trạng thái (*Chờ duyệt*, *Đã duyệt*, *Từ chối*).
     - Với mỗi đơn "Chờ duyệt", có nút thao tác nhanh **"Duyệt"** (Xanh) và **"Từ chối"** (Đỏ) ngay trên bảng mà không cần vào form sửa.
     - Bảng điều khiển (Dashboard) tự động hiển thị số lượng **"Đơn nghỉ chờ duyệt"** để Quản lý nắm bắt ngay khi đăng nhập.

## Cấu hình Cơ sở dữ liệu thật (Microsoft SQL Server)
Mặc định hệ thống kết nối tới SQL Server cục bộ trên máy tính của bạn:
- **Server:** `.\SQLEXPRESS` (hoặc `localhost\SQLEXPRESS`)
- **Database:** `QLNhanSu_Nhom9` (tự động tạo database, bảng và di chuyển cột nếu chưa có)
- **Xác thực:** Windows Authentication (`Trusted_Connection=yes`)
- **Driver:** `ODBC Driver 18 for SQL Server`

*(Bạn có thể tùy chỉnh các thông số này trong file `config.py` nếu sử dụng tài khoản SQL Server hoặc máy chủ khác).*

## Chạy ứng dụng
```bash
pip install -r requirements.txt
py app.py          # mở http://127.0.0.1:5000
```

Chạy kiểm thử tự động:
```bash
py test_app.py
```

## Tài khoản mẫu
| Actor | Đăng nhập với tư cách | Tên đăng nhập | Mật khẩu |
|---|---|---|---|
| Admin | Admin | admin | admin123 |
| Quản lý | Quản lý | ql001 | 123456 |
| Nhân viên | Nhân viên | nv002 … nv005 | 123456 |

## Phân quyền (theo use case trong báo cáo)
| Chức năng | Nhân viên | Quản lý | Admin |
|---|---|---|---|
| Đăng nhập / Đăng xuất / Đổi mật khẩu | ✔ | ✔ | ✔ |
| Xem hồ sơ cá nhân, lịch sử lương, hợp đồng, tăng ca | ✔ | ✔ | – |
| Gửi đơn xin nghỉ phép / Hủy đơn chờ duyệt | ✔ | ✔ | – |
| Xem danh sách đơn nghỉ phép, Duyệt / Từ chối đơn | – | ✔ | ✔ |
| Nhân viên, Hợp đồng, Lương, Tăng ca: xem, tìm kiếm, xuất file, CRUD | – | ✔ | ✔ |
| Xem và xuất chi tiết báo cáo nghỉ phép theo tháng | – | ✔ | ✔ |
| Phòng ban, Chức vụ, Tài khoản: xem, tìm kiếm, xuất file, CRUD | – | – | ✔ |
