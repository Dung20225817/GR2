import TopMenu from "../UI_Components/TopMenu";
import { useState } from "react";
import "../UI_Components/HandwrittenQuestionPage.css";
import ImagePreviewList from "../UI_Components/ImagePreviewList";
import ImageUploader from "../UI_Components/ImageUploader.tsx";
import UploadPopup from "../UI_Components/UploadPopup.tsx";
import ViewImageModal from "../UI_Components/ViewImageModal.tsx";


export default function HandwrittenQuestionPage() {
    const [questionFiles, setQuestionFiles] = useState<File[]>([]);
    const [questionImages, setQuestionImages] = useState<string[]>([]);

    const [resultFiles, setResultFiles] = useState<File[]>([]);
    const [resultImages, setResultImages] = useState<string[]>([]);

    const [serverResult, setServerResult] = useState<any>(null);
    const [comparisonResult, setComparisonResult] = useState<{
        percentage: number;
        details: Array<{ questionText: string; answerText: string; similarity: number }>
    } | null>(null);

    // state popup phân biệt hàng nào
    const [showPopup, setShowPopup] = useState<null | "question" | "result">(null);
    const [viewImage, setViewImage] = useState<string | null>(null);

    // Hàm tính độ tương đồng giữa 2 chuỗi (Levenshtein distance)
    const calculateSimilarity = (str1: string, str2: string): number => {
        const s1 = str1.toLowerCase().trim();
        const s2 = str2.toLowerCase().trim();

        if (s1 === s2) return 100;
        if (s1.length === 0 || s2.length === 0) return 0;

        const matrix: number[][] = [];

        for (let i = 0; i <= s2.length; i++) {
            matrix[i] = [i];
        }

        for (let j = 0; j <= s1.length; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= s2.length; i++) {
            for (let j = 1; j <= s1.length; j++) {
                if (s2.charAt(i - 1) === s1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }

        const distance = matrix[s2.length][s1.length];
        const maxLength = Math.max(s1.length, s2.length);
        const similarity = ((maxLength - distance) / maxLength) * 100;

        return Math.round(similarity * 100) / 100;
    };

    // Hàm so sánh kết quả
    const compareResults = (data: any) => {
        const questions = data.question_results || [];
        const answers = data.answer_results || [];

        if (questions.length === 0 || answers.length === 0) {
            return { percentage: 0, details: [] };
        }

        const details = questions.map((q: any, index: number) => {
            const answer = answers[index];
            if (!answer) {
                return {
                    questionText: q.result,
                    answerText: "Không có câu trả lời",
                    similarity: 0
                };
            }

            const similarity = calculateSimilarity(q.result, answer.result);
            return {
                questionText: q.result,
                answerText: answer.result,
                similarity
            };
        });

        const averageSimilarity = details.reduce((sum: number, item) => sum + item.similarity, 0) / details.length;

        return {
            percentage: Math.round(averageSimilarity * 100) / 100,
            details
        };
    };

    const handleImages = (files: FileList | null, type: "question" | "result") => {
        if (!files) return;

        const arrFiles = Array.from(files);
        const previewUrls = arrFiles.map(f => URL.createObjectURL(f));

        if (type === "question") {
            setQuestionFiles(prev => [...prev, ...arrFiles]);
            setQuestionImages(prev => [...prev, ...previewUrls]);
        } else {
            setResultFiles(prev => [...prev, ...arrFiles]);
            setResultImages(prev => [...prev, ...previewUrls]);
        }
    };

    const handleSubmit = async () => {
        const formData = new FormData();

        const uid = localStorage.getItem("uid");
        const token = localStorage.getItem("token");

        if (!uid) {
            alert("Bạn chưa đăng nhập!");
            return;
        }

        formData.append("uid", uid);
        questionFiles.forEach((file) => formData.append("question_images", file));
        resultFiles.forEach((file) => formData.append("result_images", file));

        try {
            const res = await fetch("http://localhost:8000/api/handwritten/upload", {
                method: "POST",
                body: formData,
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            const data = await res.json();
            setServerResult(data);

            // So sánh kết quả
            const comparison = compareResults(data);
            setComparisonResult(comparison);

            alert("Gửi ảnh thành công!");
        } catch (err) {
            console.error(err);
            alert("Gửi ảnh thất bại!");
        }
    };

    const removeImage = (index: number, type: "question" | "result") => {
        if (type === "question") {
            setQuestionImages(prev => prev.filter((_, i) => i !== index));
            setQuestionFiles(prev => prev.filter((_, i) => i !== index));
        } else {
            setResultImages(prev => prev.filter((_, i) => i !== index));
            setResultFiles(prev => prev.filter((_, i) => i !== index));
        }
    };

    return (
        <div>
            <TopMenu />
            <div className="handwritten-container">
                {/* Hàng 1: Ảnh câu hỏi */}
                <h2>Tải ảnh câu hỏi viết tay</h2>
                <div className="upload-area">
                    <ImageUploader onClick={() => setShowPopup("question")} />

                    <ImagePreviewList
                        images={questionImages}
                        onRemove={(idx: number) => removeImage(idx, "question")}
                        onView={(img: string) => setViewImage(img)}
                    />

                </div>

                {/* Hàng 2: Ảnh kết quả */}
                <h2 style={{ marginTop: "30px" }}>Tải ảnh kết quả</h2>
                <div className="upload-area">
                    <ImageUploader onClick={() => setShowPopup("result")} />

                    <ImagePreviewList
                        images={resultImages}
                        onRemove={(idx: number) => removeImage(idx, "result")}
                        onView={(img: string) => setViewImage(img)}
                    />

                </div>
            </div>

            {/* Popup chọn nguồn ảnh */}
            {showPopup && (
                <UploadPopup
                    onSelect={(files: FileList) => {
                        if (showPopup) handleImages(files, showPopup);
                        setShowPopup(null);
                    }}
                    onClose={() => setShowPopup(null)}
                />
            )}

            {/* Popup xem ảnh lớn */}
            {viewImage && (
                <ViewImageModal
                    img={viewImage}
                    onClose={() => setViewImage(null)}
                />
            )}


            <div className="submit-area">
                <button
                    className="submit-btn"
                    onClick={handleSubmit}
                >
                    Gửi ảnh
                </button>
            </div>

            {/* Hiển thị kết quả so sánh */}
            {comparisonResult && (
                <div className="result-box">
                    <h3>Kết quả so sánh</h3>
                    <div style={{
                        fontSize: "24px",
                        fontWeight: "bold",
                        color: comparisonResult.percentage >= 80 ? "#4caf50" :
                            comparisonResult.percentage >= 60 ? "#ff9800" : "#f44336",
                        marginBottom: "20px"
                    }}>
                        Độ chính xác: {comparisonResult.percentage}%
                    </div>

                    {comparisonResult.details.map((detail, index) => (
                        <div key={index} style={{
                            border: "1px solid #ddd",
                            padding: "15px",
                            marginBottom: "15px",
                            borderRadius: "8px",
                            backgroundColor: "#f9f9f9"
                        }}>
                            <h4>Câu {index + 1} - Độ giống: {detail.similarity}%</h4>
                            <div style={{ marginTop: "10px" }}>
                                <strong>Câu hỏi:</strong>
                                <p style={{ margin: "5px 0", padding: "10px", backgroundColor: "#e3f2fd", borderRadius: "4px" }}>
                                    {detail.questionText}
                                </p>
                            </div>
                            <div style={{ marginTop: "10px" }}>
                                <strong>Câu trả lời:</strong>
                                <p style={{ margin: "5px 0", padding: "10px", backgroundColor: "#fff3e0", borderRadius: "4px" }}>
                                    {detail.answerText}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {serverResult && (
                <div className="result-box" style={{ marginTop: "20px" }}>
                    <h3>Kết quả từ Backend (Raw Data):</h3>
                    <pre>{JSON.stringify(serverResult, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}