# 🚀 Bắt đầu với Pixelle-Video-dsfork

Chào mừng bạn đến với **Pixelle-Video-dsfork**! Đây là phiên bản được tuỳ biến đặc biệt để chạy với proxy AI cục bộ `ds2api` và xử lý hàng loạt kịch bản video với 30 tài khoản DeepSeek xoay vòng.

## 🛠 Yêu cầu hệ thống
1. **Docker & Docker Compose**: Để chạy được đồng thời web ui, api backend và ds2api.
2. **Tài khoản DeepSeek**: Chuẩn bị sẵn email và mật khẩu của các tài khoản DeepSeek để cấu hình.

## ⚙️ Các bước cài đặt nhanh

### Bước 1: Cấu hình tài khoản DeepSeek
Mở file `ds2api_config.json` nằm ở thư mục gốc của dự án. File này chứa danh sách 30 slot tài khoản.
Hãy điền `email` và `password` tài khoản DeepSeek của bạn vào các slot tương ứng:
```json
"accounts": [
  { "email": "your_email_1@example.com", "password": "your_password_1" },
  { "email": "your_email_2@example.com", "password": "your_password_2" },
  ...
]
```

### Bước 2: Chạy hệ thống bằng Docker Compose
Dự án đã được tích hợp sẵn file `docker-compose.yml` bao gồm 3 service: `init`, `ds2api`, `api`, và `web`.

Chạy lệnh sau tại thư mục gốc để khởi động toàn bộ:
```bash
docker-compose up -d --build
```

### Bước 3: Truy cập Giao diện Web
Sau khi các container đã khởi động thành công, hãy mở trình duyệt web và truy cập:
👉 **[http://localhost:8501](http://localhost:8501)**

Giao diện Web UI đã được thiết lập mặc định bằng Tiếng Việt. Bạn có thể sử dụng tab **Workspace** (Giao diện Tạo Video Hàng Loạt) để nhập vào 10-15 chủ đề mỗi lần. Hệ thống sẽ tự động chạy song song và luân phiên sử dụng 30 tài khoản DeepSeek của bạn một cách an toàn!
