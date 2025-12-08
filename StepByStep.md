# 📘 TÀI LIỆU THIẾT KẾ: HỆ THỐNG GIẢI TOÁN HÌNH HỌC (GEOMETRY SOLVER)

## 🎯 Chiến lược tổng quan

**Hybrid Model = Rule-based + Graph Search**

Dưới đây là **lộ trình 5 giai đoạn phát triển hệ thống**, tập trung vào bài toán _chứng minh tứ giác nội tiếp_.

---

## 🟦 Giai đoạn 1: Biểu diễn Dữ liệu & Chuẩn hóa (Data Representation)

### 🎯 Mục tiêu

Xây dựng **"ngôn ngữ chung"** để máy tính hiểu các đối tượng hình học.

### 📝 Nhiệm vụ chính

- Định nghĩa các Class:  
  **Point, Segment, Line, Angle, Triangle, Quadrilateral**.
- **Cơ chế Canonical ID**  
  → đảm bảo tính duy nhất (ví dụ: đoạn thẳng AB và BA phải có cùng ID).
- Định nghĩa cấu trúc **Fact** (Sự kiện/Dữ kiện) để lưu trữ thông tin logic.

---

## 🟩 Giai đoạn 2: Xây dựng Knowledge Graph (Cơ sở tri thức)

### 🎯 Mục tiêu

Tạo bộ nhớ lưu trữ trạng thái bài toán dưới dạng **đồ thị quan hệ**.

### 📝 Nhiệm vụ chính

- Tích hợp thư viện đồ thị (ví dụ: `networkx`).
- **Quản lý Nút (Entity Node)**  
  → đại diện cho góc, cạnh, hoặc giá trị số.
- **Quản lý Cạnh (Relation Edge)**  
  → đại diện cho quan hệ bằng nhau, quan hệ tổng.
- Module quản lý các tính chất hình học khác:  
  **song song, vuông góc, thẳng hàng**.

---

## 🟨 Giai đoạn 3: Động cơ Suy diễn (Inference Engine)

### 🎯 Mục tiêu

Tự động sinh ra tri thức mới từ giả thiết ban đầu.

### 📝 Nhiệm vụ chính

- Xây dựng **vòng lặp suy diễn (Forward Chaining Loop)**.
- **Pattern Matching**  
  → tìm các đối tượng thỏa mãn điều kiện của một định lý.
- Quản lý **hàng đợi Facts mới** để tránh lặp vô hạn.

---

## 🟧 Giai đoạn 4: Thư viện Định lý (Rule Library)

### 🎯 Mục tiêu

Nạp kiến thức toán học vào hệ thống.

### 📝 Nhiệm vụ chính

- Nhóm định lý nền:  
  cộng góc, tính chất tam giác, quan hệ song song/vuông góc.
- Nhóm định lý đích (Goal Rules):  
  **4 phương pháp chứng minh tứ giác nội tiếp**.

---

## 🟥 Giai đoạn 5: Trích xuất & Giải thích Lời giải (Proof Extractor)

### 🎯 Mục tiêu

Chuyển đổi đường đi logic thành **văn bản tự nhiên**.

### 📝 Nhiệm vụ chính

- Sử dụng thuật toán tìm kiếm **BFS / Traceback** trên Knowledge Graph.
- **Truy vết từ Kết luận → Giả thiết**.
- Format văn bản đầu ra dạng **“Step-by-step”**.

---
