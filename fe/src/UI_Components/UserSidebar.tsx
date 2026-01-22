import { useState, useEffect } from "react";
import { X } from "lucide-react";
import "./UserSidebar.css";

interface UserSidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

interface User {
    user_name: string;
    email: string;
    [key: string]: any; // nếu có thêm field
}

export default function UserSidebar({ isOpen, onClose }: UserSidebarProps) {
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        const userStr = localStorage.getItem("user");
        if (userStr) {
            try {
                const userObj = JSON.parse(userStr);
                setUser(userObj);
            } catch (err) {
                console.error("Lỗi parse user từ localStorage:", err);
            }
        }
    }, []);

    const handleSignOut = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/";
    };

    return (
        <div className={`sidebar-overlay ${isOpen ? "active" : ""}`} onClick={onClose}>
            <div className="sidebar" onClick={(e) => e.stopPropagation()}>
                <div className="sidebar-header">
                    <h3>Thông tin người dùng</h3>
                    <button className="close-btn" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>
                <div className="sidebar-content">
                    {user ? (
                        <>
                            <p>Tên: {user.user_name}</p>
                            <p>Email: {user.email}</p>
                        </>
                    ) : (
                        <p>Chưa có thông tin người dùng</p>
                    )}

                    <button className="signout-btn" onClick={handleSignOut}>
                        Đăng xuất
                    </button>
                </div>
            </div>
        </div>
    );
}
