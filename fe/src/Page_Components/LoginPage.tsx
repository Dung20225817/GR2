import { useState } from "react";
import "../UI_Components/LoginPage.css";
import { motion } from "framer-motion";
import { Smartphone, Mail, Lock } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  // Fake login
  const loginRequest = async (email: string, password: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) return null; // login sai

      return await res.json(); // login đúng → trả user info + token
    } catch (err) {
      console.error("Login error:", err);
      return null;
    }
  };


  const handleLogin = async () => {
    const user = await loginRequest(email, password);

    if (!user) {
      alert("Sai email hoặc mật khẩu!");
      return;
    }

    // Lưu thông tin user
    localStorage.setItem("token", user.token);
    localStorage.setItem("uid", user.uid);     // ⭐ Quan trọng
    localStorage.setItem("user_name", user.user_name);
    localStorage.setItem("email", user.email);
    localStorage.setItem("phone", user.phone);

    // Hoặc lưu tất cả vào 1 object:
    localStorage.setItem("user", JSON.stringify(user));

    navigate("/home");
  };



  return (
    <div className="login-page-container">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="login-card-wrapper"
      >
        <div className="login-card">
          <div className="login-card-content">
            <div className="login-header">
              <Smartphone className="login-icon" />
              <h2>Đăng nhập</h2>
              <p>Chấm điểm bằng hình ảnh</p>
            </div>

            <div className="inputs-container">
              <div className="input-wrapper">
                <Mail className="input-icon" />
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="login-input"
                />
              </div>

              <div className="input-wrapper">
                <Lock className="input-icon" />
                <input
                  type="password"
                  placeholder="Mật khẩu"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="login-input"
                />
              </div>
            </div>

            <button className="login-button" onClick={handleLogin}>
              Đăng nhập
            </button>

            <p className="login-footer">
              Chưa có tài khoản?{" "}
              <Link to="/register" className="register-link">
                Đăng ký
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
