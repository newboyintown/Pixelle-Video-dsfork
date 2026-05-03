# 👨‍💻 Hướng dẫn dành cho Lập trình viên (Developer Guide)

Tài liệu này giải thích các thay đổi về mặt kiến trúc và logic luồng dữ liệu (flow) của bản fork này so với bản gốc `Pixelle-Video`.

## 1. Kiến trúc hệ thống
Bản gốc của Pixelle-Video cho phép người dùng tùy chọn rất nhiều các Model AI khác nhau (OpenAI, Qwen, Ollama...) thông qua giao diện Settings của Streamlit.
Trong bản dsfork này, **toàn bộ tuỳ chọn LLM Provider đã bị loại bỏ**.
Hệ thống **chỉ kết nối duy nhất** đến `ds2api` thông qua mạng nội bộ của Docker (`http://ds2api:5001/v1`).
- File quản lý thay đổi: `pixelle_video/config/manager.py` (Hàm `get_llm_config` được hardcode giá trị).

## 2. Quản lý Concurrency (Chạy song song)
Để phục vụ yêu cầu khởi tạo 10 kịch bản cùng lúc trên một "Workspace", cơ chế batch generation truyền thống (xử lý tuần tự) đã được thay đổi.
- File quản lý thay đổi: `web/utils/batch_manager.py`
- Công nghệ sử dụng: Dùng `asyncio.gather` cùng `asyncio.Semaphore(10)` để cho phép đẩy đồng thời nhiều requests sang hệ thống tạo video.

## 3. Quản lý Session Chat của DeepSeek (50-Turn Defense)
DeepSeek sẽ chặn/giới hạn (Rate Limit/Context Limit) nếu một cuộc hội thoại (session) kéo dài quá lâu.
- **SessionLLMService**: Một class decorator được viết thêm tại `pixelle_video/services/session_llm_service.py` để bọc lấy `LLMService` gốc. Lớp này làm nhiệm vụ theo dõi lịch sử tin nhắn. Khi lịch sử đạt ngưỡng 50 lượt (max_turns), nó sẽ tự động kích hoạt tính năng **Tóm tắt (Summarize)**.
- Khi tóm tắt thành công, mảng `messages` sẽ được reset chỉ còn chứa tóm tắt của hệ thống, giúp LLM duy trì trí nhớ ngắn hạn an toàn.

## 4. Dọn dẹp Session (Clean up)
Việc sử dụng 30 accounts với hàng chục requests song song sẽ tạo ra lượng lớn session "rác" trên tài khoản DeepSeek.
Để ngăn chặn điều này, `auto_delete: {"mode": "none"}` được thiết lập trong `ds2api_config.json` để giữ session sống trong suốt quá trình tạo video (để phục vụ cho tính năng 50-turn defense).
Nhưng khi *toàn bộ tiến trình làm batch video hoàn tất*, một đoạn code dọn dẹp tại `web/utils/batch_manager.py` sẽ được kích hoạt. Nó tự động đọc file cấu hình `ds2api_config.json`, lặp qua cả 30 accounts, và gọi endpoint `/admin/accounts/sessions/delete-all` thông qua HTTP client để giải phóng bộ nhớ cho toàn bộ các accounts.

## 5. Dịch Thuật Tiếng Việt (i18n)
- Giao diện Web được dịch thông qua file `web/i18n/locales/vi_VN.json`.
- Ngôn ngữ hệ thống mặc định được đổi sang Tiếng Việt trong `web/i18n/__init__.py`.
