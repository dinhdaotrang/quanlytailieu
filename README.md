# Hệ thống Phân loại Tài liệu - Trợ lý AI cấp điều hành

Hệ thống phân loại và quản lý tài liệu tự động sử dụng Streamlit và Python, chuyên phục vụ các lĩnh vực:
- Metro – đường sắt đô thị – TOD
- Đấu thầu – đầu tư – quy hoạch dự án
- Chung cư – nhà ở xã hội
- Pháp lý – kỹ thuật – tài chính dự án

## 🚀 Tính năng

### 1. Upload & Phân loại Tài liệu
- Đọc và xử lý file PDF, DOCX, TXT
- Phân loại tự động vào 5 nhóm:
  - 🔹 Metro/Đường sắt đô thị
  - 🔹 Đấu thầu/Khu giáo dục/TOD
  - 🔹 Chung cư
  - 🔹 Nhà ở xã hội
  - 🔹 Khác
- Phân tích và tạo tóm tắt điều hành
- Trích xuất từ khóa, tags, dự án, địa danh
- Đánh giá độ tin cậy và mức độ bảo mật
- Gợi ý hành động tiếp theo

### 2. Hỏi & Đáp (Q&A)
- Tìm kiếm thông tin trong tài liệu đã phân loại
- Hỗ trợ tìm kiếm theo nhóm hoặc tất cả nhóm
- Trả về câu trả lời kèm nguồn tham khảo

### 3. Quản lý Tài liệu
- Xem danh sách tài liệu theo từng nhóm
- Xóa tài liệu không cần thiết
- Thống kê số lượng tài liệu

## 📋 Yêu cầu

- Python 3.8 trở lên
- Các thư viện trong `requirements.txt`
- OpenAI API key (tùy chọn, để sử dụng tính năng AI nâng cao)

## 🛠️ Cài đặt

1. Clone hoặc tải project về máy

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. (Tùy chọn) Cấu hình OpenAI API key:
   - Cách 1: Sử dụng UI trong ứng dụng (khuyến nghị)
     - Chạy ứng dụng và vào phần "⚙️ Cấu hình OpenAI" trong sidebar
     - Nhập API key và click "💾 Lưu"
   
   - Cách 2: Sử dụng file .env
     - Copy file `.env.example` thành `.env`
     - Điền API key của bạn vào file `.env`
   
   - Cách 3: Sử dụng biến môi trường
     - Thiết lập biến môi trường `OPENAI_API_KEY`

   Lấy API key tại: https://platform.openai.com/api-keys

## ▶️ Chạy ứng dụng

Chạy lệnh sau để khởi động ứng dụng Streamlit:

```bash
streamlit run app.py
```

Ứng dụng sẽ tự động mở trong trình duyệt tại địa chỉ: `http://localhost:8501`

## 📁 Cấu trúc Thư mục

```
.
├── app.py                      # File chính của Streamlit app
├── document_reader.py          # Module đọc file PDF, DOCX, TXT
├── classifier.py               # Module phân loại tài liệu
├── analyzer.py                 # Module phân tích tài liệu
├── qa_system.py                # Module hệ thống Q&A
├── requirements.txt            # Danh sách thư viện cần thiết
├── README.md                   # File hướng dẫn
│
├── Metro_DuongSatDoThi/        # Thư mục lưu tài liệu Metro
├── DauThau_KhuGiaoDuc_TOD/     # Thư mục lưu tài liệu Đấu thầu
├── ChungCu/                    # Thư mục lưu tài liệu Chung cư
├── NhaO_XaHoi/                 # Thư mục lưu tài liệu Nhà ở xã hội
├── Khac/                       # Thư mục lưu tài liệu Khác
└── uploads/                    # Thư mục tạm cho file upload
```

## 💡 Hướng dẫn Sử dụng

### Upload và Phân loại Tài liệu

1. Chọn tab **"📤 Upload & Phân loại"**
2. Click **"Browse files"** và chọn file (PDF, DOCX, hoặc TXT)
3. Hệ thống sẽ tự động:
   - Đọc nội dung file
   - Phân loại vào nhóm phù hợp
   - Phân tích và tạo báo cáo chi tiết
4. Xem kết quả trong các tab:
   - **Kết quả Phân loại**: Nhóm chính, nhóm phụ, độ tin cậy
   - **Phân tích Chi tiết**: Tóm tắt, từ khóa, tags, gợi ý
   - **Nội dung**: Toàn bộ nội dung tài liệu
5. Click **"✅ Lưu vào nhóm"** để lưu file vào thư mục tương ứng

### Hỏi & Đáp

1. Chọn tab **"💬 Hỏi & Đáp"**
2. Chọn nhóm tài liệu cần tìm kiếm (hoặc "Tất cả các nhóm")
3. Nhập câu hỏi vào ô text
4. (Tùy chọn) Tick vào "Sử dụng OpenAI để trả lời chính xác hơn" nếu đã cấu hình API key
5. Click **"🔍 Tìm kiếm"**
6. Xem câu trả lời và nguồn tham khảo

**Lưu ý**: Với OpenAI, câu trả lời sẽ chính xác và chi tiết hơn, nhưng sẽ tốn phí API call.

### Quản lý Tài liệu

1. Chọn tab **"📁 Quản lý Tài liệu"**
2. Chọn nhóm tài liệu muốn xem
3. Xem danh sách tài liệu trong nhóm
4. Click **"🗑️ Xóa"** để xóa tài liệu không cần thiết

## 🔧 Nguyên tắc Phân loại

Hệ thống phân loại dựa trên:
- **Nội dung thực tế** của tài liệu (ưu tiên hơn tiêu đề)
- **Từ khóa** đặc trưng của mỗi nhóm
- **Tần suất xuất hiện** của từ khóa
- **Độ tin cậy** được đánh giá tự động

## ⚠️ Lưu ý

- Hệ thống phân loại dựa trên từ khóa, có thể cần điều chỉnh thủ công trong một số trường hợp
- File upload sẽ được lưu tạm trong thư mục `uploads/` trước khi được phân loại
- Đảm bảo có đủ dung lượng ổ cứng để lưu trữ tài liệu
- Với file PDF phức tạp, một số nội dung có thể không được trích xuất đầy đủ
- **OpenAI API**: Sử dụng API key của OpenAI sẽ tốn phí theo số lượng token sử dụng. Vui lòng kiểm tra giá tại https://openai.com/pricing
- API key được lưu trong file `config.json` (local) hoặc trong session state. File `config.json` đã được thêm vào `.gitignore` để bảo mật

## 📝 Ghi chú

- Hệ thống được thiết kế để hỗ trợ quản lý tài liệu nội bộ
- Có thể mở rộng bằng cách tích hợp AI/ML để cải thiện độ chính xác phân loại
- Hệ thống Q&A hiện tại sử dụng tìm kiếm đơn giản, có thể nâng cấp với vector embeddings

## 📄 License

Dự án này được phát triển để sử dụng nội bộ.

