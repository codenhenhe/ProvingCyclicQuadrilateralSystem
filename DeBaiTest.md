# Bộ Test Case: Chứng Minh Tứ Giác Nội Tiếp

**Mục đích:** Kiểm thử hệ thống Neuro-Symbolic Geometry Solver.
**Tổng số bài:** 24 bài.
**Cấu trúc:** Phân loại theo 4 dấu hiệu nhận biết (Method) và 2 mức độ khó.

---

## 1. Phương pháp 1: Tổng hai góc đối bằng 180 độ

_Logic: $\angle A + \angle C = 180^\circ$ hoặc $\angle B + \angle D = 180^\circ$._

### Mức độ: Dễ (Easy)

**Bài 1.1**

> Cho tứ giác ABCD nội tiếp đường tròn (O). Biết $\angle A = 80^\circ$ và $\angle B = 70^\circ$. Tính số đo các góc C và D. (Đáp án mong đợi: $\angle C=100^\circ, \angle D=110^\circ$).
> _Nguồn tham khảo:_ SGK Toán 9.

**Bài 1.2**

> Cho hình thang cân ABCD ($AB // CD$). Chứng minh ABCD là tứ giác nội tiếp.
> _Nguồn tham khảo:_ VietJack (Toán 9 Cánh Diều).

**Bài 1.3**

> Cho tứ giác ABCD có $\angle A = 90^\circ$ và $\angle C = 90^\circ$. Chứng minh tứ giác ABCD nội tiếp đường tròn đường kính BD.
> _Nguồn tham khảo:_ TOANMATH.

### Mức độ: Trung bình (Medium)

**Bài 1.4**

> Cho tam giác ABC nhọn, các đường cao BD và CE cắt nhau tại H. Chứng minh tứ giác AEHD nội tiếp.
> _Gợi ý:_ $\angle AEH = 90^\circ, \angle ADH = 90^\circ$.

**Bài 1.5**

> Từ điểm A nằm ngoài đường tròn (O), kẻ hai tiếp tuyến AB, AC với đường tròn (B, C là tiếp điểm). Chứng minh tứ giác ABOC nội tiếp.
> _Gợi ý:_ Tính chất tiếp tuyến $\angle ABO = \angle ACO = 90^\circ$.

**Bài 1.6**

> Cho nửa đường tròn tâm O đường kính AB. Lấy điểm M thuộc nửa đường tròn. Kẻ $MH \perp AB$ tại H. Gọi I và K lần lượt là hình chiếu của H lên MA và MB. Chứng minh tứ giác MIHK nội tiếp.
> _Gợi ý:_ Tứ giác có 3 góc vuông.

---

## 2. Phương pháp 2: Hai đỉnh kề cùng nhìn cạnh

_Logic: Hai đỉnh kề nhau cùng nhìn cạnh chứa hai đỉnh còn lại dưới một góc bằng nhau._

### Mức độ: Dễ (Easy)

**Bài 2.1**

> Cho tam giác ABC có hai đường cao BD và CE. Chứng minh tứ giác BEDC nội tiếp.
> _Gợi ý:_ D và E cùng nhìn BC dưới góc $90^\circ$.

**Bài 2.2**

> Cho tứ giác ABCD có hai đường chéo AC và BD vuông góc với nhau tại I. Gọi M, N lần lượt là hình chiếu của I lên AB và BC. Chứng minh tứ giác BMIN nội tiếp.
> _Gợi ý:_ Góc $\angle IMB = 90^\circ, \angle INB = 90^\circ$.

**Bài 2.3**

> Cho tứ giác ABCD. Biết $\angle DAC = 60^\circ$ và $\angle DBC = 60^\circ$. Chứng minh ABCD nội tiếp.
> _Nguồn tham khảo:_ VietJack (Ví dụ minh họa định lý đảo).

### Mức độ: Trung bình (Medium)

**Bài 2.4**

> Cho tam giác ABC vuông tại A. Kẻ đường cao AH. Gọi E, F là hình chiếu của H lên AB, AC. Chứng minh tứ giác BEFC nội tiếp.
> _Gợi ý:_ Sử dụng tính chất bắc cầu qua góc trung gian hoặc nhìn cạnh (Cách nhìn cạnh phức tạp hơn cách tổng góc đối).

**Bài 2.5**

> Cho tam giác nhọn ABC. Vẽ đường tròn đường kính BC cắt AB, AC tại F và E. BF, CE cắt nhau tại H. Chứng minh tứ giác AEHF nội tiếp.
> _Nguồn tham khảo:_ Khan Academy.

**Bài 2.6**

> Cho tứ giác ABCD nội tiếp (O). Gọi E là giao điểm hai đường chéo. Biết $\angle DAC = \angle DBC$. Chứng minh ngược lại ABCD nội tiếp.
> _Gợi ý:_ Bài toán kiểm chứng logic định lý đảo.

---

## 3. Phương pháp 3: Góc ngoài bằng góc đối trong

_Logic: Góc ngoài tại một đỉnh bằng góc trong của đỉnh đối diện._

### Mức độ: Dễ (Easy)

**Bài 3.1**

> Cho tứ giác ABCD. Kéo dài cạnh AB về phía B đến điểm E. Biết $\angle CBE = 75^\circ$ và $\angle ADC = 75^\circ$. Chứng minh ABCD nội tiếp.
> _Nguồn tham khảo:_ Vuihoc.

**Bài 3.2**

> Cho tam giác ABC đều nội tiếp đường tròn (O). Điểm D nằm trên cung nhỏ BC. Chứng minh góc ngoài tại đỉnh D của tứ giác ABDC bằng $60^\circ$.
> _Nguồn tham khảo:_ SGK Toán 9.

**Bài 3.3**

> Cho hình bình hành ABCD. Đường tròn đi qua A, B, C cắt CD tại E. Chứng minh $AE = AD$.
> _Gợi ý:_ Sử dụng tính chất góc ngoài của tứ giác nội tiếp ABCE ($\angle AED = \angle B = \angle D$).

### Mức độ: Trung bình (Medium)

**Bài 3.4**

> Cho tam giác ABC vuông tại A, đường cao AH. Gọi E, F là hình chiếu của H lên AB, AC. Chứng minh $\angle AEF = \angle ACB$, từ đó suy ra tứ giác BEFC nội tiếp.
> _Gợi ý:_ Chứng minh góc ngoài bằng góc đối trong.

**Bài 3.5**

> Cho tứ giác ABCD nội tiếp. Gọi E là giao điểm của AB và CD (kéo dài). Chứng minh $\Delta EBC \sim \Delta EDA$.
> _Gợi ý:_ Sử dụng tính chất góc ngoài bằng góc đối trong để suy ra cặp góc bằng nhau.

**Bài 3.6**

> Cho tam giác ABC. Vẽ đường tròn tâm O đường kính BC cắt AB, AC tại D, E. Chứng minh tứ giác BDEC nội tiếp bằng cách so sánh góc $\angle ADE$ và $\angle ACB$.

---

## 4. Phương pháp 4: Bốn đỉnh cách đều (Tâm O)

_Logic: Tìm được điểm O sao cho $OA=OB=OC=OD$._

### Mức độ: Dễ (Easy)

**Bài 4.1**

> Chứng minh hình chữ nhật ABCD là tứ giác nội tiếp. Xác định tâm và bán kính nếu $AB=3, BC=4$.
> _Đáp án:_ Tâm là giao điểm 2 đường chéo, $R=2.5$.

**Bài 4.2**

> Chứng minh hình vuông MNPQ nội tiếp đường tròn tâm O (giao điểm hai đường chéo).
> _Nguồn tham khảo:_ Khan Academy.

**Bài 4.3**

> Cho tam giác ABC vuông tại A. Gọi M là trung điểm BC. Chứng minh A, B, C thuộc đường tròn tâm M.
> _Gợi ý:_ Trung tuyến ứng với cạnh huyền $MA=MB=MC$.

### Mức độ: Trung bình (Medium)

**Bài 4.4**

> Cho hình thang cân ABCD ($AB//CD, AB < CD$). Gọi I, K lần lượt là trung điểm của AB, CD. Chứng minh 4 điểm A, B, C, D cùng thuộc đường tròn có tâm nằm trên đường thẳng IK.
> _Nguồn tham khảo:_ Hoàng Hà Mobile (Bài tập SGK).

**Bài 4.5**

> Cho tam giác ABC cân tại A. Các đường trung trực của AB và AC cắt nhau tại O. Chứng minh A, B, C thuộc đường tròn tâm O.
> _Gợi ý:_ Tính chất giao điểm 3 đường trung trực.

**Bài 4.6**

> Cho hình thoi ABCD có góc $A=60^\circ$. Gọi E, F, G, H là trung điểm các cạnh AB, BC, CD, DA. Chứng minh E, F, G, H cùng thuộc một đường tròn.
> _Gợi ý:_ Chứng minh EFGH là hình chữ nhật, sau đó áp dụng bài 4.1.

---

## 📝 Hướng dẫn Test Hệ thống

1.  **Kiểm tra tính đúng đắn (Correctness):** Copy y nguyên đề bài vào hệ thống. Hệ thống phải giải ra "Success" và đưa ra đúng Method tương ứng.
2.  **Kiểm tra tính bền vững (Robustness):** Thử thay đổi câu chữ (VD: "Tam giác vuông" -> "Góc A bằng 90 độ").
3.  **Kiểm tra phát hiện lỗi (Error Handling):** Thử nhập các bài toán sai logic (VD: Hình thoi thường (không vuông) chứng minh nội tiếp) để xem hệ thống có báo `CONTRADICTION` hoặc `WARNING` không.
