## 1. Đặt vấn đề
Trong bối cảnh giáo dục hiện đại, nhu cầu chuyển đổi số quy trình kiểm tra đánh giá ngày càng trở nên cấp thiết. Các phương pháp chấm thi thủ công truyền thống bộc lộ nhiều hạn chế về thời gian, nhân lực và tính khách quan. Trong khi đó, các giải pháp máy chấm thi OMR chuyên dụng thường có rào cản lớn về chi phí phần cứng, và các hệ thống số hóa chữ viết tay tiếng Việt vẫn còn hạn chế về độ chính xác.

Đề tài này tập trung xây dựng hệ thống **"Chấm điểm tự động tích hợp OMR và OCR chữ viết tay"**, cung cấp một giải pháp phần mềm toàn diện, chi phí thấp và dễ dàng tiếp cận thông qua nền tảng Web.

## 2. Mục tiêu đề tài
Hệ thống hướng tới hai mục tiêu kỹ thuật chính:

1.  **Module OMR (Optical Mark Recognition):** Tự động hóa quy trình chấm thi trắc nghiệm từ ảnh chụp camera, có khả năng xử lý biến dạng phối cảnh và điều kiện ánh sáng thay đổi.
2.  **Module OCR (Optical Character Recognition):** Số hóa nội dung bài làm tự luận hoặc phiếu thông tin viết tay, sử dụng các mô hình Học sâu tiên tiến để nhận dạng tiếng Việt chính xác.

## 3. Công nghệ sử dụng
* **Backend:** Sử dụng **FastAPI** (Python) với cơ chế xử lý bất đồng bộ (Asynchronous) và đa luồng (Threading) để phục vụ nhiều yêu cầu đồng thời.
* **Frontend:** Xây dựng trên thư viện **ReactJS** và **TypeScript**, cung cấp trải nghiệm người dùng tương tác cao.
* **Computer Vision:** Thư viện **OpenCV** và **NumPy** xử lý các thuật toán thị giác máy tính cổ điển.
* **AI Core:** Thư viện **VietOCR** (dựa trên PyTorch) triển khai các mô hình Transformer cho bài toán nhận dạng chuỗi ký tự.

## 4. Tổng quan luồng hoạt động
Quy trình nghiệp vụ của hệ thống được thiết kế tối ưu trải nghiệm người dùng thông qua các bước sau:

1.  **Xác thực:** Người dùng đăng ký tài khoản mới hoặc đăng nhập vào hệ thống.
2.  **Lựa chọn chức năng:** Tại màn hình chính, người dùng chọn một trong hai module: *"Chấm điểm bài viết tay"* hoặc *"Chấm điểm bài thi trắc nghiệm"*.
3.  **Nhập liệu:** Người dùng tải lên (upload) hình ảnh bài làm và nhập/chọn đáp án mẫu (Answer Key).
4.  **Xử lý và Trả kết quả:** Các mô hình AI/Computer Vision ở phía Backend xử lý hình ảnh và trả về kết quả chấm điểm chi tiết.

---

## 5. Xây dựng các chức năng chính

### 5.1. Chức năng "Chấm điểm bài viết tay"



Hệ thống áp dụng kiến trúc đa mô hình (**Multi-model Architecture**) để giải quyết bài toán phức tạp của chữ viết tay tiếng Việt và đánh giá ngữ nghĩa:

* **Phân loại đầu vào (Input Classification):** Ảnh các vùng câu hỏi/câu trả lời trước tiên được đưa qua một mô hình **CNN** (Convolutional Neural Network) nhẹ để phân loại là "Chữ in" (Printed) hay "Chữ viết tay" (Handwritten).
* **Nhận dạng quang học (OCR):** Dựa trên kết quả phân loại, hệ thống định tuyến ảnh đến mô hình **Transformer** tương ứng để tối ưu hóa độ chính xác nhận dạng.
* **Đánh giá ngữ nghĩa (Semantic Evaluation):** Văn bản sau khi được số hóa sẽ được đưa vào mô hình ngôn ngữ **BERT**. BERT thực hiện so sánh độ tương đồng ngữ nghĩa (**Semantic Similarity**) giữa câu trả lời của học sinh và đáp án mẫu, đưa ra điểm số chính xác dựa trên ý tứ thay vì chỉ khớp từ khóa.

### 5.2. Chức năng "Chấm điểm bài thi trắc nghiệm" (OMR)
Quy trình xử lý ảnh phiếu trắc nghiệm được thực hiện tuần tự qua 11 bước kỹ thuật:



1.  **Resize ảnh:** Đưa ảnh về chuẩn cố định $700 \times 700$ pixels để đảm bảo tính nhất quán.
2.  **Chuyển đổi Grayscale:** Chuyển sang ảnh xám để giảm khối lượng tính toán.
3.  **Khử nhiễu (Gaussian Blur):** Áp dụng bộ lọc $(5 \times 5)$ để làm mượt ảnh, hỗ trợ phát hiện biên.
4.  **Phát hiện biên (Edge Detection):** Sử dụng thuật toán `cv2.Canny` để tìm các đường viền.
5.  **Tìm Contours:** Trích xuất danh sách tất cả các đường viền khép kín.
6.  **Xác định vùng bài làm:** Lọc tìm hình chữ nhật lớn nhất (Khung trả lời) và lớn thứ hai (Khung điểm số).
7.  **Biến đổi phối cảnh (Warp Perspective):** Cắt và biến đổi hình học để đưa vùng bài làm về dạng phẳng (top-down view).
8.  **Phân ngưỡng (Thresholding):** Áp dụng *Binary Inverse*. Nền giấy chuyển thành Đen (0), vết bút chì chuyển thành Trắng (255).
9.  **Cắt lưới ô (Grid Splitting):** Chia ảnh thành lưới các ô nhỏ (Hàng = Câu hỏi, Cột = Lựa chọn).
10. **Xác định đáp án chọn:** Sử dụng `cv2.countNonZero` để đếm pixel trắng. Ô có chỉ số pixel lớn nhất (`np.amax`) trong một hàng là đáp án được chọn.
11. **Chấm điểm và Trực quan hóa:**
    * So sánh với **Answer Key** để tính điểm.
    * Vẽ vòng tròn xanh (đúng) hoặc đỏ (sai) đè lên ảnh gốc bằng phép biến đổi ngược (**Inverse Warp**) để hiển thị kết quả trực quan.
