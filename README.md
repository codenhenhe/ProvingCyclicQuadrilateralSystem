# Hệ thống Suy luận Giải toán Hình học Phẳng (Geometry Solver Inference System)

Đây là dự án Niên luận ngành Khoa học máy tính, xây dựng một hệ thống có khả năng tự động giải các bài toán hình học phẳng cơ bản bằng cách sử dụng phương pháp Đồ thị Tri thức (Knowledge Graph) và suy luận logic.

## Tính năng chính

- **Phân tích đề bài:** Tự động đọc và phân tích đề bài toán hình học được viết bằng ngôn ngữ tự nhiên (tiếng Việt).
- **Biểu diễn tri thức:** Dựng một Đồ thị Tri thức (Knowledge Graph) để biểu diễn các đối tượng và mối quan hệ hình học từ đề bài.
- **Lõi suy luận:** Áp dụng các định lý, tiên đề đã được mã hóa để làm giàu đồ thị tri thức và tìm ra các sự thật mới.
- **Chứng minh tự động:** Hỗ trợ chứng minh các dạng toán phổ biến:
  - Chứng minh hai tam giác đồng dạng.
  - Chứng minh một tứ giác nội tiếp đường tròn.
- **API Backend:** Cung cấp API endpoint thông qua FastAPI để nhận đề bài và trả về các bước giải chi tiết.

## 🛠️ Công nghệ sử dụng

- **Backend:** Python 3.11+, FastAPI
- **Lõi suy luận:** NetworkX
- **Xử lý ngôn ngữ (NLP):** (Ghi thư viện bạn dùng, ví dụ: Spacy, NLTK...)
- **Thiết kế Ontology:** Protégé (Xem file thiết kế tại `docs/geometry_ontology.owl`)
- **Web Server:** Uvicorn

## Cấu trúc Dự án

```
geometry_solver_project/
├── app/                  # Logic backend FastAPI
├── core_solver/          # Lõi suy luận giải toán (NLP & Inference)
├── docs/                 # Tài liệu, báo cáo, file ontology
├── tests/                # Kiểm thử tự động
├── .venv/                # Môi trường ảo
├── README.md             # File này
└── requirements.txt      # Các thư viện cần thiết
```

## 🚀 Hướng dẫn Cài đặt và Chạy thử

**Yêu cầu:** Python 3.10 trở lên.

**1. Clone repository:**

```bash
git clone [https://your-git-repository-url.git](https://your-git-repository-url.git)
cd geometry_solver_project
```

**2. Tạo và kích hoạt môi trường ảo:**

```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt (Windows)
.\.venv\Scripts\activate

# Kích hoạt (macOS/Linux)
source .venv/bin/activate
```

**3. Cài đặt các thư viện cần thiết:**

```bash
pip install -r requirements.txt
```

**4. Chạy ứng dụng backend:**

```bash
uvicorn app.main:app --reload
```

- `--reload`: Tự động khởi động lại server khi có thay đổi trong code.

**5. Truy cập ứng dụng:**

- Mở trình duyệt và truy cập: `http://127.0.0.1:8000`
- Để xem tài liệu API và thử nghiệm trực tiếp, truy cập: `http://127.0.0.1:8000/docs`

## 📝 Ví dụ API

Bạn có thể gửi một yêu cầu `POST` đến endpoint `/api/v1/solver/solve` với nội dung như sau:

**Request Body:**

```json
{
  "problem_description": "Cho tam giác ABC nhọn có hai đường cao BE, CF cắt nhau tại H. Chứng minh tứ giác AEHF nội tiếp."
}
```

**Response Body:**

```json
{
  "success": true,
  "steps": [
    "Bước 1: Xét tứ giác AEHF, ta có góc AEH = 90 độ (vì BE là đường cao).",
    "Bước 2: Ta lại có góc AFH = 90 độ (vì CF là đường cao).",
    "Bước 3: Suy ra góc AEH + góc AFH = 90 + 90 = 180 độ.",
    "Bước 4: Mà hai góc này ở vị trí đối nhau trong tứ giác AEHF.",
    "Kết luận: Vậy tứ giác AEHF nội tiếp đường tròn."
  ]
}
```
