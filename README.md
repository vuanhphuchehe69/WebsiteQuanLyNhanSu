1. Actor Nhân viên
Cập nhật thông tin cá nhân: Cập nhật số điện thoại, email, địa chỉ liên hệ, ngày sinh, giới tính tại /me/profile/edit.
Xem thông tin công việc: Xem chi tiết chức vụ, phòng ban trực thuộc, người quản lý trực tiếp, ngày vào công ty, loại hợp đồng và mức lương cơ bản hiện tại.
Xem lịch sử chấm công & ngày công: Theo dõi chi tiết giờ vào, giờ ra, trạng thái chấm công (Đúng giờ, Đi muộn, Về sớm) và tổng số ngày công tích lũy trong tháng.
Xem thông báo nội bộ: Đọc các thông báo từ Ban Giám Đốc, Phòng Nhân sự hoặc thông báo riêng của phòng ban tại /announcements.
Xem hồ sơ & Thông tin nhân sự: Xem thông tin phòng ban, hợp đồng và quá trình công tác.
Quy trình xin nghỉ phép: Tạo đơn xin nghỉ phép, tự động kiểm tra trùng lịch nghỉ, xem trạng thái (Chờ duyệt, Đã duyệt, Từ chối) và hủy đơn khi đang chờ duyệt.
Xem bảng lương, hợp đồng, tăng ca: Lịch sử chi tiết bảng lương thực lĩnh, tăng ca và hợp đồng lao động.
2. Actor Quản lý
Theo dõi chấm công & tình hình đi làm: Xem danh sách chấm công nhân viên phòng ban, tìm kiếm, lọc theo ngày/tháng, trạng thái đi làm tại /m/chamcong.
Chấm công nhanh hôm nay: Nút thao tác nhanh tự động ghi nhận chấm công đúng giờ cho nhân viên chưa chấm công trong ngày.
Báo cáo cơ cấu nhân sự phòng ban: Quản lý và theo dõi nhân sự thuộc phạm vi quản lý.
Lập báo cáo nhân sự phòng ban: Xem và xuất file Excel/CSV báo cáo nhân sự phòng ban tại /report/hr gồm: tổng số lượng nhân sự, cơ cấu giới tính Nam/Nữ, tổng ngày công, giờ tăng ca, số ngày nghỉ phép và tỷ lệ đi làm đúng giờ.
Gửi thông báo cho nhân viên: Đăng thông báo áp dụng cho toàn công ty hoặc theo phòng ban tại /m/thongbao.
Duyệt đơn nghỉ phép: Phê duyệt hoặc từ chối đơn nghỉ phép của nhân viên trực tiếp trên danh sách /m/nghiphep.
3. Actor Admin
Quản lý chấm công toàn diện: Xem, tạo mới, chỉnh sửa, xóa bản ghi chấm công và chấm công nhanh cho toàn thể nhân viên.
Thống kê & Báo cáo nhân sự: Báo cáo tổng thể toàn công ty hoặc lọc chi tiết theo từng phòng ban, xuất file Excel/CSV.
Quản lý thông báo: Quản lý toàn bộ thông báo hệ thống, tạo thông báo mới, chỉnh sửa hoặc xóa thông báo.
Sao lưu và quản lý dữ liệu:
Xem thống kê số lượng bản ghi của tất cả 12 bảng trong cơ sở dữ liệu tại /admin/backup.
Tải bản sao lưu JSON toàn bộ hệ thống (/admin/backup/export) chỉ với 1 cú click.
Tải kịch bản SQL Script (/admin/backup/sql) chứa đầy đủ dữ liệu để phục hồi vào SQL Server.
Quản trị danh mục & tài khoản: Quản lý phòng ban, chức vụ, tài khoản đăng nhập người dùng.
Cấu hình Cơ sở dữ liệu thật (Microsoft SQL Server)
Mặc định hệ thống kết nối tới SQL Server cục bộ trên máy tính của bạn:

Server: .\SQLEXPRESS (hoặc localhost\SQLEXPRESS)
Database: QLNhanSuNhom2 (tự động tạo database, bảng và di chuyển cột nếu chưa có)
Xác thực: Windows Authentication (Trusted_Connection=yes)
Driver: ODBC Driver 18 for SQL Server
(Bạn có thể tùy chỉnh các thông số này trong file config.py nếu sử dụng tài khoản SQL Server hoặc máy chủ khác).

Chạy ứng dụng
pip install -r requirements.txt
py seed_employees.py # Khởi tạo dữ liệu mẫu 13 nhân viên, 4 phòng ban
py app.py             # mở http://127.0.0.1:5000

Chạy kiểm thử tự động toàn bộ 57 kịch bản:
py test_app.py

Tài khoản mẫu
Actor        Đăng nhập với tư cách   Tên đăng nhập   Mật khẩu
Admin        Admin                   admin           admin123
Quản lý      Quản lý (Trưởng phòng)  nv001 (PB01), nv006 (PB02), nv007 (PB03), nv008 (PB04)   123456
Nhân viên    Nhân viên               nv002, nv003, nv004, nv005, nv009...nv013               123456
