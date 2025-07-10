import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import "../styles/AuthPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const togglePassword = () => setShowPassword(!showPassword);

  const handleLogin = (e) => {
    e.preventDefault();
    console.log("Logging in...");
  };

  return (
    <div className="auth-container">
      {/* Logo Section */}
      <div className="logo-section">
        <img
          src="/nomnom-ai logo.PNG"
          alt="NomNom AI Logo"
          className="logo-img"
        />
        <h1 className="logo-text">NomNom AI</h1>
      </div>

      {/* Form Container */}
      <div className="form-container">
        <h2 className="form-title">Login.</h2>
        <p className="form-subtitle">Sign in to continue.</p>

        <form className="login-form" onSubmit={handleLogin}>
          {/* Username Field */}
          <div className="form-input-group">
            <label className="form-label">USERNAME</label>
            <input
              type="text"
              placeholder="Enter Username"
              className="form-input"
              required
            />
          </div>

          {/* Password Field */}
          <div className="form-input-group">
            <label className="form-label">PASSWORD</label>
            <div className="password-field">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter Password"
                className="form-input"
                required
              />
              <button
                type="button"
                className="toggle-btn"
                onClick={togglePassword}
              >
                {showPassword ? (
                  <EyeOff size={20} color="#FDFFFC" />
                ) : (
                  <Eye size={20} color="#FDFFFC" />
                )}
              </button>
            </div>
          </div>

          <button type="submit" className="login-btn">
            Log in
          </button>
        </form>

        <button
          className="forgot-link"
          onClick={() => alert("Forgot Password placeholder")}
        >
          Forgot Password?
        </button>
        <p className="register-text">
          Don’t have an account?{" "}
          <span
            className="register-link"
            onClick={() => navigate("/register")}
          >
            Register Here
          </span>
        </p>
      </div>
    </div>
  );
}
