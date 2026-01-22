import TopMenu from "../UI_Components/TopMenu";
import { useState } from "react";
import "../UI_Components/HandwrittenQuestionPage.css"; // Tận dụng CSS cũ
import ImagePreviewList from "../UI_Components/ImagePreviewList";
import ImageUploader from "../UI_Components/ImageUploader.tsx";
import UploadPopup from "../UI_Components/UploadPopup.tsx";
import ViewImageModal from "../UI_Components/ViewImageModal.tsx";

export default function MultichoicePage() {
    // --- STATE QUẢN LÝ ẢNH ---
    // OMR chỉ cần 1 ảnh phiếu trả lời của thí sinh
    const [omrFile, setOmrFile] = useState<File | null>(null);
    const [omrImagePreview, setOmrImagePreview] = useState<string | null>(null);

    // --- STATE CẤU HÌNH CHẤM ---
    const [answerKey, setAnswerKey] = useState<string>("1,2,0,1,4"); // Mặc định ví dụ
    const [numQuestions, setNumQuestions] = useState<number>(5);

    // --- STATE KẾT QUẢ ---
    const [serverResult, setServerResult] = useState<any>(null);
    const [resultImageUrl, setResultImageUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);

    // State Popup
    const [showPopup, setShowPopup] = useState<boolean>(false);
    const [viewImage, setViewImage] = useState<string | null>(null);

    // Xử lý khi chọn ảnh
    const handleImages = (files: FileList | null) => {
        if (!files || files.length === 0) return;
        
        // Chỉ lấy file đầu tiên vì OMR chấm từng bài
        const file = files[0];
        setOmrFile(file);
        setOmrImagePreview(URL.createObjectURL(file));
        
        // Reset kết quả cũ
        setServerResult(null);
        setResultImageUrl(null);
    };

    const removeImage = () => {
        setOmrFile(null);
        setOmrImagePreview(null);
        setServerResult(null);
    };

    const handleSubmit = async () => {
        if (!omrFile) {
            alert("Vui lòng tải lên ảnh phiếu trả lời!");
            return;
        }
        if (!answerKey) {
            alert("Vui lòng nhập đáp án đúng!");
            return;
        }

        setIsLoading(true);
        const formData = new FormData();

        // 1. Append đúng key mà Backend yêu cầu (xem file omr_grading.py)
        formData.append("file", omrFile); 
        formData.append("answers", answerKey); 
        formData.append("num_questions", numQuestions.toString());
        formData.append("num_choices", "5"); // Mặc định 5 lựa chọn

        try {
            // 2. Gọi đúng Endpoint OMR
            const res = await fetch("http://localhost:8000/api/omr/grade", {
                method: "POST",
                body: formData,
                // Lưu ý: Không cần header Authorization nếu API này public, 
                // nếu cần auth thì uncomment dòng dưới
                // headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });

            const data = await res.json();

            if (res.ok) {
                setServerResult(data.data);
                // Backend trả về đường dẫn tương đối (vd: /static/omr/...), cần nối thêm host
                setResultImageUrl(`http://localhost:8000${data.image_url}`);
                alert("Chấm điểm thành công!");
            } else {
                alert(`Lỗi: ${data.detail || data.message || "Không xác định"}`);
            }
        } catch (err) {
            console.error(err);
            alert("Gửi yêu cầu thất bại! Kiểm tra server.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <TopMenu />
            <div className="handwritten-container">
                <h1 style={{ textAlign: "center", marginBottom: "20px" }}>Chấm Thi Trắc Nghiệm (OMR)</h1>

                <div style={{ display: "flex", gap: "30px", justifyContent: "center", flexWrap: "wrap" }}>
                    
                    {/* CỘT TRÁI: CẤU HÌNH & UPLOAD */}
                    <div style={{ flex: 1, minWidth: "300px", maxWidth: "500px" }}>
                        
                        {/* 1. Nhập đáp án */}
                        <div className="config-section" style={{ marginBottom: "20px", padding: "15px", border: "1px solid #ddd", borderRadius: "8px" }}>
                            <h3>1. Cấu hình đáp án</h3>
                            <div style={{ marginBottom: "10px" }}>
                                <label style={{ display: "block", fontWeight: "bold" }}>Chuỗi đáp án đúng (cách nhau dấu phẩy):</label>
                                <input 
                                    type="text" 
                                    value={answerKey} 
                                    onChange={(e) => setAnswerKey(e.target.value)}
                                    placeholder="Ví dụ: 1,2,0,1,4"
                                    style={{ width: "100%", padding: "8px", marginTop: "5px" }}
                                />
                                <small style={{ color: "gray" }}>Quy ước: A=0, B=1, C=2, D=3, E=4</small>
                            </div>
                            <div>
                                <label style={{ display: "block", fontWeight: "bold" }}>Số câu hỏi:</label>
                                <input 
                                    type="number" 
                                    value={numQuestions} 
                                    onChange={(e) => setNumQuestions(Number(e.target.value))}
                                    style={{ width: "100%", padding: "8px", marginTop: "5px" }}
                                />
                            </div>
                        </div>

                        {/* 2. Upload Ảnh */}
                        <div className="upload-section">
                            <h3>2. Tải ảnh phiếu trả lời</h3>
                            <div className="upload-area">
                                {!omrImagePreview && (
                                    <ImageUploader onClick={() => setShowPopup(true)} />
                                )}

                                {omrImagePreview && (
                                    <ImagePreviewList
                                        images={[omrImagePreview]}
                                        onRemove={() => removeImage()}
                                        onView={(img) => setViewImage(img)}
                                    />
                                )}
                            </div>
                        </div>

                        {/* Nút Submit */}
                        <div className="submit-area" style={{ marginTop: "20px" }}>
                            <button
                                className="submit-btn"
                                onClick={handleSubmit}
                                disabled={isLoading}
                                style={{ width: "100%", opacity: isLoading ? 0.7 : 1 }}
                            >
                                {isLoading ? "Đang chấm điểm..." : "Chấm điểm ngay"}
                            </button>
                        </div>
                    </div>

                    {/* CỘT PHẢI: KẾT QUẢ */}
                    <div style={{ flex: 1, minWidth: "300px", maxWidth: "600px" }}>
                        <h3>3. Kết quả chấm</h3>
                        {serverResult ? (
                            <div style={{ border: "1px solid #4CAF50", padding: "15px", borderRadius: "8px", backgroundColor: "#f9fff9" }}>
                                <h2 style={{ color: "#2e7d32", textAlign: "center" }}>
                                    Điểm số: {serverResult.score} / 100
                                </h2>
                                
                                <div style={{ margin: "15px 0" }}>
                                    <p><strong>Đáp án của bạn:</strong> {JSON.stringify(serverResult.user_answers)}</p>
                                    <p><strong>Đáp án đúng:</strong> {JSON.stringify(serverResult.correct_answers)}</p>
                                </div>

                                {resultImageUrl && (
                                    <div style={{ textAlign: "center" }}>
                                        <p style={{ fontWeight: "bold" }}>Ảnh đã chấm:</p>
                                        <img 
                                            src={resultImageUrl} 
                                            alt="Graded Result" 
                                            style={{ maxWidth: "100%", border: "2px solid #ddd", borderRadius: "4px", cursor: "pointer" }}
                                            onClick={() => setViewImage(resultImageUrl)}
                                        />
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div style={{ padding: "20px", textAlign: "center", color: "gray", border: "1px dashed #ccc" }}>
                                Chưa có kết quả. Vui lòng tải ảnh và nhấn Chấm điểm.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Popup chọn nguồn ảnh */}
            {showPopup && (
                <UploadPopup
                    onSelect={(files) => {
                        handleImages(files);
                        setShowPopup(false);
                    }}
                    onClose={() => setShowPopup(false)}
                />
            )}

            {/* Popup xem ảnh lớn */}
            {viewImage && (
                <ViewImageModal
                    img={viewImage}
                    onClose={() => setViewImage(null)}
                />
            )}
        </div>
    );
}