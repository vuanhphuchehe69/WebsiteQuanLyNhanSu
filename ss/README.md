# Phần mềm quản lý nhân sự – Nhóm 2

Flask + Microsoft SQL Server (MSSQL), xây dựng theo phân tích nghiệp vụ và phân quyền đầy đủ cho 3 actors: **Nhân viên**, **Quản lý**, và **Admin**.

## Cấu trúc thư mục (Đã module hóa chuyên nghiệp)

```text
ss/
├── config.py              # Cấu hình app, kết nối MSSQL, 11 modules, options, menu, tone màu & icons
├── database.py            # Kết nối MSSQL qua pyodbc, DDL Schema và hàm khởi tạo/seed data (init_db)
├── utils.py               # Decorators (@login_required, @roles_required), CSRF guard, validate & parse form
│
├── routes/                # Các routes chia theo nghiệp vụ (Flask Blueprints)
│   ├── __init__.py        # Đăng ký các blueprints vào ứng dụng
│   ├── auth.py            # Đăng nhập, đăng xuất, đổi mật khẩu
│   ├── main.py            # Dashboard, hồ sơ (me), sửa profile, thông báo, xin nghỉ phép, báo cáo HR, backup dữ liệu
│   └── modules.py         # Quản lý CRUD chung (11 modules), phân trang, xuất Excel/CSV, duyệt đơn nghỉ phép
│
├── templates/             # Giao diện Jinja2 HTML tách rời
│   ├── base.html          # Khung layout tổng thể (Sidebar, Header, Flash Toast với nút đóng)
│   ├── login.html         # Màn hình đăng nhập
│   ├── dash.html          # Màn hình tổng quan / Dashboard với thao tác nhanh
│   ├── me.html            # Hồ sơ cá nhân, thông tin công việc, lịch sử chấm công, KPI, lương, nghỉ phép, hợp đồng
│   ├── profile_edit.html  # Form cập nhật thông tin cá nhân (SĐT, Email, Địa chỉ, Ngày sinh, Giới tính)
│   ├── announcements.html # Bảng tin xem thông báo nội bộ
│   ├── leave_request.html # Form gửi đơn xin nghỉ phép của nhân viên
│   ├── list.html          # Danh sách dữ liệu, phân trang (pagination), tìm kiếm, lọc trạng thái, duyệt đơn, xuất Excel/CSV
│   ├── form.html          # Form thêm mới / chỉnh sửa dữ liệu động
│   ├── report.html        # Chi tiết và tổng hợp nghỉ phép (hỗ trợ xuất CSV/Excel)
│   ├── report_hr.html     # Báo cáo nhân sự phòng ban / toàn công ty (thống kê giới tính, ngày công, KPI, xuất CSV)
│   ├── backup.html        # Trung tâm sao lưu & quản lý dữ liệu hệ thống cho Admin
│   ├── password.html      # Form đổi mật khẩu
│   └── msg.html           # Màn hình thông báo lỗi (403, 400)
│
├── static/                # Tài nguyên tĩnh
│   └── css/
│       └── style.css      # Toàn bộ CSS giao diện hiện đại, responsive
│
├── app.py                 # File thực thi chính của ứng dụng Flask
├── test_app.py            # Script kiểm thử tự động toàn bộ 26 kịch bản kiểm thử (PASS 100%)
├── requirements.txt       # Danh sách thư viện phụ thuộc (Flask, pyodbc)
└── README.md              # Tài liệu hướng dẫn
```

## Các tính năng hệ thống theo 3 Actors

### 1. Actor Nhân viên

- **Cập nhật thông tin cá nhân**: Cập nhật số điện thoại, email, địa chỉ liên hệ, ngày sinh, giới tính tại `/me/profile/edit`.
- **Xem thông tin công việc**: Xem chi tiết chức vụ, phòng ban trực thuộc, người quản lý trực tiếp, ngày vào công ty, loại hợp đồng và mức lương cơ bản hiện tại.
- **Xem lịch sử chấm công & ngày công**: Theo dõi chi tiết giờ vào, giờ ra, trạng thái chấm công (Đúng giờ, Đi muộn, Về sớm) và tổng số ngày công tích lũy trong tháng.
- **Xem thông báo nội bộ**: Đọc các thông báo từ Ban Giám Đốc, Phòng Nhân sự hoặc thông báo riêng của phòng ban tại `/announcements`.
- **Xem đánh giá hiệu suất & KPI**: Xem điểm số KPI, xếp loại và nhận xét đánh giá của quản lý theo từng tháng.
- **Quy trình xin nghỉ phép**: Tạo đơn xin nghỉ phép, tự động kiểm tra trùng lịch nghỉ, xem trạng thái (*Chờ duyệt*, *Đã duyệt*, *Từ chối*) và hủy đơn khi đang chờ duyệt.
- **Xem bảng lương, hợp đồng, tăng ca**: Lịch sử chi tiết bảng lương thực lĩnh, tăng ca và hợp đồng lao động.

