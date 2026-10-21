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
│   ├── main.py            # Bảng điều khiển (Dashboard), hồ sơ cá nhân (me), báo cáo nghỉ phép
│   └── modules.py         # Quản lý CRUD chung (Nhân viên, Hợp đồng, Lương, Nghỉ phép, Tăng ca, Phòng ban, Chức vụ, Tài khoản)
│
├── templates/             # Giao diện Jinja2 HTML tách rời
│   ├── base.html          # Khung layout tổng thể (Sidebar, Header, Flash Toast)
│   ├── login.html         # Màn hình đăng nhập
│   ├── dash.html          # Màn hình tổng quan / Dashboard
│   ├── me.html            # Thông tin cá nhân, lịch sử hợp đồng, lương, nghỉ phép, tăng ca
│   ├── list.html          # Danh sách dữ liệu, tìm kiếm, lọc theo tháng, sắp xếp
│   ├── form.html          # Form thêm mới / chỉnh sửa dữ liệu động
│   ├── report.html        # Chi tiết và tổng hợp nghỉ phép
│   ├── password.html      # Form đổi mật khẩu
│   └── msg.html           # Màn hình thông báo lỗi (403, 400)
│
├── static/                # Tài nguyên tĩnh
│   └── css/
│       └── style.css      # Toàn bộ CSS giao diện hiện đại, responsive
│
├── app.py                 # File thực thi chính của ứng dụng Flask
├── test_app.py            # Script kiểm thử tự động toàn bộ tính năng và phân quyền
├── requirements.txt       # Danh sách thư viện phụ thuộc (Flask, pyodbc)
└── README.md              # Tài liệu hướng dẫn
```

## Cấu hình Cơ sở dữ liệu thật (Microsoft SQL Server)
Mặc định hệ thống kết nối tới SQL Server cục bộ trên máy tính của bạn:
- **Server:** `.\SQLEXPRESS` (hoặc `localhost\SQLEXPRESS`)
- **Database:** `QLNhanSu_Nhom9` (tự động tạo database và bảng nếu chưa có)
- **Xác thực:** Windows Authentication (`Trusted_Connection=yes`)
- **Driver:** `ODBC Driver 18 for SQL Server`

*(Bạn có thể tùy chỉnh các thông số này trong file `config.py` nếu sử dụng tài khoản SQL Server hoặc máy chủ khác).*

## Chạy ứng dụng
```bash
pip install -r requirements.txt
python app.py          # mở http://127.0.0.1:5000
```

Chạy kiểm thử tự động:
```bash
python test_app.py
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
| Đăng nhập / Đăng xuất / Đổi mật khẩu / Tải lại | ✔ | ✔ | ✔ |
| Xem thông tin cá nhân (kèm hợp đồng, lương, nghỉ phép, tăng ca của mình) | ✔ | ✔ | – |
| Nhân viên, Hợp đồng, Lương, Nghỉ phép, Tăng ca: xem, tìm kiếm, thêm, sửa, xóa | – | ✔ | ✔ |
| Xem chi tiết nghỉ phép theo tháng | – | ✔ | ✔ |
| Phòng ban, Chức vụ, Tài khoản: xem, tìm kiếm, thêm, sửa, xóa | – | – | ✔ |

Phân quyền được kiểm tra ở server cho mọi route (trả 403 nếu sai quyền), có CSRF token,
mật khẩu băm bằng werkzeug, truy vấn dùng tham số hóa chống SQL Injection.