### 2. Actor Quản lý

- **Theo dõi chấm công & tình hình đi làm**: Xem danh sách chấm công nhân viên phòng ban, tìm kiếm, lọc theo ngày/tháng, trạng thái đi làm tại `/m/chamcong`.
- **Chấm công nhanh hôm nay**: Nút thao tác nhanh tự động ghi nhận chấm công đúng giờ cho nhân viên chưa chấm công trong ngày.
- **Đánh giá hiệu suất làm việc (KPI)**: Đánh giá nhân viên theo tháng với thang điểm KPI (0 - 100), xếp loại (*Xuất sắc, Tốt, Khá, Trung bình, Yếu*) và ghi nhận xét tại `/m/danhgia`.
- **Lập báo cáo nhân sự phòng ban**: Xem và xuất file Excel/CSV báo cáo nhân sự phòng ban tại `/report/hr` gồm: tổng số lượng nhân sự, cơ cấu giới tính Nam/Nữ, tổng ngày công, giờ tăng ca, số ngày nghỉ phép và tỷ lệ đi làm đúng giờ.
- **Gửi thông báo cho nhân viên**: Đăng thông báo áp dụng cho toàn công ty hoặc theo phòng ban tại `/m/thongbao`.
- **Duyệt đơn nghỉ phép**: Phê duyệt hoặc từ chối đơn nghỉ phép của nhân viên trực tiếp trên danh sách `/m/nghiphep`.

### 3. Actor Admin

- **Quản lý chấm công toàn diện**: Xem, tạo mới, chỉnh sửa, xóa bản ghi chấm công và chấm công nhanh cho toàn thể nhân viên.
- **Thống kê & Báo cáo nhân sự**: Báo cáo tổng thể toàn công ty hoặc lọc chi tiết theo từng phòng ban, xuất file Excel/CSV.
- **Quản lý thông báo**: Quản lý toàn bộ thông báo hệ thống, tạo thông báo mới, chỉnh sửa hoặc xóa thông báo.
- **Sao lưu và quản lý dữ liệu**:
  - Xem thống kê số lượng bản ghi của tất cả 12 bảng trong cơ sở dữ liệu tại `/admin/backup`.
  - Tải bản sao lưu JSON toàn bộ hệ thống (`/admin/backup/export`) chỉ với 1 cú click.
  - Tải kịch bản SQL Script (`/admin/backup/sql`) chứa đầy đủ dữ liệu để phục hồi vào SQL Server.
- **Quản trị danh mục & tài khoản**: Quản lý phòng ban, chức vụ, tài khoản đăng nhập người dùng.

---

## Cấu hình Cơ sở dữ liệu thật (Microsoft SQL Server)

Mặc định hệ thống kết nối tới SQL Server cục bộ trên máy tính của bạn:

- **Server:** `.\SQLEXPRESS` (hoặc `localhost\SQLEXPRESS`)
- **Database:** `QLNhanSuNhom2` (tự động tạo database, bảng và di chuyển cột nếu chưa có)
- **Xác thực:** Windows Authentication (`Trusted_Connection=yes`)
- **Driver:** `ODBC Driver 18 for SQL Server`

*(Bạn có thể tùy chỉnh các thông số này trong file `config.py` nếu sử dụng tài khoản SQL Server hoặc máy chủ khác).*

## Chạy ứng dụng

```bash
pip install -r requirements.txt
py app.py          # mở http://127.0.0.1:5000
```

Chạy kiểm thử tự động toàn bộ 26 kịch bản:

```bash
py test_app.py
```

## Tài khoản mẫu

| Actor       | Đăng nhập với tư cách | Tên đăng nhập | Mật khẩu |
| ----------- | --------------------------- | ----------------- | ---------- |
| Admin       | Admin                       | admin             | admin123   |
| Quản lý   | Quản lý                   | ql001             | 123456     |
| Nhân viên | Nhân viên                 | nv002 … nv005    | 123456     |
